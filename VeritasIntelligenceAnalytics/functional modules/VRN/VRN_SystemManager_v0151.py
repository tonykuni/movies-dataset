#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0151 — 薄尾:讓 VRN 從 U/I 正常運作輸出(操作員 2026-10-10)。
  ① ui:頁上組指令的啟動器檔名不再寫死(v0101 已退役)→ 建頁時找 Downloads 最新 Invoke-VIA-Launch-v0*.ps1;
        左面板頂加「主作業」卡:extract loop --dir <預設夾>(VRN_Config input_dir;沒有就 C:\測試樣本報告)· 參數用逗號字串(啟動器 v0113+ 拆)· 執行(滑鼠)via:// 連結 · 選夾執行(dir=1)
        右面板「結果檔」加擷取摘要(帳 → 檔數 · READ/TEXT_DOC/REVIEW/ERROR · 良率 · 門檻燈 · 最新 sha8 夾)
  ② extract loop / extract gate 跑完寫 VIA_Reports/vrn/RESULT_extract_latest.json(頁上看得到)
  ③ config input_dir <夾>:VRN 自家設定冊 SSOT/VRN_Config_v0100.json(只增)
其餘動詞照前版鏈。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import datetime
import html
import importlib.util
import json
import os
import re
import sys
import urllib.parse
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0151"


def _vnum_v0151(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0151(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0151(p) < _vnum_v0151(__file__)), key=_vnum_v0151)
PRIOR = _load_v0151(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _home():
    return Path(os.environ.get("VIA_VRN_SSOT_HOME") or HERE)


def _rep():
    return Path(os.environ.get("VIA_VRN_HEALTH_OUT") or (_home().parents[1] / "VIA_Reports" / "vrn"))


def _cfg_path():
    return _home() / "SSOT" / "VRN_Config_v0100.json"


def config_get() -> dict:
    p = _cfg_path()
    try:
        return json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() else {}
    except ValueError:
        return {}


def config_set(key: str, val: str) -> dict:
    d = config_get()
    d.setdefault("schema", "VIA.VRN.Config.v1")
    d.setdefault("history", []).append({"ts": datetime.datetime.now().isoformat(timespec="seconds"), "key": key, "old": d.get(key), "new": val})
    d[key] = val
    _cfg_path().parent.mkdir(parents=True, exist_ok=True)
    _cfg_path().write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return d


def _launcher_name() -> str:
    dl = Path(os.environ.get("VIA_LAUNCHER_DIR") or (Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Downloads"))
    hits = sorted((p for p in dl.glob("Invoke-VIA-Launch-v0*.ps1") if not re.search(r"\(\d+\)", p.name)), key=lambda p: p.name)
    return hits[-1].name if hits else "Invoke-VIA-Launch-v0116.ps1"


def extract_summary() -> dict:
    g = PRIOR._resolve("extract_gate") or getattr(PRIOR, "extract_gate", None)
    gate = g() if g else {"n": 0, "counts": {}, "good_ratio": 0, "review": 0, "error": 0, "lamp": "GRAY"}
    led = _rep() / "extract" / "VRN_Extract_Ledger.jsonl"
    last = None
    if led.exists():
        for ln in led.read_text(encoding="utf-8").splitlines()[-1:]:
            try:
                last = json.loads(ln)
            except ValueError:
                pass
    out = {"verb": "extract_summary", "ts": datetime.datetime.now().isoformat(timespec="seconds"), "gate": gate, "last": {k: last.get(k) for k in ("sha8", "status", "file", "path", "ts")} if isinstance(last, dict) else None, "lamp": gate["lamp"]}
    _rep().mkdir(parents=True, exist_ok=True)
    (_rep() / "RESULT_extract_latest.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def _ui_patch(page: Path) -> dict:
    if not page.exists():
        return {"patched": False, "why": "頁不在"}
    h = page.read_text(encoding="utf-8", errors="replace")
    ln = _launcher_name()
    n_fix = len(re.findall(r"Invoke-VIA-Launch-v\d{4}\.ps1", h))
    h = re.sub(r"Invoke-VIA-Launch-v\d{4}\.ps1", ln, h)
    cfg = config_get()
    indir = cfg.get("input_dir") or r"C:\測試樣本報告"
    s = extract_summary()
    g = s["gate"]
    cmd = 'pwsh -ExecutionPolicy Bypass -File "$env:USERPROFILE\\Downloads\\%s" -Sub VRN -Verb extract -VerbArgs \'loop,--dir,%s,--rounds,2\'' % (ln, indir)
    uri = "via://VRN/extract?args=" + urllib.parse.quote("loop,--dir,%s,--rounds,2" % indir, safe="")
    uri_pick = "via://VRN/extract?args=" + urllib.parse.quote("loop,--rounds,2", safe="") + "&dir=1"
    lampc = {"GREEN": "var(--lamp-green,#16a34a)", "YELLOW": "var(--lamp-yellow,#eab308)", "RED": "var(--lamp-red,#dc2626)", "GRAY": "var(--lamp-gray,#9ca3af)"}.get(g["lamp"], "#9ca3af")
    counts = " ".join("%s=%s" % kv for kv in sorted(g.get("counts", {}).items())) or "尚未擷取"
    card = ("<div id='vrn-main-job' style='border:1px solid var(--border,#e0e0e0);border-radius:8px;padding:10px 12px;margin:0 0 10px;background:var(--card,#fff);font-size:12px'>"
            "<div style='font-weight:700;font-size:13px;margin-bottom:4px'>VRN 主作業 · 擷取測試夾(extract loop)</div>"
            "<div>輸入夾:<code>%s</code>(改:<code>config input_dir &lt;夾&gt;</code>)</div>"
            "<div style='margin:4px 0'>指令:<code style='user-select:all;word-break:break-all'>%s</code></div>"
            "<div><a href='%s' style='display:inline-block;padding:4px 10px;border:1px solid var(--border,#e0e0e0);border-radius:6px;text-decoration:none;margin-right:6px'>執行(滑鼠)</a>"
            "<a href='%s' style='display:inline-block;padding:4px 10px;border:1px solid var(--border,#e0e0e0);border-radius:6px;text-decoration:none'>選夾執行</a></div>"
            "<div style='margin-top:6px'><i style='display:inline-block;width:10px;height:10px;border-radius:50%%;background:%s;vertical-align:middle'></i> 上次擷取:檔 %s · %s · 良率 %.1f%% · REVIEW %s · ERROR %s · %s%s</div>"
            "<div style='color:var(--muted,#6b7280);font-size:11px;margin-top:2px'>門檻 READ+TEXT_DOC ≥ 95%% · ERROR 0 · REVIEW ≤ 5%% → 綠 = VRN 正常運作輸出;結果夾 VIA_Reports\\vrn\\extract\\&lt;sha8&gt;\\ · 帳 VRN_Extract_Ledger.jsonl · 摘要 RESULT_extract_latest.json</div></div>") % (
        html.escape(indir), html.escape(cmd), uri, uri_pick, lampc, g.get("n", 0), html.escape(counts), (g.get("good_ratio") or 0) * 100, g.get("review", 0), g.get("error", 0), g["lamp"], (" · 最新 " + str(s["last"].get("sha8") or s["last"].get("file") or "")) if s.get("last") else "")
    if "id='vrn-main-job'" not in h:
        m = re.search(r"(<body[^>]*>)", h)
        h = h[:m.end()] + card + h[m.end():] if m else card + h
    page.write_text(h, encoding="utf-8")
    return {"patched": True, "launcher": ln, "fixed_refs": n_fix, "input_dir": indir, "gate": g["lamp"]}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:2] == ["config", "input_dir"] and len(args) >= 3:
        d = config_set("input_dir", args[2])
        print("[計] VRN config input_dir = %s · 冊 %s · GREEN" % (d["input_dir"], _cfg_path().name))
        return 0
    if args[:1] == ["config"]:
        print("[計] VRN config · %s · %s" % (_cfg_path().name, json.dumps({k: v for k, v in config_get().items() if k != "history"}, ensure_ascii=False)))
        return 0
    if args[:1] == ["ui"]:
        rc = PRIOR.main(args)
        r = _ui_patch(_rep() / "VRN_UI_latest.html")
        print("[計] VRN ui v0151 · 主作業卡 · 啟動器 %s(修 %s 處舊名)· 輸入夾 %s · 擷取門檻 %s · %s" % (r.get("launcher"), r.get("fixed_refs"), r.get("input_dir"), r.get("gate"), "GREEN" if r.get("patched") else "YELLOW"))
        return rc
    if args[:2] in (["extract", "loop"], ["extract", "gate"]):
        rc = PRIOR.main(args)
        s = extract_summary()
        print("[計] 擷取摘要 → RESULT_extract_latest.json · %s · %s" % (" ".join("%s=%s" % kv for kv in sorted(s["gate"].get("counts", {}).items())), s["lamp"]))
        return rc
    return PRIOR.main(args)


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    td = Path(tempfile.mkdtemp(prefix="vrnui-"))
    home = td / "functional modules" / "VRN"
    (home / "SSOT").mkdir(parents=True)
    (td / "dl").mkdir()
    rep = td / "VIA_Reports" / "vrn"
    rep.mkdir(parents=True)
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_SSOT_HOME", "VIA_VRN_HEALTH_OUT", "VIA_LAUNCHER_DIR")}
    os.environ.update({"VIA_VRN_SSOT_HOME": str(home), "VIA_VRN_HEALTH_OUT": str(rep), "VIA_LAUNCHER_DIR": str(td / "dl")})
    (td / "dl" / "Invoke-VIA-Launch-v0117.ps1").write_text("x", encoding="utf-8")
    (td / "dl" / "Invoke-VIA-Launch-v0117 (1).ps1").write_text("x", encoding="utf-8")
    (rep / "VRN_UI_latest.html").write_text("<html><body><p>pwsh -File Invoke-VIA-Launch-v0101.ps1 -Sub VRN</p></body></html>", encoding="utf-8")
    config_set("input_dir", r"D:\reports")
    r = _ui_patch(rep / "VRN_UI_latest.html")
    h = (rep / "VRN_UI_latest.html").read_text(encoding="utf-8")
    chk("① ui patch:舊啟動器名 v0101 → Downloads 最新 v0117(略過 (1) 副本)· 主作業卡 · 輸入夾來自 config · via:// 連結 · RESULT_extract_latest.json", r["launcher"] == "Invoke-VIA-Launch-v0117.ps1" and "Invoke-VIA-Launch-v0101.ps1" not in h and "vrn-main-job" in h and "D:\\reports" in h and "via://VRN/extract?args=" in h and (rep / "RESULT_extract_latest.json").exists())
    r2 = _ui_patch(rep / "VRN_UI_latest.html")
    chk("② 重跑不重複插卡", (rep / "VRN_UI_latest.html").read_text(encoding="utf-8").count("vrn-main-job") == 1 and r2["patched"])
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("③ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    chk("④ 帶加速器橋", "[VIA:ACCEL-BRIDGE:v0100]" in Path(__file__).read_text(encoding="utf-8"))
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0151 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
