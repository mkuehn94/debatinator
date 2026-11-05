#!/usr/bin/env python3
"""Build shared review-aware dataset; imported text stays under ignored data/."""
import argparse
from collections import Counter
from hashlib import sha256
from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'datasets'
LOCAL = ROOT / 'data/datasets/shared'
TRANSLATIONS = ROOT / 'data/datasets/translation_review/dataset.json'
STATUSES = ('accepted', 'rejected', 'uncertain', 'pending')
TRANSLATION_STATES = ('not_requested', 'pending', 'faithful', 'revise', 'uncertain')
DECISIONS = {'agree': 'accepted', 'disagree': 'rejected', 'uncertain': 'uncertain', 'pending': 'pending'}
INPUTS = {
    'fixtures': 'eval/fixtures/debate_cases.json',
    'catalog': 'docs/fallacies/catalog.json',
    'catalog_sources': 'docs/fallacies/sources.json',
    'mm_index': 'datasets/inputs/mm_used.json',
    'reviews': 'datasets/reviews/mm_used.json',
}


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def fingerprint(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def jsonl(records):
    return ''.join(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n' for record in records)


def passage_input(record, contexts):
    return {'a': None, 'b': None, 'context_de': None,
            'text_de': record['text_de'], 'text_en': record['text_en'],
            'context_en': contexts[record['context_id']]['text_en'],
            'translated_window': record.get('translated_window')}


def mm_snapshot(data):
    """Freeze identity/provenance and content hashes, never imported text."""
    keys = ['id', 'source_case_id', 'source_row_index', 'context_id', 'debate_id', 'source_split',
            'source_label', 'source_subcategory', 'source_span_candidates_en',
            'source_audio_begin_seconds', 'source_audio_end_seconds', 'translation_method',
            'translation_notes', 'review_hints']
    return {'schema_version': 1, 'batch_id': data['batch_id'], 'source_sha256': data['source_sha256'],
            'rights': data['rights'], 'sources': data['sources'],
            'examples': [{**{key: record[key] for key in keys},
                          'source_input_sha256': fingerprint(passage_input(record, data['contexts']))}
                         for record in data['examples']]}


def validated_reviews(index, payload):
    if (not isinstance(payload, dict) or payload.get('batch_id') != index['batch_id']
            or payload.get('source_sha256') != index['source_sha256']
            or not isinstance(payload.get('decisions'), list)):
        raise ValueError('Review batch/source identity mismatch')
    ids = {record['id'] for record in index['examples']}
    decisions = {}
    for entry in payload['decisions']:
        if (not isinstance(entry, dict) or not isinstance(entry.get('id'), str)
                or entry['id'] not in ids or entry['id'] in decisions
                or not isinstance(entry.get('label'), str) or entry['label'] not in DECISIONS
                or entry.get('translation', 'not_requested') not in TRANSLATION_STATES
                or not isinstance(entry.get('note'), str)
                or 'correction_de' not in entry
                or not (entry['correction_de'] is None or isinstance(entry['correction_de'], str))):
            raise ValueError('Invalid review decision or duplicate/unknown ID')
        decisions[entry['id']] = entry
    if set(decisions) != ids:
        raise ValueError('Review export must cover every indexed passage, including pending entries')
    return decisions


def record(identifier, collection, kind, text_kind, label, review, source, evidence, content, digest=None):
    return {'schema_version': 1, 'id': identifier, 'collection': collection, 'language': 'de',
            'input_kind': kind, 'text_kind': text_kind, 'label': label, 'review': review,
            'source': source, 'evidence': evidence, 'source_input_sha256': digest or fingerprint(content),
            'input': content}


def assemble(fixtures, catalog, index, reviews, translated=None, catalog_sources=None):
    """One schema, not one forced taxonomy. Only explicit agreement is accepted."""
    records = []
    for case in fixtures['cases']:
        confirmed = fixtures['review']['label_status'] == 'user_confirmed'
        content = {'a': case['a'], 'b': case['b'], 'context_de': case.get('context'),
                   'text_de': None, 'text_en': None, 'context_en': None, 'translated_window': None}
        records.append(record(
            'dekarldent:' + case['id'], 'dekarldent', 'exchange', fixtures['text_kind'],
            {'namespace': 'debinator_main', 'value': case['expected_main'], 'subcategory': None,
             'project_main': case['expected_main'] if confirmed else None},
            {'status': 'accepted' if confirmed else 'pending', 'decision': 'agree' if confirmed else 'pending',
             'note': '', 'translation': 'not_applicable', 'correction_de': None},
            {'record_id': case['id'], 'collection_file': INPUTS['fixtures'],
             'metadata_file': INPUTS['fixtures'] + '#sources', 'source_ids': [case['source_id']],
             'source_split': None, 'group_ids': [case['source_id']]},
            {**fixtures['review'], **{key: value for key, value in case.items()
                                     if key not in ('id', 'a', 'b', 'context', 'expected_main')}}, content))

    decisions = validated_reviews(index, reviews)
    local = {}
    if translated is not None:
        snapshot = mm_snapshot(translated)
        if snapshot != index:
            raise ValueError('Local translation content/provenance differs from tracked MM snapshot')
        local = {row['id']: row for row in translated['examples']}
    for row in index['examples']:
        decision = decisions[row['id']]
        content = passage_input(local[row['id']], translated['contexts']) if translated is not None else None
        records.append(record(
            'mm_used:' + row['source_case_id'], 'mm_used', 'passage', 'assistant_translated_snippet',
            {'namespace': 'mm_used', 'value': row['source_label'], 'subcategory': row['source_subcategory'],
             'project_main': None},
            {'status': DECISIONS[decision['label']], 'decision': decision['label'], 'note': decision['note'],
             'translation': decision.get('translation', 'not_requested'), 'correction_de': decision['correction_de']},
            {'record_id': row['id'], 'collection_file': 'data/datasets/translation_review/dataset.json',
             'metadata_file': INPUTS['mm_index'] + '#sources', 'source_ids': ['mm_used'],
             'source_sha256': index['source_sha256'], 'source_split': row['source_split'],
             'group_ids': ['mm_used:debate:' + row['debate_id'], 'mm_used:context:' + row['context_id']]},
            {'audio_verified': False, **{key: value for key, value in row.items() if key not in
             ('id', 'source_label', 'source_subcategory', 'source_input_sha256')}},
            content, row['source_input_sha256']))

    for pattern in catalog['patterns']:
        for example in pattern['examples']:
            if example['review_status'] != 'needs_user_review':
                raise ValueError('Catalog promotion requires explicit user-review adapter')
            content = {'a': example['a'], 'b': example['b'], 'context_de': example.get('context'),
                       'text_de': None, 'text_en': None, 'context_en': None, 'translated_window': None}
            groups = ['catalog:source:' + key for key in example['source_ids']]
            if catalog_sources is not None:
                for source_id in example['source_ids']:
                    source = catalog_sources[source_id]
                    url = source.get('canonical_url') or source['url']
                    groups.append('catalog:url:' + sha256(url.encode()).hexdigest())
                groups = sorted(set(groups))
            if example.get('near_duplicate_group'):
                groups.append('catalog:duplicate:' + example['near_duplicate_group'])
            records.append(record(
                'catalog:' + example['id'], 'research_catalog', 'exchange', 'editorial_a_b',
                {'namespace': 'fallacy_catalog', 'value': example['proposed_label'], 'subcategory': None,
                 'project_main': None},
                {'status': 'pending', 'decision': 'pending', 'note': '',
                 'translation': 'not_applicable', 'correction_de': None},
                {'record_id': example['id'], 'collection_file': INPUTS['catalog'],
                 'metadata_file': INPUTS['catalog_sources'], 'source_ids': example['source_ids'],
                 'source_split': None, 'group_ids': groups},
                {key: value for key, value in example.items() if key not in ('id', 'a', 'b', 'context')}, content))
    records.sort(key=lambda item: item['id'])
    validate_records(records, require_text=translated is not None)
    return records


def validate_records(records, require_text=False):
    ids = set()
    for row in records:
        if row['id'] in ids:
            raise ValueError('Duplicate shared record ID')
        ids.add(row['id'])
        if row['review']['status'] != DECISIONS.get(row['review']['decision']):
            raise ValueError('Review status/decision mismatch')
        if row['label']['project_main'] is not None and (
                row['label']['namespace'] != 'debinator_main' or row['review']['status'] != 'accepted'):
            raise ValueError('Project label requires explicit project-taxonomy confirmation')
        if not row['source']['group_ids']:
            raise ValueError('Missing source/leakage group')
        digest = row['source_input_sha256']
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('Invalid input fingerprint')
        content = row['input']
        if content is None:
            if require_text:
                raise ValueError('Full dataset cannot contain missing input')
            continue
        if fingerprint(content) != row['source_input_sha256']:
            raise ValueError('Input content fingerprint mismatch')
        if row['input_kind'] == 'passage':
            if content['a'] is not None or content['b'] is not None or not content['text_de']:
                raise ValueError('Passage must not invent an A/B exchange')
        elif row['input_kind'] == 'exchange':
            if not content['a'] or not content['b']:
                raise ValueError('Exchange needs both A and B')
        else:
            raise ValueError('Unknown input kind')


def metadata(records):
    return [{**row, 'input': None} for row in records]


def manifest(records, input_hashes):
    return {'schema_version': 1, 'purpose': 'Shared review-aware German debate-pattern dataset; not a gold benchmark.',
            'counts': {'all': len(records), 'by_status': {key: sum(r['review']['status'] == key for r in records) for key in STATUSES},
                       'by_collection': dict(sorted(Counter(r['collection'] for r in records).items()))},
            'input_sha256': input_hashes,
            'rights': 'Mixed source-specific rights; no blanket dataset license. MM-USED text stays local pending upstream license clarification.',
            'partitions': 'Review buckets only, not train/test splits. Preserve source_split and group_ids when designing evaluation.',
            'labels': 'Namespaced source labels. Only Dekarldent fixtures have confirmed project_main labels. Agreement is not audio verification.',
            'text_policy': 'Tracked index has input=null. Full inputs and contexts are generated only under ignored data/datasets/shared/.',
            'local_directory': 'data/datasets/shared'}


def render(records):
    cards = []
    for row in records:
        h = lambda value: escape(str(value), quote=True)
        text = row['input']
        body = (f'<p><b>A:</b> {h(text["a"])}</p><p><b>B:</b> {h(text["b"])}</p>'
                if row['input_kind'] == 'exchange' else f'<p><b>DE:</b> {h(text["text_de"])}</p>')
        context = ''.join(f'<details><summary>{h(key)}</summary><p>{h(text[key])}</p></details>'
                          for key in ('context_de', 'text_en', 'context_en') if text.get(key))
        if text.get('translated_window'):
            context += ('<details><summary>Deutsches Kontextfenster (gekürzt)</summary><p>'
                        + h(text['translated_window']['text_de']) + '</p></details>')
        cards.append(f'<article data-status="{h(row["review"]["status"])}"><h2>{h(row["id"])}</h2>'
                     f'<p>{h(row["review"]["status"])} · {h(row["label"]["namespace"])}: {h(row["label"]["value"])}'
                     f' / {h(row["label"]["subcategory"] or "")}</p>{body}{context}'
                     f'<p><b>Notiz:</b> {h(row["review"]["note"])}</p>'
                     '<details><summary>Provenienz / Bewertung</summary><pre>'
                     + h(json.dumps({key: value for key, value in row.items() if key != 'input'}, ensure_ascii=False, indent=2))
                     + '</pre></details></article>')
    options = ''.join(f'<option value="{value}"' + (' selected' if value == 'accepted' else '')
                      + f'>{value}</option>' for value in STATUSES)
    return '''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Debatinator – gemeinsamer Datensatz</title><style>
body{font:16px/1.5 system-ui;max-width:1000px;margin:2rem auto;padding:1rem}article{border:1px solid #bbb;padding:1rem;margin:1rem 0}h2{font-size:1rem}p,pre{white-space:pre-wrap;overflow-wrap:anywhere}input,select{font:inherit;padding:.5rem}[hidden]{display:none!important}
</style><h1>Gemeinsamer Datensatz</h1><p>Beschriftungen behalten ihr Quellsystem. „Accepted“ bedeutet Zustimmung zum Label, nicht Audio- oder Faktenprüfung. Keine automatisch erzeugten Trainings-/Testsplits.</p>
<p>Nur Leseansicht. MM-USED-Bewertungen ändern: <a href="../translation_review/index.html">Prüfseite</a>. Entscheidungen danach exportieren und importieren.</p>
<input id="search" type="search" aria-label="Suche" placeholder="Text, ID, Label, Notiz"><select id="status" aria-label="Prüfstatus"><option value="">Alle</option>''' + options + '''</select><p id="count" aria-live="polite"></p>''' + '\n'.join(cards) + '''<script>
const cards=[...document.querySelectorAll('article')];
function filter(){const q=document.getElementById('search').value.toLocaleLowerCase(),s=document.getElementById('status').value;let n=0;for(const c of cards){c.hidden=!!((s&&c.dataset.status!==s)||(q&&!c.textContent.toLocaleLowerCase().includes(q)));if(!c.hidden)n++;}document.getElementById('count').textContent=`${n} / ${cards.length}`;}
for(const id of ['search','status'])document.getElementById(id).addEventListener('input',filter);filter();
</script></html>
'''


def write_or_check(path, text, check):
    if check:
        if not path.exists() or path.read_text(encoding='utf-8') != text:
            raise ValueError(f'Stale or missing {path}; rebuild shared dataset')
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata-only', action='store_true', help='Build/check tracked index without private translated text')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        inputs = {key: json.loads((ROOT / path).read_text(encoding='utf-8')) for key, path in INPUTS.items()}
        translated = None
        if not args.metadata_only:
            if not TRANSLATIONS.exists():
                raise ValueError('Private translations missing. Restore local data/ or use --metadata-only; see datasets/README.md')
            translated = json.loads(TRANSLATIONS.read_text(encoding='utf-8'))
        records = assemble(inputs['fixtures'], inputs['catalog'], inputs['mm_index'], inputs['reviews'],
                           translated, inputs['catalog_sources'])
        hashes = {path: sha256((ROOT / path).read_bytes()).hexdigest() for path in INPUTS.values()}
        summary = manifest(records, hashes)
        outputs = {DIRECTORY / 'index.jsonl': jsonl(metadata(records)), DIRECTORY / 'manifest.json': json_text(summary)}
        if not args.metadata_only:
            outputs[LOCAL / 'all.jsonl'] = jsonl(records)
            for status in STATUSES:
                outputs[LOCAL / f'{status}.jsonl'] = jsonl([r for r in records if r['review']['status'] == status])
            outputs[LOCAL / 'index.html'] = render(records)
            outputs[LOCAL / 'manifest.json'] = json_text(summary)
        for path, text in outputs.items():
            write_or_check(path, text, args.check)
        print(json_text(summary['counts']), end='')
        if args.metadata_only:
            print('Metadata only; private text outputs not built/checked.')
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
