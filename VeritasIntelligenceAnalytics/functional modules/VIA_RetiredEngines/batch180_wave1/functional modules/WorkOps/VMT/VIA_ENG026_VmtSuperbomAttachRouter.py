# -*- coding: utf-8 -*-
"""
============================================================================
 VMT -> SuperBOM  Attachment Router  v1.0   --  接縫② 郵件附件入庫
----------------------------------------------------------------------------
 定位: 把 VMT 郵件案件裡的 BOM 附件 (東莞規格 / India 圖面 / ECAD 匯出),
       自動送進 SuperBOM ContentParser -> SSOT (M01/M02/M03), 全程留 provenance.
 來源 (自動偵測):
   1. 本機 Outlook 附件 (win32com) -- 讀你自己信箱, 主旨含 [CASE-XX] 者帶回案號
   2. bom_inbox/ 資料夾 -- 半自動: 把附件丟進去
   3. 範例
 流程:
   收附件 -> 只留 BOM-like (.csv/.json 原生; .xlsx 若有 pandas 則轉 csv, 否則列 PENDING)
         -> MD5 去重, add-only 存檔, 檔名嵌入 CASE 作 provenance
         -> 呼叫 ContentParser.def_run_bom (內建 Round-1 gate + Q01 隔離, DB append-only)
         -> 記 provenance ledger + VMT 事件
 與接縫①銜接: 檔名 = <CASE>__<md5>__<原檔名>, ContentParser 以 bom_path.name 當
   Q01.src_system, 故隔離列天生帶著來源 CASE; ①的橋讀 Q01 開追蹤時可回指原信.
----------------------------------------------------------------------------
 治理: 來源只讀; 附件 add-only + MD5 去重 (同檔不重載); ContentParser 自持
       DB append-only / 永不 UPDATE/DELETE / Q01 不阻斷主線. 本路由器不改 parser.
 相容: Python 3.11+; 需 duckdb (parser 用); .xlsx 轉檔需 pandas+openpyxl (選配).
============================================================================
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import os, re, csv, sys, json, hashlib, argparse, importlib.util, datetime as dt
from pathlib import Path

VMT_ROOT    = os.environ.get("VMT_ROOT", r"C:\VIA\VeritasMailTracker")
DATA_DIR    = os.path.join(VMT_ROOT, "data")
ATTACH_ROOT = os.path.join(VMT_ROOT, "attachments")
BOM_INBOX   = os.path.join(VMT_ROOT, "bom_inbox")
OUT_DIR     = os.path.join(VMT_ROOT, "reports")
LEDGER_PATH = os.path.join(DATA_DIR, "attachments.jsonl")
EVENT_PATH  = os.path.join(DATA_DIR, "events.jsonl")
DAYS_BACK   = int(os.environ.get("VMT_DAYS_BACK", "90"))
BOM_EXT     = {".csv", ".json", ".xlsx", ".xls"}

def now_iso(): return dt.datetime.now().isoformat()
def md5_bytes(b): return hashlib.md5(b).hexdigest()
def norm_case(s):
    if not s: return None
    m = re.search(r"CASE[-\s]?0*(\d{1,3})", str(s), re.IGNORECASE) or re.search(r"\[Case\s*0*(\d{1,3})\]", str(s), re.IGNORECASE)
    return ("CASE-%02d" % int(m.group(1))) if m else None

def append_event(evt, ref, detail):
    with open(EVENT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now_iso(), "event": evt, "ref": ref, "detail": detail}, ensure_ascii=False) + "\n")

def load_ledger():
    seen = {}
    if os.path.exists(LEDGER_PATH):
        for line in open(LEDGER_PATH, encoding="utf-8"):
            line = line.strip()
            if not line: continue
            try:
                r = json.loads(line); seen[r["md5"]] = r
            except Exception: pass
    return seen

def append_ledger(rec):
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

# ---------------------------------------------- 載入 ContentParser -----------
def load_parser(parser_path):
    p = Path(parser_path)
    if not p.exists():
        return None
    spec = importlib.util.spec_from_file_location("via_superbom_contentparser", str(p))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "def_run_bom"):
        return None
    return mod

# ---------------------------------------------- 來源 -------------------------
def source_outlook():
    try:
        import win32com.client
    except Exception:
        return None
    try:
        ns = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        inbox = ns.GetDefaultFolder(6); items = inbox.Items
        items.Sort("[ReceivedTime]", True)
        cutoff = dt.datetime.now() - dt.timedelta(days=DAYS_BACK)
        try: items = items.Restrict("[ReceivedTime] >= '%s'" % cutoff.strftime("%m/%d/%Y %H:%M %p"))
        except Exception: pass
        out = []
        for m in items:
            try:
                if getattr(m, "Class", None) != 43: continue
                if m.Attachments.Count == 0: continue
                subj = m.Subject or ""; case = norm_case(subj)
                sender = ""
                try: sender = m.SenderName or ""
                except Exception: pass
                for a in m.Attachments:
                    name = a.FileName or ""
                    if Path(name).suffix.lower() not in BOM_EXT: continue
                    tmp = os.path.join(ATTACH_ROOT, "_tmp_" + name)
                    os.makedirs(ATTACH_ROOT, exist_ok=True)
                    a.SaveAsFile(tmp)
                    data = open(tmp, "rb").read(); os.remove(tmp)
                    out.append({"name": name, "data": data, "subject": subj, "sender": sender, "case": case})
            except Exception:
                continue
        if not out: return None
        print("[來源] 本機 Outlook: %d 個 BOM 附件" % len(out))
        return out
    except Exception as e:
        print("[來源] Outlook 略過:", e); return None

def source_folder():
    if not os.path.isdir(BOM_INBOX): return None
    out = []
    for fn in sorted(os.listdir(BOM_INBOX)):
        p = os.path.join(BOM_INBOX, fn)
        if not os.path.isfile(p) or Path(fn).suffix.lower() not in BOM_EXT: continue
        out.append({"name": fn, "data": open(p, "rb").read(), "subject": fn, "sender": "FOLDER", "case": norm_case(fn)})
    if not out: return None
    print("[來源] bom_inbox/: %d 個檔" % len(out))
    return out

def source_sample():
    print("[來源] 無真實附件 -> 產生範例 BOM")
    os.makedirs(BOM_INBOX, exist_ok=True)
    (Path(BOM_INBOX) / "CASE-03_dongguan_bom.csv").write_text(
        "item_number,description,qty,refdes,value,package\n"
        "R100,RES 10K 0402,2,\"R1,R2\",10K,0402\n"
        "C200,CAP 100nF,3,\"C1,C2,C3\",100nF,0402\n"
        "U300,MCU SoC,1,U1,,QFN-48\n", encoding="utf-8")
    (Path(BOM_INBOX) / "CASE-07_module.json").write_text(json.dumps({
        "items": [{"item_number": "M-1", "description": "Module top"}],
        "edges": [{"parent": "M-1", "item_number": "SCREW", "qty": 4, "refdes": ""}]
    }, ensure_ascii=False), encoding="utf-8")
    (Path(BOM_INBOX) / "expenses_not_a_bom.csv").write_text(
        "date,amount,category\n2026-07-01,1200,travel\n", encoding="utf-8")
    return source_folder()

# ---------------------------------------------- BOM 判定 (用 parser 本體詞庫) --
def is_bom_csv(data, mod):
    try:
        text = data.decode("utf-8-sig", errors="replace")
        first = text.splitlines()[0] if text.splitlines() else ""
        headers = next(csv.reader([first])) if first else []
    except Exception:
        return False
    mapping = mod.def_map_headers([h.lstrip("\ufeff\u200b").strip() for h in headers])
    return "item_number" in mapping  # mapping = {canonical: source_header}; 至少要有料號欄

def to_csv_if_excel(name, data):
    """xlsx/xls -> 暫存 csv (需 pandas+openpyxl); 回傳 (csv_bytes 或 None, note)"""
    try:
        import pandas as pd, io
        df = pd.read_excel(io.BytesIO(data))
        return df.to_csv(index=False).encode("utf-8"), "converted-from-excel"
    except Exception as e:
        return None, "PENDING_CONVERT(需 pandas+openpyxl): %s" % type(e).__name__

# ---------------------------------------------- 主流程 -----------------------
def main():
    ap = argparse.ArgumentParser(description="VMT -> SuperBOM Attachment Router")
    ap.add_argument("--parser", required=True, help="VIA_ENG020_SuperBOMContentParser_v0100.py 路徑")
    ap.add_argument("--db", required=True, help="SuperBOM DuckDB 路徑")
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()

    print("=" * 60)
    print("  VMT -> SuperBOM Attachment Router v1.0  |  接縫②")
    print("=" * 60)
    mod = load_parser(args.parser)
    if mod is None:
        print("[Parser] 無法載入 ContentParser: %s" % args.parser); return
    print("[Parser] 已載入 %s %s" % (getattr(mod, "PARAM_ENGINE", "?"), getattr(mod, "PARAM_VERSION", "")))

    for d in (DATA_DIR, ATTACH_ROOT, OUT_DIR): os.makedirs(d, exist_ok=True)
    seen = load_ledger()
    atts = source_outlook() or source_folder() or source_sample()

    results = []
    out_root = Path(os.path.join(OUT_DIR, "sbom_load"))
    for a in atts:
        name, data = a["name"], a["data"]
        ext = Path(name).suffix.lower()
        case = a.get("case") or "NOCASE"
        md5 = md5_bytes(data)
        rec = {"md5": md5, "orig": name, "case": a.get("case"), "subject": a.get("subject", ""),
               "sender": a.get("sender", ""), "ts": now_iso()}
        if md5 in seen:
            rec["result"] = "DEDUP_SKIP"; results.append(rec); continue

        # xlsx -> csv (選配)
        feed_ext, feed_data, note = ext, data, ""
        if ext in (".xlsx", ".xls"):
            conv, note = to_csv_if_excel(name, data)
            if conv is None:
                rec["result"] = note; append_ledger(rec); results.append(rec)
                append_event("SBOM_ATTACH_PENDING", case, "%s %s" % (name, note)); continue
            feed_ext, feed_data = ".csv", conv

        # 非 BOM 的 csv 直接跳過 (不餵 parser, 不污染 Q01)
        if feed_ext == ".csv" and not is_bom_csv(feed_data, mod):
            rec["result"] = "SKIP_NOT_BOM"; append_ledger(rec); results.append(rec)
            append_event("SBOM_ATTACH_SKIP", case, "%s 非BOM (無料號欄)" % name); continue

        # add-only 存檔, 檔名嵌 CASE provenance (-> 進 Q01.src_system)
        md5s = md5[:10]
        base = re.sub(r"[^0-9A-Za-z_.\-]", "_", Path(name).stem)
        saved_name = "%s__%s__%s%s" % (case, md5s, base, feed_ext)
        saved = os.path.join(ATTACH_ROOT, saved_name)
        if not os.path.exists(saved):
            open(saved, "wb").write(feed_data)

        # 呼叫 ContentParser (Round-1 gate + Q01 + DB append-only)
        try:
            manifest = mod.def_run_bom(Path(saved), Path(args.db), out_root, a.get("case") or "")
            ls = manifest.get("load_stats") or {}
            rec.update({"result": "LOADED" if manifest.get("loaded") else "BLOCKED",
                        "saved": saved_name, "run_id": manifest.get("run_id"),
                        "items": ls.get("items"), "edges": ls.get("edges"),
                        "quarantined": ls.get("quarantined"),
                        "refdes_flags": manifest.get("refdes_qty_flags"),
                        "report": manifest.get("report_html"), "note": note})
            append_event("SBOM_ATTACH_LOAD", case,
                         "%s -> %s items=%s edges=%s q=%s" % (saved_name, rec["result"],
                          rec.get("items"), rec.get("edges"), rec.get("quarantined")))
        except Exception as e:
            rec.update({"result": "PARSER_ERROR", "saved": saved_name, "note": str(e)[:120]})
            append_event("SBOM_ATTACH_ERROR", case, "%s %s" % (saved_name, str(e)[:80]))
        append_ledger(rec); results.append(rec)

    n_load = sum(1 for r in results if r["result"] == "LOADED")
    n_block = sum(1 for r in results if r["result"] == "BLOCKED")
    n_skip = sum(1 for r in results if r["result"] in ("SKIP_NOT_BOM", "DEDUP_SKIP"))
    print("[結果] 載入 %d / 阻擋 %d / 跳過 %d (共 %d 附件)" % (n_load, n_block, n_skip, len(results)))
    for r in results:
        print("       %-14s %s%s" % (r["result"], r["orig"],
              (" items=%s edges=%s" % (r.get("items"), r.get("edges"))) if r.get("items") is not None else ""))

    build_report(results, args.db, os.path.join(OUT_DIR, "AttachmentRouter.html"))
    print("[輸出] 路由報告:", os.path.join(OUT_DIR, "AttachmentRouter.html"))
    print("       銜接①: 被阻擋/隔離的列會經 Quarantine 橋自動變成 VMT 追蹤 (帶來源 CASE)")
    try:
        if os.name == "nt" and not args.no_open:
            os.startfile(os.path.join(OUT_DIR, "AttachmentRouter.html"))  # noqa
    except Exception: pass
    print("完成.")

# ---------------------------------------------- Visual Lock 報告 -------------
def build_report(results, db, out_path):
    def esc(s): return ("" if s is None else str(s)).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    color = {"LOADED": "#5a9e6f", "BLOCKED": "#b5443a", "SKIP_NOT_BOM": "#8a857c",
             "DEDUP_SKIP": "#8a857c", "PARSER_ERROR": "#b5443a"}
    rows = ""
    for r in results:
        c = color.get(r["result"], "#c9a13a")
        cnt = ""
        if r.get("items") is not None:
            cnt = "items %s / edges %s / q %s" % (r.get("items"), r.get("edges"), r.get("quarantined"))
        rows += ("<tr><td><span class='pill' style='background:%s'>%s</span></td><td>%s</td><td>%s</td>"
                 "<td>%s</td><td>%s</td></tr>" % (
            c, esc(r["result"]), esc(r["orig"]), esc(r.get("case") or "—"), cnt, esc(r.get("note", ""))))
    if not rows: rows = "<tr><td colspan='5' class='empty'>無附件</td></tr>"
    n_load = sum(1 for r in results if r["result"] == "LOADED")
    kpis = [("載入 SSOT", n_load, "#5a9e6f"),
            ("Round-1 阻擋", sum(1 for r in results if r["result"] == "BLOCKED"), "#b5443a"),
            ("非BOM/重複跳過", sum(1 for r in results if r["result"] in ("SKIP_NOT_BOM", "DEDUP_SKIP")), "#8a857c"),
            ("待轉檔(xlsx)", sum(1 for r in results if "PENDING" in str(r["result"])), "#c9a13a")]
    kh = "".join("<div class='card'><div class='cv' style='color:%s'>%s</div><div class='cn'>%s</div></div>"
                 % (c, v, n) for n, v, c in kpis)
    now = dt.datetime.now().strftime("%Y/%m/%d %H:%M")
    html = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="UTF-8"><title>Attachment Router</title><style>
:root{--bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--hair:#dbd9d3;--teal:#439a9a;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:"DM Sans","Microsoft JhengHei",sans-serif;padding:28px}
.seal{display:inline-flex;width:44px;height:44px;background:#4c78a8;color:#fff;align-items:center;justify-content:center;font-size:20px;border-radius:3px;margin-right:14px}
header{display:flex;align-items:center;border-bottom:1px solid var(--hair);padding-bottom:16px}
h1{font-size:20px;letter-spacing:1px}.sub{font-family:"DM Mono",monospace;font-size:12px;color:#777;margin-top:2px}
.strip{height:4px;background:linear-gradient(90deg,#b5443a,#d08343,#c9a13a,#7ba86a,#4d8f63);margin:14px 0 22px;border-radius:2px}
h2{font-size:13px;font-family:"DM Mono",monospace;letter-spacing:2px;color:#555;margin:24px 0 10px;text-transform:uppercase}
.cards{display:flex;gap:12px;flex-wrap:wrap}
.card{background:var(--paper);border:1px solid var(--hair);border-radius:3px;padding:14px 20px;min-width:150px}
.cv{font-size:24px;font-weight:700}.cn{font-size:12px;color:#777;margin-top:2px}
table{width:100%;border-collapse:collapse;background:var(--paper);border:1px solid var(--hair);border-radius:3px;overflow:hidden;margin-top:6px}
th{font-family:"DM Mono",monospace;font-size:11px;text-align:left;padding:9px 10px;border-bottom:1px solid var(--hair);color:#666}
td{font-size:13px;padding:8px 10px;border-bottom:1px solid var(--hair)}tr:last-child td{border-bottom:none}
.pill{color:#fff;font-size:11px;font-family:"DM Mono",monospace;padding:2px 8px;border-radius:2px}
.empty{color:#999;text-align:center}
.gov{background:#f0f4f8;border:1px solid #cdd9e5;border-left:5px solid #4c78a8;border-radius:3px;padding:10px 14px;font-size:12px;color:#33506b;margin:8px 0 14px}
footer{margin-top:30px;font-size:11px;color:#999;font-family:"DM Mono",monospace}
</style></head><body>
<header><div class="seal">附</div><div><h1>VMT → SuperBOM 附件路由 — BOM 入庫</h1>
<div class="sub">{{NOW}} | 來源只讀 · MD5 去重 · ContentParser 自持 DB append-only</div></div></header>
<div class="strip"></div>
<div class="gov">治理：來源附件只讀；MD5 去重（同檔不重載）；載入交由你的 ContentParser（Round-1 dry-run gate + Q01 隔離不阻斷）。檔名嵌入 CASE 作 provenance → 隔離列天生帶來源，可經接縫①的橋回指原信。</div>
<h2>KPI</h2><div class="cards">{{KPI}}</div>
<h2>附件處理結果</h2>
<table><tr><th>結果</th><th>原始附件</th><th>來源 CASE</th><th>載入統計</th><th>備註</th></tr>{{ROWS}}</table>
<footer>vmt_superbom_attach_router v1.0 | DB: {{DB}} | LOADED→SSOT / BLOCKED→Q01(DRYRUN) / SKIP→非BOM或重複</footer>
</body></html>"""
    html = (html.replace("{{NOW}}", now).replace("{{KPI}}", kh)
                .replace("{{ROWS}}", rows).replace("{{DB}}", esc(db)))
    open(out_path, "w", encoding="utf-8").write(html)

if __name__ == "__main__":
    main()
