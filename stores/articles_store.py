import uuid
import datetime
from logger import get_logger
from supabase import create_client, Client
from config import Config
from typing import Optional, Any, Dict
from _types import ExtractedArticleData

ARTICLE_RETENTION_DAYS = 30

class ArticlesStore:
    _instance = None
    _initialized = False

    def __new__(cls, *args: Any, **kwargs: Any) -> 'ArticlesStore':
        if cls._instance is None:
            cls._instance = super(ArticlesStore, cls).__new__(cls)
        return cls._instance

    def __init__(self, config: Config):
        if not self._initialized:
            self.config = config
            self.logger = get_logger()

            self.supabase: Client = create_client(
                config.supabase_url,
                config.supabase_key
            )

            ArticlesStore._initialized = True
            self.logger.info("✅  ArticlesStore initialized")

    def store_article(self, article_data: ExtractedArticleData, summary: str, image_url: Optional[str] = None) -> str:
        article_id = str(uuid.uuid4())

        try:
            self.supabase.table('articles').insert({
                'id': article_id,
                'title': article_data['title'],
                'summary': summary,
                'content': article_data['content'],
                'url': article_data['url'],
                'image_url': image_url,
                'created_at': datetime.datetime.now().isoformat(),
                'expires_at': (datetime.datetime.now() + datetime.timedelta(days=ARTICLE_RETENTION_DAYS)).isoformat()
            }).execute()

            self.logger.info(f"📄  Stored article with ID: {article_id}")
            return article_id

        except Exception as e:
            self.logger.error(f"❌  Failed to store article in Supabase: {e}")
            return ""

    def get_article(self, article_id: str) -> Optional[Dict]:
        try:
            response = self.supabase.table('articles').select('*').eq('id', article_id).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            else:
                self.logger.warning(f"Article not found for ID: {article_id}")
                return None

        except Exception as e:
            self.logger.error(f"❌  Failed to get article from Supabase: {e}")
            return None

    def cleanup_old_articles(self) -> None:
        try:
            cutoff_time = datetime.datetime.now().isoformat()

            response = self.supabase.table('articles').delete().lt('expires_at', cutoff_time).execute()
            if response.data:
                self.logger.info(f"🧹  Cleaned up {len(response.data)} expired articles")

        except Exception as e:
            self.logger.error(f"❌  Failed to cleanup old articles: {e}")
