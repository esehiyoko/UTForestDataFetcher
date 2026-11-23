"""Where the public API is.

The address is not part of the package: it is given at run time, either by
``configure(base_url=...)`` or by the ``UTFOREST_API_BASE_URL`` environment
variable. ``configure`` wins over the environment.
"""

import os

ENV_BASE_URL = "UTFOREST_API_BASE_URL"
ENV_DOI_RESOLVER = "UTFOREST_DOI_RESOLVER"
DEFAULT_DOI_RESOLVER = "https://doi.org"

_settings = {}


def configure(*, base_url=None, doi_resolver=None):
    """Set the public API origin (and, for tests, the DOI resolver) for this process."""
    if base_url is not None:
        _settings["base_url"] = _clean(base_url, "base_url")
    if doi_resolver is not None:
        _settings["doi_resolver"] = _clean(doi_resolver, "doi_resolver")


def reset():
    """Forget what configure() set (the environment applies again)."""
    _settings.clear()


def api_base_url():
    value = _settings.get("base_url") or os.environ.get(ENV_BASE_URL, "").strip()
    if not value:
        raise RuntimeError(
            f"Set {ENV_BASE_URL} or call UTForestDataFetcher.configure(base_url=...) before calling the API"
        )
    return value.rstrip("/")


def doi_resolver():
    value = _settings.get("doi_resolver") or os.environ.get(ENV_DOI_RESOLVER, "").strip()
    return (value or DEFAULT_DOI_RESOLVER).rstrip("/")


def _clean(value, name):
    value = str(value).strip()
    if not value.startswith(("http://", "https://")):
        raise ValueError(f"{name} must start with http:// or https://")
    return value.rstrip("/")
