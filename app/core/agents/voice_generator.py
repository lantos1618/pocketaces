import random
from typing import Optional
from ...models.agent_models import (
    AgentPersonality,
    AgentDecision,
    AgentBehavior,
    EmotionState,
)


class VoiceLineGenerator:
    """Generates voice lines for agents based on personality and context"""

    def __init__(self) -> None:
        # Default voice lines for different actions
        self.default_voice_lines = {
            "fold": [
                "I'll fold this one.",
                "Not this time.",
                "I'm out.",
                "Too rich for my blood.",
                "I'll pass.",
            ],
            "check": [
                "I'll check.",
                "Checking.",
                "I'll see what happens.",
                "Let's see what you've got.",
                "Checking to you.",
            ],
            "call": [
                "I'll call.",
                "Calling.",
                "I'm in.",
                "Let's see the next card.",
                "I'll match that.",
            ],
            "raise": [
                "I raise.",
                "Raising the stakes.",
                "Let's make this interesting.",
                "I'll raise you.",
                "Time to put some pressure on.",
            ],
            "all_in": [
                "All in!",
                "Everything I've got!",
                "Let's do this!",
                "All or nothing!",
                "I'm going for it!",
            ],
        }

        # Emotional voice lines
        self.emotional_lines = {
            EmotionState.CONFIDENT: [
                "I've got this.",
                "This is my hand.",
                "I can feel it.",
                "The cards are with me.",
                "I'm feeling lucky.",
            ],
            EmotionState.NERVOUS: [
                "I'm not sure about this...",
                "This is risky...",
                "I hope this works...",
                "I'm a bit worried...",
                "This could go either way...",
            ],
            EmotionState.EXCITED: [
                "This is exciting!",
                "I love this game!",
                "Let's make it interesting!",
                "This is what I live for!",
                "I'm pumped!",
            ],
            EmotionState.FRUSTRATED: [
                "This is getting ridiculous.",
                "I can't catch a break.",
                "What is going on?",
                "This is frustrating.",
                "I need a change of luck.",
            ],
            EmotionState.CALM: [
                "I'm staying calm.",
                "No rush.",
                "I'll take my time.",
                "Steady as she goes.",
                "I'm in control.",
            ],
            EmotionState.AGGRESSIVE: [
                "I'm coming for you!",
                "You're going down!",
                "I'm not backing down!",
                "Let's see what you're made of!",
                "I'm taking control!",
            ],
            EmotionState.DEFENSIVE: [
                "I need to be careful.",
                "I'm playing it safe.",
                "I can't afford to lose more.",
                "I'll wait for a better hand.",
                "I'm being defensive.",
            ],
        }

    def generate_voice_line(
        self,
        personality: AgentPersonality,
        decision: AgentDecision,
        behavior: AgentBehavior,
    ) -> str:
        """Generate a voice line based on personality, decision, and behavior"""

        # First, try to get a personality-specific reaction
        reaction = personality.get_reaction(decision.emotion_state)
        if reaction:
            return reaction

        # Try to get a catchphrase or taunt based on action
        if decision.action_type.value in ["raise", "all_in"] and random.random() < 0.3:
            taunt = personality.get_random_taunt()
            if taunt:
                return taunt

        # Try to get a catchphrase
        if random.random() < 0.2:
            catchphrase = personality.get_random_catchphrase()
            if catchphrase:
                return catchphrase

        # Generate contextual line based on action
        action_line = self._get_action_based_line(decision)
        if action_line:
            return action_line

        # Fall back to emotional line
        emotional_line = self._get_emotional_line(behavior.current_emotion)
        if emotional_line:
            return emotional_line

        # Ultimate fallback
        return "My move."

    def _get_action_based_line(self, decision: AgentDecision) -> Optional[str]:
        """Get a voice line based on the action type"""
        action_type = decision.action_type.value

        if action_type in self.default_voice_lines:
            base_line = random.choice(self.default_voice_lines[action_type])

            # Add amount information for raise/all_in
            if action_type in ["raise", "all_in"] and decision.amount:
                if action_type == "raise":
                    return f"{base_line} {decision.amount} chips."
                else:
                    return f"{base_line} {decision.amount} chips!"

            return base_line

        return None

    def _get_emotional_line(self, emotion: EmotionState) -> Optional[str]:
        """Get a voice line based on emotional state"""
        if emotion in self.emotional_lines:
            return random.choice(self.emotional_lines[emotion])

        return None

    def generate_taunt(
        self, personality: AgentPersonality, target_player: str, context: str = ""
    ) -> str:
        """Generate a taunt for another player"""
        if personality.taunts:
            taunt = random.choice(personality.taunts)
            return f"Hey {target_player}, {taunt}"

        # Default taunts
        default_taunts = [
            f"Hey {target_player}, are you sure about that?",
            f"Nice try, {target_player}, but I've seen better.",
            f"{target_player}, you're making this too easy.",
            f"I hope you're ready to lose, {target_player}.",
            f"{target_player}, you might want to fold now.",
        ]

        return random.choice(default_taunts)

    def generate_reaction(
        self, personality: AgentPersonality, event: str, emotion: EmotionState
    ) -> str:
        """Generate a reaction to a game event"""
        # Try personality-specific reaction first
        reaction = personality.get_reaction(emotion)
        if reaction:
            return reaction

        # Default reactions based on event and emotion
        default_reactions = {
            "win": {
                EmotionState.EXCITED: "Yes! I knew it!",
                EmotionState.CONFIDENT: "As expected.",
                EmotionState.CALM: "Good hand.",
            },
            "lose": {
                EmotionState.FRUSTRATED: "Unbelievable!",
                EmotionState.NERVOUS: "I should have known...",
                EmotionState.CALM: "Well played.",
            },
            "bluff_success": {
                EmotionState.EXCITED: "Got you!",
                EmotionState.CONFIDENT: "That's how it's done.",
                EmotionState.AGGRESSIVE: "I own this table!",
            },
            "bluff_fail": {
                EmotionState.FRUSTRATED: "Damn it!",
                EmotionState.NERVOUS: "I shouldn't have...",
                EmotionState.DEFENSIVE: "I need to be more careful.",
            },
        }

        if event in default_reactions and emotion in default_reactions[event]:
            return default_reactions[event][emotion]

        # Fallback to emotional line
        return self._get_emotional_line(emotion) or "Interesting."

    def generate_celebration(self, personality: AgentPersonality, pot_size: int) -> str:
        """Generate a celebration line for winning a pot"""
        if personality.catchphrases:
            catchphrase = random.choice(personality.catchphrases)
            return f"{catchphrase} {pot_size} chips!"

        # Default celebrations
        default_celebrations = [
            f"Winner winner! {pot_size} chips!",
            f"That's {pot_size} chips in my pocket!",
            f"Beautiful! {pot_size} chips!",
            f"I'll take those {pot_size} chips!",
            f"Another pot for me! {pot_size} chips!",
        ]

        return random.choice(default_celebrations)
