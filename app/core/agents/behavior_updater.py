from typing import Dict, Optional
from ...models.agent_models import AgentBehavior, AgentDecision, EmotionState
from ...models.game_models import GameState


class BehaviorUpdater:
    """Manages agent behavior state and updates"""

    def __init__(self) -> None:
        self.behaviors: Dict[str, AgentBehavior] = {}

    def get_behavior(self, agent_id: str) -> Optional[AgentBehavior]:
        """Get agent behavior by ID"""
        return self.behaviors.get(agent_id)

    def create_behavior(self, agent_id: str) -> AgentBehavior:
        """Create a new behavior for an agent"""
        behavior = AgentBehavior(agent_id=agent_id)
        self.behaviors[agent_id] = behavior
        return behavior

    def update_behavior(
        self, agent_id: str, decision: AgentDecision, game_state: GameState
    ) -> None:
        """Update agent behavior based on decision and game state"""
        behavior = self.get_behavior(agent_id)
        if not behavior:
            behavior = self.create_behavior(agent_id)

        # Update emotion based on decision
        self._update_emotion(behavior, decision)

        # Update aggression modifier based on recent actions
        self._update_aggression_modifier(behavior, decision)

        # Update bluff modifier based on success/failure
        self._update_bluff_modifier(behavior, decision, game_state)

        # Update tilt level based on game outcomes
        self._update_tilt_level(behavior, decision, game_state)

        # Add action to history
        behavior.add_action(decision.action_type.value)

        # Update confidence level
        behavior.confidence_level = decision.confidence

    def _update_emotion(self, behavior: AgentBehavior, decision: AgentDecision) -> None:
        """Update emotion based on decision type"""
        match decision.action_type.value:
            case "raise" | "all_in":
                behavior.update_emotion(EmotionState.AGGRESSIVE)
            case "fold":
                behavior.update_emotion(EmotionState.DEFENSIVE)
            case _:
                if decision.confidence > 0.8:
                    behavior.update_emotion(EmotionState.CONFIDENT)
                elif decision.confidence < 0.3:
                    behavior.update_emotion(EmotionState.NERVOUS)
                else:
                    behavior.update_emotion(EmotionState.CALM)

    def _update_aggression_modifier(
        self, behavior: AgentBehavior, decision: AgentDecision
    ) -> None:
        """Update aggression modifier based on recent actions"""
        recent_actions = behavior.recent_actions[-5:]  # Last 5 actions

        aggressive_actions = sum(
            1 for action in recent_actions if action in ["raise", "all_in"]
        )
        passive_actions = sum(
            1 for action in recent_actions if action in ["fold", "check"]
        )

        match (aggressive_actions, passive_actions):
            case (a, p) if a > p:
                behavior.aggression_modifier = min(
                    1.5, behavior.aggression_modifier + 0.1
                )
            case (a, p) if p > a:
                behavior.aggression_modifier = max(
                    0.5, behavior.aggression_modifier - 0.1
                )
            case _:
                # Gradually return to baseline
                if behavior.aggression_modifier > 1.0:
                    behavior.aggression_modifier = max(
                        1.0, behavior.aggression_modifier - 0.05
                    )
                elif behavior.aggression_modifier < 1.0:
                    behavior.aggression_modifier = min(
                        1.0, behavior.aggression_modifier + 0.05
                    )

    def _update_bluff_modifier(
        self, behavior: AgentBehavior, decision: AgentDecision, game_state: GameState
    ) -> None:
        """Update bluff modifier based on bluff success/failure"""
        # This would need game outcome data to be truly effective
        # For now, we'll use a simple heuristic based on action patterns

        recent_actions = behavior.recent_actions[-3:]  # Last 3 actions

        # If agent has been raising frequently, adjust bluff modifier
        raise_count = sum(1 for action in recent_actions if action == "raise")

        if raise_count >= 2:
            # High raise frequency might indicate successful bluffing
            behavior.bluff_modifier = min(1.3, behavior.bluff_modifier + 0.1)
        else:
            # Gradually return to baseline
            if behavior.bluff_modifier > 1.0:
                behavior.bluff_modifier = max(1.0, behavior.bluff_modifier - 0.05)

    def _update_tilt_level(
        self, behavior: AgentBehavior, decision: AgentDecision, game_state: GameState
    ) -> None:
        """Update tilt level based on game outcomes and decisions"""
        # Increase tilt if agent is losing chips frequently
        recent_actions = behavior.recent_actions[-5:]

        fold_count = sum(1 for action in recent_actions if action == "fold")
        aggressive_count = sum(
            1 for action in recent_actions if action in ["raise", "all_in"]
        )

        # High fold rate after aggressive plays might indicate tilt
        if fold_count > aggressive_count and aggressive_count > 0:
            behavior.tilt_level = min(1.0, behavior.tilt_level + 0.2)
        else:
            # Gradually reduce tilt
            behavior.tilt_level = max(0.0, behavior.tilt_level - 0.1)

    def reset_behavior(self, agent_id: str) -> None:
        """Reset agent behavior to default state"""
        if agent_id in self.behaviors:
            del self.behaviors[agent_id]

    def get_all_behaviors(self) -> Dict[str, AgentBehavior]:
        """Get all agent behaviors"""
        return self.behaviors.copy()
