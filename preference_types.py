from typing import TypedDict, List

class PreferenceWithEmbedding(TypedDict):
    score: int
    embedding: List[float]

class PreferencesWithEmbeddings(TypedDict):
    __annotations__: dict[str, PreferenceWithEmbedding]
