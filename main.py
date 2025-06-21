#!/usr/bin/env python3
"""
Pocket Aces - AI Poker Game Server
Main entry point for the FastAPI application
"""

import os
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import secrets

from fastapi import (
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Header,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

from app.store.game_store import game_store
from app.core.agents.agent_manager import agent_manager
from app.core.game.poker_engine import poker_engine
from app.core.auth.auth_manager import auth_manager
from app.models.game_models import Player, PlayerAction, ActionType
from app.models.agent_models import AgentPersonality

# Load environment variables
load_dotenv()


# Configuration
class Config:
    """Application configuration"""

    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

    # Game Settings
    DEFAULT_STARTING_CHIPS = int(os.getenv("DEFAULT_STARTING_CHIPS", "1000"))
    DEFAULT_SMALL_BLIND = int(os.getenv("DEFAULT_SMALL_BLIND", "10"))
    DEFAULT_BIG_BLIND = int(os.getenv("DEFAULT_BIG_BLIND", "20"))
    MAX_PLAYERS_PER_ROOM = int(os.getenv("MAX_PLAYERS_PER_ROOM", "3"))
    GAME_TIMEOUT_SECONDS = int(os.getenv("GAME_TIMEOUT_SECONDS", "30"))

    # CORS
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:8080"
    ).split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting Pocket Aces Server...")

    # Initialize agent manager with OpenAI
    if Config.OPENAI_API_KEY:
        try:
            await agent_manager.initialize_llm(Config.OPENAI_API_KEY)
            print("✅ LangChain initialized with OpenAI")
        except Exception as e:
            print(f"⚠️  Failed to initialize OpenAI: {e}")
            print("🤖 Agents will use rule-based decision making")
    else:
        print("⚠️  No OpenAI API key provided - using rule-based agents")

    # Create default rooms
    await _create_default_rooms()

    print(f"🎮 Server ready on http://{Config.HOST}:{Config.PORT}")
    print("📚 API docs available at /docs")

    yield

    # Shutdown
    print("🛑 Shutting down Pocket Aces Server...")


async def _create_default_rooms() -> None:
    """Create default game rooms"""
    default_rooms: List[Dict[str, Any]] = [
        {
            "name": "Demo Table",
            "max_players": 3,
            "settings": {"small_blind": 5, "big_blind": 10, "starting_chips": 500},
        },
        {
            "name": "High Stakes",
            "max_players": 3,
            "settings": {"small_blind": 25, "big_blind": 50, "starting_chips": 2000},
        },
    ]

    for room_config in default_rooms:
        await game_store.create_room(
            name=str(room_config["name"]),
            max_players=int(room_config["max_players"]),
            settings=room_config["settings"],
        )


# Create FastAPI app
app = FastAPI(
    title="Pocket Aces Poker",
    description="Real-time poker game with AI agents",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.player_connections: Dict[str, str] = {}  # player_id -> client_id

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        # Remove from player connections
        player_id = None
        for pid, cid in self.player_connections.items():
            if cid == client_id:
                player_id = pid
                break

        if player_id:
            del self.player_connections[player_id]

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

    def register_player(self, player_id: str, client_id: str):
        """Register a player with their client connection."""
        self.player_connections[player_id] = client_id


manager = ConnectionManager()


# Authentication dependency
async def get_current_player(
    authorization: Optional[str] = Header(None),
) -> Optional[str]:
    """Get current player from authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.replace("Bearer ", "")
    return auth_manager.validate_token(token)


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Room endpoints
@app.get("/api/rooms")
async def get_rooms():
    """Get all available rooms"""
    rooms = game_store.get_all_rooms()
    return [room.model_dump() for room in rooms]


@app.post("/api/rooms")
async def create_room(
    name: str, max_players: int = 3, settings: Optional[Dict[str, Any]] = None
):
    """Create a new room"""
    room = await game_store.create_room(name, max_players, settings or {})
    return room.model_dump()


@app.get("/api/rooms/{room_id}")
async def get_room(room_id: str):
    """Get room details"""
    room = game_store.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room.model_dump()


# Game endpoints
@app.post("/api/rooms/{room_id}/start-game")
async def start_game(room_id: str):
    """Start a new game in a room"""
    game = poker_engine.start_new_game(room_id)
    if not game:
        raise HTTPException(status_code=400, detail="Cannot start game")
    return game.model_dump()


@app.get("/api/games/{game_id}")
async def get_game(game_id: str):
    """Get game state"""
    game = game_store.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game.model_dump()


@app.post("/api/games/{game_id}/action")
async def make_game_action(
    game_id: str,
    player_id: str,
    action_type: str,
    amount: Optional[int] = None,
    current_player: Optional[str] = Depends(get_current_player),
):
    """Make a player action in a game"""
    # Validate authentication
    if not current_player or current_player != player_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Validate action type
    try:
        valid_action_type = ActionType(action_type)
    except ValueError:
        valid_actions = [action.value for action in ActionType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action_type. Must be one of: {valid_actions}",
        )

    # Validate amount for actions that require it
    if valid_action_type in [ActionType.RAISE, ActionType.CALL] and amount is None:
        raise HTTPException(
            status_code=400,
            detail=f"Amount is required for {valid_action_type.value} action",
        )

    # Make the action
    success = await game_store.make_player_action(
        game_id, player_id, valid_action_type.value, amount
    )
    if not success:
        raise HTTPException(status_code=400, detail="Invalid action")

    # Return updated game state
    game = game_store.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game.model_dump()


@app.post("/api/rooms/{room_id}/join")
async def join_room(room_id: str, player_name: str):
    """Join a room as a player"""
    # Create player
    player = Player(
        id=f"player_{secrets.token_urlsafe(8)}", name=player_name, chips=1000
    )

    # Add to room
    success = await game_store.add_player_to_room(room_id, player)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot join room")

    # Generate authentication token
    token = auth_manager.generate_player_token(player.id, room_id)

    return {
        "player_id": player.id,
        "token": token,
        "message": "Joined room successfully",
    }


# Agent endpoints
@app.get("/api/agents")
async def get_agents():
    """Get all available AI agents"""
    agents = game_store.get_all_agents()
    return [agent.model_dump() for agent in agents]


@app.get("/api/action-types")
async def get_action_types():
    """Get all available action types"""
    return {
        "action_types": [action.value for action in ActionType],
        "descriptions": {
            ActionType.FOLD.value: "Fold your hand and exit the current round",
            ActionType.CHECK.value: "Pass the action to the next player without betting",
            ActionType.CALL.value: "Match the current bet amount",
            ActionType.RAISE.value: "Increase the current bet amount",
            ActionType.ALL_IN.value: "Bet all remaining chips",
        },
    }


@app.post("/api/rooms/{room_id}/add-agent")
async def add_agent_to_room(room_id: str, agent_id: str):
    """Add an AI agent to a room"""
    agent = game_store.get_agent_personality(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Create player from agent
    from app.models.mock_data import create_mock_player_from_agent

    player = create_mock_player_from_agent(agent)

    success = await game_store.add_player_to_room(room_id, player)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot add agent to room")

    return {"message": f"Added {agent.name} to room"}


# WebSocket endpoint for real-time game updates - SECURED
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket, client_id: str, token: Optional[str] = None
):
    await manager.connect(websocket, client_id)

    # Validate token if provided
    player_id = None
    if token:
        player_id = auth_manager.validate_token(token)
        if player_id:
            manager.register_player(player_id, client_id)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle different message types with authentication
            if message["type"] == "join_room":
                await handle_join_room(client_id, message, player_id)
            elif message["type"] == "make_action":
                await handle_make_action(client_id, message, player_id)
            elif message["type"] == "get_game_state":
                await handle_get_game_state(client_id, message)

    except WebSocketDisconnect:
        manager.disconnect(client_id)


async def handle_join_room(
    client_id: str, message: Dict[str, Any], player_id: Optional[str] = None
):
    """Handle room join request"""
    room_id = message.get("room_id")
    player_name = message.get("player_name", "Anonymous")

    if not room_id:
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": "room_id is required"}), client_id
        )
        return

    # Type assertion after validation
    assert isinstance(room_id, str)

    try:
        result = await join_room(room_id, player_name)
        await manager.send_personal_message(
            json.dumps({"type": "room_joined", "data": result}), client_id
        )
    except Exception as e:
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": str(e)}), client_id
        )


async def handle_make_action(
    client_id: str, message: Dict[str, Any], player_id: Optional[str] = None
):
    """Handle player action with authentication"""
    game_id = message.get("game_id")
    action_player_id = message.get("player_id")
    action_type = message.get("action_type")
    amount = message.get("amount")

    if not all([game_id, action_player_id, action_type]):
        await manager.send_personal_message(
            json.dumps(
                {
                    "type": "error",
                    "message": "game_id, player_id, and action_type are required",
                }
            ),
            client_id,
        )
        return

    # SECURITY CHECK: Verify player is authorized to act
    if not player_id or player_id != action_player_id:
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": "Unauthorized action"}), client_id
        )
        return

    # Type assertions after validation
    assert isinstance(game_id, str)
    assert isinstance(action_player_id, str)
    assert isinstance(action_type, str)

    # Validate action type
    try:
        valid_action_type = ActionType(action_type)
    except ValueError:
        valid_actions = [action.value for action in ActionType]
        await manager.send_personal_message(
            json.dumps(
                {
                    "type": "error",
                    "message": f"Invalid action_type. Must be one of: {valid_actions}",
                }
            ),
            client_id,
        )
        return

    # Validate amount for actions that require it
    if valid_action_type in [ActionType.RAISE, ActionType.CALL] and amount is None:
        await manager.send_personal_message(
            json.dumps(
                {
                    "type": "error",
                    "message": f"Amount is required for {valid_action_type.value} action",
                }
            ),
            client_id,
        )
        return

    try:
        success = await game_store.make_player_action(
            game_id, action_player_id, valid_action_type.value, amount
        )
        if success:
            # Broadcast updated game state
            game = game_store.get_game(game_id)
            if game:
                await manager.broadcast(
                    json.dumps({"type": "game_updated", "data": game.model_dump()})
                )
        else:
            await manager.send_personal_message(
                json.dumps({"type": "error", "message": "Invalid action"}), client_id
            )
    except Exception as e:
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": str(e)}), client_id
        )


async def handle_get_game_state(client_id: str, message: Dict[str, Any]):
    """Handle game state request"""
    game_id = message.get("game_id")

    if not game_id:
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": "game_id is required"}), client_id
        )
        return

    # Type assertion after validation
    assert isinstance(game_id, str)

    try:
        game = game_store.get_game(game_id)
        if game:
            await manager.send_personal_message(
                json.dumps({"type": "game_state", "data": game.model_dump()}), client_id
            )
        else:
            await manager.send_personal_message(
                json.dumps({"type": "error", "message": "Game not found"}), client_id
            )
    except Exception as e:
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": str(e)}), client_id
        )


if __name__ == "__main__":
    # Validate required environment variables
    if not Config.OPENAI_API_KEY:
        print("⚠️  Warning: OPENAI_API_KEY not set - agents will use rule-based logic")

    if not Config.ELEVENLABS_API_KEY:
        print(
            "⚠️  Warning: ELEVENLABS_API_KEY not set - voice features will be disabled"
        )

    # Start server
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level=Config.LOG_LEVEL,
        access_log=True,
    )
