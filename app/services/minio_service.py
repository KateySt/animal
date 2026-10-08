import json
from io import BytesIO

from minio.deleteobjects import DeleteObject
from minio.error import S3Error
from starlette.concurrency import run_in_threadpool

from app.core.config import get_minio_config
from app.core.error_codes import ErrorCode
from app.core.exceptions import NotFoundError
from app.core.minio import client


class ObjectDeletionError(Exception):
    pass


class MinioService:
    def __init__(self, bucket: str, *, public: bool) -> None:
        self._client = client
        self._bucket = bucket
        self._public = public

    async def _ensure_bucket(self) -> None:
        exists = await run_in_threadpool(self._client.bucket_exists, self._bucket)
        if exists:
            return

        await run_in_threadpool(self._client.make_bucket, self._bucket)
        if not self._public:
            return

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

    def public_url(self, object_name: str) -> str:
        if not self._public:
            raise ValueError(f"bucket {self._bucket} is private, objects have no public URL")
        return get_minio_config().bucket_url + object_name

    async def upload_file(self, object_name: str, data: bytes, content_type: str) -> None:
        await self._ensure_bucket()
        await run_in_threadpool(
            self._client.put_object,
            self._bucket,
            object_name,
            BytesIO(data),
            len(data),
            content_type=content_type,
        )

    async def delete_file(self, object_name: str) -> None:
        await self._ensure_bucket()
        await run_in_threadpool(self._client.remove_object, self._bucket, object_name)

    async def delete_files(self, object_names: list[str]) -> None:
        if not object_names:
            return
        await self._ensure_bucket()
        errors = await run_in_threadpool(self._remove_objects, object_names)
        if errors:
            raise ObjectDeletionError(f"{len(errors)} object(s) not deleted, first: {errors[0]}")

    def _remove_objects(self, object_names: list[str]) -> list:
        return list(self._client.remove_objects(self._bucket, [DeleteObject(name) for name in object_names]))

    async def file_exists(self, object_name: str) -> bool:
        await self._ensure_bucket()
        try:
            await run_in_threadpool(self._client.stat_object, self._bucket, object_name)
            return True
        except S3Error as exc:
            raise NotFoundError(ErrorCode.AVATAR_NOT_FOUND) from exc


minio_service = MinioService(get_minio_config().MINIO_BUCKET_NAME, public=True)
documents_storage = MinioService(get_minio_config().MINIO_DOCUMENTS_BUCKET_NAME, public=False)
