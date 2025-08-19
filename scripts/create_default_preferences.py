#!/usr/bin/env python3
"""
Script to create default preferences with embeddings
"""

import json
from config import Config
from services.ai_service import AIService
from _types import PreferencesWithEmbeddings

def create_default_preferences():
    """Create default preferences with embeddings"""

    print("🔧 Creating default preferences with embeddings...")

    # Initialize services
    config = Config()
    ai_service = AIService(config)

    # Define default preferences
    default_preferences: PreferencesWithEmbeddings = {
        "artificial intelligence": {
            "score": 5,
            "embedding": ai_service.get_embedding("artificial intelligence")
        },
        "ai": {
            "score": 5,
            "embedding": ai_service.get_embedding("ai")
        },
        "gaming": {
            "score": 5,
            "embedding": ai_service.get_embedding("gaming")
        },
        "cats": {
            "score": 5,
            "embedding": ai_service.get_embedding("cats")
        },
        "politics": {
            "score": -5,
            "embedding": ai_service.get_embedding("politics")
        }
    }

    # Save to JSON file
    with open('default_preferences.json', 'w') as f:
        json.dump(default_preferences, f, indent=2)

    print("✅ Default preferences saved to 'default_preferences.json'")
    print(f"📊 Created {len(default_preferences)} preferences:")

    for keyword, data in default_preferences.items():
        print(f"  - {keyword}: score {data['score']}, embedding dimensions: {len(data['embedding'])}")

    return default_preferences

if __name__ == "__main__":
    create_default_preferences()
