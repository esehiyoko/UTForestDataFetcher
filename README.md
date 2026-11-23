# UTForestDataFetcher

Python helper for the weather data API. This repository currently contains an
installable skeleton; API calls are not implemented yet.

## Install from Git

```sh
python -m pip install git+https://github.com/esehiyoko/UTForestDataFetcher.git
```

For local testing:

```sh
python -m pip install -e .
python -c "import UTForestDataFetcher; print(UTForestDataFetcher.Weather)"
```

The test API endpoint is private. Set `UTFOREST_API_BASE_URL` in your local
environment when it becomes necessary; never commit the value. The `.env` files
are ignored by Git. No token or endpoint is required for the import smoke test.

The planned interface is documented in
`fgdc_publish_platform/00_docs/design/weather-data-client.md` in the parent
workspace. Its HTTP API is documented in
`fgdc_publish_platform/00_docs/api/public.md`.

## Development and release

Pull requests to `main` run install, import, configuration, and package build
checks. Tagging a commit as `v*` builds a wheel and source archive and attaches
them to a GitHub Release. This does not publish to PyPI. The package version in
`pyproject.toml` should match the release tag before tagging.
