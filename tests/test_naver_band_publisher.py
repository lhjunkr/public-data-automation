from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from content.post_content import PostContent
from publishing.naver_band_publisher import (
    build_naver_band_content,
    publish_prepared_post_to_naver_band,
)
from publishing.prepared_post import PreparedPost


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


class TestNaverBandPublisher(unittest.TestCase):
    @patch.dict(
        os.environ,
        {
            "BAND_ACCESS_TOKEN": "band-access-token",
            "BAND_KEY": "band-key",
        },
    )
    @patch("publishing.naver_band_publisher.requests.post")
    def test_publish_prepared_post_to_naver_band_creates_post(
        self,
        mock_post,
    ) -> None:
        mock_post.return_value = FakeResponse(
            status_code=200,
            payload={
                "result_code": 1,
                "result_data": {"post_key": "band-post-key"},
            },
        )

        publish_result = publish_prepared_post_to_naver_band(make_prepared_post())

        self.assertTrue(publish_result.is_success)
        self.assertEqual(publish_result.channel_name, "naver_band")
        self.assertEqual(publish_result.remote_post_id, "band-post-key")
        mock_post.assert_called_once_with(
            "https://openapi.band.us/v2.2/band/post/create",
            data={
                "access_token": "band-access-token",
                "band_key": "band-key",
                "content": (
                    "테스트 게시 본문\n"
                    "\n"
                    "이미지:\n"
                    "https://assets.example.com/post.png"
                ),
                "do_push": "false",
            },
            timeout=30,
        )

    @patch.dict(
        os.environ,
        {
            "BAND_ACCESS_TOKEN": "band-access-token",
            "BAND_KEY": "band-key",
        },
    )
    @patch("publishing.naver_band_publisher.requests.post")
    def test_publish_prepared_post_to_naver_band_returns_failure_on_api_error(
        self,
        mock_post,
    ) -> None:
        mock_post.return_value = FakeResponse(
            status_code=200,
            payload={
                "result_code": 1001,
                "message": "Invalid band key.",
            },
        )

        publish_result = publish_prepared_post_to_naver_band(make_prepared_post())

        self.assertFalse(publish_result.is_success)
        self.assertEqual(publish_result.channel_name, "naver_band")
        self.assertEqual(publish_result.error_message, "Invalid band key.")

    @patch.dict(
        os.environ,
        {
            "BAND_ACCESS_TOKEN": "band-access-token",
            "BAND_KEY": "band-key",
        },
    )
    @patch("publishing.naver_band_publisher.requests.post")
    def test_publish_prepared_post_to_naver_band_handles_non_json_response(
        self,
        mock_post,
    ) -> None:
        mock_post.return_value = FakeResponse(
            status_code=500,
            raises_json_error=True,
        )

        publish_result = publish_prepared_post_to_naver_band(make_prepared_post())

        self.assertFalse(publish_result.is_success)
        self.assertIn("non-JSON", publish_result.error_message or "")

    @patch.dict(os.environ, {}, clear=True)
    def test_publish_prepared_post_to_naver_band_requires_environment_values(
        self,
    ) -> None:
        with self.assertRaisesRegex(RuntimeError, "BAND_ACCESS_TOKEN"):
            publish_prepared_post_to_naver_band(make_prepared_post())

    def test_build_naver_band_content_without_image_url(self) -> None:
        prepared_post = make_prepared_post(public_image_url="")

        self.assertEqual(
            build_naver_band_content(prepared_post),
            "테스트 게시 본문",
        )


def make_prepared_post(public_image_url: str = "https://assets.example.com/post.png"):
    post_content = PostContent(
        category="대구 기업지원",
        title="2026년 대구 기업지원 공고",
        source_name="대구시청 공지사항",
        source_url="https://example.com/business",
        published_at="2026.06.21",
        deadline_at="2026.07.07",
        summary="테스트 요약",
        caption="테스트 게시 본문",
        hashtags=["대구", "기업지원"],
        image_text_lines=["대구 기업지원", "기업지원 공고"],
        raw_candidate=None,
    )

    return PreparedPost(
        post_content=post_content,
        local_image_path="/tmp/post.png",
        public_image_url=public_image_url,
    )


if __name__ == "__main__":
    unittest.main()
    
    