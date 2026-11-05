"""Accepted-only dataset checks; core tests work without private source text."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
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
        return shared.assemble(data['fixtures'], data['mm_index'], data['reviews'])

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

    def test_only_107_accepted_records_remain(self):
        rows = self.build()
        self.assertEqual(len(rows), 107)
        self.assertEqual(len({row['id'] for row in rows}), 107)
        self.assertEqual(sum(row['collection'] == 'dekarldent' for row in rows), 4)
        self.assertEqual(sum(row['collection'] == 'mm_used' for row in rows), 103)
        self.assertTrue(all(row['review']['status'] == 'accepted' and row['review']['decision'] == 'agree' for row in rows))
        shared.validate_records(rows)

    def test_dekarldent_inputs_labels_and_evidence_preserved(self):
        rows = [row for row in self.build() if row['collection'] == 'dekarldent']
        originals = {case['id']: case for case in self.inputs['fixtures']['cases']}
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

    def test_unconfirmed_fixture_rejected(self):
        fixtures = copy.deepcopy(self.inputs['fixtures'])
        fixtures['review']['label_status'] = 'needs_user_review'
        with self.assertRaisesRegex(ValueError, 'Only user-confirmed'):
            self.build(fixtures=fixtures)

    def test_nonaccepted_reviews_cannot_reenter_dataset(self):
        for label in ['pending', 'uncertain', 'disagree']:
            payload = copy.deepcopy(self.inputs['reviews'])
            payload['decisions'][0]['label'] = label
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, 'Only explicitly accepted'):
                self.build(reviews=payload)

    def test_accepted_notes_source_labels_and_splits_preserved(self):
        rows = [row for row in self.build() if row['collection'] == 'mm_used']
        decisions = {row['id']: row for row in self.inputs['reviews']['decisions']}
        for row in rows:
            decision = decisions[row['source']['record_id']]
            self.assertEqual(row['review']['note'], decision['note'])
            self.assertIsNone(row['label']['project_main'])
            self.assertIsNone(row['input'])
            self.assertTrue(row['source']['source_split'])
            self.assertEqual(len(row['source']['group_ids']), 2)
        noted = next(row for row in rows if row['review']['note'] == 'AppealToEmotion')
        self.assertEqual(noted['label']['value'], 'AppealtoAuthority')
        self.assertEqual(noted['review']['status'], 'accepted')

    def test_metadata_has_no_input_text_and_matches_record_schema(self):
        rows = shared.metadata(self.build())
        schema = json.loads((ROOT / 'datasets/schema.json').read_text())
        for row in rows:
            self.assertIsNone(row['input'])
            self.assertEqual(set(row), set(schema['required']))
            self.assertEqual(set(row['review']), set(schema['properties']['review']['required']))
            self.assertRegex(row['source_input_sha256'], r'^[a-f0-9]{64}$')
        self.assertEqual(schema['properties']['review']['properties']['status'], {'const': 'accepted'})
        shared.validate_records(rows)
        with self.assertRaisesRegex(ValueError, 'missing input'):
            shared.validate_records(rows, require_text=True)

    def test_full_passage_retains_context_without_fabricating_exchange(self):
        snapshot, decisions, translated = self.tiny_translations()
        rows = shared.assemble(self.inputs['fixtures'], snapshot, decisions, translated)
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
            shared.assemble(self.inputs['fixtures'], snapshot, decisions, translated)

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
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                self.build(reviews=payload)

    def test_validator_blocks_duplicates_unaccepted_and_accidental_project_mapping(self):
        rows = self.build()
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            shared.validate_records([rows[0], rows[0]])
        row = copy.deepcopy(next(row for row in rows if row['collection'] == 'mm_used'))
        row['label']['project_main'] = 'ad_hominem'
        with self.assertRaisesRegex(ValueError, 'explicit project-taxonomy'):
            shared.validate_records([row])
        row = copy.deepcopy(rows[0])
        row['review']['status'] = 'uncertain'
        with self.assertRaisesRegex(ValueError, 'unaccepted record'):
            shared.validate_records([row])

    def test_shared_html_escapes_notes_and_has_no_review_queue(self):
        snapshot, decisions, translated = self.tiny_translations()
        decisions['decisions'][0]['note'] = '<script>alert(1)</script>'
        rows = shared.assemble(self.inputs['fixtures'], snapshot, decisions, translated)
        page = shared.render(rows)
        self.assertNotIn('<script>alert(1)</script>', page)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', page)
        self.assertNotIn('id="status"', page)
        self.assertNotIn('translation_review/index.html', page)
        self.assertEqual(page.count('<article '), len(rows))
        self.assertNotRegex(page, r'<(?:script|link|img)[^>]+(?:src|href)=["\']https?://')

    @unittest.skipUnless(shutil.which('node'), 'Node.js required for reader runtime test')
    def test_reader_search_runtime(self):
        snapshot, decisions, translated = self.tiny_translations()
        page = shared.render(shared.assemble(self.inputs['fixtures'], snapshot, decisions, translated))
        script = page.split('<script>', 1)[1].split('</script>', 1)[0]
        setup = '''
const assert=require('node:assert/strict');
const entries=[{textContent:'Alpha'},{textContent:'Beta'}];
const search={value:'',addEventListener(){}},count={textContent:''};
const document={querySelectorAll:()=>entries,getElementById:id=>({search,count})[id]};
'''
        checks = '''
assert.equal(count.textContent,'2 / 2');
search.value='ALPHA';filter();assert.equal(count.textContent,'1 / 2');
assert.equal(entries[0].hidden,false);assert.equal(entries[1].hidden,true);
search.value='missing';filter();assert.equal(count.textContent,'0 / 2');
'''
        result = subprocess.run(['node'], input=setup + script + checks, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_tracked_metadata_reproducible_without_private_corpus(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/build-shared-dataset.py'), '--metadata-only', '--check'],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shared.TRANSLATIONS.exists() and (shared.LOCAL / 'accepted.jsonl').exists(), 'Private shared dataset not installed')
    def test_local_full_outputs_current_and_discarded_buckets_absent(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/build-shared-dataset.py'), '--check'],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in ['all.jsonl', 'rejected.jsonl', 'uncertain.jsonl', 'pending.jsonl']:
            self.assertFalse((shared.LOCAL / name).exists(), name)


if __name__ == '__main__':
    unittest.main()
