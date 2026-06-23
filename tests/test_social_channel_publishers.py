from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from content.post_content import PostContent
from publishing.facebook_publisher import publish_prepared_post_to_facebook
from publishing.instagram_publisher import publish_prepared_post_to_instagram
from publishing.prepared_post import PreparedPost
from publishing.threads_publisher import publish_prepared_post_to_threads


class FakeResponse:
    def __init__(
        self,
        *,
        status_code: int,
        payload: dict | None = None,
        raises_json_error: bool = False,
    ) -> None:
        self.status_code = status_code
        self.payload = payload or {}
        self.raises_json_error = raises_json_error
        self.ok = 200 <= status_code < 300

    def json(self) -> dict:
        if self.raises_json_error:
            raise ValueError("Response body is not JSON.")

        return self.payload


class TestFacebookPublisher(unittest.TestCase):
    @patch.dict(
        os.environ,
        {
            "FACEBOOK_PAGE_ID": "facebook-page-id",
            "FACEBOOK_PAGE_ACCESS_TOKEN": "facebook-page-token",
        },
    )
    @patch("publishing.facebook_publisher.requests.post")
    def test_publish_prepared_post_to_facebook_posts_photo(
        self,
        mock_post,
    ) -> None:
        mock_post.return_value = FakeResponse(
            status_code=200,
            payload={"id": "facebook-photo-id", "post_id": "facebook-post-id"},
        )

        publish_result = publish_prepared_post_to_facebook(make_prepared_post())

        self.assertTrue(publish_result.is_success)
        self.assertEqual(publish_result.channel_name, "facebook")
        self.assertEqual(publish_result.remote_post_id, "facebook-post-id")
        self.assertEqual(
            publish_result.remote_url,
            "https://www.facebook.com/facebook-post-id",
        )
        mock_post.assert_called_once_with(
            "https://graph.facebook.com/v25.0/facebook-page-id/photos",
            data={
                "url": "https://assets.example.com/post.png",
                "caption": "테스트 게시 본문",
                "published": "true",
                "access_token": "facebook-page-token",
            },
            timeout=30,
        )

    @patch.dict(
        os.environ,
        {
            "FACEBOOK_PAGE_ID": "facebook-page-id",
            "FACEBOOK_PAGE_ACCESS_TOKEN": "facebook-page-token",
        },
    )
    @patch("publishing.facebook_publisher.requests.post")
    def test_publish_prepared_post_to_facebook_returns_failure_on_api_error(
        self,
        mock_post,
    ) -> None:
        mock_post.return_value = FakeResponse(
            status_code=400,
            payload={"error": {"message": "Invalid Facebook token."}},
        )

        publish_result = publish_prepared_post_to_facebook(make_prepared_post())

        self.assertFalse(publish_result.is_success)
        self.assertEqual(publish_result.channel_name, "facebook")
        self.assertEqual(publish_result.error_message, "Invalid Facebook token.")

    @patch.dict(
        os.environ,
        {
            "FACEBOOK_PAGE_ID": "facebook-page-id",
            "FACEBOOK_PAGE_ACCESS_TOKEN": "facebook-page-token",
        },
    )
    @patch("publishing.facebook_publisher.requests.post")
    def test_publish_prepared_post_to_facebook_requires_remote_post_id(
        self,
        mock_post,
    ) -> None:
        mock_post.return_value = FakeResponse(status_code=200, payload={})

        publish_result = publish_prepared_post_to_facebook(make_prepared_post())

        self.assertFalse(publish_result.is_success)
        self.assertEqual(
            publish_result.error_message,
            "Facebook photo post did not return post id.",
        )

    @patch.dict(os.environ, {}, clear=True)
    def test_publish_prepared_post_to_facebook_requires_environment_values(
        self,
    ) -> None:
        with self.assertRaisesRegex(RuntimeError, "FACEBOOK_PAGE_ID"):
            publish_prepared_post_to_facebook(make_prepared_post())


class TestInstagramPublisher(unittest.TestCase):
    @patch.dict(
        os.environ,
        {
            "IG_USER_ID": "instagram-user-id",
            "META_ACCESS_TOKEN": "meta-access-token",
        },
    )
    @patch("publishing.instagram_publisher.requests.post")
    def test_publish_prepared_post_to_instagram_creates_and_publishes_media(
        self,
        mock_post,
    ) -> None:
        mock_post.side_effect = [
            FakeResponse(status_code=200, payload={"id": "creation-id"}),
            FakeResponse(status_code=200, payload={"id": "instagram-post-id"}),
        ]

        publish_result = publish_prepared_post_to_instagram(make_prepared_post())

        self.assertTrue(publish_result.is_success)
        self.assertEqual(publish_result.channel_name, "instagram")
        self.assertEqual(publish_result.remote_post_id, "instagram-post-id")
        self.assertEqual(mock_post.call_count, 2)
        mock_post.assert_any_call(
            "https://graph.facebook.com/v25.0/instagram-user-id/media",
            data={
                "image_url": "https://assets.example.com/post.png",
                "caption": "테스트 게시 본문",
                "access_token": "meta-access-token",
            },
            timeout=30,
        )
        mock_post.assert_any_call(
            "https://graph.facebook.com/v25.0/instagram-user-id/media_publish",
            data={
                "creation_id": "creation-id",
                "access_token": "meta-access-token",
            },
            timeout=30,
        )

    @patch.dict(
        os.environ,
        {
            "IG_USER_ID": "instagram-user-id",
            "META_ACCESS_TOKEN": "meta-access-token",
        },
    )
    @patch("publishing.instagram_publisher.requests.post")
    def test_publish_prepared_post_to_instagram_stops_when_container_fails(
        self,
        mock_post,
    ) -> None:
        mock_post.return_value = FakeResponse(
            status_code=400,
            payload={"error": {"message": "Invalid image URL."}},
        )

        publish_result = publish_prepared_post_to_instagram(make_prepared_post())

        self.assertFalse(publish_result.is_success)
        self.assertEqual(publish_result.channel_name, "instagram")
        self.assertEqual(publish_result.error_message, "Invalid image URL.")
        self.assertEqual(mock_post.call_count, 1)

    @patch.dict(
        os.environ,
        {
            "IG_USER_ID": "instagram-user-id",
            "META_ACCESS_TOKEN": "meta-access-token",
        },
    )
    @patch("publishing.instagram_publisher.requests.post")
    def test_publish_prepared_post_to_instagram_requires_publish_post_id(
        self,
        mock_post,
    ) -> None:
        mock_post.side_effect = [
            FakeResponse(status_code=200, payload={"id": "creation-id"}),
            FakeResponse(status_code=200, payload={}),
        ]

        publish_result = publish_prepared_post_to_instagram(make_prepared_post())

        self.assertFalse(publish_result.is_success)
        self.assertEqual(
            publish_result.error_message,
            "Instagram media publish did not return post id.",
        )

    @patch.dict(
        os.environ,
        {
            "IG_USER_ID": "instagram-user-id",
            "META_ACCESS_TOKEN": "meta-access-token",
        },
    )
    @patch("publishing.instagram_publisher.time.sleep")
    @patch("publishing.instagram_publisher.requests.post")
    def test_publish_prepared_post_to_instagram_retries_when_media_is_not_ready(
        self,
        mock_post,
        mock_sleep,
    ) -> None:
        mock_post.side_effect = [
            FakeResponse(status_code=200, payload={"id": "creation-id"}),
            FakeResponse(
                status_code=400,
                payload={"error": {"message": "Media ID is not available"}},
            ),
            FakeResponse(status_code=200, payload={"id": "instagram-post-id"}),
        ]

        publish_result = publish_prepared_post_to_instagram(make_prepared_post())

        self.assertTrue(publish_result.is_success)
        self.assertEqual(publish_result.remote_post_id, "instagram-post-id")
        self.assertEqual(mock_post.call_count, 3)
        mock_sleep.assert_called_once_with(10)

    @patch.dict(os.environ, {}, clear=True)
    def test_publish_prepared_post_to_instagram_requires_environment_values(
        self,
    ) -> None:
        with self.assertRaisesRegex(RuntimeError, "IG_USER_ID"):
            publish_prepared_post_to_instagram(make_prepared_post())


class TestThreadsPublisher(unittest.TestCase):
    @patch.dict(
        os.environ,
        {
            "THREADS_USER_ID": "threads-user-id",
            "THREADS_ACCESS_TOKEN": "threads-access-token",
        },
    )
    @patch("publishing.threads_publisher.requests.post")
    def test_publish_prepared_post_to_threads_creates_and_publishes_media(
        self,
        mock_post,
    ) -> None:
        mock_post.side_effect = [
            FakeResponse(status_code=200, payload={"id": "creation-id"}),
            FakeResponse(status_code=200, payload={"id": "threads-post-id"}),
        ]

        publish_result = publish_prepared_post_to_threads(make_prepared_post())

        self.assertTrue(publish_result.is_success)
        self.assertEqual(publish_result.channel_name, "threads")
        self.assertEqual(publish_result.remote_post_id, "threads-post-id")
        self.assertEqual(
            publish_result.remote_url,
            "https://www.threads.com/@todaydaegu/post/threads-post-id",
        )
        self.assertEqual(mock_post.call_count, 2)
        mock_post.assert_any_call(
            "https://graph.threads.net/v1.0/threads-user-id/threads",
            data={
                "media_type": "IMAGE",
                "image_url": "https://assets.example.com/post.png",
                "text": "테스트 게시 본문",
                "access_token": "threads-access-token",
            },
            timeout=30,
        )
        mock_post.assert_any_call(
            "https://graph.threads.net/v1.0/threads-user-id/threads_publish",
            data={
                "creation_id": "creation-id",
                "access_token": "threads-access-token",
            },
            timeout=30,
        )

    @patch.dict(
        os.environ,
        {
            "THREADS_USER_ID": "threads-user-id",
            "THREADS_ACCESS_TOKEN": "threads-access-token",
        },
    )
    @patch("publishing.threads_publisher.requests.post")
    def test_publish_prepared_post_to_threads_stops_when_container_fails(
        self,
        mock_post,
    ) -> None:
        mock_post.return_value = FakeResponse(
            status_code=400,
            payload={"error": {"message": "Threads token expired."}},
        )

        publish_result = publish_prepared_post_to_threads(make_prepared_post())

        self.assertFalse(publish_result.is_success)
        self.assertEqual(publish_result.channel_name, "threads")
        self.assertEqual(publish_result.error_message, "Threads token expired.")
        self.assertEqual(mock_post.call_count, 1)

    @patch.dict(
        os.environ,
        {
            "THREADS_USER_ID": "threads-user-id",
            "THREADS_ACCESS_TOKEN": "threads-access-token",
        },
    )
    @patch("publishing.threads_publisher.requests.post")
    def test_publish_prepared_post_to_threads_requires_publish_post_id(
        self,
        mock_post,
    ) -> None:
        mock_post.side_effect = [
            FakeResponse(status_code=200, payload={"id": "creation-id"}),
            FakeResponse(status_code=200, payload={}),
        ]

        publish_result = publish_prepared_post_to_threads(make_prepared_post())

        self.assertFalse(publish_result.is_success)
        self.assertEqual(
            publish_result.error_message,
            "Threads media publish did not return post id.",
        )

    @patch.dict(os.environ, {}, clear=True)
    def test_publish_prepared_post_to_threads_requires_environment_values(
        self,
    ) -> None:
        with self.assertRaisesRegex(RuntimeError, "THREADS_USER_ID"):
            publish_prepared_post_to_threads(make_prepared_post())


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
        local_image_path="/tmp/post.png",
        public_image_url="https://assets.example.com/post.png",
    )


if __name__ == "__main__":
    unittest.main()
