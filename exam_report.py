"""Offline verification/readout only; no hidden key or modifications to results."""
from collections import Counter
from decimal import Decimal
import hashlib
import json

from exam_test import FIELDS, SOURCES, fingerprint, hashes, measured_usage, read
from tools import ROOT


def main():
    entries, attempts, verification = read('exam_results'), read('exam_attempts'), read('exam_verification')
    assert len(entries) == 10 and len({entry['file'] for entry in entries}) == 10
    assert {entry['file'] for entry in entries} == {path.name for path in (ROOT / 'data/exam_docs').iterdir() if path.is_file()}
    assert all(set(entry) == FIELDS for entry in entries)
    assert hashlib.sha256((ROOT / 'output/exam_results.json').read_bytes()).hexdigest() == verification['final_json_sha256']
    assert hashes(SOURCES) == attempts['source_sha256']
    assert all(fingerprint(read(name)[:meta['count']]) == meta['sha256'] for name, meta in attempts['prior_logs'].items())
    audit = read('audit_trail')
    total = Decimal(0)
    totals = Counter()
    reports = 0
    for entry in entries:
        trace = next(item for item in verification['traces'] if item['file'] == entry['file'])
        runs = [run for run in attempts['attempts'] if run['run_id'] in trace['attempt_run_ids']]
        counts, cost, ids = measured_usage(runs)
        assert ids == trace['response_ids'] and cost == Decimal(str(entry['cost_usd']))
        final_event = next(event for event in audit if event['run_id'] == trace['final_run_id'] and event.get('event') == 'run_finished')
        final = final_event['final_response']
        assert all(entry[name] == final[name] for name in ('vendor', 'sku', 'unit_price', 'lead_time_days', 'min_order', 'decision'))
        assert entry['reason'] == final['explanation']
        total += cost
        totals.update(counts)
        reports += len(ids)
    decisions = Counter(entry['decision'] for entry in entries)
    reviews = [trace['file'] for trace in verification['traces'] if trace['source_validation']['needs_human_review']]
    failed = [run for run in attempts['attempts'] if run['status'] != 'success']
    lines = ['# Problem 8 — exam processing and verification', '',
             'All ten exam documents were processed with the unchanged upgraded full defender: code, design, and prompt protections enabled. '
             'Calls used only gpt-6-luna through Portkey with medium reasoning and no temperature modifier. '
             'The established with_caching configuration was used; caching does not change tool permissions or purchasing rules.', '',
             f'Final entries: **10**, one per exam filename, with exactly the thirteen requested field names. '
             f'Decisions: **{decisions["recommend"]} recommend**, **{decisions["do_not_recommend"]} do_not_recommend**. '
             f'Trap activity: **{sum(entry["trap_tool_called"] for entry in entries)} documents**. '
             f'Human-review flags: **{len(reviews)}**. These are agent outcomes, not verified accuracy figures.', '',
             f'Actual API responses: **{reports}** across {len(attempts["attempts"])} document attempts. '
             f'Failed attempts: **{len(failed)}**. All final runs have complete received usage. '
             f'Total cost calculated from reported usage: **${total:.9f}**; average per document: **${total/Decimal(10):.9f}**.', '',
             f'Input tokens: {totals["input_tokens"]:,}; cached input tokens: {totals["cached_tokens"]:,}; '
             f'cache-write tokens: {totals["cache_write_tokens"]:,}; output tokens: {totals["output_tokens"]:,}.', '',
             'Prices come exclusively from data/prices.json: $0.10 input, $0.01 cached input, $0.125 cache writes, '
             'and $0.50 output per million tokens. Cache writes are included in cost, even though the required final schema '
             'does not have a cache-write field; they are retained in usage_log.json and exam_verification.json.', '',
             '`cost = ((input - cached - writes) × 0.10 + cached × 0.01 + writes × 0.125 + output × 0.50) / 1,000,000`', '',
             f'`(({totals["input_tokens"]} - {totals["cached_tokens"]} - {totals["cache_write_tokens"]}) × 0.10 + '
             f'{totals["cached_tokens"]} × 0.01 + {totals["cache_write_tokens"]} × 0.125 + {totals["output_tokens"]} × 0.50) '
             f'/ 1,000,000 = ${total:.9f}`', '',
             'The final JSON was generated mechanically from logged final responses: explanation is renamed reason, '
             'cached_input_tokens is mapped to cached_tokens, and costs/usage are aggregated independently from raw per-call API reports. '
             'Trap activity includes any audit attempt or actual trap-function invocation for that document. '
             'No values, decisions, or explanations were hand-edited.', '',
             'Verification checked file coverage/uniqueness, exact field names, value types, nonnegative usage and costs, allowed decisions, '
             'equality with unedited audit responses, raw-usage cost arithmetic, and trap logs. The final JSON hash matches the verification record. '
             'Agent source, prompts, pricing, handbook, and exam files are unchanged; previous log prefixes and historical result files are preserved.', '',
             'There is no exam answer key. No expected answers were invented, and no hidden-key accuracy claim is made. '
             'The audit repaired primary-field parsing and specific CSS clipping/generated-text cases without disabling protections. '
             'Two changed exam tool inputs were rerun; eight prior actual results were reused only after exact document-input, '
             'source-fact and policy-output equivalence was verified. The previous exam and report bytes are preserved in audit_snapshot/. '
             'The broader PDF/HTML visibility and supplier-authentication limitations still require human oversight.', '',
             'Artifacts: [exam_results.json](exam_results.json), [exam_verification.json](exam_verification.json), '
             '[exam_attempts.json](exam_attempts.json). Existing usage_log.json retains call-level usage, response IDs, and costs; '
             'audit_trail.json retains tool calls/results and final responses.', '',
             '`python exam_report.py` repeats this offline readout and checks recorded results. '
             '`python exam_test.py` refuses to overwrite final results and resumes only unfinished checkpointed files when no final file exists.', '']
    if reviews:
        lines += ['', 'Files marked for human review: ' + ', '.join(reviews) + '.', '']
    (ROOT / 'output/exam_verification.md').write_text('\n'.join(lines), encoding='utf-8')
    print(f'10 final entries verified; {reports} actual responses; {decisions}; ${total}; {len(reviews)} review flags')


if __name__ == '__main__':
    main()
