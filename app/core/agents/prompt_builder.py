from typing import Dict, Any, List
from langchain.prompts import PromptTemplate
from ...models.agent_models import (
    AgentPersonality,
    AgentContext,
    AgentMemory,
    AgentBehavior,
)


class PromptBuilder:
    """Builds prompts for agent decision making"""

    def __init__(self) -> None:
        self.base_template = PromptTemplate(
            input_variables=[
                "personality_name",
                "personality_description",
                "traits",
                "voice_style",
                "game_state",
                "player_state",
                "opponents",
                "memories",
                "available_actions",
                "pot_odds",
                "position",
                "stack_to_pot",
                "current_emotion",
                "aggression_level",
                "bluff_frequency",
                "risk_tolerance",
            ],
            template="""You are {personality_name}, a poker AI agent with the following personality:

PERSONALITY:
- Description: {personality_description}
- Traits: {traits}
- Voice Style: {voice_style}
- Aggression Level: {aggression_level}/10
- Bluff Frequency: {bluff_frequency}/10
- Risk Tolerance: {risk_tolerance}/10

CURRENT GAME STATE:
{game_state}

YOUR STATE:
{player_state}

OPPONENTS:
{opponents}

AVAILABLE ACTIONS: {available_actions}

STRATEGIC CONTEXT:
- Pot Odds: {pot_odds:.2f}
- Position: {position}
- Stack to Pot Ratio: {stack_to_pot:.2f}
- Current Emotion: {current_emotion}

RELEVANT MEMORIES:
{memories}

Based on your personality and the current situation, make a poker decision. Respond in this exact format:

ACTION: [fold/check/call/raise/all_in]
AMOUNT: [amount if raising, otherwise leave empty]
REASONING: [brief explanation of your decision]
EMOTION: [calm/aggressive/defensive/confident/nervous]

Consider your personality traits, the pot odds, your position, and any relevant memories when making your decision.""",
        )

    def build(
        self,
        personality: AgentPersonality,
        context: AgentContext,
        memories: List[AgentMemory],
        behavior: AgentBehavior,
    ) -> str:
        """Build the complete prompt for agent decision making"""

        # Format traits
        traits_str = ", ".join([trait.value for trait in personality.traits])

        # Format game state
        game_state_str = self._format_game_state(context.game_state)

        # Format player state
        player_state_str = self._format_player_state(context.player_state)

        # Format opponents
        opponents_str = self._format_opponents(context.opponent_profiles)

        # Format memories
        memories_str = self._format_memories(memories)

        # Format available actions
        actions_str = ", ".join(context.available_actions)

        return self.base_template.format(
            personality_name=personality.name,
            personality_description=personality.description,
            traits=traits_str,
            voice_style=personality.voice_style.value,
            game_state=game_state_str,
            player_state=player_state_str,
            opponents=opponents_str,
            memories=memories_str,
            available_actions=actions_str,
            pot_odds=context.pot_odds,
            position=context.position,
            stack_to_pot=context.stack_to_pot_ratio,
            current_emotion=behavior.current_emotion.value,
            aggression_level=personality.aggression_level,
            bluff_frequency=personality.bluff_frequency,
            risk_tolerance=personality.risk_tolerance,
        )

    def _format_game_state(self, game_state: Dict[str, Any]) -> str:
        """Format game state for prompt"""
        formatted = f"""Game ID: {game_state.get('game_id', 'Unknown')}\nPhase: {game_state.get('phase', 'Unknown')}\nPot: {game_state.get('pot', 0)}\nCurrent Bet: {game_state.get('current_bet', 0)}\nMin Raise: {game_state.get('min_raise', 0)}\nCommunity Cards: {', '.join(game_state.get('community_cards', []) )}\nDealer Position: {game_state.get('dealer_index', 0)}"""
        return formatted

    def _format_player_state(self, player_state: Dict[str, Any]) -> str:
        """Format player state for prompt"""
        return str(
            f"""Chips: {player_state.get('chips', 0)}\nCurrent Bet: {player_state.get('current_bet', 0)}\nPosition: {player_state.get('position', 0)}\nHole Cards: {', '.join(player_state.get('hole_cards', []) )}\nStatus: {player_state.get('status', 'Unknown')}"""
        )

    def _format_opponents(self, opponent_profiles: Dict[str, Dict[str, Any]]) -> str:
        """Format opponent profiles for prompt"""
        if not opponent_profiles:
            return "No opponents"

        opponent_lines = []
        for player_id, profile in opponent_profiles.items():
            opponent_lines.append(
                f"- {profile.get('name', 'Unknown')}: "
                f"{profile.get('chips', 0)} chips, "
                f"bet: {profile.get('current_bet', 0)}, "
                f"position: {profile.get('position', 0)}, "
                f"status: {profile.get('status', 'Unknown')}"
            )

        return str("\n".join(opponent_lines))

    def _format_memories(self, memories: List[AgentMemory]) -> str:
        """Format memories for prompt"""
        if not memories:
            return "No relevant memories"

        memory_lines = []
        for memory in memories[:5]:  # Limit to 5 most recent
            memory_lines.append(
                f"- vs {memory.opponent_id}: {memory.action_type.value} "
                f"({memory.amount}) in {memory.phase.value} - {memory.outcome.value if memory.outcome else 'Unknown'}"
            )

        return str("\n".join(memory_lines))
