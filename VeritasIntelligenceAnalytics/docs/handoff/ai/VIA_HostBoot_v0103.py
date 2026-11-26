#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VIA_HostBoot v0103 — 薄尾(v0100–v0102 一字不動):新動詞 lake(桌機一行建 VDF 湖 → 立刻蒸餾 / 核對)

操作員 2026-11-26:「準備建湖指令」。桌機 vdf3 的 distill / reconcile 黃在「湖目錄不在(VDF_catalog.duckdb)」。
本版:暫切 origin/<分支>(同 vdf3,一定切回;已追蹤檔有改動 = 停不碰)在真倉依序跑:
  ① VDF_ENG239_ParquetLakeBuild 尾版 --selftest
  ② VDF_ENG239_ParquetLakeBuild 尾版 run --skip-fetch(不出網:只把資料家 / 倉內現有 DuckDB 入湖;只增分片;
     起日照操作員裁定 2018-01-01;湖在 <倉>\VeritasIntelligenceAnalytics\VIA_Reports\vdf_lake,不入版控)
  ③ VDF_SystemManager 尾版 three inventory · distill · reconcile(湖有了才有東西蒸餾 / 核對)
收據:每步主控台尾巴 + vdf_three 的 SUMMARY + LAKE_STATUS_latest.json(表名 · 列數 · 起訖日 · 分片數;不含任何數值資料)。
用法:python VIA_HostBoot_v0103.py --repo <倉> lake [--branch B] [--start YYYY-MM-DD] [--push]
其餘動詞(fnc · bak · vdf · vdfp · vdf3 · fin5y · hydra)全部照前版。不用 TA-Lib · 不設同意閘 · 本檔零外呼。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_roots = [_sa_Path(__file__).resolve(), _sa_Path.cwd().resolve()]
    import os as _sa_os
    if _sa_os.environ.get("VIA_REPO"):
        _sa_roots.insert(0, _sa_Path(_sa_os.environ["VIA_REPO"]).resolve() / "VeritasIntelligenceAnalytics")
    for _sa_p in _sa_roots:
        _sa_hit = None
        while True:
            for _sa_c in (_sa_p, _sa_p / "VeritasIntelligenceAnalytics"):
                if (_sa_c / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
                    _sa_hit = _sa_c
                    break
            if _sa_hit or _sa_p.parent == _sa_p:
                break
            _sa_p = _sa_p.parent
        if _sa_hit:
            _sa_sys.path.insert(0, str(_sa_hit / "supportive modules"))
            break
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import json
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

FAMILY = "VIA_HostBoot"
VERSION = "v0103"
TAG = f"{FAMILY} {VERSION}"
HERE = Path(__file__).resolve()
_T0 = time.time()


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_" + VERSION, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.PRIOR                                  # v0101:on_branch · newest · push_receipts · say · VIA_REL
VERBS = tuple(PRIOR.VERBS) + ("lake",)
VIA_NET_TOOL_PATH = getattr(PRIOR, "VIA_NET_TOOL_PATH", None)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def say(msg: str) -> None:
    BASE.say(msg)


def lake_steps(via: Path, live: bool, extra: list) -> list:
    eng = via / "functional modules" / "VDF" / "engine"
    lb = BASE.newest(eng, "VDF_ENG239_ParquetLakeBuild_v*.py")
    vm = BASE.newest(via / "functional modules" / "VDF", "VDF_SystemManager_v*.py")
    start = []
    if "--start" in extra:
        j = extra.index("--start")
        start = ["--start", extra[j + 1]]
    return [[str(lb), "--selftest"], [str(lb), "run", "--skip-fetch", *start]] + \
           [[str(vm), "three", v] for v in ("inventory", "distill", "reconcile")]


def run_lake(rest: list, repo: Path, out: Path, env: dict) -> int:
    if "--live" in rest:
        say("[RED] lake 不出網:不收 --live(要抓新資料走 vdf3 --live)")
        return 1
    t0 = time.time()
    rc = BASE.on_branch(rest, repo, out, env, "lake", lake_steps, ("vdf_three",))
    st = repo / BASE.VIA_REL / "VIA_Reports" / "vdf_lake" / "LAKE_STATUS_latest.json"
    if st.is_file() and st.stat().st_mtime >= t0 - 2:
        shutil.copyfile(st, out / "lake_LAKE_STATUS_latest.json")
        say(f"湖狀態收據 → {out / 'lake_LAKE_STATUS_latest.json'}")
    else:
        say("[黃] 這次沒有新的 LAKE_STATUS_latest.json(入湖那步沒跑成或沒寫)")
    return rc


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if "lake" not in argv:
        return PRIOR.main(argv)
    i = argv.index("lake")
    head, rest = argv[:i], argv[i + 1:]
    push = "--push" in head + rest
    head = [x for x in head if x != "--push"]
    rest = [x for x in rest if x != "--push"]
    if "--repo" not in head:
        say("[RED] 要 --repo <倉>")
        return 1
    repo = Path(head[head.index("--repo") + 1]).expanduser().resolve()
    if not (repo / BASE.VIA_REL).is_dir():
        say(f"[RED] 不是 VIA 倉:{repo}")
        return 1
    say(f"{TAG} · 倉 {repo} · 加速器 {'載入' if VIA_ACCEL is not None else '沒載到(黃)'} · 網路工具 {'在' if VIA_NET_TOOL_PATH else '不在(黃)'}")
    import os
    from datetime import datetime
    env = dict(os.environ, VIA_REPO=str(repo))
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(tempfile.gettempdir()) / f"via_hostboot_lake_{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    rc = run_lake(rest, repo, out, env)
    (out / "lake_RUN.json").write_text(json.dumps({"tool": TAG, "verb": "lake", "rc": rc, "secs": round(time.time() - _T0, 1), "args": rest,
                                                   "accel": VIA_ACCEL is not None, "net": VIA_NET_TOOL_PATH is not None}, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
    say(f"lake · rc {rc} · 收據 → {out}")
    if push:
        say(BASE.push_receipts(repo, out, stamp))
    say(f"完成 · rc {rc} · 總計 {time.time() - _T0:.0f}s")
    return rc


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("① 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("② 動詞表 = 前版七個 + lake", VERBS[:-1] == tuple(PRIOR.VERBS) and VERBS[-1] == "lake")
    via = HERE.parents[3]
    st = lake_steps(via, False, ["--start", "2018-01-01"])
    chk("③ 步驟:ENG239 尾版 --selftest → run --skip-fetch --start 2018-01-01 → VDF 管理器尾版 three inventory / distill / reconcile",
        Path(st[0][0]).name.startswith("VDF_ENG239_ParquetLakeBuild_v") and st[0][1] == "--selftest"
        and st[1][1:] == ["run", "--skip-fetch", "--start", "2018-01-01"]
        and [x[1:] for x in st[2:]] == [["three", "inventory"], ["three", "distill"], ["three", "reconcile"]]
        and Path(st[2][0]).name.startswith("VDF_SystemManager_v"), st)
    chk("④ 不帶 --start → run 只帶 --skip-fetch(起日交給 ENG239 尾版照 DataPlane 冊)", lake_steps(via, False, [])[1][1:] == ["run", "--skip-fetch"])
    with tempfile.TemporaryDirectory() as td:
        chk("⑤ lake 不收 --live(不出網)→ RED rc 1、不跑", run_lake(["--live"], Path(td), Path(td), {}) == 1)
        seen = {}
        keep = BASE.on_branch
        BASE.on_branch = lambda rest, repo, out, env, tag, fn, rd: seen.update(tag=tag, rd=rd, rest=rest) or 0
        try:
            rc = run_lake(["--branch", "b"], Path(td), Path(td), {})
        finally:
            BASE.on_branch = keep
        chk("⑥ 走 on_branch(暫切分支 · 一定切回)· tag lake · 收 vdf_three SUMMARY · --branch 交給 on_branch",
            rc == 0 and seen.get("tag") == "lake" and seen.get("rd") == ("vdf_three",) and "--branch" in seen.get("rest", []), seen)
    rc_p = PRIOR.selftest()
    chk("⑦ 前版 v0102 自測照過(rc 0)", rc_p == 0, rc_p)
    src = HERE.read_text(encoding="utf-8")
    chk("⑧ 檔面:第 3 行加速器標記 · glob 取前版 · 零 TA-Lib · 不設同意閘 · 不含本機路徑",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "HERE.parent.glob(FAMILY" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M)
        and "C:\\Users\\" + "tonyk" not in src)
    print(f"{TAG} selftest {sum(ok)}/{len(ok)}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
