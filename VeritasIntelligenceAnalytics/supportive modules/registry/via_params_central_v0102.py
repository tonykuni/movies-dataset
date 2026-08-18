#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_params_central_v0102 — 中央參數樞紐(TOOL-069)
====================================================================
操作員令(批41,2026-08-18):「參數統儘量中央化管理」。
v0100→v0101(批43):+第 17 冊 VRN_METHOD(VRN 方法冊 def01-20:
五區抽取/雙層保存/官方對照/算術勾稽/證據仲裁;TOOL-071 方法核之
SSOT 正本)。
v0101→v0102(批44):+三冊財務字庫(TOOL-072 收割自倉內正本):
VRN_BROKER(券商縮寫 29 家)/VRN_FINDATA_SYN(153 canonical 中英
同義,多源並列)/VRN_FINSTMT_SYN(7 表 141 科目歸屬)——20 冊。
原則:
  ① 單一真相不搬家 — 各參數 SSOT 冊留在原位為正本;本樞紐只建
     「指標索引冊」(路徑+sha256+葉數+頂鍵),零複製零改寫。
  ② 衝突可見 — 同一參數鍵(dotted 葉路徑)在多冊出現且值不同
     =列 CONFLICT(建議燈,不自動改;裁決權在操作員)。
  ③ LOCKED 對齊 — regex 治理中心 LOCKED 條目跨冊比對,DRIFT 即紅。
  ④ 誠實三態 — 冊缺=MISSING(工作站 .local 冊在容器缺屬誠實)。
  ⑤ 供程式讀 — central_get(key) 供各引擎統一查參數(先冊後鍵)。
用法:
  via-params                → 全掃描+索引冊+理印 U/I
  via-params --get KEY      → 跨冊查參數(dotted 路徑或關鍵字)
  via-params --check        → 只驗衝突/LOCKED 對齊(rc1=有紅)
  via-params --selftest     → 七檢(沙盒零網路)
  via-params --no-open      → 不開 U/I(容器/批次)
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = VIA / "VIA_Reports"
INDEX_PATH = HERE / "VIA_Central_Params_SSOT_v0100.json"
UI_PATH = REPORTS / "VIA_UI_CentralParams.html"

MOTTO = "VERITAS INTELLIGENCE ANALYTICS · OBSERVA · INTELLEGE · PRAEVIDE"

# ── 參數 SSOT 冊登記表(指標不搬家;conflict_scope=入衝突比對圈)──
# domain:LOCKED=治理鎖 / CONFIG=運行參數 / KNOWLEDGE=知識庫 / REGISTRY=登記冊
BOOKS = [
    {"id": "SYNONYM_REGEX", "domain": "LOCKED", "conflict_scope": True,
     "path": "supportive modules/registry/VIA_Central_Synonym_Regex_v0100.json",
     "note": "Regex 治理中心(7 LOCKED+7 同義集)"},
    {"id": "BRAND_SSOT", "domain": "LOCKED", "conflict_scope": True,
     "path": "supportive modules/registry/VIA_Brand_SSOT_v0100.json",
     "note": "品牌銘言 Observa·Intellege·Praevide"},
    {"id": "VDF_UNIFIED", "domain": "CONFIG", "conflict_scope": True,
     "path": "functional modules/VDF/VDF_Unified_Params_v0100.json",
     "note": "VDF 統一輸入參數+六格式輸出樞紐"},
    {"id": "FLOW_PARAMS", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/VIA_FlowSystem/FlowSystem_v2/config/params.json",
     "note": "FlowSystem 主參數"},
    {"id": "FLOW_TW_ETF", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/VIA_FlowSystem/FlowSystem_v2/config/TW_Active_ETF_Registry_v0100.json",
     "note": "台灣主動式 ETF 清單 SSOT"},
    {"id": "FLOW_GLOBAL_ETF", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/VIA_FlowSystem/FlowSystem_v2/config/Global_ETF_Universe_v0100.json",
     "note": "全球 ETF 五類宇宙"},
    {"id": "FLOW_UNIVERSE", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/VIA_FlowSystem/FlowSystem_v2/config/universe.json",
     "note": "FlowSystem 標的宇宙"},
    {"id": "FLOW_MACRO", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/VIA_FlowSystem/FlowSystem_v2/config/macro.json",
     "note": "宏觀疊圖參數"},
    {"id": "FLOW_SIM", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/VIA_FlowSystem/FlowSystem_v2/config/sim.json",
     "note": "模擬參數"},
    {"id": "FLOW_PERF", "domain": "CONFIG", "conflict_scope": True,
     "path": "supportive modules/VIA_FlowSystem/FlowSystem_v2/config/perf.json",
     "note": "績效參數"},
    {"id": "VRN_LEXICON", "domain": "KNOWLEDGE", "conflict_scope": False,
     "path": "functional modules/VRN/knowledge/VRN_Lexicon_v0100.json",
     "note": "中英文字庫+K1-K8 知識樹(162 條級)"},
    {"id": "VRN_DIGEST", "domain": "CONFIG", "conflict_scope": True,
     "path": "functional modules/VRN/knowledge/VRN_Digest_Params_v0100.json",
     "note": "個股報告摘要批跑參數(TOOL-070)"},
    {"id": "VRN_METHOD", "domain": "LOCKED", "conflict_scope": True,
     "path": "functional modules/VRN/knowledge/VRN_Method_SSOT_v0100.json",
     "note": "VRN 方法冊 def01-20(五區抽取/雙層保存/官方對照/算術勾稽/證據仲裁;TOOL-071)"},
    {"id": "VRN_BROKER", "domain": "KNOWLEDGE", "conflict_scope": False,
     "path": "functional modules/VRN/knowledge/VRN_Broker_Dict_v0100.json",
     "note": "券商縮寫字典 29 家(TOOL-072 收割自 Summarizer)"},
    {"id": "VRN_FINDATA_SYN", "domain": "KNOWLEDGE", "conflict_scope": False,
     "path": "functional modules/VRN/knowledge/VRN_FinData_Synonym_v0100.json",
     "note": "財務數據中英文同義字庫 153 canonical(pattern庫+MOPS+MDL008+方法冊四源)"},
    {"id": "VRN_FINSTMT_SYN", "domain": "KNOWLEDGE", "conflict_scope": False,
     "path": "functional modules/VRN/knowledge/VRN_FinStatement_Synonym_v0100.json",
     "note": "財務報表同義字庫 7 表 141 科目歸屬(TOOL-072)"},
    {"id": "FINAL_PARAMS", "domain": "REGISTRY", "conflict_scope": False,
     "path": "supportive modules/registry/VIA_FinalParameters_CanonicalRegistry.json",
     "note": "歷史最終參數正典冊"},
    {"id": "AUTOCODE_REG", "domain": "REGISTRY", "conflict_scope": False,
     "path": "supportive modules/registry/VIA_AutoCode_Registry_v0100.json",
     "note": "自動編號命名冊(append-only;編號永不變)"},
    {"id": "IFACE_REG", "domain": "REGISTRY", "conflict_scope": False,
     "path": "supportive modules/registry/VIA_Interface_Contract_Registry_v0100.json",
     "note": "介面契約冊(2,000+ 模組)"},
    {"id": "MASTER_GOV_LOCAL", "domain": "REGISTRY", "conflict_scope": False,
     "path": "supportive modules/registry/VIA_MasterGovernance_SSOT_v0100.local.json",
     "note": "主治理冊(工作站 .local;容器缺=誠實 MISSING)"},
]

LEAF_CAP = 20000  # 大冊葉數上限(超出誠實截記,防 REGISTRY 巨冊拖垮)


def _sweep(msg: str, i: int, n: int) -> None:
    """常備令Ⅱ:動態進度條(單行覆寫,不卡斷)"""
    w = 24
    k = int(w * i / max(n, 1))
    bar = "█" * k + "░" * (w - k)
    sys.stdout.write(f"\r  [{bar}] {i}/{n} {msg[:40]:<40}")
    sys.stdout.flush()
    if i >= n:
        sys.stdout.write("\n")


def flatten(obj, prefix="", out=None, cap=LEAF_CAP):
    """JSON → dotted 葉路徑表;list 以 [i] 記;超 cap 誠實截斷"""
    if out is None:
        out = {}
    if len(out) >= cap:
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            flatten(v, f"{prefix}.{k}" if prefix else str(k), out, cap)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if len(out) >= cap:
                break
            flatten(v, f"{prefix}[{i}]", out, cap)
    else:
        if len(out) < cap:
            out[prefix] = obj
    return out


def scan_book(book: dict, root: Path) -> dict:
    p = root / book["path"]
    rec = {"id": book["id"], "domain": book["domain"], "path": book["path"],
           "note": book["note"], "conflict_scope": book["conflict_scope"]}
    if not p.exists():
        rec.update({"state": "MISSING", "sha256": "", "bytes": 0,
                    "leaf_count": 0, "top_keys": [], "truncated": False})
        return rec
    raw = p.read_bytes()
    rec["sha256"] = hashlib.sha256(raw).hexdigest()
    rec["bytes"] = len(raw)
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except Exception as exc:
        rec.update({"state": "FAIL", "error": str(exc)[:120],
                    "leaf_count": 0, "top_keys": [], "truncated": False})
        return rec
    leaves = flatten(data)
    rec["state"] = "OK"
    rec["leaf_count"] = len(leaves)
    rec["truncated"] = len(leaves) >= LEAF_CAP
    rec["top_keys"] = list(data.keys())[:12] if isinstance(data, dict) else [f"<{type(data).__name__}>"]
    rec["_leaves"] = leaves  # 記憶體內供衝突比對;不落索引冊
    return rec


META_KEYS = {"schema", "note", "_note", "policy", "updated", "updated_at", "generated"}


def find_conflicts(records: list[dict]) -> list[dict]:
    """衝突圈內:同 dotted 葉路徑跨冊出現且值不同=CONFLICT。
    排除:①元資料鍵(各冊本應自述,不是共用參數);②list 索引鍵
    (etfs[0].ticker 類位置鍵跨冊比對無語意,實為不同集合)。"""
    seen: dict[str, list[tuple[str, object]]] = {}
    for r in records:
        if r.get("state") != "OK" or not r["conflict_scope"]:
            continue
        for k, v in r.get("_leaves", {}).items():
            if "[" in k or k.rsplit(".", 1)[-1] in META_KEYS:
                continue
            seen.setdefault(k, []).append((r["id"], v))
    out = []
    for k, pairs in seen.items():
        if len(pairs) < 2:
            continue
        vals = {json.dumps(v, ensure_ascii=False, sort_keys=True) for _, v in pairs}
        if len(vals) > 1:
            out.append({"key": k,
                        "books": [{"book": b, "value": str(v)[:80]} for b, v in pairs]})
    return sorted(out, key=lambda c: c["key"])


def locked_alignment(records: list[dict]) -> list[dict]:
    """LOCKED regex 跨冊對齊:治理中心 pattern vs 他冊同名鍵"""
    gov = next((r for r in records if r["id"] == "SYNONYM_REGEX" and r.get("state") == "OK"), None)
    if not gov:
        return [{"name": "SYNONYM_REGEX", "state": "MISSING", "note": "治理中心冊缺,無從對齊"}]
    locked = {}
    for k, v in gov["_leaves"].items():
        m = re.match(r"regex\.([A-Za-z0-9_]+)\.pattern$", k)
        if m:
            locked[m.group(1)] = v
    out = []
    for name, pat in sorted(locked.items()):
        drift = []
        for r in records:
            if r["id"] == "SYNONYM_REGEX" or r.get("state") != "OK":
                continue
            for k, v in r.get("_leaves", {}).items():
                if name in k and isinstance(v, str) and v.strip() and ("\\d" in v or "^" in v):
                    if v != pat:
                        drift.append({"book": r["id"], "key": k, "value": str(v)[:80]})
        out.append({"name": name, "state": "DRIFT" if drift else "ALIGNED",
                    "pattern": pat, "drift": drift})
    return out


def central_get(key: str, root: Path = VIA) -> list[dict]:
    """跨冊查參數:dotted 路徑精確或關鍵字包含;回 [{book,key,value}]"""
    hits = []
    for book in BOOKS:
        p = root / book["path"]
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        for k, v in flatten(data).items():
            if k == key or key.lower() in k.lower():
                hits.append({"book": book["id"], "key": k, "value": v})
                if len(hits) >= 50:
                    return hits
    return hits


def build_index(records: list[dict], conflicts, locked) -> dict:
    slim = []
    for r in records:
        s = {k: v for k, v in r.items() if k != "_leaves"}
        slim.append(s)
    n_ok = sum(1 for r in slim if r["state"] == "OK")
    n_missing = sum(1 for r in slim if r["state"] == "MISSING")
    n_fail = sum(1 for r in slim if r["state"] == "FAIL")
    return {"schema": "VIA.CentralParamsSSOT.v1",
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "policy": "指標索引冊;單一真相留原冊不搬家;衝突=建議燈候操作員裁決",
            "books_total": len(slim), "books_ok": n_ok,
            "books_missing": n_missing, "books_fail": n_fail,
            "leaf_total": sum(r.get("leaf_count", 0) for r in slim),
            "conflicts": conflicts, "locked_alignment": locked,
            "books": slim}


# ── 理印紙墨 U/I ──────────────────────────────────────────────
CSS = """
body{background:#f2f1ec;color:#1b1a17;font-family:'Cormorant Garamond','Noto Serif CJK TC','Microsoft JhengHei',serif;margin:0;padding:24px}
.card{background:#fbfaf7;border:1px solid #dbd9d3;border-radius:6px;padding:18px 22px;margin:14px auto;max-width:1200px}
h1{font-size:20px;margin:0 0 2px}
.motto{color:#9e2b25;letter-spacing:.14em;font-size:11px;margin-bottom:14px}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th{color:#3c6660;text-align:left;border-bottom:1.5px solid #3c6660;padding:4px 8px}
td{border-bottom:1px solid #dbd9d3;padding:4px 8px;vertical-align:top}
.ok{color:#3d7a52;font-weight:bold}.warn{color:#8a6420;font-weight:bold}.bad{color:#9e2b25;font-weight:bold}
.mono{font-family:Consolas,monospace;font-size:11.5px}
.dim{color:#6b6a64}
"""


def render_ui(idx: dict, out: Path) -> None:
    rows = []
    for b in idx["books"]:
        cls = {"OK": "ok", "MISSING": "warn", "FAIL": "bad"}.get(b["state"], "dim")
        rows.append(
            f"<tr><td class='mono'>{b['id']}</td><td>{b['domain']}</td>"
            f"<td class='mono dim'>{b['path']}</td>"
            f"<td class='{cls}'>{b['state']}</td>"
            f"<td>{b.get('leaf_count', 0)}{'(截)' if b.get('truncated') else ''}</td>"
            f"<td class='mono dim'>{b.get('sha256', '')[:8]}</td>"
            f"<td>{'●' if b['conflict_scope'] else '—'}</td>"
            f"<td class='dim'>{b['note']}</td></tr>")
    crows = "".join(
        f"<tr><td class='mono'>{c['key']}</td><td class='mono dim'>"
        + "<br>".join(f"{p['book']}: {p['value']}" for p in c["books"]) + "</td></tr>"
        for c in idx["conflicts"]) or "<tr><td colspan=2 class='ok'>零衝突</td></tr>"
    lrows = "".join(
        f"<tr><td class='mono'>{a['name']}</td>"
        f"<td class='{'ok' if a['state'] == 'ALIGNED' else 'bad'}'>{a['state']}</td>"
        f"<td class='mono dim'>{a.get('pattern', '')}</td></tr>"
        for a in idx["locked_alignment"])
    html = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>VIA 中央參數樞紐</title><style>{CSS}</style></head><body>
<div class="card"><h1>中央參數樞紐 · Central Params SSOT</h1>
<div class="motto">{MOTTO}</div>
<div class="dim">生成 {idx['generated']} · 冊 {idx['books_total']}(OK {idx['books_ok']} / MISSING {idx['books_missing']} / FAIL {idx['books_fail']})· 葉 {idx['leaf_total']:,} · 政策:{idx['policy']}</div></div>
<div class="card"><h1>參數 SSOT 冊索引(指標不搬家)</h1>
<table><tr><th>冊</th><th>域</th><th>路徑</th><th>態</th><th>葉數</th><th>sha8</th><th>衝突圈</th><th>說明</th></tr>{''.join(rows)}</table></div>
<div class="card"><h1>跨冊衝突(建議燈,候操作員裁決)</h1>
<table><tr><th>參數鍵</th><th>各冊值</th></tr>{crows}</table></div>
<div class="card"><h1>LOCKED Regex 對齊</h1>
<table><tr><th>名</th><th>態</th><th>pattern</th></tr>{lrows}</table></div>
</body></html>"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")


def run_scan(check_only=False, no_open=True, root: Path = VIA,
             index_path: Path = INDEX_PATH, ui_path: Path = UI_PATH) -> int:
    records = []
    for i, b in enumerate(BOOKS, 1):
        _sweep(f"掃 {b['id']}", i, len(BOOKS))
        records.append(scan_book(b, root))
    conflicts = find_conflicts(records)
    locked = locked_alignment(records)
    idx = build_index(records, conflicts, locked)
    n_drift = sum(1 for a in locked if a["state"] == "DRIFT")
    if not check_only:
        index_path.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
        render_ui(idx, ui_path)
        print(f"  [冊] 索引 {index_path.name} · U/I {ui_path.name}")
    print(f"  [計] 冊 OK {idx['books_ok']} · MISSING {idx['books_missing']} · FAIL {idx['books_fail']}"
          f" · 葉 {idx['leaf_total']:,} · 衝突 {len(conflicts)} · LOCKED DRIFT {n_drift}")
    for c in conflicts[:10]:
        print(f"  [衝] {c['key']} → " + " | ".join(f"{p['book']}={p['value'][:40]}" for p in c["books"]))
    red = idx["books_fail"] + n_drift
    return 1 if (check_only and red) else 0


# ── 七檢自測(沙盒零網路)───────────────────────────────────
def selftest() -> int:
    import tempfile
    t0 = time.time()
    fails = []

    def chk(name, cond, note=""):
        state = "OK" if cond else "FAIL"
        if not cond:
            fails.append(name)
        print(f"  [{state}] {name} {note}")

    # ① 冊登記表健全:路徑唯一、id 唯一
    paths = [b["path"] for b in BOOKS]
    ids = [b["id"] for b in BOOKS]
    chk("冊登記表唯一性", len(set(paths)) == len(paths) and len(set(ids)) == len(ids),
        f"({len(BOOKS)} 冊)")

    # ② flatten 葉數正確(巢狀+list)
    leaves = flatten({"a": {"b": 1, "c": [2, {"d": 3}]}, "e": "x"})
    chk("flatten 葉路徑", leaves == {"a.b": 1, "a.c[0]": 2, "a.c[1].d": 3, "e": "x"})

    with tempfile.TemporaryDirectory() as td:
        sand = Path(td)
        # 合成兩冊:同鍵不同值=衝突;同鍵同值=無衝突
        (sand / "b1.json").write_text(json.dumps({"th": {"x": 1}, "same": 9}), encoding="utf-8")
        (sand / "b2.json").write_text(json.dumps({"th": {"x": 2}, "same": 9}), encoding="utf-8")
        recs = [scan_book({"id": "B1", "domain": "CONFIG", "conflict_scope": True,
                           "path": "b1.json", "note": ""}, sand),
                scan_book({"id": "B2", "domain": "CONFIG", "conflict_scope": True,
                           "path": "b2.json", "note": ""}, sand)]
        con = find_conflicts(recs)
        # ③ 衝突偵測:th.x 抓到
        chk("衝突偵測(異值)", len(con) == 1 and con[0]["key"] == "th.x")
        # ④ 同值不誤報
        chk("同值零誤報", all(c["key"] != "same" for c in con))
        # ⑤ sha 穩定+MISSING 誠實
        r_miss = scan_book({"id": "BX", "domain": "CONFIG", "conflict_scope": False,
                            "path": "nohere.json", "note": ""}, sand)
        chk("sha 穩定+缺冊誠實", recs[0]["sha256"] == scan_book(
            {"id": "B1", "domain": "CONFIG", "conflict_scope": True,
             "path": "b1.json", "note": ""}, sand)["sha256"]
            and r_miss["state"] == "MISSING")
        # ⑥ 索引冊寫讀 schema
        idx = build_index(recs + [r_miss], con, [])
        ip = sand / "idx.json"
        ip.write_text(json.dumps(idx, ensure_ascii=False), encoding="utf-8")
        back = json.loads(ip.read_text(encoding="utf-8"))
        chk("索引冊 schema 寫讀", back["schema"] == "VIA.CentralParamsSSOT.v1"
            and back["books_ok"] == 2 and back["books_missing"] == 1
            and not any("_leaves" in b for b in back["books"]))
        # ⑦ U/I 產出含銘言刊頭+衝突列
        up = sand / "ui.html"
        render_ui(idx, up)
        h = up.read_text(encoding="utf-8")
        chk("U/I 銘言+衝突呈現", MOTTO in h and "th.x" in h)

    # central_get 實冊煙測(唯讀;冊缺容器亦過——找治理中心 LOCKED)
    hits = central_get("TW_TICKER_LOCKED.pattern")
    print(f"  [註] central_get 實冊煙測:{len(hits)} 命中(唯讀)")
    n = 7 - len(fails)
    print(f"  [計] 七檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 中央參數樞紐 v0102 · 七檢自測(沙盒零網路)===")
        return selftest()
    if "--get" in args:
        i = args.index("--get")
        key = args[i + 1] if i + 1 < len(args) else ""
        if not key:
            print("[用法] via-params --get <dotted鍵或關鍵字>")
            return 2
        hits = central_get(key)
        if not hits:
            print(f"  [查] 「{key}」零命中(誠實)")
            return 0
        for h in hits:
            print(f"  [{h['book']}] {h['key']} = {str(h['value'])[:100]}")
        print(f"  [計] {len(hits)} 命中")
        return 0
    check_only = "--check" in args
    no_open = "--no-open" in args or check_only
    print(f"=== 中央參數樞紐 v0102 · {'驗證' if check_only else '全掃描'} · {len(BOOKS)} 冊(指標不搬家)===")
    rc = run_scan(check_only=check_only, no_open=no_open)
    if not no_open and UI_PATH.exists():
        try:
            import webbrowser
            webbrowser.open(UI_PATH.as_uri())
        except Exception:
            pass
    return rc


if __name__ == "__main__":
    sys.exit(main())
