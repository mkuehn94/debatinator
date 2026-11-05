#!/usr/bin/env python3
"""Build a private bilingual review batch; never invent dialogue or promote labels.

Inputs and generated text stay in ignored data/. Code uses no models or network.
"""
import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path
import random
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "data/datasets/translation_review"
DEFAULT_REVIEW = ROOT / "datasets/reviews/mm_used.json"
BATCH = "mm-used-de-review-150-v3"
COMPATIBLE_BATCHES = ["mm-used-de-review-100-v1", "mm-used-de-review-120-v2", BATCH]
NEXT_ROWS = [34, 69, 73, 85, 87, 93, 113, 127, 161, 171,
             189, 220, 226, 253, 300, 306, 312, 318, 328, 331,
             350, 432, 453, 467, 509, 510, 529, 538, 578, 582,
             604, 627, 628, 629, 653, 684, 706, 726, 737, 756,
             769, 825, 828, 847, 848, 857, 878, 936, 941, 949]
QUOTAS = {"AdHominem": 25, "AppealtoAuthority": 20, "AppealtoEmotion": 20,
          "FalseCause": 15, "Slipperyslope": 12, "Slogans": 8}


def review_file(folder):
    """Default project judgments are tracked; custom directories stay self-contained."""
    return DEFAULT_REVIEW if folder.resolve() == DEFAULT.resolve() else folder / 'review.json'


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def select_cases(cases, pilot, quotas=None, emotion_each=5):
    """Reproduce the original coverage-first selection, not a correctness filter."""
    quotas = QUOTAS if quotas is None else quotas
    by_row = {case['source_row_index']: case for case in cases}
    selected = {case['source_row_index'] for case in pilot}
    selected.update(case['source_row_index'] for case in cases if case['source_subcategory'] == 'Tu quoque')
    rng = random.Random(20261105)
    for subtype in ['Loaded Language', 'Flag waving', 'Appeal to pity', 'Appeal to fear']:
        present = sum(by_row[i]['source_label'] == 'AppealtoEmotion' and by_row[i]['source_subcategory'] == subtype for i in selected)
        candidates = [case['source_row_index'] for case in cases if case['source_label'] == 'AppealtoEmotion'
                      and case['source_subcategory'] == subtype and case['source_row_index'] not in selected]
        rng.shuffle(candidates)
        selected.update(candidates[:max(0, emotion_each - present)])
    for label, quota in quotas.items():
        while sum(by_row[i]['source_label'] == label for i in selected) < quota:
            candidates = [case['source_row_index'] for case in cases if case['source_label'] == label and case['source_row_index'] not in selected]
            if not candidates:
                raise ValueError(f'Not enough source cases for {label}')
            rng.shuffle(candidates)
            subcounts = Counter(by_row[i]['source_subcategory'] for i in selected if by_row[i]['source_label'] == label)
            debatecounts = Counter(by_row[i]['debate_id'] for i in selected)
            candidates.sort(key=lambda i: (subcounts[by_row[i]['source_subcategory']], debatecounts[by_row[i]['debate_id']]))
            selected.add(candidates[0])
    for row in NEXT_ROWS:
        if row not in by_row:
            raise ValueError(f'Unknown continuation row {row}')
        selected.add(row)
    return [{'row': i, 'debate': by_row[i]['debate_id'], 'label': by_row[i]['source_label'],
             'subtype': by_row[i]['source_subcategory'], 'en': by_row[i]['text_en']} for i in sorted(selected)]


def assemble(cases, contexts, selection, translations, pilot, manifest):
    by_row = {case["source_row_index"]: case for case in cases}
    by_context = {context["id"]: context for context in contexts}
    old = {str(case["source_row_index"]): case for case in pilot}
    selected = [item["row"] for item in selection]
    if len(selected) != len(set(selected)):
        raise ValueError("Duplicate selected row")
    if set(translations) - {str(row) for row in selected}:
        raise ValueError("Translation has no selected source row")
    records = []
    for item in selection:
        row = item["row"]
        case = by_row[row]
        if (item["en"] != case["text_en"] or item["label"] != case["source_label"]
                or item["subtype"] != case["source_subcategory"] or item['debate'] != case['debate_id']):
            raise ValueError(f"Selection/source mismatch: {row}")
        supplied = translations.get(str(row), old.get(str(row)))
        if not supplied or not supplied.get("text_de", "").strip():
            raise ValueError(f"Missing German translation: {row}")
        text_de = supplied["text_de"]
        context = by_context[case["context_id"]]
        for start, end in case["span_candidates_en"]:
            if context["text_en"][start:end] != case["text_en"]:
                raise ValueError(f"Invalid English span: {row}")
        window = None
        if str(row) in old and str(row) not in translations:
            previous = old[str(row)]
            start, end = previous["source_context_char_start"], previous["source_context_char_end"]
            if context["text_en"][start:end] != previous["context_en"]:
                raise ValueError(f"Pilot context/source mismatch: {row}")
            position = previous["context_de"].find(text_de)
            if position < 0:
                raise ValueError(f"Pilot German span mismatch: {row}")
            window = {"text_en": previous["context_en"], "text_de": previous["context_de"],
                      "source_span_en": [start, end], "snippet_span_de": [position, position + len(text_de)],
                      "scope": "cropped_window_not_full_context"}
        flags = []
        if len(case["text_en"].split()) <= 5:
            flags.append("very_short_source_fragment")
        if len(case["span_candidates_en"]) != 1:
            flags.append("ambiguous_repeated_english_text")
        if not window:
            flags.append("full_context_english_only")
        records.append({
            "id": case["id"] + "-de-review", "source_case_id": case["id"],
            "source_row_index": row, "source_id": "mm_used", "context_id": case["context_id"],
            "debate_id": case["debate_id"], "source_split": case["source_split"],
            "source_label": case["source_label"], "source_subcategory": case["source_subcategory"],
            "text_en": case["text_en"], "text_de": text_de,
            "source_span_candidates_en": case["span_candidates_en"], "translated_window": window,
            "source_audio_begin_seconds": case["source_audio_begin_seconds"],
            "source_audio_end_seconds": case["source_audio_end_seconds"],
            "translation_method": "assistant_translation", "review_status": "needs_user_review",
            "translation_notes": supplied.get("notes", supplied.get("translation_notes", [])),
            "review_hints": flags,
            "review": {"translation": "not_requested", "label": "pending", "note": ""},
        })
    used_contexts = {record["context_id"] for record in records}
    result = {
        "schema_version": 1, "batch_id": BATCH, "review_status": "needs_user_review",
        "source_sha256": manifest["source_sha256"],
        "review_policy": "Source-label review only; translation review not requested by user. Optional German corrections remain available. This is not individual human validation of translations.",
        "scope": "Selected source snippets translated; full context retained in English. German context windows exist only where explicitly supplied. No invented speaker attribution or A/B setup.",
        "selection": "Deterministic class/subcategory/debate coverage, seed 20261105; includes original 100-row batch plus fixed continuation rows. Not a semantic correctness screen or representative prevalence sample.",
        "rights": "Private research batch. MM repository declares CC BY 4.0; underlying USED declares CC BY-NC-SA 4.0. Clarify license chain before redistribution or commercial reuse. Text stays in gitignored data/.",
        "sources": {"mm_used": {
            "url": manifest["source_url"], "paper": "https://aclanthology.org/2024.eacl-short.16/",
            "attribution": "Eleonora Mancini, Federico Ruggeri, Paolo Torroni (EACL 2024); underlying USED: Pierpaolo Goffredo, Shohreh Haddadan, Vorakit Vorakitphan, Elena Cabrio, Serena Villata (IJCAI 2022).",
        }},
        "contexts": {key: {"text_en": value["text_en"], "speaker_boundaries": "not_reconstructed"}
                     for key, value in by_context.items() if key in used_contexts},
        "examples": records,
    }
    result["counts"] = {"examples": len(records), "contexts": len(used_contexts),
        "debates": len({record['debate_id'] for record in records}),
        "source_labels": dict(Counter(r["source_label"] for r in records)),
        "source_subcategories": dict(Counter(r["source_subcategory"] for r in records)),
        "source_splits": dict(Counter(r["source_split"] for r in records)),
        "translated_context_windows": sum(r["translated_window"] is not None for r in records),
        "neutral_examples": 0, "user_reviewed": 0,
        "label_decisions": {"agree": 0, "disagree": 0, "uncertain": 0, "pending": len(records)}}
    return result


def review_export(data):
    """Keep user judgments separate from source annotations and translated text."""
    return {"batch_id": data["batch_id"], "source_sha256": data["source_sha256"],
            "review_only": True, "decisions": [
                {"id": record["id"], **record["review"],
                 "correction_de": record["review"].get("correction_de")}
                for record in data["examples"]]}


def apply_review(data, payload):
    """Validate entire export before applying judgments; never replace source labels."""
    if (not isinstance(payload, dict) or payload.get("batch_id") not in COMPATIBLE_BATCHES
            or payload.get("source_sha256") != data["source_sha256"]
            or not isinstance(payload.get("decisions"), list)):
        raise ValueError("Different review batch, source version, or invalid decisions")
    by_id = {record["id"]: record for record in data["examples"]}
    seen = set()
    for entry in payload["decisions"]:
        if (not isinstance(entry, dict) or not isinstance(entry.get("id"), str)
                or entry["id"] not in by_id or entry["id"] in seen
                or entry.get("label") not in ("pending", "agree", "disagree", "uncertain")
                or entry.get("translation", "not_requested") not in
                    ("not_requested", "pending", "faithful", "revise", "uncertain")
                or not isinstance(entry.get("note"), str)
                or "correction_de" not in entry
                or not (entry["correction_de"] is None or isinstance(entry["correction_de"], str))):
            raise ValueError("Invalid review decision or duplicate/unknown ID")
        seen.add(entry["id"])
    for entry in payload["decisions"]:
        record = by_id[entry["id"]]
        record["review"] = {"translation": entry.get("translation", "not_requested"),
                            "label": entry["label"], "note": entry["note"],
                            "correction_de": entry["correction_de"]}
        record["review_status"] = ("needs_user_review" if entry["label"] == "pending"
                                   else "source_label_reviewed")
    counts = Counter(record["review"]["label"] for record in data["examples"])
    data["counts"]["label_decisions"] = {key: counts[key] for key in ("agree", "disagree", "uncertain", "pending")}
    data["counts"]["user_reviewed"] = len(data["examples"]) - counts["pending"]
    data["review_status"] = ("needs_user_review" if not data["counts"]["user_reviewed"]
                             else "partially_label_reviewed" if counts["pending"]
                             else "source_labels_reviewed")
    return data


def render(data):
    source_rows = []
    for source in data['sources'].values():
        for key in ['url', 'paper']:
            if urlsplit(source[key]).scheme not in {'http', 'https'}:
                raise ValueError('Unsafe source URL')
        source_rows.append('<li>' + escape(source['attribution'])
            + ' <a href="' + escape(source['url'], quote=True) + '" target="_blank" rel="noreferrer noopener">Datensatz</a>'
            + ' · <a href="' + escape(source['paper'], quote=True) + '" target="_blank" rel="noreferrer noopener">Paper</a></li>')
    cards = []
    for record in data["examples"]:
        h = lambda value: escape(str(value), quote=True)
        context = data["contexts"][record["context_id"]]["text_en"]
        window = record.get("translated_window")
        window_html = (f'<details><summary>Deutsches Kontextfenster (gekürzt, nicht vollständiger Dialog)</summary>'
                       f'<p>{h(window["text_de"])}</p></details>') if window else ''
        notes = ''.join(f'<li>{h(note)}</li>' for note in record["translation_notes"])
        hints = ' · '.join(record['review_hints'])
        decision = record['review']
        label_options = ''.join(
            f'<option value="{value}"' + (' selected' if decision['label'] == value else '')
            + f'>{text}</option>' for value, text in
            [('pending', 'Offen'), ('agree', 'Stimme zu'),
             ('disagree', 'Stimme nicht zu'), ('uncertain', 'Kontext unklar')])
        correction = decision.get('correction_de')
        if correction is None:
            correction = record['text_de']
        cards.append(f'''<article id="{h(record['id'])}" data-label="{h(record['source_label'])}" data-subtype="{h(record['source_subcategory'])}" data-translation-review="{h(record['review']['translation'])}">
<h2>{h(record['id'])}</h2><p class="meta">Quellenlabel: <b>{h(record['source_label'])}</b> / {h(record['source_subcategory'])} · Debatte {h(record['debate_id'])} · Original-Split {h(record['source_split'])}</p>
<p><b>EN:</b> {h(record['text_en'])}</p><p class="german"><b>DE:</b> <span class="original-de">{h(record['text_de'])}</span></p>
{window_html}<details><summary>Vollständiger Quellkontext: Englisch, unübersetzt; Sprechergrenzen nicht rekonstruiert</summary><p class="context">{h(context)}</p></details>
<p class="meta">Englische Audiozeit laut Quelle, nicht verifiziert: {h(record['source_audio_begin_seconds'])}–{h(record['source_audio_end_seconds'])} s. Kein deutsches Audio.</p>
<details><summary>Übersetzungshinweise / Kontextgrenzen</summary><p>{h(hints)}</p><ul>{notes}</ul></details>
<div class="review"><label>Quellenlabel <select class="label">{label_options}</select></label>
<label>Anmerkung <textarea class="note" rows="2">{h(decision['note'])}</textarea></label>
<details><summary>Deutsche Formulierung korrigieren</summary><textarea class="correction" rows="4">{h(correction)}</textarea></details></div></article>''')
    labels = ''.join(f'<option>{escape(label)}</option>' for label in data['counts']['source_labels'])
    subtypes = ''.join(f'<option value="{escape(label, quote=True)}">{escape(label or "(keine Unterkategorie)")}</option>'
                       for label in data['counts']['source_subcategories'] if label)
    header = json.dumps({"batch_id": data["batch_id"], "source_sha256": data["source_sha256"]}).replace('<', '\\u003c')
    compatible = json.dumps(COMPATIBLE_BATCHES)
    return '''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Debatinator – übersetzte Datensatzbeispiele</title><style>
body{font:16px/1.5 system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;background:#f4f6f9;color:#17212e}h2{font-size:1rem;overflow-wrap:anywhere}a{color:#175ca6}.notice{padding:1rem;background:#fff0c2;border-left:5px solid #c08a00}.toolbar{display:flex;gap:.5rem;flex-wrap:wrap;position:sticky;top:0;background:#f4f6f9;padding:.8rem 0}input,select,button,textarea{font:inherit;padding:.4rem}input{flex:1}textarea{width:100%;box-sizing:border-box}article{background:white;border:1px solid #d4dce6;border-radius:8px;padding:1rem;margin:1rem 0;overflow-wrap:anywhere}.german{background:#eaf5ed;padding:.7rem}.meta{color:#536273;font-size:.85rem}.context{white-space:pre-wrap}.review{border-top:1px solid #ddd;padding-top:.7rem;display:grid;gap:.6rem}button{cursor:pointer}[hidden]{display:none!important}
</style><h1>Übersetzte Datensatzbeispiele zur Durchsicht</h1>''' + f'<p><b>{len(cards)} Übersetzungen</b> · {len(data["counts"]["source_labels"])} Quellenklassen · {data["counts"]["source_subcategories"].get("Tu quoque", 0)} Tu quoque · keine neutralen Beispiele</p>' + '''
<p><a href="../../../docs/fallacies/index.html">Zur Hauptsammlung</a> · <a href="dataset.json">Strukturierter Datensatz</a></p>
''' + '<details><summary>Quellen und Rechte</summary><ul>' + ''.join(source_rows) + '</ul><p>' + escape(data['rights']) + '</p></details>' + '''
<p class="notice"><b>Keine bestätigten Fehlschlüsse.</b> Nur Quellenlabels beurteilen; keine Übersetzungsbewertung nötig. Deutsche Formulierungen lassen sich bei Bedarf korrigieren. Originale stammen aus englischen US-Debatten, nicht aus deutschen Debatten. Nur markierte Passagen sind übersetzt; vollständiger Kontext bleibt Englisch. Keine Sprecheridentitäten ergänzt. Auch Slogans, Emotionswörter oder ein Vorwurf sind nicht automatisch ein Fehlschluss. Rechtekette vor Veröffentlichung klären; private lokale Sammlung.</p>
<div class="toolbar"><input id="search" type="search" placeholder="EN, DE, ID oder Notiz suchen" aria-label="Suche"><select id="class" aria-label="Quellenklasse"><option value="">Alle Quellenklassen</option>''' + labels + '''</select><select id="subtype" aria-label="Unterkategorie"><option value="">Alle Unterkategorien</option>''' + subtypes + '''</select><select id="state" aria-label="Prüfstatus"><option value="">Alle Prüfstände</option><option value="pending">Noch offen</option><option value="reviewed">Quellenlabel beurteilt</option></select></div>
<p><button id="export">Prüfung als JSON exportieren</button> <label>Prüfung laden <input id="import" type="file" accept="application/json,.json"></label></p>
<p><b>Nicht automatisch gespeichert.</b> Vor Schließen exportieren. Export enthält Prüfentscheidungen und Korrekturen; der Quelldatensatz wird nicht automatisch geändert.</p><p id="count" aria-live="polite"></p><main>''' + '\n'.join(cards) + '''</main><script>
const batch = ''' + header + ''';
const cards = [...document.querySelectorAll('article')];
const compatibleBatches = new Set(''' + compatible + ''');
const translationValues = new Set(['not_requested','pending','faithful','revise','uncertain']);
const labelValues = new Set(['pending','agree','disagree','uncertain']);
function filter() {
  const text = document.getElementById('search').value.toLocaleLowerCase();
  const label = document.getElementById('class').value;
  const subtype = document.getElementById('subtype').value;
  const state = document.getElementById('state').value;
  let visible = 0;
  for (const card of cards) {
    const reviewed = card.querySelector('.label').value !== 'pending';
    const haystack = card.textContent + card.querySelector('.note').value + card.querySelector('.correction').value;
    card.hidden = !((!text || haystack.toLocaleLowerCase().includes(text)) && (!label || card.dataset.label === label)
      && (!subtype || card.dataset.subtype === subtype) && (!state || (state === 'reviewed' ? reviewed : !reviewed)));
    if (!card.hidden) visible++;
  }
  document.getElementById('count').textContent = `${visible} / ${cards.length} Beispiele sichtbar`;
}
function exportReview() {
  return {...batch, review_only: true, decisions: cards.map(card => ({id:card.id,
    translation:card.dataset.translationReview, label:card.querySelector('.label').value,
    note:card.querySelector('.note').value,
    correction_de:card.querySelector('.correction').value === card.querySelector('.original-de').textContent ? null : card.querySelector('.correction').value}))};
}
function applyReview(data) {
  if (!compatibleBatches.has(data.batch_id) || data.source_sha256 !== batch.source_sha256 || !Array.isArray(data.decisions)) throw Error('Andere Sammlung oder Quellversion.');
  const byId = new Map(cards.map(card => [card.id,card]));
  const seen = new Set();
  for (const entry of data.decisions) {
    if (!byId.has(entry.id) || seen.has(entry.id) || !translationValues.has(entry.translation ?? 'not_requested') || !labelValues.has(entry.label)
      || typeof entry.note !== 'string' || !(entry.correction_de === null || typeof entry.correction_de === 'string')) throw Error('Ungültiger Prüfdatensatz.');
    seen.add(entry.id);
  }
  for (const entry of data.decisions) {
    const card = byId.get(entry.id);
    card.dataset.translationReview = entry.translation ?? 'not_requested';
    card.querySelector('.label').value = entry.label;
    card.querySelector('.note').value = entry.note;
    card.querySelector('.correction').value = entry.correction_de === null ? card.querySelector('.original-de').textContent : entry.correction_de;
  }
  filter();
}
document.getElementById('export').addEventListener('click', () => {
  const url = URL.createObjectURL(new Blob([JSON.stringify(exportReview(),null,2)],{type:'application/json'}));
  const a = document.createElement('a'); a.href=url; a.download=batch.batch_id+'-review.json'; a.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
});
document.getElementById('import').addEventListener('change', async event => {
  try { const file = event.target.files[0]; if (file && file.size > 5000000) throw Error('Prüfdatei zu groß.'); if (file) applyReview(JSON.parse(await file.text())); }
  catch(error) { alert('Prüfung nicht geladen: '+error.message); }
});
document.querySelectorAll('input:not([type=file]),select,textarea').forEach(el=>el.addEventListener('input',filter));
filter();
</script></html>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=DEFAULT)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--import-review', type=Path, help='Validate and persist a user review export locally')
    args = parser.parse_args()
    if args.check and args.import_review:
        parser.error('--check and --import-review cannot be combined')
    folder = args.directory
    corpus = ROOT / 'data/datasets/mm_used'
    cases = read_jsonl(corpus / 'cases_en.jsonl')
    pilot = read_jsonl(corpus / 'translation_pilot_de.jsonl')
    selection = json.loads((folder / 'selection.json').read_text())
    if selection != select_cases(cases, pilot):
        raise ValueError('Frozen selection differs from reproducible source selection')
    data = assemble(cases, read_jsonl(corpus / 'contexts_en.jsonl'), selection,
        json.loads((folder / 'translations_de_new.json').read_text()),
        pilot, json.loads((corpus / 'manifest.json').read_text()))
    review_path = review_file(folder)
    if review_path.exists():
        apply_review(data, json.loads(review_path.read_text(encoding='utf-8')))
    if args.import_review:
        apply_review(data, json.loads(args.import_review.read_text(encoding='utf-8')))
        review_path.write_text(json.dumps(review_export(data), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    outputs = {'dataset.json': json.dumps(data, ensure_ascii=False, indent=2) + '\n', 'index.html': render(data)}
    for name, content in outputs.items():
        path = folder / name
        if args.check:
            if path.read_text(encoding='utf-8') != content:
                raise SystemExit(f'Stale {path}; rebuild translation review')
        else:
            path.write_text(content, encoding='utf-8')
    print(json.dumps(data['counts'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
