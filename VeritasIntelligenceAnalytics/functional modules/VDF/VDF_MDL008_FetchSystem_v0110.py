#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL008_FetchSystem v0110 — 薄尾:擷取冊一律整本讀尾版(冊 v0108 才有的 014 三代號宇宙 · 加權 / 櫃買雙指數終於跑得到)

操作員 2026-11-15 令:「VDF 中有自動生成所有台股個股引擎 + 加權櫃買雙指數 · 自動生成主動式台股 ETF 名單 · 名單自動更新驗證 ·
這兩個引擎跑出來加速器及網路工具覆蓋率測試器動無誤 不然修到好」。
容器實測(總控 v0181 → 擷取系統尾版 v0109):fetch run 009 / 010 / e232 計畫照常;fetch run 014 → 「[拒跑] 冊上沒有 014」。
根因:擷取冊 v0107 加了 014(VDF_MDL014_ThreeCodeUniverse:個股 · 主動式 ETF · 加權 / 櫃買指數 → OUT-01;操作員 2026-11-08 令),
冊 v0108 再把 009 改指 MDL009 v0103;可是擷取系統 v0107 / v0108 的載冊都還是讀「冊 v0106」(36 支),v0108 只從冊 v0108 抽 009 那一列換上
→ 014 從來沒進過擷取系統的冊,三代號宇宙(含雙指數)經擷取系統永遠被拒。冊 v0106 與 v0108 的差別只有兩列:009(已換)· 014(漏)。
本版只改一件事:載冊改讀「最新版號的擷取冊」整本(VDF_FetchSystem_SSOT_v*.json 尾版;經 v0107 同一個載冊函式);
某列的引擎檔這台沒有 → 那一列照舊用冊 v0106 的(檔也不在就照列,跑的時候照實 ABSENT,不假造)。
子行程照 v0109 的作法改指本檔(run 期間 v0107 的 __file__ = 本檔)→ 子行程也讀尾版冊。
其餘(live 改道 · curl_cffi · 列上限 · 輸出路徑 · 參數 · 同意閘)全照 v0109。不碰 TA-Lib;不讀寫同意閘;零網路(自測)。
用法同前(總控 fetch run 014 --apply);自測 --selftest(本版)· --selftest --deep(+ 前版鏈)。
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


import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL008_FetchSystem"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
BOOK_GLOB_V0110 = "VDF_FetchSystem_SSOT_v*.json"


def _vnum_v0110(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0110(p) < _vnum_v0110(__file__)), key=_vnum_v0110)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0108 = PRIOR.PRIOR
V0107, V0105, V0101, BASE = PRIOR.V0107, PRIOR.V0105, PRIOR.V0101, PRIOR.BASE
_LOAD_V0107 = V0108._LOAD_V0107                        # v0107 的載冊函式(冊 v0106 的讀法)
_RUN_V0109 = PRIOR.run_v0109
BOOK_V0106 = V0107.BOOK_V0106


def __getattr__(name):
    return getattr(PRIOR, name)


def book_tail_v0110(folder: Path = HERE) -> Path | None:
    hits = [p for p in Path(folder).glob(BOOK_GLOB_V0110) if _vnum_v0110(p) >= 0]
    return max(hits, key=_vnum_v0110) if hits else None


def load_book_v0110(path: Path | None = None) -> dict:
    """擷取冊整本讀尾版;某列的引擎檔這台沒有 → 那列照冊 v0106(也沒有就照列,跑時照實 ABSENT)。"""
    tail = book_tail_v0110() if path is None or Path(path) == BOOK_V0106 else Path(path)
    if tail is None:
        return _LOAD_V0107(BOOK_V0106)
    bk = _LOAD_V0107(tail)
    old = {r.get("id"): r for r in (_LOAD_V0107(BOOK_V0106).get("engines") or [])} if tail != BOOK_V0106 else {}
    rows, kept_old = [], []
    for r in bk.get("engines") or []:
        f = r.get("file") or ""
        if f and not (HERE / f).is_file() and r.get("id") in old and (HERE / (old[r["id"]].get("file") or "")).is_file():
            rows.append(dict(old[r["id"]]))
            kept_old.append(r.get("id"))
        else:
            rows.append(r)
    bk["engines"] = rows
    bk["book_v0110"] = {"file": tail.name, "engines": len(rows), "kept_v0106_rows": kept_old}
    return bk


def run_v0110(*args, **kwargs):
    """同 v0109 run;呼叫期間 v0107 的 __file__ 指向本檔 → 子行程 = 本版(讀尾版冊)。結束還原。"""
    keep = V0107.__dict__.get("__file__")
    V0107.__dict__["__file__"] = str(Path(__file__).resolve())
    try:
        return PRIOR._RUN_V0107(*args, **kwargs)
    finally:
        V0107.__dict__["__file__"] = keep


def _install_v0110() -> None:
    V0101.load_book_v0101 = BASE.load_book = load_book_v0110
    V0105.PRIOR.load_book_v0104 = V0105.load_book_v0105 = V0107.PRIOR.load_book_v0106 = V0107.load_book_v0107 = load_book_v0110
    V0108.load_book_v0108 = load_book_v0110
    V0105.PRIOR.run_v0104 = V0101.run_v0101 = V0105.PRIOR.V0102.run_v0102 = BASE.run = run_v0110
    V0105.run_v0105 = V0107.PRIOR.run_v0106 = V0107.run_v0107 = PRIOR.run_v0109 = run_v0110


def _restore_v0109() -> None:
    PRIOR.run_v0109 = _RUN_V0109
    V0108.load_book_v0108 = _ORIG_LOAD_V0108
    PRIOR._restore_v0108()                             # v0107 run 還原 → v0107 換裝 → v0108 載冊換裝
    PRIOR._install_v0109()                             # 再裝 v0109 的 run(子行程 = v0109)


_ORIG_LOAD_V0108 = V0108.load_book_v0108
_install_v0110()


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest(deep=False)
    if args == ["--selftest", "--deep"]:
        return selftest(deep=True)
    return PRIOR.PRIOR.main(args)                      # v0108 main(v0109 main 只多分自測;換裝已是本版)


_CHILD_PROBE_V0110 = ("import importlib.util,sys,json;from pathlib import Path;p=Path(sys.argv[1]);"
                      "s=importlib.util.spec_from_file_location('mdl008_child_probe',p);c=importlib.util.module_from_spec(s);"
                      "sys.modules['mdl008_child_probe']=c;s.loader.exec_module(c);b=c.BASE.load_book();"
                      "print(json.dumps({'n':len(b['engines']),'ids':[r['id'] for r in b['engines']],"
                      "'f009':next(r['file'] for r in b['engines'] if r['id']=='009')}))")


def _child_cmd_v0110(row_id: str = "009") -> list:
    """實跑一次 run(假 subprocess,不起真子行程、不連網),回子行程指令。"""
    seen = []
    real = subprocess.run

    def fake(cmd, *a, **k):
        if isinstance(cmd, list) and "_child" in cmd:
            seen.append(list(cmd))
            return subprocess.CompletedProcess(cmd, 0, "", "")
        return real(cmd, *a, **k)
    row = next(r for r in BASE.load_book()["engines"] if r["id"] == row_id)
    subprocess.run = fake
    try:
        with tempfile.TemporaryDirectory() as td:
            BASE.run([row], "live", Path(td) / "dict", Path(td) / "logs", 5)
    finally:
        subprocess.run = real
    return seen[0] if seen else []


def selftest(deep: bool = False) -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    rc0 = None
    if deep:
        _restore_v0109()
        try:
            rc0 = PRIOR.selftest(deep=True)
        finally:
            _install_v0110()
    print(f"=== {TAG} · 薄尾自測(擷取冊整本讀尾版 · 014 三代號宇宙跑得到)===")
    if deep:
        chk("⓪ 前版鏈 v0109(含 v0108 · 子行程 · 冊 009)自測過", rc0 == 0, f"rc {rc0}")
    tail = book_tail_v0110()
    raw = json.loads(tail.read_text(encoding="utf-8")) if tail else {}
    bk = BASE.load_book()
    ids = [r["id"] for r in bk["engines"]]
    chk("① 載冊 = 尾版冊整本(%s · %d 支)· 有 014 三代號宇宙 · 有 e232 官方雙指數 · 009 → MDL009 v0103" % (tail.name if tail else "—", len(ids)),
        tail is not None and ids == [r["id"] for r in raw.get("engines", [])] and "014" in ids and "e232" in ids
        and next(r["file"] for r in bk["engines"] if r["id"] == "009") == "VDF_MDL009_TWStockList_v0103.py", ids[-4:])
    _restore_v0109()
    try:
        old_ids = [r["id"] for r in BASE.load_book()["engines"]]
    finally:
        _install_v0110()
    chk("② 重現:前版 v0109 的冊沒有 014(%d 支)→ fetch run 014 被拒;本版有" % len(old_ids), "014" not in old_ids and "014" in ids)
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = BASE.main(["plan", "009", "010", "e232", "014"])
    out = buf.getvalue()
    pos = [out.find(k) for k in ("MDL009", "MDL010", "ENG232", "MDL014")]
    chk("③ fetch plan 009 010 e232 014:不拒跑 · 照相依排 009 / 010 → e232 → 014(014 標「需 009,010,e232」)· 計畫不執行、零網路",
        rc == 0 and "拒跑" not in out and min(pos) >= 0 and pos == sorted(pos) and "需 009,010,e232" in out, out[-500:])
    cmd = _child_cmd_v0110("014")
    chk("④ 子行程檔 = 本檔(子行程也讀尾版冊)", len(cmd) > 3 and Path(cmd[3]).name == Path(__file__).name, cmd[:4])
    r = subprocess.run([sys.executable, "-c", _CHILD_PROBE_V0110, str(Path(__file__).resolve())], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=300)
    try:
        child = json.loads((r.stdout.strip().splitlines() or ["{}"])[-1])
    except ValueError:
        child = {}
    chk("⑤ 子行程(乾淨直譯器載本檔)讀到同一本尾版冊:%s 支 · 有 014 · 009 → v0103" % child.get("n"),
        child.get("ids") == ids and child.get("f009") == "VDF_MDL009_TWStockList_v0103.py", (r.stdout[-200:], r.stderr[-200:]))
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        b6 = json.loads(BOOK_V0106.read_text(encoding="utf-8"))
        b9 = dict(raw)
        b9["engines"] = [dict(e, file="VDF_MDL009_Gone_v9999.py") if e["id"] == "009" else e for e in raw.get("engines", [])]
        (d / "VDF_FetchSystem_SSOT_v9999.json").write_text(json.dumps(b9, ensure_ascii=False), encoding="utf-8")
        got = load_book_v0110(d / "VDF_FetchSystem_SSOT_v9999.json")
        f9 = next(r["file"] for r in got["engines"] if r["id"] == "009")
    chk("⑥ 尾版冊某列的檔這台沒有 → 那列照冊 v0106(不假造)· 其餘照尾版", f9 == next(r["file"] for r in b6["engines"] if r["id"] == "009")
        and got["book_v0110"]["kept_v0106_rows"] == ["009"] and "014" in [r["id"] for r in got["engines"]], got.get("book_v0110"))
    chk("⑦ run 呼叫完 v0107 的 __file__ 還原 · 換裝全指本版(載冊 · run)",
        Path(V0107.__dict__.get("__file__", "")).name == "VDF_MDL008_FetchSystem_v0107.py" and BASE.load_book is load_book_v0110
        and V0101.load_book_v0101 is load_book_v0110 and V0108.load_book_v0108 is load_book_v0110 and BASE.run is run_v0110
        and V0107.run_v0107 is run_v0110)
    text = Path(__file__).read_text(encoding="utf-8")
    body = text.split("def selftest", 1)[0]
    chk("⑧ 加速器橋 · 網路橋在;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and "def _via_net" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", body))
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑨ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), f"{len(names)} 支")
    tailnote = "" if deep else " · 前版鏈自測另跑(--selftest --deep)"
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 合計 {'PASS' if all(ok) else 'FAIL'}{tailnote}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
