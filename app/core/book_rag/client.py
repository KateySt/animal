import logging
from uuid import UUID

import httpx
from tenacity import before_sleep_log, retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_book_rag_config
from app.core.exceptions import BookRagUnavailableError


client_book_rag = httpx.AsyncClient(
    base_url=get_book_rag_config().BOOK_RAG_BASE_URL,
    headers={"X-Internal-Token": get_book_rag_config().INTERNAL_SERVICE_TOKEN},
    timeout=get_book_rag_config().BOOK_RAG_REQUEST_TIMEOUT_SECONDS,
)


async def close_client() -> None:
    await client_book_rag.aclose()


def _raise_for_retry(response: httpx.Response) -> None:
    if response.status_code >= 500:
        raise BookRagUnavailableError(detail=f"book-rag returned {response.status_code}")
    response.raise_for_status()


with_retry = retry(
    retry=retry_if_exception_type((httpx.TransportError, BookRagUnavailableError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING),
    reraise=True,
)


@with_retry
async def request_embedding(chat_session_id: UUID, document_id: UUID, filename: str, content_type: str, data: bytes) -> None:
    response = await client_book_rag.post(
        "/documents",
        data={"chat_session_id": str(chat_session_id), "document_id": str(document_id), "filename": filename},
        files={"file": (filename, data, content_type)},
    )
    _raise_for_retry(response)


@with_retry
async def delete_document(document_id: UUID) -> None:
    response = await client_book_rag.delete(f"/documents/{document_id}")
    if response.status_code == httpx.codes.NOT_FOUND:
        return
    _raise_for_retry(response)


@with_retry
async def search_documents(chat_session_id: UUID, query: str, top_k: int = 5) -> list[dict]:
    response = await client_book_rag.post(
        "/search",
        json={"chat_session_id": str(chat_session_id), "query": query, "top_k": top_k},
    )
    _raise_for_retry(response)
    return response.json()
