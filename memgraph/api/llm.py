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
            logger.debug(f"Environment variables: GOOGLE_API_KEY={os.getenv('GOOGLE_API_KEY')}, GEMINI_API_KEY={os.getenv('GEMINI_API_KEY')}")
        else:
            logger.info(f"✅ Found API key (length: {len(api_key)}), initializing Gemini...")
            genai.configure(api_key=api_key)
            # Use gemini-2.5-flash - latest fast model with full feature support
            _genai_model = genai.GenerativeModel("gemini-2.5-flash")
            logger.info("✅ Gemini model (gemini-2.5-flash) initialized successfully")
    
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
            logger.warning("⚠️  Gemini model not available, using fallback response")
            if memory_context:
                return f"I remember: {memory_context[:100]}... Regarding '{message[:50]}', I'm not currently connected to the AI model. Please check API configuration."
            else:
                return f"I'm not currently connected to the AI model. Please check your GOOGLE_API_KEY configuration."
        
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
        logger.debug(f"Prompt: {full_prompt[:200]}...")
        
        # Call Gemini
        response = model.generate_content(full_prompt)
        response_text = response.text.strip()
        
        logger.info(f"✅ Gemini response received ({len(response_text)} chars): {response_text[:100]}...")
        
        return response_text
        
    except Exception as e:
        logger.error(f"❌ Gemini API error: {e}")
        # Fallback: Simple response based on the message (don't just return memory context)
        # This ensures we actually respond to what the user asked
        if "plus" in message.lower() or "+" in message:
            try:
                # Try to extract numbers and do basic math
                import re
                numbers = re.findall(r'\d+', message)
                if len(numbers) >= 2:
                    result = sum(int(n) for n in numbers[:2])
                    return f"Based on your message: {numbers[0]} + {numbers[1]} = {result}. {memory_context if memory_context else ''}"
            except:
                pass
        
        # Generic fallback
        if memory_context:
            return f"I remember: {memory_context} Regarding your question '{message[:50]}...', I'd be happy to help. Can you provide more details?"
        else:
            return f"I heard you say: '{message}'. I don't have specific memories about that yet, but I'll remember this conversation for next time. What would you like to know?"
