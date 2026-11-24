#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL171_PanoramaBatchPlanner v0100 — 全景式分析 · 批次修復規劃器(批670)
====================================================================
操作員令(批670):「檢查將所有 PY 檔加入加速器 · VDF 引擎都加入網路引擎 ·
PS 指令加入全景式分析 · 錯誤識別 · 可同時處理的問題 / 依序處理的問題 ·
不可傷害系統指令 · 產生九頭龍風險 · 一次同時解決一批問題」

先量前兩件,**兩件都已經滿了**(所以本批不動它們,只把數字擺上檯面):
    ACCEL  VDF 195/195 · VAP 247/247 · VRN 356/356 · VIA 1834/1834  = 100%
    NET    VDF 尾版家族 45 · 缺 0
  橋掃器報「NET 缺 8」是**尺把版史當成資產**:同一族 5 個版本,尾版有橋、舊版沒有,
  於是同一件事被數成 4 件缺。按尾版律重算是 0(同 LL:數檔案會把版史當資產)。

本支做的是後五件,而且**只規劃不動手**(預設 dry-run;--apply 只在操作員明示時才有)。
它不重做任何判準(Zero-Hydra)——判準在既有掃描器裡,本支只讀它們的存證並**排程**:

  ① 錯誤識別 —— 每一筆分四類,而不是一律叫「問題」:
       REAL_GAP   真缺:該有的東西不在
       RULER      尺的錯:判準把合法狀態判成缺(例:版史當資產、被禁庫當缺料)
       NEED_DATA  缺料:料沒到位,不是壞掉(NODATA)
       GATED      等閘:同意閘/操作員裁定,AI 不能代
     **把後三類混進「問題」裡,人會去修不該修的東西。**

  ② 可同時 / 依序 —— 依「會不會碰到同一個檔」分波:
       同一波內兩筆**目標檔案集合不相交** → 可並行
       目標相交、或宣告了前置依賴 → 排到後面的波
     分波是**保守**的:拿不準就排序列。並行做壞的代價比多跑一輪大。

  ③ 九頭龍風險 —— 標出「會長出第二顆頭」的動作:
       新建一支與既有正主同職責的件 · 把判準/名單複製到第二處 ·
       加第二個同名短令或梭(L101 一個名字只能有一扇門)
     風險件**一律不進並行波**,而且要人看過才動。

  ④ 不可傷害系統 —— 兩層:
       禁動詞閘:Stop-Process / Remove-Item / rm -rf / conda remove / pip uninstall /
                 git push --force / --approve-remove —— 出現即 BLOCK,不是警告
       影響半徑:每筆標 blast(檔數)與 reversible(能不能一鍵還原)
     **預設零動作**:本支不執行任何修復,只印出「誰先誰後、哪些可以一起」。

  ⑤ 一次一批 —— 輸出是**波**不是清單:第 1 波 N 件可並行、第 2 波 M 件……
用法:
  via-panoplan            → 全景分析 + 分波計畫(零動作)
  via-panoplan html       → 落 rich HTML 全景計畫表(零 CDN 零外連)
  via-panoplan --selftest → 廿一檢(沙盒零網路)
誠實 rc:0 無事 · 1 有真缺 · 2 只有缺料 · 4 只有等閘 · 5 只有尺的錯
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
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = VIA / "VIA_Reports" / "panoplan"
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
_SELF_FAMILY = Path(__file__).stem.rsplit("_v", 1)[0]

# ── 錯誤識別:四類。混成一類,人會去修不該修的東西 ──────────────────────
KIND = {
    "REAL_GAP": "真缺:該有的東西不在",
    "RULER": "尺的錯:判準把合法狀態判成缺",
    "NEED_DATA": "缺料:料沒到位,不是壞掉",
    "GATED": "等閘:同意閘或操作員裁定,AI 不能代",
}
KIND_ORDER = ("REAL_GAP", "NEED_DATA", "GATED", "RULER")
KIND_STYLE = {"REAL_GAP": "bold red", "NEED_DATA": "yellow",
              "GATED": "bold cyan", "RULER": "magenta"}

# ── 不可傷害系統:禁動詞。出現即 BLOCK,不是警告 ─────────────────────────
FORBIDDEN = (
    (r"\bStop-Process\b", "停別人的行程(操作員的環境,永不代停)"),
    (r"\bRemove-Item\b", "刪檔(只增不減;刪是操作員的手)"),
    (r"\brm\s+-rf\b", "遞迴刪除"),
    (r"\bconda\s+remove\b", "拆環境"),
    (r"\bpip\s+uninstall\b", "拆套件(裝與拆都是操作員的手)"),
    (r"push\s+--force|--force-with-lease", "force push(零 force push 律)"),
    (r"--approve-remove", "撤件(只在操作員明示時)"),
    (r"\.ps1\b.*(?:寫|改|注入|patch)", "改 .ps1(L70:未經逐次許可不得修改)"),
)


def forbidden_hits(text: str) -> list:
    out = []
    for pat, why in FORBIDDEN:
        if re.search(pat, str(text or ""), re.I):
            out.append(why)
    return out


# ── 九頭龍風險:會長出第二顆頭的動作 ────────────────────────────────────
HYDRA_PAT = (
    (r"新建|新造|另開一支|create a new engine", "新建一支可能已有正主的件"),
    (r"複製一份|copy the (?:table|list|rules)|抄一份", "把判準或名單複製到第二處"),
    (r"再加一個同名|第二個短令|second shim", "第二扇門(L101 一個名字只能有一扇門)"),
    (r"自己寫一份|自備一份", "自備第二份判準"),
)


def hydra_hits(text: str) -> list:
    out = []
    for pat, why in HYDRA_PAT:
        if re.search(pat, str(text or ""), re.I):
            out.append(why)
    return out


def finding(fid, kind, title, detail, targets, fix, needs=(), reversible=True) -> dict:
    """一筆發現。targets 決定分波,needs 決定先後,kind 決定它該不該被修。"""
    tg = sorted(set(targets or ()))
    blob = f"{title} {detail} {fix}"
    return {"id": fid, "kind": kind, "title": title, "detail": detail,
            "targets": tg, "blast": len(tg), "fix": fix,
            "needs": sorted(set(needs or ())), "reversible": bool(reversible),
            "hydra": hydra_hits(blob), "blocked": forbidden_hits(blob)}


def rel(p) -> str:
    try:
        return str(Path(p).relative_to(VIA)).replace("\\", "/")
    except (ValueError, TypeError):
        return str(p)


def newest(folder: Path, pattern: str) -> Path | None:
    try:
        hits = sorted(folder.glob(pattern))
    except OSError:
        return None
    return hits[-1] if hits else None


def load_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


# ── 採集:讀既有掃描器的存證,不重做判準(Zero-Hydra)────────────────────
def _tail_families(folder: Path, pattern: str) -> dict:
    """同名不同版折成一族,只留尾版。數檔案會把版史當資產(L57 誠實分母)。"""
    fam: dict = {}
    if not folder.is_dir():
        return fam
    for p in sorted(folder.glob(pattern)):
        if "__pycache__" in str(p):
            continue
        base = re.sub(r"_v\d{4}\.py$", "", p.name).replace(".py", "")
        cur = fam.get(base)
        if cur is None or p.name > cur.name:
            fam[base] = p
    return fam


NET_MARK = ("SUP_MDL740", "NetUnified", "AegisNexus", "VIA:NET-BRIDGE")
ACC_MARK = ("[VIA:ACCEL-BRIDGE:", "VIA_SuperAccel_Module")


def _sweeper_mod():
    """把橋掃器**整支載進來**,直接用它的 _excluded()。

    第一版我只 AST 取了 EXCLUDE_PARTS / READONLY_CANON 兩張靜態清單,自以為這樣
    就是「一個出處」。結果還是漏了 4 支——它們住在 **雜湊冊凍結夾**
    (VIA_CentralGovernanceFamily_b514/MANIFEST_b514.json 釘死 sha256),
    而「這個夾被雜湊冊凍結了」這件事**不在任何一張靜態清單裡**,它是 _excluded()
    裡的一段邏輯。
    → **抄清單不算一個出處,抄到函式才算。** 判準會長出靜態表看不到的分支。
    """
    eng = newest(HERE, "CGC_MDL124_BridgeSweeper_v*.py")
    if not eng:
        return None
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("panoplan_sweeper", eng)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["panoplan_sweeper"] = mod
        spec.loader.exec_module(mod)
        return mod if hasattr(mod, "_excluded") else None
    except Exception:
        return None


_SWEEP = _sweeper_mod()


def sweeper_exclusions() -> tuple[tuple, tuple]:
    """排除清單向 CGC_MDL124 橋掃器 **AST 取用**,不自己寫第二份。

    第一版我自己列了三條(intake/retired/tests),結果把 5 支判成「缺橋」——
    其中一支是 **VIA_Financial_Institution_SSOT_v0100.py**,而那是 READ_ONLY 正典,
    橋掃器的 READONLY_CANON 裡寫得清清楚楚。**我差點列出一份「該去動唯讀正典」的清單。**
    兩份排除清單一定會走鐘,而走鐘的那一天,錯的方向是「去動不該動的東西」(L30 一個出處)。
    """
    eng = newest(HERE, "CGC_MDL124_BridgeSweeper_v*.py")
    if not eng:
        return (), ()
    try:
        tree = ast.parse(eng.read_text(encoding="utf-8-sig"))
    except Exception:
        return (), ()
    got = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in ("EXCLUDE_PARTS", "READONLY_CANON"):
                    try:
                        got[t.id] = tuple(ast.literal_eval(node.value))
                    except Exception:
                        pass
    return got.get("EXCLUDE_PARTS", ()), got.get("READONLY_CANON", ())


_EXC_PARTS, _RO_CANON = sweeper_exclusions()


def sweep_excluded(p: Path) -> tuple[bool, str]:
    """回 (排不排除, 理由)。理由要留著——**具名的豁免才是豁免**(L87)。"""
    if _SWEEP is not None:
        try:
            why = _SWEEP._excluded(p)      # 正主的判準,連凍結夾那段分支一起
            if why:
                return True, str(why)
        except Exception:
            pass                           # 正主載不動才退回靜態清單,而且下面會講
    sp = str(p).replace("\\", "/")
    if p.name in _RO_CANON:
        return True, "唯讀正典(靜態清單退路)"
    for part in _EXC_PARTS:
        if part in sp:
            return True, f"排除字串 {part}(靜態清單退路)"
    return False, ""


def collect_bridges() -> list:
    """操作員點名的兩件:加速器橋 / VDF 網路橋。**按尾版家族算,不按檔案算。**"""
    out = []
    # ① VDF 網路橋
    d = VIA / "functional modules" / "VDF" / "engine"
    fam = _tail_families(d, "VDF_ENG*.py")
    miss = []
    for b, p in fam.items():
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if not any(m in t for m in NET_MARK):
            miss.append(rel(p))
    if miss:
        out.append(finding("NET-VDF", "REAL_GAP",
                           f"VDF 引擎尾版缺網路橋 {len(miss)}/{len(fam)}",
                           " · ".join(miss[:6]), miss,
                           "via-bridge-sweep --root \"functional modules/VDF\" --apply"
                           "(只插標記塊,原碼一字不動;注入前後 py_compile 皆須過)"))
    else:
        out.append(finding("NET-VDF", "RULER",
                           f"VDF 引擎尾版網路橋 {len(fam)}/{len(fam)} 已滿",
                           "橋掃器報「缺 8」是按**檔案**算,其中含舊版號;"
                           "同一族尾版有橋、舊版沒有,同一件事被數成 4 件缺。"
                           "按尾版律重算是 0 —— **數檔案會把版史當資產**",
                           [], "無須動作;要對帳看 via-bridge-sweep --subsystems 的尾版欄"))
    # ② 四系加速器橋
    sub = {"VDF": VIA / "functional modules" / "VDF",
           "VAP": VIA / "functional modules" / "VAP",
           "VRN": VIA / "functional modules" / "VRN",
           "VIA": VIA / "supportive modules"}
    gaps, tot = [], 0
    for tag, root in sub.items():
        if not root.is_dir():
            continue
        f2 = _tail_families(root, "**/*.py")
        for b, p in f2.items():
            ex, _why = sweep_excluded(p)   # 判準向橋掃器**整支**取用,連函式一起
            if ex:
                continue
            tot += 1
            try:
                t = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if not any(m in t for m in ACC_MARK):
                gaps.append(rel(p))
    if gaps:
        out.append(finding("ACC-ALL", "REAL_GAP",
                           f"加速器橋缺 {len(gaps)}/{tot}(四系尾版)",
                           " · ".join(gaps[:6]), gaps,
                           "via-bridge-sweep --subsystems --apply(graceful 零行為變更)"))
    else:
        out.append(finding("ACC-ALL", "RULER",
                           f"加速器橋 {tot}/{tot} 已滿(四系尾版)",
                           "MDL156 中央線控報的 37 是**控制點**不是全樹檔數;"
                           "兩個數字量的是兩件事,不是誰錯",
                           [], "無須動作"))
    return out


def collect_state() -> list:
    """讀 MDL169 六域現況的存證(它已經把誠實態算好了,本支不重算)。"""
    p = VIA / "VIA_Reports" / "state_matrix" / "STATE_latest.json"
    d = load_json(p)
    if not d:
        return [finding("STATE", "NEED_DATA", "六域現況存證不在",
                        f"{rel(p)} 不在", [], "先跑 via-state")]
    out = []
    for r_ in (d.get("rows") or []):
        st = r_.get("state")
        if st == "GREEN":
            continue
        kind = {"RED": "REAL_GAP", "NODATA": "NEED_DATA",
                "GATED": "GATED", "ABSENT": "REAL_GAP"}.get(st, "NEED_DATA")
        # 判錯的燈也是一種發現,但它屬於 RULER 不屬於 REAL_GAP
        det = str(r_.get("detail", ""))
        if "合律" in det or "版史" in det or "比現在的樹舊" in det or "上一輪" in det:
            kind = "RULER"
        out.append(finding(f"STATE-{r_.get('domain')}-{str(r_.get('item'))[:14]}", kind,
                           f"[{r_.get('domain')}] {r_.get('item')}", det,
                           [str(r_.get("evidence") or "")] if r_.get("evidence") else [],
                           "見六域矩陣該列;via-state 可重量"))
    return out


def collect_grid() -> list:
    """格子存證:紅站是真缺,SKIP 是環境缺件(NEED_DATA),不混為一談。"""
    d = VIA / "VIA_Reports" / "selftest_runs"
    p = newest(d, "GRID_*.json")
    ev = load_json(p) if p else None
    if not ev:
        return [finding("GRID", "NEED_DATA", "格子存證不在",
                        f"{rel(d)} 內找不到 GRID_*.json", [], "先跑 via-selftest")]
    rows = ev if isinstance(ev, list) else next(
        (v for k, v in ev.items() if isinstance(v, list) and v
         and isinstance(v[0], dict) and "state" in v[0]), [])
    bad = [r_ for r_ in rows if str(r_.get("state")) == "FAIL"]
    skip = [r_ for r_ in rows if str(r_.get("state")) == "SKIP"]
    out = []
    for r_ in bad:
        out.append(finding(f"GRID-{str(r_.get('name'))[:18]}", "REAL_GAP",
                           f"格子紅站:{str(r_.get('name'))[:40]}",
                           str(r_.get("note", ""))[:160], [rel(p)],
                           "via-selftest --refail 只重跑紅站"))
    if skip:
        out.append(finding("GRID-SKIP", "NEED_DATA",
                           f"格子 SKIP {len(skip)} 站(環境缺件,不是壞掉)",
                           " · ".join(str(r_.get("name"))[:26] for r_ in skip[:4]),
                           [rel(p)], "缺件補齊才會轉綠;**不代裝**"))
    return out


def collect() -> list:
    return collect_bridges() + collect_state() + collect_grid()


# ── 分波:可同時 / 依序 ─────────────────────────────────────────────────
def plan_waves(items: list) -> tuple[list, list]:
    """把「該動的」排成波;「不該動的」另立一堆。

    只有 REAL_GAP 進波 —— RULER / NEED_DATA / GATED 三類**不是待修項**:
      尺錯了要改尺(那是另一批的工)· 缺料要補料 · 等閘要人。
      把它們排進修復波,人就會去動不該動的東西。

    同一波的兩筆,**目標檔案集合必須不相交**。相交就排到後面的波 ——
    兩個動作同時改同一個檔,誰後寫誰贏,而且沒人知道發生過。
    有前置依賴(needs)的,等依賴落在前面的波才排得進來。
    **九頭龍風險件與被禁動詞件一律不進波**:前者要人看過,後者根本不該做。
    """
    todo = [x for x in items if x["kind"] == "REAL_GAP"]
    held = [x for x in items if x["kind"] != "REAL_GAP"]
    blocked = [x for x in todo if x["blocked"] or x["hydra"]]
    todo = [x for x in todo if not (x["blocked"] or x["hydra"])]
    done: set = set()
    waves: list = []
    remaining = list(todo)
    for _ in range(64):                     # 上限是防呆,不是期待
        if not remaining:
            break
        wave, taken, defer = [], set(), []
        for x in remaining:
            if any(n not in done for n in x["needs"]):
                defer.append(x)             # 依賴還沒做完 → 下一波
                continue
            tg = set(x["targets"])
            if tg and (tg & taken):
                defer.append(x)             # 撞到同一個檔 → 下一波
                continue
            wave.append(x)
            taken |= tg
        if not wave:                        # 全卡住:剩下的一律序列,誠實講出來
            for x in remaining:
                waves.append([x])
                done.add(x["id"])
            remaining = []
            break
        waves.append(wave)
        done |= {x["id"] for x in wave}
        remaining = defer
    return waves, held + blocked


def build(ts: str | None = None) -> dict:
    t0 = time.time()
    items = collect()
    waves, held = plan_waves(items)
    tally = {k: sum(1 for x in items if x["kind"] == k) for k in KIND_ORDER}
    n_hydra = sum(1 for x in items if x["hydra"])
    n_block = sum(1 for x in items if x["blocked"])
    rc = (1 if tally["REAL_GAP"] else
          (2 if tally["NEED_DATA"] else
           (4 if tally["GATED"] else (5 if tally["RULER"] else 0))))
    return {"schema": "VIA.PanoPlan.v1", "version": VERSION, "batch": 670,
            "generated": ts or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ"),
            "host": os.environ.get("COMPUTERNAME") or os.uname().nodename,
            "tally": tally, "hydra": n_hydra, "blocked": n_block,
            "waves": [[x["id"] for x in w] for w in waves],
            "wave_detail": waves, "held": held, "items": items,
            "parallel_max": max((len(w) for w in waves), default=0),
            "rc": rc, "secs": round(time.time() - t0, 1)}


# ── 呈現 ────────────────────────────────────────────────────────────────
def _rich(record=False, width=205):
    try:
        from rich.console import Console
        return Console(record=record, width=width), True
    except Exception:
        return None, False


def _render_rich(con, rep: dict) -> None:
    from rich import box
    from rich.panel import Panel
    from rich.table import Table
    t = rep["tally"]
    con.print(Panel.fit(
        f"[bold]VIA 全景式分析 · 批次修復計畫[/bold] · 批670 · v{rep['version']}\n"
        f"產生 {rep['generated']} · 主機 {rep['host']}\n"
        f"[bold red]真缺 {t['REAL_GAP']}[/] · [yellow]缺料 {t['NEED_DATA']}[/] · "
        f"[bold cyan]等閘 {t['GATED']}[/] · [magenta]尺的錯 {t['RULER']}[/]"
        f"  ‖  波 {len(rep['waves'])} · 單波最多可並行 [bold]{rep['parallel_max']}[/] 件"
        f"  ‖  九頭龍風險 {rep['hydra']} · 禁動詞 BLOCK {rep['blocked']}\n"
        f"[dim]預設零動作:本表只說誰先誰後、哪些可以一起做[/dim]",
        title="VERITAS INTELLIGENCE ANALYTICS", border_style="cyan"))
    if rep["wave_detail"]:
        for i, w in enumerate(rep["wave_detail"], 1):
            tb = Table(title=f"第 {i} 波 · {len(w)} 件"
                             + ("(可同時做:目標檔案互不相交)" if len(w) > 1 else "(單件)"),
                       box=box.SIMPLE_HEAVY, header_style="bold cyan", title_style="bold")
            for h in ("id", "題目", "影響檔數", "可還原", "下一步"):
                tb.add_column(h, overflow="fold")
            for x in w:
                tb.add_row(x["id"], x["title"], str(x["blast"]),
                           "是" if x["reversible"] else "否", x["fix"])
            con.print(tb)
    else:
        con.print("[bold green]沒有 REAL_GAP —— 沒有東西需要排波。[/]")
    if rep["held"]:
        tb = Table(title="不進修復波(分類就是答案)", box=box.SIMPLE_HEAVY,
                   header_style="bold cyan", title_style="bold")
        for h in ("類", "題目", "為什麼不動它", "九頭龍 / BLOCK"):
            tb.add_column(h, overflow="fold")
        for x in rep["held"]:
            risk = " · ".join(x["hydra"] + x["blocked"]) or "—"
            tb.add_row(f"[{KIND_STYLE.get(x['kind'], '')}]{x['kind']}[/]",
                       x["title"], (KIND[x["kind"]] + ";" + x["detail"])[:120], risk)
        con.print(tb)


def _render_plain(rep: dict) -> None:
    t = rep["tally"]
    print(f"=== VIA 全景式分析 · 批次修復計畫 · 批670 v{rep['version']}(rich 缺席,降級)===")
    print(f"  真缺 {t['REAL_GAP']} · 缺料 {t['NEED_DATA']} · 等閘 {t['GATED']} · "
          f"尺的錯 {t['RULER']} ‖ 波 {len(rep['waves'])} · 單波最多 {rep['parallel_max']} 件"
          f" ‖ 九頭龍 {rep['hydra']} · BLOCK {rep['blocked']}")
    for i, w in enumerate(rep["wave_detail"], 1):
        print(f"\n── 第 {i} 波 · {len(w)} 件"
              + ("(可同時)" if len(w) > 1 else "(單件)"))
        for x in w:
            print(f"   [{x['id']}] {x['title'][:60]} · 影響 {x['blast']} 檔")
            print(f"        ↳ {x['fix'][:100]}")
    if rep["held"]:
        print(f"\n── 不進修復波 {len(rep['held'])} 件")
        for x in rep["held"]:
            print(f"   [{x['kind']:<9}] {x['title'][:60]}")


def render(rep: dict) -> bool:
    con, ok = _rich()
    if ok:
        _render_rich(con, rep)
        return True
    _render_plain(rep)
    print("  [律] rich 未安裝 → 降級(**不代裝套件**);降級有講出來,不是靜默。")
    return False


def write_html(rep: dict, out: Path | None = None) -> tuple[Path, bool]:
    out = out or (REPORTS / "VIA_Panorama_Plan_v0100.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    con, ok = _rich(record=True)
    if ok:
        _render_rich(con, rep)
        out.write_text(con.export_html(inline_styles=True), encoding="utf-8")
        return out, True
    esc = (lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    t = rep["tally"]
    h = ["<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'>",
         "<title>VIA 全景批次修復計畫</title><style>",
         "body{background:#0f1116;color:#d8dee9;font-family:Consolas,monospace;padding:24px}",
         "table{border-collapse:collapse;width:100%;margin:8px 0 24px}",
         "th,td{border:1px solid #2b313c;padding:5px 8px;font-size:13px;vertical-align:top}",
         "th{background:#1b2027;text-align:left}</style></head><body>",
         f"<h1>VIA 全景式分析 · 批次修復計畫 · 批670</h1>",
         f"<p>真缺 {t['REAL_GAP']} · 缺料 {t['NEED_DATA']} · 等閘 {t['GATED']} · "
         f"尺的錯 {t['RULER']} ‖ 波 {len(rep['waves'])} · 單波最多 {rep['parallel_max']} 件"
         f" ‖ 九頭龍 {rep['hydra']} · BLOCK {rep['blocked']}</p>"]
    for i, w in enumerate(rep["wave_detail"], 1):
        h.append(f"<h2>第 {i} 波 · {len(w)} 件</h2><table>"
                 "<tr><th>id</th><th>題目</th><th>影響檔數</th><th>下一步</th></tr>")
        for x in w:
            h.append(f"<tr><td>{esc(x['id'])}</td><td>{esc(x['title'])}</td>"
                     f"<td>{x['blast']}</td><td>{esc(x['fix'])}</td></tr>")
        h.append("</table>")
    if rep["held"]:
        h.append("<h2>不進修復波</h2><table><tr><th>類</th><th>題目</th><th>為什麼</th></tr>")
        for x in rep["held"]:
            h.append(f"<tr><td>{esc(x['kind'])}</td><td>{esc(x['title'])}</td>"
                     f"<td>{esc(KIND[x['kind']])}</td></tr>")
        h.append("</table>")
    h.append("</body></html>")
    out.write_text("".join(h), encoding="utf-8")
    return out, False


def write_log(rep: dict) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    body = json.dumps(rep, ensure_ascii=False, indent=1)
    (REPORTS / f"PANOPLAN_{ts}.json").write_text(body, encoding="utf-8")
    (REPORTS / "PANOPLAN_latest.json").write_text(body, encoding="utf-8")
    t = rep["tally"]
    with (REPORTS / "PANOPLAN_LEDGER.tsv").open("a", encoding="utf-8") as f:
        f.write(f"{rep['generated']}\treal={t['REAL_GAP']}\tdata={t['NEED_DATA']}"
                f"\tgated={t['GATED']}\truler={t['RULER']}\twaves={len(rep['waves'])}"
                f"\tpar={rep['parallel_max']}\thydra={rep['hydra']}\tblock={rep['blocked']}\n")
    return REPORTS / "PANOPLAN_latest.json"


# ── 自測二十檢(沙盒零網路)──────────────────────────────────────────
def selftest() -> int:
    import tempfile
    t0 = time.time()
    fails = []

    def chk(name, cond, note=""):
        if not cond:
            fails.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")

    rep = build()
    items = rep["items"]
    # ① 四類齊備,而且每一筆都落在其中一類(第五類偷偷混進來就沒人看得懂)
    bad = [x["kind"] for x in items if x["kind"] not in KIND]
    chk("錯誤識別只有四類", not bad and set(KIND) == set(KIND_ORDER), f"(越界 {bad[:3]})")
    # ② 只有 REAL_GAP 進波 —— 尺錯/缺料/等閘排進修復波,人就會去動不該動的
    inw = {x["id"] for w in rep["wave_detail"] for x in w}
    wrong = [x["id"] for x in items if x["id"] in inw and x["kind"] != "REAL_GAP"]
    chk("只有真缺進修復波", not wrong, f"(誤入 {wrong[:3]})")
    # ③ 同一波內目標檔案兩兩不相交(相交=同時改同一個檔,誰後寫誰贏)
    clash = []
    for i, w in enumerate(rep["wave_detail"], 1):
        seen: set = set()
        for x in w:
            tg = set(x["targets"])
            if tg & seen:
                clash.append(f"波{i}:{x['id']}")
            seen |= tg
    chk("同波目標互不相交(可真並行)", not clash, f"(相交 {clash[:3]})")
    # ④ 依賴不會排在被依賴的前面
    pos = {x["id"]: i for i, w in enumerate(rep["wave_detail"]) for x in w}
    bad_dep = [f"{x['id']}←{n}" for x in items for n in x["needs"]
               if x["id"] in pos and n in pos and pos[n] >= pos[x["id"]]]
    chk("依賴排在前面的波", not bad_dep, f"({bad_dep[:3]})")
    # ⑤ 九頭龍風險件與禁動詞件**一律不進波**
    leaked = [x["id"] for x in items if x["id"] in inw and (x["hydra"] or x["blocked"])]
    chk("九頭龍/禁動詞不進波", not leaked, f"(漏進 {leaked[:3]})")
    # ⑥ 禁動詞閘真的咬得住(拿實例試,不是宣稱)
    probe = [("請 Stop-Process 掉那個行程", 1), ("Remove-Item 這個夾", 1),
             ("git push --force 上去", 1), ("conda remove 那個套件", 1),
             ("pip uninstall talib", 1), ("只是加一個欄位", 0)]
    got = [(s, len(forbidden_hits(s))) for s, _ in probe]
    chk("禁動詞閘逐例咬", all(bool(n) == bool(w) for (_s, n), (_s2, w) in zip(got, probe)),
        f"({[(s[:12], n) for s, n in got]})")
    # ⑦ 九頭龍偵測逐例咬
    hy = [("新建一支做同一件事的引擎", 1), ("把那張表複製一份到這裡", 1),
          ("再加一個同名短令", 1), ("在既有正主上加一個版號", 0)]
    chk("九頭龍偵測逐例咬",
        all(bool(len(hydra_hits(s))) == bool(w) for s, w in hy),
        f"({[(s[:10], len(hydra_hits(s))) for s, _ in hy]})")
    # ⑧ 分波演算法:拿人造案例咬,不靠現場資料碰巧
    a = finding("A", "REAL_GAP", "a", "", ["f1"], "fix")
    b = finding("B", "REAL_GAP", "b", "", ["f2"], "fix")
    c = finding("C", "REAL_GAP", "c", "", ["f1"], "fix")          # 撞 A
    dd = finding("D", "REAL_GAP", "d", "", ["f3"], "fix", needs=["A"])
    w, _h = plan_waves([a, b, c, dd])
    ids = [[x["id"] for x in ww] for ww in w]
    chk("分波:撞檔的排後面、依賴排後面",
        ids and set(ids[0]) == {"A", "B"} and "C" in ids[1] and "D" in ids[1],
        f"({ids})")
    # ⑨ 全卡住時誠實退成序列,不無限迴圈
    x1 = finding("X", "REAL_GAP", "x", "", ["f"], "fix", needs=["NOPE"])
    w2, _ = plan_waves([x1])
    chk("依賴不存在 → 退成序列不卡死", len(w2) == 1 and w2[0][0]["id"] == "X", f"({len(w2)})")
    # ⑩ 尾版折族:同名不同版算一族(數檔案會把版史當資產)
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        for n in ("E_v0100.py", "E_v0102.py", "F_v0100.py"):
            (d / n).write_text("#", encoding="utf-8")
        fam = _tail_families(d, "*.py")
        chk("尾版折族", len(fam) == 2 and fam["E"].name == "E_v0102.py", f"({sorted(fam)})")
    # ⑪ 兩件點名的橋:結論要嘛 REAL_GAP 要嘛 RULER,不准含糊
    br = {x["id"]: x for x in collect_bridges()}
    chk("加速器/網路橋逐件有結論",
        set(br) == {"NET-VDF", "ACC-ALL"}
        and all(br[k]["kind"] in ("REAL_GAP", "RULER") for k in br),
        f"({[(k, br[k]['kind']) for k in br]})")
    # ⑫ 「版史當資產」這個誤判要被講出來,不是默默算對就算了
    chk("版史誤判具名講出來",
        br["NET-VDF"]["kind"] != "RULER" or "版史" in br["NET-VDF"]["detail"],
        f"({br['NET-VDF']['kind']})")
    # ⑫-b 排除清單必須是**向橋掃器取的**,不是自己寫的第二份
    chk("判準向橋掃器**整支**取用(靜態清單看不到凍結夾那段分支)",
        bool(_EXC_PARTS) and bool(_RO_CANON)
        and "VIA_Financial_Institution_SSOT_v0100.py" in _RO_CANON
        and sweep_excluded(VIA / "supportive modules/ssot/VIA_Financial_Institution_SSOT_v0100.py")[0]
        # 負向例要用**已經入倉**的檔。連挑錯兩次:先挑了不存在的檔、再挑了本檔
        #   (還沒 commit),兩次都被判「未在冊(gitignored 產物/副本)」——
        #   那不是判錯,是我拿一個永遠成立的東西當負向例(假綠的長相)。
        and not sweep_excluded(newest(HERE, "CGC_MDL124_BridgeSweeper_v*.py"))[0]
        and _SWEEP is not None
        and sweep_excluded(VIA / "supportive modules/VIA_Central_Governance/"
                                 "VIA_CentralGovernanceFamily_b514/VIA_DownwardController.py")[0],
        f"(排除 {len(_EXC_PARTS)} 條 · 唯讀正典 {len(_RO_CANON)} 件 · "
        f"正主 _excluded {'載到了' if _SWEEP else '**沒載到,走靜態退路**'})")
    # ⑬ 每一筆都有下一步(L92 哨兵抓到就要給得出下一步)
    nofix = [x["id"] for x in items if not str(x.get("fix", "")).strip()]
    chk("逐筆有下一步", not nofix, f"(缺 {nofix[:3]})")
    # ⑭ 影響半徑=目標檔數,對得起來(摘要跟明細對不起來是最難發現的假綠)
    badb = [x["id"] for x in items if x["blast"] != len(x["targets"])]
    chk("影響半徑=目標檔數", not badb, f"({badb[:3]})")
    # ⑮ 合計=逐筆
    chk("合計=逐筆", sum(rep["tally"].values()) == len(items),
        f"({sum(rep['tally'].values())} vs {len(items)})")
    # ⑯ rc 與分類一致(真缺優先,其次缺料,其次等閘,最後尺錯)
    t = rep["tally"]
    want = (1 if t["REAL_GAP"] else (2 if t["NEED_DATA"] else
            (4 if t["GATED"] else (5 if t["RULER"] else 0))))
    chk("rc 與分類一致", rep["rc"] == want, f"(rc={rep['rc']} 應 {want})")
    # ⑰ **本支零動作**:原始碼不准有寫入樹的動作(只能寫自己的報告夾)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest(")[0]
    writes = re.findall(r"\.write_text\(|\.unlink\(|shutil\.|os\.remove", body)
    ok17 = all(("REPORTS" in body.split(w)[0][-300:] or "out." in body.split(w)[0][-40:])
               for w in ["write_text("]) and not re.search(r"\.unlink\(|shutil\.rmtree|os\.remove", body)
    chk("本支零動作(不寫樹、不刪任何東西)", ok17, f"(寫入點 {len(writes)},應只在報告夾)")
    # ⑱ HTML 零外連且逐波都在頁上
    with tempfile.TemporaryDirectory() as td:
        p, used = write_html(rep, Path(td) / "p.html")
        html = p.read_text(encoding="utf-8")
        head = html.split("</head>")[0] if "</head>" in html else html[:4000]
        chk("HTML 零外連", p.exists() and "http://" not in head and "https://" not in head
            and "<script" not in html, f"(rich={'用了' if used else '降級'} · {len(html)} 字)")
    # ⑲ 存證三件 + 台帳 append-only
    with tempfile.TemporaryDirectory() as td:
        global REPORTS
        keep, REPORTS = REPORTS, Path(td)
        try:
            lp = write_log(rep)
            write_log(rep)
            led = (Path(td) / "PANOPLAN_LEDGER.tsv").read_text(encoding="utf-8")
            chk("存證三件 + 台帳 append-only",
                lp.exists() and len(list(Path(td).glob("PANOPLAN_2*.json"))) >= 1
                and led.count("\n") == 2, f"(台帳 {led.count(chr(10))} 行)")
        finally:
            REPORTS = keep
    # ⑳ 自我指涉:本支也會被格子跑到,不能把自己那一站當成別人的紅
    chk("自我指涉閘:家族名可推導", _SELF_FAMILY == Path(__file__).stem.rsplit("_v", 1)[0],
        f"({_SELF_FAMILY})")
    n_ok = 21 - len(fails)
    print(f"  [計] 廿一檢 OK {n_ok} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        print("=== 全景式分析 · 批次修復規劃器 v0100 · 廿一檢(沙盒零網路)===")
        return selftest()
    verb = next((x for x in a if not x.startswith("-")), "plan")
    if verb not in ("plan", "html"):
        print(f"  [用法] plan | html | --selftest(收到 {verb!r})")
        return 2
    print("=== VIA 全景式分析 · 批次修復計畫(預設零動作)===")
    rep = build()
    render(rep)
    lp = write_log(rep)
    if verb == "html":
        p, used = write_html(rep)
        print(f"\n  [頁] {rel(p)}(rich {'直出' if used else '缺席→降級'};零 CDN 零外連)")
        if not os.environ.get("VIA_NO_OPEN"):
            try:
                import webbrowser
                webbrowser.open(p.as_uri())
            except Exception:
                pass
    print(f"  [紀錄] {rel(lp)} + PANOPLAN_<時間戳>.json + PANOPLAN_LEDGER.tsv")
    print("  [律] 本支**只規劃不動手**。要動哪一波,照該波的『下一步』自己下令;"
          "九頭龍風險件與禁動詞件不進波——前者要你看過,後者根本不該做。")
    return rep["rc"]


if __name__ == "__main__":
    sys.exit(main())
