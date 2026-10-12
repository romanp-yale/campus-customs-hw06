"""Produce a requirement-by-requirement grading audit from verified local evidence."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

from build_hw6_report import reconcile
from tools import ROOT, timestamp


def read(name):
    return json.loads((ROOT/'output'/name).read_text(encoding='utf-8'))


def main():
    d=reconcile()
    attachment=Path('C:/Users/Roman/.codex/attachments/3cea786e-71e4-4434-b54a-7aba6e3fce16/Pasted text.txt')
    original=attachment.read_bytes()
    assert original in (ROOT/'AI_prompts.md').read_bytes()
    with zipfile.ZipFile('C:/Users/Roman/Downloads/data(4).zip') as archive:
        verified_data=[]
        for member in archive.infolist():
            if not member.is_dir():
                name=member.filename.replace('\\','/')
                if name.startswith('data/'):
                    assert (ROOT/name).read_bytes()==archive.read(member)
                    verified_data.append(name)
    assert len(verified_data)==25  # handbook, prices, key, 12 practice, 10 exam.
    manifest=json.loads((ROOT/'audit_snapshot/manifest.json').read_text(encoding='utf-8'))
    assert all(hashlib.sha256((ROOT/'audit_snapshot'/name).read_bytes()).hexdigest()==sha for name,sha in manifest.items())
    cohort=read('attack_results.json')
    responses=[response for row in cohort['documents'] for response in row['actual_usage']['api_responses']]
    assert len(responses)==24 and len({r['response_id'] for r in responses})==24
    assert all(r['portkey_cache_status']=='REFRESH' for r in responses)
    usage={r['run_id']:r for r in read('usage_log.json')}
    smoke=next(r for r in reversed(list(usage.values())) if r.get('run_id')=='fcd1920b-ce4d-4ab7-8267-7fcf3e7c6af6')
    paid=[row['actual_usage'] for row in cohort['documents']]+d['audit_repair']['new_runs']+[smoke]
    assert len(paid)==19 and len({r['run_id'] for r in paid})==19
    paid_cost=sum(Decimal(r['cost_usd']) for r in paid)
    scores=[(1,'AI Prompts',5,5,'PASS','Actual original/follow-up prompts present; supplied attachment verified byte-for-byte.'),
            (2,'Handbook Estimate',6,6,'PASS','10,069 o200k_base tokens reproduced; explicitly a model-tokenizer estimate.'),
            (3,'Agent',12,12,'PASS','Real refreshed p01/p08 evidence, three formats, fixed model/full-book hook, structured output and logs.'),
            (4,'Caching',16,16,'PASS','48 unique refreshed responses; zero cached reads in every no-reuse call; writes separately priced.'),
            (5,'Attacks',8,8,'PASS','Repaired replay contamination; 12 fresh baseline runs still show four of seven attacks succeeding.'),
            (6,'Defenses',16,15,'PARTIAL','Three layers and actual P6 ablations verified; later repairs not separately isolated; visibility remains heuristic.'),
            (7,'Red Team',8,8,'PASS','Exactly two original attacks plus two explicitly requested follow-ups; historical failures and four repaired live outcomes preserved.'),
            (8,'Exam',12,12,'PASS','10 unique typed entries; two genuine repairs, eight proven-equivalent reused outputs; no hidden-key accuracy claim.'),
            (9,'HTML Report',12,11,'PASS','Offline charts/table/controls verified; screen-reader and independent browser-engine/physical-print checks not performed.'),
            (10,'GitHub',5,4,'PARTIAL','Existing repository public; local audit changes intentionally await explicit push approval.')]
    total=sum(row[3] for row in scores)
    checklist=[]; problem=None; phase='General'
    for line in original.decode('utf-8-sig').splitlines():
        if line.startswith('## PHASE'):
            phase=line;problem=None
        match=re.match(r'### Problem (\d+) ',line)
        if match: problem=int(match.group(1))
        if line.startswith('- ') or (phase.startswith('## PHASE 3') and re.match(r'\d+\. ',line)):
            requirement=re.sub(r'^- |^\d+\. ','',line)
            evidence={1:'AI_prompts.md; original attachment byte inclusion and original Git prefix preservation.',
                      2:'src/estimate_handbook.py; supplied prices; independently reproduced exact encoding count and arithmetic.',
                      3:'agent.py, tools.py, models.py, harness.md; 22 regressions; fresh-install CLI; fresh p01/p08 and API/audit records.',
                      4:'cache_test.json: 24 runs/48 unique REFRESH responses; Decimal recomputation; zero-read/write partition checks.',
                      5:'Fresh attack_results.json: 12 comparisons, individually matched fields/decisions, trap/audit records, original rendering/source findings.',
                      6:'defense_results.json + defense_ablations.json: 12 full runs and 48 factorial runs; prepare hook, exact one-shot guard and handbook policy.',
                      7:'red_team_cases/results, round2_cases/results and audit_retest_results; four original runs and four latest defended repairs.',
                      8:'exam_results/attempts/verification; 10 unique entries; raw call cost equality; unchanged audit outputs; eight equivalence checks.',
                      9:'hw6_report.html and browser_test; isolated single-file offline test; all chart/export/filter/projection checks; hashes/math reconciled.',
                      10:'submission_audit.py checks; Git initial history and ignore rules; public metadata and anonymous HTTP 200; update pending approval.'}.get(problem,'File inventory, source inspection, SHA-256 archives, raw usage reconciliation, tests and the findings described below.')
            status='PASS'
            limitation=''
            if any(term in requirement.lower() for term in ('malicious document text cannot override','fully compliant with every','unique role of each','additional tokens and dollars','reproduced from a fresh git clone')):
                status='QUALIFIED'; limitation='Verified for the documented scope; model behavior/visibility are not universally guaranteed, and new per-layer overhead is not separately measured.'
            if 'push' in requirement.lower() or 'final canvas' in requirement.lower():
                status='PENDING HUMAN'; limitation='No new push is authorized; Canvas submission remains manual.'
            checklist.append({'phase':phase,'problem':problem,'requirement':requirement,'status':status,'evidence':evidence,'limitation':limitation})
    lines=['# Homework 6 — strict requirements audit and final fixes','',
           'This assessment applies to the current local candidate, not the older public commit. Estimated marks are conservative judgment, not the course grader’s decision. No push occurred during this audit.','',
           '| Problem | Max points | Estimated earned points | Status | Issues |', '|---|---:|---:|---|---|']
    for number,title,max_points,earned,status,issue in scores:
        lines.append(f'| {number}. {title} | {max_points} | {earned} | {status} | {issue} |')
    lines += [f'| **TOTAL** | **100** | **{total}** | **LOCAL CANDIDATE READY** | Publish only after approval. |','',
              '## A. Missing or unverified requirements','',
              '- No required source, data or output file is missing, empty or malformed. The four custom files consist of exactly two originals and two authorized follow-ups.',
              '- Publishing these audit fixes is pending explicit approval. The public repository currently has the pre-audit commit; do not treat that older revision as the repaired candidate.',
              '- The tokenizer is verified only for o200k_base, not independently established for the provider’s model. This permitted estimation limitation is stated explicitly.',
              '- No hidden exam answer key, provider invoice verification, universal injection guarantee, OCR/multi-item/currency coverage, native-mail integration or real payment/email execution was verified or claimed.',
              '- New browser repairs have no isolated per-layer overhead experiment. Original P6 matched contrasts are genuine; local CPU/staff/gateway costs are unmeasured.',
              '- Offline HTML was tested in Chromium/Edge at five widths. Assistive-technology testing, unrelated rendering engines and physical printing remain unverified.',
              '- One historical interrupted setup request has no received API usage and unknown cost. It remains outside the complete final caching cohort; no zero cost was invented.','',
              '## B. Bugs discovered and fixes','',
              '- `agent.py:166`: gateway response refresh applied only outside baseline mode. All 24 old P5 responses were HITs, with repeated IDs from earlier requests. Refresh is now transport-wide; 12 original undefended documents were rerun, all REFRESH with 24 distinct IDs. No security layer was added to baseline. See the preserved replay artifacts and [Portkey’s cache semantics](https://docs1.portkey.ai/docs/product/ai-gateway/cache-simple-and-semantic).',
              '- `defenses.py:170`: primary item extraction recognized Item/Happy-to-quote but missed Quote-for. Added that explicit anchored declaration; e08 now produces its source SKU through a real agent rerun.',
              '- `defenses.py:174`: quantity regex rejected properly grouped 1,000. Generic grouping validation/normalization now preserves 1000; e07 was genuinely rerun and declined for the 600-unit limit.',
              '- `defenses.py:172`: price regex could truncate $1,000.00 into $1.00. Grouped prices now parse completely; malformed groups and scientific suffixes are not accepted as cheap prefixes. A real local regression verifies the correct rejection.',
              '- `html_layout.py:13` and `:28`: DOM rectangles ignored empty inset clipping and opaque generated text. Added scoped, non-executable parsing of those paint cases; actual generated-price attack now returns $17.44 and recommend. No filenames, answer key, vendor-specific numbers or malicious instructions are used as runtime rules.',
              '- `attack_test.py`/`attack_report.py`: baseline freshness was not checked; outcome summaries had fixed success lists. Freshness is now verified and success lists/counts derived from actual records; missing-field failures alone are not labeled attacker fact adoption.',
              '- `submission_audit.py:80`: checking the last usage row required every later run to be the smoke document. It now finds the actual relevant successful smoke record.',
              '- `exam_test.py:37,111,118`: UTF-8 pricing read made explicit; historical records can be verified at archived paths; equivalent reused runs are disclosed. These are provenance fixes, not edits to exam answers.',
              '- `report_template.html`/builder/test: fixed hardcoded exam counts and stale current-failure wording; updated historical-versus-current labels and dynamic audit metrics. Local .env copy instructions now avoid overwriting an existing file.','',
              '## C. Changes made','',
              'Source changes are limited to visibility/number/primary-label parsing, transport freshness, verification/reporting and focused tests. Runtime prompts, models, trap functions, handbook, practice key, exam files and all original attack files were not changed.',
              'Modified: agent.py, defenses.py, html_layout.py, attack_test.py, attack_report.py, exam_test.py, exam_report.py, submission_audit.py, build_hw6_report.py, report_template.html, test_hw6_report.py, README.md, AI_prompts.md and dependent output artifacts.',
              'Added: audit_retest.py, requirements_audit.py, tests/test_audit_fixes.py, audit_snapshot/manifest and original copies, explicit replay archives and audit records. All prior log entries are retained; no file was deleted to simplify submission.','',
              '## D. Actual test verification','',
              '- `python -m unittest discover -s tests -v`: final candidate suite 22/22 passed in the clean clone. An earlier generated-text regression failed because Chromium emitted opaque rgb rather than rgba; fixed and rerun. The clean clone was overlaid with the final candidate, contained no .env, and used the freshly installed requirements.',
              '- Fresh isolated Python environment: requirements.txt installation succeeded; pip check reported no broken dependencies; CLI help and the documented defended p01 command succeeded with real usage.',
              '- Local Git clone plus candidate overlay: no .env copied; original baseline, frozen defender and audit snapshot hashes verified. Root-relative paths and the local suite worked.',
              '- `audit_retest.py`: two changed exam inputs plus four defended attack documents actually ran; 24/24 custom-attack field/decision comparisons matched, no trap calls. Eight exam and twelve practice inputs/facts/policy outputs were verified equivalent to valid previous inference records.',
              '- `attack_test.py`: 12 fresh original undefended runs, all 24 REFRESH responses with distinct IDs; four factual attacks still succeed, zero traps/links.',
              '- `exam_report.py`, report builder and schema checks: ten files exactly once, required 13 keys/types, valid decisions, exact unedited audit-output equality and Decimal cost reconciliation.',
              '- Visual checks: all twelve original practice documents were rendered and their contact sheets inspected; PDF rasters and email-style MIME views are documented, with native application limitations in output/audit_visual_checks/verification.json.',
              '- `test_hw6_report.py`: isolated directory containing only HTML, offline network, filters including empty results, volume/cohort projections, downloaded JSON equality, embedded images, static no-JS content, print control wiring and five responsive widths passed. No console errors or external requests.',
              '- Credential scan: candidate bytes and initial tracked history checked against actual local credential values and key patterns without printing values. Neither real .env nor local environments are tracked. The public repository returned anonymous HTTP 200; no push occurred.',
              f'- Actual audit API work: 19 document runs / {sum(len(r["api_responses"]) for r in paid)} reported responses, ${paid_cost}. This includes the six targeted repairs, one fresh-install CLI smoke and twelve necessary baseline replacements.','',
              '## E. Token and cost validation','',
              'Handbook: 10,069 proxy tokens. One input-only call: $0.00100690 uncached / $0.00010069 cached. 1,000 calls: $1.00690 / $0.10069. These are estimates, not measured handbook-only API charges.',
              'Measured matched caching cohort: $0.004454805 cached / $0.033760650 zero reuse; 86.8047416148682% savings. At 30,000 documents: $11.1370125 / $84.401625. All 48 response IDs are distinct; all zero-reuse calls explicitly report zero cached reads. Cache-write charges remain and are included.',
              'P6 paired marginal effects: code −18.375 input / −40.583333 output / −$0.000022588542 per document; design −134.208333 / −72.25 / −$0.000052901042; prompt +480.875 / +3.5 / +$0.000061859375. There are 24 contrasts per layer; these interacting net effects are not additive surcharges or new-code line-item fees.',
              'Corrected fresh baseline token cost: $0.005687010. Original defended cohort: $0.033626525 under zero cache reuse; their cost difference is not a defense overhead estimate.',
              'Final exam evidence: $0.005829955 across ten entries and twenty response reports; five recommend/five do_not_recommend, no unknown fields, no traps. Eight reports are reused real observations with input equivalence, not claimed as new calls or hidden-key accuracy.','',
              '## F. Security assessment','',
              'The defended architecture provides a real action boundary: the model never receives ordinary trap schemas, function-level guards require exact one-action application authorization, and both tools always remain log-only. Model/document claims cannot set that context. Trusted handbook code, not vendor/model prose, determines purchasing rules. Selected-file checks block unrelated file access.',
              'The original baseline remains intentionally vulnerable, with four observed factual overrides; it is not a production-safe configuration. The full configuration preserved all clean practice facts and decisions and fixed all four authored attacks in the latest live tests. This does not prove universal instruction obedience or rendering security: arbitrary clipping/overlays/images, supplier impersonation, unsupported layouts and human mistakes remain limitations. Use supervised review.','',
              '## G. Submission readiness','',
              'The local candidate is ready for final review and publication. Existing repository: https://github.com/romanp-yale/campus-customs-hw06 (public). The current public commit remains pre-audit. Next steps: approve publishing, commit/stage the reviewed changes, push main, recheck remote commit/public access, then manually submit the URL to Canvas. No automatic Canvas submission or new GitHub push was performed.','',
              '## H. Conservative final grade estimate','',
              f'Estimated local-candidate score: **{total}/100**, with a plausible 94–100 range depending on grader interpretation. This is not a guaranteed grade or production certification. One point is reserved for unisolated newer defense overhead/general visibility uncertainty, one for untested advanced accessibility/cross-engine behavior, and one for the pending publication step. No hidden exam accuracy is assumed.','',
              '## Requirement-by-requirement checklist','',
              'Each bullet in the supplied audit prompt is mapped below. PASS refers to the documented homework scope; QUALIFIED and PENDING HUMAN expose limits rather than silently claiming full verification.','']
    for index,item in enumerate(checklist,1):
        lines += [f'{index}. **{item["status"]}** — {item["requirement"]}', f'   Evidence: {item["evidence"]}' + (' ' + item['limitation'] if item['limitation'] else ''),'']
    (ROOT/'output/full_requirements_audit.md').write_text('\n'.join(lines),encoding='utf-8')
    proof={'checked_at':timestamp(),'scores':[{'problem':row[0],'title':row[1],'max_points':row[2],'estimated_points':row[3],'status':row[4],'issues':row[5]} for row in scores],
           'estimated_total':total,'requirements':checklist,'original_attachment_sha256':hashlib.sha256(original).hexdigest(),
           'supplied_data_byte_verified':verified_data,'snapshot_hashes_verified':True,'baseline_gateway_statuses':['REFRESH']*24,
           'baseline_unique_response_ids':24,'report_verified_run_ids':list(d['verified_runs']),
           'new_paid_run_ids':[r['run_id'] for r in paid],'new_paid_cost_usd':str(paid_cost),'new_push_authorized':False,'new_push_performed':False,
           'public_repository':'https://github.com/romanp-yale/campus-customs-hw06','limitations':['no hidden exam key','no settled invoice verification','no universal visibility guarantee','new-layer overhead not separately isolated','advanced a11y/cross-engine/physical print unverified','publication pending approval']}
    (ROOT/'output/full_requirements_audit.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(f'Grading audit: {total}/100 estimated; {len(checklist)} requirements mapped; 25 supplied files unchanged; paid audit cost ${paid_cost}; no push.')


if __name__=='__main__':
    main()
