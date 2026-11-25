"""
scripts/_credentials.py
Shared helper: read admin credentials from the environment or a prompt.

Credentials are never hard-coded. Order of lookup:
  1. ADMIN_USERNAME / ADMIN_PASSWORD environment variables (or .env)
  2. An interactive prompt, if a terminal is attached
"""

import getpass
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:  # python-dotenv is in requirements.txt; this is a fallback
    pass


def get_admin_credentials(interactive: bool | None = None) -> tuple[str, str] | None:
    """Return (username, password), or None if unavailable and not interactive."""
    if interactive is None:
        interactive = sys.stdin.isatty()

    username = os.getenv("ADMIN_USERNAME", "").strip()
    password = os.getenv("ADMIN_PASSWORD", "")

    if not username and interactive:
        username = input("Admin username: ").strip()
    if not password and interactive:
        password = getpass.getpass("Admin password: ")

    if not username or not password:
        return None
    return username, password
