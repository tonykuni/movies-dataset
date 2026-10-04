"""Source-coordinate table repair, context clamping and conservative relationships.
No accounting values are inferred. Originals, spans and repair decisions survive.
"""
from __future__ import annotations
import copy
import re
from collections import defaultdict
from decimal import Decimal
from statistics import median
from . import VIA_ACCEL
from .SUP_MDL743_LayoutCommon_v0100 import PARAMS, RX, def_id, def_box, def_overlap, def_inside, def_number, def_word_rows, def_context

# def 01_PARAMETERS — implementation parameters are in the capability SSOT.
RELATIONS = ("INDEPENDENT", "VERTICAL_UNROLL", "ACCOUNT_SECTIONS", "HORIZONTAL_REJOIN")
EMPTY_MARKERS = ("", "-", "--", "—", "–")
# [VIA:ACCEL-BRIDGE] Inherited from the owning GenericLayoutHub runtime.


def def_cell(words, row, column):
    """No unconditional forward fill: blanks have no invented values."""
    raw = " ".join(w["text"] for w in sorted(words,key=lambda w:w["bbox"][0]))
    value = re.sub(r"\s+", " ", raw).strip()
    numeric = def_number(value)
    return {"raw":raw,"text":value,"number":str(numeric) if numeric is not None else None,
            "row":row,"column":column,"rowspan":1,"colspan":1,
            "bbox":def_box(words) if words else None,"source_ids":[w["id"] for w in words]}


def def_table_rows(words):
    """Align label and numeric baselines without joining vertically stacked cells."""
    rows=[]
    for word in sorted(words,key=lambda w:((w['bbox'][1]+w['bbox'][3])/2,w['bbox'][0])):
        center=(word['bbox'][1]+word['bbox'][3])/2
        height=word['bbox'][3]-word['bbox'][1]
        previous=rows[-1] if rows else None
        match=False
        if previous:
            row_height=median(w['bbox'][3]-w['bbox'][1] for w in previous['words'])
            tolerance=max(PARAMS['row_tolerance'],min(height,row_height)*PARAMS['table_row_center_ratio'])
            conflict=any(def_overlap(word['bbox'],w['bbox'])>=PARAMS['table_row_overlap_guard'] and abs(center-(w['bbox'][1]+w['bbox'][3])/2)>PARAMS['row_tolerance'] for w in previous['words'])
            match=abs(center-previous['cy'])<=tolerance and not conflict
        if match:
            previous['words'].append(word)
            previous['cy']=median((w['bbox'][1]+w['bbox'][3])/2 for w in previous['words'])
        else:rows.append({'cy':center,'words':[word]})
    for row in rows:
        row['words'].sort(key=lambda w:w['bbox'][0]);row['bbox']=def_box(row['words'])
        row['text']=' '.join(w['text'] for w in row['words'])
    return rows


def def_statement_regions(seed, words):
    """Find independent statement lanes, then bound each lane by its own headings."""
    box=seed['bbox'];inside=[w for w in words if def_inside(w['bbox'],box)]
    titles=[]
    for row in def_table_rows(inside):
        groups=[]
        for word in row['words']:
            if not groups or word['bbox'][0]-groups[-1][-1]['bbox'][2]>PARAMS['word_gutter']:groups.append([word])
            else:groups[-1].append(word)
        for group in groups:
            label=' '.join(w['text'] for w in group).strip()
            if re.search(r'[\u4e00-\u9fff]',label):label=re.sub(r'\s+','',label)
            if RX['statement_heading'].fullmatch(label):
                titles.append({'text':label,'bbox':def_box(group),'source_ids':[w['id'] for w in group]})
    if not titles:return []
    columns=[]
    for title in sorted(titles,key=lambda t:t['bbox'][0]):
        if not columns or abs(title['bbox'][0]-columns[-1][0]['bbox'][0])>PARAMS['column_tolerance']:columns.append([title])
        else:columns[-1].append(title)
    cuts=[box[0]]
    for column in columns[1:]:
        anchor=min(t['bbox'][0] for t in column)
        left=[w['bbox'][2] for w in inside if w['bbox'][2]<=anchor and w['bbox'][0]<anchor-PARAMS['epsilon']]
        edge=max(left,default=cuts[-1]);cuts.append((edge+anchor)/2)
    cuts.append(box[2]);regions=[]
    for index,column in enumerate(columns):
        ordered=sorted(column,key=lambda t:t['bbox'][1])
        for offset,title in enumerate(ordered):
            bottom=ordered[offset+1]['bbox'][1]-PARAMS['epsilon'] if offset+1<len(ordered) else box[3]
            bounds=[cuts[index],title['bbox'][1],cuts[index+1],bottom]
            content=[w for w in inside if def_inside(w['bbox'],bounds)]
            rows=[r for r in def_table_rows(content) if r['bbox'][1]>title['bbox'][3] and r['bbox'][1]-title['bbox'][3]<=PARAMS['statement_header_gap']]
            header=next((r for r in rows[:PARAMS['statement_header_scan_rows']] if sum(bool(RX['table_period'].fullmatch(w['text'])) for w in r['words'])>=PARAMS['table_min_numeric']),None)
            if header is None:continue
            part=copy.deepcopy(seed)
            part.update(id=def_id('STATEMENT',seed['id'],title['text'],bounds),bbox=[bounds[0],header['bbox'][1],bounds[2],bounds[3]],clip_bbox=bounds,
                        split_from=seed['id'],split_column=index,split_columns=len(columns),split_reason='independent statement heading and period header',
                        caption=title['text'],statement_identity=title['text'],title_bbox=title['bbox'],title_source_ids=title['source_ids'])
            regions.append(part)
    # Incomplete evidence must not erase an unrecognized part of a compound box.
    return sorted(regions,key=lambda t:(t['bbox'][1],t['bbox'][0])) if len(regions)==len(titles) else []


def def_project_rows(rows, bounds):
    """Infer numeric column right edges; keep label words on their own side."""
    data = [r for r in rows if sum(def_number(w["text"]) is not None for w in r["words"]) >= PARAMS["table_min_numeric"]]
    if not data: return [], []
    template = max(data,key=lambda r:sum(def_number(w["text"]) is not None for w in r["words"]))
    numeric = [w for w in template["words"] if def_number(w["text"]) is not None]
    numeric.sort(key=lambda w:w["bbox"][0])
    groups=[]
    for word in sorted(template["words"],key=lambda w:w["bbox"][0]):
        separate_numeric=groups and def_number(word["text"]) is not None and any(def_number(w["text"]) is not None for w in groups[-1])
        if not groups or separate_numeric or word["bbox"][0]-groups[-1][-1]["bbox"][2]>PARAMS["word_gutter"]:groups.append([word])
        else:groups[-1].append(word)
    anchors=[(def_box(group)[0]+def_box(group)[2])/2 for group in groups]
    cuts = [bounds[0]] + [(a+b)/2 for a,b in zip(anchors,anchors[1:])] + [bounds[2]]
    if len(groups)>1 and not any(def_number(w['text']) is not None for w in groups[0]):
        first_values=[next(w for w in sorted(row['words'],key=lambda w:w['bbox'][0]) if def_number(w['text']) is not None) for row in data]
        boundary=min(w['bbox'][0] for w in first_values)
        if cuts[0]<boundary<cuts[2]:cuts[1]=boundary-PARAMS['epsilon']
    matrix=[]
    for r,row in enumerate(rows):
        groups=[[] for _ in anchors]
        for word in row["words"]:
            center=(word["bbox"][0]+word["bbox"][2])/2
            col=sum(center>=cut for cut in cuts[1:-1])
            groups[col].append(word)
        matrix.append([def_cell(group,r,c) for c,group in enumerate(groups)])
    return matrix, cuts


def def_recover_tables(document, words, lines, seeds):
    """Extend detected header-only tables along aligned rows; retain source matrices."""
    recovered=[]
    for page in document["layout"]["pages"]:
        pn=page["physical_page"]; pw=[w for w in words if w["page"]==pn]
        ps=[copy.deepcopy(a) for a in seeds if a["page"]==pn and a["kind"]=="TABLE"]
        # A row of at least two explicit years is a useful unruled table anchor.
        for row in def_word_rows(pw):
            years=[w for w in row["words"] if RX["year"].fullmatch(w["text"]) and re.match(r'^(?:FY)?20\d{2}',w["text"],re.I)]
            if len(years)>=PARAMS["table_min_numeric"] and not any(def_inside(row["bbox"],a["bbox"]) for a in ps):
                ps.append({"id":def_id("T",document["input_sha256"],pn,row["bbox"]),"kind":"TABLE","page":pn,"bbox":row["bbox"],"width":page["width"],"height":page["height"],"source_ids":[w["id"] for w in row["words"]],"metadata":{"detected_by":"year_row"}})
        # Wide detections own their overlapping fragments, but all seed IDs remain.
        ps.sort(key=lambda a:-(a["bbox"][2]-a["bbox"][0])*(a["bbox"][3]-a["bbox"][1]))
        retained=[]
        for seed in ps:
            parent=next((a for a in retained if def_inside(seed["bbox"],a["bbox"]) and def_overlap(seed["bbox"],a["bbox"])>=PARAMS["column_overlap"]),None)
            if parent: parent["source_ids"]+=seed["source_ids"]
            else: retained.append(seed)
        retained=[part for seed in retained for part in def_split_tables(seed,pw,lines)]
        for seed in sorted(retained,key=lambda a:(a["bbox"][1],a["bbox"][0])):
            box=seed["bbox"]
            if seed.get('statement_identity'):
                region=[w for w in pw if def_inside(w['bbox'],box)]
            else:region=[w for w in pw if box[0]-PARAMS["row_tolerance"] <= (w["bbox"][0]+w["bbox"][2])/2 <= box[2]+PARAMS["row_tolerance"] and w["bbox"][3]>=box[1]-PARAMS["row_tolerance"]]
            rows=def_table_rows(region); selected=[]; seen_data=False
            for row in rows:
                if selected and seen_data and RX["source"].match(row["text"]):break
                if row["bbox"][1] > box[3]:
                    if RX["source"].match(row["text"]) or RX["caption"].match(row["text"]): break
                    if any(a["id"]!=seed["id"] and a["bbox"][1]>=box[3] and def_inside(row["bbox"],a["bbox"]) for a in retained): break
                    if selected and row["bbox"][1]-selected[-1]["bbox"][3] > median(w["size"] for w in row["words"])*PARAMS["table_row_gap"]: break
                    numeric=sum(def_number(w["text"]) is not None or w["text"] in EMPTY_MARKERS[1:] for w in row["words"])
                    if numeric<PARAMS["table_min_numeric"]: break
                selected.append(row)
                seen_data=seen_data or sum(def_number(w["text"]) is not None for w in row["words"])>=PARAMS["table_min_numeric"]
            if not selected: continue
            seed["bbox"]=def_box([w for row in selected for w in row["words"]])
            matrix,cuts=def_project_rows(selected,seed["bbox"])
            if not matrix:
                matrix=[[def_cell(row["words"],r,0)] for r,row in enumerate(selected)]
                cuts=[seed["bbox"][0],seed["bbox"][2]]
            # Header rows have no numeric body. Year-only rows are headers only when
            # the first cell is not itself a year (vertical-year tables are data).
            header_count=0
            for row in matrix:
                nums=sum(c["number"] is not None for c in row)
                first_year=bool(RX["year"].fullmatch(row[0]["text"]))
                if nums>=PARAMS["table_min_numeric"] and (first_year or not any(RX["year"].fullmatch(c["text"]) for c in row)):
                    break
                header_count+=1
            if header_count==len(matrix): header_count=min(1,len(matrix))
            if seed.get('statement_identity'):header_count=1
            seed.update(rows=matrix,header_count=header_count,column_edges=cuts,pages=[pn],
                        original_seed_bbox=box,repairs=["source_coordinate_projection"],state="REVIEW")
            if len(cuts)==2 and len(matrix)>1 and not any(c['number'] is not None for row in matrix for c in row):
                seed.update(state="UNCONFIRMED_TEXT_GRID",issue="single text column without numeric cells; preserve prose reading order")
            seed["source_ids"]=list(dict.fromkeys(seed["source_ids"]+[w["id"] for row in selected for w in row["words"]]))
            seed["context"]=def_context(seed,lines,[*retained,*[a for a in seeds if a["kind"]=="FIGURE"]])
            seed["caption"]=seed.get('caption') or " ".join(x["text"] for x in seed["context"]["above"] if RX["caption"].match(x["text"]))
            seed["sources"]=[x["text"] for x in seed["context"]["below"] if RX["source"].match(x["text"])]
            if seed.get('statement_identity'):
                selected_ids={w['id'] for row in selected for w in row['words']}
                seed['retained_non_cell_words']=[copy.deepcopy(w) for w in pw if def_inside(w['bbox'],seed['clip_bbox']) and w['id'] not in selected_ids]
            recovered.append(seed)
    return def_deduplicate(recovered)


def def_split_tables(seed, words, lines):
    """Split compound boxes only with caption boundaries or repeated-key headers."""
    statements=def_statement_regions(seed,words)
    if statements:return statements
    captions=[l for l in lines if l["page"]==seed["page"] and RX["caption"].match(l["text"]) and def_inside(l["bbox"],seed["bbox"])]
    box=seed["bbox"]; ycuts={l["bbox"][1] for l in captions if l["bbox"][1]>box[1]+PARAMS["row_tolerance"]}
    inside=def_word_rows([w for w in words if def_inside(w["bbox"],box)])
    for source in (l for l in lines if l["page"]==seed["page"] and RX["source"].match(l["text"]) and def_inside(l["bbox"],box)):
        before=[r for r in inside if r["bbox"][3]<source["bbox"][1]]
        after=[r for r in inside if r["bbox"][1]>source["bbox"][3]]
        if not before or not after:continue
        following=after[0];tokens=following["words"]
        header=sum(def_number(w["text"]) is None for w in tokens)>=PARAMS["table_min_numeric"] or sum(bool(RX["year"].fullmatch(w["text"])) for w in tokens)>=PARAMS["table_min_numeric"]
        body=any(sum(def_number(w["text"]) is not None for w in r["words"])>=PARAMS["table_min_numeric"] for r in before)
        if header and body and following["bbox"][1]-source["bbox"][3]<=median(w["size"] for w in tokens)*PARAMS["table_row_gap"]:ycuts.add(following["bbox"][1])
    ycuts=sorted(ycuts)
    boxes=[];top=box[1]
    for y in ycuts:
        if any(top<=w["bbox"][1]<y for w in words): boxes.append([box[0],top,box[2],y-PARAMS["epsilon"]])
        top=y
    boxes.append([box[0],top,box[2],box[3]])
    parts=[]
    for bbox in boxes:
        content=[w for w in words if def_inside(w["bbox"],bbox)]
        rows=def_word_rows(content);gaps=[]
        for row in rows:
            for a,b in zip(row["words"],row["words"][1:]):
                if b["bbox"][0]-a["bbox"][2]>=PARAMS["column_gutter"]:
                    midpoint=(a["bbox"][2]+b["bbox"][0])/2
                    if bbox[0]+(bbox[2]-bbox[0])*.25<midpoint<bbox[0]+(bbox[2]-bbox[0])*.75:gaps.append(midpoint)
        split=None
        for gap in gaps:
            if any(w["bbox"][0]<gap<w["bbox"][2] for w in content):continue
            cap_left=[l for l in captions if l["bbox"][2]<gap];cap_right=[l for l in captions if l["bbox"][0]>gap]
            independent=bool(cap_left and cap_right and RX["caption"].match(cap_left[0]["text"]).group()!=RX["caption"].match(cap_right[0]["text"]).group())
            repeated=any([w["text"] for w in r["words"] if w["bbox"][2]<gap]==[w["text"] for w in r["words"] if w["bbox"][0]>gap] and len([w for w in r["words"] if w["bbox"][2]<gap])>=PARAMS["table_min_numeric"] for r in rows)
            if independent or repeated:split=gap;break
        targets=[[bbox[0],bbox[1],split,bbox[3]],[split,bbox[1],bbox[2],bbox[3]]] if split else [bbox]
        for b in targets:
            part=copy.deepcopy(seed);part["bbox"]=b
            if b!=box:part["id"]=def_id("TSPLIT",seed["id"],b);part["split_from"]=seed["id"]
            parts.append(part)
    return parts


def def_deduplicate(tables):
    """Collapse contained duplicate proposals, not repeated equal values elsewhere."""
    kept=[]
    for table in sorted(tables,key=lambda t:-sum(len(c["source_ids"]) for r in t["rows"] for c in r)):
        refs={s for row in table["rows"] for c in row for s in c["source_ids"]}
        parent=next((t for t in kept if t["page"]==table["page"] and refs and refs<={s for r in t["rows"] for c in r for s in c["source_ids"]}),None)
        if parent: parent.setdefault("duplicate_candidates",[]).append(table["id"])
        else: kept.append(table)
    return sorted(kept,key=lambda t:(t["page"],t["bbox"][1],t["bbox"][0]))


def def_spans_and_fragments(table, source_cells=()):
    """Promote spans only when an original cell geometrically proves the span."""
    table=copy.deepcopy(table); edges=table["column_edges"]
    # Remove only synthetic axes that have no text, source, geometry or span.
    # An empty fiscal column with a header or an explicit blank cell is retained.
    ghost={(r,c) for r,row in enumerate(table["rows"]) for c,cell in enumerate(row) if not cell["text"] and not cell["raw"] and cell["number"] is None and not cell["bbox"] and not cell["source_ids"] and not cell.get("covered_by") and not cell.get("span_source")}
    drop_rows=[r for r,row in enumerate(table["rows"]) if all((r,c) in ghost for c in range(len(row)))]
    drop_cols=[c for c in range(len(edges)-1) if all((r,c) in ghost for r in range(len(table["rows"])))]
    if len(drop_rows)<len(table["rows"]) and len(drop_cols)<len(edges)-1 and (drop_rows or drop_cols):
        table["empty_axis_evidence"]={"rows":drop_rows,"columns":drop_cols,"rule":"no text, value, geometry, source or span"}
        table["header_count"]-=sum(r<table["header_count"] for r in drop_rows)
        table["rows"]=[[cell for c,cell in enumerate(row) if c not in drop_cols] for r,row in enumerate(table["rows"]) if r not in drop_rows]
        edges=[x for c,x in enumerate(edges[:-1]) if c not in drop_cols]+[edges[-1]];table["column_edges"]=edges
        for r,row in enumerate(table["rows"]):
            for c,cell in enumerate(row):cell.update(row=r,column=c)
        table["repairs"].append("remove_unreferenced_empty_axes")
    for source in source_cells:
        if source.get("page")!=table["page"] or not def_inside(source["bbox_pt"],table["bbox"]): continue
        box=source["bbox_pt"]
        covered=[i for i in range(len(edges)-1) if box[0]<= (edges[i]+edges[i+1])/2 <=box[2]]
        covered_rows=[r for r,row in enumerate(table["rows"][:table["header_count"]]) if any(c["bbox"] and def_inside(c["bbox"],box) for c in row)]
        if not covered or not covered_rows or len(covered)*len(covered_rows)<2:continue
        cells=[table["rows"][r][c] for r in covered_rows for c in covered if table["rows"][r][c]["bbox"] and def_inside(table["rows"][r][c]["bbox"],box)]
        anchor=table["rows"][min(covered_rows)][min(covered)]
        anchor.update(colspan=len(covered),rowspan=len(covered_rows),text=source.get("raw_text") or " ".join(c["text"] for c in cells),span_source=source["element_id"])
        for r in covered_rows:
            for c in covered:
                if r!=min(covered_rows) or c!=min(covered):table["rows"][r][c]["covered_by"]=[min(covered_rows),min(covered)]
    # A wrapped cell can be joined only with the same physical source cell.
    merged=[]
    for row in table["rows"]:
        if merged and all(c["number"] is None for c in row) and any(c["text"] for c in row):
            shared=[s for s in source_cells if s.get("page")==table["page"] and all(not c["bbox"] or def_inside(c["bbox"],s["bbox_pt"]) for c in [*merged[-1],*row])]
            if shared:
                for a,b in zip(merged[-1],row):
                    a["text"]=" ".join(x for x in (a["text"],b["text"]) if x);a["source_ids"]+=b["source_ids"]
                table["repairs"].append("same_source_cell_wrap");continue
        merged.append(row)
    table["rows"]=merged
    table["header_paths"]=[" / ".join(dict.fromkeys(r[c]["text"] for r in merged[:table["header_count"]] if r[c]["text"])) for c in range(len(edges)-1)]
    return table


def def_checksum(table):
    """Arithmetic is supporting evidence, never proof of perfect reconstruction."""
    checks=[]; segment=[]
    for row in table["rows"][table["header_count"]:]:
        if RX["total"].search(row[0]["text"]):
            for col,cell in enumerate(row[1:],1):
                values=[r[col]["number"] for r in segment if len(r)>col]
                if cell["number"] is None or not values or any(v is None for v in values): continue
                observed=Decimal(cell["number"]);computed=sum(Decimal(v) for v in values)
                checks.append({"column":col,"observed":str(observed),"sum":str(computed),"state":"MATCH" if abs(computed-observed)<=Decimal(PARAMS["checksum_tolerance"]) else "MISMATCH","source_ids":cell["source_ids"]})
            segment=[]
        else: segment.append(row)
    return {"checks":checks,"state":"CHECKED" if checks else "NOT_APPLICABLE","proves_complete":False}


def def_table_relation(left, right):
    """Independent IDs veto merging. Numeric right blocks also need row alignment."""
    lc=left.get("caption","");rc=right.get("caption","")
    lid=RX["caption"].match(lc);rid=RX["caption"].match(rc)
    if lid and rid and lid.group().casefold()!=rid.group().casefold():return "INDEPENDENT"
    shared=bool(lc and lc==rc) or left.get("shared_caption_id") and left.get("shared_caption_id")==right.get("shared_caption_id")
    if not shared:return "INDEPENDENT"
    a=left["rows"][left["header_count"]:];b=right["rows"][right["header_count"]:]
    if not a or not b:return "INDEPENDENT"
    same_header=left.get("header_paths")==right.get("header_paths") and bool(left.get("header_paths"))
    la=def_number(a[-1][0]["text"]);rb=def_number(b[0][0]["text"])
    if same_header and la is not None and rb==la+1:return "VERTICAL_UNROLL"
    combined=" ".join(left.get("header_paths",[])+right.get("header_paths",[]))
    if re.search(r'資產|assets',combined,re.I) and re.search(r'負債|權益|liabilit|equity',combined,re.I):return "ACCOUNT_SECTIONS"
    if left["header_count"]==right["header_count"] and all(r[0]["number"] is not None for r in b) and len(a)==len(b) and all(x[0].get("bbox") and y[0].get("bbox") and abs(x[0]["bbox"][1]-y[0]["bbox"][1])<=PARAMS["row_tolerance"] for x,y in zip(a,b)):
        return "HORIZONTAL_REJOIN"
    return "INDEPENDENT"


def def_adjacent(tables):
    """Bind related panels; independent and ambiguous tables stay separate."""
    tables=copy.deepcopy(tables); groups=[]
    for i,left in enumerate(tables):
        for right in tables[i+1:]:
            if left["page"]!=right["page"] or left["bbox"][2]>right["bbox"][0] or def_overlap(left["bbox"],right["bbox"],1)<PARAMS["column_overlap"]:continue
            relation=def_table_relation(left,right)
            group={"type":relation,"tables":[left["id"],right["id"]]}
            if relation=="VERTICAL_UNROLL":group["rows"]=left["rows"]+right["rows"][right["header_count"]:]
            elif relation=="HORIZONTAL_REJOIN":group["rows"]=[a+b for a,b in zip(left["rows"],right["rows"])]
            elif relation=="ACCOUNT_SECTIONS":group["sections"]={"left":left["id"],"right":right["id"]}
            groups.append(group)
    return tables,groups


def def_continue_tables(tables, lines):
    """Consecutive pages, matching geometry/schema, and no intervening prose."""
    merged=[]
    for current in copy.deepcopy(tables):
        previous=merged[-1] if merged else None
        match=False
        if previous and current["page"]==previous["pages"][-1]+1:
            a=previous; b=current;ac=a.get("caption","");bc=b.get("caption","")
            different=(a.get('statement_identity') and b.get('statement_identity') and a['statement_identity']!=b['statement_identity']) or (RX["caption"].match(ac) and RX["caption"].match(bc) and RX["caption"].match(ac).group()!=RX["caption"].match(bc).group())
            between=[l for l in lines if l.get("role") in {"BODY","H1","H2","H3","REPORT_TITLE"} and not l.get("asset_id") and ((l["page"]==a["pages"][-1] and l["bbox"][1]>a["bbox"][3]) or (l["page"]==b["page"] and l["bbox"][3]<b["bbox"][1]))]
            same=len(a["column_edges"])==len(b["column_edges"]) and all(abs(x/a["width"]-y/b["width"])<=PARAMS["column_tolerance"]/a["width"] for x,y in zip(a["column_edges"],b["column_edges"]))
            evidence=bool(RX["continued"].search(bc)) or (bool(a.get("header_paths")) and a.get("header_paths")==b.get("header_paths"))
            match=not different and not between and same and evidence and not a.get("sources") and a["bbox"][3]>=a["height"]*PARAMS["table_bottom_ratio"] and b["bbox"][1]<=b["height"]*PARAMS["table_top_ratio"]
        if match:
            rows=current["rows"][current["header_count"]:] if previous.get("header_paths")==current.get("header_paths") else current["rows"]
            if previous['rows'] and rows:
                last=previous['rows'][-1];first=rows[0]
                fragment=bool(last[0]['text']) and all(not c['text'] for c in last[1:]) and not first[0]['text'] and any(c['number'] is not None for c in first[1:])
                edge=last[0].get('bbox') and last[0]['bbox'][3]>=previous['height']*PARAMS['split_row_bottom'] and all(not c.get('bbox') or c['bbox'][1]<=current['height']*PARAMS['split_row_top'] for c in first)
                if fragment and edge:
                    previous.setdefault('boundary_row_evidence',[]).append(copy.deepcopy([last,first]))
                    first[0]=copy.deepcopy(last[0]);previous['rows'].pop()
                    previous['repairs'].append('cross_page_split_row_candidate')
            previous["rows"]+=rows;previous["pages"]+=current["pages"];previous["source_ids"]+=current["source_ids"]
            previous["sources"]=list(dict.fromkeys(previous.get("sources",[])+current.get("sources",[])))
            previous.setdefault("continuations",[]).append(current["id"]);previous["repairs"].append("cross_page_table")
            previous["bbox"]=current["bbox"]
        else:merged.append(current)
    return merged
