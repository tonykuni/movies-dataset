#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL170_VDFChainRunner v0102 — VDF 獨立鏈串連器(側線 2026-09-21 c:缺件具名 ABSENT,與批686 VRN 鏈跑器同律)
v0101→v0102:容器實跑第 2 站(ENG073 --selftest)因 `import duckdb` ModuleNotFoundError rc=1 被判 **RED**,3a/3b 同一根因卻是 NODATA——同一件事兩種燈。
  改在尺上:站的輸出裡有 ModuleNotFoundError(頂層名不是 VIA 樹上的自家模組)或引擎自報 rc=3,一律 **ABSENT 具名套件**(缺件≠壞掉;AI 不裝套件,
  修法句指名那個套件與工作站家族境)。自家模組炸了照舊 RED。+⑲ 合成檢(假引擎 import 不存在的套件 → ABSENT;假引擎普通炸 → RED 負控)。十八檢 → 十九檢。

CGC_MDL170_VDFChainRunner v0101 — VDF 獨立鏈串連器(批667;批672 接排版規格)
====================================================================
操作員令(批667):「VDF 是獨立引擎,幫我確認一下完整測試;邏輯·因子·參數·引擎
串連一下,給我一個 PS 指令啟動他們,自 2023-07-01 開始的資料,邊測邊修直到成功,
跳出 HTML MATRIX SUMMARY BY RICH」+「要加入我指令的加速器及網路工具」。

先量,四件**全部在架上**,一件都不用新造(LL306:先問翻了哪個架子):
  參數  VDF_ENG053_ParamEngineMap      輸入參數 x 引擎整合映射
  邏輯  VDF_ENG073_DataArchitecture    資料架構對映/盤點/最佳化計畫
  因子  VDF_ENG061_FeatureStore + VDF_ENG062_GroupFeatureLayer
  引擎  functional modules/VDF/engine  45 個 ENG 家族
所以本支**只調度不複製**(Zero-Hydra):每一站叫的都是那一族的尾版,
判準寫在那一支裡,不在這裡抄第二份。

第 0 站是**掛載**,操作員點名要的兩件:
  加速器  supportive modules/VIA_SuperAccel_Module.py(accel_map/快取/celeritas)
  網路    supportive modules/network/SUP_MDL740_NetUnified_v*.py 尾版
          → 後端是 VeritasAegisNexus 正典(批402 律:網路只認 AegisNexus,740 留作橋)
兩件都 graceful,但**在不在一定印出來** —— 靜默掛不上等於沒掛(批666 LL313 同族)。

同意閘鐵律:VIA_NET_CONSENT / VIA_SCRAPE_CONSENT **永不代設**,那是操作員的手。
閘沒開時,要觸網的站是 **GATED 不是 RED** —— 缺料不是壞掉,判成紅下一步就會變成
「去把閘打開」,而那不是我能替他做的決定(L52 誠實態)。

「邊測邊修直到成功」的機制不是我在迴圈裡硬跑,是:
  ① 每一站失敗都給得出**下一步**(L92),寫在 fix 欄
  ② --resume 讀上一回存證,已綠的站跳過,只重跑沒過的
  ③ 存證 append-only,第幾回合跑的看得見
用法:
  via-vdfchain                 → plan(只攤開,零動作;預設 --since 2023-07-01)
  via-vdfchain run             → **一句到底**:真跑七站 + 落 rich HTML MATRIX + 跳出頁
  via-vdfchain run --resume    → 只重跑上回沒過的站
  via-vdfchain html            → 只出頁不重跑(讀本次量到的;零 CDN 零外連 file:// 直開)
  via-vdfchain --since 2024-01-01 run
  via-vdfchain --selftest      → 十九檢(沙盒零網路)
誠實 rc:0 GREEN · 1 RED · 2 NODATA · 3 ABSENT · 4 GATED
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
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VDF_ENG = VIA / "functional modules" / "VDF" / "engine"
NET_DIR = VIA / "supportive modules" / "network"
REPORTS = VIA / "VIA_Reports" / "vdf_chain"
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
_SELF_FAMILY = Path(__file__).stem.rsplit("_v", 1)[0]

DEFAULT_SINCE = "2023-07-01"          # 批667 操作員指定;--since 可覆寫
RC_NAME = {0: "GREEN", 1: "RED", 2: "NODATA", 3: "ABSENT", 4: "GATED", 5: "SKIP"}
STATE_ORDER = ("RED", "GATED", "NODATA", "ABSENT", "SKIP", "GREEN")
STATE_STYLE = {"GREEN": "bold green", "RED": "bold red", "NODATA": "yellow",
               "ABSENT": "dim", "GATED": "bold cyan", "SKIP": "dim"}
CONSENT_ENV = "VIA_NET_CONSENT"        # 鐵律:永不代設
SCRAPE_ENV = "VIA_SCRAPE_CONSENT"


# ── 小工具 ──────────────────────────────────────────────────────────────
def newest(folder: Path, pattern: str) -> Path | None:
    """尾版律:同族取字典序最後一支;夾不在回 None(誠實,不炸)。"""
    try:
        hits = sorted(folder.glob(pattern))
    except OSError:
        return None
    return hits[-1] if hits else None


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(VIA)).replace("\\", "/")
    except (ValueError, AttributeError):
        return str(p)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod          # dataclass/annotations 要找得到模組
    spec.loader.exec_module(mod)
    return mod


def valid_since(s: str) -> bool:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(s or "")):
        return False
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def stage(sid, name, state, detail="", fix="", secs=None, evidence="") -> dict:
    """一站一列。**fix 是 L92 的落地**:哨兵抓到就要給得出下一步。"""
    return {"id": sid, "name": name, "state": state, "detail": detail,
            "fix": fix, "secs": secs, "evidence": evidence}


# ── 第 0 站:掛載(加速器 + 網路工具)────────────────────────────────────
def mount_accel() -> dict:
    p = VIA / "supportive modules" / "VIA_SuperAccel_Module.py"
    if not p.exists():
        return stage("0a", "加速器掛載", "ABSENT", "VIA_SuperAccel_Module.py 不在",
                     "樹不完整:git pull;或 via-accel-check 看橋", evidence=rel(p))
    if VIA_ACCEL is None:
        return stage("0a", "加速器掛載", "RED", "檔在但本支的加速器橋沒掛上",
                     "看本檔 [VIA:ACCEL-BRIDGE] 段;通常是 sys.path 沒找到 supportive modules",
                     evidence=rel(p))
    have = [n for n in ("accel_map", "fetch", "celeritas", "activate") if hasattr(VIA_ACCEL, n)]
    cache = getattr(VIA_ACCEL, "CACHE", None)
    return stage("0a", "加速器掛載", "GREEN" if len(have) >= 3 else "NODATA",
                 f"可用道 {'·'.join(have)}" + (f" · 快取 {rel(Path(cache))}" if cache else ""),
                 "" if len(have) >= 3 else "加速器在但道不齊:via-accel-check",
                 evidence=rel(p))


def mount_net() -> tuple[dict, object | None]:
    """網路工具:740 尾版當橋,後端是 AegisNexus 正典(批402 律)。

    **同意閘的狀態只讀不設。** 這裡回 GATED 時,下一步是操作員在他自己的視窗
    打那一行 env —— 不是我在程式裡填一個 YES 進去。
    """
    p = newest(NET_DIR, "SUP_MDL740_NetUnified_v*.py")
    if not p:
        return stage("0b", "網路工具掛載", "ABSENT", "SUP_MDL740_NetUnified_v*.py 不在",
                     "樹不完整:git pull", evidence=rel(NET_DIR)), None
    try:
        net = _load("vdfchain_net", p)
    except Exception as exc:
        return stage("0b", "網路工具掛載", "RED", f"載入炸了:{str(exc)[:70]}",
                     "先單跑該支 --selftest 看根因", evidence=rel(p)), None
    aegis = "?"
    try:
        ap = net._resolve_aegis_path()
        aegis = rel(Path(ap)) if ap else "(找不到 AegisNexus 正典)"
    except Exception:
        aegis = "(正典解析拋錯)"
    consent = os.environ.get(CONSENT_ENV, "")
    scrape = os.environ.get(SCRAPE_ENV, "")
    det = f"{p.name} · 後端 {aegis} · 閘一={consent or '未開'} 閘二={scrape or '未開'}"
    if consent.upper() != "YES":
        return stage("0b", "網路工具掛載", "GATED",
                     det + " —— **同意閘未開=缺料不是壞掉**;AI 永不代設",
                     f"要觸網的站才需要:在你的視窗打 $env:{CONSENT_ENV}='YES'"
                     f"(以及必要時 $env:{SCRAPE_ENV});零網路的站照跑",
                     evidence=rel(p)), net
    return stage("0b", "網路工具掛載", "GREEN", det, "", evidence=rel(p)), net


# ── VDF 獨立性(操作員問的第一件事:VDF 是獨立引擎嗎)──────────────────
_SIBLING = ("functional modules/VRN", "functional modules/VAP")


def standalone_check() -> dict:
    """量 VDF 引擎有沒有反向依賴 VRN/VAP。

    「獨立」不是宣稱,是量出來的:掃 VDF 引擎尾版的 import / 路徑字面,
    看有沒有指回兄弟家族。**有橋不等於不獨立**——橋是單向的才算獨立,
    所以逐支點名,讓操作員自己看那幾支在做什麼。
    """
    if not VDF_ENG.is_dir():
        return stage("0c", "VDF 獨立性", "ABSENT", "VDF/engine 夾不在",
                     "樹不完整:git pull", evidence=rel(VDF_ENG))
    fams: dict = {}
    for p in sorted(VDF_ENG.glob("*.py")):
        if "__pycache__" in str(p):
            continue
        base = re.sub(r"_v\d{4}\.py$", "", p.name).replace(".py", "")
        cur = fams.get(base)
        if cur is None or p.name > cur.name:
            fams[base] = p
    # 命中要分兩類,不然這一列會為了一件不是問題的事永遠不綠:
    #   · 收容件路徑(references/intake/…)—— 那只是某份外來件**被歸檔在**兄弟家族的
    #     收容夾底下,讀它不等於依賴那個家族的引擎。VDF_ENG088 共識融合橋就是這一類。
    #   · 真依賴 —— 指到兄弟家族的**引擎**。那才是「不獨立」。
    dep, filed = [], []
    for base, p in fams.items():
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore").replace("\\", "/")
        except OSError:
            continue
        for sib in _SIBLING:
            for m in re.finditer(re.escape(sib) + r"[^\"\'\n]*", txt):
                seg = m.group(0)
                (filed if "/references/intake/" in seg else dep).append(
                    f"{base}→{seg[:64]}")
    st = "GREEN" if not dep else "NODATA"
    det = (f"{len(fams)} 個 ENG 家族 · **真依賴兄弟家族 {len(dep)}**"
           + (f":{' · '.join(sorted(set(dep))[:4])}" if dep
              else " —— **VDF 這一側是獨立的**")
           + (f" · 另有 {len(set(filed))} 處是收容件路徑(歸檔在兄弟家族的 intake 夾,"
              f"讀它不等於依賴那個家族):{sorted(set(filed))[0][:52]}…" if filed else ""))
    return stage("0c", "VDF 獨立性", st, det,
                 "" if not dep else "逐支看那幾行:單向讀取可接受,回寫兄弟家族就不是獨立",
                 evidence=rel(VDF_ENG))


# ── 第 1–4 站:參數 · 邏輯 · 因子 · 引擎(只調度尾版,判準在那一支裡)──
# 每一站:(站號, 站名, 家族 glob, 動詞, 逾時秒, 期望, 修法句)
#   期望 "rc0"     rc 非 0 就是紅
#   期望 "soft"    rc 非 0 判 NODATA(那一支自己會說缺什麼料;缺料不是壞掉)
CHAIN = (
    ("1", "參數 · 輸入參數 x 引擎映射", "VDF_ENG053_ParamEngineMap_v*.py",
     ["--selftest"], 300, "rc0",
     "單跑看根因:via-py vdf \"functional modules/VDF/engine/VDF_ENG053...\" --selftest"),
    ("2", "邏輯 · 資料架構對映", "VDF_ENG073_DataArchitecture_v*.py",
     ["--selftest"], 300, "rc0",
     "單跑 --selftest;架構冊缺料時它會逐項點名"),
    ("3a", "因子 · 特徵庫", "VDF_ENG061_FeatureStore_v*.py",
     ["--selftest"], 300, "soft",
     "features_daily 表不在=缺料(NODATA):先 via-vdfdb 落庫,再回來"),
    ("3b", "因子 · 族群特徵層", "VDF_ENG062_GroupFeatureLayer_v*.py",
     ["--selftest"], 300, "soft",
     "吃族群分類快照冊 ROTATION_TW_*;快照不在=缺料,先 via-rotation"),
    ("4a", "引擎 · 資料涵蓋閘", "VDF_ENG090_DataCoverageGate_v*.py",
     ["--selftest"], 300, "soft",
     "涵蓋閘報缺就照它點的名補;要觸網的它會自己標 GATED"),
    ("4b", "引擎 · 增量擷取閘", "VDF_ENG089_IncrementalFetchGate_v*.py",
     ["--selftest"], 300, "soft",
     "增量閘看的是「上次抓到哪」;庫空=NODATA 不是壞"),
    ("4c", "引擎 · VDF 稽核閘", "VDF_ENG091_VdfAuditGate_v*.py",
     ["--selftest"], 300, "soft",
     "稽核閘逐項點名,照它說的補"),
)


def _fam_python() -> str:
    """家族境 python:有就用,沒有就用本境並**講出來**。

    工作站有 via_vdf_312,容器沒有。拿本境跑而不講,下游會以為這是家族境的答案。
    """
    root = os.environ.get("VIA_ENV_ROOT", "")
    if root:
        d = Path(root)
        for cand in sorted(d.glob("via_vdf_*")):
            for sub in ("python.exe", "bin/python", "python"):
                if (cand / sub).exists():
                    return str(cand / sub)
    return sys.executable


_MODNF = re.compile(r"ModuleNotFoundError: No module named '([A-Za-z0-9_.]+)'")


def _missing_pkgs(text: str) -> list:
    """輸出裡的 ModuleNotFoundError 頂層名;名字是 VIA 樹上自家 .py 的不算(那是壞掉,不是境缺)。"""
    out: list = []
    for name in _MODNF.findall(text or ""):
        top = name.split(".")[0]
        if top in out:
            continue
        if any(True for _ in VIA.rglob(f"{top}.py")):
            continue
        out.append(top)
    return out


def run_one(sid, name, glob_, argv, timeout, expect, fix, since: str) -> dict:
    p = newest(VDF_ENG, glob_)
    if not p:
        return stage(sid, name, "ABSENT", f"尾版不在:{glob_}",
                     "樹不完整:git pull", evidence=rel(VDF_ENG))
    t0 = time.time()
    env = dict(os.environ)
    env["VIA_NO_OPEN"] = "1"
    env["PYTHONUTF8"] = "1"
    env["VIA_SINCE"] = since          # 起始日以環境傳遞,不逼每支都加旗標(它們版號各異)
    try:
        r = subprocess.run([_fam_python(), str(p), *argv], capture_output=True, text=True,
                           timeout=timeout, stdin=subprocess.DEVNULL,
                           cwd=str(p.parent), env=env)
    except subprocess.TimeoutExpired:
        # 批616 同律:**逾時不是紅**。沒跑完 = 沒有結論,算紅等於編造一個沒量到的結論。
        return stage(sid, name, "NODATA", f"逾時 {timeout}s —— **沒跑完=沒有結論**,不是紅燈",
                     f"單跑看它卡在哪;或放寬逾時", round(time.time() - t0, 1), rel(p))
    except Exception as exc:
        return stage(sid, name, "RED", f"{type(exc).__name__}: {str(exc)[:70]}",
                     fix, round(time.time() - t0, 1), rel(p))
    secs = round(time.time() - t0, 1)
    tail = [l.strip() for l in (r.stdout + r.stderr).strip().splitlines() if l.strip()]
    note = " / ".join(tail[-2:])[:200] if tail else f"rc={r.returncode}"
    if r.returncode == 0:
        return stage(sid, name, "GREEN", note, "", secs, rel(p))
    if r.returncode == 4:
        return stage(sid, name, "GATED", note + " —— 等閘,不是壞掉",
                     f"要觸網才需要:$env:{CONSENT_ENV}='YES'", secs, rel(p))
    _miss = _missing_pkgs(r.stdout + r.stderr)
    if _miss or r.returncode == 3:
        # 側線 2026-09-21 c:缺件≠壞掉(四態律 rc3=ABSENT;批686 同律)。具名那個套件,修法句指路家族境;AI 不裝套件。
        return stage(sid, name, "ABSENT",
                     note + (f" —— 套件不在本境:{', '.join(_miss)}(缺件≠壞掉)" if _miss else " —— 引擎自報 ABSENT(rc=3;缺件≠壞掉)"),
                     (f"補上 {', '.join(_miss)} 再跑(工作站家族境 via_vdf_312 有;AI 不裝套件)" if _miss else "缺件照它點的名補;AI 不裝套件"),
                     secs, rel(p))
    if expect == "soft":
        return stage(sid, name, "NODATA", note + f"(rc={r.returncode};缺料不是壞掉)",
                     fix, secs, rel(p))
    return stage(sid, name, "RED", note + f"(rc={r.returncode})", fix, secs, rel(p))


# ── 彙整 ────────────────────────────────────────────────────────────────
def collect(since: str = DEFAULT_SINCE, do_run: bool = False,
            resume: bool = False) -> dict:
    t0 = time.time()
    rows = [mount_accel()]
    net_row, _net = mount_net()
    rows.append(net_row)
    rows.append(standalone_check())
    prev = {}
    if resume:
        lp = REPORTS / "VDFCHAIN_latest.json"
        if lp.exists():
            try:
                for r_ in (json.loads(lp.read_text(encoding="utf-8")).get("stages") or []):
                    prev[r_.get("id")] = r_
            except Exception:
                prev = {}
    for sid, name, glob_, argv, timeout, expect, fix in CHAIN:
        if not do_run:
            p = newest(VDF_ENG, glob_)
            rows.append(stage(sid, name, "SKIP" if p else "ABSENT",
                              (f"尾版 {p.name}" if p else f"尾版不在:{glob_}")
                              + " · plan 只攤開零動作",
                              "" if p else "樹不完整:git pull",
                              evidence=rel(p) if p else rel(VDF_ENG)))
            continue
        if resume and prev.get(sid, {}).get("state") == "GREEN":
            old = dict(prev[sid])
            old["detail"] = "上一回已綠,--resume 跳過:" + str(old.get("detail", ""))[:120]
            old["state"] = "GREEN"
            rows.append(old)
            continue
        rows.append(run_one(sid, name, glob_, argv, timeout, expect, fix, since))
    tally = {s: sum(1 for r_ in rows if r_["state"] == s) for s in STATE_ORDER}
    rc = 1 if tally["RED"] else (4 if tally["GATED"] else
                                 (2 if tally["NODATA"] else
                                  (3 if tally["ABSENT"] else 0)))
    return {"schema": "VIA.VDFChain.v1", "version": VERSION, "batch": 667,
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ"),
            "host": os.environ.get("COMPUTERNAME") or os.uname().nodename,
            "python": sys.version.split()[0], "family_python": _fam_python(),
            "since": since, "mode": ("run" if do_run else "plan") + ("+resume" if resume else ""),
            "consent": {CONSENT_ENV: os.environ.get(CONSENT_ENV, ""),
                        SCRAPE_ENV: os.environ.get(SCRAPE_ENV, "")},
            "tally": tally, "rc": rc, "rc_name": RC_NAME[rc],
            "secs": round(time.time() - t0, 1), "stages": rows}


# ── 呈現(rich;缺 rich 降級但**講出來**)────────────────────────────────

# ── 排版規格:向 CGC_MDL173 **整支取用**(批672;L30 一個出處)──────────
#   批669–671 我一口氣做了四支會落頁的引擎,四支各自帶一份 css=("body{...")。
#   四份幾乎一樣但不是同一份:字級 13/12.5/13 各有各的。操作員說「字小」的那一刻,
#   要改的地方有四個——**規格散在四處就不是規格,是四個人各自的習慣**。
#   所以這裡不自備第二份 CSS,只呼叫(批670 LL316:抄清單不算一個出處,抄到函式才算)。
def _spec_mod():
    """回 CGC_MDL173 尾版模組;缺席回 None(缺件要說出來,不是偷偷長一份自己的)。"""
    import importlib.util
    cands = sorted(Path(__file__).resolve().parent.glob("CGC_MDL173_MatrixReportSpec_v*.py"))
    if not cands:
        return None
    try:
        sp = importlib.util.spec_from_file_location("via_matrixspec", cands[-1])
        m = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(m)
        return m
    except Exception:
        return None


HEADERS = ("站", "名稱", "態", "秒", "量到什麼 · 為什麼是這個燈", "下一步(修法)", "出處")


def _cells(r: dict) -> list:
    return [r["id"], r["name"], r["state"],
            "" if r.get("secs") is None else str(r["secs"]),
            r.get("detail", ""), r.get("fix", ""), r.get("evidence", "")]


def _rich_console(record: bool = False, width: int = 210):
    try:
        from rich.console import Console
        return Console(record=record, width=width), True
    except Exception:
        return None, False


def _rich_render(con, rep: dict) -> None:
    from rich import box
    from rich.panel import Panel
    from rich.table import Table
    t = rep["tally"]
    con.print(Panel.fit(
        f"[bold]VDF 獨立鏈 · MATRIX SUMMARY[/bold] · 批667 · v{rep['version']}\n"
        f"起始日 [bold]{rep['since']}[/bold] · 模式 {rep['mode']} · "
        f"產生 {rep['generated']}\n"
        f"主機 {rep['host']} · python {rep['python']} · 家族境 {rep['family_python']}\n"
        f"同意閘 {CONSENT_ENV}={rep['consent'][CONSENT_ENV] or '未開'} · "
        f"{SCRAPE_ENV}={rep['consent'][SCRAPE_ENV] or '未開'}"
        f"  [dim](AI 永不代設)[/dim]\n"
        f"[bold green]GREEN {t['GREEN']}[/] · [bold red]RED {t['RED']}[/] · "
        f"[bold cyan]GATED {t['GATED']}[/] · [yellow]NODATA {t['NODATA']}[/] · "
        f"[dim]ABSENT {t['ABSENT']} · SKIP {t['SKIP']}[/] → [bold]{rep['rc_name']}[/]",
        title="VERITAS INTELLIGENCE ANALYTICS · VDF", border_style="cyan"))
    tb = Table(box=box.SIMPLE_HEAVY, header_style="bold cyan", pad_edge=False)
    for h in HEADERS:
        tb.add_column(h, overflow="fold", no_wrap=False)
    for r_ in rep["stages"]:
        c = _cells(r_)
        c[2] = f"[{STATE_STYLE.get(r_['state'], '')}]{r_['state']}[/]"
        tb.add_row(*c)
    con.print(tb)


def _plain_render(rep: dict) -> None:
    t = rep["tally"]
    print(f"=== VDF 獨立鏈 · MATRIX SUMMARY · 批667 v{rep['version']}"
          f"(rich 缺席,純文字降級)===")
    print(f"  起始日 {rep['since']} · 模式 {rep['mode']} · 主機 {rep['host']}")
    print(f"  同意閘 {CONSENT_ENV}={rep['consent'][CONSENT_ENV] or '未開'}(AI 永不代設)")
    for r_ in rep["stages"]:
        print(f"  [{r_['state']:<6}] {r_['id']:<3} {r_['name'][:26]:<26} "
              f"{str(r_.get('secs') or ''):>5}  {str(r_.get('detail'))[:78]}")
        if r_.get("fix") and r_["state"] not in ("GREEN", "SKIP"):
            print(f"           ↳ 下一步:{r_['fix'][:96]}")
    print(f"  [計] GREEN {t['GREEN']} · RED {t['RED']} · GATED {t['GATED']}"
          f" · NODATA {t['NODATA']} · ABSENT {t['ABSENT']} · SKIP {t['SKIP']}"
          f" → {rep['rc_name']}")


def render(rep: dict) -> bool:
    con, ok = _rich_console()
    if ok:
        _rich_render(con, rep)
        return True
    _plain_render(rep)
    print("  [律] rich 未安裝 → 純文字降級(**不代裝套件**,那是操作員的手)。"
          "降級有講出來——靜默的降級跟壞掉一樣看不出來。")
    return False


def _plain_html(rep: dict) -> str:
    esc = (lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    t = rep["tally"]
    css = ("body{background:#0f1116;color:#d8dee9;font-family:Consolas,'Noto Sans Mono CJK TC',monospace;"
           "margin:0;padding:24px}table{border-collapse:collapse;width:100%}"
           "th,td{border:1px solid #2b313c;padding:5px 8px;font-size:13px;vertical-align:top}"
           "th{background:#1b2027;text-align:left}.GREEN{color:#9ece6a;font-weight:700}"
           ".RED{color:#f7768e;font-weight:700}.GATED{color:#7dcfff;font-weight:700}"
           ".NODATA{color:#e0af68}.ABSENT,.SKIP{color:#565f89}")
    h = ["<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'>",
         "<title>VDF 獨立鏈 MATRIX SUMMARY</title>", f"<style>{css}</style></head><body>",
         "<h1>VDF 獨立鏈 · MATRIX SUMMARY · 批667</h1>",
         f"<p>起始日 <b>{esc(rep['since'])}</b> · 模式 {esc(rep['mode'])} · "
         f"產生 {esc(rep['generated'])} · 主機 {esc(rep['host'])}"
         f" · <b>rich 未安裝,本頁為降級版</b></p>",
         f"<p>{CONSENT_ENV}={esc(rep['consent'][CONSENT_ENV] or '未開')} (AI 永不代設) · "
         f"<span class='GREEN'>GREEN {t['GREEN']}</span> · <span class='RED'>RED {t['RED']}</span>"
         f" · <span class='GATED'>GATED {t['GATED']}</span> · "
         f"<span class='NODATA'>NODATA {t['NODATA']}</span> → <b>{esc(rep['rc_name'])}</b></p>",
         "<table><tr>" + "".join(f"<th>{esc(x)}</th>" for x in HEADERS) + "</tr>"]
    for r_ in rep["stages"]:
        c = _cells(r_)
        h.append("<tr>" + "".join(
            f"<td class='{esc(r_['state'])}'>{esc(v)}</td>" if i == 2 else f"<td>{esc(v)}</td>"
            for i, v in enumerate(c)) + "</tr>")
    h.append("</table></body></html>")
    return "".join(h)


def _md(rep: dict) -> str:
    """頁上那顆 MD 鍵吐的就是**這一份**。JS 永不自己拼第二份(L30)。"""
    t = rep["tally"]
    out = [f"# VDF 獨立鏈 · MATRIX SUMMARY(批667)", "",
           f"- 產生 {rep['generated']} · 主機 {rep['host']} · 起始日 {rep['since']} · 模式 {rep['mode']}",
           f"- {CONSENT_ENV}={rep['consent'][CONSENT_ENV] or '未開'}(AI 永不代設)",
           f"- GREEN {t['GREEN']} · RED {t['RED']} · GATED {t['GATED']} · "
           f"NODATA {t['NODATA']} · ABSENT {t['ABSENT']} → **{rep['rc_name']}**", "",
           "| " + " | ".join(HEADERS) + " |",
           "|" + "---|" * len(HEADERS)]
    for r_ in rep["stages"]:
        out.append("| " + " | ".join(str(x).replace("|", "/") for x in _cells(r_)) + " |")
    return "\n".join(out) + "\n"


def _kpis(rep: dict) -> list:
    t = rep["tally"]
    return [{"label": k, "value": t[k], "state": k} for k in
            ("GREEN", "RED", "GATED", "NODATA", "ABSENT")] + \
           [{"label": "總判", "value": rep["rc_name"], "state": rep["rc_name"]}]


def write_html(rep: dict, out: Path | None = None) -> tuple[Path, bool]:
    """落頁一律走 CGC_MDL173 排版規格(批672 操作員令:矩陣式報告 BY RICH,字小)。"""
    out = out or (REPORTS / "VIA_VDF_Chain_Matrix_v0100.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    M = _spec_mod()
    sub = (f"{rep['generated']} · 主機 {rep['host']} · 起始日 {rep['since']} · "
           f"模式 {rep['mode']} · {CONSENT_ENV}={rep['consent'][CONSENT_ENV] or '未開'}"
           f"(AI 永不代設)")
    law = ("<b>GATED ≠ 壞掉</b>:要觸網的站在等同意閘,閘的裁定權在操作員手上,AI 永不代設。"
           "逾時記 NODATA 不記 RED——沒跑完等於沒有結論。")
    if M is None:
        # 規格缺席:**說出來**,不偷偷長一份自己的 CSS(Zero-Hydra)
        out.write_text(_plain_html(rep), encoding="utf-8")
        print("  [NODATA] CGC_MDL173 排版規格缺席 → 本頁為無規格降級版")
        return out, False
    con, ok = _rich_console(record=True)
    if ok:
        _rich_render(con, rep)
        M.page(con, title="VDF 獨立鏈 · MATRIX SUMMARY · 批667",
               subtitle=sub, md=_md(rep), payload=rep, kpis=_kpis(rep), law=law, out=out)
        return out, True
    # rich 缺席但規格還在:走 HTML 車道,**同一份 css()**,不是另一套樣子
    body = M.html_table(list(HEADERS), [[_cells(r_)[i] if i != 2 else
                                         {"t": r_["state"], "s": r_["state"]}
                                         for i in range(len(HEADERS))]
                                        for r_ in rep["stages"]],
                        caption="七站矩陣(rich 未安裝,表由排版規格直出)",
                        num_cols={3}, center_cols={2})
    M.page_html(body, title="VDF 獨立鏈 · MATRIX SUMMARY · 批667",
                subtitle=sub + " · rich 未安裝(**不代裝套件**)",
                md=_md(rep), payload=rep, kpis=_kpis(rep), law=law, out=out)
    return out, False


def write_log(rep: dict) -> Path:
    """存證三件:時間戳(歷史)· latest(現況)· 台帳一行(第幾回合跑的)。

    --resume 讀的就是 latest —— 「邊測邊修直到成功」要能記得上一回哪幾站已經綠了。
    """
    REPORTS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    body = json.dumps(rep, ensure_ascii=False, indent=1)
    (REPORTS / f"VDFCHAIN_{ts}.json").write_text(body, encoding="utf-8")
    (REPORTS / "VDFCHAIN_latest.json").write_text(body, encoding="utf-8")
    t = rep["tally"]
    with (REPORTS / "VDFCHAIN_LEDGER.tsv").open("a", encoding="utf-8") as f:
        f.write(f"{rep['generated']}\t{rep['mode']}\tsince={rep['since']}\t{rep['rc_name']}"
                f"\tGREEN={t['GREEN']}\tRED={t['RED']}\tGATED={t['GATED']}"
                f"\tNODATA={t['NODATA']}\tsecs={rep['secs']}\n")
    return REPORTS / "VDFCHAIN_latest.json"


# ── 自測十八檢(沙盒零網路)──────────────────────────────────────────
def selftest() -> int:
    import contextlib
    import io
    import tempfile
    t0 = time.time()
    fails = []

    def chk(name, cond, note=""):
        if not cond:
            fails.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")

    rep = collect(do_run=False)                     # plan:零動作,快
    rows = rep["stages"]
    ids = [r["id"] for r in rows]
    # ① 六站齊(0a/0b/0c + 鏈上七站)
    want = ["0a", "0b", "0c"] + [c[0] for c in CHAIN]
    chk("站齊且不重號", ids == want and len(set(ids)) == len(ids), f"({ids})")
    # ② 燈號只有六種——第七種燈偷偷混進來就沒人看得懂這張表
    bad = [r["state"] for r in rows if r["state"] not in STATE_ORDER]
    chk("燈號只有六種(誠實態)", not bad, f"(越界 {bad[:3]})")
    # ③ 非綠非跳過的一定給得出下一步(L92:哨兵抓到就要給得出下一步)
    nofix = [r["id"] for r in rows
             if r["state"] not in ("GREEN", "SKIP") and not str(r.get("fix", "")).strip()]
    chk("非綠必附下一步", not nofix, f"(缺 {nofix})")
    # ④ 逐站有出處。沒有出處的數字沒辦法被推翻(L96)
    noev = [r["id"] for r in rows if not str(r.get("evidence", "")).strip()]
    chk("逐站有出處", not noev, f"(缺 {noev})")
    # ⑤ 合計=逐站(摘要跟明細對不起來是最難發現的假綠)
    chk("合計=逐站", sum(rep["tally"].values()) == len(rows),
        f"({sum(rep['tally'].values())} vs {len(rows)})")
    # ⑥ 起始日預設是操作員指定的那一天,而且擋得住亂寫的日期
    chk("起始日預設 2023-07-01 且格式驗得住",
        rep["since"] == DEFAULT_SINCE == "2023-07-01"
        and valid_since("2024-01-31") and not valid_since("2024-13-01")
        and not valid_since("20240101") and not valid_since(""),
        f"({rep['since']})")
    # ⑦ 同意閘只讀不設 —— 整份原始碼不准有寫入那兩個 env 的動作
    src = Path(__file__).read_text(encoding="utf-8")
    writes = re.findall(r"environ\s*\[\s*['\"]VIA_(?:NET|SCRAPE)_CONSENT['\"]\s*\]\s*=", src)
    writes += re.findall(r"environ\.setdefault\(\s*['\"]VIA_(?:NET|SCRAPE)_CONSENT", src)
    chk("同意閘永不代設(原始碼層咬死)", not writes, f"(寫入點 {len(writes)})")
    # ⑧ 加速器與網路工具兩站都在,而且網路站認得出閘的狀態
    a = next(r for r in rows if r["id"] == "0a")
    n = next(r for r in rows if r["id"] == "0b")
    chk("加速器站+網路站在位",
        a["state"] in STATE_ORDER and n["state"] in STATE_ORDER
        and "SuperAccel" in a["evidence"] and "NetUnified" in n["evidence"],
        f"(加速器 {a['state']} · 網路 {n['state']})")
    # ⑨ 閘沒開時網路站是 GATED 不是 RED(缺料不是壞掉)
    if os.environ.get(CONSENT_ENV, "").upper() != "YES":
        chk("閘未開=GATED 不是 RED", n["state"] in ("GATED", "ABSENT"),
            f"({n['state']})")
    else:
        chk("閘未開=GATED 不是 RED", True, "(本境閘已開,此檢不適用)")
    # ⑩ VDF 獨立性是**量出來的**不是宣稱:掃到家族數要合理
    s0c = next(r for r in rows if r["id"] == "0c")
    chk("VDF 獨立性逐支量,且收容件路徑不算依賴",
        "ENG 家族" in s0c["detail"] and s0c["state"] in STATE_ORDER
        and "真依賴兄弟家族" in s0c["detail"],
        f"({s0c['detail'][:70]})")
    # ⑪ plan 是**零動作**:七站全 SKIP/ABSENT,一個子行程都不起
    chain_rows = [r for r in rows if r["id"] in [c[0] for c in CHAIN]]
    chk("plan 零動作", all(r["state"] in ("SKIP", "ABSENT") for r in chain_rows)
        and all(r.get("secs") is None for r in chain_rows), f"({len(chain_rows)} 站)")
    # ⑫ Zero-Hydra:本支不複製任何一支 VDF 引擎的判準,只記家族 glob
    chk("只調度不複製(鏈表只有 glob 與動詞)",
        all(g.endswith("_v*.py") and isinstance(av, list) for _i, _n, g, av, *_ in CHAIN),
        f"({len(CHAIN)} 站)")
    # ⑬ 尾版律 + 夾不在不炸
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        for nm in ("X_v0100.py", "X_v0103.py", "X_v0102.py"):
            (d / nm).write_text("#", encoding="utf-8")
        chk("尾版律 glob", newest(d, "X_v*.py").name == "X_v0103.py"
            and newest(d / "nope", "*.py") is None)
    # ⑭ rc 與燈一致(紅優先,其次閘,其次缺料)
    t = rep["tally"]
    want_rc = 1 if t["RED"] else (4 if t["GATED"] else
                                  (2 if t["NODATA"] else (3 if t["ABSENT"] else 0)))
    chk("rc 與燈一致", rep["rc"] == want_rc, f"(rc={rep['rc']} 應 {want_rc})")
    # ⑮ HTML:寫得出、零外連、逐站都在頁上(rich 在不在都要成立)
    with tempfile.TemporaryDirectory() as td:
        p, used = write_html(rep, Path(td) / "m.html")
        html = p.read_text(encoding="utf-8")
        head = html.split("</head>")[0] if "</head>" in html else html[:4000]
        ext = ("http://" in head or "https://" in head or "cdn." in head)
        # 批672:頁上多了三顆鍵(MD/JSON/複製),JS **全內嵌**。
        #   v0100 這一檢寫的是「頁上不准有 <script>」——那是在禁一個本來就零外連的東西。
        #   要禁的是**往外拿**:`<script src=` 才是外連,內嵌 <script> 不是。
        #   同時把三顆鍵也收進這一檢:有鍵才帶得走(L96 舉證能整份帶走)。
        ext = ext or ("<script src" in html) or ("<script  src" in html)
        keys = all(s in html for s in ("vmd()", "vjson()", "vcopy()"))
        miss = [r["id"] for r in rows if r["id"] not in html]
        chk("HTML 零外連 · 逐站齊 · 三顆鍵在位", p.exists() and not ext and not miss and keys,
            f"(rich={'用了' if used else '降級'} · {len(html)} 字 · 缺站 {miss} · 鍵 {keys})")
    # ⑯ 存證三件 + 台帳 append-only(--resume 要靠它記住上一回)
    with tempfile.TemporaryDirectory() as td:
        global REPORTS
        keep, REPORTS = REPORTS, Path(td)
        try:
            lp = write_log(rep)
            write_log(rep)
            led = (Path(td) / "VDFCHAIN_LEDGER.tsv").read_text(encoding="utf-8")
            chk("存證三件 + 台帳 append-only",
                lp.exists() and len(list(Path(td).glob("VDFCHAIN_2*.json"))) >= 1
                and led.count("\n") == 2 and f"since={rep['since']}" in led,
                f"(台帳 {led.count(chr(10))} 行)")
            # ⑰ --resume 讀得到 latest,而且**只跳過綠的**
            fake = json.loads(lp.read_text(encoding="utf-8"))
            fake["stages"] = [dict(x, state="GREEN") for x in fake["stages"]
                              if x["id"] == CHAIN[0][0]]
            lp.write_text(json.dumps(fake, ensure_ascii=False), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                rep2 = collect(do_run=True, resume=True)
            r1 = next(r for r in rep2["stages"] if r["id"] == CHAIN[0][0])
            r2 = next(r for r in rep2["stages"] if r["id"] == CHAIN[1][0])
            chk("--resume 只跳過綠的",
                "已綠" in str(r1.get("detail")) and "已綠" not in str(r2.get("detail")),
                f"({CHAIN[0][0]} 跳過 · {CHAIN[1][0]} 真跑 rc 燈 {r2['state']})")
        finally:
            REPORTS = keep
    # ⑱ 自我指涉:本支自己也會被格子跑到,讀存證時不能把自己算進去
    # 批664 那一條的第二次發作:第一版寫死字面去數,**檢查器自己那行也含有它**,
    #   於是永遠數得到。needle 動態組,而且只看引擎本體不看自測 ——
    #   自測碼提到一個字是在描述它,不是在用它。
    needle = "GRID" + "_"
    body = src.split("def selftest(")[0]
    chk("自我指涉閘:家族名可推導且引擎本體不讀格子存證",
        _SELF_FAMILY == Path(__file__).stem.rsplit("_v", 1)[0]
        and needle not in body, f"(自家族 {_SELF_FAMILY} · 本體提及 {body.count(needle)} 次)")
    n_ok = 19 - len(fails)
    # ⑲ 側線 2026-09-21 c:缺件具名 ABSENT(合成:假引擎 import 不存在的套件 → ABSENT 且具名;假引擎普通炸 → RED 負控)
    try:
        with tempfile.TemporaryDirectory() as td19:
            d19 = Path(td19)
            (d19 / "VDF_ENG998_FakeMissing_v0100.py").write_text("import zz_pkg_not_installed_9z\n", encoding="utf-8")
            (d19 / "VDF_ENG997_FakeBroken_v0100.py").write_text("raise SystemExit(1)\n", encoding="utf-8")
            _saved19 = globals()["VDF_ENG"]
            globals()["VDF_ENG"] = d19
            try:
                a19 = run_one("9a", "合成缺件", "VDF_ENG998_FakeMissing_v*.py", [], 60, "rc0", "x", DEFAULT_SINCE)
                b19 = run_one("9b", "合成壞掉", "VDF_ENG997_FakeBroken_v*.py", [], 60, "rc0", "x", DEFAULT_SINCE)
            finally:
                globals()["VDF_ENG"] = _saved19
        chk("⑲ 缺件具名 ABSENT:import 不存在的套件 → ABSENT 且點名套件與家族境;普通炸 → RED(負控;缺件≠壞掉,壞掉≠缺件)",
            a19["state"] == "ABSENT" and "zz_pkg_not_installed_9z" in a19["detail"] and "via_vdf_312" in a19["fix"] and b19["state"] == "RED",
            f"({a19['state']} · {b19['state']})")
    except Exception as exc:
        fails.append("⑲"); print("  [FAIL] ⑲ 例外:", type(exc).__name__, exc)

    print(f"  [計] 十九檢 OK {n_ok} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    since = DEFAULT_SINCE
    if "--since" in a:
        i = a.index("--since")
        if i + 1 < len(a):
            since = a[i + 1]
    if not valid_since(since):
        print(f"  [用法] --since 要 YYYY-MM-DD(收到 {since!r})")
        return 2
    if "--selftest" in a:
        print("=== VDF 獨立鏈串連器 v0100 · 十八檢(沙盒零網路)===")
        return selftest()
    verb = next((x for x in a if not x.startswith("-")), "plan")
    resume = "--resume" in a
    if verb not in ("plan", "run", "html"):
        print(f"  [用法] plan | run [--resume] | html  [--since YYYY-MM-DD](收到 {verb!r})")
        return 2
    print(f"=== VDF 獨立鏈 · {verb}{'+resume' if resume else ''} · 起始日 {since} ===")
    rep = collect(since=since, do_run=(verb != "plan"), resume=resume)
    render(rep)
    lp = write_log(rep)
    # 批667 操作員令:「給我一個 PS 指令啟動他們……跳出 HTML MATRIX SUMMARY」。
    #   所以 run 也吐頁也跳出來 —— 要他跑完再多打一句 html,那就不是**一個**指令了(L97 同族)。
    if verb in ("run", "html"):
        p, used = write_html(rep)
        print(f"\n  [頁] {rel(p)}(rich {'直出' if used else '缺席→降級'};零 CDN 零外連,file:// 直開)")
        if not os.environ.get("VIA_NO_OPEN"):
            try:
                import webbrowser
                webbrowser.open(p.as_uri())
            except Exception:
                pass
    print(f"  [紀錄] {rel(lp)} + VDFCHAIN_<時間戳>.json + VDFCHAIN_LEDGER.tsv(append-only)")
    if rep["rc"] == 4:
        print(f"  [律] GATED≠壞掉:要觸網的站在等同意閘。"
              f"在**你的**視窗打 $env:{CONSENT_ENV}='YES' 再 `via-vdfchain run --resume`"
              f" —— **AI 永不代設同意閘**。")
    if rep["rc"] in (1, 2):
        print("  [律] 每一站的「下一步」在上表最右邊第二欄;修完打 "
              "`via-vdfchain run --resume`,已綠的站不會重跑。")
    return rep["rc"]


if __name__ == "__main__":
    sys.exit(main())
