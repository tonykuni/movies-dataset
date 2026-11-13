#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL143_MergeMedic v0106 — 薄尾:拉齊醫生加「分支合併」branch-merge(後合者升版 L25 · 三方鍵聯集 · 撞號改號 · 號冊身分判)

為什麼(操作員 2026-11-13:「合併 optimistic-goodall 自動完成」「用目前VCGC引擎去完成整合流程 若引擎未完成先完成引擎」):
  前版醫生是「工作站拉齊 main」用的:同名雙物一律取遠端(本地那支丟)、再生冊取遠端、只認台帳聯集。
  兩條 AI 分支互合時那三條律會丟東西 —— 實測 upbeat-feynman × optimistic-goodall:
    · 同版號雙物 6 族(政策冊 v0118 · 需求冊 v0249 · 工作流冊 v0147 · 盤點冊 v0225 · MCP v0103 · SDD v0108)取遠端 = 本分支內容全丟
    · 交接冊 / 元件冊 / 編號冊 / 座位冊兩邊都改 → 取遠端 = 本分支待辦(REQ224–244)全丟
    · 律號 L129–L132、需求 VCGC-REQ223 兩邊各發給不同東西(同號異物)
    · 號冊 VIA_NumberBooks/*.jsonl 同號異身分 600+ 列(兩邊從同一基準各自往下發)
本版只加一個動詞 branch-merge(其餘 status / plan / sync / resolve / 自測 全照 v0105 → v0104):
  ① 預檢:工作樹乾淨 · 取 merge-base
  ② 改號提交(只動「我方」= HEAD 自 merge-base 起新增 / 改過的檔;他方一字不動):
     · 版號族:我方新增版號 ≤ 他方新增最大版號(且內容不同)→ 我方整串往上排到他方尾版之後(git mv · 保序)。
       搬過的檔內:自己的版號字樣照對照表改;釘名前版(FAMILY_v<我方前一版>)改指他方尾版 → 鏈 = 他方尾 → 我方
     · 代碼族(冊內鍵):政策 laws.id · 需求 requirements.code · 工作流 workflows.code · 盤點 stations.id · 交接 work_items.id / test_cases 鍵
       兩邊各自新增同鍵且內容不同 = 同號異物 → 我方改成「兩邊聯集最大號 + 1」(字首與位數照舊;非數字鍵加 -b)
     · 引用改寫:我方改過的文字檔裡,舊檔名記號 / 舊代碼(含 VCGC-REQnnn 的裸 REQnnn)一律改新號;
       不改:*.jsonl 帳本 · *_Ledger_* · 交接證據 · VIA_Reports · 備份 · intake / references(凍結)
  ③ git merge --no-ff(零 force · 零 reset · 零刪檔)
  ④ 解衝突:
     · JSON 冊(有基準)= 三方遞迴合併:單邊改取那邊;兩邊改 → dict 逐鍵、清單有共同鍵(id/code/key/name/case/path)逐筆、
       同長純量清單逐位、其他純量清單取聯集(刪除照單邊);葉子兩邊都改 → 指尾版指標取較新版號,其餘取他方(全記)
     · 號冊 *.jsonl(VIA_NumberBooks)= 他方全列在前;我方獨有列:同號同身分 = 重複不加 · 同號異身分 = 不加、記「待重發」·
       同身分異號 = 不加、記別名;其餘附後(身分 = name + source)
     · 其他 *.jsonl / 帳本 = 前版台帳聯集(MDL250)· 交接證據 docs/handoff/evidence/* = 再生物取他方(合併後重跑案)
     · 修改 / 刪除衝突 = 保留有改的那邊(零刪除)· 其餘 = 誠實停(MANUAL)
  ⑤ 搬過的冊(我方新尾)= 三方聯集(基準 = merge-base 時該族尾版 · 他方尾版 · 我方)→ 內容 = 他方全部 + 我方新增;
     requirements 冊的 tally 依 status 重算
  ⑥ 合併提交 + 差異紀錄 docs/handoff/ai/merges/MERGE_<分支>_<時間>.json(版號搬家 · 代碼改號 · 號冊待重發 · 葉子取捨)
     → 之後照常跑 VCGC 閘:編號 --apply / 稽核 0·0·0 · registry-sync · 搬過族的 --selftest · handoff test · test --quick
  不加 --apply = 乾跑(只印計畫,零寫入)。零網路(除 git fetch)· 不用 TA-Lib · 提交署名用倉庫自己的 git 設定,不寫死。
用法:python <本檔> branch-merge <ref> [--apply] [--root <repo>] [--trailer-file <檔>] · --selftest(先前版,再本版)
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

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL143_MergeMedic"
VERSION = "v0106"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


_PRIOR_FILE = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("medic_prior_for_" + Path(__file__).stem, _PRIOR_FILE)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


MISSING = object()
VER_RX = re.compile(r"^(?P<stem>.+)_v(?P<v>\d{4})\.(?P<ext>[A-Za-z0-9]+)$")
SKIP_REWRITE_RX = re.compile(r"(\.jsonl$|_Ledger_|/docs/handoff/evidence/|^docs/handoff/evidence/|VIA_Reports/|/backup/|/intake|/references/)")
TEXT_EXT = {".py", ".json", ".md", ".txt", ".html", ".yml", ".yaml", ".toml", ".cfg", ".ini", ""}
NO_TOUCH_EXT = {".ps1", ".psm1", ".psd1", ".cmd", ".bat"}          # L70:.ps1 等殼腳本一字不改(引用只列不改)
# 獨立系統律(L123):只改 VCGC 自己的地盤;他系統(functional modules/ 等)只列不改
VCGC_OWNED_RX = re.compile(r"^(VeritasIntelligenceAnalytics/supportive modules/|VeritasIntelligenceAnalytics/docs/|supportive modules/|docs/|reg/|\.claude/|CLAUDE\.md$|AGENTS\.md$|\.mcp\.json$|NOTE\.md$)")
EVIDENCE_RX = re.compile(r"(^|/)docs/handoff/evidence/")
NUMBERBOOK_RX = re.compile(r"(^|/)VIA_NumberBooks/[^/]+\.jsonl$")
SHORT_RX = re.compile(r"^((?:[A-Z]+_)+?[A-Z]+\d+)_")
KEY_CANDIDATES = ("id", "code", "key", "case", "name", "path")
# 代碼族:冊家族 stem → [(集合路徑, 鍵欄)];集合為 dict 時鍵欄 = None(鍵本身)
CODE_BOOKS = {
    "VIA_Policy_Laws_SSOT": [("laws", "id")],
    "VIA_Requirements_SSOT": [("requirements", "code")],
    "VIA_Workflow_VCGC_SSOT": [("workflows", "code")],
    "VIA_VCGC_FunctionInventory_SSOT": [("stations", "id")],
    "VIA_Handoff_Continuity_SSOT": [("work_items", "id"), ("test_cases", None)],
}


# ───────────────────────── git 小工具 ─────────────────────────
def g(root: Path, *args, check=False) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=1800)
    if check and r.returncode != 0:
        raise RuntimeError("git " + " ".join(args[:3]) + " → " + (r.stderr or r.stdout).strip()[:300])
    return r


def gadd(root: Path, *paths: str) -> None:
    """git add,遇 index.lock(背景監控同時碰 git)退避重試;仍失敗才拋。"""
    import time
    last = ""
    for i in range(10):
        r = g(root, "add", "--", *paths)
        if r.returncode == 0:
            return
        last = (r.stderr or r.stdout).strip()
        if "index.lock" not in last:
            break
        time.sleep(min(0.3 * (2 ** i), 8))
    raise RuntimeError("git add → " + last[:300])


def gbytes(root: Path, spec: str) -> bytes | None:
    r = subprocess.run(["git", "-C", str(root), "show", spec], capture_output=True, timeout=600)
    return r.stdout if r.returncode == 0 else None


def changed(root: Path, a: str, b: str, filt: str = "AM") -> list:
    r = g(root, "diff", "--name-only", "-z", "--no-renames", "--diff-filter=" + filt, a, b)
    return [p for p in r.stdout.split("\0") if p]


def tree_files(root: Path, ref: str) -> list:
    r = g(root, "ls-tree", "-r", "-z", "--name-only", ref)
    return [p for p in r.stdout.split("\0") if p]


def jload(b: bytes | None):
    if b is None:
        return MISSING
    try:
        return json.loads(b.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return MISSING


def jdump(obj, like: bytes | None = None) -> bytes:
    t = (like or b"").decode("utf-8", errors="replace")
    indent = 2 if t.startswith('{\n  "') else (1 if t.startswith('{\n "') else (None if t.startswith("{\"") else 1))
    out = json.dumps(obj, ensure_ascii=False, indent=indent)
    return (out + ("\n" if t.endswith("\n") or not t else "")).encode("utf-8")


# ───────────────────────── 三方遞迴合併 ─────────────────────────
def _keyfield(*lists):
    items = [x for lst in lists if isinstance(lst, list) for x in lst]
    if not items or not all(isinstance(x, dict) for x in items):
        return None
    for k in KEY_CANDIDATES:
        ok = True
        for lst in lists:
            if not isinstance(lst, list):
                continue
            vals = [x.get(k) for x in lst]
            if any(v is None or not isinstance(v, (str, int)) for v in vals) or len(set(vals)) != len(vals):
                ok = False
                break
        if ok:
            return k
    return None


_TAIL_TOKEN = re.compile(r"([A-Za-z][A-Za-z0-9_]*?)_v(\d{4})\b")


def _tail_pick(gv, hv):
    """葉子兩邊都改:兩個字串都指同族版號檔 → 取版號較大者(指尾版指標取較新);否則 None。"""
    if not (isinstance(gv, str) and isinstance(hv, str)):
        return None
    gm, hm = dict((m.group(1), int(m.group(2))) for m in _TAIL_TOKEN.finditer(gv)), dict((m.group(1), int(m.group(2))) for m in _TAIL_TOKEN.finditer(hv))
    common = set(gm) & set(hm)
    if not common:
        return None
    fam = sorted(common)[0]
    return hv if hm[fam] > gm[fam] else gv


def merge3(b, gv, hv, path: str, log: list):
    """b = 基準 · gv = 他方(theirs)· hv = 我方(ours);MISSING = 不存在。"""
    if _eq(gv, hv):
        return gv
    if _eq(hv, b):
        return gv
    if _eq(gv, b):
        return hv
    if gv is MISSING:
        log.append({"path": path, "how": "他方刪 · 我方改 → 留我方"})
        return hv
    if hv is MISSING:
        log.append({"path": path, "how": "我方刪 · 他方改 → 留他方"})
        return gv
    bb = b if b is not MISSING else None
    if isinstance(gv, dict) and isinstance(hv, dict) and (bb is None or isinstance(bb, dict)):
        bd = bb or {}
        out = OrderedDict()
        for k in list(gv.keys()) + [k for k in hv.keys() if k not in gv]:
            r = merge3(bd.get(k, MISSING), gv.get(k, MISSING), hv.get(k, MISSING), path + "." + str(k), log)
            if r is not MISSING:
                out[k] = r
        return out
    if isinstance(gv, list) and isinstance(hv, list) and (bb is None or isinstance(bb, list)):
        bl = bb or []
        kf = _keyfield(bl, gv, hv)
        if kf:
            bm, gm, hm = ({x[kf]: x for x in lst} for lst in (bl, gv, hv))
            order = [x[kf] for x in gv] + [x[kf] for x in hv if x[kf] not in gm]
            out = []
            for k in order:
                r = merge3(bm.get(k, MISSING), gm.get(k, MISSING), hm.get(k, MISSING), f"{path}[{kf}={k}]", log)
                if r is not MISSING:
                    out.append(r)
            return out
        if len(gv) == len(hv) == len(bl) and bl:
            return [merge3(bl[i], gv[i], hv[i], f"{path}[{i}]", log) for i in range(len(bl))]
        try:
            bs, gs, hs = (set(json.dumps(x, sort_keys=True, ensure_ascii=False) for x in lst) for lst in (bl, gv, hv))
        except TypeError:
            bs = gs = hs = set()
        ks = lambda x: json.dumps(x, sort_keys=True, ensure_ascii=False)  # noqa: E731
        out = [x for x in gv if not (ks(x) in bs and ks(x) not in hs)]
        out += [x for x in hv if ks(x) not in bs and ks(x) not in gs]
        return out
    pick = _tail_pick(gv, hv)
    if pick is not None:
        log.append({"path": path, "how": "葉子兩邊都改 · 指尾版指標取較新", "theirs": _short(gv), "ours": _short(hv), "took": "ours" if pick is hv else "theirs"})
        return pick
    log.append({"path": path, "how": "葉子兩邊都改 · 取他方", "theirs": _short(gv), "ours": _short(hv)})
    return gv


def _eq(a, b) -> bool:
    if a is MISSING or b is MISSING:
        return a is b
    return json.dumps(a, sort_keys=True, ensure_ascii=False) == json.dumps(b, sort_keys=True, ensure_ascii=False)


def _short(v) -> str:
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return s[:120]


def tally_fix(obj):
    if isinstance(obj, dict) and isinstance(obj.get("tally"), dict) and isinstance(obj.get("requirements"), list):
        obj["tally"] = dict(Counter(q.get("status") for q in obj["requirements"] if isinstance(q, dict)))
    return obj


# ───────────────────────── 號冊:身分判 ─────────────────────────
def _ident(row: dict) -> str:
    if row.get("name") or row.get("source"):
        return str(row.get("name")) + "|" + str(row.get("source"))
    full = str(row.get("full") or "")
    return full.split(" ", 1)[1] if " " in full else json.dumps({k: v for k, v in row.items() if k not in ("code", "updated_at", "issued_at", "ts")}, sort_keys=True, ensure_ascii=False)


def numberbook_union(base: bytes | None, theirs: bytes | None, ours: bytes | None) -> tuple[bytes, dict]:
    bl = set(l for l in (base or b"").decode("utf-8", "replace").splitlines() if l.strip())
    tl = [l for l in (theirs or b"").decode("utf-8", "replace").splitlines() if l.strip()]
    ol = [l for l in (ours or b"").decode("utf-8", "replace").splitlines() if l.strip() and l not in bl]
    tcode, tident = {}, {}
    for l in tl:
        try:
            r = json.loads(l)
        except ValueError:
            continue
        tcode[r.get("code")] = _ident(r)
        tident.setdefault(_ident(r), r.get("code"))
    tset = set(tl)
    out, st = list(tl), {"theirs": len(tl), "added": 0, "dup": 0, "reissue": [], "alias": []}
    for l in ol:
        if l in tset:
            st["dup"] += 1
            continue
        try:
            r = json.loads(l)
        except ValueError:
            out.append(l)
            st["added"] += 1
            continue
        c, i = r.get("code"), _ident(r)
        if c in tcode:
            if tcode[c] == i:
                st["dup"] += 1
            else:
                st["reissue"].append({"code": c, "ours": i[:120], "theirs": tcode[c][:120]})
            continue
        if i in tident:
            st["alias"].append({"ours_code": c, "theirs_code": tident[i], "ident": i[:120]})
            continue
        out.append(l)
        st["added"] += 1
        tcode[c] = i
        tident.setdefault(i, c)
    return ("\n".join(out) + "\n").encode("utf-8"), st


# ───────────────────────── ② 改號計畫 ─────────────────────────
def _families(paths: list) -> dict:
    fam = {}
    for p in paths:
        d, n = os.path.split(p)
        m = VER_RX.match(n)
        if m:
            fam.setdefault((d, m.group("stem"), m.group("ext")), []).append(int(m.group("v")))
    return fam


def plan_versions(root: Path, base: str, ours: str, theirs: str) -> list:
    """回 [{dir, stem, ext, map{old:new}, prior_old, prior_new}]。"""
    oa, ta = changed(root, base, ours, "A"), changed(root, base, theirs, "A")
    of, tf = _families(oa), _families(ta)
    plans = []
    for key, ovs in sorted(of.items()):
        if key not in tf:
            continue
        d, stem, ext = key
        tmax = max(tf[key])
        clash = []
        for v in sorted(ovs):
            if v > tmax:
                continue
            p = (d + "/" if d else "") + f"{stem}_v{v:04d}.{ext}"
            ob, tb = gbytes(root, f"{ours}:{p}"), gbytes(root, f"{theirs}:{p}")
            if tb is not None and ob == tb:
                continue  # 同檔同內容 = 兩邊都合過同一份,不搬
            clash.append(v)
        if not clash:
            continue
        lo = min(clash)
        moving = sorted(v for v in ovs if v >= lo)
        occupied = set(tf[key]) | set(v for v in ovs if v < lo)
        mp, nxt = {}, tmax + 1
        for v in moving:
            while nxt in occupied:
                nxt += 1
            mp[v] = nxt
            occupied.add(nxt)
            nxt += 1
        below = [v for v in set(ovs) | set(_families(tree_files(root, base)).get(key, [])) if v < lo]
        plans.append({"dir": d, "stem": stem, "ext": ext, "map": {f"{a:04d}": f"{b:04d}" for a, b in mp.items()},
                      "prior_old": f"{max(below):04d}" if below else None, "prior_new": f"{tmax:04d}"})
    return plans


def _collection(obj, cpath):
    return obj.get(cpath) if isinstance(obj, dict) else None


def _tail_path(root: Path, ref: str, stem: str) -> str | None:
    cands = [p for p in tree_files(root, ref) if VER_RX.match(os.path.basename(p)) and VER_RX.match(os.path.basename(p)).group("stem") == stem]
    return max(cands, key=lambda p: int(VER_RX.match(os.path.basename(p)).group("v"))) if cands else None


def plan_codes(root: Path, base: str, ours: str, theirs: str) -> list:
    """冊內鍵兩邊各自新增且內容不同 → 我方改號。回 [{book, coll, old, new}]"""
    renames = []
    for stem, specs in CODE_BOOKS.items():
        bp, op, tp = _tail_path(root, base, stem), _tail_path(root, ours, stem), _tail_path(root, theirs, stem)
        if not (op and tp):
            continue
        B = jload(gbytes(root, f"{base}:{bp}")) if bp else {}
        O, T = jload(gbytes(root, f"{ours}:{op}")), jload(gbytes(root, f"{theirs}:{tp}"))
        if O is MISSING or T is MISSING:
            continue
        B = {} if B is MISSING else B
        for coll, kf in specs:
            def keys(obj):
                c = _collection(obj, coll)
                if isinstance(c, dict):
                    return {k: v for k, v in c.items()}
                if isinstance(c, list):
                    return {x.get(kf): x for x in c if isinstance(x, dict) and x.get(kf) is not None}
                return {}
            bk, ok, tk = keys(B), keys(O), keys(T)
            onew = [k for k in ok if k not in bk]
            tnew = [k for k in tk if k not in bk]
            allk = set(ok) | set(tk)
            for k in onew:
                if k in tnew and not _eq(ok[k], tk[k]):
                    m = re.match(r"^(.*?)(\d+)$", str(k))
                    if m:
                        pre, w = m.group(1), len(m.group(2))
                        nums = [int(re.match(r"^(.*?)(\d+)$", str(x)).group(2)) for x in allk
                                if re.match(r"^(.*?)(\d+)$", str(x)) and re.match(r"^(.*?)(\d+)$", str(x)).group(1) == pre]
                        nums += [int(re.match(r"^(.*?)(\d+)$", r["new"]).group(2)) for r in renames if r["new"].startswith(pre)]
                        new = f"{pre}{max(nums) + 1:0{w}d}"
                    else:
                        new = str(k) + "-b"
                    renames.append({"book": stem, "coll": coll, "old": str(k), "new": new})
                    allk.add(new)
    return renames


def _code_rx(old: str):
    pats = [re.escape(old)]
    m = re.match(r"^[A-Z]+-(REQ\d+|WKF\d+)$", old)
    bare = m.group(1) if m else None
    rx = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(old) + r"(?![0-9])")
    bx = re.compile(r"(?<![A-Za-z0-9_-])" + re.escape(bare) + r"(?![0-9])") if bare else None
    return rx, bx, pats


def rewrite_text(text: str, vplans: list, crenames: list, moved_self: dict | None = None) -> tuple[str, int]:
    n = 0
    slots = []                       # 單趟:每處換成佔位、最後一次換回 —— 換過的字不會再被下一條吃到(v0103→v0104→v0105 連鎖)

    def hold(val: str) -> str:
        slots.append(val)
        return "\u0000V" + chr(0x4E00 + len(slots) - 1) + "\u0000"
    for p in vplans:
        stem = p["stem"]
        sm = SHORT_RX.match(stem + "_")
        for old, new in sorted(p["map"].items(), key=lambda kv: -int(kv[0])):
            for pat in (re.escape(stem) + r"_v" + old, re.escape(stem) + r" v" + old) + ((re.escape(sm.group(1)) + r" v" + old,) if sm else ()):
                text, k = re.subn(r"(?<![A-Za-z0-9_])" + pat + r"(?!\d)", lambda mm: hold(mm.group(0)[:-4] + new), text)
                n += k
    if moved_self:
        # 搬過的檔自己:釘名前版改指他方尾版;裸版號照對照表
        mp = moved_self["map"]
        if moved_self.get("prior_old"):
            text, k = re.subn(r"(?<![A-Za-z0-9_])" + re.escape(moved_self["stem"]) + r"_v" + moved_self["prior_old"] + r"(?!\d)",
                              lambda mm: hold(moved_self["stem"] + "_v" + moved_self["prior_new"]), text)
            n += k
        if mp:
            rx = re.compile(r"(?<![A-Za-z0-9_])v(" + "|".join(sorted(mp, key=lambda x: -int(x))) + r")(?!\d)")
            text, k = rx.subn(lambda mm: hold("v" + mp[mm.group(1)]), text)
            n += k
    for i, val in enumerate(slots):
        text = text.replace("\u0000V" + chr(0x4E00 + i) + "\u0000", val)
    if crenames:
        table = {}
        for r in crenames:
            rx, bx, _ = _code_rx(r["old"])
            table[r["old"]] = (rx, bx, r["new"])
        # 先換成佔位再換回,避免 L129→L133 後又被別條吃到
        holders = {}
        for i, (old, (rx, bx, new)) in enumerate(table.items()):
            h = f"\u0000MM{i}\u0000"
            text, k = rx.subn(h, text)
            n += k
            if bx:
                nb = re.match(r"^[A-Z]+-(.*)$", new).group(1)
                hb = f"\u0000MB{i}\u0000"
                text, k2 = bx.subn(hb, text)
                n += k2
                holders[hb] = nb
            holders[h] = new
        for h, new in holders.items():
            text = text.replace(h, new)
    return text, n


# ───────────────────────── 主流程 ─────────────────────────
def branch_merge(root: Path, ref: str, apply: bool = False, trailer: str = "", do_print: bool = True) -> dict:
    root = Path(root)
    rep = {"engine": Path(__file__).stem, "ref": ref, "apply": apply, "stamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
           "steps": [], "version_moves": [], "code_renames": [], "numberbooks": {}, "leaf_conflicts": [], "resolved": [], "manual": []}

    def step(name, state, note=""):
        rep["steps"].append({"name": name, "state": state, "note": note})
        if do_print:
            print("  [" + state + "] " + name + (" · " + note if note else ""))

    if g(root, "status", "--porcelain", "--untracked-files=no").stdout.strip():
        step("預檢:工作樹不乾淨(已追蹤檔有改動)", "STOP", "先提交或還原再合")
        rep["state"] = "STOP"
        return rep
    if (root / ".git" / "MERGE_HEAD").exists():
        step("預檢:已有合併進行中", "STOP", "git merge --abort 或先完成")
        rep["state"] = "STOP"
        return rep
    if apply and ref.startswith("origin/"):
        g(root, "fetch", "-q", "origin", ref.split("/", 1)[1])
    theirs = g(root, "rev-parse", ref).stdout.strip()
    if not theirs:
        step("取不到 " + ref, "STOP")
        rep["state"] = "STOP"
        return rep
    base = g(root, "merge-base", "HEAD", theirs).stdout.strip()
    ahead, behind = g(root, "rev-list", "--left-right", "--count", f"HEAD...{theirs}").stdout.split()
    rep.update(base=base[:12], theirs=theirs[:12], head=g(root, "rev-parse", "--short=12", "HEAD").stdout.strip(), ahead=int(ahead), behind=int(behind))
    step("分歧", "OK", f"本分支獨有 {ahead} · {ref} 獨有 {behind} · 基準 {base[:9]}")
    if int(behind) == 0:
        rep["state"] = "OK"
        step("對方沒有新提交", "OK")
        return rep

    vplans = plan_versions(root, base, "HEAD", theirs)
    crenames = plan_codes(root, base, "HEAD", theirs)
    for p in vplans:
        rep["version_moves"].append({"family": (p["dir"] + "/" if p["dir"] else "") + p["stem"] + "." + p["ext"],
                                     "map": p["map"], "prior": f"{p['prior_old']} → {p['prior_new']}"})
        step("版號搬家 " + p["stem"], "PLAN" if not apply else "RUN", ", ".join(f"v{a}→v{b}" for a, b in p["map"].items()))
    for r in crenames:
        rep["code_renames"].append(r)
        step("代碼改號 " + r["book"] + "." + r["coll"], "PLAN" if not apply else "RUN", r["old"] + " → " + r["new"])
    foreign = [m["family"] for m in rep["version_moves"] if not VCGC_OWNED_RX.search(m["family"])]
    if foreign:
        rep["state"] = "STOP"
        step("停:同版號雙物在他系統地盤(L123 VCGC 不代改;交該系統自己合)", "STOP", ", ".join(foreign[:5]))
        return rep
    if not apply:
        rep["state"] = "PLAN"
        step("乾跑結束(--apply 才寫)", "PLAN")
        return rep

    # ② 改號提交
    ours_changed = changed(root, base, "HEAD", "AM")
    moved = {}
    for p in vplans:
        for old, new in sorted(p["map"].items(), key=lambda kv: -int(kv[0])):
            src = (p["dir"] + "/" if p["dir"] else "") + f"{p['stem']}_v{old}.{p['ext']}"
            dst = (p["dir"] + "/" if p["dir"] else "") + f"{p['stem']}_v{new}.{p['ext']}"
            g(root, "mv", "-k", src, dst, check=True)
            moved[dst] = p
    nfiles, nsubs = 0, 0
    targets = set(ours_changed)
    for p in vplans:
        for old, new in p["map"].items():
            targets.discard((p["dir"] + "/" if p["dir"] else "") + f"{p['stem']}_v{old}.{p['ext']}")
    targets |= set(moved)
    rep["refs_left"] = []
    for rel in sorted(targets):
        fp = root / rel
        if not fp.is_file():
            continue
        why = ("L70 殼腳本不改" if Path(rel).suffix.lower() in NO_TOUCH_EXT
               else ("L123 他系統地盤不改" if not VCGC_OWNED_RX.search(rel) else ""))
        if why:
            try:
                t0 = fp.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            _t1, hits = rewrite_text(t0, vplans, crenames, None)
            if hits:
                rep["refs_left"].append({"file": rel, "hits": hits, "why": why})
            continue
        if Path(rel).suffix.lower() not in TEXT_EXT:
            continue
        if SKIP_REWRITE_RX.search("/" + rel) and rel not in moved:
            continue
        if fp.resolve() == Path(__file__).resolve() or Path(rel).name.startswith(_STEM + "_v"):
            continue   # 引擎自己(含自測夾具裡的示範號)不改:2026-11-13 實跑抓到改號步改到自己的夾具
        try:
            txt = fp.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        new, n = rewrite_text(txt, vplans, crenames, moved.get(rel))
        if n and new != txt:
            fp.write_text(new, encoding="utf-8")
            gadd(root, rel)
            nfiles += 1
            nsubs += n
    if vplans or crenames:
        msg = (f"chore(vcgc): 合併前改號(L25 後合者升版 · {Path(__file__).stem} branch-merge {ref})\n\n"
               + "".join(f"- 版號 {m['family']}: {m['map']}\n" for m in rep["version_moves"])
               + "".join(f"- 代碼 {r['book']}.{r['coll']}: {r['old']} → {r['new']}\n" for r in crenames)
               + f"- 引用改寫 {nfiles} 檔 · {nsubs} 處(只動本分支改過、VCGC 地盤的檔;帳本 / 證據 / 凍結 / .ps1 / 他系統不動)\n"
               + "".join(f"- 只列不改 {x['file']}({x['why']} · {x['hits']} 處)\n" for x in rep["refs_left"]) + (("\n" + trailer) if trailer else ""))
        c = g(root, "commit", "-q", "-m", msg)
        step("改號提交", "OK" if c.returncode == 0 else "FAIL", f"搬 {len(moved)} 檔 · 改寫 {nfiles} 檔 {nsubs} 處")
        if c.returncode != 0:
            rep["state"] = "FAIL"
            return rep

    # ③ 合併
    env = dict(os.environ, GIT_EDITOR="true", GIT_MERGE_AUTOEDIT="no")
    r = subprocess.run(["git", "-C", str(root), "merge", "--no-ff", "--no-commit", theirs], capture_output=True, text=True, env=env, timeout=1800)
    un = PRIOR.unmerged(root)
    step("merge --no-ff --no-commit", "OK" if not un else "RUN", f"衝突 {len(un)} 件")

    # ④ 解衝突
    for u in un:
        path, xy = u["path"], u["xy"]
        b, o, t = gbytes(root, f":1:{path}"), gbytes(root, f":2:{path}"), gbytes(root, f":3:{path}")
        ent = {"path": path, "xy": xy}
        try:
            if o is None or t is None:
                keep = o if o is not None else t
                (root / path).write_bytes(keep)
                ent["how"] = "修改/刪除衝突 → 留有改的那邊(零刪除)"
            elif EVIDENCE_RX.search(path):
                (root / path).write_bytes(t)
                ent["how"] = "交接證據 = 再生物 → 取他方(合併後重跑案)"
            elif NUMBERBOOK_RX.search(path):
                data, st = numberbook_union(b, t, o)
                (root / path).write_bytes(data)
                rep["numberbooks"][os.path.basename(path)] = {"theirs": st["theirs"], "added": st["added"], "dup": st["dup"],
                                                             "reissue": len(st["reissue"]), "alias": len(st["alias"]),
                                                             "reissue_codes": [x["code"] for x in st["reissue"]][:2000],
                                                             "alias_pairs": st["alias"][:500]}
                ent["how"] = f"號冊身分聯集 · 他方 {st['theirs']} + 我方 {st['added']} · 重複 {st['dup']} · 待重發 {len(st['reissue'])} · 別名 {len(st['alias'])}"
            elif path.endswith(".jsonl") or PRIOR.classify(path) == "LEDGER":
                data, info = PRIOR.ledger_union(o, t)
                if data is None:
                    raise ValueError(str(info.get("why")))
                (root / path).write_bytes(data)
                ent["how"] = "台帳聯集(只增)"
            elif jload(o) is not MISSING and jload(t) is not MISSING:
                log = []
                merged = tally_fix(merge3(jload(b), jload(t), jload(o), "$", log))
                (root / path).write_bytes(jdump(merged, t))
                rep["leaf_conflicts"] += [dict(x, file=path) for x in log]
                ent["how"] = f"JSON 三方鍵聯集 · 葉子取捨 {len(log)}"
            else:
                ent["how"] = "MANUAL(非 JSON / 非帳本 / 非證據)"
                rep["manual"].append(path)
                if do_print:
                    print("  [MANUAL] " + path)
                continue
            gadd(root, path)
            rep["resolved"].append(ent)
            if do_print:
                print("  [OK] " + path[-80:] + " · " + ent["how"])
        except Exception as e:  # noqa: BLE001
            rep["manual"].append(path)
            if do_print:
                print("  [FAIL] " + path + " · " + str(e)[:160])
    if rep["manual"]:
        rep["state"] = "MANUAL"
        step("停:仍有未解衝突(現場保留;git merge --abort 可回復)", "MANUAL", ", ".join(rep["manual"][:5]))
        _write_record(root, rep)
        return rep

    # ⑤ 搬過的冊 = 三方聯集
    for dst, p in moved.items():
        if p["ext"] != "json":
            continue
        tp = _tail_path(root, theirs, p["stem"])
        bp = _tail_path(root, base, p["stem"])
        if not tp:
            continue
        tb, bbytes, ob = gbytes(root, f"{theirs}:{tp}"), gbytes(root, f"{base}:{bp}") if bp else None, (root / dst).read_bytes()
        T, B, O = jload(tb), jload(bbytes), jload(ob)
        if T is MISSING or O is MISSING:
            continue
        log = []
        merged = tally_fix(merge3(B, T, O, "$", log))
        newv = "v" + VER_RX.match(os.path.basename(dst)).group("v")
        if isinstance(merged, dict):
            if "version" in merged:
                merged["version"] = newv
            if "prior" in merged and isinstance(merged["prior"], str):
                merged["prior"] = os.path.basename(tp)
            merged["merge_" + newv] = (f"{Path(__file__).stem} branch-merge {ref}:本版 = 他方尾版 {os.path.basename(tp)} 全部 + 本分支新增"
                                       f"(L25 後合者升版;本分支原版號 v{[k for k, v in p['map'].items() if 'v' + v == newv][0]})")
        (root / dst).write_bytes(jdump(merged, ob))
        gadd(root, dst)
        rep["leaf_conflicts"] += [dict(x, file=dst) for x in log]
        step("搬過的冊三方聯集 " + os.path.basename(dst), "OK", f"基準 {os.path.basename(bp or '-')} · 他方 {os.path.basename(tp)} · 葉子取捨 {len(log)}")

    rec = _write_record(root, rep)
    gadd(root, rec)
    msg = (f"Merge {ref} → {g(root, 'rev-parse', '--abbrev-ref', 'HEAD').stdout.strip()}({Path(__file__).stem} branch-merge · L25 後合者升版 · 只增聯集)\n\n"
           f"- 衝突 {len(un)} 件全解:" + ", ".join(f"{k} {v}" for k, v in Counter(e['how'].split(' ')[0] for e in rep['resolved']).items()) + "\n"
           f"- 版號搬家 {len(rep['version_moves'])} 族 · 代碼改號 {len(rep['code_renames'])} · 葉子取捨 {len(rep['leaf_conflicts'])}\n"
           f"- 號冊待重發 {sum(v['reissue'] for v in rep['numberbooks'].values())}(合併後 CGC_MDL237 --apply 重發)\n"
           f"- 差異紀錄 {rec}\n" + (("\n" + trailer) if trailer else ""))
    c = g(root, "commit", "-q", "-m", msg)
    step("合併提交", "OK" if c.returncode == 0 else "FAIL", (c.stderr or "").strip()[:160])
    rep["state"] = "OK" if c.returncode == 0 else "FAIL"
    rep["head_after"] = g(root, "rev-parse", "--short=12", "HEAD").stdout.strip()
    return rep


def _write_record(root: Path, rep: dict) -> str:
    d = root / "VeritasIntelligenceAnalytics" / "docs" / "handoff" / "ai" / "merges"
    if not (root / "VeritasIntelligenceAnalytics").is_dir():
        d = root / "docs" / "handoff" / "ai" / "merges"
    d.mkdir(parents=True, exist_ok=True)
    name = "MERGE_" + re.sub(r"[^A-Za-z0-9._-]+", "_", rep["ref"].split("/")[-1]) + "_" + rep["stamp"] + ".json"
    (d / name).write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return str((d / name).relative_to(root))


# ───────────────────────── 自測 ─────────────────────────
def selftest() -> int:
    results = []

    def chk(name, cond, note=""):
        results.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + (" · " + str(note) if note else ""))

    print("[前版自測] " + _PRIOR_FILE.name)
    pr = subprocess.run([sys.executable, str(_PRIOR_FILE), "--selftest"], capture_output=True, text=True, timeout=1800)
    chk("① 前版 " + _PRIOR_FILE.stem + " 自測照過", pr.returncode == 0, (pr.stdout.strip().splitlines() or [""])[-1][:100])

    with tempfile.TemporaryDirectory() as td:
        R = Path(td) / "repo"
        R.mkdir()
        G = lambda *a: subprocess.run(["git", "-C", str(R), *a], capture_output=True, text=True)  # noqa: E731
        G("init", "-q", "-b", "main")
        G("config", "user.name", "selftest")
        G("config", "user.email", "selftest@localhost")
        reg = R / "reg"
        reg.mkdir()
        nb = reg / "VIA_NumberBooks"
        nb.mkdir()
        ev = R / "docs" / "handoff" / "evidence"
        ev.mkdir(parents=True)
        W = lambda p, s: (p.parent.mkdir(parents=True, exist_ok=True), p.write_text(s, encoding="utf-8"))  # noqa: E731
        Jw = lambda p, o: W(p, json.dumps(o, ensure_ascii=False, indent=1) + "\n")  # noqa: E731
        W(reg / "FAM_MDL900_Tool_v0102.py", "VERSION = 'v0102'\ndef feats():\n    return ['base']\n")
        Jw(reg / "VIA_Policy_Laws_SSOT_v0117.json", {"version": "v0117", "prior": "VIA_Policy_Laws_SSOT_v0116.json",
                                                    "laws": [{"id": "L1", "zh": "一"}]})
        Jw(reg / "VIA_Handoff_Continuity_SSOT_v0100.json", {"work_items": [{"id": "W1", "state": "PENDING"}],
                                                           "test_cases": {"c1": {"m": "a"}}, "watch": ["x"]})
        W(nb / "VIA_NumberBook_MDL_v0100.jsonl", json.dumps({"code": "N-001", "name": "base", "source": "s0"}) + "\n")
        W(ev / "e.txt", "base\n")
        Jw(R / ".mcp.json", {"mcpServers": {"v": {"args": ["reg/FAM_MDL900_Tool_v0102.py", "--serve"]}}})
        G("add", "-A")
        G("commit", "-q", "-m", "base")
        G("checkout", "-q", "-b", "theirs")
        W(reg / "FAM_MDL900_Tool_v0103.py", "import importlib\nPRIOR = 'FAM_MDL900_Tool_v0102.py'\nVERSION = 'v0103'\ndef feats():\n    return ['base', 'theirs']\n")
        Jw(reg / "VIA_Policy_Laws_SSOT_v0118.json", {"version": "v0118", "prior": "VIA_Policy_Laws_SSOT_v0117.json",
                                                    "laws": [{"id": "L1", "zh": "一"}, {"id": "L2", "zh": "他方二"}]})
        Jw(reg / "VIA_Handoff_Continuity_SSOT_v0100.json", {"work_items": [{"id": "W1", "state": "VERIFIED"}, {"id": "WT", "state": "PENDING"}],
                                                           "test_cases": {"c1": {"m": "a"}, "ct": {"m": "t"}}, "watch": ["x", "t"]})
        W(nb / "VIA_NumberBook_MDL_v0100.jsonl", json.dumps({"code": "N-001", "name": "base", "source": "s0"}) + "\n"
          + json.dumps({"code": "N-002", "name": "theirs", "source": "st"}) + "\n" + json.dumps({"code": "N-003", "name": "shared", "source": "ss"}) + "\n")
        W(ev / "e.txt", "theirs\n")
        Jw(R / ".mcp.json", {"mcpServers": {"v": {"args": ["reg/FAM_MDL900_Tool_v0103.py", "--serve"]}, "t": {"args": ["x"]}}})
        G("add", "-A")
        G("commit", "-q", "-m", "theirs")
        G("checkout", "-q", "main")
        G("checkout", "-q", "-b", "ours")
        W(reg / "FAM_MDL900_Tool_v0103.py", "PRIOR = 'FAM_MDL900_Tool_v0102.py'\nVERSION = 'v0103'\n# FAM_MDL900_Tool v0103 本支\ndef feats():\n    return ['base', 'ours']\n")
        W(reg / "FAM_MDL900_Tool_v0104.py", "PRIOR = 'glob'\nVERSION = 'v0104'  # 疊在 v0103 上\n")
        Jw(reg / "VIA_Policy_Laws_SSOT_v0118.json", {"version": "v0118", "prior": "VIA_Policy_Laws_SSOT_v0117.json",
                                                    "laws": [{"id": "L1", "zh": "一"}, {"id": "L2", "zh": "我方二(見 L2)"}]})
        Jw(reg / "VIA_Handoff_Continuity_SSOT_v0100.json", {"work_items": [{"id": "W1", "state": "PENDING"}, {"id": "WO", "state": "PENDING", "why": "依 L2"}],
                                                           "test_cases": {"c1": {"m": "a"}, "co": {"m": "o"}}, "watch": ["x", "o"]})
        W(nb / "VIA_NumberBook_MDL_v0100.jsonl", json.dumps({"code": "N-001", "name": "base", "source": "s0"}) + "\n"
          + json.dumps({"code": "N-002", "name": "ours", "source": "so"}) + "\n" + json.dumps({"code": "N-009", "name": "shared", "source": "ss"}) + "\n"
          + json.dumps({"code": "N-010", "name": "ours2", "source": "so2"}) + "\n")
        W(ev / "e.txt", "ours\n")
        W(R / "NOTE.md", "本分支新律 L2;工具 FAM_MDL900_Tool_v0104 · FAM_MDL900 v0103;L20 不動;MDL2 不動\n")
        Jw(R / ".mcp.json", {"mcpServers": {"v": {"args": ["reg/FAM_MDL900_Tool_v0104.py", "--serve"]}}})
        W(R / "Invoke-X-v0100.ps1", "# 依 L2 · FAM_MDL900_Tool_v0104\n")
        W(R / "functional modules" / "VRN" / "x.md", "VRN 自己的檔提到 L2\n")
        G("add", "-A")
        G("commit", "-q", "-m", "ours")

        dry = branch_merge(R, "theirs", apply=False, do_print=False)
        chk("② 乾跑零寫入:只出計畫(版號搬家 1 族 · 代碼改號 L2→L3)",
            dry["state"] == "PLAN" and dry["version_moves"] and dry["version_moves"][0]["map"] == {"0103": "0104", "0104": "0105"}
            and any(r["old"] == "L2" and r["new"] == "L3" for r in dry["code_renames"]) and not G("status", "--porcelain").stdout.strip(),
            json.dumps(dry["version_moves"], ensure_ascii=False)[:120])
        rep = branch_merge(R, "theirs", apply=True, do_print=False, trailer="Selftest-Trailer: yes")
        chk("③ 合併完成提交 · 零衝突殘留 · 零標記", rep["state"] == "OK" and not (R / ".git" / "MERGE_HEAD").exists()
            and "<<<<<<<" not in "".join(p.read_text(encoding="utf-8", errors="replace") for p in R.rglob("*") if p.is_file() and ".git" not in p.parts),
            rep["state"] + " · " + json.dumps(rep["manual"], ensure_ascii=False))
        t3 = (reg / "FAM_MDL900_Tool_v0103.py").read_text(encoding="utf-8")
        o4 = (reg / "FAM_MDL900_Tool_v0104.py").read_text(encoding="utf-8")
        o5 = (reg / "FAM_MDL900_Tool_v0105.py").read_text(encoding="utf-8") if (reg / "FAM_MDL900_Tool_v0105.py").exists() else ""
        chk("④ 同版號雙物:他方留原號 · 我方往上搬(v0103→v0104 · v0104→v0105)· 版號字樣跟著改",
            "'theirs'" in t3 and "'ours'" in o4 and "VERSION = 'v0104'" in o4 and "VERSION = 'v0105'" in o5)
        chk("⑯ 連鎖搬家單趟換:我方 v0103 檔內「FAM_MDL900_Tool v0103」→ v0104(不被下一條再推成 v0105)",
            "FAM_MDL900_Tool v0104 本支" in o4 and "v0105" not in o4, [l for l in o4.splitlines() if "本支" in l])
        chk("⑤ 搬過的檔釘名前版改指他方尾版(鏈 = 他方 v0103 → 我方 v0104)", "FAM_MDL900_Tool_v0103.py" in o4 and "v0102" not in o4, o4.splitlines()[0])
        note = (R / "NOTE.md").read_text(encoding="utf-8")
        chk("⑥ 引用改寫只動我方檔、只動撞號(L2→L3 · 檔名 v0104→v0105 · 短名 v0103→v0104;L20 / MDL2 不動)",
            "新律 L3" in note and "FAM_MDL900_Tool_v0105" in note and "FAM_MDL900 v0104" in note and "L20 不動" in note and "MDL2 不動" in note, note.strip())
        pol = json.loads((reg / "VIA_Policy_Laws_SSOT_v0119.json").read_text(encoding="utf-8")) if (reg / "VIA_Policy_Laws_SSOT_v0119.json").exists() else {}
        ids = [x["id"] for x in pol.get("laws", [])]
        chk("⑦ 搬過的冊 = 他方全部 + 我方新增(L1 · 他方 L2 · 我方改號 L3)· version / prior 指對",
            ids == ["L1", "L2", "L3"] and pol.get("version") == "v0119" and pol.get("prior") == "VIA_Policy_Laws_SSOT_v0118.json"
            and "他方二" in json.dumps(pol, ensure_ascii=False) and "我方二(見 L3)" in json.dumps(pol, ensure_ascii=False), ids)
        ho = json.loads((reg / "VIA_Handoff_Continuity_SSOT_v0100.json").read_text(encoding="utf-8"))
        chk("⑧ 兩邊都改的冊 = 三方鍵聯集(W1 取他方新態 · WT + WO 都在 · 我方 why 跟著改號 · test_cases 三鍵 · watch 聯集)",
            [w["id"] for w in ho["work_items"]] == ["W1", "WT", "WO"] and ho["work_items"][0]["state"] == "VERIFIED"
            and ho["work_items"][2]["why"] == "依 L3" and set(ho["test_cases"]) == {"c1", "ct", "co"} and ho["watch"] == ["x", "t", "o"],
            json.dumps(ho, ensure_ascii=False)[:160])
        rows = [json.loads(l) for l in (nb / "VIA_NumberBook_MDL_v0100.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        codes = [r["code"] for r in rows]
        stn = rep["numberbooks"].get("VIA_NumberBook_MDL_v0100.jsonl", {})
        chk("⑨ 號冊身分判:同號異身分(N-002 我方)不加記待重發 · 同身分異號(N-009)記別名 · 獨有(N-010)附後",
            codes == ["N-001", "N-002", "N-003", "N-010"] and rows[1]["name"] == "theirs" and stn.get("reissue") == 1 and stn.get("alias") == 1, codes)
        chk("⑩ 交接證據 = 再生物取他方", (ev / "e.txt").read_text(encoding="utf-8") == "theirs\n")
        mcp = json.loads((R / ".mcp.json").read_text(encoding="utf-8"))
        chk("⑪ 指尾版指標取較新(.mcp.json 指我方新尾 v0105)· 他方新增伺服器留著",
            mcp["mcpServers"]["v"]["args"][0] == "reg/FAM_MDL900_Tool_v0105.py" and "t" in mcp["mcpServers"], json.dumps(mcp, ensure_ascii=False)[:120])
        recs = list((R / "docs" / "handoff" / "ai" / "merges").glob("MERGE_theirs_*.json"))
        log = G("log", "--format=%B", "-2").stdout
        chk("⑫ 差異紀錄入倉 · 兩個提交(改號 · 合併)都帶 trailer", len(recs) == 1 and log.count("Selftest-Trailer: yes") == 2
            and not G("status", "--porcelain").stdout.strip(), recs[0].name if recs else "無紀錄")
        chk("⑮ L70 · L123:.ps1 與他系統檔一字不改、只列(refs_left)",
            (R / "Invoke-X-v0100.ps1").read_text(encoding="utf-8") == "# 依 L2 · FAM_MDL900_Tool_v0104\n"
            and (R / "functional modules" / "VRN" / "x.md").read_text(encoding="utf-8") == "VRN 自己的檔提到 L2\n"
            and sorted(x["file"] for x in rep.get("refs_left", [])) == ["Invoke-X-v0100.ps1", "functional modules/VRN/x.md"],
            json.dumps(rep.get("refs_left"), ensure_ascii=False)[:160])
        G("checkout", "-q", "-b", "dirty")
        W(R / "NOTE.md", "改了沒提交\n")
        st = branch_merge(R, "theirs", apply=True, do_print=False)
        chk("⑬ 髒樹誠實停(不 stash 不硬合)", st["state"] == "STOP")

    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑭ 加速器橋在 · 不匯入 TA-Lib · 不寫死署名信箱", "VIA:ACCEL-BRIDGE" in src and ("import " + "talib") not in src
        and "user.email=" not in src.split("def selftest")[0])
    ok = sum(results)
    print(f"[計] {Path(__file__).stem} 自測 {ok}/{len(results)} · " + ("PASS" if ok == len(results) else "FAIL"))
    return 0 if ok == len(results) else 1


def main() -> int:
    a = sys.argv[1:]
    if a and a[0] == "--selftest":
        return selftest()
    if a and a[0] == "branch-merge":
        if len(a) < 2:
            print("用法:branch-merge <ref> [--apply] [--root <repo>] [--trailer-file <檔>]")
            return 2
        root = Path(a[a.index("--root") + 1]) if "--root" in a else PRIOR.ROOT_DEFAULT
        trailer = Path(a[a.index("--trailer-file") + 1]).read_text(encoding="utf-8").strip() if "--trailer-file" in a else ""
        rep = branch_merge(Path(root), a[1], apply="--apply" in a, trailer=trailer)
        print(f"[{Path(__file__).stem}] branch-merge {a[1]} · {rep.get('state')} · 版號搬家 {len(rep['version_moves'])} · 代碼改號 {len(rep['code_renames'])}"
              f" · 衝突解 {len(rep['resolved'])} · 未解 {len(rep['manual'])}")
        return 0 if rep.get("state") in ("OK", "PLAN") else 1
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
