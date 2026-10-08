from collections.abc import Callable

from vercel.blob import Access, AsyncBlobClient, BlobError

from app.core.config import get_blob_config
from app.core.exceptions import CustomError, DocumentStorageUnavailableError, MediaStorageUnavailableError
from app.core.logger import log


def _store_base_url(token: str, access: Access) -> str:
    parts = token.split("_")
    if len(parts) < 5 or not parts[3]:
        raise ValueError("Vercel Blob token has unexpected format, expected vercel_blob_rw_<storeId>_<secret>")
    return f"https://{parts[3].lower()}.{access}.blob.vercel-storage.com/"


class BlobStorage:
    def __init__(self, token: str, access: Access, unavailable_error: Callable[[], CustomError]) -> None:
        self._client = AsyncBlobClient(token=token)
        self._access: Access = access
        self._base_url = _store_base_url(token, access)
        self._unavailable_error = unavailable_error

    def url(self, object_name: str) -> str:
        return self._base_url + object_name

    def public_url(self, object_name: str) -> str:
        if self._access != "public":
            raise ValueError("private blob store, objects have no public URL")
        return self.url(object_name)

    async def upload_file(self, object_name: str, data: bytes, content_type: str) -> None:
        try:
            await self._client.put(
                object_name,
                data,
                access=self._access,
                content_type=content_type,
                add_random_suffix=False,
            )
        except BlobError as exc:
            log.error("blob_upload_failed", access=self._access, object_name=object_name, error=type(exc).__name__)
            raise self._unavailable_error() from exc

    async def delete_file(self, object_name: str) -> None:
        await self.delete_files([object_name])

    async def delete_files(self, object_names: list[str]) -> None:
        if not object_names:
            return
        try:
            await self._client.delete([self.url(name) for name in object_names])
        except BlobError as exc:
            log.error("blob_delete_failed", access=self._access, count=len(object_names), error=type(exc).__name__)
            raise self._unavailable_error() from exc

    async def close(self) -> None:
        await self._client.aclose()


public_storage = BlobStorage(
    get_blob_config().BLOB_READ_WRITE_TOKEN.get_secret_value(), "public", MediaStorageUnavailableError
)
documents_storage = BlobStorage(
    get_blob_config().BLOB_DOCUMENTS_READ_WRITE_TOKEN.get_secret_value(), "private", DocumentStorageUnavailableError
)
