import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    news_api_key: str = os.getenv("NEWS_API_KEY", "")
    from_email: str = os.getenv("FROM_EMAIL", "")
    to_email: str = os.getenv("TO_EMAIL", "")
    smtp_password: str = os.getenv("SMTP_PASS", "")
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 465
    openai_model: str = "gpt-3.5-turbo"
    domain: str = os.getenv("NEWSBOT_DOMAIN", "")
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    ntfy_topic: str = os.getenv("NTFY_TOPIC", "")
    email_enabled: bool = os.getenv("NEWSBOT_EMAIL_ENABLED", "false").lower() == "true"

    def validate(self) -> bool:
        required_fields = [
            self.openai_api_key,
            self.news_api_key,
            self.supabase_url,
            self.supabase_key,
        ]

        if self.email_enabled:
            required_fields.extend([
                self.smtp_password,
                self.from_email,
                self.to_email,
            ])

        return all(field for field in required_fields)
