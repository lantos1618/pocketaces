import random
import asyncio
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import openai
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

from ...models.game_models import GameState, Player, PlayerAction, ActionType, GamePhase
from ...models.agent_models import (
    AgentPersonality, AgentDecision, AgentMemory, AgentStats,
    PersonalityTrait, VoiceStyle, EmotionState, AgentBehavior, AgentContext
)
from ...store.game_store import game_store
from ..game.poker_engine import poker_engine

class AgentManager:
    """Manages AI agents and their decision-making with LangChain integration"""
    
    def __init__(self) -> None:
        """Initialize the agent manager."""
        self.llm: Optional[Any] = None  # Will be ChatOpenAI when initialized
        self.agent_behaviors: Dict[str, AgentBehavior] = {}
        self.agent_memories: Dict[str, Any] = {}
        self._initialize_agents()
    
    def _initialize_agents(self) -> None:
        """Initialize available agents."""
        # This will be populated from the game store
        pass
    
    async def initialize_llm(self, api_key: str) -> None:
        """Initialize LangChain LLM with OpenAI."""
        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import SystemMessage, HumanMessage
            
            self.llm = ChatOpenAI(
                model="gpt-4",
                temperature=0.7,
                api_key=api_key
            )
            print("LangChain LLM initialized successfully")
        except Exception as e:
            print(f"Failed to initialize LangChain LLM: {e}")
            self.llm = None
    
    async def make_agent_decision(
        self, 
        agent_id: str, 
        game_state: GameState, 
        player: Player
    ) -> AgentDecision:
        """Make a decision for an AI agent"""
        
        # Get agent personality and behavior
        personality = game_store.get_agent_personality(agent_id)
        if not personality:
            raise ValueError(f"Agent {agent_id} not found")
        
        behavior = self.get_agent_behavior(agent_id)
        if not behavior:
            behavior = AgentBehavior(agent_id=agent_id)
            self.agent_behaviors[agent_id] = behavior
        
        # Build context
        context = self._build_agent_context(agent_id, game_state, player, personality, behavior)
        
        # Get relevant memories
        memories = game_store.get_agent_memories(agent_id)
        
        # Make decision
        if self.llm:
            decision = await self._langchain_decision(context, memories, personality, behavior)
        else:
            decision = self._rule_based_decision(context, memories, personality, behavior)
        
        # Update behavior based on decision
        self._update_agent_behavior(agent_id, decision, game_state)
        
        # Generate voice line
        voice_line = self._generate_voice_line(personality, decision, behavior)
        decision.voice_line = voice_line
        
        return decision
    
    def _build_agent_context(
        self, 
        agent_id: str, 
        game_state: GameState, 
        player: Player, 
        personality: AgentPersonality,
        behavior: AgentBehavior
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
                    "status": p.status
                }
        
        # Get relevant memories
        memories = game_store.get_agent_memories(agent_id)
        
        # Calculate pot odds and position
        call_amount = game_state.current_bet - player.current_bet
        pot_odds = call_amount / (game_state.pot + call_amount) if call_amount > 0 else 0
        position = "early" if player.position <= 1 else "late" if player.position >= 2 else "middle"
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
                "dealer_index": game_state.dealer_index
            },
            player_state={
                "chips": player.chips,
                "current_bet": player.current_bet,
                "position": player.position,
                "hole_cards": [str(card) for card in player.hole_cards],
                "status": player.status
            },
            recent_memories=memories,
            opponent_profiles=opponent_profiles,
            current_emotion=behavior.current_emotion,
            available_actions=available_actions,
            pot_odds=pot_odds,
            position=position,
            stack_to_pot_ratio=stack_to_pot
        )
    
    def _get_available_actions(self, player: Player, game_state: GameState) -> List[str]:
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
        behavior: AgentBehavior
    ) -> AgentDecision:
        """Use LangChain to make a sophisticated decision"""
        
        if not self.llm:
            return self._rule_based_decision(context, memories, personality, behavior)
        
        # Build system prompt
        system_prompt = self._build_langchain_prompt(personality, context, memories, behavior)
        
        # Get conversation history
        memory = self.agent_memories.get(context.agent_id)
        chat_history = memory.chat_memory.messages if memory else []
        
        # Create messages
        messages = [
            SystemMessage(content=system_prompt),
            *chat_history,
            HumanMessage(content="Make your poker decision now. Consider your personality, the current situation, and your memories.")
        ]
        
        try:
            response = await self.llm.agenerate([messages])
            decision_text = response.generations[0][0].text
            
            # Parse the decision
            action_type, amount, reasoning, emotion = self._parse_langchain_response(decision_text)
            
            # Update memory
            if memory:
                memory.chat_memory.add_user_message("Make your poker decision now.")
                memory.chat_memory.add_ai_message(decision_text)
            
            return self._create_agent_decision(
                agent_id=context.agent_id,
                game_id=context.game_state.get("game_id", ""),
                action_type=action_type,
                amount=amount,
                reasoning=reasoning,
                confidence=random.uniform(0.6, 0.9)
            )
            
        except Exception as e:
            print(f"LangChain decision failed: {e}")
            return self._rule_based_decision(context, memories, personality, behavior)
    
    def _build_langchain_prompt(
        self, 
        personality: AgentPersonality, 
        context: AgentContext,
        memories: List[AgentMemory],
        behavior: AgentBehavior
    ) -> str:
        """Build comprehensive prompt for LangChain"""
        
        prompt = f"""You are {personality.name}, a poker player with a distinct personality:

PERSONALITY:
- Traits: {', '.join([t.value for t in personality.traits])}
- Aggression Level: {personality.aggression_level} (0=passive, 1=aggressive)
- Bluff Frequency: {personality.bluff_frequency} (0=never bluff, 1=always bluff)
- Risk Tolerance: {personality.risk_tolerance} (0=conservative, 1=reckless)
- Patience Level: {personality.patience_level} (0=impatient, 1=very patient)
- Voice Style: {personality.voice_style.value}

CURRENT STATE:
- Emotion: {behavior.current_emotion.value}
- Confidence: {behavior.confidence_level}
- Tilt Level: {behavior.tilt_level}
- Recent Actions: {', '.join(behavior.recent_actions[-3:])}

GAME SITUATION:
- Phase: {context.game_state['phase']}
- Pot: {context.game_state['pot']} chips
- Current Bet: {context.game_state['current_bet']} chips
- Your Chips: {context.player_state['chips']} chips
- Your Bet: {context.player_state['current_bet']} chips
- Position: {context.position}
- Stack to Pot Ratio: {context.stack_to_pot_ratio:.2f}
- Pot Odds: {context.pot_odds:.2f}
- Community Cards: {context.game_state['community_cards']}
- Your Hole Cards: {context.player_state['hole_cards']}
- Available Actions: {', '.join(context.available_actions)}

OPPONENTS:
{self._format_opponents(context.opponent_profiles)}

RELEVANT MEMORIES:
{self._format_memories(memories)}

DECISION INSTRUCTIONS:
1. Consider your personality traits and current emotional state
2. Analyze the pot odds and your position
3. Use your memories to inform your decision
4. Choose from available actions: {', '.join(context.available_actions)}
5. If raising, specify an amount within your chip limit

Respond in this exact format:
ACTION: [action_type]
AMOUNT: [amount if raising]
REASONING: [your detailed reasoning]
EMOTION: [your emotional state after this decision]

Make your decision based on your unique personality and the current situation."""

        return prompt
    
    def _format_opponents(self, opponent_profiles: Dict[str, Dict[str, Any]]) -> str:
        """Format opponent information for prompt"""
        if not opponent_profiles:
            return "No opponents information available."
        
        formatted = []
        for opp_id, profile in opponent_profiles.items():
            formatted.append(f"- {profile['name']}: {profile['chips']} chips, bet: {profile['current_bet']}, status: {profile['status']}")
        
        return "\n".join(formatted)
    
    def _format_memories(self, memories: List[AgentMemory]) -> str:
        """Format memories for prompt"""
        if not memories:
            return "No relevant memories."
        
        formatted = []
        for memory in memories[-3:]:  # Last 3 memories
            formatted.append(f"- {memory.get_memory_summary()}")
        
        return "\n".join(formatted)
    
    def _parse_langchain_response(self, response: str) -> Tuple[str, Optional[int], str, EmotionState]:
        """Parse LangChain response to extract decision"""
        lines = response.strip().split('\n')
        action_type = "fold"  # Default
        amount = None
        reasoning = "No reasoning provided"
        emotion = EmotionState.CALM
        
        for line in lines:
            if line.startswith("ACTION:"):
                action_type = line.split(":", 1)[1].strip().lower()
            elif line.startswith("AMOUNT:"):
                amount_str = line.split(":", 1)[1].strip()
                try:
                    amount = int(amount_str)
                except ValueError:
                    amount = None
            elif line.startswith("REASONING:"):
                reasoning = line.split(":", 1)[1].strip()
            elif line.startswith("EMOTION:"):
                emotion_str = line.split(":", 1)[1].strip().lower()
                try:
                    emotion = EmotionState(emotion_str)
                except ValueError:
                    emotion = EmotionState.CALM
        
        return action_type, amount, reasoning, emotion
    
    def _rule_based_decision(
        self, 
        context: AgentContext, 
        memories: List[AgentMemory],
        personality: AgentPersonality,
        behavior: AgentBehavior
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
                    amount = current_bet if action_type == "call" else min(chips, current_bet * 1.5)
            else:
                # Conservative play
                if context.pot_odds < 0.3 or random.random() < personality.risk_tolerance:
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
            confidence=random.uniform(0.5, 0.8)
        )
    
    def _update_agent_behavior(self, agent_id: str, decision: AgentDecision, game_state: GameState) -> None:
        """Update agent behavior based on decision."""
        behavior = self.get_agent_behavior(agent_id)
        if not behavior:
            return
        
        # Update emotion based on decision
        if decision.action_type in ["raise", "all_in"]:
            behavior.update_emotion(EmotionState.AGGRESSIVE)
        elif decision.action_type == "fold":
            behavior.update_emotion(EmotionState.DEFENSIVE)
        elif decision.confidence > 0.8:
            behavior.update_emotion(EmotionState.CONFIDENT)
        else:
            behavior.update_emotion(EmotionState.CALM)
        
        # Add action to history
        behavior.add_action(decision.action_type)
        
        # Update confidence
        behavior.confidence_level = decision.confidence
    
    def _generate_voice_line(self, personality: AgentPersonality, decision: AgentDecision, behavior: AgentBehavior) -> str:
        """Generate a voice line based on personality and decision"""
        
        # Get base reaction
        reaction = personality.get_reaction(decision.emotion_state)
        if reaction:
            return reaction
        
        # Get catchphrase or taunt
        if decision.action_type in ["raise", "all_in"] and random.random() < 0.3:
            taunt = personality.get_random_taunt()
            if taunt:
                return taunt
        
        if random.random() < 0.2:
            catchphrase = personality.get_random_catchphrase()
            if catchphrase:
                return catchphrase
        
        # Generate contextual line
        if decision.action_type == "fold":
            return f"I'll fold this one."
        elif decision.action_type == "check":
            return f"I'll check."
        elif decision.action_type == "call":
            return f"I'll call."
        elif decision.action_type == "raise":
            return f"I raise to {decision.amount}."
        elif decision.action_type == "all_in":
            return "All in!"
        
        return "My move."
    
    def record_memory(
        self, 
        agent_id: str, 
        game_id: str, 
        opponent_id: str, 
        action: PlayerAction, 
        phase: GamePhase, 
        outcome: Optional[str] = None
    ) -> None:
        """Record a memory for an agent."""
        from ...models.agent_models import ActionTypeStr, GamePhaseStr, OutcomeStr, PositionStr
        
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
            importance=0.5  # Will be calculated based on outcome
        )
        
        game_store.add_agent_memory(memory)
    
    def get_agent_behavior(self, agent_id: str) -> Optional[AgentBehavior]:
        """Get agent behavior by ID."""
        return self.agent_behaviors.get(agent_id)
    
    def reset_agent_behavior(self, agent_id: str) -> None:
        """Reset agent behavior to default state."""
        if agent_id in self.agent_behaviors:
            del self.agent_behaviors[agent_id]

    def _create_agent_decision(
        self, 
        agent_id: str, 
        game_id: str, 
        action_type: str, 
        amount: Optional[int] = None,
        reasoning: str = "",
        confidence: float = 0.5
    ) -> AgentDecision:
        """Create an agent decision with proper type conversion."""
        from ...models.agent_models import ActionTypeStr
        
        # Convert string to enum
        action_enum = ActionTypeStr(action_type)
        
        return AgentDecision(
            agent_id=agent_id,
            game_id=game_id,
            action_type=action_enum,
            amount=amount,
            reasoning=reasoning,
            confidence=confidence
        )

# Global agent manager instance
agent_manager = AgentManager() 