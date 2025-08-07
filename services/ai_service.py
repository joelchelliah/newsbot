import openai
import json
from newspaper import Article
from config import Config
from logger import get_logger


class AIService:
    def __init__(self, config: Config):
        self.config = config
        self.client = openai.OpenAI(api_key=config.openai_api_key)
        self.logger = get_logger()

    def select_best_article(self, articles: list, preferences: str) -> dict:
        if not articles or len(articles) == 0:
            return None

        article_texts = [f"Title: {a['title']}\nDescription: {a['description']}" for a in articles[:10]]
        self.logger.info(f"Selecting the best article from the top {len(article_texts)} articles, based on preferences: {preferences}")

        response = self.client.chat.completions.create(
            model=self.config.openai_model,
            messages=[
                {"role": "system", "content": f"Select the most interesting and important article from the list. Consider quality, impact and personal preferences: {preferences}"},
                {"role": "user", "content": "\n\n".join(article_texts)}
            ],
            functions=[{
                "name": "select_article",
                "description": "Select the best article from the list",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "index": {
                            "type": "integer",
                            "description": "Index of the selected article (0-based)",
                            "minimum": 0,
                            "maximum": len(articles) - 1
                        }
                    },
                    "required": ["index"]
                }
            }],
            function_call={"name": "select_article"}
        )

        function_call = response.choices[0].message.function_call
        if function_call and function_call.name == "select_article":
            args = json.loads(function_call.arguments)
            index = args.get("index", 0)

            if 0 <= index < len(articles):
                self.logger.info(f"Selected article index: {index}")
                return articles[index]
            else:
                self.logger.warning(f"AI returned invalid index {index}, using first article")
                return articles[0]
        else:
            self.logger.warning("AI didn't return structured response, using first article")
            return articles[0]

    def generate_subject_line(self, article_title: str, summary: str) -> str:
        response = self.client.chat.completions.create(
            model=self.config.openai_model,
            messages=[
                {"role": "system", "content": "Create a compelling email subject line (max 40 chars) for a news article."},
                {"role": "user", "content": f"Title: {article_title}\nSummary: {summary}"}
            ],
            max_tokens=45,
            temperature=0.7,
        )
        return self._parse_response(response, "generate_subject_line")

    def summarize_article(self, url: str) -> str:
        article = Article(url)
        article.download()
        article.parse()

        response = self.client.chat.completions.create(
            model=self.config.openai_model,
            messages=[
                {"role": "system", "content": "Summarize the following article in concise and simple language, in 6-10 lines. Include context and key takeaways."},
                {"role": "user", "content": article.text}
            ],
            max_tokens=400,
            temperature=0.3,
        )
        return self._parse_response(response, "summarize_article")

    def _parse_response(self, response, function_name: str = "unknown") -> str:
        try:
            if response and response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            else:
                self.logger.warning(f"Empty or malformed OpenAI response in <{function_name}>")
                return ""
        except Exception as e:
            self.logger.error(f"Error parsing OpenAI response in <{function_name}>: {e}")
            return ""
