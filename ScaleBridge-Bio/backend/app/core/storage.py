"""Object storage abstraction supporting local filesystem and S3/MinIO with SHA-256 verification."""

from __future__ import annotations

import hashlib
from pathlib import Path

from app.core.config import settings


class ObjectStore:
    def put_bytes(
        self, storage_key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        sha256 = hashlib.sha256(data).hexdigest()
        if settings.storage_backend == "s3":
            import boto3

            s3 = boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint_url,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
            )
            try:
                s3.head_bucket(Bucket=settings.s3_bucket)
            except Exception:
                s3.create_bucket(Bucket=settings.s3_bucket)
            s3.put_object(
                Bucket=settings.s3_bucket,
                Key=storage_key,
                Body=data,
                ContentType=content_type,
            )
            return sha256

        base = Path(settings.local_storage_path).resolve()
        dest = (base / storage_key).resolve()
        if base not in dest.parents and dest != base:
            raise ValueError("Invalid storage key: path traversal detected")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return sha256

    def get_bytes(self, storage_key: str) -> bytes:
        if settings.storage_backend == "s3":
            import boto3

            s3 = boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint_url,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
            )
            resp = s3.get_object(Bucket=settings.s3_bucket, Key=storage_key)
            return bytes(resp["Body"].read())

        base = Path(settings.local_storage_path).resolve()
        src = (base / storage_key).resolve()
        if base not in src.parents and src != base:
            raise ValueError("Invalid storage key: path traversal detected")
        if not src.exists():
            raise FileNotFoundError(f"Storage object not found: {storage_key}")
        return src.read_bytes()


object_store = ObjectStore()
