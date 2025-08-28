from email.message import EmailMessage
import smtplib
import textwrap
import requests
from logger import get_logger
from typing import Dict, Optional
from config import Config
from utils import render_template


class NotificationService:
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger()


    def notify(self, article: Dict, summary: str, subject: str, image_url: Optional[str] = None, article_id: Optional[str] = None) -> None:
        if self.config.email_enabled:
            body = self._create_email_body(article, summary)
            body_html = render_template('email.html',
                title=article['title'],
                image_html=f'<img src="{image_url}" alt="Article image" class="image">' if image_url else '',
                summary=summary,
                original_url=article['url'],
                article_url=f"{self.config.domain}/article/{article_id}" if article_id else '#'
            )

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
            self.logger.error(f"❌  Failed to send push notification: {e}")
