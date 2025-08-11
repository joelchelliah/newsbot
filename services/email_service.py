from email.message import EmailMessage
import smtplib
import textwrap
from logger import get_logger


class EmailService:
    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

    def send_email(self, article, summary, summary_id, subject, image_url=None):
        body = self._create_body(article, summary)
        body_html = self._create_html_body(article, summary, summary_id, image_url)

        self._send(subject, body, body_html)
        self.logger.info("📧   News email sent successfully!")

    def _create_body(self, article, summary):
        return textwrap.dedent(f"""
            {article['title']}

            {article['description']}

            {summary}

            {article['url']}
        """)

    def _create_html_body(self, article, summary, summary_id, image_url=None):
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
                {f'<img src="{image_url}" alt="Article illustration" class="header-image">' if image_url else ''}
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

    def _send(self, subject, body, body_html):
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.config.from_email
        msg["To"] = self.config.to_email
        msg.set_content(body)
        msg.add_alternative(body_html, subtype="html")

        with smtplib.SMTP_SSL(self.config.smtp_server, self.config.smtp_port) as smtp:
            smtp.login(self.config.from_email, self.config.smtp_password)
            smtp.send_message(msg)
