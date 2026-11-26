"""Behavioral fixtures for geometry, heading barriers and lossless table repair."""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import copy
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

# def 01_PARAMETERS
HERE=Path(__file__).resolve().parent
HUB_FILE=HERE.parent/'SUP_MDL743_GenericLayoutHub_v0104.py'
# [VIA:ACCEL-BRIDGE] Tests use the owning hub's initialized compatibility bridge.


def def_load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module


H=def_load(HUB_FILE,'unified_layout_test_hub')
C,T,B,F=(H.STAGES[k] for k in ('common','text','tables','figures'))


def def_line(name,text,box,page=1,size=10,role='BODY',bold=False):
    return {'id':name,'text':text,'raw_text':text,'bbox':box,'page':page,'size':size,'bold':bold,'role':role,'width':600,'height':800,'source_ids':[name],'fill':.99,'column':0,'base_role':'BODY','font':{}}


def def_word(name,text,x,y,width=30,page=1):
    return {'id':name,'text':text,'bbox':[x,y,x+width,y+10],'page':page,'size':10}


def def_table(name,rows,page=1,bbox=None,caption='Table 1: test'):
    cells=[[B.def_cell([def_word(f'{name}-{r}-{c}',str(v),c*100,r*15)],r,c) if v is not None else B.def_cell([],r,c) for c,v in enumerate(row)] for r,row in enumerate(rows)]
    return {'id':name,'kind':'TABLE','rows':cells,'header_count':1,'column_edges':[i*100 for i in range(len(rows[0])+1)],'page':page,'pages':[page],'width':600,'height':800,'bbox':bbox or [0,650,200,780],'caption':caption,'sources':[],'header_paths':[str(x) for x in rows[0]],'source_ids':[name],'repairs':[]}


class UnifiedLayoutTests(unittest.TestCase):
    def test_effective_api_has_one_runtime_owner(self):
        catalog=H.def_manifest();owners={'hub':H,'base':H._previous,'bridge':H._previous._previous}
        expected={name for key in owners for name in catalog['definitions'][key]['functions'] if not name.startswith('_')}
        self.assertEqual(set(catalog['effective_api']),expected)
        for name,record in catalog['effective_api'].items():
            module,function=record['binding'].split(':',1)
            self.assertIs(getattr(H,name),getattr(owners[module],function),name)

    def test_loader_reuses_refreshes_and_cleans_failure(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'module.py';name='layout_loader_identity_fixture'
            path.write_text('VALUE=1\n');first=H.def_load(path,name);self.assertIs(first,H.def_load(path,name))
            path.write_text('VALUE=2\n');second=H.def_load(path,name);self.assertIsNot(first,second);self.assertEqual(second.VALUE,2)
            path.write_text('raise RuntimeError("fixture")\n')
            with self.assertRaises(RuntimeError):H.def_load(path,name)
            self.assertNotIn(name,sys.modules)
            path.write_text('VALUE=3\n');self.assertEqual(H.def_load(path,name).VALUE,3);sys.modules.pop(name,None)

    def test_definition_index_has_exact_slice_hashes(self):
        import ast,hashlib
        catalog=H.def_manifest()
        for module,definition in catalog['definitions'].items():
            lines=(H.VIA/definition['source']).read_text().splitlines(keepends=True)
            self.assertEqual(len(definition['definition_index']),sum(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) for n in ast.walk(ast.parse(''.join(lines)))))
            for name,record in definition['definition_index'].items():
                text=''.join(lines[record['start_line']-1:record['end_line']])
                self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),record['sha256'],module+':'+name)

    def test_runtime_bundle_integrity_and_unsafe_paths(self):
        bundle=H.def_load(H.PARTS/'SUP_MDL743_LayoutBundle_v0100.py','via_layout_repair_v0100.bundle_test')
        catalog=H.def_manifest();runtime=set(catalog['bundle']['runtime_files'])
        self.assertTrue(set(catalog['modules'].values())<=runtime)
        self.assertTrue(all((H.VIA/p).is_file() for p in runtime))
        self.assertFalse(runtime&set(catalog['composition']['historical_files_not_runtime']))
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/'source';source.mkdir();(source/'engine.py').write_text('VALUE=1\n')
            manifest=bundle.def_copy_runtime(source,root/'runtime',['engine.py'])
            self.assertEqual(bundle.def_verify(root/'runtime',manifest)['state'],'VERIFIED')
            self.assertEqual(bundle.def_create_zip(root/'runtime',root/'engine.zip',manifest)['state'],'VERIFIED')
            (root/'runtime/engine.py').write_text('VALUE=2\n')
            self.assertEqual(bundle.def_verify(root/'runtime',manifest)['state'],'ERROR')
            with self.assertRaises(RuntimeError):bundle.def_create_zip(root/'runtime',root/'bad.zip',manifest)
            for name in ['../escape.py','/absolute.py','C:/absolute.py','folder\\escape.py']:
                with self.assertRaises(ValueError):bundle.def_relative(name)
            with self.assertRaises(ValueError):bundle.def_copy_runtime(source,root/'duplicate',['engine.py','ENGINE.py'])

    def test_label_baseline_offset_and_numeric_columns(self):
        words=[def_word('label','資產總計',10,23.1,width=70),def_word('a','5,029',100,20),def_word('b','6,334',170,20)]
        rows=B.def_table_rows(words);self.assertEqual(len(rows),1)
        matrix,cuts=B.def_project_rows(rows,[0,0,220,40])
        self.assertEqual([c['text'] for c in matrix[0]],['資產總計','5,029','6,334'])
        stacked=[def_word('v1','100',100,20),def_word('v2','200',100,23.1)]
        self.assertEqual(len(B.def_table_rows(stacked)),2)

    def test_statement_grid_and_asymmetric_stacks(self):
        words=[]
        for title,x,y in [('資產負債表',10,20),('現金流量表',10,280),('損益表',330,20),('比率分析',330,360)]:
            words.append(def_word(title,title,x,y,width=70))
            words.append(def_word(title+'unit','(百萬元)',x,y+20,width=65))
            for col,year in enumerate(['2023','2024','2025F']):words.append(def_word(title+year,year,x+90+col*65,y+20))
            for row,label in enumerate(['科目甲','科目乙']):
                words.append(def_word(title+label,label,x,y+43.1+row*20,width=65))
                for col,val in enumerate(['10','20','30']):words.append(def_word(title+label+val,val,x+90+col*65,y+40+row*20))
        seed={'id':'grid','kind':'TABLE','page':1,'bbox':[0,0,600,500],'width':600,'height':800,'source_ids':['grid']}
        regions=B.def_split_tables(seed,words,[]);self.assertEqual(len(regions),4)
        by={t['caption']:t for t in regions}
        self.assertLess(by['資產負債表']['clip_bbox'][3],280);self.assertLess(by['損益表']['clip_bbox'][3],360)
        self.assertGreater(by['損益表']['clip_bbox'][3],by['資產負債表']['clip_bbox'][3])
        document={'input_sha256':'fixture','layout':{'pages':[{'physical_page':1,'width':600,'height':800}]}}
        tables=B.def_recover_tables(document,words,[],[seed]);self.assertEqual(len(tables),4)
        for t in tables:self.assertEqual((len(t['rows']),len(t['rows'][0])),(3,4))
        self.assertTrue(all(g['type']=='INDEPENDENT' for g in B.def_adjacent(tables)[1]))

    def test_statement_title_needs_period_header(self):
        words=[def_word('title','資產負債表',0,0,width=80),def_word('a','說明',0,20),def_word('b','1',100,20),def_word('c','2',160,20)]
        seed={'id':'s','page':1,'bbox':[0,0,220,80],'source_ids':['s']}
        self.assertEqual(B.def_statement_regions(seed,words),[])

    def test_real_four_statement_grid(self):
        fixture=json.loads((HERE/'fixtures/ctbc_financial_grid_v0100.json').read_text())
        original=copy.deepcopy(fixture['words'])
        tables=B.def_recover_tables(fixture['document'],fixture['words'],fixture['lines'],fixture['seeds'])
        self.assertEqual(fixture['words'],original);self.assertEqual(len(tables),4)
        by={t['caption']:t for t in tables};self.assertEqual(set(by),set(fixture['expected']))
        used=[]
        for title,expected in fixture['expected'].items():
            table=by[title];actual=[[re.sub(r'\s+','',c['text']) for c in row] for row in table['rows']]
            self.assertEqual(actual,expected,title)
            self.assertEqual(table['header_count'],1)
            used += [s for row in table['rows'] for c in row for s in c['source_ids']]
        self.assertEqual(len(used),len(set(used)))
        self.assertNotIn('2013',[c['text'] for t in tables for row in t['rows'] for c in row])
        self.assertNotIn('384.10594',[c['text'] for t in tables for row in t['rows'] for c in row])
        rendered=H.def_tables_html(tables)
        self.assertEqual(rendered.count('class="table-card"'),4)
        self.assertEqual(rendered.count('class="statement-lane"'),2)
        self.assertLess(rendered.index('資產負債表'),rendered.index('現金流量表'))
        self.assertLess(rendered.index('損益表'),rendered.index('比率分析'))

    def test_locked_values(self):
        self.assertTrue(all(v['state']=='UNCHANGED' for v in H._previous.def_locked_sources(H._previous.def_policy()).values()))
        self.assertEqual(H._previous.gle().__file__,H.gle().__file__)

    def test_numeric_lossless(self):
        for raw,wanted in [(0,Decimal(0)),('0.00',Decimal(0)),('( 1,250.00 )',Decimal('-1250')),('−3.4%',Decimal('-3.4'))]:self.assertEqual(C.def_number(raw),wanted)
        for raw in [None,'','—','--','(12','12)','1,2,3','2026F','（12)','(12）']:
            self.assertIsNone(C.def_number(raw),raw)
        self.assertEqual(B.def_cell([def_word('w','( 1,250 )',0,0)],0,0)['raw'],'( 1,250 )')

    def test_font_and_overprint(self):
        a=def_line('a','標題',[10,10,60,20]);a['stroking_color']=0;a['non_stroking_color']=0
        self.assertFalse(T.def_font_evidence([a])[0]['bold'])
        b=copy.deepcopy(a);b['id']='b';b['source_ids']=['b'];b['bbox']=[10.2,10,60.2,20]
        out=T.def_font_evidence([a,b]);self.assertTrue(out[0]['bold']);self.assertEqual(out[1]['duplicate_of'],'a');self.assertFalse(a['bold'])
        self.assertTrue(T.def_font_evidence([a],[{'page':1,'bbox':a['bbox'],'render_mode':2}])[0]['bold'])

    def test_seven_roles_and_margin(self):
        lines=[def_line('title','Report',[20,20,400,45],size=19),def_line('h1','Heading',[20,100,200,115],size=15),def_line('h2','Heading two',[20,130,200,143],size=12.5),def_line('h3','Subheading',[20,160,200,172],size=10,bold=True),def_line('body','Normal body。',[20,190,500,202]),def_line('foot','small footnote',[20,760,200,768],size=8),def_line('disc','免責聲明',[20,400,200,412],page=10,size=11,bold=True),def_line('legal','法律文字',[20,430,500,438],page=10,size=8)]
        roles={l['id']:l['role'] for l in T.def_classify(lines,10,10)}
        self.assertEqual([roles[x] for x in ['title','h1','h2','h3','body','foot','disc']],['REPORT_TITLE','H1','H2','H3','BODY','PAGE_FOOTER','END_MATTER'])
        repeated=[def_line(str(p),'Research '+str(p),[10,10,100,20],page=p) for p in [1,2,3]]
        self.assertTrue(all(l['role']=='RUNNING_HEADER' for l in T.def_classify(repeated,10,3)))

    def test_heading_join_veto(self):
        a=def_line('a','unfinished clause',[20,100,290,112]);b=def_line('b','New heading',[20,116,200,128],role='H3')
        self.assertFalse(T.def_can_join(a,b));out=T.def_stitch([a,b]);self.assertEqual(len(out),2)
        b['role']='BODY';a['fill']=.4;self.assertFalse(T.def_can_join(a,b))
        a['text']='finished。';a['fill']=1;self.assertFalse(T.def_can_join(a,b))

    def test_cross_page_text(self):
        a=def_line('a','當需求增加，以及',[20,730,290,742]);b=def_line('b','供給持續成長。',[20,60,290,72],page=2)
        self.assertTrue(T.def_can_join(a,b));self.assertEqual(T.def_stitch([a,b])[0]['pages'],[1,2])
        b['page']=3;self.assertFalse(T.def_can_join(a,b));b['page']=2;b['role']='H1';self.assertFalse(T.def_can_join(a,b))
        b['role']='BODY';b['width']=800;self.assertFalse(T.def_can_join(a,b))

    def test_heading_tree_and_wrap(self):
        a=def_line('a','Very long heading',[20,50,590,62],role='H1',size=15);b=def_line('b','continued title',[20,66,200,78],role='H1',size=15)
        c=def_line('c','Body。',[20,110,550,122]);out=T.def_stitch([a,b,c])
        self.assertEqual(len(out),2);self.assertEqual(out[1]['parent_id'],out[0]['id']);self.assertIn('wrapped_heading',out[0]['repairs'])

    def test_floating_and_section_order(self):
        lines=[def_line('UL','UL',[30,100,285,112]),def_line('UR','UR',[320,100,570,112]),def_line('LL','LL',[30,500,285,512]),def_line('LR','LR',[320,500,570,512])]
        asset={'id':'chart','page':1,'bbox':[30,250,570,440],'kind':'FIGURE'}
        order,_=T.def_reading_order(copy.deepcopy(lines),[asset]);self.assertEqual([l['id'] for l in order],['UL','LL','UR','LR'])
        heading=def_line('H','new section',[30,460,570,475],role='H1')
        order,_=T.def_reading_order(copy.deepcopy(lines)+[heading],[asset]);self.assertEqual([l['id'] for l in order],['UL','UR','H','LL','LR'])

    def test_table_mask_and_context(self):
        table={'id':'table','kind':'TABLE','page':1,'bbox':[20,300,280,500]}
        other={'id':'next','kind':'TABLE','page':1,'bbox':[20,580,280,650]}
        lines=[def_line('cap','Table 1: EPS',[20,270,250,282]),def_line('wrong','Source: previous',[20,240,200,252]),def_line('inside','123 456',[20,340,250,352]),def_line('source','Source: company',[20,515,230,527]),def_line('stop','Table 2: other',[20,550,240,562]),def_line('far','unrelated',[350,290,550,302])]
        context=C.def_context(table,lines,[table,other]);self.assertEqual([l['id'] for l in context['above']],['cap']);self.assertEqual([l['id'] for l in context['below']],['source'])
        ordered,_=T.def_reading_order(lines,[table]);self.assertNotIn('inside',[l['id'] for l in ordered])

    def test_projection_preserves_middle_rating(self):
        words=[def_word('date','20250912',10,10,45),def_word('rating','Buy',80,10,25),def_word('tp','65.00',140,10,35)]
        matrix,edges=B.def_project_rows(C.def_word_rows(words),[10,10,175,20])
        self.assertEqual([c['text'] for c in matrix[0]],['20250912','Buy','65.00'])

    def test_header_only_seed_recovers_body(self):
        words=[]
        for r,values in enumerate([['EPS','2025F','2026F'],['Profit','0','(1,250)'],['Margin','12.5%','-0.5%']]):
            for c,v in enumerate(values):words.append(def_word(str((r,c)),v,c*100+10,r*20+100,40))
        seed={'id':'seed','kind':'TABLE','page':1,'bbox':[10,100,250,111],'width':600,'height':800,'source_ids':['seed'],'metadata':{}}
        doc={'input_sha256':'fixture','layout':{'pages':[{'physical_page':1,'width':600,'height':800}]}}
        tables=B.def_recover_tables(doc,words,[],[seed]);self.assertEqual(len(tables),1)
        self.assertEqual([[c['text'] for c in r] for r in tables[0]['rows']],[['EPS','2025F','2026F'],['Profit','0','(1,250)'],['Margin','12.5%','-0.5%']])

    def test_single_text_grid_is_not_confirmed_table(self):
        words=[def_word('a','正文第一行',10,20,width=180),def_word('b','正文第二行',10,35,width=180)]
        document={'input_sha256':'fixture','layout':{'pages':[{'physical_page':1,'width':600,'height':800}]}}
        seed={'id':'s','kind':'TABLE','page':1,'bbox':[0,10,200,50],'width':600,'height':800,'source_ids':['s']}
        result=B.def_recover_tables(document,words,[],[seed]);self.assertEqual(result[0]['state'],'UNCONFIRMED_TEXT_GRID')
        self.assertEqual([r[0]['text'] for r in result[0]['rows']],['正文第一行','正文第二行'])

    def test_spans_need_geometric_proof(self):
        t=def_table('t',[['Header',None],['A','B'],['x','1']]);t['header_count']=2;t['bbox']=[0,0,200,45]
        plain=B.def_spans_and_fragments(t);self.assertEqual(plain['rows'][0][0]['colspan'],1)
        source={'page':1,'bbox_pt':[0,0,200,12],'element_id':'physical-merged','raw_text':'Header'}
        merged=B.def_spans_and_fragments(t,[source]);self.assertEqual(merged['rows'][0][0]['colspan'],2)
        self.assertEqual(merged['rows'][0][1]['covered_by'],[0,0]);self.assertIn('colspan="2"',H.def_html_table(merged))

    def test_empty_axes_keep_fiscal_blanks_and_zero(self):
        table=def_table('ghost',[['Item',None,'2025','2026'],['A',None,'0',None],[None,None,None,None]])
        original=copy.deepcopy(table);fixed=B.def_spans_and_fragments(table)
        self.assertEqual(table,original);self.assertEqual(fixed['empty_axis_evidence']['columns'],[1])
        self.assertEqual(fixed['empty_axis_evidence']['rows'],[2]);self.assertEqual(len(fixed['rows'][0]),3)
        self.assertEqual(fixed['rows'][1][1]['number'],'0');self.assertEqual(fixed['rows'][1][2]['raw'],'')
        table['rows'][2][1]['bbox']=[100,30,110,40]
        preserved=B.def_spans_and_fragments(table);self.assertEqual(len(preserved['rows']),3);self.assertEqual(len(preserved['rows'][0]),4)

    def test_checksum_does_not_prove_completeness(self):
        table=def_table('t',[['Item','Value'],['A','1'],['B','2'],['Total','3']]);check=B.def_checksum(table)
        self.assertEqual(check['checks'][0]['state'],'MATCH');self.assertFalse(check['proves_complete'])
        table['rows'][-1][1]['number']='4';self.assertEqual(B.def_checksum(table)['checks'][0]['state'],'MISMATCH')

    def test_duplicate_proposals_not_duplicate_values(self):
        t=def_table('t',[['Item','2025'],['A','1']]);u=copy.deepcopy(t);u['id']='duplicate'
        self.assertEqual(len(B.def_deduplicate([t,u])),1)
        u=def_table('u',[['Item','2025'],['A','1']],page=2);self.assertEqual(len(B.def_deduplicate([t,u])),2)

    def test_continuation_and_heading_barrier(self):
        a=def_table('a',[['Item','Value'],['A','1']],bbox=[0,650,200,780]);b=def_table('b',[['Item','Value'],['B','2']],page=2,bbox=[0,20,200,150])
        out=B.def_continue_tables([a,b],[]);self.assertEqual(len(out),1);self.assertEqual(len(out[0]['rows']),3);self.assertEqual(out[0]['pages'],[1,2])
        guard=def_line('h','New section',[0,2,200,14],page=2,role='H1');self.assertEqual(len(B.def_continue_tables([a,b],[guard])),2)
        b['caption']='Table 2: different';self.assertEqual(len(B.def_continue_tables([a,b],[])),2)

    def test_side_by_side_types(self):
        a=def_table('a',[['Rank','Value'],['1','9'],['2','8']],bbox=[0,100,200,250]);b=def_table('b',[['Rank','Value'],['3','7'],['4','6']],bbox=[300,100,500,250])
        self.assertEqual(B.def_table_relation(a,b),'VERTICAL_UNROLL');self.assertEqual(len(B.def_adjacent([a,b])[1][0]['rows']),5)
        b['caption']='Table 2';self.assertEqual(B.def_table_relation(a,b),'INDEPENDENT')
        a['header_paths']=['Assets','2025'];b['header_paths']=['Liabilities','2025'];b['caption']=a['caption'];self.assertEqual(B.def_table_relation(a,b),'ACCOUNT_SECTIONS')
        a=def_table('a',[['Item','2024'],['A','1'],['B','2']]);b=def_table('b',[['2025','2026'],['3','4'],['5','6']]);self.assertEqual(B.def_table_relation(a,b),'HORIZONTAL_REJOIN')

    def test_stacked_table_split(self):
        seed={'id':'s','page':1,'kind':'TABLE','bbox':[0,0,300,300],'source_ids':['s']}
        words=[def_word('a','A',10,20),def_word('b','B',10,180)];captions=[def_line('cap','Table 2: next',[10,150,200,165])]
        parts=B.def_split_tables(seed,words,captions);self.assertEqual(len(parts),2);self.assertLess(parts[0]['bbox'][3],parts[1]['bbox'][1])

    def test_source_then_header_splits_table(self):
        seed={'id':'s','page':1,'kind':'TABLE','bbox':[0,0,300,100],'source_ids':['s']}
        words=[def_word('a','10',10,20),def_word('b','20',100,20),def_word('h','項目',10,60),def_word('y','年度',100,60),def_word('v','30',10,80),def_word('w','40',100,80)]
        source=def_line('source','Source: report',[0,40,280,50])
        self.assertEqual(len(B.def_split_tables(seed,words,[source])),2)
        source['text']='普通內文'
        self.assertEqual(len(B.def_split_tables(seed,words,[source])),1)

    def test_compound_figures_and_dual_axis(self):
        from PIL import Image,ImageDraw
        image=Image.new('RGB',(240,180),'white');draw=ImageDraw.Draw(image);draw.rectangle((10,20,100,150),outline='black',width=2);draw.rectangle((140,20,230,150),outline='black',width=2)
        self.assertEqual(len(F.def_split_canvas(image,[0,0,240,180])['panels']),2)
        draw.line((10,150,230,150),fill='black',width=3)
        self.assertEqual(len(F.def_split_canvas(image,[0,0,240,180])['panels']),1)

    def test_shared_legend_and_parent(self):
        from PIL import Image,ImageDraw
        image=Image.new('RGB',(240,240),'white');d=ImageDraw.Draw(image);d.rectangle((10,20,100,180),outline='black',width=2);d.rectangle((140,20,230,180),outline='black',width=2);d.rectangle((90,220,155,230),fill='black')
        split=F.def_split_canvas(image,[0,0,240,240]);self.assertEqual(len(split['panels']),2);self.assertEqual(len(split['shared_legend']),1)
        context={'above':[{'id':'cap','text':'Figure 1: comparison','bbox':[0,0,240,10]}],'below':[{'id':'s','text':'Source: report','bbox':[0,240,240,250]}]}
        panels=F.def_figure_metadata({'id':'parent'},context,split['panels']);self.assertTrue(all(p['parent_id']=='parent' and p['sources'] for p in panels))

    def test_ocr_roles_and_pair_ambiguity(self):
        words=[def_word('unit','TWD',80,2),def_word('left','10',1,45,10),def_word('right','20',180,45,10),def_word('year','2025',90,170,20),def_word('value','5.2',90,90,20)]
        result=F.def_ocr_roles(words,[0,0,200,200]);self.assertEqual(result['roles']['left_y_axis'][0]['id'],'left');self.assertEqual(result['roles']['right_y_axis'][0]['id'],'right');self.assertEqual(result['pair_candidates'][0]['state'],'CANDIDATE_SERIES_UNASSIGNED')

    def test_missing_ocr_not_success(self):
        with patch.object(F.shutil,'which',return_value=None):self.assertEqual(F.def_ocr_status()['state'],'UNAVAILABLE')

    def test_catalog_is_complete_and_static(self):
        catalog=H.def_manifest();self.assertEqual(len(catalog['capabilities']),46);self.assertFalse(catalog['errors']);self.assertEqual(len(catalog['snippet_crosswalk']),31)
        self.assertTrue(all(c['implementation_state']=='IMPLEMENTED' for c in catalog['capabilities']))
        manager=def_load(H.VIA/'supportive modules/registry/CGC_MDL069_SystemManager_v0114.py','layout_test_manager')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);engine=root/'engine.py';ssot=root/'catalog.json'
            engine.write_text('ENGINE_MANIFEST = {"capability_ssot":"catalog.json"}\nraise RuntimeError("MUST NOT EXECUTE")\n')
            ssot.write_text(json.dumps({'modules':{},'capabilities':[]}))
            with patch.object(manager,'VIA',root):self.assertEqual(manager.def_engine_catalog(engine)['state'],'REGISTERABLE')

    def test_render_escapes_raw_text(self):
        table=def_table('t',[['<script>','2025'],['A&','0']]);render=H.def_html_table(table)
        self.assertNotIn('<script>',render);self.assertIn('&lt;script&gt;',render);self.assertIn('>0</td>',render)
        self.assertEqual(table['rows'][0][0]['raw'],'<script>')

    def test_fragment_retention(self):
        assets=[{'id':'tiny','kind':'FIGURE','page':1,'bbox':[0,0,5,5],'source_ids':['tiny']},{'id':'chart','kind':'FIGURE','page':1,'bbox':[100,100,300,300],'source_ids':['chart']}]
        figures,fragments=F.def_compact_assets(assets);self.assertEqual(len(figures),1);self.assertEqual(fragments[0]['id'],'tiny')

    def test_rowspan_and_wrapped_cell_evidence(self):
        t=def_table('t',[['Header','2025'],['continued','2026'],['A','1']]);t['header_count']=2;t['bbox']=[0,0,200,45]
        source={'page':1,'bbox_pt':[0,0,99,28],'element_id':'vertical-cell','raw_text':'Header continued'}
        result=B.def_spans_and_fragments(t,[source]);self.assertEqual(result['rows'][0][0]['rowspan'],2)
        self.assertIn('rowspan="2"',H.def_html_table(result));self.assertEqual(t['rows'][1][0]['raw'],'continued')

    def test_split_row_continuation_keeps_evidence(self):
        a=def_table('a',[['Item','Value'],['Long item',None]],bbox=[0,650,200,790]);a['rows'][-1][0]['bbox']=[0,775,60,787]
        b=def_table('b',[['Item','Value'],[None,'5']],page=2,bbox=[0,20,200,150]);b['rows'][1][1]['bbox']=[100,80,130,90]
        merged=B.def_continue_tables([a,b],[])[0]
        self.assertEqual([c['text'] for c in merged['rows'][-1]],['Long item','5']);self.assertIn('boundary_row_evidence',merged)

    def test_scoped_registry_preserves_unrelated_and_stable_ids(self):
        console=def_load(H.VIA/'supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0148.py','layout_test_console')
        seed={'schema':'VIA.ComponentInventory.v1','counters':{'MDL':8000,'FNC':8000,'FNT':8000},'records':[{'key':'module|Unrelated','category':'module','identity':'Unrelated','source':'not-downloaded.py','code':'VIA-MDL-8000','state':'ACTIVE'}]}
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'registry.json';p.write_text(json.dumps(seed))
            first=console.def_registry_layout(True,p);result=json.loads(p.read_text())
            old=next(r for r in result['records'] if r['key']=='module|Unrelated');self.assertEqual(old,seed['records'][0]);self.assertEqual(first['stale'],0)
            codes={r['key']:r['code'] for r in result['records']};second=console.def_registry_layout(True,p)
            self.assertEqual(second['new'],0);self.assertEqual(second['stale'],0);self.assertEqual(codes,{r['key']:r['code'] for r in json.loads(p.read_text())['records']})
            features=[r for r in result['records'] if r['identity'].startswith('layout/LAYOUT.')];self.assertEqual(len(features),46)

    def test_all_gate_stages_precede_layout(self):
        console=def_load(H.VIA/'supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0148.py','layout_gates_console')
        with patch.object(console.body,'require_token_gate',return_value=2),patch.object(console.prev,'def_layout_hub',return_value=H),patch.object(H,'def_run_batch') as run:
            self.assertEqual(console.main(['layout']),2);run.assert_not_called()

    def test_cache_resume_and_filename_order(self):
        with tempfile.TemporaryDirectory() as td:
            source=Path(td)/'input';source.mkdir();out=Path(td)/'output'
            for name in ['B.PDF','a.pdf']:(source/name).write_bytes(name.encode())
            docs=[{'filename':p.name,'input_sha256':H._previous.def_sha(p),'signature':p.name} for p in source.iterdir()]
            def report(*args):return {'documents':copy.deepcopy(docs),'errors':[],'financial_database_written':False}
            with patch.object(H._previous,'def_run_batch',side_effect=report),patch.object(H,'def_repair_document',return_value={'figures':[]}) as repair,patch.object(H,'def_export'):
                first=H.def_run_batch(source,out);second=H.def_run_batch(source,out)
                self.assertEqual([d['filename'] for d in first['documents']],['a.pdf','B.PDF'])
                self.assertEqual(repair.call_count,2);self.assertEqual(second['repair_cache_hits'],2)

    def test_evidence_cannot_skip_an_input_document(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/'input';source.mkdir();(source/'a.pdf').write_bytes(b'one');(source/'b.pdf').write_bytes(b'two')
            evidence=root/'evidence.json';evidence.write_text(json.dumps({'documents':[{'input_sha256':H._previous.def_sha(source/'a.pdf'),'filename':'a.pdf'}]}))
            with self.assertRaisesRegex(RuntimeError,'INPUT_EVIDENCE_SET_MISMATCH'):H.def_run_batch(source,root/'output',evidence)

    def test_corrupt_or_incomplete_checkpoint_is_not_success(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'REPAIRED.json';p.write_text('{broken')
            self.assertIsNone(H.def_cached_repair(p))
            p.write_text(json.dumps({'figures':[{'panels':[{'image_path':str(Path(td)/'missing.png')}]}]}))
            self.assertIsNone(H.def_cached_repair(p))

    def test_manager_user_same_features(self):
        catalog=H.def_manifest();render=H.def_catalog_html(catalog)
        manager=def_load(H.VIA/'supportive modules/registry/CGC_MDL069_SystemManager_v0114.py','layout_manager_render_test')
        admin=manager.def_catalog_html(catalog)
        self.assertIn(admin,render)
        for module in catalog['modules']:self.assertIn('<td>'+module+'</td>',admin)
        for feature in catalog['capabilities']:
            self.assertIn(feature['id'],render);self.assertIn(feature['id'],admin)

    def test_export_formats_preserve_values(self):
        import csv
        table=def_table('t',[['Item','Value'],['Zero','0'],['Blank',None],['Negative','(1.20)']])
        repair={'tables':[table],'figures':[],'text':{'paragraphs':[{'role':'BODY','text':'A&B。'}]},'ocr':{'state':'UNAVAILABLE'}}
        report={'documents':[{'filename':'fixture.pdf','repair':repair}],'errors':[]}
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)
            def render(data,path):path.write_text('<html><main><h2>fixture.pdf</h2></main></html>')
            with patch.object(H._previous,'def_render',side_effect=render):H.def_export(report,out,H.def_manifest())
            with (out/'LAYOUT_REPAIRED.csv').open(encoding='utf-8-sig') as handle:rows=list(csv.DictReader(handle))
            self.assertEqual([r['raw'] for r in rows if r['column']=='1'],['Value','0','','(1.20)'])
            self.assertIn('<table>',(out/'LAYOUT_REPAIRED.md').read_text());self.assertIn('A&amp;B',(out/H.HTML_NAME).read_text())
            self.assertEqual(len(json.loads((out/'ENGINE_CATALOG.json').read_text())['capabilities']),46)

    def test_figure_ocr_english_backend(self):
        from PIL import Image,ImageDraw,ImageFont
        if not F.shutil.which('tesseract'):self.skipTest('local tesseract absent')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);picture=root/'source.png';image=Image.new('RGB',(800,300),'white')
            font=ImageFont.truetype('DejaVuSans.ttf',36);ImageDraw.Draw(image).text((90,120),'Revenue 123.45',font=font,fill='black');image.save(picture)
            document={'layout':{'pages':[{'physical_page':1,'width':400,'height':150,'image_path':str(picture)}]}}
            asset={'id':'figure','kind':'FIGURE','page':1,'bbox':[20,20,380,130],'source_ids':['figure']}
            with patch.dict(F.PARAMS,{'ocr_languages':'eng'}):
                result=F.def_figures(document,[],[],[asset],root/'out',H.gle(),{'state':'AVAILABLE','languages':['eng']})
            text=' '.join(w['text'] for p in result[0]['panels'] for w in p['words'])
            self.assertIn('123.45',text);self.assertTrue(all(p['ocr_state']=='REVIEW' for p in result[0]['panels']))


if __name__=='__main__':unittest.main()
