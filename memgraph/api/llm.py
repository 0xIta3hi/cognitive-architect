"""
LLM integration for MemGraph chat endpoint using Google Gemini.
"""

import os
from typing import Optional
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Initialize Gemini client
_genai_model = None


def get_gemini_model():
    """Get or create Gemini model."""
    global _genai_model
    
    if _genai_model is None:
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("⚠️  GOOGLE_API_KEY or GEMINI_API_KEY not set - chat will use fallback responses")
        else:
            genai.configure(api_key=api_key)
            _genai_model = genai.GenerativeModel("gemini-pro")
    
    return _genai_model


def generate_chat_response(
    message: str,
    agent_name: str = "Assistant",
    memory_context: str = "",
    conversation_history: Optional[list] = None
) -> str:
    """
    Generate a chat response using Google Gemini.
    
    Args:
        message: User message
        agent_name: Name of the agent
        memory_context: Context from agent's memories
        conversation_history: Previous messages in conversation
        
    Returns:
        Generated response
    """
    try:
        model = get_gemini_model()
        
        if model is None:
            # Fallback if API not configured
            if memory_context:
                return f"I remember: {memory_context[:100]}... How can I help with that?"
            else:
                return f"I don't have specific memories about that yet, but I'll remember this conversation for next time. What would you like to know?"
        
        # Build system prompt
        system_prompt = f"""You are {agent_name}, an AI assistant with a memory system.

You have access to the following memories about previous interactions and facts:
{memory_context if memory_context else "No specific memories found yet."}

Be conversational, helpful, and build on your memories when relevant. If you don't have specific information, 
say so but offer to learn and remember it for future interactions. Keep responses concise (2-3 sentences)."""
        
        # Build full prompt combining system and user message
        if conversation_history:
            # Add conversation history context
            history_text = "\n".join([
                f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}"
                for msg in conversation_history[-4:]  # Last 4 messages for context
            ])
            full_prompt = f"{system_prompt}\n\nPrevious conversation:\n{history_text}\n\nUSER: {message}\n\nASSISTANT:"
        else:
            full_prompt = f"{system_prompt}\n\nUSER: {message}\n\nASSISTANT:"
        
        logger.info(f"🤖 Calling Gemini API for agent: {agent_name}")
        
        # Call Gemini
        response = model.generate_content(full_prompt)
        response_text = response.text.strip()
        
        logger.info(f"✅ Gemini response received ({len(response_text)} chars)")
        
        return response_text
        
    except Exception as e:
        logger.error(f"❌ Gemini API error: {e}")
        # Fallback response
        if memory_context:
            return f"I remember: {memory_context[:100]}... How can I help with that?"
        else:
            return f"I don't have specific memories about that yet, but I'll remember this conversation for next time. What would you like to know?"
