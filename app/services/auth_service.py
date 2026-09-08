import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash

load_dotenv()

SECRET = os.getenv("JWT_SECRET", "change-me-in-production")

security = HTTPBearer()

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    password: str,
    hashed_password: str
) -> bool:
    return password_hash.verify(
        password,
        hashed_password
    )


def create_access_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=12),
    }

    return jwt.encode(
        payload,
        SECRET,
        algorithm="HS256"
    )


def require_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET,
            algorithms=["HS256"]
        )

        return payload["sub"]

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )