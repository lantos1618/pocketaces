"""
WebSocket client for real-time game communication
"""

import asyncio
import json
import websockets
from typing import Dict, Any, Optional, Callable


class WebSocketClient:
    """Handles WebSocket connections and message routing"""

    def __init__(self):
        self.websocket: Optional[Any] = None
        self.connected: bool = False
        self.message_handlers: Dict[str, Callable] = {}

    async def connect(self, uri: str) -> bool:
        """Connect to WebSocket server"""
        try:
            self.websocket = await websockets.connect(uri)
            self.connected = True
            return True
        except Exception as e:
            print(f"WebSocket connection failed: {e}")
            self.connected = False
            return False

    async def send_message(self, message: Dict[str, Any]) -> bool:
        """Send a message to the server"""
        if not self.connected or not self.websocket:
            return False

        try:
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            print(f"Failed to send message: {e}")
            self.connected = False
            return False

    async def listen_for_messages(self):
        """Listen for incoming messages and route them to handlers"""
        if not self.websocket:
            return

        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self._route_message(data)
        except Exception as e:
            print(f"WebSocket error: {e}")
            self.connected = False

    async def _route_message(self, data: Dict[str, Any]):
        """Route incoming messages to appropriate handlers"""
        message_type = data.get("type")
        if message_type and isinstance(message_type, str):
            handler = self.message_handlers.get(message_type)
            if handler:
                await handler(data)
            else:
                print(f"No handler for message type: {message_type}")

    def register_handler(self, message_type: str, handler: Callable):
        """Register a message handler"""
        self.message_handlers[message_type] = handler

    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
        self.connected = False
