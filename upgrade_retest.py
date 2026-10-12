"""Fourteen actual upgraded runs; historical reports and log prefixes are preserved."""
import asyncio
import hashlib
import json

from agent import execute
from defense_test import evaluate, save
from tools import ROOT, timestamp


def read(name):
    return json.loads((ROOT / 'output' / (name + '.json')).read_text(encoding='utf-8'))


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


async def main():
    destination = ROOT / 'output/defender_upgrade_results.json'
    if destination.exists():
        raise FileExistsError('Preserve the completed upgrade retest before running again')
    key = {entry['file']: entry for entry in json.loads((ROOT / 'data/practice_key.json').read_text())}
    cases = read('red_team_cases')['cases']
    key.update({filename: case['expected'] for filename, case in cases.items()})
    original = read('attack_results')
    attacks = {entry['document'] for entry in original['documents'] if entry['document_inspection']['attack_identified']} | set(cases)
    log_names = ('usage_log', 'audit_trail', 'trap_calls', 'defense_preprocessing')
    results = {'started_at': timestamp(), 'model': 'gpt-6-luna', 'configuration': 'without_caching',
               'defender_version': 'upgraded', 'documents': [],
               'prior_logs': {name: {'count': len(read(name)), 'sha256': fingerprint(read(name))} for name in log_names},
               'historical_sha256': {name: hashlib.sha256((ROOT / 'output' / name).read_bytes()).hexdigest()
                                     for name in ('attack_results.json', 'defense_results.json', 'defense_ablations.json', 'red_team_results.json')}}
    paths = sorted((ROOT / 'data/practice_docs').iterdir()) + [ROOT / 'data/my_attacks' / name for name in sorted(cases)]
    for index, path in enumerate(paths, 1):
        print(f'Upgraded [{index}/{len(paths)}] {path.name}', flush=True)
        collected = []
        await execute(str(path.relative_to(ROOT)), 'without_caching', collected, defenses='all')
        entry = evaluate(collected[0], key, attacks)
        entry['source_validation'] = collected[0]['source_validation']
        entry['human_review_required'] = entry['source_validation']['needs_human_review'] if entry['source_validation'] else None
        results['documents'].append(entry)
        results['updated_at'] = timestamp()
        save(destination, results)
        print('  correct:', entry['all_fields_correct'], 'cost:', entry['cost_usd'], flush=True)
    results['prior_logs_preserved'] = all(fingerprint(read(name)[:metadata['count']]) == metadata['sha256']
                                         for name, metadata in results['prior_logs'].items())
    results['historical_results_preserved'] = all(hashlib.sha256((ROOT / 'output' / name).read_bytes()).hexdigest() == checksum
                                                for name, checksum in results['historical_sha256'].items())
    snapshot = json.loads((ROOT / 'defender_pre_upgrade/manifest.json').read_text())
    results['completed_at'] = timestamp()
    results['snapshot_manifest'] = snapshot
    results['snapshot_preserved'] = all(hashlib.sha256((ROOT / 'defender_pre_upgrade' / name).read_bytes()).hexdigest() == checksum
                                        for name, checksum in snapshot.items())
    save(destination, results)
    print('14 actual runs saved; preserved logs:', results['prior_logs_preserved'], flush=True)


if __name__ == '__main__':
    asyncio.run(main())
