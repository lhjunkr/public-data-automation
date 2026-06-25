from __future__ import annotations

import unittest

from content.post_content import PostContent
from pipeline.daily_social_publish import DailySocialPublishResult
from publishing.prepared_post import PreparedPost
from publishing.publish_result import (
    build_failed_publish_result,
    build_success_publish_result,
)
from reporting.console_report import (
    has_completely_failed_post,
    is_completely_failed_post,
    is_partially_failed_post,
)


class TestConsoleReportFailureClassification(unittest.TestCase):
    def test_partial_failure_is_not_treated_as_run_failure(self) -> None:
        partial_post = make_daily_publish_result(
            [success_result("facebook"), failure_result("threads")]
        )

        self.assertTrue(is_partially_failed_post(partial_post))
        self.assertFalse(is_completely_failed_post(partial_post))
        self.assertFalse(has_completely_failed_post([partial_post]))

    def test_completely_failed_post_marks_run_as_failure(self) -> None:
        failed_post = make_daily_publish_result(
            [failure_result("facebook"), failure_result("threads")]
        )

        self.assertTrue(is_completely_failed_post(failed_post))
        self.assertFalse(is_partially_failed_post(failed_post))
        self.assertTrue(has_completely_failed_post([failed_post]))

    def test_all_success_is_not_a_failure(self) -> None:
        success_post = make_daily_publish_result(
            [success_result("facebook"), success_result("instagram")]
        )

        self.assertFalse(has_completely_failed_post([success_post]))

    def test_run_fails_when_any_post_completely_fails(self) -> None:
        results = [
            make_daily_publish_result([success_result("facebook")]),
            make_daily_publish_result([failure_result("facebook")]),
        ]

        self.assertTrue(has_completely_failed_post(results))

    def test_empty_results_are_not_a_failure(self) -> None:
        self.assertFalse(has_completely_failed_post([]))


def success_result(channel_name: str):
    return build_success_publish_result(
        channel_name=channel_name,
        remote_post_id="post-id",
        remote_url=None,
        raw_response=None,
    )


def failure_result(channel_name: str):
    return build_failed_publish_result(
        channel_name=channel_name,
        error_message="실패",
        raw_response=None,
    )


def make_daily_publish_result(publish_results) -> DailySocialPublishResult:
    post_content = PostContent(
        category="대구 창업지원",
        title="테스트 공고",
        source_name="K-Startup",
        source_url="https://example.com/startup",
        published_at="2026.06.21",
        deadline_at="2026.07.07",
        summary="테스트 요약",
        caption="테스트 게시 본문",
        hashtags=["대구"],
        image_text_lines=["대구 창업지원"],
        raw_candidate=None,
    )
    prepared_post = PreparedPost(
        post_content=post_content,
        local_image_path="/tmp/post.png",
        public_image_url="https://assets.example.com/post.png",
    )

    return DailySocialPublishResult(
        prepared_post=prepared_post,
        publish_results=publish_results,
    )


if __name__ == "__main__":
    unittest.main()
