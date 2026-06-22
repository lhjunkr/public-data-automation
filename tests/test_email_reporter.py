from __future__ import annotations

import unittest

from content.post_content import PostContent
from notifications.email_reporter import (
    build_daily_publish_email_body,
    build_daily_publish_email_subject,
)
from pipeline.daily_social_publish import DailySocialPublishResult
from publishing.prepared_post import PreparedPost
from publishing.publish_result import (
    build_failed_publish_result,
    build_success_publish_result,
)


class TestEmailReporter(unittest.TestCase):
    def test_build_daily_publish_email_subject_when_no_posts(self) -> None:
        self.assertEqual(
            build_daily_publish_email_subject([]),
            "[Public Data Automation] 오늘 게시할 콘텐츠 없음",
        )

    def test_build_daily_publish_email_subject_when_all_success(self) -> None:
        self.assertEqual(
            build_daily_publish_email_subject(
                [
                    make_daily_publish_result(
                        publish_results=[
                            build_success_publish_result(
                                channel_name="facebook",
                                remote_post_id="facebook-post-id",
                                remote_url="https://facebook.com/post",
                                raw_response={"id": "facebook-post-id"},
                            )
                        ]
                    )
                ]
            ),
            "[Public Data Automation] 게시 성공",
        )

    def test_build_daily_publish_email_subject_when_some_channels_failed(self) -> None:
        self.assertEqual(
            build_daily_publish_email_subject(
                [
                    make_daily_publish_result(
                        publish_results=[
                            build_success_publish_result(
                                channel_name="facebook",
                                remote_post_id="facebook-post-id",
                                remote_url=None,
                                raw_response={"id": "facebook-post-id"},
                            ),
                            build_failed_publish_result(
                                channel_name="instagram",
                                error_message="Instagram failed.",
                            ),
                        ]
                    )
                ]
            ),
            "[Public Data Automation] 게시 완료 - 실패 채널 1건",
        )

    def test_build_daily_publish_email_body_contains_publish_details(self) -> None:
        email_body = build_daily_publish_email_body(
            [
                make_daily_publish_result(
                    publish_results=[
                        build_success_publish_result(
                            channel_name="facebook",
                            remote_post_id="facebook-post-id",
                            remote_url="https://facebook.com/post",
                            raw_response={"id": "facebook-post-id"},
                        ),
                        build_failed_publish_result(
                            channel_name="instagram",
                            error_message="Instagram failed.",
                        ),
                    ]
                )
            ]
        )

        self.assertIn("오늘 게시 대상: 1건", email_body)
        self.assertIn("[대구 창업지원] 2026년 대구 창업기업 모집", email_body)
        self.assertIn("- facebook: 성공", email_body)
        self.assertIn("게시 ID: facebook-post-id", email_body)
        self.assertIn("게시 URL: https://facebook.com/post", email_body)
        self.assertIn("- instagram: 실패", email_body)
        self.assertIn("오류: Instagram failed.", email_body)


def make_daily_publish_result(
    publish_results,
) -> DailySocialPublishResult:
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
    
    