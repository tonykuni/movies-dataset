#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0129 — 薄尾:activate 動詞 = VDF 啟動由 VDF System Manager 控管(啟動前可改各大類起始日 · 增減項目)

操作員 2026-10-05:「vcgc vdf vrn 為獨立系統 · vrn vdf 獨立性更強 · vdf 啟動指令應該由 vdf manager 控管 ·
  使用者啟動前有改各類型起始時間或要增減項目的權利」;「現在起權力下放子系統 · 掌握全局 · 母系統監控及衝突提醒全力 · 更改由我跟你定案」;
  本線(AI)經操作員授權出本版(VDF-REQ018;VCGC-REQ170 的 VDF 段)。
activate [--home 資料庫夾] [--start 大類=YYYY-MM-DD|default]… [--add 族群=值[,值]]… [--remove 族群=值[,值]]… [--import 頁上匯出.json] [--apply] [--no-open] [--as-of D]
  ① 現況:MDL012 start(各大類起始日 · 族群)
  ② 啟動前改(你的權利):--start / --add / --remove / --import 交 MDL012 自己的動詞;沒給 --apply = 乾跑只列計畫,成員帳本一個位元都不動
  ③ 讀庫現況:MDL012 monitor(族群筆數 · 最晚日 · 燈;沒料照實列,不算綠)
  ④ U/I:MDL012 ui → VIA_Reports/vdf/ui/VDF_FetchGroups_latest.html(不寫倉內已追蹤的 ui_support 頁)→ 預設瀏覽器 file:// 跳出
全部在本行程呼叫 VDF 自己的 MDL012 尾版(不另起 python、不經 VCGC 也能跑);其餘動詞照 v0128。
同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT)是操作員的手,本版不讀不寫。不碰 TA-Lib。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import sys
import time
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
_STEM = "VDF_SystemManager"
SUB = "VDF"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
OUT_DIR = VIA / "VIA_Reports" / "vdf" / "activate"
UI_OUT = VIA / "VIA_Reports" / "vdf" / "ui" / "VDF_FetchGroups_latest.html"     # 不寫倉內已追蹤的 ui_support 頁
ENTRY_VDFSM = "VIA_FROM_VDFSM"
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _vnum_v0129(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0129(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0129(p) < _vnum_v0129(__file__)), key=_vnum_v0129)
PRIOR = _load_v0129(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)
VERBS_v0129 = tuple(PRIOR.VERBS_v0128) + ("activate",)


def __getattr__(name):
    return getattr(PRIOR, name)


def mdl012():
    """VDF 擷取大族群尾版(起始日 · 成員增減 · 監控 · 頁都是它的);缺 = None(誠實 ABSENT)。"""
    tails = sorted(HERE.glob("VDF_MDL012_FetchGroups_v*.py"), key=_vnum_v0129)
    return _load_v0129(tails[-1], "vdf_mdl012_for_" + Path(__file__).stem) if tails else None


def call(mod, argv: list, capture: bool = False) -> tuple:
    """在本行程呼叫 MDL012 main(不另起 python;argparse 退出碼照收)。回 (rc, 輸出)。"""
    buf = io.StringIO()
    try:
        if capture:
            with contextlib.redirect_stdout(buf):
                rc = mod.main(list(argv))
        else:
            rc = mod.main(list(argv))
    except SystemExit as exc:
        rc = exc.code if isinstance(exc.code, int) else 2
    out = buf.getvalue()
    if capture and out:
        print(out, end="" if out.endswith("\n") else "\n", flush=True)
    return (rc or 0), out


def parse_edits(starts: list, adds: list, removes: list) -> tuple:
    """--start 大類=YYYY-MM-DD|default · --add 族群=值,值 · --remove 族群=值;格式錯 = 拒(不猜)。回 (ops, errors)。"""
    ops, errs = [], []
    for s in starts or []:
        cat, _, val = s.partition("=")
        if not cat or not (val == "default" or _DATE.match(val)):
            errs.append(f"--start {s}:要 大類=YYYY-MM-DD 或 大類=default(起始日只能按大類改)")
        else:
            ops.append(("start", cat.strip(), val.strip()))
    for kind, lst in (("add", adds), ("remove", removes)):
        for s in lst or []:
            grp, _, vals = s.partition("=")
            items = [v.strip() for v in vals.split(",") if v.strip()]
            if not grp or not items:
                errs.append(f"--{kind} {s}:要 族群=值[,值]")
            else:
                ops.append((kind, grp.strip(), items))
    return ops, errs


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16] if p.is_file() else "-"


def _lamp_line(rows: list, step: str, lamp: str, msg: str) -> None:
    rows.append({"step": step, "lamp": lamp, "summary": msg})
    print(f"  [{lamp:<6}] {step:<8} {msg}", flush=True)


def activate(rest: list) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog=f"{TAG} activate", description="VDF 啟動:現況 → 啟動前改(起始日 / 增減項目)→ 讀庫 → 跳出 U/I")
    ap.add_argument("--home"); ap.add_argument("--as-of")
    ap.add_argument("--start", action="append", default=[], metavar="大類=YYYY-MM-DD|default")
    ap.add_argument("--add", action="append", default=[], metavar="族群=值[,值]")
    ap.add_argument("--remove", action="append", default=[], metavar="族群=值[,值]")
    ap.add_argument("--import", dest="import_file", metavar="頁上匯出的輸入 .json")
    ap.add_argument("--apply", action="store_true", help="改動真的寫進成員帳本(只增);沒給 = 乾跑只列計畫")
    ap.add_argument("--no-open", action="store_true")
    try:
        a = ap.parse_args(rest)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    t0 = time.time()
    m = mdl012()
    if m is None:
        print(f"[ABSENT] {TAG}:VDF_MDL012_FetchGroups_v*.py 不在這棵樹")
        return 3
    home = ["--home", a.home] if a.home else []
    rows: list = []
    print(f"=== VDF 啟動(VDF System Manager 總控 · {TAG})· 資料庫 {a.home or '(MDL012 預設)'} ===", flush=True)

    print("  [1/4] 現況:各大類起始日 · 族群", flush=True)
    rc_s, _ = call(m, ["start"])
    _lamp_line(rows, "current", "GREEN" if rc_s == 0 else "RED", "起始日按大類(TW_MARKET · FIN · MACRO · OTHER);族群成員見 groups / members")

    print("  [2/4] 啟動前改(你的權利:各大類起始日 · 增減項目 · 頁上匯出的輸入)", flush=True)
    ops, errs = parse_edits(a.start, a.add, a.remove)
    for e in errs:
        print(f"    [拒絕] {e}")
    led = getattr(m, "LEDGER", None) or getattr(getattr(m, "V0100", None), "LEDGER", None)
    before = _sha(Path(led)) if led else "-"
    fails = 0
    for kind, key, val in ops:
        if kind == "start":
            argv = ["start", "--category", key, "--set", val]
        else:
            argv = [kind, key, *val] + home
        rc, _ = call(m, argv + (["--apply"] if a.apply else []))
        fails += rc != 0
    if a.import_file:
        rc, _ = call(m, ["ui-import", a.import_file] + (["--apply"] if a.apply else []))
        fails += rc != 0
    n_edit = len(ops) + (1 if a.import_file else 0)
    after = _sha(Path(led)) if led else "-"
    if errs or fails:
        _lamp_line(rows, "edit", "RED", f"改動 {n_edit} 項 · 拒絕 {len(errs)} · 失敗 {fails}(看上面每一行)")
    elif not n_edit:
        _lamp_line(rows, "edit", "GREEN", "沒有改動(照現況啟動);要改:--start 大類=日期 · --add 族群=值 · --remove 族群=值 · --import 檔,加 --apply 才寫")
    elif not a.apply:
        _lamp_line(rows, "edit", "YELLOW", f"乾跑:{n_edit} 項改動只列計畫,帳本未動(sha {before});確認後加 --apply 才寫入")
    else:
        _lamp_line(rows, "edit", "GREEN", f"已寫入 {n_edit} 項(成員帳本只增 · sha {before} → {after})")
        call(m, ["start"])

    print("  [3/4] 讀資料庫現況(族群筆數 · 最晚日 · 燈)", flush=True)
    rc_m, out_m = call(m, ["monitor"] + home + (["--as-of", a.as_of] if a.as_of else []), capture=True)
    lamps = re.findall(r"│\s*[A-Z][A-Z0-9_]+\s*│[^│]*│\s*\d+\s*│\s*(\d+)\s*│[^│]*│\s*([A-Z]+)\s*│", out_m)
    n_ok = sum(1 for _, lp in lamps if lp == "GREEN")
    _lamp_line(rows, "db", "RED" if rc_m not in (0, 2) else ("GREEN" if lamps and n_ok == len(lamps) else "YELLOW"),
               f"族群 {n_ok}/{len(lamps)} 有料(rc {rc_m};沒料的族群照實列,不算綠)")

    print("  [4/4] 產 U/I(VDF 擷取大族群正典頁 · file:// 零伺服器)", flush=True)
    UI_OUT.parent.mkdir(parents=True, exist_ok=True)
    rc_u, out_u = call(m, ["ui", "--out", str(UI_OUT)] + home + (["--as-of", a.as_of] if a.as_of else []), capture=True)
    page = UI_OUT if (rc_u == 0 and UI_OUT.is_file()) else None
    opened = False
    if page and not a.no_open:
        try:
            opened = webbrowser.open(page.resolve().as_uri())
        except Exception as exc:
            print(f"    [開] 預設瀏覽器開不了:{exc}")
    _lamp_line(rows, "ui", "GREEN" if page else "RED",
               (f"{page} · " + ("已跳出" if opened else ("沒跳出:--no-open" if a.no_open else "沒跳出:本機沒有可用瀏覽器 → 手動開上面的檔"))) if page else f"ui rc {rc_u}")

    lp = [r["lamp"] for r in rows]
    overall = "RED" if "RED" in lp else ("YELLOW" if "YELLOW" in lp else "GREEN")
    rep = {"engine": TAG, "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "overall": overall, "home": a.home,
           "apply": a.apply, "edits": [list(map(str, o)) for o in ops], "rejected": errs, "ledger_sha": [before, after],
           "steps": rows, "page": str(page) if page else None, "opened": opened, "sec": round(time.time() - t0, 1)}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "VDF_ACTIVATE_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [VDF 啟動] {overall} · 綠 {lp.count('GREEN')} · 黃 {lp.count('YELLOW')} · 紅 {lp.count('RED')} · {rep['sec']}s"
          f" · 報告 VIA_Reports/vdf/activate/VDF_ACTIVATE_latest.json", flush=True)
    return {"GREEN": 0, "YELLOW": 2, "RED": 1}[overall]


def main(argv=None) -> int:
    """activate 由本版接;其餘動詞照 v0128(總控標記 · 未知動詞拒跑)。"""
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] != ["activate"]:
        return PRIOR.main(args)
    had_vc, keep_vc = "VIA_FROM_VCGC" in os.environ, os.environ.get("VIA_FROM_VCGC")
    had_sm, keep_sm = ENTRY_VDFSM in os.environ, os.environ.get(ENTRY_VDFSM)
    os.environ[ENTRY_VDFSM] = "YES"
    os.environ["VIA_FROM_VCGC"] = "YES"
    try:
        return activate(args[1:])
    finally:
        for k, had, keep in (("VIA_FROM_VCGC", had_vc, keep_vc), (ENTRY_VDFSM, had_sm, keep_sm)):
            if had:
                os.environ[k] = keep
            else:
                os.environ.pop(k, None)


def selftest() -> int:
    prior_rc = PRIOR.selftest()
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {TAG} · 薄尾自測(activate:啟動前改 → 讀庫 → U/I)===")
    ops, errs = parse_edits(["TW_MARKET=2022-01-01", "FIN=default", "MACRO=2022/01/01", "=2022-01-01"], ["TW_FIN=2330, 3324"], ["INTL_FIN="])
    chk("① 改動格式:大類=日期 / default 收;斜線日期 · 空大類 · 空值 拒(不猜)",
        ops == [("start", "TW_MARKET", "2022-01-01"), ("start", "FIN", "default"), ("add", "TW_FIN", ["2330", "3324"])] and len(errs) == 3, (ops, errs))
    m = mdl012()
    led = Path(getattr(m, "LEDGER", None) or getattr(getattr(m, "V0100", None), "LEDGER", "")) if m else None
    before = _sha(led) if led else "-"
    saved = {k: os.environ.pop(k, None) for k in ("VIA_FROM_VCGC", ENTRY_VDFSM)}
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["activate", "--no-open", "--start", "TW_MARKET=2021-06-01", "--add", "TW_FIN=9999"])
            rc_bad = main(["activate", "--no-open", "--start", "TW_MARKET=yesterday"])
            rc_unknown = main(["actvate"])
        out = buf.getvalue()
        left = [k for k in ("VIA_FROM_VCGC", ENTRY_VDFSM) if k in os.environ]
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    rep = json.loads((OUT_DIR / "VDF_ACTIVATE_latest.json").read_text(encoding="utf-8")) if (OUT_DIR / "VDF_ACTIVATE_latest.json").is_file() else {}
    chk("② 沒給 --apply = 乾跑:成員帳本一個位元都沒動;改動列成計畫(edit 黃)", led is not None and _sha(led) == before and "乾跑" in out, before)
    chk("③ 四步都跑:現況 · 改動 · 讀庫 · U/I(頁寫 VIA_Reports,不碰倉內已追蹤的 ui_support 頁)",
        all(s in out for s in ("[1/4]", "[2/4]", "[3/4]", "[4/4]")) and UI_OUT.is_file() and rc in (0, 1, 2), rc)
    chk("④ 格式錯的改動 = edit RED · 整體 RED(rc 1);拼錯動詞照前版拒跑 rc 2", rc_bad == 1 and rc_unknown == 2, (rc_bad, rc_unknown))
    chk("⑤ 結束環境還原(不留 VIA_FROM_VCGC / VIA_FROM_VDFSM)· 報告寫 VIA_Reports/vdf/activate", not left and rep.get("engine") == TAG, left)
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ activate 進動詞表;加速器橋 · 網路工具橋 · 正典橋在;不碰 TA-Lib;不寫同意閘",
        "activate" in VERBS_v0129 and "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and "[VIA:LIB-BRIDGE" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", text))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if prior_rc == 0 else 'FAIL'} · 合計 {'PASS' if all(ok) and prior_rc == 0 else 'FAIL'}")
    return 0 if all(ok) and prior_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
