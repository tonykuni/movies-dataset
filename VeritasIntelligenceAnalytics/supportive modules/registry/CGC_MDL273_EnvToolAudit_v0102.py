#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC EnvToolAudit v0102 — 薄尾:外部程式(非 pip)探測 + 安裝計畫 + 還原點閘(操作員令 2026-10-10:VCGC 環境及工具管理協助安裝尚未安裝的工具
pdfplumber fitz pypdfium2 PIL docx reportlab pikepdf win32com docx2pdf soffice pdftoppm ps_word_com;紀錄造冊編碼一定要安裝;修正所有環境無衝突,以還原點進行新增)。
  ext              讀工具冊尾版 VIA_ToolRoster_SSOT_v*.json 的 external_tools 段(唯一來源,本支不另寫清單)逐件探:
                   exe(PATH + Windows 預設安裝路徑)· ps_word_com(登錄檔 ProgID Word.Application\CLSID;非 Windows = N/A)→ OK / MISSING + winget 計畫
  ext --apply      只在三閘全過才裝:① Windows 且有 winget ② VIA_NET_CONSENT=YES(操作員自己開,本支不代設)
                   ③ 還原點:VIA_RestorePoint_Ledger_v0100.jsonl 最近一筆 ≤ 24h(沒有 = 拒,先跑 CGC_MDL274_HealthMatrix restorepoint)
                   winget install --id <id> -e --silent;Word(授權)永不代裝。結果 VIA_Reports/review/vcgc_env/EXT_latest.json
  audit / fill / pdftools   照前版;audit 的外部工具另加 soffice · pdftoppm。
  pip 套件不走本支:docs 家族進 via_vrn_312 由 CGC_MDL135_EnvGovernance(via-envgov plan → resume 乾跑 CLEAN/CONFLICT → resume --approve,只增不減)。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import datetime
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ME = Path(__file__).resolve()
NAME = ME.stem
TAG = "v0102"
_STEM = "CGC_MDL273_EnvToolAudit"
RESTORE_LEDGER = "VIA_RestorePoint_Ledger_v0100.jsonl"
RESTORE_MAX_H = float(os.environ.get("VIA_RESTORE_MAX_H") or 24)


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in ME.parent.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(ME)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_v0102", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _t in ("soffice", "pdftoppm"):
    if _t not in PRIOR.EXT_TOOLS:
        PRIOR.EXT_TOOLS.append(_t)                  # audit 的外部工具欄也看得到這兩件


def __getattr__(name):
    return getattr(PRIOR, name)


def _roster(P: dict) -> tuple:
    hits = sorted(P["registry"].glob("VIA_ToolRoster_SSOT_v*.json"), key=_vnum)
    if not hits:
        return None, {}
    try:
        return hits[-1], json.loads(hits[-1].read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return hits[-1], {"_err": "%s" % type(exc).__name__}


def _progid_ok(progid: str) -> tuple:
    if sys.platform != "win32":
        return None, "N/A(非 Windows;Word COM 只在工作站)"
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, progid + "\\CLSID"):
            return True, "ProgID %s 已註冊" % progid
    except OSError:
        return False, "ProgID %s 未註冊(Word 未安裝)" % progid


def probe(spec: dict, name: str) -> dict:
    if name == "ps_word_com" or spec.get("probe", "").startswith("ProgID"):
        ok, why = _progid_ok("Word.Application")
        state = "OK" if ok else ("NA" if ok is None else "MISSING")
        return {"tool": name, "state": state, "why": why, "path": None, "winget": spec.get("winget"), "role": spec.get("role", "")}
    for exe in spec.get("exe") or [name]:
        p = shutil.which(exe)
        if p:
            return {"tool": name, "state": "OK", "why": "PATH", "path": p, "winget": spec.get("winget"), "role": spec.get("role", "")}
    for wp in spec.get("win_paths") or []:
        if sys.platform == "win32" and Path(wp).is_file():
            return {"tool": name, "state": "OK", "why": "預設安裝路徑(不在 PATH)", "path": wp, "winget": spec.get("winget"), "role": spec.get("role", "")}
    return {"tool": name, "state": "MISSING", "why": "PATH 與預設路徑都沒有", "path": None, "winget": spec.get("winget"), "role": spec.get("role", "")}


def restore_point(P: dict, now: datetime.datetime | None = None) -> dict:
    led = P["registry"] / RESTORE_LEDGER
    now = now or datetime.datetime.now()
    last, bad = None, 0
    if led.is_file():
        for line in led.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                bad += 1                             # 壞列照數,回報在 why 尾
                row = {}
            if row.get("ts"):
                last = row
    if not last:
        return {"ok": False, "why": "還原點帳沒有紀錄", "last": None}
    try:
        age_h = (now - datetime.datetime.fromisoformat(str(last["ts"])[:19])).total_seconds() / 3600
    except ValueError:
        return {"ok": False, "why": "還原點時間讀不懂:%s" % last.get("ts"), "last": last}
    skew = ""
    if -14 <= age_h < 0:                             # 帳本記工作站本地時間(+0800 等),跟本機時區不同 → 視為剛建(時區差,講明)
        skew, age_h = "(帳本時間比本機快 %.1f 小時 = 時區差,視為剛建)" % -age_h, 0.0
    return {"ok": 0 <= age_h <= RESTORE_MAX_H, "age_h": round(age_h, 1), "last": last,
            "why": "最近還原點 %s(%.1f 小時前)%s%s" % (last.get("stamp"), age_h, skew, ("(帳有 %d 列讀不懂)" % bad) if bad else "")}


def ext(P: dict | None = None, apply: bool = False) -> dict:
    P = P or PRIOR._paths()
    src, roster = _roster(P)
    tools = {k: v for k, v in (roster.get("external_tools") or {}).items() if not k.startswith("_") and isinstance(v, dict)}
    rows = [probe(spec, name) for name, spec in tools.items()]
    gates = {"windows": sys.platform == "win32", "winget": shutil.which("winget"), "consent": os.environ.get("VIA_NET_CONSENT") == "YES",
             "restore": restore_point(P)}
    out = {"verb": "ext", "engine": NAME, "ts": PRIOR._now(), "roster": str(src.name) if src else None, "apply": apply, "rows": rows, "gates": gates}
    if not tools:
        out["lamp"] = "RED"
        out["why"] = "工具冊尾版沒有 external_tools 段(先出 VIA_ToolRoster_SSOT 新版)"
        return out
    for r in rows:
        r["plan"] = ("winget install --id %s -e --silent --accept-package-agreements --accept-source-agreements" % r["winget"]) if (r["state"] == "MISSING" and r["winget"]) else \
                    ("操作員手動安裝(授權 / 無 winget 套件)" if r["state"] == "MISSING" else "")
        r["status"] = "OK" if r["state"] in ("OK", "NA") else "PLAN"
    if apply:
        block = [k for k, ok in (("Windows + winget", gates["windows"] and gates["winget"]), ("VIA_NET_CONSENT=YES(操作員自己開)", gates["consent"]),
                                 ("還原點 ≤ %gh(%s)" % (RESTORE_MAX_H, gates["restore"]["why"]), gates["restore"]["ok"])) if not ok]
        out["blocked"] = block
        for r in rows:
            if r["status"] != "PLAN":
                continue
            if block or not r["winget"]:
                r["status"] = "BLOCKED" if block else "MANUAL"
                continue
            try:
                q = subprocess.run([gates["winget"], "install", "--id", r["winget"], "-e", "--silent", "--accept-package-agreements", "--accept-source-agreements"],
                                   capture_output=True, text=True, timeout=1800)
                r["status"], r["tail"] = ("OK" if q.returncode == 0 else "FAIL"), (q.stdout + q.stderr)[-300:]
            except (subprocess.SubprocessError, OSError) as exc:
                r["status"], r["tail"] = "FAIL", type(exc).__name__
            r.update({k: v for k, v in probe(tools[r["tool"]], r["tool"]).items() if k in ("state", "why", "path")})
    st = [r["status"] for r in rows]
    out["lamp"] = "RED" if "FAIL" in st else ("GREEN" if all(s == "OK" for s in st) else "YELLOW")
    try:
        P["out"].mkdir(parents=True, exist_ok=True)
        (P["out"] / "EXT_latest.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        out["file"] = str(P["out"] / "EXT_latest.json")
    except OSError as exc:
        out["file"] = "寫不出:%s" % type(exc).__name__
    return out


def _print_ext(o: dict) -> None:
    for r in o["rows"]:
        print("  [%s] %-12s %-8s %s%s" % (r["status"], r["tool"], r["state"], r["why"], (" → " + r["plan"]) if r.get("plan") and r["status"] != "OK" else ""))
    g = o["gates"]
    print("  [閘] Windows %s · winget %s · VIA_NET_CONSENT %s · %s" % (g["windows"], bool(g["winget"]), "YES" if g["consent"] else "未開(操作員自己開)", g["restore"]["why"]))
    if o.get("blocked"):
        print("  [擋] --apply 未過:%s" % ";".join(o["blocked"]))
    print("[計] vcgc ext · 冊 %s · %d 件 · %s · %s" % (o.get("roster"), len(o["rows"]), o["lamp"], o.get("file") or o.get("why", "")))


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a[:2]:
        return selftest()
    if a[:1] == ["ext"]:
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print("[VCGC] 拒絕。只能經 via-vcgc。")
            return 2
        o = ext(apply="--apply" in a)
        print(json.dumps(o, ensure_ascii=False, indent=1)) if "--json" in a else _print_ext(o)
        return 1 if o["lamp"] == "RED" else 0
    return PRIOR.main(a)


def selftest() -> int:
    import tempfile
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        p, f = (p + 1, f) if cond else (p, f + 1)
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · %s" % (note,)) if note != "" else ""))

    keep = {k: os.environ.get(k) for k in ("VIA_ROOT", "VIA_NET_CONSENT", "VIA_ENV_NO_PIP")}
    td = Path(tempfile.mkdtemp(prefix="cgcext-"))
    try:
        os.environ["VIA_ROOT"] = str(td)
        os.environ.pop("VIA_NET_CONSENT", None)
        P = PRIOR._paths()
        P["registry"].mkdir(parents=True, exist_ok=True)
        o0 = ext(P)
        chk("① 工具冊沒有 external_tools 段 → RED 並講明", o0["lamp"] == "RED" and "external_tools" in o0["why"])
        (P["registry"] / "VIA_ToolRoster_SSOT_v0100.json").write_text(json.dumps({"envs": {}, "external_tools": {
            "_why": "x", "pyexe": {"exe": [Path(sys.executable).name, "python3"], "winget": None},
            "zz_nope": {"exe": ["zz_no_such_exe_qq"], "winget": "Zz.Nope"},
            "ps_word_com": {"probe": "ProgID Word.Application", "winget": None}}}), encoding="utf-8")
        o1 = ext(P)
        by = {r["tool"]: r for r in o1["rows"]}
        chk("② 讀冊尾版 · 有的執行檔 = OK · 沒有 = MISSING + winget 計畫 · Word COM 非 Windows = NA",
            by["pyexe"]["state"] == "OK" and by["zz_nope"]["state"] == "MISSING" and "Zz.Nope" in by["zz_nope"]["plan"]
            and (by["ps_word_com"]["state"] == "NA" if sys.platform != "win32" else by["ps_word_com"]["state"] in ("OK", "MISSING")) and "_why" not in by)
        o2 = ext(P, apply=True)
        chk("③ --apply 三閘:沒還原點 / 沒同意閘 / 非 Windows → 全擋,一件都不裝", o2["blocked"] and by and {r["tool"]: r["status"] for r in o2["rows"]}["zz_nope"] == "BLOCKED"
            and any("還原點" in b for b in o2["blocked"]) and any("CONSENT" in b for b in o2["blocked"]))
        now = datetime.datetime(2026, 10, 10, 12, 0, 0)
        (P["registry"] / RESTORE_LEDGER).write_text(json.dumps({"stamp": "20261010T100000", "ts": "2026-10-10T10:00:00"}) + "\n", encoding="utf-8")
        rp_ok = restore_point(P, now)
        rp_old = restore_point(P, now + datetime.timedelta(hours=30))
        rp_tz = restore_point(P, now - datetime.timedelta(hours=10))
        rp_fut = restore_point(P, now - datetime.timedelta(hours=40))
        chk("④ 還原點閘:2 小時前 = 過 · 32 小時前 = 不過 · 時區差(帳本快 8h)= 過並講明 · 快 38h = 不過", rp_ok["ok"] and not rp_old["ok"]
            and rp_tz["ok"] and "時區差" in rp_tz["why"] and not rp_fut["ok"], (rp_ok.get("age_h"), rp_old.get("age_h"), rp_tz.get("age_h")))
        chk("⑤ audit 外部工具欄含 soffice · pdftoppm", "soffice" in PRIOR.EXT_TOOLS and "pdftoppm" in PRIOR.EXT_TOOLS)
        body = ME.read_text(encoding="utf-8")
        chk("⑥ 加速器橋 · 不代設同意閘 · 不碰 TA-Lib", "[VIA:ACCEL-BRIDGE:v0100]" in body and 'environ["VIA_NET_' + 'CONSENT"] = "' not in body and "import " + "talib" not in body)
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(td, ignore_errors=True)
    print("  ── 前版 v0101 自測(原樣)──")
    prc = PRIOR.selftest()
    chk("⑦ 前版 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    print("[計] %s 自測 %d/%d · %s" % (NAME, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
