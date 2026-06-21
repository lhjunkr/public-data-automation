from __future__ import annotations

import argparse

from pipeline.daily_post_preparation import prepare_daily_posts


def main() -> None:
    args = parse_args()
    prepared_posts = prepare_daily_posts(
        sync_posted_history=False,
        upload_assets=not args.skip_upload,
    )

    print(f"오늘 게시 준비 결과: {len(prepared_posts)}건")

    for index, prepared_post in enumerate(prepared_posts, start=1):
        post_content = prepared_post.post_content

        print("=" * 60)
        print(f"{index}. [{post_content.category}] {post_content.title}")
        print("-" * 60)
        print("[Caption]")
        print(post_content.caption)
        print()
        print(f"이미지 파일: {prepared_post.local_image_path}")
        print(f"공개 이미지 URL: {prepared_post.public_image_url or '(업로드 생략)'}")
        print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SNS 업로드 직전 게시물 데이터를 생성합니다.",
    )
    parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="R2 assets 업로드 없이 로컬 이미지 생성까지만 확인합니다.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    main()
