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
    preferences: str = os.getenv("NEWSBOT_DEFAULT_PREFERENCES", "")

    def validate(self) -> bool:
        required_fields = [
            self.openai_api_key,
            self.news_api_key,
            self.smtp_password,
            self.from_email,
            self.to_email
        ]
        return all(field for field in required_fields)
