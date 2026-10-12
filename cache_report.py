"""Verify the saved real-API experiment and reproduce the Markdown cost report."""
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path

from tools import ROOT


def main():
    path = ROOT / 'output/cache_test.json'
    experiment = json.loads(path.read_text(encoding='utf-8'))
    if len(experiment['runs']) != 24:
        raise ValueError('Wait for all 24 main comparison runs before reporting')
    prices = json.loads((ROOT / 'data/prices.json').read_text(), parse_float=Decimal)['gpt-6-luna']
    keys = {row['file']: row for row in json.loads((ROOT / 'data/practice_key.json').read_text())}
    summaries = {}
    for configuration in ('with_caching', 'without_caching'):
        runs = [run for run in experiment['runs'] if run['configuration'] == configuration]
        calls = [call for call in experiment['calls'] if call['configuration'] == configuration]
        filenames = [Path(run['document']).name for run in runs]
        if len(runs) != 12 or len(set(filenames)) != 12:
            raise ValueError('Each configuration must contain all 12 documents exactly once')
        usage_complete = all(run['status'] == 'success' and run['usage_complete'] for run in runs)
        cache_verified = bool(calls) and all(call['cached_count_explicitly_reported'] and call['provider_response_not_gateway_replay'] for call in calls)
        cache_verified = cache_verified and (all(call['no_cache_verified'] for call in calls)
                                            if configuration == 'without_caching' else any(call['cache_hit_verified'] for call in calls))
        total = sum((Decimal(call['cost_usd']) for call in calls if call['cost_usd'] is not None), Decimal(0))
        totals = {name: sum(call[name] or 0 for call in calls) for name in ('input_tokens', 'cached_input_tokens', 'cache_write_tokens', 'output_tokens', 'total_tokens')}
        uncached = totals['input_tokens'] - totals['cached_input_tokens'] - totals['cache_write_tokens']
        components = {name: str(Decimal(count) * prices[rate] / Decimal(1_000_000)) for name, count, rate in (
            ('uncached_input', uncached, 'input_per_1m'), ('cached_input', totals['cached_input_tokens'], 'cached_input_per_1m'),
            ('cache_writes', totals['cache_write_tokens'], 'cache_write_per_1m'), ('output', totals['output_tokens'], 'output_per_1m'))}
        assert sum(map(Decimal, components.values())) == total
        assert sum((Decimal(run['cost_usd']) for run in runs if run['cost_usd'] is not None), Decimal(0)) == total
        mismatches = []
        for run in runs:
            filename = Path(run['document']).name
            final = run['final_response'] or {}
            differences = {name: {'expected': expected, 'actual': final.get(name)}
                           for name, expected in keys[filename].items() if name != 'file' and final.get(name) != expected}
            if differences:
                mismatches.append({'document': filename, 'differences': differences})
        summaries[configuration] = {'documents': len(runs), 'model_calls': len(calls), 'usage_complete': usage_complete,
                                    'cache_verified': cache_verified, **totals,
                                    'total_cost_usd': str(total), 'average_cost_per_document_usd': str(total / 12),
                                    'projected_30000_documents_usd': str(total / 12 * 30000),
                                    'cost_components_usd': components, 'answer_key_mismatches': mismatches,
                                    'gateway_cache_status_counts': dict(Counter(call['portkey_cache_status'] for call in calls))}
    verified = all(summary['usage_complete'] and summary['cache_verified'] for summary in summaries.values())
    c, n = summaries['with_caching'], summaries['without_caching']
    cached, uncached = Decimal(c['total_cost_usd']), Decimal(n['total_cost_usd'])
    savings = (uncached - cached) / uncached * 100 if verified and uncached else None
    experiment['summary'] = {'configurations': summaries, 'comparison_verified': verified,
                             'percentage_savings': str(savings) if savings is not None else None}
    usage = json.loads((ROOT / 'output/usage_log.json').read_text())
    # Use the latest actual record per run ID; a correction note can supersede an interim marker.
    latest = {run['run_id']: run for run in usage}
    ids = {run['run_id'] for run in experiment['runs']} | {run['run_id'] for run in experiment.get('initial_control_runs', [])}
    experiment['interrupted_attempts'] = [run for run in latest.values() if run['status'] == 'interrupted'
                                         and run.get('configuration') in summaries and run['run_id'] not in ids]
    setup_total = sum((Decimal(call['cost_usd']) for call in experiment.get('initial_control_calls', [])
                       if call['cost_usd'] is not None), Decimal(0))
    experiment['summary']['preliminary_control_cost_usd'] = str(setup_total)
    experiment['summary']['interrupted_attempt_cost_unknown'] = bool(experiment['interrupted_attempts'])
    path.write_text(json.dumps(experiment, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    lines = ['# Problem 4 — Measured prompt caching comparison', '',
             '## Verification and experiment design', '',
             f'Completed **24 main document runs**, 12 per configuration, with **{len(experiment["calls"])} actual API responses**.',
             f'Cache comparison verified: **{verified}**. All totals below use only this final comparison cohort.', '',
             '- With caching: `prompt_cache_options={"mode":"implicit","ttl":"30m"}`; unchanged handbook, instructions, tools, schema, model, and reasoning effort form the shared prefix.',
             '- Without caching: `prompt_cache_options={"mode":"explicit","ttl":"30m"}`, no breakpoints, plus a unique initial system-message nonce and unique `prompt_cache_key` on **every model call**, including the call after tool reading.',
             '- The extra nonce prevents prefix reuse on this route; it is labeled metadata and does not change the handbook or purchasing rules. No tokens or numbers in the handbook were altered.',
             '- Each request forces a Portkey response-cache refresh and uses a unique trace ID. Prompt-cache reuse inside the provider is the subject of this experiment; replaying whole responses would invalidate it.',
             '- Runs were paired by document with alternating configuration order; interrupted experiment recovery retained completed cached runs. Calls were sequential, with no separate prewarming call. Earlier homework runs could already have warmed the stable prefix.', '',
             'The [OpenAI prompt-caching guide](https://developers.openai.com/api/docs/guides/prompt-caching) documents that explicit-only mode without breakpoints should avoid cache reads and writes. **This Portkey route still returned cached tokens under that setting alone.** The initial control could not be verified; the exact gateway/provider component responsible is not established. Prefix isolation was therefore added and verified using actual counters, rather than assuming the requested setting worked.', '',
             '## Actual usage and costs', '',
             'Prices come exclusively from `data/prices.json`: input $0.10, cached input $0.01, cache write $0.125, and output $0.50 per million tokens.', '',
             'For every response:', '',
             '```text',
             'uncached_input = input_tokens - cached_tokens - cache_write_tokens',
             'cost = (uncached_input * 0.10 + cached_tokens * 0.01',
             '        + cache_write_tokens * 0.125 + output_tokens * 0.50) / 1,000,000',
             '```', '',
             'Cache writes and reads are partitions of total input; they are not charged again at the ordinary input rate. Output includes reported reasoning tokens without double counting. Every raw usage object, including other available counters, is preserved in `cache_test.json`. Costs are calculated from actual token usage at the assignment rates, not independently verified provider invoices.', '']
    for label, summary in [('With caching', c), ('Without caching (zero reuse)', n)]:
        lines.extend([f'### {label}', '',
                      f'- Documents: {summary["documents"]}; API calls: {summary["model_calls"]}.',
                      f'- Input: {summary["input_tokens"]:,}; cached input: {summary["cached_input_tokens"]:,}; cache writes: {summary["cache_write_tokens"]:,}; output: {summary["output_tokens"]:,}.',
                      f'- Cache verification: {summary["cache_verified"]}; complete successful usage: {summary["usage_complete"]}.',
                      f'- Total cost: **${summary["total_cost_usd"]}**.',
                      f'- Average per document = ${summary["total_cost_usd"]} / 12 = **${Decimal(summary["average_cost_per_document_usd"]):.9f}**.',
                      '- Cost components: ' + '; '.join(f'{name} ${amount}' for name, amount in summary['cost_components_usd'].items()) + '.', ''])
    lines.extend(['### Savings', '',
                  f'Savings = (${uncached} − ${cached}) / ${uncached} × 100 = **{savings:.2f}%**.' if savings is not None else 'Savings cannot be verified because one or both configurations lack valid usage/cache evidence.', '',
                  'The cached configuration reports real cache reads. Every final no-cache call explicitly reports zero cached tokens. However, the no-cache route still writes cache entries; those writes are charged in the measured comparison. This is **zero reuse**, not a verified route that disables cache writes.', '',
                  '## Comparison with Problem 2', '',
                  'Problem 2 counted 10,069 handbook tokens with tiktoken/o200k_base and estimated handbook-only costs per model call: $0.00100690 uncached or $0.00010069 fully cached, a 90% input-only reduction. For 1,000 calls: $1.00690 versus $0.10069.', '',
                  'Each document here required two model calls, each containing the handbook. A handbook-only two-call/document projection would be $0.00201380 uncached or $0.00020138 cached. For 12 documents (24 calls per configuration), the corresponding theoretical handbook-only totals are $0.02416560 and $0.00241656.', '',
                  f'The actual agent costs are ${n["total_cost_usd"]} and ${c["total_cost_usd"]}, respectively. They also include tools, schema, prompt/message formatting, document content, model output, and cache writes. The no-cache isolation prefix adds a small token overhead. These totals therefore do not directly test the handbook-only tokenizer count: the API does not itemize handbook tokens separately.', '',
                  '## Projection: 1,000 documents/day for 30 days', '',
                  'Volume = 1,000 × 30 = **30,000 documents**. Scale each measured average by 30,000:', '',
                  f'- With caching: (${c["total_cost_usd"]} / 12) × 30,000 = **${Decimal(c["projected_30000_documents_usd"]):.6f}**.',
                  f'- Without cache reuse: (${n["total_cost_usd"]} / 12) × 30,000 = **${Decimal(n["projected_30000_documents_usd"]):.6f}**.',
                  f'- Projected savings: **${(uncached - cached) / 12 * 30000:.6f}**.' if verified else '- Projected savings are not verified.', '',
                  'These are extrapolations, not observed 30-day bills. They assume the same document mix, two-call workflow, cache-hit pattern, cache-write behavior, and prices. Cold starts, retention expiration, changed prompts, concurrency, retries, different output lengths, and gateway fees can change actual costs. Warm-cache daily averages may understate cold-start costs.', '',
                  '## Surprising results and limits', '',
                  '- The explicit-only parameter was serialized correctly, yet initial no-cache attempts reported nonzero cached tokens. Four unsuccessful control runs (eight calls) are preserved separately, not included as successful no-cache data.',
                  f'- Those preliminary control calls cost ${setup_total} using the supplied rates. One additional interrupted setup attempt has no saved usage and unknown cost; it is not assigned zero. The requested 24-run final cohort therefore required extra setup attempts.',
                  '- Prefix isolation eliminated reads but did not eliminate cache writes. This adds the supplied 25% cache-write premium over ordinary input pricing and raises the measured zero-reuse baseline. Savings should not be presented as a clean “all ordinary input versus all cached input” experiment.',
                  '- The cached configuration reuses more than the handbook alone, including stable tools and instructions. It nevertheless still sends the full handbook on every request; caching changes token billing, not the local request contents.',
                  '- Both configurations use the same baseline agent. Several practice answers differ from the supplied key; the mismatches are recorded in the JSON summary. Cached and noncached purchasing facts agree for each document in this cohort, but caching does not establish factual correctness or prompt-injection safety. Those concerns remain for later problems.',
                  '- A bookkeeping pass mistakenly marked an in-progress p08 run as interrupted. Its later successful usage record and a correction event supersede that interim marker; no successful usage was dropped or counted twice.', '',
                  '## Artifacts and reproduction', '',
                  '- `output/cache_test.json`: final run records, per-call actual usage/output/cost, request cache settings, explicit verification flags, preliminary failed controls, interrupted attempt, and calculated summary.',
                  '- `output/usage_log.json` and `output/audit_trail.json`: existing records preserved with new runs appended; simulated trap attempts remain in `output/trap_calls.json`.',
                  '- `python cache_test.py`: starts the live experiment or resumes its saved cohort; it does not overwrite completed pairs.',
                  '- `python cache_report.py`: validates and reproduces this report from the saved API evidence without any new model calls.', '',
                  'Caching meaningfully reduces this measured agent’s token cost, subject to the verified route-specific cache-write caveat and the small, warm-cache sample. No future security defenses were introduced.'])
    (ROOT / 'output/cache_test.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps(experiment['summary'], indent=2))


if __name__ == '__main__':
    main()
