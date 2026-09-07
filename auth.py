"""Verifies Clerk session tokens and extracts the signed-in user's identity."""

import os

from clerk_backend_api import AuthenticateRequestOptions, Clerk
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

sdk = Clerk(bearer_auth=os.getenv("CLERK_SECRET_KEY"))


def authenticate(request):
    try:
        authorized_parties = os.getenv(
            "CLERK_AUTHORIZED_PARTIES", "http://localhost:5173"
        ).split(",")
        jwt_key = os.getenv("JWT_KEY", "").replace("\\n", "\n")

        request_state = sdk.authenticate_request(
            request,
            AuthenticateRequestOptions(
                authorized_parties=authorized_parties,
                jwt_key=jwt_key,
            ),
        )
        if not request_state.is_signed_in:
            raise HTTPException(status_code=401, detail="Unauthorised")
        return {
            "clerk_user_id": request_state.payload.get("sub"),
            "email": (request_state.payload.get("email") or "").lower().strip(),
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorised")
