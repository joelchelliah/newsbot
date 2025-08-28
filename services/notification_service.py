from email.message import EmailMessage
import smtplib
import textwrap
import requests
from logger import get_logger
from typing import Dict, Optional
from config import Config


class NotificationService:
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger()

    def notify(self, article: Dict, summary: str, subject: str, image_url: Optional[str] = None, article_id: Optional[str] = None) -> None:
        if self.config.email_enabled:
            body = self._create_email_body(article, summary)
            body_html = self._create_email_html_body(article, summary, image_url, article_id)

            self._send_email(subject, body, body_html)
            self.logger.info("📧   News email sent successfully!")
        else:
            self.logger.debug("📧   Email sending disabled - skipping email")

        self._send_push_notification(article['title'], article_id)

    def _create_email_body(self, article: Dict, summary: str) -> str:
        return textwrap.dedent(f"""
            {article['title']}

            {article['description']}

            {summary}

            {article['url']}
        """)

    def _create_email_html_body(self, article: Dict, summary: str, image_url: Optional[str] = None, article_id: Optional[str] = None) -> str:
        domain = self.config.domain

        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{article['title']} - NewsBot</title>
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
                    max-width: 600px;
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
                    font-size: 1.6rem;
                }}
                .meta {{
                    color: #666;
                    font-size: 0.9rem;
                    margin-bottom: 20px;
                }}
                .image {{
                    width: 100%;
                    max-height: 300px;
                    object-fit: cover;
                    border-radius: 8px;
                    margin: 20px 0;
                }}
                .summary {{
                    background: #e8f4fd;
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #3498db;
                    margin-bottom: 20px;
                }}
                .source-link {{
                    margin: 20px 0;
                    text-align: center;
                }}
                .source-link a {{
                    color: #3498db;
                    text-decoration: none;
                    font-weight: 500;
                }}
                .article-btn {{
                    display: inline-block;
                    background: #3498db;
                    color: white;
                    padding: 15px 30px;
                    border-radius: 25px;
                    text-decoration: none;
                    font-weight: 600;
                    font-size: 1.1rem;
                    margin: 20px auto;
                    text-align: center;
                    box-shadow: 0 2px 10px rgba(52, 152, 219, 0.3);
                }}
                .cta-section {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 2px solid #e0e0e0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{article['title']}</h1>
                    <div class="meta">📰 NewsBot • Today's Article</div>
                </div>

                {f'<img src="{image_url}" alt="Article image" class="image">' if image_url else ''}

                <div class="summary">
                    <strong>📋 Summary:</strong><br>
                    {summary}
                </div>

                <div class="source-link">
                    <a href="{article['url']}" target="_blank">📖 Read original source</a>
                </div>

                <div class="cta-section">
                    <p><strong>Read the full article and rate your preferences:</strong></p>
                    <a href="{domain}/article/{article_id}" class="article-btn">📰 Open Full Article</a>
                </div>
            </div>
        </body>
        </html>
        """

    def _send_email(self, subject: str, body: str, body_html: str) -> None:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.config.from_email
        msg["To"] = self.config.to_email
        msg.set_content(body)
        msg.add_alternative(body_html, subtype="html")

        with smtplib.SMTP_SSL(self.config.smtp_server, self.config.smtp_port) as smtp:
            smtp.login(self.config.from_email, self.config.smtp_password)
            smtp.send_message(msg)

    def _send_push_notification(self, article_title: str, article_id: Optional[str] = None) -> None:
        """Send push notification via ntfy.sh"""
        try:
            ntfy_topic = getattr(self.config, 'ntfy_topic', None)
            if not ntfy_topic:
                self.logger.warning("⚠️  NTFY_TOPIC not configured, skipping push notification")
                return

            action = "view, Open Article, {}/article/{}, clear=true".format(self.config.domain, article_id) if article_id else "view, Open Gmail, googlegmail://, clear=true"

            headers = {
                "Title": "NewsBot - Today's Article",
                "Tags": "newspaper,news",
                "Priority": "3",
                "Actions": action,
                "Content-Type": "text/plain; charset=utf-8"
            }

            message = f"{article_title}\n\nTap 'Open Article' to read the full story and rate your preferences!" if article_id else article_title

            response = requests.post(
                f"https://ntfy.sh/{ntfy_topic}",
                data=message.encode('utf-8'),
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                self.logger.info("📱  Push notification sent successfully!")
            else:
                self.logger.warning(f"⚠️  Push notification failed: HTTP {response.status_code}")

        except Exception as e:
            self.logger.error(f"❌  Failed to send push notification: {e}")
