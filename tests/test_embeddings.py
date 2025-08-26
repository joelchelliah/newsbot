#!/usr/bin/env python3
"""
Test script for the new embedding functionality
Run this to see how embeddings work with your newsbot
"""

from config import Config
from services.ai_service import AIService
from stores.preferences_store import PreferencesStore
from logger import get_logger
from _types import PreferencesWithEmbeddings

def test_embeddings() -> None:
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
        embedding = ai_service.get_embedding(text)
        logger.info(f"  '{text}': {len(embedding)} dimensions")

    # Test 2: Cosine similarity
    logger.info("📊 Test 2: Testing cosine similarity...")
    ai_embedding = ai_service.get_embedding("artificial intelligence")
    ml_embedding = ai_service.get_embedding("machine learning")
    politics_embedding = ai_service.get_embedding("politics")

    ai_ml_similarity = ai_service.cosine_similarity(ai_embedding, ml_embedding)
    ai_politics_similarity = ai_service.cosine_similarity(ai_embedding, politics_embedding)

    logger.info(f"  AI vs ML similarity: {ai_ml_similarity:.3f}")
    logger.info(f"  AI vs Politics similarity: {ai_politics_similarity:.3f}")

    # Test 3: Create preferences with embeddings manually
    logger.info("⚙️ Test 3: Testing preferences with embeddings...")

    # Create sample preferences with embeddings (simulating what would come from AI service)
    sample_preferences: PreferencesWithEmbeddings = {
        "technology": {
            "score": 4,
            "embedding": ai_service.get_embedding("technology")
        },
        "ai": {
            "score": 5,
            "embedding": ai_service.get_embedding("ai")
        },
        "politics": {
            "score": 2,
            "embedding": ai_service.get_embedding("politics")
        }
    }

    for keyword, data in sample_preferences.items():
        logger.info(f"  '{keyword}': score={data['score']}, embedding_dimensions={len(data['embedding'])}")

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
        sample_preferences
    )

    if selected_article:
        logger.info(f"  Selected article: {selected_article['title']}")
    else:
        logger.info("  No article selected")

    # Test 5: Preference update simulation
    logger.info("🔄 Test 5: Testing preference update simulation...")

    article_summary = "Scientists develop new machine learning algorithm for image recognition"
    rating = 3

    # Simulate updating preferences (this would normally be called from newsbot.py)
    updated_preferences = ai_service.update_preferences_from_rating_with_embeddings(
        sample_preferences,
        rating,
        article_summary
    )

    logger.info(f"  Original preferences: {len(sample_preferences)} keywords")
    logger.info(f"  Updated preferences: {len(updated_preferences)} keywords")

    # Show new keywords that were added
    new_keywords = set(updated_preferences.keys()) - set(sample_preferences.keys())
    if new_keywords:
        logger.info(f"  New keywords added: {list(new_keywords)}")

    logger.info("✅ Embedding tests completed!")

if __name__ == "__main__":
    test_embeddings()
