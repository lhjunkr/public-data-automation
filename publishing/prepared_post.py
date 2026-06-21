from __future__ import annotations

from dataclasses import dataclass

from content.post_content import PostContent


@dataclass(frozen=True)
class PreparedPost:
    post_content: PostContent
    local_image_path: str
    public_image_url: str
