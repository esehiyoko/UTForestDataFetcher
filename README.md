# UTForestDataFetcher

Python helper for the UTokyo Forest data published through the public site
(fgdc_publish_platform). Weather observation data is the first kind of data;
the parts shared by every kind live in `UTForestDataFetcher.core`.

The design is `fgdc_publish_platform/00_docs/design/weather-data-client.md`
(IV. C.) and the HTTP API it calls is `fgdc_publish_platform/00_docs/api/public.md`.

## Install

```sh
python -m pip install "UTForestDataFetcher[plot] @ git+https://github.com/esehiyoko/UTForestDataFetcher.git"
```

`pandas` is required; `matplotlib` (the `plot` extra) is only for `DataFrame.plot`.

## The API address

The API address is internal for now, so it is not in the package. Give it at
run time, either in the environment or in code:

```sh
export UTFOREST_API_BASE_URL=...   # or put it in .env (ignored by Git)
```

```python
import UTForestDataFetcher
UTForestDataFetcher.configure(base_url="https://...")
```

In GitHub Actions it comes from the repository secret `UTFOREST_API_BASE_URL`.
CI fails if a URL other than doi.org or a placeholder appears in the code.

## Weather

```python
from UTForestDataFetcher import Weather

Weather.Catalog(forest="千葉演習林", site="札郷")            # places, variables, periods

dois = Weather.DoiResolver(forest="千葉演習林", site="札郷",
                           range=("2026-01-01", "2026-03-31"))  # latest version of each month
Weather.DoiResolver(..., version="canonical")                 # DOIs without a version number
Weather.DoiResolver(..., as_of="2026-06-30")                  # versions published by that date
Weather.DoiResolver(..., version={"2026-01": 1, "2026-02": 3})

df = Weather.FetchData(dois=dois, filter=["降水量", "最高気温"])  # DataFrame indexed by date
df.loc["2026-01-15":"2026-02-10"]
df.plot(y="最高気温")

Weather.Cite(dois=dois, format="bibtex")   # "bibtex", "ris", "apa" or "csl"
Weather.CheckUpdates(dois=dois)            # months with a newer version
```

- `DoiResolver` returns one DOI per month in month order. Months without a
  report (or without a version yet as of `as_of`) are skipped with a warning.
  By default it keeps the CSV files that `FetchData` reads; `media_type=None`
  keeps every file (the PDF is the original, which is what to cite).
- `FetchData` and `CheckUpdates` accept versioned DOIs only. The DOIs used are
  kept in `df.attrs["dois"]`.
- `Cite` asks doi.org for the format; if the registration agency does not
  return it, the citation is made from its Citeproc JSON. Mock DOIs
  (`10.xxxxx/...`) are not registered at doi.org and cannot be cited.

## Layout

| Module | Role |
| --- | --- |
| `core/config.py` | API address (run time only) |
| `core/http.py` | GET requests; 400 → `ValueError`, 404 → `LookupError`, others → `ApiError` |
| `core/doi.py` | versioned and unversioned DOIs |
| `core/periods.py` | months in a range of dates |
| `core/versions.py` | choosing one DOI per month (current, canonical, as_of, by month) |
| `core/monthly.py` | data published as one file per month: catalog, resolve, fetch, check updates |
| `core/cite.py` | citations through doi.org |
| `Weather.py` | weather: the API name `weather` and the date column `日付` |

A new kind of monthly data is another `MonthlyData("<kind>", date_column=...)`
and a small module like `Weather.py`.

## Development and release

```sh
python -m venv .venv && .venv/bin/pip install -e ".[plot]"
.venv/bin/python -m unittest discover -s tests -v
```

The tests run against a fake API (`tests/fake_api.py`) and need no address.
Pull requests to `main` run the tests on Python 3.10 to 3.13 and build the
package. Tagging a commit as `v*` builds a wheel and source archive and attaches
them to a GitHub Release. This does not publish to PyPI. The package version is
`__version__` in `src/UTForestDataFetcher/__init__.py`.
