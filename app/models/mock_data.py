from typing import List, Optional, Dict, Any, Union
import random
from datetime import datetime, timedelta
from .game_models import Card, GameState, GameRoom, Player, GamePhase, ActionType
from .agent_models import (
    AgentPersonality,
    AgentStats,
    AgentMemory,
    AgentBehavior,
    AgentInteraction,
    PersonalityTrait,
    VoiceStyle,
    EmotionState,
    ActionTypeStr,
    GamePhaseStr,
    OutcomeStr,
    PositionStr,
    InteractionTypeStr,
    ContextStr,
)
from .constants import get_agent_voice_id

# Mock Cards
MOCK_CARDS = [
    Card(suit="hearts", rank="A", value=14),
    Card(suit="hearts", rank="K", value=13),
    Card(suit="hearts", rank="Q", value=12),
    Card(suit="hearts", rank="J", value=11),
    Card(suit="hearts", rank="10", value=10),
    Card(suit="hearts", rank="9", value=9),
    Card(suit="hearts", rank="8", value=8),
    Card(suit="hearts", rank="7", value=7),
    Card(suit="hearts", rank="6", value=6),
    Card(suit="hearts", rank="5", value=5),
    Card(suit="hearts", rank="4", value=4),
    Card(suit="hearts", rank="3", value=3),
    Card(suit="hearts", rank="2", value=2),
    Card(suit="diamonds", rank="A", value=14),
    Card(suit="diamonds", rank="K", value=13),
    Card(suit="diamonds", rank="Q", value=12),
    Card(suit="diamonds", rank="J", value=11),
    Card(suit="diamonds", rank="10", value=10),
    Card(suit="diamonds", rank="9", value=9),
    Card(suit="diamonds", rank="8", value=8),
    Card(suit="diamonds", rank="7", value=7),
    Card(suit="diamonds", rank="6", value=6),
    Card(suit="diamonds", rank="5", value=5),
    Card(suit="diamonds", rank="4", value=4),
    Card(suit="diamonds", rank="3", value=3),
    Card(suit="diamonds", rank="2", value=2),
    Card(suit="clubs", rank="A", value=14),
    Card(suit="clubs", rank="K", value=13),
    Card(suit="clubs", rank="Q", value=12),
    Card(suit="clubs", rank="J", value=11),
    Card(suit="clubs", rank="10", value=10),
    Card(suit="clubs", rank="9", value=9),
    Card(suit="clubs", rank="8", value=8),
    Card(suit="clubs", rank="7", value=7),
    Card(suit="clubs", rank="6", value=6),
    Card(suit="clubs", rank="5", value=5),
    Card(suit="clubs", rank="4", value=4),
    Card(suit="clubs", rank="3", value=3),
    Card(suit="clubs", rank="2", value=2),
    Card(suit="spades", rank="A", value=14),
    Card(suit="spades", rank="K", value=13),
    Card(suit="spades", rank="Q", value=12),
    Card(suit="spades", rank="J", value=11),
    Card(suit="spades", rank="10", value=10),
    Card(suit="spades", rank="9", value=9),
    Card(suit="spades", rank="8", value=8),
    Card(suit="spades", rank="7", value=7),
    Card(suit="spades", rank="6", value=6),
    Card(suit="spades", rank="5", value=5),
    Card(suit="spades", rank="4", value=4),
    Card(suit="spades", rank="3", value=3),
    Card(suit="spades", rank="2", value=2),
]

# Mock Agent Personalities
MOCK_AGENTS = [
    AgentPersonality(
        name="The Rock",
        description="A conservative, calculated player who waits for the perfect moment to strike.",
        traits=[
            PersonalityTrait.CONSERVATIVE,
            PersonalityTrait.SHARK,
            PersonalityTrait.TIGHT,
        ],
        aggression_level=0.4,
        bluff_frequency=0.2,
        risk_tolerance=0.3,
        patience_level=0.9,
        memory_weight=0.8,
        voice_style=VoiceStyle.CALM,
        voice_id=get_agent_voice_id("the_rock"),
        catchphrases=[
            "Patience is a virtue, especially in poker.",
            "I'll wait for the right moment.",
            "Quality over quantity, always.",
            "Let's see how this plays out.",
        ],
        taunts=[
            "Your aggression is your weakness.",
            "I've seen this pattern before.",
            "You're too predictable.",
            "Maybe try thinking before acting.",
        ],
        reactions={
            "confident": [
                "I've been waiting for this hand.",
                "This is exactly what I expected.",
                "The odds are in my favor.",
            ],
            "nervous": [
                "This is getting interesting.",
                "I need to be careful here.",
                "Let me think about this.",
            ],
            "calm": [
                "Steady as she goes.",
                "No need to rush anything.",
                "I'll take my time.",
            ],
        },
    ),
    AgentPersonality(
        name="The Maniac",
        description="A wild, unpredictable player who plays every hand and raises constantly.",
        traits=[
            PersonalityTrait.MANIAC,
            PersonalityTrait.AGGRESSIVE,
            PersonalityTrait.LOOSE,
        ],
        aggression_level=0.95,
        bluff_frequency=0.9,
        risk_tolerance=0.9,
        patience_level=0.1,
        memory_weight=0.2,
        voice_style=VoiceStyle.EXCITED,
        voice_id=get_agent_voice_id("the_maniac"),
        catchphrases=[
            "Let's make this interesting!",
            "I'm feeling lucky!",
            "All in or nothing!",
            "This is going to be epic!",
        ],
        taunts=[
            "Are you scared or just boring?",
            "Come on, live a little!",
            "You play like my grandmother!",
            "This is poker, not knitting!",
        ],
        reactions={
            "excited": [
                "This is what I live for!",
                "Let's turn this up to 11!",
                "I'm on fire tonight!",
            ],
            "frustrated": [
                "Lady Luck is being a tease!",
                "Come on, give me something!",
                "I need some action!",
            ],
            "aggressive": [
                "Time to shake things up!",
                "Let's see who's really brave!",
                "No guts, no glory!",
            ],
        },
    ),
    AgentPersonality(
        name="The Shark",
        description="A professional, analytical player who studies every detail and calculates odds perfectly.",
        traits=[
            PersonalityTrait.SHARK,
            PersonalityTrait.CONSERVATIVE,
            PersonalityTrait.TIGHT,
        ],
        aggression_level=0.6,
        bluff_frequency=0.3,
        risk_tolerance=0.5,
        patience_level=0.8,
        memory_weight=0.9,
        voice_style=VoiceStyle.CONFIDENT,
        voice_id=get_agent_voice_id("the_shark"),
        catchphrases=[
            "The numbers don't lie.",
            "I've calculated the odds.",
            "This is a mathematical certainty.",
            "Let's analyze this situation.",
        ],
        taunts=[
            "Your math is as bad as your poker.",
            "I've seen better calculations in a kindergarten.",
            "Maybe you should stick to counting on your fingers.",
            "The odds are not in your favor.",
        ],
        reactions={
            "confident": [
                "The probability is clear.",
                "This is statistically sound.",
                "I've done the calculations.",
            ],
            "nervous": [
                "Let me think about the odds.",
                "This requires careful consideration.",
                "I need to recalculate.",
            ],
            "calm": [
                "Let's approach this systematically.",
                "I'll make the optimal play.",
                "This is a calculated risk.",
            ],
        },
    ),
    AgentPersonality(
        name="The Fish",
        description="A loose, calling station who calls everything and rarely folds, relying on luck and persistence.",
        traits=[
            PersonalityTrait.LOOSE,
            PersonalityTrait.CALLING_STATION,
            PersonalityTrait.FISH,
        ],
        aggression_level=0.3,
        bluff_frequency=0.1,
        risk_tolerance=0.7,
        patience_level=0.2,
        memory_weight=0.3,
        voice_style=VoiceStyle.NERVOUS,
        voice_id=get_agent_voice_id("the_fish"),
        catchphrases=[
            "I'll call that.",
            "Why not?",
            "Let's see what happens.",
            "I'm feeling lucky!",
        ],
        taunts=[
            "Sometimes you just gotta go with it.",
            "You never know until you try.",
            "Luck beats skill sometimes.",
            "I might surprise you.",
        ],
        reactions={
            "nervous": [
                "Oh wow, that worked!",
                "I didn't expect that!",
                "Sometimes you get lucky!",
            ],
            "excited": [
                "Maybe this is my hand!",
                "I've got a good feeling about this.",
                "Let's see what the cards say.",
            ],
            "defensive": [
                "No big deal.",
                "Whatever happens, happens.",
                "I'm just here to have fun.",
            ],
        },
    ),
    AgentPersonality(
        name="The Bluffer",
        description="A street-smart player who loves to bluff and trash talk. Aggressive but calculated.",
        traits=[
            PersonalityTrait.AGGRESSIVE,
            PersonalityTrait.BLUFFER,
            PersonalityTrait.LOOSE,
        ],
        aggression_level=0.8,
        bluff_frequency=0.7,
        risk_tolerance=0.6,
        patience_level=0.3,
        memory_weight=0.5,
        voice_style=VoiceStyle.GRITTY,
        voice_id=get_agent_voice_id("the_bluffer"),
        catchphrases=[
            "I can smell the fear in your betting hand.",
            "Time to separate the men from the boys.",
            "You're playing checkers while I'm playing chess.",
            "Let's see what you're really made of.",
        ],
        taunts=[
            "That's what I thought - all bark, no bite.",
            "Your poker face is as obvious as a neon sign.",
            "Maybe you should stick to Go Fish.",
            "I've seen better bluffs in a kindergarten.",
        ],
        reactions={
            "confident": [
                "I've got you right where I want you.",
                "This is going to be beautiful.",
                "Time to collect my chips.",
            ],
            "frustrated": [
                "You got lucky this time.",
                "That was a terrible call.",
                "I'll remember this.",
            ],
            "excited": [
                "Oh, this is going to be fun!",
                "Let's make this interesting!",
                "Time to turn up the heat!",
            ],
        },
    ),
    AgentPersonality(
        name="The Queen",
        description="A sophisticated, elegant player who uses psychology and charm to win.",
        traits=[
            PersonalityTrait.AGGRESSIVE,
            PersonalityTrait.SHARK,
            PersonalityTrait.TIGHT,
        ],
        aggression_level=0.5,
        bluff_frequency=0.4,
        risk_tolerance=0.4,
        patience_level=0.7,
        memory_weight=0.6,
        voice_style=VoiceStyle.COCKY,
        voice_id=get_agent_voice_id("the_queen"),
        catchphrases=[
            "Darling, you're making this too easy.",
            "Let's make this interesting, shall we?",
            "I do love a good challenge.",
            "You're quite the character.",
        ],
        taunts=[
            "Oh honey, that was adorable.",
            "You're trying so hard, it's cute.",
            "Maybe you should stick to simpler games.",
            "I've seen better attempts at deception.",
        ],
        reactions={
            "confident": [
                "Oh, you're such a delight.",
                "This is getting quite entertaining.",
                "I do enjoy our little games.",
            ],
            "calm": [
                "How sophisticated of you.",
                "Let's keep this civilized.",
                "I appreciate the effort.",
            ],
            "excited": [
                "Oh, you're full of surprises!",
                "This is getting interesting!",
                "I love a good plot twist!",
            ],
        },
    ),
]

# Mock Agent Stats
MOCK_AGENT_STATS = {
    agent.agent_id: AgentStats(
        agent_id=agent.agent_id,
        games_played=random.randint(10, 50),
        games_won=random.randint(5, 25),
        total_profit=random.randint(-500, 1000),
        bluff_attempts=random.randint(20, 100),
        bluff_successes=random.randint(5, 40),
        average_aggression=random.uniform(0.3, 0.9),
        memory_triggers=random.randint(10, 50),
        voice_lines_used=random.randint(50, 200),
    )
    for agent in MOCK_AGENTS
}

# Mock Agent Memories
MOCK_AGENT_MEMORIES = []
for agent in MOCK_AGENTS:
    for _ in range(random.randint(5, 15)):
        memory = AgentMemory(
            agent_id=agent.agent_id,
            opponent_id=f"player_{random.randint(1, 10)}",
            game_id=f"game_{random.randint(1, 100)}",
            action_type=random.choice(
                [
                    ActionTypeStr.RAISE,
                    ActionTypeStr.CALL,
                    ActionTypeStr.FOLD,
                    ActionTypeStr.CHECK,
                    ActionTypeStr.ALL_IN,
                ]
            ),
            amount=random.randint(10, 200) if random.random() > 0.3 else None,
            phase=random.choice(
                [
                    GamePhaseStr.PRE_FLOP,
                    GamePhaseStr.FLOP,
                    GamePhaseStr.TURN,
                    GamePhaseStr.RIVER,
                ]
            ),
            outcome=random.choice(
                [
                    OutcomeStr.WON,
                    OutcomeStr.LOST,
                    OutcomeStr.FOLDED,
                    OutcomeStr.BLUFFED_SUCCESSFULLY,
                ]
            ),
            pot_size=random.randint(50, 500),
            position=random.choice(
                [PositionStr.EARLY, PositionStr.MIDDLE, PositionStr.LATE]
            ),
            importance=random.uniform(0.1, 1.0),
        )
        MOCK_AGENT_MEMORIES.append(memory)

# Mock Game Rooms
MOCK_ROOMS = [
    GameRoom(
        room_id="room_1",
        name="High Stakes Table",
        max_players=3,
        min_players=2,
        settings={"small_blind": 10, "big_blind": 20, "starting_chips": 1000},
    ),
    GameRoom(
        room_id="room_2",
        name="Demo Table",
        max_players=3,
        min_players=2,
        settings={"small_blind": 5, "big_blind": 10, "starting_chips": 500},
    ),
    GameRoom(
        room_id="room_3",
        name="Tournament Table",
        max_players=3,
        min_players=2,
        settings={"small_blind": 25, "big_blind": 50, "starting_chips": 2000},
    ),
]

# Mock Players
MOCK_PLAYERS = [
    Player(
        id="human_1",
        name="Player 1",
        chips=1000,
        position=0,
        is_human=True,
        is_agent=False,
    ),
    Player(
        id="human_2",
        name="Player 2",
        chips=1000,
        position=1,
        is_human=True,
        is_agent=False,
    ),
]

# Mock Game States
MOCK_GAME_STATES = [
    GameState(
        game_id="game_1",
        room_id="room_1",
        phase=GamePhase.PRE_FLOP,
        players=MOCK_PLAYERS[:2],
        pot=30,
        current_bet=20,
        min_raise=20,
        active_player_index=0,
        dealer_index=0,
    ),
    GameState(
        game_id="game_2",
        room_id="room_2",
        phase=GamePhase.FLOP,
        players=MOCK_PLAYERS,
        community_cards=MOCK_CARDS[:3],
        pot=150,
        current_bet=0,
        min_raise=10,
        active_player_index=1,
        dealer_index=0,
    ),
]


# Helper functions
def get_random_cards(count: int) -> List[Card]:
    """Get random cards for testing"""
    return random.sample(MOCK_CARDS, count)


def get_random_agent() -> AgentPersonality:
    """Get a random agent personality"""
    return random.choice(MOCK_AGENTS)


def get_agent_by_name(name: str) -> Optional[AgentPersonality]:
    """Get agent by name"""
    for agent in MOCK_AGENTS:
        if agent.name == name:
            return agent
    return None


def create_mock_player_from_agent(agent: AgentPersonality, chips: int = 1000) -> Player:
    """Create a player from an agent personality"""
    return Player(
        id=agent.agent_id,
        name=agent.name,
        chips=chips,
        position=0,
        is_human=False,
        is_agent=True,
        agent_id=agent.agent_id,
    )
