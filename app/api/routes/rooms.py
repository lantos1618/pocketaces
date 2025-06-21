from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException
from ...store.game_store import game_store
from ...models.game_models import GameRoom

router = APIRouter(prefix="/api/rooms", tags=["Rooms"])


@router.get("/")  # type: ignore[misc]
async def get_rooms() -> List[Dict[str, Any]]:
    """Get all available rooms"""
    rooms = game_store.get_all_rooms()
    return [dict(room.model_dump()) for room in rooms]


@router.post("/")  # type: ignore[misc]
async def create_room(
    name: str, max_players: int = 3, settings: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a new game room"""
    try:
        room = await game_store.create_room(
            name=name, max_players=max_players, settings=settings or {}
        )
        return dict(room.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{room_id}")  # type: ignore[misc]
async def get_room(room_id: str) -> Dict[str, Any]:
    """Get a specific room by ID"""
    room = game_store.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return dict(room.model_dump())


@router.post("/{room_id}/start-game")  # type: ignore[misc]
async def start_game(room_id: str) -> Dict[str, Any]:
    """Start a new game in a room"""
    game = await game_store.create_game(room_id)
    if not game:
        raise HTTPException(status_code=400, detail="Cannot start game")
    return dict(game.model_dump())


@router.post("/{room_id}/join")  # type: ignore[misc]
async def join_room(room_id: str, player_name: str) -> Dict[str, Any]:
    """Join a room as a player"""
    from ...models.game_models import Player

    # Create a new player
    player = Player(
        name=player_name,
        chips=1000,  # Default starting chips
        position=0,  # Will be assigned by the game
        is_human=True,
    )

    # Add player to room
    success = await game_store.add_player_to_room(room_id, player)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot join room")

    return {
        "player_id": player.id,
        "room_id": room_id,
        "message": f"Successfully joined room as {player_name}",
    }


@router.post("/{room_id}/add-agent")  # type: ignore[misc]
async def add_agent_to_room(room_id: str, agent_id: str) -> Dict[str, Any]:
    """Add an AI agent to a room"""
    from ...models.game_models import Player

    # Get agent personality
    agent_personality = game_store.get_agent_personality(agent_id)
    if not agent_personality:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Create agent player
    agent_player = Player(
        name=agent_personality.name,
        chips=1000,  # Default starting chips
        position=0,  # Will be assigned by the game
        is_agent=True,
        agent_id=agent_id,
    )

    # Add agent to room
    success = await game_store.add_player_to_room(room_id, agent_player)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot add agent to room")

    return {
        "player_id": agent_player.id,
        "agent_id": agent_id,
        "room_id": room_id,
        "message": f"Successfully added {agent_personality.name} to room",
    }
