#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN_ENG089_TemplateView v0101 — VRN 模板(制式 U/I 套版)· synchronizer 控制 · 上下游自動連結與新增檢查(批735)

v0100→v0101(批735 收尾;PR #119 的 Codex 審查 P2 + 晚一分鐘沒趕上併入的 66268665):
  ① 比對基準的說法一處定義 basis_text():自動找到的上一輪 =「對上一輪」· 同一個夾重建 =「對這個夾的上一版」·
     都沒有 =「首建」。v0100 的新增段說明不分情況一律寫「對上一輪」(連結段標題本來就分對了),同一個夾手動重建時
     會讓人把重建前後的差當成跨輪的差;頁 · CLI · 交接口 · 自測迴圈橫幅都改用這一支。build() / handover() 多回
     compared_to · previous · basis,呼叫端照抄就對,不必自己猜。
  ② build() 走「不重寫」(SAME)時也回中央頁 / synchronizer 路徑(v0100 少了這兩個鍵:`build --shot` 不截圖、
     呼叫端會當成沒建成)。
  ③ 自測 ⑥ +同一個夾重建 → 說法是「對這個夾的上一版」(頁上新增段說明也驗)且 SAME 回得出兩頁路徑;
     ⑪ +跨輪 → 說法是「對上一輪」(頁上也驗)。仍十二檢。
  版號律補記:v0100 隨 PR #118 併進 main 之後,PR #119 的 86336a94 又原地改了 v0100(當時還不知道 #118 已併)——
  本版起照 L04 出新版,v0100 保持 main 上的位元組,不再動。

操作員 2026-09-24:「用制式模板html u/i套進去形成vrn模板都由synchonizer控制交接自適應式自動化」
               「上下的自動連結更新新增檢查機能建構須完成」「若成功跑一次測試文件的成果用我們使用的html u/i顯示」

制式模板 = VIA_HTML_UI/(L100:正典 U/I 是 file:// 零 server 的 TEMPLATE;manifest.json 逐檔 sha256,CGC_MDL160 驗)。
本支**不改模板一個位元組**:
  ① 建構前三個入口(啟動頁 / 中央 U/I / synchronizer)逐檔對 manifest 的 sha256;對不上就不建(rc1,講哪一支)。
     工作站 git 把換行改成 CRLF 的,換回 LF 再比一次——內容一致照建,點名「換行被改寫」(批650 同一條:換行 ≠ 內容漂移)
  ② 三個入口原樣複製到輸出夾 ui/(檔名不變 → 模板自己頁與頁之間的相對連結照通)
  ③ 中央 U/I 與 synchronizer 只**插入**三段(拿掉插入段 = 模板原檔,自測逐位元組驗):
     · 預置(<head> 之後):synchronizer 共享狀態 via.sync.state.v2 的模組冊**只增不減**加一個 VRN 模組;
       沒存過狀態 → 用模板自己的 DEFAULT_MODULES(建構時從 synchronizer 原始碼抽出來,不另寫一份);
       VRN 模組已在(就算被操作員關掉)→ 一個字都不動,照 synchronizer 的設定
     · 資料(</body> 之前):這一輪的成果(type="application/json",頁上零連線)
     · 外掛(</body> 之前):走模板正式外掛 API——中央頁 VIA_REGISTER_ADDON、synchronizer 頁 VIA_REGISTER_SYNC_ADDON
  ④ **由 synchronizer 控制**:中央頁的 VRN 面板開 / 關跟著 synchronizer 模組冊的 enabled 走
     (localStorage + BroadcastChannel via.sync.v2,即時;在 synchronizer 關掉 → 中央頁面板當場收起)
上下游自動連結 · 自動更新 · 新增檢查:
  上游 = 自測迴圈報告(VRN_AutoTest_Report.json)+ 產出它的引擎(報告 engines 欄,逐支 sha256)+ 模板三入口
  下游 = 衍生頁三張 + synchronizer 模組 + 交接(VCGC 讀本支的連結冊)
  每次建構寫連結冊 VRN_TEMPLATE_LINKS.json,跟同一個輸出夾上一次的比:NEW / CHANGED / GONE / SAME 逐項;
  **新增檢查**:上游新出現的東西(新頂層欄 · 新關卡 · 新檔 · 新欄位規格)逐項點名,而且驗它**真的上了頁**
  (面板照資料逐段畫;不認得的頂層欄一律走「其他欄位」通用段,不吞)——有一項沒上頁 = rc1。
  上游、模板都沒變且頁都在 → 頁不重寫(冪等,SAME)。建構器自己也列上游(本支換版或改碼 → 舊頁 STALE)。
  **跨輪自動連結**:自測迴圈(v0106 起)每輪跑完就把模板建在自己的工作夾 <工作夾>/template(自測、單元測試的工作夾
  都是暫存 → 永遠只寫暫存);比對基準自動找「同一個上層夾裡上一輪的連結冊」(PS 第六步每輪一夾
  VIA_Reports/vrn_autotest/<時間>/ → 每一輪自動接上前一輪),新增 / 異動 / 消失講的是**對上一輪**。
  交接:handover() 報最新一版在哪、對不對得上、這一版新增幾項——VCGC 一頁交接讀這一個口(一處定義)。
用法:
  python VRN_ENG089_TemplateView_v0100.py build --report <VRN_AutoTest_Report.json> [--out <夾>] [--baseline <連結冊>] [--shot <png>]
                                                    # --out 預設 VIA_Reports/vrn/template;--shot 另截 synchronizer 頁
  python VRN_ENG089_TemplateView_v0100.py check [--out <夾>]    # 上游變了沒 / 模板漂了沒 / 下游被改了沒(rc0 一致 · rc1 過期或漂移 · rc2 還沒建過)
  python VRN_ENG089_TemplateView_v0100.py status [--out <夾>]   # 印連結冊;不給 --out = 找得到的最新一版(與交接同一個口)
  python VRN_ENG089_TemplateView_v0100.py --selftest
律:模板零改動(L100)· 頁上零連線(CGC_MDL160 離線四尺)· 只增不減(synchronizer 模組)· 自測只寫暫存(L17)·
    誠實三態 · 尾版律(模板入口與 MDL160 都照尾版取)· 一處定義(離線四尺與「面」的判法借 MDL160,不另寫)。
"""
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

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
ENGINE_TAG = "VRN_ENG089_TemplateView v" + VERSION
TEMPLATE_ROOT = VIA / "VIA_HTML_UI"
MANIFEST = TEMPLATE_ROOT / "manifest.json"
ROLES = ("launcher", "centralUI", "synchronizer")
LATEST_DIR = VIA / "VIA_Reports" / "vrn" / "template"
AUTOTEST_ROOT = VIA / "VIA_Reports" / "vrn_autotest"      # PS 第六步(Invoke-VIA-VRN)每輪一個工作夾 <時間>/
RUN_SUBDIR = "template"                                    # 自測迴圈把這一輪的模板建在 <工作夾>/template
LINKS_NAME = "VRN_TEMPLATE_LINKS.json"
UNREADABLE: dict = {}                                      # runs() 讀不動的根 → 例外名(交接口照實帶出)
STATE_KEY = "via.sync.state.v2"
CHANNEL = "via.sync.v2"
MODULE = {"id": "vrn-report-template", "name": "VRN 研報自測成果", "type": "dashboard", "enabled": True,
          "pinned": True, "system": False, "note": "VRN_ENG089 制式模板外掛(上游:自測迴圈報告)"}
#: 每一輪都不一樣的欄——內容變了不算「異動」(不然每一輪都一片 CHANGED 蓋掉真的異動);新增 / 消失照報
VOLATILE = {"generated", "workdir", "samples", "last_summary", "rounds"}


def _mark(block: str, edge: str) -> str:
    return "<!-- VRN-TEMPLATE:" + block + ":" + edge + " -->"


# ---------------------------------------------------------------- 模板
def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def template_check(root: Path | None = None) -> dict:
    """三個入口對 manifest。回 {ok, rows[{role, path, sha256, want, ok, crlf}], release, why}。零寫檔。"""
    root = Path(root or TEMPLATE_ROOT)
    man = root / "manifest.json"
    if not man.is_file():
        return {"ok": False, "rows": [], "release": None, "why": f"模板 manifest 不在:{man}"}
    try:
        m = json.loads(man.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"ok": False, "rows": [], "release": None, "why": f"模板 manifest 讀不動:{type(exc).__name__}"}
    ent = m.get("canonicalEntrypoints") or {}
    want = {f.get("path"): f.get("sha256") for f in m.get("files") or [] if isinstance(f, dict)}
    rows = []
    for role in ROLES:
        rel = ent.get(role)
        p = root / rel if rel else None
        data = p.read_bytes() if p is not None and p.is_file() else None
        sha = _sha(data) if data is not None else None
        ok, crlf = sha is not None and sha == want.get(rel), False
        if not ok and data is not None and b"\r\n" in data and _sha(data.replace(b"\r\n", b"\n")) == want.get(rel):
            ok, crlf = True, True
        rows.append({"role": role, "path": rel, "sha256": sha, "want": want.get(rel), "ok": ok, "crlf": crlf})
    bad = [r for r in rows if not r["ok"]]
    why = "" if not bad else "模板入口跟 manifest 對不上:" + " · ".join(
        f"{r['role']} {r['path'] or '(manifest 沒列)'} {'不在' if r['sha256'] is None else '內容不同'}" for r in bad)
    return {"ok": not bad and len(rows) == len(ROLES), "rows": rows, "release": m.get("release"), "why": why}


def _js_literal_to_json(src: str):
    """模板裡的 JS 物件字面(單引號字串、不加引號的鍵)→ Python。字串先抽出來佔位,鍵加引號,再放回。"""
    strings = []

    def keep(mm):
        strings.append(json.dumps(mm.group(1).replace("\\'", "'"), ensure_ascii=False))
        return "\x00" + str(len(strings) - 1) + "\x00"

    body = re.sub(r"'((?:[^'\\]|\\.)*)'", keep, src)
    body = re.sub(r"([{,]\s*)([A-Za-z_]\w*)\s*:", r'\1"\2":', body)
    body = re.sub(r"\x00(\d+)\x00", lambda mm: strings[int(mm.group(1))], body)
    return json.loads(body)


def default_modules(sync_html: str) -> list:
    """synchronizer 原始碼裡的 DEFAULT_MODULES(沒存過狀態時它用的那一份)——從模板抽,不另寫一份。"""
    m = re.search(r"const DEFAULT_MODULES=\[(.*?)\];", sync_html, re.S)
    if not m:
        raise ValueError("synchronizer 原始碼裡找不到 DEFAULT_MODULES(模板改版了?)")
    mods = _js_literal_to_json("[" + m.group(1) + "]")
    if not mods or not all(isinstance(x, dict) and {"id", "name", "type"} <= set(x) for x in mods):
        raise ValueError("DEFAULT_MODULES 抽出來不是模組清單")
    return mods


def _mdl160():
    """CGC_MDL160 尾版(離線四尺 OFFLINE_RX 與 surface_of 一處定義,本支不另寫)。載不到 = None。"""
    hits = sorted((VIA / "supportive modules" / "registry").glob("CGC_MDL160_UIUnifyGate_v*.py"))
    if not hits:
        return None
    try:
        spec = importlib.util.spec_from_file_location("_vrn089_mdl160", hits[-1])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:  # noqa: BLE001 -- 誠實:載不到就回 None,呼叫端照報
        return None


# ---------------------------------------------------------------- 上游 → 資料
def _slug(s: str) -> str:
    return re.sub(r"[^0-9A-Za-z一-鿿]+", "-", str(s)).strip("-").lower()[:60] or "x"


def _tone(v) -> str:
    s = str(v or "").upper()
    return "ok" if s in ("GREEN", "PASS", "OK") else "bad" if s in ("RED", "FAIL") else "warn" if s in ("YELLOW", "AMBER", "WARN") else ""


def _cell(v):
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    return json.dumps(v, ensure_ascii=False, sort_keys=True, default=str)


#: 逐檔欄的中文名(認得的才換;不認得的鍵照原名上表,不吞)
FILE_COL_ZH = {"state": "狀態", "upside_adj": "上漲空間(最新 ADJ)", "upside_page": "上漲空間(頁面價)", "basis": "因子分母",
               "has_target": "有目標價", "why": "因由", "rows": "列", "checked": "可驗", "passed": "成立", "n_failed": "不成立",
               "periods_unclear": "季別缺年", "estimate_rows": "預估欄", "failed": "不成立明細"}


def _file_table(files: dict, prefer: tuple = ()) -> tuple:
    """逐檔表的欄自適應:每一檔記錄的鍵取聯集(認得的排前面)——上游每檔多一個欄,表就多一欄。
    回 (columns, rows, status_col);有 state 欄就拿它當狀態欄。"""
    recs = {name: (rec if isinstance(rec, dict) else {"值": rec}) for name, rec in (files or {}).items()}
    seen = []
    for rec in recs.values():
        seen += [k for k in rec if k not in seen]
    cols = [k for k in prefer if k in seen] + [k for k in seen if k not in prefer]
    rows = [[name] + [_cell(rec.get(c)) for c in cols] for name, rec in recs.items()]
    return ["檔"] + [FILE_COL_ZH.get(c, c) for c in cols], rows, (cols.index("state") + 1 if "state" in cols else None)


def build_payload(report: dict, report_path: Path, links: dict | None = None) -> dict:
    """自適應:認得的欄畫專屬段,不認得的頂層欄一律一欄一段(通用樹)——上游多了什麼,頁上就多什麼。
    回 {sections, homes, …};homes = 每個上游項目落在哪一段(新增檢查用)。"""
    report = report if isinstance(report, dict) else {}
    secs, homes = [], {}

    def add(sec, keys=()):
        secs.append(sec)
        for k in keys:
            homes["欄|" + k] = sec["id"]

    counts = report.get("counts") or {}
    add({"id": "summary", "title": "總覽", "kind": "kpi", "items": [
        {"label": "總判定", "value": report.get("verdict", "—"), "tone": _tone(report.get("verdict"))},
        {"label": "PASS", "value": counts.get("PASS", 0), "tone": "ok"},
        {"label": "WARN", "value": counts.get("WARN", 0), "tone": "warn" if counts.get("WARN") else ""},
        {"label": "SKIP", "value": counts.get("SKIP", 0)},
        {"label": "FAIL", "value": counts.get("FAIL", 0), "tone": "bad" if counts.get("FAIL") else "ok"},
        {"label": "檔案", "value": report.get("file_count", 0), "foot": "實檔" if report.get("real_mode") else "合成語料"},
        {"label": "輪數", "value": f"{report.get('rounds_run', '—')}/{report.get('rounds_max', '—')}"}]},
        ("verdict", "counts", "file_count", "real_mode", "rounds_run", "rounds_max"))
    add({"id": "run", "title": "這一輪", "kind": "kv", "rows": [
        ["迴圈", report.get("loop")], ["產生時間", report.get("generated")], ["樣本夾", report.get("samples")],
        ["工作夾", report.get("workdir")], ["報告檔", str(report_path)], ["建構", ENGINE_TAG]]},
        ("loop", "generated", "samples", "workdir"))
    rounds = report.get("rounds") or []
    last = rounds[-1] if rounds and isinstance(rounds[-1], dict) else {}
    grows = [r for r in (last.get("rows") or []) if isinstance(r, dict)]
    by_gate: dict = {}
    for r in grows:
        g = by_gate.setdefault(str(r.get("gate")), {"PASS": 0, "WARN": 0, "SKIP": 0, "FAIL": 0})
        g[str(r.get("status"))] = g.get(str(r.get("status")), 0) + 1
    add({"id": "gate-sum", "title": f"關卡總表(第 {last.get('round', len(rounds))} 輪 · {len(by_gate)} 關)", "kind": "table",
         "columns": ["關卡", "PASS", "WARN", "SKIP", "FAIL", "判定"],
         "rows": [[g, c.get("PASS", 0), c.get("WARN", 0), c.get("SKIP", 0), c.get("FAIL", 0),
                   "FAIL" if c.get("FAIL") else "WARN" if c.get("WARN") else "PASS"] for g, c in by_gate.items()],
         "status_col": 5})
    add({"id": "gates", "title": f"關卡明細({len(grows)} 列)", "kind": "table", "columns": ["關卡", "項目", "狀態", "說明"],
         "rows": [[r.get("gate"), r.get("name"), r.get("status"), r.get("detail")] for r in grows], "status_col": 2},
        ("rounds",))
    for r in grows:
        homes["關卡|" + str(r.get("gate")) + "|" + str(r.get("name"))] = "gates"
    fs = [x for x in (report.get("fieldspec") or []) if isinstance(x, dict)]
    add({"id": "fieldspec", "title": f"欄位規格({len(fs)} 欄)", "kind": "table", "columns": ["欄", "中文", "狀態", "有 / 共"],
         "rows": [[x.get("key"), x.get("zh"), x.get("state"), f"{x.get('have')}/{x.get('total')}"] for x in fs],
         "status_col": 2}, ("fieldspec",))
    for x in fs:
        homes["欄位規格|" + str(x.get("key"))] = "fieldspec"
    fin = report.get("financial") if isinstance(report.get("financial"), dict) else {}
    if fin:
        add({"id": "financial", "title": "財報表格", "kind": "kv",
             "rows": [[k, _cell(v)] for k, v in fin.items() if k != "files"]}, ("financial",))
        fcols, frows, fst = _file_table(fin.get("files"), ("rows", "checked", "passed", "n_failed", "periods_unclear", "estimate_rows"))
        add({"id": "financial-files", "title": f"財報表格 · 逐檔({len(frows)} 檔)", "kind": "table", "columns": fcols,
             "rows": frows, "status_col": fst})
        for name in (fin.get("files") or {}):
            homes["檔|" + name] = "financial-files"
    adj = report.get("adj") if isinstance(report.get("adj"), dict) else {}
    if adj:
        add({"id": "adj", "title": "上漲空間(最新 ADJ CLOSE)", "kind": "kv",
             "rows": [[k, _cell(v)] for k, v in adj.items() if k not in ("files", "why")]}, ("adj",))
        if adj.get("why"):
            add({"id": "adj-why", "title": "ADJ 算不出的因由", "kind": "table", "columns": ["因由", "檔數"],
                 "rows": [[w.get("reason"), w.get("count")] for w in adj["why"] if isinstance(w, dict)]})
        if isinstance(adj.get("files"), dict) and adj["files"]:
            acols, arows, ast = _file_table(adj["files"], ("state", "upside_adj", "upside_page", "basis", "has_target", "why"))
            add({"id": "adj-files", "title": f"上漲空間 · 逐檔({len(arows)} 檔)", "kind": "table", "columns": acols,
                 "rows": arows, "status_col": ast})
            for name in adj["files"]:
                homes.setdefault("檔|" + name, "adj-files")
    for key, title in (("appendix", "附錄小字"), ("dependencies", "相依套件"), ("engines", "引擎"),
                       ("engine_errors", "引擎錯誤"), ("vcgc", "VCGC 尺"), ("truth_summary", "真值對照"),
                       ("last_summary", "最後一輪入庫摘要")):
        val = report.get(key)
        if isinstance(val, dict):
            add({"id": _slug(key), "title": title, "kind": "kv", "rows": [[k, _cell(v)] for k, v in val.items()]}, (key,))
    for key, title in (("fixes_applied", "自動修正"), ("appendix_new_rating_words", "附錄新評等詞(候選)")):
        val = report.get(key)
        if isinstance(val, list):
            add({"id": _slug(key), "title": f"{title}({len(val)})", "kind": "table", "columns": ["#", "內容"],
                 "rows": [[i + 1, _cell(v)] for i, v in enumerate(val)]}, (key,))
    for key, val in report.items():                       # 自適應:沒人認得的頂層欄,一欄一段,不吞
        if "欄|" + key not in homes:
            add({"id": "extra-" + _slug(key), "title": f"其他欄位:{key}(自動收)", "kind": "tree", "data": val}, (key,))
    links = links or {}
    if links.get("rows"):
        c, cmp_, prev_at = links.get("counts") or {}, links.get("compared_to"), links.get("previous")
        basis = basis_text(cmp_, prev_at)
        add({"id": "links", "title": f"上下游連結(自動更新 · {basis} · 新增 {c.get('NEW', 0)} · 異動 {c.get('CHANGED', 0)} · "
                                     f"消失 {c.get('GONE', 0)} · 未變 {c.get('SAME', 0)})",
             "kind": "table", "columns": ["方向", "項目", "參照", "狀態"], "rows": links["rows"], "status_col": 3})
        news = [r for r in links.get("new_items") or []]
        lost = sum(1 for n in news if not n.get("on_page"))
        note = ("首建:沒有上一輪可比,每一項都算新增(下一輪起只列真的新出現的)" if not cmp_ else
                f"{basis_text(cmp_)}沒有新增項目" if not news else
                f"{basis_text(cmp_)}新出現 {len(news)} 項" + (f",其中 {lost} 項沒上頁(建構判 rc1)" if lost else ",逐項驗過都上了頁"))
        add({"id": "new", "title": f"新增檢查({len(news)} 項)", "kind": "table", "columns": ["類別", "項目", "上了哪一段", "在頁上"],
             "rows": [[n["kind"], n["what"], n.get("home") or "—", "OK" if n.get("on_page") else "FAIL"] for n in news],
             "status_col": 3, "note": note})
    return {"engine": ENGINE_TAG, "module": MODULE, "stateKey": STATE_KEY, "channel": CHANNEL,
            "summary": {"verdict": report.get("verdict"), "counts": counts, "file_count": report.get("file_count"),
                        "generated": report.get("generated"), "loop": report.get("loop")},
            "links": {"counts": links.get("counts", {}), "previous": links.get("previous")},
            "sections": secs, "homes": homes}


# ---------------------------------------------------------------- 上下游連結冊
def _report_sig(report: dict) -> str:
    """報告的「內容」簽章:每一輪都不一樣的欄(VOLATILE)不算——兩輪結果一樣就是 SAME,不會每輪都報一條「報告異動」;
    檔案本身重寫過(頁上印著產生時間)另用 report_sha 抓:check 判 STALE、build 不走 SAME 捷徑。"""
    body = {k: v for k, v in report.items() if k not in VOLATILE}
    return _sha(json.dumps(body, ensure_ascii=False, sort_keys=True, default=str).encode())


def link_items(report: dict, report_path: Path, tpl: dict) -> dict:
    """上游項目與內容項目的簽章。{key: {dir, kind, what, ref, sig}}。"""
    items = {}
    items["上游|報告"] = {"dir": "上游", "kind": "報告", "what": "自測迴圈報告(內容;每輪必變的欄不算)", "ref": Path(report_path).name,
                        "sig": _report_sig(report)}
    for role, path in (report.get("engines") or {}).items():
        p = Path(str(path))
        items["上游|引擎|" + role] = {"dir": "上游", "kind": "引擎", "what": role, "ref": p.name,
                                   "sig": _sha(p.read_bytes()) if p.is_file() else "ABSENT"}
    for r in tpl.get("rows") or []:
        items["上游|模板|" + r["role"]] = {"dir": "上游", "kind": "模板", "what": r["role"], "ref": r["path"], "sig": r["sha256"]}
    # 建構器自己也是上游:本支換了(新版號或改碼),舊頁就是舊建構器畫的 → 不能算 SAME
    me = Path(__file__)
    items["上游|建構器"] = {"dir": "上游", "kind": "建構器", "what": ENGINE_TAG, "ref": me.name, "sig": _sha(me.read_bytes())}
    for k, v in report.items():
        sig = "per-run" if k in VOLATILE else _sha(json.dumps(v, ensure_ascii=False, sort_keys=True, default=str).encode())
        items["欄|" + k] = {"dir": "內容", "kind": "欄", "what": k, "ref": "", "sig": sig}
    rounds = report.get("rounds") or []
    last = rounds[-1] if rounds and isinstance(rounds[-1], dict) else {}
    for r in last.get("rows") or []:
        if isinstance(r, dict):
            items["關卡|" + str(r.get("gate")) + "|" + str(r.get("name"))] = {
                "dir": "內容", "kind": "關卡", "what": f"{r.get('gate')} · {r.get('name')}", "ref": "", "sig": str(r.get("status"))}
    for x in report.get("fieldspec") or []:
        if isinstance(x, dict):
            items["欄位規格|" + str(x.get("key"))] = {"dir": "內容", "kind": "欄位規格", "what": str(x.get("key")), "ref": "",
                                                  "sig": f"{x.get('state')}|{x.get('have')}/{x.get('total')}"}
    files = {}
    for src in ("financial", "adj"):
        for name, rec in ((report.get(src) or {}).get("files") or {}).items():
            files.setdefault(name, {})[src] = rec
    for name, rec in files.items():
        items["檔|" + name] = {"dir": "內容", "kind": "檔", "what": name, "ref": "",
                              "sig": _sha(json.dumps(rec, ensure_ascii=False, sort_keys=True, default=str).encode())}
    return items


def diff_items(prev: dict, now: dict) -> dict:
    """{key: NEW / CHANGED / GONE / SAME}。"""
    out = {}
    for k, v in now.items():
        out[k] = "NEW" if k not in prev else "SAME" if prev[k].get("sig") == v.get("sig") else "CHANGED"
    for k in prev:
        if k not in now:
            out[k] = "GONE"
    return out


def basis_text(compared_to, previous=None) -> str:
    """比對基準的說法(一處定義;頁 · CLI · 交接口 · 自測迴圈橫幅都用這一支):
    baseline =「對上一輪」(自動找到的上一輪)· self =「對這個夾的上一版」(同一個夾重建)· 其餘 =「首建」。"""
    at = f"({previous})" if previous else ""
    return (f"對上一輪{at}" if compared_to == "baseline" else f"對這個夾的上一版{at}" if compared_to == "self"
            else "首建:沒有上一輪可比")


def _read_links(out_dir: Path) -> dict:
    p = Path(out_dir)
    p = p if p.suffix == ".json" else p / LINKS_NAME
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
    except (OSError, ValueError):
        return {}


def runs(roots=None) -> list:
    """找得到的每一版連結冊,新到舊 [(built_at, 夾, 冊)]。預設看自測迴圈每輪的 <工作夾>/template(PS 第六步在
    VIA_Reports/vrn_autotest/<時間>/)與手建的 VIA_Reports/vrn/template;給 roots 就只看 roots 底下每個子夾。零寫檔。"""
    dirs = []
    for root in (roots if roots is not None else (AUTOTEST_ROOT,)):
        if not Path(root).is_dir():                       # 還沒跑過第六步 = 這個根不在:沒有就是沒有
            continue
        try:
            dirs += [p / RUN_SUBDIR for p in Path(root).iterdir() if p.is_dir()]
        except OSError as exc:                            # 讀不動(權限 / 網路磁碟斷線)照實記,交接口帶出去,不當成「沒有版」
            UNREADABLE[str(root)] = type(exc).__name__
    if roots is None:
        dirs.append(LATEST_DIR)
    found = []
    for d in dirs:
        rec = _read_links(d)
        if rec.get("built_at"):
            found.append((str(rec["built_at"]), d, rec))
    return sorted(found, key=lambda t: t[0], reverse=True)


def find_baseline(run_dir) -> Path | None:
    """上一輪的連結冊:同一個上層夾裡、別的工作夾的 template/ 中建構時間最新的一本(自動連到前一輪);沒有 = None(首建全算新增)。"""
    run_dir = Path(run_dir).resolve()
    for _at, d, _rec in runs((run_dir.parent,)):
        if d.parent.resolve() != run_dir:
            return d / LINKS_NAME
    return None


# ---------------------------------------------------------------- 注入
PRESEED_JS = r"""(function () {
  'use strict';
  var result = 'NOSTORE';
  try {
    var KEY = __KEY__, MOD = __MODULE__, DEFAULTS = __DEFAULTS__;
    if (typeof localStorage !== 'undefined' && localStorage) {
      var raw = localStorage.getItem(KEY), st = null;
      result = 'ADDED';
      if (raw) { try { st = JSON.parse(raw); } catch (e) { st = undefined; result = 'CORRUPT'; } }
      if (result === 'ADDED' && st && (Number(st.version) < 2 || !st.view)) result = 'LEGACY';
      if (result === 'ADDED') {
        if (!st || typeof st !== 'object') st = { version: 2, updatedAt: new Date().toISOString(), source: 'VRN-TEMPLATE', view: {}, modules: [] };
        if (!Array.isArray(st.modules) || !st.modules.length) st.modules = JSON.parse(JSON.stringify(DEFAULTS));
        for (var i = 0; i < st.modules.length; i++) { if (st.modules[i] && st.modules[i].id === MOD.id) { result = 'PRESENT'; break; } }
        if (result === 'ADDED') {
          var mx = 0;
          for (var j = 0; j < st.modules.length; j++) { var o = Number(st.modules[j] && st.modules[j].order) || 0; if (o > mx) mx = o; }
          var add = JSON.parse(JSON.stringify(MOD)); add.order = mx + 1;
          st.modules.push(add);
          st.updatedAt = new Date().toISOString();
          localStorage.setItem(KEY, JSON.stringify(st));
        }
      }
    }
  } catch (e) { result = 'ERROR'; }
  window.VRN_TEMPLATE_PRESEED = result;
})();"""

CENTRAL_JS = r"""(function () {
  'use strict';
  var MID = __MODULE_ID__, NAME = __MODULE_NAME__, VERSION = __VERSION__, KEY = __KEY__, CHANNEL = __CHANNEL__;
  var P = null;
  try { P = JSON.parse(document.getElementById('vrn-template-payload').textContent); } catch (e) { P = null; }
  var OK = { PASS: 1, OK: 1, GREEN: 1, SAME: 1, ADJ_OK: 1 }, WARN = { WARN: 1, YELLOW: 1, AMBER: 1, SKIP: 1, NODATA: 1, CHANGED: 1, NEW: 1, STALE: 1 },
      BAD = { FAIL: 1, RED: 1, GONE: 1, ERROR: 1, ABSENT: 1 };
  function el(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls; if (text !== undefined && text !== null) n.textContent = String(text); return n; }
  function txt(v) { if (v === null || v === undefined || v === '') return '—'; if (typeof v === 'object') { try { return JSON.stringify(v); } catch (e) { return String(v); } } return String(v); }
  function badge(v) {
    var s = txt(v), k = s.split(/[\s(:·|]/)[0].toUpperCase(), wrap = el('span', 'status'), dot = el('span', 'status-dot');
    if (BAD[k]) dot.style.background = 'var(--danger, #dc2626)'; else if (WARN[k]) dot.className = 'status-dot warn'; else if (!OK[k]) dot.style.background = 'var(--muted, #94a3b8)';
    wrap.appendChild(dot); wrap.appendChild(document.createTextNode(s)); return wrap;
  }
  function kpis(sec) {
    var grid = el('div', 'kpi-grid');
    (sec.items || []).forEach(function (it) {
      var card = el('article', 'kpi-card'), top = el('div', 'kpi-top'), val = el('div', 'kpi-value', txt(it.value));
      top.appendChild(el('span', '', it.label)); card.appendChild(top);
      if (it.tone === 'bad') val.style.color = 'var(--danger, #dc2626)'; else if (it.tone === 'warn') val.style.color = 'var(--warning, #d97706)'; else if (it.tone === 'ok') val.style.color = 'var(--success, #16a34a)';
      card.appendChild(val);
      if (it.foot) { var foot = el('div', 'kpi-foot'); foot.appendChild(el('span', '', it.foot)); card.appendChild(foot); }
      grid.appendChild(card);
    });
    return grid;
  }
  function table(columns, rows, statusCol) {
    var wrap = el('div', 'table-wrap'), t = el('table'), head = el('thead'), tr = el('tr'), body = el('tbody');
    (columns || []).forEach(function (c) { tr.appendChild(el('th', '', c)); }); head.appendChild(tr); t.appendChild(head);
    (rows || []).forEach(function (row) {
      var r = el('tr');
      (row || []).forEach(function (v, i) { var td = el('td'); if (i === statusCol) td.appendChild(badge(v)); else td.textContent = txt(v); r.appendChild(td); });
      body.appendChild(r);
    });
    t.appendChild(body); wrap.appendChild(t); return wrap;
  }
  function tree(sec) {
    var pre = el('pre', 'vrn-tpl-tree'), s;
    try { s = JSON.stringify(sec.data, null, 2); } catch (e) { s = String(sec.data); }
    if (s && s.length > 20000) s = s.slice(0, 20000) + '\n…(截斷;完整資料在 synchronizer 頁「下載 VRN 資料」)';
    pre.textContent = s === undefined ? 'null' : s; return pre;
  }
  var FOLD = 25;
  function keyOf(v) { return txt(v).split(/[\s(:·|]/)[0].toUpperCase(); }
  function sizeOf(v) { try { return JSON.stringify(v).length; } catch (e) { return 0; } }
  function tally(rows, col) {
    var c = {}, order = [];
    rows.forEach(function (r) { var k = keyOf(r[col]); if (!(k in c)) { c[k] = 0; order.push(k); } c[k] += 1; });
    return order.map(function (k) { return k + ' ' + c[k]; }).join(' · ');
  }
  // 大段收合(列都在頁上,收合只為好讀);WARN / FAIL / 異動 / 消失的列拉到收合外面,不展開也看得到
  function section(sec) {
    var box = el('section', 'panel vrn-tpl-sec'), head = el('div', 'panel-header'), titles = el('div');
    box.id = 'vrn-sec-' + sec.id; box.setAttribute('data-vrn-section', sec.id);
    titles.appendChild(el('h3', 'panel-title', sec.title)); head.appendChild(titles); box.appendChild(head);
    var rows = sec.rows || [], sc = typeof sec.status_col === 'number' ? sec.status_col : -1, isTable = sec.kind === 'table' || sec.kind === 'kv';
    if (sec.note) box.appendChild(el('p', 'panel-caption vrn-tpl-note', sec.note));
    if (isTable && !rows.length) { if (!sec.note) box.appendChild(el('p', 'panel-caption vrn-tpl-note', '(這一段沒有列)')); return box; }
    var body = sec.kind === 'kpi' ? kpis(sec) : sec.kind === 'table' ? table(sec.columns, rows, sc)
      : sec.kind === 'kv' ? table(['項目', '值'], rows, -1) : tree(sec);
    if (!(isTable ? rows.length > FOLD : sec.kind === 'tree' && sizeOf(sec.data) > 1500)) { box.appendChild(body); return box; }
    if (sc >= 0) {
      var hot = rows.filter(function (r) { var k = keyOf(r[sc]); return BAD[k] || (WARN[k] && k !== 'NEW'); });
      if (hot.length && hot.length <= FOLD) {
        box.appendChild(el('p', 'panel-caption', '需要看的列(' + hot.length + '):'));
        box.appendChild(table(sec.columns, hot, sc));
      }
    }
    var det = el('details', 'vrn-tpl-fold');
    det.appendChild(el('summary', 'panel-caption', (isTable ? '展開全部 ' + rows.length + ' 列' : '展開資料') + (sc >= 0 ? ' · ' + tally(rows, sc) : '')));
    det.appendChild(body); box.appendChild(det);
    return box;
  }
  function moduleOf(state) {
    try {
      var st = state || JSON.parse(localStorage.getItem(KEY) || 'null'), mods = st && Array.isArray(st.modules) ? st.modules : [];
      for (var i = 0; i < mods.length; i++) { if (mods[i] && mods[i].id === MID) return mods[i]; }
    } catch (e) { }
    return null;
  }
  function apply(ui, state) {
    var m = moduleOf(state), on = !m || m.enabled !== false;
    ui.body.hidden = !on; ui.off.hidden = on;
    ui.root.setAttribute('data-vrn-enabled', on ? '1' : '0');
    ui.pin.hidden = !(m && m.pinned);
  }
  function mount(host, api) {
    // 模板既有缺陷的衍生頁補丁:中央頁同步段呼叫的 toast() 在它的範圍裡解析到 <div id="toast">(window 具名存取),
    // synchronizer 每改一次狀態中央頁就丟「toast is not a function」。把模板自己的 toast(外掛 API 給的)掛上 window;
    // 模板修好(window.toast 已是函式)這段就不作用。模板本身一個位元組都不動。
    var shim = 'NOT_NEEDED';
    if (typeof window.toast !== 'function' && api && typeof api.toast === 'function') { try { window.toast = api.toast; shim = 'APPLIED'; } catch (e) { shim = 'ERROR'; } }
    window.VRN_TEMPLATE_TOAST_SHIM = shim;
    host.className = 'vrn-tpl'; host.replaceChildren();
    // 面板自己的樣式只作用在 .vrn-tpl-root 底下;[hidden] 一律真的藏(批735 使用者路徑實測抓到:行內 display 會蓋掉 hidden)
    var css = el('style');
    css.textContent = '.vrn-tpl-root{display:grid;gap:14px;width:100%}.vrn-tpl-root [hidden]{display:none!important}'
      + '.vrn-tpl-body{display:grid;gap:14px}.vrn-tpl-root>.panel-header{flex-wrap:wrap;gap:8px 14px}'
      + '.vrn-tpl-off{padding:14px 16px;line-height:1.6}.vrn-tpl-note{margin:4px 0 8px}.vrn-tpl-fold>summary{cursor:pointer;padding:6px 0}'
      + '.vrn-tpl-tree{white-space:pre-wrap;overflow-wrap:anywhere;max-height:520px;overflow:auto;margin:0}';
    host.appendChild(css);
    var root = el('div', 'vrn-tpl-root'), head = el('div', 'panel-header'), titles = el('div'), s = (P && P.summary) || {};
    titles.appendChild(el('h2', 'panel-title', 'VRN 研報自測成果 · 制式 U/I'));
    titles.appendChild(el('p', 'panel-caption', txt(s.loop) + ' · ' + txt(s.generated) + ' · ' + ((P && P.engine) || '')));
    head.appendChild(titles); head.appendChild(badge(s.verdict));
    var pin = el('span', 'status', '已在 synchronizer 釘選'); head.appendChild(pin);
    var ctl = el('p', 'panel-caption');
    ctl.appendChild(document.createTextNode('由 synchronizer 控制:模組 ' + MID + '(開 / 關 / 釘選 / 排序在 '));
    var a = el('a', 'link', 'synchronizer 頁'); a.setAttribute('href', 'VIA-SYNCHRONIZER-Standalone.html'); ctl.appendChild(a);
    ctl.appendChild(document.createTextNode(')'));
    var off = el('div', 'panel vrn-tpl-off', 'VRN 面板已在 synchronizer 停用——到 synchronizer 頁的模組清單把「' + NAME + '」勾回來,這裡會即時回來(請用停用,不要刪:刪掉的話下一次開這一頁會照只增不減再加回來)。');
    var body = el('div', 'vrn-tpl-body');
    if (!P) body.appendChild(el('div', 'panel', '這一頁的 VRN 資料讀不到(建構不完整);重跑 VRN_ENG089 build。'));
    ((P && P.sections) || []).forEach(function (sec) { body.appendChild(section(sec)); });
    root.appendChild(head); root.appendChild(ctl); root.appendChild(off); root.appendChild(body); host.appendChild(root);
    var ui = { root: root, body: body, off: off, pin: pin };
    apply(ui, null);
    try { var ch = new BroadcastChannel(CHANNEL); ch.onmessage = function (ev) { var d = ev && ev.data; if (d && d.type === 'via-state-v2' && d.state) apply(ui, d.state); if (d && d.type === 'via-clear-v2') apply(ui, null); }; } catch (e) { }
    window.addEventListener('storage', function (ev) { if (ev.key === KEY) apply(ui, null); });
    window.VRN_TEMPLATE_UI = ui;
  }
  function register(left) {
    if (typeof window.VIA_REGISTER_ADDON === 'function') {
      var ok = false;
      try { ok = window.VIA_REGISTER_ADDON({ id: MID, name: NAME, version: VERSION, mount: mount }); } catch (e) { ok = false; }
      window.VRN_TEMPLATE_MOUNTED = ok !== false; return;
    }
    if (left > 0) setTimeout(function () { register(left - 1); }, 50); else window.VRN_TEMPLATE_MOUNTED = false;
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { register(200); }); else register(200);
})();"""

SYNC_JS = r"""(function () {
  'use strict';
  var MID = __MODULE_ID__, NAME = __MODULE_NAME__, VERSION = __VERSION__;
  var P = null;
  try { P = JSON.parse(document.getElementById('vrn-template-payload').textContent); } catch (e) { P = null; }
  function mount(host, api) {
    var s = (P && P.summary) || {}, c = s.counts || {}, lc = (P && P.links && P.links.counts) || {};
    var moves = [['新增', lc.NEW], ['異動', lc.CHANGED], ['消失', lc.GONE]].filter(function (m) { return m[1]; })
      .map(function (m) { return ' · ' + m[0] + ' ' + m[1]; }).join('');
    host.replaceChildren(); host.style.cssText = 'display:flex;flex-wrap:wrap;gap:8px;align-items:center';
    var label = document.createElement('span');
    label.textContent = NAME + ' v' + VERSION + ' · ' + (s.verdict || '—') + ' · PASS ' + (c.PASS || 0) + ' · FAIL ' + (c.FAIL || 0) + moves;
    host.appendChild(label);
    var btn = document.createElement('button'); btn.className = 'btn'; btn.type = 'button'; btn.textContent = '下載 VRN 資料';
    btn.addEventListener('click', function () {
      if (api && typeof api.download === 'function') api.download('VRN_template_payload' + '.js' + 'on', JSON.stringify(P, null, 2), 'application/' + 'js' + 'on');
    });
    host.appendChild(btn);
    window.VRN_TEMPLATE_SYNC_MOUNTED = true;
  }
  function register(left) {
    if (typeof window.VIA_REGISTER_SYNC_ADDON === 'function') {
      var ok = false;
      try { ok = window.VIA_REGISTER_SYNC_ADDON({ id: MID, name: NAME, version: VERSION, mount: mount }); } catch (e) { ok = false; }
      window.VRN_TEMPLATE_SYNC_MOUNTED = ok !== false; return;
    }
    if (left > 0) setTimeout(function () { register(left - 1); }, 50); else window.VRN_TEMPLATE_SYNC_MOUNTED = false;
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { register(200); }); else register(200);
})();"""


def _jsval(v) -> str:
    """JSON 進 <script>:</ 與 <!-- 拆開,頁不會被資料提前收尾。"""
    return json.dumps(v, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--")


def _fill(js: str, defaults: list) -> str:
    for k, v in (("__KEY__", STATE_KEY), ("__CHANNEL__", CHANNEL), ("__MODULE__", MODULE), ("__DEFAULTS__", defaults),
                 ("__MODULE_ID__", MODULE["id"]), ("__MODULE_NAME__", MODULE["name"]), ("__VERSION__", VERSION)):
        js = js.replace(k, _jsval(v))
    return js


def inject(html: str, payload: dict, defaults: list, page: str) -> str:
    """模板原文 + 三段插入(<head> 之後:預置;</body> 之前:資料 + 外掛)。其餘一個字元都不動。"""
    head = re.search(r"<head\b[^>]*>", html, re.I)
    body_at = html.lower().rfind("</body>")
    if not head or body_at < 0:
        raise ValueError(f"{page} 找不到 <head> 或 </body>(模板改版了?)")
    pre = (_mark("preseed", "BEGIN") + "\n<script>\n" + _fill(PRESEED_JS, defaults) + "\n</script>\n"
           + _mark("preseed", "END"))
    tail = (_mark("addon", "BEGIN") + "\n<script id=\"vrn-template-payload\" type=\"application/json\">"
            + _jsval(payload) + "</script>\n<script>\n" + _fill(CENTRAL_JS if page == "centralUI" else SYNC_JS, defaults)
            + "\n</script>\n" + _mark("addon", "END"))
    at = head.end()
    out = html[:at] + pre + html[at:body_at] + tail + html[body_at:]
    return out


def strip_injection(html: str) -> str:
    """拿掉本支插入的段(自測用:拿掉之後必須 = 模板原文)。"""
    for block in ("preseed", "addon"):
        b, e = _mark(block, "BEGIN"), _mark(block, "END")
        i, j = html.find(b), html.find(e)
        if i >= 0 and j > i:
            html = html[:i] + html[j + len(e):]
    return html


def injected_text(html: str) -> str:
    parts = []
    for block in ("preseed", "addon"):
        b, e = _mark(block, "BEGIN"), _mark(block, "END")
        i, j = html.find(b), html.find(e)
        if i >= 0 and j > i:
            parts.append(html[i:j + len(e)])
    return "\n".join(parts)


# ---------------------------------------------------------------- 建構
def build(report_path, out_dir=None, template_root=None, _sections_hook=None, baseline=None) -> dict:
    """建一版 VRN 模板。回 {state: BUILT/SAME/BLOCKED, rc, pages, links, new_items, why}。
    比對基準:輸出夾自己的上一版;輸出夾還沒建過就用 baseline(上一輪的連結冊,find_baseline 自動找)——
    新增 / 異動 / 消失是「對上一輪」,不是每一輪都全算新增。"""
    t0 = time.time()
    report_path = Path(report_path)
    out_dir = Path(out_dir or LATEST_DIR)
    troot = Path(template_root or TEMPLATE_ROOT)
    tpl = template_check(troot)
    if not tpl["ok"]:
        return {"state": "BLOCKED", "rc": 1, "why": tpl["why"], "pages": {}, "links": {}, "new_items": []}
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"state": "BLOCKED", "rc": 1, "why": f"上游報告讀不動:{report_path}({type(exc).__name__})",
                "pages": {}, "links": {}, "new_items": []}
    man = json.loads((troot / "manifest.json").read_text(encoding="utf-8"))
    ent = man["canonicalEntrypoints"]
    sync_html = (troot / ent["synchronizer"]).read_bytes().decode("utf-8")
    try:
        defaults = default_modules(sync_html)
    except ValueError as exc:
        return {"state": "BLOCKED", "rc": 1, "why": str(exc), "pages": {}, "links": {}, "new_items": []}
    prev = _read_links(out_dir)
    base_used = None
    if not prev and baseline:
        prev = _read_links(Path(baseline))
        base_used = str(baseline) if prev else None
    prev_items = prev.get("items") or {}
    compared = "baseline" if base_used else "self" if prev else None
    basis = basis_text(compared, prev.get("built_at"))
    items = link_items(report, report_path, tpl)
    states = diff_items(prev_items, items)
    ui_dir = out_dir / "ui"
    names = {role: Path(ent[role]).name for role in ROLES}
    report_sha = _sha(report_path.read_bytes())
    upstream_same = (prev_items and prev.get("report_sha") == report_sha
                     and all(states.get(k) == "SAME" for k in items if k.startswith("上游|")))
    pages_intact = all((ui_dir / names[r]).is_file() and _sha((ui_dir / names[r]).read_bytes()) == (prev.get("pages") or {}).get(names[r])
                       for r in ROLES)
    if upstream_same and pages_intact and all(v == "SAME" for v in states.values()):
        return {"state": "SAME", "rc": 0, "why": "上游、模板都沒變,頁都在 → 不重寫", "pages": prev.get("pages") or {},
                "links": prev.get("counts") or {}, "new_items": [], "out": str(out_dir),
                "central": str(ui_dir / names["centralUI"]), "synchronizer": str(ui_dir / names["synchronizer"]),
                "compared_to": compared, "previous": prev.get("built_at"), "basis": basis}
    counts = {s: sum(1 for v in states.values() if v == s) for s in ("NEW", "CHANGED", "GONE", "SAME")}
    rows = []
    for k, st in sorted(states.items(), key=lambda kv: ({"NEW": 0, "CHANGED": 1, "GONE": 2, "SAME": 3}[kv[1]], kv[0])):
        it = items.get(k) or prev_items.get(k) or {}
        if it.get("dir") in ("上游",) or st != "SAME":
            rows.append([it.get("dir", "—"), f"{it.get('kind', '')} · {it.get('what', k)}", it.get("ref") or "", st])
    rows += [["下游", "頁 · " + names[r], "ui/" + names[r], "REBUILT"] for r in ROLES]
    rows.append(["下游", "synchronizer 模組 · " + MODULE["id"], STATE_KEY, "REGISTERED"])
    new_keys = [k for k, st in states.items() if st == "NEW" and not k.startswith("上游|")]
    payload = build_payload(report, report_path, {"rows": rows, "counts": counts, "previous": prev.get("built_at"),
                                                  "compared_to": compared, "new_items": []})
    if _sections_hook:
        _sections_hook(payload)
    homes, sec_ids = payload["homes"], {s["id"] for s in payload["sections"]}
    row_index = {}
    for s in payload["sections"]:
        for r in s.get("rows") or []:
            if r:
                row_index.setdefault(s["id"], set()).add(str(r[0]))
                if len(r) > 1:
                    row_index[s["id"]].add(f"{r[0]}|{r[1]}")
    new_items = []
    for k in new_keys:
        it = items[k]
        home = homes.get(k)
        on = bool(home and home in sec_ids)
        if on and it["kind"] == "關卡":
            g, n = k.split("|", 2)[1:]
            on = f"{g}|{n}" in row_index.get(home, set())
        elif on and it["kind"] in ("檔", "欄位規格"):
            on = it["what"] in row_index.get(home, set())
        new_items.append({"kind": it["kind"], "what": it["what"], "home": home, "on_page": on})
    payload = build_payload(report, report_path, {"rows": rows, "counts": counts, "previous": prev.get("built_at"),
                                                  "compared_to": compared, "new_items": new_items})
    if _sections_hook:
        _sections_hook(payload)
    rendered = {}                      # 三張先在記憶體組好;組不出來(模板改版找不到插入點)= BLOCKED,一張都不寫(不留半套)
    for role in ROLES:
        src = (troot / ent[role]).read_bytes()
        try:
            rendered[role] = src if role == "launcher" else inject(src.decode("utf-8"), payload, defaults, role).encode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            return {"state": "BLOCKED", "rc": 1, "why": f"{names[role]} 插不進去:{exc}", "pages": {}, "links": {}, "new_items": []}
    ui_dir.mkdir(parents=True, exist_ok=True)
    pages = {}
    for role in ROLES:
        dst = ui_dir / names[role]
        dst.write_bytes(rendered[role])
        pages[names[role]] = _sha(rendered[role])
    missing = [n for n in new_items if not n["on_page"]]
    rec = {"schema": "VIA.VRN.TemplateLinks.v1", "engine": ENGINE_TAG, "built_at": datetime.now().isoformat(timespec="seconds"),
           "report": str(report_path), "report_sha": report_sha, "out": str(out_dir),
           "template": {"release": tpl["release"], "rows": tpl["rows"]},
           "compared_to": compared, "baseline": base_used,
           "previous": prev.get("built_at"), "entry": {role: "ui/" + names[role] for role in ROLES},
           "module": MODULE, "pages": pages, "items": items, "states": states, "counts": counts,
           "new_items": new_items, "new_missing": [n["what"] for n in missing],
           "summary": {"verdict": report.get("verdict"), "counts": report.get("counts"), "file_count": report.get("file_count"),
                       "generated": report.get("generated")},
           "seconds": round(time.time() - t0, 2)}
    (out_dir / LINKS_NAME).write_text(json.dumps(rec, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    return {"state": "BUILT", "rc": 1 if missing else 0, "why": ("新增項目沒上頁:" + " · ".join(rec["new_missing"][:5])) if missing else "",
            "pages": pages, "links": counts, "new_items": new_items, "out": str(out_dir),
            "central": str(ui_dir / names["centralUI"]), "synchronizer": str(ui_dir / names["synchronizer"]),
            "crlf": [r["role"] for r in tpl["rows"] if r.get("crlf")],
            "compared_to": compared, "previous": prev.get("built_at"), "basis": basis}


def check(out_dir=None, template_root=None) -> dict:
    """最新一版還對嗎:上游(報告 / 引擎 / 模板)變了 → STALE;頁被改 / 不見 → DRIFT;都對 → OK。零寫檔。"""
    out_dir = Path(out_dir or LATEST_DIR)
    rec = _read_links(out_dir)
    if not rec:
        return {"state": "NONE", "rc": 2, "why": f"還沒建過(連結冊不在:{out_dir / LINKS_NAME})"}
    tpl = template_check(template_root)
    stale = []
    rp = Path(rec.get("report", ""))
    try:
        report = json.loads(rp.read_text(encoding="utf-8"))
        now = link_items(report, rp, tpl)
    except (OSError, ValueError):
        return {"state": "STALE", "rc": 1, "why": f"上游報告不在或讀不動:{rp}"}
    for k, st in diff_items(rec.get("items") or {}, now).items():
        if k.startswith("上游|") and st != "SAME":
            stale.append(f"{k} {st}")
    if rec.get("report_sha") and _sha(rp.read_bytes()) != rec["report_sha"] and not any(s.startswith("上游|報告") for s in stale):
        stale.append("上游|報告 檔案重寫過(內容一樣,頁上的產生時間已經不對)")
    drift = [n for n, sha in (rec.get("pages") or {}).items()
             if not (out_dir / "ui" / n).is_file() or _sha((out_dir / "ui" / n).read_bytes()) != sha]
    if not tpl["ok"]:
        return {"state": "DRIFT", "rc": 1, "why": tpl["why"]}
    if stale:
        return {"state": "STALE", "rc": 1, "why": "上游變了:" + " · ".join(stale[:6]) + " → 重跑 build"}
    if drift:
        return {"state": "DRIFT", "rc": 1, "why": "下游頁被改或不見:" + " · ".join(drift)}
    return {"state": "OK", "rc": 0, "why": f"上游 · 模板 · 建構器 · 下游三頁都跟 {rec.get('built_at')} 那一版一致"}


def handover(roots=None) -> dict:
    """交接用(VCGC 一頁交接讀這一支,不自己找檔;一處定義):最新一版在哪 · 跟上游還對不對(check)·
    這一版對上一輪新增 / 異動 / 消失幾項 · 新增有沒有都上頁 · 共找到幾版。零寫檔。"""
    rs = runs(roots)
    bad = "".join(f" · 讀不動 {k}({v})" for k, v in UNREADABLE.items())
    if not rs:
        return {"state": "ABSENT", "runs": 0, "unreadable": dict(UNREADABLE),
                "why": "還沒有任何一版 VRN 模板(自測迴圈 v0106 起每輪自動建在 <工作夾>/template;或 build --report …)" + bad}
    at, d, rec = rs[0]
    ck = check(d)
    ent = rec.get("entry") or {}
    return {"state": ck["state"], "why": ck["why"] + bad, "runs": len(rs), "unreadable": dict(UNREADABLE),
            "built_at": at, "out": str(d), "engine": rec.get("engine"),
            "report": rec.get("report"), "compared_to": rec.get("compared_to"), "baseline": rec.get("baseline"),
            "previous": rec.get("previous"), "basis": basis_text(rec.get("compared_to"), rec.get("previous")),
            "counts": rec.get("counts") or {}, "new_items": len(rec.get("new_items") or []), "new_missing": rec.get("new_missing") or [],
            "summary": rec.get("summary") or {}, "module": MODULE["id"],
            "central": str(d / ent["centralUI"]) if ent.get("centralUI") else "",
            "synchronizer": str(d / ent["synchronizer"]) if ent.get("synchronizer") else ""}


# ---------------------------------------------------------------- 自測
def _node() -> str | None:
    return shutil.which("node")


def _run_node(script: str, cwd: Path, env_extra: dict | None = None, timeout: int = 180) -> tuple:
    js = cwd / "_vrn089_probe.js"
    js.write_text(script, encoding="utf-8")
    env = dict(os.environ)
    env.update(env_extra or {})
    try:
        p = subprocess.run([_node(), str(js)], cwd=str(cwd), capture_output=True, text=True, timeout=timeout, env=env)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return -1, type(exc).__name__


PRESEED_PROBE = r"""
const vm = require('vm');
function run(stored) {
  const store = new Map(stored === undefined ? [] : [['via.sync.state.v2', stored]]);
  const localStorage = { getItem: k => store.has(k) ? store.get(k) : null, setItem: (k, v) => store.set(k, String(v)) };
  const window = {};
  vm.runInNewContext(__JS__, { window, localStorage, JSON, Number, Array, Date });
  const out = store.get('via.sync.state.v2');
  return { result: window.VRN_TEMPLATE_PRESEED, state: out === undefined ? null : out };
}
const MID = __MID__;
const a = run(undefined);
const sa = JSON.parse(a.state);
const b0 = JSON.stringify({ version: 2, updatedAt: '2026-01-01T00:00:00Z', view: { theme: 'light' }, modules: [{ id: 'overview', name: 'x', order: 7, enabled: false }], extra: { keep: 1 } });
const b = run(b0); const sb = JSON.parse(b.state);
const c0 = JSON.stringify({ version: 2, view: {}, modules: [{ id: MID, enabled: false, pinned: false, order: 3 }] });
const c = run(c0);
const d = run('{not json'); const e0 = JSON.stringify({ version: 1, modules: [] }); const e = run(e0);
console.log(JSON.stringify({
  a: a.result === 'ADDED' && sa.modules.length === __NDEF__ + 1 && sa.modules[sa.modules.length - 1].id === MID,
  b: b.result === 'ADDED' && sb.modules.length === 2 && sb.modules[0].enabled === false && sb.modules[0].order === 7 && sb.modules[1].order === 8 && sb.extra.keep === 1 && sb.view.theme === 'light',
  c: c.result === 'PRESENT' && c.state === c0,
  d: d.result === 'CORRUPT' && d.state === '{not json',
  e: e.result === 'LEGACY' && e.state === e0 }));
"""

BROWSER_PROBE = r"""
const { chromium } = require('playwright');
(async () => {
  const out = { errors: [], template_errors: [] };
  const browser = await chromium.launch({ headless: true });
  // 對照組:原封模板(沒有插入)——在 synchronizer 切一個預設模組,記中央頁丟的錯(模板既有缺陷就在這裡點名)
  const ctx0 = await browser.newContext();
  const s0 = await ctx0.newPage(); const c0 = await ctx0.newPage(); c0.on('pageerror', e => out.template_errors.push(e.message));
  await s0.goto(__TPL_SYNC_URL__); await c0.goto(__TPL_CENTRAL_URL__);
  await s0.waitForSelector('.module-row .module-toggle', { timeout: 15000 });
  await s0.evaluate(() => document.querySelector('.module-row .module-toggle').click());
  await c0.waitForTimeout(800);
  await ctx0.close();
  const ctx = await browser.newContext({ acceptDownloads: true });
  const sync = await ctx.newPage(); sync.on('pageerror', e => out.errors.push('sync:' + e.message));
  await sync.goto(__SYNC_URL__); await sync.waitForFunction(() => window.VRN_TEMPLATE_SYNC_MOUNTED === true, null, { timeout: 15000 });
  out.sync_mounted = true;
  out.sync_row = await sync.evaluate(mid => Array.from(document.querySelectorAll('.module-row small')).some(n => n.textContent === mid), __MID__);
  const cen = await ctx.newPage(); cen.on('pageerror', e => out.errors.push('central:' + e.message));
  await cen.goto(__CENTRAL_URL__); await cen.waitForFunction(() => window.VRN_TEMPLATE_MOUNTED === true, null, { timeout: 15000 });
  out.central_mounted = true;
  out.enabled_before = await cen.evaluate(() => document.querySelector('.vrn-tpl-root').getAttribute('data-vrn-enabled'));
  out.sections = await cen.evaluate(() => Array.from(document.querySelectorAll('[data-vrn-section]')).map(n => n.getAttribute('data-vrn-section')));
  out.verdict_text = await cen.evaluate(() => document.querySelector('.vrn-tpl-root').textContent.includes(__VERDICT__));
  await sync.evaluate(mid => { const row = Array.from(document.querySelectorAll('.module-row')).find(r => (r.querySelector('small') || {}).textContent === mid); row.querySelector('.module-toggle').click(); }, __MID__);
  await cen.waitForFunction(() => document.querySelector('.vrn-tpl-root').getAttribute('data-vrn-enabled') === '0', null, { timeout: 15000 }).catch(() => {});
  out.enabled_after_off = await cen.evaluate(() => document.querySelector('.vrn-tpl-root').getAttribute('data-vrn-enabled'));
  // 量「真的看不看得到」(高度),不只看屬性——批735 使用者路徑實測抓到:行內 display 會蓋掉 hidden,屬性對了畫面沒收
  out.seen_off = await cen.evaluate(() => { const r = document.querySelector('.vrn-tpl-root'), o = r.querySelector('.vrn-tpl-off');
    return { body: r.querySelector('.vrn-tpl-body').offsetHeight > 0, hint: !!o && o.offsetHeight > 0 }; });
  await sync.evaluate(mid => { const row = Array.from(document.querySelectorAll('.module-row')).find(r => (r.querySelector('small') || {}).textContent === mid); row.querySelector('.module-toggle').click(); }, __MID__);
  await cen.waitForFunction(() => document.querySelector('.vrn-tpl-root').getAttribute('data-vrn-enabled') === '1', null, { timeout: 15000 }).catch(() => {});
  out.enabled_after_on = await cen.evaluate(() => document.querySelector('.vrn-tpl-root').getAttribute('data-vrn-enabled'));
  out.seen_on = await cen.evaluate(() => { const r = document.querySelector('.vrn-tpl-root'), o = r.querySelector('.vrn-tpl-off');
    return { body: r.querySelector('.vrn-tpl-body').offsetHeight > 0, hint: !!o && o.offsetHeight > 0 }; });
  // 釘選:synchronizer 取消 → 中央頁標記真的收;釘回 → 出來
  const pinSeen = () => cen.evaluate(() => { const n = Array.from(document.querySelectorAll('.vrn-tpl-root .status')).find(x => x.textContent.includes('釘選')); return !!n && n.offsetHeight > 0; });
  const pinClick = () => sync.evaluate(mid => Array.from(document.querySelectorAll('.module-row')).find(r => (r.querySelector('small') || {}).textContent === mid).querySelector('.module-pin').click(), __MID__);
  await pinClick(); await cen.waitForTimeout(300); out.pin_after_unpin = await pinSeen();
  await pinClick(); await cen.waitForTimeout(300); out.pin_after_repin = await pinSeen();
  // 下載 VRN 資料:真的下載一份 JSON、讀得回來
  try {
    const [dl] = await Promise.all([sync.waitForEvent('download', { timeout: 10000 }), sync.click('#syncAddonSlotBody button')]);
    const fs = require('fs'); const p = await dl.path();
    const dj = JSON.parse(fs.readFileSync(p, 'utf-8'));
    out.download = { name: dl.suggestedFilename(), sections: Array.isArray(dj.sections) ? dj.sections.length : -1 };
  } catch (e) { out.download = { error: String(e && e.message || e) }; }
  // 手機寬 390:頁面不橫向捲(收合全打開再量;表格在自己的捲動框裡)
  await cen.setViewportSize({ width: 390, height: 844 }); await cen.waitForTimeout(300);
  out.narrow = await cen.evaluate(() => { document.querySelectorAll('.vrn-tpl-root details').forEach(d => { d.open = true; });
    return { sw: document.documentElement.scrollWidth, iw: window.innerWidth }; });
  out.shim = await cen.evaluate(() => window.VRN_TEMPLATE_TOAST_SHIM || null);
  out.toast_shown = await cen.evaluate(() => { const t = document.getElementById('toast'); return !!(t && t.classList.contains('show')); });
  if (__SHOT__) {
    // 截圖:中央頁捲到外掛槽(讓出黏頂的頂欄)· synchronizer 頁捲到 VRN 模組列
    await cen.setViewportSize({ width: 1440, height: 1600 }); await cen.waitForTimeout(2800);
    await cen.evaluate(() => {
      const s = document.getElementById('addonSlot') || document.querySelector('.vrn-tpl-root'); s.scrollIntoView({ block: 'start' });
      for (let p = s.parentElement; p; p = p.parentElement) { if (p.scrollTop > 0) { p.scrollTop = Math.max(0, p.scrollTop - 80); break; } }
    });
    await cen.screenshot({ path: __SHOT__ });
    await sync.setViewportSize({ width: 1440, height: 1600 });
    await sync.evaluate(mid => { const row = Array.from(document.querySelectorAll('.module-row')).find(r => (r.querySelector('small') || {}).textContent === mid); if (row) row.scrollIntoView({ block: 'center' }); }, __MID__);
    await sync.screenshot({ path: __SHOT_SYNC__ });
  }
  await browser.close();
  console.log(JSON.stringify(out));
})().catch(e => { console.log(JSON.stringify({ fatal: String(e && e.message || e) })); process.exit(3); });
"""


def browser_probe(central: Path, synchronizer: Path, verdict: str, shot: str = "", template_root=None) -> dict:
    """headless Chromium 實跑(要 node + playwright;找不到 = SKIP 並講缺什麼)。
    先跑對照組(原封模板):模板自己丟的錯記在 template_errors,點名「模板既有缺陷」;衍生頁必須零錯。"""
    if not _node():
        return {"state": "SKIP", "why": "本境沒有 node"}
    troot = Path(template_root or TEMPLATE_ROOT)
    try:
        ent = json.loads((troot / "manifest.json").read_text(encoding="utf-8"))["canonicalEntrypoints"]
    except (OSError, ValueError, KeyError) as exc:
        return {"state": "FAIL", "why": f"模板 manifest 讀不動({type(exc).__name__}),對照組跑不了"}
    shot_sync = str(Path(shot).with_name(Path(shot).stem + "_synchronizer" + Path(shot).suffix)) if shot else ""
    probe_dir = Path(tempfile.mkdtemp(prefix="vrn089_browser_"))
    try:
        rc0, _ = _run_node("require('playwright');", probe_dir, timeout=60)
        if rc0 != 0:
            return {"state": "SKIP", "why": "node 找不到 playwright(NODE_PATH 指到裝了 playwright 的 node_modules 才跑)"}
        script = (BROWSER_PROBE.replace("__SHOT_SYNC__", json.dumps(shot_sync))
                  .replace("__SYNC_URL__", json.dumps(synchronizer.resolve().as_uri()))
                  .replace("__CENTRAL_URL__", json.dumps(central.resolve().as_uri())).replace("__MID__", json.dumps(MODULE["id"]))
                  .replace("__TPL_SYNC_URL__", json.dumps((troot / ent["synchronizer"]).resolve().as_uri()))
                  .replace("__TPL_CENTRAL_URL__", json.dumps((troot / ent["centralUI"]).resolve().as_uri()))
                  .replace("__VERDICT__", json.dumps(str(verdict))).replace("__SHOT__", json.dumps(shot) if shot else "''"))
        rc, out = _run_node(script, probe_dir, timeout=240)
        try:
            res = json.loads(out.strip().splitlines()[-1])
        except (ValueError, IndexError):
            return {"state": "FAIL", "why": "瀏覽器探針沒有結果:" + out[-300:]}
        defect = sorted(set(res.get("template_errors") or []))
        # 模板有缺陷 → 補丁一定要作用、模板自己的通知要真的出來;模板沒缺陷 → 補丁不作用也對
        shim_ok = (res.get("shim") == "APPLIED" and res.get("toast_shown")) if defect else res.get("shim") in ("NOT_NEEDED", "APPLIED")
        so, sn, dl, nw = res.get("seen_off") or {}, res.get("seen_on") or {}, res.get("download") or {}, res.get("narrow") or {}
        seen_ok = so.get("body") is False and so.get("hint") is True and sn.get("body") is True and sn.get("hint") is False
        pin_ok = res.get("pin_after_unpin") is False and res.get("pin_after_repin") is True
        dl_ok = str(dl.get("name", "")).endswith(".json") and (dl.get("sections") or 0) >= 1
        narrow_ok = bool(nw) and nw.get("sw", 10 ** 6) <= nw.get("iw", 0) + 1
        ok = (rc == 0 and not res.get("errors") and res.get("sync_mounted") and res.get("sync_row") and res.get("central_mounted")
              and res.get("enabled_before") == "1" and res.get("enabled_after_off") == "0" and res.get("enabled_after_on") == "1"
              and res.get("verdict_text") and "summary" in (res.get("sections") or []) and shim_ok
              and seen_ok and pin_ok and dl_ok and narrow_ok)
        why = ("模板既有缺陷(原封模板對照:中央頁 " + " · ".join(defect) + ")→ 衍生頁補丁 " + str(res.get("shim"))
               + (" · 模板通知照出" if res.get("toast_shown") else "") + " · " if defect else "原封模板對照零錯 · ")
        why += (f"衍生頁錯 {len(res.get('errors') or [])} · synchronizer 模組列 {'有' if res.get('sync_row') else '無'} · "
                f"關 / 開 → 中央 {res.get('enabled_before')}→{res.get('enabled_after_off')}→{res.get('enabled_after_on')}"
                f"(量高度:{'真的收起再回來' if seen_ok else '沒真的收起!'})· 釘選 {'跟著' if pin_ok else '沒跟!'} · "
                f"下載 {dl.get('name') or dl.get('error') or '-'} · 手機寬 {nw.get('sw')}/{nw.get('iw')} · 段 {len(res.get('sections') or [])}")
        if not ok:
            why += " · " + json.dumps(res, ensure_ascii=False)[:400]
        return {"state": "OK" if ok else "FAIL", "why": why, "res": res, "template_defect": defect,
                "shots": [p for p in (shot, shot_sync) if p and Path(p).is_file()]}
    finally:
        shutil.rmtree(probe_dir, ignore_errors=True)


def _page_note(html_path: Path, sec_id: str = "new") -> str:
    """從建好的頁讀回內嵌資料裡某一段的說明(瀏覽器實際會畫的那一句)。讀不到 = 空字串。"""
    try:
        html = Path(html_path).read_text(encoding="utf-8")
        a = html.index('<script id="vrn-template-payload" type="application/json">') + len('<script id="vrn-template-payload" type="application/json">')
        payload = json.loads(html[a:html.index("</script>", a)])
        return next((x.get("note") or "" for x in payload.get("sections") or [] if x.get("id") == sec_id), "")
    except (OSError, ValueError, StopIteration):
        return ""


def _sample_report(tmp: Path) -> dict:
    eng = tmp / "fake_engine.py"
    eng.write_text("# fake engine\n", encoding="utf-8")
    return {"loop": "VRN_AutoTestLoop 自測", "generated": "2026-09-24T20:00:00", "verdict": "GREEN", "samples": str(tmp),
            "real_mode": False, "workdir": str(tmp), "rounds_run": 1, "rounds_max": 1,
            "counts": {"PASS": 3, "WARN": 0, "SKIP": 0, "FAIL": 0}, "fixes_applied": [], "file_count": 2,
            "engines": {"database": str(eng)}, "engine_errors": {}, "dependencies": {"duckdb": True},
            "rounds": [{"round": 1, "verdict": "GREEN", "rows": [
                {"gate": "G01 COMPILE", "name": "a.py", "status": "PASS", "detail": ""},
                {"gate": "G06 BATCH", "name": "x.pdf", "status": "PASS", "detail": "ok"},
                {"gate": "G06 BATCH", "name": "y.pdf", "status": "PASS", "detail": "ok"}]}],
            "fieldspec": [{"key": "report_date", "zh": "報告日", "state": "GREEN", "have": 2, "total": 2}],
            "financial": {"n_files": 2, "rows": 36, "files": {"x.pdf": {"rows": 36, "checked": 18, "passed": 18}}},
            "adj": {"n_files": 2, "states": {"ADJ_OK": 1}, "files": {"y.pdf": "ADJ_OK"}}}


def selftest() -> int:
    fails, skips, n = [], [], [0]

    def chk(name, ok, note=""):
        n[0] += 1
        print(f"  [{'OK' if ok else 'FAIL'}] {name} {note}".rstrip())
        if not ok:
            fails.append(name)

    def skp(name, why):
        n[0] += 1
        skips.append(name)
        print(f"  [SKIP] {name}({why})")

    latest_links = LATEST_DIR / LINKS_NAME
    fp0 = (latest_links.stat().st_size, latest_links.stat().st_mtime_ns) if latest_links.is_file() else None
    tpl = template_check()
    chk("① 制式模板三入口對 manifest(sha256;換行被改寫認內容一致並點名)", tpl["ok"],
        f"(release {tpl.get('release')} · " + " · ".join(f"{r['role']} {'OK' if r['ok'] else 'X'}{'(CRLF)' if r.get('crlf') else ''}"
                                                        for r in tpl["rows"]) + ")")
    try:
        man = json.loads(MANIFEST.read_text(encoding="utf-8"))
        sync_html = (TEMPLATE_ROOT / man["canonicalEntrypoints"]["synchronizer"]).read_bytes().decode("utf-8")
        mods = default_modules(sync_html)
    except (OSError, ValueError, KeyError) as exc:
        mods, sync_html = [], ""
        print(f"      {type(exc).__name__}: {exc}")
    chk("② DEFAULT_MODULES 從 synchronizer 原始碼抽得出(不另寫一份)", len(mods) >= 1 and all(
        {"id", "name", "type", "enabled", "pinned", "order"} <= set(m) for m in mods), f"({len(mods)} 個:{', '.join(m['id'] for m in mods)})")
    tmp = Path(tempfile.mkdtemp(prefix="vrn089_selftest_"))
    try:
        rep = _sample_report(tmp)
        rp = tmp / "VRN_AutoTest_Report.json"
        rp.write_text(json.dumps(rep, ensure_ascii=False), encoding="utf-8")
        out = tmp / "tpl"
        r1 = build(rp, out)
        ui = out / "ui"
        ent = man["canonicalEntrypoints"] if tpl["ok"] else {}
        exact = r1["state"] == "BUILT" and all(
            ((ui / Path(ent[role]).name).read_bytes() == (TEMPLATE_ROOT / ent[role]).read_bytes()) if role == "launcher" else
            (strip_injection((ui / Path(ent[role]).name).read_bytes().decode("utf-8")).encode("utf-8")
             == (TEMPLATE_ROOT / ent[role]).read_bytes()) for role in ROLES)
        chk("③ 套版不改模板:啟動頁逐位元組 = 模板;中央 / synchronizer 拿掉插入段 = 模板逐位元組", exact,
            f"({r1['state']} · {len(r1.get('pages') or {})} 張)")
        m160 = _mdl160()
        if m160 is None or not hasattr(m160, "OFFLINE_RX"):
            skp("④ 頁上零連線(借 CGC_MDL160 離線四尺與「面」)", "CGC_MDL160 尾版載不到")
        else:
            inj = "".join(injected_text((ui / Path(ent[r]).name).read_text(encoding="utf-8")) for r in ("centralUI", "synchronizer"))
            hits = [k for k, rx in m160.OFFLINE_RX.items() if rx.search(inj)]
            faces = {r: m160.surface_of((ui / Path(ent[r]).name).read_text(encoding="utf-8")) for r in ROLES}
            chk("④ 頁上零連線(借 CGC_MDL160 離線四尺:插入段零命中;三張衍生頁的「面」都是 VIEW)",
                not hits and set(faces.values()) == {"VIEW"}, f"(命中 {hits or '零'} · 面 {sorted(set(faces.values()))})")
        rep2 = json.loads(json.dumps(rep))
        rep2["brand_new_section"] = {"hello": "上游新欄"}
        rep2["rounds"][0]["rows"].append({"gate": "G99 NEWGATE", "name": "z.pdf", "status": "WARN", "detail": "新關卡"})
        rep2["financial"]["files"]["z.pdf"] = {"rows": 12, "checked": 6, "passed": 6}
        rep2["fieldspec"].append({"key": "target_price", "zh": "目標價", "state": "GREEN", "have": 1, "total": 1})
        rp.write_text(json.dumps(rep2, ensure_ascii=False), encoding="utf-8")
        r2 = build(rp, out)
        kinds = {(x["kind"], x["what"]): x for x in r2["new_items"]}
        want = [("欄", "brand_new_section"), ("關卡", "G99 NEWGATE · z.pdf"), ("檔", "z.pdf"), ("欄位規格", "target_price")]
        chk("⑤ 自適應 + 新增檢查:上游多一個沒見過的頂層欄 · 新關卡 · 新檔 · 新欄位規格 → 逐項點名 NEW 且都上了頁",
            r2["rc"] == 0 and all(k in kinds and kinds[k]["on_page"] for k in want),
            f"(NEW {len(r2['new_items'])} 項:" + " · ".join(f"{k[0]}:{k[1]}→{(kinds.get(k) or {}).get('home')}" for k in want) + ")")
        r3 = build(rp, out)
        pages_before = {p.name: p.stat().st_mtime_ns for p in ui.iterdir()}
        r4 = build(rp, out)
        pages_after = {p.name: p.stat().st_mtime_ns for p in ui.iterdir()}
        rep3 = json.loads(json.dumps(rep2))
        rep3["rounds"][0]["rows"][0]["status"] = "FAIL"
        del rep3["brand_new_section"]
        rp.write_text(json.dumps(rep3, ensure_ascii=False), encoding="utf-8")
        r5 = build(rp, out)
        st5 = _read_links(out).get("states") or {}
        note5 = _page_note(Path(r5["central"]))
        chk("⑥ 上下游連結冊:同一份再建 → 全 SAME 且頁不重寫(冪等,照樣回兩頁路徑);關卡狀態變 → CHANGED;拿掉一欄 → GONE;"
            "同一個夾重建的說法是「對這個夾的上一版」(頁上新增段說明也是),不冒充「對上一輪」",
            r1["links"].get("NEW", 0) > 0 and r3["state"] in ("SAME", "BUILT") and r4["state"] == "SAME" and pages_before == pages_after
            and Path(r4.get("central", "")).is_file() and Path(r4.get("synchronizer", "")).is_file()
            and st5.get("關卡|G01 COMPILE|a.py") == "CHANGED" and st5.get("欄|brand_new_section") == "GONE"
            and r1.get("compared_to") is None and r1.get("basis", "").startswith("首建")
            and r4.get("compared_to") == "self" and r5.get("compared_to") == "self" and r5.get("basis", "").startswith("對這個夾的上一版")
            and note5.startswith("對這個夾的上一版") and "對上一輪" not in note5,
            f"(首建 NEW {r1['links'].get('NEW')} · 再建 {r4['state']} · 關卡 {st5.get('關卡|G01 COMPILE|a.py')} · 欄 {st5.get('欄|brand_new_section')} · "
            f"說法 {r1.get('basis', '')[:4]} → {r5.get('basis', '')[:8]} · 頁上「{note5[:14]}」)")

        def drop(payload):
            payload["sections"] = [s for s in payload["sections"] if s["id"] != "extra-another-new"]

        rep4 = json.loads(json.dumps(rep3))
        rep4["another_new"] = [1, 2]
        rp.write_text(json.dumps(rep4, ensure_ascii=False), encoding="utf-8")
        r6 = build(rp, out, _sections_hook=drop)
        # 模板改版、找不到插入點(假模板:中央頁沒有 </body>,manifest 跟著改)→ BLOCKED,一張都不寫
        fake, man_f, files_f = tmp / "fake_tpl", json.loads(MANIFEST.read_text(encoding="utf-8")), []
        for role in ROLES:
            rel = man_f["canonicalEntrypoints"][role]
            data = (TEMPLATE_ROOT / rel).read_bytes()
            if role == "centralUI":
                data = re.sub(rb"(?i)</body>", b"</body-gone>", data)
            (fake / rel).parent.mkdir(parents=True, exist_ok=True)
            (fake / rel).write_bytes(data)
            files_f.append({"path": rel, "sha256": _sha(data)})
        man_f["files"] = files_f
        (fake / "manifest.json").write_text(json.dumps(man_f, ensure_ascii=False), encoding="utf-8")
        rb7 = build(rp, tmp / "blocked_out", template_root=fake)
        blocked7 = rb7["state"] == "BLOCKED" and "插不進去" in rb7["why"] and not (tmp / "blocked_out").exists()
        chk("⑦ 反面控制:新增項目的落點段不在 → build rc1 並點名(新增不能被吞)· 模板找不到插入點 → BLOCKED 且一張都不寫",
            r6["rc"] == 1 and "another_new" in r6["why"] and blocked7, f"({r6['why'][:80]} · 插入點不在 {rb7['state']})")
        chk_state = check(out)
        rep_v = json.loads(rp.read_text(encoding="utf-8"))
        rep_v["generated"] = "2099-01-01T00:00:00"             # 只改每輪必變的欄:內容簽章不變,但檔案重寫過
        rp.write_text(json.dumps(rep_v, ensure_ascii=False), encoding="utf-8")
        vol = check(out)
        r_vol = build(rp, out)
        rp.write_text(json.dumps(rep, ensure_ascii=False), encoding="utf-8")
        stale = check(out)
        (ui / Path(ent["launcher"]).name).write_text("changed", encoding="utf-8")
        build(rp, out)
        (ui / Path(ent["centralUI"]).name).write_text("hand edit", encoding="utf-8")
        drift = check(out)
        chk("⑧ check 動詞:剛建完 rc0 · 報告只重寫每輪必變的欄 → STALE 且重建(不走 SAME)但零異動 · 上游報告內容改了 rc1 STALE · "
            "下游頁被手改 rc1 DRIFT · 沒建過 rc2",
            chk_state["rc"] == 0 and vol["state"] == "STALE" and "重寫過" in vol["why"] and r_vol["state"] == "BUILT"
            and not r_vol["links"].get("CHANGED") and not r_vol["links"].get("NEW")
            and stale["rc"] == 1 and stale["state"] == "STALE" and drift["state"] == "DRIFT"
            and check(tmp / "nowhere")["rc"] == 2,
            f"({chk_state['state']} · 重寫 {vol['state']}→{r_vol['state']} 異動 {r_vol['links'].get('CHANGED', 0)} · {stale['state']} · {drift['state']})")
        if not _node():
            skp("⑨ synchronizer 預置只增不減(node 實跑五種狀態)", "本境沒有 node")
        else:
            probe = (PRESEED_PROBE.replace("__JS__", json.dumps(_fill(PRESEED_JS, mods)))
                     .replace("__MID__", json.dumps(MODULE["id"])).replace("__NDEF__", str(len(mods))))
            rc, outp = _run_node(probe, tmp)
            try:
                res = json.loads(outp.strip().splitlines()[-1])
            except (ValueError, IndexError):
                res = {}
            chk("⑨ synchronizer 預置只增不減(node 實跑):沒狀態 → 模板預設 + VRN · 有狀態沒 VRN → 只加一個、其餘與未知欄照舊 · "
                "VRN 已在且被關 → 一字不動 · 壞 JSON / 舊 v1 → 不寫",
                rc == 0 and res and all(res.values()), f"({res or outp[-200:]})")
        r7 = build(rp, out)
        br = browser_probe(Path(r7["central"]), Path(r7["synchronizer"]), rep["verdict"])
        name10 = ("⑩ 瀏覽器實跑(原封模板對照組點名模板既有缺陷 · 中央頁外掛掛上 · synchronizer 模組清單有 VRN · "
                  "在 synchronizer 關 / 開 → 中央頁即時跟著且**量高度真的收起再回來** · 釘選跟著 · 下載鈕真的下載 JSON · "
                  "手機寬不橫捲 · 衍生頁零頁面錯誤)")
        if br["state"] == "SKIP":
            skp(name10, br["why"])
        else:
            chk(name10, br["state"] == "OK", f"({br['why'][:420]})")
        # ⑪ 跨輪自動連結:自測迴圈每輪一個工作夾,模板建在 <工作夾>/template;第二輪自動找到第一輪當基準
        runs_root = tmp / "runs"
        rp_a, rp_b = runs_root / "r1" / "VRN_AutoTest_Report.json", runs_root / "r2" / "VRN_AutoTest_Report.json"
        rp_a.parent.mkdir(parents=True)
        rp_b.parent.mkdir(parents=True)
        rp_a.write_text(json.dumps(rep, ensure_ascii=False), encoding="utf-8")
        ra = build(rp_a, rp_a.parent / RUN_SUBDIR, baseline=find_baseline(rp_a.parent))
        time.sleep(1.1)                                      # built_at 到秒;兩輪要分得出先後
        rep_b = json.loads(json.dumps(rep))
        rep_b["next_round_field"] = {"k": 1}
        rep_b["rounds"][0]["rows"][1]["status"] = "WARN"
        rp_b.write_text(json.dumps(rep_b, ensure_ascii=False), encoding="utf-8")
        base_b = find_baseline(rp_b.parent)
        rb = build(rp_b, rp_b.parent / RUN_SUBDIR, baseline=base_b)
        note_b = _page_note(Path(rb["central"]))
        lb = _read_links(rp_b.parent / RUN_SUBDIR)
        stb = lb.get("states") or {}
        ho = handover((runs_root,))
        items_now = link_items(rep_b, rp_b, template_check())
        chk("⑪ 跨輪自動連結:第二輪自動以第一輪為基準(不是全算新增)· 新欄 NEW · 關卡變 CHANGED · 其餘 SAME · 建構器 sha 列為上游 · "
            "交接口報最新一版且 check 對得上 · 說法是「對上一輪」(建構回值 · 頁上 · 交接口三處一致)",
            ra["links"].get("SAME", 0) == 0 and base_b is not None and base_b.parent == rp_a.parent / RUN_SUBDIR
            and lb.get("compared_to") == "baseline" and stb.get("欄|next_round_field") == "NEW"
            and stb.get("關卡|G06 BATCH|x.pdf") == "CHANGED" and stb.get("上游|模板|centralUI") == "SAME"
            and rb["links"].get("SAME", 0) > 0 and items_now.get("上游|建構器", {}).get("sig") == _sha(Path(__file__).read_bytes())
            and ho.get("runs") == 2 and ho.get("state") == "OK" and Path(ho.get("out", "")).parent == rp_b.parent
            and Path(ho.get("central", "")).is_file()
            and rb.get("compared_to") == "baseline" and rb.get("basis", "").startswith("對上一輪") and note_b.startswith("對上一輪")
            and ho.get("basis", "").startswith("對上一輪"),
            f"(基準 {base_b.parent.parent.name if base_b else '無'} · 第二輪 新增 {rb['links'].get('NEW')} · 異動 {rb['links'].get('CHANGED')} · "
            f"未變 {rb['links'].get('SAME')} · 交接 {ho.get('state')} 共 {ho.get('runs')} 版 · 說法 {rb.get('basis', '')[:4]} · 頁上「{note_b[:14]}」)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    fp1 = (latest_links.stat().st_size, latest_links.stat().st_mtime_ns) if latest_links.is_file() else None
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑫ 紀律:自測只寫暫存(正式 VIA_Reports/vrn/template 前後不變)· 加速橋 · 律宣告",
        fp0 == fp1 and "VIA:ACCEL-BRIDGE" in src and all(k in src for k in ("模板零改動", "只增不減", "誠實三態", "尾版律")),
        f"(連結冊 {'不在' if fp0 is None else '前後一致' if fp0 == fp1 else '變了'})")
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails) - len(skips)} · FAIL {len(fails)} · SKIP {len(skips)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=ENGINE_TAG)
    ap.add_argument("verb", nargs="?", default="status", choices=("build", "check", "status"))
    ap.add_argument("--report", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--shot", default="", help="build 後用瀏覽器實跑並截中央頁(要 node + playwright)")
    ap.add_argument("--baseline", default="", help="build:對哪一版比新增 / 異動 / 消失(連結冊或它的夾;預設 = 輸出夾自己的上一版)")
    a = ap.parse_args()
    if a.selftest:
        print(f"=== {ENGINE_TAG} · VRN 模板(制式 U/I · synchronizer 控制 · 上下游連結與新增檢查)自測 ===")
        return selftest()
    out = Path(a.out) if a.out else LATEST_DIR
    if a.verb == "build":
        if not a.report:
            print("[VRN 模板] build 要 --report <VRN_AutoTest_Report.json>")
            return 2
        res = build(Path(a.report), out, baseline=a.baseline or None)
        lc = res.get("links") or {}
        print(f"[VRN 模板] {res['state']} · {res.get('basis') or '-'} · 新增 {lc.get('NEW', 0)} · 異動 {lc.get('CHANGED', 0)} · "
              f"消失 {lc.get('GONE', 0)} · 未變 {lc.get('SAME', 0)}" + (f" · {res['why']}" if res.get("why") else ""))
        if res.get("crlf"):
            print(f"[VRN 模板] 模板換行被改寫(內容一致,照建):{', '.join(res['crlf'])}")
        if res.get("central"):
            print(f"[VRN 模板] 中央頁 {res['central']}")
            print(f"[VRN 模板] synchronizer {res['synchronizer']}")
        if a.shot and res.get("central"):
            rep = json.loads(Path(a.report).read_text(encoding="utf-8"))
            br = browser_probe(Path(res["central"]), Path(res["synchronizer"]), rep.get("verdict", ""), shot=a.shot)
            print(f"[VRN 模板] 瀏覽器實跑 {br['state']} · {br['why'][:300]}")
            for p in br.get("shots") or []:
                print(f"[VRN 模板] 截圖 {p}")
        return res["rc"]
    if a.verb == "check":
        res = check(out)
        print(f"[VRN 模板] {res['state']} · {res['why']}")
        return res["rc"]
    if not a.out:                                          # 沒指定夾:看全部找得到的版,報最新一版(交接用同一個口)
        h = handover()
        if h["state"] == "ABSENT":
            print(f"[VRN 模板] {h['why']}")
            return 2
        print(f"[VRN 模板] 最新一版 {h['built_at']} · 共 {h['runs']} 版 · {h['state']} · {h['why']}")
        out = Path(h["out"])
    rec = _read_links(out)
    if not rec:
        print(f"[VRN 模板] 還沒建過({out / LINKS_NAME} 不在)")
        return 2
    print(f"[VRN 模板] {rec.get('built_at')} · {rec.get('engine')} · 上游 {rec.get('report')}"
          + f" · {basis_text(rec.get('compared_to'), rec.get('previous'))}" + (f"(基準 {rec.get('baseline')})" if rec.get("baseline") else ""))
    print(f"           新增 {rec['counts'].get('NEW', 0)} · 異動 {rec['counts'].get('CHANGED', 0)} · 消失 {rec['counts'].get('GONE', 0)} · "
          f"未變 {rec['counts'].get('SAME', 0)} · 新增沒上頁 {len(rec.get('new_missing') or [])}")
    for n_ in (rec.get("new_items") or [])[:12]:
        print(f"           · NEW {n_['kind']} {n_['what']} → {n_.get('home')} {'OK' if n_.get('on_page') else '沒上頁'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
