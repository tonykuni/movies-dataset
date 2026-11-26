#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VIA_HostBoot v0104 — 薄尾(v0100–v0103 一字不動):新動詞 vdfcheck(桌機一行跑 VDF 輸出驗證,收據回推)

操作員 2026-11-26:「所有VDF過關輸出驗證」。VDF 的資料庫只在桌機;容器只能驗程式面
(VDF test 失敗 2 → 0 已修在倉)。輸出驗證要在有庫的機器跑 VDF 管理器自己的動詞:
  ① test                    各引擎自測(UNIT)
  ② db check                冊 VIA_DB_Table_SSOT 每張表對真庫清點(缺庫 · 缺表 · 空表 · 列數 · 落後天)
  ③ db verify               獨立重核 ② 的每一列(檔 · 列數 · 最新日 · 狀態 · 燈)
  ④ synchronizer run --no-open   HTML U/I 頁對收據(VDF 自己的唯讀 / 乾跑動詞;不開瀏覽器)
  ⑤ monitor --json          九格總燈(UNIT · SYSTEM · 參數 · 加速器/網路 · HTML U/I · 輸出驗證 · 資料庫 …)
暫切 origin/<分支>(同 lake / vdf3,一定切回;已追蹤檔有改動 = 停不碰)。不出網(不收 --live)· 不擷取 · 不寫庫。
入口標記:VDF 管理器的 db 動詞只收 VIA_FROM_VCGC=YES(VDF 啟動器也是設這個);本動詞只在子行程環境帶入口標記,
          不寫進任何檔;同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT)一律不碰。
收據(只帶結構與計數,不帶任何資料值):DB_CHECK_latest.json · VERIFY_latest.json · VDF_MONITOR_latest.json
  + 每步主控台尾巴。DB_STATUS_MATRIX 含「最新幾列」的實際資料 → 不收、不推(資料邊界)。
用法:python VIA_HostBoot_v0104.py --repo <倉> vdfcheck [--branch B] [--push]
另修 bak(桌機 2026-11-26 19:02 實錄:前版 bak 取「工作夾 ∪ TEMP 取出的 HostBoot 旁」的 VIA_DailyBackup 尾版,
  工作夾落後 → 拿到 v0103(沒有 full 動詞)→ argparse 拒絕 rc 2,沒有備份):
  bak 改成跟 lake / vdfcheck 一樣暫切 origin/<分支>,用分支上的 VIA_DailyBackup 尾版跑 full(第五章六題已定案);
  分支上的尾版不到 v0104(沒有 full)= RED rc 1、不跑。收據照前版 collect("bak")。
  用法:python VIA_HostBoot_v0104.py --repo <倉> bak [--branch B] [--keep 5 …] [--push]
其餘動詞(fnc · vdf · vdfp · vdf3 · fin5y · hydra · lake)全部照前版。不用 TA-Lib · 不設同意閘 · 本檔零外呼。
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
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

FAMILY = "VIA_HostBoot"
VERSION = "v0104"
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
BASE = PRIOR.BASE                                   # v0101:on_branch · newest · push_receipts · say · VIA_REL
VERBS = tuple(PRIOR.VERBS) + ("vdfcheck",)
VIA_NET_TOOL_PATH = getattr(PRIOR, "VIA_NET_TOOL_PATH", None)
ENTRY_FLAG = ("VIA_FROM_VCGC", "YES")               # VDF 管理器 db 動詞收的入口標記(只放子行程環境)
RECEIPTS = ("DB_CHECK_latest.json", "VERIFY_latest.json", "monitor/VDF_MONITOR_latest.json")
NEVER_PUSH = ("DB_STATUS_MATRIX_latest.json",)      # 含實際資料列 → 不收


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def say(msg: str) -> None:
    BASE.say(msg)


def vdfcheck_steps(via: Path, live: bool, extra: list) -> list:
    vm = BASE.newest(via / "functional modules" / "VDF", "VDF_SystemManager_v*.py")
    return [[str(vm), "test"], [str(vm), "db", "check"], [str(vm), "db", "verify"],
            [str(vm), "synchronizer", "run", "--no-open"],
            [str(vm), "monitor", "--lanes", "3", "--timeout", "400", "--json"]]


def collect_receipts(via: Path, out: Path, t0: float) -> list:
    """只收白名單、而且是這一輪寫的(mtime ≥ 開跑);資料列報告一律不收。"""
    got = []
    base = via / "VIA_Reports" / "vdf"
    for rel in RECEIPTS:
        p = base / rel
        if Path(rel).name in NEVER_PUSH:
            continue
        if p.is_file() and p.stat().st_mtime >= t0 - 2:
            dst = out / ("vdfcheck_" + Path(rel).name)
            shutil.copyfile(p, dst)
            got.append(dst.name)
    return got


def lamps(out: Path) -> dict:
    res = {}
    for name in ("vdfcheck_DB_CHECK_latest.json", "vdfcheck_VERIFY_latest.json", "vdfcheck_VDF_MONITOR_latest.json"):
        p = out / name
        if p.is_file():
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                res[name] = {"lamp": d.get("lamp"), "summary": d.get("summary") if not isinstance(d.get("summary"), (list, dict)) else None,
                             "counts": d.get("counts")}
            except ValueError:
                res[name] = {"lamp": "UNREADABLE"}
    return res


AI_REL = Path("VeritasIntelligenceAnalytics") / "docs" / "handoff" / "ai"
BAK_MIN = 104                                       # VIA_DailyBackup v0104 起才有 full


def run_bak(rest: list, repo: Path, out: Path, env: dict) -> int:
    """暫切 origin/<分支>,用分支上的 VIA_DailyBackup 尾版跑 full;尾版不到 v0104 = RED。"""
    seen = {}

    def steps(via: Path, live: bool, extra: list) -> list:
        t = BASE.newest(via / "docs" / "handoff" / "ai", "VIA_DailyBackup_v*.py")
        seen["tail"] = t
        if t is None or _vnum(t) < BAK_MIN:
            return []
        return [[str(t), "full", "--via", str(via), *extra]]

    rc = BASE.on_branch(rest, repo, out, env, "bak", steps, ())
    t = seen.get("tail")
    if t is None or _vnum(t) < BAK_MIN:
        say(f"[RED] 分支上的 VIA_DailyBackup 尾版是 {Path(t).name if t else '無'},要 v{BAK_MIN:04d} 以上才有 full;沒有備份")
        return 1
    got = BASE.collect("bak", repo, out)
    say(f"備份收據 → {' · '.join(got) if got else '[黃] 沒有新的 BACKUP_latest / GATES(看主控台尾巴)'}")
    if not got:
        rc = max(rc, 2)
    return rc


def run_vdfcheck(rest: list, repo: Path, out: Path, env: dict) -> int:
    if "--live" in rest:
        say("[RED] vdfcheck 不出網:不收 --live(要抓新資料走 vdf3 --live)")
        return 1
    t0 = time.time()
    env = dict(env)
    env[ENTRY_FLAG[0]] = ENTRY_FLAG[1]
    rc = BASE.on_branch(rest, repo, out, env, "vdfcheck", vdfcheck_steps, ())
    got = collect_receipts(repo / BASE.VIA_REL, out, t0)
    say("收據 → " + (" · ".join(got) if got else "[黃] 這一輪沒有新寫的 DB_CHECK / VERIFY / MONITOR"))
    for k, v in lamps(out).items():
        say(f"  {k.replace('vdfcheck_', '')} · 燈 {v.get('lamp')}" + (f" · {v.get('counts')}" if v.get("counts") else ""))
    if len(got) < len(RECEIPTS):
        rc = max(rc, 2)
    return rc


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    verb = "vdfcheck" if "vdfcheck" in argv else ("bak" if "bak" in argv else None)
    if verb is None:
        return PRIOR.main(argv)
    i = argv.index(verb)
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
    from datetime import datetime
    env = dict(os.environ, VIA_REPO=str(repo))
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(tempfile.gettempdir()) / f"via_hostboot_{verb}_{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    rc = (run_vdfcheck if verb == "vdfcheck" else run_bak)(rest, repo, out, env)
    (out / f"{verb}_RUN.json").write_text(json.dumps({"tool": TAG, "verb": verb, "rc": rc, "secs": round(time.time() - _T0, 1),
                                                     "args": rest, "accel": VIA_ACCEL is not None, "net": VIA_NET_TOOL_PATH is not None,
                                                     "lamps": lamps(out) if verb == "vdfcheck" else None}, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    say(f"{verb} · rc {rc} · 收據 → {out}")
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
    chk("② 動詞表 = 前版八個 + vdfcheck", VERBS[:-1] == tuple(PRIOR.VERBS) and VERBS[-1] == "vdfcheck" and "lake" in VERBS)
    via = HERE.parents[3]
    st = vdfcheck_steps(via, False, [])
    chk("③ 步驟:VDF 管理器尾版 test → db check → db verify → synchronizer run --no-open → monitor --json(全唯讀;不擷取不寫庫)",
        all(Path(s[0]).name.startswith("VDF_SystemManager_v") for s in st)
        and [s[1:] for s in st] == [["test"], ["db", "check"], ["db", "verify"], ["synchronizer", "run", "--no-open"],
                                    ["monitor", "--lanes", "3", "--timeout", "400", "--json"]], st)
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        chk("④ 不收 --live(不出網)→ RED rc 1、不跑", run_vdfcheck(["--live"], tdp, tdp, {}) == 1)
        seen = {}
        keep = BASE.on_branch
        BASE.on_branch = lambda rest, repo, out, env, tag, fn, rd: seen.update(tag=tag, rd=rd, rest=rest, env=env) or 0
        before = os.environ.get(ENTRY_FLAG[0])
        try:
            (tdp / BASE.VIA_REL).mkdir(parents=True)
            rc = run_vdfcheck(["--branch", "b"], tdp, tdp, {"X": "1"})
        finally:
            BASE.on_branch = keep
        chk("⑤ 走 on_branch(暫切 · 一定切回)· tag vdfcheck · --branch 交給 on_branch · 入口標記只在子行程環境",
            seen.get("tag") == "vdfcheck" and "--branch" in seen.get("rest", []) and seen.get("env", {}).get(ENTRY_FLAG[0]) == ENTRY_FLAG[1]
            and os.environ.get(ENTRY_FLAG[0]) == before, {k: v for k, v in seen.items() if k != "env"})
        chk("⑥ 收據缺件 → 不冒充綠(rc ≥ 2)", rc >= 2, rc)
        rep = tdp / "via" / "VIA_Reports" / "vdf"
        (rep / "monitor").mkdir(parents=True)
        t0 = time.time()
        for rel in RECEIPTS + NEVER_PUSH:
            (rep / rel).write_text(json.dumps({"lamp": "GREEN", "counts": {"GREEN": 1}}), encoding="utf-8")
        out = tdp / "out"
        out.mkdir()
        got = collect_receipts(tdp / "via", out, t0)
        chk("⑦ 只收白名單三份 · DB_STATUS_MATRIX(含資料列)不收", sorted(got) == sorted("vdfcheck_" + Path(r).name for r in RECEIPTS)
            and not any("DB_STATUS_MATRIX" in g for g in got), got)
        old = rep / "VERIFY_latest.json"
        os.utime(old, (t0 - 3600, t0 - 3600))
        out2 = tdp / "out2"
        out2.mkdir()
        chk("⑧ 舊收據(開跑前寫的)不收", "vdfcheck_VERIFY_latest.json" not in collect_receipts(tdp / "via", out2, t0))
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        ai = tdp / "via" / "docs" / "handoff" / "ai"
        ai.mkdir(parents=True)
        keep_ob, keep_col = BASE.on_branch, BASE.collect
        calls = {}

        def fake_on_branch(rest, repo, out, env, tag, fn, rd):
            calls["tag"], calls["steps"] = tag, fn(tdp / "via", False, ["--keep", "5"])
            return 0
        try:
            BASE.on_branch, BASE.collect = fake_on_branch, (lambda verb, repo, out, fnc_dir=None: ["bak_00_BACKUP_latest.json"])
            (ai / "VIA_DailyBackup_v0103.py").write_text("x = 1\n", encoding="utf-8")
            rc_old = run_bak([], tdp, tdp, {})
            (ai / "VIA_DailyBackup_v0105.py").write_text("x = 1\n", encoding="utf-8")
            rc_new = run_bak(["--keep", "5"], tdp, tdp, {})
        finally:
            BASE.on_branch, BASE.collect = keep_ob, keep_col
        chk("⑨ bak 走 on_branch;分支尾版只有 v0103(沒有 full)= RED rc 1 · v0105 → full --via <分支 VIA> --keep 5",
            rc_old == 1 and rc_new == 0 and calls.get("tag") == "bak" and calls.get("steps")
            and Path(calls["steps"][0][0]).name == "VIA_DailyBackup_v0105.py" and calls["steps"][0][1:4] == ["full", "--via", str(tdp / "via")]
            and calls["steps"][0][-2:] == ["--keep", "5"], calls)
    rc_p = PRIOR.selftest()
    chk("⑨b 前版 v0103 自測照過(rc 0)", rc_p == 0, rc_p)
    src = HERE.read_text(encoding="utf-8")
    chk("⑩ 檔面:第 3 行加速器標記 · glob 取前版 · 零 TA-Lib · 不設同意閘 · 不寫入口標記到 os.environ · 不含本機路徑",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "HERE.parent.glob(FAMILY" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M)
        and not re.search(r"^\s*os\.environ\[", src, re.M)
        and "C:\\Users\\" + "tonyk" not in src)
    print(f"{TAG} selftest {sum(ok)}/{len(ok)}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
