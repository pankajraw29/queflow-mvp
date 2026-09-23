"""QueueFlow API."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .ratelimit import limiter
from .routers import auth, public, queues


def create_app() -> FastAPI:
    app = FastAPI(title="QueueFlow API", version="1.0.0")
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth.router)
    app.include_router(queues.router)
    app.include_router(public.router)

    @app.get("/api/health")
    async def health():
        return {"ok": True}

    return app


app = create_app()
