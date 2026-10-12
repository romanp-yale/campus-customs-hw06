"""Local submission audit; scans candidate/staged/history bytes without printing secrets."""
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from dotenv import dotenv_values
from tools import ROOT

SAFE = ['git', '-c', 'safe.directory=' + ROOT.as_posix()]
REQUIRED = ('AI_prompts.md', 'README.md', '.gitignore', '.env.example', 'requirements.txt', 'agent.py', 'tools.py', 'models.py',
            'prompts/prompt.md', 'data/shop_handbook.md', 'data/prices.json', 'data/practice_key.json',
            'output/handbook_estimate.md', 'output/trap_calls.json', 'output/usage_log.json', 'output/audit_trail.json',
            'output/harness.md', 'output/cache_test.json', 'output/cache_test.md', 'output/attack_results.json', 'output/attack_results.md',
            'output/defense_results.json', 'output/defense_results.md', 'output/red_team.md', 'output/exam_results.json', 'output/hw6_report.html')


def git(*args):
    result = subprocess.run([*SAFE, *args], cwd=ROOT, capture_output=True)
    if result.returncode:
        raise RuntimeError('Git check failed: ' + ' '.join(args[:2]))
    return result.stdout


def audit():
    assert all((ROOT / name).is_file() for name in REQUIRED)
    assert len(list((ROOT / 'data/practice_docs').iterdir())) == 12
    assert len(list((ROOT / 'data/exam_docs').iterdir())) == 10
    attacks = sorted(path.name for path in (ROOT / 'data/my_attacks').iterdir() if path.is_file())
    assert len(attacks) == 4
    assert all(f'## Problem {number} ' in (ROOT / 'AI_prompts.md').read_text(encoding='utf-8') for number in range(1,11))
    examples = dotenv_values(ROOT / '.env.example')
    assert examples['PORTKEY_API_KEY'] == 'replace_with_your_portkey_api_key'
    assert not any(value and not ('placeholder' in value or 'replace_with_' in value) for value in examples.values())
    known = []
    for source in (dotenv_values(ROOT / '.env'), dotenv_values(ROOT.parent.parent / '.env'), os.environ):
        for name, value in source.items():
            if value and len(value) > 12 and re.search(r'(API_KEY|TOKEN|SECRET|PASSWORD)$', name, re.I) and not value.startswith('replace_with_'):
                raw = value.encode()
                known.extend((raw, base64.b64encode(raw)))
    patterns = [re.compile(rb'\b(?:ghp_|gho_|ghu_|ghs_|ghr_)[A-Za-z0-9]{30,}'),
                re.compile(rb'\bgithub_pat_[A-Za-z0-9_]{30,}'), re.compile(rb'\bsk-[A-Za-z0-9_-]{20,}'),
                re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')]
    names = git('ls-files', '--cached', '--others', '--exclude-standard', '-z').decode().split('\0')
    names = sorted(set(name for name in names if name))
    staged = [name for name in git('diff', '--cached', '--name-only', '-z').decode().split('\0') if name]
    assert not any(Path(name).name == '.env' or name.startswith(('.venv/', 'venv/', 'env/')) or '__pycache__' in name for name in names)
    assert subprocess.run([*SAFE, 'check-ignore', '.env', '.venv'], cwd=ROOT, capture_output=True).returncode == 0
    findings = []
    def scan(name, raw):
        if any(secret in raw for secret in known) or any(pattern.search(raw) for pattern in patterns):
            findings.append(name)  # Names only; never credentials or matching excerpts.
    for name in names:
        scan(name, (ROOT / name).read_bytes())
    for name in staged:
        scan('staged:' + name, git('show', ':' + name))
    objects = git('rev-list', '--objects', '--all').decode().splitlines()
    history_blobs = 0
    for entry in objects:
        oid, _, name = entry.partition(' ')
        if git('cat-file', '-t', oid).strip() == b'blob':
            history_blobs += 1
            assert Path(name).name != '.env'
            scan('history:' + name, git('cat-file', 'blob', oid))
    assert not findings, 'Credential pattern found in paths: ' + ', '.join(findings)
    # Verify every archived successful run points at real API responses; preserve unknown interrupted usage.
    usage = json.loads((ROOT / 'output/usage_log.json').read_text(encoding='utf-8'))
    latest = {run['run_id']: run for run in usage}
    successful = [run for run in latest.values() if run['status'] == 'success']
    assert all(run['model'] == 'gpt-6-luna' and run['provider'] == 'Portkey' and run['usage_complete']
               and run['api_responses'] and all(response.get('response_id') and response.get('usage') for response in run['api_responses']) for run in successful)
    for filename in ('agent.py', 'baseline_snapshot/agent.py', 'defender_pre_upgrade/agent.py'):
        text = (ROOT / filename).read_text(encoding='utf-8')
        assert "MODEL = 'gpt-6-luna'" in text and "https://api.portkey.ai/v1" in text
    cli = usage[-1]
    assert cli['status'] == 'success' and cli['defense_layers'] == ['code', 'design', 'prompt'] and cli['configuration'] == 'with_caching'
    assert cli['document'] == 'data/practice_docs/p01_bluehen_quote.html'
    browser = json.loads((ROOT / 'output/hw6_report_browser_test.json').read_text(encoding='utf-8'))
    assert not browser['javascript_errors'] and not browser['external_resource_requests']
    assert browser['html_sha256'] == hashlib.sha256((ROOT / 'output/hw6_report.html').read_bytes()).hexdigest()
    report = {
        'checked_at': datetime.now(timezone.utc).isoformat(), 'required_paths': list(REQUIRED), 'all_required_files_present': True,
        'practice_docs': 12, 'exam_docs': 10, 'custom_attacks': attacks, 'prompt_problems': list(range(1,11)),
        'candidate_files_scanned': len(names), 'staged_files_scanned': len(staged), 'tracked_history_blobs_scanned': history_blobs,
        'secret_findings': findings, 'local_env_and_virtualenv_ignored': True, 'env_example_placeholders_only': True,
        'only_model_gpt6luna_portkey': True, 'successful_usage_runs': len(successful), 'saved_successes_have_actual_api_usage': True,
        'submission_cli_smoke': {'run_id': cli['run_id'], 'status': cli['status'], 'cost_usd': cli['cost_usd'],
                                 'input_tokens': cli['input_tokens'], 'cached_tokens': cli['cached_input_tokens'], 'output_tokens': cli['output_tokens']},
        'offline_report_browser_checks_passed': True,
        'public_repository': 'https://github.com/romanp-yale/campus-customs-hw06',
        'publication_status': 'Not established by this local audit; verify remote commit and anonymous access separately.'}
    if '--check-only' not in sys.argv:
        (ROOT / 'output/submission_audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'All required files present; {len(names)} candidate and {len(staged)} staged files scanned; {history_blobs} history blobs; no credential findings.')


if __name__ == '__main__':
    audit()
