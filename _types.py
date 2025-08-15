from typing import TypedDict, List

class PreferenceWithEmbedding(TypedDict):
    score: int  # Range: -5 to 5 (negative = disliked, positive = liked)
    embedding: List[float]

class PreferencesWithEmbeddings(TypedDict):
    __annotations__: dict[str, PreferenceWithEmbedding]
