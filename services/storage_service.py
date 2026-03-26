import os
from pathlib import Path
from typing import Any

try:
    import boto3
except ImportError:  # pragma: no cover - optional at edit time
    boto3 = None


def upload_to_s3(file_path: str, object_key: str | None = None) -> dict[str, Any]:
    bucket = os.getenv("S3_BUCKET_NAME", "").strip()
    region = os.getenv("AWS_REGION", "ap-south-1").strip()

    source = Path(file_path)
    if not source.exists():
        return {"status": "error", "reason": f"File not found: {file_path}"}

    if not bucket:
        return {
            "status": "skipped",
            "reason": "S3_BUCKET_NAME is not configured yet.",
            "file_path": file_path,
        }

    if boto3 is None:
        return {
            "status": "error",
            "reason": "boto3 is not installed in this runtime.",
            "file_path": file_path,
        }

    key = object_key or source.name
    try:
        client = boto3.client("s3", region_name=region)
        client.upload_file(str(source), bucket, key)
        return {
            "status": "ok",
            "bucket": bucket,
            "object_key": key,
            "file_path": file_path,
        }
    except Exception as exc:  # pragma: no cover - runtime dependent
        return {
            "status": "error",
            "reason": str(exc),
            "bucket": bucket,
            "object_key": key,
            "file_path": file_path,
        }


def get_s3_health() -> dict[str, Any]:
    bucket = os.getenv("S3_BUCKET_NAME", "").strip()
    region = os.getenv("AWS_REGION", "ap-south-1").strip()

    if not bucket:
        return {"status": "skipped", "message": "S3_BUCKET_NAME is not configured yet."}

    if boto3 is None:
        return {"status": "error", "message": "boto3 is not installed in this runtime."}

    try:
        client = boto3.client("s3", region_name=region)
        client.head_bucket(Bucket=bucket)
        return {"status": "ok", "bucket": bucket, "message": "S3 bucket is reachable."}
    except Exception as exc:  # pragma: no cover - runtime dependent
        return {"status": "error", "bucket": bucket, "message": str(exc)}
