from __future__ import annotations

from dataclasses import dataclass, field

from selection.content_candidate import ContentCandidate


@dataclass(frozen=True)
class PostContent:
    category: str
    title: str
    source_name: str
    source_url: str
    published_at: str
    deadline_at: str
    summary: str
    caption: str
    hashtags: list[str] = field(default_factory=list)
    image_text_lines: list[str] = field(default_factory=list)
    raw_candidate: ContentCandidate | None = None
    