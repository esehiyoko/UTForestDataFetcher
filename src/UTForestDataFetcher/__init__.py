"""Client helpers for UTokyo Forest data.

The API address is given at run time::

    import UTForestDataFetcher
    UTForestDataFetcher.configure(base_url="https://...")   # or UTFOREST_API_BASE_URL
    dois = UTForestDataFetcher.Weather.DoiResolver(forest=..., site=..., range=(FROM, TO))
"""

__version__ = "0.1.0.dev0"

from . import Weather  # noqa: E402
from .core.config import configure  # noqa: E402

__all__ = ["Weather", "configure", "__version__"]
