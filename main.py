#!/usr/bin/env python3
"""
Pocket Aces - AI Poker Game Server
Main entry point for the FastAPI application
"""

import os
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

from app.store.game_store import game_store
from app.core.agents.agent_manager import agent_manager
from app.core.game.poker_engine import poker_engine
from app.models.game_models import Player, PlayerAction, ActionType
from app.models.agent_models import AgentPersonality

# Load environment variables
load_dotenv()

# Configuration
class Config:
    """Application configuration"""
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
    
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    
    # Game Settings
    DEFAULT_STARTING_CHIPS = int(os.getenv("DEFAULT_STARTING_CHIPS", "1000"))
    DEFAULT_SMALL_BLIND = int(os.getenv("DEFAULT_SMALL_BLIND", "10"))
    DEFAULT_BIG_BLIND = int(os.getenv("DEFAULT_BIG_BLIND", "20"))
    MAX_PLAYERS_PER_ROOM = int(os.getenv("MAX_PLAYERS_PER_ROOM", "3"))
    GAME_TIMEOUT_SECONDS = int(os.getenv("GAME_TIMEOUT_SECONDS", "30"))
    
    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting Pocket Aces Server...")
    
    # Initialize agent manager with OpenAI
    if Config.OPENAI_API_KEY:
        try:
            await agent_manager.initialize_llm(Config.OPENAI_API_KEY)
            print("✅ LangChain initialized with OpenAI")
        except Exception as e:
            print(f"⚠️  Failed to initialize OpenAI: {e}")
            print("🤖 Agents will use rule-based decision making")
    else:
        print("⚠️  No OpenAI API key provided - using rule-based agents")
    
    # Create default rooms
    _create_default_rooms()
    
    print(f"🎮 Server ready on http://{Config.HOST}:{Config.PORT}")
    print("📚 API docs available at /docs")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Pocket Aces Server...")

def _create_default_rooms():
    """Create default game rooms"""
    default_rooms = [
        {
            "name": "Demo Table",
            "max_players": 3,
            "settings": {
                "small_blind": 5,
                "big_blind": 10,
                "starting_chips": 500
            }
        },
        {
            "name": "High Stakes",
            "max_players": 3,
            "settings": {
                "small_blind": 25,
                "big_blind": 50,
                "starting_chips": 2000
            }
        }
    ]
    
    for room_config in default_rooms:
        game_store.create_room(**room_config)

# Create FastAPI app
app = FastAPI(
    title="Pocket Aces Poker",
    description="Real-time poker game with AI agents",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

manager = ConnectionManager()

# Initialize components
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    # Initialize agent manager with OpenAI API key if available
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        await agent_manager.initialize_llm(openai_key)
    
    # Create some default rooms
    game_store.create_room("High Stakes Table", 3, {"small_blind": 10, "big_blind": 20})
    game_store.create_room("Demo Table", 3, {"small_blind": 5, "big_blind": 10})
    
    print("Pocket Aces server started successfully!")

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Room endpoints
@app.get("/api/rooms")
async def get_rooms():
    """Get all available rooms"""
    rooms = game_store.get_all_rooms()
    return [room.dict() for room in rooms]

@app.post("/api/rooms")
async def create_room(name: str, max_players: int = 3, settings: Dict[str, Any] = None):
    """Create a new room"""
    room = game_store.create_room(name, max_players, settings or {})
    return room.dict()

@app.get("/api/rooms/{room_id}")
async def get_room(room_id: str):
    """Get room details"""
    room = game_store.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room.dict()

# Game endpoints
@app.post("/api/rooms/{room_id}/start-game")
async def start_game(room_id: str):
    """Start a new game in a room"""
    game = poker_engine.start_new_game(room_id)
    if not game:
        raise HTTPException(status_code=400, detail="Cannot start game")
    return game.dict()

@app.get("/api/games/{game_id}")
async def get_game(game_id: str):
    """Get game state"""
    game = game_store.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game.dict()

# Player endpoints
@app.post("/api/rooms/{room_id}/join")
async def join_room(room_id: str, player_name: str):
    """Join a room as a player"""
    player = Player(
        id=f"player_{datetime.now().timestamp()}",
        name=player_name,
        chips=1000,
        position=0,
        is_human=True,
        is_agent=False
    )
    
    success = game_store.add_player_to_room(room_id, player)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot join room")
    
    return {"player_id": player.id, "message": "Joined room successfully"}

# Agent endpoints
@app.get("/api/agents")
async def get_agents():
    """Get all available AI agents"""
    agents = game_store.get_all_agents()
    return [agent.dict() for agent in agents]

@app.post("/api/rooms/{room_id}/add-agent")
async def add_agent_to_room(room_id: str, agent_id: str):
    """Add an AI agent to a room"""
    agent = game_store.get_agent_personality(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Create player from agent
    from app.models.mock_data import create_mock_player_from_agent
    player = create_mock_player_from_agent(agent)
    
    success = game_store.add_player_to_room(room_id, player)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot add agent to room")
    
    return {"message": f"Added {agent.name} to room"}

# WebSocket endpoint for real-time game updates
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message["type"] == "join_room":
                await handle_join_room(client_id, message)
            elif message["type"] == "make_action":
                await handle_make_action(client_id, message)
            elif message["type"] == "get_game_state":
                await handle_get_game_state(client_id, message)
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)

async def handle_join_room(client_id: str, message: Dict[str, Any]):
    """Handle room join request"""
    room_id = message.get("room_id")
    player_name = message.get("player_name", "Anonymous")
    
    try:
        result = await join_room(room_id, player_name)
        await manager.send_personal_message(
            json.dumps({"type": "room_joined", "data": result}),
            client_id
        )
    except Exception as e:
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": str(e)}),
            client_id
        )

async def handle_make_action(client_id: str, message: Dict[str, Any]):
    """Handle player action"""
    game_id = message.get("game_id")
    player_id = message.get("player_id")
    action_type = message.get("action_type")
    amount = message.get("amount")
    
    try:
        success = game_store.make_player_action(game_id, player_id, action_type, amount)
        if success:
            # Broadcast updated game state
            game = game_store.get_game(game_id)
            await manager.broadcast(json.dumps({
                "type": "game_updated",
                "data": game.dict()
            }))
        else:
            await manager.send_personal_message(
                json.dumps({"type": "error", "message": "Invalid action"}),
                client_id
            )
    except Exception as e:
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": str(e)}),
            client_id
        )

async def handle_get_game_state(client_id: str, message: Dict[str, Any]):
    """Handle game state request"""
    game_id = message.get("game_id")
    
    try:
        game = game_store.get_game(game_id)
        if game:
            await manager.send_personal_message(
                json.dumps({"type": "game_state", "data": game.dict()}),
                client_id
            )
        else:
            await manager.send_personal_message(
                json.dumps({"type": "error", "message": "Game not found"}),
                client_id
            )
    except Exception as e:
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": str(e)}),
            client_id
        )

if __name__ == "__main__":
    # Validate required environment variables
    if not Config.OPENAI_API_KEY:
        print("⚠️  Warning: OPENAI_API_KEY not set - agents will use rule-based logic")
    
    if not Config.ELEVENLABS_API_KEY:
        print("⚠️  Warning: ELEVENLABS_API_KEY not set - voice features will be disabled")
    
    # Start server
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level=Config.LOG_LEVEL,
        access_log=True
    ) 