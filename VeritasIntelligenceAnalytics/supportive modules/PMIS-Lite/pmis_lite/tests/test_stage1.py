"""Stage-1 自我測試。執行：python -m pytest tests/ -v  或  python tests/test_stage1.py"""
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
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pmis_lite.schema import Record
from pmis_lite.encoding import detect_file_encoding, repair_mojibake
from pmis_lite.numbering import content_hash, make_uid
from pmis_lite.textrepair import clean_email_text
from pmis_lite.classify import classify_record
from pmis_lite.stakeholders import build_registry
from pmis_lite.actions import extract_actions
from pmis_lite.completeness import CompletenessReport
from pmis_lite.attachments import extract_attachment
from pmis_lite.normalize.terms import TermStore, mine_candidates
from pmis_lite.adapters import MSProjectAdapter, PLMExportAdapter, ExcelCsvAdapter

SD = os.path.join(ROOT, "sample_data")


def test_encoding_big5():
    p = os.path.join(SD, "legacy_big5.csv")
    enc = detect_file_encoding(p)
    assert enc in ("cp950", "big5"), enc


def test_mojibake_repair_keeps_clean_text():
    assert repair_mojibake("電源供應器") == "電源供應器"


def test_numbering_stable():
    # 同身分 → 同 uid；身分不變則 uid 不變
    h1 = content_hash("PSU 設計", "Alex")
    h2 = content_hash("PSU 設計", "Alex")
    assert h1 == h2
    assert make_uid("PRJ", "GEN", h1, 6) == make_uid("PRJ", "GEN", h2, 6)


def test_textrepair_strips_reply_tail():
    raw = "本週進度正常。\nOn 2026-06-27 RD_Lin wrote:\n> 舊內容引用"
    cleaned, removed = clean_email_text(raw)
    assert "本週進度正常" in cleaned
    assert "舊內容引用" not in cleaned
    assert removed


def test_classify_uses_synonym():
    cfg = {"product": {"電源供應器": ["psu", "電供"]}}
    store = TermStore(seed={"電源供應器": ["電供"]})
    rec = Record(title="電供老化測試")
    classify_record(rec, cfg, normalize_fn=store.normalize)
    assert rec.product == "電源供應器"


def test_term_mining_rejects_role_abbr():
    # RD/PM 是單位角色 → 不應成為產品同義候選；VFD(變頻器) 應被括號標註抓到
    store = TermStore(seed={"變頻器": ["VFD"], "電源供應器": []})
    recs = [
        Record(title="本週 VFD 量產", body="變頻器(VFD) MP OK", uid="A"),
        Record(title="PSU 案", body="RD 與 PM 討論 電源供應器", uid="B"),
        Record(title="PSU 案2", body="RD 回覆 電源供應器", uid="C"),
    ]
    # VFD 已在 seed → 不會再被提；改測 RD/PM 不被當同義詞
    store2 = TermStore(seed={"電源供應器": []})
    cands = mine_candidates(recs, store2, min_frequency=1, min_confidence=0.55)
    surfaces = {c.surface for c in cands}
    assert "RD" not in surfaces and "PM" not in surfaces


def test_stakeholder_registry():
    recs = [
        Record(actor="Alex", counterparts="Ben;Cathy", product="PSU"),
        Record(actor="Alex", counterparts="Ben", product="PSU"),
    ]
    reg = build_registry(recs)
    assert reg["Alex"].as_sender == 2
    assert reg["Alex"].engagement == "active"
    assert reg["Ben"].as_recipient == 2


def test_action_extraction_with_due():
    recs = [Record(uid="X", title="效率追蹤", body="請 RD 改善，2026-07-05 前回覆", actor="Alex")]
    items = extract_actions(recs)
    assert items and items[0].due == "2026-07-05"
    assert items[0].owner == "Alex"


def test_msproject_adapter_skips_empty_task():
    audit = CompletenessReport()
    recs = list(MSProjectAdapter(os.path.join(SD, "project_export.xml"), audit=audit).read())
    titles = [r.title for r in recs]
    assert "PSU 電路設計" in titles
    # 4 個 task，1 個空名 → seen=4, extracted=3, failed=1
    a = audit.audit("msproject")
    assert a.seen == 4 and a.extracted == 3 and a.failed == 1
    assert a.unexplained_gap == 0   # 失敗有原因 → 無未解釋遺漏


def test_plm_adapter_flags_empty_row():
    audit = CompletenessReport()
    recs = list(PLMExportAdapter(os.path.join(SD, "plm_export.csv"), audit=audit).read())
    assert any("PSU-2026-001" in r.title for r in recs)
    a = audit.audit("plm")
    assert a.failed == 1            # 空列被標記
    assert a.unexplained_gap == 0


def test_attachment_docx_and_xlsx():
    d = extract_attachment(os.path.join(SD, "attachments", "PSU_LLC_efficiency_report.docx"))
    assert d.ok and "效率" in d.text
    x = extract_attachment(os.path.join(SD, "attachments", "EVT_results.xlsx"))
    assert x.ok and "FAIL" in x.text


def test_attachment_unsupported_is_honest():
    r = extract_attachment(os.path.join(SD, "attachments", "weird_file.dat"))
    assert not r.ok and "unsupported" in r.reason


def test_completeness_gate_pass():
    rep = CompletenessReport()
    a = rep.audit("src"); a.seen = 10; a.extracted = 8
    a.failures = [("x", "empty_row"), ("y", "no_title_or_body")]  # 結構性略過
    o = rep.overall()
    assert o["status"] == "PASS"
    assert o["structural_skipped"] == 2
    assert o["coverage_pct"] == 100.0          # 結構略過不拉低涵蓋率


def test_completeness_gate_fail_on_unexplained():
    rep = CompletenessReport()
    a = rep.audit("src"); a.seen = 10; a.extracted = 8   # 2 筆憑空消失，無 failures 記錄
    assert rep.overall()["status"] == "FAIL"


def test_completeness_recoverable_vs_structural():
    from pmis_lite.completeness import categorize
    assert categorize("unsupported_type") == "recoverable"
    assert categorize("no_text_layer(掃描檔，需OCR)") == "recoverable"
    assert categorize("empty_row") == "structural"
    assert categorize("error:ValueError") == "error"
    rep = CompletenessReport()
    a = rep.audit("att"); a.seen = 3; a.extracted = 2
    a.failures = [("scan.pdf", "no_text_layer(掃描檔，需OCR)")]
    o = rep.overall()
    assert o["recoverable"] == 1 and o["status"] == "PASS"
    assert rep.recoverable_items()[0][1] == "scan.pdf"


def test_detection_audit_reports_unclassified():
    from pmis_lite.autodetect import probe, verify_detection
    info = probe(scan_roots=[SD])
    v = verify_detection(info)
    assert v["total_files"] >= 5
    assert any("weird_file.dat" in p for p in v["unclassified_samples"])
    assert 0 < v["classify_rate"] <= 100


def test_autodetect_separates_plm_and_excel():
    from pmis_lite.autodetect import probe, build_sources
    info = probe(scan_roots=[SD])
    d = info["discovered"]
    # plm_export.csv 應歸 PLM，不應同時出現在 excel_csv
    assert any("plm_export" in p for p in d["plm"])
    assert not any("plm_export" in p for p in d["excel_csv"])
    assert any("project_export.xml" in p for p in d["msproject_xml"])
    srcs = build_sources(info)
    plm = [s for s in srcs if s["type"] == "plm"]
    excel = [s for s in srcs if s["type"] == "excel_csv"]
    assert plm and excel
    assert not any("plm_export" in s["path"] for s in excel)


def test_classify_multipass_thread_propagation():
    from pmis_lite.classify import classify_all
    cls = {"product": {"電源供應器": ["psu"]}}
    recs = [
        Record(title="PSU 設計", body="psu 案", uid="A", thread_id="T1"),
        Record(title="回覆", body="收到了", uid="B", thread_id="T1"),   # 同串無關鍵字
    ]
    classify_all(recs, cls)
    assert recs[0].product == "電源供應器"
    assert recs[1].product == "電源供應器"   # 由討論串傳播救回


def test_seed_buckets_from_data():
    from pmis_lite.classify import seed_buckets_from_data
    cls = {"product": {}}
    recs = [Record(title="x", product="變頻器"), Record(title="y", product="散熱模組")]
    seed_buckets_from_data(recs, cls, dims=("product",))
    assert "變頻器" in cls["product"] and "散熱模組" in cls["product"]


def test_keyword_generation_discriminative():
    from pmis_lite.keywords import generate_keyword_candidates
    cls = {"product": {"電源供應器": [], "變頻器": []}}
    recs = [
        Record(title="a", body="LLC 諧振 拓樸", product="電源供應器", uid="1"),
        Record(title="b", body="LLC 效率 量測", product="電源供應器", uid="2"),
        Record(title="c", body="散熱片 風扇 變更", product="變頻器", uid="3"),
        Record(title="d", body="散熱片 噪音 風扇", product="變頻器", uid="4"),
    ]
    cands = generate_keyword_candidates(recs, cls, dim="product", min_count=2, min_score=0.6)
    terms = {(c["bucket"], c["term"]) for c in cands}
    assert ("電源供應器", "llc") in terms       # LLC 只在電源桶 → 高鑑別
    assert ("變頻器", "散熱片") in terms or ("變頻器", "風扇") in terms


def test_panorama_stalled_detection():
    from pmis_lite.panorama import build_panorama
    recs = [
        Record(title="舊案", event_time="2026-05-01", product="A", status="進行中"),
        Record(title="新案", event_time="2026-06-28", product="B", status="進行中"),
    ]
    pan = build_panorama(recs, stalled_days=14)
    stalled = {s["product"] for s in pan["stalled"]}
    assert "A" in stalled and "B" not in stalled



def test_resilience_fallback_chain():
    from pmis_lite.resilience import Strategy, run_chain
    def boom(): raise RuntimeError("x")
    chain = [Strategy("a", boom), Strategy("b", lambda: None), Strategy("c", lambda: [1, 2])]
    r = run_chain(chain, validate=lambda v: bool(v))
    assert r.ok and r.used == "c"
    assert [a[1] for a in r.attempts] == ["fail", "empty", "ok"]



def test_selfcheck_runs_offline():
    from pmis_lite.selfcheck import run_selfcheck
    rep = run_selfcheck()
    assert rep["overall"] in ("PASS", "WARN", "FAIL")
    names = [c.name for c in rep["checks"]]
    assert "離線運作保證" in names
    assert any("Python" in n for n in names)


def test_selfcheck_detects_bad_data():
    from pmis_lite.selfcheck import check_data
    class A: unexplained_gap = 3
    checks = check_data({"records": [], "audit": A()})
    statuses = {c.name: c.status for c in checks}
    assert statuses.get("擷取結果") == "FAIL"
    assert statuses.get("完整性 gate") == "FAIL"



def test_feedback_capture_and_summary(tmp_path=None):
    import tempfile, os
    from pmis_lite.feedback import record_feedback, summarize, DELIGHT, DISAPPOINT
    assert len(DELIGHT) == 20 and len(DISAPPOINT) == 20
    fp = os.path.join(tempfile.mkdtemp(), "fb.jsonl")
    for t in ["D03", "D03", "X04"]:
        record_feedback(fp, t)
    s = summarize(fp)
    assert s["total"] == 3
    assert s["delight"][0][0] == "D03" and s["delight"][0][2] == 2
    assert s["priority"][0]["tag"] == "X04" and s["priority"][0]["remedy"]



def test_mail_imap_message_to_record():
    from datetime import datetime
    from pmis_lite.adapters.mail_imap import message_to_record
    class M:
        uid="9"; subject="Re: PSU 效率"; from_="a@x.com"; to=("b@y.com",); cc=()
        date=datetime(2026,6,28,14,30); text="效率 92%\n\n> 引文"; html=""; headers={"message-id":["<i@x>"]}
    r=message_to_record(M())
    assert r.source_type=="mail_imap" and r.thread_id=="PSU 效率"
    assert isinstance(r.body,str) and "引文" not in r.body   # 引文已剝除


def test_supplement_record_and_enrich():
    import csv, os, tempfile
    from pmis_lite.schema import Record
    from pmis_lite.adapters.supplement import SupplementAdapter, enrich_records
    p=os.path.join(tempfile.mkdtemp(),"s.csv")
    with open(p,"w",encoding="utf-8-sig",newline="") as f:
        w=csv.writer(f); w.writerow(["relate_to","title","note","status"])
        w.writerow(["T1","電話結論","交期延一週","進行中"])
    # 模式A：獨立補充事件
    recs=list(SupplementAdapter(p).fetch())
    assert recs and recs[0].source_type=="supplement" and recs[0].thread_id=="T1"
    # 模式B：enrich 既有（append-only，不覆寫，補空欄）
    base=[Record(title="x", body="原文", thread_id="T1")]
    n=enrich_records(base, p)
    assert n==1 and "原文" in base[0].body and "人工補充" in base[0].body and base[0].status=="進行中"



def test_oauth_message_to_record():
    import base64
    from pmis_lite.adapters.mail_oauth import _gmail_msg_to_record, _graph_msg_to_record
    b=base64.urlsafe_b64encode("效率 92%\n\n> 引文".encode()).decode()
    g={"id":"a","snippet":"","payload":{"mimeType":"x","headers":[
        {"name":"Subject","value":"Re: PSU"},{"name":"From","value":"a@x"},
        {"name":"Date","value":"Sun, 28 Jun 2026 14:30:00 +0800"}],
        "parts":[{"mimeType":"text/plain","body":{"data":b}}]}}
    r=_gmail_msg_to_record(g)
    assert r.source_type=="gmail_oauth" and r.thread_id=="PSU" and "引文" not in r.body
    j={"id":"m","subject":"DVT","from":{"emailAddress":{"address":"p@x"}},
       "toRecipients":[{"emailAddress":{"address":"t@y"}}],"ccRecipients":[],
       "receivedDateTime":"2026-06-27T09:15:00Z","body":{"content":"公差"},"bodyPreview":""}
    r2=_graph_msg_to_record(j)
    assert r2.source_type=="m365_oauth" and r2.actor=="p@x"


def test_mail_fallback_chain_degrades():
    from pmis_lite.mail_chain import fetch_with_fallback
    fetchers={
        "outlook": lambda months: (_ for _ in ()).throw(RuntimeError("no com")),
        "m365_oauth": lambda *a: (_ for _ in ()).throw(RuntimeError("blocked")),
        "gmail_oauth": lambda *a: [], "imap": lambda *a: [{"title":"x"}], "export": lambda d: [],
    }
    cfg={"outlook":{"enabled":True},"m365_oauth":{"client_id":"a","tenant":"t"},
         "imap":{"provider":"gmail","user":"u","token":"t"}}
    recs,res=fetch_with_fallback(cfg,fetchers)
    assert res.used=="IMAP App Password" and len(recs)==1
    assert "blocked" in res.report()


def test_jsonl_mail_adapter(tmp=None):
    import json, os, tempfile
    from pmis_lite.adapters import JsonlMailAdapter
    p=os.path.join(tempfile.mkdtemp(),"m.jsonl")
    open(p,"w",encoding="utf-8").write(json.dumps({"title":"PSU","thread_id":"PSU","source_type":"gmail_oauth"})+"\n")
    recs=list(JsonlMailAdapter(p).read())
    assert len(recs)==1 and recs[0].title=="PSU" and recs[0].source_type=="gmail_oauth"



def test_process_mining_dfg_bottleneck_rework_conformance():
    from pmis_lite.schema import Record
    from pmis_lite import process_mining as pm
    def R(c, a, d): return Record(title=a, thread_id=c, topic=a, event_time=f"2026-06-{d:02d}", actor="x")
    recs = [R("A","EVT",1), R("A","DVT",5), R("A","DVT",9), R("A","PVT",14), R("A","MP",20),
            R("B","EVT",2), R("B","PVT",6)]
    res = pm.mine(recs, expected_sequence=["EVT","DVT","PVT","MP"], activity_field="topic")
    assert res["cases"] == 2
    # 返工：A 的 DVT 出現兩次 + 自我環
    assert res["rework"]["self_loops"].get("DVT") == 1
    assert any(v["activity"]=="DVT" and v["times"]==2 for v in res["rework"]["revisits"])
    # 合規：B 偷跑跳過 DVT
    assert any(v["type"].startswith("偷跑") for v in res["conformance"])
    # DFG 有邊、瓶頸有排序
    assert res["dfg"]["edges"] and res["bottlenecks"]
    svg = pm.render_svg(res, ["EVT","DVT","PVT","MP"])
    assert svg.startswith("<svg") and "返工" in svg




def test_enterprise_presets_and_html_ui():
    from pmis_lite.presets import apply_preset, list_presets, ENTERPRISE_PRESETS
    from pmis_lite import html_ui
    assert len(ENTERPRISE_PRESETS) >= 6
    # SAP MM：原始單號原封存 source_ref
    rows = [{"EBELN":"4500012345","MATNR":"PSU","MAKTX":"電源","LIFNR":"V1","BEDAT":"2026-06-20","MENGE":"1000"}]
    r = apply_preset(rows, "sap_mm")[0]
    assert r.source_ref == "4500012345" and r.product == "PSU" and r.title == "電源"
    assert "1000" in r.body
    # HTML UI：表格/表單/JS
    html = '<table><tr><th>EBELN</th><th>MATNR</th></tr><tr><td>4500012346</td><td>FAN</td></tr></table>' \
           '<input name="werks" value="TW01"><script>var c={"module":"MM","rows":1};</script>'
    ui = html_ui.read_html_ui(html)
    assert ui["table_rows"][0]["EBELN"] == "4500012346"
    assert any(f["name"]=="werks" for f in ui["form_fields"])
    assert ui["js_data"][0]["module"] == "MM"
    # HTML 表格 → preset → Record
    recs = apply_preset(ui["table_rows"], "sap_mm")
    assert recs[0].source_ref == "4500012346"


def test_autocode_domain_agnostic_and_dedup():
    from pmis_lite.schema import Record
    from pmis_lite.autocode import mint_universal_id, identity_key
    r1 = Record(title="PSU 審查", actor="a@x", body="v1", event_time="2026-06-20")
    r2 = Record(title="PSU 審查", actor="a@x", body="v2-改了", event_time="2026-06-20")  # 內容變
    c1, c2 = mint_universal_id(r1, "mail"), mint_universal_id(r2, "mail")
    assert c1 == c2                       # 身分碼綁標題+行為者，內容變不影響 → 天然去重
    r3 = Record(title="別的事", actor="b@y", body="x", event_time="2026-06-20")
    assert mint_universal_id(r3, "mail") != c1


def test_auto_ssot_zero_config():
    from pmis_lite.schema import Record
    from pmis_lite.autocode import auto_ssot
    recs = [Record(title="A EVT", topic="EVT", event_time="2026-06-01", source_type="mail"),
            Record(title="A DVT", topic="DVT", event_time="2026-06-05", source_type="mail"),
            Record(title="B EVT", topic="EVT", event_time="2026-06-02", source_type="mail")]
    out = auto_ssot(recs, dims=("topic",))
    assert out["verify"]["pass"] and out["verify"]["duplicate_codes"] == 0
    assert out["verify"]["buckets_discovered"]["topic"] >= 2   # 桶自資料長出


def test_msproject_and_plm_presets():
    from pmis_lite.presets import apply_preset, ENTERPRISE_PRESETS
    assert "plm_ecm" in ENTERPRISE_PRESETS and "ms_project" in ENTERPRISE_PRESETS
    msp = apply_preset([{"UID":"1001","Name":"EVT","Text1":"PN-PSU-500","Start":"2026-06-01","PercentComplete":"100"}], "ms_project")
    assert msp[0].source_ref == "1001" and "PN-PSU-500" in msp[0].raw_keys
    ecm = apply_preset([{"ChangeNumber":"ECN-088","Description":"改銅質","Reason":"降溫","AffectedMaterial":"PN-PSU-500","ValidFrom":"2026-06-12"}], "plm_ecm")
    assert ecm[0].source_ref == "ECN-088" and ecm[0].product == "PN-PSU-500" and "降溫" in ecm[0].body



def test_self_training_learning_curve():
    from pmis_lite.schema import Record
    from pmis_lite.self_train import run_training
    recs = [Record(title="P1", body="LLC 效率", product="電源供應器", uid="1"),
            Record(title="P2", body="LLC 輕載 效率", product="電源供應器", uid="2"),
            Record(title="回覆", body="LLC 效率 量測", product="", uid="3"),
            Record(title="V1", body="散熱片 風扇", product="變頻器", uid="4"),
            Record(title="V2", body="散熱片 風扇 振動", product="變頻器", uid="5")]
    res = run_training(recs, dim="product", rounds=3, auto_approve_score=0.9)
    # 學習後歸類率應提升，且詞庫 append-only 長出關鍵字
    assert res["final_rate"] >= res["curve"][0]["rate"] - 0.01
    kws = res["final_keywords"]["product"]
    assert any(len(v) > 0 for v in kws.values())      # 有學到詞
    # 收斂：最後一輪 gain 為 0（學不到就停）
    assert res["curve"][-1]["gain"] == 0.0 or len(res["curve"]) == 3



def test_psu_industry_seed_coldstart():
    from pmis_lite.schema import Record
    from pmis_lite import psu_taxonomy as tax
    from pmis_lite.classify import classify_all
    seed = tax.build_psu_seed()
    assert len(seed["product"]) >= 8 and len(seed["topic"]) >= 10 and len(seed["component"]) >= 8
    # 高信心 keyword 命中（確定性）
    cls = {"topic": dict(seed["topic"])}
    r1 = Record(title="LLC 諧振", body="llc 諧振 resonant", uid="1")
    r2 = Record(title="散熱", body="散熱片 heatsink 風扇", uid="2")
    classify_all([r1, r2], cls)
    assert r1.topic.startswith("主轉換") and r2.topic.startswith("散熱")
    cls2 = {"product": dict(seed["product"])}
    r3 = Record(title="CRPS", body="crps 冗餘 熱插拔 server", uid="3")
    classify_all([r3], cls2)
    assert "Server" in r3.product



def test_bom_template_validate_and_tree():
    from pmis_lite import bom_template as bt
    assert len(bt.template_header()) >= 30 and len(bt.REQUIRED) >= 8
    assert "電容" in bt.classify_commodity("MLCC 100uF")
    assert "電晶體" in bt.classify_commodity("GaN MOSFET")
    bom = [
        {"Level":0,"Parent_PN":"","Item_PN":"P1","Description":"成品","Commodity":"板類 Board / PCBA","Qty":1,"UOM":"PC","Item_Status":"Active","RoHS":"Y","Rev":"A"},
        {"Level":1,"Parent_PN":"P1","Item_PN":"C1","Description":"電容","Commodity":"被動元件 Passive / 電容 Capacitor","Qty":2,"UOM":"PC","Ref_Des":"C1,C2","Item_Status":"Active","RoHS":"Y","Rev":"A","Unit_Cost":10},
        {"Level":1,"Parent_PN":"P1","Item_PN":"BAD","Description":"","Commodity":"","Qty":1,"UOM":"PC","Item_Status":"Active","RoHS":"Y","Rev":"A"},
    ]
    v = bt.validate_bom(bom)
    assert v["pass"] is False and v["stats"]["errors"] >= 2   # BAD 缺 Description/Commodity
    assert bt.where_used(bom, "C1") == ["P1"]
    assert bt.cost_rollup([r for r in bom if r["Item_PN"]!="BAD"])["P1"] == 20.0
    d = bt.diff_bom([{"Item_PN":"A","Qty":1}], [{"Item_PN":"A","Qty":2},{"Item_PN":"B","Qty":1}])
    assert "B" in d["added"] and d["qty_changed"][0]["to"] == 2



def test_super_bom_dims_and_thermal():
    from pmis_lite import super_bom as sb
    c = sb.coverage()
    assert c["companies"] >= 6 and c["product_families"] >= 40
    assert "水冷板" in sb.classify_commodity_super("cold plate 水冷板")
    assert "熱導管" in sb.classify_commodity_super("heat pipe")
    assert "均熱片" in sb.classify_commodity_super("IHS 均熱片")
    assert "電晶體" in sb.classify_commodity_super("GaN MOSFET")   # 電子域仍可歸
    assert set(sb.SUPER_DIMENSIONS) <= set(sb.super_bom_header())
    bom = [
        {"Company":"奇鋐 AVC","Business_Unit":"液冷","Product_Family":"水冷板","Level":0,"Parent_PN":"","Item_PN":"CP1","Description":"水冷板","Commodity":"散熱-液冷 Thermal-Liquid / 水冷板 Cold Plate","Qty":1,"UOM":"PC","Item_Status":"Active","RoHS":"Y","Rev":"A"},
        {"Company":"","Business_Unit":"","Product_Family":"","Level":1,"Parent_PN":"CP1","Item_PN":"X1","Description":"件","Commodity":"其他 Others / 原材料 Raw","Qty":1,"UOM":"PC","Item_Status":"Active","RoHS":"Y","Rev":"A"},
    ]
    v = sb.validate_super_bom(bom)
    assert v["pass"] is False   # 第二列缺三維
    assert any(i["type"] == "缺維度" for i in v["issues"])



def test_ingest_engine_guarantee_dedup():
    import os, tempfile
    from pmis_lite import ingest_engine as ie
    d = tempfile.mkdtemp()
    open(os.path.join(d,"a.txt"),"w",encoding="utf-8").write("重要決定\n\n客戶交期提前\n")
    open(os.path.join(d,"b.csv"),"w",encoding="utf-8-sig").write("料號,量\nP1,4\n,\n")
    open(os.path.join(d,"c.txt"),"w",encoding="utf-8").write("重要決定\n")   # 與 a 首行重複
    open(os.path.join(d,"img.png"),"wb").write(b"\x89PNG\r\n")
    paths=[os.path.join(d,x) for x in ["a.txt","b.csv","c.txt","img.png"]]
    res = ie.run_ingest(paths, dims=("topic",))
    g = res["completeness"]
    assert g["unexplained_gap"] == 0 and g["guarantee_pass"] is True   # 每個未擷取都有原因
    assert res["parameters"]["dedup"]["duplicates"] >= 1               # 抓到重複
    assert res["parameters"]["correction"]["verify_pass"] is True      # 校正無資料流失
    # image 誠實標記 needs-OCR（recoverable，不假裝抓到）
    assert g["failures_by_cause"]["recoverable"] >= 1
    assert isinstance(res["summary"]["key_terms"], list)


def test_module_scan_and_nodedup_csv():
    import os, tempfile
    from pmis_lite import module_scan as ms, ingest_engine as ie
    # cwd 相依修正:相對 "pmis_lite" 只在套件母目錄執行時成立(操作員自庫根跑
    # 即 FAIL count>=20)— 改以 ROOT 錨定,任何 cwd 皆可跑
    r = ms.scan_project(os.path.join(ROOT, "pmis_lite"))
    assert r["count"] >= 20
    roles = r["by_role"]
    assert roles.get("SUPPORTIVE", 0) >= 1 and roles.get("FUNCTIONAL", 0) >= 1
    # schema 應為高扇入 SUPPORTIVE
    schema = [it for it in r["inventory"] if it["module"] == "schema"]
    if schema:
        assert schema[0]["role"] == "SUPPORTIVE" and schema[0]["fan_in"] >= 3
    # 不去重 + 逐筆編號 + CSV
    d = tempfile.mkdtemp()
    open(os.path.join(d, "x.txt"), "w", encoding="utf-8").write("甲\n乙\n甲\n")  # 重複「甲」
    csvp = os.path.join(d, "out.csv")
    res = ie.run_ingest([os.path.join(d, "x.txt")], dedup_on=False, csv_path=csvp)
    assert res["parameters"]["dedup"]["mode"] == "no-dedup"
    assert res["data"][0]["seq"].startswith("VIS-")
    assert os.path.exists(csvp)
    assert len(res["data"]) == 3   # 不去重，三筆都在（含重複的甲）



def test_fin_verify_gate_and_cost():
    from pmis_lite import fin_verify as fv
    good = {"revenue":100,"cogs":60,"grossProfit":40,"opex":10,"opInc":30,
            "pretax":30,"tax":6,"netInc":24,"ta":200,"tl":80,"equity":120,
            "ca":90,"cash":30,"ar":30,"inventory":20,"otherCA":10}
    r = fv.verify_report(good)
    assert r["usable"] is True and r["status"] == "VERIFIED"
    bad = dict(good); bad["equity"] = 100   # 資產≠負債+權益
    r2 = fv.verify_report(bad)
    assert r2["usable"] is False and r2["status"] == "UNVERIFIED"
    assert any(not c["ok"] and c["hard"] for c in r2["checks"])
    # 成本結構
    cs = fv.cost_structure(unit_variable=60, fixed_cost=1000, price=100, volume=50)
    assert cs["unit_contribution"] == 40 and cs["breakeven_units"] == 25.0
    assert cs["margin_of_safety"] is not None
    # 校準
    cal = fv.calibrate(95, 100, 0.05)
    assert cal["within_tolerance"] is True   # -5% 剛好在容忍內
    # 同業
    pt = fv.peer_table([{"name":"A","gm":0.3},{"name":"B","gm":0.4}], ["gm"])
    assert pt["n"] == 2 and pt["stats"]["gm"]["max"] == 0.4



def test_bom_analysis_deep():
    from pmis_lite import bom_analysis as ba
    bom = [
        {"parent":"A","child":"B","qty":2},
        {"parent":"A","child":"C","qty":3},
        {"parent":"B","child":"D","qty":4},
        {"parent":"B","child":"D2","qty":4,"alt":"DG"},  # 替代群組
        {"parent":"B","child":"D2ALT","qty":4,"alt":"DG"},
    ]
    im = {"B":{"rohs":True,"lead_days":30,"std_cost":0},
          "C":{"rohs":False,"lead_days":10,"std_cost":5},
          "D":{"rohs":True,"lead_days":60,"std_cost":2},
          "D2":{"rohs":True,"lead_days":20,"std_cost":9},
          "D2ALT":{"rohs":True,"lead_days":15,"std_cost":7}}
    aml = [{"item":"C","rank":1,"price":5},{"item":"D","rank":1,"price":2},
           {"item":"D2","rank":1,"price":9},{"item":"D2ALT","rank":1,"price":7}]
    ex = ba.explode(bom,"A")
    # 累計用量：D 在 B(=2) 之下用量4 → 8
    d = [l for l in ex if l["child"]=="D"][0]
    assert d["accumulated_qty"] == 8 and d["level"] == 2
    r = ba.analyze(bom,"A",im,aml)
    assert r["max_depth"] == 2
    assert r["compliance"]["compliant"] is False and "C" in r["compliance"]["non_compliant"]
    assert r["lead_time"]["critical_days"] == 60 and r["lead_time"]["critical_item"] == "D"
    # 替代料：lowest 應比 preference 便宜或相等（此處 D2ALT 7 < D2 9）
    assert r["total_cost_lowest"] <= r["total_cost_preference"]
    assert ba.where_used(bom,"D") == ["B"]
    # 決策群組去重：DG 群組只計一次
    dg_lines = [l for l in r["cost_lines"] if l.get("alt")=="DG"]
    assert len(dg_lines) == 1



def test_synonym_ssot_and_plm_pmbok():
    from pmis_lite import ssot_synonyms as ss, plm_pmbok_ref as pp
    s = ss.build_default()
    # 唯一基準：多術語 → 同一 canonical
    assert s.resolve("ECO") == "SSOT-CHANGE"
    assert s.resolve("AENR") == "SSOT-CHANGE"
    assert s.resolve("工程變更單") == "SSOT-CHANGE"
    n0 = len(s.canonical)
    # 增量加同義字（append-only，canonical 不增）
    assert s.add_synonym("變更管制", "SSOT-CHANGE")["ok"] is True
    assert len(s.canonical) == n0
    # 衝突：改指別的 canonical 被擋
    c = s.add_synonym("ECO", "SSOT-BOM")
    assert c["ok"] is False and c["reason"] == "conflict"
    # 宣告後可覆寫
    assert s.add_synonym("ECO", "SSOT-BOM", declare_override=True)["ok"] is True
    s.add_synonym("ECO", "SSOT-CHANGE", declare_override=True)  # 還原
    # PLM + PMBOK 同步
    rep = pp.sync_frameworks(s)
    assert rep["usable"] is True and rep["missing"] == 0
    assert s.resolve("Task") == "SSOT-SCHEDULE"
    assert s.resolve("Schedule 時程管理") == "SSOT-SCHEDULE"
    assert len(pp.PMBOK_AREAS) == 10 and len(pp.PMBOK_PROCESS) == 5
    # canonical 仍唯一
    assert len(s.canonical) == n0


def test_ingest_plus_smart_asset():
    import os, tempfile
    from pmis_lite import code_parse as cp, table_repair as tbl, smart_asset as sa, ingest_plus as ip
    # 程式語言解析
    st = cp.parse_structure("def foo():\n  pass\nclass Bar:\n  pass\nimport os", lang="Python")
    assert "foo" in st["functions"] and "Bar" in st["classes"]
    assert cp.detect_language(path="x.ps1") == "PowerShell"
    # 表格修復:參差列補齊
    rows = [["a","b","c"],["1","2"],["3","4","5"]]
    rep = tbl.repair_table(rows)
    assert rep["cols"] == 3 and rep["report"]["padded_cells"] >= 1
    assert rep["report"]["verify_pass"] is True
    # 智慧資產:實體萃取 + 型別
    ents = sa.extract_entities("料號 CP-GB200 金額 1,250,000 影響 3653 毛利 38%")
    assert "partno" in ents and "ticker_tw" in ents and "amount" in ents
    db = sa.build_asset_db([{"text":"CP-GB200 缺料 3653","source":"t"},{"text":"a@b.com 通知","source":"t"}])
    assert db["stats"]["total"] == 2
    assert db["stats"]["validation"]["verify_pass"] is True
    # 末日統一入口
    d = tempfile.mkdtemp()
    open(os.path.join(d,"m.py"),"w").write("def run():\n return 1")
    open(os.path.join(d,"t.csv"),"w").write("k,v\n3017,1450\n3324,720,x")
    rep2, db2 = ip.doomsday_intake([os.path.join(d,"m.py"), os.path.join(d,"t.csv")])
    assert rep2["guarantee"]["guarantee_pass"] is True
    assert rep2["asset_db"]["total"] >= 1
    assert rep2["intake_pass"] is True


def test_via_unified_engines():
    from pmis_lite.via_engines import VIA
    via = VIA()
    eng = via.engines()
    assert len(eng) == 7                       # 50 模組整合為 7 引擎
    assert via.ssot.resolve("AENR") == "SSOT-CHANGE"
    assert "Where-Used" in via.knowledge.tcode("CS15")
    assert "水冷板" in via.bom.classify("液冷 水冷板 cold plate")
    r = via.finance.verify({"assets":100,"liabilities":40,"equity":60,"revenue":50,
                            "cogs":30,"gross":20,"opex":10,"op":10,"net":8})
    assert r.get("usable") is True
    ss = {}
    rep = via.sync.sync(ss, [{"project_id":"P","task_id":"T1","name":"x","resource":"A",
                              "start":"2026-07-01","finish":"2026-07-10","pct":50,"predecessors":[]}])
    assert len(rep["added"]) == 1
    assert via.sync.bom_anchor("CP-1","A","Active") == "CP-1-A-Active"


def test_sync_writeback_and_ocr():
    from pmis_lite import sync_ssot as sy, msproject_io as mio, ocr_intake as oc
    tasks = [
        {"project_id":"P","task_id":"T1","name":"設計","resource":"A","start":"2026-07-01","finish":"2026-07-10","pct":100,"predecessors":[]},
        {"project_id":"P","task_id":"T2","name":"打樣","resource":"B","start":"2026-07-11","finish":"2026-07-20","pct":50,"predecessors":["T1"]},
        {"project_id":"P","task_id":"T3","name":"組裝","resource":"A","start":"2026-07-05","finish":"2026-07-15","pct":0,"predecessors":["T2"]},
    ]
    # 雙向回寫:核可閘門(T3 衝突被 held)
    ss = {}; sy.sync_tasks(ss, tasks)
    wb = sy.writeback_set(ss, tasks, approved_only=True)
    held_ids = [h["task"] for h in wb["held"]]
    assert "T3" in held_ids and len(wb["writeback"]) == 2
    # MS Project XML 生成 + 可反解析
    xml = mio.to_xml(wb["writeback"], "P")
    assert "<Task>" in xml and "PredecessorLink" in xml
    back = mio.from_xml(xml)
    assert len(back) == 2 and back[0]["name"] == "設計"
    # round-trip 無資料流失
    rt = mio.roundtrip(tasks)
    assert rt["match"] is True and len(rt["diffs"]) == 0
    # OCR:VRN 檔名分解錨點(no-OCR 也有錨)
    d = oc.decompose_filename("元大_2330_台積電_20260701.pdf")
    assert d["ticker"] == "2330" and d["broker"] == "元大" and d["date"] == "2026-07-01"
    assert d["ticker_conf"] >= 0.9
    o = oc.ocr_image("富邦_3017_奇鋐_20260630.png")
    assert o["needs_ocr"] is True and o["fallback_anchor"]["ticker"] == "3017"
    assert o["usable"] is True

def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {fn.__name__}: {e}")
        except Exception as e:
            print(f"  ERROR {fn.__name__}: {e.__class__.__name__}: {e}")
    print(f"\n{passed}/{len(fns)} passed")
    return passed == len(fns)


if __name__ == "__main__":
    ok = _run_all()
    sys.exit(0 if ok else 1)


def test_sync_ssot_and_sap_bom():
    from pmis_lite import sync_ssot as sy, sap_bom_ref as sb
    ssot = {}
    tasks = [
        {"project_id":"P","task_id":"T1","name":"設計","resource":"A","start":"2026-07-01","finish":"2026-07-10","pct":100,"predecessors":[],"part":"CP-1"},
        {"project_id":"P","task_id":"T2","name":"打樣","resource":"B","start":"2026-07-05","finish":"2026-07-15","pct":0,"predecessors":["T1"]},
    ]
    r = sy.sync_tasks(ssot, tasks)
    assert len(r["added"]) == 2 and len(r["unchanged"]) == 0
    # T2 開始 2026-07-05 早於前置 T1 完成 2026-07-10 → 排程衝突
    assert any(c["type"] == "schedule" for c in r["conflicts"])
    assert r["usable"] is False
    # append-only：改進度 → 版本化、保留歷史，不覆寫
    tasks[0]["pct"] = 50
    r2 = sy.sync_tasks(ssot, tasks)
    assert "P-T1" in r2["versioned"] and ssot["P-T1"]["version"] == 2
    assert len(ssot.get("_history", [])) == 1
    # 錨點
    assert sy.bom_anchor("CP-1", "A", "Active") == "CP-1-A-Active"
    # 任務↔BOM 橋接
    lk = sy.link_task_bom(tasks, [{"part":"CP-1","rev":"A","state":"Active"}])
    assert len(lk["links"]) == 1 and lk["links"][0]["part"] == "CP-1"
    # SAP BOM 知識
    assert "Where-Used" in sb.tcode("CS15")
    assert sb.select_bom_method(has_pv=True, lot_size_ranges=False) == "V"
    assert sb.explode_blocked_reason(True, True, True, True)["exploded"] is False
    assert len(sb.as_registry()) >= 15
