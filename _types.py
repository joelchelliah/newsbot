from typing import TypedDict, List, Dict, Optional
from datetime import datetime

class PreferenceWithEmbedding(TypedDict):
    score: int  # Range: -5 to 5 (negative = disliked, positive = liked)
    embedding: List[float]

class ExtractedArticleData(TypedDict):
    title: str
    content: str
    authors: List[str]
    publish_date: Optional[datetime]
    top_image: Optional[str]
    url: str

# Type alias for preferences with embeddings
PreferencesWithEmbeddings = Dict[str, PreferenceWithEmbedding]
