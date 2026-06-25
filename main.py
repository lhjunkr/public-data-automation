from __future__ import annotations

import sys
from datetime import date, datetime

from pipeline.daily_social_publish import publish_daily_posts_to_social_channels
from reporting.console_report import (
    has_completely_failed_post,
    print_daily_publish_results,
)
from reporting.run_report import (
    create_run_output_dir,
    save_failure_report,
    save_run_report,
)


def main() -> int:
    run_date = date.today()
    run_output_dir = create_run_output_dir(run_date)
    started_at = datetime.now().astimezone()

    try:
        daily_publish_results = publish_daily_posts_to_social_channels(
            today=run_date,
            sync_posted_history=True,
            upload_assets=True,
            record_posted_history=True,
            upload_posted_history=True,
        )
        finished_at = datetime.now().astimezone()
        print_daily_publish_results(daily_publish_results)
        save_run_report(
            run_output_dir=run_output_dir,
            daily_publish_results=daily_publish_results,
            started_at=started_at,
            finished_at=finished_at,
        )

        if has_completely_failed_post(daily_publish_results):
            return 1

        return 0
    except Exception as error:
        failed_at = datetime.now().astimezone()
        save_failure_report(
            run_output_dir=run_output_dir,
            error=error,
            started_at=started_at,
            failed_at=failed_at,
        )
        print(f"Public Data Automation 실행 실패: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
