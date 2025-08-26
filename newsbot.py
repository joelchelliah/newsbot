from config import Config
from logger import get_logger
from flask import Flask, jsonify, request, Response
import os
from services import AIService, NewsApiService, EmailService
from stores import SummariesStore, PreferencesStore
from _types import PreferencesWithEmbeddings
from typing import Union, Tuple

app = Flask(__name__)

@app.route('/')
def health_check() -> Response:
    return jsonify({"status": "healthy", "message": "NewsBot is running"})


@app.route('/trigger', methods=['POST'])
def trigger_newsbot() -> Union[Response, Tuple[Response, int]]:
    try:
        logger = get_logger()
        logger.info("🤖  Triggering the NewsBot")

        config = Config()
        if not config.validate():
            logger.error("⚠️  Missing required environment variables")
            return

        ai_service = AIService(config)
        news_service = NewsApiService(config)
        email_service = EmailService(config)
        summaries_store = SummariesStore(config)
        preferences_store = PreferencesStore(config)

        summaries_store.cleanup_old_summaries()
        preferences: PreferencesWithEmbeddings = preferences_store.get_preferences_with_embeddings()
        articles = news_service.fetch_top_news_articles()
        article = ai_service.select_best_article_with_embeddings(articles, preferences)

        if article:
            title = article['title']
            logger.info(f"🗞️  Found article: {title}")

            summary = ai_service.summarize_article(article['url'])
            subject = "📰 " + ai_service.generate_subject_line(title, summary)
            image_url = ai_service.generate_image(title, summary)
            summary_id = summaries_store.store_summary(summary)

            email_service.send_email(article, summary, summary_id, subject, image_url)
            return jsonify({"status": "success", "message": "News email sent successfully!"})
        else:
            logger.warning("❌  No articles found")
            return jsonify({"status": "warning", "message": "No articles found"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/preferences', methods=['GET'])
def get_preferences() -> PreferencesWithEmbeddings:
    preferences_store = PreferencesStore(Config())
    preferences = preferences_store.get_preferences_with_embeddings()

    return preferences

@app.route('/r<int:rating>/<summary_id>', methods=['GET'])
def submit_rating(rating: int, summary_id: str) -> Union[Response, str, Tuple[Response, int]]:
    try:
        if rating < 1 or rating > 3:
            return jsonify({"status": "error", "message": "Rating must be between 1 and 3"}), 400

        config = Config()
        summaries_store = SummariesStore(config)

        article_summary = summaries_store.get_summary(summary_id)
        if not article_summary:
            return jsonify({"status": "error", "message": "Summary not found or expired"}), 404

        ai_service = AIService(config)
        preferences_store = PreferencesStore(config)

        current_preferences: PreferencesWithEmbeddings = preferences_store.get_preferences_with_embeddings()
        updated_preferences: PreferencesWithEmbeddings = ai_service.update_preferences_from_rating_with_embeddings(
            current_preferences, rating, article_summary
        )

        if updated_preferences:
            success = preferences_store.update_preferences_with_embeddings(updated_preferences)
            if success:
                return f"""
                <html>
                <head>
                    <title>Rating Submitted</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                        .success {{ color: green; font-size: 18px; }}
                        .message {{ margin: 20px 0; }}
                    </style>
                </head>
                <body>
                    <div class="success">✅ Thank you for your {rating}-star rating!</div>
                    <div class="message">Your preferences have been updated to improve future recommendations.</div>
                    <div class="message">You can close this window now.</div>
                </body>
                </html>
                """
            else:
                return jsonify({"status": "error", "message": "Failed to save updated preferences"}), 500
        else:
            return jsonify({"status": "error", "message": "Failed to update preferences"}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.errorhandler(404)
def not_found(_: Exception) -> Tuple[Response, int]:
    return jsonify({"error": "Not found"}), 404


if __name__ == "__main__":
    # Suppress Flask development server warning in production
    if os.environ.get('RENDER'):
        import logging
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))
