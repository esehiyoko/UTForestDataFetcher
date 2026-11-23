"""DOIs with a version number (``10.xxxxx/2026.000007/v2``) and without one (canonical)."""

import re

# Same rule as the Rails registration API (fgdc_publish_platform app/models/registration.rb).
VERSIONED = re.compile(r"^(10\.[A-Za-z0-9.]+/[A-Za-z0-9._;()/-]+?)/v([1-9]\d*)$", re.IGNORECASE)
DOI = re.compile(r"^10\.[A-Za-z0-9.]+/\S+$")
MOCK_PREFIX = "10.xxxxx"


def normalize(doi):
    """Strip ``https://doi.org/`` and ``doi:`` and spaces."""
    value = str(doi).strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "doi:"):
        if value.lower().startswith(prefix):
            value = value[len(prefix):]
    if not DOI.match(value):
        raise ValueError(f"not a DOI: {doi!r}")
    return value


def split(doi):
    """(canonical, version) for a versioned DOI, (canonical, None) for an unversioned one."""
    value = normalize(doi)
    m = VERSIONED.match(value)
    return (m.group(1), int(m.group(2))) if m else (value, None)


def is_versioned(doi):
    return split(doi)[1] is not None


def is_mock(doi):
    return normalize(doi).startswith(MOCK_PREFIX + "/")


def require_versioned(dois):
    """The DOIs as a list, refusing unversioned (canonical) ones and empty input."""
    if isinstance(dois, str):
        dois = [dois]
    values = [normalize(d) for d in dois]
    if not values:
        raise ValueError("no DOI is given")
    unversioned = [d for d in values if not is_versioned(d)]
    if unversioned:
        raise ValueError(f"unversioned DOI is not accepted: {', '.join(unversioned)}")
    return list(dict.fromkeys(values))
