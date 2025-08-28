from newspaper import Article
from logger import get_logger
from typing import Optional
from _types import ExtractedArticleData


class ExtractionService:
    def __init__(self):
        self.logger = get_logger()

    def extract_article_content(self, url: str) -> Optional[ExtractedArticleData]:
        try:
            article = Article(url)
            article.download()
            article.parse()

            if not article.text:
                self.logger.warning(f"❌  No text content extracted from {url}")
                return None

            return {
                'title': article.title or "Untitled",
                'content': article.text,
                'authors': article.authors,
                'publish_date': article.publish_date,
                'top_image': article.top_image,
                'url': url
            }

        except Exception as e:
            self.logger.error(f"❌  Failed to extract article content from {url}: {e}")
            return None
