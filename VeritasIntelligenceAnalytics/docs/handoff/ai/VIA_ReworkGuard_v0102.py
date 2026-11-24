#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_ReworkGuard v0102 — 薄尾(v0101 以前一字不動;v0100 / v0101 已鎖成功,修改開新版)

  PR 732 Codex P2:v0101 的撞號判斷把一筆紀錄附近的 key · identity · full · source · name 全混成一個集合,
  兩邊只要「任一個值」相同就當成同一個東西 → 同一個 source 檔裡兩個不同類別被發同號也不報(違反重號 0)。
  本版:每個號只取一個「正式身分」—— 那一筆紀錄自己的 key,沒有就 identity → full → declared(就近、同一筆);
        兩邊正式身分一樣才算同一個東西;拿不到正式身分 = 不能證明是同一個 → 照樣報撞號(保守)。
  另:自測先清掉 VIA_OPEN_PRS 再跑前版鏈(LL-20261124-07:v0100 自測情境 ②b 吃到 CI 的環境變數);跑完照原樣放回。
  其餘全照 v0101 / v0100(經 v0101 模組全域換上 added_ids;d_openpr 照 v0101)。
用法同 v0100:python VIA_ReworkGuard_v0102.py check [--fetch-prs] | report | causes | --selftest
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

VERSION = "v0102"
HERE = Path(__file__).resolve()
FAMILY = "VIA_ReworkGuard"
TAG = "VIA_ReworkGuard " + VERSION


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0102", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.P                                                               # v0100(main / render / CAUSES 的本體)
_V0101_ADDED, _V0101_TAG, _V0101_INSTALL = PRIOR.added_ids, PRIOR.TAG, PRIOR._install
CANON_KEYS = ("key", "identity", "full", "declared")
_FIELD = re.compile(r'"(%s)"\s*:\s*"([^"]{2,200})"' % "|".join(CANON_KEYS))


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _canon(lines, i) -> str | None:
    """第 i 行那一筆紀錄的正式身分:jsonl 一列一筆看本列;多行 json 由本行往上找到 '{' 為止、往下到 '}' 為止(同一筆)。"""
    ln = lines[i]
    if ln.count('"') > 4:
        rec = [ln]
    else:
        lo = i
        while lo > 0 and "{" not in lines[lo] and i - lo < 40:
            lo -= 1
        hi = i
        while hi < len(lines) - 1 and "}" not in lines[hi] and hi - i < 40:
            hi += 1
        rec = lines[lo: hi + 1]
    found = {}
    for x in rec:
        for k, v in _FIELD.findall(x):
            found.setdefault(k, v)
    return next((found[k] for k in CANON_KEYS if k in found), None)


def added_ids(repo, rng) -> dict:
    """同 v0101(只認代碼欄位的號),但每個號回傳 {正式身分};拿不到正式身分 → 每次都不一樣的記號(不能證明是同一個 → 照報)。"""
    lines = [ln[1:] for ln in BASE.git(repo, "diff", "-U0", rng, check=False).splitlines() if ln.startswith("+") and not ln.startswith("+++")]
    out = {}
    for i, ln in enumerate(lines):
        for c in PRIOR.CODE_KEY.findall(ln):
            if not BASE.NUM_ID.fullmatch(c):
                continue
            ident = _canon(lines, i)
            out.setdefault(c, set()).add(ident if ident else "<無正式身分:%s:%d:%s>" % (rng, i, c))
    return out


def _install():
    _V0101_INSTALL()
    PRIOR.added_ids = added_ids                                              # v0101 d_openpr 叫模組全域 added_ids → 換上本版
    BASE.TAG = TAG
    for c in BASE.CAUSES:
        c["cmd"] = c["cmd"].replace(PRIOR_PATH.name, HERE.name)


_install()


def run_check(*a, **kw) -> dict:
    r = PRIOR.run_check(*a, **kw)
    r["tool"] = TAG
    return r


def selftest() -> int:
    import contextlib
    import io
    import shutil
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)

    keep = os.environ.pop("VIA_OPEN_PRS", None)                              # LL-20261124-07:自測不吃執行環境
    buf = io.StringIO()
    try:
        PRIOR.added_ids, BASE.TAG = _V0101_ADDED, _V0101_TAG
        with contextlib.redirect_stdout(buf):
            rc0 = PRIOR.selftest()                                           # v0101 自測照 v0101 的函式跑(它再照 v0100 跑前版)
    finally:
        _install()
    print(f"=== {TAG} · 薄尾自測(正式身分比對 · 自測不吃環境變數 · 前版原封不動;暫存 git 倉 · 零網路)===", flush=True)
    chk("⓪ 前版 %s 自測照過(含 v0100;VIA_OPEN_PRS 已先清掉)" % PRIOR_PATH.name, rc0 == 0, buf.getvalue()[-300:])
    td = Path(tempfile.mkdtemp(prefix="via_rework102_"))
    try:
        r = td / "repo"
        r.mkdir()

        def sh(*a):
            return BASE.git(r, *a)
        sh("init", "-q", "-b", "main")
        sh("config", "user.email", "t@example.invalid")
        sh("config", "user.name", "t")
        sh("config", "commit.gpgsign", "false")
        reg = r / BASE.VIA / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        inv = reg / "VIA_Inv_v0100.json"
        inv.write_text("{}", encoding="utf-8")
        sh("add", "-A")
        sh("commit", "-qm", "base")
        sh("update-ref", "refs/remotes/origin/main", "HEAD")

        def side(branch, rows, ref=None):
            sh("checkout", "-q", "-B", branch, "origin/main")
            inv.write_text(json.dumps({"rows": rows}, indent=1), encoding="utf-8")
            sh("add", "-A")
            sh("commit", "-qm", branch)
            if ref:
                sh("update-ref", ref, "HEAD")
        side("pr5", [{"key": "class|Hub:A", "code": "VIA-CLS-0900", "source": "shared.py"}], "refs/remotes/pr/5")
        side("work", [{"key": "class|Hub:B", "code": "VIA-CLS-0900", "source": "shared.py"}])
        a = run_check(r, "origin/main", "HEAD", open_prs={"5"})
        chk("① PR 732 Codex P2:同一個 source 裡兩個不同類別(key 不同)發同號 → 紅 R2", any(f["lamp"] == "RED" and "VIA-CLS-0900" in f["what"] for f in a["findings"]), a["findings"])
        side("work", [{"key": "class|Hub:A", "code": "VIA-CLS-0900", "source": "shared.py", "first_seen": "t2"}])
        b = run_check(r, "origin/main", "HEAD", open_prs={"5"})
        chk("② 兩邊替同一個元件(key 相同)登同號 → 不算撞號", not any("VIA-CLS-0900" in f["what"] for f in b["findings"]), b["findings"])
        side("pr5", [{"code": "VIA-CLS-0901", "source": "x.py"}], "refs/remotes/pr/5")
        side("work", [{"code": "VIA-CLS-0901", "source": "x.py"}])
        c = run_check(r, "origin/main", "HEAD", open_prs={"5"})
        chk("③ 兩邊都沒有正式身分(只有 source)→ 不能證明是同一個 → 照報紅", any(f["lamp"] == "RED" and "VIA-CLS-0901" in f["what"] for f in c["findings"]), c["findings"])
        lines = ['{"code":"VIA-MDL-1","full":"VIA-MDL-1 X_v0100","source":"s"}', '  {', '   "key": "k1",', '   "code": "VIA-CLS-1",', '   "source": "s"', '  },',
                 '  {', '   "code": "VIA-CLS-2",', '   "identity": "k2"', '  }']
        chk("④ 正式身分只取同一筆:jsonl 本列 full · 多行 json 同一個 { } 裡的 key / identity(不越過別筆)",
            _canon(lines, 0) == "VIA-MDL-1 X_v0100" and _canon(lines, 3) == "k1" and _canon(lines, 7) == "k2")
    finally:
        shutil.rmtree(td, ignore_errors=True)
        if keep is not None:
            os.environ["VIA_OPEN_PRS"] = keep
    os.environ["VIA_OPEN_PRS"] = "999"
    try:
        buf2 = io.StringIO()
        PRIOR.added_ids, BASE.TAG = _V0101_ADDED, _V0101_TAG
        try:
            with contextlib.redirect_stdout(buf2):
                rc_env = selftest_prior_only()
        finally:
            _install()
    finally:
        if keep is None:
            os.environ.pop("VIA_OPEN_PRS", None)
        else:
            os.environ["VIA_OPEN_PRS"] = keep
    chk("⑤ 執行環境設了 VIA_OPEN_PRS(CI 情境)前版鏈自測照過(本版先清掉再跑)", rc_env == 0, buf2.getvalue()[-200:])
    chk("⑥ 本版真的換上:v0101 模組的 added_ids 是本版 · 工具名本版 · 內建指令指向本檔",
        PRIOR.added_ids is added_ids and BASE.TAG == TAG and any(HERE.name in c["cmd"] for c in BASE.CAUSES))
    src = HERE.read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑦ 加速器橋 · 不出網 · 不碰 TA-Lib · 不設他系統入口旗標", "import VIA_SuperAccel_Module" in src and "talib" not in body.lower()
        and not re.search(r"^\s*(import|from)\s+(requests|urllib|socket|http)\b", src, re.M)
        and not re.search(r"environ(?:\[[\"']VIA_FROM_\w+[\"']\]\s*=|\.setdefault\([\"']VIA_FROM_)", body))
    pub = [n for n in vars(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n)) and getattr(getattr(PRIOR, n), "__module__", "") == PRIOR.__name__]
    chk("⑧ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), f"{len(pub)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def selftest_prior_only() -> int:
    """只跑前版鏈自測(先清 VIA_OPEN_PRS),給 ⑤ 驗「CI 設了環境變數也照過」。"""
    keep = os.environ.pop("VIA_OPEN_PRS", None)
    try:
        return PRIOR.selftest()
    finally:
        if keep is not None:
            os.environ["VIA_OPEN_PRS"] = keep


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    BASE.run_check = run_check
    return BASE.main(a)


if __name__ == "__main__":
    sys.exit(main())
