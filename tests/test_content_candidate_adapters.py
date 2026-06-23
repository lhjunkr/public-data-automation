from __future__ import annotations

import unittest

from selection.content_candidate_adapters import recruitment_notice_to_candidate
from sources.daegu_public_recruitment import DaeguPublicRecruitmentNotice


class TestContentCandidateAdapters(unittest.TestCase):
    def test_recruitment_notice_keeps_clear_institution_source_name(self) -> None:
        notice = DaeguPublicRecruitmentNotice(
            category="대구 채용·시험",
            section="공공",
            title="2026년도 대구광역시 지방공무원 임용시험 공고",
            source_name="대구광역시 시험정보 - 공채/경채 공무원",
            source_url="https://www.daegu.go.kr/example",
            published_at="2026.06.23",
        )

        candidate = recruitment_notice_to_candidate(notice)

        self.assertEqual(
            candidate.source_name,
            "대구광역시 시험정보 - 공채/경채 공무원",
        )


if __name__ == "__main__":
    unittest.main()
