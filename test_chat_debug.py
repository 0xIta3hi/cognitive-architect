#!/usr/bin/env python3
"""
Debug script to test chat endpoint functionality.
"""

import os
import sys
from dotenv import load_dotenv
import logging

# Load environment
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Check API key
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
logger.info(f"API Key found: {bool(api_key)}")
if api_key:
    logger.info(f"API Key length: {len(api_key)}")
    logger.info(f"API Key starts with: {api_key[:20]}...")
else:
    logger.error("NO API KEY FOUND!")
    sys.exit(1)

# Test importing and using gemini
try:
    import google.generativeai as genai
    logger.info("✅ google-generativeai imported successfully")
    
    genai.configure(api_key=api_key)
    logger.info("✅ Gemini configured successfully")
    
    model = genai.GenerativeModel("gemini-2.5-flash")
    logger.info("✅ Gemini model (gemini-2.5-flash) created successfully")
    
    # Test a simple call
    logger.info("Testing Gemini with simple math problem...")
    response = model.generate_content("What is 5 plus 7? Answer with just the number.")
    logger.info(f"✅ Gemini response: {response.text}")
    
except Exception as e:
    logger.error(f"❌ Error: {e}", exc_info=True)
    sys.exit(1)

# Now test the actual llm.py module
logger.info("\n" + "="*50)
logger.info("Testing memgraph.api.llm module...")
logger.info("="*50)

try:
    from memgraph.api.llm import generate_chat_response
    logger.info("✅ Imported generate_chat_response successfully")
    
    # Test with memory context
    response = generate_chat_response(
        message="What is 5 plus 7?",
        agent_name="TestAgent",
        memory_context="You are good at math"
    )
    logger.info(f"Response: {response}")
    
except Exception as e:
    logger.error(f"❌ Error: {e}", exc_info=True)
    sys.exit(1)

logger.info("\n✅ All tests passed!")
