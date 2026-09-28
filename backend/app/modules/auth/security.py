import hashlib
import secrets
import time
from collections import OrderedDict
from threading import Lock

from pwdlib import PasswordHash

from app.core.errors import fail

password_hasher = PasswordHash.recommended()
dummy_hash = password_hasher.hash(secrets.token_urlsafe(32))


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def csrf_token(token: str) -> str:
    return hashlib.sha256(("medical-ba-csrf:" + token).encode()).hexdigest()


class LoginLimiter:
    """Bounded, single-process development limiter. No raw identifiers retained."""

    def __init__(self):
        self.buckets = OrderedDict()
        self.lock = Lock()

    def check(self, key: str, maximum: int, window: int):
        stamp = time.monotonic()
        with self.lock:
            hits = [t for t in self.buckets.pop(key, []) if t > stamp - window]
            if len(hits) >= maximum:
                self.buckets[key] = hits
                fail(429, "RATE_LIMITED", "Too many login attempts; try again later.")
            self.buckets[key] = hits + [stamp]
            while len(self.buckets) > 10000:
                self.buckets.popitem(last=False)


login_limiter = LoginLimiter()
