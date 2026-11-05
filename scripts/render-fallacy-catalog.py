#!/usr/bin/env python3
"""Validate the review catalog and render offline HTML + Markdown (no network)."""
import argparse
import ast
from collections import Counter
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "docs/fallacies"
ORIGINS = {
    "source_example_adaptation": "Quellenbeispiel, bearbeitet",
    "synthetic_from_definition": "Neu erstellt nach Definition",
    "synthetic_control": "Neu erstellte Negativkontrolle",
}
ASSESSMENTS = {
    "fallacious": "Fehlerbeispiel (Vorschlag)",
    "not_fallacious": "Kein entsprechender Fehler",
    "context_dependent": "Kontextabhängig / nicht eindeutig",
}

SETTINGS = {
    "teaching_example": "Lehrbeispiel auf Website",
    "forum_teaching_example": "Im Forum angeführtes Beispiel / erinnerter Spruch",
    "forum_exchange": "Tatsächlicher schriftlicher Forumswechsel",
    "reported_political_speech": "Politische Äußerung, nur sekundär berichtet",
    "documented_political_speech": "Politische Rede, offizielles Transkript geprüft",
    "historical_example": "Historisches Beispiel / Gleichnis",
}
LABEL_BASES = {
    "source_explicit": "Quelle erläutert diese Einordnung",
    "editorial_interpretation": "Eigener Einordnungsvorschlag",
    "editorial_disagreement": "Quellenetikett ausdrücklich bestritten",
}
DIALOGUE_STATUSES = {
    "constructed": "Neu konstruierter Dialog",
    "editorial_setup": "A/B-Rahmen redaktionell ergänzt",
    "adapted_source_dialogue": "Quellendialog paraphrasiert",
    "compressed_exchange": "Mehrere Beiträge / Schritte verdichtet",
}


def validate(catalog, sources):
    if catalog.get("schema_version") != 2 or catalog.get("review_status") != "needs_user_review":
        raise ValueError("Catalog must remain schema 2 and unreviewed")
    tree = ast.parse((ROOT / "eval/taxonomy.py").read_text())
    main = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "MAIN" for t in n.targets))
    required = set(main["criteria"]) - {"sachlich"}
    pattern_ids, example_ids, supported = set(), set(), set()
    for p in catalog["patterns"]:
        if p["id"] in pattern_ids:
            raise ValueError(f"Duplicate pattern: {p['id']}")
        pattern_ids.add(p["id"])
        if p["repo_label"] is not None:
            if p["repo_label"] not in required:
                raise ValueError(f"Unknown repository label: {p['repo_label']}")
            supported.add(p["repo_label"])
        for key in p["source_ids"]:
            if key not in sources:
                raise ValueError(f"Unknown source: {key}")
        for e in p["examples"]:
            if e["id"] in example_ids:
                raise ValueError(f"Duplicate example: {e['id']}")
            example_ids.add(e["id"])
            if e["origin"] not in ORIGINS or e["assessment"] not in ASSESSMENTS:
                raise ValueError(f"Invalid provenance/assessment: {e['id']}")
            for field in ("a", "b", "source_locator", "explanation"):
                if not e[field].strip():
                    raise ValueError(f"Missing {field}: {e['id']}")
            if not e["source_ids"] or not set(e["source_ids"]) <= set(sources):
                raise ValueError(f"Invalid sources: {e['id']}")
            if (e.get("setting") not in SETTINGS or e.get("label_basis") not in LABEL_BASES
                    or e.get("dialogue_status") not in DIALOGUE_STATUSES
                    or e.get("review_status") != "needs_user_review"):
                raise ValueError(f"Invalid review/evidence metadata: {e['id']}")
            if e["setting"] == "documented_political_speech":
                if (e.get("verification") != "official_transcript_checked" or not e.get("speaker")
                        or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", e.get("event_date", ""))):
                    raise ValueError(f"Missing speech verification: {e['id']}")
            if not set(e["source_ids"]) <= set(p["source_ids"]):
                raise ValueError(f"Example source absent from pattern: {e['id']}")
            expected = "sachlich" if e["assessment"] == "not_fallacious" else p["id"]
            if e["proposed_label"] != expected:
                raise ValueError(f"Inconsistent proposed label: {e['id']}")
    if supported != required:
        raise ValueError(f"Missing repository labels: {required - supported}")
    for key, s in sources.items():
        urls = [s[field] for field in ("url", "canonical_url", "revision_url") if field in s]
        if (any(urlsplit(url).scheme != "https" or not urlsplit(url).netloc for url in urls)
                or not re.fullmatch(r"[a-f0-9]{64}", s.get("sha256", ""))):
            raise ValueError(f"Invalid source metadata: {key}")


def source_links(keys, sources, html=False):
    if html:
        return " · ".join(f'<a href="{escape(sources[k].get("revision_url", sources[k]["url"]), quote=True)}" '
                          f'target="_blank" rel="noopener noreferrer">{escape(k)}</a>' for k in keys)
    return ", ".join(f'[{k}]({sources[k].get("revision_url", sources[k]["url"])})' for k in keys)


def render(catalog, sources):
    examples = [e for p in catalog["patterns"] for e in p["examples"]]
    counts = Counter(e["origin"] for e in examples)
    summary = (f'{len(catalog["patterns"])} Muster · {len(examples)} Beispiele · '
               f'{counts["source_example_adaptation"]} bearbeitete Quellenbeispiele · '
               f'{counts["synthetic_from_definition"]} neue Lehrbeispiele · '
               f'{counts["synthetic_control"]} neue Negativkontrollen')
    md = ["# Deutsche Fehlschluss-Beispiele zur Durchsicht", "", summary, "",
          "**Alle Labels sind Vorschläge und noch nicht nutzergeprüft. Keine wörtlichen Quellenauszüge.**", "",
          catalog["purpose"], "", catalog["provenance_note"], "",
          "Die sieben vorhandenen Repo-Labels stehen zuerst. Erweiterungen ändern die Taxonomie nicht.", "",
          "Quelle, Revision, Abrufdatum, Rechtehinweise: [sources.json](sources.json). "
          "Methodik: [README.md](README.md). Offline-Suche: [index.html](index.html).", "",
          "## Inhalt", ""]
    md += [f'- [{p["name"]}](#{p["id"]})' for p in catalog["patterns"]]
    sections = []
    for p in catalog["patterns"]:
        scope = "repo" if p["repo_label"] else "extended"
        scope_label = "Vorhandenes Repo-Label" if p["repo_label"] else "Erweiterung, noch nicht im Klassifikator"
        md += ["", f'<a id="{p["id"]}"></a>', f'## {p["name"]}', "",
               f'`{p["id"]}` · {scope_label} · `{p["kind"]}`', "", p["definition"], "",
               f'**Abgrenzung:** {p["caution"]}', ""]
        cards = []
        for e in p["examples"]:
            md += [f'### {e["id"]}', "", f'{ORIGINS[e["origin"]]} · {ASSESSMENTS[e["assessment"]]}', ""]
            if e.get("context"):
                md += [f'**Kontext:** {e["context"]}', ""]
            md += [f'**A:** {e["a"]}', "", f'**B:** {e["b"]}', "",
                   f'**Labelvorschlag:** `{e["proposed_label"]}`', "",
                   f'**Begründung:** {e["explanation"]}', "",
                   f'**Quelle:** {source_links(e["source_ids"], sources)}', "",
                   f'**Fundstelle / Bearbeitung:** {e["source_locator"]}', "",
                   f'**Material:** {SETTINGS[e["setting"]]} · {DIALOGUE_STATUSES[e["dialogue_status"]]}', "",
                   f'**Einordnung:** {LABEL_BASES[e["label_basis"]]}', ""]
            claimed = e.get("source_claimed_label")
            if claimed:
                md += [f'**Quellenetikett (nicht automatisch übernommen):** `{claimed}`', ""]
            context = f'<p><strong>Kontext:</strong> {escape(e["context"])}</p>' if e.get("context") else ""
            claim_html = (f'<p class="meta">Quellenetikett (nicht automatisch übernommen): '
                          f'<code>{escape(claimed)}</code></p>') if claimed else ""
            batch = "new" if e.get("collection_batch") else "baseline"
            cards.append(f'''<article id="{escape(e['id'])}" data-origin="{escape(e['origin'])}" data-assessment="{escape(e['assessment'])}" data-setting="{escape(e['setting'])}" data-basis="{escape(e['label_basis'])}" data-batch="{batch}">
<h3><a href="#{escape(e['id'])}">{escape(e['id'])}</a></h3><p class="meta">{ORIGINS[e['origin']]} · {ASSESSMENTS[e['assessment']]}</p>
<p class="meta">{SETTINGS[e['setting']]} · {DIALOGUE_STATUSES[e['dialogue_status']]}<br>{LABEL_BASES[e['label_basis']]}</p>{claim_html}
{context}<p><strong>A:</strong> {escape(e['a'])}</p><p><strong>B:</strong> {escape(e['b'])}</p>
<p><strong>Labelvorschlag:</strong> <code>{escape(e['proposed_label'])}</code> · ungeprüft</p>
<p><strong>Begründung:</strong> {escape(e['explanation'])}</p>
<p class="meta">Quelle: {source_links(e['source_ids'], sources, html=True)}<br>{escape(e['source_locator'])}</p></article>''')
        sections.append(f'''<section data-scope="{scope}"><h2>{escape(p['name'])}</h2>
<p class="meta"><code>{escape(p['id'])}</code> · {scope_label} · {escape(p['kind'])}</p>
<p>{escape(p['definition'])}</p><p class="caution"><strong>Abgrenzung:</strong> {escape(p['caution'])}</p>
{''.join(cards)}</section>''')
    source_rows = []
    md += ["## Quellen und Rechte", "", "Bearbeitungen sind keine unveränderten Zitate. Quellenkritik und Labelprüfung bleiben erforderlich.", ""]
    for key, s in sources.items():
        link = source_links([key], sources)
        md += [f'- {link}: {s["title"]}. {s["authors"]}. Abruf: {s["retrieved_at"][:10]}. {s["license"]}']
        source_rows.append(f'<li>{source_links([key], sources, html=True)}: {escape(s["title"])}. '
                           f'{escape(s["authors"])}. Abruf: {escape(s["retrieved_at"][:10])}. {escape(s["license"])}</li>')
    origin_options = ''.join(f'<option value="{k}">{v}</option>' for k, v in ORIGINS.items())
    assessment_options = ''.join(f'<option value="{k}">{v}</option>' for k, v in ASSESSMENTS.items())
    setting_options = ''.join(f'<option value="{k}">{v}</option>' for k, v in SETTINGS.items())
    basis_options = ''.join(f'<option value="{k}">{v}</option>' for k, v in LABEL_BASES.items())
    page = '''<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Deutsche Fehlschluss-Beispiele</title>
<style>
:root{color-scheme:light dark;font:17px/1.6 system-ui,sans-serif}body{max-width:1000px;margin:0 auto;padding:24px}
a{color:#428fe8}h1,h2,h3{line-height:1.25}h2{margin-top:0}section{margin:35px 0;padding-top:22px;border-top:2px solid #888}
article{border:1px solid #8888;border-radius:10px;padding:18px;margin:18px 0}article p:last-child{margin-bottom:0}
.meta{font-size:.87rem;opacity:.85}code{font-size:.9em}.caution,.notice{border-left:4px solid #be8a28;padding:10px 16px;background:#aa881112}
.filters{position:sticky;top:0;background:Canvas;border:1px solid #8888;padding:12px;display:flex;gap:10px;flex-wrap:wrap;z-index:1}
label{display:flex;flex-direction:column;font-size:.85rem}input,select{font:inherit;padding:7px;max-width:100%}input{min-width:210px}
[hidden]{display:none!important}details{overflow-wrap:anywhere}li{margin:10px 0}
</style></head><body>
<h1>Deutsche Fehlschluss-Beispiele</h1><p>__SUMMARY__</p>
<p class="notice"><strong>Zur Durchsicht, kein Goldstandard.</strong> Alle Labels sind ungeprüfte Vorschläge.
Alle A/B-Texte sind bearbeitet oder neu erstellt – keine wörtlichen Quellenauszüge. Lehrdialoge, echte schriftliche Forumswechsel
und politische Redepassagen sind getrennt markiert. Auch transkriptgeprüfte Reden sind nicht audioverifiziert.
Bewertet wird B im angegebenen Kontext, nicht die Person. Eine Quelle belegt nicht automatisch jede redaktionelle Bewertung.</p>
<p><a href="catalog.json">Strukturierte Daten</a> · <a href="examples.md">Markdown</a> · <a href="README.md">Methodik</a> · <a href="sources.json">Quellenmetadaten</a> · <a href="discovery.html">Neue ungeprüfte Suchfunde</a></p>
<p><button type="button" data-preset="new">Neue Recherche</button> <button type="button" data-preset="forums">Echte Forumswechsel</button>
<button type="button" data-preset="speeches">Politische Redepassagen</button> <button type="button" data-preset="disputed">Bestrittene Quellenlabels</button>
<button type="button" data-preset="all">Alle zeigen</button></p>
<div class="filters">
<label>Suche<input id="search" type="search" placeholder="Label, Beispiel, Erklärung …"></label>
<label>Umfang<select id="scope"><option value="">Alle Muster</option value="repo">Sieben Repo-Labels</option><option value="extended">Erweiterungen</option></select></label>
<label>Herkunft<select id="origin"><option value="">Alle Herkünfte</option>__ORIGIN_OPTIONS__</select></label>
<label>Bewertung<select id="assessment"><option value="">Alle Bewertungen</option>__ASSESSMENT_OPTIONS__</select></label>
<label>Material<select id="setting"><option value="">Alle Materialarten</option><option value="political_speech">Alle politischen Äußerungen</option>__SETTING_OPTIONS__</select></label>
<label>Einordnung<select id="basis"><option value="">Alle Einordnungen</option>__BASIS_OPTIONS__</select></label>
<label>Sammlung<select id="batch"><option value="">Gesamte Sammlung</option><option value="new">Neue Tiefenrecherche (__NEW_COUNT__)</option><option value="baseline">Erste Sammlung (__BASELINE_COUNT__)</option></select></label>
</div><p id="count" role="status" aria-live="polite"></p>
<main>__SECTIONS__</main><p id="empty" hidden>Keine passenden Beispiele gefunden.</p>
<details><summary>Quellen, Attribution und Rechtehinweise</summary><ul>__SOURCES__</ul></details>
<noscript>JavaScript ist deaktiviert. Alle Beispiele sind unten lesbar; nur die Filter benötigen JavaScript.</noscript>
<script>
const fields = ['search','scope','origin','assessment','setting','basis','batch'].map(id => document.getElementById(id));
const sections = [...document.querySelectorAll('main section')];
function filter() {
  const [query, scope, origin, assessment, setting, basis, batch] = fields.map(el => el.value.toLocaleLowerCase('de'));
  let count = 0;
  for (const section of sections) {
    let shown = 0;
    const heading = section.querySelector('h2').textContent.toLocaleLowerCase('de');
    for (const card of section.querySelectorAll('article')) {
      const text = heading + ' ' + card.textContent.toLocaleLowerCase('de');
      const match = (!scope || section.dataset.scope === scope) && (!origin || card.dataset.origin === origin)
        && (!assessment || card.dataset.assessment === assessment) && (!query || text.includes(query))
        && (!setting || card.dataset.setting === setting || (setting === 'political_speech' && card.dataset.setting.endsWith('political_speech')))
        && (!basis || card.dataset.basis === basis) && (!batch || card.dataset.batch === batch);
      card.hidden = !match;
      if (match) shown++;
    }
    section.hidden = !shown;
    count += shown;
  }
  document.getElementById('count').textContent = count + ' Beispiele angezeigt';
  document.getElementById('empty').hidden = count !== 0;
}
fields.forEach(el => el.addEventListener('input', filter));
const params = new URLSearchParams(location.search);
fields.forEach(el => { if (params.has(el.id)) el.value = params.get(el.id); });
document.querySelectorAll('[data-preset]').forEach(button => button.addEventListener('click', () => {
  fields.forEach(el => { el.value = ''; });
  const preset = button.dataset.preset;
  if (preset === 'new') document.getElementById('batch').value = 'new';
  if (preset === 'forums') document.getElementById('setting').value = 'forum_exchange';
  if (preset === 'speeches') document.getElementById('setting').value = 'political_speech';
  if (preset === 'disputed') document.getElementById('basis').value = 'editorial_disagreement';
  filter();
}));
filter();
</script></body></html>
'''
    for key, value in {"SUMMARY": escape(summary), "ORIGIN_OPTIONS": origin_options,
                       "ASSESSMENT_OPTIONS": assessment_options, "SETTING_OPTIONS": setting_options,
                       "BASIS_OPTIONS": basis_options,
                       "NEW_COUNT": str(sum(bool(e.get("collection_batch")) for e in examples)),
                       "BASELINE_COUNT": str(sum(not e.get("collection_batch") for e in examples)),
                       "SECTIONS": ''.join(sections),
                       "SOURCES": ''.join(source_rows)}.items():
        page = page.replace(f"__{key}__", value)
    return {"examples.md": "\n".join(md) + "\n", "index.html": page}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if generated files are stale")
    args = parser.parse_args()
    catalog = json.loads((DIRECTORY / "catalog.json").read_text(encoding="utf-8"))
    sources = json.loads((DIRECTORY / catalog["sources_file"]).read_text(encoding="utf-8"))
    validate(catalog, sources)
    for name, text in render(catalog, sources).items():
        path = DIRECTORY / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                raise SystemExit(f"Stale generated file: {path.relative_to(ROOT)}")
        else:
            path.write_text(text, encoding="utf-8")
            print(path.relative_to(ROOT))
    print("Catalog valid; all seven existing fallacy labels covered.")


if __name__ == "__main__":
    main()
