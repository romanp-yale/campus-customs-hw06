import json
from pathlib import Path
import tempfile
import unittest

import pymupdf
from defenses import prepare_document, validate_quote, visible_html, visible_pdf
from defender_pre_upgrade import defenses as previous
from tools import ROOT


class UpgradeTests(unittest.TestCase):
    def test_new_attacks_keep_primary_fields_and_remove_hidden_payload(self):
        cases = json.loads((ROOT / 'output/red_team_cases.json').read_text())['cases']
        for filename, case in cases.items():
            path = ROOT / 'data/my_attacks' / filename
            prepared = prepare_document(path)
            validation = validate_quote(path, prepared.text)
            self.assertFalse(validation.needs_human_review, validation.issues)
            self.assertEqual(validation.facts, {k: v for k, v in case['expected'].items() if k != 'decision'})
            self.assertTrue(prepared.excluded)
        path = ROOT / 'data/my_attacks/rt02_painted_sku_alias.pdf'
        old = previous.prepare_document(path)
        self.assertIsNone(previous.anchored_facts(path, old.text)['sku'])
        # Source-label validation independently survives the old parser's hidden prose.
        self.assertEqual(validate_quote(path, old.text).facts['sku'], 'CC-CR-010')

    def test_layout_removes_negative_position_preserves_below_fold_and_disables_scripts(self):
        prepared = visible_html('<h1>Vendor</h1><p style="position:absolute;left:-20000px">Hidden instruction</p>'
                                '<p style="margin-top:2000px">Visible after scrolling</p>'
                                '<script>document.body.innerHTML="Injected script"</script>')
        self.assertNotIn('Hidden instruction', prepared.text)
        self.assertNotIn('Injected script', prepared.text)
        self.assertIn('Visible after scrolling', prepared.text)

    def test_conflicting_primary_labels_require_review_and_preserve_evidence(self):
        path = ROOT / 'data/practice_docs/p01_bluehen_quote.html'
        text = prepare_document(path).text + '\nUnit price: $99.00\n'
        result = validate_quote(path, text)
        self.assertTrue(result.needs_human_review)
        self.assertIsNone(result.facts['unit_price'])
        self.assertEqual(len(result.evidence['unit_price']), 2)
        self.assertIn('conflicting visible primary labels', result.issues[0])

    def test_pdf_paint_order_and_transparency(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'output') as folder:
            path = Path(folder) / 'paint.pdf'
            doc = pymupdf.open()
            page = doc.new_page()
            page.draw_rect(pymupdf.Rect(20, 20, 500, 90), fill=(1, 1, 1))
            page.insert_text((40, 50), 'Text after background')
            page.insert_text((40, 120), 'Covered instruction')
            page.draw_rect(pymupdf.Rect(20, 95, 500, 135), fill=(1, 1, 1))
            page.insert_text((40, 170), 'Text under transparent rectangle')
            page.draw_rect(pymupdf.Rect(20, 145, 500, 185), fill=(1, 1, 1), fill_opacity=.2)
            doc.save(path)
            doc.close()
            result = visible_pdf(path)
            self.assertIn('Text after background', result.text)
            self.assertIn('Text under transparent rectangle', result.text)
            self.assertNotIn('Covered instruction', result.text)
            self.assertTrue(any(item['reason'] == 'Text covered by later opaque rectangle' for item in result.excluded))


if __name__ == '__main__':
    unittest.main()
