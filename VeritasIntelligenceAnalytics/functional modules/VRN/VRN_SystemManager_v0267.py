#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0267 — v0266 薄尾(v0266 一字不動):collect() 自報改原生(只讀冊 · 不 import 他系統)+ token 省 Token 動詞(經 VCGC 鎖冊 · 子行程 · 唯讀)。

操作員 2026-11-14:「SYSTEM MANAGER 應該據最新狀況及政策重寫並導入多個 VCGC TOKEN-SAVING 工具去完成」。
實錄:v0263 起的標準重寫沒有自己的 collect(),靠轉接回到 v0262 → v0256 的舊 collect(),其上行七處 import VCGC 主控台來算(違反標準 P4)。
本版照標準 v0101:七處只讀 VCGC 的冊與檔面文字;省 Token 工具(read · slice · digest · chain)只經鎖冊解析、以子行程唯讀執行,目標限 VRN 自己的樹與收據。
  collect [--json]                 自報:七處 · 健康 · 規範自查(給 VCGC 全景只讀)
  token read|slice|digest|chain …  省 Token 讀檔(只收 VRN 自己的檔 / 家族 / 收據)
其餘動詞照前版:子程序環境照 v0265 sm_child_env(帶 VIA_FROM_VCGC=YES,引擎自測走 VCGC 閘);本管理器自己的動詞不以它為前提(標準 P3)。
零網路 · 不用 TA-Lib · 不寫同意閘 · 不裝套件。
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

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
VERSION = "v0267"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
CORE = PRIOR.PRIOR                         # v0265 標準核心(sm_health · sm_conform · SM_NATIVE 在這一層)
SM_CONFIG = CORE.SM_CONFIG
SM_TAG = SM_CONFIG["manager_family"] + " " + VERSION
sm_via_root = CORE.sm_via_root
SM_NATIVE = tuple(CORE.SM_NATIVE)


def __getattr__(name):
    """前版公開面照轉(尾版不少名字)。"""
    return getattr(PRIOR, name)


# ══════════════════════════ v0267:collect() 自報改原生(只讀冊 · 不 import 他系統)+ token 省 Token 動詞(經鎖冊 · 子行程 · 唯讀)══════════════════════════
# 操作員 2026-11-14:「SYSTEM MANAGER 應該據最新狀況及政策重寫並導入多個 VCGC TOKEN-SAVING 工具去完成」。
# 實錄:11/11 依標準重寫時拿掉了 collect()(VCGC 全景 / 啟動門讀的自報介面),VCGC 那一格一直是 NODATA;舊 collect() 的上行七處靠 import VCGC
# 主控台來算,違反標準 P4。本段:七處改成只讀 VCGC 的冊與檔面文字來判(不 import、不執行);省 Token 工具只經鎖冊解析、以子行程唯讀執行,
# 目標限本系統自己的樹與自己的收據;鎖冊或工具不在 → ABSENT,管理器其他功能不受影響。
V75_SEVEN = ("spec", "grid", "register", "deck", "manager", "inventory", "handover")
V75_KEYS = {"VDF": {"spec_id": "vdf_system", "deck": "vdf_system", "cmd": "via-vdfsys"},
            "VRN": {"spec_id": "vrn_system", "deck": "vrn_system", "cmd": "via-vrnsys"}}
V75_TOKEN_SUBS = ("read", "slice", "digest", "chain")
V75_VERBS = ("collect", "token")


def _v75_cfg() -> dict:
    return SM_CONFIG


def _v75_vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def _v75_newest(folder: Path, pattern: str):
    hits = [p for p in folder.glob(pattern) if p.is_file()] if folder.is_dir() else []
    return max(hits, key=lambda p: (_v75_vnum(p), p.name)) if hits else None


def _v75_text(p) -> str:
    try:
        return Path(p).read_text(encoding="utf-8", errors="replace") if p else ""
    except OSError as exc:
        return "\0READ_ERROR " + type(exc).__name__


def v75_upstream(root: Path) -> dict:
    """上行七處自審:全部只讀 VCGC 的冊與檔面文字(不 import、不執行;標準 P4)。找不到的那一處照實記 False,不假綠。"""
    cfg = _v75_cfg()
    fam, key = cfg["manager_family"], V75_KEYS[cfg["system"]]
    reg = root / "supportive modules" / "registry"
    src = {"spec": _v75_newest(reg, "VIA_InputConsole_Spec_v*.json"), "grid": _v75_newest(reg, "CGC_MDL064_SelftestGrid_v*.py"),
           "register": _v75_newest(root, "Register-VIA-Commands-v*.ps1"), "deck": _v75_newest(reg, "CGC_MDL095_DeckServer_v*.py"),
           "inventory": _v75_newest(reg, "VIA_Component_Inventory_SSOT_v*.json")}
    mgrs = sorted(root.glob("VIA_SYSTEM_MANAGER_v*.py"), key=_v75_vnum)
    out = {"via": SM_TAG, "mode": "file_read", "how": "只讀 VCGC 的冊與檔面文字(不 import、不執行 · 標準 P4)",
           "sources": {k: (v.name if v else None) for k, v in src.items()}}
    out["spec"] = bool(re.search(r'"id"\s*:\s*"%s"' % re.escape(key["spec_id"]), _v75_text(src["spec"])))
    out["grid"] = fam in _v75_text(src["grid"])
    books = sorted(root.glob("Register-VIA-Commands-v*.ps1"), key=_v75_vnum)      # 命令冊是 dot-source 鏈:整條讀
    out["register"] = any(re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(key["cmd"]), _v75_text(b)) for b in books)
    dk = _v75_text(src["deck"])
    out["deck"] = ('"%s"' % key["deck"]) in dk or ("'%s'" % key["deck"]) in dk
    out["manager"] = any(('"%s"' % fam) in _v75_text(p) for p in mgrs)
    out["via_manager"] = mgrs[-1].name if mgrs else "ABSENT"
    inv = False
    try:
        j = json.loads(_v75_text(src["inventory"]) or "{}")
        rec = next((r for r in j.get("records") or [] if r.get("identity") == fam and r.get("state", "ACTIVE") == "ACTIVE"), None)
        inv = (rec or {}).get("code") or False
    except ValueError as exc:
        out["inventory_error"] = type(exc).__name__
    out["inventory"] = inv
    docs = sorted((root / "docs").glob("*.md"))[-40:]
    out["handover"] = any(fam in _v75_text(q) for q in docs)
    out["seven"] = {k: out.get(k, False) for k in V75_SEVEN}
    out["done"] = sum(1 for k in V75_SEVEN if out.get(k))
    return out


def _v75_lamp(x) -> str:
    return x.get("lamp", "NODATA") if isinstance(x, dict) else "NODATA"


def collect() -> dict:
    """給對等系統只讀監控的自報(VCGC 全景 · 啟動門讀這個):七處 · 健康 · 規範自查。不寫檔、不出網、不 import 他系統。"""
    root = sm_via_root()
    up = v75_upstream(root)
    lamps = {"upstream": "GREEN" if up["done"] == len(V75_SEVEN) else "YELLOW"}
    for name, fn in (("health", CORE.sm_health), ("conform", CORE.sm_conform)):
        try:
            lamps[name] = _v75_lamp(fn(root))
        except Exception as exc:  # noqa: BLE001 — 自報不讓單一檢查拖垮;照實記
            lamps[name] = "NODATA"
            up.setdefault("errors", {})[name] = "%s: %s" % (type(exc).__name__, str(exc)[:120])
    out = {"schema": "VIA.%s.SystemManager.collect.v2" % _v75_cfg()["system"], "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "me": Path(__file__).name, "version": VERSION, "system": _v75_cfg()["system"], "served_by": {"tail": SM_TAG},
           "upstream": up, "lamps": lamps}

    worst = list(lamps.values()) + ([out["launch"]["state"]] if isinstance(out.get("launch"), dict) else [])
    out["rc"] = 1 if "RED" in worst else (0 if all(x == "GREEN" for x in worst) else 2)
    out["rc_name"] = {0: "GREEN", 1: "RED", 2: "YELLOW/NODATA"}[out["rc"]]
    return out


def _v75_scope(root: Path) -> list:
    cfg = _v75_cfg()
    return [root / cfg["dir"]] + [root / r for r in cfg.get("reports") or []] + [root / "docs" / "handoff" / "evidence"]


def _v75_resolve(root: Path, target: str):
    """目標路徑:絕對 → 照用;相對 → 先以目前目錄、再以 VIA 根找。回 (絕對路徑, 是否在本系統範圍內)。"""
    cands = [Path(target)] if Path(target).is_absolute() else [Path.cwd() / target, root / target]
    t = next((c for c in cands if c.exists()), cands[-1])
    try:
        t = t.resolve()
    except (OSError, ValueError):
        return t, False
    return t, any(t == s.resolve() or s.resolve() in t.parents for s in _v75_scope(root))


def v75_token(root: Path, args: list, capture: bool = False) -> dict:
    """省 Token:read(骨架卡)· slice(一個定義)· digest(日誌判決行)· chain(薄尾版本鏈)。
    工具路徑只從 VCGC 鎖冊 VIA_ToolVersion_Lock 的 token.path 解析(不釘檔名、不 import);以子行程唯讀執行;目標限本系統的樹與自己的收據。"""
    sub = args[0] if args else ""
    if sub not in V75_TOKEN_SUBS:
        return {"lamp": "YELLOW", "why": "用法:token <%s> <目標…>(read / slice / digest 收本系統的檔;chain 收本系統的家族名)" % "|".join(V75_TOKEN_SUBS)}
    rest = [a for a in args[1:]]
    pos = [a for a in rest if not a.startswith("-")]
    if not pos:
        return {"lamp": "YELLOW", "why": "少了目標"}
    if sub == "chain":
        prefixes = tuple(_v75_cfg().get("own_prefixes") or ())
        if not pos[0].startswith(prefixes):
            return {"lamp": "DENY", "why": "chain 只收本系統的家族(%s…)" % "/".join(prefixes), "target": pos[0]}
    else:
        absp, inside = _v75_resolve(root, pos[0])
        if not inside:
            return {"lamp": "DENY", "why": "目標不在本系統的樹或自己的收據內(對等系統只讀不代看)", "target": pos[0]}
        rest = [str(absp) if a == pos[0] else a for a in rest]
    lock = _v75_newest(root / "supportive modules" / "registry", "VIA_ToolVersion_Lock_v*.json")
    try:
        rel = ((json.loads(_v75_text(lock)) if lock else {}).get("token") or {}).get("path")
    except ValueError:
        rel = None
    tool = None
    if rel:                                 # 鎖冊的路徑以倉根為準(前綴 VIA 根夾名);兩種寫法都認
        for base in (root.parent, root):
            if (base / rel).is_file():
                tool = base / rel
                break
    if tool is None:
        return {"lamp": "ABSENT", "why": "鎖冊或省 Token 工具不在(本管理器其他功能照常)", "lock": lock.name if lock else None, "tool": rel}
    cp = subprocess.run([sys.executable, str(tool), sub, *rest], cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    text = cp.stdout or ""
    ledger = next((l.strip() for l in text.splitlines() if l.startswith("[token 帳]")), "")
    if not capture:
        sys.stdout.write(text)
        if cp.stderr.strip():
            sys.stderr.write(cp.stderr[-2000:])
    return {"lamp": "GREEN" if cp.returncode == 0 else "RED", "rc": cp.returncode, "tool": tool.name, "lock": lock.name, "ledger": ledger,
            "out": text if capture else None}


def _v75_cmd(verb: str, args: list) -> int:
    root = sm_via_root()
    if verb == "collect":
        r = collect()
        if "--json" in args:
            print(json.dumps(r, ensure_ascii=False, indent=1, default=str))
        else:
            up = r["upstream"]
            print("[%s] collect · rc %s %s · 七處 %d/7 %s · 燈 %s%s" % (SM_TAG, r["rc"], r["rc_name"], up["done"],
                  " ".join(k for k, v in up["seven"].items() if not v) and ("缺 " + " ".join(k for k, v in up["seven"].items() if not v)) or "",
                  r["lamps"], (" · 啟動 " + r["launch"]["state"]) if isinstance(r.get("launch"), dict) else ""), flush=True)
        return r["rc"]
    r = v75_token(root, args)
    if r["lamp"] != "GREEN":
        print("[%s] token %s · %s" % (SM_TAG, r["lamp"], r.get("why") or ("rc %s" % r.get("rc"))), flush=True)
    return {"GREEN": 0, "RED": 1, "DENY": 2, "YELLOW": 2, "ABSENT": 3}.get(r["lamp"], 2)


def _v75_selftest_new() -> list:
    """本版新增的自測(回 [(名稱, 過否, 附註)])。零網路 · 只在 tempfile 寫。"""
    res = []
    root = sm_via_root()
    before = {n for n in sys.modules if n.startswith(("CGC_", "vcgc", "via_vcgc"))}
    r = collect()
    loaded = {n for n in sys.modules if n.startswith(("CGC_", "vcgc", "via_vcgc"))} - before
    res.append(("① collect():上行七鍵齊 · rc / 燈都有 · 呼叫後沒有載入任何 VCGC 模組(P4)",
                set(r["upstream"]["seven"]) == set(V75_SEVEN) and "rc" in r and "lamps" in r and not loaded, (r["upstream"]["done"], sorted(loaded))))
    res.append(("② collect():rc_name · 健康 / 規範自查燈都有", "rc_name" in r and {"health", "conform"} <= set(r["lamps"]), r["lamps"]))
    with tempfile.TemporaryDirectory() as td:
        tr = Path(td)
        reg = tr / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        cfg = _v75_cfg()
        (reg / "VIA_InputConsole_Spec_v0100.json").write_text(json.dumps({"x": [{"id": V75_KEYS[cfg["system"]]["spec_id"], "state": "ON"}]}), encoding="utf-8")
        (reg / "VIA_Component_Inventory_SSOT_v0100.json").write_text(json.dumps({"records": [{"identity": cfg["manager_family"], "code": "VIA-SYS-TEST", "state": "ACTIVE"}]}), encoding="utf-8")
        up = v75_upstream(tr)
        res.append(("③ 夾具:只有規格冊與元件冊 → 七處只 spec / inventory 真,其餘照實 False(不假綠)",
                    up["seven"]["spec"] is True and up["seven"]["inventory"] == "VIA-SYS-TEST" and up["done"] == 2, up["seven"]))
        t0 = v75_token(tr, ["read", cfg["dir"] + "/x.py"], capture=True)
        res.append(("④ token:鎖冊不在 → ABSENT(不崩 · 其他功能照常)", t0["lamp"] == "ABSENT", t0))
    other = "functional modules/VRN/VRN_SystemManager_v0266.py" if _v75_cfg()["system"] == "VDF" else "functional modules/VDF/VDF_SystemManager_v0174.py"
    t1 = v75_token(root, ["read", other], capture=True)
    t2 = v75_token(root, ["chain", "CGC_MDL149_VeritasCentralGovernanceConsole"], capture=True)
    res.append(("⑤ token:目標是對等系統的檔 / 家族 → DENY(只讀自己的樹)", t1["lamp"] == "DENY" and t2["lamp"] == "DENY", (t1["lamp"], t2["lamp"])))
    t3 = v75_token(root, ["read", _v75_cfg()["dir"] + "/" + Path(__file__).name], capture=True)
    res.append(("⑥ token read 本檔:經鎖冊解析的工具出骨架卡 + [token 帳](鎖冊不在則照實 ABSENT)",
                (t3["lamp"] == "GREEN" and "[token 帳]" in (t3.get("out") or "")) or t3["lamp"] == "ABSENT", (t3["lamp"], t3.get("tool"), t3.get("ledger", "")[:60])))
    src = Path(__file__).read_text(encoding="utf-8")
    block = src[src.index("# ══════════════════════════ " + VERSION + ":"):]
    bad = re.findall(r"^\s*(?:import|from)\s+(CGC_\w+|VIA_VCGC_\w+|VRN\w*|VDF\w*)\b", block, re.M)
    gate_write = re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", block)
    ta = re.search(r"^\s*(?:import|from)\s+" + "ta" + "lib", block, re.M)
    res.append(("⑦ 本段原始碼:不 import 他系統 · 不寫同意閘 · 不碰 TA-Lib", not bad and not gate_write and not ta, (bad, bool(gate_write), bool(ta))))
    res.append(("⑧ 動詞齊:collect · token 都在原生動詞表", all(v in SM_NATIVE for v in V75_VERBS), ""))
    return res


SM_NATIVE = SM_NATIVE + tuple(v for v in V75_VERBS if v not in SM_NATIVE)
CORE.SM_NATIVE = SM_NATIVE                  # 規範自查(conform)看的動詞表含本版新動詞
CORE.SM_VERSION = VERSION
CORE.SM_TAG = SM_TAG
PRIOR.SM_VERSION = VERSION


def selftest() -> int:
    print(f"=== {SM_TAG} 自測(前版鏈 + 本版 collect / token)===", flush=True)
    cp = subprocess.run([sys.executable, str(PRIOR_PATH), "--selftest"], cwd=str(HERE), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    sys.stdout.write(cp.stdout)                # 前版自測在乾淨子行程跑(本版改過的全域值不干擾前版)
    prior_ok = cp.returncode == 0
    res = [("⓪ 前版 v0266 自測照過(乾淨子行程)", prior_ok, "")] + _v75_selftest_new()
    for name, ok, note in res[1:]:
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + str(note)) if note and not ok else ''}", flush=True)
    n = sum(1 for _, ok, _ in res if ok)
    print(f"[計] {SM_TAG} 薄尾 {n}/{len(res)} {'PASS' if n == len(res) else 'FAIL'}", flush=True)
    return 0 if n == len(res) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] and args[0] in V75_VERBS:
        return _v75_cmd(args[0], args[1:])
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(args)


if __name__ == "__main__":
    sys.exit(main())
