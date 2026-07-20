from app.core import app_config
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import CustomError
from app.routers import animal_router

app = FastAPI(
    title=app_config.APP_NAME,
    debug=app_config.DEBUG,
    root_path="/api",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(CustomError)
async def app_error_handler(request: Request, error: CustomError):
    return JSONResponse(
        status_code=error.status_code,
        content={"detail": error.detail}
    )


app.include_router(animal_router, prefix="/animals", tags=["Animals"])
