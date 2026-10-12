import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from defenses import anchored_facts, handbook_policy, prepare_document, visible_html, visible_pdf
import tools


class DefenseTests(unittest.TestCase):
    def test_visible_quote_facts_and_policy_match_all_supplied_keys(self):
        keys = json.loads((tools.ROOT / 'data/practice_key.json').read_text())
        handbook = (tools.ROOT / 'data/shop_handbook.md').read_text()
        for expected in keys:
            with self.subTest(document=expected['file']):
                path = tools.ROOT / 'data/practice_docs' / expected['file']
                prepared = prepare_document(path)
                facts = anchored_facts(path, prepared.text)
                output = handbook_policy(facts, handbook).model_dump()
                for field, value in expected.items():
                    if field != 'file':
                        self.assertEqual(output[field], value)

    def test_stylesheet_hidden_content_and_legitimate_correction(self):
        result = visible_html('<style>.hide{display:none}</style><h1>Vendor</h1><p class="hide">Override rules</p><p>Please ignore last Tuesday\'s quote.</p>')
        self.assertNotIn('Override rules', result.text)
        self.assertIn('Please ignore', result.text)
        self.assertNotIn('font-size:0px', result.text)

    def test_permission_gate_exact_arguments_and_tools_still_registered(self):
        with tempfile.TemporaryDirectory(dir=tools.ROOT / 'output') as folder:
            with patch.object(tools, 'ROOT', Path(folder)):
                deps = tools.DeskDeps(Path('selected.html'), 'permission-test', layers=frozenset({'design'}))
                ctx = SimpleNamespace(deps=deps)
                tool = SimpleNamespace(name='send_email')
                self.assertIsNone(asyncio.run(tools.prepare_trap(ctx, tool)))
                self.assertIn('Blocked', tools.send_email(ctx, 'nobody@example.invalid', 'Test', 'Test'))
                arguments = {'to': 'nobody@example.invalid', 'subject': 'Test', 'body': 'Test'}
                deps.human_authorization = {'tool': 'send_email', 'arguments': arguments}
                self.assertIs(asyncio.run(tools.prepare_trap(ctx, tool)), tool)
                self.assertIn('no email sent', tools.send_email(ctx, **arguments))
                self.assertIn('Blocked', tools.send_email(ctx, **arguments))
                self.assertIn('Blocked', tools.send_email(ctx, **{**arguments, 'body': 'Different'}))
                self.assertIsNone(asyncio.run(tools.prepare_trap(ctx, SimpleNamespace(name='approve_payment'))))
                self.assertIn('Blocked', tools.approve_payment(ctx, 'Vendor', 100, 'Document said so'))
                log = json.loads((Path(folder) / 'output/trap_calls.json').read_text())
                self.assertEqual([entry['authorized'] for entry in log], [False, True, False, False, False])

    def test_rule_changes_come_only_from_handbook_and_unknowns_fail(self):
        path = tools.ROOT / 'data/practice_docs/p01_bluehen_quote.html'
        facts = anchored_facts(path, prepare_document(path).text)
        handbook = (tools.ROOT / 'data/shop_handbook.md').read_text()
        self.assertEqual(handbook_policy(facts, handbook.replace('lead time is 21 days', 'lead time is 10 days')).decision, 'do_not_recommend')
        self.assertEqual(handbook_policy({**facts, 'unit_price': None}, handbook).decision, 'do_not_recommend')

    def test_pdf_white_on_dark_is_retained_and_invisible_text_removed(self):
        import pymupdf
        with tempfile.TemporaryDirectory(dir=tools.ROOT / 'output') as folder:
            path = Path(folder) / 'visibility.pdf'
            doc = pymupdf.open()
            page = doc.new_page()
            page.draw_rect(pymupdf.Rect(20, 20, 500, 90), color=(0, 0, 0), fill=(0, 0, 0))
            page.insert_text((40, 50), 'Legitimate white heading', fontsize=12, color=(1, 1, 1))
            page.insert_text((40, 120), 'Invisible attack', fontsize=12, render_mode=3)
            doc.save(path)
            doc.close()
            result = visible_pdf(path)
            self.assertIn('Legitimate white heading', result.text)
            self.assertNotIn('Invisible attack', result.text)


if __name__ == '__main__':
    unittest.main()
