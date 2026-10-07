from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.error_codes import ErrorCode
from app.core.logger import log


class UnhandledErrorMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def send_wrapper(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            if response_started:
                raise
            log.exception("unhandled_error", method=scope["method"], path=scope["path"])
            response = JSONResponse(
                status_code=500,
                content={"detail": ErrorCode.INTERNAL_ERROR.message, "error_code": ErrorCode.INTERNAL_ERROR.code},
            )
            await response(scope, receive, send)
