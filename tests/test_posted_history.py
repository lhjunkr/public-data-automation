from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from storage.posted_history import (
    POST_STATUS_PUBLISHED,
    PostedHistoryRecord,
    append_posted_history_records,
    build_posted_history_key,
    collect_history_lines_for_date,
    is_recent_posted_history_key,
    load_posted_source_urls,
    parse_posted_history_date,
)


class TestPostedHistory(unittest.TestCase):
    def test_build_posted_history_key(self) -> None:
        self.assertEqual(
            build_posted_history_key("2026-06-21"),
            "private/history/2026-06-21/history.jsonl",
        )

    def test_parse_posted_history_date(self) -> None:
        parsed_date = parse_posted_history_date(
            "private/history/2026-06-21/history.jsonl"
        )

        self.assertEqual(parsed_date, date(2026, 6, 21))

    def test_parse_posted_history_date_ignores_non_history_key(self) -> None:
        parsed_date = parse_posted_history_date("images/2026-06-21/post.png")

        self.assertIsNone(parsed_date)

    def test_is_recent_posted_history_key_keeps_recent_history(self) -> None:
        self.assertTrue(
            is_recent_posted_history_key(
                object_key="private/history/2026-06-10/history.jsonl",
                today=date(2026, 6, 21),
                retention_days=20,
            )
        )

    def test_is_recent_posted_history_key_excludes_old_history(self) -> None:
        self.assertFalse(
            is_recent_posted_history_key(
                object_key="private/history/2026-06-01/history.jsonl",
                today=date(2026, 6, 21),
                retention_days=20,
            )
        )

    def test_load_posted_source_urls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "history.jsonl"
            history_path.write_text(
                "\n".join(
                    [
                        '{"source_url": "https://example.com/1"}',
                        '{"source_url": "https://example.com/2"}',
                        '{"source_url": ""}',
                        "invalid-json",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            posted_source_urls = load_posted_source_urls(str(history_path))

        self.assertEqual(
            posted_source_urls,
            {"https://example.com/1", "https://example.com/2"},
        )

    def test_append_posted_history_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "history.jsonl"

            append_posted_history_records(
                history_records=[
                    PostedHistoryRecord(
                        recorded_at="2026-06-21T09:00:00+09:00",
                        status=POST_STATUS_PUBLISHED,
                        category="대구 창업지원",
                        title="테스트 공고",
                        source_name="K-Startup",
                        source_url="https://example.com/startup",
                        facebook_post_id="facebook-1",
                    )
                ],
                local_history_path=str(history_path),
            )

            history_text = history_path.read_text(encoding="utf-8")

        self.assertIn('"source_url": "https://example.com/startup"', history_text)
        self.assertIn('"facebook_post_id": "facebook-1"', history_text)

    def test_collect_history_lines_for_date(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            history_path = Path(temp_dir) / "history.jsonl"
            history_path.write_text(
                "\n".join(
                    [
                        '{"recorded_at": "2026-06-21T09:00:00+09:00", "source_url": "https://example.com/today"}',
                        '{"recorded_at": "2026-06-20T09:00:00+09:00", "source_url": "https://example.com/yesterday"}',
                        '{"recorded_at": "invalid-date", "source_url": "https://example.com/invalid"}',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            today_lines = collect_history_lines_for_date(
                history_path=history_path,
                run_date="2026-06-21",
            )

        self.assertEqual(len(today_lines), 1)
        self.assertIn("https://example.com/today", today_lines[0])


if __name__ == "__main__":
    unittest.main()