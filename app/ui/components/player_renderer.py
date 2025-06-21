"""
Player rendering component for poker UI
"""

from typing import Dict, Any, Optional

try:
    from nicegui import ui
except ImportError:
    ui = None

from .card_renderer import CardRenderer


class PlayerRenderer:
    """Handles rendering of player information and cards"""

    @staticmethod
    def render_player(
        player_id: str, player_data: Dict[str, Any], is_current: bool = False
    ) -> Optional[Any]:
        """Render a player's information and cards"""
        if not ui:
            return None

        name = player_data.get("name", "Unknown")
        chips = player_data.get("chips", 0)
        current_bet = player_data.get("current_bet", 0)
        cards = player_data.get("cards", [])
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
                        CardRenderer.render_card(card, "player")
                else:
                    CardRenderer.render_hidden_cards()

    @staticmethod
    def render_players_grid(
        players: Dict[str, Any], current_player: Optional[str] = None
    ) -> Optional[Any]:
        """Render all players in a grid layout"""
        if not ui:
            return None

        with ui.grid(columns=3).classes("gap-4"):
            for player_id, player_data in players.items():
                is_current = player_id == current_player
                PlayerRenderer.render_player(player_id, player_data, is_current)
