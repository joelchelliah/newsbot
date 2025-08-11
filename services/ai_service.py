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
        self.logger.info(f"Summarizing article")
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

    def update_preferences_from_rating(self, current_preferences: str, rating: int, article_summary: str) -> str:
        try:
            self.logger.info(f"Updating preferences based on {rating}-star rating")

            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": f"""You are an AI that helps update user preferences for news articles.

IMPORTANT: You must PRESERVE all existing preferences and only ADD or MODIFY based on the rating.

Current user preferences: {current_preferences}

Based on the provided rating and article summary, update the user's preferences to better reflect what they like.
- If they gave a high rating (4-5 stars), ADD similar topics, ideas, or writing styles to existing preferences
- If they gave a low rating (1-2 stars), ADD negative preferences to avoid similar content
- If they gave a neutral rating (3 stars), make minor adjustments or clarifications
- ALWAYS keep ALL existing preferences and only ADD new ones or MODIFY relevant existing ones
- Keep the preferences concise, actionable, and keyword-based
- DO NOT separate preferences into 'Current preferences' and 'Updated preferences'. It should be a single concise list.
- If the prefereces contain a keyword that is both positively-weighted and negatively-weighted, remove that keyword.
- Return the MERGED preferences including original preferences plus any additions/modifications, and removing duplicates, as a single list."""},
                    {"role": "user", "content": f"Please update my preferences based on my {rating}-star rating of this article. The article summary is: {article_summary}. Remember to keep ALL my existing preferences and only add or modify based on this specific article."}
                ],
                max_tokens=300,
                temperature=0.3,
            )

            updated_preferences = self._parse_response(response, "update_preferences_from_rating")

            if updated_preferences and updated_preferences.strip():
                self.logger.info(f"Successfully updated preferences based on {rating}-star rating: {updated_preferences}")
                return updated_preferences.strip()
            else:
                self.logger.warning("Failed to get updated preferences from AI")
                return current_preferences

        except Exception as e:
            self.logger.error(f"Error updating preferences from rating: {e}")
            return current_preferences

    def generate_image(self, article_title: str, summary: str) -> str:
        try:
            self.logger.info("🎨   Generating cartoon image for article")

            prompt = f"""Create a fun, cartoon-style illustration for a news article.

Article Title: {article_title}
Summary: {summary}

Style: Cartoon, comic, friendly, colorful, engaging, professional but playful
Format: Digital illustration, suitable for email header
Tone: Light and engaging, not too serious
Size: Wide format, suitable for email header (2:1 ratio)"""

            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x512",
                quality="standard",
                n=1,
            )

            if response.data and len(response.data) > 0:
                image_url = response.data[0].url
                self.logger.info("Successfully generated image")
                return image_url
            else:
                self.logger.warning("❌  Failed to generate image")
                return ""

        except Exception as e:
            self.logger.error(f"❌  Error generating image: {e}")
            return ""

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
