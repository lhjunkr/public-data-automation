from __future__ import annotations

import unittest

from content.post_content import PostContent
from publishing.prepared_post import PreparedPost
from publishing.publish_result import (
    build_failed_publish_result,
    build_success_publish_result,
)
from publishing.social_publish_pipeline import publish_prepared_post_to_social_channels


class TestSocialPublishPipeline(unittest.TestCase):
    def test_publish_prepared_post_to_social_channels_returns_all_results(self) -> None:
        prepared_post = make_prepared_post()

        publish_results = publish_prepared_post_to_social_channels(
            prepared_post=prepared_post,
            publish_functions=(
                fake_success_facebook_publish,
                fake_success_instagram_publish,
                fake_success_threads_publish,
            ),
        )

        self.assertEqual(len(publish_results), 3)
        self.assertTrue(all(result.is_success for result in publish_results))
        self.assertEqual(
            [result.channel_name for result in publish_results],
            ["facebook", "instagram", "threads"],
        )

    def test_publish_prepared_post_to_social_channels_keeps_going_after_failure(
        self,
    ) -> None:
        prepared_post = make_prepared_post()

        publish_results = publish_prepared_post_to_social_channels(
            prepared_post=prepared_post,
            publish_functions=(
                fake_success_facebook_publish,
                fake_raising_instagram_publish,
                fake_success_threads_publish,
            ),
        )

        self.assertEqual(len(publish_results), 3)
        self.assertTrue(publish_results[0].is_success)
        self.assertFalse(publish_results[1].is_success)
        self.assertTrue(publish_results[2].is_success)
        self.assertEqual(publish_results[1].channel_name, "instagram")
        self.assertIn("Instagram API error", publish_results[1].error_message or "")


def fake_success_facebook_publish(prepared_post: PreparedPost):
    return build_success_publish_result(
        channel_name="facebook",
        remote_post_id="facebook-post-id",
        remote_url="https://www.facebook.com/facebook-post-id",
        raw_response={"id": "facebook-photo-id", "post_id": "facebook-post-id"},
    )


def fake_success_instagram_publish(prepared_post: PreparedPost):
    return build_success_publish_result(
        channel_name="instagram",
        remote_post_id="instagram-post-id",
        remote_url=None,
        raw_response={"id": "instagram-post-id"},
    )


def fake_success_threads_publish(prepared_post: PreparedPost):
    return build_success_publish_result(
        channel_name="threads",
        remote_post_id="threads-post-id",
        remote_url="https://www.threads.com/@todaydaegu/post/threads-post-id",
        raw_response={"id": "threads-post-id"},
    )


def fake_raising_instagram_publish(prepared_post: PreparedPost):
    raise RuntimeError("Instagram API error")


def make_prepared_post() -> PreparedPost:
    post_content = PostContent(
        category="대구 창업지원",
        title="2026년 대구 창업기업 모집",
        source_name="K-Startup",
        source_url="https://example.com/startup",
        published_at="2026.06.21",
        deadline_at="2026.07.07",
        summary="테스트 요약",
        caption="테스트 게시 본문",
        hashtags=["대구", "창업지원"],
        image_text_lines=["대구 창업지원", "창업기업 모집"],
        raw_candidate=None,
    )

    return PreparedPost(
        post_content=post_content,
        local_image_path="/tmp/test.png",
        public_image_url="https://example.com/test.png",
    )


if __name__ == "__main__":
    unittest.main()
    
    