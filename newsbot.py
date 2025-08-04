import requests
import datetime
from email.message import EmailMessage
import smtplib
import openai
from newspaper import Article
import textwrap
from config import Config
from logger import setup_logger


def summarize_article(config, url):
    article = Article(url)
    article.download()
    article.parse()

    client = openai.OpenAI(api_key=config.openai_api_key)
    response = client.chat.completions.create(
        model=config.openai_model,
        messages=[
            {"role": "system", "content": "Summarize the following article in concise and informative language, in 5-10 lines."},
            {"role": "user", "content": article.text}
        ],
        max_tokens=config.max_tokens,
        temperature=config.temperature,
    )
    return response.choices[0].message.content.strip()

def fetch_top_news(config, logger):
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

        return articles[0] if articles else None
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
    logger = setup_logger()
    logger.info("Starting NewsBot application")

    config = Config()
    if not config.validate():
        logger.error("Missing required environment variables")
        return

    logger.info("Fetching top news article")
    article = fetch_top_news(config, logger)

    if article:
        logger.info(f"Found article: {article['title']}")
        subject = f"📰 NEWSBOT: {article['title']}"
        summary = summarize_article(config, article['url'])

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
    else:
        logger.warning("No articles found")

if __name__ == "__main__":
    main()
