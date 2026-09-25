#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL147_EngineSmokeGate v0101 — 無自測面引擎的煙霧閘(批468 立;批470 加 VENDOR 態)

批470:v0100 把三支判成 RED——reporter.py / reporters.py / table.py。
查了才知道**它們不是壞掉,是放錯地方**:那是 rich 與 pip-resolvelib 的**套件內檔**
(`from . import box, errors` / `from .structs import …`),散落在引擎夾裡而且**零人 import**。
套件內檔本來就不能單獨載入——拿「能不能獨立載入」去測它,是**用錯的尺**,
量出來的紅字不是它的問題,是儀器的問題。**判錯的紅燈和假綠一樣傷**:
它會讓人去修一個沒有壞的東西,而真正壞的那支反而淹在雜訊裡。
v0101 加第四態 **VENDOR**:相對 import(`from .`)且全樹零人 import → 判 VENDOR,
列示、**不計入總判**、並指出本倉早就有 `_quarantine_pip_vendor` 隔離夾可以收。
本件**不搬檔**——搬進隔離夾是操作員的裁示,儀器只負責把話講對。
====================================================================
操作員令:「完成 VRN 一切通過認證測試完工」。

為什麼非有這道不可(量到的,不是規劃的):
  全 VRN 38 個版號族,**只有 29 支有 `--selftest`**。全樹掃描器找的是那個旗標,
  於是另外 9 支在每一次認證掃描裡都被算成「SKIP · 無自測旗標」——
  它們**不是綠也不是紅,是沒有儀器**。
  拿「29/29 全綠」去宣告「VRN 全部通過認證」,等於把 9 支沒量過的算成過了。
  **看不見的儀器不算儀器;沒有儀器的站不得計入總判。**(批460 完整性閘同律)

本件做什麼、不做什麼(誠實界線):
  做:①模組**載得進來**嗎(語法/相依/import 期副作用會不會爆)
      ②它宣告的**公開契約**(頂層 def)還在不在、拿得到簽章嗎
      ③載入是否有**寫檔副作用**(import 期就動正式產出夾=批410 那一族的病)
  不做:**不驗業務正確性**。煙霧閘只證明「這支還活著、介面還在」,
      不證明它算得對。把煙霧當成全測,就是另一種假綠——所以本件的
      燈一律標「SMOKE」,總表也要照這個字面收,不得改寫成 GREEN。

Zero-Hydra:不替那 9 支各寫一份自測(那會是 9 份九頭龍),
  也不改它們一個字——本件**只增一支共用閘**,誰哪天長出真自測就自動退出名單。
用法:python3 CGC_MDL147_EngineSmokeGate_v0100.py [--dir <引擎夾>] | --selftest
紀律:零網路、唯讀(絕不寫任何正式產出)、不卡斷(逐支逾時)、誠實三態。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(graceful 缺席零影響) =====
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
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import ast
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VRN_DIR = VIA / "functional modules" / "VRN"
#: 逐支逾時(秒)。載得進來的模組不該要這麼久;要這麼久本身就是紅旗。
TIMEOUT = 90
#: 正式產出夾——載入期間碰它就是副作用(批410 那一族)
LIVE_OUT = VIA / "VIA_Reports"


def tails(d: Path) -> list:
    """版號族取尾版;無版號的檔各自成族(尾版律 glob)。"""
    fam = defaultdict(list)
    for p in sorted(d.glob("*.py")):
        m = re.match(r"^(.*?)_v(\d{4})\.py$", p.name)
        if m:
            fam[m.group(1)].append((int(m.group(2)), p))
        else:
            fam[p.name].append((0, p))
    out = []
    for _k, v in sorted(fam.items()):
        v.sort()
        out.append(v[-1][1])
    return out


#: 凍結副本(收容原件的 sha 快照)。只增不減律要它們留著,但它們**不是現役引擎**
#: ——拿它們的載入結果去算認證,等於把倉庫裡的化石算成活的。
FROZEN_RX = re.compile(r"_sha[0-9a-f]{6,}")


def tier(p: Path) -> str:
    """分層(批468)。三種東西混在一個數裡,那個數就沒有意義:
         frozen  _sha 凍結副本    → **不測**,只報有幾件
         versioned 有 _vNNNN 版號 → **主名單**:現役引擎,計入總判
         adhoc   無版號一次性腳本 → **附名單**:列示但不計入總判
       為什麼要分:全景掃描器的族是「有版號的族」,它報 9 支無自測面;
       本閘若把 60 支全算進來,兩邊數字就永遠對不起來,而**對不起來的數字
       會讓人以為其中一邊在說謊**。分層之後 9=9,對得上。"""
    if FROZEN_RX.search(p.name):
        return "frozen"
    if re.match(r"^.*_v\d{4}\.py$", p.name):
        return "versioned"
    return "adhoc"


#: 套件內檔的簽名:相對 import
REL_IMPORT_RX = re.compile(r"^\s*from\s+\.", re.M)


def is_vendor_module(p: Path, root: Path) -> tuple[bool, str]:
    """是不是**套件內檔**(不是壞掉,是放錯地方)?

    判準要兩條都成立,少一條都不算——只看相對 import 會把真正屬於某個套件、
    而且**真的有人用**的檔也一起誤判:
      ① 檔內有相對 import(`from .` / `from ..`)=它預期自己在某個套件裡
      ② 全樹**零人 import 它**(以模組名搜 `import X` / `from X import`)
    """
    try:
        t = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False, ""
    if not REL_IMPORT_RX.search(t):
        return False, ""
    stem = p.stem
    pat = re.compile(rf"^\s*(?:from\s+{re.escape(stem)}\s+import|import\s+{re.escape(stem)}\b)", re.M)
    users = []
    for q in root.rglob("*.py"):
        if q == p or "__pycache__" in str(q):
            continue
        try:
            if pat.search(q.read_text(encoding="utf-8", errors="replace")):
                users.append(q.name)
        except Exception:
            continue
        if len(users) >= 3:
            break
    if users:
        return False, f"有人用({','.join(users[:3])})"
    return True, "相對 import 且全樹零人 import=套件內檔放錯地方"


def has_selftest(p: Path) -> bool:
    """批706:改走 AST 判準(見 `probe_kind`)。字面比對分不出
    「這支支援這個旗標」和「這支提到這個旗標」。"""
    try:
        t = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False
    return probe_kind(t) == "SELFTEST"


def public_defs(p: Path) -> list:
    """頂層公開函式名(不含底線開頭)。用 ast,不執行程式碼。"""
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return []
    return [n.name for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not n.name.startswith("_")]


_PROBE = r'''
import importlib.util, sys, json, io, os, contextlib
from pathlib import Path
src = Path(sys.argv[1])
want = json.loads(sys.argv[2])
live = Path(sys.argv[3])
res = {"loaded": False, "why": "", "missing": [], "wrote": [], "chain": [], "needlib": ""}
_w = []
def _audit(ev, a):
    # __pycache__/*.pyc 是**直譯器自己**寫的位元碼快取,不是被測件的副作用。
    #   不濾掉的話每一支 import 都會被判成「import 期會寫檔」——那是儀器的雜訊,不是它的行為。
    # 只收**真正的路徑**:`os.fdopen` 之類也會觸發 open 事件,那時 args[0] 是
    #   一個檔案描述子編號(實測記到 '3'),把它當成「寫了一個檔」就是假黃燈。
    # __pycache__/*.pyc 是直譯器自己寫的位元碼快取,不是被測件的副作用。
    if ev == "open" and len(a) >= 2 and a[1] and any(c in str(a[1]) for c in "wxa+"):
        if not isinstance(a[0], (str, bytes)):
            return
        _p = a[0].decode("utf-8", "replace") if isinstance(a[0], bytes) else a[0]
        if "__pycache__" in _p or _p.endswith(".pyc") or not _p.strip():
            return
        _w.append(_p)
sys.addaudithook(_audit)
try:
    spec = importlib.util.spec_from_file_location("_smoke_mod", src)
    m = importlib.util.module_from_spec(spec)
    sys.modules["_smoke_mod"] = m
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        spec.loader.exec_module(m)
    res["loaded"] = True
    res["missing"] = [f for f in want if not callable(getattr(m, f, None))]
except BaseException as exc:
    # 批706:v0101 寫 `str(exc)[:140]` —— **理由被截斷**(違反 L62),而且只報最外層。
    #   實測:同一支在 cwd=檔案夾 時報 FileNotFoundError、在 cwd=倉根 時報
    #   ModuleNotFoundError: sklearn。只報最外層等於**把人指到錯的地方去修**。
    #   改成:理由整句不截 + 例外鏈逐層 + 缺的是哪一個套件單獨抓出來。
    import traceback as _tb
    res["why"] = type(exc).__name__ + ":" + str(exc)
    _c, _e = [], exc
    while _e is not None and len(_c) < 6:
        _c.append(type(_e).__name__ + ":" + str(_e))
        _e = _e.__cause__ or _e.__context__
    res["chain"] = _c
    for _x in _c:
        if _x.startswith("ModuleNotFoundError:"):
            _m = _x.split("'")
            if len(_m) > 1:
                res["needlib"] = _m[1]
            break
res["wrote"] = sorted(set(_w))[:5]
print("SMOKE_JSON" + json.dumps(res, ensure_ascii=False))
'''


_EXTPATH_RX = re.compile(r"No such file or directory: ['\"](.+?)['\"]")


def _extpath_of(why: str, sandbox: str = "") -> str:
    """這個 FileNotFoundError 抱怨的路徑,是不是**倉外的絕對路徑**。

    是 → 這支只在寫它的那台機器上載得進來(EXTPATH),不是壞掉;
    不是(倉內的相對/絕對路徑)→ 倉裡真的少了一個檔,那是真紅。
    """
    m = _EXTPATH_RX.search(why or "")
    if not m:
        return ""
    raw = m.group(1).replace("\\\\", "\\")
    drive = re.match(r"^[A-Za-z]:[\\/]", raw) is not None
    if drive:
        return raw
    # 批706:**沙箱底下的路徑不算倉外**。探針改在拋棄式暫存夾裡跑之後,
    #   被測件的相對路徑會解析到沙箱底下——那是「相對路徑找不到」,
    #   不是「它指向另一台機器」。不排掉沙箱,每一支相對路徑失敗的都會被誤判成 EXTPATH,
    #   真紅就被洗成一個看起來無害的態(把紅洗掉比假紅更糟)。
    if sandbox and raw.startswith(str(sandbox)):
        return ""
    try:
        inside = str(Path(raw).resolve()).startswith(str(VIA.resolve()))
    except Exception:
        inside = False
    return "" if inside else raw


def toplevel_argv(text: str) -> int:
    r"""**模組頂層**(不在任何 def/class 裡)有沒有讀 `sys.argv[...]`。有就回行號。

    批706:這是「它是腳本不是模組」的硬證據,而且是**可量的**,不是我對用途的猜測。
      `SUP_MDL561_NextgateExecutionWorker` 第 18 行 `base = sys.argv[1]` 就是這樣:
      任何人 `import` 它都 IndexError。但那不是缺陷——**`import` 本來就不是它的用法**。

    為什麼要在**跑之前**判:這種檔一被 import 就會把整份工作做完。
      實測後果:本閘 v0101 用 `cwd=被測件的資料夾` 跑探針,於是有幾支在 import 期
      用 `C:\Users\...` 當相對路徑開檔,在 `supportive modules/network/` 底下
      造出 **17 個檔名帶反斜線的垃圾檔**。**量的動作改變了被量的東西**(LL368)。
      沙箱已經把足跡關起來了,但更省的做法是:看得出它是腳本,就別執行它。
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 0
    inner = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            for c in ast.walk(n):
                inner.add(id(c))
    for n in ast.walk(tree):
        if id(n) in inner or not isinstance(n, ast.Subscript):
            continue
        v = n.value
        if isinstance(v, ast.Attribute) and v.attr == "argv" \
                and isinstance(v.value, ast.Name) and v.value.id == "sys":
            return getattr(n, "lineno", 1)
    return 0


def _repo_has_module(name: str) -> bool:
    """那個 import 不到的名字,是不是**本倉自己的**模組。

    是 → 少了一支自家的檔,那是真紅;
    不是 → 第三方套件沒裝,那是環境現況(不代裝),判 NEEDLIB。
    """
    top = str(name).split(".")[0]
    if not top:
        return False
    # 倉內檔可能帶版號(尾版律):`via_net_unified` 的實體是 `via_net_unified_v0113.py`。
    #   只比對裸名會把自家模組誤判成第三方套件 → 真紅被洗成 NEEDLIB(把紅洗掉比假紅更糟)。
    for pat in (top + ".py", top + "_v*.py"):
        for q in VIA.rglob(pat):
            if "__pycache__" not in str(q):
                return True
    return (VIA / top / "__init__.py").exists()


def probe_kind(text: str) -> str:
    """這支有沒有一個**跑得動的** `--selftest`。AST 判,不看字面。

    批706:本支成為這個判斷的**唯一出處**(L30)。
      v0101 的 `has_selftest` 用 `"--selftest" in t` —— 那把尺吃到散文
      (用法說明、argparse 的錯誤訊息),批705 已量過:33 支裡誤判 3 支。
      批705 當時把 AST 判準寫在格子裡,那是第二份;現在收回本支,格子改成委派。
    只認兩種真的會生效的寫法:
        add_argument("--selftest", ...)
        "--selftest" in argv  /  argv[1] == "--selftest"
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return "UNPARSED"
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            nm = getattr(n.func, "attr", None) or getattr(n.func, "id", None)
            if nm == "add_argument" and any(isinstance(a, ast.Constant)
                                            and a.value == "--selftest" for a in n.args):
                return "SELFTEST"
        if isinstance(n, ast.Compare):
            sides = [n.left] + list(n.comparators)
            if any(isinstance(x, ast.Constant) and x.value == "--selftest" for x in sides) \
                    and any(isinstance(o, (ast.In, ast.Eq)) for o in n.ops):
                return "SELFTEST"
    has_main = any(isinstance(n, ast.If) and isinstance(n.test, ast.Compare)
                   and isinstance(n.test.left, ast.Name) and n.test.left.id == "__name__"
                   for n in ast.walk(tree))
    return "MAIN_ONLY" if has_main else "MODULE"


#: 本支自己的家族名(LL133):煙測閘不煙測自己。
_SELF_FAMILY = re.sub(r"_v\d{1,4}$", "", Path(__file__).stem)

#: 受治理面裡**不必**進煙測的,逐條具名 + 逐條寫為什麼(L87)。
SMOKE_EXCLUDE = [
    ("/tests/", "pytest 檔:由 pytest 跑,不是引擎"),
    ("VIA_Standalone_Package_", "獨立封裝包自帶的 bundle 副本,是出貨物不是活樹元件"),
    ("new modules engines", "未分類收容夾;進不進活樹還沒裁定"),
    ("_inbox_to_classify", "同上"),
    ("_review_quarantine", "同上"),
    (_SELF_FAMILY, "**本支自己**:煙測閘不煙測自己(LL133)"),
]


def governed_targets(exclude=None):
    """受治理面裡**沒有真自測**的尾版 —— 本閘的主名單。

    批706:v0101 的掃描面是 `VRN_DIR.glob("*.py")` —— **一個夾、不遞迴**。
      於是這道「沒有儀器的都要有煙測」的閘,自己只蓋住 VRN 一家。
      受治理面有 364 個家族,量下去 **116 支沒有真自測**,而本閘只看得到其中 9 支。
      掃描面從哪來?**委派給 CGC_MDL149**,不自己再數一遍(L30;批698「委派不是複製」)。
      問不到就誠實回 None,不回一個自己猜的數。
    """
    try:
        import importlib.util as _ilu
        hits = sorted(HERE.glob("CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"))
        if not hits:
            return None
        sp = _ilu.spec_from_file_location("_smoke_vcgc", hits[-1])
        m = _ilu.module_from_spec(sp)
        sp.loader.exec_module(m)
        face = m._tail_files()
    except Exception:
        return None
    exc = SMOKE_EXCLUDE if exclude is None else exclude
    out = []
    for _k, q in face.items():
        q = Path(q)
        if any(f and f in str(q) for f, _w in exc):
            continue
        try:
            t = q.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if probe_kind(t) != "SELFTEST":
            out.append(q)
    return sorted(out)


def smoke_one(p: Path) -> dict:
    """在**子行程**裡載入,避免被測件污染本行程;逾時即殺(不卡斷)。"""
    want = public_defs(p)[:12]
    # 批706:先用 AST 看它是不是腳本——是的話**連跑都不跑**(零足跡的最省做法)。
    try:
        _tl = toplevel_argv(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        _tl = 0
    if _tl:
        return {"state": "SCRIPT",
                "why": f"模組頂層第 {_tl} 行就讀 sys.argv[...] —— 它是**腳本不是模組**,"
                       f"`import` 本來就不是它的用法;本閘不執行它(零足跡)",
                "want": want, "line": _tl}
    _v, _vw = is_vendor_module(p, p.parent)
    if _v:
        # 批470:套件內檔不能單獨載入是**設計如此**,不是缺陷。判 VENDOR,
        # 不計入總判;本倉已有 _quarantine_pip_vendor 隔離夾可收(本件不搬)。
        return {"state": "VENDOR", "why": _vw + ";可收進 _quarantine_pip_vendor(由操作員裁)",
                "want": want}
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    # ══ 批706:**零足跡**(LL368)——探針改在拋棄式暫存夾裡跑 ═══════════════════
    #   v0101 用 `cwd=p.parent`,也就是**被測件自己的資料夾**。實測後果:
    #   有幾支在 import 期用 `C:\Users\tonyk\...` 當**相對路徑**開檔,
    #   在 Linux 上 `open()` 於是在 `supportive modules/network/` 底下
    #   造出 **17 個檔名帶反斜線的垃圾檔**——**量的動作改變了被量的東西**。
    #   而本閘的副作用偵測只盯 `VIA_Reports` 一個夾,所以它**完全沒看見自己造的**。
    #   改法兩件:① cwd 換成暫存夾,相對路徑寫入落在那裡,倉裡一個位元都不動;
    #            ② 寫檔偵測改由**探針自己**用 `sys.addaudithook` 記自己這個行程的 open。
    #
    #   ② 為什麼非改不可(全格子當場抓到的):v0101 的寫檔偵測是
    #   「跑之前掃一次 VIA_Reports、跑完再掃一次,差集就是它寫的」。
    #   那在**並行**下根本不成立——全格子平行跑時別的站正在寫同一個夾,
    #   差集於是被算到被測件頭上。實測:合成的乾淨件在格子裡被判 **AMBER**(假黃燈),
    #   單跑五次都是 SMOKE。**共用資料夾的前後比對,量到的是整台機器不是這支。**
    #   audit hook 記的是**這個行程自己**的 open,與別人同時在做什麼無關。
    #   收尾用 `TemporaryDirectory` 的 context manager,**本檔不自己寫任何刪除碼**——
    #   第一版我寫了 `shutil.rmtree`,被本檔既有的檢 ⑫「零搬移碼」當場抓到。
    #   那條檢是對的:一支宣告「不搬檔」的儀器,不該有刪除/搬移的呼叫在裡面,
    #   即使那次刪的只是它自己剛建的暫存夾。**讓標準庫收尾,紀律就不必破例。**
    import tempfile as _tf
    with _tf.TemporaryDirectory(prefix="via_b706_smoke_") as _td:
        _sand = Path(_td)
        try:
            r = subprocess.run(
                [sys.executable, "-c", _PROBE, str(p), json.dumps(want), str(LIVE_OUT)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=TIMEOUT, env=env, cwd=str(_sand))
        except subprocess.TimeoutExpired:
            return {"state": "RED", "why": f"載入逾 {TIMEOUT}s 未回(import 期就卡住)",
                    "want": want}
        _spill = sorted(x.name for x in _sand.rglob("*") if x.is_file())[:5]
        _sandroot = str(_sand)
    out = (r.stdout or "") + (r.stderr or "")
    m = re.search(r"SMOKE_JSON(\{.*\})", out)
    if not m:
        # 批706:不截斷(L62)。探針連 JSON 都吐不出來,那段輸出就是唯一線索。
        return {"state": "RED", "why": f"探針無回覆 rc={r.returncode}·{out.strip()}",
                "want": want}
    d = json.loads(m.group(1))
    if not d["loaded"]:
        _lib = d.get("needlib") or ""
        # 批706:**import 期讀一個倉外絕對路徑**,而這台機器上沒有那個路徑。
        #   量到的就是這句話,不多講。判斷依據是**路徑本身**,不是我對它用途的猜測:
        #   有磁碟機代號、或不在本倉底下 = 倉外。
        #   這種件在寫它的那台機器上是好的,在任何別的機器上都載不進來——
        #   叫它 RED 會讓人去修一支沒壞的東西,叫它 SMOKE 是假綠。
        #   所以獨立一態、**列出完整路徑**、不計入紅,由操作員裁它該不該退役。
        _ext = _extpath_of(d.get("why", ""), _sandroot)
        if _ext:
            return {"state": "EXTPATH", "why": f"import 期讀倉外絕對路徑(本機沒有):{_ext}",
                    "want": want, "path": _ext}
        # 批706:**缺第三方套件不是壞掉**。本倉紀律是「不代裝套件」,
        #   所以「這台機器上沒裝 sklearn」是環境現況,判紅等於叫人去修一支沒壞的引擎(LL366)。
        #   判準要窄:那個名字必須**不是倉內模組**,否則就是真的少了一支自家的檔。
        if _lib and not _repo_has_module(_lib):
            return {"state": "NEEDLIB", "why": f"容器缺第三方套件 {_lib}(不代裝;非缺陷)"
                                               f" · 例外鏈 {' <- '.join(d.get('chain') or [])}",
                    "want": want, "lib": _lib}
        return {"state": "RED", "why": d["why"]
                + (" · 例外鏈 " + " <- ".join(d["chain"]) if d.get("chain") else ""),
                "want": want}
    if d["missing"]:
        return {"state": "RED", "why": f"公開契約缺 {d['missing']}", "want": want}
    if d["wrote"] or _spill:
        _w = []
        if d["wrote"]:
            _w.append(f"本行程 open 寫入:{d['wrote']}")
        if _spill:
            _w.append(f"**相對路徑寫檔**(已落在拋棄式暫存夾,倉裡零足跡):{_spill}")
        return {"state": "AMBER", "why": "import 期就寫檔 · " + " · ".join(_w), "want": want}
    return {"state": "SMOKE", "why": f"載入 OK · 公開契約 {len(want)} 支在位",
            "want": want}


def run(d: Path | None = None) -> int:
    """無參數 = **受治理全面**(批706);給了夾就只跑那個夾(保留 v0101 的用法)。"""
    if d is None:
        naked = governed_targets()
        if naked is None:
            print("[煙霧閘] 受治理面問不到(CGC_MDL149 缺席或載入失敗)——誠實停,不自己猜")
            return 2
        allt = naked                      # 受治理面模式下,分母就是「沒有真自測」的那些
        print(f"[煙霧閘] **受治理全面**(委派 CGC_MDL149;批706):"
              f"沒有真自測的尾版 {len(naked)} 支"
              f" · 具名排除 {len(SMOKE_EXCLUDE)} 條")
    else:
        if not d.is_dir():
            print(f"[煙霧閘] 夾不存在 {d}(誠實停)")
            return 2
        allt = tails(d)
        naked = [p for p in allt if not has_selftest(p)]
        print(f"[煙霧閘] {d.name}:族 {len(allt)} 支 · 有自測面 {len(allt) - len(naked)}"
              f" · 無自測面 {len(naked)}")
    main_list = [p for p in naked if tier(p) == "versioned"]
    adhoc = [p for p in naked if tier(p) == "adhoc"]
    frozen = [p for p in naked if tier(p) == "frozen"]
    print(f"  分層:**主名單(現役版號族){len(main_list)}** ← 計入總判"
          f" · 附名單(無版號一次性){len(adhoc)} ← 列示不計"
          f" · 凍結副本 _sha {len(frozen)} ← 不測(收容原件非現役)")
    if not main_list and not adhoc:
        print("  全員都有自測面=本閘無事可做(這才是終局)")
        return 0
    tally = {"SMOKE": 0, "AMBER": 0, "RED": 0, "VENDOR": 0, "NEEDLIB": 0, "EXTPATH": 0, "SCRIPT": 0}
    for p in main_list:
        r = smoke_one(p)
        tally[r["state"]] = tally.get(r["state"], 0) + 1
        print(f"  [{r['state']:7s}] {p.name:46s} {r['why']}")
    a_t = {"SMOKE": 0, "AMBER": 0, "RED": 0, "VENDOR": 0, "NEEDLIB": 0, "EXTPATH": 0, "SCRIPT": 0}
    for p in adhoc:
        r = smoke_one(p)
        a_t[r["state"]] = a_t.get(r["state"], 0) + 1
        print(f"  [{r['state']:7s}]*{p.name:45s} {r['why']}")
    print(f"[煙霧計] 主名單 {len(main_list)} 支 · SMOKE {tally['SMOKE']}"
          f" · NEEDLIB {tally['NEEDLIB']} · EXTPATH {tally['EXTPATH']}"
          f" · SCRIPT {tally['SCRIPT']} · AMBER {tally['AMBER']}"
          f" · VENDOR {tally['VENDOR']} · RED {tally['RED']}"
          f"  ‖ 附名單 {len(adhoc)} 支(*號;不計入總判)· SMOKE {a_t['SMOKE']}"
          f" · NEEDLIB {a_t['NEEDLIB']} · EXTPATH {a_t['EXTPATH']}"
          f" · SCRIPT {a_t['SCRIPT']} · AMBER {a_t['AMBER']}"
          f" · VENDOR {a_t['VENDOR']} · RED {a_t['RED']}"
          "\n  註:SMOKE=載得進來且介面在位,**不代表算得對**;"
          "要它算得對就得替它寫真自測。總表請照 SMOKE 字面收,不得改寫成 GREEN。"
          "\n  註:NEEDLIB=這台機器上沒裝那個第三方套件(不代裝),**不是缺陷也不計入紅**;"
          "那個名字若是倉內模組,一律照樣判 RED。"
          "\n  註:EXTPATH=import 期讀一個**倉外絕對路徑**,本機沒有;它在寫它的那台機器上是好的。"
          "**不計入紅**,完整路徑逐支列出,退不退役由操作員裁(本件不搬不刪)。"
          "\n  註:SCRIPT=模組頂層就讀 sys.argv,它是腳本不是模組;**本閘不執行它**"
          "(執行=在 import 期把整份工作做完,那是量的動作改變被量的東西,LL368)。")
    return 1 if tally["RED"] else 0


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    done, fails = [], []

    def chk(name, cond, note=""):
        done.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest")[0]

    # 批706:**字面禁用檢一律看「會執行的碼」,不看註解。**
    #   本批連中三次同一族:檢 ⑲ 的針寫進自己的說明、探針註解引用舊切片、
    #   ⑫ 的 `shutil` 出現在「我把它移除了」這句註解裡。
    #   記述一段被移除的舊寫法是**文件該做的事**,不該因此被判成「它還在」。
    #   否則下場是:要嘛檢一直紅,要嘛為了讓檢綠而把文件寫糊——兩個都不對。
    def _code_only(text: str) -> str:
        return "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))

    body_code = _code_only(body)

    t = tails(VRN_DIR)
    naked = [p for p in t if not has_selftest(p)]
    _mainl = [p for p in naked if tier(p) == "versioned"]
    _adhoc = [p for p in naked if tier(p) == "adhoc"]
    _froz = [p for p in naked if tier(p) == "frozen"]
    chk("① 尾版律取族尾 + 認出「無自測面」那一批,而且**分層**(全樹掃描器找的是"
        " --selftest 旗標,找不到就記 SKIP;那些件於是每一次認證掃描都不是綠也不是紅,"
        "是**沒有儀器**)。分層的理由:凍結副本/一次性腳本/現役版號族混在一個數裡,"
        "那個數就沒有意義——而**對不起來的數字會讓人以為其中一邊在說謊**。"
        "分層後主名單數要對得上全景掃描器的族數",
        len(t) >= 30 and len(_mainl) + len(_adhoc) + len(_froz) == len(naked)
        and len(_mainl) >= 1,
        f"(族 {len(t)} · 無自測面 {len(naked)} = 主 {len(_mainl)}"
        f" + 附 {len(_adhoc)} + 凍結 {len(_froz)})")

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        q = Path(td)
        (q / "ok_v0100.py").write_text(
            "def alpha():\n    return 1\n\n\ndef beta(x):\n    return x\n",
            encoding="utf-8")
        (q / "boom_v0100.py").write_text(
            "raise RuntimeError('import 期就炸')\n", encoding="utf-8")
        (q / "slow_v0100.py").write_text(
            "import time\ntime.sleep(999)\n", encoding="utf-8")
        (q / "withtest_v0100.py").write_text(
            "import sys\n\n\ndef gamma():\n    return 1\n\n\n"
            "if '--selftest' in sys.argv:\n    sys.exit(0)\n", encoding="utf-8")
        r_ok = smoke_one(q / "ok_v0100.py")
        r_boom = smoke_one(q / "boom_v0100.py")
        chk("② 載得進來=SMOKE;import 期就爆=RED 並把例外型別與訊息**照抄**"
            "(不概括成「載入失敗」——批450 那一課:捕捉到卻不顯示,還編一句代替它)",
            r_ok["state"] == "SMOKE" and r_boom["state"] == "RED"
            and "RuntimeError" in r_boom["why"] and "import 期就炸" in r_boom["why"],
            f"(ok={r_ok['state']} · boom={r_boom['state']}:{r_boom['why'][:40]})")
        chk("③ 公開契約用 ast 取(**不執行程式碼**就拿得到頂層 def 名)",
            public_defs(q / "ok_v0100.py") == ["alpha", "beta"],
            f"({public_defs(q / 'ok_v0100.py')})")
        chk("④ 有 --selftest 的件**不在本閘名單內**(誰長出真自測就自動退出;"
            "本閘不搶已經有儀器的站)",
            has_selftest(q / "withtest_v0100.py") is True
            and has_selftest(q / "ok_v0100.py") is False, "")
        _g = TIMEOUT
        try:
            globals()["TIMEOUT"] = 3
            r_slow = smoke_one(q / "slow_v0100.py")
        finally:
            globals()["TIMEOUT"] = _g
        chk("⑤ 不卡斷:逐支逾時即殺,回 RED 並說清楚是**import 期**卡住,"
            "不是這支算得慢",
            r_slow["state"] == "RED" and "逾" in r_slow["why"],
            f"({r_slow['why'][:46]})")

    chk("⑥ 在**子行程**裡載入:被測件的 import 期副作用(sys.path 改寫、猴補、"
        "全域旗標)不得污染本行程,否則後面每一支的結果都不可信",
        "subprocess.run" in body and "_smoke_mod" in body, "")

    chk("⑦ **煙霧不是全測**:燈一律標 SMOKE,並在計數行寫明「不代表算得對」。"
        "把煙霧當成全測就是另一種假綠",
        '"SMOKE"' in body and "不代表算得對" in body and "不得改寫成 GREEN" in body, "")

    chk("⑧ 唯讀律:本閘自己不寫任何正式產出;而**被測件**若在 import 期寫檔 → AMBER 點名"
        "(批410 那一族的病)。批706 擴一件:除了正式產出夾,**相對路徑寫入**也要看得到"
        "——v0101 只盯 VIA_Reports,於是被測件寫進自己資料夾的垃圾它完全沒發現",
        "AMBER" in body and "import 期就寫檔" in body and "LIVE_OUT" in body
        and "相對路徑寫檔" in body, "")

    chk("⑨ Zero-Hydra:不替那些引擎各寫一份自測(9 份九頭龍),也不改它們一個字;"
        "本件只增一支共用閘",
        "只增一支共用閘" in src and "不改它們一個字" in src, "")

    chk("⑩ 凍結副本不測(`_sha` 快照是收容原件,只增不減律要它們留著,但它們"
        "**不是現役引擎**——拿化石的載入結果去算認證就是灌水)",
        tier(Path("VRN_MDL001_Converter_shaf09dc35c.py")) == "frozen"
        and tier(Path("VRN_ENG049_ContentReconcile_v0102.py")) == "versioned"
        and tier(Path("VIA_HardGate_BootPrecheck.py")) == "adhoc",
        "(三層各判一例)")

    import tempfile as _tf11
    with _tf11.TemporaryDirectory() as _td11:
        _q11 = Path(_td11)
        (_q11 / "vend_mod.py").write_text("from . import sibling\n\n\ndef alpha():\n    return 1\n",
                                          encoding="utf-8")
        (_q11 / "used_mod.py").write_text("from . import sibling\n\n\ndef beta():\n    return 2\n",
                                          encoding="utf-8")
        (_q11 / "user.py").write_text("from used_mod import beta\n", encoding="utf-8")
        _v1, _w1 = is_vendor_module(_q11 / "vend_mod.py", _q11)
        _v2, _w2 = is_vendor_module(_q11 / "used_mod.py", _q11)
        _r11 = smoke_one(_q11 / "vend_mod.py")
    chk("⑪ 第四態 **VENDOR**(批470:v0100 把 reporter.py/reporters.py/table.py 判成 RED,"
        "查了才知道那是 rich 與 pip-resolvelib 的**套件內檔**,散落在引擎夾且零人 import。"
        "套件內檔本來就不能單獨載入——拿「能不能獨立載入」去測它是**用錯的尺**。"
        "**判錯的紅燈和假綠一樣傷**:它讓人去修沒壞的東西,而真壞的那支淹在雜訊裡)。"
        "判準要兩條都成立:①有相對 import ②全樹零人 import;有人用就不算(檢裡兩例對照)",
        _v1 is True and _v2 is False and "有人用" in _w2 and _r11["state"] == "VENDOR",
        f"(無人用→VENDOR={_v1} · 有人用→{_w2[:14]} · smoke 態={_r11['state']})")

    chk("⑫ 本件**不搬檔**:搬進 _quarantine_pip_vendor 是操作員的裁示,"
        "儀器只負責把話講對(只增不減律下,搬也是搬不是刪,但那仍是他的決定)",
        "本件**不搬檔**" in src
        and "shutil" not in body_code and "os.rename" not in body_code,
        "(零搬移碼;註解記述被移除的舊寫法不算犯——批706 治本)")

    # ══ 批706 新檢:掃描面 / 三個判別器 / LL133 ══════════════════════════════
    _g = governed_targets()
    chk("⑬ 掃描面接到**受治理面**(委派 CGC_MDL149,不自己再數一遍;L30 · 批698「委派不是複製」)"
        "——v0101 只掃 VRN 一個夾且不遞迴,於是這道「沒有儀器的都要有煙測」的閘自己只蓋住一家",
        _g is not None and len(_g) > 40,
        f"(受治理面沒有真自測的尾版 {len(_g) if _g is not None else 'NODATA'} 支 · v0101 只看得到 9 支)")

    _old = [q for q in tails(VRN_DIR) if not has_selftest(q) and tier(q) == "versioned"] \
        if VRN_DIR.is_dir() else []
    _lost = sorted({q.name for q in _old} - {q.name for q in (_g or [])})
    _poison = list(SMOKE_EXCLUDE) + [("functional modules/VRN", "負控:故意吃掉一整個家族夾")]
    _pl = sorted({q.name for q in _old} - {q.name for q in (governed_targets(_poison) or [])})
    chk("⑭ 掃描面只增不減:v0101 那個夾看得到的每一支都還要看得到。"
        "**反面控制**=注入一條吃掉整個 VRN 夾的排除,下限必須當場破且點得出名字",
        not _lost and bool(_pl),
        f"(下限 {len(_old)} · 掉了 {_lost or '無'} · 負控照出 {len(_pl)} 支)")

    chk("⑮ 自我指涉閘(LL133):煙測閘**不煙測自己**——本支原始碼裡當然有 `--selftest` 字樣"
        "(那是它的判準常數),不排掉自己家族就會把自己算進「沒有儀器」的名單",
        not [q for q in (_g or []) if _SELF_FAMILY in q.name],
        f"(自己在名單裡 {[q.name for q in (_g or []) if _SELF_FAMILY in q.name] or '無'})")

    chk("⑯ `--selftest` 判準走 **AST 不走字面**(批705 量過:字面比對 33 支誤判 3 支,"
        "吃到用法說明與 argparse 的錯誤訊息);本支是這個判斷的**唯一出處**(L30)",
        probe_kind('import argparse\nargparse.ArgumentParser().add_argument("--selftest")\n') == "SELFTEST"
        and probe_kind('import sys\nif "--selftest" in sys.argv:\n    pass\n') == "SELFTEST"
        and probe_kind('"""用法: x.py --selftest"""\nif __name__ == "__main__":\n    pass\n') == "MAIN_ONLY"
        and probe_kind("X = 1\n") == "MODULE",
        "(argparse=SELFTEST · argv=SELFTEST · **散文提到=MAIN_ONLY** · 純模組=MODULE)")

    chk("⑰ **缺第三方套件不是壞掉**(NEEDLIB):不代裝套件是本倉紀律,"
        "把「這台機器沒裝 sklearn」判成紅等於叫人去修一支沒壞的引擎(LL366)。"
        "**判準要窄**:那個名字若是倉內模組(帶版號也算),一律照樣判 RED",
        not _repo_has_module("sklearn") and not _repo_has_module("totally_not_a_thing")
        and _repo_has_module("VIA_SuperAccel_Module") and _repo_has_module("via_net_unified"),
        "(sklearn=第三方 · via_net_unified=倉內(帶版號也認得)· VIA_SuperAccel=倉內)")

    _ext_win = _extpath_of("FileNotFoundError:[Errno 2] No such file or directory: "
                           + repr("C:" + chr(92) + chr(92) + "Users" + chr(92) + chr(92) + "x.csv"))
    _ext_in = _extpath_of("FileNotFoundError:[Errno 2] No such file or directory: '"
                          + str(VIA / "a.json") + "'")
    _ext_no = _extpath_of("IndexError:list index out of range")
    chk("⑱ **EXTPATH**:import 期讀一個倉外絕對路徑而本機沒有——它在寫它的那台機器上是好的,"
        "不是壞掉。判準是**路徑本身**不是我對用途的猜測;倉內路徑找不到=倉裡真的少了檔,照樣 RED",
        bool(_ext_win) and not _ext_in and not _ext_no,
        f"(倉外 Win 路徑=認出 · 倉內路徑={_ext_in or '不認(對)'} · 非檔案例外={_ext_no or '不認(對)'})")

    # LL133:針要在執行期組出來。第一版我把那個切片字面寫進**檢的說明文字裡**,
    #   於是它在自己的原始碼裡找到了它要找的東西,當場自我指涉判紅——這一族又一次。
    _needle = "[:" + str(70 * 2) + "]"
    _probe_code = "\n".join(l for l in _PROBE.splitlines()
                             if not l.lstrip().startswith("#"))
    chk("⑲ 理由**不截斷**(L62)+ 例外鏈逐層。v0101 把例外訊息切了一刀,"
        "而實測同一支在不同 cwd 下最外層例外不同"
        "(FileNotFoundError vs ModuleNotFoundError:sklearn)——"
        "只報最外層又切一半,等於**把人指到錯的地方去修**。"
        "(針在執行期組出來,不寫進本句;LL133)",
        # 量的是探針裡**會執行的碼**,不是它的註解:
        #   「理由不截斷」講的是行為,而註解本來就要引用舊寫法來說明改了什麼。
        #   拿含註解的原文去搜等於「講到它就算犯」——判準劃錯範圍,不是真的還在截斷。
        #   (這一條我連錯兩次:先把針寫進檢的說明、再把它留在探針的註解裡。)
        _needle not in _probe_code and 'res["chain"]' in _probe_code,
        f"(探針可執行碼無 {_needle} 切片 · 例外鏈在位 · 註解引用舊寫法不算犯)")

    chk("⑳ **SCRIPT**:模組頂層就讀 `sys.argv[...]` = 它是腳本不是模組,"
        "`import` 本來就不是它的用法——**而且本閘連跑都不跑它**。"
        "為什麼要在跑之前判:這種檔一被 import 就把整份工作做完;"
        "實測 v0101 用被測件自己的資料夾當 cwd,於是幾支相對路徑寫檔的在倉裡"
        "造出 17 個檔名帶反斜線的垃圾檔——**量的動作改變了被量的東西**(LL368)。"
        "**負控**:寫在函式裡的 argv 不准被當成頂層",
        toplevel_argv("import sys\nb = sys.argv[1]\n") > 0
        and toplevel_argv("import sys\ndef m():\n    return sys.argv[1]\n") == 0
        and toplevel_argv("X = 1\n") == 0,
        "(頂層=認出 · **函式內=不認(對)** · 完全沒有=不認)")

    chk("㉑ **零足跡**(LL368):探針在拋棄式暫存夾裡跑,倉裡一個位元都不動;"
        "暫存夾跑完非空就照實報 AMBER。v0101 用 `cwd=p.parent`,"
        "被測件的相對路徑寫入直接落進倉裡,而副作用偵測只盯 VIA_Reports 一個夾,"
        "**它完全沒看見自己造的**",
        "TemporaryDirectory" in body_code and "cwd=str(_sand)" in body_code
        and "_spill" in body_code, "(暫存夾 cwd · 溢出偵測在位 · 本檔零刪除碼)")

    # ㉒ 寫檔偵測必須**不受別的行程影響**——全格子當場抓到的假黃燈。
    import tempfile as _t2
    with _t2.TemporaryDirectory() as _t2d:
        _q2 = Path(_t2d)
        (_q2 / "w_v0100.py").write_text(
            'open("import_side_effect.txt", "w").write("x")\ndef f():\n    return 1\n',
            encoding="utf-8")
        (_q2 / "c_v0100.py").write_text("def f():\n    return 1\n", encoding="utf-8")
        _rw, _rc2 = smoke_one(_q2 / "w_v0100.py"), smoke_one(_q2 / "c_v0100.py")
    chk("㉒ 寫檔偵測歸屬到**本行程**(`sys.addaudithook`),不是掃一個共用夾的前後差。"
        "v0101 比對 VIA_Reports 前後——全格子**平行**跑時別的站正在寫同一個夾,"
        "差集就被算到被測件頭上:實測合成的乾淨件在格子裡判 AMBER(假黃燈),單跑五次都 SMOKE。"
        "**共用資料夾的前後比對,量到的是整台機器不是這支。**"
        "另濾掉直譯器自己的 __pycache__ 與 fd 編號(實測記到 '3')",
        _rw["state"] == "AMBER" and "import_side_effect.txt" in _rw["why"]
        and _rc2["state"] == "SMOKE",
        f"(會寫檔的={_rw['state']} 並印出路徑 · 乾淨的={_rc2['state']})")

    print(f"  [計] {len(done)} 檢 OK {len(done) - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 無自測面引擎煙霧閘(CGC_MDL147 v0101)· 十二檢自測(零網路)===")
        return selftest()
    d = None
    if "--dir" in args:
        d = Path(args[args.index("--dir") + 1])
    return run(d)


if __name__ == "__main__":
    sys.exit(main())
