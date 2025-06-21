from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Header
from ...store.game_store import game_store
from ...core.game.game_service import GameService
from ...core.auth.auth_manager import auth_manager

router = APIRouter(prefix="/api/games", tags=["Games"])

# Initialize game service
game_service = GameService(game_store)


async def get_current_player(
    authorization: Optional[str] = Header(None),
) -> Optional[str]:
    """Get current player from authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.replace("Bearer ", "")
    return auth_manager.validate_token(token)


@router.get("/{game_id}")  # type: ignore[misc]
async def get_game(game_id: str) -> Dict[str, Any]:
    """Get game state by ID"""
    game = await game_service.get_game_state(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return dict(game.model_dump())


@router.post("/{game_id}/action")  # type: ignore[misc]
async def make_game_action(
    game_id: str,
    player_id: str,
    action_type: str,
    amount: Optional[int] = None,
    current_player: Optional[str] = Depends(get_current_player),
) -> Dict[str, Any]:
    """Make a game action"""

    # Validate authentication if required
    if current_player and current_player != player_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to act for this player"
        )

    # Make the action
    success = await game_service.make_player_action(
        game_id=game_id, player_id=player_id, action_type=action_type, amount=amount
    )

    if not success:
        raise HTTPException(status_code=400, detail="Invalid action")

    # Get updated game state
    game = await game_service.get_game_state(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    return {
        "success": True,
        "game_state": game.model_dump(),
        "message": f"Successfully performed {action_type}",
    }


@router.get("/{game_id}/actions")  # type: ignore[misc]
async def get_available_actions(game_id: str, player_id: str) -> Dict[str, Any]:
    """Get available actions for a player"""
    actions = await game_service.get_available_actions(game_id, player_id)
    return {"game_id": game_id, "player_id": player_id, "available_actions": actions}
