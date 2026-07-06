from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .db import close_db, init_db
from .routers import checkout, orders, products, streams


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
    yield
    await close_db()


app = FastAPI(title="Live Commerce API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(streams.router)
app.include_router(products.router)
app.include_router(checkout.router)
app.include_router(orders.router)


@app.get("/api/health")
async def health():
    return {"ok": True, "cfMock": settings.cf_mock, "authMock": settings.auth_mock}


# Imágenes de producto en dev local (prod: R2 + CDN)
Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.uploads_dir), name="uploads")
