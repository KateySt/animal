from fastapi import status


class CustomError(Exception):
    def __init__(
        self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class ValidationError(CustomError):
    def __init__(self, detail: str):
        super().__init__(detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class NotFoundError(CustomError):
    def __init__(self, detail: str):
        super().__init__(detail, status_code=status.HTTP_404_NOT_FOUND)


class BadRequestError(CustomError):
    def __init__(self, detail: str):
        super().__init__(detail, status_code=status.HTTP_400_BAD_REQUEST)


class AlreadyExistsError(CustomError):
    def __init__(self, detail: str):
        super().__init__(detail, status_code=status.HTTP_409_CONFLICT)


class ForbiddenError(CustomError):
    def __init__(self, detail: str):
        super().__init__(detail, status_code=status.HTTP_403_FORBIDDEN)


class UnauthorizedError(CustomError):
    def __init__(self, detail: str):
        super().__init__(detail, status_code=status.HTTP_401_UNAUTHORIZED)
