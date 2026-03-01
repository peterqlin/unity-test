import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.core.logging import setup_logging
from app.routers import scene

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Server ready — Unity Scene Generator API")
    yield
    logger.info("Server shutting down")


app = FastAPI(title="Unity Scene Generator API", lifespan=lifespan)
app.include_router(scene.router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    logger.info(f"→ {request.method} {request.url.path}")
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    logger.info(f"← {response.status_code}  ({elapsed * 1000:.0f}ms)")
    return response


@app.get("/")
def hello():
    return {"message": "Hello, world!"}
