from __future__ import annotations

import sys
from datetime import date

from pipeline.daily_social_publish import publish_daily_posts_to_social_channels


def main() -> int:
    daily_publish_results = publish_daily_posts_to_social_channels(
        today=date.today(),
        sync_posted_history=True,
        upload_assets=True,
        record_posted_history=True,
        upload_posted_history=True,
    )

    if not daily_publish_results:
        print("오늘 게시할 후보가 없습니다.")
        return 0

    has_failed_channel = False

    print(f"오늘 게시 대상: {len(daily_publish_results)}건")

    for index, daily_publish_result in enumerate(daily_publish_results, start=1):
        post_content = daily_publish_result.prepared_post.post_content
        print(f"{index}. [{post_content.category}] {post_content.title}")

        for publish_result in daily_publish_result.publish_results:
            status_text = "성공" if publish_result.is_success else "실패"
            print(f"   - {publish_result.channel_name}: {status_text}")

            if not publish_result.is_success:
                has_failed_channel = True
                print(f"     오류: {publish_result.error_message}")

    if has_failed_channel:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
    
    