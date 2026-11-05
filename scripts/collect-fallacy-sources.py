#!/usr/bin/env python3
"""Cache allowlisted German reference pages; never label examples automatically.

Usage: python scripts/collect-fallacy-sources.py [--refresh]
Dependencies: requests (already in requirements.txt). Raw pages stay in ignored data/.
"""
import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import requests

ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "DebatinatorResearch/0.1 (local educational source collection)"


class TextParser(HTMLParser):
    """Plain text cache for human review, not a semantic example extractor."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "head", "nav", "header", "footer"}:
            self.hidden += 1
        if not self.hidden and tag in {"p", "li", "h1", "h2", "h3", "h4", "br", "blockquote", "dd", "tr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "head", "nav", "header", "footer"}:
            self.hidden = max(0, self.hidden - 1)
        if not self.hidden and tag in {"p", "li", "h1", "h2", "h3", "h4", "blockquote", "dd", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)

    def text(self):
        lines = (re.sub(r"\s+", " ", line).strip() for line in "".join(self.parts).splitlines())
        return "\n".join(line for line in lines if line) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, default=ROOT / "docs/fallacies/source_urls.json",
                        help="Explicit URL allowlist JSON (default: curated reference candidates)")
    parser.add_argument("--refresh", action="store_true", help="Redownload cached pages")
    parser.add_argument("--keep-going", action="store_true",
                        help="On an inaccessible source, skip its host and continue other hosts")
    args = parser.parse_args()
    urls = json.loads(args.sources.read_text())
    out = ROOT / "data/fallacy_sources"
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    robots = {}
    # A new invocation must not silently retry hosts denied earlier in this batch.
    blocked_origins = {
        "{0.scheme}://{0.netloc}".format(urlsplit(item["url"]))
        for item in manifest.values()
        if args.keep_going and not args.refresh
        and item.get("status") in {403, 429, "fetch_error", "access_challenge"}
    }

    def record(key, item):
        manifest[key] = item
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for key, url in urls.items():
        if (key in manifest and manifest[key].get("status") == 200
                and manifest[key].get("url") == url and not args.refresh):
            print(f"cached {key}")
            continue
        origin = "{0.scheme}://{0.netloc}".format(urlsplit(url))
        if origin in blocked_origins:
            if key not in manifest:
                record(key, {"url": url, "status": "host_skipped_after_access_failure"})
            print(f"host skipped: {key}", flush=True)
            continue
        try:
            if origin not in robots:
                r = session.get(origin + "/robots.txt", timeout=30)
                if r.status_code == 404:
                    policy = None
                else:
                    r.raise_for_status()
                    if "<html" in r.text[:500].lower():
                        raise ValueError("robots.txt returned HTML instead of a crawl policy")
                    policy = RobotFileParser()
                    policy.parse(r.text.splitlines())
                robots[origin] = policy
            policy = robots[origin]
            if policy is not None and not policy.can_fetch(USER_AGENT, url):
                record(key, {"url": url, "status": "robots_disallowed"})
                print(f"robots disallowed: {url}", flush=True)
                continue
            # Explicit allowlist, sequential fetches, no access-control bypass.
            time.sleep(max(1.5, policy.crawl_delay(USER_AGENT) or 0) if policy else 1.5)
            r = session.get(url, timeout=40)
        except (requests.RequestException, ValueError) as exc:
            record(key, {"url": url, "status": "fetch_error", "error": str(exc),
                         "retrieved_at": datetime.now(timezone.utc).isoformat()})
            if not args.keep_going:
                raise SystemExit(f"Source unavailable; stopped: {exc}") from exc
            blocked_origins.add(origin)
            print(f"unavailable {key}: {exc}", flush=True)
            continue
        item = {
            "url": url,
            "resolved_url": r.url,
            "status": r.status_code,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }
        if r.status_code == 200:
            raw = r.content
            is_pdf = raw.startswith(b"%PDF-")
            if is_pdf:
                (out / f"{key}.pdf").write_bytes(raw)
                # Optional system utility; never execute content supplied by a page.
                try:
                    extracted = subprocess.run(["pdftotext", "-layout", "-", "-"], input=raw,
                                               capture_output=True, check=True, timeout=30)
                    document = extracted.stdout.decode("utf-8")
                except (OSError, subprocess.SubprocessError) as exc:
                    record(key, {**item, "status": "pdf_extraction_failed", "error": str(exc)})
                    print(f"PDF extraction failed: {key}", flush=True)
                    continue
                plain_text = document
            else:
                # Legacy pages sometimes declare UTF-8 but contain mixed bytes.
                # Preserve exact raw cache/hash; replacement affects review text only.
                document = raw.decode(r.encoding or "utf-8", errors="replace")
                # Wikimedia and Gutenberg declare UTF-8; avoid requests' ISO fallback.
                if "charset=\"utf-8\"" in document.lower() or "charset=utf-8" in document.lower():
                    document = raw.decode("utf-8", errors="replace")
                (out / f"{key}.html").write_bytes(raw)
                parsed = TextParser()
                parsed.feed(document)
                plain_text = parsed.text()
            (out / f"{key}.txt").write_text(plain_text, encoding="utf-8")
            title = re.search(r"<title[^>]*>(.*?)</title>", document, re.S | re.I)
            revision = re.search(r'"wgRevisionId"\s*:\s*(\d+)', document)
            if not revision:
                revision = re.search(r"[?&]oldid=(\d+)", document)
            item.update({
                "title": html.unescape(re.sub("<[^>]+>", "", title.group(1))).strip() if title else key,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "revision_id": revision.group(1) if revision else None,
                "media_type": "application/pdf" if is_pdf else "text/html",
                "cc_by_sa_4_link_present": "creativecommons.org/licenses/by-sa/4.0" in document,
            })
        record(key, item)
        print(f"{r.status_code} {key}: {item.get('title', '')}", flush=True)
        if r.status_code in {403, 429}:
            if not args.keep_going:
                raise SystemExit("Access denied/rate limited; stopped rather than bypassing or retrying.")
            blocked_origins.add(origin)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
