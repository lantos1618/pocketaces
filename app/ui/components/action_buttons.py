"""
Action buttons component for poker UI
"""

from typing import Dict, Any, Optional, Callable

try:
    from nicegui import ui
except ImportError:
    ui = None


class ActionButtons:
    """Handles rendering of player action buttons"""

    @staticmethod
    def render_action_buttons(
        available_actions: list,
        call_amount: int = 0,
        on_action: Optional[Callable] = None,
    ) -> Optional[Any]:
        """Render action buttons for current player"""
        if not ui:
            return None

        with ui.row().classes("gap-2"):
            if "fold" in available_actions:
                ui.button(
                    "Fold",
                    on_click=lambda: ActionButtons._handle_action("fold", 0, on_action),
                ).classes("bg-red-500 hover:bg-red-600")

            if "call" in available_actions:
                ui.button(
                    f"Call ${call_amount}",
                    on_click=lambda: ActionButtons._handle_action(
                        "call", call_amount, on_action
                    ),
                ).classes("bg-blue-500 hover:bg-blue-600")

            if "raise" in available_actions:
                ui.button(
                    "Raise",
                    on_click=lambda: ActionButtons._show_raise_dialog(on_action),
                ).classes("bg-green-500 hover:bg-green-600")

    @staticmethod
    def _handle_action(action: str, amount: int, on_action: Optional[Callable]):
        """Handle action button clicks"""
        if on_action:
            on_action(action, amount)

    @staticmethod
    def _show_raise_dialog(on_action: Optional[Callable]):
        """Show raise amount input dialog"""
        if not ui:
            return

        with ui.dialog() as dialog, ui.card():
            ui.label("Enter raise amount:").classes("text-lg")
            amount_input = ui.number("Amount", min=1, max=1000)

            with ui.row().classes("gap-2"):
                ui.button(
                    "Raise",
                    on_click=lambda: ActionButtons._handle_raise(
                        dialog, amount_input.value, on_action
                    ),
                )
                ui.button("Cancel", on_click=dialog.close).classes("bg-gray-500")

    @staticmethod
    def _handle_raise(dialog, amount: int, on_action: Optional[Callable]):
        """Handle raise action"""
        if dialog:
            dialog.close()
        if on_action:
            on_action("raise", amount)
