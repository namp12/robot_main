import time
import logging

logger = logging.getLogger("ModeOrchestrator")
logger.setLevel(logging.INFO)


class ModeLogger:
    """Audit Trail Logger for Mode Orchestration framework events."""

    def log_request(self, source: str, target_mode: str, reason: str):
        logger.info(f"[MODE_REQUEST] Source={source} -> Target={target_mode} | Reason='{reason}'")

    def log_transition(self, from_mode: str, to_mode: str, status: str):
        logger.info(f"[MODE_TRANSITION] {from_mode} -> {to_mode} | Status={status}")

    def log_reject(self, source: str, target_mode: str, reason: str):
        logger.warning(f"[MODE_REJECTED] Source={source} -> Target={target_mode} | Reason='{reason}'")
