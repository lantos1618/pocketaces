import re
from typing import Optional, Tuple, Any, Dict
from pydantic import BaseModel, Field, validator
from ...models.agent_models import EmotionState


class ParsedDecision(BaseModel):
    """Structured decision parsed from LLM response"""

    action_type: str = Field(
        ..., description="The poker action (fold, check, call, raise, all_in)"
    )
    amount: Optional[int] = Field(None, description="Amount for raise/all_in actions")
    reasoning: str = Field(
        default="No reasoning provided", description="Explanation for the decision"
    )
    emotion: EmotionState = Field(
        default=EmotionState.CALM, description="Current emotional state"
    )

    @validator("action_type")  # type: ignore[misc]
    def validate_action_type(cls, v: str) -> str:
        valid_actions = ["fold", "check", "call", "raise", "all_in"]
        if v.lower() not in valid_actions:
            raise ValueError(
                f"Invalid action type: {v}. Must be one of {valid_actions}"
            )
        return v.lower()

    @validator("amount")  # type: ignore[misc]
    def validate_amount(cls, v: Optional[int], values: dict[str, Any]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Amount must be non-negative")
        if (
            "action_type" in values
            and values["action_type"] in ["raise", "all_in"]
            and v is None
        ):
            raise ValueError(f'Amount is required for {values["action_type"]} action')
        return v


class DecisionParser:
    """Robust parser for LLM decision responses using multiple strategies"""

    def __init__(self) -> None:
        # Regex patterns for different response formats
        self.patterns = {
            "structured": re.compile(
                r"ACTION:\s*(fold|check|call|raise|all_in)\s*\n"
                r"AMOUNT:\s*(\d+)?\s*\n"
                r"REASONING:\s*(.*?)\s*\n"
                r"EMOTION:\s*(calm|aggressive|defensive|confident|nervous)",
                re.IGNORECASE | re.DOTALL,
            ),
            "inline": re.compile(
                r"ACTION:\s*(fold|check|call|raise|all_in)"
                r"(?:\s+AMOUNT:\s*(\d+))?"
                r"(?:\s+REASONING:\s*(.*?))?"
                r"(?:\s+EMOTION:\s*(calm|aggressive|defensive|confident|nervous))?",
                re.IGNORECASE,
            ),
            "simple": re.compile(r"(fold|check|call|raise|all_in)", re.IGNORECASE),
        }

    def parse(self, response: str) -> ParsedDecision:
        """
        Parse LLM response using multiple strategies for robustness

        Args:
            response: Raw text response from LLM

        Returns:
            ParsedDecision with structured data

        Raises:
            ValueError: If response cannot be parsed
        """
        response = response.strip()

        # Try structured format first (most reliable)
        match = self.patterns["structured"].search(response)
        if match:
            return self._parse_structured_match(match)

        # Try inline format
        match = self.patterns["inline"].search(response)
        if match:
            return self._parse_inline_match(match)

        # Try simple format (just action)
        match = self.patterns["simple"].search(response)
        if match:
            return self._parse_simple_match(match, response)

        # Fallback: try to extract any action from the text
        return self._fallback_parse(response)

    def _parse_structured_match(self, match: re.Match) -> ParsedDecision:
        """Parse structured format match"""
        action_type = match.group(1).lower()
        amount_str = match.group(2)
        reasoning = (
            match.group(3).strip() if match.group(3) else "No reasoning provided"
        )
        emotion_str = match.group(4).lower() if match.group(4) else "calm"

        amount = int(amount_str) if amount_str else None
        emotion = self._parse_emotion(emotion_str)

        return ParsedDecision(
            action_type=action_type, amount=amount, reasoning=reasoning, emotion=emotion
        )

    def _parse_inline_match(self, match: re.Match) -> ParsedDecision:
        """Parse inline format match"""
        action_type = match.group(1).lower()
        amount_str = match.group(2)
        reasoning = (
            match.group(3).strip() if match.group(3) else "No reasoning provided"
        )
        emotion_str = match.group(4).lower() if match.group(4) else "calm"

        amount = int(amount_str) if amount_str else None
        emotion = self._parse_emotion(emotion_str)

        return ParsedDecision(
            action_type=action_type, amount=amount, reasoning=reasoning, emotion=emotion
        )

    def _parse_simple_match(
        self, match: re.Match, full_response: str
    ) -> ParsedDecision:
        """Parse simple format match (just action)"""
        action_type = match.group(1).lower()

        # Try to extract amount from the text
        amount = self._extract_amount_from_text(full_response)

        # Try to extract reasoning from the text
        reasoning = self._extract_reasoning_from_text(full_response)

        # Try to extract emotion from the text
        emotion = self._extract_emotion_from_text(full_response)

        return ParsedDecision(
            action_type=action_type, amount=amount, reasoning=reasoning, emotion=emotion
        )

    def _fallback_parse(self, response: str) -> ParsedDecision:
        """Fallback parsing when no patterns match"""
        # Default to fold if we can't parse anything
        action_type = "fold"

        # Try to extract any action mentioned
        for action in ["fold", "check", "call", "raise", "all_in"]:
            if action.lower() in response.lower():
                action_type = action
                break

        amount = self._extract_amount_from_text(response)
        reasoning = self._extract_reasoning_from_text(response)
        emotion = self._extract_emotion_from_text(response)

        return ParsedDecision(
            action_type=action_type, amount=amount, reasoning=reasoning, emotion=emotion
        )

    def _extract_amount_from_text(self, text: str) -> Optional[int]:
        """Extract amount from text using various patterns"""
        # Look for numbers that could be amounts
        amount_patterns = [
            r"(\d+)\s*chips?",
            r"raise\s+to\s+(\d+)",
            r"bet\s+(\d+)",
            r"amount:\s*(\d+)",
            r"(\d+)\s*dollars?",
        ]

        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue

        return None

    def _extract_reasoning_from_text(self, text: str) -> str:
        """Extract reasoning from text"""
        # Look for reasoning indicators
        reasoning_patterns = [
            r"reasoning:\s*(.*?)(?:\n|$)",
            r"because\s+(.*?)(?:\n|\.)",
            r"since\s+(.*?)(?:\n|\.)",
            r"as\s+(.*?)(?:\n|\.)",
        ]

        for pattern in reasoning_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                reasoning = match.group(1).strip()
                if len(reasoning) > 10:  # Only use if it's substantial
                    return reasoning

        return "No reasoning provided"

    def _extract_emotion_from_text(self, text: str) -> EmotionState:
        """Extract emotion from text"""
        emotion_mapping = {
            "calm": EmotionState.CALM,
            "aggressive": EmotionState.AGGRESSIVE,
            "defensive": EmotionState.DEFENSIVE,
            "confident": EmotionState.CONFIDENT,
            "nervous": EmotionState.NERVOUS,
        }

        text_lower = text.lower()
        for emotion_str, emotion_enum in emotion_mapping.items():
            if emotion_str in text_lower:
                return emotion_enum

        return EmotionState.CALM

    def _parse_emotion(self, emotion_str: str) -> EmotionState:
        """Parse emotion string to enum"""
        emotion_mapping = {
            "calm": EmotionState.CALM,
            "aggressive": EmotionState.AGGRESSIVE,
            "defensive": EmotionState.DEFENSIVE,
            "confident": EmotionState.CONFIDENT,
            "nervous": EmotionState.NERVOUS,
        }

        return emotion_mapping.get(emotion_str.lower(), EmotionState.CALM)
