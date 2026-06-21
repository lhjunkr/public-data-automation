from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import boto3


POSTED_HISTORY_RETENTION_DAYS = 20
POSTED_HISTORY_LOCAL_PATH = "history.jsonl"
R2_POSTED_HISTORY_PREFIX = "private/history"

POST_STATUS_PUBLISHED = "published"
POST_STATUS_PARTIAL_FAILED = "partial_failed"
POST_STATUS_FAILED = "failed"


@dataclass(frozen=True)
class PostedHistoryRecord:
    recorded_at: str
    status: str
    category: str
    title: str
    source_name: str
    source_url: str
    facebook_post_id: str = ""
    instagram_post_id: str = ""
    threads_post_id: str = ""
    naver_band_post_key: str = ""


def create_r2_client() -> Any:
    account_id = get_required_env("R2_ACCOUNT_ID")
    access_key_id = get_required_env("R2_ACCESS_KEY_ID")
    secret_access_key = get_required_env("R2_SECRET_ACCESS_KEY")

    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name="auto",
    )


def get_required_env(env_name: str) -> str:
    env_value = os.getenv(env_name, "").strip()

    if not env_value:
        raise RuntimeError(f"{env_name} GitHub Actions Secret이 필요합니다.")

    return env_value


def get_r2_bucket_name() -> str:
    return get_required_env("R2_BUCKET_NAME")


def build_posted_history_key(run_date: str) -> str:
    return f"{R2_POSTED_HISTORY_PREFIX}/{run_date}/history.jsonl"


def parse_posted_history_date(object_key: str) -> date | None:
    prefix = f"{R2_POSTED_HISTORY_PREFIX}/"

    if not object_key.startswith(prefix) or not object_key.endswith("/history.jsonl"):
        return None

    date_text = object_key.removeprefix(prefix).split("/", 1)[0]

    try:
        return datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        return None


def is_recent_posted_history_key(
    object_key: str,
    today: date,
    retention_days: int = POSTED_HISTORY_RETENTION_DAYS,
) -> bool:
    history_date = parse_posted_history_date(object_key)

    if history_date is None:
        return False

    age_days = (today - history_date).days

    return 0 <= age_days < retention_days


def list_r2_posted_history_keys() -> list[str]:
    client = create_r2_client()
    bucket_name = get_r2_bucket_name()

    history_keys: list[str] = []
    continuation_token: str | None = None

    while True:
        list_kwargs: dict[str, Any] = {
            "Bucket": bucket_name,
            "Prefix": f"{R2_POSTED_HISTORY_PREFIX}/",
        }

        if continuation_token:
            list_kwargs["ContinuationToken"] = continuation_token

        response = client.list_objects_v2(**list_kwargs)

        for item in response.get("Contents", []):
            object_key = str(item.get("Key", "")).strip()

            if object_key:
                history_keys.append(object_key)

        if not response.get("IsTruncated"):
            break

        continuation_token = response.get("NextContinuationToken")

    return history_keys


def download_recent_posted_history_from_r2(
    local_history_path: str = POSTED_HISTORY_LOCAL_PATH,
    today: date | None = None,
    retention_days: int = POSTED_HISTORY_RETENTION_DAYS,
) -> None:
    run_date = today or date.today()
    client = create_r2_client()
    bucket_name = get_r2_bucket_name()

    recent_history_keys = [
        object_key
        for object_key in list_r2_posted_history_keys()
        if is_recent_posted_history_key(
            object_key=object_key,
            today=run_date,
            retention_days=retention_days,
        )
    ]

    if not recent_history_keys:
        Path(local_history_path).write_text("", encoding="utf-8")
        print("R2 게시 이력 없음: 새 history.jsonl로 시작합니다.")
        return

    history_lines: list[str] = []
    seen_lines: set[str] = set()

    for object_key in sorted(recent_history_keys):
        response = client.get_object(Bucket=bucket_name, Key=object_key)
        body = response["Body"].read().decode("utf-8")

        for line in body.splitlines():
            cleaned_line = line.strip()

            if not cleaned_line or cleaned_line in seen_lines:
                continue

            try:
                json.loads(cleaned_line)
            except json.JSONDecodeError:
                continue

            seen_lines.add(cleaned_line)
            history_lines.append(cleaned_line)

    Path(local_history_path).write_text(
        "\n".join(history_lines) + "\n",
        encoding="utf-8",
    )
    print(f"R2 게시 이력 동기화 완료: {len(history_lines)}건")


def load_posted_source_urls(
    local_history_path: str = POSTED_HISTORY_LOCAL_PATH,
) -> set[str]:
    history_path = Path(local_history_path)

    if not history_path.exists():
        return set()

    posted_source_urls: set[str] = set()

    with open(history_path, encoding="utf-8") as history_file:
        for line in history_file:
            record = load_history_record_from_line(line)

            if record is None:
                continue

            source_url = str(record.get("source_url", "")).strip()

            if source_url:
                posted_source_urls.add(source_url)

    return posted_source_urls


def append_posted_history_records(
    history_records: list[PostedHistoryRecord],
    local_history_path: str = POSTED_HISTORY_LOCAL_PATH,
) -> None:
    if not history_records:
        return

    with open(local_history_path, "a", encoding="utf-8") as history_file:
        for history_record in history_records:
            history_file.write(
                json.dumps(asdict(history_record), ensure_ascii=False) + "\n"
            )


def upload_today_posted_history_to_r2(
    run_date: str,
    local_history_path: str = POSTED_HISTORY_LOCAL_PATH,
) -> None:
    history_path = Path(local_history_path)

    if not history_path.exists():
        print("업로드할 게시 이력 파일이 없습니다.")
        return

    today_lines = collect_history_lines_for_date(
        history_path=history_path,
        run_date=run_date,
    )

    if not today_lines:
        print("오늘 업로드할 게시 이력이 없습니다.")
        return

    client = create_r2_client()
    bucket_name = get_r2_bucket_name()
    object_key = build_posted_history_key(run_date)
    body = "\n".join(today_lines) + "\n"

    client.put_object(
        Bucket=bucket_name,
        Key=object_key,
        Body=body.encode("utf-8"),
        ContentType="application/jsonl; charset=utf-8",
    )
    print(f"R2 게시 이력 업로드 완료: {object_key}")


def collect_history_lines_for_date(history_path: Path, run_date: str) -> list[str]:
    today_lines: list[str] = []

    with open(history_path, encoding="utf-8") as history_file:
        for line in history_file:
            cleaned_line = line.strip()

            if not cleaned_line:
                continue

            record = load_history_record_from_line(cleaned_line)

            if record is None:
                continue

            recorded_at = str(record.get("recorded_at", ""))

            try:
                recorded_date = datetime.fromisoformat(recorded_at).date()
            except ValueError:
                continue

            if recorded_date.isoformat() == run_date:
                today_lines.append(cleaned_line)

    return today_lines


def cleanup_old_r2_posted_history(
    today: date | None = None,
    retention_days: int = POSTED_HISTORY_RETENTION_DAYS,
) -> None:
    run_date = today or date.today()
    client = create_r2_client()
    bucket_name = get_r2_bucket_name()

    for object_key in list_r2_posted_history_keys():
        history_date = parse_posted_history_date(object_key)

        if history_date is None:
            continue

        age_days = (run_date - history_date).days

        if age_days >= retention_days:
            client.delete_object(Bucket=bucket_name, Key=object_key)
            print(f"오래된 R2 게시 이력 삭제: {object_key}")


def load_history_record_from_line(line: str) -> dict[str, Any] | None:
    cleaned_line = line.strip()

    if not cleaned_line:
        return None

    try:
        record = json.loads(cleaned_line)
    except json.JSONDecodeError:
        return None

    if not isinstance(record, dict):
        return None

    return record