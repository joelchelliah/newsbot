import os
from typing import Any, Optional
from _types import ExtractedArticleData
from newspaper import Article, Config
from logger import get_logger
import time

def render_template(template_name: str, **kwargs: Any) -> str:
    template_path = os.path.join('templates', template_name)
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    for key, value in kwargs.items():
        template = template.replace(f'{{{{{key}}}}}', str(value))

    return template

def extract_article_content(url: str) -> Optional[ExtractedArticleData]:
    # Different user agents to try if one fails
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
    ]

    logger = get_logger()

    for i, user_agent in enumerate(user_agents):
        try:
            # Configure newspaper with user agent
            config = Config()
            config.browser_user_agent = user_agent
            config.request_timeout = 10

            article = Article(url, config=config)
            article.download()
            article.parse()

            if not article.text:
                logger.warning(f"⚠️  Article text is empty for URL: {url}")
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
            if i < len(user_agents) - 1:
                logger.debug(f"🔄  Retry {i+1} failed for {url}: {str(e)}")
                time.sleep(1)  # Brief delay before retry
                continue
            else:
                logger.error(f"❌  Error extracting article content from {url}: {str(e)}")
                return None

    return None
