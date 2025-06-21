import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from ...store.game_store import game_store
from ...core.auth.auth_manager import auth_manager

router = APIRouter(tags=["WebSockets"])


class ConnectionManager:
    """Manages WebSocket connections"""

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


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket, client_id: str, token: Optional[str] = None
) -> None:
    """WebSocket endpoint for real-time game updates"""

    await manager.connect(websocket, client_id)

    try:
        # Validate token if provided
        player_id = None
        if token:
            player_id = auth_manager.validate_token(token)
            if player_id:
                manager.register_player(player_id, client_id)

        # Send welcome message
        await manager.send_personal_message(
            json.dumps(
                {
                    "type": "connection_established",
                    "client_id": client_id,
                    "player_id": player_id,
                }
            ),
            client_id,
        )

        # Handle incoming messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            await handle_websocket_message(client_id, message, player_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(client_id)


async def handle_websocket_message(
    client_id: str, message: Dict[str, Any], player_id: Optional[str]
) -> None:
    """Handle incoming WebSocket messages"""

    message_type = message.get("type")

    if message_type == "join_room":
        await handle_join_room(client_id, message, player_id)
    elif message_type == "make_action":
        await handle_make_action(client_id, message, player_id)
    elif message_type == "get_game_state":
        await handle_get_game_state(client_id, message)
    else:
        await manager.send_personal_message(
            json.dumps(
                {"type": "error", "message": f"Unknown message type: {message_type}"}
            ),
            client_id,
        )


async def handle_join_room(
    client_id: str, message: Dict[str, Any], player_id: Optional[str]
) -> None:
    """Handle join room request"""

    room_id = message.get("room_id")
    if not room_id:
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": "Room ID required"}), client_id
        )
        return

    # Get room state
    room = game_store.get_room(room_id)
    if not room:
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": "Room not found"}), client_id
        )
        return

    # Send room state
    await manager.send_personal_message(
        json.dumps(
            {"type": "room_joined", "room": room.model_dump(), "player_id": player_id}
        ),
        client_id,
    )


async def handle_make_action(
    client_id: str, message: Dict[str, Any], player_id: Optional[str]
) -> None:
    """Handle make action request"""

    game_id = message.get("game_id")
    action_type = message.get("action_type")
    amount = message.get("amount")

    if not all([game_id, action_type]):
        await manager.send_personal_message(
            json.dumps(
                {"type": "error", "message": "Game ID and action type required"}
            ),
            client_id,
        )
        return

    # Validate player can make this action
    if player_id and player_id != message.get("player_id"):
        await manager.send_personal_message(
            json.dumps(
                {"type": "error", "message": "Not authorized to act for this player"}
            ),
            client_id,
        )
        return

    # Make the action (this would use the game service)
    # For now, just acknowledge the action
    await manager.send_personal_message(
        json.dumps(
            {
                "type": "action_acknowledged",
                "game_id": game_id,
                "action_type": action_type,
                "amount": amount,
            }
        ),
        client_id,
    )


async def handle_get_game_state(client_id: str, message: Dict[str, Any]) -> None:
    """Handle get game state request"""

    game_id = message.get("game_id")
    if not game_id:
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": "Game ID required"}), client_id
        )
        return

    # Get game state
    game = game_store.get_game(game_id)
    if not game:
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": "Game not found"}), client_id
        )
        return

    # Send game state
    await manager.send_personal_message(
        json.dumps({"type": "game_state", "game": game.model_dump()}), client_id
    )
