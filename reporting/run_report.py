from __future__ import annotations

import traceback
from datetime import date, datetime
from pathlib import Path

from pipeline.daily_social_publish import DailySocialPublishResult


OUTPUTS_DIR_NAME = "outputs"
RUN_REPORT_FILE_NAME = "run_report.txt"
FAILURE_REPORT_FILE_NAME = "failure_report.txt"


def create_run_output_dir(run_date: date | None = None) -> Path:
    output_date = run_date or date.today()
    run_output_dir = Path(OUTPUTS_DIR_NAME) / output_date.isoformat()
    run_output_dir.mkdir(parents=True, exist_ok=True)
    return run_output_dir


def save_run_report(
    *,
    run_output_dir: Path,
    daily_publish_results: list[DailySocialPublishResult],
    started_at: datetime,
    finished_at: datetime,
) -> None:
    report_text = build_run_report(
        daily_publish_results=daily_publish_results,
        started_at=started_at,
        finished_at=finished_at,
    )
    (run_output_dir / RUN_REPORT_FILE_NAME).write_text(report_text, encoding="utf-8")


def save_failure_report(
    *,
    run_output_dir: Path,
    error: BaseException,
    started_at: datetime,
    failed_at: datetime,
) -> None:
    report_text = build_failure_report(
        error=error,
        started_at=started_at,
        failed_at=failed_at,
    )
    (run_output_dir / FAILURE_REPORT_FILE_NAME).write_text(
        report_text,
        encoding="utf-8",
    )


def build_run_report(
    *,
    daily_publish_results: list[DailySocialPublishResult],
    started_at: datetime,
    finished_at: datetime,
) -> str:
    lines = [
        "Public Data Automation Run Report",
        "",
        f"Started At: {started_at.isoformat(timespec='seconds')}",
        f"Finished At: {finished_at.isoformat(timespec='seconds')}",
        f"Post Count: {len(daily_publish_results)}",
        "",
    ]

    if not daily_publish_results:
        lines.append("오늘 게시할 후보가 없습니다.")
        return "\n".join(lines).rstrip() + "\n"

    for index, daily_publish_result in enumerate(daily_publish_results, start=1):
        post_content = daily_publish_result.prepared_post.post_content
        lines.extend(
            [
                f"{index}. [{post_content.category}] {post_content.title}",
                f"   Source: {post_content.source_name}",
                f"   Source URL: {post_content.source_url}",
                f"   Image URL: {daily_publish_result.prepared_post.public_image_url}",
            ]
        )

        for publish_result in daily_publish_result.publish_results:
            status_text = "success" if publish_result.is_success else "failed"
            lines.append(f"   - {publish_result.channel_name}: {status_text}")

            if publish_result.remote_post_id:
                lines.append(f"     Remote Post ID: {publish_result.remote_post_id}")

            if publish_result.remote_url:
                lines.append(f"     Remote URL: {publish_result.remote_url}")

            if publish_result.error_message:
                lines.append(f"     Error: {publish_result.error_message}")

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_failure_report(
    *,
    error: BaseException,
    started_at: datetime,
    failed_at: datetime,
) -> str:
    return "\n".join(
        [
            "Public Data Automation Failure Report",
            "",
            f"Started At: {started_at.isoformat(timespec='seconds')}",
            f"Failed At: {failed_at.isoformat(timespec='seconds')}",
            f"Error Type: {type(error).__name__}",
            f"Error Message: {error}",
            "",
            "Traceback:",
            "".join(traceback.format_exception(error)).rstrip(),
            "",
        ]
    )
