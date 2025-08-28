from config import Config
from logger import get_logger
from flask import Flask, jsonify, request, Response
import os
import threading
from services import AIService, NewsApiService, NotificationService, ExtractionService
from stores import PreferencesStore, ArticlesStore
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
            return jsonify({"status": "error", "message": "Missing required environment variables"}), 500

        ai_service = AIService(config)
        news_service = NewsApiService(config)
        notification_service = NotificationService(config)
        extraction_service = ExtractionService()
        articles_store = ArticlesStore(config)
        preferences_store = PreferencesStore(config)

        articles_store.cleanup_old_articles()
        preferences: PreferencesWithEmbeddings = preferences_store.get_preferences_with_embeddings()
        articles = news_service.fetch_top_news_articles()
        article = ai_service.select_best_article_with_embeddings(articles, preferences)

        if article:
            title = article['title']
            logger.info(f"🗞️  Found article: {title}")

            # Extract full article content
            article_data = extraction_service.extract_article_content(article['url'])
            if not article_data:
                logger.error("❌  Failed to extract article content")
                return jsonify({"status": "error", "message": "Failed to extract article content"}), 500

            # Generate summary from extracted content
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
    preferences = preferences_store.get_preferences_with_embeddings()

    return preferences


@app.route('/article/<article_id>')
def view_article(article_id: str) -> Union[str, Tuple[Response, int]]:
    try:
        config = Config()
        articles_store = ArticlesStore(config)

        article_data = articles_store.get_article(article_id)
        if not article_data:
            return jsonify({"status": "error", "message": "Article not found or expired"}), 404

        # Create mobile-friendly HTML
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{article_data['title']} - NewsBot</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                    color: #333;
                }}
                .container {{
                    max-width: 700px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid #e0e0e0;
                }}
                .header h1 {{
                    margin: 0 0 10px 0;
                    color: #2c3e50;
                    font-size: 1.8rem;
                }}
                .meta {{
                    color: #666;
                    font-size: 0.9rem;
                    margin-bottom: 20px;
                }}
                .image {{
                    width: 100%;
                    max-height: 400px;
                    object-fit: cover;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .summary {{
                    background: #e8f4fd;
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #3498db;
                    margin-bottom: 30px;
                }}
                .content {{
                    font-size: 1.1rem;
                    line-height: 1.8;
                    text-align: justify;
                }}
                .content p {{
                    margin-bottom: 1.5em;
                    text-indent: 0;
                }}
                .content p:last-child {{
                    margin-bottom: 0;
                }}
                .rating-section {{
                    margin-top: 40px;
                    padding-top: 30px;
                    border-top: 2px solid #e0e0e0;
                    text-align: center;
                }}
                .rating-buttons {{
                    display: flex;
                    justify-content: center;
                    gap: 20px;
                    margin: 20px 0;
                }}
                .rating-btn {{
                    padding: 12px 60px;
                    border: none;
                    border-radius: 25px;
                    font-size: 2rem;
                    cursor: pointer;
                    transition: transform 0.3s;
                }}
                .rating-btn:hover {{
                    transform: scale(1.1);
                }}
                .dislike {{ background: #a52525; color: white; }}
                .neutral {{ background: #dcaa3b; color: white; }}
                .like {{ background: #35c341; color: white; }}
                .source-link {{
                    margin-top: 24px;
                    text-align: center;
                }}
                .source-link a {{
                    color: #3498db;
                    text-decoration: none;
                    font-weight: 500;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{article_data['title']}</h1>
                    <div class="meta">📰 NewsBot • {article_data['created_at'][:10]}</div>
                </div>

                {f'<img src="{article_data["image_url"]}" alt="Article image" class="image">' if article_data.get('image_url') else ''}

                <div class="summary">
                    <strong>📋 Summary:</strong><br>
                    {article_data['summary']}
                </div>

                <div class="content">
                    {''.join(f'<p>{para.strip()}</p>' for para in article_data['content'].split('\n\n') if para.strip())}
                </div>

                <div class="rating-section">
                    <h3>Rate this article</h3>
                    <div class="rating-buttons">
                        <button class="rating-btn dislike" onclick="submitRating(1)">😡</button>
                        <button class="rating-btn neutral" onclick="submitRating(2)">😐</button>
                        <button class="rating-btn like" onclick="submitRating(3)">🤩</button>
                    </div>
                </div>

                <div class="source-link">
                    <a href="{article_data['url']}" target="_blank">📖  Read the original article</a>
                </div>
            </div>

            <script>
                function submitRating(rating) {{
                    // Disable buttons during request
                    const buttons = document.querySelectorAll('.rating-btn');
                    buttons.forEach(btn => btn.disabled = true);

                    fetch('/article/{article_id}/rate/' + rating, {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }}
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        if (data.status === 'success') {{
                            alert('✅ ' + data.message);
                        }} else {{
                            alert('❌ Error: ' + data.message);
                        }}
                    }})
                    .catch(error => {{
                        alert('❌ Error submitting rating: ' + error.message);
                    }})
                    .finally(() => {{
                        // Re-enable buttons
                        buttons.forEach(btn => btn.disabled = false);
                    }});
                }}
            </script>
        </body>
        </html>
        """
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

        return jsonify({"status": "success", "message": f"Thanks for rating this article {rating} stars! Your preferences will be updated."})

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
