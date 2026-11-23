"""The browser path (JupyterLite / Pyodide) with a fake js.XMLHttpRequest."""

import sys
import types
import unittest
from unittest.mock import patch

from UTForestDataFetcher.core import http


class FakeXhr:
    answers = {}
    sent = []

    @classmethod
    def new(cls):
        return cls()

    def open(self, method, url, is_async):
        self.method, self.url, self.is_async, self.headers = method, url, is_async, {}

    def setRequestHeader(self, k, v):
        self.headers[k] = v

    def send(self):
        FakeXhr.sent.append(self)
        self.status, self.responseText, self.content_type = FakeXhr.answers[self.url]

    def getResponseHeader(self, name):
        return self.content_type if name == "Content-Type" else None


class BrowserTest(unittest.TestCase):
    def setUp(self):
        FakeXhr.sent = []
        self.js = types.ModuleType("js")
        self.js.XMLHttpRequest = FakeXhr
        patches = [patch.dict(sys.modules, {"js": self.js}), patch.object(sys, "platform", "emscripten")]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def test_a_synchronous_get_with_the_accept_header(self):
        FakeXhr.answers = {"https://api.example.invalid/x": (200, "日付\n", "text/csv")}
        self.assertEqual(http.get("https://api.example.invalid/x", accept="text/csv"), ("日付\n".encode(), "text/csv"))
        xhr = FakeXhr.sent[0]
        self.assertEqual((xhr.method, xhr.is_async, xhr.headers), ("GET", False, {"Accept": "text/csv"}))

    def test_errors_map_like_urllib(self):
        FakeXhr.answers = {"u400": (400, '{"message": "版番号付きの DOI"}', "application/json"),
                           "u404": (404, '{"message": "登録されていない"}', "application/json"),
                           "u500": (500, "boom", "text/plain"), "u0": (0, "", None)}
        with self.assertRaisesRegex(ValueError, "版番号付き"):
            http.get("u400")
        with self.assertRaisesRegex(LookupError, "登録されていない"):
            http.get("u404")
        with self.assertRaisesRegex(http.ApiError, "HTTP 500"):
            http.get("u500")
        with self.assertRaisesRegex(http.ApiError, "CORS"):
            http.get("u0")


if __name__ == "__main__":
    unittest.main()
