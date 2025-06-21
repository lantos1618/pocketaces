"""
Pocket Aces - Modern Poker UI with AI Agents
Built with NiceGUI for seamless real-time updates
"""

import asyncio
import json
import websockets
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from fastapi import FastAPI

try:
    from nicegui import ui
except ImportError:
    print("NiceGUI not installed. Please run: pip install nicegui")
    ui = None
    FastAPI = None

from .components.game_ui import GameUI
from .styles.poker_styles import POKER_STYLES


# UI State Management
class GameUI:
    def __init__(self):
        self.game_state: Dict[str, Any] = {}
        self.players: Dict[str, Any] = {}
        self.community_cards: List[Dict[str, str]] = []
        self.current_player: Optional[str] = None
        self.game_phase: str = "waiting"
        self.pot: int = 0
        self.websocket: Optional[Any] = None  # websockets.WebSocketClientProtocol
        self.connected: bool = False

        # UI Elements
        self.game_status_label: Optional[Any] = None
        self.community_cards_div: Optional[Any] = None
        self.players_div: Optional[Any] = None
        self.action_buttons_div: Optional[Any] = None
        self.agent_selection_div: Optional[Any] = None
        self.chat_log_div: Optional[Any] = None
        self.pot_label: Optional[Any] = None
        self.game_area: Optional[Any] = None

        # Game state
        self.current_game_id: Optional[str] = None
        self.player_id: Optional[str] = None
        self.selected_agent: Optional[str] = None

    async def connect_websocket(self, game_id: str, player_id: str):
        """Connect to the game WebSocket for real-time updates"""
        try:
            uri = f"ws://localhost:8000/ws/{player_id}"
            self.websocket = await websockets.connect(uri)
            self.connected = True

            # Subscribe to game updates
            if self.websocket:
                await self.websocket.send(
                    json.dumps({"type": "subscribe_game", "game_id": game_id})
                )

            # Start listening for messages
            asyncio.create_task(self._listen_for_messages())

            if self.game_status_label:
                self.game_status_label.set_text("🟢 Connected - Waiting for game...")

        except Exception as e:
            if self.game_status_label:
                self.game_status_label.set_text(f"🔴 Connection failed: {str(e)}")
            self.connected = False

    async def _listen_for_messages(self):
        """Listen for WebSocket messages and update UI"""
        if not self.websocket:
            return

        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self._handle_message(data)
        except Exception as e:
            print(f"WebSocket error: {e}")
            self.connected = False
            if self.game_status_label:
                self.game_status_label.set_text("🔴 Connection lost")

    async def _handle_message(self, data: Dict[str, Any]):
        """Handle incoming WebSocket messages"""
        message_type = data.get("type")

        if message_type == "game_state":
            await self._update_game_state(data["game"])
        elif message_type == "player_action":
            await self._handle_player_action(data)
        elif message_type == "agent_voice":
            await self._handle_agent_voice(data)
        elif message_type == "game_phase":
            await self._handle_phase_change(data)

    async def _update_game_state(self, game_data: Dict[str, Any]):
        """Update the UI with new game state"""
        self.game_state = game_data
        self.players = game_data.get("players", {})
        self.community_cards = game_data.get("community_cards", [])
        self.current_player = game_data.get("current_player")
        self.game_phase = game_data.get("phase", "waiting")
        self.pot = game_data.get("pot", 0)

        # Update UI elements
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
                if self.community_cards:
                    for card in self.community_cards:
                        self._render_card(card, "community")
                else:
                    ui.label("Waiting for cards...").classes("text-gray-500")

        # Update players
        if self.players_div:
            with self.players_div:
                ui.clear()
                for player_id, player_data in self.players.items():
                    self._render_player(player_id, player_data)

        # Update action buttons
        if self.action_buttons_div:
            with self.action_buttons_div:
                ui.clear()
                if self.current_player == self.player_id:
                    self._render_action_buttons()

    def _render_card(self, card: Dict[str, str], card_type: str = "player"):
        """Render a playing card with animations"""
        if not ui:
            return

        rank = card.get("rank", "?")
        suit = card.get("suit", "?")
        suit_symbol = {"hearts": "♥", "diamonds": "♦", "clubs": "♣", "spades": "♠"}.get(
            suit, "?"
        )
        color = "text-red-600" if suit in ["hearts", "diamonds"] else "text-gray-800"

        with ui.card().classes(f"card {card_type}-card animate-deal"):
            ui.label(f"{rank}{suit_symbol}").classes(f"text-2xl font-bold {color}")

    def _render_player(self, player_id: str, player_data: Dict[str, Any]):
        """Render a player's information and cards"""
        if not ui:
            return

        name = player_data.get("name", "Unknown")
        chips = player_data.get("chips", 0)
        current_bet = player_data.get("current_bet", 0)
        cards = player_data.get("cards", [])
        is_current = player_id == self.current_player
        is_folded = player_data.get("folded", False)

        # Player card styling
        card_classes = "player-card"
        if is_current:
            card_classes += " current-player"
        if is_folded:
            card_classes += " folded"

        with ui.card().classes(card_classes):
            ui.label(name).classes("text-lg font-bold")
            ui.label(f"Chips: ${chips}").classes("text-sm")
            if current_bet > 0:
                ui.label(f"Bet: ${current_bet}").classes("text-sm text-blue-600")

            # Render player's cards
            with ui.row().classes("gap-1"):
                if cards:
                    for card in cards:
                        self._render_card(card, "player")
                else:
                    ui.label("🂠 🂠").classes("text-2xl")

    def _render_action_buttons(self):
        """Render action buttons for current player"""
        if not ui:
            return

        available_actions = self.game_state.get("available_actions", [])

        with ui.row().classes("gap-2"):
            if "fold" in available_actions:
                ui.button("Fold", on_click=lambda: self._make_action("fold")).classes(
                    "bg-red-500 hover:bg-red-600"
                )

            if "call" in available_actions:
                call_amount = self.game_state.get("call_amount", 0)
                ui.button(
                    f"Call ${call_amount}", on_click=lambda: self._make_action("call")
                ).classes("bg-blue-500 hover:bg-blue-600")

            if "raise" in available_actions:
                ui.button("Raise", on_click=self._show_raise_dialog).classes(
                    "bg-green-500 hover:bg-green-600"
                )

    async def _make_action(self, action: str, amount: int = 0):
        """Send player action to server"""
        if not self.connected or not self.websocket:
            return

        try:
            await self.websocket.send(
                json.dumps(
                    {
                        "type": "player_action",
                        "game_id": self.current_game_id,
                        "player_id": self.player_id,
                        "action": action,
                        "amount": amount,
                    }
                )
            )
        except Exception as e:
            print(f"Failed to send action: {e}")

    def _show_raise_dialog(self):
        """Show raise amount input dialog"""
        if not ui:
            return

        with ui.dialog() as dialog, ui.card():
            ui.label("Enter raise amount:").classes("text-lg")
            amount_input = ui.number("Amount", min=1, max=1000)

            with ui.row().classes("gap-2"):
                ui.button(
                    "Raise",
                    on_click=lambda: self._handle_raise(dialog, amount_input.value),
                )
                ui.button("Cancel", on_click=dialog.close).classes("bg-gray-500")

    async def _handle_raise(self, dialog, amount: int):
        """Handle raise action"""
        if dialog:
            dialog.close()
        await self._make_action("raise", amount)

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
            await self.connect_websocket(self.current_game_id, self.player_id)

        except Exception as e:
            print(f"Failed to create game: {e}")


# Global UI instance
game_ui = GameUI()


def create_poker_ui(fastapi_app: FastAPI):
    """Create the main poker UI using modular components"""
    if not ui or not fastapi_app:
        print("NiceGUI or FastAPI not available")
        return

    # Add custom CSS styles
    ui.add_head_html(POKER_STYLES)

    @ui.page("/")
    def main_page():
        """Main poker game page"""

        # Header
        with ui.header().classes("bg-gray-900 text-white"):
            ui.label("🃏 Pocket Aces - AI Poker").classes("text-2xl font-bold")
            game_ui.game_status_label = ui.label(
                "Welcome! Select an agent to start"
            ).classes("text-lg")

        # Main content
        with ui.column().classes("w-full p-4 gap-4"):
            # Agent Selection (shown initially)
            game_ui.agent_selection_div = ui.column().classes(
                "agent-selection text-white"
            )
            with game_ui.agent_selection_div:
                ui.label("🤖 Choose Your AI Opponent").classes("text-xl font-bold mb-4")

                agents = [
                    {
                        "id": "the_rock",
                        "name": "The Rock",
                        "description": "Conservative, calculated player",
                        "emoji": "🪨",
                    },
                    {
                        "id": "the_maniac",
                        "name": "The Maniac",
                        "description": "Aggressive, unpredictable",
                        "emoji": "😈",
                    },
                    {
                        "id": "the_shark",
                        "name": "The Shark",
                        "description": "Professional, analytical",
                        "emoji": "🦈",
                    },
                    {
                        "id": "the_fish",
                        "name": "The Fish",
                        "description": "Loose, calling station",
                        "emoji": "🐟",
                    },
                ]

                with ui.grid(columns=2).classes("gap-4"):
                    for agent in agents:
                        with ui.card().classes(
                            "agent-card cursor-pointer hover:bg-gray-700"
                        ):
                            ui.label(f"{agent['emoji']} {agent['name']}").classes(
                                "text-lg font-bold"
                            )
                            ui.label(agent["description"]).classes(
                                "text-sm text-gray-300"
                            )
                            ui.button(
                                "Select", on_click=lambda a=agent: select_agent(a)
                            ).classes("mt-2 bg-blue-600 hover:bg-blue-700")

            # Game Area (hidden initially)
            game_ui.game_area = ui.column().classes("w-full hidden")

            with game_ui.game_area:
                # Pot display
                game_ui.pot_label = ui.label("💰 Pot: $0").classes(
                    "text-xl font-bold text-center"
                )

                # Poker table
                with ui.card().classes("poker-table w-full"):
                    # Community cards
                    ui.label("Community Cards").classes(
                        "text-white text-lg font-bold mb-2"
                    )
                    game_ui.community_cards_div = ui.row().classes(
                        "justify-center gap-2"
                    )

                    # Players area
                    ui.label("Players").classes(
                        "text-white text-lg font-bold mt-4 mb-2"
                    )
                    game_ui.players_div = ui.grid(columns=3).classes("gap-4")

                # Action buttons
                game_ui.action_buttons_div = ui.row().classes("justify-center mt-4")

                # Chat log
                ui.label("Game Log").classes("text-lg font-bold mt-4")
                game_ui.chat_log_div = ui.column().classes(
                    "bg-gray-100 p-4 rounded-lg max-h-40 overflow-y-auto"
                )

    def select_agent(agent: Dict[str, str]):
        """Handle agent selection and start game"""
        # Hide agent selection
        if game_ui.agent_selection_div:
            game_ui.agent_selection_div.classes("hidden")

        # Show game area
        if game_ui.game_area:
            game_ui.game_area.classes("")

        # Create game
        asyncio.create_task(game_ui.create_game(agent["id"]))

        # Update status
        if game_ui.game_status_label:
            game_ui.game_status_label.set_text(f"🎮 Playing against {agent['name']}")

    # Mount NiceGUI to FastAPI
    ui.run_with(fastapi_app, storage_secret="pocket_aces_secret_key_2024")


# Export the function for use in main.py
__all__ = ["create_poker_ui"]
