"""A fake public API (fgdc_publish_platform 00_docs/api/public.md) and a fake doi.org, on 127.0.0.1."""

import json
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

P = "10.example"


def csv(month, days=3, start=10.0):
    rows = ["日付,平均気温,最高気温,降水量"]
    for d in range(1, days + 1):
        rows.append(f"{month}-{d:02d},{start + d},{start + d + 5},{d * 1.5}")
    return "\n".join(rows) + "\n"


def report(month, serial, versions, media_type="text/csv"):
    ext = "csv" if media_type == "text/csv" else "pdf"
    canonical = f"{P}/2026.{serial:06d}"
    return {"month": month, "file": {"name": f"Cfud_{month}.{ext}", "media_type": media_type},
            "canonical": canonical,
            "versions": [{"version": n, "doi": f"{canonical}/v{n}", "issued": issued} for n, issued in versions]}


# 2026-01: v1 (Apr) and v2 (Jul). 2026-02: v1 to v3. 2026-03: v1 only, published in Aug. 2026-04: none.
# 2026-02 also has a PDF.
REPORTS = [
    report("2026-01", 1, [(1, "2026-04-01"), (2, "2026-07-01")]),
    report("2026-02", 2, [(1, "2026-04-01"), (2, "2026-05-01"), (3, "2026-08-01")]),
    report("2026-02", 12, [(1, "2026-04-01")], media_type="application/pdf"),
    report("2026-03", 3, [(1, "2026-08-15")]),
]
CATALOG = [
    {"forest": "千葉演習林", "site": "札郷", "variable": "降水量", "unit": "mm", "from": "2026-01", "to": "2026-03"},
    {"forest": "千葉演習林", "site": "札郷", "variable": "最高気温", "unit": "℃", "from": "2026-01", "to": "2026-03"},
    {"forest": "千葉演習林", "site": "清澄", "variable": "降水量", "unit": "mm", "from": "2026-01", "to": "2026-03"},
]
CSL = {"type": "dataset", "title": "札郷の気象月報（2026年2月）", "publisher": "東京大学演習林",
       "author": [{"literal": "東京大学演習林"}], "issued": {"date-parts": [[2026, 8, 1]]}, "version": "v3"}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, status, body, content_type="application/json"):
        data = body.encode() if isinstance(body, str) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urllib.parse.urlsplit(self.path)
        q = urllib.parse.parse_qs(url.query)
        self.server.requests.append((url.path, q, self.headers.get("Accept")))
        if url.path == "/api/v1/weather/catalog":
            rows = [r for r in CATALOG if all(r[k] == q[k][0] for k in ("forest", "site") if k in q)]
            return self.send(200, rows)
        if url.path == "/api/v1/weather/reports":
            if "doi[]" in q:
                wanted = {d.rsplit("/v", 1)[0] for d in q["doi[]"]} | set(q["doi[]"])
                return self.send(200, [r for r in REPORTS if r["canonical"] in wanted])
            if q.get("site") != ["札郷"]:
                return self.send(200, [])
            return self.send(200, [r for r in REPORTS if q["from"][0] <= r["month"] <= q["to"][0]])
        if url.path == "/api/v1/weather/data":
            doi = q["doi"][0]
            for r in REPORTS:
                for v in r["versions"]:
                    if v["doi"] == doi:
                        if r["file"]["media_type"] != "text/csv":
                            return self.send(400, {"error": "not_csv", "message": "CSV ではないファイルです。"})
                        return self.send(200, csv(r["month"], start=10.0 * v["version"]), "text/csv")
            return self.send(404, {"error": "not_found", "message": "登録されていない DOI です。"})
        if url.path.startswith("/doi/"):  # the fake doi.org
            accept = self.headers.get("Accept", "")
            if self.server.agency_formats and accept.split(";")[0] in self.server.agency_formats:
                return self.send(200, "@misc{agency, doi = {%s}}" % url.path[5:], "application/x-bibtex")
            if accept.startswith("application/vnd.citationstyles.csl+json"):
                return self.send(200, CSL, "application/vnd.citationstyles.csl+json")
            return self.send(406, "not acceptable", "text/plain")
        return self.send(404, {"error": "no_route"})


class FakeApi:
    def __enter__(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.requests, self.server.agency_formats = [], set()
        threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()

    @property
    def requests(self):
        return self.server.requests
