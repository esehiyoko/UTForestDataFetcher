"""Data published as one file per month and place (weather now; others can reuse it).

A kind of data is set up with the name used in the API paths
(``/api/v1/<kind>/...``), the date column of its CSV, and which files hold the
data (CSV). Everything else (choosing versions, fetching, checking for updates,
the catalog) is the same for every kind.
"""

import io
import warnings

from . import doi as doi_
from . import http
from .periods import months as months_in
from .versions import latest, select


class MonthlyData:
    def __init__(self, kind, *, date_column, data_media_type="text/csv"):
        self.kind, self.date_column, self.data_media_type = kind, date_column, data_media_type

    def path(self, name):
        return f"/api/v1/{self.kind}/{name}"

    # ---- catalog -------------------------------------------------------------

    def catalog(self, **filters):
        """What can be asked for (places, variables, periods) as a DataFrame."""
        import pandas as pd

        rows = http.get_json(self.path("catalog"), filters)
        return pd.DataFrame(rows, columns=_columns(rows, ["forest", "site", "variable", "unit", "from", "to"]))

    # ---- DOIs ----------------------------------------------------------------

    def reports(self, *, months=None, dois=None, **filters):
        """The reports of the API, either for months and places or for DOIs."""
        if dois is not None:
            params = {"doi[]": [doi_.normalize(d) for d in dois]}
        else:
            params = dict(filters, **{"from": months[0], "to": months[-1]})
        return http.get_json(self.path("reports"), params)

    def resolve(self, *, range, version="current", as_of=None, media_type="data", **filters):
        """One DOI per month (and file) in the range, in month order.

        media_type  "data" (default) keeps the files FetchData can read (CSV);
                    None keeps every file (for example the PDF to cite).
        Months without a report, or without a version yet as of ``as_of``,
        are skipped with a warning.
        """
        months = months_in(range)
        reports = self.reports(months=months, **filters)
        wanted = self.data_media_type if media_type == "data" else media_type
        if wanted is not None:
            reports = [r for r in reports if (r.get("file") or {}).get("media_type") == wanted]
        dois, missing = select(reports, months, version=version, as_of=as_of)
        if missing:
            when = f" as of {as_of}" if as_of is not None else ""
            warnings.warn(f"no report{when} for: {', '.join(missing)}", stacklevel=3)
        return dois

    # ---- data ----------------------------------------------------------------

    def fetch(self, dois, filter=None):
        """The data of versioned DOIs as one DataFrame indexed by date.

        The DOIs used are kept in ``df.attrs["dois"]``.
        """
        import pandas as pd

        dois = doi_.require_versioned(dois)
        frames = []
        for d in dois:
            text = http.get_text(self.path("data"), {"doi": d})
            frame = pd.read_csv(io.StringIO(text))
            if self.date_column not in frame.columns:
                raise ValueError(f"{d}: the CSV has no {self.date_column} column")
            frames.append(frame)
        df = pd.concat(frames, ignore_index=True)
        df[self.date_column] = pd.to_datetime(df[self.date_column])
        df = df.set_index(self.date_column).sort_index()
        if filter is not None:
            wanted = [filter] if isinstance(filter, str) else list(filter)
            unknown = [c for c in wanted if c not in df.columns]
            if unknown:
                raise KeyError(f"no such column: {', '.join(unknown)} (columns: {', '.join(df.columns)})")
            df = df[wanted]
        df.attrs["dois"] = dois
        return df

    # ---- updates -------------------------------------------------------------

    def check_updates(self, dois):
        """Months whose report has a newer version than the DOI given."""
        import pandas as pd

        dois = doi_.require_versioned(dois)
        reports = self.reports(dois=dois)
        rows = []
        for d in dois:
            canonical, number = doi_.split(d)
            report = next((r for r in reports if r["canonical"] == canonical), None)
            if report is None:
                raise LookupError(f"not found: {d}")
            newest = latest(report)
            if newest["version"] > number:
                rows.append({"month": report["month"], "doi": d, "latest": newest["doi"], "issued": newest["issued"]})
        return pd.DataFrame(rows, columns=["month", "doi", "latest", "issued"])


def _columns(rows, preferred):
    extra = [k for row in rows for k in row if k not in preferred]
    return preferred + list(dict.fromkeys(extra))
