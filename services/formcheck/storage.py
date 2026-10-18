"""MinIO / S3-compatible object storage abstraction."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from formcheck.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ObjectStat:
    key: str
    size: int
    content_type: str | None
    etag: str | None


def source_object_key(analysis_id: str, filename: str) -> str:
    safe = filename.replace("\\", "/").split("/")[-1] or "upload.bin"
    return f"analyses/{analysis_id}/source/{safe}"


class ObjectStorage:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._internal = self._client(self.settings.minio_endpoint)
        self._public = self._client(self.settings.minio_public_endpoint)

    def _client(self, endpoint: str):
        return boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=self.settings.minio_access_key,
            aws_secret_access_key=self.settings.minio_secret_key,
            region_name=self.settings.minio_region,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    @property
    def bucket(self) -> str:
        return self.settings.minio_bucket

    def ensure_bucket(self) -> None:
        try:
            self._internal.head_bucket(Bucket=self.bucket)
        except ClientError:
            self._internal.create_bucket(Bucket=self.bucket)
        self._apply_cors()

    def _apply_cors(self) -> None:
        origins = get_settings().cors_origin_list or ["*"]
        try:
            self._internal.put_bucket_cors(
                Bucket=self.bucket,
                CORSConfiguration={
                    "CORSRules": [
                        {
                            "AllowedOrigins": origins,
                            "AllowedMethods": ["GET", "PUT", "HEAD"],
                            "AllowedHeaders": ["*"],
                            "ExposeHeaders": ["ETag", "Content-Length"],
                            "MaxAgeSeconds": 3600,
                        }
                    ]
                },
            )
        except ClientError as exc:
            logger.warning("Unable to set MinIO CORS: %s", exc)

    def put_bytes(self, key: str, payload: bytes, content_type: str) -> None:
        self._internal.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=payload,
            ContentType=content_type,
            ContentLength=len(payload),
        )

    def presign_put(self, key: str, content_type: str, expires_in: int | None = None) -> str:
        expires = expires_in or self.settings.upload_url_expires_seconds
        return self._public.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=expires,
        )

    def object_exists(self, key: str) -> bool:
        try:
            self.stat_object(key)
            return True
        except FileNotFoundError:
            return False

    def stat_object(self, key: str) -> ObjectStat:
        try:
            head = self._internal.head_object(Bucket=self.bucket, Key=key)
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in {"404", "NoSuchKey", "NotFound", "404 Not Found"}:
                raise FileNotFoundError(key) from exc
            raise
        return ObjectStat(
            key=key,
            size=int(head.get("ContentLength") or 0),
            content_type=head.get("ContentType"),
            etag=head.get("ETag"),
        )

    def download_file(self, key: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._internal.download_file(self.bucket, key, str(destination))
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code", "")
            if code in {"404", "NoSuchKey", "NotFound", "404 Not Found"}:
                raise FileNotFoundError(key) from exc
            raise

    def upload_file(self, key: str, source: Path, *, content_type: str) -> ObjectStat:
        self._internal.upload_file(
            str(source),
            self.bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )
        return self.stat_object(key)

    def delete_object(self, key: str) -> None:
        self._internal.delete_object(Bucket=self.bucket, Key=key)

    def delete_prefix(self, prefix: str) -> list[str]:
        deleted: list[str] = []
        paginator = self._internal.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents") or []:
                key = obj["Key"]
                self.delete_object(key)
                deleted.append(key)
        return deleted


def rewrite_presign_host_for_browser(url: str, public_endpoint: str) -> str:
    """Ensure presigned URLs use the browser-reachable host."""
    public = urlparse(public_endpoint)
    parsed = urlparse(url)
    return parsed._replace(
        scheme=public.scheme or parsed.scheme,
        netloc=public.netloc or parsed.netloc,
    ).geturl()
