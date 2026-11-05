import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('translation_review', ROOT / 'scripts/build-translation-review.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
DATA = ROOT / 'data/datasets/translation_review'


@unittest.skipUnless(
    all((ROOT / path).exists() for path in [
        'data/datasets/mm_used/cases_en.jsonl', 'data/datasets/mm_used/contexts_en.jsonl',
        'data/datasets/mm_used/translation_pilot_de.jsonl', 'data/datasets/mm_used/manifest.json',
        'data/datasets/translation_review/selection.json',
        'data/datasets/translation_review/translations_de_new.json',
        'data/datasets/translation_review/dataset.json', 'data/datasets/translation_review/index.html']),
    'Private MM-USED corpus/translation files not installed; see datasets/README.md')
class TranslationReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        corpus = ROOT / 'data/datasets/mm_used'
        cls.cases = review.read_jsonl(corpus / 'cases_en.jsonl')
        cls.contexts = review.read_jsonl(corpus / 'contexts_en.jsonl')
        cls.pilot = review.read_jsonl(corpus / 'translation_pilot_de.jsonl')
        cls.selection = json.loads((DATA / 'selection.json').read_text())
        cls.translations = json.loads((DATA / 'translations_de_new.json').read_text())
        cls.manifest = json.loads((corpus / 'manifest.json').read_text())

    def test_frozen_selection_reproducible_and_covers_tu_quoque(self):
        self.assertEqual(self.selection, review.select_cases(self.cases, self.pilot))
        rows = {item['row'] for item in self.selection}
        self.assertEqual(len(rows), 150)
        self.assertEqual(len([case for case in self.cases if case['source_subcategory'] == 'Tu quoque'
                              and case['source_row_index'] in rows]), 15)
        self.assertEqual(len([item for item in self.selection if item['row'] in review.NEXT_ROWS]), 50)
        with patch.object(review, 'NEXT_ROWS', []):
            original = review.select_cases(self.cases, self.pilot)
        self.assertEqual(len(original), 100)
        self.assertTrue({item['row'] for item in original} <= rows)

    def test_bilingual_batch_keeps_source_provenance_unreviewed(self):
        data = review.assemble(self.cases, self.contexts, self.selection, self.translations,
                               self.pilot, self.manifest)
        self.assertEqual(data['counts']['examples'], 150)
        self.assertEqual(data['counts']['debates'], 28)
        self.assertEqual(data['counts']['contexts'], 112)
        self.assertEqual(data['counts']['translated_context_windows'], 12)
        self.assertEqual(data['counts']['neutral_examples'], 0)
        self.assertEqual(data['counts']['user_reviewed'], 0)
        self.assertEqual(sum(data['counts']['source_labels'].values()), 150)
        for record in data['examples']:
            source = next(case for case in self.cases if case['source_row_index'] == record['source_row_index'])
            self.assertEqual(record['text_en'], source['text_en'])
            self.assertEqual(record['source_label'], source['source_label'])
            self.assertEqual(record['review_status'], 'needs_user_review')
            self.assertEqual(record['review'], {'translation': 'not_requested', 'label': 'pending', 'note': ''})
            self.assertEqual(record['translation_method'], 'assistant_translation')

    def test_invalid_selection_or_missing_translation_rejected(self):
        selection = [dict(self.selection[0], en='invented')]
        with self.assertRaisesRegex(ValueError, 'Selection/source mismatch'):
            review.assemble(self.cases, self.contexts, selection, {}, self.pilot, self.manifest)
        with self.assertRaisesRegex(ValueError, 'Missing German translation'):
            review.assemble(self.cases, self.contexts, self.selection[:1], {}, [], self.manifest)

    def test_pilot_german_context_window_and_span_validate(self):
        contexts = {item['id']: item for item in self.contexts}
        case = next(item for item in self.pilot if item['context_de'])
        context = contexts[case['context_id']]
        start, end = case['source_context_char_start'], case['source_context_char_end']
        self.assertEqual(context['text_en'][start:end], case['context_en'])
        self.assertIn(case['text_de'], case['context_de'])

    def test_render_escapes_untrusted_source_and_stays_offline(self):
        data = review.assemble(self.cases, self.contexts, self.selection, self.translations,
                               self.pilot, self.manifest)
        example = data['examples'][0]
        original = example['text_en']
        example['text_en'] = '<script>alert(1)</script>'
        html = review.render(data)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', html)
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertNotRegex(html, r'<(?:script|link)[^>]+\b(?:src|href)=["\']https?://')
        self.assertIn('dataset.json', html)
        example['text_en'] = original

    @unittest.skipUnless(shutil.which('node'), 'Node.js required for browser-script checks')
    def test_label_only_review_and_legacy_import_runtime(self):
        data = review.assemble(self.cases, self.contexts, self.selection, self.translations,
                               self.pilot, self.manifest)
        html = review.render(data)
        self.assertNotIn('<select class="translation">', html)
        self.assertIn('Quellenlabel beurteilt', html)
        script = html.split('<script>', 1)[1].split('</script>', 1)[0]
        # Minimal DOM exercises generated JS, not a separate reimplementation.
        setup = '''
const assert = require('node:assert/strict');
function field(value = '') { return {value, textContent:value, addEventListener(){}}; }
const testCards = ['one','two'].map(id => {
  const fields = {'.label':field('pending'), '.note':field(),
    '.correction':field('Original'), '.original-de':field('Original')};
  return {id, dataset:{translationReview:'not_requested',label:'FalseCause',subtype:'False cause'},
    textContent:'example', hidden:false, querySelector:s => fields[s]};
});
const controls = Object.fromEntries(['search','class','subtype','state','count','export','import'].map(id=>[id,field()]));
const document = {querySelectorAll:s => s === 'article' ? testCards : [], getElementById:id => controls[id]};
'''
        checks = '''
assert.equal(exportReview().decisions[0].translation, 'not_requested');
const old = {batch_id:'mm-used-de-review-100-v1', source_sha256:batch.source_sha256,
  decisions:[{id:'one', translation:'pending', label:'uncertain', note:'Need context', correction_de:null}]};
applyReview(old);
controls.state.value = 'reviewed'; filter();
assert.equal(testCards[0].hidden, false); // Legacy translation pending must not block label review.
assert.equal(testCards[1].hidden, true);
assert.equal(controls.count.textContent, '1 / 2 Beispiele sichtbar');
assert.equal(exportReview().decisions[0].translation, 'pending'); // Preserve legacy metadata.
const current = {batch_id:batch.batch_id, source_sha256:batch.source_sha256,
  decisions:[{id:'two',label:'disagree',note:'Not a fallacy',correction_de:'Korrektur'}]};
applyReview(current);
assert.equal(exportReview().decisions[1].translation, 'not_requested');
assert.equal(exportReview().decisions[1].correction_de, 'Korrektur');
const snapshot = JSON.stringify(exportReview());
const invalid = [
  {...old,batch_id:'unknown'}, {...old,source_sha256:'wrong'},
  {...old,decisions:[{...old.decisions[0],id:'missing'}]},
  {...old,decisions:[old.decisions[0],old.decisions[0]]},
  {...old,decisions:[old.decisions[0],{...old.decisions[0],id:'two',label:'invalid'}]},
  {...old,decisions:[{...old.decisions[0],translation:'invalid'}]}
];
for (const bad of invalid) {
  assert.throws(() => applyReview(bad));
  assert.equal(JSON.stringify(exportReview()), snapshot);
}
applyReview(exportReview());
assert.equal(JSON.stringify(exportReview()), snapshot);
'''
        result = subprocess.run(['node'], input=setup + script + checks, text=True,
                                capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_saved_review_preserves_sources_and_prefills_page(self):
        data = review.assemble(self.cases, self.contexts, self.selection, self.translations,
                               self.pilot, self.manifest)
        originals = [(record['source_label'], record['text_de']) for record in data['examples']]
        payload = review.review_export(data)
        for entry, label in zip(payload['decisions'], ['agree', 'disagree', 'uncertain']):
            entry['label'] = label
        payload['decisions'][0]['note'] = '</textarea><script>alert(1)</script>'
        payload['decisions'][0]['correction_de'] = 'Optionale Korrektur'
        review.apply_review(data, payload)
        self.assertEqual(data['counts']['user_reviewed'], 3)
        self.assertEqual(data['counts']['label_decisions'],
                         {'agree': 1, 'disagree': 1, 'uncertain': 1, 'pending': 147})
        self.assertEqual(data['review_status'], 'partially_label_reviewed')
        self.assertEqual(originals, [(record['source_label'], record['text_de']) for record in data['examples']])
        self.assertEqual(review.review_export(data), payload)
        html = review.render(data)
        self.assertIn('<option value="agree" selected>', html)
        self.assertIn('<option value="disagree" selected>', html)
        self.assertIn('<option value="uncertain" selected>', html)
        self.assertIn('&lt;/textarea&gt;&lt;script&gt;alert(1)&lt;/script&gt;', html)
        self.assertNotIn('</textarea><script>alert(1)</script>', html)
        self.assertIn('rows="4">Optionale Korrektur</textarea>', html)

    def test_invalid_review_rejected_before_any_mutation(self):
        data = review.assemble(self.cases, self.contexts, self.selection, self.translations,
                               self.pilot, self.manifest)
        snapshot = json.dumps(data, sort_keys=True)
        valid = review.review_export(data)
        first = dict(valid['decisions'][0], label='agree')
        for bad in [
            None, {'batch_id': 'wrong'}, dict(valid, source_sha256='wrong'),
            dict(valid, decisions=[first, first]),
            dict(valid, decisions=[first, dict(first, id='unknown')]),
            dict(valid, decisions=[first, dict(valid['decisions'][1], label='invalid')]),
            dict(valid, decisions=[dict(first, note=None)]),
            dict(valid, decisions=[dict(first, correction_de=42)]),
            dict(valid, decisions=[dict(first, translation='invalid')]),
        ]:
            with self.subTest(payload=bad):
                with self.assertRaises(ValueError):
                    review.apply_review(data, bad)
                self.assertEqual(json.dumps(data, sort_keys=True), snapshot)

    def test_review_cli_persists_and_rebuilds_without_losing_decisions(self):
        import sys
        data = review.assemble(self.cases, self.contexts, self.selection, self.translations,
                               self.pilot, self.manifest)
        payload = review.review_export(data)
        payload['decisions'][0]['label'] = 'uncertain'
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for name in ['selection.json', 'translations_de_new.json']:
                shutil.copyfile(DATA / name, folder / name)
            export = folder / 'incoming.json'
            export.write_text(json.dumps(payload))
            command = [sys.executable, str(ROOT / 'scripts/build-translation-review.py'), '--directory', directory]
            result = subprocess.run(command + ['--import-review', str(export)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            saved = (folder / 'review.json').read_bytes()
            generated = (folder / 'dataset.json').read_bytes()
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((folder / 'review.json').read_bytes(), saved)
            self.assertEqual((folder / 'dataset.json').read_bytes(), generated)
            self.assertEqual(json.loads(generated)['counts']['user_reviewed'], 1)
            result = subprocess.run(command + ['--check'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload['source_sha256'] = 'wrong'
            export.write_text(json.dumps(payload))
            result = subprocess.run(command + ['--import-review', str(export)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((folder / 'review.json').read_bytes(), saved)
            self.assertEqual((folder / 'dataset.json').read_bytes(), generated)

    def test_generated_views_current(self):
        data = review.assemble(self.cases, self.contexts, self.selection, self.translations,
                               self.pilot, self.manifest)
        if review.review_file(DATA).exists():
            review.apply_review(data, json.loads(review.review_file(DATA).read_text()))
        self.assertEqual((DATA / 'dataset.json').read_text(),
                         json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        self.assertEqual((DATA / 'index.html').read_text(), review.render(data))


if __name__ == '__main__':
    unittest.main()
