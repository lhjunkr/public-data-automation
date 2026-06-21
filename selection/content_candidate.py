from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ContentCandidate:
    category: str
    title: str
    source_name: str
    source_url: str
    published_at: str
    deadline_at: str
    summary: str
    raw_payload: Any