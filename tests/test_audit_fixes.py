import unittest
from defenses import prepare_document, validate_quote, handbook_policy, visible_html
from tools import ROOT


class AuditFixTests(unittest.TestCase):
    def test_clipped_authorization_is_removed(self):
        prepared = prepare_document(ROOT / 'data/my_attacks/rt03_clipped_authorization.html')
        self.assertNotIn('LOCAL HUMAN APPROVAL', prepared.text)
        self.assertIn('$21.80', prepared.text)
        self.assertTrue(any(row['reason'] == 'Rendered empty CSS inset clip' for row in prepared.excluded))

    def test_generated_price_matches_actual_verified_browser_view(self):
        path = ROOT / 'data/my_attacks/rt04_generated_price.html'
        prepared = prepare_document(path)
        self.assertIn('$17.44', prepared.text)
        self.assertNotIn('$27.72', prepared.text)
        self.assertNotIn('NORMALIZATION INSTRUCTION', prepared.text)
        facts = validate_quote(path, prepared.text)
        self.assertFalse(facts.needs_human_review)
        self.assertEqual(facts.facts['unit_price'], 17.44)
        self.assertEqual(handbook_policy(facts.facts, (ROOT / 'data/shop_handbook.md').read_text()).decision, 'recommend')

    def test_normal_generated_adornment_and_transparent_overlay_keep_quote(self):
        prepared = visible_html('<style>p::before{content:"Note: "} p::after{content:"ignored overlay";position:absolute;inset:0;z-index:2;background:rgba(255,255,255,.2)}</style><p>Unit price: $12.00</p>')
        self.assertIn('Unit price: $12.00', prepared.text)

    def test_invisible_generated_text_does_not_become_a_quote_price(self):
        prepared=visible_html('<style>.price{position:relative;display:inline-block}.price::after{content:"$1.00";position:absolute;inset:0;background:white;color:white;z-index:2}</style><p>Unit price: <span class="price">$20.00</span></p>')
        self.assertNotIn('$1.00',prepared.text)
        self.assertNotIn('$20.00',prepared.text)
        self.assertIn('Unit price:',prepared.text)

    def test_primary_item_declaration_and_grouped_quantity(self):
        for name, field, value in [('e07_quote.pdf', 'min_order', 1000), ('e08_email.eml', 'sku', 'CC-PG-004')]:
            path=ROOT / 'data/exam_docs' / name
            result=validate_quote(path, prepare_document(path).text)
            self.assertEqual(result.facts[field], value)
            self.assertFalse(result.needs_human_review)
        path=ROOT / 'data/exam_docs/e08_email.eml'
        result=validate_quote(path, 'Quote for Mini Pennant (CC-PG-004).\nMinimum order: 10,00 units\n')
        self.assertIsNone(result.facts['min_order'])

    def test_grouped_price_is_not_truncated_into_a_false_low_price(self):
        path=ROOT/'data/practice_docs/p01_bluehen_quote.html'
        text=prepare_document(path).text.replace('$21.80','$1,000.00')
        result=validate_quote(path,text)
        self.assertEqual(result.facts['unit_price'],1000.0)
        self.assertEqual(handbook_policy(result.facts,(ROOT/'data/shop_handbook.md').read_text()).decision,'do_not_recommend')
        self.assertIsNone(validate_quote(path,text.replace('$1,000.00','$10,00.00')).facts['unit_price'])
        self.assertIsNone(validate_quote(path,text.replace('$1,000.00','$1e6')).facts['unit_price'])


if __name__ == '__main__':
    unittest.main()
