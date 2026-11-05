"""Offline checks for the unreviewed teaching-example collection."""
import copy
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "docs/fallacies"
spec = importlib.util.spec_from_file_location("fallacy_renderer", ROOT / "scripts/render-fallacy-catalog.py")
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


class FallacyCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((DIRECTORY / "catalog.json").read_text(encoding="utf-8"))
        cls.sources = json.loads((DIRECTORY / "sources.json").read_text(encoding="utf-8"))

    def test_catalog_valid_and_existing_labels_covered(self):
        renderer.validate(self.catalog, self.sources)

    def test_review_status_not_promoted_to_gold(self):
        self.assertEqual(self.catalog["review_status"], "needs_user_review")
        for p in self.catalog["patterns"]:
            for e in p["examples"]:
                self.assertNotIn("expected_main", e)
                self.assertIn("proposed_label", e)

    def test_duplicate_example_rejected(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["patterns"][0]["examples"].append(catalog["patterns"][0]["examples"][0])
        with self.assertRaisesRegex(ValueError, "Duplicate example"):
            renderer.validate(catalog, self.sources)

    def test_unknown_source_rejected(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["patterns"][0]["examples"][0]["source_ids"] = ["missing-source"]
        with self.assertRaisesRegex(ValueError, "Invalid sources"):
            renderer.validate(catalog, self.sources)

    def test_source_metadata_has_attribution_and_cache_identity(self):
        for source in self.sources.values():
            self.assertTrue(source["authors"])
            self.assertTrue(source["license"])
            self.assertRegex(source["sha256"], r"^[a-f0-9]{64}$")
            self.assertTrue(source["retrieved_at"])
            if "de.wikipedia.org" in source["canonical_url"]:
                self.assertTrue(source["revision_id"])
                self.assertIn("oldid=", source["revision_url"])

    def test_negative_controls_and_context_dependent_cases_present(self):
        examples = [e for p in self.catalog["patterns"] for e in p["examples"]]
        for assessment in ("not_fallacious", "context_dependent", "fallacious"):
            self.assertTrue(any(e["assessment"] == assessment for e in examples))
        self.assertTrue(any(e["origin"] == "synthetic_from_definition" for e in examples))
        self.assertTrue(any(e["origin"] == "source_example_adaptation" for e in examples))

    def test_new_research_is_sourced_not_synthetic_padding(self):
        examples = [e for p in self.catalog["patterns"] for e in p["examples"]
                    if e.get("collection_batch")]
        batches = self.catalog["research_batches"]
        self.assertEqual(len(examples), sum(b["added_examples"] for b in batches))
        self.assertTrue(all(e["origin"] == "source_example_adaptation" for e in examples))
        self.assertTrue(any(e["setting"] == "forum_exchange" for e in examples))
        self.assertTrue(any(e["setting"] == "documented_political_speech" for e in examples))
        for e in examples:
            if e["label_basis"] == "editorial_disagreement":
                self.assertTrue(e.get("source_claimed_label"), e["id"])

    def test_missing_speech_verification_rejected(self):
        catalog = copy.deepcopy(self.catalog)
        speech = next(e for p in catalog["patterns"] for e in p["examples"]
                      if e["setting"] == "documented_political_speech")
        speech.pop("verification")
        with self.assertRaisesRegex(ValueError, "Missing speech verification"):
            renderer.validate(catalog, self.sources)

    def test_promoted_example_review_status_rejected(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["patterns"][0]["examples"][0]["review_status"] = "gold"
        with self.assertRaisesRegex(ValueError, "Invalid review/evidence"):
            renderer.validate(catalog, self.sources)

    def test_non_https_revision_link_rejected(self):
        sources = copy.deepcopy(self.sources)
        next(iter(sources.values()))["revision_url"] = "javascript:alert(1)"
        with self.assertRaisesRegex(ValueError, "Invalid source metadata"):
            renderer.validate(self.catalog, sources)

    def test_research_log_and_source_snapshot_agree(self):
        log = json.loads((DIRECTORY / "research_log.json").read_text(encoding="utf-8"))
        entries = log["entries"]
        self.assertEqual(len(entries), log["summary"]["candidate_records"])
        self.assertEqual(len({e["url"] for e in entries}), log["summary"]["candidate_urls"])
        self.assertEqual(len({e["url"] for e in entries if e["status"] == 200}),
                         log["summary"]["retrieved_unique_urls"])
        self.assertEqual(sum(e["status"] == 200 for e in entries), log["summary"]["retrieved_ok"])
        for entry in entries:
            if entry["decision"] == "used":
                source = self.sources[entry["id"]]
                self.assertEqual(entry["status"], 200)
                self.assertEqual(entry["sha256"], source["sha256"])
        self.assertEqual(sum(e["decision"] == "used" for e in entries),
                         log["summary"]["used_source_records"])

    def test_filter_metadata_and_counts_rendered(self):
        page = renderer.render(self.catalog, self.sources)["index.html"]
        self.assertNotIn("__NEW_COUNT__", page)
        self.assertNotIn("__SETTING_OPTIONS__", page)
        expected = sum(e["setting"] == "forum_exchange"
                       for p in self.catalog["patterns"] for e in p["examples"])
        self.assertEqual(page.count('data-setting="forum_exchange"'), expected)
        self.assertIn('data-preset="disputed"', page)
        self.assertIn('id="batch"', page)

    def test_html_escapes_example_content(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["patterns"][0]["examples"][0]["b"] = '<img src=x onerror="alert(1)">'
        page = renderer.render(catalog, self.sources)["index.html"]
        self.assertNotIn('<img src=x onerror=', page)
        self.assertIn('&lt;img', page)

    def test_html_has_no_remote_resources(self):
        class Resources(HTMLParser):
            def handle_starttag(inner, tag, attrs):
                attrs = dict(attrs)
                if tag in {"script", "img", "iframe", "link"}:
                    self.assertNotIn("src", attrs)
                    self.assertNotIn("href", attrs)
        Resources().feed(renderer.render(self.catalog, self.sources)["index.html"])

    def test_generated_views_current(self):
        for name, text in renderer.render(self.catalog, self.sources).items():
            self.assertEqual((DIRECTORY / name).read_text(encoding="utf-8"), text, name)


if __name__ == "__main__":
    unittest.main()
