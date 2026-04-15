# -*- coding: utf-8 -*-
"""Server-side HTML sanitization for rich text (Quill, etc.). Strips scripts and unsafe markup."""
from __future__ import annotations

import bleach
from bleach.css_sanitizer import CSSSanitizer

# Quill-style content: keep formatting; block script/on* and dangerous URLs via bleach.
_CSS = CSSSanitizer(
    allowed_css_properties=[
        "color",
        "background-color",
        "text-align",
        "font-size",
        "font-weight",
        "font-family",
        "line-height",
        "margin",
        "margin-left",
        "margin-right",
        "padding",
        "padding-left",
        "width",
        "height",
        "max-width",
    ]
)

_ALLOWED_TAGS = frozenset(
    [
        "p",
        "br",
        "span",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "blockquote",
        "pre",
        "code",
        "ul",
        "ol",
        "li",
        "hr",
        "strong",
        "b",
        "em",
        "i",
        "u",
        "s",
        "sub",
        "sup",
        "a",
        "img",
    ]
)

_ALLOWED_ATTRS = {
    "*": ["class", "style"],
    "a": ["href", "title", "rel", "target"],
    "img": ["src", "alt", "width", "height", "class"],
}


def sanitize_activity_html(html: str) -> str:
    if not html:
        return ""
    return bleach.clean(
        html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        css_sanitizer=_CSS,
        strip=True,
    )
