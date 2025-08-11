import uuid
import datetime
from logger import get_logger
from supabase import create_client, Client
from config import Config


class SummariesStore:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SummariesStore, cls).__new__(cls)
        return cls._instance

    def __init__(self, config: Config):
        if not self._initialized:
            self.config = config
            self.logger = get_logger()

            self.supabase: Client = create_client(
                config.supabase_url,
                config.supabase_key
            )

            SummariesStore._initialized = True
            self.logger.info("✅  SummariesStore initialized")

    def store_summary(self, summary: str) -> str:
        summary_id = str(uuid.uuid4())

        try:
            self.supabase.table('summaries').insert({
                'id': summary_id,
                'summary': summary,
                'created_at': datetime.datetime.now().isoformat(),
                'expires_at': (datetime.datetime.now() + datetime.timedelta(hours=48)).isoformat()
            }).execute()

            self.logger.info(f"Stored summary with ID: {summary_id}")
            return summary_id

        except Exception as e:
            self.logger.error(f"❌  Failed to store summary in Supabase: {e}")
            return ""

    def get_summary(self, summary_id: str) -> str:
        try:
            response = self.supabase.table('summaries').select('summary').eq('id', summary_id).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]['summary']
            else:
                self.logger.warning(f"Summary not found for ID: {summary_id}")
                return ""

        except Exception as e:
            self.logger.error(f"❌  Failed to get summary from Supabase: {e}")
            return ''

    def cleanup_old_summaries(self):
        try:
            cutoff_time = datetime.datetime.now().isoformat()
            response = self.supabase.table('summaries').delete().lt('expires_at', cutoff_time).execute()

            if response.data:
                self.logger.info(f"🧹  Cleaned up {len(response.data)} expired summaries")

        except Exception as e:
            self.logger.error(f"❌  Failed to cleanup old summaries: {e}")
