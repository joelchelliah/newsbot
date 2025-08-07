import uuid
import datetime
from logger import get_logger


class SummariesStore:
    _instance = None
    _storage = {}
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SummariesStore, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.logger = get_logger()
            SummariesStore._initialized = True
            self.logger.info("Using in-memory summary storage (singleton)")

    def store_summary(self, summary: str) -> str:
        """Store a summary with a UUID in memory and return the UUID"""
        summary_id = str(uuid.uuid4())
        summary_data = {
            "summary": summary,
            "timestamp": str(datetime.datetime.now())
        }

        SummariesStore._storage[summary_id] = summary_data
        self.logger.info(f"Stored summary with ID: {summary_id}")

        return summary_id

    def get_summary(self, summary_id: str) -> str:
        """Retrieve a summary by UUID from memory"""
        try:
            data = SummariesStore._storage.get(summary_id, {})
            return data.get('summary', '')
        except KeyError:
            return ''

    def cleanup_old_summaries(self):
        """Clean up summary entries older than 48 hours from memory"""
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=48)

        expired_keys = []
        for summary_id, data in SummariesStore._storage.items():
            try:
                timestamp_str = data.get('timestamp', '')
                if timestamp_str:
                    file_time = datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    if file_time < cutoff_time:
                        expired_keys.append(summary_id)
            except (ValueError, TypeError):
                # If timestamp is invalid, remove it
                expired_keys.append(summary_id)

        # Remove expired entries
        for key in expired_keys:
            del SummariesStore._storage[key]

        if expired_keys:
            self.logger.info(f"Cleaned up {len(expired_keys)} expired summaries")

    def get_stats(self) -> dict:
        """Get storage statistics for debugging"""
        return {
            "total_summaries": len(SummariesStore._storage),
            "storage_size": len(str(SummariesStore._storage)),
            "summary_ids": list(SummariesStore._storage.keys())
        }
