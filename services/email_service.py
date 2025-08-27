from email.message import EmailMessage
import smtplib
import textwrap
import requests
from logger import get_logger
from typing import Dict, Optional
from config import Config


class EmailService:
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger()

    def send_email(self, article: Dict, summary: str, summary_id: str, subject: str, image_url: Optional[str] = None) -> None:
        body = self._create_body(article, summary)
        body_html = self._create_html_body(article, summary, summary_id, image_url)

        self._send(subject, body, body_html)
        self.logger.info("📧   News email sent successfully!")

        # Send push notification
        self._send_push_notification(article['title'])

    def _create_body(self, article: Dict, summary: str) -> str:
        return textwrap.dedent(f"""
            {article['title']}

            {article['description']}

            {summary}

            {article['url']}
        """)

    def _create_html_body(self, article: Dict, summary: str, summary_id: str, image_url: Optional[str] = None) -> str:
        domain = self.config.domain

        return f"""
            <html>
            <head>
                <style>
                    .header-image {{
                        width: 100%;
                        max-width: 600px;
                        max-height: 512px;
                        height: auto;
                        border-radius: 8px;
                        margin: 20px 0;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                        object-fit: contain;
                    }}
                    .rating-container {{
                        margin: 20px 0;
                        text-align: center;
                    }}
                    .star-link {{
                        text-decoration: none;
                        color: #666;
                        font-size: 16px;
                        padding: 12px 16px;
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
                {f'<img src="{image_url}" alt="Article illustration" class="header-image">' if image_url else ''}
                <p><strong>Description:</strong> {article['description']}</p>
                <p><strong>Summary:</strong> {summary}</p>
                <p>📰 <a href="{article['url']}">Read the full article</a></p>

                <div class="rating-container">
                    <p><strong>Rate this article:</strong></p>
                    <div>
                        <a href="{domain}/r1/{summary_id}" class="star-link" title="Dislike">🤢</a>
                        <a href="{domain}/r2/{summary_id}" class="star-link" title="Neutral">😐</a>
                        <a href="{domain}/r3/{summary_id}" class="star-link" title="Like">🤩</a>
                    </div>
                    <p class="rating-text">How would you rate this article?</p>
                </div>
            </body>
            </html>
        """

    def _send(self, subject: str, body: str, body_html: str) -> None:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.config.from_email
        msg["To"] = self.config.to_email
        msg.set_content(body)
        msg.add_alternative(body_html, subtype="html")

        with smtplib.SMTP_SSL(self.config.smtp_server, self.config.smtp_port) as smtp:
            smtp.login(self.config.from_email, self.config.smtp_password)
            smtp.send_message(msg)

    def _send_push_notification(self, article_title: str) -> None:
        """Send push notification via ntfy.sh"""
        try:
            ntfy_topic = getattr(self.config, 'ntfy_topic', None)
            if not ntfy_topic:
                self.logger.warning("⚠️  NTFY_TOPIC not configured, skipping push notification")
                return

            headers = {
                "Title": "NewsBot - Today's Article",
                "Tags": "newspaper,news",
                "Priority": "3",
                "Actions": "view, Open Gmail, googlegmail://, clear=true",
                "Content-Type": "text/plain; charset=utf-8"
            }

            response = requests.post(
                f"https://ntfy.sh/{ntfy_topic}",
                data=article_title.encode('utf-8'),
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                self.logger.info("📱  Push notification sent successfully!")
            else:
                self.logger.warning(f"⚠️  Push notification failed: HTTP {response.status_code}")

        except Exception as e:
            # Don't let push notification failures break email sending
            self.logger.error(f"❌  Failed to send push notification: {e}")
