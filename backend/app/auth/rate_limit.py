# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 SpyrosDr

"""In-process login brute-force throttling.

Keeps failed-login counters in memory, keyed separately by username and by
client IP. This is deliberately simple -- no Redis, no cross-process
coordination -- which fits this app's single-process dev/small-deployment
target. State resets on process restart and is not shared across multiple
worker processes; a multi-worker production deployment would need a shared
store (e.g. Redis) instead.

Two independent limiters are kept:
  * per-account -- a small number of failures locks out that *username*,
    protecting a single account from credential stuffing.
  * per-IP -- a much larger allowance locks out that *client IP*, catching
    an attacker spraying many different usernames from one address without
    punishing a whole office/NAT for one user mistyping a password.
"""

import threading
import time
from dataclasses import dataclass

from app.config import settings


@dataclass
class _Bucket:
    count: int = 0
    window_start: float = 0.0
    locked_until: float = 0.0


_lock = threading.Lock()
_accounts: dict[str, _Bucket] = {}
_ips: dict[str, _Bucket] = {}


def _seconds_locked(store: dict[str, _Bucket], key: str) -> float:
    with _lock:
        bucket = store.get(key)
        if bucket is None:
            return 0.0
        remaining = bucket.locked_until - time.monotonic()
        return remaining if remaining > 0 else 0.0


def _record_failure(
    store: dict[str, _Bucket], key: str, *, max_attempts: int
) -> None:
    now = time.monotonic()
    with _lock:
        bucket = store.setdefault(key, _Bucket(window_start=now))
        if now - bucket.window_start > settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS:
            bucket.count = 0
            bucket.window_start = now
        bucket.count += 1
        if bucket.count >= max_attempts:
            bucket.locked_until = now + settings.LOGIN_RATE_LIMIT_LOCKOUT_SECONDS


def _record_success(store: dict[str, _Bucket], key: str) -> None:
    with _lock:
        store.pop(key, None)


def seconds_until_unlocked(username: str, ip: str) -> float:
    """The larger of the account's and the IP's remaining lockout, in
    seconds, or 0 if neither is currently locked out."""
    return max(
        _seconds_locked(_accounts, _account_key(username)),
        _seconds_locked(_ips, _ip_key(ip)),
    )


def record_failure(username: str, ip: str) -> None:
    _record_failure(
        _accounts, _account_key(username), max_attempts=settings.LOGIN_RATE_LIMIT_ATTEMPTS
    )
    _record_failure(
        _ips, _ip_key(ip), max_attempts=settings.LOGIN_RATE_LIMIT_IP_ATTEMPTS
    )


def record_success(username: str, ip: str) -> None:
    _record_success(_accounts, _account_key(username))
    _record_success(_ips, _ip_key(ip))


def _account_key(username: str) -> str:
    return username.strip().lower()


def _ip_key(ip: str) -> str:
    return ip
