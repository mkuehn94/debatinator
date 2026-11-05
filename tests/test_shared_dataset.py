"""Shared schema/review tests run offline, including on a clone without data/."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('shared_dataset', ROOT / 'scripts/build-shared-dataset.py')
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)


class SharedDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = {key: json.loads((ROOT / path).read_text()) for key, path in shared.INPUTS.items()}

    def build(self, **overrides):
        data = {**self.inputs, **overrides}
        return shared.assemble(data['fixtures'], data['catalog'], data['mm_index'], data['reviews'],
                               catalog_sources=data['catalog_sources'])

    def tiny_translations(self):
        index = self.inputs['mm_index']
        source = copy.deepcopy(index['examples'][0])
        source.update(text_en='Original.', text_de='Übersetzung.', translated_window=None)
        translated = {'batch_id': index['batch_id'], 'source_sha256': index['source_sha256'],
                      'rights': index['rights'], 'sources': index['sources'], 'examples': [source],
                      'contexts': {source['context_id']: {'text_en': 'Original. Context.'}}}
        snapshot = shared.mm_snapshot(translated)
        decisions = {'batch_id': index['batch_id'], 'source_sha256': index['source_sha256'],
                     'decisions': [{'id': source['id'], 'label': 'agree', 'translation': 'not_requested',
                                    'note': 'Alternative category?', 'correction_de': 'Optionale Korrektur'}]}
        return snapshot, decisions, translated

    def test_all_inputs_unified_with_explicit_review_buckets(self):
        rows = self.build()
        self.assertEqual(len(rows), 306)
        self.assertEqual(len({row['id'] for row in rows}), 306)
        counts = {status: sum(row['review']['status'] == status for row in rows) for status in shared.STATUSES}
        self.assertEqual(counts, {'accepted': 107, 'rejected': 4, 'uncertain': 42, 'pending': 153})
        shared.validate_records(rows)

    def test_dekarldent_inputs_labels_and_evidence_preserved(self):
        fixtures = self.inputs['fixtures']
        rows = [row for row in self.build() if row['collection'] == 'dekarldent']
        self.assertEqual(len(rows), 4)
        originals = {case['id']: case for case in fixtures['cases']}
        for row in rows:
            original = originals[row['source']['record_id']]
            self.assertEqual(row['input']['a'], original['a'])
            self.assertEqual(row['input']['b'], original['b'])
            self.assertEqual(row['input']['context_de'], original['context'])
            self.assertEqual(row['label']['project_main'], original['expected_main'])
            self.assertEqual(row['text_kind'], 'caption_based_paraphrase')
            self.assertFalse(row['evidence']['audio_verified'])
            self.assertNotIn('rationale', row['input'])
            self.assertEqual(row['evidence']['rationale'], original['rationale'])

    def test_unconfirmed_fixture_not_silently_accepted(self):
        fixtures = copy.deepcopy(self.inputs['fixtures'])
        fixtures['review']['label_status'] = 'needs_user_review'
        rows = [row for row in self.build(fixtures=fixtures) if row['collection'] == 'dekarldent']
        self.assertTrue(all(row['review']['status'] == 'pending' and row['label']['project_main'] is None for row in rows))

    def test_review_rejections_notes_and_source_labels_not_reinterpreted(self):
        rows = [row for row in self.build() if row['collection'] == 'mm_used']
        decisions = {row['id']: row for row in self.inputs['reviews']['decisions']}
        for row in rows:
            decision = decisions[row['source']['record_id']]
            self.assertEqual(row['review']['status'], shared.DECISIONS[decision['label']])
            self.assertEqual(row['review']['note'], decision['note'])
            self.assertIsNone(row['label']['project_main'])
            self.assertIsNone(row['input'])
            self.assertTrue(row['source']['source_split'])
            self.assertEqual(len(row['source']['group_ids']), 2)
        noted = next(row for row in rows if row['review']['note'] == 'AppealToEmotion')
        self.assertEqual(noted['label']['value'], 'AppealtoAuthority')
        self.assertEqual(noted['review']['status'], 'accepted')
        rejected = next(row for row in rows if row['review']['note'] == 'anekdotische Evidenz')
        self.assertEqual(rejected['review']['status'], 'rejected')
        self.assertNotEqual(rejected['label']['value'], 'sachlich')

    def test_research_including_controls_stays_pending(self):
        rows = [row for row in self.build() if row['collection'] == 'research_catalog']
        self.assertEqual(len(rows), 152)
        self.assertTrue(all(row['review']['status'] == 'pending' for row in rows))
        self.assertTrue(any(row['evidence']['assessment'] == 'not_fallacious' for row in rows))
        catalog = copy.deepcopy(self.inputs['catalog'])
        catalog['patterns'][0]['examples'][0]['review_status'] = 'gold'
        with self.assertRaisesRegex(ValueError, 'explicit user-review'):
            self.build(catalog=catalog)

    def test_source_aliases_have_common_leakage_group(self):
        sources = copy.deepcopy(self.inputs['catalog_sources'])
        catalog = copy.deepcopy(self.inputs['catalog'])
        first, second = catalog['patterns'][0]['examples'][:2]
        sources['alias-one'] = {'canonical_url': 'https://example.org/same-page'}
        sources['alias-two'] = {'canonical_url': 'https://example.org/same-page'}
        first['source_ids'] = ['alias-one']
        second['source_ids'] = ['alias-two']
        rows = self.build(catalog=catalog, catalog_sources=sources)
        a = next(row for row in rows if row['id'] == 'catalog:' + first['id'])
        b = next(row for row in rows if row['id'] == 'catalog:' + second['id'])
        common = set(a['source']['group_ids']) & set(b['source']['group_ids'])
        self.assertTrue(any(group.startswith('catalog:url:') for group in common))

    def test_metadata_has_no_input_text_and_matches_record_schema(self):
        rows = shared.metadata(self.build())
        schema = json.loads((ROOT / 'datasets/schema.json').read_text())
        for row in rows:
            self.assertIsNone(row['input'])
            self.assertEqual(set(row), set(schema['required']))
            self.assertEqual(set(row['review']), set(schema['properties']['review']['required']))
            self.assertRegex(row['source_input_sha256'], r'^[a-f0-9]{64}$')
        shared.validate_records(rows)
        with self.assertRaisesRegex(ValueError, 'missing input'):
            shared.validate_records(rows, require_text=True)

    def test_full_passage_retains_context_without_fabricating_exchange(self):
        snapshot, decisions, translated = self.tiny_translations()
        rows = shared.assemble(self.inputs['fixtures'], self.inputs['catalog'], snapshot, decisions, translated)
        row = next(row for row in rows if row['collection'] == 'mm_used')
        self.assertIsNone(row['input']['a'])
        self.assertIsNone(row['input']['b'])
        self.assertEqual(row['input']['text_de'], 'Übersetzung.')
        self.assertEqual(row['input']['text_en'], 'Original.')
        self.assertEqual(row['input']['context_en'], 'Original. Context.')
        self.assertEqual(row['review']['correction_de'], 'Optionale Korrektur')
        self.assertEqual(row['review']['translation'], 'not_requested')
        shared.validate_records(rows, require_text=True)
        translated['examples'][0]['text_de'] = 'Changed.'
        with self.assertRaisesRegex(ValueError, 'differs from tracked'):
            shared.assemble(self.inputs['fixtures'], self.inputs['catalog'], snapshot, decisions, translated)

    def test_mismatched_missing_duplicate_or_invalid_reviews_rejected(self):
        valid = self.inputs['reviews']
        entry = valid['decisions'][0]
        invalid = [None, dict(valid, batch_id='wrong'), dict(valid, source_sha256='wrong'),
                   dict(valid, decisions=[]), dict(valid, decisions=[entry, entry]),
                   dict(valid, decisions=[dict(entry, id='unknown')]),
                   dict(valid, decisions=[dict(entry, label=['agree'])]),
                   dict(valid, decisions=[dict(entry, translation='auto_verified')]),
                   dict(valid, decisions=[dict(entry, note=None)]),
                   dict(valid, decisions=[dict(entry, correction_de=123)])]
        for payload in invalid:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    self.build(reviews=payload)

    def test_validator_blocks_duplicate_ids_and_accidental_project_mapping(self):
        rows = self.build()
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            shared.validate_records([rows[0], rows[0]])
        row = copy.deepcopy(next(row for row in rows if row['collection'] == 'mm_used'))
        row['label']['project_main'] = 'ad_hominem'
        with self.assertRaisesRegex(ValueError, 'explicit project-taxonomy'):
            shared.validate_records([row])
        row = copy.deepcopy(rows[0])
        row['review']['status'] = 'rejected'
        with self.assertRaisesRegex(ValueError, 'status/decision'):
            shared.validate_records([row])

    def test_shared_html_escapes_untrusted_notes_and_starts_with_accepted_filter(self):
        snapshot, decisions, translated = self.tiny_translations()
        decisions['decisions'][0]['note'] = '<script>alert(1)</script>'
        rows = shared.assemble(self.inputs['fixtures'], self.inputs['catalog'], snapshot, decisions, translated)
        page = shared.render(rows)
        self.assertNotIn('<script>alert(1)</script>', page)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', page)
        self.assertIn('<option value="accepted" selected>', page)
        self.assertNotRegex(page, r'<(?:script|link|img)[^>]+(?:src|href)=["\']https?://')

    def test_tracked_metadata_reproducible_without_private_corpus(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/build-shared-dataset.py'), '--metadata-only', '--check'],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shared.TRANSLATIONS.exists() and (shared.LOCAL / 'all.jsonl').exists(), 'Private shared dataset not installed')
    def test_local_full_outputs_current(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/build-shared-dataset.py'), '--check'],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
