from config import Config
from logger import get_logger
from flask import Flask, jsonify, Response
import os
import threading
from services import AIService, NewsApiService, NotificationService
from stores import PreferencesStore, ArticlesStore
from _types import PreferencesWithEmbeddings
from utils import render_template, extract_article_content
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
            return jsonify({"status": "error", "message": "Missing required environment variables"}), 500

        ai_service = AIService(config)
        news_service = NewsApiService(config)
        notification_service = NotificationService(config)
        articles_store = ArticlesStore(config)
        preferences_store = PreferencesStore(config)

        articles_store.cleanup_old_articles()
        preferences: PreferencesWithEmbeddings = preferences_store.get_preferences_with_embeddings()
        articles = news_service.fetch_top_news_articles()
        article = ai_service.select_best_article_with_embeddings(articles, preferences)

        if article:
            title = article['title']
            logger.info(f"🗞️  Found article: {title}")

            article_data = extract_article_content(article['url'])
            if not article_data:
                logger.error("❌  Failed to extract article content")
                return jsonify({"status": "error", "message": "Failed to extract article content"}), 500

            summary = ai_service.summarize_article(article_data['content'])
            subject = "📰 " + ai_service.generate_subject_line(title, summary)
            image_url = ai_service.generate_image(title, summary)

            article_id = articles_store.store_article(
                article_data,
                summary,
                image_url
            )

            notification_service.notify(article, summary, subject, image_url, article_id)
            logger.info(f"📄  Article available at: {config.domain}/article/{article_id}")
            return jsonify({"status": "success", "message": "News email sent successfully!", "article_id": article_id})
        else:
            logger.warning("❌  No articles found")
            return jsonify({"status": "warning", "message": "No articles found"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/preferences', methods=['GET'])
def get_preferences() -> PreferencesWithEmbeddings:
    preferences_store = PreferencesStore(Config())

    return preferences_store.get_preferences_with_embeddings()


@app.route('/article/<article_id>')
def view_article(article_id: str) -> Union[str, Tuple[Response, int]]:
    try:
        config = Config()
        articles_store = ArticlesStore(config)

        article_data = articles_store.get_article(article_id)
        if not article_data:
            return jsonify({"status": "error", "message": "Article not found or expired"}), 404

        return render_template('article.html',
            title=article_data['title'],
            created_at=article_data['created_at'][:10],
            image_html=f'<img src="{article_data["image_url"]}" alt="Article image" class="image">' if article_data.get('image_url') else '',
            summary=article_data['summary'],
            content_html=''.join(f'<p>{para.strip()}</p>' for para in article_data['content'].split('\n\n') if para.strip()),
            original_url=article_data['url'],
            article_id=article_id
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/article/<article_id>/rate/<int:rating>', methods=['POST'])
def submit_article_rating(article_id: str, rating: int) -> Union[Response, Tuple[Response, int]]:
    try:
        if rating < 1 or rating > 3:
            return jsonify({"status": "error", "message": "Rating must be between 1 and 3"}), 400

        config = Config()
        articles_store = ArticlesStore(config)

        article_data = articles_store.get_article(article_id)
        if not article_data:
            return jsonify({"status": "error", "message": "Article not found or expired"}), 404

        def update_preferences_async():
            try:
                logger = get_logger()
                logger.info(f"🔄 Starting async preference update for {rating}-star rating on article")

                ai_service = AIService(config)
                preferences_store = PreferencesStore(config)

                current_preferences: PreferencesWithEmbeddings = preferences_store.get_preferences_with_embeddings()
                updated_preferences: PreferencesWithEmbeddings = ai_service.update_preferences_from_rating_with_embeddings(
                    current_preferences, rating, article_data['summary']
                )

                if updated_preferences:
                    success = preferences_store.update_preferences_with_embeddings(updated_preferences)
                    if success:
                        logger.info(f"✅ Successfully updated preferences for {rating}-star rating on article")
                    else:
                        logger.error(f"❌ Failed to save updated preferences for {rating}-star rating on article")
                else:
                    logger.error(f"❌ Failed to update preferences for {rating}-star rating on article")
            except Exception as background_error:
                logger = get_logger()
                logger.error(f"❌ Async preference update failed: {background_error}")

        threading.Thread(target=update_preferences_async, daemon=True).start()

        return jsonify({
            "status": "success", 
            "message": f"Rated {rating} star(s)! Preferences will be updated.",
            "rating": rating
        })

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
