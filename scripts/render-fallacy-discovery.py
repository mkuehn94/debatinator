#!/usr/bin/env python3
"""Render the unreviewed search queue. Does not change the example catalog."""
import argparse
from html import escape
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "docs/fallacies"


def render(data):
    """Escape all remote text; links are the only external resources."""
    summary = data["summary"]
    names = {row["pattern_id"]: row["name"] for row in data["coverage"]}
    options = ''.join(
        f'<option value="{escape(row["pattern_id"], quote=True)}">'
        f'{escape(row["name"])} ({row["new_leads"]})</option>'
        for row in data["coverage"]
    )
    cards = []
    for lead in data["leads"]:
        url = lead["url"]
        for candidate in [url, *(p["url"] for p in lead.get("reference_parents", []))]:
            if urlsplit(candidate).scheme not in {"https", "http"}:
                raise ValueError(f"Unsafe source URL: {candidate}")
        tags = ' · '.join(names[key] for key in lead["fallacy_search_ids"]) or 'Allgemeine Debatten-/Rhetorik-Suchspur'
        video = lead.get("video_metadata", {})
        views = video.get("view_count_at_search")
        views = max(0, int(views)) if isinstance(views, (int, float)) else 0
        view_label = f'{views:,}'.replace(',', '.') if isinstance(video.get("view_count_at_search"), (int, float)) else 'nicht angegeben'
        video_note = ''
        if video:
            channel = escape(video.get("channel") or 'nicht angegeben')
            video_note = (f'<p><b>Videometadaten:</b> Kanal {channel} · '
                          f'{view_label} Aufrufe laut Suchmetadaten. Nicht angesehen; '
                          'Titel, Echtheit und Veröffentlichungsdatum ungeprüft.</p>')
        retrieved = lead.get("retrieval", {})
        status = str(retrieved.get("status", "not_selected_for_fetch"))
        cached = status == "200" and bool(retrieved.get("cached_text_path"))
        fetch_note = "Seitentext lokal gespeichert" if cached else f"Seitenabruf: {status}"
        query_ids = [d["query_id"] for d in lead["discoveries"]]
        queries = [q["query"] for q in data["queries"] if q["id"] in query_ids]
        references = ''.join(
            '<li><a href="' + escape(parent["url"] + "#" + parent["locator"], quote=True)
            + '" target="_blank" rel="noreferrer noopener">' + escape(parent["url"])
            + '</a> · ' + escape(parent["locator"]) + '</li>'
            for parent in lead.get("reference_parents", [])
        )
        excerpt = lead["search_snippet"] or ('Kein Suchauszug; Videometadaten.' if video else 'Kein Suchauszug; Fund aus Referenzliste.')
        cards.append(
            f'<article id="{escape(lead["id"], quote=True)}" '
            f'data-patterns="{escape(" ".join(lead["fallacy_search_ids"]), quote=True)}" '
            f'data-format="{escape(lead["format_hint"], quote=True)}" '
            f'data-cached="{str(cached).lower()}" data-views="{views}">'
            f'<small>{escape(lead["id"])} · {escape(lead["format_hint"])} · '
            f'{escape(fetch_note)}</small>'
            f'<h2><a href="{escape(url, quote=True)}" target="_blank" rel="noreferrer noopener">'
            f'{escape(lead["title"])}</a></h2>'
            f'<p class="url">{escape(url)}</p>'
            f'<p><b>Suchauszug, ungeprüft:</b> '
            f'{escape(excerpt)}</p>'
            f'{video_note}'
            f'<p><b>Gesucht unter:</b> {escape(tags)}</p>'
            f'<details><summary>Suchanfragen ({len(queries)})</summary><ul>'
            + ''.join(f'<li>{escape(q)}</li>' for q in queries)
            + '</ul></details>'
            + ('<details><summary>Referenzpfad</summary><ul>' + references + '</ul></details>' if references else '')
            + '</article>'
        )
    coverage = ''.join(
        f'<tr><td>{escape(row["name"])}</td><td>{row["queries_attempted"]}</td>'
        f'<td>{row["new_leads"]}</td></tr>' for row in data["coverage"]
    )
    return '''<!doctype html>
<html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Debatinator – ungeprüfte Suchfunde</title>
<style>
body{font:16px/1.5 system-ui,sans-serif;max-width:1080px;margin:2rem auto;padding:0 1rem;color:#17212e;background:#f5f7fa}
a{color:#1459a0}h1{line-height:1.2}h2{font-size:1.1rem;margin:.5rem 0}p{margin:.5rem 0}
.notice{padding:1rem;background:#fff3cc;border-left:5px solid #c38b00}
.filters{position:sticky;top:0;background:#f5f7fa;padding:1rem 0;display:flex;gap:.5rem;flex-wrap:wrap}
input,select{font:inherit;padding:.4rem;max-width:100%}input{flex:1;min-width:200px}
article{background:white;border:1px solid #d6dfe8;border-radius:8px;padding:1rem;margin:1rem 0;overflow-wrap:anywhere}
small,.url{color:#526071}.url{font-size:.85rem}table{border-collapse:collapse}td,th{padding:.3rem 1rem;text-align:left;border-bottom:1px solid #ddd}
[hidden]{display:none!important}
</style>
<h1>Ungeprüfte Suchfunde</h1>
<p><a href="index.html">Zur Beispielsammlung</a> · <a href="discovery.json">Rohdaten</a> · <a href="discovery_queries.json">Suchplan</a></p>
''' + (
        f'<p><b>{summary["new_unique_leads"]} neue URLs</b> · {summary["hosts"]} Hosts · '
        f'{summary["queries_attempted"]} Suchanfragen · {summary["patterns_searched"]} Muster gesucht</p>'
    ) + '''<p class="notice"><b>Recherchewarteschlange, keine bewerteten Beispiele.</b>
Typen sind Suchabsichten, keine Annotationen. Treffer können Definitionen, Lehrbeispiele, legitime Argumente oder bloße Vorwürfe sein.
Keine Debattenstelle, kein Vorwurf, keine Popularität verifiziert. Suchauszüge können irreführen. Zusätzlich wurden Referenzlisten deutscher und englischer Themenartikel verfolgt.
Auch „Seitentext gespeichert“ bedeutet nicht „inhaltlich bestätigt“. Formatangaben sind URL-Heuristiken.</p>
<details><summary>Abdeckung und Lücken pro Muster</summary>
<p>Mehrfach zugeordnete URLs zählen pro Suchmuster. Null Treffer bleibt sichtbare Lücke.</p>
<table><tr><th>Muster</th><th>Suchanfragen</th><th>Neue URLs</th></tr>''' + coverage + '''</table></details>
<div class="filters">
<input id="search" type="search" placeholder="Titel, Suchauszug, URL, Debatte …" aria-label="Suche">
<select id="pattern" aria-label="Suchmuster"><option value="">Alle Suchmuster</option>''' + options + '''</select>
<select id="format" aria-label="URL-Format"><option value="">Alle URL-Formate</option><option value="forum">Forum-Hinweis</option><option value="video">Video-Hinweis</option><option value="page">Sonstige Seite</option></select>
<select id="fetch" aria-label="Seitenabruf"><option value="">Alle Abrufe</option><option value="true">Text lokal gespeichert</option><option value="false">Kein Text gespeichert</option></select>
<select id="sort" aria-label="Sortierung"><option value="default">Recherche-Reihenfolge</option><option value="views">Video-Aufrufe ↓ (Suchmetadaten)</option></select>
</div>
<p id="count" aria-live="polite"></p>
<main>''' + '\n'.join(cards) + '''</main>
<script>
const cards = [...document.querySelectorAll('article')];
const inputs = ['search','pattern','format','fetch'].map(id => document.getElementById(id));
const sort = document.getElementById('sort');
function filter() {
  const [text,pattern,format,cached] = inputs.map(el => el.value);
  let shown = 0;
  for (const card of cards) {
    card.hidden = !((!text || card.textContent.toLocaleLowerCase().includes(text.toLocaleLowerCase()))
      && (!pattern || card.dataset.patterns.split(' ').includes(pattern))
      && (!format || card.dataset.format === format)
      && (!cached || card.dataset.cached === cached));
    if (!card.hidden) shown++;
  }
  const ordered = sort.value === 'views' ? [...cards].sort((a,b) => Number(b.dataset.views) - Number(a.dataset.views)) : cards;
  for (const card of ordered) document.querySelector('main').appendChild(card);
  document.getElementById('count').textContent = `${shown} / ${cards.length} Suchfunde sichtbar`;
}
sort.addEventListener('input', filter);
inputs.forEach(el => el.addEventListener('input', filter));
filter();
</script></html>
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = json.loads((DIRECTORY / "discovery.json").read_text(encoding="utf-8"))
    content = render(data)
    target = DIRECTORY / "discovery.html"
    if args.check:
        if target.read_text(encoding="utf-8") != content:
            raise SystemExit("Stale discovery.html; run scripts/render-fallacy-discovery.py")
    else:
        target.write_text(content, encoding="utf-8")
    print(f'{"Checked" if args.check else "Rendered"}: {target.relative_to(ROOT)}')


if __name__ == "__main__":
    main()
