"""Local correctness checks; synthetic fixtures are never added to live usage logs."""
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import json
import asyncio
from unittest.mock import AsyncMock
from pydantic_ai.messages import ModelRequest, SystemPromptPart
from pydantic_ai.models.openai import OpenAIResponsesModel

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent import calculate_usage, cache_settings, IsolatedCacheModel
from models import VendorRecommendation
import tools


class VendorDeskTests(unittest.TestCase):
    def test_cache_configuration_controls(self):
        self.assertEqual(cache_settings('baseline'), {})
        self.assertEqual(cache_settings('with_caching')['openai_prompt_cache_options']['mode'], 'implicit')
        self.assertEqual(cache_settings('without_caching')['openai_prompt_cache_options']['mode'], 'explicit')
        with self.assertRaises(ValueError):
            cache_settings('unknown')

    def test_no_cache_nonce_changes_for_each_model_call(self):
        async def check():
            original = [ModelRequest(parts=[SystemPromptPart('Original handbook')])]
            model = object.__new__(IsolatedCacheModel)
            with patch.object(OpenAIResponsesModel, 'request', new_callable=AsyncMock) as parent:
                await model.request(original, {}, None)
                await model.request(original, {}, None)
                first, second = [call.args for call in parent.await_args_list]
                self.assertNotEqual(first[0][0].parts[0].content, second[0][0].parts[0].content)
                self.assertNotEqual(first[1]['openai_prompt_cache_key'], second[1]['openai_prompt_cache_key'])
                self.assertEqual(first[0][1:], original)
                self.assertEqual(len(original), 1)
        asyncio.run(check())

    def test_supplied_formats_extract(self):
        for filename in ('p01_bluehen_quote.html', 'p05_maplemills_quote.pdf', 'p08_chapelst_email.eml'):
            with self.subTest(filename=filename):
                self.assertIn('CC-', tools.extract_document(tools.ROOT / 'data/practice_docs' / filename))

    def test_reader_opens_only_selected_document(self):
        path = tools.ROOT / 'data/practice_docs/p01_bluehen_quote.html'
        deps = tools.DeskDeps(path.resolve(), 'local-test')
        ctx = SimpleNamespace(deps=deps)
        self.assertIn('Blue Hen', tools.read_document(ctx, str(path)))
        self.assertTrue(deps.read_completed)
        with self.assertRaises(ValueError):
            tools.read_document(ctx, '.env')

    def test_traps_only_record_attempts(self):
        original_root = tools.ROOT
        with tempfile.TemporaryDirectory(dir=original_root / 'output') as folder:
            with patch.object(tools, 'ROOT', Path(folder)):
                ctx = SimpleNamespace(deps=tools.DeskDeps(Path('selected.html'), 'local-test'))
                self.assertIn('no email sent', tools.send_email(ctx, 'nobody@example.invalid', 'Test', 'Test'))
                self.assertIn('no payment approved', tools.approve_payment(ctx, 'Test vendor', 1.0, 'Test'))
                files = [p for p in Path(folder).rglob('*') if p.is_file()]
                self.assertEqual([p.name for p in files], ['trap_calls.json'])
                entries = json.loads(files[0].read_text())
                self.assertEqual([e['tool'] for e in entries], ['send_email', 'approve_payment'])
                self.assertEqual(entries[1]['arguments']['amount'], 1.0)

    def test_cost_partitions_input_without_double_counting(self):
        fixture = [{'usage': {'input_tokens': 1000, 'output_tokens': 100,
                              'input_tokens_details': {'cached_tokens': 600, 'cache_write_tokens': 100}}}]
        # 300 * .10 + 600 * .01 + 100 * .125 + 100 * .50, divided by 1M.
        self.assertEqual(calculate_usage(fixture)['cost_usd'], '0.0000985')
        self.assertIsNone(calculate_usage([])['cost_usd'])
        self.assertIsNone(calculate_usage([{'usage': None}])['input_tokens'])

    def test_unknown_facts_are_nullable(self):
        output = VendorRecommendation(vendor=None, sku=None, unit_price=None,
                                      lead_time_days=None, min_order=None,
                                      decision='do_not_recommend', explanation='Required facts are unknown.')
        self.assertIsNone(output.unit_price)


if __name__ == '__main__':
    unittest.main()
