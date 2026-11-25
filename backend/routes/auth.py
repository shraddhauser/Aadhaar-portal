"""
backend/routes/auth.py
Admin authentication endpoints — login, token verification.
JWT_SECRET_KEY must be set via environment variable in production.
"""

import logging
import os
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.models import AdminUser

router = APIRouter()
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------
# Security config
# -----------------------------------------------------------------
def _load_secret_key() -> str:
    """Return the JWT signing key from JWT_SECRET_KEY.

    In production (ENV=production) a missing key is a startup error. In any
    other environment a random key is generated for this process, so tokens
    stop working whenever the server restarts.
    """
    key = os.getenv("JWT_SECRET_KEY", "").strip()
    if key:
        return key
    if os.getenv("ENV", "development").strip().lower() == "production":
        raise RuntimeError(
            "JWT_SECRET_KEY must be set when ENV=production. "
            "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
        )
    logger.warning(
        "JWT_SECRET_KEY is not set; using a random key for this process. "
        "Logins will not survive a restart. Set JWT_SECRET_KEY in .env."
    )
    return secrets.token_urlsafe(64)


SECRET_KEY      = _load_secret_key()
ALGORITHM       = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480   # 8-hour session

pwd_context    = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")
oauth2_scheme  = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ----- Pydantic schemas -----

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    full_name: str


class TokenData(BaseModel):
    username: str | None = None


# ----- Helpers -----

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire    = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Dependency: decode JWT and return the current admin user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    admin = db.query(AdminUser).filter(AdminUser.username == username).first()
    if admin is None:
        raise credentials_exception
    return admin


# ----- Endpoints -----

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate admin and return a JWT access token."""
    admin = db.query(AdminUser).filter(AdminUser.username == form_data.username).first()
    if not admin or not verify_password(form_data.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Update last login timestamp
    admin.last_login = datetime.utcnow()
    db.commit()

    access_token = create_access_token(
        data={"sub": admin.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": admin.role,
        "full_name": admin.full_name or admin.username,
    }


def require_admin(current_admin: AdminUser = Depends(get_current_admin)) -> AdminUser:
    """Dependency: allow only users with the SuperAdmin role."""
    if current_admin.role != "SuperAdmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return current_admin


@router.get("/me")
def me(current_admin: AdminUser = Depends(get_current_admin)):
    """Return the logged-in admin's profile."""
    return {
        "username":  current_admin.username,
        "full_name": current_admin.full_name,
        "role":      current_admin.role,
    }
