#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL178_ToolInventoryRatchet v0101 — 工具與支援性模組盤點 + 棘輪 + 撞號 + 同意閘(批695)
=========================================================================
操作員令(批691B):「這裡負責環境工具及 VCGC 對接子系統,並盤點支援性及所有工具模組;
  將 VRN 接進來補充,**以之前紀錄最成功的狀態來自測、自修正**。」

先量再寫(LL341):樹上已經有 `CGC_MDL164_GovernanceCompletenessAudit`,
但它審的是**冊 / 收容 / 自指 / 規格**,不是「每一支在四個註冊面上的狀態」;
而 `VIA_Reports/**/GRID_*.json` 躺著 190+ 份逐站存證,**沒有任何引擎在讀它們**。
所以本支補的是這兩個真空,不是再開一份清冊。

## 四把尺,分四欄各自報(LL327,永不相加)

**① 盤點**：支援性模組 × 工具短令,逐支照 LL199 四個註冊面量：
     冊(中央元件冊 ACTIVE) · 自測門(--selftest) · 格子站(尾版格子上有沒有) · 梭(bin/*.cmd)
   缺哪一面就指名哪一面。**缺件不是壞掉**——四態誠實,不混成一個百分比。

**② 棘輪**：掃過**每一份**歷史格子存證,取每一站**歷來最佳**狀態,再跟最新一跑比：
     退步  曾經 OK、現在 FAIL/TIMEOUT      ← 真正要看的那一欄
     未曾綠 從來沒有 OK 過                  ← 不是退步(它沒有退,它本來就沒站起來)
     進步  歷來最佳不是 OK、現在 OK
     配不到 站名改過或新站                  ← **不是退步**,單獨一欄
   站名會隨敘述改版而變(「二十二檢」→「二十六檢」),
   直接拿全名當鍵會把**改名誤判成退步**——所以配不到的先做正規化再配,
   仍配不到就誠實列進「配不到」,不塞進退步裡充數。

## 自修正的邊界(這一支只做安全的,其餘只提不做)

  可代跑   registry-sync(冪等)——但**它補不完**:批691B 實測 --apply 之後回「新 0」,
           冊外仍有 92 支尾版模組沒被 VCGC 的掃描規則走到。可代跑那一欄一定要帶這句話。
  只提不做 缺自測門 / 缺格子站 / 缺梭 —— 那要寫碼,是下一批的事,不是掃描器該順手做的
  永不     裝套件 · 開同意閘 · 改任何 .ps1(L70)——那三件永遠是操作員的手

## 律

  L77   掃描根一律帶排除清單(退役 / 封存 / 收容 / 快照副本 / __pycache__)
  LL332 會隨裁定改變的數字不可以當斷言——自測驗的是不變量,不是今天的計數
  LL336 探針值從那一份資料當場取,不打字進來
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

import ast
import glob as _glob
import json
import re
import sys
from collections import Counter
from pathlib import Path

# ===== [VIA:ACCEL-BRIDGE] 加速器橋(缺席=原樣跑,零行為變更)=====
try:  # pragma: no cover
    _p = Path(__file__).resolve()
    while _p.parent != _p:
        _d = _p / "supportive modules"
        if _d.is_dir():
            _h = sorted(_glob.glob(str(_d / "VeritasCeleritas.py")))
            if _h:
                sys.path.insert(0, str(_d))
            break
        _p = _p.parent
except Exception:
    pass


def _via_root() -> Path:
    p = Path(__file__).resolve()
    while p.parent != p:
        if (p / "supportive modules").is_dir() and (p / "functional modules").is_dir():
            return p
        p = p.parent
    return Path(__file__).resolve().parents[2]


VIA = _via_root()

# L77 排除清單:退役 / 封存 / 收容正本 / 快照副本 / 位元組快取
EXCLUDE = ("__pycache__", "_superseded", "RetiredEngines", "references/intake",
           "SCOPE_COPY", "/VAP/ASSETS/", "/BACKUP/", "20260804")


def _excluded(p: Path) -> bool:
    s = p.as_posix()
    return any(x in s for x in EXCLUDE)


def _family(stem: str) -> str:
    """去掉 _vNNNN 得家族名;沒有版號的回原樣(表示它不走尾版律)。"""
    return re.sub(r"_v\d{3,4}$", "", stem)


def _newest(d: Path, pat: str):
    hits = sorted(x for x in d.glob(pat) if not _excluded(x))
    return hits[-1] if hits else None


# ───────────────────────── 盤點:四個註冊面 ─────────────────────────

def tail_modules() -> dict:
    """支援性模組的**活尾版**:family → Path。只看 supportive modules 樹(本 session 的範圍)。"""
    out: dict = {}
    root = VIA / "supportive modules"
    if not root.is_dir():
        return out
    for q in root.rglob("*.py"):
        if _excluded(q):
            continue
        fam = _family(q.stem)
        if fam == q.stem:          # 沒有版號 = 不走尾版律,不進分母(它另有自己的規矩)
            continue
        cur = out.get(fam)
        if cur is None or q.stem > cur.stem:
            out[fam] = q
    return out


def _inventory() -> dict:
    """中央元件冊:category → {identity: state}。冊缺席=空,誠實。"""
    out: dict = {}
    hits = sorted(_glob.glob(str(VIA / "supportive modules" / "registry" /
                                 "VIA_Component_Inventory_SSOT_v*.json")))
    if not hits:
        return out
    try:
        d = json.loads(Path(hits[-1]).read_text(encoding="utf-8"))
    except Exception:
        return out
    for r in (d.get("records") or []):
        out.setdefault(r.get("category"), {})[str(r.get("identity"))] = r.get("state")
    return out


def _has_selftest(p: Path) -> bool:
    """有沒有自測門:AST 找 selftest 定義,或引數裡認得 --selftest。看結構不看字面(LL340 同族)。"""
    try:
        src = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return "--selftest" in src
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and "selftest" in n.name.lower():
            return True
    return "--selftest" in src


def _grid_families() -> set:
    """尾版格子上有站的家族(從 newest("…_v*.py") 的樣式取,不是從敘述猜)。"""
    g = _newest(VIA / "supportive modules" / "registry", "CGC_MDL064_SelftestGrid_v*.py")
    if g is None:
        return set()
    try:
        src = g.read_text(encoding="utf-8")
    except Exception:
        return set()
    fams = set()
    for m in re.finditer(r'newest\(\s*"([^"]+)"', src):
        fams.add(_family(Path(m.group(1)).stem.replace("_v*", "_v0000")))
    return {f.replace("_v0000", "") for f in fams}


def _shuttles() -> set:
    d = VIA / "bin"
    return {q.stem for q in d.glob("*.cmd")} if d.is_dir() else set()


def inventory() -> dict:
    """盤點:支援性模組 × 工具短令,逐支照四個註冊面報。缺哪一面就指名哪一面。"""
    inv, grid, shut = _inventory(), _grid_families(), _shuttles()
    mods, tools = tail_modules(), {}
    for ident, state in (inv.get("tool") or {}).items():
        if state == "ACTIVE":
            tools[ident] = state

    mrows = []
    for fam, p in sorted(mods.items()):
        mrows.append({
            "family": fam,
            "path": p.relative_to(VIA).as_posix(),
            "冊": (inv.get("module") or {}).get(fam) == "ACTIVE"
                  or (inv.get("engine") or {}).get(fam) == "ACTIVE",
            "自測門": _has_selftest(p),
            "格子站": fam in grid,
        })
    # 批340 梭律講的是**短令**(via-*):每個短令配同名 .cmd,任何殼在本夾直打即通。
    #   `launcher:Invoke-VIA-*` 這類是 PS 啟動器,**本來就不配梭**——把它們算進分母,
    #   「齊 25/173」這個數字就是假的。分母錯了,比例再漂亮也沒有意義。
    trows, others = [], []
    for t in sorted(tools):
        (trows if t.startswith("via-") else others).append(t)
    trows = [{"tool": t, "冊": True, "梭": t in shut} for t in trows]

    def _miss(rows, keys):
        return {k: [r.get("family") or r.get("tool") for r in rows if not r.get(k)] for k in keys}

    return {
        "modules": {"n": len(mrows), "rows": mrows, "missing": _miss(mrows, ("冊", "自測門", "格子站"))},
        "tools": {"n": len(trows), "rows": trows, "missing": _miss(trows, ("梭",))},
        "other_kinds": {"n": len(others), "些": others[:8],
                        "why": "PS 啟動器等非短令:不配梭是規格,不是缺件——另欄報,不進短令分母(LL327)"},
        "srcs": {"冊": bool(inv), "格子": bool(grid), "梭夾": bool(shut)},
    }


# ───────────────────── 梭配對:短令 ↔ bin/*.cmd ─────────────────────
#   CGC_MDL136 的 `deadends` 量的是**「文件裡指路的短令在不在冊上」**;
#   這裡量的是**另一個方向**:Register 尾版的函式 ↔ bin 的 .cmd,兩側互相對得起來嗎。
#   互補不重複(LL341:先量樹上有沒有人在做,再決定補哪一塊)。
_SHUTTLE_MARKS = ("Register-VIA-Commands-v", "%~n0")


def _register_funcs() -> set:
    """Register 尾版裡**真的定義**的短令(function global:via-*)。
    註解裡提到不算數——批686b 實錄:我曾經拿一行註解當成「它有定義」。"""
    hits = sorted(x for x in VIA.glob("Register-VIA-Commands-v*.ps1") if not _excluded(x))
    if not hits:
        return set()
    try:
        src = hits[-1].read_text(encoding="utf-8", errors="replace")
    except Exception:
        return set()
    return {m.group(1) for m in
            re.finditer(r"^\s*function\s+(?:global:)?(via-[A-Za-z0-9_-]+)\s*\{", src, re.M)}


def shuttles() -> dict:
    """三分類,分三欄各自報(LL327):

      缺真梭 Register 有函式、bin 沒有同名**梭** → cmd 殼走不到
             (注意:盤點那一欄的「有 .cmd」是**更寬的問法**——它只問「有沒有同名的 .cmd」。
              同名的 .cmd 有 25 支,其中只有 12 支是真梭,另外 13 支是撞名的獨立實作。
              兩欄都叫「缺梭」就會讓 141 和 154 同時出現在同一頁上——⑮ 把這條恆等式釘死)
      死梭   bin 有**梭**、Register 沒有那個函式 → 看起來是門,打下去走不到任何地方(更危險)
      撞名   bin 有**獨立實作**而 Register 也有同名函式 → 同一個名字兩扇門(L101;CGC_MDL165 棘輪那一族)
      獨立無函式  bin 有 .cmd 而 Register 連同名函式都沒有 → 繞過短令那一層的獨立入口(只點名,不裁)

    梭 = 點源 Register 尾版 + 叫 `%~n0` 同名函式(批340 律)。
    直接跑引擎的 .cmd **不是梭是獨立實作**——批686b 我自己犯過這一條,格子當場擋住。
    """
    fns = _register_funcs()
    d = VIA / "bin"
    sh, ind = set(), set()
    if d.is_dir():
        for q in d.glob("*.cmd"):
            try:
                t = q.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            (sh if all(m in t for m in _SHUTTLE_MARKS) else ind).add(q.stem)
    if not fns and not sh and not ind:
        return {"state": "NODATA", "why": "Register 尾版與 bin 都讀不到——不猜"}
    miss, dead, clash = sorted(fns - sh), sorted(sh - fns), sorted(ind & fns)
    # 第四欄:只有 .cmd、Register 連同名函式都沒有 —— 它不是死梭(它不是梭),
    #   是**完全繞過短令那一層**的獨立入口。是不是缺陷要操作員裁(LL90),這裡只點名。
    solo = sorted(ind - fns)
    return {"state": "RED" if dead else "GREEN",
            "n_func": len(fns), "n_cmd": len(sh) + len(ind), "n_shuttle": len(sh), "n_standalone": len(ind),
            "缺真梭": miss, "死梭": dead, "撞名": clash, "獨立無函式": solo,
            "tally": {"缺真梭": len(miss), "死梭": len(dead), "撞名": len(clash),
                      "獨立無函式": len(solo)}}


# ───────────────────────── 棘輪:逐站歷來最佳 ─────────────────────────

_NOISE = re.compile(r"[（(].*?[)）]|[〇一二三四五六七八九十廿卅百千两兩0-9]+\s*檢|\s+")


def _norm_station(name: str) -> str:
    """站名正規化:去括號內容(批號/實錄)、去「NN 檢」、去空白。
    站名會隨敘述改版而變,直接拿全名當鍵會把**改名誤判成退步**。"""
    return _NOISE.sub("", str(name or ""))


def _grid_runs() -> list:
    out = []
    for f in sorted(_glob.glob(str(VIA / "VIA_Reports" / "**" / "GRID_*.json"), recursive=True)):
        try:
            d = json.loads(Path(f).read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(d.get("results"), list):
            out.append((Path(f).name, d))
    return out


_RANK = {"OK": 3, "SKIP": 2, "TIMEOUT": 1, "FAIL": 0}


def ratchet(runs: list | None = None) -> dict:
    """逐站歷來最佳 vs 最新一跑。四欄各自報,永不相加(LL327)。

    runs 可注入(自測用合成存證;正控/負控要能咬得住 LL89)。
    """
    runs = _grid_runs() if runs is None else runs
    if not runs:
        return {"state": "NODATA", "why": "VIA_Reports 下沒有 GRID_*.json 存證——不猜"}
    best: dict = {}
    best_where: dict = {}
    for fname, d in runs[:-1]:                     # 歷史(不含最新那一跑)
        for r in (d.get("results") or []):
            k = _norm_station(r.get("name"))
            s = str(r.get("state") or "")
            if _RANK.get(s, -1) > _RANK.get(best.get(k, ""), -1):
                best[k], best_where[k] = s, fname
    last_name, last = runs[-1]
    cur = {_norm_station(r.get("name")): str(r.get("state") or "") for r in (last.get("results") or [])}
    cur_raw = {_norm_station(r.get("name")): r.get("name") for r in (last.get("results") or [])}

    regress, never, improve, unmatched = [], [], [], []
    for k, s in cur.items():
        b = best.get(k)
        if b is None:
            unmatched.append(cur_raw[k])
            continue
        if b == "OK" and s in ("FAIL", "TIMEOUT"):
            regress.append({"station": cur_raw[k], "best": b, "now": s, "best_in": best_where.get(k)})
        elif b != "OK" and s == "OK":
            improve.append({"station": cur_raw[k], "best": b, "now": s})
        elif b != "OK" and s != "OK":
            never.append({"station": cur_raw[k], "best": b, "now": s})
    return {
        "state": "RED" if regress else "GREEN",
        "runs": len(runs), "latest": last_name, "stations": len(cur),
        "regress": regress, "never_green": never, "improve": improve, "unmatched": unmatched,
        "tally": {"退步": len(regress), "未曾綠": len(never),
                  "進步": len(improve), "配不到": len(unmatched)},
    }


# ───────────────────────── 修法:只提安全的 ─────────────────────────

def plan() -> dict:
    """修法建議。**可代跑的只有冪等的補登**;要寫碼的只提不做;三件事永遠是操作員的手。"""
    inv = inventory()
    steps, propose = [], []
    if inv["modules"]["missing"]["冊"]:
        # **實測過才敢寫**(批691B):跑完 `registry-sync --apply` 之後再跑一次 plan,
        #   回的是「新 0」,而冊外仍有 92 支尾版模組。也就是說這道門**按它自己的尺已經滿了**,
        #   那 92 支是 VCGC `live_components()` 的掃描規則根本沒走到的一群。
        #   原本這裡寫「冊上未登 → 跑這道就好」——那是**假的修法**,
        #   跟指一條死路一樣傷(L89:我要他打的東西,必須是他打得動的)。
        steps.append({"why": "冊上未登:VCGC 掃得到的那一種,這道門冪等補得上",
                      "cmd": "via-vcgc registry-sync --apply",
                      "n": len(inv["modules"]["missing"]["冊"]),
                      "caveat": "**這道門補不完**——批691B 實測:--apply 跑完後 plan 回「新 0」,"
                                "冊外仍留 92 支。那群是 VCGC live_components() 掃描規則沒走到的,"
                                "不是還沒跑。要動那條規則是 CGC_MDL149 的事,另批。"})
        propose.append({"面": "冊外", "n": len(inv["modules"]["missing"]["冊"]),
                        "why": "registry-sync 說「新 0」卻仍在冊外 → 不是漏跑,是**掃描規則沒走到**;"
                               "這裡只點名,不代改別人的掃描規則",
                        "些": inv["modules"]["missing"]["冊"][:8]})
    for key, note in (("自測門", "沒有自測門的支不准上站(LL317)——補門要寫碼"),
                      ("格子站", "有門卻沒站=改壞了沒人知道——上站要改格子")):
        miss = inv["modules"]["missing"][key]
        if miss:
            propose.append({"面": key, "n": len(miss), "why": note, "些": miss[:8]})
    _sh = shuttles()
    _nosh = _sh.get("缺真梭") if _sh.get("state") != "NODATA" else inv["tools"]["missing"]["梭"]
    if _nosh:
        propose.append({"面": "真梭", "n": len(_nosh),
                        "why": "短令在 Register 裡有、cmd 殼走不到(批340 梭律);"
                               "**梭要點源 Register 尾版叫同名函式,不是自己跑引擎**(批686b 實錄)",
                        "些": inv["tools"]["missing"]["梭"][:8]})
    return {"apply": steps, "propose": propose,
            "never": ["裝套件", "開同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT / API 金鑰)",
                      "改任何 .ps1(L70)"]}


# ═════ [VIA:VERSION-RACE:v0100] 第三把尺:跨分支撞號 —— 只讀本地 refs,零網路 ═════
#
# LL334 的病:兩條活線同時把**下一個版號**拿去用。誰先併誰得號,
# 後到的那一份在**尾版律**下會整個消失 —— 而且沒有任何一盞燈會紅。
# 批686 撞過 `CGC_MDL149_v0120`;批691B 取號時當場量到 `CGC_MDL064_v0441`
# **同時長在三條活線上**,而 main 一份都還沒有。
#
# 這把尺**只報不裁**:版號還給誰是合併當下的事,裁定權在操作員(LL90)。

_RACE_FAM = re.compile(r"(?:^|/)([A-Za-z][A-Za-z0-9_]*)_v(\d{3,4})\.py$")


def _git(*a) -> str:
    """本地 git,零網路(只讀已經 fetch 過的 refs)。失敗=空字串,由呼叫端回 NODATA。"""
    import subprocess
    try:
        r = subprocess.run(["git", "-C", str(VIA), *a],
                           capture_output=True, text=True, timeout=30)
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""


def _live_refs() -> list:
    out = _git("for-each-ref", "--format=%(refname:short)", "refs/remotes")
    return [r for r in out.split() if r and not r.endswith("/HEAD")]


def _ver_blobs(ref: str) -> dict:
    """`家族_vNNNN` → blob sha。**要 blob 不要只要名字**:
    同名同 blob 是「一份檔長在很多條線上」(多半是 main 刪掉的舊檔還留在老分支),
    那不是撞號;**同名不同 blob 才是兩個人各寫了一份**(批691B 實測:
    `VAP_ENG004_TAFactory_v0100` 在 12 條線上都是 5237e5a8 同一顆 → 旁觀;
    `CGC_MDL064_SelftestGrid_v0441` 在三條活線上是三顆不同的 blob → 真撞)。"""
    out = {}
    for line in _git("ls-tree", "-r", ref).splitlines():
        try:
            meta, path = line.split("\t", 1)
            sha = meta.split()[2]
        except Exception:
            continue
        m = _RACE_FAM.search(path)
        if m and not _excluded(Path(path)):
            out[f"{m.group(1)}_v{m.group(2)}"] = sha
    return out


def version_race(refs: dict | None = None, base: str = "origin/main") -> dict:
    """同一個 `家族_vNNNN` 長在**兩條以上**活線、而 `base` 還沒有 → 撞號。

    `refs` 可注入 `{ref: {版號名: blob}}` ——正控/負控不靠今天的樹(LL89/LL336)。
    (給集合 `{版號名, …}` 也吃得下,但那時分不出血,**一律算同名同血、絕不報成撞**:
     判不出來就不准點紅燈。)
    **base 已經有的不算撞**(那是併完的常態);**只長在一條線上的不算撞**(那是正常開新版)。
    """
    if refs is None:
        refs = {r: _ver_blobs(r) for r in _live_refs()}
    if not refs:
        return {"state": "NODATA", "why": "查不到本地 remote refs(淺複製或非 git 樹)——"
                                          "**查不到不等於沒有撞**",
                "n_refs": 0, "base": base, "me": "", "races": [], "mine": [],
                # 形狀不准隨態改變:NODATA 也給齊同一組鍵,
                # 不然取用端在缺料那一天才會 KeyError —— 缺料本來就是最常見的那一天
                "tally": {"撞號": 0, "本線涉入": 0, "同名同血(非撞)": 0}}
    inbase = set(refs.get(base) or ())
    me = (_git("rev-parse", "--abbrev-ref", "HEAD").strip() or "")
    seen: dict = {}
    for ref, names in refs.items():
        if ref == base:
            continue
        for n, sha in (names.items() if isinstance(names, dict) else ((x, x) for x in names)):
            if n not in inbase:
                seen.setdefault(n, {}).setdefault(sha, []).append(ref)
    races,同名同血 = [], 0
    for n, by_sha in seen.items():
        lines = sorted(x for v in by_sha.values() for x in v)
        if len(lines) < 2:
            continue
        if len(by_sha) < 2:           # 同名**同 blob** → 一份檔長在很多線上,不是撞
            同名同血 += 1
            continue
        races.append({"版號": n, "活線": lines, "n": len(lines), "血": len(by_sha)})
    races.sort(key=lambda r: (-r["血"], -r["n"], r["版號"]))
    mine = [r for r in races
            if me and any(x == me or x.endswith("/" + me) for x in r["活線"])]
    return {"state": "RED" if races else "GREEN", "n_refs": len(refs), "base": base,
            "me": me or "(不在分支上)", "races": races, "mine": mine,
            "tally": {"撞號": len(races), "本線涉入": len(mine), "同名同血(非撞)": 同名同血}}


# ═════ [VIA:GATE-CONSISTENCY:v0100] 第四把尺:同意閘一致性 —— 只讀不裁,零網路 ═════
#
# 批695。這把尺是被兩件實錄逼出來的,兩件都在批691B–692 當場量到:
#
#   ① **期望值分裂**:`via-gates` 印給操作員看的期望值是 token,
#      而全樹 Python 呼叫點只認 "YES"。照畫面上的指示設,引擎照樣 fail-closed。
#   ② **fail-open 分支**:同一支啟動器,治理函式在 scope 時把閘設 OFF(fail-closed),
#      不在 scope 時把閘設 YES(**fail-open**)。同一支腳本、同一組旗標,閘態相反。
#
# 兩件的**修**都在 `.ps1` 裡,而 L70 說未經操作員逐次許可不得改任何 `.ps1`。
# 所以這把尺**只報不修、也不裁**(LL90):它負責讓這兩件從任務清單變成量得到的數。

_SELF_FAMILY = Path(__file__).stem.rsplit("_v", 1)[0]   # LL133:排掉自己
CONSENT_VARS = ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")
#: 設定端:`$env:VAR = "值"`(ps1)/ `VAR=值`(sh export)
_G_SET_PS = re.compile(r"\$env:(VIA_(?:NET|SCRAPE)_CONSENT)\s*=\s*[\"']([^\"']*)[\"']")
_G_SET_SH = re.compile(r"(VIA_(?:NET|SCRAPE)_CONSENT)=([A-Za-z_][A-Za-z0-9_]*)")
#: 檢查端。**兩個方向的錯都踩過,所以兩邊都釘住**(批695 自審實錄):
#:   假陽 —— `out["consent"]["VIA_NET_CONSENT"] != "OPEN"` 比的是**回報用的標籤**,
#:          不是環境變數。所以檢查端一定要錨在真的讀環境的那個動作上
#:          (`environ.get` / `getenv` / `$env:`),不能只看變數名出現。
#:   假陰 —— `$g2 = $env:VIA_SCRAPE_CONSENT` 之後 `$g2 -eq $tok`:**變數轉手**,
#:          跟比較式隔了兩行。不追這一手就會漏掉 `via-gates` 真正的期望值。
#:   兩個錯當時剛好互相抵銷成同一個總數 —— **靠抵銷得到的對,是最糟的一種綠。**
_G_CHK_PY = re.compile(
    r"(?:environ\.get\(|environ\[|getenv\()\s*[\"'](VIA_(?:NET|SCRAPE)_CONSENT)[\"']\s*"
    r"(?:,[^)]*)?\)?\]?\s*[!=]=\s*[\"']([^\"']+)[\"']")
_G_CHK_PS = re.compile(r"\$env:(VIA_(?:NET|SCRAPE)_CONSENT)\s*-(?:eq|ne)\s*[\"']([^\"']+)[\"']")
_G_TOKVAR = re.compile(r"\$(\w+)\s*=\s*[\"']([^\"']+)[\"']")
#: 變數轉手:`$g2 = $env:VIA_SCRAPE_CONSENT` → 之後 `$g2 -eq <字面值|$tok>` 都算它的期望值
_G_ALIAS = re.compile(r"\$(\w+)\s*=\s*\$env:(VIA_(?:NET|SCRAPE)_CONSENT)")
#: 放行值 = 讓閘打開的值(相對於 OFF/空這種關閉值)
_G_OPEN = ("YES", "I_ACCEPT_RESPONSIBLE_SCRAPING", "1", "TRUE")


def _tail_scripts(exts=(".ps1", ".sh")) -> list:
    """全樹尾版腳本(尾版律:同家族只取最新;L77 排除清單照帶)。"""
    fam: dict = {}
    for e in exts:
        for q in VIA.rglob("*" + e):
            if _excluded(q) or not q.is_file():
                continue
            # `.ps1` 的版號是 `-vNNNN`(Register-VIA-Commands-v0242),不是 `_vNNNN`;
            # 用 `_family()` 會讓每一版各自成家,尾版律就失效了。
            fam.setdefault(str(q.parent) + "/" + re.sub(r"[-_]v\d{3,4}$", "", q.stem),
                           []).append(q)
    return [sorted(v, key=lambda x: x.name)[-1] for v in fam.values()]


def _py_tails() -> list:
    fam: dict = {}
    for q in VIA.rglob("*.py"):
        if _excluded(q) or not q.is_file():
            continue
        fam.setdefault(str(q.parent) + "/" + _family(q.stem), []).append(q)
    return [sorted(v, key=lambda x: x.name)[-1] for v in fam.values()]


def gates(files: dict | None = None) -> dict:
    """同意閘一致性。`files` 可注入 {相對路徑: 內容} —— 正控/負控不靠今天的樹(LL89)。

    三欄各自報,永不相加(LL327):
      期望值    檢查端認哪些值;**多於一種 = 分裂**(照 A 設,走 B 的那一半仍 fail-closed)
      fail-open 設定端把閘設成放行值的位置
      雙態      同一支檔裡兩條分支**方向相反**(治理層在場關、不在場開)——最危險的一種
    """
    if files is None:
        files = {}
        for q in _tail_scripts() + _py_tails():
            # LL133 自我指涉:判定器**一定要排掉自己的家族**。
            #   本檔的註解裡寫著 `$env:VAR -eq "值"` 當說明,不排就會把自己的
            #   文件算成一筆發現(批695 自審實錄:期望值多出一種叫「值」的)。
            if _family(q.stem) == _SELF_FAMILY:
                continue
            try:
                files[q.relative_to(VIA).as_posix()] = q.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
    if not files:
        return {"state": "NODATA", "why": "讀不到任何尾版腳本/模組——不猜",
                "expect": {}, "fail_open": [], "both": [],
                "tally": {"期望值種數": 0, "fail_open": 0, "雙態": 0}}

    expect: dict = {}
    fail_open, both = [], []
    for path, txt in files.items():
        for m in _G_CHK_PY.finditer(txt):
            expect.setdefault(m.group(2), set()).add(path)
        for m in _G_CHK_PS.finditer(txt):
            expect.setdefault(m.group(2), set()).add(path)
        # 追一手變數轉手(ps1):$g2 = $env:VAR → $g2 -eq "值" / $g2 -eq $tok
        svars = {m.group(1) for m in _G_ALIAS.finditer(txt)}   # 別名本身,不是變數名
        lits = {k: v for k, v in (m.groups() for m in _G_TOKVAR.finditer(txt))}
        for alias in svars:
            for m in re.finditer(r"\$" + re.escape(alias) + r"\s*-(?:eq|ne)\s*(?:[\"']([^\"']+)[\"']|\$(\w+))", txt):
                val = m.group(1) or lits.get(m.group(2) or "")
                if val:
                    expect.setdefault(val, set()).add(path)
        sets = [(m.group(1), m.group(2)) for m in _G_SET_PS.finditer(txt)]
        if path.endswith(".sh"):
            sets += [(m.group(1), m.group(2)) for m in _G_SET_SH.finditer(txt)
                     if "export" in txt[max(0, m.start() - 40):m.start()]]
        opens = sorted({v for _, v in sets if v.upper() in _G_OPEN})
        closes = sorted({v for _, v in sets if v.upper() not in _G_OPEN})
        if opens:
            fail_open.append({"檔": path, "設成": opens})
        if opens and closes:                      # 同一支檔兩條分支方向相反
            both.append({"檔": path, "開": opens, "關": closes})
    return {"state": "RED" if (len(expect) > 1 or both) else "GREEN", "why": "",
            "expect": {k: sorted(v) for k, v in expect.items()},
            "fail_open": fail_open, "both": both,
            "tally": {"期望值種數": len(expect), "fail_open": len(fail_open), "雙態": len(both)}}


# ───────────────────────── 報 ─────────────────────────

def report() -> int:
    inv, rat = inventory(), ratchet()
    print("=== 工具與支援性模組盤點 + 逐站歷來最佳棘輪(CGC_MDL178 v0100)===")
    m, t = inv["modules"], inv["tools"]
    print(f"  [盤點] 支援性模組尾版 {m['n']} 支 · 工具短令 {t['n']} 支"
          f"  (出處 冊={inv['srcs']['冊']} 格子={inv['srcs']['格子']} 梭夾={inv['srcs']['梭夾']})")
    for k in ("冊", "自測門", "格子站"):
        miss = m["missing"][k]
        print(f"     模組·{k:4s} 齊 {m['n'] - len(miss):4d} / {m['n']:4d} · 缺 {len(miss):3d}"
              + (f" → {'、'.join(miss[:4])}{' …' if len(miss) > 4 else ''}" if miss else ""))
    miss = t["missing"]["梭"]
    o = inv["other_kinds"]
    sh0 = shuttles()
    _of = ("" if sh0.get("state") == "NODATA"
           else f"(其中真梭 {sh0['n_shuttle']} · 撞名的獨立實作 {len(sh0['撞名'])})")
    print(f"     短令·有 .cmd 齊 {t['n'] - len(miss):4d} / {t['n']:4d} · 無 {len(miss):3d} {_of}"
          + (f" → {'、'.join(miss[:4])}{' …' if len(miss) > 4 else ''}" if miss else ""))
    print(f"     非短令    {o['n']:4d} 支(PS 啟動器等)· {o['why']}")
    sh = sh0
    if sh.get("state") == "NODATA":
        print(f"  [梭配對] NODATA · {sh['why']}")
    else:
        print(f"  [梭配對] Register 函式 {sh['n_func']} · bin .cmd {sh['n_cmd']}"
              f"(梭 {sh['n_shuttle']} · 獨立實作 {sh['n_standalone']})· {sh['tally']}")
        if sh["死梭"]:
            print(f"     **死梭**(看起來是門,打下去走不到)→ {'、'.join(sh['死梭'][:6])}")
        if sh["撞名"]:
            print(f"     撞名(同一個名字兩扇門 L101)→ {'、'.join(sh['撞名'][:6])}")
        if sh.get("獨立無函式"):
            print(f"     獨立無函式 {len(sh['獨立無函式'])} 支(有 .cmd 而 Register 沒有同名函式,"
                  f"繞過短令那一層;是不是缺陷待裁 LL90)→ {'、'.join(sh['獨立無函式'][:6])}")
    if rat["state"] == "NODATA":
        print(f"  [棘輪] NODATA · {rat['why']}")
    else:
        print(f"  [棘輪] 存證 {rat['runs']} 份 · 最新 {rat['latest']} · 站 {rat['stations']}"
              f" · {rat['tally']}")
        for r in rat["regress"]:
            print(f"     **退步** {r['station'][:60]} · 歷來最佳 {r['best']}({r['best_in']}) → 現在 {r['now']}")
        for r in rat["never_green"][:5]:
            print(f"     未曾綠 {r['station'][:60]} · 最佳 {r['best']} → 現在 {r['now']}")
    vr = version_race()
    if vr["state"] == "NODATA":
        print(f"  [撞號] NODATA · {vr['why']}")
    else:
        print(f"  [撞號] 活線 {vr['n_refs']} 條(基線 {vr['base']})· 本線 {vr['me']} · {vr['tally']}")
        for r in vr["races"][:6]:
            mark = "**本線涉入**" if r in vr["mine"] else "旁觀"
            print(f"     {mark} {r['版號']} · {r['n']} 條活線 / **{r['血']} 顆不同 blob** → "
                  + "、".join(x.replace("origin/", "") for x in r["活線"]))
    gt = gates()
    if gt["state"] == "NODATA":
        print(f"  [同意閘] NODATA · {gt['why']}")
    else:
        print(f"  [同意閘] {gt['tally']}")
        for k, v in sorted(gt["expect"].items(), key=lambda x: -len(x[1])):
            print(f"     期望值 {k!r} ← {len(v)} 處 · 例 {v[0]}")
        for r in gt["both"]:
            print(f"     **雙態** {r['檔']} · 開 {r['開']} / 關 {r['關']}"
                  "(治理層不在場時自己打開——最危險的一種)")
        if gt["fail_open"]:
            print(f"     fail-open {len(gt['fail_open'])} 支 → "
                  + "、".join(r["檔"].split("/")[-1] for r in gt["fail_open"][:4]) + " …")
        print("     [只報不修] 修都在 .ps1(L70 逐次許可);要不要升成紅燈是操作員的裁定(LL90)")
    p = plan()
    for s in p["apply"]:
        print(f"  [可代跑] {s['cmd']}  ({s['why']} · {s['n']} 支)")
        if s.get("caveat"):
            print(f"     ⚠ {s['caveat']}")
    for s in p["propose"]:
        print(f"  [只提不做] 缺{s['面']} {s['n']} 支 — {s['why']}")
    print("  [永不] " + " · ".join(p["never"]))
    print("  [律] 三把尺分三欄各自報,永不相加(LL327)。"
          "「未曾綠」不是退步;「配不到」多半是站名改過;"
          "「撞號」只報不裁——版號還給誰是合併當下的事(LL90/LL334)。")
    return 1 if rat.get("regress") else 0


# ───────────────────────── 自測 ─────────────────────────

def selftest() -> int:
    fails: list = []

    def chk(name, ok, detail=""):
        print(f"  [{'OK' if ok else 'FAIL'}] {name} {detail}")
        if not ok:
            fails.append(name)

    inv = inventory()
    chk("① 盤點有料而且出處講得出來(冊/格子/梭夾三個來源,缺席要說缺席不假裝有)",
        inv["modules"]["n"] > 0 and isinstance(inv["srcs"], dict) and len(inv["srcs"]) == 3,
        f"(模組 {inv['modules']['n']} · 工具 {inv['tools']['n']} · 出處 {inv['srcs']})")

    rows = inv["modules"]["rows"]
    chk("② 每一列四個面都要有答案(True/False),不准留空——空的會被讀成「沒問題」",
        all(isinstance(r.get(k), bool) for r in rows for k in ("冊", "自測門", "格子站")),
        f"({len(rows)} 列 × 3 面)")

    miss_sum = sum(len(v) for v in inv["modules"]["missing"].values())
    chk("③ 缺件要**指名**,不只報數字(數字自己不會告訴你去修哪一支)",
        all(isinstance(v, list) for v in inv["modules"]["missing"].values())
        and (miss_sum == 0 or any(inv["modules"]["missing"].values())),
        f"(缺件合計 {miss_sum} 支,逐支具名)")

    # ④⑤⑥ 棘輪:用**合成存證**當正控/負控——會過的檢等於沒有檢(LL89)
    syn_hist = ("GRID_SYN_A.json", {"results": [
        {"name": "甲站(十檢)", "state": "OK"}, {"name": "乙站(八檢)", "state": "FAIL"},
        {"name": "丙站(六檢)", "state": "FAIL"}]})
    syn_now = ("GRID_SYN_B.json", {"results": [
        {"name": "甲站(十二檢)", "state": "FAIL"},   # 曾經 OK、改過名、現在紅 → **退步**
        {"name": "乙站(八檢)", "state": "FAIL"},      # 從來沒綠過 → 未曾綠,**不是退步**
        {"name": "丙站(六檢)", "state": "OK"},        # 轉綠 → 進步
        {"name": "丁站(新)", "state": "OK"}]})        # 歷史沒有 → 配不到,**不是退步**
    r = ratchet([syn_hist, syn_now])
    chk("④ 棘輪正控:曾經 OK、現在紅 = **退步**(即使站名改過也要配得到——"
        "站名會隨敘述改版而變,拿全名當鍵會把改名誤判成退步)",
        r["tally"]["退步"] == 1 and r["regress"][0]["station"].startswith("甲站"),
        f"({r['tally']})")
    chk("⑤ 棘輪負控:**從來沒綠過的不是退步**(它沒有退,它本來就沒站起來);"
        "**歷史配不到的也不是退步**(多半是新站或改名)",
        r["tally"]["未曾綠"] == 1 and r["tally"]["配不到"] == 1 and r["tally"]["進步"] == 1,
        f"({r['tally']})")
    chk("⑥ 沒有存證要回 NODATA,不回 GREEN(缺料≠沒問題)",
        ratchet([])["state"] == "NODATA", f"({ratchet([])['state']})")

    chk("③b 分母要對:梭只量**短令(via-*)**——PS 啟動器不配梭是規格不是缺件,"
        "混進分母會讓比例變成假的(批691B 修尺實錄)",
        all(str(r["tool"]).startswith("via-") for r in inv["tools"]["rows"])
        and inv["other_kinds"]["n"] >= 0,
        f"(短令 {inv['tools']['n']} · 非短令另欄 {inv['other_kinds']['n']})")

    sh = shuttles()
    chk("⑨ 梭配對三分類各自報:缺真梭 / 死梭 / 撞名 是三件不同的事,不准相加(LL327)。"
        "**梭 = 點源 Register 叫同名函式**;直接跑引擎的 .cmd 是獨立實作不是梭(批686b 實錄)",
        sh.get("state") != "NODATA" and set(sh["tally"]) == {"缺真梭", "死梭", "撞名", "獨立無函式"}
        and sh["n_shuttle"] + sh["n_standalone"] == sh["n_cmd"],
        f"(函式 {sh.get('n_func')} · 梭 {sh.get('n_shuttle')} · 獨立 {sh.get('n_standalone')} · {sh.get('tally')})")
    chk("⑩ 註解裡提到**不算**有定義:只認 `function global:via-*`"
        "(批686b 實錄:我曾拿一行註解當成「它有定義」,差點把一支死梭當成合法的門)",
        all(f.startswith("via-") for f in _register_funcs()) and len(_register_funcs()) > 0,
        f"(Register 尾版真定義 {len(_register_funcs())} 條)")

    _have = inv["tools"]["n"] - len(inv["tools"]["missing"]["梭"])
    _sh15 = shuttles()
    chk("⑮ 兩欄不准共用一個詞:盤點問的是「有沒有同名 .cmd」(寬)、梭配對問的是「是不是真梭」(嚴),"
        "兩個都叫「缺梭」就會讓 141 和 154 同時出現在同一頁上。**釘死兩條恆等式**:"
        "有同名 .cmd = 真梭 + 撞名;bin 全部 .cmd = 真梭 + 撞名 + 獨立無函式"
        "(分割要蓋滿,不然中間那一群會從兩邊的縫裡掉出去)",
        _sh15.get("state") == "NODATA"
        or (_have == _sh15["n_shuttle"] + len(_sh15["撞名"])
            and _sh15["n_cmd"] == _sh15["n_shuttle"] + len(_sh15["撞名"]) + len(_sh15["獨立無函式"])),
        f"(有 .cmd {_have} = 真梭 {_sh15.get('n_shuttle')} + 撞名 {len(_sh15.get('撞名') or [])}"
        f" · bin .cmd {_sh15.get('n_cmd')} = 真梭 + 撞名 + 獨立無函式 {len(_sh15.get('獨立無函式') or [])})")

    # ⑰⑱⑲ 同意閘:注入合成檔當正控/負控——不靠今天的樹(LL332)
    syn_g = {
        "a.ps1": ('if (Get-Command Set-VIAGateDefaults) { Set-VIAGateDefaults }\n'
                  'else { $env:VIA_NET_CONSENT = "YES" }\n'),          # 只設放行 → fail-open
        "b.ps1": ('$env:VIA_NET_CONSENT = "OFF"\n'
                  '$env:VIA_SCRAPE_CONSENT = "OFF"\n'),                # 只設關閉 → 不是 fail-open
        "c.ps1": ('$g2 = $env:VIA_SCRAPE_CONSENT\n$tok = "TOKEN_X"\n'
                  'if ($g2 -eq $tok) { "OPEN" }\n'
                  'if (-not $env:VIA_NET_CONSENT) { $env:VIA_NET_CONSENT = "OFF" }\n'
                  'else { $env:VIA_NET_CONSENT = "YES" }\n'),           # 兩條分支方向相反 → 雙態
        "d.py": ('import os\n'
                 'ok = os.environ.get("VIA_SCRAPE_CONSENT") == "YES"\n'
                 'lbl = rec["consent"]["VIA_NET_CONSENT"] != "OPEN"\n'),  # 後者是標籤,不算期望值
    }
    g = gates(syn_g)
    chk("⑰ 期望值分裂:檢查端認的值多於一種 = 照 A 設的人,走 B 的那一半仍 fail-closed。"
        "**錨在真的讀環境的動作上**(environ.get/getenv/$env:)——"
        "`rec[\"consent\"][\"VIA_NET_CONSENT\"] != \"OPEN\"` 比的是回報標籤,不算期望值"
        "(批695 自審實錄:這個假陽差點跟一個假陰互相抵銷成對的總數)",
        set(g["expect"]) == {"YES", "TOKEN_X"},
        f"(量到 {sorted(g['expect'])};標籤比對已排除)")
    chk("⑱ fail-open 只數**設成放行值**的那一種:設成 OFF / 空是 fail-closed,不算。"
        "(L70:這兩件的修都在 .ps1,所以這把尺只報不修;LL90 裁定權在操作員)",
        {r["檔"] for r in g["fail_open"]} == {"a.ps1", "c.ps1"},
        f"(fail-open {sorted(r['檔'] for r in g['fail_open'])};b.ps1 只設 OFF 不入列)")
    chk("⑲ 雙態最危險:同一支檔兩條分支**方向相反**——治理函式在 scope 時關、不在時開,"
        "同一支腳本同一組旗標閘態相反(批691B 對照實驗實錄)。"
        "沒有料要回 NODATA 不回綠(查不到不等於沒有)",
        [r["檔"] for r in g["both"]] == ["c.ps1"] and gates({})["state"] == "NODATA",
        f"(雙態 {[r['檔'] for r in g['both']]} · 空輸入 → {gates({})['state']})")

    p16 = plan()
    _apply16 = [x for x in p16["apply"] if "registry-sync" in x["cmd"]]
    chk("⑯ 「可代跑」那一欄不准只寫好消息:**跑完補不完就要當場講**。"
        "批691B 實測 --apply 之後 plan 回「新 0」而冊外仍有 92 支 —— "
        "一句「跑這道就好」等於指一條死路(L89)。釘死:冊那一步必須帶 caveat,"
        "而且冊外那一群要另列一條 propose,不准併進可代跑裡充數",
        (not _apply16) or (bool(_apply16[0].get("caveat"))
                           and any(x["面"] == "冊外" for x in p16["propose"])),
        f"(可代跑 {len(p16['apply'])} 步 · 帶 caveat "
        f"{sum(1 for x in p16['apply'] if x.get('caveat'))} · "
        f"冊外另列 {'有' if any(x['面'] == '冊外' for x in p16['propose']) else '無'})")

    p = plan()
    never = set(p["never"])
    chk("⑦ 自修正的邊界:可代跑的只有**冪等補登**;裝套件 / 開同意閘 / 改 .ps1 永遠在「永不」那一欄",
        len(never) == 3 and all("registry-sync" in s["cmd"] for s in p["apply"]),
        f"(可代跑 {len(p['apply'])} 步 · 只提不做 {len(p['propose'])} 類 · 永不 {len(never)} 件)")

    # ⑧ 不變量:本檔自己也要守自己的尺(LL339 自己剛立的律,最先違反的人通常是自己)
    me = Path(__file__)
    chk("⑧ 本支自己也在尺上:有自測門、家族名可推導、掃描根帶排除清單(L77)",
        _has_selftest(me) and _family(me.stem) == "CGC_MDL178_ToolInventoryRatchet"
        and len(EXCLUDE) >= 5,
        f"(排除 {len(EXCLUDE)} 條)")

    # ⑫⑬⑭ 撞號:注入合成 refs 當正控/負控——**不靠今天的樹**(LL332:
    #        會隨裁定改變的數字不可以當斷言)
    syn = {"origin/main": {"F_v0100": "b0"},
           "origin/a": {"F_v0100": "b0", "F_v0101": "b1", "G_v0100": "b9", "H_v0100": "bh"},
           "origin/b": {"F_v0100": "b0", "F_v0101": "b2", "H_v0100": "bh"},
           "origin/c": {"G_v0101": "b8", "H_v0100": "bh"}}
    vr = version_race(syn)
    chk("⑫ 撞號正控:同一個版號長在**兩條以上**活線、而基線還沒有 = 撞號"
        "(LL334;後到的那一份在尾版律下會整個消失,而且沒有任何一盞燈會紅)",
        vr["tally"]["撞號"] == 1 and vr["races"] and vr["races"][0]["版號"] == "F_v0101"
        and vr["races"][0]["n"] == 2,
        f"({vr['tally']} · {[r['版號'] for r in vr['races']]})")
    chk("⑬ 撞號負控三條:**基線已經有的**不算撞(併完的常態)· **只長在一條線上的**不算撞"
        "(正常開新版)· **同名同 blob 的**不算撞(一份檔長在很多線上,"
        "多半是 main 刪掉的舊檔——批691B 實測 12 條線同一顆 5237e5a8)",
        all(r["版號"] not in ("F_v0100", "G_v0100", "G_v0101", "H_v0100") for r in vr["races"])
        and vr["tally"]["同名同血(非撞)"] == 1 and vr["races"][0]["血"] == 2,
        f"(同名同血另欄 {vr['tally']['同名同血(非撞)']} · 真撞血數 {vr['races'][0]['血']})")
    chk("⑭ 查不到 refs 要回 **NODATA** 不回 GREEN——查不到不等於沒有撞;"
        "綠燈只能由量得到的東西點亮(LL342)",
        version_race({})["state"] == "NODATA" and version_race(syn)["state"] == "RED",
        f"(空 refs → {version_race({})['state']})")

    print(f"  [計] 十九檢 OK {19 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== CGC_MDL178 工具與支援性模組盤點 + 棘輪 · 十九檢自測(零網路零寫入)===")
        return selftest()
    verb = args[0] if args and not args[0].startswith("-") else "report"
    if verb == "inventory":
        print(json.dumps(inventory(), ensure_ascii=False, indent=1)[:4000])
        return 0
    if verb == "ratchet":
        print(json.dumps(ratchet(), ensure_ascii=False, indent=1)[:4000])
        return 0
    if verb == "race":
        print(json.dumps(version_race(), ensure_ascii=False, indent=1)[:4000])
        return 0
    if verb == "plan":
        print(json.dumps(plan(), ensure_ascii=False, indent=1)[:4000])
        return 0
    return report()


if __name__ == "__main__":
    sys.exit(main())
