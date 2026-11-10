#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
"""
VIA NON-STOCK SUMMARIZER ENGINE v0300
=====================================
Single-entry integration engine.

Reuses, rather than rewrites:
- VRN_M03_PDF_Layout_JSON v3       -> PDF layout / roles / blocks
- VRN_MDL003_TableRestorer         -> TextRepairEngine / axis-noise / dedup
- VRN_M07_Summarizer               -> local extractive NLP helper
- NON_STOCK_CORE v0200             -> Story/claim/evidence/guards/events

Output philosophy:
    ONE REPORT = ONE MAIN ROW
    Details live in TOPIC / COMPANY / EVIDENCE child tables.

Main summary contract:
    TITLE
    POINT_1 = core thesis / what happened
    POINT_2 = driver / why
    POINT_3 = impact / who benefits or is affected
    POINT_4 = outlook / risk / what next

Local-only. No model download. No source mutation.
"""

# =============================================================================
# def 00 PARAMETERS — all editable parameters are kept at the top
# =============================================================================
from dataclasses import asdict
from pathlib import Path
from collections import Counter, defaultdict
from typing import Any, Optional
import argparse, csv, hashlib, html, importlib.util, json, os, re, sys

ENGINE_ID = "VIA-NON-STOCK-SUMMARIZER-INTEGRATED-001"
ENGINE_VERSION = "v0300"
ENGINE_NAME = "VIA NON-STOCK SUMMARIZER ENGINE"
NETWORK_ALLOWED = False

MAX_REPORT_POINT_CHARS = 220
MAX_TOPIC_POINT_CHARS = 220
MAX_TOPICS_PER_REPORT_HTML = 40
MAX_COMPANIES_PER_REPORT_HTML = 40
TOPIC_MIN_CHARS = 30
MIN_REPORT_EVIDENCE = 1

BROKER_PATTERNS = {
    "UBS": ("UBS",), "MS": ("MS-", "Morgan Stanley"), "GS": ("GS-", "Goldman"),
    "CITI": ("Citi-",), "DAIWA": ("Daiwa-",), "JPM": ("JP-", "JPM"),
    "MEGA": ("兆豐",), "TAISHIN": ("台新",), "CTBC": ("中信", "CTBC"),
    "CATHAY": ("國泰",), "YUANTA": ("元大",), "CLSA": ("CLST-", "CLSA"),
}

INDUSTRY_MAP = {
    "AI_INFRASTRUCTURE":"AI Infrastructure",
    "ASIC_CUSTOM_SILICON":"Semiconductor / ASIC",
    "AI_THERMAL":"Thermal / Cooling",
    "MEMORY":"Memory",
    "PCB_MATERIALS":"PCB / Materials",
    "CPO_OPTICAL":"Optical / CPO",
    "FOUNDRY_ADVANCED":"Foundry",
    "ADVANCED_PACKAGING":"Advanced Packaging",
    "SEMICONDUCTOR_MATERIALS":"Semiconductor Materials",
    "SEMICONDUCTOR_EQUIPMENT":"Semiconductor Equipment",
    "AEROSPACE":"Aerospace",
    "DEFENSE_DRONE":"Defense / Drone",
    "ROBOTICS_PHYSICAL_AI":"Robotics / Physical AI",
    "EV_AUTOMOTIVE":"Automotive / EV",
    "SHIPPING":"Shipping",
    "RATES_BONDS":"Macro / Rates / Bonds",
    "ENERGY_GEOPOLITICS":"Energy / Geopolitics",
    "DISPLAY_ESL":"Display / E-paper / ESL",
    "CDMO_PHARMA":"Pharma / CDMO",
    "POWER_GRID":"Power Grid",
}

REPORT_COLUMNS = [
    "REPORT_ID","REPORT_DATE","FILE_NAME","REPORT_TYPE","SOURCE","ANALYST_AUTHOR",
    "MAIN_STORY","MAIN_INDUSTRY","TITLE",
    "POINT_1","POINT_2","POINT_3","POINT_4",
    "DIRECTION","HORIZON","COMPANY_COUNT","TOPIC_COUNT","EVIDENCE_COUNT",
    "LAYOUT_ENGINE","TEXT_REPAIR_ENGINE","NLP_ENGINE","STATUS","DETAIL_REF"
]
TOPIC_COLUMNS = [
    "REPORT_ID","TOPIC_ID","SOURCE_UNIT","TOPIC_TITLE","STORY_L1","INDUSTRY",
    "TITLE","POINT_1","POINT_2","POINT_3","POINT_4","DIRECTION","HORIZON",
    "TICKERS","GLOBAL_ANCHORS","EVIDENCE_SIDS","NLP_HINT","STATUS"
]
COMPANY_COLUMNS = [
    "REPORT_ID","TICKER","COMPANY_NAME","STORIES","INDUSTRY","RATING","TARGET_PRICE",
    "TITLE","POINT_1","POINT_2","POINT_3","POINT_4","EVIDENCE_SIDS","STATUS"
]
EVIDENCE_COLUMNS = [
    "REPORT_ID","CLAIM_ID","EVIDENCE_SID","PAGE","ATTRIBUTION","IMPORTANCE","DIRECTION",
    "STORIES","TICKERS","DRIVERS","RELATIONS","PERIODS","TEXT"
]

# =============================================================================
# def 01 MODULE LOADER
# =============================================================================
def def_load_module(name: str, path: Path):
    spec=importlib.util.spec_from_file_location(name,path)
    if not spec or not spec.loader: raise ImportError(f"Cannot load {name}: {path}")
    mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod

ROOT=Path(__file__).resolve().parents[1]
CORE=def_load_module("nonstock_core_v0200", ROOT/"internal"/"NON_STOCK_CORE_v0200.py")
VRN_LAYOUT=def_load_module("vrn2_layout", ROOT/"reuse"/"vrn2"/"VRN_M03_PDF_Layout_JSON_v3.py")
VRN_REPAIR=def_load_module("vrn2_repair", ROOT/"reuse"/"vrn2"/"VRN_MDL003_TableRestorer.py")
VRN_NLP=def_load_module("vrn2_nlp", ROOT/"reuse"/"vrn2"/"VRN_M07_Summarizer.py")
REPAIR=VRN_REPAIR.TextRepairEngine()
NLP_LIBS=VRN_NLP.load_libraries()

# =============================================================================
# def 02 GENERIC HELPERS
# =============================================================================
def def_hash8(text:str)->str: return hashlib.sha256(text.encode("utf-8",errors="ignore")).hexdigest()[:8].upper()
def def_clean(text:str)->str: return CORE.def_normalize_text(text or "")
def def_clip(text:str,n:int=MAX_REPORT_POINT_CHARS)->str:
    t=def_clean(text); return t if len(t)<=n else t[:n-1].rstrip()+"…"
def def_join_unique(items:list[str],sep:str=";")->str:
    out=[]
    for x in items:
        if x and x not in out: out.append(x)
    return sep.join(out)
def def_file_sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def def_source_name(path:Path, blocks:list[Any])->str:
    hay=path.name+"\n"+"\n".join(b.text for b in blocks[:20])
    for source,pats in BROKER_PATTERNS.items():
        if any(p.lower() in hay.lower() for p in pats): return source
    return "UNKNOWN"

def def_report_date(path:Path, blocks:list[Any])->str:
    hay=path.name+"\n"+"\n".join(b.text for b in blocks[:25])
    pats=[
      r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)",
      r"(?<!\d)(20\d{2})[年/\-.](\d{1,2})[月/\-.](\d{1,2})日?",
    ]
    for p in pats:
        m=re.search(p,hay)
        if m:
            y,mo,d=m.groups(); return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    return ""

def def_author(blocks:list[Any])->str:
    hay="\n".join(b.text for b in blocks[:25])
    for p in [r"(?:研究員|分析師|報告人)[：:]?\s*([\u4e00-\u9fff]{2,4})",r"([\u4e00-\u9fff]{2,4})\s*(?:證券研究員|合格證券投資分析人員)"]:
        m=re.search(p,hay)
        if m:return m.group(1)
    return ""

# =============================================================================
# def 03 VRN-2 PDF LAYOUT + TEXT REPAIR ADAPTER
# =============================================================================
def def_page_title_from_layout(layout_page:dict[str,Any])->str:
    spans=layout_page.get("spans",[])
    cand=[s for s in spans if s.get("role") in {"TITLE","SUBTITLE","SECTION_HEADING"} and len(def_clean(s.get("text","")))>1]
    if not cand:return ""
    # Preserve reading order; prefer larger font / upper page. Merge nearby title fragments.
    cand=sorted(cand,key=lambda s:(round(s.get("bbox",(0,0,0,0))[1],1),s.get("bbox",(0,0,0,0))[0]))
    top_y=min(s.get("bbox",(0,0,0,0))[1] for s in cand)
    near=[s for s in cand if s.get("bbox",(0,0,0,0))[1] <= top_y+65]
    text=" ".join(def_clean(s.get("text","")) for s in near[:4])
    return re.sub(r"\s+"," ",text).strip()

def def_extract_pdf_vrn2(path:Path)->tuple[list[Any],dict[str,Any],dict[int,str]]:
    layout=VRN_LAYOUT.analyze_pdf_layout(str(path),use_ocr_for_image_only=False)
    title_map={int(p["page"])+1:def_page_title_from_layout(p) for p in layout}
    raw_blocks=[]
    pages=len(layout)
    for pi in range(pages):
        try: items=VRN_LAYOUT.extract_blocks_pymupdf(str(path),pi)
        except Exception: items=[]
        for j,it in enumerate(items):
            text=def_clean(getattr(it,"text","") if not isinstance(it,dict) else it.get("text",""))
            # PyMuPDF blocks often preserve visual line wraps; prose should be semantic sentences, not layout fragments.
            if len(CORE.NUMBER_RE.findall(text)) < 5:
                text=re.sub(r"\s*\n\s*"," ",text).strip()
            if not text or (text.isdigit() and len(text)<=3): continue
            if re.search(r"本刊所刊載之內容僅做為參考|僅供內部參考|請勿外傳",text):
                btype="DISCLAIMER"
            elif text.startswith("資料來源") or text.startswith("Source"):
                btype="SOURCE"
            elif CORE.URL_RE.fullmatch(text): btype="URL"
            else: btype=CORE.def_guess_block_type(text)
            raw_blocks.append({"page":pi+1,"block_index":j,"text":text,"block_type":btype,"is_title": text==title_map.get(pi+1,"")})
    # VRN MDL003 nine-step repair. Reflow within each page only: fixes wrapped prose
    # while preventing cross-page merges and preserving page-level topic boundaries.
    repaired=[]
    by_page=defaultdict(list)
    for b in raw_blocks: by_page[int(b.get("page",1))].append(b)
    for pg in sorted(by_page): repaired.extend(REPAIR.repair_text_blocks(by_page[pg],reflow=True))
    blocks=[]
    for j,b in enumerate(repaired):
        text=def_clean(b.get("text","")); page=int(b.get("page",1)); btype=b.get("block_type") or CORE.def_guess_block_type(text)
        sid=f"VRN-P{page:03d}-B{j:04d}-{def_hash8(text)}"
        blocks.append(CORE.SourceBlock(sid,path.name,page,j,btype,text))
    meta={
      "backend":"VRN2_M03_LAYOUT+MDL003_REPAIR",
      "pages":pages,
      "layout_module":"VRN_M03_PDF_Layout_JSON_v3",
      "repair_module":"VRN_MDL003_TableRestorer.TextRepairEngine",
    }
    return blocks,meta,title_map

# =============================================================================
# def 04 SOURCE EXTRACTION / ROUTER
# =============================================================================
def def_extract_source(path:Path)->tuple[list[Any],dict[str,Any],dict[int,str]]:
    if path.suffix.lower()==".pdf": return def_extract_pdf_vrn2(path)
    blocks,meta=CORE.def_extract_input(path)
    return blocks,meta,{}

# =============================================================================
# def 05 TOPIC UNIT SPLITTER — physical boundary first, semantic second
# =============================================================================
def def_message_subunits(block:Any)->list[dict[str,Any]]:
    text=block.text
    # Keep strong structural headings; don't split on every bullet.
    pieces=re.split(r"\n(?=(?:\d+\.\s*(?:結論|重點|內容|評論|拜訪|財報|未來)|\(\d+\)\s*(?:現況|未來|產能|產品|產業)|\[[^\]]{2,20}\]|《[^》]{2,20}》))",text)
    out=[]
    for i,p in enumerate(pieces):
        p=def_clean(p)
        if len(p)<TOPIC_MIN_CHARS: continue
        first=p.splitlines()[0][:80]
        out.append({"unit_key":f"{block.sid}-T{i+1:02d}","source_unit":block.sid,"title":first,"text":p,"page":block.page})
    if not out and len(text)>=TOPIC_MIN_CHARS:
        out=[{"unit_key":f"{block.sid}-T01","source_unit":block.sid,"title":text.splitlines()[0][:80],"text":text,"page":block.page}]
    return out

def def_pdf_units(blocks:list[Any],title_map:dict[int,str])->list[dict[str,Any]]:
    by_page=defaultdict(list)
    for b in blocks:
        if b.block_type in {"DISCLAIMER","SOURCE","URL"}: continue
        by_page[b.page].append(b)
    units=[]
    for p in sorted(by_page):
        txt="\n".join(b.text for b in by_page[p] if len(b.text)>1)
        if len(txt)<TOPIC_MIN_CHARS: continue
        title=title_map.get(p) or next((b.text for b in by_page[p] if b.block_type=="HEADING"),f"Page {p}")
        # Skip cover-only pages unless they contain meaningful body text.
        units.append({"unit_key":f"P{p:03d}","source_unit":f"PAGE-{p}","title":def_clip(title,100),"text":txt,"page":p})
    return units

def def_build_topic_units(profile:str, blocks:list[Any], title_map:dict[int,str])->list[dict[str,Any]]:
    if profile==CORE.PROFILE_MESSENGER:
        # One physical Messenger/LINE message is one detail row. Long Call Memos stay intact;
        # their internal sections are summarized into the four fixed points instead of exploding rows.
        return [
            {"unit_key":f"{b.sid}-T01","source_unit":b.sid,"title":def_clip(b.text.splitlines()[0],100),"text":b.text,"page":b.page}
            for b in blocks if len(b.text)>=TOPIC_MIN_CHARS
        ]
    return def_pdf_units(blocks,title_map) if title_map else [
        {"unit_key":b.sid,"source_unit":b.sid,"title":def_clip(b.text.splitlines()[0],100),"text":b.text,"page":b.page}
        for b in blocks if b.block_type not in {"DISCLAIMER","SOURCE","URL"} and len(b.text)>=TOPIC_MIN_CHARS
    ]

# =============================================================================
# def 05B REPORT-TYPE ROUTER OVERRIDE — filename/layout wins over semantic noise
# =============================================================================
def def_route_profile(path:Path, blocks:list[Any])->tuple[str,str]:
    name=path.name.lower()
    if "test message" in name or "messenger" in name or "line" in name:
        return CORE.PROFILE_MESSENGER,"DAILY_MESSAGE_STREAM"
    if "晨會" in name or "morning meeting" in name:
        return CORE.PROFILE_OTHER,"MORNING_MEETING"
    if any(k in name for k in ("盤勢","盤後分析","投資早報","market strategy")):
        return CORE.PROFILE_OTHER,"MARKET_STRATEGY"
    if any(k in name for k in ("債券etf周報","債券週報","macro","總經")):
        return CORE.PROFILE_OTHER,"MACRO_OUTLOOK"
    if any(k in name for k in ("產業專題","industry","outlook","pcb","thermal solutions","memory","automation","ai power")):
        return CORE.PROFILE_INDUSTRY,"INDUSTRY_REPORT"
    return CORE.def_profile_router(path,blocks)

# =============================================================================
# def 06 CLAIM EXTRACTION PER UNIT + VRN NLP HINT
# =============================================================================
def def_claims_for_unit(path:Path, unit:dict[str,Any], profile:str)->list[Any]:
    text=unit["text"]
    if profile==CORE.PROFILE_MESSENGER:
        # Preserve URL as message metadata upstream, but do not let query strings become investment claims.
        text=CORE.URL_RE.sub(" ",text)
    b=CORE.SourceBlock(
      sid=unit["unit_key"],source_id=path.name,page=unit["page"],block_index=0,
      block_type="MESSAGE" if profile==CORE.PROFILE_MESSENGER else "TOPIC_UNIT",text=text
    )
    return CORE.def_extract_claims([b])

def def_vrn_nlp_hint(text:str)->str:
    # Reuse VRN_M07 only in its extractive/local path; never call transformers/models here.
    try:
        hint=VRN_NLP.extractive_summary_fallback(text,NLP_LIBS)
        return def_clip(hint,500)
    except Exception:
        return ""

# =============================================================================
# def 07 FOUR-POINT SUMMARY CONTRACT
# =============================================================================
def def_claim_score(c:Any)->float:
    imp={"MUST_KEEP":12,"IMPORTANT":6,"SUPPORTING":1}.get(c.importance,1)
    score=imp + 2*len(c.metrics) + 1.2*len(c.stories) + .8*min(len(c.tickers),2) + .5*len(c.relations) + .4*len(c.drivers)
    low=c.text.lower()
    if len(c.tickers)>=6 or low.startswith(("多單","空單","推薦相關個股")): score-=4
    if c.text.rstrip().endswith((",","，",":","：")): score-=3
    if "http://" in low or "https://" in low or "證券研究員" in c.text: score-=5
    return score

def def_pick(claims:list[Any], used:set[str], pred, fallback:bool=True)->Optional[Any]:
    pool=[c for c in claims if c.claim_id not in used and pred(c)]
    if not pool and fallback: pool=[c for c in claims if c.claim_id not in used]
    if not pool:return None
    c=max(pool,key=def_claim_score); used.add(c.claim_id); return c

def def_four_points(claims:list[Any], title_hint:str="")->dict[str,Any]:
    used=set(); ranked=sorted(claims,key=def_claim_score,reverse=True)
    # P1: thesis / major result, avoid tiny metadata-only claims.
    p1=def_pick(ranked,used,lambda c:c.importance in {"MUST_KEEP","IMPORTANT"} and len(c.text)>18)
    # P2: why / driver / causality / demand-supply-capex.
    p2=def_pick(ranked,used,lambda c:bool(c.drivers or c.relations) and len(c.text)>18)
    # P3: impact / company / anchor / recommended stock.
    p3=def_pick(ranked,used,lambda c:bool(c.tickers or c.anchors) and len(c.text)>12)
    # P4: future / risk / guidance / forecast.
    p4=def_pick(ranked,used,lambda c:bool(c.periods) or c.uncertain or c.conditional or c.direction=="NEGATIVE" or c.attribution in {"MANAGEMENT_GUIDANCE","ANALYST_VIEW"})
    pts=[p1,p2,p3,p4]
    title=def_clip(title_hint or (p1.text if p1 else "投資情報摘要"),100)
    direction=Counter(c.direction for c in pts if c).most_common(1)[0][0] if any(pts) else "NEUTRAL_OR_MIXED"
    horizon=def_join_unique([p for c in pts if c for p in c.periods])
    return {
      "TITLE":title,
      "POINT_1":def_clip(p1.text) if p1 else "",
      "POINT_2":def_clip(p2.text) if p2 else "",
      "POINT_3":def_clip(p3.text) if p3 else "",
      "POINT_4":def_clip(p4.text) if p4 else "",
      "DIRECTION":direction,"HORIZON":horizon,
      "EVIDENCE_SIDS":def_join_unique([c.evidence_sid for c in pts if c]),
    }

# =============================================================================
# def 08 COMPANY RESOLUTION / FINANCIAL QUICK FIELDS
# =============================================================================
def def_company_map(text:str)->dict[str,str]:
    out={}
    patterns=[
      r"([A-Za-z\u4e00-\u9fff][A-Za-z0-9\u4e00-\u9fff\-]{1,24})\s*[（(]([1-9]\d{3})[）)]",
      r"(?:即時訊息_|Call Memo_|個股報告_)([1-9]\d{3})\s*([^\n\r]{1,30})",
    ]
    for m in re.finditer(patterns[0],text):
        ticker,name=m.group(2),m.group(1).strip()
        if len(name)>len(out.get(ticker,"")): out[ticker]=name
    for m in re.finditer(patterns[1],text,re.I):
        ticker=m.group(1); name=re.split(r"\s|法說會|TT",m.group(2).strip())[0]; out.setdefault(ticker,name)
    return out

def def_rating(text:str)->str:
    m=re.search(r"(?:投資評等|評等)[：:]?\s*(強力買進|買進|逢低買進|區間操作|中立|持有|賣出|未評等)",text)
    return m.group(1) if m else ""

def def_target_price(text:str)->str:
    m=re.search(r"(?:目標價|6M\s*目標價)[：:]?\s*([0-9][0-9,.]*)\s*元?",text,re.I)
    return m.group(1).replace(",","") if m else ""

def def_point_from_claim(c:Optional[Any])->str:
    return def_clip(c.text) if c else ""

def def_best_distinct_story_claims(claims:list[Any], n:int=3)->list[Any]:
    grouped=defaultdict(list)
    for c in claims:
        for st in c.stories: grouped[st].append(c)
    scored=[]
    for st,cs in grouped.items():
        best=max(cs,key=def_claim_score)
        weight=sum({"MUST_KEEP":3,"IMPORTANT":2,"SUPPORTING":1}.get(x.importance,1) for x in cs)
        scored.append((weight,st,best))
    out=[]; seen=set()
    for _,_,best in sorted(scored,key=lambda z:(-z[0],z[1])):
        if best.claim_id in seen: continue
        out.append(best); seen.add(best.claim_id)
        if len(out)>=n: break
    return out

def def_special_four(profile:str, subtype:str, claims:list[Any])->Optional[dict[str,Any]]:
    if not claims:return None
    used=set(); pts=[]
    if profile==CORE.PROFILE_MESSENGER:
        pts=def_best_distinct_story_claims(claims,3)
        macro=def_pick(claims,{c.claim_id for c in pts},lambda c:bool(c.macro_terms) and len(c.text)>20,False)
        if macro: pts.append(macro)
    elif subtype=="MARKET_STRATEGY":
        p1=def_pick(claims,used,lambda c:any(k in c.text for k in ("操作策略","台股","加權指數","重回","偏多","偏空")) and len(c.text)>20,False)
        p2=def_pick(claims,used,lambda c:bool(c.stories) and bool(c.drivers or c.relations) and len(c.text)>20)
        p3=def_pick(claims,used,lambda c:bool(c.tickers) and len(c.tickers)<=5 and len(c.text)>20)
        p4=def_pick(claims,used,lambda c:c.direction=="NEGATIVE" or c.uncertain or bool(c.periods))
        pts=[p1,p2,p3,p4]
    elif subtype=="MORNING_MEETING":
        seen=set()
        preferred=sorted(claims,key=lambda c:(c.attribution not in {"ANALYST_VIEW","MANAGEMENT_GUIDANCE"}, -def_claim_score(c)))
        for c in preferred:
            if len(c.text)<25 or len(c.text)>260: continue
            ts=[t for t in c.tickers if t not in seen]
            if not ts: continue
            pts.append(c); seen.update(ts)
            if len(pts)>=4: break
    elif subtype=="MACRO_OUTLOOK":
        p1=def_pick(claims,used,lambda c:bool(c.macro_terms) and bool(c.relations or c.drivers) and len(c.text)>25)
        p2=def_pick(claims,used,lambda c:"RATES_BONDS" in c.stories and len(c.text)>20)
        p3=def_pick(claims,used,lambda c:bool(c.periods) or c.attribution in {"MANAGEMENT_GUIDANCE","ANALYST_VIEW"})
        p4=def_pick(claims,used,lambda c:c.direction=="NEGATIVE" or c.uncertain or "風險" in c.text)
        pts=[p1,p2,p3,p4]
    else:
        return None
    pts=[p for p in pts if p]
    if not pts:return None
    while len(pts)<4:
        nxt=def_pick(claims,{c.claim_id for c in pts},lambda c:len(c.text)>18,False)
        if not nxt:break
        pts.append(nxt)
    direction=Counter(c.direction for c in pts).most_common(1)[0][0]
    return {"TITLE":"","POINT_1":def_point_from_claim(pts[0] if len(pts)>0 else None),"POINT_2":def_point_from_claim(pts[1] if len(pts)>1 else None),"POINT_3":def_point_from_claim(pts[2] if len(pts)>2 else None),"POINT_4":def_point_from_claim(pts[3] if len(pts)>3 else None),"DIRECTION":direction,"HORIZON":def_join_unique([p for c in pts for p in c.periods]),"EVIDENCE_SIDS":def_join_unique([c.evidence_sid for c in pts])}

# =============================================================================
# def 09 REPORT-LEVEL SUMMARY — one report, one row
# =============================================================================
def def_report_title(path:Path, profile:str, title_map:dict[int,str], topic_rows:list[dict[str,Any]], report_date:str)->str:
    if profile==CORE.PROFILE_MESSENGER:
        return f"{report_date or 'Daily'} Messenger / 即時投資情報摘要"
    if "晨會" in path.name:
        return path.stem
    if title_map:
        top=[]
        for p in sorted(title_map):
            t=def_clean(title_map[p])
            if t and t not in top: top.append(t)
            if len(top)>=2: break
        if top:return "｜".join(top)
    return path.stem

def def_report_summary(path:Path, profile:str, subtype:str, blocks:list[Any], title_map:dict[int,str], all_claims:list[Any], topic_rows:list[dict[str,Any]])->dict[str,Any]:
    rid=f"RPT-{def_hash8(path.name+def_file_sha(path)[:16])}"
    # Industry reports: conclusion/outline pages have editorial priority.
    preferred=[]
    if title_map:
        priority_pages={p for p,t in title_map.items() if any(k in t for k in ("結論","簡報大綱","市場焦點","重點"))}
        preferred=[]; _seen_pref=[]
        for c in [c for c in all_claims if c.page in priority_pages]:
            if any(CORE.def_similarity(c.text,x.text)>=0.88 for x in _seen_pref): continue
            preferred.append(c); _seen_pref.append(c)
    ordered=(preferred + [c for c in all_claims if c not in preferred]) if preferred else all_claims
    if profile==CORE.PROFILE_INDUSTRY and preferred:
        four=def_four_points(preferred,"")
        # Fill missing slots from the rest without allowing detailed company tables to dominate the main thesis.
        used_text={four[k] for k in ("POINT_1","POINT_2","POINT_3","POINT_4") if four[k]}
        for key,pred in [
            ("POINT_1",lambda c:len(c.text)>20),
            ("POINT_2",lambda c:bool(c.drivers or c.relations)),
            ("POINT_3",lambda c:bool(c.tickers or c.anchors)),
            ("POINT_4",lambda c:bool(c.periods) or c.uncertain or c.direction=="NEGATIVE"),
        ]:
            if four[key]: continue
            cand=next((c for c in sorted(all_claims,key=def_claim_score,reverse=True) if pred(c) and c.text not in used_text),None)
            if cand: four[key]=def_clip(cand.text); used_text.add(cand.text)
    else:
        four=def_special_four(profile,subtype,ordered) or def_four_points(ordered,"")
    story_scores=Counter()
    for c in all_claims:
        for st in c.stories: story_scores[st]+={"MUST_KEEP":3,"IMPORTANT":2,"SUPPORTING":1}.get(c.importance,1)
    main_story=story_scores.most_common(1)[0][0] if story_scores else ""
    company_map=def_company_map("\n".join(b.text for b in blocks))
    all_company_tickers=set(company_map) | {t for c in all_claims for t in c.tickers}
    rdate=def_report_date(path,blocks)
    four["TITLE"]=def_report_title(path,profile,title_map,topic_rows,rdate)
    if not four["POINT_3"] and company_map:
        four["POINT_3"]="涉及公司："+"、".join(f"{n}({t})" for t,n in list(company_map.items())[:8])
    status="PASS" if sum(bool(four[k]) for k in ("POINT_1","POINT_2","POINT_3","POINT_4"))>=3 else "REVIEW"
    return {
      "REPORT_ID":rid,"REPORT_DATE":rdate,"FILE_NAME":path.name,
      "REPORT_TYPE":profile if profile!=CORE.PROFILE_OTHER else subtype,
      "SOURCE":"MULTI_SOURCE" if profile==CORE.PROFILE_MESSENGER else def_source_name(path,blocks),"ANALYST_AUTHOR":"" if profile==CORE.PROFILE_MESSENGER else def_author(blocks),
      "MAIN_STORY":main_story,"MAIN_INDUSTRY":INDUSTRY_MAP.get(main_story,main_story),
      "TITLE":four["TITLE"],"POINT_1":four["POINT_1"],"POINT_2":four["POINT_2"],"POINT_3":four["POINT_3"],"POINT_4":four["POINT_4"],
      "DIRECTION":four["DIRECTION"],"HORIZON":four["HORIZON"],
      "COMPANY_COUNT":len(all_company_tickers),"TOPIC_COUNT":len(topic_rows),"EVIDENCE_COUNT":len(all_claims),
      "LAYOUT_ENGINE":"VRN_M03_PDF_Layout_JSON_v3" if path.suffix.lower()==".pdf" else "CORE_INPUT_PARSER",
      "TEXT_REPAIR_ENGINE":"VRN_MDL003_TextRepairEngine" if path.suffix.lower()==".pdf" else "CORE_NORMALIZER",
      "NLP_ENGINE":"VRN_M07_EXTRACTIVE+NONSTOCK_CORE_v0200",
      "STATUS":status,"DETAIL_REF":rid,
    }

# =============================================================================
# def 10 TOPIC / COMPANY / EVIDENCE TABLE BUILDERS
# =============================================================================
def def_topic_rows(path:Path, report_id:str, profile:str, units:list[dict[str,Any]])->tuple[list[dict[str,Any]],list[Any]]:
    rows=[]; all_claims=[]
    for i,u in enumerate(units,1):
        claims=def_claims_for_unit(path,u,profile); all_claims.extend(claims)
        if not claims: continue
        four=def_four_points(claims,u.get("title",f"Topic {i}"))
        sc=Counter(s for c in claims for s in c.stories); story=sc.most_common(1)[0][0] if sc else ""
        tickers=sorted({t for c in claims for t in c.tickers}); anchors=sorted({a for c in claims for a in c.anchors})
        rows.append({
          "REPORT_ID":report_id,"TOPIC_ID":f"{report_id}-T{i:03d}","SOURCE_UNIT":u["source_unit"],"TOPIC_TITLE":u.get("title","")[:120],
          "STORY_L1":story,"INDUSTRY":INDUSTRY_MAP.get(story,story),
          "TITLE":four["TITLE"],"POINT_1":four["POINT_1"],"POINT_2":four["POINT_2"],"POINT_3":four["POINT_3"],"POINT_4":four["POINT_4"],
          "DIRECTION":four["DIRECTION"],"HORIZON":four["HORIZON"],"TICKERS":def_join_unique(tickers),"GLOBAL_ANCHORS":def_join_unique(anchors),
          "EVIDENCE_SIDS":four["EVIDENCE_SIDS"],"NLP_HINT":def_vrn_nlp_hint(u["text"]),"STATUS":"PASS"
        })
    return rows,all_claims

def def_company_rows(report_id:str, blocks:list[Any], claims:list[Any])->list[dict[str,Any]]:
    full="\n".join(b.text for b in blocks); names=def_company_map(full); rows=[]
    all_tickers=sorted({t for c in claims for t in c.tickers} | set(names))
    for ticker in all_tickers:
        cs=[c for c in claims if ticker in c.tickers]
        if not cs: continue
        four=def_four_points(cs,f"{names.get(ticker,ticker)} ({ticker})")
        stories=sorted({s for c in cs for s in c.stories}); main=stories[0] if stories else ""
        local_text="\n".join(c.text for c in cs)
        rows.append({
          "REPORT_ID":report_id,"TICKER":ticker,"COMPANY_NAME":names.get(ticker,""),"STORIES":def_join_unique(stories),"INDUSTRY":INDUSTRY_MAP.get(main,main),
          "RATING":def_rating(local_text or full),"TARGET_PRICE":def_target_price(local_text or full),
          "TITLE":four["TITLE"],"POINT_1":four["POINT_1"],"POINT_2":four["POINT_2"],"POINT_3":four["POINT_3"],"POINT_4":four["POINT_4"],
          "EVIDENCE_SIDS":four["EVIDENCE_SIDS"],"STATUS":"PASS"
        })
    return rows

def def_evidence_rows(report_id:str,claims:list[Any])->list[dict[str,Any]]:
    return [{
      "REPORT_ID":report_id,"CLAIM_ID":c.claim_id,"EVIDENCE_SID":c.evidence_sid,"PAGE":c.page,"ATTRIBUTION":c.attribution,
      "IMPORTANCE":c.importance,"DIRECTION":c.direction,"STORIES":def_join_unique(c.stories),"TICKERS":def_join_unique(c.tickers),
      "DRIVERS":def_join_unique(c.drivers),"RELATIONS":def_join_unique(c.relations),"PERIODS":def_join_unique(c.periods),"TEXT":c.text
    } for c in claims]

# =============================================================================
# def 11 SINGLE FILE ANALYSIS
# =============================================================================
def def_analyze_one(path:Path)->dict[str,Any]:
    blocks,meta,title_map=def_extract_source(path)
    profile,subtype=def_route_profile(path,blocks)
    if profile==CORE.PROFILE_MESSENGER:
        blocks=CORE.def_parse_messenger_blocks(path,blocks)
    if profile==CORE.PROFILE_EVERNOTE:
        blocks=CORE.def_apply_note_layers(blocks)
    units=def_build_topic_units(profile,blocks,title_map)
    provisional_rid=f"RPT-{def_hash8(path.name+def_file_sha(path)[:16])}"
    topics,claims=def_topic_rows(path,provisional_rid,profile,units)
    # Fallback if unit splitting missed claims.
    if not claims: claims=CORE.def_extract_claims(blocks)
    report=def_report_summary(path,profile,subtype,blocks,title_map,claims,topics)
    # Ensure child rows carry final report id.
    for r in topics:r["REPORT_ID"]=report["REPORT_ID"]
    companies=def_company_rows(report["REPORT_ID"],blocks,claims)
    evidence=def_evidence_rows(report["REPORT_ID"],claims)
    return {"report":report,"topics":topics,"companies":companies,"evidence":evidence,"meta":meta,"title_map":title_map}

# =============================================================================
# def 12 BATCH / OUTPUT
# =============================================================================
def def_collect_inputs(inputs:list[str])->list[Path]:
    out=[]; allowed={".pdf",".txt",".md",".html",".htm",".docx",".enex",".json"}
    for raw in inputs:
        p=Path(raw)
        if p.is_dir(): out.extend(sorted(x for x in p.iterdir() if x.is_file() and x.suffix.lower() in allowed))
        elif p.is_file() and p.suffix.lower() in allowed: out.append(p)
    return out

def def_write_csv(path:Path,cols:list[str],rows:list[dict[str,Any]])->None:
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore'); w.writeheader(); w.writerows(rows)

def def_write_parquet_if_available(path:Path,rows:list[dict[str,Any]])->str:
    if not rows:return ""
    try:
        import pandas as pd
        pd.DataFrame(rows).to_parquet(path,index=False); return str(path)
    except Exception:return ""

def def_render_html(reports:list[dict[str,Any]],topics:list[dict[str,Any]],companies:list[dict[str,Any]])->str:
    trs="".join("<tr>"+"".join(f"<td>{html.escape(str(r.get(c,'')))}</td>" for c in ["REPORT_DATE","REPORT_TYPE","SOURCE","MAIN_STORY","TITLE","POINT_1","POINT_2","POINT_3","POINT_4","STATUS"])+"</tr>" for r in reports)
    trows="".join("<tr>"+"".join(f"<td>{html.escape(str(r.get(c,'')))}</td>" for c in ["REPORT_ID","TOPIC_TITLE","STORY_L1","TITLE","POINT_1","POINT_2","POINT_3","POINT_4"])+"</tr>" for r in topics[:MAX_TOPICS_PER_REPORT_HTML*max(1,len(reports))])
    crows="".join("<tr>"+"".join(f"<td>{html.escape(str(r.get(c,'')))}</td>" for c in ["REPORT_ID","TICKER","COMPANY_NAME","STORIES","RATING","TARGET_PRICE","POINT_1","POINT_4"])+"</tr>" for r in companies[:MAX_COMPANIES_PER_REPORT_HTML*max(1,len(reports))])
    return f"""<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>NON-STOCK SUMMARIZER v0300</title>
<style>body{{font:11px/1.45 Segoe UI,Noto Sans TC,sans-serif;background:#f4f5f7;margin:0;color:#222}}main{{padding:14px;max-width:1800px;margin:auto}}h1{{font-size:18px}}h2{{font-size:14px;margin-top:18px}}table{{width:100%;border-collapse:collapse;background:#fff}}th,td{{border-bottom:1px solid #ddd;padding:5px;vertical-align:top;text-align:left}}th{{position:sticky;top:0;background:#eee}}.note{{background:#fff;border:1px solid #ddd;padding:8px;border-radius:7px}}</style><main>
<h1>VIA NON-STOCK SUMMARIZER ENGINE v0300</h1><div class="note">One Report = One Main Row · VRN-2 Layout + Text Repair + NLP reused · Detail on demand</div>
<h2>REPORT_SUMMARY</h2><table><thead><tr>{''.join(f'<th>{c}</th>' for c in ['DATE','TYPE','SOURCE','STORY','TITLE','P1','P2','P3','P4','STATUS'])}</tr></thead><tbody>{trs}</tbody></table>
<h2>TOPIC_DETAIL</h2><table><thead><tr>{''.join(f'<th>{c}</th>' for c in ['REPORT','TOPIC','STORY','TITLE','P1','P2','P3','P4'])}</tr></thead><tbody>{trows}</tbody></table>
<h2>COMPANY_DETAIL</h2><table><thead><tr>{''.join(f'<th>{c}</th>' for c in ['REPORT','TICKER','COMPANY','STORIES','RATING','TP','P1','P4'])}</tr></thead><tbody>{crows}</tbody></table></main></html>"""

def def_run(inputs:list[str],outdir:Path)->dict[str,Any]:
    paths=def_collect_inputs(inputs); outdir.mkdir(parents=True,exist_ok=True)
    reports=[];topics=[];companies=[];evidence=[];runs=[]
    for p in paths:
        try:
            x=def_analyze_one(p); reports.append(x["report"]); topics+=x["topics"]; companies+=x["companies"]; evidence+=x["evidence"]
            runs.append({"file":p.name,"status":"PASS","report_id":x["report"]["REPORT_ID"],"topics":len(x["topics"]),"companies":len(x["companies"]),"evidence":len(x["evidence"]),"backend":x["meta"].get("backend")})
        except Exception as e:
            runs.append({"file":p.name,"status":"ERROR","error":f"{type(e).__name__}: {e}"})
    def_write_csv(outdir/'REPORT_SUMMARY.csv',REPORT_COLUMNS,reports)
    def_write_csv(outdir/'TOPIC_DETAIL.csv',TOPIC_COLUMNS,topics)
    def_write_csv(outdir/'COMPANY_DETAIL.csv',COMPANY_COLUMNS,companies)
    def_write_csv(outdir/'EVIDENCE_DETAIL.csv',EVIDENCE_COLUMNS,evidence)
    pq={
      "report":def_write_parquet_if_available(outdir/'REPORT_SUMMARY.parquet',reports),
      "topic":def_write_parquet_if_available(outdir/'TOPIC_DETAIL.parquet',topics),
      "company":def_write_parquet_if_available(outdir/'COMPANY_DETAIL.parquet',companies),
      "evidence":def_write_parquet_if_available(outdir/'EVIDENCE_DETAIL.parquet',evidence),
    }
    (outdir/'REPORT_SUMMARY.html').write_text(def_render_html(reports,topics,companies),encoding='utf-8')
    payload={
      "engine_id":ENGINE_ID,"version":ENGINE_VERSION,"network_allowed":False,
      "reused_modules":["VRN_M03_PDF_Layout_JSON_v3","VRN_MDL003_TableRestorer.TextRepairEngine","VRN_M07_Summarizer.extractive_summary_fallback","NON_STOCK_CORE_v0200"],
      "runs":runs,"report_summary":reports,"topic_detail":topics,"company_detail":companies,
      "parquet":pq,
    }
    (outdir/'RESULTS.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    return payload

# =============================================================================
# def 13 DOCTOR / SELFTEST / CLI
# =============================================================================
def def_doctor()->dict[str,Any]:
    return {
      "engine":ENGINE_NAME,"version":ENGINE_VERSION,"network_allowed":False,
      "modules":{
        "layout":"VRN_M03_PDF_Layout_JSON_v3",
        "text_repair":"VRN_MDL003_TableRestorer.TextRepairEngine",
        "nlp":"VRN_M07_Summarizer.extractive_summary_fallback",
        "core":"NON_STOCK_CORE_v0200",
      },
      "output_tables":["REPORT_SUMMARY","TOPIC_DETAIL","COMPANY_DETAIL","EVIDENCE_DETAIL"],
      "contract":"ONE_REPORT_ONE_ROW + ONE_TITLE_FOUR_POINTS + DETAILS_ON_DEMAND",
    }

def def_selftest()->int:
    checks=[]
    checks.append(("layout_loaded",hasattr(VRN_LAYOUT,"analyze_pdf_layout")))
    checks.append(("repair_loaded",hasattr(REPAIR,"repair_text_blocks")))
    checks.append(("nlp_loaded",hasattr(VRN_NLP,"extractive_summary_fallback")))
    c=CORE.Claim("c","s","e","CSP CAPEX上調帶動ASIC需求成長",1,"x","SOURCE_FACT_OR_REPORTED_DATA","POSITIVE",False,False,"IMPORTANT",stories=["ASIC_CUSTOM_SILICON"],drivers=["CAPEX","DEMAND"])
    four=def_four_points([c],"ASIC")
    checks.append(("four_point_contract",bool(four["POINT_1"])))
    checks.append(("network_off",NETWORK_ALLOWED is False))
    ok=sum(bool(v) for _,v in checks)
    print(json.dumps({"passed":ok,"total":len(checks),"checks":checks},ensure_ascii=False,indent=2))
    return 0 if ok==len(checks) else 1

def def_main(argv:Optional[list[str]]=None)->int:
    p=argparse.ArgumentParser(description=ENGINE_NAME)
    p.add_argument("inputs",nargs="*")
    p.add_argument("--outdir",default="output")
    p.add_argument("--doctor",action="store_true")
    p.add_argument("--selftest",action="store_true")
    args=p.parse_args(argv)
    if args.doctor: print(json.dumps(def_doctor(),ensure_ascii=False,indent=2)); return 0
    if args.selftest: return def_selftest()
    if not args.inputs: p.error("Provide one or more files/folders")
    result=def_run(args.inputs,Path(args.outdir))
    errors=sum(r.get("status")!="PASS" for r in result["runs"])
    print(json.dumps({"runs":result["runs"],"outdir":str(Path(args.outdir).resolve())},ensure_ascii=False,indent=2))
    return 0 if errors==0 else 2

if __name__=="__main__": raise SystemExit(def_main())
