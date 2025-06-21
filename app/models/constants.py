"""
Constants for ElevenLabs voice configurations
"""

from typing import Dict, List, Optional

# ElevenLabs Voice Configurations
ELEVENLABS_VOICES = [
    {
        "name": "Aria",
        "id": "9BWtsMINqrJLrRacOk9x",
        "description": "A middle-aged female with an African-American accent, suited for clear and authoritative delivery",
        "accent": "American",
        "category": "Informative & Educational",
    },
    {
        "name": "Sarah",
        "id": "EXAVITQu4vr4xnSDxMaL",
        "description": "Young adult woman with a confident and warm, expressive tone",
        "accent": "American",
        "category": "Entertainment & TV",
    },
    {
        "name": "Laura",
        "id": "FGY2WhTYpPnrIDTdsKH5",
        "description": "This young adult female voice delivers sunny, upbeat narration",
        "accent": "American",
        "category": "Social Media",
    },
    {
        "name": "Charlie",
        "id": "IKne3meq5aSn9XLyUdCD",
        "description": "A young Australian male with a confident and casual tone",
        "accent": "Australian",
        "category": "Conversational",
    },
    {
        "name": "George",
        "id": "JBFqnCBsd6RMkjVDRZzb",
        "description": "Warm resonance that instantly captivates listeners",
        "accent": "British",
        "category": "Narrative & Story",
    },
    {
        "name": "Callum",
        "id": "N2lVS1w4EtoT3dr4eOWO",
        "description": "Deceptively gravelly, yet unsettling edge",
        "accent": "American",
        "category": "Not specified",
    },
    {
        "name": "River",
        "id": "SAz9YHcvj6GT2YYXdXww",
        "description": "A relaxed, neutral voice ready for narrations or casual conversation",
        "accent": "American",
        "category": "Conversational",
    },
    {
        "name": "Liam",
        "id": "TX3LPaxmHKxFdv7VOQHJ",
        "description": "A young adult with energy and warmth – suitable for social platforms",
        "accent": "American",
        "category": "Social Media",
    },
    {
        "name": "Charlotte",
        "id": "XB0fDUnXU5powFXDhCwa",
        "description": "Sensual and raspy, she's ready to voice your character roles",
        "accent": "Swedish",
        "category": "Characters & Animation",
    },
    {
        "name": "Alice",
        "id": "Xb7hH8MSUJpSbSDYk0k2",
        "description": "Clear and engaging, friendly woman with a British accent – ideal for advertising",
        "accent": "British",
        "category": "Advertisement",
    },
    {
        "name": "Matilda",
        "id": "XrExE9yKIg1WjnnlVkGX",
        "description": "A professional woman with a pleasing alto pitch – suitable for training and narration",
        "accent": "American",
        "category": "Informative & Educational",
    },
]

# Voice ID mappings for agent personalities
AGENT_VOICE_MAPPINGS = {
    "the_rock": "JBFqnCBsd6RMkjVDRZzb",  # George - British, warm resonance
    "the_maniac": "IKne3meq5aSn9XLyUdCD",  # Charlie - Australian, confident and casual
    "the_shark": "XrExE9yKIg1WjnnlVkGX",  # Matilda - American, professional alto
    "the_fish": "SAz9YHcvj6GT2YYXdXww",  # River - American, relaxed and neutral
    "the_bluffer": "N2lVS1w4EtoT3dr4eOWO",  # Callum - American, gravelly and unsettling
    "the_queen": "XB0fDUnXU5powFXDhCwa",  # Charlotte - Swedish, sensual and raspy
}


def get_voice_by_id(voice_id: str) -> Optional[Dict]:
    """Get voice configuration by ID"""
    for voice in ELEVENLABS_VOICES:
        if voice["id"] == voice_id:
            return voice
    return None


def get_voice_by_name(name: str) -> Optional[Dict]:
    """Get voice configuration by name"""
    for voice in ELEVENLABS_VOICES:
        if voice["name"].lower() == name.lower():
            return voice
    return None


def get_agent_voice_id(agent_id: str) -> str:
    """Get voice ID for a specific agent"""
    return AGENT_VOICE_MAPPINGS.get(
        agent_id, "JBFqnCBsd6RMkjVDRZzb"
    )  # Default to George
