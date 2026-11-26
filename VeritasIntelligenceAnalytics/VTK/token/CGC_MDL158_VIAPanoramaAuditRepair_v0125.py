#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""CGC_MDL158_VIAPanoramaAuditRepair v0125 — 薄尾(v0124 以前一字不動):hydra 已發布的檔不原地改(AGENTS.md 第 4 條「修改開新版」)

PR #749 審查(Codex P1,對 AGENTS.md L10 屬實):hydra --apply 在版控倉裡原地覆寫有版號的正本;v0124 雖已擋前版 / 已鎖,
已發布(origin/main 上有)的尾版仍會被原地改 → 薄尾鏈下游與已記的 SHA / 測試收據跟著失效,違反「修改開新版;已鎖成功來源維持原樣」。
本版:目標在 git 倉裡時,檔案已在 origin/main(沒有 origin/main 就看 main,再沒有就看 HEAD)= 區位「已發布」,一律不寫、
發現照列並標「要改請開新版號(AGENTS.md 4)」;只有這條分支新加、還沒發布的檔(本 PR 自己的新版)才可原地修。
不在 git 裡的夾(桌機 via_01_vdf 類)照 v0124 的區位規則。其餘照 v0124。
只讀程式碼結構;不執行被掃的檔;不出網;不用 TA-Lib;不設同意閘。舊主控台字串門:"read" "slice" "digest" --if-etag def pack_payload。
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

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL158_VIAPanoramaAuditRepair"
_HYDRA_VER4 = "v0125"
TAG = f"{_STEM} {_HYDRA_VER4}"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("panorama_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V122 = PRIOR.V122
VERBS = dict(PRIOR.VERBS)          # 動詞表照前版:"read" "slice" "digest" "pack" "tools" "verbs" … hydra
VERBS["hydra"] = (PRIOR.VERBS["hydra"][0], PRIOR.VERBS["hydra"][1],
                  PRIOR.VERBS["hydra"][2] + ";v0125:版控倉裡已發布(origin/main 有)的檔不原地改,標「要改請開新版號」(AGENTS.md 4)")


def __getattr__(name: str):
    return getattr(PRIOR, name)


def pack_payload(root, limit: int = 200) -> dict:
    """整夾索引:原樣轉交前版鏈(明寫在本檔,讓只認字串的舊門也看得到)。"""
    return PRIOR.pack_payload(root, limit)


def _git(top: Path, *args) -> tuple:
    try:
        cp = subprocess.run(["git", "-C", str(top), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        return cp.returncode, cp.stdout
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""


_PUB = {}


def published(top: Path) -> tuple:
    """→ (已發布的倉內相對路徑集合, 用哪個參照)。依序 origin/main → main → HEAD。"""
    if top in _PUB:
        return _PUB[top]
    for ref in ("origin/main", "main", "HEAD"):
        rc, out = _git(top, "ls-tree", "-r", "--name-only", ref)
        if rc == 0 and out.strip():
            _PUB[top] = ({ln.strip() for ln in out.splitlines() if ln.strip()}, ref)
            return _PUB[top]
    _PUB[top] = (set(), "")
    return _PUB[top]


def git_top(p: Path):
    rc, out = _git(p if p.is_dir() else p.parent, "rev-parse", "--show-toplevel")
    return Path(out.strip()).resolve() if rc == 0 and out.strip() else None


def panorama(targets: list, workers: int = 0) -> dict:
    pan = _PREV_PAN(targets, workers)
    pan["zones"].setdefault("已發布", 0)
    pan["zone_files"].setdefault("已發布", 0)
    tops = {}
    moved = {}
    for rel, ab in pan["_files"].items():
        ab = Path(ab).resolve()
        top = tops.setdefault(ab.parent, git_top(ab.parent))
        if top is None:
            continue
        pub, ref = published(top)
        try:
            key = ab.relative_to(top).as_posix()
        except ValueError:
            continue
        if key in pub:
            moved[rel] = ref
    by_file = {}
    for x in pan["findings"]:
        by_file.setdefault(x["file"], []).append(x)
    for rel, ref in moved.items():
        fs = by_file.get(rel, [])
        if fs and all(x.get("zone", "正本") == "正本" for x in fs):
            pan["zone_files"]["正本"] = max(0, pan["zone_files"].get("正本", 0) - 1)
            pan["zone_files"]["已發布"] += 1
            for x in fs:
                pan["zones"]["正本"] -= 1
                pan["zones"]["已發布"] += 1
                x["zone"], x["mode"] = "已發布", "不寫(已發布 · 要改請開新版號)"
                if x["fix"] == "auto":
                    x["fix"] = "skip"
                    x["why_manual"] = f"已在 {ref} 發布:原地改違反 AGENTS.md 第 4 條「修改開新版」→ 出新版號後再修"
    keep = lambda r: r not in moved  # noqa: E731
    pan["groups"]["不寫"] = sorted(set(pan["groups"].get("不寫", [])) | {r for r in moved if r in by_file})
    pan["groups"]["A"] = [r for r in pan["groups"]["A"] if keep(r)]
    pan["groups"]["B"] = [r for r in pan["groups"]["B"] if keep(r)]
    return pan


_PREV_PAN = V122.panorama


def _install():
    V122.panorama, V122.TAG = panorama, TAG


def _uninstall():
    V122.panorama, V122.TAG = _PREV_PAN, PRIOR.TAG


_install()


def print_verbs() -> int:
    e = '$E'
    print(f"[{TAG} 動詞表] {len(VERBS)} 個 · {e} = 鎖冊 token 那一支")
    for k, (use, when, what) in VERBS.items():
        print(f"  {k:<10} python3 \"{e}\" {use}")
        print(f"             何時:{when} · 做什麼:{what}")
    return 0


def main() -> int:
    argv = sys.argv[1:]
    if argv == ["--selftest"]:
        return selftest()
    if argv[:1] == ["verbs"]:
        return print_verbs()
    if argv[:1] == ["hydra"]:
        return PRIOR.main()
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("① 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        eng = repo / "eng"
        eng.mkdir(parents=True)
        (eng / "Pub_v0100.py").write_text("def r():\n    return open('a.json').read()\n", encoding="utf-8")
        g = ["-c", "user.email=selftest@example.invalid", "-c", "user.name=selftest"]
        for args in (["init", "-q", "-b", "main"], [*g, "add", "-A"], [*g, "commit", "-q", "-m", "base"], ["update-ref", "refs/remotes/origin/main", "HEAD"]):
            subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True)
        (eng / "New_v0100.py").write_text("def r():\n    return open('b.json').read()\n", encoding="utf-8")
        _PUB.clear()
        pan = V122.panorama([str(eng)], 2)
        z = {x["file"]: x.get("zone") for x in pan["findings"]}
        chk("② 已在 origin/main 的 Pub_v0100 → 已發布(不寫);這條分支新加的 New_v0100 → 正本(可修)",
            z.get("Pub_v0100.py") == "已發布" and z.get("New_v0100.py") == "正本", z)
        h0 = hashlib.sha256((eng / "Pub_v0100.py").read_bytes()).hexdigest()
        fx = V122.apply(pan, [str(eng)], 2)
        chk("③ --apply:已發布的檔位元不變 · 新檔照修(encoding 插入)",
            hashlib.sha256((eng / "Pub_v0100.py").read_bytes()).hexdigest() == h0
            and "encoding=" in (eng / "New_v0100.py").read_text(encoding="utf-8")
            and [r["file"] for r in fx["results"]] == ["New_v0100.py"], fx["results"])
        why = [x.get("why_manual", "") for x in pan["findings"] if x["file"] == "Pub_v0100.py" and x["cls"] == "ENCODING"]
        chk("④ 已發布那筆寫明理由(AGENTS.md 第 4 條 · 出新版號後再修)", why and "AGENTS.md" in why[0] and "新版號" in why[0], why)
        plain = Path(td) / "plain"
        plain.mkdir()
        (plain / "X_v0100.py").write_text("def r():\n    return open('c.json').read()\n", encoding="utf-8")
        p2 = V122.panorama([str(plain)], 2)
        chk("⑤ 不在 git 裡的夾:沒有「已發布」這回事,照 v0124 規則(正本可修)",
            all(x.get("zone") == "正本" for x in p2["findings"]) and p2["zones"].get("已發布", 0) == 0, p2["zones"])
    chk("⑥ VERBS 前版全在(含 hydra)", set(PRIOR.VERBS) <= set(VERBS))
    import contextlib
    import io
    _uninstall()
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc_p = PRIOR.selftest()
    finally:
        _install()
    tail = [ln for ln in buf.getvalue().splitlines() if ln.strip()][-1:] or [""]
    chk("⑦ 前版 v0124 鏈自測(本版換裝卸下)照過", rc_p == 0, tail[0][:200])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 檔面:第 3 行加速器標記 · glob 取前版 · 零 TA-Lib · 不設同意閘 · 字串門字樣在",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "HERE.glob(_STEM" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M)
        and all(w in src for w in ('"read"', '"slice"', '"digest"', "--if-etag", "def pack_payload")))
    print(f"[計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    _ = json
    return 0 if all(ok) else 2


if __name__ == "__main__":
    raise SystemExit(main())
