from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import patch

from content.post_content import PostContent
from pipeline.daily_social_publish import (
    build_posted_history_records_from_publish_results,
    publish_daily_posts_to_social_channels,
    publish_prepared_posts_to_social_channels,
)
from publishing.prepared_post import PreparedPost
from publishing.publish_result import (
    build_failed_publish_result,
    build_success_publish_result,
)
from storage.posted_history import POST_STATUS_PARTIAL_FAILED, POST_STATUS_PUBLISHED


class TestDailySocialPublish(unittest.TestCase):
    @patch("pipeline.daily_social_publish.cleanup_old_r2_posted_history")
    @patch("pipeline.daily_social_publish.upload_today_posted_history_to_r2")
    @patch("pipeline.daily_social_publish.append_posted_history_records")
    @patch("pipeline.daily_social_publish.prepare_daily_posts")
    def test_publish_daily_posts_to_social_channels_prepares_publishes_and_records_history(
        self,
        mock_prepare_daily_posts,
        mock_append_posted_history_records,
        mock_upload_today_posted_history_to_r2,
        mock_cleanup_old_r2_posted_history,
    ) -> None:
        prepared_posts = [
            make_prepared_post(title="첫 번째 공고"),
            make_prepared_post(title="두 번째 공고"),
        ]
        mock_prepare_daily_posts.return_value = prepared_posts

        daily_publish_results = publish_daily_posts_to_social_channels(
            today=date(2026, 6, 22),
            sync_posted_history=True,
            upload_assets=True,
            publish_functions=(fake_success_facebook_publish,),
        )

        mock_prepare_daily_posts.assert_called_once_with(
            today=date(2026, 6, 22),
            sync_posted_history=True,
            upload_assets=True,
        )
        self.assertEqual(len(daily_publish_results), 2)
        self.assertEqual(
            daily_publish_results[0].prepared_post.post_content.title,
            "첫 번째 공고",
        )
        self.assertEqual(
            daily_publish_results[0].publish_results[0].channel_name,
            "facebook",
        )
        mock_append_posted_history_records.assert_called_once()
        history_records = mock_append_posted_history_records.call_args.args[0]
        self.assertEqual(len(history_records), 2)
        self.assertEqual(history_records[0].status, POST_STATUS_PUBLISHED)
        mock_upload_today_posted_history_to_r2.assert_called_once_with(
            run_date="2026-06-22"
        )
        mock_cleanup_old_r2_posted_history.assert_called_once_with(
            today=date(2026, 6, 22)
        )

    @patch("pipeline.daily_social_publish.cleanup_old_r2_posted_history")
    @patch("pipeline.daily_social_publish.upload_today_posted_history_to_r2")
    @patch("pipeline.daily_social_publish.append_posted_history_records")
    @patch("pipeline.daily_social_publish.prepare_daily_posts")
    def test_publish_daily_posts_to_social_channels_can_skip_history_recording(
        self,
        mock_prepare_daily_posts,
        mock_append_posted_history_records,
        mock_upload_today_posted_history_to_r2,
        mock_cleanup_old_r2_posted_history,
    ) -> None:
        mock_prepare_daily_posts.return_value = [
            make_prepared_post(title="첫 번째 공고"),
        ]

        publish_daily_posts_to_social_channels(
            today=date(2026, 6, 22),
            publish_functions=(fake_success_facebook_publish,),
            record_posted_history=False,
        )

        mock_append_posted_history_records.assert_not_called()
        mock_upload_today_posted_history_to_r2.assert_not_called()
        mock_cleanup_old_r2_posted_history.assert_not_called()

    def test_publish_prepared_posts_to_social_channels_publishes_each_post(
        self,
    ) -> None:
        prepared_posts = [
            make_prepared_post(title="첫 번째 공고"),
            make_prepared_post(title="두 번째 공고"),
        ]

        daily_publish_results = publish_prepared_posts_to_social_channels(
            prepared_posts=prepared_posts,
            publish_functions=(
                fake_success_facebook_publish,
                fake_success_instagram_publish,
            ),
        )

        self.assertEqual(len(daily_publish_results), 2)
        self.assertEqual(
            [result.channel_name for result in daily_publish_results[0].publish_results],
            ["facebook", "instagram"],
        )
        self.assertEqual(
            [result.channel_name for result in daily_publish_results[1].publish_results],
            ["facebook", "instagram"],
        )

    def test_build_posted_history_records_marks_partial_failure(self) -> None:
        daily_publish_results = publish_prepared_posts_to_social_channels(
            prepared_posts=[make_prepared_post(title="부분 성공 공고")],
            publish_functions=(
                fake_success_facebook_publish,
                fake_failed_instagram_publish,
                fake_success_threads_publish,
                fake_success_naver_band_publish,
            ),
        )

        history_records = build_posted_history_records_from_publish_results(
            daily_publish_results
        )

        self.assertEqual(len(history_records), 1)
        self.assertEqual(history_records[0].status, POST_STATUS_PARTIAL_FAILED)
        self.assertTrue(history_records[0].facebook_post_id)
        self.assertEqual(history_records[0].instagram_post_id, "")
        self.assertTrue(history_records[0].threads_post_id)
        self.assertTrue(history_records[0].naver_band_post_key)

    def test_build_posted_history_records_skips_all_failed_publish_results(
        self,
    ) -> None:
        daily_publish_results = publish_prepared_posts_to_social_channels(
            prepared_posts=[make_prepared_post(title="전체 실패 공고")],
            publish_functions=(
                fake_failed_facebook_publish,
                fake_failed_instagram_publish,
                fake_failed_threads_publish,
                fake_failed_naver_band_publish,
            ),
        )

        history_records = build_posted_history_records_from_publish_results(
            daily_publish_results
        )

        self.assertEqual(history_records, [])


def fake_success_facebook_publish(prepared_post: PreparedPost):
    return build_success_publish_result(
        channel_name="facebook",
        remote_post_id=f"facebook-{prepared_post.post_content.title}",
        remote_url=None,
        raw_response={"id": "facebook-id"},
    )


def fake_success_instagram_publish(prepared_post: PreparedPost):
    return build_success_publish_result(
        channel_name="instagram",
        remote_post_id=f"instagram-{prepared_post.post_content.title}",
        remote_url=None,
        raw_response={"id": "instagram-id"},
    )


def fake_success_threads_publish(prepared_post: PreparedPost):
    return build_success_publish_result(
        channel_name="threads",
        remote_post_id=f"threads-{prepared_post.post_content.title}",
        remote_url=None,
        raw_response={"id": "threads-id"},
    )


def fake_success_naver_band_publish(prepared_post: PreparedPost):
    return build_success_publish_result(
        channel_name="naver_band",
        remote_post_id=f"naver-band-{prepared_post.post_content.title}",
        remote_url=None,
        raw_response={"result_data": {"post_key": "naver-band-id"}},
    )


def fake_failed_facebook_publish(prepared_post: PreparedPost):
    return build_failed_publish_result(
        channel_name="facebook",
        error_message="Facebook failed.",
    )


def fake_failed_instagram_publish(prepared_post: PreparedPost):
    return build_failed_publish_result(
        channel_name="instagram",
        error_message="Instagram failed.",
    )


def fake_failed_threads_publish(prepared_post: PreparedPost):
    return build_failed_publish_result(
        channel_name="threads",
        error_message="Threads failed.",
    )


def fake_failed_naver_band_publish(prepared_post: PreparedPost):
    return build_failed_publish_result(
        channel_name="naver_band",
        error_message="Naver Band failed.",
    )


def make_prepared_post(title: str) -> PreparedPost:
    post_content = PostContent(
        category="대구 창업지원",
        title=title,
        source_name="K-Startup",
        source_url=f"https://example.com/{title}",
        published_at="2026.06.21",
        deadline_at="2026.07.07",
        summary="테스트 요약",
        caption="테스트 게시 본문",
        hashtags=["대구", "창업지원"],
        image_text_lines=["대구 창업지원", title],
        raw_candidate=None,
    )

    return PreparedPost(
        post_content=post_content,
        local_image_path="/tmp/post.png",
        public_image_url="https://assets.example.com/post.png",
    )


if __name__ == "__main__":
    unittest.main()


