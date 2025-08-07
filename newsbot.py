from email.message import EmailMessage
import smtplib
import textwrap
from config import Config
from logger import get_logger
from flask import Flask, jsonify, request
import os
from services import AIService, NewsApiService, PreferencesService

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
    logger.info("Starting NewsBot application")

    config = Config()
    if not config.validate():
        logger.error("Missing required environment variables")
        return

    ai_service = AIService(config)
    news_service = NewsApiService(config)
    preferences_service = PreferencesService(config)

    preferences = preferences_service.get_preferences()

    logger.info("Fetching top news article")
    articles = news_service.fetch_top_news_articles()
    article = ai_service.select_best_article(articles, preferences)

    if article:
        logger.info(f"Found article: {article['title']}")

        summary = ai_service.summarize_article(article['url'])
        subject = "📰 " + ai_service.generate_subject_line(article['title'], summary)

        body = textwrap.dedent(f"""
            {article['title']}

            {article['description']}

            {summary}

            {article['url']}
        """)
        body_html = f"""
            <html>
            <body>
                <h2>{article['title']}</h2>
                <p><strong>Description:</strong> {article['description']}</p>
                <p><strong>Summary:</strong> {summary}</p>
                <p>📰 <a href="{article['url']}">Read the full article</a></p>
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
    preferences_service = PreferencesService(Config())

    return preferences_service.get_preferences()

@app.route('/preferences/history', methods=['GET'])
def get_preferences_history():
    preferences_service = PreferencesService(Config())
    history = preferences_service.get_history()

    return jsonify({"count": len(history), "history": history})

@app.route('/preferences', methods=['POST'])
def update_preferences():
    try:
        data = request.get_json()
        new_preferences = data.get('preferences', '')

        preferences_service = PreferencesService(Config())
        success = preferences_service.update_preferences(new_preferences)

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

if __name__ == "__main__":
    # Suppress Flask development server warning in production
    if os.environ.get('RENDER'):
        import logging
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))
