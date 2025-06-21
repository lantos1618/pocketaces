import secrets
import hashlib
from typing import Dict, Optional, Tuple, Any, List
from datetime import datetime, timedelta
from pydantic import BaseModel

# JWT import with proper error handling
try:
    import jwt as _jwt

    jwt = _jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

    # Create a mock jwt module for development
    class MockJWT:
        @staticmethod
        def encode(
            payload: Dict[str, Any], secret: str, algorithm: str = "HS256"
        ) -> str:
            import base64
            import json

            data = json.dumps(payload).encode()
            return base64.b64encode(data).decode()

        @staticmethod
        def decode(
            token: str, secret: str, algorithms: Optional[List[str]] = None
        ) -> Dict[str, Any]:
            import base64
            import json

            try:
                data = base64.b64decode(token).decode()
                return json.loads(data)
            except:
                raise ValueError("Invalid token")

    jwt: Any = MockJWT()


class PlayerToken(BaseModel):
    """Player authentication token."""

    player_id: str
    room_id: Optional[str] = None
    game_id: Optional[str] = None
    created_at: datetime
    expires_at: datetime


class AuthManager:
    """Manages player authentication and authorization."""

    def __init__(self, secret_key: Optional[str] = None):
        """Initialize the auth manager."""
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.active_tokens: Dict[str, PlayerToken] = {}
        self.player_sessions: Dict[
            str, Dict[str, Optional[str]]
        ] = {}  # player_id -> {token, room_id, game_id}

    def generate_player_token(
        self,
        player_id: str,
        room_id: Optional[str] = None,
        game_id: Optional[str] = None,
    ) -> str:
        """Generate a new authentication token for a player."""
        # Create token data
        now = datetime.now()
        expires_at = now + timedelta(hours=24)  # 24 hour expiry

        token_data = PlayerToken(
            player_id=player_id,
            room_id=room_id,
            game_id=game_id,
            created_at=now,
            expires_at=expires_at,
        )

        # Generate JWT token
        payload = {
            "player_id": player_id,
            "room_id": room_id,
            "game_id": game_id,
            "exp": expires_at.timestamp(),
            "iat": now.timestamp(),
        }

        token = jwt.encode(payload, self.secret_key, algorithm="HS256")

        # Store token data
        self.active_tokens[token] = token_data
        self.player_sessions[player_id] = {
            "token": token,
            "room_id": room_id,
            "game_id": game_id,
        }

        return token

    def validate_token(self, token: str) -> Optional[str]:
        """Validate a token and return the player_id if valid."""
        try:
            # Decode JWT
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            player_id = payload.get("player_id")

            if not player_id:
                return None

            # Check if token is in active tokens
            if token not in self.active_tokens:
                return None

            token_data = self.active_tokens[token]

            # Check if expired
            if datetime.now() > token_data.expires_at:
                self._remove_token(token)
                return None

            return player_id

        except Exception:
            return None

    def get_token_data(self, token: str) -> Optional[PlayerToken]:
        """Get token data if token is valid."""
        if token in self.active_tokens:
            token_data = self.active_tokens[token]
            if datetime.now() <= token_data.expires_at:
                return token_data
            else:
                self._remove_token(token)
        return None

    def update_player_session(
        self,
        player_id: str,
        room_id: Optional[str] = None,
        game_id: Optional[str] = None,
    ) -> bool:
        """Update a player's session with new room/game information."""
        if player_id not in self.player_sessions:
            return False

        session = self.player_sessions[player_id]
        token = session.get("token")

        if token and token in self.active_tokens:
            token_data = self.active_tokens[token]
            token_data.room_id = room_id
            token_data.game_id = game_id

            # Update session
            session["room_id"] = room_id
            session["game_id"] = game_id

            return True

        return False

    def authorize_player_action(self, token: str, game_id: str, player_id: str) -> bool:
        """Authorize a player to make an action in a specific game."""
        token_data = self.get_token_data(token)
        if not token_data:
            return False

        # Player can only act for themselves
        if token_data.player_id != player_id:
            return False

        # Player must be in the game they're trying to act in
        if token_data.game_id != game_id:
            return False

        return True

    def authorize_room_access(self, token: str, room_id: str) -> bool:
        """Authorize a player to access a specific room."""
        token_data = self.get_token_data(token)
        if not token_data:
            return False

        # Player must be in the room they're trying to access
        if token_data.room_id != room_id:
            return False

        return True

    def _remove_token(self, token: str) -> None:
        """Remove a token from active tokens."""
        if token in self.active_tokens:
            token_data = self.active_tokens[token]
            player_id = token_data.player_id

            # Remove from active tokens
            del self.active_tokens[token]

            # Remove from player sessions if this is the current token
            if player_id in self.player_sessions:
                session = self.player_sessions[player_id]
                if session.get("token") == token:
                    del self.player_sessions[player_id]

    def revoke_player_token(self, player_id: str) -> bool:
        """Revoke all tokens for a player."""
        if player_id in self.player_sessions:
            token = self.player_sessions[player_id].get("token")
            if token:
                self._remove_token(token)
                return True
        return False

    def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens and return count of removed tokens."""
        now = datetime.now()
        expired_tokens = []

        for token, token_data in self.active_tokens.items():
            if now > token_data.expires_at:
                expired_tokens.append(token)

        for token in expired_tokens:
            self._remove_token(token)

        return len(expired_tokens)


# Global auth manager instance
auth_manager = AuthManager()
