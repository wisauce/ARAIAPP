import asyncio
import io
from functools import lru_cache
from pathlib import Path
from typing import Protocol

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError

from app.config import Settings, get_settings
from app.errors import AppError


class ObjectStorage(Protocol):
    async def ensure_bucket(self) -> None: ...
    async def upload(self, key: str, data: bytes, content_type: str) -> None: ...
    def signed_url(self, key: str) -> str: ...


class LocalDiskStorage:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.root = Path(settings.local_storage_dir)

    async def ensure_bucket(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    async def upload(self, key: str, data: bytes, content_type: str) -> None:
        path = self._path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_bytes, data)

    def signed_url(self, key: str) -> str:
        base = self.settings.public_base_url.rstrip("/")
        return f"{base}/media/{key}"

    def _path_for(self, key: str) -> Path:
        relative = Path(key)
        if relative.is_absolute() or ".." in relative.parts:
            raise AppError(400, "VALIDATION_ERROR", "Invalid object key.")
        return self.root / relative


class S3Storage:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client: BaseClient = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key.get_secret_value(),
            region_name=settings.s3_region,
        )
        self.public_client: BaseClient = boto3.client(
            "s3",
            endpoint_url=settings.s3_public_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key.get_secret_value(),
            region_name=settings.s3_region,
        )

    async def ensure_bucket(self) -> None:
        def ensure() -> None:
            try:
                self.client.head_bucket(Bucket=self.settings.s3_bucket)
            except ClientError as exc:
                status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
                if status not in {403, 404}:
                    raise
                self.client.create_bucket(Bucket=self.settings.s3_bucket)

        try:
            await asyncio.to_thread(ensure)
        except ClientError as exc:
            raise AppError(503, "STORAGE_ERROR", "Object storage is unavailable.") from exc

    async def upload(self, key: str, data: bytes, content_type: str) -> None:
        try:
            await asyncio.to_thread(
                self.client.upload_fileobj,
                io.BytesIO(data),
                self.settings.s3_bucket,
                key,
                ExtraArgs={"ContentType": content_type},
            )
        except ClientError as exc:
            raise AppError(503, "STORAGE_ERROR", "Floor plan upload failed.") from exc

    def signed_url(self, key: str) -> str:
        try:
            return self.public_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.settings.s3_bucket, "Key": key},
                ExpiresIn=self.settings.signed_url_expires_seconds,
            )
        except ClientError as exc:
            raise AppError(503, "STORAGE_ERROR", "Floor plan URL could not be created.") from exc


@lru_cache
def get_storage() -> ObjectStorage:
    settings = get_settings()
    if settings.storage_backend.lower() == "s3":
        return S3Storage(settings)
    return LocalDiskStorage(settings)
