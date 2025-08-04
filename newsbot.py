import requests
import datetime
from email.message import EmailMessage
import smtplib
import os
import openai
from newspaper import Article
import textwrap
from dotenv import load_dotenv

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



def summarize_article(url):
    article = Article(url)
    article.download()
    article.parse()

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Summarize the following article in concise and informative language, in 5-10 lines."},
            {"role": "user", "content": article.text}
        ],
        max_tokens=300,
        temperature=0.4,
    )
    return response.choices[0].message.content.strip()

def fetch_top_news(api_key):
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q=world&"
        f"from={yesterday}&to={today}&"
        f"language=en&"
        f"sortBy=popularity"
    )
    response = requests.get(url, headers={"Authorization": api_key})
    articles = response.json().get("articles", [])

    return articles[0] if articles else None

def send_email(subject, body, body_html, to_email, from_email, smtp_password):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(body)
    msg.add_alternative(body_html, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(from_email, smtp_password)
        smtp.send_message(msg)

def main():
    news_api_key = os.getenv("NEWS_API_KEY")
    smtp_pass = os.getenv("SMTP_PASS")
    from_email = os.getenv("FROM_EMAIL")
    to_email = os.getenv("TO_EMAIL")

    article = fetch_top_news(news_api_key)
    if article:
        subject = f"📰 NEWSBOT: {article['title']}"
        body = textwrap.dedent(f"""
            {article['title']}

            {article['description']}

            {summarize_article(article['url'])}

            {article['url']}
        """)
        body_html = f"""
            <html>
            <body>
                <h2>{article['title']}</h2>
                <p><strong>Description:</strong> {article['description']}</p>
                <p><strong>Summary:</strong> {summarize_article(article['url'])}</p>
                <p>📰 <a href="{article['url']}">Read the full article</a></p>
            </body>
            </html>
        """

        send_email(subject, body, body_html, to_email, from_email, smtp_pass)
    else:
        print("No articles found.")

if __name__ == "__main__":
    main()
