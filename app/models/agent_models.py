from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from uuid import uuid4

# Type aliases for better type safety
class ActionTypeStr(str, Enum):
    """Action types for agent decisions."""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"

class GamePhaseStr(str, Enum):
    """Game phases for agent memories."""
    WAITING = "waiting"
    PRE_FLOP = "pre_flop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"
    FINISHED = "finished"

class OutcomeStr(str, Enum):
    """Possible outcomes for agent memories."""
    WON = "won"
    LOST = "lost"
    FOLDED = "folded"
    BLUFFED_SUCCESSFULLY = "bluffed_successfully"
    FOLDED_EARLY = "folded_early"
    BLUFFED_FAILED = "bluffed_failed"

class PositionStr(str, Enum):
    """Player positions."""
    EARLY = "early"
    MIDDLE = "middle"
    LATE = "late"

class InteractionTypeStr(str, Enum):
    """Types of agent interactions."""
    CALL = "call"
    TAUNT = "taunt"
    STRATEGY = "strategy"
    REACTION = "reaction"

class ContextStr(str, Enum):
    """Contexts for voice lines."""
    ACTION = "action"
    REACTION = "reaction"
    TAUNT = "taunt"
    CELEBRATION = "celebration"
    DEFEAT = "defeat"
    VICTORY = "victory"

class PersonalityTrait(str, Enum):
    """Traits that define an agent's poker style."""
    AGGRESSIVE = "aggressive"
    CONSERVATIVE = "conservative"
    BLUFFER = "bluffer"
    SHARK = "shark"
    LOOSE = "loose"
    TIGHT = "tight"
    MANIAC = "maniac"
    CALLING_STATION = "calling_station"
    ROCK = "rock"
    FISH = "fish"

class VoiceStyle(str, Enum):
    """Voice style for agent speech synthesis."""
    GRITTY = "gritty"
    SARCASTIC = "sarcastic"
    CALM = "calm"
    EXCITED = "excited"
    CONFIDENT = "confident"
    NERVOUS = "nervous"
    COCKY = "cocky"
    HUMBLE = "humble"

class EmotionState(str, Enum):
    """Possible emotional states for an agent."""
    CONFIDENT = "confident"
    NERVOUS = "nervous"
    EXCITED = "excited"
    FRUSTRATED = "frustrated"
    CALM = "calm"
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"

class AgentDecision(BaseModel):
    """A decision made by an agent during a game."""
    agent_id: str
    game_id: str
    action_type: ActionTypeStr
    amount: Optional[int] = None
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
    personality_factors: Dict[str, Any] = Field(default_factory=dict)
    memory_influence: Optional[str] = None
    emotion_state: EmotionState = EmotionState.CALM
    voice_line: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class AgentMemory(BaseModel):
    """A memory recorded by an agent about a game event."""
    memory_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str
    opponent_id: str
    game_id: str
    action_type: ActionTypeStr
    amount: Optional[int] = None
    phase: GamePhaseStr
    outcome: Optional[OutcomeStr] = None
    opponent_reaction: Optional[str] = None
    pot_size: int
    position: PositionStr
    created_at: datetime = Field(default_factory=datetime.now)
    importance: float = Field(ge=0.0, le=1.0, default=0.5)  # How important this memory is
    
    def get_memory_summary(self) -> str:
        """Get a human-readable summary of this memory."""
        summary = f"In {self.phase.value}, I {self.action_type.value}"
        if self.amount:
            summary += f" {self.amount} chips"
        summary += f" against {self.opponent_id}"
        if self.outcome:
            summary += f" and {self.outcome.value}"
        return summary

class AgentPersonality(BaseModel):
    """Defines the personality and style of an AI agent."""
    agent_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    traits: List[PersonalityTrait]
    aggression_level: float = Field(ge=0.0, le=1.0)  # How often to raise/bet
    bluff_frequency: float = Field(ge=0.0, le=1.0)  # How often to bluff
    risk_tolerance: float = Field(ge=0.0, le=1.0)  # How much risk to take
    patience_level: float = Field(ge=0.0, le=1.0)  # How long to wait for good hands
    memory_weight: float = Field(ge=0.0, le=1.0)  # How much to rely on memories
    voice_style: VoiceStyle
    voice_id: str  # ElevenLabs voice ID
    catchphrases: List[str] = Field(default_factory=list)
    taunts: List[str] = Field(default_factory=list)
    reactions: Dict[str, List[str]] = Field(default_factory=dict)  # emotion -> phrases
    created_at: datetime = Field(default_factory=datetime.now)
    
    def get_random_catchphrase(self) -> Optional[str]:
        """Get a random catchphrase."""
        return random.choice(self.catchphrases) if self.catchphrases else None
    
    def get_random_taunt(self) -> Optional[str]:
        """Get a random taunt."""
        return random.choice(self.taunts) if self.taunts else None
    
    def get_reaction(self, emotion: EmotionState) -> Optional[str]:
        """Get a random reaction for the given emotion."""
        reactions = self.reactions.get(emotion.value, [])
        return random.choice(reactions) if reactions else None

class AgentStats(BaseModel):
    """Statistics for an agent's performance."""
    agent_id: str
    games_played: int = 0
    games_won: int = 0
    win_rate: float = 0.0
    total_profit: int = 0
    average_profit_per_game: float = 0.0
    bluff_attempts: int = 0
    bluff_successes: int = 0
    bluff_success_rate: float = 0.0
    average_aggression: float = 0.0
    memory_triggers: int = 0
    voice_lines_used: int = 0
    total_chips_won: int = 0
    total_chips_lost: int = 0
    biggest_pot_won: int = 0
    longest_winning_streak: int = 0
    current_streak: int = 0
    last_updated: datetime = Field(default_factory=datetime.now)
    
    def update_win_rate(self) -> None:
        """Update win rate based on current stats."""
        if self.games_played > 0:
            self.win_rate = self.games_won / self.games_played
    
    def update_bluff_success_rate(self) -> None:
        """Update bluff success rate."""
        if self.bluff_attempts > 0:
            self.bluff_success_rate = self.bluff_successes / self.bluff_attempts
    
    def update_average_profit(self) -> None:
        """Update average profit per game."""
        if self.games_played > 0:
            self.average_profit_per_game = self.total_profit / self.games_played

class AgentInteraction(BaseModel):
    """Represents an interaction between two agents."""
    interaction_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str
    target_agent_id: str
    game_id: str
    interaction_type: InteractionTypeStr
    message: str
    emotion: EmotionState
    timestamp: datetime = Field(default_factory=datetime.now)
    was_heard: bool = False  # Whether other players heard this interaction

class VoiceLine(BaseModel):
    """A line of speech generated by an agent."""
    line_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str
    text: str
    emotion: EmotionState
    context: ContextStr
    audio_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class AgentBehavior(BaseModel):
    """Dynamic behavior that changes based on game state."""
    agent_id: str
    current_emotion: EmotionState = EmotionState.CALM
    confidence_level: float = Field(ge=0.0, le=1.0, default=0.5)
    tilt_level: float = Field(ge=0.0, le=1.0, default=0.0)  # How tilted the agent is
    aggression_modifier: float = 1.0  # Multiplier for aggression
    bluff_modifier: float = 1.0  # Multiplier for bluffing
    recent_actions: List[str] = Field(default_factory=list)  # Last 5 actions
    opponent_observations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    def update_emotion(self, new_emotion: EmotionState, intensity: float = 1.0) -> None:
        """Update agent's emotional state."""
        self.current_emotion = new_emotion
        if new_emotion in [EmotionState.FRUSTRATED, EmotionState.NERVOUS]:
            self.tilt_level = min(1.0, self.tilt_level + intensity * 0.2)
        elif new_emotion in [EmotionState.CONFIDENT, EmotionState.EXCITED]:
            self.tilt_level = max(0.0, self.tilt_level - intensity * 0.1)
    
    def add_action(self, action: str) -> None:
        """Add recent action to history."""
        self.recent_actions.append(action)
        if len(self.recent_actions) > 5:
            self.recent_actions.pop(0)
    
    def observe_opponent(self, opponent_id: str, observation: Dict[str, Any]) -> None:
        """Record observation about opponent."""
        if opponent_id not in self.opponent_observations:
            self.opponent_observations[opponent_id] = {}
        self.opponent_observations[opponent_id].update(observation)

class AgentContext(BaseModel):
    """Context for agent decision making."""
    agent_id: str
    game_state: Dict[str, Any]
    player_state: Dict[str, Any]
    recent_memories: List[AgentMemory]
    opponent_profiles: Dict[str, Dict[str, Any]]
    current_emotion: EmotionState
    available_actions: List[str]
    pot_odds: float
    position: str
    stack_to_pot_ratio: float
    created_at: datetime = Field(default_factory=datetime.now)

# Import random for the personality methods
import random 