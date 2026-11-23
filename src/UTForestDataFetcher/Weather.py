"""Weather observation data (気象観測データ).

One CSV per month and observation site, with a ``日付`` column
(fgdc_publish_platform 00_docs/design/weather-data-client.md IV. C.).
The work is done by the shared parts in ``UTForestDataFetcher.core``.
"""

from .core import cite as _cite
from .core.monthly import MonthlyData

_data = MonthlyData("weather", date_column="日付")


def DoiResolver(*, forest, site, range, version="current", as_of=None, media_type="data"):
    """DOIs of the monthly reports of a site in a range of dates (one per month).

    >>> DoiResolver(forest="千葉演習林", site="札郷", range=("2026-01-01", "2026-03-31"))
    """
    return _data.resolve(range=range, version=version, as_of=as_of, media_type=media_type, forest=forest, site=site)


def FetchData(*, dois, filter=None):
    """The data of versioned DOIs as a pandas DataFrame indexed by date."""
    return _data.fetch(dois, filter=filter)


def Cite(*, dois, format="bibtex"):
    """Citations of the DOIs ("bibtex", "ris", "apa" or "csl") as a string."""
    return _cite.cite(dois, format=format)


def CheckUpdates(*, dois):
    """Months whose report has a newer version than the DOI given, as a DataFrame."""
    return _data.check_updates(dois)


def Catalog(*, forest=None, site=None):
    """Forests, sites, variables and periods that can be asked for, as a DataFrame."""
    return _data.catalog(forest=forest, site=site)
