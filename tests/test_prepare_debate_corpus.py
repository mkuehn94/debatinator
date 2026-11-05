"""Offline import checks; tiny structural fixtures, no semantic fallacy claims."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("debate_corpus", ROOT / "scripts/prepare-debate-corpus.py")
corpus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(corpus)


def row(**overrides):
    return {"Dialogue ID": "debate-a", "Dialogue": "First statement. Second statement.",
            "Snippet": "First statement.", "Fallacy": "SourceCategory",
            "Subcategory": "SourceSubtype", "Split": "Train", "Unnamed: 0": "0", **overrides}


class PrepareDebateCorpusTests(unittest.TestCase):
    def test_context_deduplicated_without_losing_snippets(self):
        contexts, cases, summary = corpus.normalize([row(), row(Snippet="Second statement.")], "a" * 64)
        self.assertEqual(len(contexts), 1)
        self.assertEqual(len(cases), 2)
        self.assertEqual(cases[0]["context_id"], cases[1]["context_id"])
        self.assertEqual(summary["contexts"], 1)

    def test_repeated_text_keeps_all_span_candidates(self):
        _, cases, summary = corpus.normalize([row(Dialogue="Yes. Yes.", Snippet="Yes.")], "a" * 64)
        self.assertEqual(cases[0]["span_candidates_en"], [[0, 4], [5, 9]])
        self.assertEqual(cases[0]["span_alignment_status"], "ambiguous_repeated_text")
        self.assertEqual(summary["ambiguous_english_spans"], 1)

    def test_missing_source_text_rejected(self):
        with self.assertRaisesRegex(ValueError, "Snippet missing"):
            corpus.normalize([row(Snippet="Absent")], "a" * 64)

    def test_labels_not_promoted_and_translation_not_invented(self):
        contexts, cases, _ = corpus.normalize([row()], "a" * 64)
        self.assertEqual(cases[0]["source_label"], "SourceCategory")
        self.assertEqual(cases[0]["label_review_status"], "source_annotation_not_revalidated")
        self.assertNotIn("expected_main", cases[0])
        self.assertIsNone(cases[0]["text_de"])
        self.assertIsNone(contexts[0]["text_de"])
        self.assertIsNone(cases[0]["span_de"])

    def test_split_overlap_reported_not_silently_fixed(self):
        _, _, summary = corpus.normalize([row(), row(Split="Test")], "a" * 64)
        self.assertEqual(summary["debates_in_multiple_source_splits"], {"debate-a": ["Test", "Train"]})

    def test_source_row_numbers_not_assumed_globally_unique(self):
        _, cases, _ = corpus.normalize([row(), row(**{"Dialogue ID": "debate-b"})], "a" * 64)
        self.assertEqual(cases[0]["source_row_id"], cases[1]["source_row_id"])
        self.assertNotEqual(cases[0]["id"], cases[1]["id"])


if __name__ == "__main__":
    unittest.main()
