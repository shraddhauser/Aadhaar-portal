"""
backend/rate_limit.py
Per-client-IP rate limits (slowapi, in-memory storage).

Limits use slowapi's rate syntax ("5/minute") and can be changed with
LOGIN_RATE_LIMIT and CHAT_RATE_LIMIT. Storage is per process: with several
workers or instances each keeps its own counters.

Behind a reverse proxy (e.g. Render) start uvicorn with --proxy-headers so the
client IP comes from X-Forwarded-For instead of the proxy's address.
"""

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

LOGIN_RATE_LIMIT = os.getenv("LOGIN_RATE_LIMIT", "5/minute")
CHAT_RATE_LIMIT = os.getenv("CHAT_RATE_LIMIT", "10/minute")

limiter = Limiter(key_func=get_remote_address)
