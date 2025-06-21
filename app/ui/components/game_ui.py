"""
Main GameUI component that orchestrates the poker game interface
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

try:
    from nicegui import ui
except ImportError:
    ui = None

from .websocket_client import WebSocketClient
from .card_renderer import CardRenderer
from .player_renderer import PlayerRenderer
from .action_buttons import ActionButtons


class GameUI:
    """Main UI orchestrator for the poker game"""

    def __init__(self):
        # Game state
        self.game_state: Dict[str, Any] = {}
        self.players: Dict[str, Any] = {}
        self.community_cards: List[Dict[str, str]] = []
        self.current_player: Optional[str] = None
        self.game_phase: str = "waiting"
        self.pot: int = 0

        # Game identifiers
        self.current_game_id: Optional[str] = None
        self.player_id: Optional[str] = None
        self.selected_agent: Optional[str] = None

        # WebSocket client
        self.websocket_client = WebSocketClient()

        # UI Elements
        self.game_status_label: Optional[Any] = None
        self.community_cards_div: Optional[Any] = None
        self.players_div: Optional[Any] = None
        self.action_buttons_div: Optional[Any] = None
        self.agent_selection_div: Optional[Any] = None
        self.chat_log_div: Optional[Any] = None
        self.pot_label: Optional[Any] = None
        self.game_area: Optional[Any] = None

        # Register message handlers
        self._register_message_handlers()

    def _register_message_handlers(self):
        """Register WebSocket message handlers"""
        self.websocket_client.register_handler("game_state", self._handle_game_state)
        self.websocket_client.register_handler(
            "player_action", self._handle_player_action
        )
        self.websocket_client.register_handler("agent_voice", self._handle_agent_voice)
        self.websocket_client.register_handler("game_phase", self._handle_phase_change)

    async def connect_to_game(self, game_id: str, player_id: str):
        """Connect to a game via WebSocket"""
        uri = f"ws://localhost:8000/ws/{player_id}"
        success = await self.websocket_client.connect(uri)

        if success:
            # Subscribe to game updates
            await self.websocket_client.send_message(
                {"type": "subscribe_game", "game_id": game_id}
            )

            # Start listening for messages
            asyncio.create_task(self.websocket_client.listen_for_messages())

            if self.game_status_label:
                self.game_status_label.set_text("🟢 Connected - Waiting for game...")
        else:
            if self.game_status_label:
                self.game_status_label.set_text("🔴 Connection failed")

    async def _handle_game_state(self, data: Dict[str, Any]):
        """Handle game state updates"""
        game_data = data.get("game", {})
        self.game_state = game_data
        self.players = game_data.get("players", {})
        self.community_cards = game_data.get("community_cards", [])
        self.current_player = game_data.get("current_player")
        self.game_phase = game_data.get("phase", "waiting")
        self.pot = game_data.get("pot", 0)

        await self._refresh_ui()

    async def _refresh_ui(self):
        """Refresh all UI elements with current game state"""
        if not ui:
            return

        # Update pot
        if self.pot_label:
            self.pot_label.set_text(f"💰 Pot: ${self.pot}")

        # Update community cards
        if self.community_cards_div:
            with self.community_cards_div:
                ui.clear()
                CardRenderer.render_community_cards(self.community_cards)

        # Update players
        if self.players_div:
            with self.players_div:
                ui.clear()
                PlayerRenderer.render_players_grid(self.players, self.current_player)

        # Update action buttons
        if self.action_buttons_div:
            with self.action_buttons_div:
                ui.clear()
                if self.current_player == self.player_id:
                    available_actions = self.game_state.get("available_actions", [])
                    call_amount = self.game_state.get("call_amount", 0)
                    ActionButtons.render_action_buttons(
                        available_actions, call_amount, self._make_action
                    )

    async def _make_action(self, action: str, amount: int = 0):
        """Send player action to server"""
        if not self.websocket_client.connected:
            return

        await self.websocket_client.send_message(
            {
                "type": "player_action",
                "game_id": self.current_game_id,
                "player_id": self.player_id,
                "action": action,
                "amount": amount,
            }
        )

    async def _handle_player_action(self, data: Dict[str, Any]):
        """Handle player action updates"""
        if not ui:
            return

        player_name = data.get("player_name", "Unknown")
        action = data.get("action", "unknown")
        amount = data.get("amount", 0)

        # Add to chat log
        if self.chat_log_div:
            with self.chat_log_div:
                action_text = f"{player_name} {action}"
                if amount > 0:
                    action_text += f" ${amount}"
                ui.label(f"🎮 {action_text}").classes("text-sm")

    async def _handle_agent_voice(self, data: Dict[str, Any]):
        """Handle agent voice messages"""
        if not ui:
            return

        agent_name = data.get("agent_name", "Unknown")
        message = data.get("message", "")
        voice_url = data.get("voice_url")

        # Add to chat log
        if self.chat_log_div:
            with self.chat_log_div:
                ui.label(f"🤖 {agent_name}: {message}").classes(
                    "text-sm text-purple-600"
                )

                # Play voice if available
                if voice_url:
                    ui.audio(voice_url, autoplay=True)

    async def _handle_phase_change(self, data: Dict[str, Any]):
        """Handle game phase changes"""
        phase = data.get("phase", "unknown")
        if self.game_status_label:
            self.game_status_label.set_text(f"🎯 {phase.upper()}")

    async def create_game(self, agent_id: str):
        """Create a new game with selected agent"""
        try:
            # This would call your API to create a game
            # For now, we'll simulate it
            self.current_game_id = "demo_game_1"
            self.player_id = "human_player_1"
            self.selected_agent = agent_id

            # Connect to WebSocket
            await self.connect_to_game(self.current_game_id, self.player_id)

        except Exception as e:
            print(f"Failed to create game: {e}")

    async def disconnect(self):
        """Disconnect from WebSocket"""
        await self.websocket_client.disconnect()
