#!/usr/bin/env python3
"""
Pocket Aces - AI Poker Game Server
Main entry point for the FastAPI application
"""

import os
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any, List
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
from fastapi.responses import RedirectResponse

# Import routers
from app.api.routes import rooms, games, agents, websockets

# Import core services
from app.store.game_store import game_store
from app.core.agents.agent_manager import agent_manager
from app.core.game.poker_engine import poker_engine

# Import frontend
try:
    from app.ui.frontend import create_poker_ui

    FRONTEND_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Frontend not available: {e}")
    FRONTEND_AVAILABLE = False

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
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

    # Game Settings
    DEFAULT_STARTING_CHIPS = int(os.getenv("DEFAULT_STARTING_CHIPS", "1000"))
    DEFAULT_SMALL_BLIND = int(os.getenv("DEFAULT_SMALL_BLIND", "10"))
    DEFAULT_BIG_BLIND = int(os.getenv("DEFAULT_BIG_BLIND", "20"))
    MAX_PLAYERS_PER_ROOM = int(os.getenv("MAX_PLAYERS_PER_ROOM", "3"))
    GAME_TIMEOUT_SECONDS = int(os.getenv("GAME_TIMEOUT_SECONDS", "30"))

    # CORS
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:8080"
    ).split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting Pocket Aces Server...")

    # Initialize agent manager with Mistral
    if Config.MISTRAL_API_KEY:
        try:
            await agent_manager.initialize_llm(Config.MISTRAL_API_KEY)
            print("✅ LangChain initialized with Mistral")
        except Exception as e:
            print(f"⚠️  Failed to initialize Mistral: {e}")
            print("🤖 Agents will use rule-based decision making")
    else:
        print("⚠️  No Mistral API key provided - using rule-based agents")

    # Create default rooms
    await _create_default_rooms()

    print(f"🎮 Server ready on http://{Config.HOST}:{Config.PORT}")
    print("📚 API docs available at /docs")
    if FRONTEND_AVAILABLE:
        print("🎨 Frontend available at /")

    yield

    # Shutdown
    print("🛑 Shutting down Pocket Aces Server...")


async def _create_default_rooms() -> None:
    """Create default game rooms"""
    default_rooms: List[Dict[str, Any]] = [
        {
            "name": "Demo Table",
            "max_players": 3,
            "settings": {"small_blind": 5, "big_blind": 10, "starting_chips": 500},
        },
        {
            "name": "High Stakes",
            "max_players": 3,
            "settings": {"small_blind": 25, "big_blind": 50, "starting_chips": 2000},
        },
    ]

    for room_config in default_rooms:
        await game_store.create_room(
            name=str(room_config["name"]),
            max_players=int(room_config["max_players"]),
            settings=room_config["settings"],
        )


# Create FastAPI app
app = FastAPI(
    title="Pocket Aces Poker",
    description="Real-time poker game with AI agents",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(rooms.router)
app.include_router(games.router)
app.include_router(agents.router)
app.include_router(websockets.router)


# Health check (must be before frontend to avoid NiceGUI interception)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Redirect root to UI
@app.get("/")
async def root():
    return RedirectResponse(url="/ui")


# Initialize frontend if available
if FRONTEND_AVAILABLE:
    create_poker_ui(app)
    print("✅ Frontend initialized")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level=Config.LOG_LEVEL,
    )
