#!/usr/bin/env python3
"""
Pocket Aces - AI Poker Game Server
Main entry point for the FastAPI application
"""

import os
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any, List, AsyncGenerator
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles

# Import routers
from app.api.routes import rooms, games, agents, websockets

# Import core services
from app.store.game_store import game_store
from app.core.agents.agent_manager import agent_manager
from app.core.game.poker_engine import poker_engine


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
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
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
    print(f"🎨 Frontend available at http://{Config.HOST}:{Config.PORT}")

    yield

    # Shutdown
    print("🛑 Stopping Pocket Aces Server...")
    # You can add cleanup code here if needed, like closing database connections


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


# FastAPI App Initialization
app = FastAPI(
    title="Pocket Aces Poker API",
    description="A modern, real-time poker platform with AI agents.",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)

# CORS Middleware
# This allows the frontend (running on a different port/domain) to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


# API Routers
# Include all the different API route modules
app.include_router(games.router)
app.include_router(rooms.router)
app.include_router(agents.router)
app.include_router(websockets.router)


# Static Files
# Serve static files (like CSS, JS, images) from the 'static' directory
app.mount("/static", StaticFiles(directory="static"), name="static")


# Health check
@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level=Config.LOG_LEVEL,
    )
