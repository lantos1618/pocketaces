import httpx
import asyncio

try:
    from nicegui import ui
except ImportError:
    ui = None


class Lobby:
    def build(self):
        if not ui:
            return
        with ui.column().classes("w-full items-center"):
            ui.label("Poker Lobby").classes("text-2xl font-bold")
            with ui.row():
                ui.button("Refresh", on_click=self.refresh_rooms)
                ui.button("Create Room", on_click=self.show_create_room_dialog)
            self.room_list = ui.column()
            ui.timer(0.1, self.refresh_rooms, once=True)

    async def refresh_rooms(self):
        if not ui or not self.room_list:
            return
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/api/rooms/")
                response.raise_for_status()
                rooms = response.json()

            self.room_list.clear()
            with self.room_list:
                if not rooms:
                    ui.label("No rooms available. Create one!")
                else:
                    for room in rooms:
                        with ui.card():
                            ui.label(room.get("name", "Unnamed Room"))
        except Exception as e:
            self.room_list.clear()
            with self.room_list:
                ui.label(f"Could not fetch rooms: {e}")

    def show_create_room_dialog(self):
        if not ui:
            return
        with ui.dialog() as dialog, ui.card():
            ui.label("Create New Room").classes("text-xl font-bold")
            room_name = ui.input("Room Name", value="Poker Night")
            max_players = ui.number("Max Players", value=3, min=2, max=8)

            def handle_create():
                if not room_name.value:
                    if ui:
                        ui.notify("Room name is required.", color="negative")
                    return
                dialog.close()
                asyncio.create_task(
                    self.create_room(room_name.value, max_players.value)
                )

            with ui.row():
                ui.button("Create", on_click=handle_create)
                ui.button("Cancel", on_click=dialog.close)

    async def create_room(self, name: str, max_players: int):
        if not ui:
            return
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(
                    "http://localhost:8000/api/rooms/",
                    params={"name": name, "max_players": max_players},
                )
                res.raise_for_status()
                room = res.json()
                ui.notify(f"Room '{name}' created!", color="positive")
            await self.refresh_rooms()
        except Exception as e:
            ui.notify(f"Error creating room: {e}", color="negative")
