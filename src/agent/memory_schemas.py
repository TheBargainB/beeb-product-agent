"""Memory schemas for the enhanced assistant system with flexible language configuration."""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class AssistantLanguageConfig(BaseModel):
    """Configuration for assistant language behavior."""
    primary_language: str = Field(
        description="Primary language for responses (e.g., 'arabic', 'english', 'spanish', 'french', 'german')"
    )
    language_enforcement: Literal["strict", "flexible", "auto"] = Field(
        description="How strictly to enforce language: 'strict'=always respond in primary language, 'flexible'=match user language, 'auto'=detect best approach"
    )
    fallback_language: str = Field(
        default="english",
        description="Fallback language if primary language processing fails"
    )
    translation_enabled: bool = Field(
        default=True,
        description="Whether to offer translations between languages"
    )
    cultural_context: Optional[str] = Field(
        default=None,
        description="Cultural context to consider (e.g., 'middle_east', 'europe', 'north_america')"
    )


class UserMemory(BaseModel):
    """General user memory for personal information and preferences."""
    content: str = Field(
        description="The main content of the memory about the user. Examples: 'User prefers organic food', 'User has two children', 'User works as a teacher'"
    )
    category: Literal["personal", "preference", "interest", "experience", "goal"] = Field(
        description="Category of memory for better organization"
    )
    importance: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="Importance level for prioritizing memories"
    )
    last_referenced: datetime = Field(
        default_factory=datetime.now,
        description="When this memory was last referenced in conversation"
    )


class UserProfile(BaseModel):
    """Comprehensive user profile with personal information."""
    name: Optional[str] = Field(
        default=None,
        description="User's preferred name"
    )
    location: Optional[str] = Field(
        default=None,
        description="User's location (city, country)"
    )
    occupation: Optional[str] = Field(
        default=None,
        description="User's job or profession"
    )
    age_range: Optional[str] = Field(
        default=None,
        description="User's age range (e.g., '25-35', '40s', 'senior')"
    )
    family_status: Optional[str] = Field(
        default=None,
        description="Family information (e.g., 'married with 2 children', 'single', 'lives with partner')"
    )
    languages: List[str] = Field(
        default_factory=list,
        description="Languages the user speaks"
    )
    interests: List[str] = Field(
        default_factory=list,
        description="User's interests and hobbies"
    )
    preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="Various user preferences as key-value pairs"
    )
    communication_style: Optional[str] = Field(
        default=None,
        description="Preferred communication style (e.g., 'formal', 'casual', 'detailed', 'concise')"
    )


class ConversationMemory(BaseModel):
    """Memory about specific conversations or interactions."""
    topic: str = Field(
        description="Main topic of the conversation"
    )
    key_points: List[str] = Field(
        description="Key points discussed in the conversation"
    )
    user_requests: List[str] = Field(
        default_factory=list,
        description="Specific requests made by the user"
    )
    follow_up_needed: bool = Field(
        default=False,
        description="Whether follow-up is needed on this conversation"
    )
    date: datetime = Field(
        default_factory=datetime.now,
        description="When this conversation took place"
    )


class AssistantInstructions(BaseModel):
    """Instructions for how the assistant should behave."""
    language_config: AssistantLanguageConfig = Field(
        description="Language configuration for the assistant"
    )
    persona: Optional[str] = Field(
        default=None,
        description="Assistant persona (e.g., 'professional', 'friendly', 'academic')"
    )
    specialization: Optional[str] = Field(
        default=None,
        description="Area of specialization (e.g., 'grocery_assistant', 'language_tutor', 'general_assistant')"
    )
    response_style: Optional[str] = Field(
        default=None,
        description="How to structure responses (e.g., 'detailed', 'concise', 'step_by_step')"
    )
    custom_instructions: Optional[str] = Field(
        default=None,
        description="Any custom instructions from the user"
    )
    restrictions: List[str] = Field(
        default_factory=list,
        description="Things the assistant should not do or discuss"
    )


class MemoryCollection(BaseModel):
    """Collection of different types of memories about the user."""
    user_memories: List[UserMemory] = Field(
        default_factory=list,
        description="General memories about the user"
    )
    conversation_memories: List[ConversationMemory] = Field(
        default_factory=list,
        description="Memories about specific conversations"
    )


# Language configuration templates for common use cases
LANGUAGE_CONFIGS = {
    "arabic_only": AssistantLanguageConfig(
        primary_language="arabic",
        language_enforcement="strict",
        fallback_language="english",
        cultural_context="middle_east"
    ),
    "english_only": AssistantLanguageConfig(
        primary_language="english",
        language_enforcement="strict",
        fallback_language="english"
    ),
    "spanish_only": AssistantLanguageConfig(
        primary_language="spanish",
        language_enforcement="strict",
        fallback_language="english",
        cultural_context="latin_america"
    ),
    "french_only": AssistantLanguageConfig(
        primary_language="french",
        language_enforcement="strict",
        fallback_language="english",
        cultural_context="europe"
    ),
    "multilingual_flexible": AssistantLanguageConfig(
        primary_language="english",
        language_enforcement="flexible",
        fallback_language="english",
        translation_enabled=True
    ),
    "multilingual_auto": AssistantLanguageConfig(
        primary_language="english",
        language_enforcement="auto",
        fallback_language="english",
        translation_enabled=True
    )
}


def get_language_instructions(config: AssistantLanguageConfig) -> str:
    """Generate language instructions based on configuration."""
    instructions = []
    
    # Primary language instruction
    if config.language_enforcement == "strict":
        instructions.append(
            f"**CRITICAL LANGUAGE REQUIREMENT**: You MUST respond in {config.primary_language} only, "
            f"regardless of the input language. Always reply in {config.primary_language} even if the user "
            f"writes in English or any other language."
        )
    elif config.language_enforcement == "flexible":
        instructions.append(
            f"**LANGUAGE PREFERENCE**: Prefer to respond in {config.primary_language}, but you may match "
            f"the user's language if it seems more appropriate for the context."
        )
    elif config.language_enforcement == "auto":
        instructions.append(
            f"**LANGUAGE ADAPTATION**: Automatically choose the best language for each response. "
            f"Consider using {config.primary_language} when appropriate, but adapt to the user's preferences."
        )
    
    # Cultural context
    if config.cultural_context:
        instructions.append(
            f"**CULTURAL CONTEXT**: Consider {config.cultural_context} cultural context in your responses."
        )
    
    # Translation offer
    if config.translation_enabled:
        instructions.append(
            "**TRANSLATION ASSISTANCE**: Offer to translate important information between languages when helpful."
        )
    
    return "\n".join(instructions) 