"""VRN_TableGeometry v0101 — 薄尾(VRN 2026-10-10):只在檔頭加入加速器橋(找不到加速器 = 不改任何行為);其餘與 v0100 相同。"""
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====
PARAMS = {
    'version': 'v0101', 'up_lines': 4, 'down_lines': 3,
    'row_tolerance_pt': 2.4, 'edge_snap_pt': 0.5, 'clip_epsilon_pt': 0.15,
    'context_padding_pt': 1.0, 'max_tables_per_page': 30,
    'auto_min_rows': 3, 'auto_min_cols': 2, 'numeric_context_ratio':0.4,
    'boundary_padding_pt':0.05, 'max_grid_slots':10000, 'white_pixel_min':255, 'visibility_render_scale':2,
    'year_pattern':r'^(?:FY)?(?:19|20)\d{2}(?:A|E|F|CT)?$',
    'contact_pattern':r'@|\(?(?:852|886)\)?[ -]+\d|\+?(?:852|886)[ -]',
    'source_pattern': r'^(?:source|sources|note|notes|資料來源|來源|註|注)\s*[:：.]?',
    'number_pattern': r'^[+\-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?$',
}
import math
import re
import statistics
import unicodedata


def def_normalize(text):
    text=unicodedata.normalize('NFKC',str(text or '')).replace('\u2212','-')
    text='\n'.join(re.sub(r'[^\S\n]+',' ',line).strip() for line in text.splitlines()).strip()
    return re.sub(r'(?<=[\u3400-\u9fff]) +(?=[\u3400-\u9fff])','',text)


def def_key(text):
    return re.sub(r'\s+','',def_normalize(text))


def def_inside(word,box):
    cx=(word['bbox'][0]+word['bbox'][2])/2;cy=(word['bbox'][1]+word['bbox'][3])/2
    return box[0]<=cx<box[2] and box[1]<=cy<box[3]


def def_union(boxes):
    return [min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)]


def def_lines(words):
    rows=[]
    for word in sorted(words,key=lambda w:((w['bbox'][1]+w['bbox'][3])/2,w['bbox'][0])):
        center=(word['bbox'][1]+word['bbox'][3])/2
        if rows and abs(center-statistics.median((w['bbox'][1]+w['bbox'][3])/2 for w in rows[-1]))<=PARAMS['row_tolerance_pt']:
            rows[-1].append(word)
        else:rows.append([word])
    return [sorted(row,key=lambda w:w['bbox'][0]) for row in rows]


def def_text(words):
    return '\n'.join(' '.join(w['text'] for w in line) for line in def_lines(words))


def def_read_page(native,plumber):
    import fitz
    words=[{'id':i,'bbox':list(w[:4]),'text':w[4],'visibility':'VISIBLE_OR_UNASSESSED'} for i,w in enumerate(native.get_text('words',sort=True))]
    white_spans=[span for block in native.get_text('dict')['blocks'] for line in block.get('lines',[]) for span in line['spans'] if span.get('color')==0xFFFFFF]
    for word in words:
        if any(def_inside(word,span['bbox']) for span in white_spans):
            pixels=native.get_pixmap(matrix=fitz.Matrix(PARAMS['visibility_render_scale'],PARAMS['visibility_render_scale']),clip=fitz.Rect(word['bbox']),colorspace=fitz.csRGB,alpha=False)
            if pixels.samples and min(pixels.samples)>=PARAMS['white_pixel_min']:
                word['visibility']='EXCLUDED_WHITE_ON_WHITE'
                word['visibility_evidence']={'text_color':'FFFFFF','render_min_rgb':min(pixels.samples),'scale':PARAMS['visibility_render_scale']}
    hidden=[w for w in words if w['visibility']=='EXCLUDED_WHITE_ON_WHITE']
    other=[{'id':i,'bbox':[w['x0'],w['top'],w['x1'],w['bottom']],'text':w['text']} for i,w in enumerate(plumber.extract_words(x_tolerance=1,y_tolerance=2))]
    other=[w for w in other if not any(def_inside(w,h['bbox']) for h in hidden)]
    return words,other


def def_validate_layout(table,width,height):
    cells=table['cells'];rows=table['rows'];cols=table['cols']
    if type(rows) is not int or type(cols) is not int or rows<=0 or cols<=0 or rows*cols>PARAMS['max_grid_slots']:raise ValueError('INVALID_GRID_SIZE')
    slots={};ids=set()
    for cell in cells:
        for field in ['row','col','rowspan','colspan']:
            if type(cell.get(field,1 if 'span' in field else None)) is not int:raise ValueError('INVALID_CELL_INDEX')
        r,c=cell['row'],cell['col'];rs,cs=cell.get('rowspan',1),cell.get('colspan',1)
        if min(r,c)<0 or min(rs,cs)<1 or r+rs>rows or c+cs>cols:raise ValueError('SPAN_OUTSIDE_GRID')
        key=f'R{r}C{c}'
        if key in ids:raise ValueError('DUPLICATE_CELL_ID')
        ids.add(key);cell['id']=key;cell['rowspan']=rs;cell['colspan']=cs
        b=cell['bbox']
        if len(b)!=4 or not all(isinstance(x,(int,float)) and math.isfinite(x) for x in b) or not(0<=b[0]<b[2]<=width and 0<=b[1]<b[3]<=height):raise ValueError('INVALID_CELL_BBOX: '+key)
        for rr in range(r,r+rs):
            for cc in range(c,c+cs):
                if (rr,cc) in slots:raise ValueError('OVERLAPPING_MERGED_CELLS')
                slots[(rr,cc)]=key
    if len(slots)!=rows*cols:raise ValueError('UNEXPLAINED_GRID_HOLE')
    return slots


def def_snap(values):
    groups=[]
    for value in sorted(set(values)):
        if groups and value-groups[-1][-1]<=PARAMS['edge_snap_pt']:groups[-1].append(value)
        else:groups.append([value])
    return [statistics.mean(g) for g in groups]


def def_auto_tables(page):
    """Layout candidates only; neither finder nor dual-reader agreement proves structure."""
    proposals=[];notes=[]
    for strategy in ['lines','text']:
        try:found=page.find_tables(strategy=strategy).tables
        except Exception as exc:
            notes.append({'strategy':strategy,'error':type(exc).__name__+': '+str(exc)});continue
        for candidate in found[:PARAMS['max_tables_per_page']]:
            boxes=[list(b) for b in candidate.cells if b]
            if not boxes:continue
            xs=def_snap([x for b in boxes for x in (b[0],b[2])]);ys=def_snap([y for b in boxes for y in (b[1],b[3])])
            if len(xs)-1<PARAMS['auto_min_cols'] or len(ys)-1<PARAMS['auto_min_rows']:continue
            cells=[]
            for b in boxes:
                c0=min(range(len(xs)),key=lambda i:abs(xs[i]-b[0]));c1=min(range(len(xs)),key=lambda i:abs(xs[i]-b[2]))
                r0=min(range(len(ys)),key=lambda i:abs(ys[i]-b[1]));r1=min(range(len(ys)),key=lambda i:abs(ys[i]-b[3]))
                cells.append({'row':r0,'col':c0,'rowspan':r1-r0,'colspan':c1-c0,'bbox':b})
            proposals.append({'id':f'P{page.number+1}-AUTO{len(proposals)+1}','page':page.number+1,'bbox':list(candidate.bbox),'rows':len(ys)-1,'cols':len(xs)-1,'cells':cells,'structure_origin':'PYMUPDF_'+strategy.upper(),'header_rows':[]})
        if proposals:break
    return proposals,notes


def def_context(words,table,neighbor_boxes):
    core=def_union([c['bbox'] for c in table['cells']]);lane=table.get('lane_bbox',core)
    lane_words=[w for w in words if lane[0]<=(w['bbox'][0]+w['bbox'][2])/2<lane[2]]
    rows=def_lines(lane_words)
    before=[r for r in rows if max(w['bbox'][3] for w in r)<=core[1]][-PARAMS['up_lines']:]
    after=[r for r in rows if min(w['bbox'][1] for w in r)>=core[3]][:PARAMS['down_lines']]
    result=[]
    for side,lines in [('ABOVE',before),('BELOW',after)]:
        for line in lines:
            text=def_text(line);bbox=def_union([w['bbox'] for w in line])
            overlaps=[region for region in neighbor_boxes if any(def_inside(w,region['bbox'] if isinstance(region,dict) else region) for w in line)]
            neighbor=bool(overlaps)
            neighbor_role='NEIGHBOR_FIGURE' if any(isinstance(r,dict) and r.get('kind')=='FIGURE' for r in overlaps) else 'NEIGHBOR_TABLE'
            numbers=sum(bool(re.fullmatch(PARAMS['number_pattern'],w['text'].strip('()'))) for w in line)
            years=sum(bool(re.fullmatch(PARAMS['year_pattern'],w['text'],re.I)) for w in line)
            role=neighbor_role if neighbor else 'SOURCE_OR_NOTE' if re.search(PARAMS['source_pattern'],text,re.I) else 'CONTACT_METADATA' if re.search(PARAMS['contact_pattern'],text) else 'TABLE_HEADER_CONTEXT' if years>=2 else 'POSSIBLE_MISSING_TABLE_ROW' if numbers>=2 and numbers/max(1,len(line))>=PARAMS['numeric_context_ratio'] else 'CONTEXT_TEXT'
            result.append({'side':side,'role':role,'bbox':bbox,'text':text,'word_ids':[w['id'] for w in line]})
    inspect=def_union([core]+[x['bbox'] for x in result])
    return core,inspect,result



def def_adjust_word_boundaries(table,words):
    """Move only a shared divider into observed whitespace, preserving word ownership."""
    repairs=[]
    if table.get('physical_grid') or table.get('structure_origin')=='PYMUPDF_LINES':return repairs
    for row in range(table['rows']):
        cells=sorted([c for c in table['cells'] if c['row']==row and c['rowspan']==1],key=lambda c:c['col'])
        for left,right in zip(cells,cells[1:]):
            if left['col']+left['colspan']!=right['col'] or abs(left['bbox'][2]-right['bbox'][0])>PARAMS['edge_snap_pt']:continue
            a=[w for w in words if def_inside(w,left['bbox'])];b=[w for w in words if def_inside(w,right['bbox'])]
            boundary=left['bbox'][2];pad=PARAMS['boundary_padding_pt']
            lo=max([w['bbox'][2]+pad for w in a],default=left['bbox'][0]+pad)
            hi=min([w['bbox'][0]-pad for w in b],default=right['bbox'][2]-pad)
            if lo>=hi or lo<=boundary<=hi:continue
            new=(lo+hi)/2
            if not left['bbox'][0]<new<right['bbox'][2]:continue
            old=boundary;left['bbox'][2]=new;right['bbox'][0]=new
            # New dividers must retain every prior center assignment.
            if not all(def_inside(w,left['bbox']) for w in a) or not all(def_inside(w,right['bbox']) for w in b):
                left['bbox'][2]=old;right['bbox'][0]=old;continue
            repairs.append({'action':'MOVE_DIVIDER_TO_SOURCE_WHITESPACE','row':row,'left':left['id'],'right':right['id'],'before':old,'after':new,'basis':'Observed native word bounds; no gold values consulted'})
    return repairs

def def_repair_table(table,words,other,page_size,neighbor_boxes):
    hidden=[w for w in words if w.get('visibility')=='EXCLUDED_WHITE_ON_WHITE']
    words=[w for w in words if w.get('visibility')!='EXCLUDED_WHITE_ON_WHITE']
    slots=def_validate_layout(table,*page_size)
    edge_repairs=def_adjust_word_boundaries(table,words)
    core,inspect,context=def_context(words,table,neighbor_boxes)
    issues=[];repairs=edge_repairs;used={};result=[]
    if any(abs(a-b)>PARAMS['clip_epsilon_pt'] for a,b in zip(core,table['bbox'])):
        repairs.append({'action':'RESTORE_LAYOUT_EXTENT','before_bbox':table['bbox'],'after_bbox':core,'basis':'Union of layout cell rectangles; no new source values invented'})
    for cell in table['cells']:
        chosen=[w for w in words if def_inside(w,cell['bbox'])]
        second=[w for w in other if def_inside(w,cell['bbox'])]
        text=def_text(chosen);alternate=def_text(second)
        flags=[]
        for word in chosen:
            used.setdefault(word['id'],[]).append(cell['id'])
            b=word['bbox'];c=cell['bbox'];e=PARAMS['clip_epsilon_pt']
            if b[0]<c[0]-e or b[1]<c[1]-e or b[2]>c[2]+e or b[3]>c[3]+e:flags.append('GLYPH_CROSSES_CELL_BOUNDARY')
        if def_key(text)!=def_key(alternate):flags.append('READERS_DISAGREE')
        if '\ufffd' in text or '\x00' in text:flags.append('INVALID_GLYPH')
        if re.search(r'\d[ \t]+\d',text) and all(re.fullmatch(r'[\d\s,.()%+\-]+',line or 'x') for line in text.splitlines()):flags.append('AMBIGUOUS_SPACED_NUMBER')
        flags=sorted(set(flags));issues.extend({'cell':cell['id'],'code':f} for f in flags)
        result.append({**cell,'raw_text':text,'text':def_normalize(text),'comparison_key':def_key(text),'alternate_text':alternate,
                       'word_ids':[w['id'] for w in chosen],'word_boxes':[w['bbox'] for w in chosen],
                       'empty_kind':'PRINTED_EMPTY' if not text else 'PRINTED_TEXT','reader_status':'PASS' if not flags else 'REVIEW','issues':flags})
    for word in words:
        if def_inside(word,core) and word['id'] not in used:issues.append({'word_id':word['id'],'code':'UNASSIGNED_SOURCE_WORD_IN_TABLE'})
    for key,owners in used.items():
        if len(owners)>1:issues.append({'word_id':key,'code':'MULTIPLE_CELL_OWNERS','owners':owners})
    if any(x['role']=='POSSIBLE_MISSING_TABLE_ROW' for x in context):issues.append({'code':'CONTEXT_HAS_POSSIBLE_OMITTED_ROW'})
    if not any(c['raw_text'] for c in result):issues.append({'code':'NO_TEXT_NEEDS_OCR'})
    excluded_words=[w for w in hidden if def_inside(w,core)]
    ghost_rows=[]
    for r in range(table['rows']):
        rowcells=[c for c in result if c['row']<=r<c['row']+c['rowspan']]
        if rowcells and all(c['rowspan']==1 and not c['raw_text'] for c in rowcells) and any(any(def_inside(w,c['bbox']) for c in rowcells) for w in excluded_words) and not table.get('physical_grid') and table.get('structure_origin')!='PYMUPDF_LINES':ghost_rows.append(r)
    if ghost_rows:
        result=[c for c in result if c['row'] not in ghost_rows]
        id_map={}
        for c in result:
            old_id=c['id'];c['source_layout_row']=c['row'];c['row']-=sum(r<c['row'] for r in ghost_rows);c['id']=f"R{c['row']}C{c['col']}";id_map[old_id]=c['id']
        for rule in table.get('equations',[]):
            rule['inputs']=[id_map.get(k,k) for k in rule['inputs']];rule['target']=id_map.get(rule['target'],rule['target'])
        table['rows']-=len(ghost_rows)
        slots=def_validate_layout({**table,'cells':result},*page_size)
        repairs.append({'action':'REMOVE_CONFIRMED_HIDDEN_TEXT_ONLY_ROWS','original_rows':ghost_rows,'basis':'Only white-on-white words; all visible cells empty; physical blank grid rows preserved'})
        core=def_union([c['bbox'] for c in result])
    # Empty primitive slots in a merged cell point to their owner, never copied values.
    merged=[{'row':r,'col':c,'owner':owner} for (r,c),owner in slots.items() if owner!=f'R{r}C{c}']
    return {**{k:v for k,v in table.items() if k!='cells'},'cells':result,'body_bbox':core,'inspection_bbox':inspect,
            'context':context,'excluded_hidden_words':excluded_words,'covered_slots':merged,'repairs':repairs,'issues':issues,
            'native_check_status':'PASS' if not issues else 'REVIEW','structure_status':'REQUIRES_GOLD_OR_HUMAN_REVIEW',
            'source_word_coverage':{'assigned_unique':len(used),'inside_table':sum(def_inside(w,core) for w in words)},
            'reconstruction_status':'REVIEW','raw_values_not_forward_filled':True}
