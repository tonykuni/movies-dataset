from pathlib import Path
import ast
import hashlib
import importlib.util
import json
import sqlite3
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT/'deliverables/VIA_NLP_OneEngine_v1_9_0.py'

def def_run():
    spec=importlib.util.spec_from_file_location('via19',ENGINE)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    cfg=m.def_config()
    tests=[]
    def check(name,ok):
        tests.append({'name':name,'status':'PASS' if ok else 'FAIL'})
    samples=[
        '收益率-3.50%，EPS +12.0，00981A.TW，2330 TT，2026/09/27，FY2027',
        '```python\na = "你好,世界!"\n```\r\n另一段,內文!',
        '<script>\nalert("你好,世界!")\n</script>\n正文,文字!',
        '價格 | 數值\n---|---\n台積電 | 1,250.00\n',
        '甲\ue000\ue001乙👩‍💻，全文不該吞字。',
        '他說:“外層‘內層中文’結束。”',
    ]
    for i,s in enumerate(samples):
        r=m.def_process(s,cfg)
        check(f'edge_{i}_facts',m.def_facts(s)==m.def_facts(r['processed_text']))
        check(f'edge_{i}_idempotence',m.def_process(r['processed_text'],cfg)['processed_text']==r['processed_text'])
    check('html_script_untouched','alert("你好,世界!")' in m.def_process(samples[2],cfg)['processed_text'])
    check('unfenced_assignment_untouched',m.def_process('value = "你好,世界!"',cfg)['processed_text']=='value = "你好,世界!"')
    huge='```text\n'+'x'*2000+'\n```\n後續內容。'
    c=m.def_chunks(huge,cfg)
    check('oversize_code_explicit',any(x['oversize_protected_span'] for x in c))
    check('oversize_code_not_cut',c[0]['text'].startswith('```text') and c[0]['text'].endswith('```\n'))
    for size in (1,2,7,128,801,4000):
        text=('甲乙丙丁。Dr. Smith EPS 12.50。\n'*300)[:size]
        chunks=m.def_chunks(text,{**cfg,'chunk_chars':37,'overlap_chars':8})
        ranges=set()
        for part in chunks:
            ranges.update(range(part['start'],part['end']))
        check(f'coverage_{size}',len(ranges)==len(text) and all(part['text']==text[part['start']:part['end']] for part in chunks))
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        source=root/'records.jsonl'
        source.write_text('\n'.join(m.def_json({'id':i,'text':'你好,世界! EPS 12.50元。'}) for i in range(20))+'\n',encoding='utf-8')
        a=m.def_batch(source,root/'one',{**cfg,'workers':1})
        b=m.def_batch(source,root/'four',{**cfg,'workers':4})
        check('worker_output_equivalence',(Path(a['output'])/'records.jsonl').read_bytes()==(Path(b['output'])/'records.jsonl').read_bytes())
        cache=sqlite3.connect(root/'one/checkpoint.sqlite3')
        previous='0'*64
        chain=True
        for prev,digest,payload in cache.execute('SELECT previous,digest,payload FROM events ORDER BY seq'):
            chain &= prev==previous and digest==m.def_sha(prev+payload)
            previous=digest
        check('append_event_chain',chain)
        cache.close()
        pii=root/'pii.jsonl'
        pii.write_text(m.def_json({'text':'電話0912345678，A123456789','email':'a@example.test'})+'\n',encoding='utf-8')
        p=m.def_batch(pii,root/'private',{**cfg,'redact':True})
        output=(Path(p['output'])/'records.jsonl').read_text()
        check('batch_privacy_metadata_omitted',all(s not in output for s in ('0912345678','A123456789','a@example.test')))
        fake=m.def_minhash_bands
        m.def_minhash_bands=lambda shingles,cfg:['forced-collision']*cfg['bands']
        collision=root/'collision.jsonl'
        collision.write_text('\n'.join(m.def_json({'text':t}) for t in ('abcd','bcde','cdef','zzzz'))+'\n',encoding='utf-8')
        d=m.def_dedup(collision,root/'collision',{**cfg,'ngram':1,'min_near_chars':1,'threshold':.6,'near_action':'project'})
        check('collision_requires_exact_jaccard',d['counts'].get('KEEP')==3 and d['counts'].get('DUPLICATE')==1)
        retained=(Path(d['output'])/'retained.jsonl').read_text()
        check('no_transitive_false_merge','cdef' in retained and 'zzzz' in retained)
        longest=root/'longest.jsonl'
        longest.write_text('\n'.join(m.def_json({'text':t}) for t in ('abcd','abcde'))+'\n',encoding='utf-8')
        d=m.def_dedup(longest,root/'longest',{**cfg,'ngram':1,'min_near_chars':1,'threshold':.6,'keep':'longest','near_action':'project'})
        check('longest_representative',(Path(d['output'])/'retained.jsonl').read_text()==m.def_json({'text':'abcde'})+'\n')
        review=m.def_dedup(longest,root/'near_review',{**cfg,'ngram':1,'min_near_chars':1,'threshold':.6})
        check('near_matches_retained_by_default',review['counts'].get('NEAR_REVIEW')==1 and len((Path(review['output'])/'retained.jsonl').read_text().splitlines())==2)
        cap=m.def_dedup(collision,root/'cap',{**cfg,'ngram':1,'min_near_chars':1,'threshold':1.0,'candidate_limit':1})
        check('candidate_limit_not_success',cap['status']=='REVIEW' and cap['counts'].get('KEEP_REVIEW',0)>0)
        m.def_minhash_bands=fake
        snapshot=m.def_file_sha(source)
        check('source_still_readable',snapshot==hashlib.sha256(source.read_bytes()).hexdigest())
    payload=m.def_runtime(ROOT/'nlp_build/review_runtime')
    python_files=list(payload.rglob('*.py'))
    check('embedded_modules_ast_compile',all(compile(ast.parse(p.read_text(encoding='utf-8')),str(p),'exec') for p in python_files))
    legacy=m.def_legacy_analysis('台積電2330.TW預估EPS 12.50元，目標價1250元。\n風險是需求下降。',ROOT/'nlp_build/review_runtime','knowledge')
    check('integrated_knowledge_result',bool(legacy))
    md=m.def_markdown_analysis('| 項目 | 數值 |\n|---|---|\n|EPS|12.50|\n',ROOT/'nlp_build/review_runtime')
    check('integrated_markdown_table',md['summary']['tables']==1)
    report={'tests':tests,'counts':{'PASS':sum(t['status']=='PASS' for t in tests),'FAIL':sum(t['status']=='FAIL' for t in tests)},'embedded_python_files':len(python_files)}
    (ROOT/'nlp_build/regression.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('counts','embedded_python_files')}))
    return 1 if report['counts']['FAIL'] else 0

if __name__=='__main__':
    raise SystemExit(def_run())
