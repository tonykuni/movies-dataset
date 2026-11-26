#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VIA_HostBoot v0102 — 薄尾(v0100 / v0101 一字不動):新動詞 hydra(桌機一行跑 VCGC 三回合探針到 via_01_vdf)

操作員 2026-11-26:「請問目前短指令有以下這套短指令嗎?若有如下面內容優化,用 py 寫 AST 導入加速器」(目標夾
~\OneDrive\Documents\VeritasIntelligenceAnalytics\via_01_vdf,只在桌機)。VCGC 的省 Token 工具 CGC_MDL158 v0122 已加 hydra 動詞;
本版讓桌機一行就能跑它(同 vdf3:暫切 origin/<分支> 在真倉取 VCGC 尾版 → 一定切回),戰報 JSON(只有程式碼結構:檔 · 行 · 類別 ·
依賴邊;不含資料)跟收據一起 --push 回來給 AI 讀。
用法:python VIA_HostBoot_v0102.py --repo <倉> hydra [--dir <夾>]… [--apply] [--branch B] [--push]
  --dir 不給 = ~/OneDrive/Documents/VeritasIntelligenceAnalytics/via_01_vdf(在才掃;不在就照實 RED,不猜別的夾)
  不帶 --apply = 乾跑(零寫入);帶 --apply = 照 CGC_MDL158 hydra 的規矩只修 ENCODING · BOM(備份 · 重掃不變差 · 不過還原)。
其餘動詞(fnc · bak · vdf · vdfp · vdf3 · fin5y)全部照 v0101。
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
import sys
import tempfile
import time
from pathlib import Path

FAMILY = "VIA_HostBoot"
VERSION = "v0102"
TAG = f"{FAMILY} {VERSION}"
HERE = Path(__file__).resolve()
_T0 = time.time()
DEFAULT_DIR = Path.home() / "OneDrive" / "Documents" / "VeritasIntelligenceAnalytics" / "via_01_vdf"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(str(p)).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_" + VERSION, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
VERBS = tuple(PRIOR.VERBS) + ("hydra",)
VIA_NET_TOOL_PATH = getattr(PRIOR, "VIA_NET_TOOL_PATH", None)
_via_net = getattr(PRIOR, "_via_net", None)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def say(msg: str) -> None:
    PRIOR.say(msg)


def hydra_dirs(rest: list) -> tuple:
    """--dir 可重複;沒給 = 預設 via_01_vdf。→ (dirs, 其餘參數)"""
    rest, dirs = list(rest), []
    while "--dir" in rest:
        j = rest.index("--dir")
        dirs.append(str(Path(rest[j + 1]).expanduser()))
        del rest[j:j + 2]
    return (dirs or [str(DEFAULT_DIR)]), rest


def run_hydra(rest: list, repo: Path, out: Path, env: dict) -> int:
    dirs, rest = hydra_dirs(rest)
    missing = [d for d in dirs if not Path(d).exists()]
    if missing:
        say(f"[RED] 目標夾不在:{missing}(--dir 指定;不猜別的夾)")
        return 1
    report = out / "hydra_report.json"

    def steps(via: Path, live: bool, extra: list) -> list:
        t = PRIOR.newest(via / "supportive modules" / "registry", "CGC_MDL158_VIAPanoramaAuditRepair_v*.py")
        return [[str(t), "hydra", *dirs, *[x for x in extra if x in ("--apply",)], "--out", str(report), "--max", "60"]]
    return PRIOR.on_branch(rest, repo, out, env, "hydra", steps, ())


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if "hydra" not in argv:
        return PRIOR.main(argv)
    i = argv.index("hydra")
    head, rest = argv[:i], argv[i + 1:]
    push = "--push" in head + rest
    head = [x for x in head if x != "--push"]
    rest = [x for x in rest if x != "--push"]
    if "--repo" not in head:
        say("[RED] 要 --repo <倉>")
        return 1
    repo = Path(head[head.index("--repo") + 1]).expanduser().resolve()
    if not (repo / PRIOR.VIA_REL).is_dir():
        say(f"[RED] 不是 VIA 倉:{repo}")
        return 1
    say(f"{TAG} · 倉 {repo} · 加速器 {'載入' if VIA_ACCEL is not None else '沒載到(黃)'} · 網路工具 {'在' if VIA_NET_TOOL_PATH else '不在(黃)'}")
    import os
    from datetime import datetime
    env = dict(os.environ, VIA_REPO=str(repo))
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(tempfile.gettempdir()) / f"via_hostboot_hydra_{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    rc = run_hydra(rest, repo, out, env)
    (out / "hydra_RUN.json").write_text(json.dumps({"tool": TAG, "verb": "hydra", "rc": rc, "secs": round(time.time() - _T0, 1), "args": rest,
                                                    "accel": VIA_ACCEL is not None, "net": VIA_NET_TOOL_PATH is not None}, ensure_ascii=False, indent=1),
                                        encoding="utf-8")
    say(f"hydra · rc {rc} · 收據 → {out}")
    if push:
        say(PRIOR.push_receipts(repo, out, stamp))
    say(f"完成 · rc {rc} · 總計 {time.time() - _T0:.0f}s")
    return rc


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("① 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("② 動詞表 = 前版六個 + hydra", VERBS[:-1] == tuple(PRIOR.VERBS) and VERBS[-1] == "hydra" and len(VERBS) == len(PRIOR.VERBS) + 1)
    d, r = hydra_dirs(["--dir", "~/x", "--apply", "--dir", "/y"])
    d0, _ = hydra_dirs([])
    chk("③ --dir 可重複 · ~ 展開 · 其餘參數保留;沒給 = 預設 via_01_vdf",
        d == [str(Path("~/x").expanduser()), "/y"] and r == ["--apply"] and d0 == [str(DEFAULT_DIR)], (d, r, d0))
    seen = {}
    keep = PRIOR.on_branch
    PRIOR.on_branch = lambda rest, repo, out, env, tag, steps_fn, rd: seen.update(
        steps=steps_fn(Path(repo) / PRIOR.VIA_REL, False, rest), tag=tag, rest=rest) or 0
    try:
        with tempfile.TemporaryDirectory() as td:
            tgt = Path(td) / "via_01_vdf"
            tgt.mkdir()
            repo = HERE.parents[4] if (HERE.parents[4] / PRIOR.VIA_REL).is_dir() else Path(td)
            rc1 = run_hydra(["--dir", str(tgt), "--apply", "--branch", "b"], repo, Path(td), {})
            st = seen.get("steps", [[""]])[0]
            chk("④ 步驟 = VCGC CGC_MDL158 尾版 hydra <夾> --apply --out <收據夾>/hydra_report.json(--branch 交給 on_branch)",
                rc1 == 0 and seen.get("tag") == "hydra" and Path(st[0]).name.startswith("CGC_MDL158_VIAPanoramaAuditRepair_v")
                and st[1:4] == ["hydra", str(tgt), "--apply"] and st[st.index("--out") + 1].endswith("hydra_report.json")
                and "--branch" in seen.get("rest", []), seen)
            rc2 = run_hydra(["--dir", str(Path(td) / "nope")], repo, Path(td), {})
            chk("⑤ 目標夾不在 → RED rc 1,不猜別的夾、不跑", rc2 == 1)
    finally:
        PRIOR.on_branch = keep
    rc_p = PRIOR.selftest()
    chk("⑥ 前版 v0101 自測照過(rc 0)", rc_p == 0, rc_p)
    src = HERE.read_text(encoding="utf-8")
    chk("⑦ 檔面:第 3 行加速器標記 · glob 取前版 · 零 TA-Lib · 不設同意閘 · 不含本機路徑",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "HERE.parent.glob(FAMILY" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M)
        and "C:\\Users\\" + "tonyk" not in src)
    print(f"{TAG} selftest {sum(ok)}/{len(ok)}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
