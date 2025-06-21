from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from uuid import uuid4

class GamePhase(str, Enum):
    """Phases of a poker game."""
    WAITING = "waiting"
    PRE_FLOP = "pre_flop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"
    FINISHED = "finished"

class ActionType(str, Enum):
    """Possible player actions in poker."""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"

class PlayerStatus(str, Enum):
    """Status of a player in the game."""
    ACTIVE = "active"
    FOLDED = "folded"
    ALL_IN = "all_in"
    SITTING_OUT = "sitting_out"

class Card(BaseModel):
    """A playing card."""
    suit: str  # hearts, diamonds, clubs, spades
    rank: str  # 2-10, J, Q, K, A
    value: int  # 2-14 (A=14)
    
    def __str__(self) -> str:
        return f"{self.rank}{self.suit[0].upper()}"
    
    def __repr__(self) -> str:
        return self.__str__()

class PlayerAction(BaseModel):
    """An action taken by a player during the game."""
    player_id: str
    action_type: ActionType
    amount: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def __str__(self) -> str:
        if self.action_type == ActionType.FOLD:
            return f"{self.player_id} folded"
        elif self.action_type == ActionType.CHECK:
            return f"{self.player_id} checked"
        elif self.action_type == ActionType.CALL:
            return f"{self.player_id} called {self.amount}"
        elif self.action_type == ActionType.RAISE:
            return f"{self.player_id} raised to {self.amount}"
        elif self.action_type == ActionType.ALL_IN:
            return f"{self.player_id} went all-in with {self.amount}"
        return f"{self.player_id} {self.action_type}"

class Player(BaseModel):
    """A player in the game."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    chips: int
    position: int  # 0=dealer, 1=small blind, 2=big blind
    status: PlayerStatus = PlayerStatus.ACTIVE
    hole_cards: List[Card] = Field(default_factory=list)
    current_bet: int = 0
    total_bet: int = 0
    is_human: bool = False
    is_agent: bool = False
    agent_id: Optional[str] = None
    last_action: Optional[PlayerAction] = None
    joined_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True

class HandRank(BaseModel):
    """Represents the best hand a player can make."""
    rank: str  # "high_card", "pair", "two_pair", etc.
    value: int  # 1-10 for ranking
    cards: List[Card]  # Best 5 cards
    kickers: List[Card] = Field(default_factory=list)  # Additional cards for tie-breaking

class GameState(BaseModel):
    """State of a poker game."""
    game_id: str = Field(default_factory=lambda: str(uuid4()))
    room_id: str
    phase: GamePhase = GamePhase.WAITING
    players: List[Player] = Field(default_factory=list)
    community_cards: List[Card] = Field(default_factory=list)
    pot: int = 0
    current_bet: int = 0
    min_raise: int = 0
    active_player_index: int = 0
    dealer_index: int = 0
    small_blind: int = 10
    big_blind: int = 20
    last_action: Optional[PlayerAction] = None
    action_history: List[PlayerAction] = Field(default_factory=list)
    winners: List[str] = Field(default_factory=list)  # Player IDs
    winning_hand: Optional[HandRank] = None
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def get_active_player(self) -> Optional[Player]:
        """Get the currently active player."""
        if not self.players or self.active_player_index >= len(self.players):
            return None
        return self.players[self.active_player_index]
    
    def get_active_players(self) -> List[Player]:
        """Get all players who haven't folded."""
        return [p for p in self.players if p.status == PlayerStatus.ACTIVE]
    
    def get_player_by_id(self, player_id: str) -> Optional[Player]:
        """Get player by ID."""
        for player in self.players:
            if player.id == player_id:
                return player
        return None
    
    def get_next_active_player(self) -> Optional[Player]:
        """Get the next player who should act."""
        active_players = self.get_active_players()
        if not active_players:
            return None
        
        current_player = self.get_active_player()
        if not current_player:
            return active_players[0]
        
        # Find current player in active players list
        try:
            current_index = next(i for i, p in enumerate(active_players) if p.id == current_player.id)
            next_index = (current_index + 1) % len(active_players)
            return active_players[next_index]
        except StopIteration:
            return active_players[0]

class GameRoom(BaseModel):
    """A room where poker games are played."""
    room_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    max_players: int = 3
    min_players: int = 2
    current_game: Optional[GameState] = None
    game_history: List[GameState] = Field(default_factory=list)
    players: List[Player] = Field(default_factory=list)
    spectators: List[str] = Field(default_factory=list)  # Player IDs
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    settings: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True
    
    def can_start_game(self) -> bool:
        """Check if game can start."""
        human_players = [p for p in self.players if p.is_human]
        agent_players = [p for p in self.players if p.is_agent]
        return len(human_players) >= 1 and len(agent_players) >= 1
    
    def add_player(self, player: Player) -> bool:
        """Add player to room."""
        if len(self.players) >= self.max_players:
            return False
        if any(p.id == player.id for p in self.players):
            return False
        self.players.append(player)
        return True
    
    def remove_player(self, player_id: str) -> bool:
        """Remove player from room."""
        for i, player in enumerate(self.players):
            if player.id == player_id:
                self.players.pop(i)
                return True
        return False

class GameResult(BaseModel):
    """Result of a completed game."""
    game_id: str
    room_id: str
    winners: List[str]
    winning_hand: Optional[HandRank]
    pot: int
    player_results: Dict[str, Dict[str, Any]]  # player_id -> {profit, final_chips, actions}
    duration: float  # seconds
    ended_at: datetime = Field(default_factory=datetime.now)

class GameEvent(BaseModel):
    """Event that occurred in a game or room."""
    event_type: str  # "player_joined", "game_started", "action_made", "game_ended", etc.
    game_id: str
    room_id: str
    player_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now) 