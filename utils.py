import os
from typing import Any, Optional
from _types import ExtractedArticleData
from newspaper import Article

def render_template(template_name: str, **kwargs: Any) -> str:
    template_path = os.path.join('templates', template_name)
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    for key, value in kwargs.items():
        template = template.replace(f'{{{{{key}}}}}', str(value))

    return template

def extract_article_content(url: str) -> Optional[ExtractedArticleData]:
    try:
        article = Article(url)
        article.download()
        article.parse()

        if not article.text:
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
        return None
