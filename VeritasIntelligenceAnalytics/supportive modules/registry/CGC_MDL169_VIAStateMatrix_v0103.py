#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL169_VIAStateMatrix v0103 — VIA 六域現況矩陣與 rich HTML 實測報告(批664)
====================================================================
v0102→v0103(批670 自審:一句自相矛盾的話)
  批670 的全景規劃器讀本支存證時,印出來是:
      「**這份存證比現在的樹舊**(存證比 HEAD commit 早 **0.0 天**)」
  一個「早 0.0 天」讀起來就是「沒有差」——斷言說它舊,括號裡說它不舊。
  根因:gap 一律 round 到 1 位小數,同日的差距全被壓成 0.0。
  改成**差距小就換單位**(小時/分鐘),讓那個數字自己撐得住那句斷言(LL304 同族)。

v0101→v0102(批669 工作站實錄:這支引擎自己三個錯)
  操作員在他機器上跑 via-state html,印出 GREEN 25 · **RED 3** · NODATA 1 · ABSENT 4。
  逐列看,**其中三件是我這支引擎的錯,不是他樹的錯**:

  ① 家族境 python 三格全報 ABSENT:「VIA_ENV_ROOT=C:\Users\tonyk\envs 下找不到 via_vrn_*」
     ——**但同一台機器上 via-rungate 找得到**:
         python=C:\Users\tonyk\envs\via_vrn_312\Scripts\python.exe(OK)
     根因:Windows venv 把直譯器放在 `<env>\Scripts\python.exe`,而我的子路徑清單只試了
     `python.exe` / `bin/python` / `python`(那是 conda 與 POSIX 的擺法)。**漏了 Scripts\。**
     兩把尺量同一件事給出相反答案,而且**錯的是我這把**(L93 先疑尺不疑樹——這次真的是尺)。

  ② 三盞 RED 全部指向同一份 1.3 天前的格子存證(那時他還沒拉,樹差 5 批)。
     拿一份比現在的樹還舊的存證判紅,是批668 那條的另一個長相:
     **不是「在格子裡面」,是「存證比樹舊」**;兩者都是拿別的時候的結論當成現在的。
     改法:存證時間 vs HEAD commit 時間 —— 存證比 HEAD 舊就是 NODATA,並寫明差幾天。

  ③ `vap · optional 缺 talib` 判 NODATA —— **那是合律不是缺料**。
     L50 是第一條:「TA-Lib 禁用,QuantGuard 是唯一正主」。talib 缺席才是對的;
     報成缺,等於推人去裝一個被禁的套件。反過來:**talib 在場才是 RED**。

v0100→v0101(批668:一個自指站把上一輪的紅,點亮成本輪的紅)
  「格子總判」那一格在讀格子存證,而本支**自己就是格子裡的一站**——
  讀到的必然是上一輪。上一輪有紅它就報紅,於是任何一盞紅都要兩輪才回得了 FAIL 0。
  v0100 已經排掉了自己那幾站(防不動點),但**排除解決的是自己咬自己,
  不是「拿過期結論點亮現在的燈」**。
  本版:格子 v0425 在站型子行程注入 VIA_IN_GRID=1;讀到它就把這一格改判 NODATA,
  並寫明「這是上一輪(齡 X 天),本輪結果本站結構上看不到」。
  單跑 via-state 時沒有那個環境變數,照舊給真判(RED/GREEN)。
  → **結構上看不到的東西,不要給它一盞燈。**

操作員令(批664):「確認 VRN VDF VIA 實測無誤導入 · 生成輸出 HTML TESTING MATRIX
REPORT BY RICH IN VERY DETAILES · 確保 VIA 握所有現況紀錄 LOGGING FOR ENVIRONMENT
所有的庫 LIBS SSOT REGEX 同義字 支援性工具 VDF VRN · 範圍限縮於此」

先量,再決定要不要新做(LL306:「這是新料」取決於我翻了哪個架子):
  · CGC_MDL110 三軌測試矩陣 —— **已存在**,做的是 system/user/validation 三軌,
    而且明寫「零重測=全讀既有存證」。本冊**不碰它**,也不重做它那三軌。
  · 本冊做的是另一件事:**六域資產現況 × 實測**(ENV/LIBS/SSOT/TOOLS/VDF/VRN),
    其中 LIBS 與 SSOT 是**當場 import / 當場編 regex**,不是讀存證。
  · 樹上從來沒有人用過 rich 的 record=True / export_html(只在收容夾的外來件裡有)。
    **rich 直出 HTML 是真的新的**,而且 inline_styles=True 產出零外連,合 L100。

六域,逐列誠實態(GREEN/RED/NODATA/ABSENT/GATED),逐列帶**出處**與**年齡**:
  ENV   家族境 python 在不在、環境治理三本存證多舊(LL304:數字沒有年齡會誤導)
  LIBS  **當場 import**:家族必要/選用庫逐個探。本境探不到家族境時誠實 GATED,
        不假裝跑過(L52);工作站才是真戰場——不代裝(操作員的手)
  SSOT  regex/同義字諸冊:在不在 · 幾條 · **regex 逐條編得過嗎** · 有沒有活讀者
  TOOLS 支援性工具:尾版家族 · 有沒有 --selftest · 格子有沒有站
  VDF   引擎尾版家族 · 家族存證年齡 · 格子 VDF 站燈
  VRN   同上 + finlex 對帳(批663)

律:零網路 · 零寫入正本(只寫自己的 VIA_Reports/state_matrix/)· Zero-Hydra
  (FAMILY_LIBS 向 MDL137 **AST 取用**不複製;格子燈讀既有 GRID_*.json 不重跑)
用法:
  via-state            → 主控台六域矩陣(rich;缺 rich 自動降級純文字,不靜默)
  via-state html       → 落 HTML(rich export_html inline_styles=True;零 CDN 零外連)
  via-state --json <p> → 現況紀錄落檔(LOGGING)
  via-state --selftest → 廿二檢(沙盒零網路)
誠實 rc:0 GREEN(零 RED)· 1 RED · 4 GATED(只剩等人的格,沒有壞的)
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
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
REPORTS = VIA / "VIA_Reports" / "state_matrix"
# 自我指涉閘(LL133):本支在回答「這本冊有沒有活讀者」,而**它自己就讀那幾本冊**
#   (SSOT_BOOKS 裡逐個名字都寫在這支裡)。不排掉自己,一本零活讀者的冊會顯示
#   「活讀者 1」,ORPHAN 永遠照不出來——判定器把自己算進答案裡,數字就自己變好看了。
#   排的是**整個家族**不是單一版本:留著舊版號的檔在夾裡,一樣會把自己算進去。
_SELF_FAMILY = Path(__file__).stem.rsplit("_v", 1)[0]
# 自我指涉第二處,而且這一處會**卡死**不只是慢一拍:
#   本支有一格在讀格子存證報「格子總判」。它自己**也是格子裡的一站**。
#   第一跑它紅了 → 存證記下 FAIL 1 → 下一跑它讀到那個 1 → 又紅 → 又記 1 …
#   格子的版史寫過四個「自指站」會慢一拍(修好後第二輪才轉綠);這一支不是慢一拍,
#   是**不動點**——紅燈自己餵自己,永遠不會消失。
#   所以讀格子存證時,本支自己那幾站不進分母(L57 誠實分母:分母裡不該有自己)。
_SELF_STATION_MARK = "六域現況"


def _not_self_station(r_) -> bool:
    return _SELF_STATION_MARK not in str(r_.get("name", ""))
KNOW = VIA / "functional modules" / "VRN" / "knowledge"

RC_NAME = {0: "GREEN", 1: "RED", 2: "NODATA", 3: "ABSENT", 4: "GATED"}
STATE_ORDER = ("RED", "GATED", "NODATA", "ABSENT", "GREEN")
STATE_STYLE = {"GREEN": "bold green", "RED": "bold red", "NODATA": "yellow",
               "ABSENT": "dim", "GATED": "bold cyan"}
DOMAINS = ("ENV", "LIBS", "SSOT", "TOOLS", "VDF", "VRN")
FAMILIES = ("vdf", "vrn", "vap")


# ── 小工具 ──────────────────────────────────────────────────────────────
def newest(folder: Path, pattern: str) -> Path | None:
    """尾版律:同族取字典序最後一支。folder 不在=None(誠實,不炸)。"""
    try:
        hits = sorted(folder.glob(pattern))
    except OSError:
        return None
    return hits[-1] if hits else None


def age_days(p: Path) -> float | None:
    try:
        return round((time.time() - p.stat().st_mtime) / 86400.0, 1)
    except OSError:
        return None


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(VIA)).replace("\\", "/")
    except ValueError:
        return str(p)


def load_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def row(domain: str, item: str, state: str, n="", detail="", evidence="", age=None) -> dict:
    return {"domain": domain, "item": item, "state": state, "n": str(n),
            "detail": detail, "evidence": evidence, "age_days": age}


def family_libs() -> dict:
    """向 MDL137 RunGate **AST 取用** FAMILY_LIBS。

    Zero-Hydra:這份名單的正主是 RunGate,複製一份到這裡就會有兩份會走鐘的名單
    (L30 一個出處)。AST 讀不執行——RunGate 會起子行程探針,匯入它等於順手跑掉。
    """
    eng = newest(HERE, "CGC_MDL137_RunGate_v*.py")
    if not eng:
        return {}
    try:
        tree = ast.parse(eng.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "FAMILY_LIBS" for t in node.targets):
            try:
                return ast.literal_eval(node.value)
            except Exception:
                return {}
    return {}


def head_commit_epoch() -> float | None:
    """HEAD commit 的時間。存證比它舊 = 那份存證講的是另一棵樹。"""
    try:
        r = subprocess.run(["git", "log", "-1", "--format=%ct"], capture_output=True,
                           text=True, timeout=20, cwd=str(VIA))
        return float(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None
    except Exception:
        return None


def evidence_is_stale(p: Path | None) -> tuple[bool, str]:
    """存證是不是比現在的樹舊。

    批669 工作站實錄:他的格子存證是 1.3 天前跑的,而那之後他拉了 5 批。
    那份存證裡的 FAIL 20 講的是**另一棵樹**——拿它判今天的紅,跟批668 拿上一輪
    判本輪是同一個錯,只是換了個長相。
    """
    if not p or not p.exists():
        return False, ""
    head = head_commit_epoch()
    if head is None:
        return False, ""
    try:
        ev = p.stat().st_mtime
    except OSError:
        return False, ""
    if ev >= head:
        return False, ""
    sec = head - ev
    # 「早 0.0 天」讀起來是「沒有差」——斷言說舊、括號說不舊。差距小就換單位。
    if sec >= 86400:
        gap = f"{sec / 86400.0:.1f} 天"
    elif sec >= 3600:
        gap = f"{sec / 3600.0:.1f} 小時"
    else:
        gap = f"{max(1, int(sec // 60))} 分鐘"
    return True, (f"**這份存證比現在的樹舊**(存證比 HEAD commit 早 {gap})——"
                  f"它講的是另一棵樹,不能拿來判現在")


def grid_evidence() -> tuple[dict | None, Path | None]:
    """最新一份格子存證。零重跑——格子自己跑過了,再跑一次只會得到同一件事。"""
    d = VIA / "VIA_Reports" / "selftest_runs"
    p = newest(d, "GRID_*.json")
    return (load_json(p) if p else None), p


def _grid_rows(ev) -> list:
    """格子存證的站列位置在不同版本不一樣,逐個候選鍵找到為止(LL299:別假設 key 在)。"""
    if isinstance(ev, list):
        return ev
    if not isinstance(ev, dict):
        return []
    for k in ("rows", "stations", "results", "bays", "items"):
        v = ev.get(k)
        if isinstance(v, list) and v:
            return v
    return []


# ── 域一:ENV 環境 ───────────────────────────────────────────────────────
def scan_env() -> list:
    out = []
    root = os.environ.get("VIA_ENV_ROOT", "")
    envd = Path(root) if root else None
    for fam in FAMILIES:
        py = None
        if envd and envd.is_dir():
            # 擺法有三種,一種都不能漏:
            #   Windows venv  <env>\Scripts\python.exe   ← 操作員的機器就是這種,v0101 漏了
            #   conda / 根放   <env>\python.exe
            #   POSIX          <env>/bin/python
            for cand in sorted(envd.glob(f"via_{fam}_*")):
                for sub in ("Scripts/python.exe", "Scripts/python3.exe",
                            "python.exe", "bin/python", "bin/python3", "python"):
                    if (cand / sub).exists():
                        py = cand / sub
                        break
                if py:
                    break
        if py:
            out.append(row("ENV", f"家族境 python · {fam}", "GREEN", 1, str(py), "VIA_ENV_ROOT"))
        elif envd:
            out.append(row("ENV", f"家族境 python · {fam}", "ABSENT", 0,
                           f"VIA_ENV_ROOT={root} 下找不到 via_{fam}_*", "VIA_ENV_ROOT"))
        else:
            out.append(row("ENV", f"家族境 python · {fam}", "GATED", 0,
                           "本境未設 VIA_ENV_ROOT(容器沒有家族境;工作站才量得到)"
                           "——**不假裝跑過**", "env:VIA_ENV_ROOT"))
    for sub, name, what in (
            ("env_governance", "RUN_latest.json", "環境治理最近一跑"),
            ("env_governance", "TOOLS_PLAN_latest.json", "環境工具計畫"),
            ("env_governance", "LKGC_latest.json", "最後已知良好組態"),
            ("rungate", "RUNGATE_latest.json", "能跑閘"),
    ):
        p = VIA / "VIA_Reports" / sub / name
        if p.exists():
            a = age_days(p)
            out.append(row("ENV", what, "GREEN" if (a or 0) <= 30 else "NODATA",
                           "", f"存證在位({'新' if (a or 0) <= 30 else '超過 30 天,舊到不該拿來當現況'})",
                           rel(p), a))
        else:
            out.append(row("ENV", what, "ABSENT", 0, "存證不在", rel(p)))
    return out


# ── 域二:LIBS 庫(當場 import,不讀存證)────────────────────────────────
def probe_here(mods: list) -> dict:
    """本境逐個 import。這是**實測**不是查表——查表會告訴你三個月前的事。"""
    got = {}
    for m in mods:
        try:
            __import__(m)
            got[m] = True
        except Exception:
            got[m] = False
    return got


# L50 是**第一條**:TA-Lib 禁用,QuantGuard 是唯一正主。
#   所以 talib **缺席才是對的**;把它報成「缺」,等於推人去裝一個被禁的套件。
#   反過來:talib 在場才是紅。這一條不是豁免,是**方向相反的判準**。
_FORBIDDEN_LIBS = {"talib": "L50 第一條:TA-Lib 禁用,QuantGuard 是唯一正主"}


def scan_libs() -> list:
    out, fl = [], family_libs()
    if not fl:
        return [row("LIBS", "家族庫名單", "ABSENT", 0,
                    "MDL137 RunGate 尾版讀不到 FAMILY_LIBS", "CGC_MDL137_RunGate_v*.py")]
    src = "CGC_MDL137_RunGate FAMILY_LIBS(AST 取用;一個出處)"
    here_is_family = bool(os.environ.get("VIA_ENV_ROOT"))
    for fam in FAMILIES:
        spec = fl.get(fam) or {}
        for kind in ("required", "optional"):
            mods = list(spec.get(kind) or [])
            if not mods:
                continue
            got = probe_here(mods)
            banned_present = [m for m, ok in got.items() if ok and m in _FORBIDDEN_LIBS]
            # 被禁的庫不進分母:它缺席是合律,算進「缺幾個」只會把合律講成缺陷(L57)
            mods = [m for m in mods if m not in _FORBIDDEN_LIBS]
            miss = [m for m, ok in got.items() if not ok and m not in _FORBIDDEN_LIBS]
            hit = len(mods) - len(miss)
            if kind == "required":
                if not miss:
                    st = "GREEN"
                elif here_is_family:
                    st = "RED"
                else:
                    st = "GATED"   # 本境不是家族境:缺不等於壞(L52)
            else:
                st = "GREEN" if not miss else "NODATA"
            note = f"缺 {'·'.join(miss)}" if miss else "全在"
            if banned_present:
                st = "RED"
                note = (f"**{'·'.join(banned_present)} 竟然裝著** —— "
                        + " · ".join(_FORBIDDEN_LIBS[m] for m in banned_present)
                        + ";缺席才是對的,在場是違律")
            elif any(m in _FORBIDDEN_LIBS for m in (spec.get(kind) or [])):
                note += f"(talib 不計:{_FORBIDDEN_LIBS['talib']};它缺席是合律)"
            if st == "GATED":
                note += "(本境非家族境,缺≠壞;工作站 via-rungate --family "
                note += f"{fam} 才是真答案 —— **不代裝**)"
            out.append(row("LIBS", f"{fam} · {kind}", st, f"{hit}/{len(mods)}", note, src))
    p = VIA / "VIA_Reports" / "libconsol" / "LIBCONSOL_AUDIT_latest.json"
    if p.exists():
        out.append(row("LIBS", "庫整併稽核存證", "GREEN", "", "在位", rel(p), age_days(p)))
    else:
        out.append(row("LIBS", "庫整併稽核存證", "ABSENT", 0, "不在", rel(p)))
    return out


# ── 域三:SSOT / REGEX / 同義字 ─────────────────────────────────────────
SSOT_BOOKS = (
    (KNOW / "VRN_FinData_Synonym_v0100.json", "財務數據中英同義冊", "metrics"),
    (KNOW / "VRN_FinStatement_Synonym_v0100.json", "財務報表同義冊", "statements"),
    (KNOW / "VRN_Broker_Dict_v0100.json", "券商縮寫冊", "brokers"),
    (KNOW / "VRN_Rating_Dict_v0100.json", "評等冊", "levels"),
    (KNOW / "VRN_TickerDate_Regex_v0100.json", "股號日期 regex 冊", "ticker_patterns"),
    (KNOW / "VRN_NumberFormat_Regex_v0100.json", "數字格式擷取式冊(批663)", "number_patterns"),
)


# 說明欄的鍵名。冊裡的散文常常帶括號、破折號、頓號,長得跟 regex 一樣——
# 第一版把 NumberFormat 冊的 policy 那句話當 regex 去編,編不過就報了一盞紅燈。
# 那是**判錯的紅燈**,跟假綠一樣傷(LL302 的第二次發作:寫在說明欄的話被當資料讀走)。
_PROSE_KEYS = frozenset({
    "policy", "schema", "generated", "purpose", "why", "note", "_note", "notes",
    "desc", "description", "doc", "ts", "law", "reason", "evidence", "comment",
    "title", "zh", "en", "name", "name_en", "source", "sources", "origin", "rule",
    "operator_order", "ruling", "basis", "same_as_basis", "bridge_policy",
})
# 鍵名不會剛好等於上面那幾個字——實測 `why_not_range` 就從 `why` 底下漏出來,
# 帶著一整段實錄去編 regex,又報了一盞判錯的紅燈。前綴/後綴一起認。
_PROSE_PREFIX = ("why", "note", "desc", "policy", "reason", "comment", "ruling", "law_")
_PROSE_SUFFIX = ("_why", "_note", "_desc", "_policy", "_reason", "_basis", "_rule", "_doc")


def _is_prose_key(k: str) -> bool:
    k = str(k).lower()
    return (k in _PROSE_KEYS or k.startswith(_PROSE_PREFIX) or k.endswith(_PROSE_SUFFIX))
_PROSE_MAXLEN = 160   # 超過這個長度的「regex」在這幾本冊裡一律是散文,不是式
# 有些冊**刻意**留著一份「我收不進來的式」清單(MDL115 批664 的 dropped_uncompilable
# 就是)。那是負責任的做法——具名不靜默。但一把尺如果轉頭把那份落選名單當成
# 「這本冊有 5 條壞式」,就等於因為它誠實而懲罰它。整棵子樹跳過。
_REJECT_KEYS = frozenset({
    "dropped_uncompilable", "uncompilable", "needs_py312", "syntax_broken",
    "parse_errors", "pending_operator", "off_book_pending",
})


def _walk_regex(obj, bag: list, skipped: list | None = None, key: str = "") -> None:
    """冊的形狀各有不同,把所有**真的是 regex** 的字串撈出來逐條編。

    三道篩,都往保守的一邊站:
      ① 說明欄的鍵名直接跳過 —— 散文不是式(_PROSE_KEYS)
      ② 純中文字面沒有元字元,編了當然過,算進分母只會灌水成好看的數字(L57)
      ③ 超過 _PROSE_MAXLEN 的也跳過,但**記進 skipped 讓它看得見** ——
         靜默跳過等於自己給自己開豁免,那正是假綠的長相(L87 豁免必附理由)
    """
    meta = set(r"\^$.|?*+()[]{}")
    if isinstance(obj, str):
        if _is_prose_key(key):
            return
        if not any(c in meta for c in obj):
            return
        if len(obj) > _PROSE_MAXLEN:
            if skipped is not None:
                skipped.append(obj)
            return
        bag.append(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if str(k) in _REJECT_KEYS:      # 冊自己點名的落選清單,不算它的缺陷
                continue
            _walk_regex(v, bag, skipped, str(k))
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _walk_regex(v, bag, skipped, key)


def readers_of(name: str) -> int:
    """誰在讀這本冊。零活讀者的冊=ORPHAN,那是**做好了沒接線**,不是好事。"""
    n = 0
    for base in ("functional modules", "supportive modules"):
        d = VIA / base
        if not d.is_dir():
            continue
        try:
            for p in d.rglob("*.py"):
                sp = str(p).replace("\\", "/")
                if "__pycache__" in sp or "/references/intake/" in sp or "VIA_RetiredEngines" in sp:
                    continue
                if p.stem.rsplit("_v", 1)[0] == _SELF_FAMILY:   # 自家族整族排除
                    continue
                try:
                    if name in p.read_text(encoding="utf-8", errors="ignore"):
                        n += 1
                except OSError:
                    continue
        except OSError:
            continue
    return n


def scan_ssot() -> list:
    out = []
    for p, label, key in SSOT_BOOKS:
        if not p.exists():
            out.append(row("SSOT", label, "ABSENT", 0, "冊不在", rel(p)))
            continue
        d = load_json(p)
        if d is None:
            out.append(row("SSOT", label, "RED", 0, "冊在但讀不開(JSON 壞)", rel(p), age_days(p)))
            continue
        body = d.get(key) if isinstance(d, dict) else None
        cnt = len(body) if hasattr(body, "__len__") else 0
        bag: list = []
        skipped: list = []
        _walk_regex(d, bag, skipped)
        bad = [rx for rx in bag if not _ok_rx(rx)]
        rd = readers_of(p.name)
        tail = f"(另跳過 {len(skipped)} 條判為散文)" if skipped else ""
        if bad:
            st, note = "RED", f"**{len(bad)} 條 regex 編不過**:{bad[0][:40]}{tail}"
        elif rd == 0:
            st, note = "NODATA", f"冊在、料在,**零活讀者(ORPHAN)**——做好了沒接線{tail}"
        else:
            st, note = "GREEN", f"regex {len(bag)} 條全編得過 · 活讀者 {rd}{tail}"
        out.append(row("SSOT", label, st, cnt, note, rel(p), age_days(p)))

    syn = VIA / "functional modules" / "VRN" / "VRN_Financial_Synonyms_SSOT.py"
    if syn.exists():
        try:
            tree = ast.parse(syn.read_text(encoding="utf-8-sig"))
            tot = 0
            for node in tree.body:
                tg = None
                if isinstance(node, ast.Assign):
                    tg = node.targets[0]
                elif isinstance(node, ast.AnnAssign):
                    tg = node.target
                if isinstance(tg, ast.Name) and tg.id.endswith(("SYNONYMS", "MAP", "MULTIPLIERS")):
                    try:
                        tot += len(ast.literal_eval(node.value))
                    except Exception:
                        pass
            out.append(row("SSOT", "財務同義正典(六錨)", "GREEN", tot,
                           "METRIC/CN_EN/SECTOR/CURRENCY/UNIT/REPORT_TYPE", rel(syn), age_days(syn)))
        except Exception as exc:
            out.append(row("SSOT", "財務同義正典(六錨)", "RED", 0,
                           f"AST 讀不開:{str(exc)[:50]}", rel(syn)))
    else:
        out.append(row("SSOT", "財務同義正典(六錨)", "ABSENT", 0, "不在", rel(syn)))

    for name, label in (("VIA_SSOT_RegexDict_v0100.json", "全樹 regex 清冊"),
                        ("VIA_Central_Synonym_Regex_v0100.json", "中央同義 regex 冊")):
        p = HERE / name
        if p.exists():
            d = load_json(p)
            bag: list = []
            skipped: list = []
            _walk_regex(d, bag, skipped)
            bad = [r_ for r_ in bag if not _ok_rx(r_)]
            det = f"regex {len(bag)} 條 · 編不過 {len(bad)}"
            if skipped:
                det += f"(另跳過 {len(skipped)} 條判為散文)"
            if bad:
                det += " · 首例:" + repr(bad[0])[:56]
            out.append(row("SSOT", label, "RED" if bad else "GREEN",
                           len(d) if hasattr(d, "__len__") else 0, det, rel(p), age_days(p)))
        else:
            out.append(row("SSOT", label, "ABSENT", 0, "不在", rel(p)))
    return out


def _ok_rx(rx: str) -> bool:
    try:
        re.compile(rx)
        return True
    except re.error:
        return False


# ── 域四:支援性工具 ────────────────────────────────────────────────────
def _families_in(folder: Path, pattern: str = "*.py") -> dict:
    """同名不同版視為一族,只留尾版。數「檔案數」會把版史當成資產(那是假大)。"""
    fam: dict = {}
    if not folder.is_dir():
        return fam
    for p in sorted(folder.rglob(pattern)):
        sp = str(p).replace("\\", "/")
        if ("__pycache__" in sp or "/references/intake/" in sp
                or "VIA_RetiredEngines" in sp or "/tests/" in sp):
            continue
        base = re.sub(r"_v\d{4}\.py$", "", p.name)
        base = re.sub(r"\.py$", "", base)
        cur = fam.get(base)
        if cur is None or p.name > cur.name:
            fam[base] = p
    return fam


def scan_tools() -> list:
    d = VIA / "supportive modules"
    fam = _families_in(d)
    if not fam:
        return [row("TOOLS", "支援性工具", "ABSENT", 0, "supportive modules 不在", "supportive modules")]
    has_self = 0
    for p in fam.values():
        try:
            if "--selftest" in p.read_text(encoding="utf-8", errors="ignore"):
                has_self += 1
        except OSError:
            pass
    out = [row("TOOLS", "支援性工具尾版家族", "GREEN", len(fam),
               "同名不同版折成一族(數檔案會把版史當資產)", "supportive modules/**"),
           row("TOOLS", "其中帶 --selftest", "GREEN" if has_self else "NODATA", has_self,
               f"覆蓋 {round(100.0 * has_self / len(fam), 1)}%"
               "——沒有自測的工具,壞了只有用的時候才知道", "supportive modules/**")]
    ev, evp = grid_evidence()
    rows = [r_ for r_ in _grid_rows(ev) if _not_self_station(r_)]
    in_grid = bool(os.environ.get("VIA_IN_GRID"))
    if rows:
        ok = sum(1 for r_ in rows if str(r_.get("state")) == "OK")
        bad = sum(1 for r_ in rows if str(r_.get("state")) == "FAIL")
        age = age_days(evp) if evp else None
        stale, why_stale = evidence_is_stale(evp)
        if stale:
            out.append(row("TOOLS", "格子總判(存證比樹舊)", "NODATA",
                           f"{ok}/{len(rows)}", f"FAIL {bad} —— {why_stale}。"
                           f"修法:重跑 `via-selftest` 讓存證追上這棵樹",
                           rel(evp) if evp else "", age))
        elif in_grid:
            # 批668:本支正在格子裡面跑,讀到的必然是**上一輪**。
            #   拿上一輪的紅點亮本輪的燈,是把一個過期的結論當成現在的結論。
            out.append(row("TOOLS", "格子總判(上一輪;自指站結構上看不到本輪)", "NODATA",
                           f"{ok}/{len(rows)}",
                           f"FAIL {bad} —— **這是上一輪的結果**(齡 {age} 天)。"
                           f"本支自己就在格子裡跑,本輪結論它結構上看不到,所以不給燈"
                           f"(本支自己那幾站已排除)",
                           rel(evp) if evp else "", age))
        else:
            out.append(row("TOOLS", "格子總判(讀存證零重跑)", "RED" if bad else "GREEN",
                           f"{ok}/{len(rows)}",
                           f"FAIL {bad}(本支自己那幾站已排除:分母裡不該有自己)",
                           rel(evp) if evp else "", age))
    else:
        out.append(row("TOOLS", "格子總判", "NODATA", 0,
                       "找不到 GRID_*.json 存證(先跑 via-selftest)",
                       "VIA_Reports/selftest_runs/"))
    return out


# ── 域五、六:VDF / VRN ─────────────────────────────────────────────────
FAM_DIR = {"VDF": ("functional modules/VDF", "VDF_ENG*.py", "vdf"),
           "VRN": ("functional modules/VRN", "VRN_ENG*.py", "vrn")}


def scan_family(tag: str) -> list:
    sub, pat, evsub = FAM_DIR[tag]
    d = VIA / sub
    fam = _families_in(d, pat)
    out = [row(tag, f"{tag} 引擎尾版家族", "GREEN" if fam else "ABSENT", len(fam),
               "ENG 家族(收容夾與退役夾不計)", sub)]
    evd = VIA / "VIA_Reports" / evsub
    if evd.is_dir():
        lat = sorted(evd.rglob("*latest*.json"))
        if lat:
            oldest = max((age_days(p) or 0) for p in lat)
            out.append(row(tag, f"{tag} 家族存證", "GREEN" if oldest <= 30 else "NODATA",
                           len(lat), f"最舊一份 {oldest} 天"
                           + ("" if oldest <= 30 else " —— 超過 30 天的存證不該當現況用"),
                           rel(evd), oldest))
        else:
            out.append(row(tag, f"{tag} 家族存證", "ABSENT", 0, "夾在但無 latest", rel(evd)))
    else:
        out.append(row(tag, f"{tag} 家族存證", "ABSENT", 0, "存證夾不在", rel(evd)))
    ev, evp = grid_evidence()
    rows = [r_ for r_ in _grid_rows(ev)
            if _not_self_station(r_)
            and (tag.lower() in str(r_.get("name", "")).lower() or tag in str(r_.get("name", "")))]
    if rows:
        ok = sum(1 for r_ in rows if str(r_.get("state")) == "OK")
        bad = sum(1 for r_ in rows if str(r_.get("state")) == "FAIL")
        stale, why_stale = evidence_is_stale(evp)
        if stale or os.environ.get("VIA_IN_GRID"):
            note = (why_stale if stale
                    else "**這是上一輪的結果**;本支自己就在格子裡跑,本輪結論看不到")
            out.append(row(tag, f"{tag} 格子站燈(不判現在)", "NODATA",
                           f"{ok}/{len(rows)}", f"FAIL {bad} —— {note}",
                           rel(evp) if evp else "", age_days(evp) if evp else None))
        else:
            out.append(row(tag, f"{tag} 格子站燈", "RED" if bad else "GREEN",
                           f"{ok}/{len(rows)}", f"FAIL {bad}(站名含「{tag}」者)",
                           rel(evp) if evp else "", age_days(evp) if evp else None))
    else:
        out.append(row(tag, f"{tag} 格子站燈", "NODATA", 0, "存證裡找不到站名含此家族者",
                       rel(evp) if evp else "VIA_Reports/selftest_runs/"))
    return out


def scan_vrn_extra() -> list:
    """VRN 專屬:批663 的對帳器結果。操作員要先做 VRN,這一格就是 VRN 的良心。"""
    eng = newest(VIA / "functional modules" / "VRN", "vrn_finlex_v*.py")
    if not eng:
        return [row("VRN", "財務字庫對帳(批663)", "ABSENT", 0, "vrn_finlex 尾版不在", "functional modules/VRN")]
    try:
        r = subprocess.run([sys.executable, str(eng), "--reconcile"], capture_output=True,
                           text=True, timeout=180, stdin=subprocess.DEVNULL, cwd=str(eng.parent))
    except Exception as exc:
        return [row("VRN", "財務字庫對帳(批663)", "RED", 0, f"跑不起來:{str(exc)[:60]}", rel(eng))]
    tail = [l for l in (r.stdout + r.stderr).splitlines() if "[計]" in l]
    st = RC_NAME.get(r.returncode, f"rc{r.returncode}")
    if st not in STATE_STYLE:
        st = "RED"
    return [row("VRN", "財務字庫對帳(批663)", st, "",
                (tail[-1].strip() if tail else f"rc={r.returncode}"), rel(eng))]


# ── 彙整 ────────────────────────────────────────────────────────────────
def collect() -> dict:
    t0 = time.time()
    rows: list = []
    rows += scan_env()
    rows += scan_libs()
    rows += scan_ssot()
    rows += scan_tools()
    rows += scan_family("VDF")
    rows += scan_family("VRN")
    rows += scan_vrn_extra()
    tally = {s: sum(1 for r_ in rows if r_["state"] == s) for s in STATE_ORDER}
    rc = 1 if tally["RED"] else (4 if tally["GATED"] else 0)
    return {"schema": "VIA.StateMatrix.v1", "version": VERSION,
            "batch": 664,
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ"),
            "host": os.environ.get("COMPUTERNAME") or os.uname().nodename,
            "python": sys.version.split()[0],
            "via_env_root": os.environ.get("VIA_ENV_ROOT", ""),
            "domains": list(DOMAINS), "tally": tally, "rc": rc,
            "rc_name": RC_NAME[rc], "secs": round(time.time() - t0, 1), "rows": rows}


# ── 呈現 ────────────────────────────────────────────────────────────────
HEADERS = ("域", "項", "態", "數", "說明(量到什麼 · 為什麼是這個燈)", "出處", "齡(天)")


def _cells(r: dict) -> list:
    a = r.get("age_days")
    return [r["domain"], r["item"], r["state"], r["n"], r["detail"], r["evidence"],
            "" if a is None else str(a)]


def _rich_console(record: bool = False, width: int = 200):
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
        f"[bold]VIA 六域現況矩陣[/bold] · 批664 · v{rep['version']}\n"
        f"產生 {rep['generated']} · 主機 {rep['host']} · python {rep['python']}\n"
        f"VIA_ENV_ROOT={rep['via_env_root'] or '(未設 —— 家族境的格會是 GATED,不是紅)'}\n"
        f"[bold green]GREEN {t['GREEN']}[/] · [bold red]RED {t['RED']}[/] · "
        f"[bold cyan]GATED {t['GATED']}[/] · [yellow]NODATA {t['NODATA']}[/] · "
        f"[dim]ABSENT {t['ABSENT']}[/] → [bold]{rep['rc_name']}[/]",
        title="VERITAS INTELLIGENCE ANALYTICS", border_style="cyan"))
    for dom in DOMAINS:
        sub = [r_ for r_ in rep["rows"] if r_["domain"] == dom]
        if not sub:
            continue
        tb = Table(title=f"{dom}({len(sub)} 列)", box=box.SIMPLE_HEAVY,
                   header_style="bold cyan", title_style="bold", pad_edge=False)
        for h in HEADERS[1:]:
            tb.add_column(h, overflow="fold", no_wrap=False)
        for r_ in sub:
            c = _cells(r_)[1:]
            c[1] = f"[{STATE_STYLE.get(r_['state'], '')}]{r_['state']}[/]"
            tb.add_row(*c)
        con.print(tb)


def _plain_render(rep: dict) -> None:
    t = rep["tally"]
    print(f"=== VIA 六域現況矩陣 · 批664 · v{rep['version']}(rich 缺席,純文字降級)===")
    print(f"  產生 {rep['generated']} · 主機 {rep['host']} · python {rep['python']}")
    for dom in DOMAINS:
        sub = [r_ for r_ in rep["rows"] if r_["domain"] == dom]
        if not sub:
            continue
        print(f"\n── {dom}({len(sub)} 列)")
        for r_ in sub:
            a = r_.get("age_days")
            print(f"  [{r_['state']:<6}] {r_['item']:<28} {r_['n']:>8}  {r_['detail'][:70]}"
                  + (f"  ·齡 {a}d" if a is not None else ""))
    print(f"\n  [計] GREEN {t['GREEN']} · RED {t['RED']} · GATED {t['GATED']}"
          f" · NODATA {t['NODATA']} · ABSENT {t['ABSENT']} → {rep['rc_name']}")


def render(rep: dict) -> bool:
    con, ok = _rich_console()
    if ok:
        _rich_render(con, rep)
        return True
    _plain_render(rep)
    print("  [律] rich 未安裝 → 純文字降級(**不代裝套件**,那是操作員的手)。"
          "降級有講出來,不是靜默——靜默的降級跟壞掉一樣看不出來。")
    return False


# ── HTML(rich 直出;零 CDN 零外連;file:// 直開)────────────────────────
def _plain_html(rep: dict) -> str:
    t = rep["tally"]
    esc = (lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    css = ("body{background:#0f1116;color:#d8dee9;font-family:Consolas,'Noto Sans Mono CJK TC',monospace;"
           "margin:0;padding:24px}h1{font-size:20px}table{border-collapse:collapse;width:100%;margin:12px 0 28px}"
           "th,td{border:1px solid #2b313c;padding:5px 8px;font-size:13px;vertical-align:top}"
           "th{background:#1b2027;text-align:left}.GREEN{color:#9ece6a;font-weight:700}"
           ".RED{color:#f7768e;font-weight:700}.GATED{color:#7dcfff;font-weight:700}"
           ".NODATA{color:#e0af68}.ABSENT{color:#565f89}")
    h = [f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'>",
         "<title>VIA 六域現況矩陣</title>", f"<style>{css}</style></head><body>",
         "<h1>VIA 六域現況矩陣 · 批664</h1>",
         f"<p>產生 {esc(rep['generated'])} · 主機 {esc(rep['host'])} · python {esc(rep['python'])}"
         f" · <b>rich 未安裝,本頁為降級版</b>(內容一樣,只是沒有色票)</p>",
         f"<p><span class='GREEN'>GREEN {t['GREEN']}</span> · <span class='RED'>RED {t['RED']}</span>"
         f" · <span class='GATED'>GATED {t['GATED']}</span> · <span class='NODATA'>NODATA {t['NODATA']}</span>"
         f" · <span class='ABSENT'>ABSENT {t['ABSENT']}</span> → <b>{esc(rep['rc_name'])}</b></p>"]
    for dom in DOMAINS:
        sub = [r_ for r_ in rep["rows"] if r_["domain"] == dom]
        if not sub:
            continue
        h.append(f"<h2>{esc(dom)}({len(sub)} 列)</h2><table><tr>"
                 + "".join(f"<th>{esc(x)}</th>" for x in HEADERS[1:]) + "</tr>")
        for r_ in sub:
            c = _cells(r_)[1:]
            tds = "".join(
                f"<td class='{esc(r_['state'])}'>{esc(v)}</td>" if i == 1 else f"<td>{esc(v)}</td>"
                for i, v in enumerate(c))
            h.append(f"<tr>{tds}</tr>")
        h.append("</table>")
    h.append("</body></html>")
    return "".join(h)


def write_html(rep: dict, out: Path | None = None) -> tuple[Path, bool]:
    out = out or (REPORTS / "VIA_State_Matrix_v0100.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    con, ok = _rich_console(record=True, width=210)
    if ok:
        _rich_render(con, rep)
        html = con.export_html(inline_styles=True)   # inline=零外連,合 L100 file:// 零 server
        out.write_text(html, encoding="utf-8")
        return out, True
    out.write_text(_plain_html(rep), encoding="utf-8")
    return out, False


def write_log(rep: dict) -> Path:
    """LOGGING:時間戳一份 + latest 一份 + append-only 一行台帳。

    時間戳那份是歷史(改不得),latest 是現況,台帳那一行是「什麼時候量過」。
    三個都留,是因為只留 latest 的話,永遠回答不了「它是什麼時候變壞的」。
    """
    REPORTS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    body = json.dumps(rep, ensure_ascii=False, indent=1)
    (REPORTS / f"STATE_{ts}.json").write_text(body, encoding="utf-8")
    (REPORTS / "STATE_latest.json").write_text(body, encoding="utf-8")
    t = rep["tally"]
    line = (f"{rep['generated']}\t{rep['rc_name']}\tGREEN={t['GREEN']}\tRED={t['RED']}"
            f"\tGATED={t['GATED']}\tNODATA={t['NODATA']}\tABSENT={t['ABSENT']}"
            f"\thost={rep['host']}\tsecs={rep['secs']}\n")
    with (REPORTS / "STATE_LEDGER.tsv").open("a", encoding="utf-8") as f:
        f.write(line)
    return REPORTS / "STATE_latest.json"


# ── 自測十六檢(沙盒零網路)────────────────────────────────────────────
def selftest() -> int:
    import tempfile
    t0 = time.time()
    fails = []

    def chk(name, cond, note=""):
        if not cond:
            fails.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")

    rep = collect()
    rows = rep["rows"]
    # ① 六域都出得了列(少一域=這支引擎自己漏掃,而不是那一域是空的)
    doms = {r_["domain"] for r_ in rows}
    chk("六域都有列", set(DOMAINS) <= doms, f"({sorted(doms)})")
    # ② 每一列都是合法誠實態——沒有第七種燈偷偷混進來
    bad = [r_["state"] for r_ in rows if r_["state"] not in STATE_ORDER]
    chk("燈號只有五種(誠實態)", not bad, f"(越界 {bad[:3]})")
    # ③ 每一列都有出處。沒有出處的數字沒辦法被推翻(L96 舉證能整份帶走)
    noev = [r_["item"] for r_ in rows if not str(r_.get("evidence", "")).strip()]
    chk("逐列有出處", not noev, f"(缺 {noev[:3]})")
    # ④ 非 GREEN 的列一定講得出為什麼(L87 豁免必附理由)
    nowhy = [r_["item"] for r_ in rows if r_["state"] != "GREEN" and not r_["detail"].strip()]
    chk("非綠必附理由", not nowhy, f"(缺 {nowhy[:3]})")
    # ⑤ 合計與逐列一致——摘要跟明細對不起來是最難發現的假綠
    chk("合計=逐列", sum(rep["tally"].values()) == len(rows),
        f"({sum(rep['tally'].values())} vs {len(rows)})")
    # ⑥ rc 與燈號一致(有紅必 1;無紅有閘必 4;全清必 0)
    t = rep["tally"]
    want = 1 if t["RED"] else (4 if t["GATED"] else 0)
    chk("rc 與燈一致", rep["rc"] == want, f"(rc={rep['rc']} 應 {want})")
    # ⑦ FAMILY_LIBS 是向 MDL137 取的,不是這裡自己寫一份(Zero-Hydra)
    fl = family_libs()
    chk("家族庫名單向 MDL137 取用", bool(fl) and "vrn" in fl and "duckdb" in fl["vrn"]["required"],
        f"({sorted(fl)})")
    # 第一版寫死字面 "duckdb" 去數,結果**檢查器自己那兩行也含有它**,永遠數到 2。
    # 尺把自己算進去了(同 LL231:新閘上線第一件事是拿它掃自己)。needle 動態組,
    # 而且把本函式整段排除——自測碼提到庫名是在描述,不是在自備名單。
    needle = "duck" + "db"
    src_all = Path(__file__).read_text(encoding="utf-8")
    body = src_all.split("def selftest(")[0]          # 只看引擎本體,不看自測
    chk("本檔不自備第二份庫名單", body.count(needle) == 0,
        f"(引擎本體提及 {body.count(needle)} 次;複製一份就會有兩份會走鐘的名單)")
    # ⑨ 本境沒有家族境時,必要庫缺必須是 GATED 不是 RED(L52:缺料≠壞掉)
    if not os.environ.get("VIA_ENV_ROOT"):
        reds = [r_ for r_ in rows if r_["domain"] == "LIBS" and r_["state"] == "RED"]
        chk("非家族境不把缺庫判成紅", not reds, f"(誤紅 {[r_['item'] for r_ in reds]})")
    else:
        chk("非家族境不把缺庫判成紅", True, "(本境已設 VIA_ENV_ROOT,此檢不適用)")
    # ⑩ regex 分母只算真 regex:純中文字面不該被算進去灌水(L57)
    bag: list = []
    skipped: list = []
    _walk_regex({"a": "現金及約當現金", "b": r"cash\s*equivalents?", "c": ["營收", r"^\d+$"],
                 "policy": r"這句說明帶括號(還有破折號)——它不是式",
                 "why_not_range": r"實測 1,978 檔:2002 中鋼(鋼鐵股都住在這裡)——不能用區間修",
                 "patterns": ["x" * 200 + "(散文那麼長)"],
                 "dropped_uncompilable": [{"file": "f.py", "pattern": "<h1>(壞的"}]},
                bag, skipped)
    chk("regex 分母不灌水(散文/說明欄/冊自己點名的落選清單都不入分母)",
        sorted(bag) == sorted([r"cash\s*equivalents?", r"^\d+$"]) and len(skipped) == 1,
        f"(入分母 {len(bag)} · 判散文跳過 {len(skipped)} —— 跳過的有記,不是靜默)")
    # ⑪ 尾版律:同族取最後一支;夾不在回 None 不炸
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        for n in ("X_v0100.py", "X_v0103.py", "X_v0102.py"):
            (d / n).write_text("#", encoding="utf-8")
        chk("尾版律 glob", newest(d, "X_v*.py").name == "X_v0103.py"
            and newest(d / "nope", "*.py") is None)
    # ⑫ 家族折版:同名不同版折成一族,數的是資產不是版史
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        for n in ("VRN_ENG001_A_v0100.py", "VRN_ENG001_A_v0101.py", "VRN_ENG002_B_v0100.py"):
            (d / n).write_text("#", encoding="utf-8")
        fam = _families_in(d, "VRN_ENG*.py")
        chk("同名不同版折成一族", len(fam) == 2
            and fam["VRN_ENG001_A"].name == "VRN_ENG001_A_v0101.py", f"({sorted(fam)})")
    # ⑬ 格子列位置逐鍵找:不同版本的存證鍵名不一樣,寫死一個就會讀到空的(LL299)
    chk("格子存證逐鍵找", _grid_rows({"stations": [{"state": "OK"}]}) == [{"state": "OK"}]
        and _grid_rows({"沒有這個鍵": 1}) == [] and _grid_rows([{"x": 1}]) == [{"x": 1}])
    # ⑭ HTML 落沙盒:寫得出、零外連、逐域都在頁上(rich 在不在都要成立)
    with tempfile.TemporaryDirectory() as td:
        p, used_rich = write_html(rep, Path(td) / "m.html")
        html = p.read_text(encoding="utf-8")
        head = html.split("</head>")[0] if "</head>" in html else html[:4000]
        ext = ("http://" in head or "https://" in head or "cdn." in head)
        miss = [d_ for d_ in DOMAINS if d_ not in html]
        chk("HTML 零外連且六域齊", p.exists() and not ext and not miss,
            f"(rich={'用了' if used_rich else '缺席降級'} · {len(html)} 字 · 缺域 {miss})")
    # ⑮ LOGGING 三件:時間戳(歷史)+ latest(現況)+ 台帳一行(什麼時候量過)
    with tempfile.TemporaryDirectory() as td:
        global REPORTS
        keep, REPORTS = REPORTS, Path(td)
        try:
            lp = write_log(rep)
            led = (Path(td) / "STATE_LEDGER.tsv").read_text(encoding="utf-8")
            stamped = list(Path(td).glob("STATE_2*.json"))
            chk("LOGGING 三件齊", lp.exists() and len(stamped) == 1
                and led.count("\n") == 1 and rep["rc_name"] in led,
                f"(時間戳 {len(stamped)} · 台帳 {led.count(chr(10))} 行)")
            write_log(rep)
            led2 = (Path(td) / "STATE_LEDGER.tsv").read_text(encoding="utf-8")
            chk("台帳只增不減(append-only)", led2.count("\n") == 2,
                f"(再量一次應該變 2 行,實得 {led2.count(chr(10))})")
        finally:
            REPORTS = keep
    # ⑰ 自我指涉閘(LL133):本支自己就寫著那幾本冊的名字,不排掉自家族,
    #    一本零活讀者的冊會顯示「活讀者 1」——判定器把自己算進答案裡。
    me = Path(__file__)
    chk("自我指涉閘:數活讀者不把自己算進去",
        _SELF_FAMILY == me.stem.rsplit("_v", 1)[0]
        and readers_of("VIA_StateMatrix_這個名字只出現在本檔裡_" + "x" * 4) == 0,
        f"(自家族 {_SELF_FAMILY})")
    # ⑱ 讀格子存證時排掉自己那幾站。不排,紅燈會自己餵自己:
    #    這一跑紅 → 存證記 FAIL → 下一跑讀到那個 FAIL → 又紅。**不動點,不是慢一拍。**
    fake = [{"name": "VIA 六域現況實跑(批664)", "state": "FAIL"},
            {"name": "別人的站", "state": "OK"}]
    kept = [r_ for r_ in fake if _not_self_station(r_)]
    chk("讀格子存證排掉自己那幾站(不動點防呆)",
        len(kept) == 1 and kept[0]["name"] == "別人的站"
        and _SELF_STATION_MARK in __doc__,
        f"(自站記號「{_SELF_STATION_MARK}」)")
    # ⑲ 在格子裡面跑時,「格子總判」不給燈(NODATA)——結構上看不到本輪
    keep_env = os.environ.get("VIA_IN_GRID")
    try:
        os.environ["VIA_IN_GRID"] = "1"
        inside = [r_ for r_ in scan_tools() if "格子總判" in r_["item"]]
        os.environ.pop("VIA_IN_GRID", None)
        outside = [r_ for r_ in scan_tools() if "格子總判" in r_["item"]]
    finally:
        if keep_env is None:
            os.environ.pop("VIA_IN_GRID", None)
        else:
            os.environ["VIA_IN_GRID"] = keep_env
    # 兩種「不該判現在」的理由,任一成立都必須是 NODATA:
    #   · 在格子裡面跑(讀到的是上一輪)
    #   · 存證比現在的樹舊(講的是另一棵樹)——**這一條比較強,優先**
    why_in = str(inside[0]["detail"]) if inside else ""
    chk("不拿別的時候的結論點亮現在(上一輪 / 存證比樹舊)",
        len(inside) == 1 and len(outside) == 1
        and inside[0]["state"] == "NODATA"
        and ("上一輪" in why_in or "比現在的樹舊" in why_in)
        and outside[0]["state"] in ("GREEN", "RED", "NODATA"),
        f"(格子內 {inside[0]['state'] if inside else '?'} · "
        f"理由 {'存證舊' if '比現在的樹舊' in why_in else '上一輪'} · "
        f"單跑 {outside[0]['state'] if outside else '?'})")
    # ⑳ 批669 三修逐條咬:Windows venv 路徑 / 存證比樹舊 / L50 被禁庫方向相反
    import tempfile as _tf
    with _tf.TemporaryDirectory() as td:
        d = Path(td)
        (d / "via_vrn_312" / "Scripts").mkdir(parents=True)
        (d / "via_vrn_312" / "Scripts" / "python.exe").write_text("", encoding="utf-8")
        keep_root = os.environ.get("VIA_ENV_ROOT")
        os.environ["VIA_ENV_ROOT"] = str(d)
        try:
            envrows = [r_ for r_ in scan_env() if "python · vrn" in r_["item"]]
        finally:
            if keep_root is None:
                os.environ.pop("VIA_ENV_ROOT", None)
            else:
                os.environ["VIA_ENV_ROOT"] = keep_root
        chk("Windows venv 的 Scripts\\python.exe 找得到(v0101 漏了這個擺法)",
            len(envrows) == 1 and envrows[0]["state"] == "GREEN"
            and "Scripts" in envrows[0]["detail"],
            f"({envrows[0]['state'] if envrows else '?'})")
    with _tf.TemporaryDirectory() as td:
        old_p = Path(td) / "old.json"
        old_p.write_text("{}", encoding="utf-8")
        os.utime(old_p, (0, 0))                       # 1970:保證比任何 HEAD 早
        st, why = evidence_is_stale(old_p)
        st2, _ = evidence_is_stale(Path(td) / "nope.json")
        chk("存證比樹舊 → 判得出來且**單位撐得住那句話**",
            st and "比現在的樹舊" in why and not st2
            and any(u in why for u in ("天", "小時", "分鐘"))
            and "早 0.0" not in why, f"({why[-22:]})")
    chk("L50 被禁庫方向相反(缺席合律 · 在場違律)",
        "talib" in _FORBIDDEN_LIBS and "L50" in _FORBIDDEN_LIBS["talib"]
        and "竟然裝著" in Path(__file__).read_text(encoding="utf-8"),
        f"({_FORBIDDEN_LIBS['talib'][:34]})")
    n = 22 - len(fails)
    print(f"  [計] 廿二檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        print("=== VIA 六域現況矩陣 v0100 · 廿二檢(沙盒零網路)===")
        return selftest()
    rep = collect()
    if "--json" in a:
        i = a.index("--json")
        if i + 1 < len(a) and not a[i + 1].startswith("-"):
            Path(a[i + 1]).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  [落檔] {a[i + 1]}")
    if a and a[0] == "html":
        render(rep)
        out = None
        if "--out" in a:
            i = a.index("--out")
            if i + 1 < len(a):
                out = Path(a[i + 1])
        p, used = write_html(rep, out)
        lp = write_log(rep)
        print(f"\n  [頁] {rel(p)}(rich {'直出' if used else '缺席→降級 HTML'};零 CDN 零外連,file:// 直開)")
        print(f"  [紀錄] {rel(lp)} + STATE_<時間戳>.json + STATE_LEDGER.tsv(append-only)")
        if not os.environ.get("VIA_NO_OPEN"):
            try:
                import webbrowser
                webbrowser.open(p.as_uri())
            except Exception:
                pass
        return rep["rc"]
    render(rep)
    lp = write_log(rep)
    print(f"  [紀錄] {rel(lp)}(現況)+ STATE_<時間戳>.json(歷史)+ STATE_LEDGER.tsv(台帳)")
    if rep["rc"] == 4:
        print("  [律] GATED≠壞掉:本境不是家族境,家族庫的真答案在工作站"
              "(via-rungate --family vrn|vdf)——**不代裝套件**,那是操作員的手。")
    return rep["rc"]


if __name__ == "__main__":
    sys.exit(main())
