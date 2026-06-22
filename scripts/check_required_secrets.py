from __future__ import annotations

import os
import sys


ALWAYS_REQUIRED_ENV_NAMES = [
    "KSTARTUP_API_KEY",
    "GEMINI_API_KEY",
    "R2_ACCOUNT_ID",
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
    "R2_BUCKET_NAME",
    "R2_ASSETS_ACCESS_KEY_ID",
    "R2_ASSETS_SECRET_ACCESS_KEY",
    "R2_ASSETS_BUCKET_NAME",
    "R2_ASSETS_PUBLIC_BASE_URL",
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USERNAME",
    "SMTP_PASSWORD",
    "NOTIFICATION_EMAIL_TO",
    "NOTIFICATION_EMAIL_FROM",
]

CHANNEL_REQUIRED_ENV_NAMES = {
    "facebook": {
        "enable_env_name": "ENABLE_FACEBOOK_PUBLISH",
        "required_env_names": [
            "FACEBOOK_PAGE_ID",
            "FACEBOOK_PAGE_ACCESS_TOKEN",
        ],
    },
    "instagram": {
        "enable_env_name": "ENABLE_INSTAGRAM_PUBLISH",
        "required_env_names": [
            "IG_USER_ID",
            "META_ACCESS_TOKEN",
        ],
    },
    "threads": {
        "enable_env_name": "ENABLE_THREADS_PUBLISH",
        "required_env_names": [
            "THREADS_USER_ID",
            "THREADS_ACCESS_TOKEN",
        ],
    },
    "naver_band": {
        "enable_env_name": "ENABLE_NAVER_BAND_PUBLISH",
        "required_env_names": [
            "BAND_ACCESS_TOKEN",
            "BAND_KEY",
        ],
    },
}


def main() -> int:
    missing_env_names = collect_missing_required_env_names()

    if missing_env_names:
        print("필수 환경변수가 누락되었습니다.")
        for env_name in missing_env_names:
            print(f"- {env_name}")

        return 1

    print("필수 환경변수 확인 완료")
    return 0


def collect_missing_required_env_names() -> list[str]:
    required_env_names = list(ALWAYS_REQUIRED_ENV_NAMES)

    for channel_config in CHANNEL_REQUIRED_ENV_NAMES.values():
        if is_enabled(channel_config["enable_env_name"]):
            required_env_names.extend(channel_config["required_env_names"])

    return [
        env_name
        for env_name in required_env_names
        if not os.getenv(env_name, "").strip()
    ]


def is_enabled(enable_env_name: str) -> bool:
    env_value = os.getenv(enable_env_name)

    if env_value is None:
        return True

    return env_value.strip().lower() == "true"


if __name__ == "__main__":
    sys.exit(main())
    
    