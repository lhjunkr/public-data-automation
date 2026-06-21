import unittest

from sources.daegu_notice_classifier import (
    DAEGU_BUSINESS_SUPPORT_CATEGORY,
    DAEGU_PUBLIC_OPPORTUNITY_CATEGORY,
    classify_daegu_notice,
)
from sources.daegu_notice_rss import DaeguNotice


class DaeguNoticeClassifierTest(unittest.TestCase):
    def build_notice(self, title: str, summary: str = "") -> DaeguNotice:
        return DaeguNotice(
            title=title,
            source_name="대구시청 공지사항",
            source_url="https://www.daegu.go.kr/example",
            published_at="Sun, 21 Jun 2026 08:00:00 GMT",
            summary=summary,
        )

    def test_classifies_business_support_for_company_recruitment(self):
        notice = self.build_notice("2026년 대구식품산업 마케팅 지원사업 참여업체 모집 안내")

        self.assertEqual(classify_daegu_notice(notice), DAEGU_BUSINESS_SUPPORT_CATEGORY)

    def test_classifies_business_support_for_family_friendly_certification(self):
        notice = self.build_notice("2026년 가족친화인증 신청 연장 안내")

        self.assertEqual(classify_daegu_notice(notice), DAEGU_BUSINESS_SUPPORT_CATEGORY)

    def test_classifies_public_opportunity_for_photo_contest(self):
        notice = self.build_notice("제19회 동물사랑 사진·영상 공모전 개최 안내")

        self.assertEqual(classify_daegu_notice(notice), DAEGU_PUBLIC_OPPORTUNITY_CATEGORY)

    def test_classifies_public_opportunity_for_supporters_recruitment(self):
        notice = self.build_notice("청년 귀환 채널구축 사업 SNS 서포터즈 모집")

        self.assertEqual(classify_daegu_notice(notice), DAEGU_PUBLIC_OPPORTUNITY_CATEGORY)

    def test_excludes_startup_notice_to_avoid_duplicate_with_kstartup(self):
        notice = self.build_notice("2026년 제6회 대구 여성창업스타전 개최 안내")

        self.assertIsNone(classify_daegu_notice(notice))

    def test_excludes_recruitment_notice_to_avoid_duplicate_with_recruitment_rss(self):
        notice = self.build_notice("2026년도 대구광역시 지방공무원 임용시험 시행계획 공고")

        self.assertIsNone(classify_daegu_notice(notice))

    def test_excludes_general_procurement_notice(self):
        notice = self.build_notice("대명천 하천기본계획 수립 용역 사업책임기술인 평가결과 공개")

        self.assertIsNone(classify_daegu_notice(notice))

    def test_excludes_low_value_challenge_notice(self):
        notice = self.build_notice("2026 적극행정 응원 챌린지 공모전 안내")

        self.assertIsNone(classify_daegu_notice(notice))


if __name__ == "__main__":
    unittest.main()