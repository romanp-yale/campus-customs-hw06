"""Minimal real repair tests; reuse records only when model inputs and policy facts match."""
import asyncio
from decimal import Decimal
import hashlib
import json

from agent import execute
from defenses import prepare_document, validate_quote, handbook_policy
from exam_test import finalize, hashes, SOURCES, fingerprint, save
from tools import ROOT, timestamp


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


async def main():
    target=ROOT / 'output/audit_retest_results.json'
    if target.exists():
        raise FileExistsError('Preserve audit retest results before repeating paid runs')
    original=read('audit_snapshot/output/exam_attempts.json')
    manifest=read('audit_snapshot/manifest.json')
    # Same model, handbook, prompts, tools, schemas and agent request architecture.
    for name in ('agent.py','tools.py','models.py','prompts/prompt.md','prompts/baseline.md'):
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==original['source_sha256'][name]
    audit={'started_at':timestamp(),'new_runs':[],'reused_exam_files':[],'equivalence_checks':[],
           'practice_input_equivalence':[], 'source_sha256':hashes(SOURCES)}
    handbook=(ROOT/'data/shop_handbook.md').read_text(encoding='utf-8')
    for entry in read('output/defender_upgrade_results.json')['documents'][:12]:
        path=ROOT/'data/practice_docs'/entry['document']
        prepared=prepare_document(path)
        validation=validate_quote(path,prepared.text)
        assert prepared.text==entry['preprocessing']['visible_text'] and validation.facts==entry['source_anchors']
        assert handbook_policy(validation.facts,handbook).model_dump(mode='json')==entry['final_response']
        audit['practice_input_equivalence'].append({'file':path.name,'run_id':entry['run_id'],'unchanged_model_input_and_final_policy':True})
    log_names=('usage_log','audit_trail','trap_calls','defense_preprocessing')
    historical=('attack_results.json','defense_results.json','defense_ablations.json','red_team_results.json','defender_upgrade_results.json','red_team_round2_results.json')
    cohort={'started_at':timestamp(),'files':original['files'],'source_sha256':hashes(SOURCES),
            'document_sha256':original['document_sha256'],'prior_logs':{name:{'count':len(read('output/'+name+'.json')),'sha256':fingerprint(read('output/'+name+'.json'))} for name in log_names},
            'historical_sha256':{name:hashlib.sha256((ROOT/'output'/name).read_bytes()).hexdigest() for name in historical},
            'cache_configuration':'with_caching','attempts':[],'reuse_method':'Exact prepared document, source-anchor and policy equivalence; same model/tool/prompt architecture.'}
    for old in original['attempts']:
        path=ROOT/old['document']
        prepared=prepare_document(path)
        validation=validate_quote(path,prepared.text)
        same=prepared.text==old['preprocessing']['visible_text'] and validation.facts==old['source_anchors'] and not validation.issues
        if same:
            assert handbook_policy(validation.facts,handbook).model_dump(mode='json')==old['final_response']
            cohort['attempts'].append(old)
            cohort.setdefault('reused_run_ids', []).append(old['run_id'])
            audit['reused_exam_files'].append(path.name)
            audit['equivalence_checks'].append({'file':path.name,'reused_run_id':old['run_id'],'same_prepared_text':True,'same_source_facts':True,'same_policy_result':True})
        else:
            collected=[]
            print('Repair live exam:',path.name,flush=True)
            await execute(old['document'],'with_caching',collected,defenses='all')
            assert collected[0]['status']=='success' and collected[0]['usage_complete']
            cohort['attempts'].extend(collected)
            audit['new_runs'].extend(collected)
        save(target,audit)
    save(ROOT/'output/exam_attempts.json',cohort)
    finalize(cohort)  # Generated from actual agent/audit records, never patched answers.
    cases={**read('output/red_team_cases.json')['cases'],**read('output/red_team_round2_cases.json')['cases']}
    audit['attack_runs']=[]
    for filename,case in cases.items():
        collected=[]
        print('Repair live defended attack:',filename,flush=True)
        await execute('data/my_attacks/'+filename,'with_caching',collected,defenses='all')
        run=collected[0]
        assert run['status']=='success' and run['usage_complete']
        traps=[event for event in read('output/trap_calls.json') if event['run_id']==run['run_id']]
        comparisons={field:{'actual':run['final_response'][field],'expected':value,'matched':run['final_response'][field]==value} for field,value in case['expected'].items()}
        audit['attack_runs'].append({'file':filename,'comparisons':comparisons,'all_fields_correct':all(v['matched'] for v in comparisons.values()),'trap_calls':traps,'actual_run':run})
        audit['new_runs'].append(run)
        save(target,audit)
    audit['completed_at']=timestamp()
    audit['new_run_count']=len(audit['new_runs'])
    audit['new_cost_usd']=str(sum(Decimal(run['cost_usd']) for run in audit['new_runs']))
    audit['historical_results_preserved']=all(hashlib.sha256((ROOT/'output'/name).read_bytes()).hexdigest()==sha for name,sha in cohort['historical_sha256'].items())
    audit['prior_logs_preserved']=all(fingerprint(read('output/'+name+'.json')[:meta['count']])==meta['sha256'] for name,meta in cohort['prior_logs'].items())
    assert audit['historical_results_preserved'] and audit['prior_logs_preserved']
    save(target,audit)
    print('Actual repair runs:',len(audit['new_runs']),'cost:',audit['new_cost_usd'],'reused exam:',len(audit['reused_exam_files']),flush=True)


if __name__=='__main__':
    asyncio.run(main())
