"""Client for the LAION-fMRI stimulus access service.

The access service is a small FastAPI app at
``https://laion-fmri.hebartlab.com`` that gates the copyrighted stimulus
images behind a Terms-of-Use submission. After acceptance, it mints
short-lived presigned S3 URLs.

This module is the loader-side client:

* ``submit_access_request`` — POST the form (called once per machine).
* ``refresh_urls`` — re-mint URLs for a cached ``request_id``.
* ``download_file`` — stream a presigned URL to disk with sha256 verification
  and ``Range``-based resume on flaky networks.
* ``save_request_id`` / ``load_request_id`` / ``clear_request_id`` —
  ``~/.cache/laion-fmri/auth.json`` plus an env-var override for headless use.

The raw ``request_id`` lives only here on disk (mode 0600 where possible)
and as the ``LAION_FMRI_REQUEST_ID`` env var. The server only stores the
HMAC hash of it.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from laion_fmri._constants import ACCESS_SERVICE_URL


# ── Errors ──────────────────────────────────────────────────────

class AccessServiceError(RuntimeError):
    """Base class for stimulus access errors."""


class TermsOutdatedError(AccessServiceError):
    """The cached request_id needs to re-accept an updated ToU."""

    def __init__(self, accept_url: str, terms_version: str):
        super().__init__(
            f"The LAION-fMRI Terms of Use have been updated to "
            f"v{terms_version}. Visit {accept_url} to accept, then "
            f"re-run."
        )
        self.accept_url = accept_url
        self.terms_version = terms_version


class AccessRevokedError(AccessServiceError):
    """The cached request_id has been revoked by an admin."""


class AccessNotFoundError(AccessServiceError):
    """The server doesn't know this request_id (likely a typo or stale)."""


# ── Local cache (auth.json) ─────────────────────────────────────

def auth_dir() -> Path:
    """Cache directory for stimulus auth state."""
    return Path.home() / ".cache" / "laion-fmri"


def auth_path() -> Path:
    """Path to the local request_id cache."""
    return auth_dir() / "auth.json"


def load_request_id() -> Optional[str]:
    """Return the raw request_id from env var or auth.json, else None.

    ``LAION_FMRI_REQUEST_ID`` takes precedence over the on-disk cache,
    which lets cluster jobs supply the id without copying the cache file.
    """
    env = os.environ.get("LAION_FMRI_REQUEST_ID")
    if env:
        return env.strip()
    p = auth_path()
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    rid = data.get("request_id")
    return rid if isinstance(rid, str) and rid else None


def save_request_id(
    raw_request_id: str,
    email: str | None = None,
    server_url: str = ACCESS_SERVICE_URL,
) -> Path:
    """Persist the raw request_id to ``auth.json`` (mode 0600 on POSIX)."""
    d = auth_dir()
    d.mkdir(parents=True, exist_ok=True)
    p = auth_path()
    payload = {
        "server_url": server_url,
        "request_id": raw_request_id,
        "email": email,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    p.write_text(json.dumps(payload, indent=2))
    try:
        p.chmod(0o600)
    except OSError:
        # Windows or other POSIX-mode-unaware fs; rely on home-dir ACLs.
        pass
    return p


def clear_request_id() -> bool:
    """Remove the cached request_id. Returns True if a file was deleted."""
    p = auth_path()
    if p.exists():
        p.unlink()
        return True
    return False


# ── HTTP plumbing ──────────────────────────────────────────────

def _request_json(url: str, payload: Optional[dict] = None, method: str = "GET",
                  timeout: float = 30.0) -> dict:
    """Send a JSON request, return parsed JSON, translate errors to our exceptions."""
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"detail": raw}
        detail = data.get("detail", data)
        if e.code == 403 and isinstance(detail, dict) and detail.get("error") == "terms_outdated":
            raise TermsOutdatedError(
                accept_url=detail.get("accept_url", f"{ACCESS_SERVICE_URL}/terms/accept"),
                terms_version=detail.get("current_terms_version", "?"),
            ) from None
        if e.code == 403 and "revoked" in str(detail).lower():
            raise AccessRevokedError(str(detail)) from None
        if e.code == 404:
            raise AccessNotFoundError(str(detail)) from None
        if e.code == 429:
            raise AccessServiceError(f"Rate limit exceeded: {detail}") from None
        raise AccessServiceError(f"HTTP {e.code}: {detail}") from None
    except urllib.error.URLError as e:
        raise AccessServiceError(
            f"Could not reach the access service at {url}: {e.reason}"
        ) from None


def fetch_manifest(server_url: str = ACCESS_SERVICE_URL) -> dict:
    """GET /api/v1/manifest. Returns the public manifest."""
    return _request_json(f"{server_url}/api/v1/manifest", method="GET")


def current_terms_version(server_url: str = ACCESS_SERVICE_URL) -> str:
    """Fetch the current ToU version the server expects in submissions."""
    return fetch_manifest(server_url)["current_terms_version"]


def submit_access_request(form_data: dict, server_url: str = ACCESS_SERVICE_URL) -> dict:
    """POST /api/v1/access/request. Returns ``{request_id, expires_at, files}``."""
    return _request_json(f"{server_url}/api/v1/access/request", form_data, method="POST")


def refresh_urls(
    request_id: str,
    dataset_version: str = "v1",
    server_url: str = ACCESS_SERVICE_URL,
) -> dict:
    """POST /api/v1/refresh. Returns ``{expires_at, files}``."""
    return _request_json(
        f"{server_url}/api/v1/refresh",
        {"request_id": request_id, "dataset_version": dataset_version},
        method="POST",
    )


# ── Streamed download with sha256 verification + Range resume ─

_CHUNK = 1024 * 1024  # 1 MB


def _sha256_of(path: "Path") -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def _format_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def download_file(
    url: str,
    dest: Path,
    expected_size: int,
    expected_sha256: str,
    *,
    show_progress: bool = True,
) -> None:
    """Stream ``url`` to ``dest`` with sha256 verification.

    Idempotent:

    * If ``dest`` already exists with the right size and sha256, returns
      immediately (no network call).
    * If a partial ``.part`` file is left from a previous interrupted run,
      a ``Range`` request resumes from where it left off.

    Raises :class:`AccessServiceError` on sha256 mismatch (and removes
    the bad ``.part``).
    """
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists() and dest.stat().st_size == expected_size:
        if _sha256_of(dest) == expected_sha256:
            if show_progress:
                print(f"  {dest.name}: cached, sha256 ok")
            return
        # Wrong sha256: drop and refetch.
        dest.unlink()

    tmp = dest.with_suffix(dest.suffix + ".part")
    start = tmp.stat().st_size if tmp.exists() else 0
    if start >= expected_size:
        # Partial is somehow too big — start over.
        tmp.unlink()
        start = 0

    headers: dict[str, str] = {}
    mode = "wb"
    if start > 0:
        headers["Range"] = f"bytes={start}-"
        mode = "ab"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp, tmp.open(mode) as f:
            done = start
            last_print = time.monotonic()
            while True:
                chunk = resp.read(_CHUNK)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if show_progress and time.monotonic() - last_print > 0.25:
                    pct = (done / expected_size) * 100 if expected_size else 100.0
                    sys.stderr.write(
                        f"\r  {dest.name}: {_format_bytes(done)} / "
                        f"{_format_bytes(expected_size)} ({pct:.1f}%)   "
                    )
                    sys.stderr.flush()
                    last_print = time.monotonic()
    except urllib.error.HTTPError as e:
        raise AccessServiceError(
            f"Download of {dest.name} failed: HTTP {e.code} "
            f"(the presigned URL may have expired; ask for a fresh one)"
        ) from None
    except urllib.error.URLError as e:
        raise AccessServiceError(
            f"Download of {dest.name} failed: {e.reason}"
        ) from None

    if show_progress:
        sys.stderr.write("\n")

    got = _sha256_of(tmp)
    if got != expected_sha256:
        tmp.unlink()
        raise AccessServiceError(
            f"sha256 mismatch for {dest.name}: "
            f"expected {expected_sha256[:16]}…, got {got[:16]}…"
        )
    tmp.replace(dest)
    if show_progress:
        print(f"  {dest.name}: sha256 verified")
