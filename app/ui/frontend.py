from fastapi import FastAPI

try:
    from nicegui import ui
except ImportError:
    ui = None
from .components.lobby import Lobby


def create_poker_ui(app: FastAPI):
    if not ui:
        return

    @ui.page("/ui")
    def main_page():
        Lobby().build()

    ui.run_with(app, storage_secret="secret_key")


__all__ = ["create_poker_ui"]
