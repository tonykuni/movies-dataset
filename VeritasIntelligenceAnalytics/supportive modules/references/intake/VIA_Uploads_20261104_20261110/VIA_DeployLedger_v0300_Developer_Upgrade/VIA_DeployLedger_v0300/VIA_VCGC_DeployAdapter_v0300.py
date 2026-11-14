from __future__ import annotations
"""VCGC deployment receipt adapter; no install permission / network bypass.
VIA:ACCEL-BRIDGE uses the same bounded, resource-budgeted runner as DeployLedger.
"""
# def PARAMETERS
SCHEMA = 'via.vcgc-deploy-probes.v3'
REQUIRED_AUDITS = {'environment','ssot','regex','synonyms','registry','network'}
import argparse
import json
import os
import re
from pathlib import Path
import VIA_DeployLedger_v0300 as d


def get_field(doc, dotted):
    for name in dotted.split('.'):
        doc = doc[name]
    return doc


def probe(spec, cwd):
    tool = Path(spec['tool']).resolve()
    if d.sha(tool) != spec['sha256']:
        raise ValueError('VCGC probe tool hash changed')
    command = spec['command']
    if str(tool) not in [str(Path(x).resolve()) for x in command if not x.startswith('-')]:
        raise ValueError('Pinned tool must appear in the exact command argv')
    report = Path(spec['report']) if spec.get('report') else None
    previous = (report.stat().st_mtime_ns, d.sha(report)) if report and report.is_file() else None
    result = d.run(command, cwd, spec.get('timeout',600))
    output = result['stdout_tail'] + result['stderr_tail']
    if spec.get('parser') == 'install_gate_doctor_v0104':
        # Source-confirmed behavior: GREEN_SHADOWED returns exit 1 in v0104.
        matches = re.findall(r'\[裁決\]\s+(GREEN_SHADOWED|GREEN|RED_COLLISION|RED_IMPORT|YELLOW_ABSENT)\b',output)
        if not matches or matches[-1] not in {'GREEN','GREEN_SHADOWED'} or result['timed_out'] or result['output_limited'] or result['exit_code'] not in {0,1}:
            raise ValueError('VCGC InstallGate doctor did not pass')
        return {'category':spec['category'],'status':matches[-1],'tool_sha256':spec['sha256'],'result':result}
    if not result['ok'] or not report or not report.is_file():
        raise ValueError('VCGC probe failed / structured report missing')
    if previous == (report.stat().st_mtime_ns,d.sha(report)):
        raise ValueError('Stale VCGC report cannot be reused')
    doc=d.read(report)
    if get_field(doc,spec['status_path']) not in spec['pass_values']:
        raise ValueError('VCGC structured status is not passing')
    conflicts = get_field(doc,spec['conflicts_path'])
    if conflicts != []:
        raise ValueError('VCGC conflicts remain or are not represented by an empty list')
    if spec['category']=='accelerator':
        threads=get_field(doc,spec['threads_path'])
        if type(threads) is not int or threads < 1:
            raise ValueError('Accelerator has no verified active thread budget')
    return {'category':spec['category'],'status':'PASS','tool_sha256':spec['sha256'],'report_sha256':d.sha(report),'result':result}


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--config',required=True)
    p.add_argument('--mode',choices=['audit','accelerator'],required=True)
    a=p.parse_args(argv)
    try:
        config=d.read(a.config)
        if config.get('schema') != SCHEMA:
            raise ValueError('VCGC probes contract v3 required')
        selected=[s for s in config['probes'] if (s['category']=='accelerator') == (a.mode=='accelerator')]
        categories={s['category'] for s in selected}
        required={'accelerator'} if a.mode=='accelerator' else REQUIRED_AUDITS
        if not required <= categories:
            raise ValueError('Missing real VCGC probes: '+str(sorted(required-categories)))
        result=[probe(s,config['root']) for s in selected]
        destination=os.environ['VIA_DEPLOY_RECEIPT']
        receipt={'schema':'via.vcgc-deploy-receipt.v3','status':'PASS','conflicts':[],'nonce':os.environ['VIA_DEPLOY_NONCE'],'binding':os.environ['VIA_DEPLOY_BINDING'],'probes':result,'network_consent_changed':False}
        d.write(destination,receipt)
        print(json.dumps({'status':'PASS','probes':len(result)}))
        return 0
    except Exception as exc:
        print(json.dumps({'status':'BLOCKED','error':str(exc)},ensure_ascii=False))
        return 2


if __name__=='__main__':raise SystemExit(main())
