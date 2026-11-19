#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL149_VeritasCentralGovernanceConsole v0200 — 薄尾(v0199 一字不動):功能一覽分系統卡片(VCGC 可展開 · 同儕只讀自報)+ 同步台認得現行入口

操作員 2026-11-19:「展現的方式可分卡片,VCGC 自己可以展開卡片;VDF VRN VQG VAP VDB(資料庫)」
「VCGC VDF VRN 各自有各自的 system manager 做總控,包含顯示,互不干擾,互相觀察更新狀態」。
清點(同日)量到兩個缺口,本版只補這兩個,其餘動詞一律原樣轉交前版 v0199:
  ① overview:多一區「⑫ 同儕系統自報(只讀)」。照收據契約冊(VIA_SystemReceipt_Contract_SSOT 尾版)列的檔,讀 VDF / VRN-2 / VQG / VAP
     與 VDB(資料庫管理)各自寫出的收據,把它自己報的燈、時間、版本原樣攤開;收據不在就亮灰「還沒自報」,不代判、不代跑、不改對方。
     ②「依系統」的卡片照 VCGC · VDF · VRN-2 · VQG · VAP · VDB 出;③ VCGC 自己的十一區收進可展開的區塊(點 VCGC 那張卡會展開)。
     同儕的燈不算進 VCGC 自己的燈:收據多記 own_content_lamp(只算 VCGC 的列)與 peers(各系統最差的自報燈)。
     各系統自己的顯示由它自己的管理器出(VDF / VRN-2 的 ui · synchronizer);本動詞不替它們做頁。
  ② synchronizer:v0198 把「現行入口」寫成它自己那一支,入口出了新尾版之後,串測矩陣那一頁永遠是黃(「是 v0199 跑的,入口現在是 v0198」)。
     本版在同一行程裡叫 v0198 的同步台,設定裡的入口改成家族此刻的尾版(看檔,不看本檔版號;以後再出新版也不用再改)。
零網路([VIA:NET-BRIDGE] 留名);不碰 TA-Lib;不讀寫同意閘;輸出只寫 VIA_Reports/vcgc。不是 Windows 主機跑的不算主機實測。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本版兩扇門都不出網。"""
    return None if VIA_NET_TOOL_PATH is None else VIA_NET_TOOL_PATH
# ===== [VIA:NET-BRIDGE:END] =====
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

VERSION = "v0200"
FAMILY = "CGC_MDL149_VeritasCentralGovernanceConsole"
TAG = FAMILY + " " + VERSION
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
OWN_FLAG = "VIA_FROM_VCGC"
REP = "VIA_Reports/vcgc/"
CMF_MIN = 106                                        # 卡片矩陣正主 v0106 起項目冊可自帶系統順序與展開區
CONTRACT = "VIA_SystemReceipt_Contract_SSOT"
PEER_SECTION = "⑫ 同儕系統自報(只讀)"
SYS_CARDS = ["VCGC", "VDF", "VRN-2", "VQG", "VAP", "VDB"]
SYS_NAME = {"VRN2": "VRN-2", "VRN": "VRN-2"}
EXPAND = {"system": "VCGC", "label": "VCGC 展開:自己的各區(點一張卡,矩陣只看那一區)", "open": False}
LAMP = {"GREEN": "g", "YELLOW": "y", "AMBER": "y", "RED": "r", "GRAY": "x", "GREY": "x", "G": "g", "Y": "y", "R": "r", "X": "x"}
ZH = {"r": "紅", "y": "黃", "g": "綠", "x": "灰"}


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _prior_path():
    cands = [p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)]
    return max(cands, key=_vnum) if cands else None


def _tail(d: Path, pattern: str):
    hits = [p for p in Path(d).glob(pattern) if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def _env() -> dict:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.setdefault(OWN_FLAG, "YES")                     # 只補本系統自己的入口旗標
    return env


def forward(args: list) -> int:
    """前版其餘功能原樣轉交 v0199(子行程 · rc 不變)。"""
    pp = _prior_path()
    if pp is None:
        print("[%s] ABSENT · 要轉交的檔不在(動詞 %s)" % (TAG, args[:1]))
        return 3
    return subprocess.run([sys.executable, str(pp), *args], env=_env()).returncode


_PRIOR = None


def _prior_module():
    global _PRIOR
    if _PRIOR is None:
        pp = _prior_path()
        if pp is None:
            raise AttributeError("前版不在")
        spec = importlib.util.spec_from_file_location(FAMILY + "_prior_for_" + Path(__file__).stem, pp)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        _PRIOR = mod
    return _PRIOR


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接(要用才載)。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(_prior_module(), name)


# ---------------- ① 同儕自報(只讀收據契約冊列的檔) ----------------
def pv_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None


def pv_first(doc, keys):
    for k in keys or []:
        v = doc.get(k) if isinstance(doc, dict) else None
        if v not in (None, "", [], {}):
            return v
    return None


def pv_lamp(value, spec, maps):
    """對方自己報的值 → 四色。認不得的值亮灰並照寫原值,不猜。"""
    if value is None:
        return "x"
    v = str(value).strip()
    m = (maps or {}).get(spec.get("lamp_map") or "") or {}
    v = m.get(v, m.get(v.upper(), v))
    return LAMP.get(str(v).upper(), "x")


def pv_age_hours(at, now=None):
    s = str(at or "").strip().replace("Z", "+00:00")
    for fmt in (None, "%Y-%m-%d %H:%M:%S", "%Y%m%d_%H%M%S"):
        try:
            import datetime as _dt
            d = _dt.datetime.fromisoformat(s) if fmt is None else _dt.datetime.strptime(s, fmt)
            if d.tzinfo is None:
                d = d.astimezone()                      # 沒帶時區的收據時間當本機時間
            return ((now or _dt.datetime.now(_dt.timezone.utc)) - d).total_seconds() / 3600.0
        except (ValueError, TypeError):
            continue
    return None


def peer_rows(via, now=None):
    """回 (rows, notes)。只讀:契約冊尾版 + 冊上列的收據檔;不執行、不 import、不寫任何系統。"""
    via = Path(via)
    book = _tail(via / "supportive modules" / "registry", CONTRACT + "_v*.json")
    doc = pv_json(book) if book else None
    if not isinstance(doc, dict) or not isinstance(doc.get("systems"), dict):
        return [], ["收據契約冊 %s 讀不到:同儕自報這一區是空的" % CONTRACT]
    maps, stale_h = doc.get("lamp_maps") or {}, doc.get("stale_hours") or 48
    specs = [(k, v) for k, v in doc["systems"].items() if k != "VCGC"] + list((doc.get("observed_only") or {}).items())
    rows, notes = [], []
    for key, sp in specs:
        if not isinstance(sp, dict):
            continue
        name = SYS_NAME.get(key, key)
        ent = sorted(via.glob(sp.get("entry_glob") or "\0")) if sp.get("entry_glob") else []
        ent = [p for p in ent if _vnum(p) >= 0]
        e = max(ent, key=_vnum) if ent else None
        rows.append({"section": PEER_SECTION, "system": name, "lamp": "g" if e else "y", "id": name + ":入口", "title": "%s %s · 入口尾版" % (name, sp.get("zh") or ""),
                     "detail": ("入口檔在(只看檔在不在;健康看它自己報的收據)" if e else "照契約冊的樣式找不到入口檔:%s" % sp.get("entry_glob")),
                     "ver": (re.search(r"v\d{4}", e.stem).group(0) if e else ""), "at": "", "needs": "" if e else "由 %s 這條線確認入口位置;VCGC 只攤開" % name})
        for r in sp.get("receipts") or []:
            p = via / str(r.get("path") or "")
            got = pv_json(p) if p.is_file() else None
            rid, zh = str(r.get("id") or "?"), str(r.get("zh") or "")
            row = {"section": PEER_SECTION, "system": name, "id": "%s:%s" % (name, rid), "title": "%s · %s" % (name, zh or rid), "ver": "", "at": "", "needs": ""}
            if not isinstance(got, dict):
                row.update(lamp="x", detail="還沒自報:這台機器上沒有這份收據(%s)%s" % ("選配" if r.get("optional") else "契約要求", " · " + str(r["note"])[:80] if r.get("note") else ""),
                           needs="" if r.get("optional") else "由 %s 自己的管理器跑出這份收據;VCGC 不代跑、不代寫" % name)
            else:
                raw = got.get(r["lamp_key"]) if r.get("lamp_key") else None
                lamp = pv_lamp(raw, r, maps) if r.get("lamp_key") else "x"
                at = pv_first(got, r.get("at_keys"))
                age = pv_age_hours(at, now)
                old = age is not None and age > float(stale_h)
                miss = [k for k in r.get("required") or [] if k not in got]
                bits = [("自報 %s" % raw) if r.get("lamp_key") else "這份收據不帶燈(只記時間)"]
                if r.get("lamp_key") and lamp == "x" and raw is not None and str(raw).upper() not in LAMP:
                    bits.append("認不得的值,不判")
                if old:
                    bits.append("已 %d 小時沒更新(契約 %s 小時)" % (age, stale_h))
                if miss:
                    bits.append("缺契約欄位 " + "、".join(miss[:4]))
                s = pv_first(got, ["summary", "next", "note"])
                if isinstance(s, str) and s.strip():
                    bits.append(s.strip()[:90])
                row.update(lamp=lamp, detail=" · ".join(bits), at=str(at or ""), ver=str(pv_first(got, r.get("version_keys")) or "")[:40],
                           needs=("由 %s 自己的管理器處理;VCGC 只攤開" % name) if lamp in "ry" else "")
            rows.append(row)
    if not (doc.get("observed_only") or {}).get("VDB"):
        notes.append("契約冊 %s 沒有 VDB(資料庫管理)一節:那張卡是空的" % (book.name if book else CONTRACT))
    return rows, notes


def worst(lamps):
    ls = [l for l in lamps if l in "rygx"]
    return "r" if "r" in ls else "y" if "y" in ls else "g" if "g" in ls else "x"


def overview(args: list, via=None, rep=None) -> int:
    """功能一覽(v0199 的動詞)多一區同儕自報、系統卡片與展開區;做法:同一行程叫 v0199,只在它讀冊與寫檔的兩個點補資料,跑完還原。"""
    P = _prior_module()
    via_p = Path(via) if via else VIA
    keep = {"collect": P.ov_collect, "write": P.ov_write, "ver": P.VERSION, "min": P.CMF_MIN, "sections": list(P.OV_SECTIONS)}
    seen = {"rows": [], "own": "x"}

    def collect(v):
        doc = keep["collect"](v)
        rows, notes = peer_rows(v)
        seen["own"] = worst([it.get("lamp") for it in doc["items"]])
        seen["rows"] = rows
        doc["items"] = list(doc["items"]) + rows
        doc["notes"] = list(doc.get("notes") or []) + notes
        return doc

    def write(path, text):
        path = Path(path)
        if path.name in (P.OV_BOOK, P.OV_RECEIPT):
            try:
                d = json.loads(text)
            except ValueError:
                d = None
            if isinstance(d, dict) and path.name == P.OV_BOOK:
                d.update(systems=list(SYS_CARDS), expand=dict(EXPAND))
                text = json.dumps(d, ensure_ascii=False)
            elif isinstance(d, dict):
                peers = {}
                for r in seen["rows"]:
                    if not r["id"].endswith(":入口"):
                        peers.setdefault(r["system"], []).append(r["lamp"])
                d.update(own_content_lamp=seen["own"], peers={k: worst(v) for k, v in peers.items()}, peer_rule="同儕的燈是它自己報的,不算進 own_content_lamp")
                text = json.dumps(d, ensure_ascii=False, indent=1)
        return keep["write"](path, text)

    P.ov_collect, P.ov_write, P.VERSION, P.CMF_MIN = collect, write, VERSION, CMF_MIN
    if PEER_SECTION not in P.OV_SECTIONS:
        P.OV_SECTIONS.append(PEER_SECTION)
    try:
        return P.overview(args, via=via_p, rep=rep)
    finally:
        P.ov_collect, P.ov_write, P.VERSION, P.CMF_MIN = keep["collect"], keep["write"], keep["ver"], keep["min"]
        P.OV_SECTIONS[:] = keep["sections"]


# ---------------- ② 同步台:現行入口 = 家族此刻的尾版 ----------------
def sync_owner():
    """沿前版鏈找定義同步台的那一支(v0198)。"""
    m, hops = _prior_module(), 0
    while m is not None and hops < 12:
        if callable(m.__dict__.get("sy_command")) and callable(m.__dict__.get("config")):
            return m
        nxt = m.__dict__.get("_prior_module")
        m, hops = (nxt() if callable(nxt) else None), hops + 1
    return None


def sync_config(owner) -> dict:
    tail = _tail(HERE, FAMILY + "_v*.py") or Path(__file__)
    ver = re.search(r"v\d{4}$", tail.stem).group(0)
    return dict(owner.config(), engine=tail.stem, version=ver, tag=FAMILY + " " + ver)


def synchronizer(args: list) -> int:
    owner = sync_owner()
    if owner is None:
        return forward(["synchronizer", *args])
    return owner.sy_command(sync_config(owner), args)


def help_extra() -> None:
    print("  ── v0200 overview 分系統卡片(VCGC 可展開 · 同儕只讀自報)· synchronizer 認得現行入口 ──")
    print("  overview [--no-open] [--json]   ② 系統卡 %s · ③ VCGC 自己的各區可展開 · ⑫ 同儕自報照收據契約冊讀(不代判 · 不代跑)" % " · ".join(SYS_CARDS))
    print("  synchronizer […]                同 v0198;「現行入口」改看家族此刻的尾版")


def selftest() -> int:
    import datetime as _dt
    import shutil
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("=== %s 自測(薄尾 · overview 同儕與系統卡 + synchronizer 入口;夾具 · 零網路 · 真樹只讀)===" % TAG, flush=True)
    pp = _prior_path()
    chk("① 前版 v0199 在且是本家族上一版", pp is not None and _vnum(pp) == _vnum(__file__) - 1, pp.name if pp else None)
    cp = subprocess.run([sys.executable, str(pp), "version"], env=_env(), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    chk("② 其餘動詞原樣轉交(version → 前版鏈 rc 0)", cp.returncode == 0, (cp.stdout.strip().splitlines() or ["?"])[-1][:80])
    tmp = Path(tempfile.mkdtemp(prefix="via_console200_"))
    try:
        reg = tmp / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        now = _dt.datetime(2026, 11, 19, 6, 0, 0, tzinfo=_dt.timezone.utc)
        (tmp / "fm").mkdir()
        (tmp / "fm" / "A_Manager_v0003.py").write_text("", encoding="utf-8")
        contract = {"stale_hours": 48, "lamp_maps": {"m": {"PASS": "GREEN", "OPEN": "RED"}}, "systems": {
            "VCGC": {"zh": "自己", "receipts": [{"id": "x", "path": "r/own.json", "lamp_key": "lamp"}]},
            "AAA": {"zh": "甲", "entry_glob": "fm/A_Manager_v*.py", "receipts": [
                {"id": "ok", "path": "r/a_ok.json", "lamp_key": "lamp", "at_keys": ["at"], "version_keys": ["version"], "required": ["lamp", "at"], "zh": "健康"},
                {"id": "map", "path": "r/a_map.json", "lamp_key": "state", "lamp_map": "m", "at_keys": ["ts"], "required": ["state", "per"], "zh": "收尾"},
                {"id": "none", "path": "r/a_none.json", "lamp_key": "lamp", "zh": "沒跑過"},
                {"id": "opt", "path": "r/a_opt.json", "lamp_key": "lamp", "optional": True, "zh": "選配"}]},
            "VRN2": {"zh": "乙", "entry_glob": "fm/Nope_v*.py", "receipts": [{"id": "odd", "path": "r/b_odd.json", "lamp_key": "lamp", "at_keys": ["at"], "zh": "怪值"}]}},
            "observed_only": {"VDB": {"zh": "資料庫", "receipts": [{"id": "cat", "path": "r/cat.json", "lamp_key": None, "at_keys": ["ts"], "zh": "目錄"}]}}}
        (reg / (CONTRACT + "_v0009.json")).write_text(json.dumps(contract, ensure_ascii=False), encoding="utf-8")
        (tmp / "r").mkdir()
        (tmp / "r" / "a_ok.json").write_text(json.dumps({"lamp": "GREEN", "at": "2026-11-19T05:00:00Z", "version": "v0003", "summary": "都好"}), encoding="utf-8")
        (tmp / "r" / "a_map.json").write_text(json.dumps({"state": "OPEN", "ts": "2026-11-10T05:00:00Z"}), encoding="utf-8")
        (tmp / "r" / "b_odd.json").write_text(json.dumps({"lamp": "PURPLE", "at": "2026-11-19T05:30:00Z"}), encoding="utf-8")
        (tmp / "r" / "cat.json").write_text(json.dumps({"ts": "2026-11-19T05:30:00Z"}), encoding="utf-8")
        rows, notes = peer_rows(tmp, now)
        by = {r["id"]: r for r in rows}
        chk("③ 同儕列只來自契約冊:不含 VCGC 自己;每個系統一列入口 + 每份收據一列;系統名照對外寫法(VRN2 → VRN-2)",
            sorted(by) == sorted(["AAA:入口", "AAA:ok", "AAA:map", "AAA:none", "AAA:opt", "VRN-2:入口", "VRN-2:odd", "VDB:入口", "VDB:cat"]) and not notes, (sorted(by), notes))
        chk("④ 燈是對方自己報的:GREEN → 綠;經對照表 OPEN → 紅;認不得的值亮灰並照寫;不帶燈的收據亮灰",
            by["AAA:ok"]["lamp"] == "g" and by["AAA:map"]["lamp"] == "r" and by["VRN-2:odd"]["lamp"] == "x" and "PURPLE" in by["VRN-2:odd"]["detail"] and "認不得" in by["VRN-2:odd"]["detail"]
            and by["VDB:cat"]["lamp"] == "x" and "不帶燈" in by["VDB:cat"]["detail"], {k: (v["lamp"], v["detail"]) for k, v in by.items()})
        chk("⑤ 收據不在 → 灰「還沒自報」(契約要求的寫去向,選配的不寫);過期與缺欄位只加註、不改它報的燈",
            by["AAA:none"]["lamp"] == "x" and "還沒自報" in by["AAA:none"]["detail"] and by["AAA:none"]["needs"] and by["AAA:opt"]["needs"] == ""
            and "沒更新" in by["AAA:map"]["detail"] and "缺契約欄位 per" in by["AAA:map"]["detail"] and by["AAA:map"]["lamp"] == "r" and "沒更新" not in by["AAA:ok"]["detail"])
        chk("⑥ 入口列只看檔在不在:在 → 綠帶版號;找不到 → 黃;紅黃列都寫「由該系統處理」", by["AAA:入口"]["lamp"] == "g" and by["AAA:入口"]["ver"] == "v0003" and by["VRN-2:入口"]["lamp"] == "y"
            and all("VCGC 只攤開" in r["needs"] or "VCGC 不代跑" in r["needs"] for r in rows if r["lamp"] in "ry"))
        before = sorted(str(p.relative_to(tmp)) for p in tmp.rglob("*"))
        empty = Path(tempfile.mkdtemp(prefix="via_console200_e_"))
        r0, n0 = peer_rows(empty)
        shutil.rmtree(str(empty), ignore_errors=True)
        chk("⑦ 契約冊不在:不炸、不編列,只留一句說明;讀同儕不寫任何檔", r0 == [] and len(n0) == 1 and before == sorted(str(p.relative_to(tmp)) for p in tmp.rglob("*")), n0)
        P = _prior_module()
        snap = (P.ov_collect, P.ov_write, P.VERSION, P.CMF_MIN, list(P.OV_SECTIONS))
        rep = tmp / "rep"
        with open(os.devnull, "w", encoding="utf-8") as nul:
            keep_out, sys.stdout = sys.stdout, nul
            try:
                rc = overview(["--no-open"], via=VIA, rep=rep)
            finally:
                sys.stdout = keep_out
        book = pv_json(rep / "overview" / P.OV_BOOK) or {}
        rec = pv_json(rep / P.OV_RECEIPT) or {}
        page = (rep / P.OV_PAGE).read_text(encoding="utf-8") if (rep / P.OV_PAGE).is_file() else ""
        peers = [it for it in book.get("items") or [] if it.get("section") == PEER_SECTION]
        chk("⑧ 真樹(只讀)出頁到暫存夾:rc 0 · 項目冊帶系統順序與展開區 · 同儕區有 VDF / VRN-2 / VQG / VAP / VDB · VCGC 的列一列不少",
            rc == 0 and book.get("systems") == SYS_CARDS and (book.get("expand") or {}).get("system") == "VCGC" and {"VDF", "VRN-2", "VQG", "VAP", "VDB"} <= {p["system"] for p in peers}
            and len(book.get("items") or []) - len(peers) >= 1000 and all(it.get("system") == "VCGC" for it in book["items"] if it.get("section") != PEER_SECTION),
            (rc, book.get("systems"), sorted({p["system"] for p in peers}), len(book.get("items") or [])))
        chk("⑨ 頁面:系統卡有 VDB · VCGC 的各區在可展開區 · 群組卡有同儕那一區", 'data-kind="sys" data-key="VDB"' in page and 'id="xp" data-sys="VCGC"' in page and PEER_SECTION in page)
        chk("⑩ 收據:版本是本版 · 多記 own_content_lamp 與 peers(同儕的燈不混進自己的)· 頁燈綠",
            rec.get("version") == VERSION and rec.get("engine") == FAMILY + "_" + VERSION and rec.get("lamp") == "g" and rec.get("own_content_lamp") in "rygx"
            and set(rec.get("peers") or {}) >= {"VDF", "VRN-2", "VQG", "VAP", "VDB"}, {k: rec.get(k) for k in ("version", "engine", "lamp", "own_content_lamp", "peers")})
        chk("⑪ 跑完還原 v0199 模組(讀冊點 · 寫檔點 · 版本 · 區塊表);沒留下暫存檔",
            (P.ov_collect, P.ov_write, P.VERSION, P.CMF_MIN, list(P.OV_SECTIONS)) == snap and not list(rep.rglob("*.tmp")))
        owner = sync_owner()
        cfg = sync_config(owner) if owner else {}
        tail = _tail(HERE, FAMILY + "_v*.py")
        chk("⑫ 同步台設定:找得到定義它的那一支;現行入口 = 家族此刻的尾版(不是定義它的那一支);其餘設定不動",
            owner is not None and cfg.get("engine") == tail.stem and cfg.get("version") == re.search(r"v\d{4}$", tail.stem).group(0) and _vnum(tail) >= _vnum(__file__)
            and cfg.get("engine") != owner.config()["engine"] and {k: v for k, v in cfg.items() if k not in ("engine", "version", "tag", "env", "locker")}
            == {k: v for k, v in owner.config().items() if k not in ("engine", "version", "tag", "env", "locker")}, (cfg.get("engine"), cfg.get("version")))
        fx = tmp / "fx"
        (fx / "rep").mkdir(parents=True)
        spec = {"id": "test", "name": "串測矩陣", "page": "rep/T.html", "receipt": "rep/T.json", "step": None, "time": "at", "lamp": "lamp", "ver": "console", "tail_key": "console", "by": "test"}
        at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        (fx / "rep" / "T.json").write_text(json.dumps({"lamp": "GREEN", "at": at, "console": cfg.get("engine", "") + ".py"}), encoding="utf-8")
        (fx / "rep" / "T.html").write_text("<html>%s 綠 GREEN %s</html>" % (at, cfg.get("version", "")), encoding="utf-8")
        try:
            new = owner.sy_pair_check(spec, fx, tail=cfg["engine"], version=cfg["version"])
            old = owner.sy_pair_check(spec, fx, tail=owner.config()["engine"], version=owner.config()["version"])
            chk("⑬ 同一份串測收據(現行入口跑的):照本版的設定不再報「入口現在是 …」;照 v0198 原設定會報(缺口重現)",
                "入口現在是" not in new.get("note", "") and "入口現在是" in old.get("note", ""), (new.get("note"), old.get("note")))
        except Exception as e:
            chk("⑬ 同一份串測收據(現行入口跑的):照本版的設定不再報「入口現在是 …」", False, "%s: %s" % (type(e).__name__, e))
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)
    seen = []
    real = globals()["forward"]
    globals()["forward"] = lambda x: seen.append(list(x)) or 0
    try:
        m1 = main(["status"])
        m2 = main(["monitor", "status", "--last"])
        with open(os.devnull, "w", encoding="utf-8") as nul:
            keep_out, sys.stdout = sys.stdout, nul
            try:
                m3 = main(["synchronizer", "manifest"])
            finally:
                sys.stdout = keep_out
    finally:
        globals()["forward"] = real
    chk("⑭ 只有 overview 與 synchronizer 留在本版;其餘動詞原樣轉交前版", seen == [["status"], ["monitor", "status", "--last"]] and m1 == 0 and m2 == 0 and m3 == 0, (seen, m3))
    names = [n for n in dir(_prior_module()) if not n.startswith("_") and callable(getattr(_prior_module(), n, None))]
    chk("⑮ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), "%d 支" % len(names))
    src = Path(__file__).read_text(encoding="utf-8")
    live = src.split("def selftest")[0]
    chk("⑯ 零網路 · 不用 TA-Lib · 不 import 他系統 · 不寫同意閘 · 本版自己不寫檔(寫檔只經 v0199 的 ov_write)· 本檔沒有色碼",
        not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib|socket|VDF_|VRN_|VQG_|VAP_)", src, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src)
        and ".write_text(" not in live and "open(" not in live and not re.search(r"#[0-9a-fA-F]{6}\b", live))
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", TAG, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("--selftest", "selftest") and "--legacy" not in args:
        return selftest()
    if args[:1] == ["overview"]:
        return overview(args[1:])
    if args[:1] == ["synchronizer"]:
        return synchronizer(args[1:])
    if not args or args[0] == "help":
        rc = forward(args or ["help"])
        help_extra()
        return rc
    return forward(args)


if __name__ == "__main__":
    sys.exit(main())
