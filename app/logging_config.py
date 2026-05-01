import logging

from app.config import SECURITY_LOG_FILE


security_logger = logging.getLogger("security")
security_logger.setLevel(logging.INFO)
security_logger.propagate = False

if not security_logger.handlers:
    handler = logging.FileHandler(SECURITY_LOG_FILE)
    handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
    security_logger.addHandler(handler)


def log_forbidden_attempt(
    *,
    username: str,
    method: str,
    path: str,
    reason: str,
) -> None:
    security_logger.info(
        "403 Forbidden | user=%s | method=%s | path=%s | reason=%s",
        username or "unknown",
        method,
        path,
        reason,
    )
