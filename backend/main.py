"""FastAPI application entrypoint — CORS, rate limiting, error handling, router registration."""

import logging
import os

from sqlalchemy.orm import Session
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from rate_limit import limiter
from dependencies import get_current_user, user_global_roles
from routes import change_requests, clients, dashboard, projects, reference, roles, users
from database import get_db
from models import User
from schemas import MeOut, MeUpdate


load_dotenv()
logger = logging.getLogger(__name__)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app = FastAPI(title="Project Tracker")
app.include_router(projects.router)
app.include_router(dashboard.router)
app.include_router(change_requests.router)
app.include_router(clients.router)
app.include_router(reference.router)
app.include_router(roles.router)
app.include_router(users.router)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/")
def root():
    return {"message": "Project Tracker API is running."}


@app.get("/api/me", response_model=MeOut)
def me(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Front-end gate based on user-roles."""
    return MeOut(
        id=user.id,
        email=user.email,
        name=user.name,
        timezone=user.timezone,
        avatar=user.avatar,
        is_head_pm_override=user.is_head_pm_override,
        roles=sorted(user_global_roles(db, user)),
    )


@app.patch("/api/me", response_model=MeOut)
def update_me(
    payload: MeUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """A user's own preferences. Avatar is a key into a preset set, not an upload."""
    data = payload.model_dump(exclude_unset=True)
    if "avatar" in data:
        user.avatar = data["avatar"]
    db.commit()
    db.refresh(user)
    return MeOut(
        id=user.id,
        email=user.email,
        name=user.name,
        timezone=user.timezone,
        avatar=user.avatar,
        is_head_pm_override=user.is_head_pm_override,
        roles=sorted(user_global_roles(db, user)),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    origin = request.headers.get("origin", "")
    headers = {}
    if origin in allowed_origins:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers=headers,
    )
