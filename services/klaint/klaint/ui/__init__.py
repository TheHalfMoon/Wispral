# SPDX-License-Identifier: Apache-2.0
"""Static & HTML template loader for Klaint Studio (`/`) and Customer Widget (`/widget`)."""

from __future__ import annotations

from pathlib import Path

UI_ROOT = Path(__file__).resolve().parent
TEMPLATES_DIR = UI_ROOT / "templates"
STATIC_DIR = UI_ROOT / "static"


def load_studio_html() -> bytes:
    return (TEMPLATES_DIR / "studio.html").read_bytes()


def load_widget_html() -> bytes:
    return (TEMPLATES_DIR / "widget.html").read_bytes()


def load_static_asset(filename: str) -> tuple[bytes, str] | None:
    if filename not in ("studio.css", "studio.js"):
        return None
    target = (STATIC_DIR / filename).resolve()
    if not target.is_relative_to(STATIC_DIR.resolve()) or not target.exists():
        return None
    content_type = (
        "text/css; charset=utf-8"
        if filename.endswith(".css")
        else "application/javascript; charset=utf-8"
    )
    return target.read_bytes(), content_type
