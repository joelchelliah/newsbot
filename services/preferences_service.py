import json
import os
from config import Config
from logger import get_logger

class PreferencesService:
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger()
        self.file_path = os.getenv('PREFERENCES_FILE', 'data/preferences.json')

        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

        if not os.path.exists(self.file_path):
            self.logger.info(f"Creating preferences file at {self.file_path}")
            self.update_preferences(self.config.preferences)

    def get_preferences(self) -> str:
        try:
            self.logger.info(f"Getting preferences from {self.file_path}")
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    return data.get('preferences', self.config.preferences)
        except Exception:
            self.logger.error(f"Failed to get preferences from {self.file_path}")
            pass

        self.logger.info(f"Getting default preferences from config")
        return self.config.preferences

    def get_history(self) -> list:
        try:
            self.logger.info(f"Getting history from {self.file_path}")
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    return data.get('history', [])
        except Exception:
            self.logger.error(f"Failed to get history from {self.file_path}")
            pass
        return []

    def update_preferences(self, new_preferences: str) -> bool:
        try:
            self.logger.info(f"Saving preferences to {self.file_path}")

            current_preferences = self.get_preferences()
            history = self.get_history()

            if current_preferences != new_preferences and (not history or current_preferences != history[0]):
                history.insert(0, current_preferences)
                history = history[:20] # Max 20 entries

            data = {
                "preferences": new_preferences,
                "history": history
            }

            with open(self.file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception:
            self.logger.error(f"Failed to save preferences to {self.file_path}")
            return False
