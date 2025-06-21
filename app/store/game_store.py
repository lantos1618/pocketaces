from typing import Dict, List, Optional, Any, TypedDict
from datetime import datetime, timedelta
import asyncio
from ..models.game_models import (
    GameRoom,
    GameState,
    Player,
    GameEvent,
    GameResult,
    HandRank,
)
from ..models.agent_models import AgentPersonality, AgentStats, AgentMemory
from ..models.mock_data import MOCK_AGENTS, MOCK_AGENT_STATS, MOCK_AGENT_MEMORIES


class PlayerSession(TypedDict):
    """Player session data."""

    joined_at: datetime
    current_room: Optional[str]
    current_game: Optional[str]
    total_games: int
    total_wins: int


class PlayerResult(TypedDict):
    """Player result data for a game."""

    profit: int
    final_chips: int
    actions: int


class RoomStats(TypedDict):
    """Room statistics."""

    total_games: int
    active_players: int
    average_pot: float
    most_active_player: Optional[str]


class AgentPerformance(TypedDict):
    """Agent performance metrics."""

    win_rate: float
    average_profit: float
    bluff_success_rate: float
    total_games: int
    recent_form: List[str]


class RoomInfo(TypedDict):
    """Room information for API responses."""

    room_id: str
    name: str
    player_count: int
    max_players: int
    has_active_game: bool
    settings: Dict[str, Any]


class GameStore:
    """Centralized store for managing game state and data."""

    def __init__(self) -> None:
        # Game rooms and active games
        self.rooms: Dict[str, GameRoom] = {}
        self.active_games: Dict[str, GameState] = {}
        self.game_history: List[GameResult] = []

        # Agent management
        self.available_agents: Dict[str, AgentPersonality] = {}
        self.agent_stats: Dict[str, AgentStats] = {}
        self.agent_memories: Dict[str, List[AgentMemory]] = {}

        # Player sessions
        self.player_sessions: Dict[str, PlayerSession] = {}

        # Event history
        self.game_events: List[GameEvent] = []

        # Concurrency control
        self._game_locks: Dict[str, asyncio.Lock] = {}
        self._room_locks: Dict[str, asyncio.Lock] = {}
        self._store_lock = asyncio.Lock()

        # Initialize with mock data
        self._initialize_mock_data()

    def _get_game_lock(self, game_id: str) -> asyncio.Lock:
        """Get or create a lock for a specific game."""
        if game_id not in self._game_locks:
            self._game_locks[game_id] = asyncio.Lock()
        return self._game_locks[game_id]

    def _get_room_lock(self, room_id: str) -> asyncio.Lock:
        """Get or create a lock for a specific room."""
        if room_id not in self._room_locks:
            self._room_locks[room_id] = asyncio.Lock()
        return self._room_locks[room_id]

    def _initialize_mock_data(self) -> None:
        """Initialize store with mock data."""
        # Add mock agents
        for agent in MOCK_AGENTS:
            self.available_agents[agent.agent_id] = agent

        # Add mock agent stats
        self.agent_stats.update(MOCK_AGENT_STATS)

        # Add mock agent memories
        for memory in MOCK_AGENT_MEMORIES:
            if memory.agent_id not in self.agent_memories:
                self.agent_memories[memory.agent_id] = []
            self.agent_memories[memory.agent_id].append(memory)

    # Room Management
    async def create_room(
        self, name: str, max_players: int = 3, settings: Optional[Dict[str, Any]] = None
    ) -> GameRoom:
        """Create a new game room."""
        async with self._store_lock:
            room = GameRoom(name=name, max_players=max_players, settings=settings or {})
            self.rooms[room.room_id] = room
            return room

    def get_room(self, room_id: str) -> Optional[GameRoom]:
        """Get room by ID."""
        return self.rooms.get(room_id)

    def get_all_rooms(self) -> List[GameRoom]:
        """Get all rooms."""
        return list(self.rooms.values())

    async def delete_room(self, room_id: str) -> bool:
        """Delete a room."""
        async with self._get_room_lock(room_id):
            if room_id in self.rooms:
                del self.rooms[room_id]
                return True
            return False

    # Game Management
    async def create_game(self, room_id: str) -> Optional[GameState]:
        """Create a new game in a room."""
        async with self._get_room_lock(room_id):
            room = self.get_room(room_id)
            if not room or not room.can_start_game():
                return None

            game = GameState(
                room_id=room_id,
                players=room.players.copy(),
                small_blind=room.settings.get("small_blind", 10),
                big_blind=room.settings.get("big_blind", 20),
            )

            self.active_games[game.game_id] = game
            room.current_game = game

            # Record event
            await self._record_event("game_created", game.game_id, room_id)

            return game

    def get_game(self, game_id: str) -> Optional[GameState]:
        """Get game by ID."""
        return self.active_games.get(game_id)

    def get_active_games(self) -> List[GameState]:
        """Get all active games."""
        return list(self.active_games.values())

    async def end_game(
        self, game_id: str, winners: List[str], winning_hand: Optional[HandRank] = None
    ) -> Optional[GameResult]:
        """End a game and create result."""
        async with self._get_game_lock(game_id):
            game = self.get_game(game_id)
            if not game:
                return None

            # Get room settings for starting chips
            room = self.get_room(game.room_id)
            starting_chips = room.settings.get("starting_chips", 1000) if room else 1000

            # Calculate results
            player_results: Dict[str, Dict[str, Any]] = {}
            for player in game.players:
                profit = player.chips - starting_chips
                player_results[player.id] = {
                    "profit": profit,
                    "final_chips": player.chips,
                    "actions": len(
                        [a for a in game.action_history if a.player_id == player.id]
                    ),
                }

            # Create result
            result = GameResult(
                game_id=game_id,
                room_id=game.room_id,
                winners=winners,
                winning_hand=winning_hand,
                pot=game.pot,
                player_results=player_results,
                duration=(datetime.now() - game.created_at).total_seconds(),
            )

            # Store result
            self.game_history.append(result)

            # Update room
            if room:
                room.game_history.append(game)
                room.current_game = None

            # Remove from active games
            del self.active_games[game_id]

            # Record event
            await self._record_event(
                "game_ended", game_id, game.room_id, data={"winners": winners}
            )

            return result

    # Player Management
    async def add_player_to_room(self, room_id: str, player: Player) -> bool:
        """Add player to a room."""
        async with self._get_room_lock(room_id):
            room = self.get_room(room_id)
            if not room:
                return False

            success = room.add_player(player)
            if success:
                await self._record_event("player_joined", None, room_id, player.id)
            return success

    async def remove_player_from_room(self, room_id: str, player_id: str) -> bool:
        """Remove player from a room."""
        async with self._get_room_lock(room_id):
            room = self.get_room(room_id)
            if not room:
                return False

            success = room.remove_player(player_id)
            if success:
                await self._record_event("player_left", None, room_id, player_id)
            return success

    def get_player_session(self, player_id: str) -> PlayerSession:
        """Get or create player session."""
        if player_id not in self.player_sessions:
            self.player_sessions[player_id] = {
                "joined_at": datetime.now(),
                "current_room": None,
                "current_game": None,
                "total_games": 0,
                "total_wins": 0,
            }
        return self.player_sessions[player_id]

    # Agent Management
    def get_agent_personality(self, agent_id: str) -> Optional[AgentPersonality]:
        """Get agent personality."""
        return self.available_agents.get(agent_id)

    def get_all_agents(self) -> List[AgentPersonality]:
        """Get all available agents."""
        return list(self.available_agents.values())

    def get_agent_stats(self, agent_id: str) -> Optional[AgentStats]:
        """Get agent statistics."""
        return self.agent_stats.get(agent_id)

    def update_agent_stats(self, agent_id: str, stats: AgentStats) -> None:
        """Update agent statistics."""
        self.agent_stats[agent_id] = stats

    def get_agent_memories(self, agent_id: str) -> List[AgentMemory]:
        """Get agent memories."""
        return self.agent_memories.get(agent_id, [])

    def add_agent_memory(self, memory: AgentMemory) -> None:
        """Add a memory for an agent."""
        if memory.agent_id not in self.agent_memories:
            self.agent_memories[memory.agent_id] = []
        self.agent_memories[memory.agent_id].append(memory)

    def get_relevant_memories(
        self, agent_id: str, opponent_id: str, limit: int = 5
    ) -> List[AgentMemory]:
        """Get memories relevant to a specific opponent."""
        memories = self.agent_memories.get(agent_id, [])
        relevant = [m for m in memories if m.opponent_id == opponent_id]
        return sorted(relevant, key=lambda x: x.importance, reverse=True)[:limit]

    # Game Actions - CRITICAL FIX: Added proper locking
    async def make_player_action(
        self,
        game_id: str,
        player_id: str,
        action_type: str,
        amount: Optional[int] = None,
    ) -> bool:
        """Make a player action in a game with proper concurrency control."""
        async with self._get_game_lock(game_id):
            game = self.get_game(game_id)
            if not game:
                return False

            player = game.get_player_by_id(player_id)
            if not player or player.status != "active":
                return False

            # Create action
            from ..models.game_models import PlayerAction, ActionType, PlayerStatus

            action = PlayerAction(
                player_id=player_id, action_type=ActionType(action_type), amount=amount
            )

            # Execute action based on type
            match action_type:
                case "fold":
                    player.status = PlayerStatus.FOLDED
                case "call":
                    call_amount = game.current_bet - player.current_bet
                    if player.chips >= call_amount:
                        player.chips -= call_amount
                        player.current_bet = game.current_bet
                        game.pot += call_amount
                    else:
                        return False
                case "raise":
                    if amount is None or amount < game.min_raise:
                        return False
                    total_needed = game.current_bet - player.current_bet + amount
                    if player.chips >= total_needed:
                        player.chips -= total_needed
                        player.current_bet = game.current_bet + amount
                        game.pot += total_needed
                        game.current_bet = player.current_bet
                        game.min_raise = amount
                    else:
                        return False
                case "all_in":
                    all_in_amount = player.chips
                    player.current_bet += all_in_amount
                    game.pot += all_in_amount
                    player.chips = 0
                    player.status = PlayerStatus.ALL_IN
                    if player.current_bet > game.current_bet:
                        game.current_bet = player.current_bet
                case _:
                    return False

            # Update game state
            player.last_action = action
            game.last_action = action
            game.action_history.append(action)

            # Move to next player
            game.active_player_index = (game.active_player_index + 1) % len(
                game.players
            )

            # Record event
            await self._record_event(
                "action_made",
                game_id,
                game.room_id,
                player_id,
                {"action_type": action_type, "amount": amount},
            )

            return True

    # Event Management
    async def _record_event(
        self,
        event_type: str,
        game_id: Optional[str] = None,
        room_id: Optional[str] = None,
        player_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a game event."""
        async with self._store_lock:
            event = GameEvent(
                event_type=event_type,
                game_id=game_id or "",
                room_id=room_id or "",
                player_id=player_id,
                data=data or {},
            )
            self.game_events.append(event)

    def get_game_events(
        self,
        game_id: Optional[str] = None,
        room_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[GameEvent]:
        """Get game events with optional filtering."""
        events = self.game_events

        if game_id:
            events = [e for e in events if e.game_id == game_id]
        if room_id:
            events = [e for e in events if e.room_id == room_id]

        return sorted(events, key=lambda x: x.timestamp, reverse=True)[:limit]

    # Statistics and Analytics
    def get_room_stats(self, room_id: str) -> Optional[RoomStats]:
        """Get statistics for a room."""
        room = self.get_room(room_id)
        if not room:
            return None

        total_games = len(room.game_history)
        active_players = len(room.players)

        # Calculate average pot
        total_pot = sum(game.pot for game in room.game_history)
        average_pot = total_pot / total_games if total_games > 0 else 0

        # Find most active player
        player_games: Dict[str, int] = {}
        for game in room.game_history:
            for player in game.players:
                player_games[player.id] = player_games.get(player.id, 0) + 1

        most_active = (
            max(player_games.items(), key=lambda x: x[1])[0] if player_games else None
        )

        return {
            "total_games": total_games,
            "active_players": active_players,
            "average_pot": average_pot,
            "most_active_player": most_active,
        }

    def get_agent_performance(self, agent_id: str) -> Optional[AgentPerformance]:
        """Get performance metrics for an agent."""
        stats = self.get_agent_stats(agent_id)
        if not stats:
            return None

        # Get recent form (last 5 games)
        recent_games = [g for g in self.game_history if agent_id in g.winners][-5:]
        recent_form = ["W" if agent_id in g.winners else "L" for g in recent_games]

        return {
            "win_rate": stats.win_rate,
            "average_profit": stats.average_profit_per_game,
            "bluff_success_rate": stats.bluff_success_rate,
            "total_games": stats.games_played,
            "recent_form": recent_form,
        }

    def get_available_rooms(self) -> List[RoomInfo]:
        """Get list of available rooms for API responses."""
        rooms_info: List[RoomInfo] = []
        for room in self.rooms.values():
            rooms_info.append(
                {
                    "room_id": room.room_id,
                    "name": room.name,
                    "player_count": len(room.players),
                    "max_players": room.max_players,
                    "has_active_game": room.current_game is not None,
                    "settings": room.settings,
                }
            )
        return rooms_info

    # Maintenance
    async def cleanup_inactive_rooms(self, max_age_hours: int = 24) -> int:
        """Clean up inactive rooms older than specified hours."""
        async with self._store_lock:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            rooms_to_delete = []

            for room_id, room in self.rooms.items():
                if (
                    room.created_at < cutoff_time
                    and not room.players
                    and not room.current_game
                ):
                    rooms_to_delete.append(room_id)

            for room_id in rooms_to_delete:
                del self.rooms[room_id]

            return len(rooms_to_delete)


# Global game store instance
game_store = GameStore()
