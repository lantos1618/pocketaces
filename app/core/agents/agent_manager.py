import random
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime

from langchain_mistralai import ChatMistralAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.memory import ConversationBufferMemory
from pydantic import SecretStr

from ...models.game_models import GameState, Player, PlayerAction, ActionType, GamePhase
from ...models.agent_models import (
    AgentPersonality,
    AgentDecision,
    AgentMemory,
    AgentStats,
    PersonalityTrait,
    VoiceStyle,
    EmotionState,
    AgentBehavior,
    AgentContext,
)
from ...store.game_store import game_store
from ..game.poker_engine import poker_engine

# Import specialized services
from .prompt_builder import PromptBuilder
from .decision_parser import DecisionParser
from .behavior_updater import BehaviorUpdater
from .voice_generator import VoiceLineGenerator


class AgentManager:
    """Manages AI agents and their decision-making with LangChain integration"""

    def __init__(self) -> None:
        """Initialize the agent manager."""
        self.llm: Optional[ChatMistralAI] = None
        self.agent_memories: Dict[str, Any] = {}

        # Initialize specialized services
        self.prompt_builder = PromptBuilder()
        self.decision_parser = DecisionParser()
        self.behavior_updater = BehaviorUpdater()
        self.voice_generator = VoiceLineGenerator()

    async def initialize_llm(self, api_key: str) -> None:
        """Initialize LangChain LLM with Mistral."""
        try:
            self.llm = ChatMistralAI(
                api_key=SecretStr(api_key),
                model_name="mistral-large-latest",
                temperature=0.7,
            )
            print("LangChain LLM initialized successfully with Mistral")
        except Exception as e:
            print(f"Failed to initialize LangChain LLM: {e}")
            self.llm = None

    async def make_agent_decision(
        self, agent_id: str, game_state: GameState, player: Player
    ) -> AgentDecision:
        """Make a decision for an AI agent"""

        # Get agent personality and behavior
        personality = game_store.get_agent_personality(agent_id)
        if not personality:
            raise ValueError(f"Agent {agent_id} not found")

        behavior = self.behavior_updater.get_behavior(agent_id)
        if not behavior:
            behavior = self.behavior_updater.create_behavior(agent_id)

        # Build context
        context = self._build_agent_context(
            agent_id, game_state, player, personality, behavior
        )

        # Get relevant memories
        memories = game_store.get_agent_memories(agent_id)

        # Make decision using specialized services
        if self.llm:
            decision = await self._langchain_decision(
                context, memories, personality, behavior
            )
        else:
            decision = self._rule_based_decision(
                context, memories, personality, behavior
            )

        # Update behavior using specialized service
        self.behavior_updater.update_behavior(agent_id, decision, game_state)

        # Generate voice line using specialized service
        voice_line = self.voice_generator.generate_voice_line(
            personality, decision, behavior
        )
        decision.voice_line = voice_line

        return decision

    def _build_agent_context(
        self,
        agent_id: str,
        game_state: GameState,
        player: Player,
        personality: AgentPersonality,
        behavior: AgentBehavior,
    ) -> AgentContext:
        """Build context for agent decision making"""

        # Get opponent profiles
        opponent_profiles = {}
        for p in game_state.players:
            if p.id != agent_id:
                opponent_profiles[p.id] = {
                    "name": p.name,
                    "chips": p.chips,
                    "current_bet": p.current_bet,
                    "position": p.position,
                    "hole_cards": [str(card) for card in p.hole_cards],
                    "status": p.status,
                }

        # Get relevant memories
        memories = game_store.get_agent_memories(agent_id)

        # Calculate pot odds and position
        call_amount = game_state.current_bet - player.current_bet
        pot_odds = (
            call_amount / (game_state.pot + call_amount) if call_amount > 0 else 0
        )
        position = (
            "early"
            if player.position <= 1
            else "late"
            if player.position >= 2
            else "middle"
        )
        stack_to_pot = player.chips / game_state.pot if game_state.pot > 0 else 0

        # Get available actions
        available_actions = self._get_available_actions(player, game_state)

        return AgentContext(
            agent_id=agent_id,
            game_state={
                "game_id": game_state.game_id,
                "phase": game_state.phase.value,
                "pot": game_state.pot,
                "current_bet": game_state.current_bet,
                "min_raise": game_state.min_raise,
                "community_cards": [str(card) for card in game_state.community_cards],
                "dealer_index": game_state.dealer_index,
            },
            player_state={
                "chips": player.chips,
                "current_bet": player.current_bet,
                "position": player.position,
                "hole_cards": [str(card) for card in player.hole_cards],
                "status": player.status,
            },
            recent_memories=memories,
            opponent_profiles=opponent_profiles,
            current_emotion=behavior.current_emotion,
            available_actions=available_actions,
            pot_odds=pot_odds,
            position=position,
            stack_to_pot_ratio=stack_to_pot,
        )

    def _get_available_actions(
        self, player: Player, game_state: GameState
    ) -> List[str]:
        """Get available actions for the player."""
        actions: List[str] = []

        if player.status == "folded":
            return actions

        call_amount = game_state.current_bet - player.current_bet

        if call_amount == 0:
            actions.extend(["check", "raise"])
        else:
            actions.extend(["fold", "call"])
            if player.chips > call_amount:
                actions.append("raise")

        if player.chips > 0:
            actions.append("all_in")

        return actions

    async def _langchain_decision(
        self,
        context: AgentContext,
        memories: List[AgentMemory],
        personality: AgentPersonality,
        behavior: AgentBehavior,
    ) -> AgentDecision:
        """Use LangChain to make a sophisticated decision"""

        if not self.llm:
            return self._rule_based_decision(context, memories, personality, behavior)

        # Use PromptBuilder to build the prompt
        prompt = self.prompt_builder.build(personality, context, memories, behavior)

        # Get conversation history
        memory = self.agent_memories.get(context.agent_id)
        chat_history = memory.chat_memory.messages if memory else []

        # Create messages
        messages = [
            SystemMessage(content=prompt),
            *chat_history,
            HumanMessage(
                content="Make your poker decision now. Consider your personality, the current situation, and your memories."
            ),
        ]

        try:
            response = await self.llm.agenerate([messages])
            decision_text = response.generations[0][0].text

            # Use DecisionParser to parse the response
            parsed_decision = self.decision_parser.parse(decision_text)

            # Create the decision
            decision = self._create_agent_decision(
                agent_id=context.agent_id,
                game_id=context.game_state.get("game_id", ""),
                action_type=parsed_decision.action_type,
                amount=parsed_decision.amount,
                reasoning=parsed_decision.reasoning,
                confidence=random.uniform(
                    0.6, 0.9
                ),  # LLM decisions are generally more confident
            )

            # Set emotion from parsed decision
            decision.emotion_state = parsed_decision.emotion

            return decision

        except Exception as e:
            print(f"LangChain decision failed: {e}")
            return self._rule_based_decision(context, memories, personality, behavior)

    def _rule_based_decision(
        self,
        context: AgentContext,
        memories: List[AgentMemory],
        personality: AgentPersonality,
        behavior: AgentBehavior,
    ) -> AgentDecision:
        """Make decision using rule-based logic when LLM is unavailable"""

        chips = context.player_state["chips"]
        current_bet = context.game_state["current_bet"]
        player_bet = context.player_state["current_bet"]
        pot = context.game_state["pot"]
        phase = context.game_state["phase"]
        available_actions = context.available_actions

        # Apply personality modifiers
        aggression = personality.aggression_level * behavior.aggression_modifier
        bluff_freq = personality.bluff_frequency * behavior.bluff_modifier

        # Apply tilt effects
        if behavior.tilt_level > 0.7:
            aggression *= 1.5
            bluff_freq *= 1.3

        # Decision logic
        if "check" in available_actions:
            if random.random() < aggression * 0.6:
                action_type = "raise"
                amount = min(chips, pot // 2)
            else:
                action_type = "check"
                amount = None
        else:
            # Must call or raise
            call_amount = current_bet - player_bet

            if random.random() < aggression:
                if random.random() < bluff_freq:
                    # Bluff
                    action_type = "raise"
                    amount = min(chips, current_bet * 2)
                else:
                    # Value bet
                    action_type = "call" if random.random() < 0.7 else "raise"
                    amount = (
                        current_bet
                        if action_type == "call"
                        else min(chips, current_bet * 1.5)
                    )
            else:
                # Conservative play
                if (
                    context.pot_odds < 0.3
                    or random.random() < personality.risk_tolerance
                ):
                    action_type = "call"
                    amount = current_bet
                else:
                    action_type = "fold"
                    amount = None

        reasoning = f"Based on {personality.name}'s {personality.traits[0].value} personality and current situation"

        return self._create_agent_decision(
            agent_id=context.agent_id,
            game_id=context.game_state.get("game_id", ""),
            action_type=action_type,
            amount=amount,
            reasoning=reasoning,
            confidence=random.uniform(0.5, 0.8),
        )

    def record_memory(
        self,
        agent_id: str,
        game_id: str,
        opponent_id: str,
        action: PlayerAction,
        phase: GamePhase,
        outcome: Optional[str] = None,
    ) -> None:
        """Record a memory for an agent."""
        from ...models.agent_models import (
            ActionTypeStr,
            GamePhaseStr,
            OutcomeStr,
            PositionStr,
        )

        # Convert enum values to strings for the memory
        action_type_str = ActionTypeStr(action.action_type.value)
        phase_str = GamePhaseStr(phase.value)
        outcome_str = OutcomeStr(outcome) if outcome else None

        memory = AgentMemory(
            agent_id=agent_id,
            opponent_id=opponent_id,
            game_id=game_id,
            action_type=action_type_str,
            amount=action.amount,
            phase=phase_str,
            outcome=outcome_str,
            pot_size=0,  # Will be updated from game state
            position=PositionStr.MIDDLE,  # Will be calculated
            importance=0.5,  # Will be calculated based on outcome
        )

        game_store.add_agent_memory(memory)

    def get_agent_behavior(self, agent_id: str) -> Optional[AgentBehavior]:
        """Get agent behavior by ID."""
        return self.behavior_updater.get_behavior(agent_id)

    def reset_agent_behavior(self, agent_id: str) -> None:
        """Reset agent behavior to default state."""
        self.behavior_updater.reset_behavior(agent_id)

    def _create_agent_decision(
        self,
        agent_id: str,
        game_id: str,
        action_type: str,
        amount: Optional[int] = None,
        reasoning: str = "",
        confidence: float = 0.5,
    ) -> AgentDecision:
        """Create an agent decision with proper type conversion."""
        from ...models.agent_models import ActionTypeStr

        return AgentDecision(
            agent_id=agent_id,
            game_id=game_id,
            action_type=ActionTypeStr(action_type),
            amount=amount,
            reasoning=reasoning,
            confidence=confidence,
            emotion_state=EmotionState.CALM,
        )


# Global agent manager instance
agent_manager = AgentManager()
