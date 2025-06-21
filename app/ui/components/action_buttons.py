from typing import Any, Callable, Dict, List, Optional
from nicegui import ui
from datetime import datetime

# This is a placeholder for the actual ui object until it's imported in a live environment
# This helps with type hinting and avoiding linter errors.
if not ui:
    ui: Any = None


def action_buttons(state: Dict[str, Any]) -> None:
    """Render action buttons based on game state."""
    if not ui:
        return
    with ui.row().classes("justify-center items-center mt-4"):
        ui.button("Fold", on_click=lambda: handle_action("fold", state), color="red")
        ui.button(
            "Check/Call", on_click=lambda: handle_action("check", state), color="blue"
        )
        with ui.row().classes("items-center"):
            ui.button(
                "Raise", on_click=lambda: handle_action("raise", state), color="green"
            )
            ui.number("Amount", value=100, step=10, format="%d").bind_value(
                state, "raise_amount"
            )


def handle_action(action_type: str, state: Dict[str, Any]) -> None:
    """Handle player action."""
    # This would typically call a backend service
    print(f"Action: {action_type}, Amount: {state.get('raise_amount')}")


def agent_selection(agents: List[Dict[str, Any]], on_select: Callable) -> None:
    """Render agent selection interface."""
    if not ui:
        return

    with ui.column().classes("w-full p-4 agent-selection items-center gap-4"):
        ui.label("Choose Your Opponents").classes("text-2xl font-bold text-white mb-4")
        with ui.row().classes("justify-center gap-4"):
            for agent in agents:
                with ui.card().classes(
                    "w-64 bg-gray-800 text-white cursor-pointer hover:bg-gray-700"
                ):
                    with ui.card_section():
                        ui.label(agent["name"]).classes("text-lg font-bold")
                        ui.label(agent["description"]).classes("text-sm text-gray-300")
                    with ui.card_actions():
                        ui.button("Select", on_click=lambda a=agent: on_select(a))


def player_controls(state: Dict[str, Any], on_start: Callable) -> None:
    """Render player controls."""
    if not ui:
        return
    with ui.row().classes("my-4 justify-center items-center gap-4"):
        ui.input("Your Name").bind_value(state, "player_name")
        ui.button("Start Game", on_click=on_start)


def game_log(state: Dict[str, Any]) -> None:
    """Render the game log."""
    if not ui:
        return

    # Update log messages
    if state.get("new_log_message"):
        state.setdefault("log_messages", []).append(
            f"[{datetime.now().strftime('%H:%M:%S')}] {state.pop('new_log_message')}"
        )

    with ui.column().classes(
        "w-full p-2 bg-gray-800 text-white rounded-lg h-32 overflow-y-auto"
    ):
        for msg in state.get("log_messages", []):
            ui.label(msg).classes("text-sm font-mono")
