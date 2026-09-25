#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL187_ModuleChangeKillGate v0101 — 模組更新/修正的把關擊斃閘(批736;v0101 側線第十六段加許可冊)

v0100→v0101(側線 2026-09-25 第十六段,操作員令「NO TA-LIBS ALLOWED REMOVE ALL TAL-LIB」):
  **擊斃閘要能分辨「AI 私改」與「操作員下令的改」,而且只能靠位元分辨,不能靠說詞。**
  拔 TA-Lib 必然要動不可動清單上的 VeritasCeleritas.py(KILL-04)、刪帶 talib 的舊版 v1140(KILL-02)、
  拔 .ps1 裡的 talib 接線(KILL-05)——三條都是「要操作員逐次許可」的條款,可是 v0100 **沒有許可這個東西**,
  於是操作員親口下令的改動跟 AI 私改一樣被擊斃,閘只剩兩條路:關掉它,或不照令辦。兩條都錯。
  加一本許可冊 VIA_ModuleChange_Permits_v*.json(冊在 registry/,判的是 cwd 底下那一本):
    ①只有 KILL-02/04/05 可以許可(PERMITTABLE)——語法、正本、L50、同意閘、自測、檢號、留痕、基線時效
      **沒有許可這回事**;冊上列了也只記債、照殺
    ②許可釘**位元**:modify 要 sha256 完全相同、delete 要檔真的不在——許可之後再動一個位元,照殺
    ③每筆要有 ruled_by / ruling / date(誰、原話、哪天),缺一樣就不算許可
    ④冊讀不到 = 沒有許可 = 照常擊斃(fail-closed);被許可的件數照印 [許可],不藏進「全過」裡

操作員令:「更新模組或修正模組都要有嚴格的把關擊斃機制」。

**擊斃 ≠ 報告。** 本樹已經有一整排會「報」的閘;報了沒人擋,改動照樣進得去。
這一支只做一件事:拿一組**改動過的檔**去對十條擊斃條款,中一條就 rc=1,
而且印出位置、犯的是哪一條律、下一步怎麼辦。rc=1 就是擊斃,呼叫端照 rc 辦事。

**十條擊斃條款**(每一條背後都有一筆已經付過的學費,不是憑空想出來的):
    KILL-01 語法      改動過的 .py 必須 ast.parse 得過(批727:寫壞過一次,靠眼睛沒看出來)
    KILL-02 尾版律    出了新 _vNNNN,同名的**舊版必須一個位元都沒動**(只增不減)
    KILL-03 正本      references/intake/ 底下一個位元都不准改(正本零觸碰)
    KILL-04 不可動    批345 VeritasCeleritas/VeritasAegisNexus · 金融機構 SSOT(READ_ONLY)
    KILL-05 L70       .ps1 未經操作員逐次許可不得改(AI 這一側一律擊斃)
    KILL-06 L50       新增行不得 import talib / 呼叫 talib.(QuantGuard 是唯一正主)
    KILL-07 同意閘    新增行不得把 VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 設成放行值,
                      不得寫死金鑰(**AI 永不代設**;那是操作員的手)
    KILL-08 自測      改動過的引擎要有 --selftest,而且 rc 必須誠實(0/2/3/5),
                      不准 traceback、不准 rc1 還往下走
    KILL-09 檢號      同一檔的自測檢號不得**新增**撞號(既有撞號記債不擊斃=棘輪)
    KILL-10 翻令留痕  改動刪掉了既有的 chk 檢名 = 動到釘住的合約,
                      檔內必須留得出痕(取代批/裁示/ruled_by),否則擊斃(LL90)

**這道閘 fail-closed。** 量不到就不准說 PASS ——
量不到的時候回 ABSENT(rc3)或 NODATA(rc2),**永遠不回 0**。
本倉已經有一個 fail-open 的同意閘在單子上(#67:else 分支把閘開成 YES),
一道「出事就放行」的閘,比沒有閘更糟:它會讓人以為有人在看。

律:唯讀(只讀檔、只跑 git 讀指令,不寫任何檔)· 零網路 · 不代設同意閘。
用法:python3 CGC_MDL187_ModuleChangeKillGate_v0101.py [--base <ref>] [--path <檔>…] [--json]
      python3 CGC_MDL187_ModuleChangeKillGate_v0101.py --selftest
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
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ENGINE_ID = "CGC_MDL187_ModuleChangeKillGate"
VERSION = "v0101"
BATCH = "批736 · 許可冊 側線第十六段"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ROOT = VIA.parent

#: 擊斃條款表。**條款寫在這裡一份**,render / selftest / judge 都讀這一份——
#:   抄第二份就是第二顆會漂移的頭(LL297 同族),而且下次只改一邊。
CLAUSES = {
    "KILL-01": ("語法", "改動過的 .py 必須 ast.parse 得過",
                "照行號去修;修完再跑一次本閘"),
    "KILL-02": ("尾版律", "出了新 _vNNNN,同名舊版必須一個位元都沒動",
                "把舊版還原(git checkout <舊版檔>),改動只留在新版"),
    "KILL-03": ("正本零觸碰", "references/intake/ 底下不准改",
                "把正本還原;要改就在樹上另開衍生檔,不動收容件"),
    "KILL-04": ("不可動律", "批345 Celeritas/AegisNexus · 金融機構 SSOT(READ_ONLY)",
                "把檔還原;要動這幾支得操作員逐次許可"),
    "KILL-05": ("L70", ".ps1 未經操作員逐次許可不得改",
                "把 .ps1 還原,改動寫成一段給操作員貼的文字"),
    "KILL-06": ("L50", "新增行不得 import talib / 呼叫 talib.",
                "改走 QuantGuard(唯一正主)"),
    "KILL-07": ("不代設同意閘", "新增行不得把同意閘設成放行值、不得寫死金鑰",
                "把設值拿掉;同意閘是操作員的手,列成一段讓他自己貼"),
    "KILL-08": ("自測在位", "改動過的引擎要有 --selftest 且 rc 誠實(0/2/3/5)",
                "補自測,或把 rc 改成誠實態;traceback 不是紅燈是壞掉"),
    "KILL-09": ("檢號", "同一檔的自測檢號不得**新增**撞號",
                "把新加的檢換一個沒人用的號(既有撞號記債不擊斃)"),
    "KILL-10": ("翻令留痕", "刪掉既有 chk 檢名=動到釘住的合約,檔內要留得出痕",
                "在檔裡寫明取代了哪一批的裁示、為什麼(LL90 留痕義務)"),
    "KILL-11": ("基線時效", "新出的 _vNNNN 必須接在**預設分支當下的尾版**之後",
                "先把分支跟上預設分支,讀那一版,再重編號續上去"),
}

#: KILL-11 要比對的預設分支參照。**這一條是批736 自己付的學費。**
#:   本批在一個落後 89 個 commit 的基線上做完一整批,才發現:
#:   預設分支上早就有同名的 `_v0137`(內容完全不同,是別的批做的),而且 `_v0138` 也在了;
#:   我要的功能,預設分支在批729 就交付了,批730 還拿真料把它修得更對。
#:   **十條條款一條都沒攔住它**——因為它們全部只看「這次改了什麼」,
#:   沒有一條問「你改的是不是當下那一版」。基線錯了,改得再乾淨也是廢的。
BASE_REFS = ("origin/main", "origin/master", "main", "master")

#: KILL-04 的點名清單。用**檔名**比對(不釘路徑),因為同名檔在樹上不只一處。
IMMUTABLE_NAMES = ("VeritasCeleritas.py", "VeritasAegisNexus.py",
                   "VIA_Financial_Institution_SSOT_v0100.py")

#: 批647 例外:VIA_HTML_UI/ 是位元精確的正本,由它自己的 manifest.json 把關,
#:   不受本閘 KILL-02 的尾版律管(它根本不用版號)。
EXEMPT_PREFIXES = ("VeritasIntelligenceAnalytics/VIA_HTML_UI/",)

_VER_RX = re.compile(r"^(?P<stem>.+)_v(?P<num>\d{4})\.(?P<ext>py|json|ps1)$")
#: KILL-06/07 的字面。**拼接寫**——不拼接的話這支自己的原始碼就會咬中自己
#:   (LL384:字面禁用檢要先剝註解,而且檢自己不能含那個字面)。
#: Codex 審查(PR #121 P2)實測漏判:`from ta·lib import RSI` 這個常見寫法
#:   既不含 `import ta·lib` 也不含 `ta·lib.`,舊式三條分支一條都不中。
_TALIB_RX = re.compile(r"^\+.*(?:import\s+ta" + r"lib\b|from\s+ta"
                       + r"lib\b|\bta" + r"lib\s*\.)")
_CONSENT_KEYS = ("VIA_NET" + "_CONSENT", "VIA_SCRAPE" + "_CONSENT")
#: Codex 審查(PR #121 P1)實測漏判三種:本樹最常見的
#:   `os.environ["同意閘"] = "YES"`(鍵後面先是引號再是 `]`)、
#:   `{"同意閘": "YES"}`(冒號)、`setdefault("同意閘", "YES")`(逗號)。
#:   舊式要求 `]` 緊貼鍵,於是**最該擋的那個寫法正好過**——
#:   一條在最常見寫法上漏判的條款,等於只在罕見寫法上生效。
#:   讀取比較(`== "YES"`)不是賦值,不得誤判。
_CONSENT_GRANT_RX = re.compile(
    r"^\+.*(?:" + "|".join(_CONSENT_KEYS) + r")[\"']?\s*\]?\s*(?:=|:|,)\s*[\"']?"
    r"(?:YES|yes|true|True|GRANTED|granted)\b")
_APIKEY_RX = re.compile(
    r"^\+.*(?:API_KEY|APIKEY|SECRET_KEY|ACCESS_TOKEN)\s*=\s*[\"'][A-Za-z0-9_\-]{16,}[\"']")
_CHK_RX = re.compile(r"""chk\(\s*f?["']([^\s"']+)""")
#: KILL-10 的留痕證據。Codex 審查(PR #121 P1)實測:舊式拿
#:   `取代批|裁示|ruled_by|操作員令` 去搜**整份檔**,而 `操作員令` 是本樹表頭的常見詞——
#:   於是任何一支表頭有那三個字的引擎,刪掉釘住的 chk 都自動放行,KILL-10 實質失效。
#:   改兩件事:①證據只認**這次的新增行** ②要點得出批號或 ruled_by。
_TRACE_RX = re.compile(
    r"取代批\s*\d+|supersedes?\b|ruled_by"
    r"|(?:裁示|操作員令|裁定)[^\n]{0,60}?批\s*\d+"
    r"|批\s*\d+[^\n]{0,60}?(?:裁示|操作員令|裁定)")

HONEST_RCS = (0, 2, 3, 5)      # 0綠 2缺料 3缺席 5跳過;1=紅 不算誠實態(它就是擊斃)

#: v0101 許可冊。**只有這三條可以許可**——它們的條款本文就寫著「要操作員逐次許可」。
#:   其餘八條(語法/正本/L50/同意閘/自測/檢號/留痕/基線時效)沒有許可這回事:
#:   操作員也不會下令「請引入 TA-Lib」或「請把同意閘代設成 YES」,冊上列了只記債、照殺。
PERMITTABLE = ("KILL-02", "KILL-04", "KILL-05")
#: 許可冊相對 cwd 的所在(取尾版)。沙盒 cwd 底下沒有這本 = 沒有許可(fail-closed)。
PERMITS_DIR = ("VeritasIntelligenceAnalytics", "supportive modules", "registry")
PERMITS_GLOB = "VIA_ModuleChange_Permits_v*.json"


def _sha256(fp: Path) -> str | None:
    try:
        return hashlib.sha256(fp.read_bytes()).hexdigest()
    except Exception:
        return None                      # 讀不到 → 比不上任何許可 → 照殺


def load_permits(cwd: Path, permits_path: Path | None = None) -> tuple[list[dict], list[str]]:
    """讀許可冊。回 (合格許可, 問題清單)。**讀不到就沒有許可**——問題照記,擊斃照常。"""
    if permits_path is None:
        d = cwd.joinpath(*PERMITS_DIR)
        cands = sorted(d.glob(PERMITS_GLOB)) if d.is_dir() else []
        if not cands:
            return [], []                # 沒有冊 = 沒有許可(不是問題,是常態)
        permits_path = cands[-1]
    try:
        book = json.loads(Path(permits_path).read_text(encoding="utf-8"))
        rows = book["permits"]
        assert isinstance(rows, list)
    except Exception as exc:
        return [], [f"許可冊讀不到({Path(permits_path).name}):{type(exc).__name__}"
                    "——沒有許可,照常擊斃"]
    good, bad = [], []
    for i, p in enumerate(rows):
        if not isinstance(p, dict):
            bad.append(f"許可 #{i} 不是物件,略過")
            continue
        pid = p.get("id") or f"#{i}"
        if p.get("code") not in PERMITTABLE:
            bad.append(f"許可 {pid} 列的是 {p.get('code')}:只有 {'/'.join(PERMITTABLE)} 可以許可,略過")
            continue
        if not all(str(p.get(k) or "").strip() for k in ("path", "ruled_by", "ruling", "date")):
            bad.append(f"許可 {pid} 缺 path/ruled_by/ruling/date(誰、原話、哪天),不算許可")
            continue
        if p.get("kind") == "modify" and not re.fullmatch(r"[0-9a-f]{64}", str(p.get("sha256") or "")):
            bad.append(f"許可 {pid} 是 modify 卻沒釘 sha256(許可只放行那一份位元),不算許可")
            continue
        if p.get("kind") not in ("modify", "delete"):
            bad.append(f"許可 {pid} 的 kind={p.get('kind')!r} 不認得(只認 modify/delete),不算許可")
            continue
        good.append(p)
    return good, bad


def permit_holds(p: dict, cwd: Path, path: str) -> tuple[bool, str]:
    """這一筆許可對這個檔**此刻的位元**成不成立。"""
    fp = cwd / path
    if p["kind"] == "delete":
        return (not fp.exists(), "許可的是刪除,檔卻還在")
    if not fp.is_file():
        return (False, "許可的是修改,檔卻不在")
    got = _sha256(fp)
    return (got == p["sha256"],
            f"位元與許可冊釘的不同(冊 {p['sha256'][:12]}… · 現 {(got or '讀不到')[:12]}…)"
            "——許可只放行那一份位元,之後再動一個位元都照殺")


# ── git 讀指令(只讀;任何一個失敗都往 fail-closed 走)────────────────
def _git(args: list[str], cwd: Path | None = None) -> tuple[int, str]:
    try:
        p = subprocess.run(["git"] + args, cwd=str(cwd or ROOT),
                           capture_output=True, text=True, timeout=90)
        return p.returncode, p.stdout
    except Exception as exc:                 # git 不在/逾時 → 量不到,不是通過
        return 127, f"{exc}"


def changed_files(base: str | None = None, cwd: Path | None = None) -> tuple[list[str], str]:
    """哪些檔被改了。回 (檔清單, 出處);量不到回 ([], 原因)。

    四個來源合起來看,因為「改動」在四個地方都可能:工作區、暫存區、**未追蹤**、
    以及相對於 base 的已提交差異。只看其中一個,就會有一種改動永遠躲過這道閘。

    第四個來源是本閘自測當場咬出來的:`git diff` **從來不列未追蹤檔**,
    於是「新出一個 _vNNNN」「整支全新的模組」在 `git add` 之前一個都不會被看到——
    那偏偏正是這道閘最該攔的一類。漏在閘自己身上,不在夾具。
    """
    rcs = []
    got: list[str] = []
    for args, why in ((["diff", "--name-only"], "工作區"),
                      (["diff", "--cached", "--name-only"], "暫存區"),
                      (["ls-files", "--others", "--exclude-standard"], "未追蹤")):
        rc, out = _git(args, cwd)
        rcs.append(rc)
        if rc == 0:
            got += [l for l in out.splitlines() if l.strip()]
    if base:
        rc, out = _git(["diff", "--name-only", f"{base}...HEAD"], cwd)
        rcs.append(rc)
        if rc == 0:
            got += [l for l in out.splitlines() if l.strip()]
    if all(r != 0 for r in rcs):
        return [], "git 讀不到(不是 git 樹?git 不在?)——量不到就不准說通過"
    return sorted(set(got)), ("工作區+暫存區+未追蹤" + (f"+{base}...HEAD" if base else ""))


def added_lines(path: str, base: str | None = None,
                cwd: Path | None = None) -> list[tuple[int, str]]:
    """這個檔**新增**的行,回 `(行號, 含前導 + 的行)`。

    KILL-06/07 只看新增行——既有行是既有債,棘輪的規矩是
    「量出來、記下來,不當成這一批的紅燈」。
    行號從 `@@ … +c,d @@` 的 hunk 標頭來,因為判的是**遮蔽過**的那一份,
    要對得上行才知道那一行到底是碼還是說明文字。"""
    out_all = []
    for args in (["diff", "-U0", "--", path],
                 ["diff", "--cached", "-U0", "--", path]):
        rc, out = _git(args, cwd)
        if rc == 0:
            out_all.append(out)
    if base:
        rc, out = _git(["diff", "-U0", f"{base}...HEAD", "--", path], cwd)
        if rc == 0:
            out_all.append(out)
    # 未追蹤檔沒有 diff 可看:整份都是新增的。不這樣做的話,
    # KILL-06/07 對「全新的一支檔」永遠不會響——又是同一個漏的另一面。
    rc_u, out_u = _git(["ls-files", "--others", "--exclude-standard", "--", path], cwd)
    if rc_u == 0 and out_u.strip():
        fp = (cwd or ROOT) / path
        if fp.is_file():
            try:
                return [(i, "+" + l) for i, l in enumerate(
                    fp.read_text(encoding="utf-8", errors="replace").splitlines(), 1)]
            except Exception:
                return []
    lines: list[tuple[int, str]] = []
    for out in out_all:
        ln = 0
        for l in out.splitlines():
            if l.startswith("@@"):
                m = re.search(r"\+(\d+)", l)
                ln = int(m.group(1)) if m else 0
                continue
            if l.startswith("+") and not l.startswith("+++"):
                lines.append((ln, l))
                ln += 1
    return lines


def _head_text(path: str, cwd: Path | None = None) -> str | None:
    """檔在 HEAD 的樣子;HEAD 沒有這個檔(新檔)回 None。"""
    rc, out = _git(["show", f"HEAD:{path}"], cwd)
    return out if rc == 0 else None


def _exempt(path: str) -> bool:
    return any(path.startswith(p) for p in EXEMPT_PREFIXES)


def _chk_syms(text: str) -> list[str]:
    """這份原始碼裡**真的被呼叫**的 chk() 檢號(依出現序)。

    走 AST,不走 regex。第一版走 regex,第一次真判就咬中自測沙盒夾具裡那串
    `'chk("① a", 1)'` **字串字面**——字串裡長得像呼叫的東西不是呼叫。
    (同 LL432 一族:量的是像那個東西的文字,不是那個東西。)
    語法壞掉回空:那歸 KILL-01 管,一個洞不報兩次。
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    syms = []
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == "chk" and n.args):
            continue
        a, lit = n.args[0], None
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            lit = a.value                     # 隱式相接的多行字串,AST 已經接好
        elif isinstance(a, ast.JoinedStr) and a.values:
            v = a.values[0]
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                lit = v.value                 # f"{_n}(…)" 開頭就是變數 → 沒有固定號,略過
        if lit and lit.split():
            syms.append(lit.split()[0])
    return syms


def _dup_syms(text: str) -> set[str]:
    """同一份原始碼裡撞號的檢號集合。"""
    syms = _chk_syms(text)
    return {s for s in syms if syms.count(s) > 1}


def _masked_lines(text: str, mode: str = "code") -> dict[int, str]:
    """把該當成散文的東西挖空、行號不動的一份。KILL-06 / KILL-07 各判各的。

    **「字串」不是一種東西,是兩種**,混成一種就會各錯一次:
      docstring / 裸字串 = **散文**(說明),永遠不是值
      右值字串           = **值**(同意閘的放行值就住在這裡)

    兩條條款因此要不同的遮蔽。這兩件事都是被本閘自己的檢咬出來的,不是想出來的:
      `mode="code"`(KILL-06 talib):註解 + **所有**字串全遮。
        相依不會寫在字串裡;全遮才擋得掉 `CLAUSES` 裡那句說明——第一次真判咬中的就是它。
      `mode="prose"`(KILL-07 同意閘):註解 + **只有 docstring / 裸字串**。
        全遮的話,放行值會連同右值字串一起被遮成看不見 → **漏判,fail-open**(正控 ⑤ 咬出);
        完全不遮的話,連「說明這條規則」的那句 docstring 都會被判成違規(第二次真判咬中的就是它)。

    挖不動(語法壞)就回空,呼叫端退回判原始行——**退回的是比較嚴的那一邊**,
    不是比較鬆的那一邊(fail-closed)。
    """
    import io
    import tokenize
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except Exception:
        return {}
    lines = {i: l for i, l in enumerate(text.splitlines(), 1)}
    def blank(r1, c1, r2, c2):
        for r in range(r1, r2 + 1):
            if r not in lines:
                continue
            a = c1 if r == r1 else 0
            b = c2 if r == r2 else len(lines[r])
            lines[r] = lines[r][:a] + " " * max(0, b - a) + lines[r][b:]

    for t in toks:
        if t.type == tokenize.COMMENT or (t.type == tokenize.STRING and mode == "code"):
            blank(t.start[0], t.start[1], t.end[0], t.end[1])
    if mode == "prose":
        # 散文 = 裸字串運算式(docstring,以及夾在碼中間當說明用的字串段)。右值字串一個都不碰。
        try:
            for n in ast.walk(ast.parse(text)):
                v = getattr(n, "value", None)
                if (isinstance(n, ast.Expr) and isinstance(v, ast.Constant)
                        and isinstance(v.value, str) and v.end_lineno is not None):
                    blank(v.lineno, v.col_offset, v.end_lineno, v.end_col_offset)
        except SyntaxError:
            return {}                          # 解析不了 → 退回判原始行(比較嚴的那一邊)
    return lines


# ── 十條擊斃條款 ──────────────────────────────────────────────────
def judge(paths: list[str] | None = None, base: str | None = None,
          cwd: Path | None = None, run_selftest: bool = False,
          permits_path: Path | None = None) -> dict:
    """對一組改動下判。回 {state, rc, kills[], permitted[], debts[], checked, why}。

    state:  PASS(rc0) · KILL(rc1) · NODATA(rc2 沒有改動可判) · ABSENT(rc3 量不到)
    **fail-closed**:量不到走 ABSENT,絕不走 PASS。
    """
    cwd = cwd or ROOT
    base = resolve_base(base, cwd)         # 落後的本地 main 會讓判的檔數差 645 倍(見 resolve_base)
    if paths:
        files, src = sorted(set(paths)), "指定路徑"
    else:
        files, src = changed_files(base, cwd)
        if not files and src.startswith("git 讀不到"):
            return {"state": "ABSENT", "rc": 3, "kills": [], "permitted": [], "debts": [],
                    "checked": 0, "why": src}
    if not files:
        return {"state": "NODATA", "rc": 2, "kills": [], "permitted": [], "debts": [], "checked": 0,
                "why": "沒有改動可判(這不是通過,是沒東西可量)"}

    kills: list[dict] = []
    debts: list[dict] = []
    unmeasured: list[dict] = []
    permitted: list[dict] = []
    permits, permit_issues = load_permits(cwd, permits_path)
    for why in permit_issues:
        debts.append({"code": "PERMIT", "path": "(許可冊)", "detail": why})

    #: **KILL-11 要同時問 HEAD 與基線,問一邊都會漏掉一種。**
    #:   初版只問 HEAD(`_head_text is None`):改動一旦提交,檔就在 HEAD 裡了,
    #:   於是「提交後帶 `--base main` 跑」這條路——**接進 CI 之後唯一會走的那條路**——
    #:   永遠不觸發(Codex 審查 PR #121 P1 指出的)。
    #:   改成只問基線又漏掉另一種,而那正是本批真的犯的那一種:
    #:   我在本機**新造**了一支 v0137,而基線上早就有同名的 v0137(內容完全不同)——
    #:   對基線來說那支「存在」,於是只問基線就不會響。
    #:   四種組合只有兩種是 KILL-11 的事:
    #:     ①我新造 + 基線已有 → **撞號**(本批真的犯的那一種)
    #:     ②基線沒有(不管提交了沒)→ 版號必須正好是基線尾版 +1
    #:     ③我在改基線也有的檔 → 那是 KILL-02 的事,不是這一條
    ref = _base_ref(cwd)

    def _ver_cands() -> list[tuple[str, int, str]]:
        out = []
        for path in files:
            mm = _VER_RX.match(Path(path).name)
            if not mm or _exempt(path):
                continue
            # 被刪掉的檔不算「新出一支版本」。git 的改動清單把刪除也列進來,
            #   不擋掉的話,**把一支過時的版本拿掉**這個動作本身會被判成
            #   「你出了一支比基線舊的版本」——那正好是反過來的。
            #   (KILL-01 早就同律跳過不存在的檔:「被刪掉的檔不判語法」。)
            #   註:刪除本身該不該擋(只增不減)是另一條條款的事,目前沒有人管,已記單。
            if not (cwd / path).is_file():
                continue
            mine = int(mm.group("num"))
            in_head = _head_text(path, cwd) is not None
            on_base = _on_ref(ref, path, cwd) if ref else in_head
            if not on_base:
                out.append((path, mine, "new"))
            elif not in_head:
                out.append((path, mine, "collide"))
        return out

    def kill(code, path, detail):
        # v0101:可許可的三條先查許可冊。**比的是位元,不是說詞**;不成立就把理由接在犯行後面照殺。
        if code in PERMITTABLE:
            hit = next((p for p in permits if p["code"] == code and p["path"] == path), None)
            if hit is not None:
                ok, why = permit_holds(hit, cwd, path)
                if ok:
                    permitted.append({"code": code, "律": CLAUSES[code][0], "path": path,
                                      "detail": detail, "permit": hit.get("id", ""),
                                      "ruled_by": hit["ruled_by"], "date": hit["date"],
                                      "ruling": hit["ruling"]})
                    return
                detail = f"{detail} · 許可 {hit.get('id', '')} 不成立:{why}"
        kills.append({"code": code, "律": CLAUSES[code][0], "path": path,
                      "detail": detail, "下一步": CLAUSES[code][2]})

    py_files = [f for f in files if f.endswith(".py")]

    for f in files:
        fp = cwd / f
        # KILL-03 正本零觸碰
        if "/references/intake/" in f or f.startswith("references/intake/"):
            kill("KILL-03", f, "收容件正本被改動")
        # KILL-04 不可動律
        if Path(f).name in IMMUTABLE_NAMES:
            kill("KILL-04", f, f"{Path(f).name} 在不可動清單上")
        # KILL-05 L70
        if f.endswith(".ps1"):
            kill("KILL-05", f, ".ps1 被改動(AI 這一側一律擊斃)")

    for f in py_files:
        fp = cwd / f
        if not fp.is_file():
            continue                         # 被刪掉的檔不判語法(刪檔另有只增不減的律管)
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            kill("KILL-01", f, f"讀不到:{exc}")
            continue
        # KILL-01 語法
        try:
            ast.parse(text)
        except SyntaxError as exc:
            kill("KILL-01", f, f"L{exc.lineno}: {exc.msg}")
            continue

        head = _head_text(f, cwd)
        prev = _prev_version_text(f, cwd)

        # KILL-09 檢號:**新增**撞號才擊斃;既有撞號記債(棘輪)
        base_text = head if head is not None else (prev or "")
        now_dups = _dup_syms(text)
        was_dups = _dup_syms(base_text) if base_text else set()
        new_dups = now_dups - was_dups
        if new_dups:
            kill("KILL-09", f, "新增撞號 " + "、".join(sorted(new_dups)))
        if now_dups & was_dups:
            debts.append({"code": "KILL-09", "path": f,
                          "detail": "既有撞號 " + "、".join(sorted(now_dups & was_dups))
                                    + "(記債,不擊斃)"})

        # KILL-10 翻令留痕:既有 chk 檢名被刪 = 動到釘住的合約。
        #   證據只認**這次的新增行**,而且要點得出批號或 ruled_by(見 _TRACE_RX 的因由)。
        if base_text:
            gone = set(_chk_syms(base_text)) - set(_chk_syms(text))
            if gone:
                added_txt = "\n".join(l for _ln, l in added_lines(f, base, cwd))
                if not _TRACE_RX.search(added_txt):
                    kill("KILL-10", f,
                         "刪掉檢號 " + "、".join(sorted(gone))
                         + ",而這次的新增行裡沒有指名批號的留痕")

        # KILL-06 / KILL-07:只看新增行,而且判的是**遮蔽過註解與字串**的那一份。
        #   遮蔽不了(tokenize 失敗)就退回判原始行——退回比較嚴的那一邊。
        m_all = _masked_lines(text, mode="code")       # KILL-06:註解+所有字串
        m_cmt = _masked_lines(text, mode="prose")      # KILL-07:註解+docstring(保住右值)
        for ln, l in added_lines(f, base, cwd):
            p6 = ("+" + m_all[ln]) if ln in m_all else l
            p7 = ("+" + m_cmt[ln]) if ln in m_cmt else l
            if _TALIB_RX.search(p6):
                kill("KILL-06", f, f"L{ln}: " + l.strip()[:80])
            if _CONSENT_GRANT_RX.search(p7) or _APIKEY_RX.search(p7):
                kill("KILL-07", f, f"L{ln}: " + l.strip()[:80])

    # KILL-02 尾版律:出了新版,舊版必須一個位元沒動
    new_stems = {}
    #   「出了新版」也要含**已提交的**新增(同 Codex P1 的因由:只問 HEAD 會漏掉提交後那條路)
    for f, mine, _kind in _ver_cands():
        mm = _VER_RX.match(Path(f).name)
        new_stems[str(Path(f).parent / mm.group("stem"))] = mine
    for f in files:
        m = _VER_RX.match(Path(f).name)
        if not m or _exempt(f):
            continue
        # **只判基線上真的有的那些舊版。** 這一條律是「舊版一個位元不動」——
        #   基線上不存在的版本沒有「舊內容」可以保:它是這次**新造**的,不是被改的。
        #   實例(批736c,真 PR 上遇到的):本線先出 v0494,main 隨後走到 v0495,
        #   於是本線照 LL334 補出 v0496;此時 v0494 與 v0496 都是「相對基線新增」,
        #   舊式把 v0494 判成「舊版被改動」——誤判,我沒改它,我造了它。
        #   它該由 KILL-11 判「比基線還舊」,那一條才是對的;一件事由對的那條判就好。
        if ref and not _on_ref(ref, f, cwd):
            continue
        stem = str(Path(f).parent / m.group("stem"))
        if stem in new_stems and int(m.group("num")) < new_stems[stem]:
            kill("KILL-02", f, f"舊版被改動(同名新版 v{new_stems[stem]:04d} 已出)")

    # KILL-11 基線時效:新出的 _vNNNN 必須接在**預設分支當下的尾版**之後。
    #   量不到(找不到預設分支參照)**不算通過**——記進 unmeasured,整體降成 PARTIAL(rc2)。
    cands = _ver_cands()
    if cands and ref is None:
        unmeasured.append({"code": "KILL-11", "path": "(全部新版檔)",
                           "detail": "找不到預設分支參照("
                                     + "/".join(BASE_REFS) + ")—— 量不到基線是不是當下的尾版"})
    elif cands:
        for f, mine, kind in cands:
            tail = _tail_on_ref(ref, f, cwd)
            if kind == "collide":
                kill("KILL-11", f,
                     f"這支是新造的,但 {ref} 上**已經有同名的 v{mine:04d}**(內容不同)"
                     f"——撞號;該分支尾版是 v{(tail if tail is not None else mine):04d}")
                continue
            if tail is None:
                continue                   # 那個 stem 在基線上完全不存在=全新一族,沒有基線可比
            if mine <= tail:
                kill("KILL-11", f,
                     f"{ref} 上同名尾版已是 v{tail:04d},這支卻是 v{mine:04d}——版號比基線還舊")
            elif mine > tail + 1:
                kill("KILL-11", f,
                     f"{ref} 上同名尾版是 v{tail:04d},這支跳到 v{mine:04d}"
                     f"——中間那幾版沒讀過,等於在舊基線上改")

    # KILL-08 自測在位。**拆成兩段,而且沒跑的那一段不准當過。**
    #   Codex 審查(PR #121 P1)實測:舊版把整條 KILL-08 關在 `--run-selftest` 後面,
    #   而**兩個生產接法都沒帶那個旗標**(格子站空參數、報告頁只給 `--json`),
    #   於是這條條款在真判時從來沒生效過——一支改壞的引擎、或根本沒有 `--selftest` 的引擎,
    #   照樣拿到 PASS,而 render 還印「11 條全過」。**那是我自己的閘在報假綠。**
    #     (a) 有沒有 `--selftest` —— 便宜,**永遠檢**。
    #     (b) 真的跑一次看 rc 誠不誠實 —— 貴(每支最多 600s),要旗標;
    #         沒跑就記進 `unmeasured` → 整體 PARTIAL(rc2),**絕不是 PASS**。
    eng_files = [f for f in py_files
                 if (cwd / f).is_file() and re.search(r"_(ENG|MDL)\d+_", Path(f).name)]
    no_st = []
    for f in eng_files:
        if "--selftest" not in (cwd / f).read_text(encoding="utf-8", errors="replace"):
            kill("KILL-08", f, "引擎沒有 --selftest(這一段永遠檢,不吃旗標)")
            no_st.append(f)
    runnable = [f for f in eng_files if f not in no_st]
    if run_selftest:
        for f in runnable:
            try:
                p = subprocess.run([sys.executable, str(cwd / f), "--selftest"],
                                   capture_output=True, text=True, timeout=600)
            except Exception as exc:
                kill("KILL-08", f, f"自測跑不起來:{exc}")
                continue
            if p.returncode not in HONEST_RCS:
                tail = (p.stdout or p.stderr or "").strip().splitlines()[-1:] or [""]
                kill("KILL-08", f, f"自測 rc={p.returncode}(誠實態只有 {HONEST_RCS}):{tail[0][:70]}")
    elif runnable:
        unmeasured.append(
            {"code": "KILL-08", "path": f"({len(runnable)} 支引擎)",
             "detail": "沒帶 --run-selftest → 只檢了「有沒有 --selftest」,"
                       "**rc 誠不誠實這一段沒量**;要量就帶 --run-selftest"})

    # 次序有意義:擊斃 > 量不到 > 通過。**量不到永遠不是通過**(fail-closed)。
    if kills:
        state, rc = "KILL", 1
    elif unmeasured:
        state, rc = "PARTIAL", 2
    else:
        state, rc = "PASS", 0
    return {"state": state, "rc": rc, "kills": kills, "permitted": permitted, "debts": debts,
            "unmeasured": unmeasured, "checked": len(files), "why": f"改動來源:{src}"}


def _base_ref(cwd: Path | None = None) -> str | None:
    """找得到的第一個預設分支參照;一個都沒有回 None(量不到,不是通過)。"""
    for r in BASE_REFS:
        rc, _ = _git(["rev-parse", "--verify", "--quiet", r], cwd)
        if rc == 0:
            return r
    return None


def resolve_base(base: str | None, cwd: Path | None = None) -> str | None:
    """把使用者給的 `--base main` 解成**真的跟得上的那一個** ref:先試 `origin/main`,再試 `main`。

    **這一條是這道閘自己實跑時咬出來的,而且跟 KILL-11 是同一個病。**
    容器裡本地 `main` 停在舊 commit、`origin/main` 已經往前走——
    於是 `--base main` 的 `main...HEAD` 吐出 **4,518 檔**(把併進來的 89 個 commit
    全算成「這次的改動」,連別的批動過的收容件都被 KILL-03 擊斃),
    而 `origin/main...HEAD` 只有 **7 檔**——正好是這次那一個 commit。
    **一個落後的參照會讓答案整個錯掉**,不管你判得多仔細。
    """
    if not base:
        return None
    for cand in ((f"origin/{base}", base) if "/" not in base else (base,)):
        rc, _ = _git(["rev-parse", "--verify", "--quiet", cand], cwd)
        if rc == 0:
            return cand
    return base                            # 兩個都解不開:照原樣交給 git 去報錯(不安靜換掉)


def _on_ref(ref: str, path: str, cwd: Path | None = None) -> bool:
    """這個檔在 `ref` 上存在嗎。"""
    rc, _ = _git(["cat-file", "-e", f"{ref}:{path}"], cwd)
    return rc == 0


def _tail_on_ref(ref: str, path: str, cwd: Path | None = None) -> int | None:
    """同 stem 在 `ref` 上的最大版號;那支在 ref 上完全不存在回 None。"""
    m = _VER_RX.match(Path(path).name)
    if not m:
        return None
    d = str(Path(path).parent)
    rc, out = _git(["ls-tree", "-r", "--name-only", ref, "--", d], cwd)
    if rc != 0:
        return None
    import re as _re
    rx = _re.compile(_re.escape(m.group("stem")) + r"_v(\d{4})\." + m.group("ext") + r"$")
    ns = [int(mm.group(1)) for line in out.splitlines()
          if (mm := rx.search(line.strip()))]
    return max(ns) if ns else None


def _prev_version_text(path: str, cwd: Path | None = None) -> str | None:
    """同 stem 的前一版(尾版律的基線)。找不到回 None。"""
    m = _VER_RX.match(Path(path).name)
    if not m:
        return None
    d = (cwd or ROOT) / Path(path).parent
    if not d.is_dir():
        return None
    sibs = sorted(p for p in d.glob(f"{m.group('stem')}_v[0-9][0-9][0-9][0-9].{m.group('ext')}")
                  if p.name != Path(path).name)
    if not sibs:
        return None
    try:
        return sibs[-1].read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


def render(d: dict) -> str:
    head = {"PASS": "[通過]", "KILL": "[擊斃]", "PARTIAL": "[PARTIAL]",
            "NODATA": "[NODATA]", "ABSENT": "[ABSENT]"}.get(d["state"], "[?]")
    out = [f"=== 模組更新擊斃閘 {VERSION}({BATCH})=== {head} rc={d['rc']} · "
           f"判了 {d['checked']} 檔 · {d['why']}"]
    for k in d["kills"]:
        out.append(f"  {head} {k['code']}({k['律']}) {k['path']}")
        out.append(f"        犯:{k['detail']}")
        out.append(f"        下一步:{k['下一步']}")
    for p in d.get("permitted", []):
        out.append(f"  [許可] {p['code']}({p['律']}) {p['path']} · 許可 {p['permit']}"
                   f"({p['ruled_by']} {p['date']}:{p['ruling'][:60]})")
    for t in d["debts"]:
        out.append(f"  [債] {t['code']} {t['path']} · {t['detail']}")
    for u in d.get("unmeasured", []):
        out.append(f"  [量不到] {u['code']} {u['path']} · {u['detail']}(量不到不是通過)")
    un = {u["code"] for u in d.get("unmeasured", [])}
    if d["state"] == "PASS":
        npm = len(d.get("permitted", []))
        out.append(f"  {len(CLAUSES)} 條全過(既有債 {len(d['debts'])} 筆另記"
                   + (f";另 {npm} 件是**操作員許可**放行、位元吻合,見上 [許可]" if npm else "")
                   + ")")
    elif d["state"] == "PARTIAL":
        # **不准說「全過」。** 沒量到的那幾條要點名——
        #   「其餘都過」配著一條沒量過的條款,就是把分母偷偷變小(L57)。
        out.append(f"  {len(CLAUSES) - len(un)}/{len(CLAUSES)} 條量過且全過 · "
                   f"{len(un)} 條沒量到({'、'.join(sorted(un))})—— 量不到不是通過")
    return "\n".join(out)


# ── 自測 ─────────────────────────────────────────────────────────
def selftest() -> int:
    import tempfile
    ran, fails = [], []

    def chk(name, cond, note=""):
        ran.append(name)
        ok = bool(cond)
        if not ok:
            fails.append(name)
        print("  [%s] %s%s" % ("OK" if ok else "FAIL", name, (" (%s)" % note) if note else ""))

    print(f"=== 模組更新擊斃閘 {VERSION} · 自測(沙盒 · 零網路 · 唯讀)===")

    with tempfile.TemporaryDirectory() as td:
        r = Path(td)
        for a in (["init", "-q", "-b", "main"], ["config", "user.email", "t@t"],
                  ["config", "user.name", "t"]):
            _git(a, r)
        (r / "m").mkdir()
        (r / "m" / "E_ENG001_X_v0100.py").write_text(
            'def f():\n    return 1\n\nif "--selftest" in []:\n    pass\n', encoding="utf-8")
        _git(["add", "-A"], r)
        _git(["commit", "-qm", "base"], r)

        # ① 負控:乾淨的樹不准報擊斃,而且**不准報通過**——沒有改動就是沒東西可量
        d0 = judge(base=None, cwd=r)
        chk("① **沒有改動 ≠ 通過**:乾淨的樹回 NODATA(rc2),不是 PASS。"
            "一道「沒東西可量也說通過」的閘,綠燈裡有一半是空的",
            d0["state"] == "NODATA" and d0["rc"] == 2, f"({d0['state']} rc={d0['rc']})")

        # ② KILL-01 語法:正控
        (r / "m" / "bad.py").write_text("def f(:\n", encoding="utf-8")
        d1 = judge(cwd=r)
        chk("② KILL-01 正控:語法壞掉的 .py 必須被擊斃(rc1),"
            "而且要講得出行號——批727 我寫壞過一次,靠眼睛沒看出來",
            d1["rc"] == 1 and any(k["code"] == "KILL-01" for k in d1["kills"]),
            f"({[k['code'] for k in d1['kills']]})")
        (r / "m" / "bad.py").unlink()

        # ③ KILL-02 尾版律:出新版時動舊版
        (r / "m" / "E_ENG001_X_v0101.py").write_text("x = 1\n", encoding="utf-8")
        (r / "m" / "E_ENG001_X_v0100.py").write_text(
            'def f():\n    return 2\n', encoding="utf-8")       # 舊版被動了
        d2 = judge(cwd=r)
        chk("③ KILL-02 正控:出了 v0101 就不准再動 v0100(只增不減)。"
            "舊版被改一個位元都算——「順手修一下舊版」是這條律最常見的破口",
            any(k["code"] == "KILL-02" and "v0100" in k["path"] for k in d2["kills"]),
            f"({[(k['code'], Path(k['path']).name) for k in d2['kills']]})")
        _git(["checkout", "--", "m/E_ENG001_X_v0100.py"], r)

        # ④ KILL-02 負控:出新版但**沒動**舊版 → 這一條不准響
        d3 = judge(cwd=r)
        chk("④ KILL-02 負控:同樣出了 v0101,舊版沒動就**不准**擊斃 —— "
            "一道永遠響的閘跟永遠不響的閘一樣沒有判斷力",
            not any(k["code"] == "KILL-02" for k in d3["kills"]),
            f"(kills={[k['code'] for k in d3['kills']]})")

        # ⑤ KILL-06 / KILL-07:新增行才算(既有債走棘輪)
        (r / "m" / "E_ENG001_X_v0101.py").write_text(
            "import ta" + "lib\n" + "VIA_NET" + "_CONSENT = 'YES'\n", encoding="utf-8")
        d4 = judge(cwd=r)
        codes = {k["code"] for k in d4["kills"]}
        chk("⑤ KILL-06/07 正控:新增行 import ta·lib(L50 第一條)與代設同意閘"
            "(**AI 永不代設**,那是操作員的手)各自擊斃",
            "KILL-06" in codes and "KILL-07" in codes, f"({sorted(codes)})")

        # ⑬ 負控:說明文字裡提到 talib 不是相依(第一次真判就咬中自己的 CLAUSES 說明)
        (r / "m" / "prose.py").write_text(
            '"""不得 import ta' + 'lib"""\n# 呼叫 ta' + 'lib. 也不行\nx = 1\n', encoding="utf-8")
        d_p = judge(paths=["m/prose.py"], cwd=r)
        chk("⑬ KILL-06 負控:**說明文字與註解裡提到 talib 不是相依**。"
            "第一次真判本閘就被自己 CLAUSES 裡那句說明咬中——量文字不量碼,"
            "跟 LL432「量的是冊上那一份、不是真在跑的那一份」同一族",
            not any(k["code"] == "KILL-06" for k in d_p["kills"]),
            f"({[k['code'] for k in d_p['kills']] or '無'})")

        # ⑭ 這個洞的反面:遮蔽若一視同仁,KILL-07 會被自己的遮蔽遮瞎(fail-open)
        (r / "m" / "grant.py").write_text(
            "VIA_NET" + "_CONSENT = 'YES'\n", encoding="utf-8")
        d_g = judge(paths=["m/grant.py"], cwd=r)
        chk("⑭ KILL-07 正控**在遮蔽之後仍然響**:放行值 `'YES'` 本身就是字串字面,"
            "若跟 KILL-06 共用同一份「連字串一起遮」的遮蔽,代設同意閘就漏判了——"
            "那是 fail-open。兩條條款各用各的遮蔽,這一檢就是釘住這件事",
            any(k["code"] == "KILL-07" for k in d_g["kills"]),
            f"({[k['code'] for k in d_g['kills']] or '無'})")

        # ⑮ 成對:docstring 裡**說明**同意閘不算違規,同一支檔裡**真的設值**仍要擋。
        #    第二次真判咬中的,就是我自己寫來說明這條規則的那句 docstring。
        _G = "VIA_NET" + "_CONSENT = 'YES'"
        (r / "m" / "doc.py").write_text(
            f'"""說明:不得把 {_G} 這樣寫死。"""\nx = 1\n', encoding="utf-8")
        (r / "m" / "both.py").write_text(
            f'"""說明:不得把 {_G} 這樣寫死。"""\n{_G}\n', encoding="utf-8")
        d_doc = judge(paths=["m/doc.py"], cwd=r)
        d_both = judge(paths=["m/both.py"], cwd=r)
        chk("⑮ KILL-07 成對:docstring 裡**說明**這條規則不算違規;同一支檔裡**真的設值**照擋。"
            "分不開散文與值,就只剩兩條爛路——要嘛把說明判成違規,"
            "要嘛為了讓說明過關而把值一起遮瞎(那是 fail-open)",
            not any(k["code"] == "KILL-07" for k in d_doc["kills"])
            and any(k["code"] == "KILL-07" for k in d_both["kills"]),
            f"(只有說明→{[k['code'] for k in d_doc['kills']] or '無'} · "
            f"說明+真設值→{[k['code'] for k in d_both['kills']]})")

        # ── KILL-11 基線時效:這一批自己付的學費,夾具照著真實情形擺 ──
        #    真實情形:我的分支落後預設分支 89 個 commit,於是我開的 v0137
        #    跟預設分支上**別的批做的同名 v0137** 撞在一起,而且 v0138 也已經在了。
        #    十條條款一條都沒攔住——它們全部只看「這次改了什麼」,
        #    沒有一條問「你改的是不是當下那一版」。
        (r / "m" / "E_ENG009_Z_v0105.py").write_text("x = 1\n", encoding="utf-8")
        _git(["add", "-A"], r); _git(["commit", "-qm", "base has v0105"], r)
        _git(["checkout", "-q", "-b", "feat", "HEAD~1"], r)     # 落後一個 commit 的分支
        (r / "m" / "E_ENG009_Z_v0105.py").write_text("y = 2\n", encoding="utf-8")
        d_col = judge(cwd=r)                                    # 撞號:mine == 預設分支尾版
        (r / "m" / "E_ENG009_Z_v0105.py").unlink()
        (r / "m" / "E_ENG009_Z_v0103.py").write_text("y = 2\n", encoding="utf-8")
        d_old = judge(cwd=r)                                    # 版號比基線還舊
        (r / "m" / "E_ENG009_Z_v0103.py").unlink()
        (r / "m" / "E_ENG009_Z_v0109.py").write_text("y = 2\n", encoding="utf-8")
        d_jmp = judge(cwd=r)                                    # 跳號:中間那幾版沒讀過
        (r / "m" / "E_ENG009_Z_v0109.py").unlink()
        (r / "m" / "E_ENG009_Z_v0106.py").write_text("y = 2\n", encoding="utf-8")
        d_ok = judge(cwd=r)                                     # 負控:正好接在尾版之後
        (r / "m" / "E_ENG009_Z_v0106.py").unlink()
        _git(["checkout", "-q", "main"], r)
        def _k11(d):
            return [k["detail"] for k in d["kills"] if k["code"] == "KILL-11"]
        chk("⑯ KILL-11 正控 ×3(**本批自己付的學費**):分支落後預設分支時,"
            "① 開一個預設分支**已經有**的版號=撞號(我真的做了:v0137 撞上別的批的 v0137)· "
            "② 版號比基線還舊 · ③ 跳號(中間那幾版沒讀過,等於在舊基線上改)。"
            "前十條條款一條都攔不住這件事——它們全部只問「這次改了什麼」,"
            "**沒有一條問「你改的是不是當下那一版」**。基線錯了,改得再乾淨也是廢的",
            len(_k11(d_col)) == 1 and "撞號" in _k11(d_col)[0]
            and len(_k11(d_old)) == 1 and "比基線還舊" in _k11(d_old)[0]
            and len(_k11(d_jmp)) == 1 and "沒讀過" in _k11(d_jmp)[0],
            f"(撞號 {bool(_k11(d_col))} · 舊號 {bool(_k11(d_old))} · 跳號 {bool(_k11(d_jmp))})")
        chk("⑰ KILL-11 負控:正好接在預設分支尾版之後(v0105 → v0106)就**不准**擊斃——"
            "一道連正常升版都攔的閘會被關掉,而被關掉的閘等於沒有閘",
            not _k11(d_ok), f"({_k11(d_ok) or '無'})")

        # ⑥ KILL-05 L70:.ps1
        (r / "m" / "S.ps1").write_text("Write-Host 1\n", encoding="utf-8")
        d5 = judge(cwd=r)
        chk("⑥ KILL-05 正控:.ps1 被改就擊斃(L70:未經操作員逐次許可不得改 .ps1)",
            any(k["code"] == "KILL-05" for k in d5["kills"]))
        (r / "m" / "S.ps1").unlink()

        # ⑦ KILL-03 正本零觸碰
        (r / "references").mkdir(); (r / "references" / "intake").mkdir()
        (r / "references" / "intake" / "z.py").write_text("x = 1\n", encoding="utf-8")
        d6 = judge(cwd=r)
        chk("⑦ KILL-03 正控:references/intake/ 底下動一個位元就擊斃(正本零觸碰)",
            any(k["code"] == "KILL-03" for k in d6["kills"]))

        # ⑧ KILL-09 棘輪:既有撞號記債、新增撞號擊斃
        (r / "m" / "dup.py").write_text(
            'chk("① a", 1)\nchk("① b", 1)\n', encoding="utf-8")
        _git(["add", "-A"], r); _git(["commit", "-qm", "debt"], r)
        d7 = judge(paths=["m/dup.py"], cwd=r)
        (r / "m" / "dup.py").write_text(
            'chk("① a", 1)\nchk("① b", 1)\nchk("② c", 1)\nchk("② d", 1)\n', encoding="utf-8")
        d8 = judge(paths=["m/dup.py"], cwd=r)
        chk("⑧ KILL-09 **棘輪**:既有撞號 ① 記債不擊斃、後來新增的撞號 ② 擊斃。"
            "既有債一律擊斃的話,這道閘第一天就會把整棵樹擋死,然後被關掉——"
            "被關掉的閘等於沒有閘",
            not d7["kills"] and any(t["code"] == "KILL-09" for t in d7["debts"])
            and any(k["code"] == "KILL-09" and "②" in k["detail"] for k in d8["kills"]),
            f"(既有:kills={len(d7['kills'])} debts={len(d7['debts'])} · 新增:"
            f"{[k['detail'] for k in d8['kills'] if k['code'] == 'KILL-09']})")

        # ⑨ KILL-10 翻令留痕
        (r / "m" / "pin.py").write_text('chk("㊿ 釘住的合約", 1)\n', encoding="utf-8")
        _git(["add", "-A"], r); _git(["commit", "-qm", "pin"], r)
        (r / "m" / "pin.py").write_text("x = 1\n", encoding="utf-8")
        d9 = judge(paths=["m/pin.py"], cwd=r)
        (r / "m" / "pin.py").write_text(
            "# 本批取代批240 的裁示,因由:…\nx = 1\n", encoding="utf-8")
        d10 = judge(paths=["m/pin.py"], cwd=r)
        chk("⑨ KILL-10 正負成對:刪掉釘住的 chk 檢名而**沒有留痕**=擊斃;"
            "寫明取代了哪一批的裁示就放行(LL90:裁定權在操作員,留痕義務沒有轉移)",
            any(k["code"] == "KILL-10" for k in d9["kills"])
            and not any(k["code"] == "KILL-10" for k in d10["kills"]),
            f"(無痕→{[k['code'] for k in d9['kills']]} · 有痕→{[k['code'] for k in d10['kills']]})")

    # ⑱ 量不到 ≠ 通過:找不到預設分支參照時,KILL-11 記進 unmeasured,整體降 PARTIAL(rc2)
    with tempfile.TemporaryDirectory() as td3:
        r3 = Path(td3)
        for a in (["init", "-q", "-b", "wip"], ["config", "user.email", "t@t"],
                  ["config", "user.name", "t"]):
            _git(a, r3)
        (r3 / "m").mkdir()
        # 帶 `--selftest` 字樣:新的 KILL-08「有沒有 --selftest」是**永遠檢**的,
        #   夾具若不帶,這一格會被 KILL-08 擊斃,量不到 KILL-11 的 PARTIAL(夾具的事,不是規則的事)
        _ST = '"--selftest"\n'
        (r3 / "m" / "E_ENG010_Q_v0100.py").write_text("x = 1\n" + _ST, encoding="utf-8")
        _git(["add", "-A"], r3); _git(["commit", "-qm", "b"], r3)
        (r3 / "m" / "E_ENG010_Q_v0101.py").write_text("y = 1\n" + _ST, encoding="utf-8")
        d_un = judge(cwd=r3)
        chk("⑱ KILL-11 **量不到 ≠ 通過**:沒有 main/master 可比時,這一條記進 `unmeasured`,"
            "整體降成 PARTIAL(rc2),**不准報 PASS**。"
            "一條「找不到基線就算過」的條款,等於這條款只在好天氣生效",
            d_un["state"] == "PARTIAL" and d_un["rc"] == 2
            and any(u["code"] == "KILL-11" for u in d_un["unmeasured"]),
            f"({d_un['state']} rc={d_un['rc']} · unmeasured "
            f"{[u['code'] for u in d_un['unmeasured']]})")

    # ⑩ fail-closed:不是 git 樹的地方,必須 ABSENT,**不准 PASS**
    with tempfile.TemporaryDirectory() as td2:
        d11 = judge(cwd=Path(td2))
        chk("⑩ **fail-closed**:量不到(不是 git 樹)回 ABSENT rc3,絕不回 PASS。"
            "本倉單子上就有一個 fail-open 的同意閘(#67:else 分支把閘開成 YES)——"
            "出事就放行的閘比沒有閘更糟,它讓人以為有人在看",
            d11["state"] in ("ABSENT", "NODATA") and d11["rc"] != 0,
            f"({d11['state']} rc={d11['rc']})")

    # ⑲–㉓:Codex 審查(PR #121)抓出的四個 fail-open + 本閘實跑咬出的落後基線,逐條正負控。
    #   四個都是「出事就放行」—— 那比沒有閘更糟,所以一條都不能只修不釘。
    src = Path(__file__).read_text(encoding="utf-8")
    _G = "VIA_NET" + "_CONSENT"
    consent_cases = [
        (f'+{_G} = "YES"', True, "裸賦值"),
        (f'+os.environ["{_G}"] = "YES"', True, "os.environ 形(本樹最常見)"),
        (f'+cfg = {{"{_G}": "YES"}}', True, "dict 形"),
        (f'+os.environ.setdefault("{_G}", "YES")', True, "setdefault 形"),
        (f'+if os.environ.get("{_G}", "") == "YES":', False, "讀取比較(負控)"),
        (f'+if os.environ["{_G}"] == "YES":', False, "讀取比較(負控)"),
    ]
    consent_bad = [w for l, want, w in consent_cases
                   if bool(_CONSENT_GRANT_RX.search(l)) != want]
    chk("⑲ Codex P1:KILL-07 要認得**本樹最常見的那個寫法**。實測舊式漏判三種:"
        "os.environ 形(鍵後面先是引號再是 `]`)、dict 冒號形、setdefault 逗號形 —— "
        "**最該擋的那個寫法正好過**,那是 fail-open。而讀取比較不是賦值,不得誤判",
        not consent_bad, "(六形全對)" if not consent_bad else f"(錯 {consent_bad})")

    talib_cases = [("+import ta" + "lib", True, "import"),
                   ("+from ta" + "lib import RSI", True, "from-import(舊式漏判)"),
                   ("+x = ta" + "lib.RSI(c)", True, "屬性呼叫")]
    talib_bad = [y for l, w, y in talib_cases if bool(_TALIB_RX.search(l)) != w]
    chk("⑳ Codex P2:KILL-06 要認得 `from ta·lib import RSI` —— 那個寫法既不含 `import ta·lib` "
        "也不含 `ta·lib.`,舊式三條分支一條都不中,禁用的相依可以大方走進來",
        not talib_bad, "(三形全中)" if not talib_bad else f"(錯 {talib_bad})")

    chk("㉑ Codex P1:KILL-08 **拆兩段,而且沒跑的那一段不准當過**。舊版把整條關在 "
        "`--run-selftest` 後面,而兩個生產接法都沒帶那個旗標(格子站空參數、報告頁只給 --json)"
        "—— 於是這條條款在真判時從來沒生效過,render 還印「11 條全過」。那是我自己的閘在報假綠。"
        "現在:『有沒有 --selftest』永遠檢;『rc 誠不誠實』沒跑就記 unmeasured 降 PARTIAL",
        "永遠檢,不吃旗標" in src and '"code": "KILL-08"' in src
        and "量不到不是通過" in src)

    trace_cases = [("本令取代批240,因由:…", True, "取代批NNN(強痕)"),
                   ("ruled_by: 操作員", True, "ruled_by(強痕)"),
                   ("(批736 操作員令)", True, "批號+泛詞同句(算痕)"),
                   ("這支引擎的表頭寫著操作員令,跟這次改動無關", False,
                    "**泛詞單獨出現**(負控:舊式在這裡放行,KILL-10 就實質失效)")]
    trace_bad = [y for t, w, y in trace_cases if bool(_TRACE_RX.search(t)) != w]
    chk("㉒ Codex P1:KILL-10 的留痕證據要**這次新增的行**、而且點得出批號或 ruled_by。"
        "舊式拿 `操作員令` 這種表頭常見詞去搜**整份檔** —— 任何表頭有那三個字的引擎,"
        "刪掉釘住的 chk 都自動放行,那條條款實質失效",
        not trace_bad and "added_lines(f, base, cwd)" in src,
        "(四形全對)" if not trace_bad else f"(錯 {trace_bad})")

    chk("㉓ 本閘實跑咬出來的:`--base main` 要解成**跟得上的那一個** ref(先 `origin/main` 再 `main`)。"
        "容器本地 main 停在舊 commit,`main...HEAD` 吐出 4,518 檔 —— 把併進來的 89 個 commit "
        "全算成「這次的改動」,連別的批動過的收容件都被 KILL-03 擊斃;"
        "`origin/main...HEAD` 只有 7 檔,正好是這次那一個 commit。"
        "**一個落後的參照會讓答案整個錯掉,不管你判得多仔細** —— 跟 KILL-11 同一個病",
        "def resolve_base" in src and "resolve_base(base, cwd)" in src
        and 'f"origin/{base}"' in src)

    # ⑪ 條款表一份(Zero-Hydra)
    chk("⑪ 條款寫在 CLAUSES 一份,render/judge/自測都讀它(Zero-Hydra:抄第二份=第二顆會漂移的頭)",
        len(CLAUSES) == 11 and 'CLAUSES[code][2]' in src and 'len(CLAUSES)' in src,
        f"(條款 {len(CLAUSES)} 條)")

    # ⑫ 唯讀
    # 掃描範圍:**判決邏輯**那一段(檔頭到 def selftest 之前)。
    #   自測的沙盒夾具本來就要能寫它自己的 tempfile 夾,把它算進來就是自己咬自己。
    judge_src = src.split("def selftest(")[0]
    code = "\n".join(l for l in judge_src.split("\n") if not l.lstrip().startswith("#"))
    # 違禁字面一律**拼接**寫。第一版我原樣寫在名單裡,這一檢當場咬中自己的名單——
    #   跟 MDL181 批712 踩的是同一個坑(LL384:字面禁用檢自己不能含那個字面)。
    banned = [b for b in ("write_" + "text(", "un" + "link(", "rm" + "tree(",
                          "mk" + "dir(", "os.re" + "move(")
              if b in code]
    chk("⑫ **唯讀**:判決邏輯只讀檔、只跑 git 讀指令,不寫、不刪任何被判的檔 —— "
        "一支會改東西的把關閘,把的是它自己改過的關(LL368)。"
        "〔掃描範圍刻意排除 selftest:沙盒夾具要能寫它自己的 tempfile 夾。"
        "第一版我把違禁字面原樣寫進名單,這一檢當場咬中自己——MDL181 批712 踩過同一個坑〕",
        "capture_output=True" in code and not banned, f"(違禁 {banned or '無'})")

    # ㉔㉕ v0101 許可冊:正控(位元吻合才放行)與負控(差一個位元、冊外條款、缺裁示、冊讀不到都照殺)
    with tempfile.TemporaryDirectory() as td2, tempfile.TemporaryDirectory() as tb:
        r2, bk = Path(td2), Path(tb) / "VIA_ModuleChange_Permits_v0100.json"
        for a in (["init", "-q", "-b", "main"], ["config", "user.email", "t@t"],
                  ["config", "user.name", "t"]):
            _git(a, r2)
        (r2 / "a").mkdir()
        (r2 / "a" / "VeritasCeleritas.py").write_text("x = 1\n", encoding="utf-8")
        (r2 / "a" / "t.ps1").write_text("Write-Host 1\n", encoding="utf-8")
        (r2 / "a" / "E_ENG001_X_v0100.py").write_text('x = 1\n# --selftest\n', encoding="utf-8")
        _git(["add", "-A"], r2)
        _git(["commit", "-qm", "base"], r2)
        (r2 / "a" / "VeritasCeleritas.py").write_text("x = 2\n", encoding="utf-8")
        (r2 / "a" / "t.ps1").write_text("Write-Host 2\n", encoding="utf-8")
        (r2 / "a" / "E_ENG001_X_v0101.py").write_text('x = 2\n# --selftest\n', encoding="utf-8")
        _git(["rm", "-q", "a/E_ENG001_X_v0100.py"], r2)

        def _sha_of(rel):
            return hashlib.sha256((r2 / rel).read_bytes()).hexdigest()

        def _book(rows):
            bk.write_text(json.dumps({"permits": rows}, ensure_ascii=False), encoding="utf-8")
            return bk
        who = {"ruled_by": "操作員", "date": "2026-09-25", "ruling": "「NO TA-LIBS ALLOWED」"}
        good = [dict(id="P1", code="KILL-04", path="a/VeritasCeleritas.py", kind="modify",
                     sha256=_sha_of("a/VeritasCeleritas.py"), **who),
                dict(id="P2", code="KILL-05", path="a/t.ps1", kind="modify",
                     sha256=_sha_of("a/t.ps1"), **who),
                dict(id="P3", code="KILL-02", path="a/E_ENG001_X_v0100.py", kind="delete", **who)]
        dp = judge(cwd=r2, permits_path=_book(good))
        pcodes = sorted(x["code"] for x in dp["permitted"])
        chk("㉔ v0101 許可冊正控:操作員下令的三件(改不可動檔 KILL-04 · 改 .ps1 KILL-05 · "
            "出新版刪舊版 KILL-02)位元與冊吻合 → **不擊斃**、列進 permitted、render 照印 [許可]"
            "(不藏進「全過」)。v0100 沒有許可這個東西,操作員親口下令的改動跟 AI 私改一樣被殺",
            not dp["kills"] and pcodes == ["KILL-02", "KILL-04", "KILL-05"]
            and "[許可]" in render(dp),
            f"(kills={[k['code'] for k in dp['kills']]} permitted={pcodes})")

        (r2 / "a" / "VeritasCeleritas.py").write_text("x = 3\n", encoding="utf-8")   # 許可之後又動
        _git(["checkout", "HEAD", "--", "a/E_ENG001_X_v0100.py"], r2)               # 許可刪,卻沒刪還改了
        (r2 / "a" / "E_ENG001_X_v0100.py").write_text("x = 9\n# --selftest\n", encoding="utf-8")
        (r2 / "a" / "E_ENG001_X_v0101.py").write_text(
            'import ta' + 'lib\n# --selftest\n', encoding="utf-8")
        bad_rows = good + [dict(id="P4", code="KILL-06", path="a/E_ENG001_X_v0101.py",
                                kind="modify", sha256=_sha_of("a/E_ENG001_X_v0101.py"), **who),
                           dict(id="P5", code="KILL-05", path="a/u.ps1", kind="modify",
                                sha256="0" * 64, ruled_by="操作員", date="2026-09-25", ruling="")]
        dn = judge(cwd=r2, permits_path=_book(bad_rows))
        k4 = [k for k in dn["kills"] if k["code"] == "KILL-04"]
        issues = " ".join(t["detail"] for t in dn["debts"] if t["code"] == "PERMIT")
        dz = judge(cwd=r2, permits_path=Path(tb) / "no_such_book.json")
        zc = sorted({k["code"] for k in dz["kills"]})
        chk("㉕ v0101 許可冊負控:①許可之後**再動一個位元** → KILL-04 照殺並說明許可不成立 "
            "②冊上列 KILL-06(L50)的許可 → 照殺 + 記債(只有 KILL-02/04/05 可以許可)"
            "③缺原話(ruling)的許可不算 ④冊讀不到 = 沒有許可 → 三件全殺(fail-closed)"
            "⑤許可的是刪除、舊版卻還在(還被改了)→ KILL-02 照殺",
            k4 and "不成立" in k4[0]["detail"]
            and any(k["code"] == "KILL-02" and "不成立" in k["detail"] for k in dn["kills"])
            and any(k["code"] == "KILL-06" for k in dn["kills"])
            and "P4" in issues and "P5" in issues
            and {"KILL-02", "KILL-04", "KILL-05"} <= set(zc)
            and any("讀不到" in t["detail"] for t in dz["debts"]),
            f"(負控 kills={sorted({k['code'] for k in dn['kills']})} · 無冊 kills={zc})")

    print("  [計] %d 檢 OK %d · FAIL %d" % (len(ran), len(ran) - len(fails), len(fails)))
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a or "--self-test" in a:
        return selftest()
    base = a[a.index("--base") + 1] if "--base" in a and len(a) > a.index("--base") + 1 else None
    paths = [a[i + 1] for i, x in enumerate(a) if x == "--path" and i + 1 < len(a)] or None
    d = judge(paths=paths, base=base, run_selftest="--run-selftest" in a)
    print(json.dumps(d, ensure_ascii=False, indent=1) if "--json" in a else render(d))
    return d["rc"]


if __name__ == "__main__":
    sys.exit(main())
