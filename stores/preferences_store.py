from config import Config
from logger import get_logger
from supabase import create_client, Client


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

    def get_preferences(self) -> str:
        try:
            response = self.supabase.table('preferences').select('preferences').eq('is_latest', True).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]['preferences']
            else:
                self.logger.warning("No preferences found in Supabase, using config default")
                return self.config.preferences

        except Exception as e:
            self.logger.error(f"Failed to get preferences from Supabase: {e}")
            return self.config.preferences

    def get_history(self) -> list:
        try:
            response = self.supabase.table('preferences').select('preferences, version, created_at').order('version', desc=True).limit(20).execute()

            if response.data:
                return [item['preferences'] for item in response.data]
            else:
                return []

        except Exception as e:
            self.logger.error(f"Failed to get preferences history from Supabase: {e}")
            return []

    def update_preferences(self, new_preferences: str) -> bool:
        try:
            response = self.supabase.table('preferences').select('version').order('version', desc=True).limit(1).execute()
            current_version = 1
            if response.data and len(response.data) > 0:
                current_version = response.data[0]['version'] + 1

            self.supabase.table('preferences').update({'is_latest': False}).eq('is_latest', True).execute()
            self.supabase.table('preferences').insert({
                'preferences': new_preferences,
                'version': current_version,
                'is_latest': True
            }).execute()

            self.logger.info(f"Updated preferences. Latest version: {current_version}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save preferences to Supabase: {e}")
            return False
