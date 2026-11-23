import datetime
import os
import unittest
import warnings
from unittest.mock import patch

import UTForestDataFetcher
from UTForestDataFetcher import Weather
from UTForestDataFetcher.core import config, versions
from fake_api import P, REPORTS, FakeApi

Q1 = ("2026-01-01", "2026-03-31")
SITE = {"forest": "千葉演習林", "site": "札郷"}


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.api = FakeApi().__enter__()
        UTForestDataFetcher.configure(base_url=self.api.url, doi_resolver=self.api.url + "/doi")

    def tearDown(self):
        config.reset()
        self.api.__exit__(None, None, None)


class ConfigTest(unittest.TestCase):
    def tearDown(self):
        config.reset()

    def test_the_api_address_is_given_at_run_time(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "UTFOREST_API_BASE_URL"):
                config.api_base_url()
        with patch.dict(os.environ, {"UTFOREST_API_BASE_URL": "https://example.invalid/"}):
            self.assertEqual(config.api_base_url(), "https://example.invalid")
            UTForestDataFetcher.configure(base_url="https://other.invalid")
            self.assertEqual(config.api_base_url(), "https://other.invalid", "configure() wins")
        with self.assertRaises(ValueError):
            UTForestDataFetcher.configure(base_url="example.invalid")


class DoiResolverTest(ApiTest):
    def test_current_is_the_latest_version_today(self):
        dois = Weather.DoiResolver(**SITE, range=Q1)
        self.assertEqual(dois, [f"{P}/2026.000001/v2", f"{P}/2026.000002/v3", f"{P}/2026.000003/v1"])
        path, q, _ = self.api.requests[-1]
        self.assertEqual((path, q["from"], q["to"], q["forest"]), ("/api/v1/weather/reports", ["2026-01"], ["2026-03"], ["千葉演習林"]))

    def test_canonical(self):
        self.assertEqual(Weather.DoiResolver(**SITE, range=Q1, version="canonical"),
                         [f"{P}/2026.000001", f"{P}/2026.000002", f"{P}/2026.000003"])

    def test_as_of_skips_months_not_yet_published_with_a_warning(self):
        with self.assertWarnsRegex(UserWarning, "2026-03"):
            dois = Weather.DoiResolver(**SITE, range=Q1, as_of="2026-06-30")
        self.assertEqual(dois, [f"{P}/2026.000001/v1", f"{P}/2026.000002/v2"])

    def test_a_version_for_some_months(self):
        dois = Weather.DoiResolver(**SITE, range=Q1, version={"2026-01": 1, "2026-02": 3})
        self.assertEqual(dois, [f"{P}/2026.000001/v1", f"{P}/2026.000002/v3", f"{P}/2026.000003/v1"])
        with self.assertRaisesRegex(ValueError, "2026-02 has no version 9"):
            Weather.DoiResolver(**SITE, range=Q1, version={"2026-02": 9})
        with self.assertRaisesRegex(ValueError, "outside the range"):
            Weather.DoiResolver(**SITE, range=Q1, version={"2025-12": 1})

    def test_refused_combinations(self):
        for kwargs in ({"version": "canonical", "as_of": "2026-06-30"}, {"version": {"2026-01": 1}, "as_of": "2026-06-30"},
                       {"version": 2}, {"version": "latest"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Weather.DoiResolver(**SITE, range=Q1, **kwargs)

    def test_missing_months_are_skipped_with_a_warning(self):
        with self.assertWarnsRegex(UserWarning, "2026-04"):
            dois = Weather.DoiResolver(**SITE, range=("2026-03-01", "2026-04-30"))
        self.assertEqual(dois, [f"{P}/2026.000003/v1"])

    def test_every_file_when_asked(self):
        dois = Weather.DoiResolver(**SITE, range=("2026-02-01", "2026-02-28"), media_type=None)
        self.assertEqual(dois, [f"{P}/2026.000002/v3", f"{P}/2026.000012/v1"], "CSV and PDF, by file name")

    def test_dates_and_ranges(self):
        dois = Weather.DoiResolver(**SITE, range=(datetime.date(2026, 2, 10), "2026/02/20"))
        self.assertEqual(dois, [f"{P}/2026.000002/v3"])
        with self.assertRaises(ValueError):
            Weather.DoiResolver(**SITE, range=("2026-03-01", "2026-01-01"))


class FetchDataTest(ApiTest):
    def test_the_data_of_the_dois_indexed_by_date(self):
        dois = Weather.DoiResolver(**SITE, range=Q1)
        df = Weather.FetchData(dois=dois)
        self.assertEqual(len(df), 9)
        self.assertEqual(str(df.index[0].date()), "2026-01-01")
        self.assertEqual(df.loc["2026-02-02", "平均気温"], 32.0, "2026-02 is v3")
        self.assertEqual(df.attrs["dois"], dois)
        self.assertEqual(len(df.loc["2026-01-02":"2026-02-02"]), 4)

    def test_filter(self):
        df = Weather.FetchData(dois=[f"{P}/2026.000001/v1"], filter=["降水量", "最高気温"])
        self.assertEqual(list(df.columns), ["降水量", "最高気温"])
        with self.assertRaisesRegex(KeyError, "風速"):
            Weather.FetchData(dois=[f"{P}/2026.000001/v1"], filter=["風速"])

    def test_unversioned_dois_are_refused_before_any_request(self):
        with self.assertRaisesRegex(ValueError, "unversioned DOI is not accepted"):
            Weather.FetchData(dois={f"{P}/2026.000001", f"{P}/2026.000002/v1"})
        self.assertEqual(self.api.requests, [])

    def test_errors_of_the_api(self):
        with self.assertRaisesRegex(ValueError, "CSV ではない"):
            Weather.FetchData(dois=[f"{P}/2026.000012/v1"])
        with self.assertRaisesRegex(LookupError, "登録されていない"):
            Weather.FetchData(dois=[f"{P}/2026.000099/v1"])

    def test_plot_is_pandas(self):
        try:
            import matplotlib
        except ImportError:
            self.skipTest("matplotlib is optional")
        matplotlib.use("Agg")
        ax = Weather.FetchData(dois=[f"{P}/2026.000001/v2"]).plot(y="最高気温")
        self.assertEqual(ax.get_lines()[0].get_ydata().tolist(), [26.0, 27.0, 28.0])


class CheckUpdatesTest(ApiTest):
    def test_months_with_a_newer_version(self):
        df = Weather.CheckUpdates(dois=[f"{P}/2026.000001/v2", f"{P}/2026.000002/v1", f"{P}/2026.000003/v1"])
        self.assertEqual(df.to_dict("records"),
                         [{"month": "2026-02", "doi": f"{P}/2026.000002/v1", "latest": f"{P}/2026.000002/v3", "issued": "2026-08-01"}])
        path, q, _ = self.api.requests[-1]
        self.assertEqual(q["doi[]"], [f"{P}/2026.000001/v2", f"{P}/2026.000002/v1", f"{P}/2026.000003/v1"])

    def test_nothing_new_is_an_empty_frame(self):
        df = Weather.CheckUpdates(dois=[f"{P}/2026.000001/v2"])
        self.assertTrue(df.empty)
        self.assertEqual(list(df.columns), ["month", "doi", "latest", "issued"])

    def test_refusals(self):
        with self.assertRaisesRegex(ValueError, "unversioned"):
            Weather.CheckUpdates(dois=[f"{P}/2026.000001"])
        with self.assertRaisesRegex(LookupError, "2026.000099"):
            Weather.CheckUpdates(dois=[f"{P}/2026.000099/v1"])


class CatalogTest(ApiTest):
    def test_all_and_filtered(self):
        self.assertEqual(len(Weather.Catalog()), 3)
        df = Weather.Catalog(forest="千葉演習林", site="札郷")
        self.assertEqual(list(df.columns), ["forest", "site", "variable", "unit", "from", "to"])
        self.assertEqual(df["variable"].tolist(), ["降水量", "最高気温"])
        self.assertNotIn("forest", self.api.requests[0][1], "absent filters are not sent")


class CiteTest(ApiTest):
    def test_made_from_citeproc_json_when_the_agency_lacks_the_format(self):
        d = f"{P}/2026.000002/v3"
        bib = Weather.Cite(dois=[d])
        self.assertIn("@misc{2026000002v3,", bib)
        self.assertIn("doi = {10.example/2026.000002/v3}", bib)
        self.assertIn("author = {{東京大学演習林}}", bib)
        ris = Weather.Cite(dois=[d], format="ris")
        self.assertTrue(ris.startswith("TY  - DATA\nAU  - 東京大学演習林\n"))
        self.assertIn("ET  - v3", ris)
        apa = Weather.Cite(dois=[d], format="apa")
        self.assertEqual(apa.strip(), "東京大学演習林 (2026). 札郷の気象月報（2026年2月） (Version v3) [Data set]. https://doi.org/10.example/2026.000002/v3")

    def test_the_agency_format_is_used_when_returned(self):
        self.api.server.agency_formats = {"application/x-bibtex"}
        self.assertEqual(Weather.Cite(dois=[f"{P}/2026.000001/v2"]), "@misc{agency, doi = {10.example/2026.000001/v2}}\n")

    def test_refusals(self):
        with self.assertRaisesRegex(ValueError, "mock DOIs"):
            Weather.Cite(dois=["10.xxxxx/2026.000002/v1"])
        with self.assertRaisesRegex(ValueError, "format"):
            Weather.Cite(dois=[f"{P}/2026.000001/v2"], format="mla")


class VersionsTest(unittest.TestCase):
    def test_as_of_uses_the_issued_dates(self):
        months = ["2026-01", "2026-02"]
        dois, missing = versions.select(REPORTS[:2], months, as_of=datetime.date(2026, 5, 1))
        self.assertEqual((dois, missing), ([f"{P}/2026.000001/v1", f"{P}/2026.000002/v2"], []))
        dois, missing = versions.select(REPORTS[:2], months, as_of="2026-03-31")
        self.assertEqual((dois, missing), ([], months))


@unittest.skipUnless(os.environ.get("UTFOREST_API_BASE_URL"), "needs the API address (GitHub secret UTFOREST_API_BASE_URL)")
class LiveApiTest(unittest.TestCase):
    """Runs against the real API only when its address is given (never in the code)."""

    def test_catalog_answers(self):
        df = Weather.Catalog()
        self.assertEqual(list(df.columns)[:6], ["forest", "site", "variable", "unit", "from", "to"])


if __name__ == "__main__":
    unittest.main()
