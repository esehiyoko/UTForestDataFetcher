# UTForestDataFetcher

Python helper for the weather data API. This repository currently contains an
installable skeleton; API calls are not implemented yet.

## Install from Git

After the repository is published, replace `OWNER` in the command below:

```sh
python -m pip install git+https://github.com/OWNER/FGDCDataClientPy.git
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
