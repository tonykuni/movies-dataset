"""Font hierarchy, safe paragraph repair and reading order for the one Layout hub.
Raw elements remain in the locked extraction. Every repair carries source IDs.
"""
from __future__ import annotations
import copy
import re
from collections import Counter, defaultdict
from statistics import median
from . import VIA_ACCEL
from .SUP_MDL743_LayoutCommon_v0100 import PARAMS, RX, def_id, def_box, def_overlap, def_inside, def_join

# def 01_PARAMETERS — all thresholds come from the central capability SSOT.
HEADING_ROLES = ("REPORT_TITLE", "H1", "H2", "H3")
NOISE_ROLES = ("RUNNING_HEADER", "PAGE_FOOTER", "END_MATTER")
BRACKETS = {"(": ")", "（": "）", "「": "」", "『": "』", "[": "]", "【": "】"}
# [VIA:ACCEL-BRIDGE] Inherited from the owning GenericLayoutHub runtime.


def def_font_evidence(lines, traces=()):
    """A color match alone is never bold. Require a font, rendering mode or overlay."""
    result = copy.deepcopy(lines)
    for i, line in enumerate(result):
        reasons = ["font"] if line["bold"] else []
        for trace in traces:
            if trace["page"] == line["page"] and trace.get("render_mode") in {1, 2} and def_overlap(trace["bbox"], line["bbox"]) >= PARAMS["column_overlap"] and def_overlap(trace["bbox"], line["bbox"], 1) >= PARAMS["column_overlap"]:
                reasons.append("stroke")
        for other in result[:i]:
            if other["page"] == line["page"] and other["text"] == line["text"] and max(abs(a-b) for a,b in zip(other["bbox"],line["bbox"])) <= PARAMS["bold_duplicate_tolerance"]:
                reasons.append("overprint"); other["bold"] = True
                line["duplicate_of"] = other["id"]
                other["source_ids"] = list(dict.fromkeys(other["source_ids"] + line["source_ids"]))
                break
        line["bold"] = bool(reasons); line["bold_evidence"] = reasons
    return result


def def_classify(lines, body_size, total_pages):
    """Seven text levels plus retained running margins; keyword-backed end matter."""
    lines = copy.deepcopy(lines)
    fingerprints = defaultdict(set)
    for line in lines:
        if line["bbox"][1] < line["height"]*PARAMS["header_zone"] or line["bbox"][1] > line["height"]*PARAMS["footer_zone"]:
            fingerprints[re.sub(r"\d+", "#", line["text"].strip())].add(line["page"])
    per_page = defaultdict(list)
    for line in lines:
        per_page[line["page"]].append(line)
    end_regions = {}
    for page, group in per_page.items():
        if page >= max(2, total_pages*PARAMS["end_zone"]):
            marked = [l for l in group if RX["disclaimer"].search(l["text"])]
            if marked:
                start = min(l["bbox"][1] for l in marked)
                tail = [l for l in group if l["bbox"][1] >= start]
                small = sum(l["size"] < body_size*PARAMS["small_font"] for l in tail)/max(len(tail),1)
                if small >= PARAMS["end_small_ratio"] or any(l["bold"] for l in marked):
                    end_regions[page] = start
    for line in lines:
        text = line["text"].strip(); ratio = line["size"]/max(body_size, PARAMS["epsilon"])
        y = line["bbox"][1]/line["height"]
        signature = re.sub(r"\d+", "#", text)
        repeated = total_pages > 1 and len(fingerprints[signature]) >= max(2, total_pages*PARAMS["repeat_ratio"])
        short = len(text) <= PARAMS["heading_max_chars"] and not RX["sentence_end"].search(text)
        line["ratio"] = ratio; line["role"] = "BODY"
        page_start = end_regions.get(line["page"])
        if page_start is not None:
            if line["bbox"][1] >= page_start:
                line["role"] = "END_MATTER"; continue
        if (y > PARAMS["footer_zone"] and (ratio < PARAMS["small_font"] or repeated or RX["page_number"].fullmatch(text))):
            line["role"] = "PAGE_FOOTER"
        elif y < PARAMS["header_zone"] and (repeated or RX["page_number"].fullmatch(text)):
            line["role"] = "RUNNING_HEADER"
        elif short:
            ratios = PARAMS["title_ratios"]
            if line["page"] == 1 and y < .5 and ratio >= ratios[0]:
                line["role"] = "REPORT_TITLE"
            elif ratio >= ratios[1]: line["role"] = "H1"
            elif ratio >= ratios[2]: line["role"] = "H2"
            elif ratio >= ratios[3] and (line["bold"] or RX["heading"].match(text)): line["role"] = "H3"
            elif line["bold"] or RX["heading"].match(text): line["role"] = "H3"
        if RX["caption"].match(text): line["role"] = "CAPTION"
        elif RX["source"].match(text): line["role"] = "SOURCE"
    return lines


def def_reading_order(lines, assets):
    """Column-first between full-width text barriers; floating assets stay separate."""
    ordered = []; floating = []
    for page in sorted({l["page"] for l in lines}):
        group = [l for l in lines if l["page"] == page and not l.get("duplicate_of")]
        pa = [a for a in assets if a["page"] == page]
        for line in group:
            owners = [a for a in pa if def_inside(line["bbox"], a["bbox"])]
            if owners:
                line["asset_id"] = min(owners, key=lambda a:(a["bbox"][2]-a["bbox"][0])*(a["bbox"][3]-a["bbox"][1]))["id"]
        body = [l for l in group if not l.get("asset_id") and l["role"] not in NOISE_ROLES]
        if not body:
            continue
        x0 = min(l["bbox"][0] for l in body); x1 = max(l["bbox"][2] for l in body)
        width = max(x1-x0, 1); mid = (x0+x1)/2
        left = [l for l in body if l["bbox"][2] <= mid+PARAMS["word_gutter"]]
        right = [l for l in body if l["bbox"][0] >= mid-PARAMS["word_gutter"]]
        two = bool(left and right) and min(l["bbox"][0] for l in right)-max(l["bbox"][2] for l in left) >= PARAMS["word_gutter"]
        for line in body:
            full = two and line["bbox"][2]-line["bbox"][0] >= width*PARAMS["span_width_ratio"]
            line["column"] = -1 if full else (1 if two and line["bbox"][0] >= mid else 0)
            peers = right if line["column"] == 1 else left if two and line["column"] == 0 else body
            line["column_box"] = [min(l["bbox"][0] for l in peers), max(l["bbox"][2] for l in peers)]
            line["fill"] = (line["bbox"][2]-line["column_box"][0])/max(line["column_box"][1]-line["column_box"][0],1)
        for column in sorted({l['column'] for l in body}):
            run=sorted([l for l in body if l['column']==column],key=lambda l:l['bbox'][1])
            for previous,line in zip(run,run[1:]):
                short=len(line['text'])<=PARAMS['plain_heading_chars'] and not re.search(r'[，、,。！？.!?]',line['text'])
                gap=line['bbox'][1]-previous['bbox'][3]
                if line['role']=='BODY' and short and line['fill']<=PARAMS['plain_heading_fill'] and gap>=line['size']*PARAMS['gap_ratio']:
                    line['role']='H3';line['role_evidence']='short standalone line with paragraph gap'
        barriers = sorted([l for l in body if l["column"] == -1],key=lambda l:l["bbox"][1])
        used = set(); lower = -1
        for barrier in barriers + [None]:
            upper = barrier["bbox"][1] if barrier else float("inf")
            band = [l for l in body if l["id"] not in used and l["column"] != -1 and lower <= l["bbox"][1] < upper]
            band.sort(key=lambda l:(l["column"],l["bbox"][1],l["bbox"][0]))
            ordered.extend(band); used.update(l["id"] for l in band)
            if barrier:
                ordered.append(barrier); used.add(barrier["id"]); lower=barrier["bbox"][1]
        ordered.extend(sorted((l for l in body if l["id"] not in used), key=lambda l:(l["bbox"][1],l["bbox"][0])))
        floating.extend({"id":a["id"],"page":page,"kind":a["kind"],"bbox":a["bbox"],"mode":"FLOATING_ASSET"} for a in pa)
    for i,line in enumerate(ordered,1): line["reading_order"] = i
    return ordered, floating


def def_can_join(previous, current, assets=()):
    """Veto headings, indentation, columns and incompatible page geometry first."""
    if previous["role"] != "BODY" or current["role"] != "BODY": return False
    if RX["sentence_end"].search(previous["text"].strip()) or RX["heading"].match(current["text"].strip()): return False
    if previous.get("column",0) != current.get("column",0): return False
    if abs(previous["size"]-current["size"]) > previous["size"]*(1-PARAMS["small_font"]): return False
    if abs(previous["bbox"][0]/previous["width"]-current["bbox"][0]/current["width"]) > PARAMS["word_gutter"]/previous["width"]: return False
    unfinished = bool(RX["continuation"].search(previous["text"].strip())) or previous.get("fill",0) >= PARAMS["line_full"]
    stack=[]
    for char in previous["text"]:
        if char in BRACKETS: stack.append(BRACKETS[char])
        elif stack and char==stack[-1]: stack.pop()
    unfinished = unfinished or bool(stack)
    if not unfinished: return False
    if current["page"] == previous["page"]+1:
        return previous["bbox"][3] >= previous["height"]*PARAMS["table_bottom_ratio"] and current["bbox"][1] <= current["height"]*PARAMS["table_top_ratio"] and abs(previous["width"]-current["width"]) < PARAMS["word_gutter"]
    if current["page"] != previous["page"]: return False
    gap=current["bbox"][1]-previous["bbox"][3]
    islands=[a for a in assets if a["page"]==current["page"] and previous["bbox"][3] <= a["bbox"][1] and a["bbox"][3] <= current["bbox"][1]]
    return gap <= previous["size"]*PARAMS["gap_ratio"] or bool(islands)


def def_stitch(lines, assets=()):
    paragraphs=[]; previous=None
    for line in lines:
        if line["role"] in NOISE_ROLES or line.get("asset_id"): continue
        join = previous and def_can_join(previous,line,assets)
        wrapped = previous and previous["role"]==line["role"] and line["role"] in HEADING_ROLES and previous.get("fill",0) >= PARAMS["line_full"] and not RX["heading"].match(line["text"]) and line["page"]==previous["page"] and abs(line["bbox"][0]-previous["bbox"][0])<=PARAMS["word_gutter"] and 0<=line["bbox"][1]-previous["bbox"][3]<=line["size"] and abs(line["size"]-previous["size"])<=PARAMS["epsilon"]
        if paragraphs and (join or wrapped):
            item=paragraphs[-1]; item["text"]=def_join(item["text"],line["text"])
            item["source_ids"]+=line["source_ids"]; item["pages"]=sorted(set(item["pages"]+[line["page"]]))
            item["repairs"].append("cross_page" if previous["page"]!=line["page"] else "wrapped_heading" if wrapped else "line_join")
        else:
            paragraphs.append({"id":def_id("P",line["id"]),"role":line["role"],"text":line["text"],"pages":[line["page"]],"source_ids":list(line["source_ids"]),"repairs":[]})
        previous=line
    stack=[]
    for paragraph in paragraphs:
        if paragraph["role"] in HEADING_ROLES:
            level=HEADING_ROLES.index(paragraph["role"])
            while stack and stack[-1][0]>=level: stack.pop()
            paragraph["parent_id"]=stack[-1][1] if stack else None
            stack.append((level,paragraph["id"]))
        else: paragraph["parent_id"]=stack[-1][1] if stack else None
        paragraph["heading_path"]=[item[1] for item in stack]
    return paragraphs
