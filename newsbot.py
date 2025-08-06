import requests
import datetime
from email.message import EmailMessage
import smtplib
import textwrap
from config import Config
from logger import get_logger
from flask import Flask, jsonify
import os
from ai_service import AIService

app = Flask(__name__)


def fetch_top_news_articles(config, logger):
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q=world&"
        f"from={yesterday}&to={today}&"
        f"language=en&"
        f"sortBy=popularity"
    )
    try:
        response = requests.get(url, headers={"Authorization": config.news_api_key}, timeout=30)
        response.raise_for_status()
        articles = response.json().get("articles", [])

        return articles if articles else None
    except Exception as e:
        logger.error(f"Failed to fetch news: {e}")
        return None

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

    logger.info("Fetching top news article")
    articles = fetch_top_news_articles(config, logger)
    article = ai_service.select_best_article(articles, "Only positive or funny articles.")

    if article:
        logger.info(f"Found article: {article['title']}")

        summary = ai_service.summarize_article(article['url'])
        subject = ai_service.generate_subject_line(article['title'], summary)

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

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))
