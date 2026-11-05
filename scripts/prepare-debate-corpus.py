#!/usr/bin/env python3
"""Normalize a locally downloaded MM-USED TSV; no model calls or label promotion.

Default output stays in gitignored data/. German full-dialogue translation is a
separate step. Source timestamps refer to English recordings, not German audio.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://github.com/nlp-unibo/multimodal-am-fallacy/blob/main/local_database/MM-DatasetFallacies/no_duplicates/dataset.csv"


def normalize(rows, source_sha256):
    contexts = {}
    cases = []
    debate_splits = defaultdict(set)
    required = {"Dialogue ID", "Dialogue", "Snippet", "Fallacy", "Subcategory", "Split"}
    for index, row in enumerate(rows):
        if not required.issubset(row):
            raise ValueError("Missing MM-USED source columns")
        text, snippet = row["Dialogue"], row["Snippet"]
        if not snippet or snippet not in text:
            raise ValueError(f"Snippet missing from source context at row {index}")
        debate = row["Dialogue ID"]
        debate_splits[debate].add(row["Split"])
        context_id = "context-" + hashlib.sha256((debate + "\0" + text).encode()).hexdigest()[:20]
        if context_id not in contexts:
            contexts[context_id] = {
                "id": context_id, "debate_id": debate, "file_name": row.get("FileName"),
                "source_split": row["Split"], "text_en": text, "text_de": None,
                "speaker_boundaries": "not_reconstructed",
            }
        spans = []
        offset = 0
        while (start := text.find(snippet, offset)) != -1:
            spans.append([start, start + len(snippet)])
            offset = start + 1
        cases.append({
            "id": f"mm-used-{source_sha256[:12]}-r{index:04d}",
            "source_row_index": index, "source_row_id": row.get("Unnamed: 0"),
            "context_id": context_id, "debate_id": debate, "source_split": row["Split"],
            "text_en": snippet, "text_de": None,
            "source_label": row["Fallacy"], "source_subcategory": row["Subcategory"],
            "source_component_label": row.get("CompLabel"), "source_relation_label": row.get("RelLAbel"),
            "span_candidates_en": spans,
            "span_alignment_status": "unique_exact_match" if len(spans) == 1 else "ambiguous_repeated_text",
            "span_de": None,
            "source_audio_begin_seconds": row.get("BeginSnippet"),
            "source_audio_end_seconds": row.get("EndSnippet"),
            "source_audio_clip_id": row.get("idClipSnippet"),
            "label_review_status": "source_annotation_not_revalidated",
            "translation_status": "not_translated",
        })
    overlapping = {debate: sorted(splits) for debate, splits in debate_splits.items() if len(splits) > 1}
    return list(contexts.values()), cases, {
        "source_sha256": source_sha256, "source_url": SOURCE_URL,
        "contexts": len(contexts), "cases": len(cases), "debates": len(debate_splits),
        "source_label_counts": dict(Counter(c["source_label"] for c in cases)),
        "source_split_counts": dict(Counter(c["source_split"] for c in cases)),
        "debates_in_multiple_source_splits": overlapping,
        "ambiguous_english_spans": sum(len(c["span_candidates_en"]) > 1 for c in cases),
        "translated_cases": 0,
        "license_review": "MM repository declares CC BY 4.0; underlying USED release declares CC BY-NC-SA 4.0. Do not assume commercial or unrestricted redistribution rights. Newer ElecDeb HF release declares CC BY-NC-ND 4.0.",
        "purpose": "Research import, not a gold benchmark or approved training set. Context blocks may contain multiple speakers without explicit speaker labels.",
    }


def main():
    import csv
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Downloaded no_duplicates/dataset.csv (tab-separated)")
    parser.add_argument("--output", type=Path, default=ROOT / "data/datasets/mm_used")
    args = parser.parse_args()
    csv.field_size_limit(20_000_000)
    with args.source.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    source_hash = hashlib.sha256(args.source.read_bytes()).hexdigest()
    contexts, cases, manifest = normalize(rows, source_hash)
    manifest["prepared_at"] = datetime.now(timezone.utc).isoformat()
    args.output.mkdir(parents=True, exist_ok=True)
    for name, records in [("contexts_en.jsonl", contexts), ("cases_en.jsonl", cases)]:
        (args.output / name).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records), encoding="utf-8")
    (args.output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
