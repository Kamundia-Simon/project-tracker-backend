"""Verifies Clerk session tokens and extracts the signed-in user's identity."""

import logging
import os

from clerk_backend_api import AuthenticateRequestOptions, Clerk
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()
logger = logging.getLogger(__name__)

sdk = Clerk(bearer_auth=os.getenv("CLERK_SECRET_KEY"))

ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
DEV_AUTH_EMAIL = os.getenv("DEV_AUTH_EMAIL")


def authenticate(request):
    # Development-only bypass: skips Clerk entirely so /docs can be tested without fighting 60-second token expiry.
    if ENVIRONMENT == "development" and DEV_AUTH_EMAIL:
        logger.warning("DEV AUTH BYPASS ACTIVE — authenticating as %s", DEV_AUTH_EMAIL)
        return {
            "clerk_user_id": f"dev_{DEV_AUTH_EMAIL}",
            "email": DEV_AUTH_EMAIL.lower().strip(),
        }

    authorized_parties = os.getenv(
        "CLERK_AUTHORIZED_PARTIES", "http://localhost:5173"
    ).split(",")
    jwt_key = os.getenv("JWT_KEY", "").replace("\\n", "\n") or None

    try:
        request_state = sdk.authenticate_request(
            request,
            AuthenticateRequestOptions(
                authorized_parties=authorized_parties,
                jwt_key=jwt_key,
            ),
        )
    except Exception:
        logger.exception("Clerk token verification raised")
        raise HTTPException(status_code=401, detail="Token verification failed")

    if not request_state.is_signed_in:
        raise HTTPException(
            status_code=401,
            detail=request_state.message or "Not signed in",
        )

    return {
        "clerk_user_id": request_state.payload.get("sub"),
        "email": (request_state.payload.get("email") or "").lower().strip(),
    }
