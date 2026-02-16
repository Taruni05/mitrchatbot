"""
Conversation Memory Service
Maintains conversation context across messages for intelligent follow-up responses.
"""

from collections import deque
from typing import List, Dict, Optional
import streamlit as st
from services.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


class ConversationMemory:
    """Maintains conversation context across messages"""
    
    def __init__(self, max_turns: int = 5):
        """
        Initialize conversation memory.
        
        Args:
            max_turns: Maximum number of conversation turns to remember
        """
        self.max_turns = max_turns
        
        # Initialize session state storage
        if "conversation_history" not in st.session_state:
            st.session_state.conversation_history = deque(maxlen=max_turns)
        
        if "conversation_entities" not in st.session_state:
            # Track mentioned entities (locations, restaurants, etc.)
            st.session_state.conversation_entities = {}
    
    def add_turn(self, user_input: str, bot_response: str, intent: str, entities: Dict = None):
        """
        Add a conversation turn to memory.
        
        Args:
            user_input: User's message
            bot_response: Bot's response
            intent: Detected intent
            entities: Extracted entities (location, restaurant name, etc.)
        """
        turn = {
            "user": user_input,
            "bot": bot_response,
            "intent": intent,
            "entities": entities or {}
        }
        
        st.session_state.conversation_history.append(turn)
        
        # Update entity tracking
        if entities:
            for entity_type, entity_value in entities.items():
                st.session_state.conversation_entities[entity_type] = entity_value
        
        logger.debug(f"Added turn to memory: intent={intent}, entities={entities}")
    
    def get_context_prompt(self, current_query: str) -> str:
        """
        Build context-aware prompt including conversation history.
        
        Args:
            current_query: Current user query
            
        Returns:
            Enhanced prompt with context
        """
        if not st.session_state.conversation_history:
            return current_query
        
        # Get last 3 turns for context (not too much, not too little)
        recent = list(st.session_state.conversation_history)[-3:]
        
        context = "=== CONVERSATION HISTORY ===\n"
        for i, turn in enumerate(recent, 1):
            context += f"\nTurn {i}:\n"
            context += f"User: {turn['user']}\n"
            # Truncate long responses
            bot_response = turn['bot'][:200] + "..." if len(turn['bot']) > 200 else turn['bot']
            context += f"Assistant: {bot_response}\n"
            context += f"Intent: {turn['intent']}\n"
        
        context += "\n=== CURRENT QUERY ===\n"
        context += f"User: {current_query}\n\n"
        context += "IMPORTANT: Consider the conversation history above when responding. "
        context += "If this is a follow-up question (uses 'there', 'it', 'that', 'also'), "
        context += "resolve references to previous context.\n"
        
        return context
    
    def detect_followup(self, query: str) -> bool:
        """
        Detect if this is a follow-up question.
        
        Args:
            query: User query
            
        Returns:
            True if this appears to be a follow-up
        """
        if not st.session_state.conversation_history:
            return False
        
        query_lower = query.lower().strip()
        
        # Follow-up indicators
        followup_patterns = [
            # Pronouns
            "that", "there", "it", "this", "these", "those",
            # Connectors
            "what about", "how about", "also", "and", "or",
            # Questions continuing previous topic
            "more", "other", "another", "else",
            # Time references
            "when", "timing", "schedule",
            # Short questions (usually follow-ups)
            query_lower.startswith("how ") and len(query.split()) < 4,
            query_lower.startswith("what ") and len(query.split()) < 4,
            query_lower.startswith("where ") and len(query.split()) < 4,
        ]
        
        is_followup = any(
            pattern if isinstance(pattern, bool) else pattern in query_lower
            for pattern in followup_patterns
        )
        
        if is_followup:
            logger.info(f"Detected follow-up question: {query}")
        
        return is_followup
    
    def resolve_references(self, query: str) -> str:
        """
        Resolve pronoun references to previous context.
        
        Args:
            query: User query possibly containing references
            
        Returns:
            Query with references resolved
        """
        if not self.detect_followup(query):
            return query
        
        if not st.session_state.conversation_history:
            return query
        
        last_turn = st.session_state.conversation_history[-1]
        last_entities = last_turn.get("entities", {})
        last_intent = last_turn["intent"]
        
        resolved = query
        
        # Replace pronouns with actual entities
        replacements = {
            "there": last_entities.get("location", ""),
            "that place": last_entities.get("location", ""),
            "that restaurant": last_entities.get("restaurant", ""),
            "it": last_entities.get("location", "") or last_entities.get("restaurant", ""),
            "this": last_entities.get("location", "") or last_entities.get("restaurant", ""),
        }
        
        for pronoun, replacement in replacements.items():
            if pronoun in query.lower() and replacement:
                # Case-insensitive replacement
                import re
                pattern = re.compile(re.escape(pronoun), re.IGNORECASE)
                resolved = pattern.sub(replacement, resolved, count=1)
                logger.info(f"Resolved '{pronoun}' -> '{replacement}'")
        
        # Handle context-dependent short questions
        if len(query.split()) <= 3:
            # "how to get there?" -> "how to get to [location]?"
            if "how" in query.lower() and "get" in query.lower():
                location = last_entities.get("location", "")
                if location and "there" in query.lower():
                    resolved = f"How to get to {location}?"
            
            # "timings?" -> "[restaurant/location] timings?"
            elif "timing" in query.lower() or "time" in query.lower():
                entity = last_entities.get("restaurant") or last_entities.get("location", "")
                if entity:
                    resolved = f"{entity} timings"
            
            # "cost?" -> "[location/restaurant] cost?"
            elif "cost" in query.lower() or "price" in query.lower():
                entity = last_entities.get("restaurant") or last_entities.get("location", "")
                if entity:
                    resolved = f"{entity} cost"
        
        if resolved != query:
            logger.info(f"Reference resolution: '{query}' -> '{resolved}'")
        
        return resolved
    
    def get_last_intent(self) -> Optional[str]:
        """Get the intent from the last conversation turn."""
        if not st.session_state.conversation_history:
            return None
        return st.session_state.conversation_history[-1]["intent"]
    
    def get_last_location(self) -> Optional[str]:
        """Get the last mentioned location from context."""
        return st.session_state.conversation_entities.get("location")
    
    def clear_history(self):
        """Clear conversation history (for new topics or user request)."""
        st.session_state.conversation_history.clear()
        st.session_state.conversation_entities.clear()
        logger.info("Cleared conversation history")


# Singleton instance
_memory_instance = None

def get_conversation_memory() -> ConversationMemory:
    """Get or create conversation memory instance."""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = ConversationMemory()
    return _memory_instance


def extract_entities(query: str, intent: str) -> Dict[str, str]:
    """
    Extract entities from query based on intent.
    
    Args:
        query: User query
        intent: Detected intent
        
    Returns:
        Dictionary of entity_type: entity_value
    """
    entities = {}
    
    # Extract location names (common Hyderabad areas)
    from services.locations import HYDERABAD_AREA_COORDS
    
    query_lower = query.lower()
    for area in HYDERABAD_AREA_COORDS.keys():
        if area in query_lower:
            entities["location"] = area.title()
            break
    
    # Extract restaurant/landmark names (you can expand this list)
    landmarks = [
        "charminar", "golconda", "hussain sagar", "ramoji film city",
        "birla mandir", "tank bund", "paradise", "bawarchi", "shah ghouse",
        "nimrah", "karachi bakery"
    ]
    
    for landmark in landmarks:
        if landmark in query_lower:
            entities["restaurant" if "paradise" in landmark or "bawarchi" in landmark else "location"] = landmark.title()
            break
    
    return entities