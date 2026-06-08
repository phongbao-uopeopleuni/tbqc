#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Storage helpers for homepage ticker announcements and memorial countdowns."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

MAX_ANNOUNCEMENTS = 10
MAX_ANNOUNCEMENT_LENGTH = 180
MEMORIAL_MAX_TEXT_LENGTH = 80
ANNOUNCEMENTS_FILE = Path(__file__).resolve().parents[1] / "instance" / "site_announcements.json"

DEFAULT_MEMORIALS = {
    "xuan": {
        "title": "GIỖ XUÂN 2026",
        "lunar_label": "07/2 ÂL",
        "date": "2026-03-25",
    },
    "thu": {
        "title": "GIỖ THU 2026",
        "lunar_label": "03/7 ÂL",
        "date": "2026-08-15",
    },
}


def _normalize_line(value: object) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
    if len(text) > MAX_ANNOUNCEMENT_LENGTH:
        text = text[:MAX_ANNOUNCEMENT_LENGTH].rstrip()
    return text


def _normalize_slots(lines: object) -> list[str]:
    raw_items = list(lines) if isinstance(lines, (list, tuple)) else []
    slots = [_normalize_line(item) for item in raw_items[:MAX_ANNOUNCEMENTS]]
    if len(slots) < MAX_ANNOUNCEMENTS:
        slots.extend([""] * (MAX_ANNOUNCEMENTS - len(slots)))
    return slots


def _normalize_memorial_text(value: object, fallback: str) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
    if not text:
        return fallback
    if len(text) > MEMORIAL_MAX_TEXT_LENGTH:
        text = text[:MEMORIAL_MAX_TEXT_LENGTH].rstrip()
    return text


def _normalize_date(value: object, fallback: str) -> str:
    text = str(value or "").strip()
    try:
        return datetime.strptime(text, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return fallback


def _normalize_memorial(key: str, payload: object) -> dict[str, str]:
    defaults = DEFAULT_MEMORIALS[key]
    source = payload if isinstance(payload, dict) else {}
    return {
        "title": _normalize_memorial_text(source.get("title"), defaults["title"]),
        "lunar_label": _normalize_memorial_text(source.get("lunar_label"), defaults["lunar_label"]),
        "date": _normalize_date(source.get("date"), defaults["date"]),
    }


def _normalize_memorials(memorials: object) -> dict[str, dict[str, str]]:
    source = memorials if isinstance(memorials, dict) else {}
    return {
        "xuan": _normalize_memorial("xuan", source.get("xuan")),
        "thu": _normalize_memorial("thu", source.get("thu")),
    }


def _display_date(value: str) -> str:
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return value


def _read_payload() -> dict:
    try:
        return json.loads(ANNOUNCEMENTS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError, TypeError):
        return {}


def load_announcement_settings() -> dict:
    """Return normalized ticker settings, including memorial countdown config."""
    payload = _read_payload()
    lines = _normalize_slots(payload.get("lines"))
    memorials = _normalize_memorials(payload.get("memorials"))
    return {"lines": lines, "memorials": memorials}


def load_announcement_slots() -> list[str]:
    """Backward-compatible helper for announcement rows only."""
    return load_announcement_settings()["lines"]


def get_active_announcements() -> list[str]:
    """Return only non-empty announcement lines for homepage rendering."""
    return [line for line in load_announcement_slots() if line]


def get_memorial_settings() -> dict[str, dict[str, str]]:
    """Return normalized memorial settings with display_date for templates."""
    memorials = _normalize_memorials(load_announcement_settings()["memorials"])
    return {
        key: {
            **value,
            "display_date": _display_date(value["date"]),
        }
        for key, value in memorials.items()
    }


def save_announcement_settings(lines: object, memorials: object) -> dict:
    """Persist ticker lines + memorial countdown settings atomically."""
    normalized = {
        "lines": _normalize_slots(lines),
        "memorials": _normalize_memorials(memorials),
    }
    ANNOUNCEMENTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    temp_path = None
    try:
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=str(ANNOUNCEMENTS_FILE.parent),
            delete=False,
        ) as handle:
            json.dump(normalized, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            temp_path = Path(handle.name)
        os.replace(temp_path, ANNOUNCEMENTS_FILE)
    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass

    return normalized


def save_announcement_slots(lines: object) -> list[str]:
    """Backward-compatible helper for line-only updates."""
    existing = load_announcement_settings()
    return save_announcement_settings(lines, existing["memorials"])["lines"]
