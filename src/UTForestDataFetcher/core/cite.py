"""Citations through doi.org content negotiation (weather-data-client.md IV. C. 4., IV. D. 3.).

doi.org passes the request to the registration agency (JaLC). If the agency
does not return the format asked for, the citation is made here from its
Citeproc JSON.
"""

import json
import re

from . import config
from . import doi as doi_
from . import http

ACCEPT = {
    "bibtex": "application/x-bibtex",
    "ris": "application/x-research-info-systems",
    "apa": "text/x-bibliography; style=apa",
    "csl": "application/vnd.citationstyles.csl+json",
}
CSL = ACCEPT["csl"]


def cite(dois, format="bibtex"):
    """The citations of the DOIs as one string, in the order given."""
    if format not in ACCEPT:
        raise ValueError(f"format must be one of {', '.join(ACCEPT)}")
    if isinstance(dois, str):
        dois = [dois]
    values = list(dict.fromkeys(doi_.normalize(d) for d in dois))
    if not values:
        raise ValueError("no DOI is given")
    mock = [d for d in values if doi_.is_mock(d)]
    if mock:
        raise ValueError(f"mock DOIs are not registered at doi.org and cannot be cited: {', '.join(mock)}")
    items = [_one(d, format) for d in values]
    if format == "csl":
        return json.dumps(items, ensure_ascii=False, indent=2)
    return ("\n" if format == "ris" else "\n\n").join(s.strip() for s in items) + "\n"


def _one(doi, format):
    url = f"{config.doi_resolver()}/{doi}"
    if format != "csl":
        try:
            body, content_type = http.get(url, accept=ACCEPT[format])
            if _matches(format, content_type):
                return body.decode("utf-8")
        except http.ApiError:
            pass
    body, content_type = http.get(url, accept=CSL)
    try:
        item = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise http.ApiError(f"{doi}: the resolver returned neither {format} nor Citeproc JSON") from None
    return item if format == "csl" else FORMATTERS[format](item, doi)


def _matches(format, content_type):
    kind = content_type.split(";")[0].strip().lower()
    return kind == ACCEPT[format].split(";")[0] or (format == "apa" and kind == "text/plain")


# ---- formatting Citeproc JSON (CSL-JSON) ----------------------------------------

def _names(item):
    out = []
    for a in item.get("author") or []:
        if a.get("literal"):
            out.append((a["literal"], None))
        else:
            out.append((a.get("family", ""), a.get("given")))
    return out


def _year(item):
    for key in ("issued", "published", "created"):
        parts = (item.get(key) or {}).get("date-parts") or [[]]
        if parts and parts[0]:
            return str(parts[0][0])
    return None


def _first(value):
    return value[0] if isinstance(value, list) else value


def bibtex(item, doi):
    names = " and ".join(f"{f}, {g}" if g else f"{{{f}}}" for f, g in _names(item))
    year = _year(item)
    key = re.sub(r"[^A-Za-z0-9]", "", doi.split("/", 1)[1])
    fields = [("author", names), ("title", _first(item.get("title"))), ("publisher", _first(item.get("publisher"))),
              ("year", year), ("version", item.get("version")), ("doi", doi), ("url", f"https://doi.org/{doi}")]
    body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields if v)
    return f"@misc{{{key},\n{body}\n}}"


def ris(item, doi):
    lines = ["TY  - DATA"]
    lines += [f"AU  - {f}, {g}" if g else f"AU  - {f}" for f, g in _names(item)]
    for tag, value in (("TI", _first(item.get("title"))), ("PY", _year(item)), ("PB", _first(item.get("publisher"))),
                       ("ET", item.get("version")), ("DO", doi), ("UR", f"https://doi.org/{doi}")):
        if value:
            lines.append(f"{tag}  - {value}")
    lines.append("ER  - ")
    return "\n".join(lines)


def apa(item, doi):
    names = [f"{f}, {g[0]}." if g else f for f, g in _names(item)]
    who = names[0] if len(names) == 1 else ", ".join(names[:-1]) + (", & " + names[-1] if names else "")
    title = _first(item.get("title")) or doi
    version = f" (Version {item['version']})" if item.get("version") else ""
    publisher = _first(item.get("publisher"))
    parts = [f"{who}" if who else "", f"({_year(item) or 'n.d.'}).", f"{title}{version} [Data set].",
             f"{publisher}." if publisher and publisher != who else "", f"https://doi.org/{doi}"]
    return " ".join(p for p in parts if p)


FORMATTERS = {"bibtex": bibtex, "ris": ris, "apa": apa}
