from __future__ import annotations

import sys
from datetime import date

from pipeline.daily_social_publish import publish_daily_posts_to_social_channels
from reporting.console_report import (
    has_completely_failed_post,
    print_daily_publish_results,
)


def main() -> int:
    daily_publish_results = publish_daily_posts_to_social_channels(
        today=date.today(),
        sync_posted_history=True,
        upload_assets=True,
        record_posted_history=True,
        upload_posted_history=True,
    )

    print_daily_publish_results(daily_publish_results)

    if has_completely_failed_post(daily_publish_results):
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
