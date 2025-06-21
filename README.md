# 🃏 Pocket Aces - AI Poker Game

*AI Agents That Play, Talk, and Outsmart You in Poker*

## 🎯 Overview

Pocket Aces is a real-time poker game featuring intelligent AI opponents with unique personalities, voice interaction, and adaptive behavior. It brings together game strategy, bluff psychology, and expressive voice agents in a live, competitive format designed for demos, entertainment, and AI experimentation.

Players face off against agents who don't just play — they **trash talk, learn from you, and evolve.**

## 🚀 Quick Start

### Prerequisites

- **Python 3.12.3** (required - use [pyenv](https://github.com/pyenv/pyenv) to manage versions)
- OpenAI API key
- ElevenLabs API key (for voice synthesis)

### Installation

#### Option 1: Automated Setup (Recommended)
```bash
git clone <repository-url>
cd pocketaces
./setup.sh
```

#### Option 2: Manual Setup
1. **Install pyenv and Python 3.12.3**
   ```bash
   curl https://pyenv.run | bash
   pyenv install 3.12.3
   pyenv local 3.12.3
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run the server**
   ```bash
   python main.py
   ```

#### Option 3: Using Make
```bash
make setup    # Full setup
make run      # Start server
make dev      # Development mode with auto-reload
```

The server will start on `http://localhost:8000`

## 🛠️ Development Commands

```bash
make help     # Show all available commands
make setup    # Full project setup
make venv     # Create virtual environment only
make install  # Install dependencies
make run      # Start the server
make dev      # Development mode with auto-reload
make test     # Run tests
make clean    # Clean up generated files
```

## 🧩 Core Features

### ♠️ Live Poker Gameplay
- Texas Hold'em–style multiplayer matches
- 3-player games: 1 human vs. 2 AI agents
- Real-time, turn-by-turn gameplay
- Full hand progression: pre-flop, flop, turn, river, showdown

### 🧠 Agent Personalities
Each AI agent has a defined profile affecting behavior and speech:
- **Max 'The Gritty Bluffer'** - Aggressive, loves to bluff and trash talk
- **Claire 'The Conservative Shark'** - Patient, calculating, waits for perfect moments
- **Rex 'The Maniac'** - Wild, unpredictable, plays every hand
- **Sophie 'The Calling Station'** - Calls everything, relies on luck
- **Victor 'The Rock'** - Tight, conservative, only plays premium hands

### 🎙️ Voice-Enabled AI
- Real-time voice synthesis using ElevenLabs
- Personality-specific speech patterns
- Dynamic trash talk and commentary
- Agent-to-agent communication

### 📊 Agent Benchmarking
Real-time evaluation of agent performance:
- Win Rate
- Bluff Success Rate
- Aggression Score
- Memory Triggers
- Voice Line Count

## 🏗️ Architecture

```
pocketaces/
├── app/
│   ├── core/
│   │   ├── game/           # Game logic & rules
│   │   ├── agents/         # AI decision making
│   │   └── websocket/      # Real-time communication
│   ├── models/             # Data structures
│   ├── store/              # State management
│   └── api/                # REST & WebSocket endpoints
├── requirements.txt
├── .env.example
└── main.py
```

## 🎮 API Endpoints

### Game Management
- `POST /api/rooms` - Create new game room
- `GET /api/rooms` - List available rooms
- `POST /api/rooms/{room_id}/join` - Join room
- `POST /api/games/{game_id}/action` - Make poker move

### Agent Management
- `GET /api/agents` - List available agents
- `GET /api/agents/{agent_id}/stats` - Get agent performance
- `GET /api/agents/{agent_id}/memories` - Get agent memories

### WebSocket
- `WS /ws/game/{game_id}` - Real-time game updates

## 🎯 Demo Experience

1. **Judge picks agent** to play against
2. **Live match starts** (3-player table)
3. **AI agents speak** their thoughts and act
4. **Benchmark stats** shown post-game
5. **Optional**: agents call each other mid-game

> *"Don't fold now — I can smell the fear in your betting hand."*
> 
> *"Let's trap him like last round, Max…"*

## 🔧 Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your_openai_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# Optional
DEBUG=true
HOST=0.0.0.0
PORT=8000
DATABASE_URL=sqlite:///./pocketaces.db
```

### Game Settings

```python
# Default game configuration
DEFAULT_STARTING_CHIPS = 1000
DEFAULT_SMALL_BLIND = 10
DEFAULT_BIG_BLIND = 20
MAX_PLAYERS_PER_ROOM = 3
GAME_TIMEOUT_SECONDS = 30
```

## 🧪 Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
flake8 .
```

### Adding New Agents

1. **Define personality** in `app/models/mock_data.py`
2. **Add voice ID** to ElevenLabs configuration
3. **Test behavior** with different game scenarios

### Extending Features

- **New personality traits** - Add to `PersonalityTrait` enum
- **Voice styles** - Extend `VoiceStyle` enum
- **Game modes** - Implement new game variants
- **Agent interactions** - Add agent-to-agent communication

## 🎯 Use Cases

- **Hackathon demo** - Engaging, voice-rich, fun to watch
- **LLM research** - Controlled benchmarking of reasoning agents
- **Poker training** - Play against a range of personalities
- **Entertainment** - Live stream-ready game format

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT-4 integration
- **ElevenLabs** for voice synthesis
- **LangChain** for AI agent framework
- **FastAPI** for the web framework

---

**Ready to play against AI agents that actually have personality? Let's deal the cards!** 🃏 