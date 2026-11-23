"""Choosing one DOI per monthly report (weather-data-client.md IV. C. 1.).

A report is one entry of ``GET /api/v1/<kind>/reports`` (fgdc_publish_platform
00_docs/api/public.md 2.): ``month``, ``file``, ``canonical`` and ``versions``
(``version``, ``doi``, ``issued``).
"""

import datetime

from .periods import check_month, to_date


def select(reports, months, *, version="current", as_of=None, today=None):
    """Return (DOIs in month order, months without a report or without a version yet).

    version   "current" (the latest version as of ``as_of``, default today),
              "canonical" (DOIs without a version number), or a dict
              {"YYYY-MM": version number}; months not in the dict are current.
    as_of     a date; only with "current".
    """
    today = today or datetime.date.today()
    if isinstance(version, bool) or isinstance(version, int):
        raise ValueError('version must be "current", "canonical" or a dict {"YYYY-MM": number}; one number for all months is not supported')
    if isinstance(version, dict):
        if as_of is not None:
            raise ValueError("as_of cannot be given with a version for each month")
        chosen = {check_month(k): _number(k, v) for k, v in version.items()}
        outside = sorted(set(chosen) - set(months))
        if outside:
            raise ValueError(f"months outside the range: {', '.join(outside)}")
        cutoff = today
    elif version == "canonical":
        if as_of is not None:
            raise ValueError('as_of cannot be given with version="canonical"')
        chosen, cutoff = None, None
    elif version == "current":
        chosen, cutoff = {}, to_date(as_of, "as_of") if as_of is not None else today
    else:
        raise ValueError(f'unknown version: {version!r} (use "current", "canonical" or a dict)')

    by_month = {}
    for report in reports:
        by_month.setdefault(report["month"], []).append(report)

    dois, missing = [], []
    for month in months:
        found = []
        for report in sorted(by_month.get(month, []), key=lambda r: (r.get("file") or {}).get("name", "")):
            if chosen is None:
                found.append(report["canonical"])
            elif month in chosen:
                found.append(_exact(report, month, chosen[month]))
            else:
                doi = _latest(report, cutoff)
                if doi:
                    found.append(doi)
        if found:
            dois.extend(found)
        else:
            missing.append(month)
    return dois, missing


def latest(report):
    """The newest version of a report (whatever its date)."""
    return max(report["versions"], key=lambda v: v["version"])


def _latest(report, cutoff):
    issued = [v for v in report["versions"] if to_date(v["issued"], "issued") <= cutoff]
    return max(issued, key=lambda v: v["version"])["doi"] if issued else None


def _exact(report, month, number):
    for v in report["versions"]:
        if v["version"] == number:
            return v["doi"]
    have = ", ".join(str(v["version"]) for v in sorted(report["versions"], key=lambda v: v["version"]))
    raise ValueError(f"{month} has no version {number} (versions: {have})")


def _number(month, value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"the version of {month} must be a positive integer")
    return value
