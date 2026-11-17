#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL282_LocalMonitor v0101 — 薄尾(v0100 一字不動):把現況矩陣還沒管到的面向補上,並列出仍然沒有來源的面向。

操作員 2026-11-17:「黃色燈也是白色字 · 現況矩陣偵測還有哪方面沒管理到的請完善測試」。

v0100 管到的只有五塊:系統 · 工具 · 參數 · 模組引擎(號冊只讀 MDL / ENG)· 收據。本版多十二塊(sec_extra 一次回傳,欄位是通用項目格式):
  號冊        MDL / ENG 以外每一本號冊(CLS · FNC · LIB · ENV · REQ · WKF · TST · PLCY …),依「類 × 系統」彙總列數與冊列自己的燈
  號冊待辦    REQ · WKF · TST · LIB · TOOL 的非綠列逐列;其他類的紅列逐列(退役列不算)。名單 / 來源 / 因子類的列只帶編號,不帶名稱(名稱屬資料)
  衝突登記    VIA_RC1_ConflictRegistry 尾版逐筆(OPEN 紅且待裁 · CONTAINED 黃 · RULED / FIXED 綠)
  收據契約    VIA_SystemReceipt_Contract_SSOT 宣告的每一份收據:在不在 · 必填欄 · 時效 · 燈(照契約的對照表)
  測試分級    五系統 × 六級(單元 · 整合 · 系統 · 使用者實測 · 輸出驗證 · U/I 同步);來源是 TST 號冊、收據契約、門面登記的收據,沒有來源的格子亮灰
  橋覆蓋      每個家族尾版用語法樹判:加速器橋有沒有真的匯入(只有標記 = 黃);會出網的檔有沒有走網路橋。靜態判定,不逐支執行
  環境套件    VIA_Env_Requirements 列的套件在這台機器裝了沒
  資料庫      VIA_Config_SSOT 的 db.path / parquet_root 在不在、大小、parquet 檔數(只看檔案系統,不開庫、不讀內容)
  版本線      分支 · HEAD · 落後 / 超前 origin/main(用本機記得的 origin/main,不 fetch)· 未提交檔數
  應有收據    VCGC MCP 唯讀門面登記的每一份收據:在不在 · 新不新(內容的燈仍看「收據」區塊)。v0100 只掃得到存在的檔,該有卻沒有的看不到
  同義字正則  同義字聯集 · 正則字典 · 中央同義正則 · 正則參數紀錄各冊尾版:在不在、筆數(不判內容對錯)
  執行環境    這一輪在哪種機器跑(容器跑的系統級綠不算主機實測)
  管理面覆蓋  操作員列過的每個管理面向各一列:綠 = 這一輪有來源且有資料 · 灰 = 還沒有來源。這一塊就是「還有哪方面沒管到」的答案
另:自己那一頁的黃燈改白字(只換燈上字的顏色規則,燈色不動)。
唯讀:不寫倉、不發號、不裝套件、不連網、不載 TA-Lib、不執行被掃的檔。沒有示範資料。
動詞  run(照 v0100)· extra(只印新九塊的摘要)· selftest · version
呼叫  VIA_FROM_VCGC=YES python3 CGC_MDL149_…_vNNNN.py run CGC_MDL282_LocalMonitor run
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

import ast
import datetime as _dt
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

ENGINE = "CGC_MDL282_LocalMonitor_v0101"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "CGC_MDL282_LocalMonitor_v0100.py"
_PRIOR_FILE = HERE / PRIOR_NAME
_spec = importlib.util.spec_from_file_location("CGC_MDL282_LocalMonitor_v0100", _PRIOR_FILE)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["CGC_MDL282_LocalMonitor_v0100"] = PRIOR
_spec.loader.exec_module(PRIOR)
PRIOR.ENGINE = ENGINE
PRIOR.CSS = re.sub(r"\.y\{background:var\(--y\);color:[^}]+\}", ".y{background:var(--y)}", PRIOR.CSS)  # 黃燈白字(跟其他三色一樣吃 .lamp 的字色)
VER_RX = re.compile(r"[-_]v(\d{4})(?=\.[A-Za-z0-9]+$)")
BOOK_RX = re.compile(r"^VIA_NumberBook_([A-Z]+)(?:_([A-Z0-9]+))?_v\d{4}\.jsonl$")
ROWWISE = ("REQ", "WKF", "TST", "LIB", "TOOL")
NAMED = ROWWISE + ("PLCY", "ENV", "CLS", "FNC", "STP", "PRMT")  # 這幾類的名稱是程式 / 治理物件;其餘類(名單、來源、因子等)的名稱屬資料,只帶編號不帶名稱
LAMP = {"GREEN": "g", "AMBER": "y", "YELLOW": "y", "RED": "r"}
SKIP = (".git", "__pycache__", "node_modules", "VIA_Reports", ".venv", "venv", "tests", "fixtures")
NET_LIBS = {"requests", "urllib", "urllib3", "httpx", "aiohttp", "yfinance", "akshare", "FinMind", "socket", "ftplib", "http"}
SYSTEMS = ["VCGC", "VDF", "VRN-2", "VQG", "VAP"]
LEVELS = ["單元", "整合", "系統", "使用者實測", "輸出驗證", "U/I 同步"]
# 門面收據鍵 → 測試分級的格子(系統, 級)。只對得上名字明確的;對不上的只進「應有收據」
RECEIPT_CELL = {"workbench/ui-usertest": ("全樹", "使用者實測"), "workbench/responsive": ("全樹", "U/I 同步"), "vdf/ui-manifest": ("VDF", "U/I 同步"),
                "vrn2/closeout": ("VRN-2", "U/I 同步"), "vdf/macro-crosscheck": ("VDF", "輸出驗證"), "vqg/export-vap": ("VQG", "輸出驗證")}
SYN_BOOKS = ("VIA_SSOT_SynonymUnion", "VIA_SSOT_RegexDict", "VIA_Central_Synonym_Regex", "VIA_VCGC_RegexParamRecord", "VIA_TickerRegex_Scope_SSOT")
PIP_IMPORT = {"pymupdf": "fitz", "beautifulsoup4": "bs4", "pyyaml": "yaml", "scikit-learn": "sklearn", "pillow": "PIL", "python-dateutil": "dateutil",
              "opencv-python": "cv2", "markitdown": "markitdown", "finmind": "FinMind"}


def cut(s, n=160) -> str:
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[: n - 1] + "…"


def tail_json(folder: Path, stem: str):
    best = None
    for p in folder.glob(stem + "_v*.json"):
        m = VER_RX.search(p.name)
        if m and (best is None or int(m.group(1)) > best[0]):
            best = (int(m.group(1)), p)
    return best[1] if best else None


def age_hours(s):
    try:
        t = _dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=_dt.timezone.utc)
        return (_dt.datetime.now(_dt.timezone.utc) - t).total_seconds() / 3600
    except ValueError:
        return None


# ---------------- 號冊 ----------------
def _read_book(p: Path):
    m = BOOK_RX.match(p.name)
    kind, fsub = m.group(1), m.group(2)
    agg, todo, bad = {}, [], 0
    with open(str(p), encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except ValueError:
                bad += 1
                continue
            sub = r.get("sub") or fsub or (str(r.get("code", "")).split("-") + ["", ""])[1] or "—"
            a = agg.setdefault(sub, {"n": 0, "g": 0, "y": 0, "r": 0, "none": 0, "gone": 0})
            a["n"] += 1
            if r.get("gone_since"):
                a["gone"] += 1
                continue
            lamp = LAMP.get(str(r.get("lamp") or "").upper())
            a[lamp or "none"] += 1
            if lamp in ("y", "r") and (kind in ROWWISE or lamp == "r"):
                todo.append({"section": "號冊待辦", "system": sub, "lamp": lamp, "id": r.get("code") or r.get("full"), "title": cut((r.get("name") or r.get("q") or r.get("full")) if kind in NAMED else (r.get("code") or kind), 90),
                             "ver": "%s %s" % (kind, r.get("version") or ""), "at": str(r.get("updated_at") or ""),
                             "detail": "%s · %s" % (r.get("cat") or kind, cut(r.get("note") or "冊列自己的燈是%s,沒有附註" % ("紅" if lamp == "r" else "黃"), 150))})
    return kind, agg, todo, bad, p.name


def sec_books(via: Path):
    nb = via / "supportive modules" / "registry" / "VIA_NumberBooks"
    files = sorted(p for p in nb.glob("VIA_NumberBook_*_v*.jsonl") if BOOK_RX.match(p.name) and BOOK_RX.match(p.name).group(1) not in ("MDL", "ENG"))
    if not files:
        return [{"section": "號冊", "system": "VCGC", "lamp": "x", "id": "號冊", "title": "MDL / ENG 以外的號冊", "detail": "一本都找不到,沒有證據"}], [], set()
    summ, todo, kinds = [], [], set()
    for kind, agg, td, bad, name in PRIOR.pmap(_read_book, files):
        kinds.add(kind)
        todo += td
        for sub, a in sorted(agg.items()):
            lamp = "r" if a["r"] else ("y" if a["y"] or bad else ("g" if a["g"] else "x"))
            note = "冊列沒有燈欄,只登錄不評燈" if not (a["g"] or a["y"] or a["r"]) else ("紅列與待辦列另在「號冊待辦」逐列,那邊也各算一項" if a["r"] or (a["y"] and kind in ROWWISE) else "")
            summ.append({"section": "號冊", "system": sub, "lamp": lamp, "id": "%s|%s" % (kind, sub), "title": "%s 號冊 · %s" % (kind, sub), "ver": name,
                         "detail": "彙總 · 列 %d · 綠 %d · 黃 %d · 紅 %d · 無燈 %d · 退役 %d%s%s" % (a["n"], a["g"], a["y"], a["r"], a["none"], a["gone"], (" · 壞列 %d" % bad) if bad else "", (" · " + note) if note else "")})
    return summ, todo, kinds


# ---------------- 衝突 · 收據契約 · 測試分級 ----------------
def sec_conflicts(via: Path):
    p = tail_json(via / "docs" / "handoff" / "ai", "VIA_RC1_ConflictRegistry")
    d = PRIOR.load_json(p) if p else None
    if not d:
        return [{"section": "衝突登記", "system": "VCGC", "lamp": "x", "id": "衝突登記冊", "title": "VIA_RC1_ConflictRegistry", "detail": "冊不在,沒有證據"}]
    out = []
    for e in d.get("entries") or []:
        st = str(e.get("status") or "")
        head = re.split(r"[((·\s]", st.strip(), maxsplit=1)[0].upper()
        lamp = "r" if head == "OPEN" else ("g" if head in ("RULED", "FIXED", "CLOSED", "RESOLVED") else "y")
        out.append({"section": "衝突登記", "system": "VCGC", "lamp": lamp, "id": e.get("id"), "title": "%s %s" % (e.get("id"), cut(e.get("class"), 50)), "ver": p.stem[-5:],
                    "needs": head == "OPEN", "detail": "%s · %s · %s" % (cut(st, 40), e.get("severity") or "—", cut(e.get("what"), 110))})
    return out


def sec_contract(via: Path):
    p = tail_json(via / "supportive modules" / "registry", "VIA_SystemReceipt_Contract_SSOT")
    d = PRIOR.load_json(p) if p else None
    if not d:
        return [{"section": "收據契約", "system": "VCGC", "lamp": "x", "id": "收據契約冊", "title": "VIA_SystemReceipt_Contract_SSOT", "detail": "冊不在,沒有證據"}]
    stale_h, maps, out = d.get("stale_hours") or 48, d.get("lamp_maps") or {}, []
    for sysn, s in (d.get("systems") or {}).items():
        name = "VRN-2" if sysn == "VRN2" else sysn
        for r in s.get("receipts") or []:
            base = {"section": "收據契約", "system": name, "id": "%s|%s" % (sysn, r.get("id")), "title": "%s · %s" % (r.get("zh") or r.get("id"), r.get("path"))}
            rec = PRIOR.load_json(via / r["path"]) if (via / r["path"]).is_file() else None
            if not isinstance(rec, dict):
                out.append(dict(base, lamp="x", detail="沒有收據(這台機器還沒跑)"))
                continue
            raw = str(rec.get(r.get("lamp_key") or "lamp") or "")
            mapped = (maps.get(r.get("lamp_map") or "") or {}).get(raw, raw).upper()
            lamp = LAMP.get(mapped, "x")
            notes = ["自報 %s" % (raw or "空")]
            miss = [k for k in r.get("required") or [] if k not in rec]
            if miss:
                notes.append("缺必填欄 " + ",".join(miss))
                lamp = "y" if lamp == "g" else lamp
            at = next((rec.get(k) for k in r.get("at_keys") or [] if rec.get(k)), "")
            a = age_hours(at) if at else None
            if a is None:
                notes.append("收據裡沒有時間")
                lamp = "y" if lamp == "g" else lamp
            elif a > stale_h:
                notes.append("已 %d 小時,超過時效 %d" % (a, stale_h))
                lamp = "y" if lamp == "g" else lamp
            out.append(dict(base, lamp=lamp, at=str(at), ver=str(next((rec.get(k) for k in r.get("version_keys") or [] if rec.get(k)), "")), detail=" · ".join(notes)))
    return out


def sec_expected(via: Path):
    """VCGC MCP 唯讀門面登記的收據:在不在、新不新。回 (項目, {鍵: 燈})。"""
    reg = via / "supportive modules" / "registry"
    best = None
    for p in reg.glob("CGC_MDL279_MCPServer_v*.py"):
        m = VER_RX.search(p.name)
        if m and (best is None or int(m.group(1)) > best[0]):
            best = (int(m.group(1)), p)
    recs = None
    if best:
        try:
            sp = importlib.util.spec_from_file_location("_via_mcp_tail_for_monitor", str(best[1]))
            mod = importlib.util.module_from_spec(sp)
            sp.loader.exec_module(mod)
            recs = dict(getattr(mod, "RECEIPTS", None) or mod.P0.RECEIPTS)
        except Exception as e:
            return [{"section": "應有收據", "system": "VCGC", "lamp": "y", "id": "門面", "title": best[1].name, "detail": "門面載不到(%s),這一輪沒辦法列應有收據" % type(e).__name__}], {}
    if not recs:
        return [{"section": "應有收據", "system": "VCGC", "lamp": "x", "id": "門面", "title": "CGC_MDL279_MCPServer", "detail": "門面不在,沒有證據"}], {}
    out, lamps = [], {}
    for key, rel in sorted(recs.items()):
        if key.startswith("vcgc/feedback"):
            continue  # 本平台自己的輸出,不算別人的收據
        sysn = {"vdf": "VDF", "vrn2": "VRN-2", "vqg": "VQG", "vap": "VAP"}.get(key.split("/")[0], "VCGC")
        base = {"section": "應有收據", "system": sysn, "id": key, "title": "%s · %s" % (key, rel)}
        f = via / rel
        if not f.is_file():
            out.append(dict(base, lamp="x", detail="沒有收據(這台機器還沒跑)"))
            lamps[key] = "x"
            continue
        at, lamp, note = "", "g", "在"
        if rel.endswith(".json"):
            d = PRIOR.load_json(f)
            if isinstance(d, dict):
                at = next((str(d[k]) for k in ("at", "ts", "generated_at", "generated_utc", "updated_at", "built_at", "completed_at") if d.get(k)), "")
        a = age_hours(at) if at else None
        if rel.endswith("_latest.json") and a is None:
            lamp, note = "y", "在,但收據裡沒有時間"
        elif a is not None and a > 48 and "_latest" in rel:
            lamp, note = "y", "在,但已 %d 小時" % a
        out.append(dict(base, lamp=lamp, at=at, detail=note + " · 內容的燈看「收據」區塊"))
        lamps[key] = lamp
    return out, lamps


def sec_synregex(via: Path):
    reg, out = via / "supportive modules" / "registry", []
    for stem in SYN_BOOKS:
        p = tail_json(reg, stem)
        base = {"section": "同義字正則", "system": "VCGC", "id": stem, "title": stem}
        d = PRIOR.load_json(p) if p else None
        if not p:
            out.append(dict(base, lamp="x", detail="冊不在,沒有證據"))
        elif not isinstance(d, (dict, list)):
            out.append(dict(base, lamp="r", ver=p.stem[-5:], detail="冊讀不懂(不是合法 JSON)"))
        else:
            parts = {"(整本)": d} if isinstance(d, list) else {k: v for k, v in d.items() if isinstance(v, (list, dict))}
            k, v = max(parts.items(), key=lambda kv: len(kv[1])) if parts else ("", [])
            out.append(dict(base, lamp="g" if len(v) else "y", ver=p.stem[-5:], at=str(d.get("ts") or d.get("updated_at") or d.get("created_at") or "") if isinstance(d, dict) else "",
                            detail=("最大一節 %s 有 %d 筆" % (k, len(v)) if len(v) else "冊是空的") + " · 只看在不在與筆數,不判內容對錯"))
    return out


def sec_testgrid(via: Path, contract_items, expected=None):
    """五系統 × 六級。來源:TST 號冊(單元 / 整合 / 系統)· 收據契約(系統級)· 門面登記的收據;其餘沒有來源,照實亮灰。"""
    cell = {}
    p = via / "supportive modules" / "registry" / "VIA_NumberBooks" / "VIA_NumberBook_TST_v0100.jsonl"
    if p.is_file():
        with open(str(p), encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    r = {"gone_since": "壞列"}  # 壞列在「號冊」區塊已點名,這裡不重複計
                if r.get("gone_since"):
                    continue
                cat = str(r.get("cat") or "")
                sysn = "VRN-2" if "VRNCHAIN" in cat else ("VDF" if "VDFCHAIN" in cat else ("VCGC" if r.get("sub") == "VCGC" else "全樹"))
                lvl = {"unit": "單元", "integration": "整合", "system": "系統"}.get(str(r.get("full") or "").rsplit("_", 1)[-1])
                if lvl:
                    c = cell.setdefault((sysn, lvl), {"g": 0, "y": 0, "r": 0, "src": "TST 號冊"})
                    c[LAMP.get(str(r.get("lamp") or "").upper(), "y")] += 1
    for it in contract_items:
        if it["section"] == "收據契約" and it["lamp"] in ("g", "y", "r"):
            c = cell.setdefault((it["system"], "系統"), {"g": 0, "y": 0, "r": 0, "src": "收據契約"})
            c[it["lamp"]] += 1
            c["src"] = "收據契約" if c["src"] == "收據契約" else c["src"] + " + 收據契約"
    wait = {}
    for key, lamp in (expected or {}).items():
        if key in RECEIPT_CELL:
            if lamp == "x":
                wait.setdefault(RECEIPT_CELL[key], []).append(key)
            else:
                c = cell.setdefault(RECEIPT_CELL[key], {"g": 0, "y": 0, "r": 0, "src": "門面收據 " + key})
                c[lamp] += 1
    out = []
    for sysn in SYSTEMS + ["全樹"]:
        for lvl in LEVELS:
            c = cell.get((sysn, lvl))
            if sysn == "全樹" and not c and (sysn, lvl) not in wait:
                continue
            if not c and (sysn, lvl) in wait:
                out.append({"section": "測試分級", "system": sysn, "lamp": "x", "id": "%s|%s" % (sysn, lvl), "title": "%s · %s" % (sysn, lvl),
                            "detail": "沒有收據:門面有登記 %s,這台機器還沒跑" % "、".join(wait[(sysn, lvl)])})
            elif not c:
                out.append({"section": "測試分級", "system": sysn, "lamp": "x", "id": "%s|%s" % (sysn, lvl), "title": "%s · %s" % (sysn, lvl), "detail": "沒有證據:沒有登錄的測試,也沒有收據"})
            else:
                lamp = "r" if c["r"] else ("y" if c["y"] else "g")
                out.append({"section": "測試分級", "system": sysn, "lamp": lamp, "id": "%s|%s" % (sysn, lvl), "title": "%s · %s" % (sysn, lvl),
                            "detail": "綠 %d · 黃 %d · 紅 %d · 來源 %s" % (c["g"], c["y"], c["r"], c["src"])})
    return out


# ---------------- 橋覆蓋(語法樹) ----------------
def _sys_of(rel: str) -> str:
    low = rel.replace("\\", "/")
    for key, name in (("functional modules/VDF", "VDF"), ("functional modules/VRN", "VRN-2"), ("functional modules/VQG", "VQG"), ("functional modules/VAP", "VAP")):
        if low.startswith(key):
            return name
    if low.startswith("supportive modules/registry") and os.path.basename(low).startswith("CGC_"):
        return "VCGC"
    return "SUP" if low.startswith("supportive modules") else "CORE"


def _scan_py(args):
    via, rel = args
    try:
        src = (Path(via) / rel).read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src)
    except (OSError, SyntaxError, ValueError) as e:
        return rel, {"err": type(e).__name__}
    mods = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            mods.add(n.module.split(".")[0])
    return rel, {"accel": "VIA_SuperAccel_Module" in mods, "net": "VIA_NetSupport" in mods, "needs_net": bool(mods & NET_LIBS),
                 "m_accel": "[VIA:ACCEL-BRIDGE" in src, "m_net": "[VIA:NET-BRIDGE" in src}


def tails_py(via: Path):
    best = {}
    for root, dirs, files in os.walk(str(via)):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for fn in files:
            m = VER_RX.search(fn)
            if fn.endswith(".py") and m:
                rel = os.path.relpath(os.path.join(root, fn), str(via)).replace("\\", "/")
                fam = rel[: rel.rfind(m.group(0))]
                if fam not in best or int(m.group(1)) > best[fam][0]:
                    best[fam] = (int(m.group(1)), rel)
    return sorted(r for _, r in best.values())


def sec_bridge(via: Path):
    warnings.filterwarnings("ignore", category=SyntaxWarning)  # 被掃的檔自己的跳脫字元警告不是本引擎的事
    files = tails_py(via)
    if not files:
        return [{"section": "橋覆蓋", "system": "VCGC", "lamp": "x", "id": "橋覆蓋", "title": "加速器橋 / 網路橋", "detail": "找不到帶版號的 .py,沒有證據"}], 0
    have_a = (via / "supportive modules" / "VIA_SuperAccel_Module.py").is_file()
    have_n = (via / "supportive modules" / "VIA_NetSupport.py").is_file()
    per, rows = {}, []
    for rel, f in PRIOR.pmap(_scan_py, [(str(via), r) for r in files]):
        sysn = _sys_of(rel)
        d = per.setdefault(sysn, {"n": 0, "a_ok": 0, "a_mark": 0, "a_none": 0, "net_need": 0, "n_ok": 0, "n_bad": 0, "err": 0})
        d["n"] += 1
        base = {"section": "橋覆蓋", "system": sysn, "title": os.path.basename(rel), "ver": "v" + VER_RX.search(rel).group(1)}
        if "err" in f:
            d["err"] += 1
            rows.append(dict(base, lamp="y", id="語法樹|" + rel, detail="語法樹解析不過(%s),沒辦法判橋" % f["err"]))
            continue
        if f["accel"] and have_a:
            d["a_ok"] += 1
        elif f["m_accel"] or f["accel"]:
            d["a_mark"] += 1
            rows.append(dict(base, lamp="y", id="加速器|" + rel, detail="加速器橋只有標記,沒有真的匯入" if not f["accel"] else "有匯入加速器橋,但橋檔 VIA_SuperAccel_Module.py 不在"))
        else:
            d["a_none"] += 1
            rows.append(dict(base, lamp="y", id="加速器|" + rel, detail="沒掛加速器橋"))
        if f["needs_net"]:
            d["net_need"] += 1
            if f["net"] and have_n:
                d["n_ok"] += 1
            else:
                d["n_bad"] += 1
                rows.append(dict(base, lamp="y", id="網路|" + rel, detail="會出網但網路橋只有標記,沒有真的匯入" if f["m_net"] and not f["net"] else "會出網但沒走網路橋"))
    out = []
    for sysn, d in sorted(per.items()):
        bad = d["a_mark"] + d["a_none"] + d["n_bad"] + d["err"]
        out.append({"section": "橋覆蓋", "system": sysn, "lamp": "y" if bad else "g", "id": "彙總|" + sysn, "title": "%s 橋覆蓋彙總" % sysn,
                    "detail": "彙總(缺的另逐列,各算一項)· 家族尾版 %d · 加速器:生效 %d · 只有標記 %d · 沒掛 %d;會出網 %d:走網路橋 %d · 沒走 %d%s · 靜態判定" % (
                        d["n"], d["a_ok"], d["a_mark"], d["a_none"], d["net_need"], d["n_ok"], d["n_bad"], (" · 解析不過 %d" % d["err"]) if d["err"] else "")})
    return out + rows, len(files)


# ---------------- 環境套件 · 資料庫 · 版本線 · 執行環境 ----------------
def sec_envlib(via: Path):
    p = via / "supportive modules" / "registry" / "VIA_Env_Requirements_v0100.txt"
    if not p.is_file():
        return [{"section": "環境套件", "system": "VCGC", "lamp": "x", "id": "環境套件冊", "title": "VIA_Env_Requirements", "detail": "冊不在,沒有證據"}]
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        name = re.split(r"[<>=!~;\[ ]", line.strip(), maxsplit=1)[0]
        if not name or line.strip().startswith("#"):
            continue
        imp = PIP_IMPORT.get(name.lower(), name.replace("-", "_"))
        try:
            have = importlib.util.find_spec(imp) is not None
        except (ImportError, ValueError):
            have = False
        ver = ""
        if have:
            try:
                import importlib.metadata as _md
                ver = _md.version(name)
            except Exception:
                ver = ""
        out.append({"section": "環境套件", "system": "VCGC", "lamp": "g" if have else "y", "id": name, "title": name, "ver": ver,
                    "detail": "已裝" if have else "這台機器沒裝(核心套件冊有列;由操作員的 boot 自補,AI 不代裝)"})
    return out


def sec_db(via: Path):
    cfg = PRIOR.load_json(via / "supportive modules" / "registry" / "VIA_Config_SSOT_v0100.json") or {}
    db = cfg.get("db") or {}
    if not db:
        return [{"section": "資料庫", "system": "VCGC", "lamp": "x", "id": "資料庫設定", "title": "VIA_Config_SSOT 的 db", "detail": "設定冊不在或沒有 db 節,沒有證據"}]
    out = []
    for key, kind in (("path", "資料庫檔"), ("parquet_root", "Parquet 根夾")):
        v = str(db.get(key) or "")
        base = {"section": "資料庫", "system": "VCGC", "id": "db." + key, "title": "%s(db.%s)" % (kind, key), "ver": str(db.get("kind") or "")}
        p = Path(v) if v else None
        if not v:
            out.append(dict(base, lamp="y", detail="設定冊沒填"))
        elif p.is_file():
            st = p.stat()
            out.append(dict(base, lamp="g", at=_dt.datetime.fromtimestamp(st.st_mtime, _dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), detail="檔在 · %.1f MB(只看檔案系統,沒開庫)" % (st.st_size / 2 ** 20)))
        elif p.is_dir():
            n = size = unread = 0
            for root, _, files in os.walk(str(p)):
                for fn in files:
                    if fn.endswith(".parquet"):
                        n += 1
                        try:
                            size += os.path.getsize(os.path.join(root, fn))
                        except OSError:
                            unread += 1
            out.append(dict(base, lamp="g" if n and not unread else "y", detail="夾在 · parquet %d 檔 · %.1f MB%s(只數檔,沒讀內容)" % (n, size / 2 ** 20, (" · 量不到大小 %d 檔" % unread) if unread else "")))
        else:
            out.append(dict(base, lamp="x", detail="這台機器沒有這個路徑,未量"))
    return out


def sec_git(via: Path):
    def g(*a):
        try:
            r = subprocess.run(["git", "--no-optional-locks", "-C", str(via)] + list(a), capture_output=True, timeout=90)
            return r.stdout.decode("utf-8", "replace").strip() if r.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            return None
    head = g("rev-parse", "--short=9", "HEAD")
    if not head:
        return [{"section": "版本線", "system": "VCGC", "lamp": "x", "id": "版本線", "title": "git", "detail": "讀不到 git,沒有證據"}]
    br, beh, ahd, om = g("rev-parse", "--abbrev-ref", "HEAD"), g("rev-list", "--count", "HEAD..origin/main"), g("rev-list", "--count", "origin/main..HEAD"), g("rev-parse", "--short=9", "origin/main")
    st = g("status", "--porcelain")
    dirty = len(st.splitlines()) if st is not None else None
    lamp = "x" if beh is None else ("y" if int(beh) or (dirty or 0) else "g")
    return [{"section": "版本線", "system": "VCGC", "lamp": lamp, "id": "版本線", "title": "分支 %s" % br, "ver": head,
             "detail": "落後 origin/main %s · 超前 %s · 未提交 %s 檔 · origin/main 記得的是 %s(沒有 fetch)" % (beh if beh is not None else "讀不到", ahd if ahd is not None else "讀不到", dirty if dirty is not None else "讀不到", om or "讀不到")}]


def sec_host():
    win = platform.system() == "Windows"
    box = os.path.exists("/.dockerenv") or bool(os.environ.get("CLAUDE_CODE_REMOTE") or os.environ.get("CODESPACES"))
    return [{"section": "執行環境", "system": "VCGC", "lamp": "g" if win else "x", "id": "執行環境", "title": "這一輪在哪跑", "ver": platform.python_version(),
             "detail": "Windows 主機" if win else "%s%s:系統級的綠不算主機實測" % (platform.system(), "(容器)" if box else "")}]


# ---------------- 管理面覆蓋 ----------------
def sec_coverage(via: Path, items, kinds, expected=None):
    secs = {}
    for it in items:
        secs[it["section"]] = secs.get(it["section"], 0) + 1
    tg = {(it["id"].split("|")[1]): it for it in items if it["section"] == "測試分級"}
    exp = expected or {}
    lv = {l: sum(1 for it in items if it["section"] == "測試分級" and it["id"].endswith("|" + l) and (it["lamp"] != "x" or "門面有登記" in it["detail"])) for l in LEVELS}
    reg = via / "supportive modules" / "registry"
    try:
        prm = [r for r in PRIOR.sec_params(via) if r.get("lamp") != "x"]  # 參數區塊是 v0100 收的,這裡只問它有沒有資料
    except Exception:
        prm = []
    psys = sorted({r.get("sys") for r in prm if r.get("sys")})
    pio = sorted({r.get("sys") for r in prm if re.search(r"輸入|輸出|時間", str(r.get("cls") or ""))})
    les = tail_json(via / "docs" / "handoff" / "ai", "VIA_RC1_LessonRegistry")
    pol = tail_json(reg, "VIA_Policy_Laws_SSOT")
    rows = [("單元測試", lv["單元"], "TST 號冊"), ("整合測試", lv["整合"], "TST 號冊"), ("系統測試", lv["系統"], "TST 號冊 + 收據契約"),
            ("使用者實測", lv["使用者實測"], "門面收據 workbench/ui-usertest(只有全樹一份;各系統自己的使用者實測沒有來源)"),
            ("輸出驗證", lv["輸出驗證"], "門面收據 vdf/macro-crosscheck · vqg/export-vap(VCGC · VRN-2 · VAP 的輸出驗證沒有來源)"),
            ("HTML U/I 同步", lv["U/I 同步"], "門面收據 workbench/responsive · vdf/ui-manifest · vrn2/closeout(VCGC · VQG · VAP 沒有來源)"),
            ("參數", len(prm), "參數區塊有資料的系統:%s;其餘系統沒有參數列管冊" % ("、".join(psys) or "沒有")),
            ("輸入 / 輸出 / 時間範圍", len(pio), "參數冊裡有輸入 / 輸出 / 時間分類的系統:%s;其餘沒有來源" % ("、".join(pio) or "沒有")),
            ("模組 / 引擎", 1, "MDL · ENG 號冊(v0100 已收)"), ("類別 CLS", int("CLS" in kinds), "CLS 號冊"), ("函式 FNC", int("FNC" in kinds), "FNC 號冊"),
            ("函式庫 LIB", int("LIB" in kinds), "LIB 號冊"), ("環境變數 ENV", int("ENV" in kinds), "ENV 號冊"), ("環境套件", secs.get("環境套件", 0), "VIA_Env_Requirements"),
            ("資料庫", sum(1 for it in items if it["section"] == "資料庫" and it["id"].startswith("db.")), "VIA_Config_SSOT 的 db(路徑在不在、大小);表與列數沒有來源(不開庫)"),
            ("需求 / 工作流", int("REQ" in kinds and "WKF" in kinds), "REQ · WKF 號冊"), ("政策", int("PLCY" in kinds), "PLCY 號冊" + (" + " + pol.stem if pol else "")),
            ("衝突", sum(1 for it in items if it["section"] == "衝突登記" and it["lamp"] != "x"), "VIA_RC1_ConflictRegistry"),
            ("收據時效與必填欄", sum(1 for it in items if it["section"] == "收據契約"), "VIA_SystemReceipt_Contract_SSOT"),
            ("加速器橋 / 網路橋生效", sum(1 for it in items if it["section"] == "橋覆蓋" and it["id"].startswith("彙總|")), "語法樹靜態判定;執行時載不載得到要看各系統引擎矩陣的收據"),
            ("版本線", sum(1 for it in items if it["section"] == "版本線" and it["lamp"] != "x"), "git"),
            ("教訓帳", 1 if les else 0, les.stem if les else "沒有來源"),
            ("同義字 / 正則", sum(1 for it in items if it["section"] == "同義字正則" and it["lamp"] != "x"), "同義字聯集 · 正則字典等冊的尾版與筆數;彼此衝不衝突沒有來源"),
            ("備份", int("backup/check" in exp or "backup/manifest" in exp), "門面收據 backup/check · backup/manifest"),
            ("資料內容品質", 0, "沒有來源:擷取後的 datamatrix 結果沒有統一收據;本引擎也不讀資料內容")]
    return [{"section": "管理面覆蓋", "system": "VCGC", "lamp": "g" if n else "x", "id": name, "title": name, "detail": ("有來源 · " if n else "還沒管到 · ") + src} for name, n, src in rows]


def sec_extra(via, tails=None):
    """本版新增的全部區塊(通用項目格式);供 CGC_MDL283 併進卡片與矩陣。"""
    via = Path(via)
    print("[延伸] 號冊 …", flush=True)
    summ, todo, kinds = sec_books(via)
    con = sec_contract(via)
    print("[延伸] 橋覆蓋(語法樹)…", flush=True)
    bridge, nfiles = sec_bridge(via)
    exp_items, exp = sec_expected(via)
    items = summ + todo + sec_conflicts(via) + con + exp_items + sec_testgrid(via, con, exp) + sec_synregex(via) + bridge + sec_envlib(via) + sec_db(via) + sec_git(via) + sec_host()
    items += sec_coverage(via, items, kinds, exp)
    for it in items:
        it.setdefault("ver", "")
        it.setdefault("at", "")
    print("[延伸] 新增 %d 項 · 號冊 %d 類 · 橋覆蓋掃 %d 支尾版" % (len(items), len(kinds), nfiles), flush=True)
    return items


def __getattr__(name):  # 薄尾轉接:v0100 的公開名稱照樣拿得到
    return getattr(PRIOR, name)


def find_via(arg=""):
    if arg and (Path(arg) / "supportive modules" / "registry").is_dir():
        return Path(arg)
    if arg and (Path(arg) / "VeritasIntelligenceAnalytics" / "supportive modules" / "registry").is_dir():
        return Path(arg) / "VeritasIntelligenceAnalytics"
    for up in HERE.parents:
        if (up / "supportive modules" / "registry").is_dir():
            return up
    return None


def selftest() -> int:
    fails = []

    def chk(name, cond, got=None):
        print("  [%s] %s%s" % ("過" if cond else "敗", name, "" if cond else " · 得到 %r" % (got,)), flush=True)
        if not cond:
            fails.append(name)
    chk("v0100 的自測在本版掛上後仍全過", PRIOR.selftest() == 0)
    chk("自己那一頁的黃燈不再另設字色", ".y{background:var(--y)}" in PRIOR.CSS and "color:" not in PRIOR.CSS.split(".y{")[1].split("}")[0])
    tmp = Path(tempfile.mkdtemp(prefix="via_lm101_st_"))
    try:
        via = tmp / "via"
        reg, nb, ai = via / "supportive modules" / "registry", via / "supportive modules" / "registry" / "VIA_NumberBooks", via / "docs" / "handoff" / "ai"
        for d in (nb, ai, via / "functional modules" / "VDF", via / "VIA_Reports" / "vdf"):
            d.mkdir(parents=True)

        def book(name, rows):
            (nb / name).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n壞掉的一列\n", encoding="utf-8")
        book("VIA_NumberBook_REQ_v0100.jsonl", [{"code": "VIA-VDF-REQ001", "sub": "VDF", "name": "需求一", "lamp": "GREEN"}, {"code": "VIA-VDF-REQ002", "sub": "VDF", "name": "需求二", "lamp": "AMBER", "note": "待實測"},
                                                {"code": "VIA-VDF-REQ003", "sub": "VDF", "name": "退役的", "lamp": "RED", "gone_since": "2026-10-01"}])
        book("VIA_NumberBook_PLCY_v0100.jsonl", [{"code": "VIA-CORE-PLCY001", "sub": "CORE", "name": "律一", "lamp": "AMBER"}, {"code": "VIA-CORE-PLCY002", "sub": "CORE", "name": "律二", "lamp": "RED", "note": "壞了"}])
        book("VIA_NumberBook_FM_v0100.jsonl", [{"code": "VIA-VDF-FM-0001", "sub": "VDF", "name": "某檔股票名", "lamp": "RED", "note": "兩源不一"}])
        (nb / "VIA_NumberBook_FNC_VQG_v0100.jsonl").write_text(json.dumps({"code": "VIA-VQG-MDL001-FNC001", "q": "f"}) + "\n", encoding="utf-8")
        book("VIA_NumberBook_MDL_v0100.jsonl", [{"code": "VIA-VCGC-MDL001", "sub": "VCGC", "lamp": "RED"}])
        book("VIA_NumberBook_TST_v0100.jsonl", [{"code": "T1", "sub": "CORE", "full": "x 測一_unit", "cat": "測試/VDFCHAIN_latest.json", "lamp": "GREEN"},
                                                {"code": "T2", "sub": "CORE", "full": "x 測二_integration", "cat": "測試/VRNCHAIN_latest.json", "lamp": "RED", "name": "測二"}])
        summ, todo, kinds = sec_books(via)
        s = {x["id"]: x for x in summ}
        chk("號冊:MDL / ENG 不重收,其餘每類每系統一列", "MDL|VCGC" not in s and {"REQ|VDF", "PLCY|CORE", "FNC|VQG", "TST|CORE"} <= set(s), sorted(s))
        chk("號冊:燈取冊列自己的燈,退役不算,壞列算黃並點名", s["REQ|VDF"]["lamp"] == "y" and "退役 1" in s["REQ|VDF"]["detail"] and "壞列 1" in s["REQ|VDF"]["detail"] and s["PLCY|CORE"]["lamp"] == "r", s["REQ|VDF"]["detail"])
        chk("號冊:沒有燈欄的冊亮灰並說明", s["FNC|VQG"]["lamp"] == "x" and "不評燈" in s["FNC|VQG"]["detail"])
        t = {x["id"]: x for x in todo}
        chk("號冊待辦:REQ 黃列逐列、PLCY 只列紅列、退役紅列不列", set(t) == {"VIA-VDF-REQ002", "VIA-CORE-PLCY002", "T2", "VIA-VDF-FM-0001"}, sorted(t))
        chk("名單類的列只帶編號,不帶名稱", t["VIA-VDF-FM-0001"]["title"] == "VIA-VDF-FM-0001" and "某檔股票名" not in json.dumps(t["VIA-VDF-FM-0001"], ensure_ascii=False) and t["VIA-CORE-PLCY002"]["title"] == "律二")
        (ai / "VIA_RC1_ConflictRegistry_v0100.json").write_text(json.dumps({"entries": [{"id": "CONFLICT-00001", "status": "OPEN", "class": "舊"}]}), encoding="utf-8")
        (ai / "VIA_RC1_ConflictRegistry_v0101.json").write_text(json.dumps({"entries": [
            {"id": "CONFLICT-00001", "status": "FIXED(已修)", "class": "a"}, {"id": "CONFLICT-00002", "status": "OPEN · 待裁", "class": "b", "severity": "HIGH"},
            {"id": "CONFLICT-00003", "status": "CONTAINED(只在審閱夾)", "class": "c"}]}, ensure_ascii=False), encoding="utf-8")
        c = {x["id"]: x for x in sec_conflicts(via)}
        chk("衝突:讀尾版;FIXED 綠 · OPEN 紅且待裁 · CONTAINED 黃", (c["CONFLICT-00001"]["lamp"], c["CONFLICT-00002"]["lamp"], c["CONFLICT-00002"]["needs"], c["CONFLICT-00003"]["lamp"]) == ("g", "r", True, "y"))
        now = _dt.datetime.now(_dt.timezone.utc)
        (reg / "VIA_SystemReceipt_Contract_SSOT_v0100.json").write_text(json.dumps({"stale_hours": 48, "lamp_maps": {"m": {"PASS": "GREEN"}}, "systems": {"VDF": {"receipts": [
            {"id": "health", "path": "VIA_Reports/vdf/H.json", "lamp_key": "lamp", "at_keys": ["ts"], "required": ["lamp", "ts", "summary"], "zh": "健康"},
            {"id": "old", "path": "VIA_Reports/vdf/O.json", "lamp_key": "state", "lamp_map": "m", "at_keys": ["ts"], "required": ["state"], "zh": "舊的"},
            {"id": "none", "path": "VIA_Reports/vdf/N.json", "lamp_key": "lamp", "at_keys": ["ts"], "required": [], "zh": "沒跑"}]}}}), encoding="utf-8")
        (via / "VIA_Reports" / "vdf" / "H.json").write_text(json.dumps({"lamp": "GREEN", "ts": now.isoformat()}), encoding="utf-8")
        (via / "VIA_Reports" / "vdf" / "O.json").write_text(json.dumps({"state": "PASS", "ts": (now - _dt.timedelta(hours=100)).isoformat()}), encoding="utf-8")
        k = {x["id"]: x for x in sec_contract(via)}
        chk("收據契約:缺必填欄降黃 · 過時效降黃(燈經對照表)· 沒收據亮灰", (k["VDF|health"]["lamp"], k["VDF|old"]["lamp"], k["VDF|none"]["lamp"]) == ("y", "y", "x") and "缺必填欄 summary" in k["VDF|health"]["detail"] and "超過時效" in k["VDF|old"]["detail"],
            [(v["lamp"], v["detail"]) for v in k.values()])
        g = {x["id"]: x for x in sec_testgrid(via, list(k.values()))}
        chk("測試分級:五系統 × 六級都有格子,沒來源的亮灰", all("%s|%s" % (a, b) in g for a in SYSTEMS for b in LEVELS) and g["VCGC|使用者實測"]["lamp"] == "x" and "沒有證據" in g["VQG|單元"]["detail"])
        chk("測試分級:有來源的格子照來源給燈", (g["VDF|單元"]["lamp"], g["VRN-2|整合"]["lamp"], g["VDF|系統"]["lamp"]) == ("g", "r", "y"), (g["VDF|單元"], g["VDF|系統"]))
        fm = via / "functional modules" / "VDF"
        (via / "supportive modules" / "VIA_SuperAccel_Module.py").write_text("x = 1\n", encoding="utf-8")
        (fm / "A_v0100.py").write_text("import VIA_SuperAccel_Module\n", encoding="utf-8")
        (fm / "A_v0101.py").write_text("# [VIA:ACCEL-BRIDGE:v0100]\nx = 'import VIA_SuperAccel_Module'\n", encoding="utf-8")  # 尾版:只有標記與字串,沒有真的匯入
        (fm / "B_v0100.py").write_text("try:\n    import VIA_SuperAccel_Module as VIA_ACCEL\nexcept Exception:\n    VIA_ACCEL = None\nimport requests\n", encoding="utf-8")
        (fm / "C_v0100.py").write_text("def broken(:\n", encoding="utf-8")
        (fm / "D_v0100.py").write_text("x = 1\n", encoding="utf-8")
        (fm / "novers.py").write_text("x = 1\n", encoding="utf-8")
        br, n = sec_bridge(via)
        b = {x["id"]: x for x in br}
        chk("橋覆蓋:只掃家族尾版(沒版號的不算)", n == 4, n)
        chk("橋覆蓋:字串裡的 import 不算匯入(語法樹判)、只有標記亮黃", "只有標記" in b["加速器|functional modules/VDF/A_v0101.py"]["detail"])
        chk("橋覆蓋:try 裡的匯入算生效;會出網沒走網路橋點名", "加速器|functional modules/VDF/B_v0100.py" not in b and "沒走網路橋" in b["網路|functional modules/VDF/B_v0100.py"]["detail"])
        chk("橋覆蓋:解析不過與沒掛都逐列,彙總數字對得上", "語法樹|functional modules/VDF/C_v0100.py" in b and "沒掛加速器橋" in b["加速器|functional modules/VDF/D_v0100.py"]["detail"]
            and "家族尾版 4 · 加速器:生效 1 · 只有標記 1 · 沒掛 1;會出網 1:走網路橋 0 · 沒走 1 · 解析不過 1" in b["彙總|VDF"]["detail"], b["彙總|VDF"]["detail"])
        (reg / "CGC_MDL279_MCPServer_v0100.py").write_text('RECEIPTS = {"backup/check": "VIA_Reports/backup/CHECK_latest.json", "vdf/ui-manifest": "VIA_Reports/vdf/H.json", '
                                                            '"workbench/ui-usertest": "VIA_Reports/wb/U.json", "vcgc/feedback": "VIA_Reports/vcgc/FEEDBACK_latest.txt", "vdf/old": "VIA_Reports/vdf/O_latest.json"}\n', encoding="utf-8")
        (via / "VIA_Reports" / "vdf" / "O_latest.json").write_text(json.dumps({"lamp": "GREEN", "ts": (now - _dt.timedelta(hours=100)).isoformat()}), encoding="utf-8")
        xi, xl = sec_expected(via)
        x = {i["id"]: i for i in xi}
        chk("應有收據:該有卻沒有的亮灰、在的綠、過期的黃、自己的回饋檔不列", (xl.get("backup/check"), xl.get("vdf/ui-manifest"), xl.get("vdf/old")) == ("x", "g", "y") and "vcgc/feedback" not in x and "還沒跑" in x["backup/check"]["detail"], xl)
        g2 = {i["id"]: i for i in sec_testgrid(via, [], xl)}
        chk("測試分級吃門面收據:在的給燈,登記了但沒跑的亮灰並點名", g2["VDF|U/I 同步"]["lamp"] == "g" and g2["全樹|使用者實測"]["lamp"] == "x" and "門面有登記 workbench/ui-usertest" in g2["全樹|使用者實測"]["detail"])
        (reg / "VIA_SSOT_SynonymUnion_v0100.json").write_text(json.dumps({"groups": [1, 2, 3], "meta": {"a": 1}}), encoding="utf-8")
        (reg / "VIA_SSOT_RegexDict_v0100.json").write_text("不是 json", encoding="utf-8")
        y = {i["id"]: i for i in sec_synregex(via)}
        chk("同義字正則:在的報筆數、讀不懂紅、不在灰", y["VIA_SSOT_SynonymUnion"]["lamp"] == "g" and "groups 有 3 筆" in y["VIA_SSOT_SynonymUnion"]["detail"] and y["VIA_SSOT_RegexDict"]["lamp"] == "r" and y["VIA_Central_Synonym_Regex"]["lamp"] == "x")
        (reg / "VIA_Env_Requirements_v0100.txt").write_text("# 註解\njson5_no_such_pkg_xyz\npytest>=7\n", encoding="utf-8")
        e = {x["id"]: x for x in sec_envlib(via)}
        chk("環境套件:註解略過、沒裝亮黃並說不代裝", set(e) == {"json5_no_such_pkg_xyz", "pytest"} and e["json5_no_such_pkg_xyz"]["lamp"] == "y" and "不代裝" in e["json5_no_such_pkg_xyz"]["detail"])
        (tmp / "pq").mkdir()
        (tmp / "pq" / "a.parquet").write_bytes(b"0" * 10)
        (reg / "VIA_Config_SSOT_v0100.json").write_text(json.dumps({"db": {"kind": "duckdb", "path": str(tmp / "no.duckdb"), "parquet_root": str(tmp / "pq")}}), encoding="utf-8")
        d = {x["id"]: x for x in sec_db(via)}
        chk("資料庫:路徑不在亮灰寫未量;parquet 只數檔", d["db.path"]["lamp"] == "x" and "未量" in d["db.path"]["detail"] and d["db.parquet_root"]["lamp"] == "g" and "parquet 1 檔" in d["db.parquet_root"]["detail"])
        chk("版本線:不是 git 倉時亮灰不亂猜", sec_git(tmp / "pq")[0]["lamp"] == "x")
        items = sec_extra(via)
        cov = {x["id"]: x for x in items if x["section"] == "管理面覆蓋"}
        chk("管理面覆蓋:有來源綠、沒來源灰並說明", cov["衝突"]["lamp"] == "g" and cov["備份"]["lamp"] == "g" and cov["資料內容品質"]["lamp"] == "x" and "還沒管到" in cov["資料內容品質"]["detail"] and cov["函式 FNC"]["lamp"] == "g" and cov["資料庫"]["lamp"] == "g")
        keys = [(x["section"], x["system"], x["id"]) for x in items]
        chk("新增項目鍵不重複、欄位齊", len(keys) == len(set(keys)) and all({"section", "system", "lamp", "id", "title", "detail", "ver", "at"} <= set(x) for x in items))
        chk("燈只有四種", {x["lamp"] for x in items} <= {"g", "y", "r", "x"})
        src = Path(__file__).read_text(encoding="utf-8")
        chk("本檔沒有色碼、沒有本機家目錄路徑", not re.search(r"#[0-9a-fA-F]{6}\b", src) and not re.search(r"[A-Za-z]:\\\\Users\\\\\w", src))
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)
    print("[selftest] %s · %d 敗 · %s" % ("GREEN" if not fails else "RED", len(fails), ENGINE), flush=True)
    return 0 if not fails else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    verb = a[0] if a and not a[0].startswith("-") else "run"
    if verb == "selftest" or "--selftest" in a:
        return selftest()
    if verb == "version":
        print("%s · %s(薄尾,本體 %s)" % (Path(__file__).name, ENGINE, PRIOR_NAME))
        return 0
    if verb == "extra":
        via = find_via(a[a.index("--root") + 1] if "--root" in a and a.index("--root") + 1 < len(a) else "")
        if via is None:
            print("[紅] 找不到 VIA 夾")
            return 3
        cnt = {}
        for it in sec_extra(via):
            d = cnt.setdefault(it["section"], {"g": 0, "y": 0, "r": 0, "x": 0})
            d[it["lamp"]] += 1
        for s, d in cnt.items():
            print("[區塊] %s:紅 %d · 黃 %d · 綠 %d · 灰 %d" % (s, d["r"], d["y"], d["g"], d["x"]))
        return 0
    rc = PRIOR.main(a)
    if verb == "run":
        print("[延伸偵測] 本版新增的區塊與「管理面覆蓋」在平台頁:via-vcgc run CGC_MDL283_CardMatrixFeedback run", flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
