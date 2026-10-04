#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SYSTEM MANAGER / 使用者功能說明 — 模組化單一 Layout 與擷取後修復引擎。

唯一執行入口：via-vcgc layout。既有 GLE 四模組與成功擷取保持鎖定。
私有階段：共用座標 → 文本位階 → 表格修復 → 圖片 OCR → 統一證據與呈現。
文：字級/真假粗體、七階位階、頁首頁尾、免責子樹、標題防誤併、跨頁接句、
    混合單雙欄閱讀順序、浮動圖表與章節分界、標題樹。
表：原字座標還原、上下五行防撞、補回漏列、多層表頭/跨格、同格折行、合計
    驗算、跨頁續表、重複表頭、多表切分、雙欄展開、帳戶分區、寬表防誤切。
    財報先依各自標題及年度表頭分左右欄，再按各欄標題切上下表，科目與數字對齊。
圖：子圖切分、雙Y軸防切、共用圖例、母子圖號來源、獨立OCR、座標角色與標籤。
治理：功能/def/依賴完整清冊、System Manager 卡片、輸入鎖定、快取斷點、
      原值與修復沿革、HTML/JSON/CSV/內嵌表格Markdown、檔名及實體頁排序。
實作與狀態的唯一正典是 ENGINE_MANIFEST 指向的 SSOT，不以註解宣稱功能已實測。
"""
from __future__ import annotations
import ast
import copy
import csv
import hashlib
import html
import importlib.util
import json
import sys
from pathlib import Path

# def 01_PARAMETERS — discoverable using AST literal_eval without importing code.
ENGINE_MANIFEST = {
    "schema":"VIA.EngineManifest.v1", "engine_id":"SUP_MDL743_GenericLayoutHub",
    "version":"v0104", "public_entry":"via-vcgc layout",
    "capability_ssot":"supportive modules/registry/VIA_Layout_Capabilities_SSOT_v0100.json",
    "description":"模組化單一 Layout 分析與擷取後修復；保留既有成功擷取",
    "manager_visible":True, "user_visible":True, "production_database_writes":False,
}
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
PREVIOUS = HERE / "SUP_MDL743_GenericLayoutHub_v0101.py"
PARTS = HERE / "layout_repair_v0100"
POLICY = VIA / ENGINE_MANIFEST["capability_ssot"]
SUMMARY_NAME = "LAYOUT_REVIEW.json"
HTML_NAME = "LAYOUT_REVIEW.html"
PART_NAMES = {"common":"SUP_MDL743_LayoutCommon_v0100", "text":"SUP_MDL743_LayoutText_v0100", "tables":"SUP_MDL743_LayoutTables_v0101", "figures":"SUP_MDL743_LayoutFigures_v0100"}
TABLE_GRID_STYLE = '<style>.statement-grid{display:grid;grid-template-columns:repeat(var(--statement-columns),minmax(0,1fr));gap:14px}.statement-lane{min-width:0}.table-card{padding:10px;border:1px solid #ded8ca;background:#fffdf8;margin:10px 0;break-inside:avoid}.table-card h4{margin:0 0 8px}.table-card table{width:100%}.table-card th,.table-card td{padding:4px 5px;text-align:right;white-space:nowrap}.table-card th:first-child,.table-card td:first-child{text-align:left;white-space:normal}.table-card th{background:#eee9df;border:1px solid #ded8ca}@media(max-width:850px){.statement-grid{grid-template-columns:1fr}}</style>'

# ===== [VIA:ACCEL-BRIDGE:v0100] existing canonical compatibility bridge =====
try:
    sys.path.insert(0,str(VIA / "supportive modules"))
    import VIA_SuperAccel_Module as VIA_ACCEL
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====


def def_load(path, name, package=False):
    """One instance per module name and source hash; failed imports never stay cached."""
    path=path.resolve();source=path.read_bytes();digest=hashlib.sha256(source).hexdigest()
    existing=sys.modules.get(name)
    if existing is not None and getattr(existing,'_via_source_sha256',None)==digest and Path(existing.__file__).resolve()==path:return existing
    spec=importlib.util.spec_from_file_location(name,path,submodule_search_locations=[str(path.parent)] if package else None)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    try:exec(compile(source,str(path),'exec',dont_inherit=True),module.__dict__)
    except BaseException:
        sys.modules.pop(name,None)
        raise
    module._via_source_sha256=digest
    return module


_previous=def_load(PREVIOUS,"layout_locked_hub_v0101")
_package=def_load(PARTS/"__init__.py","via_layout_repair_v0100",True)
STAGES={key:def_load(PARTS/(name+".py"),"via_layout_repair_v0100."+name) for key,name in PART_NAMES.items()}


def __getattr__(name):
    return getattr(_previous,name)


def def_manager():
    """Share one static catalog reader and renderer with System Manager."""
    choices=sorted((VIA/"supportive modules/registry").glob("CGC_MDL069_SystemManager_v*.py"))
    return def_load(choices[-1],"layout_static_manager_catalog")


def def_manifest():
    """Same complete, AST-verified catalog for VCGC, System Manager and users."""
    return def_manager().def_engine_catalog(Path(__file__))


def def_traces(source):
    """Read supplementary stroke evidence, leaving original extraction untouched."""
    if source is None:return []
    import fitz
    traces=[]
    with fitz.open(source) as doc:
        for page in doc:
            for span in page.get_texttrace():
                if span.get("type")==1:
                    traces.append({"page":page.number+1,"bbox":list(span["bbox"]),"render_mode":1,"source":"PyMuPDF stroke trace"})
    return traces


def def_repair_document(document, output, source=None, ocr_status=None):
    common,text,tables,figures=(STAGES[k] for k in ("common","text","tables","figures"))
    original_hash=hashlib.sha256(json.dumps(document,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    words=common.def_words(document);lines=common.def_lines(document);assets=common.def_assets(document)
    lines=text.def_font_evidence(lines,def_traces(source))
    lines=text.def_classify(lines,document["layout"].get("body_font_size") or common.PARAMS["font_fallback"],len(document["layout"]["pages"]))
    repaired=tables.def_recover_tables(document,words,lines,assets)
    unconfirmed=[t for t in repaired if t['state']=='UNCONFIRMED_TEXT_GRID']
    repaired=[t for t in repaired if t['state']!='UNCONFIRMED_TEXT_GRID']
    cells=[e for p in document["layout"]["pages"] for e in p["elements"] if e.get("source_method")=="pdfplumber.table_cell"]
    repaired=[tables.def_spans_and_fragments(t,cells) for t in repaired]
    figure_assets,fragments=figures.def_compact_assets(assets)
    relevant_assets=figure_assets+repaired
    ordered,floating=text.def_reading_order(lines,relevant_assets)
    repaired=tables.def_continue_tables(repaired,lines)
    repaired,relations=tables.def_adjacent(repaired)
    for table in repaired:table["checksum"]=tables.def_checksum(table)
    paragraphs=text.def_stitch(ordered,relevant_assets)
    ocr_status=ocr_status or figures.def_ocr_status()
    pictures=figures.def_figures(document,words,lines,relevant_assets,output,_previous.gle(),ocr_status)
    result={"state":"REVIEW","raw_document_sha256":original_hash,"filename":document["filename"],
            "input_sha256":document["input_sha256"],"text":{"lines":lines,"paragraphs":paragraphs,
            "retained_noise":[l for l in lines if l["role"] in text.NOISE_ROLES],"floating_assets":floating},
            "tables":repaired,"retained_table_candidates":unconfirmed,"table_relationships":relations,"figures":pictures,"retained_image_fragments":fragments,"ocr":ocr_status,
            "source_word_count":len(words),"source_words":words,"numerical_values_inferred":False}
    assert original_hash==hashlib.sha256(json.dumps(document,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),"locked extraction mutated"
    return result


def def_html_table(table):
    rows=[]
    for i,row in enumerate(table["rows"]):
        cells=[]
        for cell in row:
            if "covered_by" in cell:continue
            tag="th" if i<table["header_count"] else "td"
            cells.append(f'<{tag} colspan="{cell["colspan"]}" rowspan="{cell["rowspan"]}" title="{html.escape(cell["raw"],quote=True)}">{html.escape(cell["text"])}</{tag}>')
        rows.append("<tr>"+"".join(cells)+"</tr>")
    return '<div class="matrix"><table>'+"".join(rows)+"</table></div>"


def def_tables_html(tables):
    """Separate cards and independent lanes; never concatenate neighboring cells."""
    groups={}
    for table in sorted(tables,key=lambda t:(t['page'],t['bbox'][1],t['bbox'][0])):
        key=(table['page'],table.get('split_from') if table.get('statement_identity') else table['id'])
        groups.setdefault(key,[]).append(table)
    output=[]
    for members in groups.values():
        lanes={}
        for table in members:
            heading='第 '+','.join(map(str,table['pages']))+' 頁 · '+(table.get('caption') or table['id'])
            card='<section class="table-card" data-table-id="'+html.escape(table['id'],quote=True)+'"><h4>'+html.escape(heading)+'</h4>'+def_html_table(table)+'</section>'
            lanes.setdefault(table.get('split_column',0),[]).append(card)
        if len(lanes)>1:
            output.append('<div class="statement-grid" style="--statement-columns:'+str(len(lanes))+'">'+''.join('<div class="statement-lane" data-column="'+str(column)+'">'+''.join(lanes[column])+'</div>' for column in sorted(lanes))+'</div>')
        else:output.extend(next(iter(lanes.values())))
    return ''.join(output)


def def_catalog_html(catalog):
    return '<details class="engine-catalog"><summary>引擎完整功能與驗證範圍（System Manager 同一清冊）</summary>'+def_manager().def_catalog_html(catalog)+'</details>'


def def_figure_html(figures):
    import base64
    output=[]
    for figure in figures:
        panels=[]
        for panel in figure["panels"]:
            picture=Path(panel["image_path"])
            image='<img loading="lazy" alt="來源圖區" src="data:image/png;base64,'+base64.b64encode(picture.read_bytes()).decode()+'">' if picture.is_file() else ''
            roles=''.join('<p>'+html.escape(role)+'：'+html.escape(' | '.join(w['text'] for w in words))+'</p>' for role,words in panel["information"]["roles"].items() if words)
            panels.append('<details><summary>'+html.escape(panel.get("caption") or panel["id"])+' · '+panel["ocr_state"]+'</summary>'+image+roles+'<p>'+html.escape(panel.get("ocr_reason",""))+'</p></details>')
        output.append('<section><h4>圖區 · 第 '+str(figure["page"])+' 頁</h4>'+''.join(panels)+'</section>')
    return ''.join(output)


def def_export(report, output, catalog):
    """Export derivations separately; never update the financial production database."""
    output.mkdir(parents=True,exist_ok=True)
    _previous.def_render(report,output/HTML_NAME)
    page=(output/HTML_NAME).read_text(encoding="utf-8");markdown=[];flat=[]
    page=page.replace("<main>","<main>"+TABLE_GRID_STYLE+def_catalog_html(catalog),1)
    for document in report["documents"]:
        repair=document.get("repair")
        if not repair:continue
        name=html.escape(document["filename"])
        text="".join('<p data-role="'+p["role"]+'">'+html.escape(p["text"])+"</p>" for p in repair["text"]["paragraphs"])
        tables=def_tables_html(repair["tables"])
        notes=f'<p>狀態 REVIEW · {len(repair["tables"])} 個修復表格 · {len(repair["figures"])} 個圖區 · OCR {repair["ocr"]["state"]}</p>'
        panel='<details open class="repaired-content"><summary>整合修復：本文／FINANCIAL DATA／圖</summary>'+notes+'<details><summary>修復本文與標題</summary>'+text+'</details>'+tables+'<details><summary>圖區與 OCR 狀態</summary>'+def_figure_html(repair["figures"])+'</details></details>'
        marker=f'<h2>{name}</h2>';page=page.replace(marker,marker+panel,1)
        markdown.append("# "+document["filename"]+"\n\n"+"\n\n".join(p["text"] for p in repair["text"]["paragraphs"])+"\n\n"+tables)
        for table in repair["tables"]:
            for row in table["rows"]:
                for cell in row:flat.append({"filename":document["filename"],"table_id":table["id"],"pages":",".join(map(str,table["pages"])),"row":cell["row"],"column":cell["column"],"raw":cell["raw"],"repaired":cell["text"],"number":cell["number"],"source_ids":";".join(cell["source_ids"])})
    (output/HTML_NAME).write_text(page,encoding="utf-8")
    (output/"LAYOUT_REPAIRED.md").write_text("\n\n".join(markdown),encoding="utf-8")
    (output/"LAYOUT_REPAIRED.json").write_text(json.dumps([d.get("repair") for d in report["documents"]],ensure_ascii=False,indent=2),encoding="utf-8")
    with (output/"LAYOUT_REPAIRED.csv").open("w",encoding="utf-8-sig",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=["filename","table_id","pages","row","column","raw","repaired","number","source_ids"]);writer.writeheader();writer.writerows(flat)
    (output/"ENGINE_CATALOG.json").write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding="utf-8")
    temporary=output/(SUMMARY_NAME+".tmp");temporary.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8");temporary.replace(output/SUMMARY_NAME)


def def_cached_repair(checkpoint):
    """A corrupt or incomplete checkpoint is a cache miss, never a successful run."""
    if not checkpoint.is_file():return None
    try:
        repair=json.loads(checkpoint.read_text(encoding='utf-8'))
        pictures=[Path(p['image_path']) for f in repair['figures'] for p in f['panels']]
        if any(not p.is_file() or not p.resolve().is_relative_to(checkpoint.parent.resolve()) for p in pictures):return None
        return repair
    except (ValueError,KeyError,TypeError,OSError):return None


def def_run_batch(source, output_root, evidence=None):
    catalog=def_manifest()
    if catalog["errors"]:raise RuntimeError("CAPABILITY_REGISTRATION: "+str(catalog["errors"]))
    locks=_previous.def_locked_sources(_previous.def_policy())
    if any(v["state"]!="UNCHANGED" for v in locks.values()):raise RuntimeError("LOCK_MISMATCH")
    inputs=[source] if source.is_file() else sorted((p for p in source.rglob("*") if p.is_file() and p.suffix.casefold()==".pdf"),key=lambda p:(p.name.casefold(),p.name,str(p)))
    hashes={(_previous.def_sha(p),p.name):p for p in inputs}
    if evidence:
        report=json.loads(Path(evidence).read_text(encoding="utf-8"))
        if {(d['input_sha256'],d['filename']) for d in report['documents']}!=set(hashes):raise RuntimeError("INPUT_EVIDENCE_SET_MISMATCH")
        for doc in report["documents"]:
            key=(doc["input_sha256"],doc["filename"])
            if key not in hashes:raise RuntimeError("INPUT_EVIDENCE_MISMATCH")
            if doc["signature"]!=_previous.def_signature(hashes[key],_previous.def_policy()):raise RuntimeError("ENGINE_EVIDENCE_MISMATCH")
            proof=Path(evidence).parent/"documents"/doc["signature"]/"layout_review.json"
            if not proof.is_file():raise RuntimeError("SOURCE_CHECKPOINT_ABSENT")
            canonical=json.loads(proof.read_text(encoding="utf-8"))
            if any(doc.get(k)!=canonical.get(k) for k in ("native_geometry","layout","financial_tables")):raise RuntimeError("SOURCE_EVIDENCE_CHANGED")
        report=copy.deepcopy(report)
    else:report=_previous.def_run_batch(source,output_root)
    report["documents"].sort(key=lambda d:(d["filename"].casefold(),d["filename"]))
    report["engine"]="SUP_MDL743/v0104";report["repair_cache_hits"]=0
    runtime=STAGES["figures"].def_ocr_status()
    for doc in report["documents"]:
        signature=STAGES["common"].def_id("REPAIR",doc["signature"],_previous.def_sha(POLICY),_previous.def_sha(Path(__file__)),{n:d["sha256"] for n,d in catalog["definitions"].items()},runtime)
        folder=output_root/"repairs"/signature;folder.mkdir(parents=True,exist_ok=True);checkpoint=folder/"REPAIRED.json"
        try:
            repair=def_cached_repair(checkpoint)
            if repair is not None:
                report["repair_cache_hits"]+=1
            else:
                repair=def_repair_document(doc,folder,hashes[(doc["input_sha256"],doc["filename"])],runtime)
                tmp=checkpoint.with_suffix(".tmp");tmp.write_text(json.dumps(repair,ensure_ascii=False,indent=2),encoding="utf-8");tmp.replace(checkpoint)
            doc["repair"]=repair
        except Exception as exc:report["errors"].append({"filename":doc["filename"],"error":type(exc).__name__+": "+str(exc)})
    after=_previous.def_locked_sources(_previous.def_policy())
    if locks!=after:raise RuntimeError("LOCK_MISMATCH after repair")
    report["state"]="ERROR" if report["errors"] else "REVIEW" if report["documents"] else "NODATA"
    def_export(report,output_root,catalog)
    return report


def selftest():
    import unittest
    tests=def_load(HERE/"tests/test_layout_unified_v0102.py","via_layout_unified_tests")
    suite=unittest.defaultTestLoader.loadTestsFromModule(tests)
    return 0 if unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful() else 1


def main():
    if "--selftest" in sys.argv:return selftest()
    if "--manifest" in sys.argv:
        print(json.dumps(def_manifest(),ensure_ascii=False,indent=2));return 0
    return _previous.main()


if __name__=="__main__":raise SystemExit(main())
