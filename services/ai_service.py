import openai
import json
import numpy as np
from newspaper import Article
from config import Config
from logger import get_logger
from _types import PreferencesWithEmbeddings
from typing import List, Dict, Optional, Any


class AIService:
    def __init__(self, config: Config):
        self.config = config
        self.client = openai.OpenAI(api_key=config.openai_api_key)
        self.logger = get_logger()


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

    def generate_image(self, article_title: str, summary: str) -> str:
        def _generate_with_prompt(prompt: str) -> str:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1792x1024",
                quality="standard",
                n=1,
            )
            if response.data and len(response.data) > 0:
                return response.data[0].url
            return ""

        try:
            specific_prompt = f"""Create a fun, cartoon-style illustration for a news article.

Article Title: {article_title}
Summary: {summary}

Style: Cartoon, comic, friendly, colorful, engaging, professional but playful
Format: Digital illustration, suitable for email header
Tone: Light and engaging, not too serious
Size: Wide format, suitable for email header (2:1 ratio)"""

            image_url = _generate_with_prompt(specific_prompt)
            if image_url:
                self.logger.info("🎨  Generated specific image for article")
                return image_url

        except Exception as e:
            self.logger.warning(f"⚠️  Failed to generate specific image ({e}), trying generic image")

        try:
            # Fall back to generic image if specific generation fails
            generic_prompt = """Create a fun, cartoon-style illustration for a news article.

Style: Cartoon, comic, friendly, colorful, engaging, professional but playful
Format: Digital illustration, suitable for email header
Tone: Light and engaging, not too serious
Size: Wide format, suitable for email header (2:1 ratio)
Content: Generic news reading scene with newspapers, coffee, and reading glasses"""

            image_url = _generate_with_prompt(generic_prompt)
            if image_url:
                self.logger.info("🎨  Generated generic image for article")
                return image_url

        except Exception as e:
            self.logger.error(f"❌  Failed to generate generic image: {e}")

        return ""


    def select_best_article_with_embeddings(self, articles: List[Dict], preferences_with_embeddings: PreferencesWithEmbeddings) -> Optional[Dict]:
        """Select best article using embedding-based similarity"""
        if not articles or len(articles) == 0:
            return None

        self.logger.info(f"🔍 Selecting best article using embeddings from {len(articles)} articles")

        best_article = articles[0]  # Always have a fallback
        best_score = float('-inf')  # Start with lowest possible score

        for article in articles:
            # Create text representation of article
            article_text = f"Title: {article['title']}\nDescription: {article['description']}"

            # Get embedding for this article
            article_embedding = self.get_embedding(article_text)

            # Calculate total preference score
            total_score = 0
            for pref_name, pref_data in preferences_with_embeddings.items():
                # Calculate similarity between article and this preference
                similarity = self.cosine_similarity(article_embedding, pref_data["embedding"])

                # Weight by user's preference score (1-5)
                weighted_score = similarity * pref_data["score"]
                total_score += weighted_score

                self.logger.debug(f"  {pref_name}: similarity={similarity:.3f}, score={pref_data['score']}, weighted={weighted_score:.3f}")

            self.logger.debug(f"  Article '{article['title'][:50]}...': total_score={total_score:.3f}")

            if total_score > best_score:
                best_score = total_score
                best_article = article

        self.logger.info(f"✅ Selected article with embeddings: {best_article['title']} (score: {best_score:.3f})")
        return best_article

    def update_preferences_from_rating_with_embeddings(self, current_preferences: PreferencesWithEmbeddings, rating: int, article_summary: str) -> PreferencesWithEmbeddings:
        try:
            current_prefs = current_preferences or {}

            article_summary_embedding = self.get_embedding(article_summary)

            # Find existing preferences that are semantically similar to the entire article summary
            # Overkill?
            existing_prefs_similar_to_article_summary = self._find_preferences_with_similar_embeddings(current_prefs, article_summary_embedding)

            current_pref_keywords = list(current_prefs.keys()) if current_prefs else []

            extracted_keywords_from_article = self._extract_relevant_keywords_from_text(article_summary, current_pref_keywords)

            if not extracted_keywords_from_article:
                self.logger.warning("❌  No valid keywords extracted from article summary. Aborting update!")
                return current_preferences

            updated_prefs = self._update_preferences_based_on_embeddings_and_keywords(
                current_prefs,
                existing_prefs_similar_to_article_summary,
                extracted_keywords_from_article,
                rating
            )

            self.logger.info(f"📝 Updated preferences with embeddings based on {rating}-star rating: {len(updated_prefs)} preferences")
            self.logger.debug(f"  Similar preferences updated: {list(existing_prefs_similar_to_article_summary.keys())}")
            self.logger.debug(f"  New keywords added: {extracted_keywords_from_article}")

            return updated_prefs

        except Exception as e:
            self.logger.error(f"❌ Error updating preferences from rating with embeddings: {e}")
            return current_preferences or {}

    def _extract_relevant_keywords_from_text(self, text: str, current_keywords: List[str]) -> List[str]:
        """Extract, clean, and normalize relevant keywords from text"""
        try:
            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": f"""You are an AI that extracts relevant keywords from news articles.

Here are the current user preferences as examples. The keywords do not need to match these preferences exactly, but should be relevant to the article summary:
{", ".join(current_keywords)}

Extract 3-8 relevant keywords from the article summary. Focus on:
- Main topics/themes
- Content types
- Subject areas
- Key concepts

Return only the keywords as a comma-separated list, no explanations."""},
                    {"role": "user", "content": f"Extract keywords from this article summary: {text}"}
                ],
                max_tokens=100,
                temperature=0.3,
            )

            # Parse extracted keywords
            keywords_text = self._parse_response(response, "extract_keywords")
            if not keywords_text:
                self.logger.warning("❌ Failed to extract keywords from article.")
                return []

            # Clean and normalize keywords
            extracted_keywords = []
            for keyword in keywords_text.split(','):
                clean_keyword = keyword.strip().lower()
                if clean_keyword and len(clean_keyword) > 2:
                    extracted_keywords.append(clean_keyword)

            self.logger.debug(f"  Extracted keywords: {extracted_keywords}")
            return extracted_keywords

        except Exception as e:
            self.logger.error(f"❌ Error extracting keywords: {e}")
            return []

    def _find_preferences_with_similar_embeddings(self, current_preferences: PreferencesWithEmbeddings, article_embedding: List[float]) -> Dict:
        """Find existing preferences that are semantically similar to the article"""
        similar_preferences = {}

        for keyword, data in current_preferences.items():
            if isinstance(data, dict) and "embedding" in data:
                # Calculate similarity between article and this preference
                similarity = self.cosine_similarity(article_embedding, data["embedding"])
                if similarity > 0.3:  # Only consider reasonably similar preferences
                    similar_preferences[keyword] = {
                        "similarity": similarity,
                        "current_score": data["score"]
                    }

        return similar_preferences

    def _update_preferences_based_on_embeddings_and_keywords(self, current_preferences: PreferencesWithEmbeddings, similar_preferences: Dict, extracted_keywords: List[str], rating: int) -> PreferencesWithEmbeddings:
        """Update preferences based on article similarity and extracted keywords"""
        updated_prefs = current_preferences.copy()
        updated_preference_keys = set()

        # Step 1: Update preferences similar to the article summary
        for keyword, info in similar_preferences.items():
            current_score = info["current_score"]
            similarity = info["similarity"]

            # Adjust score based on rating and similarity strength
            if rating == 3:
                boost = 1 if similarity > 0.7 else 0.5
                updated_prefs[keyword]["score"] = min(5, current_score + boost)
            elif rating == 1:
                reduction = 1 if similarity > 0.7 else 0.5
                updated_prefs[keyword]["score"] = max(1, current_score - reduction)
            # rating == 2: no change (neutral)

            updated_preference_keys.add(keyword)
            self.logger.debug(f"  Updated similar preference '{keyword}' (article similarity: {similarity:.3f})")

        # Step 2: Process each extracted keyword
        for keyword in extracted_keywords:
            if keyword not in updated_prefs:
                # NEW KEYWORD: Add with initial score
                base_score = self._get_initial_score_for_rating(rating)
                keyword_embedding = self.get_embedding(keyword)
                updated_prefs[keyword] = {
                    "score": base_score,
                    "embedding": keyword_embedding
                }
                self.logger.debug(f"  Added new preference '{keyword}' with score {base_score}")
            else:
                # EXISTING KEYWORD: Handle if not already updated
                if keyword not in updated_preference_keys:
                    self._handle_existing_keyword_update(
                        updated_prefs,
                        current_preferences,
                        updated_preference_keys,
                        keyword,
                        rating
                    )

        return updated_prefs

    def _get_initial_score_for_rating(self, rating: int) -> int:
        if rating == 3:
            return 4  # High initial score for liked content
        elif rating == 1:
            return -2  # Negative score for disliked content
        else:  # rating == 2
            return 0  # Neutral score (no preference)

    def _handle_existing_keyword_update(self, updated_prefs: PreferencesWithEmbeddings, current_prefs: PreferencesWithEmbeddings, updated_preference_keys: set, keyword: str, rating: int) -> None:
        """Handle updating an existing keyword preference"""
        # Check for semantic similarity first
        keyword_updated = self._update_similar_preferences_via_keyword(
            updated_prefs, current_prefs, updated_preference_keys, keyword, rating
        )

        # If no semantic similarity found, update the keyword itself
        if not keyword_updated:
            self._update_keyword_score(updated_prefs, keyword, rating)

    def _update_similar_preferences_via_keyword(self, updated_prefs: PreferencesWithEmbeddings, current_prefs: PreferencesWithEmbeddings, updated_preference_keys: set, keyword: str, rating: int) -> bool:
        """Update preferences that are similar to the given keyword"""
        if not isinstance(current_prefs[keyword], dict) or "embedding" not in current_prefs[keyword]:
            return False

        keyword_embedding = self.get_embedding(keyword)

        for existing_keyword, data in current_prefs.items():
            if existing_keyword == keyword or existing_keyword in updated_preference_keys:
                continue  # Skip self or already updated

            if isinstance(data, dict) and "embedding" in data:
                keyword_similarity = self.cosine_similarity(keyword_embedding, data["embedding"])

                if keyword_similarity > 0.7:  # High similarity threshold
                    current_score = data["score"]
                    new_score = self._calculate_new_score(current_score, rating, keyword_similarity)

                    updated_prefs[existing_keyword]["score"] = new_score
                    updated_preference_keys.add(existing_keyword)

                    self.logger.debug(f"  Updated similar preference '{existing_keyword}' via keyword '{keyword}' (similarity: {keyword_similarity:.3f})")
                    return True

        return False

    def cosine_similarity(self, vector_a: List[float], vector_b: List[float]) -> float:
        try:
            # Convert to numpy arrays
            a = np.array(vector_a)
            b = np.array(vector_b)

            # Cosine similarity formula: dot product / (magnitude_a * magnitude_b)
            dot_product = np.dot(a, b)
            magnitude_a = np.linalg.norm(a)
            magnitude_b = np.linalg.norm(b)

            # Avoid division by zero
            if magnitude_a == 0 or magnitude_b == 0:
                return 0.0

            similarity = dot_product / (magnitude_a * magnitude_b)

            # Ensure result is between -1 and 1
            return max(-1.0, min(1.0, similarity))

        except Exception as e:
            self.logger.error(f"❌  Error calculating cosine similarity: {e}. Returning 0.0.")
            return 0.0

    def _update_keyword_score(self, updated_prefs: PreferencesWithEmbeddings, keyword: str, rating: int) -> None:
        if isinstance(updated_prefs[keyword], dict) and "score" in updated_prefs[keyword]:
            current_score = updated_prefs[keyword]["score"]
        else:
            current_score = updated_prefs[keyword]

        new_score = self._calculate_new_score(current_score, rating, 1.0)  # Exact match = 1.0 similarity

        # Ensure the preference has embedding data
        if isinstance(updated_prefs[keyword], dict) and "embedding" in updated_prefs[keyword]:
            updated_prefs[keyword]["score"] = new_score
        else:
            # Generate embedding for existing keyword that doesn't have one
            keyword_embedding = self.get_embedding(keyword)
            updated_prefs[keyword] = {
                "score": new_score,
                "embedding": keyword_embedding
            }

        self.logger.debug(f"  Updated exact match preference '{keyword}' from {current_score} to {new_score}")

    def _calculate_new_score(self, current_score: int, rating: int, similarity: float) -> int:
        """Calculate new preference score based on rating and similarity"""
        if rating == 3:
            boost = 1 if similarity > 0.7 else 0.5
            return min(5, current_score + boost)
        elif rating == 1:
            reduction = 1 if similarity > 0.7 else 0.5
            return max(-5, current_score - reduction)  # Allow negative scores
        else:  # rating == 2
            return current_score  # no change

    def get_embedding(self, text: str) -> List[float]:
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
                encoding_format="float"
            )

            return response.data[0].embedding

        except Exception as e:
            self.logger.error(f"❌  Error getting embedding: {e}. Returning zero vector.")
            return [0.0] * 1536

    def _parse_response(self, response: Any, function_name: str = "unknown") -> str:
        try:
            if response and response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            else:
                self.logger.warning(f"😖  Empty or malformed OpenAI response in <{function_name}>")
                return ""
        except Exception as e:
            self.logger.error(f"❌  Error parsing OpenAI response in <{function_name}>: {e}")
            return ""
