import json
from io import BytesIO

from app.core.config import get_minio_config
from app.core.error_codes import ErrorCode
from app.core.exceptions import NotFoundError
from app.core.minio import client
from minio.error import S3Error
from starlette.concurrency import run_in_threadpool


class MinioService:
    def __init__(self) -> None:
        self._client = client
        self._bucket = get_minio_config().MINIO_BUCKET_NAME

    async def _ensure_bucket(self) -> None:
        exists = await run_in_threadpool(self._client.bucket_exists, self._bucket)
        if exists:
            return

        await run_in_threadpool(self._client.make_bucket, self._bucket)
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{self._bucket}/*"],
                }
            ],
        }
        await run_in_threadpool(self._client.set_bucket_policy, self._bucket, json.dumps(policy))

    async def upload_file(self, object_name: str, data: bytes, content_type: str) -> str:
        await self._ensure_bucket()
        await run_in_threadpool(
            self._client.put_object,
            self._bucket,
            object_name,
            BytesIO(data),
            len(data),
            content_type=content_type,
        )
        return get_minio_config().bucket_url + object_name

    async def delete_file(self, object_name: str) -> None:
        await self._ensure_bucket()
        await run_in_threadpool(self._client.remove_object, self._bucket, object_name)

    async def file_exists(self, object_name: str) -> bool:
        await self._ensure_bucket()
        try:
            await run_in_threadpool(self._client.stat_object, self._bucket, object_name)
            return True
        except S3Error as exc:
            raise NotFoundError(ErrorCode.AVATAR_NOT_FOUND) from exc


minio_service = MinioService()
