from fastapi import status

from app.core.error_codes import ErrorCode


class CustomError(Exception):
    def __init__(
        self,
        error: ErrorCode,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        headers: dict[str, str] | None = None,
        detail: str | None = None,
    ):
        self.error_code = error.code
        self.detail = detail or error.message
        self.status_code = status_code
        self.headers = headers
        super().__init__(self.detail)


class ValidationError(CustomError):
    def __init__(self, error: ErrorCode, detail: str | None = None):
        super().__init__(error, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class NotFoundError(CustomError):
    def __init__(self, error: ErrorCode, detail: str | None = None):
        super().__init__(error, status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class BadRequestError(CustomError):
    def __init__(self, error: ErrorCode, detail: str | None = None):
        super().__init__(error, status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class AlreadyExistsError(CustomError):
    def __init__(self, error: ErrorCode, detail: str | None = None):
        super().__init__(error, status_code=status.HTTP_409_CONFLICT, detail=detail)


class ForbiddenError(CustomError):
    def __init__(self, error: ErrorCode, headers: dict[str, str] | None = None, detail: str | None = None):
        super().__init__(error, status_code=status.HTTP_403_FORBIDDEN, headers=headers, detail=detail)


class UnauthorizedError(CustomError):
    def __init__(self, error: ErrorCode, headers: dict[str, str] | None = None, detail: str | None = None):
        super().__init__(error, status_code=status.HTTP_401_UNAUTHORIZED, headers=headers, detail=detail)


class BookRagUnavailableError(CustomError):
    def __init__(self, detail: str | None = None):
        super().__init__(ErrorCode.DOCUMENT_SERVICE_UNAVAILABLE, status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)


class DocumentStorageUnavailableError(CustomError):
    def __init__(self, detail: str | None = None):
        super().__init__(ErrorCode.DOCUMENT_STORAGE_UNAVAILABLE, status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)


class MediaStorageUnavailableError(CustomError):
    def __init__(self, detail: str | None = None):
        super().__init__(ErrorCode.MEDIA_STORAGE_UNAVAILABLE, status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)


class ImageGenerationUnavailableError(CustomError):
    def __init__(self, detail: str | None = None):
        super().__init__(ErrorCode.IMAGE_GENERATION_UNAVAILABLE, status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
