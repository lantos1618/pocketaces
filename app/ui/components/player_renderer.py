from typing import Any, Dict, List
from nicegui import ui
from .card_renderer import player_cards_view  # Import necessary component

ui = None


def player_view(
    player: Dict[str, Any], is_current: bool = False, is_human: bool = False
) -> None:
    """Render a player's information and cards."""
    if not ui:
        return

    base_classes = "p-4 rounded-lg shadow-lg w-48 min-h-48 flex flex-col justify-between items-center transition-all duration-300"
    state_classes = ""
    if is_current:
        state_classes += " border-4 border-blue-400"
    if player.get("status") == "folded":
        state_classes += " opacity-50 grayscale"

    with ui.card().classes(f"{base_classes} {state_classes}"):
        with ui.column().classes("items-center"):
            ui.label(player["name"]).classes("text-lg font-bold")
            if player.get("current_bet", 0) > 0:
                ui.chip(
                    f"Bet: {player['current_bet']}",
                    color="secondary",
                    text_color="white",
                    icon="monetization_on",
                ).classes("mt-1")

        # Render cards
        hole_cards = player.get("hole_cards", [])
        player_cards_view(
            hole_cards, is_hidden=not is_human and not player.get("showdown", False)
        )

        with ui.column().classes("items-center text-center"):
            ui.label(f"${player['chips']}").classes("text-xl font-semibold")
            if player.get("last_action"):
                action = player["last_action"]
                action_text = action["action_type"].title()
                if action.get("amount"):
                    action_text += f" {action['amount']}"
                ui.label(action_text).classes("text-xs italic text-gray-400")


def poker_table_layout(players: list, current_player_id: str) -> None:
    """Lay out players around a central poker table."""
    if not ui:
        return

    # This is a simplified layout. A real implementation might use absolute positioning.
    with ui.column().classes(
        "w-full items-center p-8 bg-green-800 rounded-full border-8 border-yellow-700 shadow-2xl gap-8"
    ):
        # Top player (opponent)
        if len(players) >= 2:
            player_view(
                players[1], is_current=players[1].get("id") == current_player_id
            )

        # Middle row for community cards
        # This part should be handled by the main game UI logic to pass community cards

        # Bottom player (human)
        if len(players) >= 1:
            player_view(
                players[0],
                is_current=players[0].get("id") == current_player_id,
                is_human=True,
            )
