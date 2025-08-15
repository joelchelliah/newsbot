#!/usr/bin/env python3
"""
Test script for the new embedding functionality
Run this to see how embeddings work with your newsbot
"""

from config import Config
from services.ai_service import AIService
from stores.preferences_store import PreferencesStore
from logger import get_logger

def test_embeddings():
    """Test the embedding functionality"""
    logger = get_logger()
    logger.info("🧪 Testing embedding functionality...")

    # Initialize services
    config = Config()
    ai_service = AIService(config)
    preferences_store = PreferencesStore(config)

    # Test 1: Basic embedding generation
    logger.info("📝 Test 1: Generating embeddings...")
    test_texts = ["artificial intelligence", "machine learning", "politics", "sports"]

    for text in test_texts:
        embedding = ai_service._get_embedding(text)
        logger.info(f"  '{text}': {len(embedding)} dimensions")

    # Test 2: Cosine similarity
    logger.info("📊 Test 2: Testing cosine similarity...")
    ai_embedding = ai_service._get_embedding("artificial intelligence")
    ml_embedding = ai_service._get_embedding("machine learning")
    politics_embedding = ai_service._get_embedding("politics")

    ai_ml_similarity = ai_service._cosine_similarity(ai_embedding, ml_embedding)
    ai_politics_similarity = ai_service._cosine_similarity(ai_embedding, politics_embedding)

    logger.info(f"  AI vs ML similarity: {ai_ml_similarity:.3f}")
    logger.info(f"  AI vs Politics similarity: {ai_politics_similarity:.3f}")

    # Test 3: Preferences with embeddings
    logger.info("⚙️ Test 3: Testing preferences with embeddings...")

    # Create sample preferences
    sample_preferences = {
        "technology": 4,
        "ai": 5,
        "politics": 2
    }

    # Get preferences with embeddings
    preferences_with_embeddings = preferences_store._add_embeddings_to_preferences(sample_preferences)

    for keyword, data in preferences_with_embeddings.items():
        if isinstance(data, dict) and "embedding" in data:
            logger.info(f"  '{keyword}': score={data['score']}, embedding_dimensions={len(data['embedding'])}")
        else:
            logger.info(f"  '{keyword}': score={data}")

    # Test 4: Article selection with embeddings
    logger.info("📰 Test 4: Testing article selection with embeddings...")

    sample_articles = [
        {
            "title": "New AI breakthrough in machine learning",
            "description": "Scientists develop revolutionary artificial intelligence algorithm"
        },
        {
            "title": "Congress passes new technology bill",
            "description": "Legislation aims to regulate emerging technologies"
        },
        {
            "title": "Sports team wins championship",
            "description": "Local team celebrates victory in national tournament"
        }
    ]

    selected_article = ai_service.select_best_article_with_embeddings(
        sample_articles,
        preferences_with_embeddings
    )

    if selected_article:
        logger.info(f"  Selected article: {selected_article['title']}")
    else:
        logger.info("  No article selected")

    logger.info("✅ Embedding tests completed!")

if __name__ == "__main__":
    test_embeddings()
