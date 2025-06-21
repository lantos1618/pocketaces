"""
Card rendering component for poker UI
"""

from typing import Dict, Optional, Any

try:
    from nicegui import ui
except ImportError:
    ui = None


class CardRenderer:
    """Handles rendering of playing cards with animations"""

    SUIT_SYMBOLS = {"hearts": "♥", "diamonds": "♦", "clubs": "♣", "spades": "♠"}

    SUIT_COLORS = {
        "hearts": "text-red-600",
        "diamonds": "text-red-600",
        "clubs": "text-gray-800",
        "spades": "text-gray-800",
    }

    @staticmethod
    def render_card(card: Dict[str, str], card_type: str = "player") -> Optional[Any]:
        """Render a playing card with animations"""
        if not ui:
            return None

        rank = card.get("rank", "?")
        suit = card.get("suit", "?")
        suit_symbol = CardRenderer.SUIT_SYMBOLS.get(suit, "?")
        color = CardRenderer.SUIT_COLORS.get(suit, "text-gray-800")

        with ui.card().classes(f"card {card_type}-card animate-deal"):
            ui.label(f"{rank}{suit_symbol}").classes(f"text-2xl font-bold {color}")

    @staticmethod
    def render_hidden_cards() -> Optional[Any]:
        """Render face-down cards"""
        if not ui:
            return None

        with ui.row().classes("gap-1"):
            ui.label("🂠 🂠").classes("text-2xl")

    @staticmethod
    def render_community_cards(cards: list) -> Optional[Any]:
        """Render community cards on the table"""
        if not ui:
            return None

        with ui.row().classes("justify-center gap-2"):
            if cards:
                for card in cards:
                    CardRenderer.render_card(card, "community")
            else:
                ui.label("Waiting for cards...").classes("text-gray-500")
