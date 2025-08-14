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

    def select_best_article(self, articles: list, preferences) -> dict:
        if not articles or len(articles) == 0:
            return None

        article_texts = [f"Title: {a['title']}\nDescription: {a['description']}" for a in articles[:10]]
        self.logger.info(f"🔍  Selecting the best article from the top {len(article_texts)} articles")

        # Convert preferences to JSON string if it's a dict
        preferences_json = json.dumps(preferences) if isinstance(preferences, dict) else preferences

        response = self.client.chat.completions.create(
            model=self.config.openai_model,
            messages=[
                {"role": "system", "content": f"""Select the most interesting and important article from the list. Consider quality, impact and user preferences.

User preferences (JSON format with keyword scores 1-5, higher is better):
{preferences_json}

Use these preferences to guide your selection. Higher scored keywords (4,5) indicate stronger user interest. A lower score (1,2) means that these should generally be avoided. A score of 3 is neutral."""},
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

    def update_preferences_from_rating(self, current_preferences: dict, rating: int, article_summary: str) -> dict:
        try:
            current_prefs = current_preferences or {}

            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": f"""You are an AI that extracts relevant keywords from news articles.

Here are the current user preferences (JSON format with keyword scores 1-5) just as an example. The keywords do not need to match these preferences exactly, but should be relevant to the article summary:
{json.dumps(current_prefs, indent=2)}

Extract 3-8 relevant keywords from the article summary. Focus on:
- Main topics/themes
- Content types
- Subject areas
- Key concepts

Return only the keywords as a comma-separated list, no explanations."""},
                    {"role": "user", "content": f"Extract keywords from this article summary: {article_summary}"}
                ],
                max_tokens=100,
                temperature=0.3,
            )

            # Parse extracted keywords
            keywords_text = self._parse_response(response, "extract_keywords")
            if not keywords_text:
                self.logger.warning("❌  Failed to extract keywords from article. Returning current preferences.")
                return current_preferences

            # Clean and normalize keywords
            extracted_keywords = []
            for keyword in keywords_text.split(','):
                clean_keyword = keyword.strip().lower()
                if clean_keyword and len(clean_keyword) > 2:
                    extracted_keywords.append(clean_keyword)

            if not extracted_keywords:
                self.logger.warning("❌  No valid keywords extracted. Returning current preferences.")
                return current_preferences

            updated_prefs = current_prefs.copy()

            # Process keywords from the article
            for keyword in extracted_keywords:
                if keyword not in updated_prefs:
                    # Add new keyword with initial score based on rating (1-3 scale)
                    if rating == 3:
                        base_score = 4  # High initial score for liked content
                    elif rating == 1:
                        base_score = 2  # Low initial score for disliked content
                    else:  # rating == 2
                        base_score = 3  # Neutral score
                    updated_prefs[keyword] = base_score
                else:
                    # Update existing keyword score
                    if rating == 3:
                        updated_prefs[keyword] = min(5, updated_prefs[keyword] + 1)
                    elif rating == 1:
                        updated_prefs[keyword] = max(1, updated_prefs[keyword] - 1)
                    # rating == 2: no change (neutral)

            self.logger.info(f"📝  Updated preferences based on {rating}-star rating: {updated_prefs}")
            return updated_prefs

        except Exception as e:
            self.logger.error(f"❌  Error updating preferences from rating: {e}")
            return current_preferences or {}

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
