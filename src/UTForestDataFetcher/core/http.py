"""GET requests to the public API (standard library only)."""

import json
import urllib.error
import urllib.parse
import urllib.request

from . import config

TIMEOUT = 30


class ApiError(RuntimeError):
    """The API answered with an error that is not the caller's fault (5xx, bad JSON, network)."""


def _user_agent():
    from .. import __version__

    return f"UTForestDataFetcher/{__version__}"


def url(path, params=None, base=None):
    """The URL of an API path. List values are repeated (``doi[]=a&doi[]=b``)."""
    query = urllib.parse.urlencode(
        [(k, v) for k, v in (params or {}).items() if v is not None], doseq=True
    )
    return (base or config.api_base_url()) + path + (f"?{query}" if query else "")


def get(target, accept="application/json"):
    """GET a URL and return (body bytes, content type). Maps 400 to ValueError and 404 to LookupError."""
    request = urllib.request.Request(target, headers={"Accept": accept, "User-Agent": _user_agent()})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.read(), response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as error:
        message = _message(error)
        if error.code == 400:
            raise ValueError(message) from None
        if error.code == 404:
            raise LookupError(message) from None
        raise ApiError(f"HTTP {error.code}: {message}") from None
    except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
        raise ApiError(f"cannot reach the API: {error}") from None


def get_json(path, params=None):
    body, _ = get(url(path, params))
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ApiError(f"the API did not return JSON for {path}") from None


def get_text(path, params=None, accept="text/csv"):
    body, _ = get(url(path, params), accept=accept)
    return body.decode("utf-8")


def _message(error):
    try:
        text = error.read().decode("utf-8", "replace")
    except Exception:
        return error.reason or ""
    try:
        data = json.loads(text)
        return data.get("message") or data.get("error") or text
    except (json.JSONDecodeError, AttributeError):
        return text[:300] or str(error.reason or "")
