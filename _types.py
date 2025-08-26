from typing import TypedDict, List, Dict

class PreferenceWithEmbedding(TypedDict):
    score: int  # Range: -5 to 5 (negative = disliked, positive = liked)
    embedding: List[float]

# Type alias for preferences with embeddings
PreferencesWithEmbeddings = Dict[str, PreferenceWithEmbedding]
