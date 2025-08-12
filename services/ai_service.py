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
        self.logger.info(f"🔍  Selecting the best article from the top {len(article_texts)} articles, based on preferences: {preferences}")

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
                return articles[index]
            else:
                self.logger.warning(f"❌  AI returned invalid index {index}, using first article")
                return articles[0]
        else:
            self.logger.warning("❌  AI didn't return structured response, using first article")
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

    def update_preferences_from_rating(self, current_preferences: str, rating: int, article_summary: str) -> str:
        try:
            self.logger.info(f"Updating preferences based on {rating}-star rating")

            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": f"""You are an AI that helps update user preferences for news articles.

IMPORTANT: You must PRESERVE all existing preferences and only ADD or MODIFY based on the rating.

Current user preferences: {current_preferences}

Based on the provided rating and article summary, intelligently update the user's preferences:
- For HIGH ratings (4-5 stars): Add topics, themes, or content types that are SIMILAR to what they liked
- For LOW ratings (1-2 stars): Add topics, themes, or content types to AVOID that are similar to what they disliked
- For NEUTRAL ratings (3 stars): Make minor clarifications or adjustments

CRITICAL RULES:
1. NEVER copy phrases directly from the article summary
2. Extract the UNDERLYING TOPICS, THEMES, or CONTENT TYPES from the article
3. Convert these into general preference keywords that would apply to similar content
4. Keep preferences concise, actionable, and keyword-based
5. Return a single merged list of all preferences (original + updates)
6. Remove any duplicates or conflicting preferences

Examples:
- If they dislike a "website closed on Monday" article → add "avoid: business hours updates, mundane operational news"
- If they like a "funny cat video" article → add "humor, animal content, viral videos"
- If they dislike a "philosophical debate" article → add "avoid: abstract philosophy, theoretical discussions\""""},
                    {"role": "user", "content": f"Please update my preferences based on my {rating}-star rating of this article. The article summary is: {article_summary}. Remember to keep ALL my existing preferences and only add or modify based on this specific article."}
                ],
                max_tokens=300,
                temperature=0.3,
            )

            updated_preferences = self._parse_response(response, "update_preferences_from_rating")

            if updated_preferences and updated_preferences.strip():
                self.logger.info(f"📝  Updated preferences based on {rating}-star rating: {updated_preferences}")
                return updated_preferences.strip()
            else:
                self.logger.warning("❌  Failed to get updated preferences from AI")
                return current_preferences

        except Exception as e:
            self.logger.error(f"❌  Error updating preferences from rating: {e}")
            return current_preferences

    def generate_image(self, article_title: str, summary: str) -> str:
        try:
            sanitized_content = self._ai_sanitize_for_image(article_title, summary)

            if sanitized_content.get('use_generic', False):
                self.logger.info("⚠️  AI flagged content as too sensitive, using generic image prompt")
                prompt = """Create a fun, cartoon-style illustration for a news article.

Style: Cartoon, comic, friendly, colorful, engaging, professional but playful
Format: Digital illustration, suitable for email header
Tone: Light and engaging, not too serious
Size: Wide format, suitable for email header (2:1 ratio)
Content: Generic news reading scene with newspapers, coffee, and reading glasses"""
            else:
                prompt = f"""Create a fun, cartoon-style illustration for a news article.

Article Title: {sanitized_content['title']}
Summary: {sanitized_content['summary']}

Style: Cartoon, comic, friendly, colorful, engaging, professional but playful
Format: Digital illustration, suitable for email header
Tone: Light and engaging, not too serious
Size: Wide format, suitable for email header (2:1 ratio)"""

            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1792x1024",
                quality="standard",
                n=1,
            )

            if response.data and len(response.data) > 0:
                image_url = response.data[0].url
                self.logger.info("🎨  Generated image for article")
                return image_url
            else:
                self.logger.warning("❌  Failed to generate image")
                return ""

        except Exception as e:
            self.logger.error(f"❌  Error generating image: {e}")
            return ""

    def _ai_sanitize_for_image(self, title: str, summary: str) -> dict:
        try:
            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": """You are an AI that sanitizes news content for image generation to avoid content policy violations.

Your task is to:
1. Clean the title and summary to make them suitable for DALL-E image generation
2. Replace problematic terms with safer alternatives
3. If content is too sensitive/violent/controversial, flag it for generic image use
4. Maintain the core meaning while making it image-generation friendly

Return a JSON object with:
- "title": cleaned title
- "summary": cleaned summary
- "use_generic": true if content is too sensitive for specific images, false otherwise

Examples of what to avoid: violence, graphic content, controversial political topics, sensitive personal issues"""},
                    {"role": "user", "content": f"Please sanitize this content for image generation:\nTitle: {title}\nSummary: {summary}"}
                ],
                functions=[{
                    "name": "sanitize_content",
                    "description": "Sanitize content for image generation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Cleaned title suitable for image generation"
                            },
                            "summary": {
                                "type": "string",
                                "description": "Cleaned summary suitable for image generation"
                            },
                            "use_generic": {
                                "type": "boolean",
                                "description": "True if content is too sensitive and should use generic image"
                            }
                        },
                        "required": ["title", "summary", "use_generic"]
                    }
                }],
                function_call={"name": "sanitize_content"}
            )

            function_call = response.choices[0].message.function_call
            if function_call and function_call.name == "sanitize_content":
                args = json.loads(function_call.arguments)
                return {
                    "title": args.get("title", title),
                    "summary": args.get("summary", summary),
                    "use_generic": args.get("use_generic", False)
                }
            else:
                self.logger.warning("❌  AI didn't return structured sanitization response")
                return {"title": title, "summary": summary, "use_generic": False}

        except Exception as e:
            self.logger.error(f"❌  Error sanitizing content with AI: {e}")
            return {"title": title, "summary": summary, "use_generic": False}

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
