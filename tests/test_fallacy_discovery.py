"""Offline integrity checks for search leads, not semantic label validation."""
from collections import Counter
import copy
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "docs/fallacies"
spec = importlib.util.spec_from_file_location("discovery_renderer", ROOT / "scripts/render-fallacy-discovery.py")
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


class FallacyDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((DIRECTORY / "discovery.json").read_text(encoding="utf-8"))

    def test_every_existing_pattern_searched_and_gaps_retained(self):
        patterns = json.loads((DIRECTORY / "catalog.json").read_text(encoding="utf-8"))["patterns"]
        self.assertEqual({p["id"] for p in patterns}, {c["pattern_id"] for c in self.data["coverage"]})
        queries = self.data["queries"]
        self.assertEqual(len(queries), len({q["id"] for q in queries}))
        for row in self.data["coverage"]:
            attempted = [q for q in queries if q["pattern_id"] == row["pattern_id"] and q["status"] != "not_run"]
            self.assertGreater(len(attempted), 0)
            self.assertEqual({q.get("platform", "bing") for q in attempted}, {"bing", "youtube"})
            self.assertEqual(row["queries_attempted"], len(attempted))
            self.assertEqual(row["new_leads"], sum(row["pattern_id"] in l["fallacy_search_ids"] for l in self.data["leads"]))

    def test_plan_and_retrieval_counts_match_snapshot(self):
        plan = json.loads((DIRECTORY / "discovery_queries.json").read_text(encoding="utf-8"))
        self.assertEqual({q["id"]: q["query"] for q in plan["queries"]},
                         {q["id"]: q["query"] for q in self.data["queries"]})
        leads = self.data["leads"]
        self.assertEqual(self.data["summary"]["queries_attempted"], len(self.data["queries"]))
        self.assertEqual(self.data["summary"]["formats"], dict(Counter(l["format_hint"] for l in leads)))
        self.assertEqual(self.data["summary"]["source_fetches"], dict(Counter(str(l["retrieval"]["status"]) for l in leads)))
        self.assertEqual(self.data["summary"]["cached_page_texts"],
                         sum(bool(l["retrieval"].get("cached_text_path")) for l in leads))

    def test_video_metadata_is_not_playback_or_content_evidence(self):
        for lead in self.data["leads"]:
            video = lead.get("video_metadata")
            if not video:
                continue
            self.assertRegex(video["id"], r"^[A-Za-z0-9_-]{11}$")
            self.assertEqual(lead["format_hint"], "video")
            self.assertEqual(lead["retrieval"]["status"], "video_metadata_only")
            self.assertNotIn("verified_fallacy", video)
            self.assertNotIn("transcript", video)

    def test_no_duplicate_urls_or_automatic_annotations(self):
        leads = self.data["leads"]
        self.assertEqual(len(leads), len({l["id"] for l in leads}))
        self.assertEqual(len(leads), len({l["url"] for l in leads}))
        self.assertEqual(len(leads), self.data["summary"]["new_unique_leads"])
        query_ids = {q["id"] for q in self.data["queries"]}
        for lead in leads:
            self.assertEqual(lead["review_status"], "unreviewed_search_lead")
            self.assertTrue(lead["discoveries"] or lead.get("reference_parents"))
            self.assertNotIn("expected_main", lead)
            self.assertNotIn("assessment", lead)
            self.assertNotIn("proposed_label", lead)
            self.assertTrue(all(d["query_id"] in query_ids for d in lead["discoveries"]))

    def test_reference_parents_use_explicit_reference_allowlist(self):
        urls = set(json.loads((DIRECTORY / "discovery_reference_urls.json").read_text()).values())
        for lead in self.data["leads"]:
            for parent in lead.get("reference_parents", []):
                self.assertIn(parent["url"], urls)
                self.assertIn(parent["pattern_id"], lead["fallacy_search_ids"])

    def test_untrusted_content_escaped(self):
        data = copy.deepcopy(self.data)
        data["leads"][0]["title"] = '<img src=x onerror="alert(1)">'
        data["leads"][0]["search_snippet"] = '</script><script>alert(2)</script>'
        page = renderer.render(data)
        self.assertNotIn('<img src=x', page)
        self.assertNotIn('</script><script>alert(2)', page)
        self.assertIn('&lt;img', page)

    def test_unsafe_urls_rejected(self):
        data = copy.deepcopy(self.data)
        data["leads"][0]["url"] = 'javascript:alert(1)'
        with self.assertRaisesRegex(ValueError, 'Unsafe source URL'):
            renderer.render(data)

    def test_no_remote_resources(self):
        case = self
        class Resources(HTMLParser):
            def handle_starttag(self, tag, attrs):
                if tag in {"script", "img", "iframe", "link"}:
                    attrs = dict(attrs)
                    case.assertNotIn("src", attrs)
                    case.assertNotIn("href", attrs)
        Resources().feed(renderer.render(self.data))

    def test_generated_view_current(self):
        self.assertEqual((DIRECTORY / "discovery.html").read_text(encoding="utf-8"), renderer.render(self.data))


if __name__ == "__main__":
    unittest.main()
