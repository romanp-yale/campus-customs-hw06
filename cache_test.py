"""Run all twelve documents in both real-API cache configurations, sequentially."""
import asyncio
import json
from pathlib import Path
from uuid import uuid4

from agent import calculate_usage, execute
from tools import ROOT, timestamp


def call_entry(run: dict, response: dict, index: int) -> dict:
    usage = response.get('usage') or {}
    details = usage.get('input_tokens_details') or {}
    cache_reported = 'cached_tokens' in details
    gateway_status = response.get('portkey_cache_status')
    replay = gateway_status is not None and 'HIT' in gateway_status.upper()
    measured = calculate_usage([response])
    return {'configuration': run['configuration'], 'document': Path(run['document']).name,
            'run_id': run['run_id'], 'call_number': index, **response,
            **{key: measured[key] for key in ('input_tokens', 'cached_input_tokens', 'cache_write_tokens', 'output_tokens', 'total_tokens', 'cost_usd')},
            'cached_count_explicitly_reported': cache_reported,
            'provider_response_not_gateway_replay': not replay,
            'no_cache_verified': cache_reported and details['cached_tokens'] == 0 and not replay
                                 and response['http_status'] == 200,
            'cache_hit_verified': cache_reported and details['cached_tokens'] > 0 and not replay
                                  and response['http_status'] == 200}


async def main():
    destination = ROOT / 'output/cache_test.json'
    files = sorted((ROOT / 'data/practice_docs').iterdir())
    if len(files) != 12:
        raise ValueError('Expected exactly 12 practice documents')
    experiment = {'experiment_id': str(uuid4()), 'started_at': timestamp(),
                  'model': 'gpt-6-luna', 'provider': 'Portkey', 'pricing_file': 'data/prices.json',
                  'configurations': {'with_caching': {'mode': 'implicit', 'ttl': '30m'},
                                     'without_caching': {'mode': 'explicit', 'ttl': '30m', 'breakpoints': []}},
                  'order': 'paired by document; configuration order alternates', 'runs': [], 'calls': []}
    if destination.exists():
        experiment = json.loads(destination.read_text(encoding='utf-8'))
        # Preserve failed explicit-only controls; never count them as no-cache evidence.
        invalid_ids = {run['run_id'] for run in experiment['runs']
                       if run['configuration'] == 'without_caching'
                       and any(not call['no_cache_verified'] for call in experiment['calls']
                               if call['run_id'] == run['run_id'])}
        experiment.setdefault('initial_control_runs', []).extend(run for run in experiment['runs'] if run['run_id'] in invalid_ids)
        experiment.setdefault('initial_control_calls', []).extend(call for call in experiment['calls'] if call['run_id'] in invalid_ids)
        experiment['runs'] = [run for run in experiment['runs'] if run['run_id'] not in invalid_ids]
        experiment['calls'] = [call for call in experiment['calls'] if call['run_id'] not in invalid_ids]
        experiment['configurations']['without_caching']['isolation'] = 'unique initial system-message nonce and prompt_cache_key on every API call'
    for doc_index, path in enumerate(files):
        order = ['with_caching', 'without_caching'] if doc_index % 2 == 0 else ['without_caching', 'with_caching']
        for configuration in order:
            if any(run['configuration'] == configuration and Path(run['document']).name == path.name
                   for run in experiment['runs']):
                continue
            print(f'[{len(experiment["runs"]) + 1}/24] {configuration}: {path.name}', flush=True)
            collected = []
            await execute(str(path.relative_to(ROOT)), configuration, collected)
            run = collected[0]
            experiment['runs'].append(run)
            experiment['calls'].extend(call_entry(run, response, i) for i, response in enumerate(run['api_responses'], 1))
            experiment['updated_at'] = timestamp()
            temporary = destination.with_suffix('.json.tmp')
            temporary.write_text(json.dumps(experiment, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            temporary.replace(destination)
            print(f'  status={run["status"]}; input={run["input_tokens"]}; cached={run["cached_input_tokens"]}; cost=${run["cost_usd"]}', flush=True)
    print('All 24 document runs attempted; raw individual responses saved to output/cache_test.json.', flush=True)


if __name__ == '__main__':
    asyncio.run(main())
