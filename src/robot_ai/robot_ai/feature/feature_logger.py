import logging

logger = logging.getLogger("FeatureOrchestrator")
logger.setLevel(logging.INFO)


class FeatureLogger:
    """Audit logger recording feature lifecycle events."""

    def log_start(self, feature_id: str, source: str):
        logger.info(f"🟢 [FEATURE_START] Feature='{feature_id}' | Source={source}")

    def log_stop(self, feature_id: str, duration_sec: float):
        logger.info(f"🔴 [FEATURE_STOP] Feature='{feature_id}' | Duration={duration_sec:.1f}s")

    def log_cleanup(self, feature_id: str):
        logger.info(f"🧹 [FEATURE_CLEANUP] Cleaned up resources for Feature='{feature_id}'")

    def log_release(self, feature_id: str):
        logger.info(f"🔓 [FEATURE_RELEASE] Released Feature='{feature_id}'")
