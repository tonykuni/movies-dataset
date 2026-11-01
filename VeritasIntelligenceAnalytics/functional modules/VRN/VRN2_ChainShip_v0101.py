#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_ChainShip v0101 — VRN-2 薄尾鏈隨船(VRN-2 自己的工具 · 只增不減 · 不改任何既有版本檔)。
v0101(2026-10-29 桌機實跑貼回):桌機 ship 後 check 仍紅(v0248 / v0253 不在 `functional modules/VRN`)→ 缺的環先在本機別處找
(VIA 樹 · 私有 runtime `functional modules/VRN2` · 備份夾 · Downloads 的 VRN2_* 套件夾與 zip · `--extra` 指定夾),同名且內容唯一、語法 / JSON 過
→ 原樣複製進 VRN 夾(或 SSOT/)再隨船;多份不同內容 → 只列不代選;v0100 其餘一字不動。

起因(2026-10-28 容器實測):倉上 VRN_SystemManager_v0254 `--selftest` → FileNotFoundError「前版 v0253 不在」;
⑨ 自動上船只帶「當輪新落地的檔」,薄尾釘名的前版(v0242 / v0246 / v0247 / v0248 / v0253 …)留在桌機沒入倉,
乾淨 clone(雲端 · 另一台機 · CI)載不起 VRN-2。本工具把「鏈是否完整」變成可量的燈,並在桌機把在位前版補上船。

動詞:
  check [--heads] [--json 路徑] 釘名前版盤點:每一個 VRN-2 版號檔(--heads = 只走各家族尾版)的 PRIOR 往回走到底,
                                 每一環判 TRACKED(VRN 夾在位)/ BUNDLED(只在 vrn2_ship 船包)/ MISSING(都沒有)
                                 MISSING > 0 → rc 1(紅);只有 BUNDLED 或引用冊未入倉 → rc 2(黃);全在位 → rc 0
                                 注意:MISSING 那一環再往前(例 v0253 之前的 v0250~v0252)看不到;補上後再跑一次
  ship  [--commit] [--push]      桌機:用 git 找出 VRN 夾內「本機在位但未入倉」的 VRN-2 自己的版號檔(白名單;未追蹤 + 已暫存但 HEAD 沒有的)→ 加進暫存區;
                                 已追蹤但內容不同 = 同名不同內容 → 只列出、不覆寫(rc 2);語法不過的 .py 不帶;
                                 --commit 落一筆只含這些檔的提交;--push 推當前分支(被拒只報 rc 2,交 ⑨ 持續解衝突)
  recover [--extra 夾…]          只找缺的環並複製進 VRN 夾(不碰 git);ship 預設先做這一步(--no-recover 關)
  --selftest                     臨時 git 倉 + 合成鏈,驗 check / ship / recover 全部判定

白名單(VRN-2 自己的檔;其他系統的檔一律不碰):
  VRN_SystemManager_v####.py · VRN_ENG###_*_v####.py · VRN2_*_v####.(py|json) · SSOT/VRN2_*_v####.json · _vdf_fetch/*(VRN-2 的 VDF 引擎包副本)
收據:<VIA>/VIA_Reports/vrn2/VRN2_ChainShip_latest.json(被 .gitignore 排除,不入倉)
[VIA:AST-CLASS] 類別 = 工具(VRN-2 隨船 / 鏈盤點)· 入口 = 本檔(桌機一鍵 / CI check)
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

TAG = "v0101"
DISPLAY_NAME = "VRN2_ChainShip"
HERE = Path(__file__).resolve().parent
NAME_RE = re.compile(r"^(?P<fam>[A-Za-z0-9_]+?)_v(?P<ver>\d{4})\.(?P<ext>py|json)$")
REF_RE = re.compile(r"""["']([A-Za-z0-9_]+_v\d{4}\.(?:py|json))["']""")
OWN_FAMILY_RE = re.compile(r"^(VRN_SystemManager|VRN_ENG\d{3}_[A-Za-z0-9]+|VRN2_[A-Za-z0-9_]+)$")
SSOT_BOOK_RE = re.compile(r"^VRN2_[A-Za-z0-9_]+_v\d{4}\.json$")
BUNDLE_REL = Path("docs/handoff/ai/vrn2_ship/VRN2_Bundle_latest.zip")
RECEIPT_REL = Path("VIA_Reports/vrn2/VRN2_ChainShip_latest.json")
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}
ZIP_MAX_BYTES = 512 * 1024 * 1024
MAX_SHIP_BYTES = 8 * 1024 * 1024

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass


def say(line: str) -> None:
    print(line, flush=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def via_root(start: Path) -> Path | None:
    p = start
    while True:
        if (p / "supportive modules").is_dir() and (p / "functional modules").is_dir():
            return p
        if p.parent == p:
            return None
        p = p.parent


def parse_name(name: str):
    m = NAME_RE.match(name)
    if not m:
        return None
    return m.group("fam"), int(m.group("ver")), m.group("ext")


def is_own_family(fam: str) -> bool:
    return bool(OWN_FAMILY_RE.match(fam))


# ===== 船包(vrn2_ship)成員 =====
class Bundle:
    def __init__(self, root: Path | None):
        self.path = (root / BUNDLE_REL) if root else None
        self.members: dict[str, str] = {}  # 檔名 → zip 內路徑
        self._zip = None
        if self.path and self.path.is_file():
            try:
                self._zip = zipfile.ZipFile(self.path)
                for n in self._zip.namelist():
                    if not n.endswith("/"):
                        self.members[Path(n).name] = n
            except Exception:  # noqa: BLE001
                self._zip = None
                self.members = {}

    def has(self, name: str) -> bool:
        return name in self.members

    def read(self, name: str) -> bytes | None:
        if self._zip is None or name not in self.members:
            return None
        try:
            return self._zip.read(self.members[name])
        except Exception:  # noqa: BLE001
            return None


# ===== 釘名前版 =====
def pinned_refs(name: str, text: str):
    """回 (同家族前版清單, 引用的 VRN2_ 冊 / 模組清單)。同家族且版號小於自己才算釘名前版;測試夾具名(A_v0101.py 等)不算。"""
    info = parse_name(name)
    if not info or info[0] == DISPLAY_NAME:  # 本工具自己(自測夾具字串)不掃
        return [], []
    fam, ver, _ = info
    priors, books = [], []
    for ref in dict.fromkeys(REF_RE.findall(text)):
        if ref == name:
            continue
        r = parse_name(ref)
        if not r:
            continue
        rfam, rver, _ = r
        if rfam == fam and rver < ver:
            priors.append(ref)
        elif rfam != fam and rfam.startswith("VRN2_"):
            books.append(ref)
    return priors, books


def read_text_local_or_bundle(vrn: Path, bundle: Bundle, name: str):
    """回 (text, state):TRACKED / BUNDLED / MISSING"""
    p = vrn / name
    if p.is_file():
        return p.read_text(encoding="utf-8", errors="replace"), "TRACKED"
    data = bundle.read(name)
    if data is not None:
        return data.decode("utf-8", errors="replace"), "BUNDLED"
    return None, "MISSING"


def family_heads(vrn: Path) -> dict[str, str]:
    heads: dict[str, tuple[int, str]] = {}
    for p in vrn.iterdir():
        if not p.is_file():
            continue
        info = parse_name(p.name)
        if not info or info[2] != "py" or not is_own_family(info[0]):
            continue
        fam, ver, _ = info
        if fam not in heads or ver > heads[fam][0]:
            heads[fam] = (ver, p.name)
    return {fam: name for fam, (ver, name) in sorted(heads.items())}


def check(vrn: Path, root: Path | None, scan_all: bool = True) -> dict:
    bundle = Bundle(root)
    starts = []
    if scan_all:
        starts = sorted(p.name for p in vrn.iterdir() if p.is_file() and parse_name(p.name) and parse_name(p.name)[2] == "py" and is_own_family(parse_name(p.name)[0]))
    else:
        starts = list(family_heads(vrn).values())
    chains, missing, bundled, books_missing = {}, [], [], []
    seen: dict[str, str] = {}
    for head in starts:
        links = []
        queue = [head]
        while queue:
            name = queue.pop(0)
            if name in seen:
                links.append({"name": name, "state": seen[name]})
                continue
            text, state = read_text_local_or_bundle(vrn, bundle, name)
            seen[name] = state
            links.append({"name": name, "state": state})
            if state == "MISSING":
                continue
            priors, books = pinned_refs(name, text)
            for b in books:
                bp = vrn / "SSOT" / b if b.endswith(".json") else vrn / b
                if not bp.is_file() and not (vrn / b).is_file() and not bundle.has(b):
                    books_missing.append({"ref_by": name, "book": b})
            queue.extend(priors)
        chains[head] = links
    for name, state in seen.items():
        if state == "MISSING":
            missing.append(name)
        elif state == "BUNDLED":
            bundled.append(name)
    missing = sorted(set(missing))
    bundled = sorted(set(bundled))
    uniq_books = {(b["ref_by"], b["book"]) for b in books_missing}
    books_missing = [{"ref_by": a, "book": b} for a, b in sorted(uniq_books)]
    lamp = "RED" if missing else ("YELLOW" if (bundled or books_missing) else "GREEN")
    return {"engine": "%s %s" % (DISPLAY_NAME, TAG), "verb": "check", "at": utc_now(), "lamp": lamp, "vrn_dir": str(vrn), "scan_all": scan_all,
            "bundle": str(bundle.path) if bundle.path else None, "bundle_members": len(bundle.members), "heads": starts, "family_heads": list(family_heads(vrn).values()),
            "links": sum(len(v) for v in chains.values()), "missing": missing, "bundled": bundled, "books_missing": books_missing, "chains": chains}


def print_check(r: dict) -> None:
    say("=== %s · check · 鏈盤點 · %s ===" % (r["engine"], r["vrn_dir"]))
    say("  船包 %s · 成員 %d" % (r["bundle"] or "(無)", r["bundle_members"]))
    heads = set(r.get("family_heads") or r["heads"])
    quiet = 0
    for head, links in r["chains"].items():
        states = [l["state"] for l in links]
        tail = links[-1]["name"] if links else "-"
        bad = [l["name"] for l in links if l["state"] == "MISSING"]
        mark = "RED" if bad else ("YEL" if "BUNDLED" in states else "OK ")
        if mark == "OK " and head not in heads:
            quiet += 1  # 非尾版且全在位:不逐行印
            continue
        say("  [%s] %s · 環 %d · 到 %s%s" % (mark, head, len(links), tail, (" · 缺 " + " / ".join(bad)) if bad else ""))
    if quiet:
        say("  (另 %d 個非尾版起點全在位,不逐行印)" % quiet)
    for b in r["books_missing"]:
        say("  [YEL] 引用冊未入倉(可能桌機生成):%s ← %s" % (b["book"], b["ref_by"]))
    if r["bundled"]:
        say("  [YEL] 只在船包(② 補回才在位):%d 檔 · %s…" % (len(r["bundled"]), " / ".join(r["bundled"][:4])))
    say("[計] %s · check · %s · 起點 %d(家族尾版 %d)· 環 %d · MISSING %d · BUNDLED %d · 引用冊缺 %d" % (
        r["engine"], r["lamp"], len(r["heads"]), len(r.get("family_heads") or []), r["links"], len(r["missing"]), len(r["bundled"]), len(r["books_missing"])))
    if r["missing"]:
        say("  缺:" + " · ".join(r["missing"]))
        say("  注意:缺的那一環再往前的版本看不到(例 v0253 之前的 v0250~v0252);桌機補船後再跑一次 check")


# ===== recover(v0101):缺的環在本機別處找 =====
def _candidate_roots(vrn: Path, root: Path | None, extra_dirs=(), home: Path | None = None) -> list:
    roots = []
    if root:
        roots.append(root)
    for d in extra_dirs:
        roots.append(Path(d))
    hp = home if home is not None else Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or "")
    if hp and str(hp):
        dl = hp / "Downloads"
        if dl.is_dir():
            roots.append(dl)
    out, seen = [], set()
    for r in roots:
        try:
            rr = r.resolve()
        except OSError:
            continue
        if rr.is_dir() and str(rr) not in seen:
            seen.add(str(rr))
            out.append(rr)
    return out


def _content_ok(name: str, data: bytes) -> tuple:
    if name.endswith(".py"):
        try:
            ast.parse(data.decode("utf-8", errors="replace"))
        except SyntaxError as exc:
            return False, "SYNTAX 行 %s" % exc.lineno
        return True, ""
    try:
        json.loads(data.decode("utf-8-sig", errors="replace"))
    except Exception:  # noqa: BLE001
        return False, "JSON 不合法"
    return True, ""


def find_elsewhere(names: list, vrn: Path, root: Path | None, extra_dirs=(), home: Path | None = None, downloads_only_vrn2: bool = True) -> dict:
    """每個缺的檔名:在候選根(VIA 樹 · --extra 夾 · Downloads)的檔案與 zip 成員裡找同名檔 → {name: {sha: {"data", "where": [..]}}}(VRN 夾本身與 .git 不算)。"""
    want = set(names)
    found: dict = {n: {} for n in names}
    if not want:
        return found
    vrn_r = vrn.resolve()
    for base in _candidate_roots(vrn, root, extra_dirs, home):
        in_downloads = base.name.lower() == "downloads"
        for dp, dns, fns in os.walk(base):
            dns[:] = [d for d in dns if d not in SKIP_DIRS and not (in_downloads and Path(dp) == base and not d.upper().startswith("VRN2_"))]
            dpp = Path(dp)
            if dpp == vrn_r or (dpp.is_relative_to(vrn_r) if hasattr(dpp, "is_relative_to") else str(dpp).startswith(str(vrn_r) + os.sep)):
                continue
            for fn in fns:
                p = dpp / fn
                if fn in want:
                    try:
                        data = p.read_bytes()
                    except OSError:
                        continue
                    found[fn].setdefault(sha256_bytes(data), {"data": data, "where": []})["where"].append(str(p))
                elif fn.lower().endswith(".zip") and (not in_downloads or fn.upper().startswith("VRN2_") or dpp != base):
                    try:
                        if p.stat().st_size > ZIP_MAX_BYTES:
                            continue
                        with zipfile.ZipFile(p) as z:
                            for m in z.namelist():
                                mn = m.rsplit("/", 1)[-1]
                                if mn in want:
                                    data = z.read(m)
                                    found[mn].setdefault(sha256_bytes(data), {"data": data, "where": []})["where"].append("%s::%s" % (p, m))
                                elif mn.lower().endswith(".zip") and mn.upper().startswith("VRN2_"):
                                    try:
                                        import io as _io
                                        with zipfile.ZipFile(_io.BytesIO(z.read(m))) as z2:
                                            for m2 in z2.namelist():
                                                mn2 = m2.rsplit("/", 1)[-1]
                                                if mn2 in want:
                                                    data = z2.read(m2)
                                                    found[mn2].setdefault(sha256_bytes(data), {"data": data, "where": []})["where"].append("%s::%s::%s" % (p, m, m2))
                                    except Exception:  # noqa: BLE001
                                        continue
                    except Exception:  # noqa: BLE001
                        continue
    return found


def recover(vrn: Path, root: Path | None, extra_dirs=(), home: Path | None = None, names: list | None = None) -> dict:
    """缺的環(check 的 MISSING + 引用冊缺)在本機別處找到、內容唯一且語法 / JSON 過 → 原樣複製進 VRN 夾(冊進 SSOT/);已在位的不覆寫。回 dict(不碰 git)。"""
    chk = check(vrn, root) if names is None else None
    missing = list(names) if names is not None else sorted(set(chk["missing"]) | {b["book"] for b in chk["books_missing"]})
    found = find_elsewhere(missing, vrn, root, extra_dirs, home)
    copied, ambiguous, absent, rejected = [], [], [], []
    for n in missing:
        dest = (vrn / "SSOT" / n) if (n.endswith(".json") and SSOT_BOOK_RE.match(n)) else (vrn / n)
        cands = found.get(n) or {}
        good = {sha: c for sha, c in cands.items() if _content_ok(n, c["data"])[0]}
        bad = [(sha, _content_ok(n, c["data"])[1], c["where"][0]) for sha, c in cands.items() if sha not in good]
        if not cands:
            absent.append(n)
            continue
        if not good:
            rejected.append({"file": n, "why": bad[0][1], "where": bad[0][2]})
            continue
        if len(good) > 1:
            ambiguous.append({"file": n, "versions": [{"sha256": sha, "where": c["where"][:3]} for sha, c in good.items()]})
            continue
        sha, c = next(iter(good.items()))
        if dest.exists():
            copied.append({"file": n, "sha256": sha, "from": c["where"][0], "to": str(dest), "note": "已在位 · 不覆寫"})
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(c["data"])
        copied.append({"file": n, "sha256": sha, "from": c["where"][0], "to": str(dest)})
    lamp = "GREEN" if missing and not (ambiguous or absent or rejected) else ("YELLOW" if (ambiguous or absent or rejected) else "GREEN")
    return {"engine": "%s %s" % (DISPLAY_NAME, TAG), "verb": "recover", "at": utc_now(), "lamp": lamp, "vrn_dir": str(vrn), "missing": missing,
            "roots": [str(r) for r in _candidate_roots(vrn, root, extra_dirs, home)], "copied": copied, "ambiguous": ambiguous, "absent": absent, "rejected": rejected}


def print_recover(r: dict) -> None:
    say("=== %s · recover · 缺的環在本機別處找 · %s ===" % (r["engine"], r["vrn_dir"]))
    say("  找的根:" + " · ".join(r["roots"]))
    for c in r["copied"]:
        say("  [FIND] %s ← %s · %s%s" % (c["file"], c["from"], c["sha256"][:12], (" · " + c["note"]) if c.get("note") else " · 複製到 " + c["to"]))
    for a in r["ambiguous"]:
        say("  [FIND?] %s · %d 份不同內容 · 不代選:%s" % (a["file"], len(a["versions"]), " / ".join("%s(%s)" % (v["sha256"][:12], v["where"][0]) for v in a["versions"])))
    for x in r["rejected"]:
        say("  [SKIP] %s · %s · %s" % (x["file"], x["why"], x["where"]))
    for n in r["absent"]:
        say("  [FIND-] %s · 本機找不到(VIA 樹 · Downloads 的 VRN2_* · --extra)" % n)
    say("[計] %s · recover · %s · 缺 %d · 複製 %d · 多份不同 %d · 找不到 %d · 內容不過 %d" % (
        r["engine"], r["lamp"], len(r["missing"]), len([c for c in r["copied"] if not c.get("note")]), len(r["ambiguous"]), len(r["absent"]), len(r["rejected"])))


# ===== git =====
def git(args, cwd: Path) -> tuple[int, str]:
    cmd = ["git", "-c", "core.quotepath=false"] + list(args)
    try:
        cp = subprocess.run(cmd, cwd=str(cwd), capture_output=True, encoding="utf-8", errors="replace", timeout=600)
    except Exception as exc:  # noqa: BLE001
        return 127, str(exc)
    out = (cp.stdout or "") + (cp.stderr or "")
    return cp.returncode, out.strip()


def ship_whitelisted(rel: str) -> bool:
    parts = rel.replace("\\", "/").split("/")
    if "__pycache__" in parts:
        return False
    if len(parts) == 1:
        info = parse_name(parts[0])
        return bool(info and is_own_family(info[0]))
    if parts[0] == "SSOT" and len(parts) == 2:
        return bool(SSOT_BOOK_RE.match(parts[1]))
    if parts[0] == "_vdf_fetch":
        return not parts[-1].endswith((".pyc", ".log", ".tmp"))
    return False


def ship(vrn: Path, root: Path | None, do_commit: bool = False, do_push: bool = False, do_recover: bool = True, extra_dirs=(), home: Path | None = None) -> dict:
    rc, top = git(["rev-parse", "--show-toplevel"], vrn)
    if rc != 0:
        return {"engine": "%s %s" % (DISPLAY_NAME, TAG), "verb": "ship", "at": utc_now(), "lamp": "RED", "error": "不是 git 倉:" + top}
    rec = None
    if do_recover:
        rec = recover(vrn, root, extra_dirs, home)                             # v0101 缺的環先在本機別處找 → 複製進 VRN 夾 → 下面當「在位未入倉」帶上船
        if rec["missing"]:
            print_recover(rec)
    rc, branch = git(["rev-parse", "--abbrev-ref", "HEAD"], vrn)
    rc, others = git(["ls-files", "--others", "--exclude-standard", "--", "."], vrn)
    untracked = [l.strip() for l in others.splitlines() if l.strip()]
    rc, cached = git(["diff", "--cached", "--name-only", "--diff-filter=A", "--relative", "--", "."], vrn)  # 已暫存但 HEAD 沒有(上一次 ship 沒 --commit · 或 commit 失敗後重跑)
    untracked = sorted(set(untracked) | {l.strip() for l in cached.splitlines() if l.strip()})
    rc, diff = git(["diff", "--name-only", "--relative", "--", "."], vrn)  # --relative:路徑相對本夾(porcelain 是相對倉根)
    modified = [l.strip() for l in diff.splitlines() if l.strip()]
    staged, skipped, conflicts = [], [], []
    for rel in sorted(untracked):
        if not ship_whitelisted(rel):
            continue
        p = vrn / rel
        try:
            size = p.stat().st_size
        except OSError as exc:
            skipped.append({"file": rel, "why": "讀不到:%s" % exc.__class__.__name__})
            continue
        if size > MAX_SHIP_BYTES:
            skipped.append({"file": rel, "why": "超過 %d MB" % (MAX_SHIP_BYTES // (1024 * 1024))})
            continue
        if rel.endswith(".py"):
            try:
                ast.parse(p.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError as exc:
                skipped.append({"file": rel, "why": "SYNTAX 行 %s" % exc.lineno})
                continue
        if rel.endswith(".json"):
            try:
                json.loads(p.read_text(encoding="utf-8-sig", errors="replace"))
            except Exception:  # noqa: BLE001
                skipped.append({"file": rel, "why": "JSON 不合法"})
                continue
        staged.append({"file": rel, "bytes": size, "sha256": sha256_bytes(p.read_bytes())})
    for rel in modified:
        if ship_whitelisted(rel):
            conflicts.append({"file": rel, "why": "已追蹤但內容不同 · 同名不同內容 · 不覆寫(出 v+1)"})
    result = {"engine": "%s %s" % (DISPLAY_NAME, TAG), "verb": "ship", "at": utc_now(), "repo": top, "branch": branch, "vrn_dir": str(vrn),
              "staged": staged, "skipped": skipped, "conflicts": conflicts, "commit": None, "push": None,
              "recover": ({k: rec[k] for k in ("lamp", "missing", "copied", "ambiguous", "absent", "rejected")} if rec else None)}
    if staged:
        rc, out = git(["add", "--"] + [s["file"] for s in staged], vrn)
        if rc != 0:
            result["lamp"] = "RED"
            result["error"] = "git add 失敗:" + out
            return result
    if do_commit and staged:
        msg = "VRN-2 薄尾鏈隨船 · 補 %d 個在位未入倉的 VRN-2 檔(只增不減 · %s %s)" % (len(staged), DISPLAY_NAME, TAG)
        rc, out = git(["commit", "-m", msg, "--"] + [s["file"] for s in staged], vrn)
        if rc != 0:
            result["lamp"] = "RED"
            result["error"] = "git commit 失敗:" + out
            return result
        rc, sha = git(["rev-parse", "--short", "HEAD"], vrn)
        result["commit"] = {"sha": sha, "message": msg}
    if do_push and result.get("commit"):
        pushed = False
        for i, wait in enumerate((0, 2, 4, 8)):
            if wait:
                time.sleep(wait)
            rc, out = git(["push", "origin", "HEAD:%s" % branch], vrn)
            if rc == 0:
                pushed = True
                break
            if "rejected" in out or "non-fast-forward" in out or "fetch first" in out:
                result["push"] = {"ok": False, "why": "被拒(分支落後)· 交 ⑨ 持續解衝突後再推", "out": out[-400:]}
                break
            result["push"] = {"ok": False, "why": "網路 / 其他(第 %d 次)" % (i + 1), "out": out[-400:]}
        if pushed:
            result["push"] = {"ok": True, "branch": branch}
    lamp = "GREEN"
    if conflicts or skipped or (result.get("push") and not result["push"]["ok"]) or (rec and (rec["ambiguous"] or rec["absent"] or rec["rejected"])):
        lamp = "YELLOW"
    result["lamp"] = lamp
    return result


def print_ship(r: dict) -> None:
    say("=== %s · ship · 在位未入倉補船 · %s ===" % (r["engine"], r.get("vrn_dir", "")))
    if r.get("error"):
        say("  [RED] " + r["error"])
    for s in r.get("staged", []):
        say("  [ADD] %s · %d B · %s" % (s["file"], s["bytes"], s["sha256"][:12]))
    for s in r.get("skipped", []):
        say("  [SKIP] %s · %s" % (s["file"], s["why"]))
    for c in r.get("conflicts", []):
        say("  [YEL] %s · %s" % (c["file"], c["why"]))
    if r.get("commit"):
        say("  [COMMIT] %s · %s" % (r["commit"]["sha"], r["commit"]["message"]))
    if r.get("push"):
        say("  [PUSH] %s" % ("推上 %s" % r["push"]["branch"] if r["push"]["ok"] else r["push"]["why"]))
    say("[計] %s · ship · %s · 分支 %s · 加入 %d · 跳過 %d · 同名不同內容 %d · commit %s · push %s" % (
        r["engine"], r.get("lamp", "RED"), r.get("branch", "-"), len(r.get("staged", [])), len(r.get("skipped", [])), len(r.get("conflicts", [])),
        (r["commit"] or {}).get("sha") if r.get("commit") else "-", ("ok" if r["push"]["ok"] else "fail") if r.get("push") else "-"))


def write_receipt(root: Path | None, payload: dict, explicit: str | None = None) -> Path | None:
    target = Path(explicit) if explicit else ((root / RECEIPT_REL) if root else None)
    if target is None:
        return None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        return target
    except OSError:
        return None


# ===== selftest =====
def _w(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def selftest() -> int:
    oks, fails = [], []

    def chk(label, cond):
        (oks if cond else fails).append(label)
        say("  [%s] %s" % ("OK" if cond else "FAIL", label))

    with tempfile.TemporaryDirectory() as td:
        top = Path(td) / "repo"
        root = top / "VeritasIntelligenceAnalytics"
        vrn = root / "functional modules" / "VRN"
        (root / "supportive modules").mkdir(parents=True)
        vrn.mkdir(parents=True)
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@x")
        subprocess.run(["git", "init", "-q", str(top)], check=True, env=env)
        subprocess.run(["git", "-C", str(top), "config", "user.email", "t@x"], check=True)
        subprocess.run(["git", "-C", str(top), "config", "user.name", "t"], check=True)
        # 合成鏈:SystemManager v0100(追蹤)← v0101(未入倉)← v0102 尾版(追蹤)
        _w(vrn / "VRN_SystemManager_v0100.py", "X = 1\n")
        _w(vrn / "VRN_SystemManager_v0102.py", 'PRIOR_NAME = "VRN_SystemManager_v0101.py"\n')
        # ENG500 v0101 尾版 → v0100 只在船包
        _w(vrn / "VRN_ENG500_Demo_v0101.py", 'PRIOR_NAME = "VRN_ENG500_Demo_v0100.py"\nFIXTURE = "A_v0101.py"\n')
        # VRN2_Foo v0101 → v0100 哪裡都沒有(MISSING);引用冊 VRN2_Regex_v0100.json 沒有(YEL)
        _w(vrn / "VRN2_Foo_v0101.py", 'PRIOR_NAME = "VRN2_Foo_v0100.py"\nBOOK = "VRN2_Regex_v0100.json"\n')
        # 他系統的檔不算
        _w(vrn / "VRN2_Foo_v0101.py", (vrn / "VRN2_Foo_v0101.py").read_text(encoding="utf-8") + 'LOCK = "VIA_ToolVersion_Lock_v0100.json"\n')
        bz = root / BUNDLE_REL
        bz.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(bz, "w") as z:
            z.writestr("functional modules/VRN/VRN_ENG500_Demo_v0100.py", "Y = 2\n")
        subprocess.run(["git", "-C", str(top), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(top), "commit", "-q", "-m", "base"], check=True, env=env)
        # 桌機狀態:v0101 落地未入倉 · SSOT 冊未入倉 · 語法壞的未入倉 · 非白名單未入倉 · 封存夾 · 已追蹤被改
        _w(vrn / "VRN_SystemManager_v0101.py", 'PRIOR_NAME = "VRN_SystemManager_v0100.py"\n')
        _w(vrn / "SSOT" / "VRN2_Regex_v0100.json", '{"a": 1}\n')
        _w(vrn / "VRN2_Broken_v0100.py", "def (:\n")
        _w(vrn / "notes.txt", "x\n")
        _w(vrn / "_archive_vrn2" / "VRN_SystemManager_v0050.py", "Z = 0\n")
        _w(vrn / "_vdf_fetch" / "VDF_TW_DataFetchEngine_v036.py", "W = 36\n")
        _w(vrn / "VRN_SystemManager_v0100.py", "X = 1  # 被改\n")

        r = check(vrn, root, scan_all=False)
        say("  check 結果:lamp %s · missing %s · bundled %s · books %s" % (r["lamp"], r["missing"], r["bundled"], r["books_missing"]))
        chk("① 尾版判定:SystemManager v0102 · ENG500 v0101 · VRN2_Foo v0101 · Broken v0100", set(r["heads"]) == {"VRN_SystemManager_v0102.py", "VRN_ENG500_Demo_v0101.py", "VRN2_Foo_v0101.py", "VRN2_Broken_v0100.py"})
        chk("② 鏈走到底:v0102 → v0101 → v0100 三環皆 TRACKED", [l["state"] for l in r["chains"]["VRN_SystemManager_v0102.py"]] == ["TRACKED", "TRACKED", "TRACKED"])
        chk("③ 只在船包 = BUNDLED(黃)", r["bundled"] == ["VRN_ENG500_Demo_v0100.py"])
        chk("④ 哪裡都沒有 = MISSING(紅)· 夾具名 A_v0101.py 與他系統鎖冊不算", r["missing"] == ["VRN2_Foo_v0100.py"])
        chk("⑤ 引用冊 VRN2_Regex_v0100.json 落在 SSOT/ 就不算缺", r["books_missing"] == [])
        chk("⑥ 燈:有 MISSING → RED", r["lamp"] == "RED")
        (vrn / "VRN2_Foo_v0100.py").write_text("F = 0\n", encoding="utf-8")
        (vrn / "SSOT" / "VRN2_Regex_v0100.json").unlink()
        r2 = check(vrn, root, scan_all=False)
        chk("⑦ 補上 v0100 後:MISSING 0 · 引用冊缺 1 · 燈 YELLOW", r2["missing"] == [] and r2["books_missing"] == [{"ref_by": "VRN2_Foo_v0101.py", "book": "VRN2_Regex_v0100.json"}] and r2["lamp"] == "YELLOW")
        _w(vrn / "SSOT" / "VRN2_Regex_v0100.json", '{"a": 1}\n')
        _w(vrn / "VRN_ENG600_Mid_v0101.py", 'PRIOR_NAME = "VRN_ENG600_Mid_v0100.py"\n')
        _w(vrn / "VRN_ENG600_Mid_v0102.py", 'PRIOR_NAME = "VRN_ENG600_Mid_v0101.py"\n')
        ra = check(vrn, root)
        rh = check(vrn, root, scan_all=False)
        chk("⑧ 預設掃每一檔:非尾版 v0101 釘的 v0100 缺 → 也抓到(--heads 只看尾版就抓不到)", "VRN_ENG600_Mid_v0100.py" in ra["missing"] and "VRN_ENG600_Mid_v0100.py" in rh["missing"] and len(ra["heads"]) > len(rh["heads"]))
        _w(vrn / "VRN_ENG600_Mid_v0100.py", "M = 0\n")

        home = Path(td) / "home"
        (home / "Downloads").mkdir(parents=True)
        s = ship(vrn, root, do_commit=True, do_push=False, home=home)
        files = sorted(x["file"] for x in s["staged"])
        say("  ship 結果:lamp %s · staged %s · skipped %s · conflicts %s" % (s["lamp"], files, [x["file"] for x in s["skipped"]], [x["file"] for x in s["conflicts"]]))
        chk("⑨ 白名單只帶 VRN-2 版號檔 / SSOT 冊 / _vdf_fetch;notes.txt 與封存夾不帶",
            files == ["SSOT/VRN2_Regex_v0100.json", "VRN2_Foo_v0100.py", "VRN_ENG600_Mid_v0100.py", "VRN_ENG600_Mid_v0101.py", "VRN_ENG600_Mid_v0102.py",
                      "VRN_SystemManager_v0101.py", "_vdf_fetch/VDF_TW_DataFetchEngine_v036.py"])
        chk("⑩ 語法不過的 .py 跳過並記理由", [x["file"] for x in s["skipped"]] == ["VRN2_Broken_v0100.py"] and "SYNTAX" in s["skipped"][0]["why"])
        chk("⑪ 已追蹤被改 = 同名不同內容 · 只列不覆寫", [x["file"] for x in s["conflicts"]] == ["VRN_SystemManager_v0100.py"])
        chk("⑫ 燈:有同名不同內容 / 跳過 → YELLOW", s["lamp"] == "YELLOW")
        rc, shown = git(["show", "--stat", "--format=%s", "HEAD"], vrn)
        chk("⑬ 提交只含加入的 7 檔 · 被改的 v0100 沒進提交", s["commit"] and shown.count("|") == 7 and "VRN_SystemManager_v0100.py" not in shown and "薄尾鏈隨船" in shown)
        rc, st = git(["diff", "--name-only", "--relative", "--", "."], vrn)
        rc, un = git(["ls-files", "--others", "--exclude-standard", "--", "."], vrn)
        chk("⑭ 提交後:被改的 v0100 仍在工作樹(未覆寫)· Broken / notes 仍未追蹤", st.strip() == "VRN_SystemManager_v0100.py" and "VRN2_Broken_v0100.py" in un and "notes.txt" in un)
        r3 = check(vrn, root)
        chk("⑮ 補船後 check:MISSING 0 · 只剩船包黃", r3["missing"] == [] and r3["lamp"] == "YELLOW")
        s2 = ship(vrn, root, do_commit=True, do_push=True, home=home)
        chk("⑯ 再跑 ship:無新檔 → 不提交 · push 不做 · 燈 YELLOW(同名不同內容仍在)", s2["commit"] is None and s2["push"] is None and s2["lamp"] == "YELLOW")
        rp = write_receipt(root, r3)
        chk("⑰ 收據落在 VIA_Reports/vrn2/VRN2_ChainShip_latest.json", rp is not None and rp.is_file() and json.loads(rp.read_text(encoding="utf-8"))["lamp"] == "YELLOW")
        nr = ship(Path(td), None)
        chk("⑱ 不是 git 倉 → RED 不動作", nr["lamp"] == "RED")
        _w(vrn / "VRN_ENG700_Late_v0100.py", "L = 0\n")
        s3 = ship(vrn, root, home=home)  # 乾跑:只暫存不提交
        s4 = ship(vrn, root, do_commit=True, home=home)  # 再跑要把已暫存的帶進提交
        rc, shown = git(["show", "--stat", "--format=%s", "HEAD"], vrn)
        chk("⑲ 先 ship 再 ship --commit:已暫存未提交的檔也進提交(不會靜默跳過)",
            [x["file"] for x in s3["staged"]] == ["VRN_ENG700_Late_v0100.py"] and [x["file"] for x in s4["staged"]] == ["VRN_ENG700_Late_v0100.py"]
            and s4["commit"] is not None and "VRN_ENG700_Late_v0100.py" in shown and shown.count("|") == 1)

        # v0101 recover:尾版 v0802 釘 v0801 · v0801 不在 VRN 夾 —— 在私有 runtime 夾(同內容兩份)· 另一個缺的只在 Downloads 的 VRN2_* zip 裡 · 第三個兩份不同內容 · 第四個哪都沒有
        _w(vrn / "VRN_ENG800_Rec_v0802.py", 'PRIOR_NAME = "VRN_ENG800_Rec_v0801.py"\nB1 = "VRN2_RecBook_v0100.json"\nB2 = "VRN2_Amb_v0100.json"\n')
        _w(vrn / "VRN_ENG801_Gone_v0101.py", 'PRIOR_NAME = "VRN_ENG801_Gone_v0100.py"\n')
        _w(root / "functional modules" / "VRN2" / "VRN_ENG800_Rec_v0801.py", "R = 801\n")
        _w(root / "VIA_Reports" / "vrn2" / "backup" / "x" / "VRN_ENG800_Rec_v0801.py", "R = 801\n")
        _w(root / "functional modules" / "VRN2" / "VRN2_Amb_v0100.json", '{"v": 1}\n')
        _w(root / "VIA_Reports" / "vrn2" / "backup" / "VRN2_Amb_v0100.json", '{"v": 2}\n')
        with zipfile.ZipFile(home / "Downloads" / "VRN2_Closeout_v0999.zip", "w") as z:
            z.writestr("VRN2_Closeout_v0999/VRN2_Runtime_v0999.zip", b"")
        import io as _io
        inner = _io.BytesIO()
        with zipfile.ZipFile(inner, "w") as z2:
            z2.writestr("VRN2_RecBook_v0100.json", '{"b": 1}\n')
        with zipfile.ZipFile(home / "Downloads" / "VRN2_Closeout_v0999.zip", "w") as z:
            z.writestr("VRN2_Closeout_v0999/VRN2_Runtime_v0999.zip", inner.getvalue())
        _w(home / "Downloads" / "notes" / "VRN_ENG801_Gone_v0100.py", "G = 0\n")   # Downloads 下非 VRN2_* 的夾不找
        rc0 = check(vrn, root)
        chk("⑳ recover 前:v0801 · 兩本冊 · Gone 都缺", "VRN_ENG800_Rec_v0801.py" in rc0["missing"] and "VRN_ENG801_Gone_v0100.py" in rc0["missing"] and {b["book"] for b in rc0["books_missing"]} >= {"VRN2_RecBook_v0100.json", "VRN2_Amb_v0100.json"})
        rr = recover(vrn, root, home=home)
        say("  recover 結果:lamp %s · copied %s · ambiguous %s · absent %s" % (rr["lamp"], [c["file"] for c in rr["copied"]], [a["file"] for a in rr["ambiguous"]], rr["absent"]))
        chk("㉑ 同內容兩份 → 當一份複製進 VRN 夾(原處不動)", (vrn / "VRN_ENG800_Rec_v0801.py").read_text(encoding="utf-8") == "R = 801\n" and (root / "functional modules" / "VRN2" / "VRN_ENG800_Rec_v0801.py").exists())
        chk("㉒ 只在 Downloads 的 VRN2_* zip 裡(套件 zip 內的 runtime zip)→ 複製進 SSOT/", (vrn / "SSOT" / "VRN2_RecBook_v0100.json").read_text(encoding="utf-8") == '{"b": 1}\n')
        chk("㉓ 兩份不同內容 → 不代選 · 列出兩個 sha", [a["file"] for a in rr["ambiguous"]] == ["VRN2_Amb_v0100.json"] and len(rr["ambiguous"][0]["versions"]) == 2 and not (vrn / "SSOT" / "VRN2_Amb_v0100.json").exists())
        chk("㉔ Downloads 下非 VRN2_* 夾不找 → 找不到", rr["absent"] == ["VRN_ENG801_Gone_v0100.py"] and rr["lamp"] == "YELLOW")
        s5 = ship(vrn, root, do_commit=True, home=home)
        chk("㉕ ship 先 recover 再帶上船:v0801 / RecBook / v0802 都進提交 · 收據有 recover 欄", {x["file"] for x in s5["staged"]} >= {"VRN_ENG800_Rec_v0801.py", "SSOT/VRN2_RecBook_v0100.json", "VRN_ENG800_Rec_v0802.py"} and s5["recover"] and s5["lamp"] == "YELLOW")
        rc1 = check(vrn, root)
        chk("㉖ 補船後 check:v0801 不再缺 · 只剩代選不了的冊與找不到的", "VRN_ENG800_Rec_v0801.py" not in rc1["missing"] and rc1["missing"] == ["VRN_ENG801_Gone_v0100.py"])
        s6 = ship(vrn, root, do_recover=False, home=home)
        chk("㉗ --no-recover:不找 · 收據 recover 欄為空", s6["recover"] is None)
    say("[計] %s %s --selftest · OK %d · FAIL %d" % (DISPLAY_NAME, TAG, len(oks), len(fails)))
    return 0 if not fails else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="VRN2_ChainShip_%s" % TAG, description="VRN-2 薄尾鏈隨船 / 鏈盤點")
    ap.add_argument("verb", nargs="?", choices=["check", "ship", "recover"], default="check")
    ap.add_argument("--vrn-dir", default=None, help="VRN 夾(預設 = 本檔所在夾)")
    ap.add_argument("--heads", action="store_true", help="check:只走各家族尾版(預設每一個版號檔都當起點)")
    ap.add_argument("--json", default=None, help="收據路徑(預設 <VIA>/VIA_Reports/vrn2/VRN2_ChainShip_latest.json)")
    ap.add_argument("--commit", action="store_true", help="ship:把加入的檔落一筆提交")
    ap.add_argument("--push", action="store_true", help="ship:提交後推當前分支(被拒只報黃)")
    ap.add_argument("--no-recover", action="store_true", help="ship:不先在本機別處找缺的環")
    ap.add_argument("--extra", action="append", default=[], help="recover / ship:另外要找的夾(可多次)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    vrn = Path(a.vrn_dir).resolve() if a.vrn_dir else HERE
    root = via_root(vrn)
    if a.verb == "check":
        r = check(vrn, root, scan_all=not a.heads)
        print_check(r)
        rp = write_receipt(root, r, a.json)
        if rp:
            say("  收據 %s" % rp)
        return {"GREEN": 0, "YELLOW": 2, "RED": 1}[r["lamp"]]
    if a.verb == "recover":
        r = recover(vrn, root, a.extra)
        print_recover(r)
        rp = write_receipt(root, r, a.json)
        if rp:
            say("  收據 %s" % rp)
        return {"GREEN": 0, "YELLOW": 2, "RED": 1}[r["lamp"]]
    r = ship(vrn, root, do_commit=a.commit, do_push=a.push, do_recover=not a.no_recover, extra_dirs=a.extra)
    print_ship(r)
    rp = write_receipt(root, r, a.json)
    if rp:
        say("  收據 %s" % rp)
    return {"GREEN": 0, "YELLOW": 2, "RED": 1}[r["lamp"]]


if __name__ == "__main__":
    sys.exit(main())
