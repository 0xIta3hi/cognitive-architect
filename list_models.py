#!/usr/bin/env python3
"""List available Gemini models."""

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

print("Available models:")
for model in genai.list_models():
    print(f"  - {model.name}")
    if "generateContent" in model.supported_generation_methods:
        print(f"    ✓ Supports generateContent")
