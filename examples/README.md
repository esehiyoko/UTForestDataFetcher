# Examples

| Notebook | What it shows |
| --- | --- |
| [weather_quickstart.ipynb](weather_quickstart.ipynb) | Catalog, DoiResolver (current, canonical, as_of), FetchData and plots, CheckUpdates, Cite |

The DOIs are mock DOIs (`10.xxxxx/...`) until JaLC is contracted, so `Cite` cannot
resolve them yet.

## The API address

The API address is internal for now and is not written in the notebooks. The
notebook looks for it in this order: the `API_BASE_URL` variable in the notebook
(clear it before sharing), the `UTFOREST_API_BASE_URL` environment variable, the
Google Colab secret `UTFOREST_API_BASE_URL`, and finally a prompt.

The API must be reachable from where the notebook runs: MyBinder and Colab run in
the cloud, so they need an API reachable from the internet. A local API (for
example the development Rails on this machine) works with a local Jupyter or the
local JupyterLite below.

## MyBinder

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/esehiyoko/UTForestDataFetcher/main?labpath=examples%2Fweather_quickstart.ipynb)

MyBinder builds this repository with [binder/requirements.txt](../binder/requirements.txt)
(the package with the `plot` extra). Binder has no secrets, so the notebook asks
for the address.

## Google Colab

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/esehiyoko/UTForestDataFetcher/blob/main/examples/weather_quickstart.ipynb)

The first cell installs the package from this repository. Add the secret
`UTFOREST_API_BASE_URL` (the key icon on the left) and allow the notebook to read it.

## JupyterLite (in the browser, local)

```sh
examples/jupyterlite/build.sh    # builds examples/jupyterlite/_output and serves it on :8000
```

Open `http://localhost:8000/lab/index.html?path=weather_quickstart.ipynb`, set
`API_BASE_URL` in the second code cell, and run all cells. The notebook runs in
Pyodide: the package (a wheel bundled into the site) talks to the API through the
browser, so the API must allow the page's origin with CORS. The development Rails
of fgdc_publish_platform allows `http://localhost:8000` and `http://127.0.0.1:8000`
(`FGDC_API_CORS_ORIGINS` in `compose.development.yaml`).

To have data in the development Rails, register the weather fixtures with
`script/seed-weather-demo` of fgdc_publish_platform.
