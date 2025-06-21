from typing import Any, Dict, List
from nicegui import ui


def get_suit_char(suit: str) -> str:
    return (
        "♠"
        if suit == "spades"
        else "♥"
        if suit == "hearts"
        else "♦"
        if suit == "diamonds"
        else "♣"
    )


def card_view(card: Dict[str, str], is_hidden: bool = False) -> None:
    """Render a single card."""
    if not ui:
        return
    with ui.card().classes(
        "p-2 w-16 h-24 bg-white rounded-lg flex justify-center items-center relative shadow-md"
    ):
        card_content = ui.column().classes(
            "w-full h-full justify-between items-center relative"
        )
        with card_content:
            if is_hidden:
                ui.label("?").classes("text-4xl")
            else:
                suit_char = get_suit_char(card["suit"])
                color_class = (
                    "text-red-500"
                    if card["suit"] in ["hearts", "diamonds"]
                    else "text-black"
                )

                with ui.row().classes("w-full justify-between items-start"):
                    ui.label(card["rank"]).classes(f"text-xl {color_class}")
                    ui.label(suit_char).classes(f"text-lg {color_class}")
                ui.label(suit_char).classes(f"text-4xl {color_class} absolute-center")
                with ui.row().classes("w-full justify-between items-end"):
                    ui.label(suit_char).classes(f"text-lg {color_class} rotate-180")
                    ui.label(card["rank"]).classes(f"text-xl {color_class} rotate-180")


def community_cards_view(cards: List[Dict[str, str]]) -> None:
    """Render the community cards on the table."""
    if not ui:
        return
    with ui.row().classes("justify-center items-center gap-2"):
        ui.label("Community:").classes("text-lg font-bold text-white")
        for card in cards:
            card_view(card)


def player_cards_view(cards: List[Dict[str, str]], is_hidden: bool = False) -> None:
    """Render a player's hole cards."""
    if not ui:
        return
    with ui.row().classes("gap-1"):
        for card in cards:
            card_view(card, is_hidden=is_hidden)
