"""Weather client API skeleton.

The public functions will follow the weather data client design document.
"""

import os


def api_base_url():
    """Return the configured public API origin without exposing a test endpoint."""
    value = os.environ.get("UTFOREST_API_BASE_URL", "").strip()
    if not value:
        raise RuntimeError("Set UTFOREST_API_BASE_URL before calling the weather API")
    return value.rstrip("/")


def DoiResolver(*, forest, site, range, version="current", as_of=None):
    raise NotImplementedError("DoiResolver is not implemented yet")


def FetchData(*, dois, filter=None):
    raise NotImplementedError("FetchData is not implemented yet")


def Cite(*, dois, format="bibtex"):
    raise NotImplementedError("Cite is not implemented yet")


def CheckUpdates(*, dois):
    raise NotImplementedError("CheckUpdates is not implemented yet")


def Catalog(*, forest=None, site=None):
    raise NotImplementedError("Catalog is not implemented yet")
