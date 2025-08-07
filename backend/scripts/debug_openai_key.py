#!/usr/bin/env python3
"""
Debug OpenAI API Key configuration
"""

import sys
import os
sys.path.insert(0, '/Users/roberdan/GitHub/convergio/backend')

from src.core.config import settings

def debug_openai_config():
    print("🔍 Debugging OpenAI Configuration...")
    
    # Check environment variable
    env_key = os.getenv('OPENAI_API_KEY')
    print(f"Environment OPENAI_API_KEY: {env_key[:20] if env_key else 'None'}...")
    
    # Check settings
    try:
        settings_key = settings.OPENAI_API_KEY
        print(f"Settings OPENAI_API_KEY: {settings_key[:20] if settings_key else 'None'}...")
    except Exception as e:
        print(f"❌ Settings error: {e}")
        return False
    
    # Test OpenAI client directly
    try:
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        
        client = OpenAIChatCompletionClient(
            model="gpt-4o-mini",
            api_key=settings.OPENAI_API_KEY,
        )
        print("✅ OpenAI client created successfully")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI client creation failed: {e}")
        return False

if __name__ == "__main__":
    success = debug_openai_config()
    print(f"🎯 Result: {'SUCCESS' if success else 'FAILED'}")