from email.message import EmailMessage
import smtplib
import textwrap
from config import Config
from logger import get_logger
from flask import Flask, jsonify, request
import os
from services import AIService, NewsApiService
from stores import SummariesStore, PreferencesStore

app = Flask(__name__)


def send_email(subject, body, body_html, config):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config.from_email
    msg["To"] = config.to_email
    msg.set_content(body)
    msg.add_alternative(body_html, subtype="html")

    with smtplib.SMTP_SSL(config.smtp_server, config.smtp_port) as smtp:
        smtp.login(config.from_email, config.smtp_password)
        smtp.send_message(msg)

def main():
    logger = get_logger()
    logger.info("🤖  Starting NewsBot application")

    config = Config()
    if not config.validate():
        logger.error("⚠️  Missing required environment variables")
        return

    logger.info("🧹  Cleaning up old summaries")
    summaries_store = SummariesStore(config)
    summaries_store.cleanup_old_summaries()

    ai_service = AIService(config)
    news_service = NewsApiService(config)
    preferences_store = PreferencesStore(config)

    preferences = preferences_store.get_preferences()

    logger.info("📰  Fetching top news article...")
    articles = news_service.fetch_top_news_articles()
    article = ai_service.select_best_article(articles, preferences)

    if article:
        logger.info(f"🗞️  Found article: {article['title']}")

        summary = ai_service.summarize_article(article['url'])
        subject = "📰 " + ai_service.generate_subject_line(article['title'], summary)
        summary_id = summaries_store.store_summary(summary)

        body = textwrap.dedent(f"""
            {article['title']}

            {article['description']}

            {summary}

            {article['url']}
        """)
        domain = config.domain

        body_html = f"""
            <html>
            <head>
                <style>
                    .rating-container {{
                        margin: 20px 0;
                        text-align: center;
                    }}
                    .star-link {{
                        text-decoration: none;
                        color: #666;
                        font-size: 16px;
                        padding: 8px 12px;
                        margin: 0 2px;
                        display: inline-block;
                        border: 1px solid #ccc;
                        border-radius: 4px;
                        background-color: #f9f9f9;
                    }}
                    .star-link:hover {{
                        color: #333;
                        background-color: #e9e9e9;
                        border-color: #999;
                    }}
                    .rating-text {{
                        margin-top: 10px;
                        font-size: 14px;
                        color: #666;
                    }}
                </style>
            </head>
            <body>
                <h2>{article['title']}</h2>
                <p><strong>Description:</strong> {article['description']}</p>
                <p><strong>Summary:</strong> {summary}</p>
                <p>📰 <a href="{article['url']}">Read the full article</a></p>

                <div class="rating-container">
                    <p><strong>Rate this article:</strong></p>
                    <div>
                        <a href="{domain}/r1/{summary_id}" class="star-link" title="Rate 1 star">[1★]</a>
                        <a href="{domain}/r2/{summary_id}" class="star-link" title="Rate 2 stars">[2★]</a>
                        <a href="{domain}/r3/{summary_id}" class="star-link" title="Rate 3 stars">[3★]</a>
                        <a href="{domain}/r4/{summary_id}" class="star-link" title="Rate 4 stars">[4★]</a>
                        <a href="{domain}/r5/{summary_id}" class="star-link" title="Rate 5 stars">[5★]</a>
                    </div>
                    <p class="rating-text">Click a star to rate this article and help improve future recommendations</p>
                </div>
            </body>
            </html>
        """

        logger.info("Sending email")
        send_email(subject, body, body_html, config)
        logger.info("News email sent successfully!")
        return True
    else:
        logger.warning("No articles found")
        return False

@app.route('/')
def health_check():
    return jsonify({"status": "healthy", "message": "NewsBot is running"})

@app.route('/trigger', methods=['POST'])
def trigger_newsbot():
    try:
        success = main()
        if success:
            return jsonify({"status": "success", "message": "News email sent successfully!"})
        else:
            return jsonify({"status": "warning", "message": "No articles found"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/preferences', methods=['GET'])
def get_preferences():
    preferences_store = PreferencesStore(Config())

    return preferences_store.get_preferences()

@app.route('/preferences/history', methods=['GET'])
def get_preferences_history():
    preferences_store = PreferencesStore(Config())
    history = preferences_store.get_history()

    return jsonify({"count": len(history), "history": history})

@app.route('/preferences', methods=['POST'])
def update_preferences():
    try:
        data = request.get_json()
        new_preferences = data.get('preferences', '')

        preferences_store = PreferencesStore(Config())
        success = preferences_store.update_preferences(new_preferences)

        if success:
            return jsonify({
                "status": "success",
                "message": "Preferences updated and saved",
                "preferences": new_preferences
            })
        else:
            return jsonify({"status": "error", "message": "Failed to save preferences"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/r<int:rating>/<summary_id>', methods=['GET'])
def submit_rating(rating, summary_id):
    try:
        if rating < 1 or rating > 5:
            return jsonify({"status": "error", "message": "Rating must be between 1 and 5"}), 400

        config = Config()
        summaries_store = SummariesStore(config)

        article_summary = summaries_store.get_summary(summary_id)
        if not article_summary:
            return jsonify({"status": "error", "message": "Summary not found or expired"}), 404

        ai_service = AIService(config)
        preferences_store = PreferencesStore(config)

        current_preferences = preferences_store.get_preferences()
        updated_preferences = ai_service.update_preferences_from_rating(
            current_preferences, rating, article_summary
        )

        if updated_preferences:
            success = preferences_store.update_preferences(updated_preferences)
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

if __name__ == "__main__":
    # Suppress Flask development server warning in production
    if os.environ.get('RENDER'):
        import logging
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))
