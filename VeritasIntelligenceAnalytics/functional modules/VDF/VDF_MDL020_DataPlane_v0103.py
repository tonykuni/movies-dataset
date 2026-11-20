#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_MDL020_DataPlane v0103 — 薄尾:自測不吃本機狀態(清單閘「找不到清單」改在暫存夾裡造)

壞在哪:v0102 自測 ⑤「前版 v0101 自測照過」紅(v0101 自測 10/11),紅的是 v0101 ⑦「backfill:清單閘紅(找不到清單)→ 不擷取不同步」。
根因(讀碼確認):
  · v0101 L625 ⑦ 只把 --lists-home 指到暫存的 nolists(不存在),就假設「到處都找不到清單」;L629 斷言閘紅。
  · 但清單閘 v0100 lists_home(L709-718)在 --lists-home 找不到時會往下找:L711 env VIA_VDF_FETCH_HOME →
    L713 資料家 → L714 倉內 VIA/VIA_Reports/vdf_fetch/dict 與 HERE/output_hub(兩個是模組常數 VIA / HERE,指到真的倉)。
  · 昨晚真擷取在倉內 VIA_Reports/vdf_fetch/dict 產出 0-1-TWStockList / 0-2-ActiveETFList → 閘找到真清單、不紅 →
    ⑦ 紅;而且 v0101 backfill(L348-353)接著 sync + view,view 沒給 root 時寫到真的 VIA_Reports/vdf/VDF_PARQUET_VIEW_latest(v0101 L481)。
  · v0102 L363-366 以子行程跑 v0101 自測,所以同一個本機狀態讓 v0102 ⑤ 跟著紅。
  → 自測的前提依賴「這台剛好沒有清單」,違反「自測不吃本機狀態」。擷取 / 同步 / 清單閘的正式邏輯沒有錯,不動。
本版改的(只有自測;其餘全部經 __getattr__ 轉接前版,main 除 --selftest 外原樣交給前版):
  ① 前版自測改在隔離子行程跑:清單閘的 lists_home 換成同一份程式碼、但 VIA / HERE 兩個常數指到空的暫存夾
     (env VIA_VDF_FETCH_HOME 在子行程拿掉);view 沒給 root 時寫到暫存夾。前版自測再以子行程叫更前版時同樣隔離。
  ② 對照組:同一個 v0101 自測,清單閘指到「放了清單」的暫存夾 → ⑦ 必須紅(證明 ⑦ 只看清單在不在);指到空暫存夾 → ⑦ 綠。
  ③ 真的清單夾(VIA_Reports/vdf_fetch/dict 與 VDF/output_hub 的 0-1-TWStockList · 0-2-ActiveETFList)與真的檢視頁
     自測前後逐檔比大小 + 修改時間,必須一樣(不建、不改、不刪)。
前版 v0102 / v0101 / v0100 一字不動(載入不改檔;前版以 glob 取比本版低的最高版號,不寫死檔名)。
零網路 · 不碰 TA-Lib · 不讀寫同意閘 · 不刪使用者的檔。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本支零外呼。"""
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

import hashlib
import importlib.util
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_MDL020_DataPlane"
TAG = STEM + " v" + Path(__file__).stem.rsplit("_v", 1)[-1]


def _vn(p) -> int:
    s = Path(p).stem.rsplit("_v", 1)[-1]
    return int(s) if len(s) == 4 and s.isdigit() else -1


MY_VN = _vn(__file__)


def _prior_path() -> Path:
    """比本版低的最高版號(glob 取,不寫死檔名);_sha 分身等不合 _vNNNN 的不算。"""
    cands = [p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vn(p) < MY_VN]
    if not cands:
        raise ImportError("%s:找不到比 v%04d 低的前版" % (TAG, MY_VN))
    return max(cands, key=_vn)


PRIOR_PATH = _prior_path()
PRIOR_NAME = PRIOR_PATH.name


def _load_prior():
    spec = importlib.util.spec_from_file_location("vdf_mdl020_prior_for_v%04d" % MY_VN, PRIOR_PATH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


V2 = _load_prior()                     # 前版(v0102;它的 V1 = v0101,P = v0100)
V1 = getattr(V2, "V1", V2)
P = V2.P
V2.TAG = V1.TAG = P.TAG = TAG


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接(先 v0102,再 v0101 / v0100)。"""
    return getattr(V2, name)


# ---------------------------------------------------------------- CLI:除 --selftest 外原樣交給前版
def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    return V2.main(args)


# ---------------------------------------------------------------- 自測隔離
# 隔離殼:自測時寫到暫存夾再以子行程跑(不落倉)。它載入前版檔(不改檔),把清單閘 lists_home 換成同一份程式碼、
# 只是 VIA / HERE 兩個常數指到暫存夾;env VIA_VDF_FETCH_HOME 拿掉;view 沒給 root 時寫到暫存夾;
# 前版自測再以子行程叫更前版的 --selftest 時,同樣經這個殼。
_BOOT = r'''# VDF_MDL020_DataPlane 自測隔離殼(v0103 自測寫到暫存夾;不落倉)
import importlib.util, os, re, subprocess, sys, types
from pathlib import Path
SRC, LISTS, VIEW_ROOT = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
os.environ.pop("VIA_VDF_FETCH_HOME", None)
_run = subprocess.run


def _iso_run(args, *a, **k):
    if isinstance(args, (list, tuple)) and len(args) == 3 and str(args[2]) == "--selftest" \
            and re.fullmatch(r"VDF_MDL020_DataPlane_v\d{4}\.py", Path(str(args[1])).name):
        args = [args[0], __file__, str(args[1]), str(LISTS), str(VIEW_ROOT)]
        env = dict(k.get("env") or os.environ)
        env.pop("VIA_VDF_FETCH_HOME", None)
        k["env"] = env
    return _run(args, *a, **k)


subprocess.run = _iso_run
spec = importlib.util.spec_from_file_location("vdf_mdl020_isolated_v" + Path(SRC).stem.rsplit("_v", 1)[-1], SRC)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
P = getattr(m, "P", m)
lh = P.lists_home
P.lists_home = types.FunctionType(lh.__code__, dict(lh.__globals__, VIA=LISTS / "via", HERE=LISTS / "vdf"),
                                  lh.__name__, lh.__defaults__, lh.__closure__)
owner = getattr(m, "V1", m)
if hasattr(owner, "view"):
    _view = owner.view

    def _iso_view(home, pq_dir=None, start=None, root=None, today=None):
        return _view(home, pq_dir, start, root or VIEW_ROOT, today)
    owner.view = _iso_view
print("[隔離] %s · 清單閘 VIA / HERE → 暫存夾 · env VIA_VDF_FETCH_HOME 拿掉 · view 預設 root → 暫存夾" % Path(SRC).name, flush=True)
sys.exit(m.selftest())
'''


def _run_isolated(src: Path, lists: Path, view_root: Path, boot: Path) -> tuple:
    """在隔離殼裡跑 src 的 --selftest → (rc, stdout, 計數行)。"""
    env = {k: v for k, v in os.environ.items() if k != "VIA_VDF_FETCH_HOME"}
    env["VIA_FROM_VDFSM"] = "YES"                       # VDF 自己的總控旗標(同 v0101 / v0102 叫前版自測);同意閘不代設
    cp = subprocess.run([sys.executable, str(boot), str(src), str(lists), str(view_root)], env=env, cwd=str(boot.parent),
                        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    out = cp.stdout or ""
    last = [x for x in out.splitlines() if x.startswith("[計]")]
    return cp.returncode, out + (cp.stderr or ""), (last[-1] if last else "")


def _list_fixture(d: Path) -> None:
    """暫存夾裡放一份合格的清單(同 v0101 ⑧ 的形狀,日期 = 今天,免得新鮮度閘把它判紅)。"""
    duckdb = P._duck()
    day = date.today().isoformat()
    (d / "0-1-TWStockList").mkdir(parents=True)
    (d / "0-2-ActiveETFList").mkdir(parents=True)
    con = duckdb.connect()
    con.execute("COPY (SELECT * FROM (VALUES ('%s', '2330', '2330.TW', 'TWSE', 'ACTIVE')) t(date, ticker, yf_ticker, market, status)) TO %s (FORMAT PARQUET)"
                % (day, P._lit(d / "0-1-TWStockList" / "tw_stock_list_latest.parquet")))
    con.execute("COPY (SELECT * FROM (VALUES ('%s', '00981A', '00981A.TW', 'TWSE', 'ACTIVE', true)) t(date, ticker, yf_ticker, market, status, domestic)) TO %s (FORMAT PARQUET)"
                % (day, P._lit(d / "0-2-ActiveETFList" / "active_etf_list_latest.parquet")))
    con.close()
    for sub in ("0-1-TWStockList", "0-2-ActiveETFList"):
        (d / sub / "verify_report.json").write_text('{"engine": "fixture", "date": "%s", "lamp": "GREEN", "checks": []}' % day, encoding="utf-8")
    (d / "0-2-ActiveETFList" / "active_etf_qualified_latest.csv").write_text("date,ticker,qualified,reason\n%s,00981A,True,ok\n" % day, encoding="utf-8")


def _guard_paths() -> list:
    """真的清單夾(清單閘倉內兩個後備位置)+ 真的檢視頁:自測不得建 / 改 / 刪。"""
    out = []
    for root in (P.VIA / "VIA_Reports" / "vdf_fetch" / "dict", P.HERE / "output_hub"):
        out += [root / "0-1-TWStockList", root / "0-2-ActiveETFList"]
    return out + [P.VIA / P.OUT_REL / (V1.VIEW_NAME + ext) for ext in (".html", ".json")]


def _snap(paths) -> dict:
    s = {}
    for p in paths:
        k = os.path.relpath(p, P.VIA)
        if p.is_dir():
            s[k] = ("dir", p.stat().st_mtime_ns)
            for f in sorted(p.rglob("*")):
                st = f.stat()
                s[os.path.relpath(f, P.VIA)] = ("dir" if f.is_dir() else "file", st.st_size, st.st_mtime_ns)
        elif p.is_file():
            st = p.stat()
            s[k] = ("file", st.st_size, st.st_mtime_ns)
        else:
            s[k] = None
    return s


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _line(out: str, mark: str) -> str:
    return next((x.strip() for x in out.splitlines() if x.strip().startswith(("[OK] " + mark, "[FAIL] " + mark))), "")


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:400]) if note and not cond else ""), flush=True)

    priors = sorted((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vn(p) < MY_VN), key=_vn)
    sha0 = {p.name: _sha(p) for p in priors}
    guard = _guard_paths()
    snap0 = _snap(guard)
    real = [k for k, v in snap0.items() if v and v[0] == "dir" and k.endswith("0-1-TWStockList")]
    print("  [資訊] 本機真清單夾:%s(自測不靠它;只比前後不變)" % (" · ".join(real) or "沒有"), flush=True)
    v1_src = Path(V1.__file__)
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        boot = t / "boot_isolated.py"
        boot.write_text(_BOOT, encoding="utf-8")
        empty, full = t / "lists_empty", t / "lists_full"
        empty.mkdir()
        _list_fixture(full / "via" / "VIA_Reports" / "vdf_fetch" / "dict")

        rc, out, last = _run_isolated(PRIOR_PATH, empty, t / "view_a", boot)
        chk("① 前版 %s 自測在隔離下照過(%s)· 它的「前版自測」那一檢也綠" % (PRIOR_PATH.stem.rsplit("_v", 1)[-1], last[4:] if last else "沒有計數行"),
            rc == 0 and "PASS" in last and "[FAIL]" not in out, out[-400:])

        rc, out, last = _run_isolated(v1_src, empty, t / "view_b", boot)
        l7 = _line(out, "⑦")
        chk("② 清單閘指到空暫存夾:v0101 ⑦「找不到清單 → 閘紅」綠 · v0101 自測照過(%s)" % (last[4:] if last else "沒有計數行"),
            rc == 0 and "PASS" in last and l7.startswith("[OK]"), out[-400:])

        rc, out, last = _run_isolated(v1_src, full, t / "view_c", boot)
        l7n = _line(out, "⑦")
        chk("③ 對照組:清單閘指到放了清單的暫存夾 → v0101 ⑦ 必紅(⑦ 只看清單在不在;本機有真清單時就是這樣紅的)",
            l7n.startswith("[FAIL]") and rc != 0, (l7n, last))
        chk("④ 隔離殼的檢視頁寫在暫存夾(view 沒給 root 不落倉)",
            any((t / v / P.OUT_REL / (V1.VIEW_NAME + ".html")).is_file() for v in ("view_a", "view_b", "view_c")))
    snap1 = _snap(guard)
    diff = sorted(k for k in set(snap0) | set(snap1) if snap0.get(k) != snap1.get(k))
    chk("⑤ 真的清單夾(%d 項:VIA_Reports/vdf_fetch/dict · VDF/output_hub 的 0-1 / 0-2)與真的檢視頁:前後大小 + 修改時間一樣(不建、不改、不刪)" % len(snap0),
        not diff, diff[:8])
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 薄尾:前版 = glob 取比本版低的最高版號(%s)· 前版檔前後 sha256 不變 · 前版公開名稱經 __getattr__ 轉接 · main 只攔 --selftest · 不碰 TA-Lib / 同意閘 · 兩座橋在" % PRIOR_NAME,
        priors and priors[-1] == PRIOR_PATH and sha0 == {p.name: _sha(p) for p in priors} and callable(__getattr__("status"))
        and __getattr__("backfill") is V2.backfill and "[VIA:ACCEL-BRIDGE:v0100]" in text and "[VIA:NET-BRIDGE:v0100]" in text
        and not re.search(r"^\s*(import|from)\s+(talib|CGC_|VRN_|VQG_|VAP_)", text, re.M) and ("environ[" + '"VIA_NET_' + 'CONSENT"]') not in text,
        (PRIOR_NAME, [p.name for p in priors]))
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
