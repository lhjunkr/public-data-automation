from __future__ import annotations

import unittest

from content.date_formatting import format_display_date


class TestDateFormatting(unittest.TestCase):
    def test_format_display_date_from_yyyymmdd(self) -> None:
        self.assertEqual(format_display_date("20260707"), "2026.07.07")

    def test_format_display_date_from_iso_date(self) -> None:
        self.assertEqual(format_display_date("2026-06-21"), "2026.06.21")

    def test_format_display_date_from_rss_date(self) -> None:
        self.assertEqual(
            format_display_date("Sun, 21 Jun 2026 10:58:52 GMT"),
            "2026.06.21",
        )

    def test_format_display_date_returns_empty_string_for_empty_value(self) -> None:
        self.assertEqual(format_display_date(""), "")

    def test_format_display_date_returns_original_value_when_parse_fails(self) -> None:
        self.assertEqual(format_display_date("날짜 없음"), "날짜 없음")


if __name__ == "__main__":
    unittest.main()
    
    