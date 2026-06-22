from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

from pipeline.daily_social_publish import DailySocialPublishResult


SMTP_HOST_ENV_NAME = "SMTP_HOST"
SMTP_PORT_ENV_NAME = "SMTP_PORT"
SMTP_USERNAME_ENV_NAME = "SMTP_USERNAME"
SMTP_PASSWORD_ENV_NAME = "SMTP_PASSWORD"
NOTIFICATION_EMAIL_TO_ENV_NAME = "NOTIFICATION_EMAIL_TO"
NOTIFICATION_EMAIL_FROM_ENV_NAME = "NOTIFICATION_EMAIL_FROM"


def send_daily_publish_email_report(
    daily_publish_results: list[DailySocialPublishResult],
) -> None:
    email_message = build_daily_publish_email_message(daily_publish_results)

    with smtplib.SMTP_SSL(
        get_required_environment_value(SMTP_HOST_ENV_NAME),
        int(get_required_environment_value(SMTP_PORT_ENV_NAME)),
    ) as smtp_client:
        smtp_client.login(
            get_required_environment_value(SMTP_USERNAME_ENV_NAME),
            get_required_environment_value(SMTP_PASSWORD_ENV_NAME),
        )
        smtp_client.send_message(email_message)


def build_daily_publish_email_message(
    daily_publish_results: list[DailySocialPublishResult],
) -> EmailMessage:
    email_message = EmailMessage()
    email_message["Subject"] = build_daily_publish_email_subject(
        daily_publish_results
    )
    email_message["From"] = get_required_environment_value(
        NOTIFICATION_EMAIL_FROM_ENV_NAME
    )
    email_message["To"] = get_required_environment_value(
        NOTIFICATION_EMAIL_TO_ENV_NAME
    )
    email_message.set_content(
        build_daily_publish_email_body(daily_publish_results),
        subtype="plain",
        charset="utf-8",
    )

    return email_message


def build_daily_publish_email_subject(
    daily_publish_results: list[DailySocialPublishResult],
) -> str:
    if not daily_publish_results:
        return "[Public Data Automation] 오늘 게시할 콘텐츠 없음"

    failed_channel_count = count_failed_publish_channels(daily_publish_results)

    if failed_channel_count:
        return f"[Public Data Automation] 게시 완료 - 실패 채널 {failed_channel_count}건"

    return "[Public Data Automation] 게시 성공"


def build_daily_publish_email_body(
    daily_publish_results: list[DailySocialPublishResult],
) -> str:
    if not daily_publish_results:
        return "오늘 게시할 후보가 없습니다."

    body_lines = [
        f"오늘 게시 대상: {len(daily_publish_results)}건",
        "",
    ]

    for index, daily_publish_result in enumerate(daily_publish_results, start=1):
        post_content = daily_publish_result.prepared_post.post_content
        body_lines.extend(
            [
                f"{index}. [{post_content.category}] {post_content.title}",
                f"   출처: {post_content.source_name}",
                f"   URL: {post_content.source_url}",
            ]
        )

        for publish_result in daily_publish_result.publish_results:
            status_text = "성공" if publish_result.is_success else "실패"
            body_lines.append(f"   - {publish_result.channel_name}: {status_text}")

            if publish_result.remote_post_id:
                body_lines.append(f"     게시 ID: {publish_result.remote_post_id}")

            if publish_result.remote_url:
                body_lines.append(f"     게시 URL: {publish_result.remote_url}")

            if publish_result.error_message:
                body_lines.append(f"     오류: {publish_result.error_message}")

        body_lines.append("")

    return "\n".join(body_lines).strip()


def count_failed_publish_channels(
    daily_publish_results: list[DailySocialPublishResult],
) -> int:
    return sum(
        1
        for daily_publish_result in daily_publish_results
        for publish_result in daily_publish_result.publish_results
        if not publish_result.is_success
    )


def get_required_environment_value(environment_name: str) -> str:
    environment_value = os.getenv(environment_name, "").strip()

    if environment_value:
        return environment_value

    raise RuntimeError(f"{environment_name} environment variable is required.")

