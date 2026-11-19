#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL149_VeritasCentralGovernanceConsole v0201 — 薄尾(v0200 一字不動):每個系統一句話 · VDB 引用既有畫面 · 管理器六面補三區

操作員 2026-11-19:「顯示系統狀況每個系統一個資訊,透過 SYSTEM MANAGER 彙總,全部再由 VCGC 看全部」「(VDB)好,善用 VCGC 的顯示畫面引用」
「SDD 整個系統架構做到掌握 system manager 就掌握整個系統:參數、引擎、功能、工具、輸入輸出、合約介面」。
本版只在 overview 上補資料,其餘動詞(含 synchronizer)一律原樣轉交前版 v0200;做法同 v0200:同一行程叫前版,只在讀冊與寫檔的點補,跑完還原。
  ① 每個系統一句話:收據契約冊(v0105 起)每個系統指定一份由它自己的管理器彙總的收據(summary)。本版只讀那一份,
     把它自己報的燈 · 內容燈 · 時間 · 版本寫在 ② 那個系統的卡片上;沒有彙總收據的系統亮灰「管理器還沒有彙總收據」。
     VCGC 自己那張照自己的列算,不拿別人的燈。細項仍在 ⑫ 同儕自報。
  ② VDB 的畫面引用 VCGC 既有的頁:契約冊 VDB 一節的 pages,頁在不在、檔案時間;不另做頁。
  ③ 管理器六面補三區(都讀既有的冊與收據,不另做引擎、不執行任何東西):
     ⑬ 參數冊:中央參數索引冊(VIA_Central_Params_SSOT)列的每一本——檔在不在、內容雜湊對不對、鎖定正則對齊、衝突數。
     ⑭ 介面契約:VIA_SystemInterface_Contract_SSOT 的每一條(IFC 號 · 狀態 · 提供方 → 使用方 · 輸入 · 輸出)。
     ⑮ VCGC 自己的收據:契約冊 VCGC 一節(串測 · 系統卡 · 現況 · 同步台 · 功能一覽 · SDD · 工具覆蓋 · 環境)各自報的燈與時間。
零網路([VIA:NET-BRIDGE] 留名);不碰 TA-Lib;不讀寫同意閘;本版自己不寫檔。不是 Windows 主機跑的不算主機實測。
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
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

VERSION = "v0201"
FAMILY = "CGC_MDL149_VeritasCentralGovernanceConsole"
TAG = FAMILY + " " + VERSION
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
OWN_FLAG = "VIA_FROM_VCGC"
CMF_MIN = 107                                        # 卡片矩陣正主 v0107 起系統卡片可寫上那個系統的一句話
SEC_PARAM, SEC_IFC, SEC_OWN = "⑬ 參數冊", "⑭ 介面契約", "⑮ VCGC 自己的收據"
PARAM_BOOK, IFC_BOOK = "VIA_Central_Params_SSOT", "VIA_SystemInterface_Contract_SSOT"
NO_SUMMARY = "管理器還沒有彙總收據"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _prior_path():
    cands = [p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)]
    return max(cands, key=_vnum) if cands else None


def _env() -> dict:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.setdefault(OWN_FLAG, "YES")                     # 只補本系統自己的入口旗標
    return env


def forward(args: list) -> int:
    """前版其餘功能原樣轉交 v0200(子行程 · rc 不變)。"""
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


def _row(section, system, lamp, rid, title, detail, ver="", at="", needs=""):
    return {"section": section, "system": system, "lamp": lamp, "id": rid, "title": title, "detail": detail, "ver": ver, "at": at, "needs": needs}


def _sha_ok(path: Path, want: str) -> bool:
    """內容雜湊對得上(原樣 / 行尾換成 LF / 行尾換成 CRLF 任一相同都算;冊是在 Windows 上記的)。"""
    try:
        raw = path.read_bytes()
    except OSError:
        return False
    lf = raw.replace(b"\r\n", b"\n")
    return str(want).lower() in {hashlib.sha256(x).hexdigest() for x in (raw, lf, lf.replace(b"\n", b"\r\n"))}


def _mtime(p: Path) -> str:
    try:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(p.stat().st_mtime))
    except OSError:
        return ""


# ---------------- ③ 管理器六面補三區(只讀) ----------------
def param_rows(via):
    """⑬ 參數冊:中央參數索引冊列的每一本。回 (rows, notes)。"""
    P = _prior_module()
    via = Path(via)
    book = P._tail(via / "supportive modules" / "registry", PARAM_BOOK + "_v*.json")
    doc = P.pv_json(book) if book else None
    if not isinstance(doc, dict) or not isinstance(doc.get("books"), list):
        return [], ["參數索引冊 %s 讀不到:參數冊這一區是空的" % PARAM_BOOK]
    ver, at, rows = (re.search(r"v\d{4}", book.stem) or [""])[0] if re.search(r"v\d{4}", book.stem) else "", str(doc.get("generated") or ""), []
    n_conf = len(doc.get("conflicts") or [])
    rows.append(_row(SEC_PARAM, "VCGC", "r" if n_conf else "g", "PARAM:索引冊", "中央參數索引冊 %s" % book.name,
                     "列管 %d 本 · 葉節點 %s · 衝突 %d(索引產生於 %s;之後的變動看下面各列)" % (len(doc["books"]), doc.get("leaf_total", "?"), n_conf, at or "?"), ver, at,
                     "衝突由操作員與 AI 解掉後再發號" if n_conf else ""))
    for b in doc["books"]:
        if not isinstance(b, dict) or not b.get("path"):
            continue
        p = via / str(b["path"])
        bid = str(b.get("id") or Path(str(b["path"])).stem)
        if not p.is_file():
            lamp, det, needs = "r", "索引冊列的檔不在:%s" % b["path"], "確認是搬走還是改名;索引冊要出新版"
        elif b.get("sha256") and not _sha_ok(p, b["sha256"]):
            lamp, det, needs = "y", "檔在,內容和索引冊記的不一樣(索引產生之後改過)", "參數索引冊重新產生一版"
        else:
            lamp, det, needs = "g", "檔在 · 內容與索引冊相同" if b.get("sha256") else "檔在(索引冊沒記雜湊)", ""
        rows.append(_row(SEC_PARAM, "VCGC", lamp, "PARAM:" + bid, "%s · %s" % (bid, b.get("domain") or ""), det + ((" · " + str(b["note"])[:60]) if b.get("note") else ""),
                         (re.search(r"v\d{3,4}", p.stem) or [""])[0] if re.search(r"v\d{3,4}", p.stem) else "", "", needs))
    for a in doc.get("locked_alignment") or []:
        if isinstance(a, dict) and a.get("name"):
            ok = str(a.get("state") or "").upper() == "ALIGNED" and not a.get("drift")
            rows.append(_row(SEC_PARAM, "VCGC", "g" if ok else "r", "LOCK:" + str(a["name"]), "鎖定正則 · %s" % a["name"],
                             "對齊" if ok else "不對齊:%s · 漂移 %d 處" % (a.get("state"), len(a.get("drift") or [])), "", at, "" if ok else "漂移由操作員與 AI 解掉"))
    return rows, []


def ifc_rows(via):
    """⑭ 介面契約:系統介面契約冊的每一條。回 (rows, notes)。"""
    P = _prior_module()
    via = Path(via)
    book = P._tail(via / "supportive modules" / "registry", IFC_BOOK + "_v*.json")
    doc = P.pv_json(book) if book else None
    if not isinstance(doc, dict) or not isinstance(doc.get("contracts"), list):
        return [], ["介面契約冊 %s 讀不到:介面契約這一區是空的" % IFC_BOOK]
    lamp_of = {"ACTIVE": "g", "DEPRECATED": "y", "SUNSET": "y", "DRAFT": "y", "CANDIDATE": "y", "TERMINATED": "x"}
    rows = []
    for c in doc["contracts"]:
        if not isinstance(c, dict):
            continue
        cid = str(c.get("ifc_id") or c.get("cand") or "?")
        st = str(c.get("state") or "").upper()
        lamp = lamp_of.get(st, "x") if c.get("ifc_id") else "y"
        who = lambda v: "、".join(v) if isinstance(v, list) else str(v or "?")
        rows.append(_row(SEC_IFC, "VCGC", lamp, cid, "%s · %s" % (cid, str(c.get("title") or "")[:60]),
                         "%s · %s → %s · 入:%s · 出:%s" % (st or "沒寫狀態", who(c.get("provider")), who(c.get("consumer")), str(c.get("INPUT") or "?")[:50], str(c.get("OUTPUT") or "?")[:60])
                         + ("" if c.get("ifc_id") else " · 還沒有 IFC 號"), str(c.get("version") or ""), str(doc.get("ts") or ""),
                         "" if lamp == "g" else ("還沒發號:欄位與驗證全過、無衝突後由 VCGC 發" if not c.get("ifc_id") else "照契約生命週期處理(棄用 / 落日 / 終止)")))
    for t in doc.get("tombstones") or []:
        if isinstance(t, dict):
            rows.append(_row(SEC_IFC, "VCGC", "x", str(t.get("ifc_id") or "?") + ":墓碑", "%s · 已終止(號不重用)" % (t.get("ifc_id") or "?"), str(t.get("why") or t.get("note") or "")[:100], "", str(t.get("at") or "")))
    return rows, []


def contract_doc(via):
    P = _prior_module()
    book = P._tail(Path(via) / "supportive modules" / "registry", P.CONTRACT + "_v*.json")
    doc = P.pv_json(book) if book else None
    return doc if isinstance(doc, dict) and isinstance(doc.get("systems"), dict) else None


def receipt_row(via, sysname, r, maps, stale_h, section, owner_note, now=None):
    """照契約冊的一份收據規格讀一份收據,回一列(做法同 v0200 的同儕列;燈是那份收據自己報的)。"""
    P = _prior_module()
    p = Path(via) / str(r.get("path") or "")
    got = P.pv_json(p) if p.is_file() else None
    rid, zh = str(r.get("id") or "?"), str(r.get("zh") or "")
    row = _row(section, sysname, "x", "%s:%s" % (sysname, rid), "%s · %s" % (sysname, zh or rid), "")
    if not isinstance(got, dict):
        row.update(detail="還沒有這份收據(%s)" % ("選配" if r.get("optional") else "契約要求"), needs="" if r.get("optional") else owner_note)
        return row, None
    raw = got.get(r["lamp_key"]) if r.get("lamp_key") else None
    lamp = P.pv_lamp(raw, r, maps) if r.get("lamp_key") else "x"
    at = P.pv_first(got, r.get("at_keys"))
    age = P.pv_age_hours(at, now)
    bits = [("自報 %s" % raw) if r.get("lamp_key") else "這份收據不帶燈(只記時間)"]
    if age is not None and age > float(stale_h):
        bits.append("已 %d 小時沒更新(契約 %s 小時)" % (age, stale_h))
    miss = [k for k in r.get("required") or [] if k not in got]
    if miss:
        bits.append("缺契約欄位 " + "、".join(miss[:4]))
    s = P.pv_first(got, ["summary", "next"])
    if isinstance(s, str) and s.strip():
        bits.append(s.strip()[:90])
    row.update(lamp=lamp, detail=" · ".join(bits), at=str(at or ""), ver=str(P.pv_first(got, r.get("version_keys")) or "")[:60], needs=owner_note if lamp in "ry" else "")
    return row, got


def own_receipt_rows(via, now=None):
    """⑮ VCGC 自己的收據:契約冊 VCGC 一節。回 (rows, notes)。"""
    doc = contract_doc(via)
    if doc is None or not isinstance(doc["systems"].get("VCGC"), dict):
        return [], ["收據契約冊讀不到 VCGC 一節:自己的收據這一區是空的"]
    rows = [receipt_row(via, "VCGC", r, doc.get("lamp_maps") or {}, doc.get("stale_hours") or 48, SEC_OWN, "VCGC 這條線處理(跑對應的動詞就有這份收據)", now)[0]
            for r in doc["systems"]["VCGC"].get("receipts") or [] if isinstance(r, dict)]
    return rows, []


# ---------------- ① 每個系統一句話 · ② VDB 引用既有畫面 ----------------
def system_info(via, now=None):
    """回 ({系統: {lamp, note}}, 頁面列)。只讀契約冊指定的那一份彙總收據;VCGC 自己不在內。"""
    P = _prior_module()
    doc = contract_doc(via)
    if doc is None:
        return {}, []
    maps, stale_h, info, pages = doc.get("lamp_maps") or {}, doc.get("stale_hours") or 48, {}, []
    for key, sp in doc["systems"].items():
        if key == "VCGC" or not isinstance(sp, dict):
            continue
        name = P.SYS_NAME.get(key, key)
        spec = next((r for r in sp.get("receipts") or [] if isinstance(r, dict) and r.get("id") == sp.get("summary")), None) if sp.get("summary") else None
        if spec is None:
            info[name] = {"lamp": "x", "note": NO_SUMMARY}
        else:
            row, got = receipt_row(via, name, spec, maps, stale_h, P.PEER_SECTION, "", now)
            if got is None:
                info[name] = {"lamp": "x", "note": "管理器的彙總收據這台機器上沒有"}
            else:
                cl = got.get("content_lamp")
                when = str(got.get("local") or row["at"])[:16]
                info[name] = {"lamp": row["lamp"], "note": "管理器自報 %s%s · %s · %s" % (P.ZH.get(row["lamp"], "灰"), (" · 內容 %s" % P.ZH.get(P.pv_lamp(cl, {}, maps), "灰")) if cl else "", when, row["ver"][-5:] or "?")}
        for pg in sp.get("pages") or []:
            if isinstance(pg, dict) and pg.get("path"):
                p = Path(via) / str(pg["path"])
                pages.append(_row(P.PEER_SECTION, name, "g" if p.is_file() else "x", "%s:頁:%s" % (name, pg.get("id") or "?"), "%s · %s" % (name, pg.get("zh") or "頁"),
                                  ("頁在(引用既有畫面,不另做):%s" % pg["path"]) if p.is_file() else ("這台機器上還沒有這張頁:%s" % pg["path"]), "", _mtime(p) if p.is_file() else ""))
    return info, pages


def overview(args: list, via=None, rep=None) -> int:
    """功能一覽:在 v0200 之上補三區、每個系統一句話、VDB 的頁。同一行程叫 v0200(它再叫 v0199),只在讀冊與寫檔的點補,跑完還原。"""
    P = _prior_module()                    # v0200
    Q = P._prior_module()                  # v0199
    via_p = Path(via) if via else VIA
    keep = {"collect": Q.ov_collect, "write": Q.ov_write, "sections": list(Q.OV_SECTIONS), "peer": P.peer_rows, "pver": P.VERSION, "pmin": P.CMF_MIN}
    seen = {"info": {}}

    def collect(v):
        doc = keep["collect"](v)
        extra, notes = [], []
        for fn in (param_rows, ifc_rows, own_receipt_rows):
            rows, ns = fn(v)
            extra += rows
            notes += ns
        doc["items"] = list(doc["items"]) + extra
        doc["notes"] = list(doc.get("notes") or []) + notes
        return doc

    def peer(v, now=None):
        rows, notes = keep["peer"](v, now)
        info, pages = system_info(v, now)
        seen["info"] = info
        doc = contract_doc(v) or {}
        if "VDB" in (doc.get("systems") or {}):
            notes = [n for n in notes if "沒有 VDB" not in n]
        return rows + pages, notes

    def write(path, text):
        path = Path(path)
        if path.name in (Q.OV_BOOK, Q.OV_RECEIPT):
            try:
                d = json.loads(text)
            except ValueError:
                d = None
            if isinstance(d, dict) and path.name == Q.OV_BOOK:
                d["sys_info"] = dict(seen["info"])
                text = json.dumps(d, ensure_ascii=False)
            elif isinstance(d, dict):
                d["system_info"] = dict(seen["info"])
                d["system_info_rule"] = "每個系統一句話 = 它自己的管理器彙總的那一份收據(收據契約冊 summary);VCGC 只讀"
                text = json.dumps(d, ensure_ascii=False, indent=1)
        return keep["write"](path, text)

    Q.ov_collect, Q.ov_write, P.peer_rows, P.VERSION, P.CMF_MIN = collect, write, peer, VERSION, CMF_MIN
    Q.OV_SECTIONS[:] = keep["sections"] + [P.PEER_SECTION, SEC_PARAM, SEC_IFC, SEC_OWN]
    try:
        return P.overview(args, via=via_p, rep=rep)
    finally:
        Q.ov_collect, Q.ov_write, P.peer_rows, P.VERSION, P.CMF_MIN = keep["collect"], keep["write"], keep["peer"], keep["pver"], keep["pmin"]
        Q.OV_SECTIONS[:] = keep["sections"]


def help_extra() -> None:
    print("  ── v0201 overview:每個系統一句話(管理器彙總)· VDB 引用既有畫面 · 管理器六面補三區 ──")
    print("  overview [--no-open] [--json]   ② 系統卡寫上各系統管理器自報的那一句 · %s · %s · %s" % (SEC_PARAM, SEC_IFC, SEC_OWN))


def selftest() -> int:
    import datetime as _dt
    import shutil
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("=== %s 自測(薄尾 · overview 補三區 + 每個系統一句話;夾具 · 零網路 · 真樹只讀)===" % TAG, flush=True)
    pp = _prior_path()
    chk("① 前版 v0200 在且是本家族上一版", pp is not None and _vnum(pp) == _vnum(__file__) - 1, pp.name if pp else None)
    cp = subprocess.run([sys.executable, str(pp), "version"], env=_env(), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    chk("② 其餘動詞原樣轉交(version → 前版鏈 rc 0)", cp.returncode == 0, (cp.stdout.strip().splitlines() or ["?"])[-1][:80])
    P = _prior_module()
    Q = P._prior_module()
    tmp = Path(tempfile.mkdtemp(prefix="via_console201_"))
    try:
        reg = tmp / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        now = _dt.datetime(2026, 11, 19, 6, 0, 0, tzinfo=_dt.timezone.utc)
        (tmp / "b").mkdir()
        (tmp / "b" / "same.json").write_bytes(b'{"a": 1}\n')
        (tmp / "b" / "crlf.json").write_bytes(b'{"a": 1}\r\n{"b": 2}\r\n')
        (tmp / "b" / "changed.json").write_bytes(b'{"a": 2}\n')
        sha = lambda x: hashlib.sha256(x).hexdigest()
        params = {"generated": "2026-09-25 21:44:53", "leaf_total": 9, "conflicts": [], "books": [
            {"id": "SAME", "domain": "D", "path": "b/same.json", "sha256": sha(b'{"a": 1}\n')},
            {"id": "CRLF", "domain": "D", "path": "b/crlf.json", "sha256": sha(b'{"a": 1}\n{"b": 2}\n')},
            {"id": "CHANGED", "domain": "D", "path": "b/changed.json", "sha256": sha(b'{"a": 1}\n')},
            {"id": "GONE", "domain": "D", "path": "b/gone.json", "sha256": "0" * 64}],
            "locked_alignment": [{"name": "A", "state": "ALIGNED", "drift": []}, {"name": "B", "state": "DRIFT", "drift": [1, 2]}]}
        (reg / (PARAM_BOOK + "_v0003.json")).write_text(json.dumps(params), encoding="utf-8")
        rows, notes = param_rows(tmp)
        by = {r["id"]: r for r in rows}
        chk("③ 參數冊:索引冊一列 + 每本一列 + 每條鎖定正則一列;全部掛在 VCGC 自己的區",
            sorted(by) == sorted(["PARAM:索引冊", "PARAM:SAME", "PARAM:CRLF", "PARAM:CHANGED", "PARAM:GONE", "LOCK:A", "LOCK:B"]) and not notes
            and all(r["section"] == SEC_PARAM and r["system"] == "VCGC" for r in rows), sorted(by))
        chk("④ 參數冊的燈:內容相同 → 綠(行尾不同也算相同);改過 → 黃;檔不在 → 紅;鎖定正則不對齊 → 紅;衝突 0 → 索引冊綠",
            (by["PARAM:SAME"]["lamp"], by["PARAM:CRLF"]["lamp"], by["PARAM:CHANGED"]["lamp"], by["PARAM:GONE"]["lamp"], by["LOCK:A"]["lamp"], by["LOCK:B"]["lamp"], by["PARAM:索引冊"]["lamp"])
            == ("g", "g", "y", "r", "g", "r", "g"), {k: v["lamp"] for k, v in by.items()})
        ifc = {"ts": "2026-11-10T14:32:18Z", "contracts": [
            {"cand": "IFC-CAND-01", "ifc_id": "IFC-001", "version": "v1.0", "state": "ACTIVE", "title": "甲", "provider": ["VDF"], "consumer": ["VCGC"], "INPUT": "無", "OUTPUT": "收據"},
            {"cand": "IFC-CAND-02", "ifc_id": "IFC-002", "state": "DEPRECATED", "title": "乙", "provider": "VRN-2", "consumer": "VQG"},
            {"cand": "IFC-CAND-09", "state": "ACTIVE", "title": "還沒發號"}], "tombstones": [{"ifc_id": "IFC-000", "why": "合併"}]}
        (reg / (IFC_BOOK + "_v0002.json")).write_text(json.dumps(ifc, ensure_ascii=False), encoding="utf-8")
        irows, inotes = ifc_rows(tmp)
        ib = {r["id"]: r for r in irows}
        chk("⑤ 介面契約:每條一列(號 · 狀態 · 提供方 → 使用方 · 入出);ACTIVE 綠 · 棄用黃 · 沒有 IFC 號的黃並寫明 · 墓碑灰",
            sorted(ib) == sorted(["IFC-001", "IFC-002", "IFC-CAND-09", "IFC-000:墓碑"]) and not inotes and ib["IFC-001"]["lamp"] == "g" and "VDF → VCGC" in ib["IFC-001"]["detail"]
            and ib["IFC-002"]["lamp"] == "y" and ib["IFC-CAND-09"]["lamp"] == "y" and "還沒有 IFC 號" in ib["IFC-CAND-09"]["detail"] and ib["IFC-000:墓碑"]["lamp"] == "x", {k: (v["lamp"], v["detail"]) for k, v in ib.items()})
        contract = {"stale_hours": 48, "lamp_maps": {"v": {"RED": "RED", "AMBER": "YELLOW"}}, "systems": {
            "VCGC": {"summary": "sync", "receipts": [{"id": "sync", "path": "r/own.json", "lamp_key": "lamp", "at_keys": ["at"], "version_keys": ["version"], "zh": "同步台"},
                                                      {"id": "tool", "path": "r/tool.json", "lamp_key": "verdict", "lamp_map": "v", "at_keys": ["ts"], "zh": "工具", "optional": True},
                                                      {"id": "none", "path": "r/none.json", "lamp_key": "lamp", "zh": "沒跑過"}]},
            "AAA": {"zh": "甲", "summary": "sync", "receipts": [{"id": "sync", "path": "r/a.json", "lamp_key": "lamp", "at_keys": ["at"], "version_keys": ["version"], "zh": "同步台"}]},
            "BBB": {"zh": "乙", "summary": "sync", "receipts": [{"id": "sync", "path": "r/b.json", "lamp_key": "lamp", "zh": "同步台"}]},
            "VDB": {"zh": "庫", "receipts": [], "pages": [{"id": "report", "path": "p/here.html", "zh": "報告頁"}, {"id": "cat", "path": "p/nope.html", "zh": "目錄頁"}]}}}
        (reg / (P.CONTRACT + "_v0009.json")).write_text(json.dumps(contract, ensure_ascii=False), encoding="utf-8")
        (tmp / "r").mkdir()
        (tmp / "p").mkdir()
        (tmp / "p" / "here.html").write_text("<html></html>", encoding="utf-8")
        (tmp / "r" / "own.json").write_text(json.dumps({"lamp": "YELLOW", "at": "2026-11-19T05:00:00Z", "version": "v0201", "summary": "一頁待重跑"}), encoding="utf-8")
        (tmp / "r" / "tool.json").write_text(json.dumps({"verdict": "AMBER", "ts": "2026-11-19 13:00:00"}), encoding="utf-8")
        (tmp / "r" / "a.json").write_text(json.dumps({"lamp": "GREEN", "content_lamp": "YELLOW", "at": "2026-11-19T05:00:00Z", "local": "2026-11-19 13:00", "version": "v0186"}), encoding="utf-8")
        orows, onotes = own_receipt_rows(tmp, now)
        ob = {r["id"]: r for r in orows}
        chk("⑥ VCGC 自己的收據:契約冊 VCGC 一節每份一列;燈是那份收據自己報的(經對照表);不在 → 灰(契約要求的寫去向,選配的不寫)",
            sorted(ob) == ["VCGC:none", "VCGC:sync", "VCGC:tool"] and not onotes and ob["VCGC:sync"]["lamp"] == "y" and ob["VCGC:tool"]["lamp"] == "y" and "AMBER" in ob["VCGC:tool"]["detail"]
            and ob["VCGC:none"]["lamp"] == "x" and ob["VCGC:none"]["needs"] and all(r["section"] == SEC_OWN for r in orows), {k: (v["lamp"], v["detail"]) for k, v in ob.items()})
        info, pages = system_info(tmp, now)
        pb = {r["id"]: r for r in pages}
        chk("⑦ 每個系統一句話:只讀契約冊指定的那一份;有 → 它報的燈 + 內容燈 + 時間 + 版本;收據不在 / 沒指定 → 灰並寫明;VCGC 自己不在內",
            set(info) == {"AAA", "BBB", "VDB"} and info["AAA"]["lamp"] == "g" and "管理器自報 綠 · 內容 黃 · 2026-11-19 13:00 · v0186" == info["AAA"]["note"]
            and info["BBB"] == {"lamp": "x", "note": "管理器的彙總收據這台機器上沒有"} and info["VDB"] == {"lamp": "x", "note": NO_SUMMARY}, info)
        chk("⑧ VDB 的頁引用既有畫面:頁在 → 綠帶檔案時間;不在 → 灰;列掛在那個系統", sorted(pb) == ["VDB:頁:cat", "VDB:頁:report"] and pb["VDB:頁:report"]["lamp"] == "g" and pb["VDB:頁:report"]["at"]
            and pb["VDB:頁:cat"]["lamp"] == "x" and all(r["system"] == "VDB" and r["section"] == P.PEER_SECTION for r in pages), pb)
        before = sorted(str(p.relative_to(tmp)) for p in tmp.rglob("*"))
        empty = Path(tempfile.mkdtemp(prefix="via_console201_e_"))
        e = (param_rows(empty), ifc_rows(empty), own_receipt_rows(empty), system_info(empty))
        shutil.rmtree(str(empty), ignore_errors=True)
        chk("⑨ 冊都不在:不炸、不編列,各留一句說明;三區與系統資訊都不寫任何檔",
            e[0][0] == [] and len(e[0][1]) == 1 and e[1][0] == [] and len(e[1][1]) == 1 and e[2][0] == [] and len(e[2][1]) == 1 and e[3] == ({}, [])
            and before == sorted(str(p.relative_to(tmp)) for p in tmp.rglob("*")), e)
        snap = (Q.ov_collect, Q.ov_write, list(Q.OV_SECTIONS), P.peer_rows, P.VERSION, P.CMF_MIN)
        rep = tmp / "rep"
        with open(os.devnull, "w", encoding="utf-8") as nul:
            keep_out, sys.stdout = sys.stdout, nul
            try:
                rc = overview(["--no-open"], via=VIA, rep=rep)
            finally:
                sys.stdout = keep_out
        book = P.pv_json(rep / "overview" / Q.OV_BOOK) or {}
        rec = P.pv_json(rep / Q.OV_RECEIPT) or {}
        page = (rep / Q.OV_PAGE).read_text(encoding="utf-8") if (rep / Q.OV_PAGE).is_file() else ""
        secs = {}
        for it in book.get("items") or []:
            secs[it["section"]] = secs.get(it["section"], 0) + 1
        chk("⑩ 真樹(只讀)出頁到暫存夾:rc 0 · 新三區都有列 · 同儕區還在 · 原本十一區一列不少 · 新三區全是 VCGC 自己的列",
            rc == 0 and all(secs.get(s, 0) >= 1 for s in (SEC_PARAM, SEC_IFC, SEC_OWN, P.PEER_SECTION)) and sum(v for k, v in secs.items() if k in snap[2]) >= 1000
            and all(it["system"] == "VCGC" for it in book["items"] if it["section"] in (SEC_PARAM, SEC_IFC, SEC_OWN)), (rc, secs))
        si = book.get("sys_info") or {}
        chk("⑪ 項目冊帶每個系統一句話(VDF · VRN-2 · VQG · VAP · VDB;沒有 VCGC)· 系統順序與展開區照舊 · 頁面的系統卡寫著那一句",
            {"VDF", "VRN-2", "VQG", "VAP", "VDB"} <= set(si) and "VCGC" not in si and book.get("systems") == P.SYS_CARDS and (book.get("expand") or {}).get("system") == "VCGC"
            and all(v["note"] in page for v in si.values()), si)
        chk("⑫ 收據:版本是本版 · 帶 system_info · v0200 的 own_content_lamp 與 peers 還在 · 頁燈綠 · 沒有「沒有 VDB」的說明",
            rec.get("version") == VERSION and rec.get("engine") == FAMILY + "_" + VERSION and rec.get("lamp") == "g" and set(rec.get("system_info") or {}) == set(si)
            and rec.get("own_content_lamp") in "rygx" and "VDB" in (rec.get("peers") or {}) and not any("沒有 VDB" in n for n in rec.get("notes") or []),
            {k: rec.get(k) for k in ("version", "engine", "lamp", "own_content_lamp", "peers", "notes")})
        chk("⑬ 跑完還原 v0200 與 v0199 模組(讀冊點 · 寫檔點 · 區塊表 · 同儕函式 · 版本);沒留下暫存檔",
            (Q.ov_collect, Q.ov_write, list(Q.OV_SECTIONS), P.peer_rows, P.VERSION, P.CMF_MIN) == snap and not list(rep.rglob("*.tmp")))
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)
    seen = []
    real = globals()["forward"]
    globals()["forward"] = lambda x: seen.append(list(x)) or 0
    try:
        m1 = main(["status"])
        m2 = main(["synchronizer", "check"])
    finally:
        globals()["forward"] = real
    chk("⑭ 只有 overview 留在本版;其餘動詞(含 synchronizer)原樣轉交前版", seen == [["status"], ["synchronizer", "check"]] and m1 == 0 and m2 == 0, seen)
    names = [n for n in dir(P) if not n.startswith("_") and callable(getattr(P, n, None))]
    chk("⑮ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), "%d 支" % len(names))
    src = Path(__file__).read_text(encoding="utf-8")
    live = src.split("def selftest")[0]
    chk("⑯ 零網路 · 不用 TA-Lib · 不 import 他系統 · 不寫同意閘 · 本版自己不寫檔 · 本檔沒有色碼",
        not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib|socket|VDF_|VRN_|VQG_|VAP_)", src, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src)
        and ".write_text(" not in live and ".write_bytes(" not in live and "open(" not in live and not re.search(r"#[0-9a-fA-F]{6}\b", live))
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", TAG, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("--selftest", "selftest") and "--legacy" not in args:
        return selftest()
    if args[:1] == ["overview"]:
        return overview(args[1:])
    if not args or args[0] == "help":
        rc = forward(args or ["help"])
        help_extra()
        return rc
    return forward(args)


if __name__ == "__main__":
    sys.exit(main())
