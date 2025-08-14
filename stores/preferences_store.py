from config import Config
from logger import get_logger
from supabase import create_client, Client
import json


class PreferencesStore:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PreferencesStore, cls).__new__(cls)
        return cls._instance

    def __init__(self, config: Config):
        if not self._initialized:
            self.config = config
            self.logger = get_logger()

            self.supabase: Client = create_client(
                config.supabase_url,
                config.supabase_key
            )

            PreferencesStore._initialized = True
            self.logger.info("✅  PreferencesStore initialized")

    def get_preferences(self) -> dict:
        try:
            response = self.supabase.table('preferences').select('preferences').eq('is_latest', True).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]['preferences']
            else:
                self.logger.warning("🤷  No preferences found in Supabase. Using config default.")
                return self._parse_config_default()

        except Exception as e:
            self.logger.error(f"❌  Failed to get preferences from Supabase: {e}. Using config default.")
            return self._parse_config_default()

    def get_history(self) -> list:
        try:
            response = self.supabase.table('preferences').select('preferences, version, created_at').order('version', desc=True).limit(20).execute()

            if response.data:
                return [json.dumps(item['preferences']) for item in response.data]
            else:
                self.logger.warning("🤷  No preferences history found in Supabase.")
                return []

        except Exception as e:
            self.logger.error(f"❌  Failed to get preferences history from Supabase: {e}")
            return []

    def update_preferences(self, new_preferences) -> bool:
        try:
            # Handle both dict and string inputs
            if isinstance(new_preferences, str):
                preferences_dict = json.loads(new_preferences)
            else:
                preferences_dict = new_preferences

            response = self.supabase.table('preferences').select('version').order('version', desc=True).limit(1).execute()
            current_version = 1
            if response.data and len(response.data) > 0:
                current_version = response.data[0]['version'] + 1

            self.supabase.table('preferences').update({'is_latest': False}).eq('is_latest', True).execute()
            self.supabase.table('preferences').insert({
                'preferences': preferences_dict,
                'version': current_version,
                'is_latest': True
            }).execute()

            return True

        except Exception as e:
            self.logger.error(f"❌  Failed to save preferences to Supabase: {e}")
            return False

    def _parse_config_default(self) -> dict:
        if not self.config.preferences:
            return {}

        try:
            return json.loads(self.config.preferences)
        except json.JSONDecodeError:
            self.logger.warning("❌  Config default preferences is not valid JSON, using empty dict.")
            return {}
