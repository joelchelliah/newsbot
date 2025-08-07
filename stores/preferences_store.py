from config import Config
from logger import get_logger

class PreferencesStore:
    _instance = None
    _preferences = None
    _history = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PreferencesStore, cls).__new__(cls)
        return cls._instance

    def __init__(self, config: Config):
        if not self._initialized:
            self.config = config
            self.logger = get_logger()

            PreferencesStore._preferences = config.preferences
            PreferencesStore._history = []
            PreferencesStore._initialized = True

            self.logger.info("Using in-memory preferences storage (singleton)")

    def get_preferences(self) -> str:
        self.logger.info("Getting preferences from memory")
        return PreferencesStore._preferences

    def get_history(self) -> list:
        self.logger.info("Getting history from memory")
        return PreferencesStore._history

    def update_preferences(self, new_preferences: str) -> bool:
        try:
            self.logger.info("Saving preferences to memory")

            current_preferences = PreferencesStore._preferences

            if current_preferences != new_preferences and (not PreferencesStore._history or current_preferences != PreferencesStore._history[0]):
                PreferencesStore._history.insert(0, current_preferences)
                PreferencesStore._history = PreferencesStore._history[:20] # Max 20 entries

            PreferencesStore._preferences = new_preferences
            return True
        except Exception as e:
            self.logger.error(f"Failed to save preferences to memory: {e}")
            return False
