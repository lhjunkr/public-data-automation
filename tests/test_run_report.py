from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from content.post_content import PostContent
from pipeline.daily_social_publish import DailySocialPublishResult
from publishing.prepared_post import PreparedPost
from publishing.publish_result import (
    build_failed_publish_result,
    build_success_publish_result,
)
from reporting.run_report import (
    FAILURE_REPORT_FILE_NAME,
    RUN_REPORT_FILE_NAME,
    build_failure_report,
    build_run_report,
    save_failure_report,
    save_run_report,
)


class TestRunReport(unittest.TestCase):
    def test_build_run_report_includes_post_and_channel_results(self) -> None:
        started_at = datetime(2026, 6, 24, 18, 8, 0)
        finished_at = datetime(2026, 6, 24, 18, 9, 0)

        report_text = build_run_report(
            daily_publish_results=[make_daily_publish_result()],
            started_at=started_at,
            finished_at=finished_at,
        )

        self.assertIn("Post Count: 1", report_text)
        self.assertIn("[대구 창업지원] 2026년 대구 창업기업 모집", report_text)
        self.assertIn("facebook: success", report_text)
        self.assertIn("instagram: failed", report_text)
        self.assertIn("Instagram API error", report_text)

    def test_build_run_report_handles_empty_result(self) -> None:
        report_text = build_run_report(
            daily_publish_results=[],
            started_at=datetime(2026, 6, 24, 18, 8, 0),
            finished_at=datetime(2026, 6, 24, 18, 8, 1),
        )

        self.assertIn("Post Count: 0", report_text)
        self.assertIn("오늘 게시할 후보가 없습니다.", report_text)

    def test_save_run_report_writes_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            run_output_dir = Path(temporary_dir)

            save_run_report(
                run_output_dir=run_output_dir,
                daily_publish_results=[make_daily_publish_result()],
                started_at=datetime(2026, 6, 24, 18, 8, 0),
                finished_at=datetime(2026, 6, 24, 18, 9, 0),
            )

            report_path = run_output_dir / RUN_REPORT_FILE_NAME
            self.assertTrue(report_path.exists())
            self.assertIn("facebook: success", report_path.read_text(encoding="utf-8"))

    def test_save_failure_report_writes_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            run_output_dir = Path(temporary_dir)
            error = RuntimeError("RSS timeout")

            save_failure_report(
                run_output_dir=run_output_dir,
                error=error,
                started_at=datetime(2026, 6, 24, 18, 8, 0),
                failed_at=datetime(2026, 6, 24, 18, 8, 10),
            )

            report_path = run_output_dir / FAILURE_REPORT_FILE_NAME
            self.assertTrue(report_path.exists())
            self.assertIn("RuntimeError", report_path.read_text(encoding="utf-8"))

    def test_build_failure_report_includes_error_context(self) -> None:
        report_text = build_failure_report(
            error=RuntimeError("R2 upload failed"),
            started_at=datetime(2026, 6, 24, 18, 8, 0),
            failed_at=datetime(2026, 6, 24, 18, 8, 10),
        )

        self.assertIn("Error Type: RuntimeError", report_text)
        self.assertIn("Error Message: R2 upload failed", report_text)


def make_daily_publish_result() -> DailySocialPublishResult:
    prepared_post = PreparedPost(
        post_content=PostContent(
            category="대구 창업지원",
            title="2026년 대구 창업기업 모집",
            source_name="K-Startup",
            source_url="https://example.com/startup",
            published_at="2026.06.24",
            deadline_at="2026.07.08",
            summary="테스트 요약",
            caption="테스트 본문",
            hashtags=["대구", "창업", "사업", "지원"],
            image_text_lines=["대구 창업지원", "창업기업 모집"],
            raw_candidate=None,
        ),
        local_image_path="/tmp/post.png",
        public_image_url="https://assets.example.com/post.png",
    )

    return DailySocialPublishResult(
        prepared_post=prepared_post,
        publish_results=[
            build_success_publish_result(
                channel_name="facebook",
                remote_post_id="facebook-post-id",
                remote_url="https://facebook.com/facebook-post-id",
                raw_response={"id": "facebook-post-id"},
            ),
            build_failed_publish_result(
                channel_name="instagram",
                error_message="Instagram API error",
            ),
        ],
    )


if __name__ == "__main__":
    unittest.main()
