"""Collector access-policy regressions. Fake HTTP only; never contact source sites."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fallacy_collector", ROOT / "scripts/collect-fallacy-sources.py")
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


def response(url, status=200, body="User-agent: *\nAllow: /\n"):
    item = collector.requests.Response()
    item.status_code = status
    item.url = url
    item.encoding = "utf-8"
    item._content = body.encode("utf-8") if isinstance(body, str) else body
    return item


class FallacyCollectorTests(unittest.TestCase):
    def run_collector(self, urls, replies, *, argv=None, manifest=None, pdf_result=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs/fallacies").mkdir(parents=True)
            default = root / "docs/fallacies/source_urls.json"
            default.write_text(json.dumps(urls))
            argv = list(argv or [])
            if "--sources" in argv:
                index = argv.index("--sources") + 1
                custom = root / argv[index]
                custom.write_text(json.dumps(urls))
                argv[index] = str(custom)
                default.write_text('{"wrong": "https://wrong.example/not-selected"}')
            cache = root / "data/fallacy_sources"
            cache.mkdir(parents=True)
            if manifest is not None:
                (cache / "manifest.json").write_text(json.dumps(manifest))
            calls = []

            def get(url, **kwargs):
                calls.append(url)
                if url not in replies:
                    raise AssertionError(f"Unexpected network request: {url}")
                return replies[url]

            session = SimpleNamespace(headers={}, get=get)
            with (patch.object(collector, "ROOT", root),
                  patch.object(collector.requests, "Session", return_value=session),
                  patch.object(collector.time, "sleep"),
                  patch.object(collector.subprocess, "run", return_value=pdf_result) as pdf,
                  patch("sys.argv", ["collect-fallacy-sources.py", *(argv or [])]),
                  contextlib.redirect_stdout(io.StringIO())):
                error = None
                try:
                    collector.main()
                except SystemExit as exc:
                    error = str(exc)
                result = json.loads((cache / "manifest.json").read_text())
                files = {p.name: p.read_bytes() for p in cache.iterdir()}
                return result, calls, files, error, pdf.call_args

    def test_denied_host_skipped_but_other_hosts_continue(self):
        urls = {"a": "https://denied.example/one", "b": "https://denied.example/two",
                "c": "https://allowed.example/one"}
        replies = {
            "https://denied.example/robots.txt": response("https://denied.example/robots.txt"),
            urls["a"]: response(urls["a"], 403, "Denied"),
            "https://allowed.example/robots.txt": response("https://allowed.example/robots.txt"),
            urls["c"]: response(urls["c"], body="<title>Allowed</title><p>Example</p>"),
        }
        result, calls, _, error, _ = self.run_collector(urls, replies, argv=["--keep-going"])
        self.assertIsNone(error)
        self.assertEqual(result["a"]["status"], 403)
        self.assertEqual(result["b"]["status"], "host_skipped_after_access_failure")
        self.assertEqual(result["c"]["status"], 200)
        self.assertNotIn(urls["b"], calls)

    def test_default_stops_on_rate_limit(self):
        urls = {"a": "https://limited.example/one", "b": "https://other.example/one"}
        replies = {
            "https://limited.example/robots.txt": response("https://limited.example/robots.txt"),
            urls["a"]: response(urls["a"], 429, "Limited"),
        }
        result, calls, _, error, _ = self.run_collector(urls, replies)
        self.assertIn("stopped rather than bypassing", error)
        self.assertEqual(result["a"]["status"], 429)
        self.assertNotIn(urls["b"], calls)

    def test_robots_disallow_prevents_page_fetch(self):
        url = "https://forum.example/private-thread"
        result, calls, _, error, _ = self.run_collector({"a": url}, {
            "https://forum.example/robots.txt": response("https://forum.example/robots.txt",
                                                         body="User-agent: *\nDisallow: /\n")})
        self.assertIsNone(error)
        self.assertEqual(result["a"]["status"], "robots_disallowed")
        self.assertNotIn(url, calls)

    def test_unavailable_robots_does_not_allow_page_fetch(self):
        url = "https://forum.example/thread"
        result, calls, _, error, _ = self.run_collector({"a": url}, {
            "https://forum.example/robots.txt": response("https://forum.example/robots.txt", 403)},
            argv=["--keep-going"])
        self.assertIsNone(error)
        self.assertEqual(result["a"]["status"], "fetch_error")
        self.assertNotIn(url, calls)

    def test_second_run_does_not_retry_denied_host(self):
        url = "https://denied.example/one"
        for status in (403, 429, "fetch_error", "access_challenge"):
            with self.subTest(status=status):
                original = {"url": url, "status": status, "retrieved_at": "earlier"}
                result, calls, _, _, _ = self.run_collector({"a": url}, {}, argv=["--keep-going"],
                                                          manifest={"a": original})
                self.assertEqual(calls, [])
                self.assertEqual(result["a"], original)

    def test_malformed_utf8_keeps_raw_bytes_and_continues(self):
        url = "https://legacy.example/thread"
        raw = b'<meta charset="utf-8"><title>Forum</title><p>discussi\xf3n</p>'
        result, _, files, error, _ = self.run_collector({"legacy": url}, {
            "https://legacy.example/robots.txt": response("https://legacy.example/robots.txt"),
            url: response(url, body=raw),
        }, argv=["--keep-going"])
        self.assertIsNone(error)
        self.assertEqual(result["legacy"]["status"], 200)
        self.assertEqual(result["legacy"]["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(files["legacy.html"], raw)
        self.assertIn("discussi\ufffdn", files["legacy.txt"].decode("utf-8"))

    def test_custom_allowlist_path(self):
        # The default and explicit allowlist use the same access-policy path.
        url = "https://allowed.example/one"
        result, _, _, error, _ = self.run_collector({"a": url}, {
            "https://allowed.example/robots.txt": response("https://allowed.example/robots.txt"),
            url: response(url, body="<p>Example</p>"),
        }, argv=["--sources", "docs/fallacies/discovery_source_urls.json"])
        self.assertIsNone(error)
        self.assertEqual(result["a"]["status"], 200)

    def test_pdf_cache_uses_raw_hash_and_optional_text_extractor(self):
        url = "https://official.example/protocol.pdf"
        raw = b"%PDF-1.4\nfixture"
        result, _, files, error, args = self.run_collector({"protocol": url}, {
            "https://official.example/robots.txt": response("https://official.example/robots.txt"),
            url: response(url, body=raw),
        }, pdf_result=SimpleNamespace(stdout="Redeprüfung".encode("utf-8")))
        self.assertIsNone(error)
        self.assertEqual(result["protocol"]["media_type"], "application/pdf")
        self.assertEqual(result["protocol"]["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(files["protocol.pdf"], raw)
        self.assertEqual(files["protocol.txt"].decode("utf-8"), "Redeprüfung")
        self.assertEqual(args.args[0], ["pdftotext", "-layout", "-", "-"])


if __name__ == "__main__":
    unittest.main()
