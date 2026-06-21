from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import boto3


R2_ASSETS_BUCKET_ENV_NAME = "R2_ASSETS_BUCKET_NAME"
R2_ASSETS_PUBLIC_BASE_URL_ENV_NAME = "R2_ASSETS_PUBLIC_BASE_URL"
R2_ASSETS_ACCESS_KEY_ID_ENV_NAME = "R2_ASSETS_ACCESS_KEY_ID"
R2_ASSETS_SECRET_ACCESS_KEY_ENV_NAME = "R2_ASSETS_SECRET_ACCESS_KEY"

ASSET_IMAGE_PREFIX = "images"


def create_r2_assets_client() -> Any:
    account_id = get_required_env("R2_ACCOUNT_ID")
    access_key_id = get_required_env(R2_ASSETS_ACCESS_KEY_ID_ENV_NAME)
    secret_access_key = get_required_env(R2_ASSETS_SECRET_ACCESS_KEY_ENV_NAME)

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


def get_r2_assets_bucket_name() -> str:
    return get_required_env(R2_ASSETS_BUCKET_ENV_NAME)


def get_r2_assets_public_base_url() -> str:
    return get_required_env(R2_ASSETS_PUBLIC_BASE_URL_ENV_NAME).rstrip("/")


def build_asset_image_key(run_date: str, image_filename: str) -> str:
    safe_image_filename = Path(image_filename).name

    if not safe_image_filename:
        raise ValueError("image_filename이 비어 있습니다.")

    return f"{ASSET_IMAGE_PREFIX}/{run_date}/{safe_image_filename}"


def build_asset_public_url(object_key: str, public_base_url: str | None = None) -> str:
    base_url = (public_base_url or get_r2_assets_public_base_url()).rstrip("/")

    return f"{base_url}/{object_key.lstrip('/')}"


def upload_image_asset_to_r2(
    local_image_path: Path,
    object_key: str,
) -> str:
    if not local_image_path.exists():
        raise FileNotFoundError(f"업로드할 이미지 파일을 찾을 수 없습니다: {local_image_path}")

    client = create_r2_assets_client()
    bucket_name = get_r2_assets_bucket_name()

    client.upload_file(
        str(local_image_path),
        bucket_name,
        object_key,
        ExtraArgs={"ContentType": "image/png"},
    )

    return build_asset_public_url(object_key)
