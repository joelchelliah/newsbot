import requests
import datetime
from config import Config
from logger import get_logger


class NewsApiService:
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger()

    def fetch_top_news_articles(self, days_back: int = 1) -> list:
        today = datetime.date.today()
        from_date = today - datetime.timedelta(days=days_back)

        url = "https://newsapi.org/v2/everything"
        params = {
            "q": "world",
            "from": from_date,
            "to": today,
            "language": "en",
            "sortBy": "popularity"
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers={"Authorization": self.config.news_api_key},
                timeout=30
            )
            response.raise_for_status()

            articles = response.json().get("articles", [])
            self.logger.info(f"Found {len(articles)} articles from {from_date} to {today}")

            return articles if articles else []

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch news: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error fetching news: {e}")
            return []
