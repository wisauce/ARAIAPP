from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from mimetypes import guess_type

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api import router
from app.config import get_settings
from app.errors import AppError, install_error_handlers
from app.storage import LocalDiskStorage, get_storage


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await get_storage().ensure_bucket()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        debug=settings.debug,
        lifespan=lifespan,
    )
    install_error_handlers(app)
    app.include_router(router)

    @app.get("/health", include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/media/{object_key:path}", include_in_schema=False)
    async def media(object_key: str) -> FileResponse:
        storage = get_storage()
        if not isinstance(storage, LocalDiskStorage):
            raise AppError(404, "NOT_FOUND", "Media is not served by this API.")
        path = storage._path_for(object_key)
        if not path.is_file():
            raise AppError(404, "NOT_FOUND", "File not found.")
        media_type = guess_type(path.name)[0] or "application/octet-stream"
        return FileResponse(path, media_type=media_type)

    return app


app = create_app()
