# -*- coding: utf-8 -*-
"""Structured security events for Railway / JSON log aggregation. Never log passwords."""
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger("tbqc.security")


def log_security_event(event_type: str, **kwargs) -> None:
    """
    Emit one JSON object per line (no secrets — callers must not pass password fields).
    """
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event_type,
        **kwargs,
    }
    logger.info(json.dumps(payload, ensure_ascii=False, default=str))
