#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL161_PEISCapabilityEngine v0104 — PEIS 能力引擎(批570:改號——MDL158 撞號了)

v0103→v0104(批586 操作員令「1. yes(備用件也要納入)… 先跟 via / vdf 斷開」)
  本版修的全是**尺沒伸到**那一類。假的零跟假綠是同一件事,而且更難發現——紅燈會有人吵,
  零不會。
  ① 死樹兩族 `retired` / `backup` 起點原本寫死路徑。實測當場打臉:墓園有**兩座**——
     根下 `VIA_RetiredEngines/`(批581 起,**0 支 .py**)與 `functional modules/VIA_RetiredEngines/`
     (批180 起十一波,**261 支**)。寫死根下那座,回報「0 支」,而樹上明明有 261 支。
     備份夾同理,散在 `supportive modules/_nexuscore_*/RUN_*/_backup` 等**七處**。
     兩族一律改走**全樹 glob**:樹上有幾座吃幾座,不靠我記路徑。
  ② **斷開**(操作員令「先跟 via / vdf 斷開」):死樹與活樹不同掃。混掃會把墓園的舊件
     算進活樹的帳,「活樹有幾個重複」這個問題就永遠答不準。同掃回 GATED(rc=4,閘住不是壞)
     並指名兩條各自的令;庫名各帶簽章,兩棵樹兩個庫,不互相蓋。
  ③ 排除詞的**放行門只對本次明示的那一族有效**:沒指名 retired 就照舊排除,
     收容正本(`references/intake`)**永遠**不放行——正本零觸碰沒有例外。
  ④ 讀庫回退原本挑**最新**的庫。剛掃完 retired,最新的就是墓園那本,`run`/`cards` 於是拿
     墓園當能力庫——自測 檢⑱ 當場 FAIL 把它抓出來。改成挑**蓋得最寬的活樹庫**。
     (斷開不是只斷掃描,讀也要斷。)
  +`deadcheck` 動詞:回答操作員真正問的那句「備用件裡有沒有活樹沒有的東西?」
     死樹能力名 × 活樹能力庫對名,輸出**分兩層**,不把第一層當答案——
     批585 量過同一件事:名字只在舊件出現的,絕大多數是改名或重構(348 族疑似 8 族,真掉一族)。
       · only_dead 989 —— 名字只在死樹出現(這一層數字大是正常的,不是紅燈)
       · suspect   105 —— 連詞根都在活樹找不到的(這一層才值得人看)
     壓平葉名那一層是拿實測樣品修出來的:`misc.walkforward` 原本被判「活樹沒有」,
     而活樹有 `misc.walk_forward`——差的只是一條底線。加上壓平比對後 120→105。
  自測 二十一檢 → **二十五檢**。


v0101→v0102(批570 撞號更正):批568 我把這支取名 **CGC_MDL158**,而樹上**早就有** `CGC_MDL158_VIAPanoramaAuditRepair`。
  一個號兩個家族=編號冊的唯一性被我自己破掉,而且我在批570 又用 MDL159 撞了 `CGC_MDL159_VIAUnifiedConsole` 一次。
  兩次都不是誰改壞,是我**取號之前沒掃過樹**。本版改用 **MDL161**(掃過,無人使用);
  舊的 MDL158_PEIS 兩版退役到 `VIA_RetiredEngines/batch570_number_collision/`(只增不減=退役不刪)。
  守衛同批補上:CGC_MDL157 加一檢「同一個編號不得有兩個家族」,基線收錄既有的 MDL142,
  超出基線就報紅——這種事從此由機器抓,不靠我記得。

v0100→v0101(批569 操作員工作站實錄:`via-peis scan --family vdf,vrn` → ABSENT「家族沒有可掃的起點:['vdf vrn']」):
  PowerShell 把 `vdf,vrn` 當**陣列**傳,轉成行程參數時用空白相連,argparse 收到的是**一個字** "vdf vrn"。
  更難看的是:**冊裡早就有這一課**——`ConvertTo-VIACleanArgs` 的註解逐字寫著
  「PowerShell 把 `vrn,vap` 這種逗號寫法當陣列傳進來…不然 "$t" 會變成 "vrn vap",家族驗證就把合法輸入擋掉」。
  我寫 via-peis 時沒走那個輔助函式,於是同一個坑再踩一次。
  兩邊都修(帶腰帶也繫吊帶):① Python 這側切 `[,\s;]+`,任何殼都吃得下;
  ② Register v0216 讓 via-peis 走 ConvertTo-VIACleanArgs。
  另把 ABSENT 的話改成**可行動**:認不得的家族逐一指名,並列出合法家族(L62 敗了就要說得清楚)。

操作員令(批568):「將 session_01FQMN8uBxreDrzmDUpPrXTG 引擎整合進來」+ PEIS 系統說明六功能
  + 「用引擎去執行以節省 TOKEN」+「你自己收留整合後啟動她」。

【先量再說 · 零九頭龍】
  PEIS 那六件功能(搜尋領域→AST 全景→聚眾→低風險合併→完整測試→鎖定→能力抽象→快速截取)
  **已經有一支寫好的正主**:`via_unified_engine.py` v0200(VIA-VIA-ENG996),6,628 行、純標準庫、
  零網路、零安裝、不改來源檔、自測 69/69。那是操作員自己另一個 session 的產出。
  所以這一批**不重寫**——重寫就是第二顆頭(零九頭龍),而且要把別人驗過的 69 檢再驗一次。
  做法是 VIA 的老規矩:**正本收容 + 一個掛線口**。

【正本零觸碰】
  正本放在 `functional modules/VIA_PEIS/references/intake/PEIS_UnifiedEngine_b568/`,
  連同 `_INTAKE_MANIFEST_b568.json`(來源 repo/commit + 每檔 md5/sha256)。
  本檔**一個 byte 都不改它**,只用 subprocess 代跑(它本來就設計成可獨立執行)。
  正本換版=收容夾換一份 + manifest 換一份,本檔的路徑解析走 glob 尾版,零維護。

【誠實四態】
  rc 0=GREEN(有重複、聚成能力、帳算得出來)· 1=RED(引擎自己報錯/守則被破)
  · 2=NODATA(掃得動但**沒有重複** —— 照 PEIS 啟動條件,無重複就不啟動整合,這不是紅燈)
  · 3=ABSENT(收容正本不在)

【紀律(寫在檔頭,因為「整合」最容易偷偷破掉)】
  · **不代設同意閘**:本檔不設任何 VIA_*_CONSENT / API key。
  · **不代裝套件**:正本是純標準庫,本檔也是;缺件就誠實 ABSENT,不裝。
  · **零網路**:自測零網路;代跑時 env 明示 VIA_NET_DISABLED=1。
  · **不改來源**:PEIS 預設 AUDIT/READ_ONLY_SOURCES,本檔**不提供 --apply**——
    能力表落地與引擎鎖定是操作員的裁定(LL90 同族),要落地請直接對正本下 `--apply`。
  · **只增不減**:能力庫與能力表 append-only,本檔只讀不刪。

用法:
  via-peis status                 收容正本在不在 · 版本 · 自測(69 檢)
  via-peis scan  [--family vdf]   INTAKE→SCAN→CLUSTER→TEST→LOCK→ANNOTATE→STORE(AUDIT)
  via-peis cards [--cap X]        能力卡 capsule(AI 只讀卡,不讀全文原始碼)
  via-peis run   <能力> [--params JSON]   快速截取層 RUN(capability, params)
  via-peis report                 token 節省帳 + CME 能力表現況
  via-peis --selftest             本掛線口自測
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
import argparse
import ast
import sqlite3
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
REPORTS = VIA / "VIA_Reports" / "peis"
STORE = REPORTS / "VIA_Capability_Store.sqlite"   # 能力庫(append-only;省略 --db 就只在記憶體=白掃)


def _store_for(fams: list) -> Path:
    """批585 根因修:**能力庫要跟掃描範圍綁在一起**。

    封印(LOCK)是在某一次掃描的 plan 上蓋的。先用 `cgc sup vdf vrn` 掃過、
    再用 `vdf vrn` 掃,上一輪蓋在 cgc/sup 能力上的封印在這一輪的 plan 裡**找不到對應記錄**
    → 收容正本直接 raise「封印指紋沒有對應記錄:load.path」,整支 RED。
    (那支是收容正本,**零觸碰**;所以修在這一層。)

    作法:庫名帶掃描範圍的簽章。範圍一樣就沿用同一個庫(append-only 照舊),
    範圍不一樣就各用各的庫,封印永遠只跟自己的 plan 比對。
    舊的單一庫檔保留不動(只增不減),`--family` 與上次相同時仍讀得到。
    """
    sig = "-".join(sorted({str(x).lower() for x in fams})) or "default"
    return REPORTS / f"VIA_Capability_Store__{sig}.sqlite"


def _store_read(fams: list | None = None) -> Path | None:
    """讀的時候:先找**本範圍**的庫,沒有才回退到舊的單一庫(相容)。

    批586 自測當場抓到的坑:回退是挑**最新**的庫。剛掃完 retired,最新的就是墓園那本,
    `run` / `cards` 於是拿墓園當能力庫——檢⑱ 直接 FAIL。所以回退只在**活樹的庫**裡挑,
    死樹的庫要讀就得明示 `fams`(斷開不是只斷掃描,讀也要斷)。
    """
    if fams:
        p = _store_for(fams)
        if p.is_file():
            return p
    # 回退挑**蓋得最寬的活樹庫**,不挑最新的:最新只代表剛跑過,不代表答得最全。
    return _live_store() or (STORE if STORE.is_file() else None)
INTAKE_GLOB = "functional modules/VIA_PEIS/references/intake/PEIS_UnifiedEngine_b*"

# 家族 → 掃描起點(只給目錄,PEIS 自己遞迴;不觸網、不改檔)
FAMILIES = {
    "vdf": ["functional modules/VDF/engine"],
    "vrn": ["functional modules/VRN"],
    "vap": ["functional modules/VAP/engine"],
    "cgc": ["supportive modules/registry"],
    "sup": ["supportive modules"],
    # 批586 操作員令「備用件也要納入」:退役墓園與備份夾各成一族,**可單掃、不混進活樹**。
    # 用途不是治理它們(它們本來就不在活樹),是回答一個問題:
    # **備用件裡有沒有活樹沒有的東西?** 掃進來才答得出「有/沒有」。
    #
    # 這兩行原本寫死成 `["VIA_RetiredEngines"]` / 單一備份路徑,實測當場打臉:
    #   · 墓園有**兩座**——根下 `VIA_RetiredEngines/`(批581 起,0 支 .py)與
    #     `functional modules/VIA_RetiredEngines/`(批180 起十一波,261 支 .py)。
    #     寫死根下那座 → 掃出 0 支,**假的零**(LL131:分母縮水和分母灌水一樣傷)。
    #   · 備份夾散在 `supportive modules/_nexuscore_*/RUN_*/_backup` 等七處,不是單一路徑。
    # 所以兩族一律走**全樹 glob**:樹上有幾座就吃幾座,不靠我記路徑。
    "retired": ["**/VIA_RetiredEngines"],
    "backup": ["**/_backup"],
}

#: LL133:一把尺不能是它要量的東西的一部分。本檔住在 `supportive modules/registry` = `cgc` 族,
#: 活樹能力庫掃 cgc 時會把**本檔自己的函式**收成能力,那些能力接著就進了「活樹有什麼」的對照集。
#: 於是我多寫一個帶 `recognize` 字樣的函式,墓園那支 `misc.recognize` 就自動不再是疑似——
#: **用自己的版本號製造一個假的進步**。批578 在 MDL164 身上踩過一模一樣的坑。
#: 排要排**整個家族**,不是只排 `__file__` 這一支:一開新版號,舊版就變成第二個貢獻者。
_SELF_FAMILY = Path(__file__).stem.rsplit("_v", 1)[0]

# 死樹家族:退役件與備份件**不是活樹**。可以單掃,但不跟活樹同一次掃描(見 scan 的斷開閘)。
DEAD_FAMILIES = ("retired", "backup")
# 死樹家族 → 掃它時要暫時放行的排除詞(只在**明示要掃**那一族時放行,其餘一律照舊排除)
DEAD_ALLOW = {"retired": ("VIA_RetiredEngines",), "backup": ()}
# 收容件與退役件不掃:正本零觸碰,退役件不是活樹(L38 同族)
SKIP_PARTS = ("references/intake", "VIA_RetiredEngines", "__pycache__", "node_modules", ".git",
              "ASSETS/SCOPE_COPY")


# ────────────────────────── 收容正本解析(尾版律) ──────────────────────────
def intake_dir() -> Path | None:
    cands = sorted(VIA.glob(INTAKE_GLOB))
    return cands[-1] if cands else None


def engine_path() -> Path | None:
    d = intake_dir()
    if d is None:
        return None
    p = d / "via_unified_engine.py"
    return p if p.exists() else None


def manifest() -> dict:
    d = intake_dir()
    if d is None:
        return {"state": "ABSENT", "why": "收容夾不在"}
    m = sorted(d.glob("_INTAKE_MANIFEST_b*.json"))
    if not m:
        return {"state": "ABSENT", "why": "manifest 不在"}
    try:
        j = json.loads(m[-1].read_text(encoding="utf-8"))
    except Exception as exc:
        return {"state": "FAIL", "why": f"{type(exc).__name__}: {exc}"}
    return {"state": "OK", "src": m[-1].name, "batch": j.get("batch"),
            "source": j.get("source", {}), "files": j.get("files", [])}


def _env() -> dict:
    e = dict(os.environ)
    e["VIA_NET_DISABLED"] = "1"      # 零網路:代跑時明示(正本本來就不連網,這是雙保險)
    e["PYTHONUTF8"] = "1"
    e["PYTHONIOENCODING"] = "utf-8"
    return e


def call(args: list, timeout: int = 1800, cwd: Path | None = None) -> dict:
    """代跑收容正本。回 {rc, out, err};正本零觸碰——只讀它、只跑它。"""
    p = engine_path()
    if p is None:
        return {"rc": 3, "out": "", "err": "收容正本不在(誠實 ABSENT)"}
    # PEIS 的能力庫/報告是**相對 cwd** 落檔的。不指定就會散到 VIA 根目錄變成未追蹤雜訊,
    # 所以一律關進 VIA_Reports/peis(已在 .gitignore),自測則各自關進自己的暫存夾。
    REPORTS.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([sys.executable, str(p), *args], capture_output=True, text=True,
                       timeout=timeout, stdin=subprocess.DEVNULL,
                       cwd=str(cwd or REPORTS), env=_env())
    return {"rc": r.returncode, "out": r.stdout, "err": r.stderr}


def _json_call(args: list, timeout: int = 1800, cwd: Path | None = None) -> dict:
    r = call([*args, "--json"], timeout=timeout, cwd=cwd)
    if r["rc"] == 3:
        return {"state": "ABSENT", "why": r["err"]}
    line = ""
    for l in (r["out"] or "").strip().splitlines():
        if l.strip().startswith("{"):
            line = l.strip()
    if not line:
        # 批567 L62:敗了就給全文,不切
        return {"state": "FAIL", "rc": r["rc"], "why": (r["err"] or r["out"] or "無輸出").strip()}
    try:
        return {"state": "OK", "rc": r["rc"], "json": json.loads(line)}
    except Exception as exc:
        return {"state": "FAIL", "rc": r["rc"], "why": f"{type(exc).__name__}: {exc} / {line}"}


# ────────────────────────── 家族掃描來源 ──────────────────────────
def split_families(raw) -> list:
    """把家族輸入切開。逗號、空白、分號都算分隔——PowerShell 的 `a,b` 會變成 "a b"(批569)。"""
    import re as _re
    if isinstance(raw, str):
        raw = [raw]
    out = []
    for chunk in (raw or []):
        for tok in _re.split(r"[,;\s]+", str(chunk).strip()):
            tok = tok.strip().lower()
            if tok and tok not in out:
                out.append(tok)
    return out


def family_srcs(fam: str) -> list:
    """家族起點。含 `*` 的寫法走**全樹 glob**;不含就照舊當固定路徑。

    批586 根因:死樹家族(墓園/備份夾)在樹上不只一處,寫死路徑會掃到空的那一座,
    回報「0 支」——那不是「沒有」,是**尺沒伸到**。假的零跟假綠是同一件事。

    三道收斂:①只收目錄(glob 會撈到同名檔案) ②跳過 .git
    ③剔掉被別的起點包住的子起點(否則同一批檔會被 PEIS 吃兩次,重複數直接灌水)。
    """
    out = []
    for rel in FAMILIES.get(fam, []):
        cands = sorted(VIA.glob(rel)) if "*" in rel else [VIA / rel]
        for c in cands:
            s = str(c).replace("\\", "/")
            if not c.is_dir() or "/.git/" in s or s.endswith("/.git"):
                continue
            out.append(c)
    keep = []
    for c in out:
        if any(o != c and o in c.parents for o in out):
            continue
        keep.append(c)
    return keep


def _live(p: Path, allow: tuple = ()) -> bool:
    """起點在不在活樹上。`allow` 是**本次明示要掃的死樹**要暫時放行的排除詞。

    放行只對這一次掃描、只對明示的那一族有效;沒指名就一律照舊排除
    (正本零觸碰 · 退役件不是活樹,兩條都沒鬆)。
    """
    s = str(p).replace("\\", "/")
    keys = tuple(k for k in SKIP_PARTS if k not in allow)
    return not any(k in s for k in keys)


# ────────────────────────── 動詞 ──────────────────────────
def status() -> dict:
    p, m = engine_path(), manifest()
    if p is None:
        return {"state": "ABSENT", "why": "收容正本 via_unified_engine.py 不在", "manifest": m}
    v = _json_call(["version"], timeout=300)
    st = call(["selftest"], timeout=900)
    tail = [l for l in (st["out"] + st["err"]).strip().splitlines() if l.strip()][-1:]
    return {"state": "OK" if st["rc"] == 0 else "FAIL", "engine": str(p.relative_to(VIA)),
            "selftest_rc": st["rc"], "selftest_tail": " / ".join(tail),
            "version": (v.get("json") or {}) if v.get("state") == "OK" else v,
            "manifest": m}


def scan(fams: list, out_dir: Path | None = None) -> dict:
    fams = split_families(fams)
    unknown = [f for f in fams if f not in FAMILIES]
    # 批586 操作員令「先跟 via / vdf 斷開」:死樹(退役/備份)與活樹**不同掃**。
    # 理由不是潔癖:混在一起掃,重複數、能力數、省 token 率全部會把墓園的舊件算進活樹的帳,
    # 「活樹有幾個重複」這個問題就永遠答不準了。庫檔名也各自帶簽章 → 兩棵樹兩個庫,不互相蓋。
    dead = [f for f in fams if f in DEAD_FAMILIES]
    live = [f for f in fams if f in FAMILIES and f not in DEAD_FAMILIES]
    if dead and live:
        return {"state": "GATED", "asked": fams, "dead": dead, "live": live,
                "why": f"死樹家族 {dead} 與活樹家族 {live} 不同掃:混掃會把墓園的舊件算進活樹的帳。",
                "how": [f"via-peis scan --family {','.join(live)}",
                        f"via-peis scan --family {','.join(dead)}"],
                "stores": [_store_for(live).name, _store_for(dead).name]}
    allow = tuple(k for f in dead for k in DEAD_ALLOW.get(f, ()))
    srcs = []
    for f in fams:
        srcs += [s for s in family_srcs(f) if _live(s, allow)]
    if not srcs:
        # L62:敗了就要說得清楚——認不得的逐一指名,並把合法家族列出來
        why = (f"認不得的家族:{unknown}。" if unknown else f"家族 {fams} 在本樹沒有起點。")
        return {"state": "ABSENT", "why": why + f"合法家族:{sorted(FAMILIES)}",
                "asked": fams, "unknown": unknown, "valid": sorted(FAMILIES)}
    args = ["ingest", "--db", str(_store_for(fams)), "--root", str(VIA)]
    for s in srcs:
        args += ["--src", str(s)]
    r = _json_call(args, timeout=3600, cwd=out_dir)
    if r.get("state") != "OK":
        return r
    j = r["json"]
    c, t = j.get("counts", {}), j.get("token_ledger", {})
    # PEIS 啟動條件:無重複 → 不啟動整合(誠實 NODATA,不是紅燈)
    dup = int(c.get("collapsed", 0)) + int(c.get("near_duplicates", 0))
    return {"state": "OK" if dup > 0 else "NODATA",
            "families": fams, "srcs": [str(s.relative_to(VIA)) for s in srcs],
            "files": c.get("files"), "functions": c.get("functions"),
            "capabilities": c.get("capabilities"), "sealed": c.get("sealed"),
            "pending": c.get("pending"), "collapsed": c.get("collapsed"),
            "near": c.get("near_duplicates"), "dup_total": dup,
            "source_tokens": t.get("source_tokens"), "capsule_tokens": t.get("capsule_tokens"),
            "saved_tokens": t.get("saved_tokens"), "saved_percent": t.get("saved_percent"),
            "mode": j.get("mode"), "source_mutation": j.get("source_mutation"),
            "why": "" if dup > 0 else "零重複=照 PEIS 啟動條件不啟動整合(誠實 NODATA)"}


# ────────────────────── 批588:能力卡書(一看就知道它的功能) ──────────────────────
#: 操作員令:「讓 AI 讀取時不需要大量掃描,而是一看就知道它的功能」。
#: 現況的成本是可量的:VDF 144 檔原始碼 127 萬 token。AI 要回答「這一族有哪些引擎、各做什麼」,
#: 今天的作法是把檔案一支一支讀進去——那一趟就把上下文燒光了,而且**下一次還要再燒一次**。
#: 卡書把這件事變成一次性的:引擎掃一次,落成一本 JSON;之後 AI 只讀那一本。
#:
#: 一張卡回答五件事,不多不少:**它是誰 · 它做什麼 · 怎麼叫它 · 它碰哪些資料 · 它靠誰**。
#: 資料全部從 AST 與能力庫推導,**沒有一個字是我寫的形容詞**——寫得出來的才寫,寫不出來就留空,
#: 留空不補話(LL138:回報「沒有」要說得出尺伸到哪裡)。
_BOOK_DIR = Path(__file__).resolve().parent          # 卡書落在 registry,因為它就是要被讀的正本
_ENG_RX = re.compile(r'\b((?:VDF|VRN|VAP|CGC|SUP|GRP|VIS)_(?:ENG|MDL)\d{3}_[A-Za-z0-9]+)')
_CONTRACT_FN = ("status", "selftest", "probe", "report", "plan", "run")
#: 資料表名要像資料表。第一版我用 `from|join|into\s+(\w+)` 去抓,結果把 `from datetime import`、
#: `from pathlib import` 全抓成「資料表」——**尺抓到的不是它要抓的東西**。改成兩道:
#: ①只在 SQL 關鍵字後面抓 ②排掉 import 行與標準模組名。
_SQL_RX = re.compile(r'\b(?:from|join|into|update|table)\s+["\'`]?([a-z][a-z0-9_]{3,40})\b', re.I)
_IMPORT_LINE = re.compile(r'^\s*(?:from|import)\s', re.M)
_NOT_TABLE = {"datetime", "pathlib", "typing", "collections", "subprocess", "importlib",
              "concurrent", "argparse", "sqlite3", "duckdb", "pandas", "numpy", "decimal",
              "functools", "itertools", "dataclasses", "contextlib", "operator", "random",
              "string", "textwrap", "traceback", "warnings", "shutil", "tempfile", "hashlib",
              "unicodedata", "statistics", "urllib", "requests", "httpx", "__future__"}


def _doc_first(src: str) -> str:
    """模組 docstring 的第一句有內容的話。**用 AST 取,不用正則猜。**

    第一版我用正則從檔頭往下比,45 支裡抓不到 21 支——因為批115 的網路橋與加速器橋
    是**注入在 docstring 前面**的,檔頭第一個字串早就不是 docstring 了。
    `ast.get_docstring` 沒有這個問題:它問的是語法樹,不是長相。
    抓不到就回空字串,**不替它編一句**。
    """
    try:
        d = ast.get_docstring(ast.parse(src)) or ""
    except SyntaxError:
        return ""
    for ln in d.splitlines():
        ln = ln.strip()
        if len(ln) >= 8 and not ln.startswith(("v0", "批", "=", "-", "用法", "律:")):
            return ln[:170]
    return ""


def _verbs(src: str) -> list:
    """引擎吃哪些動詞。三種寫法都要認,**只認一種就等於漏掉九成**。

    實測:45 支裡只有 3 支用 argparse `choices=[...]`,其餘 42 支是
    `if verb == "x"` / `elif verb in ("a","b")` / `sys.argv[1] == "x"` 這一類手寫分派。
    第一版只認 choices,於是 42 支的 verbs 全空——**空的不是引擎,是尺**。
    """
    out = set()
    for m in re.finditer(r'choices\s*=\s*\[([^\]]*)\]', src):
        out |= set(re.findall(r'["\']([a-z][a-z0-9_-]{1,24})["\']', m.group(1)))
    # verb == "x" / verb in ("a","b") / argv[1] == "x" / a[0] == "x"
    for m in re.finditer(r'(?:verb|cmd|action|sub|argv\[1\]|a\[0\]|args\[0\])\s*(?:==|in)\s*'
                         r'(\(?[^\n:]{0,120}?)\s*(?::|\n)', src):
        out |= set(re.findall(r'["\']([a-z][a-z0-9_-]{1,24})["\']', m.group(1)))
    out -= {"true", "false", "none", "json", "help", "yes", "no"}
    return sorted(out)


def _flags(src: str) -> list:
    """引擎吃哪些旗標。**沒有動詞不等於沒得叫**——45 支裡有一半是旗標驅動的
    (`--lane` / `--since` / `--limit`),不是動詞驅動。卡上只寫動詞,那一半會看起來像壞的。
    分開寫,讀卡的人才分得出「旗標驅動」與「尺沒抓到」。"""
    out = set(re.findall(r'add_argument\(\s*["\'](--[a-z][a-z0-9-]{1,24})["\']', src))
    #: 第四種寫法:完全不用 argparse,直接 `"--status" in args` / `args.index("--days")`。
    #: 實測這是本樹最常見的一種——只認 argparse 的話,ENG056 這種引擎卡上會是「叫不出來」,
    #: 而它明明吃 `--status` / `--derive` / `--days` / `--workers`。**空的是尺,不是引擎。**
    out |= set(re.findall(r'["\'](--[a-z][a-z0-9-]{1,24})["\']\s*(?:in\s+(?:args|argv|a)\b|\))', src))
    out |= set(re.findall(r'\.index\(\s*["\'](--[a-z][a-z0-9-]{1,24})["\']', src))
    out -= {"--json", "--selftest", "--help"}
    return sorted(out)


def _tables(src: str) -> list:
    """引擎碰哪些資料表。排掉 import 行(不然 `from datetime import` 會變成一張表)。"""
    body = "\n".join(l for l in src.splitlines() if not _IMPORT_LINE.match(l))
    hits = {x.lower() for x in _SQL_RX.findall(body)}
    return sorted(x for x in hits - _NOT_TABLE if "_" in x or x.startswith(("tw_", "vdf_", "via_")))


def book(fams: list, write: bool = True) -> dict:
    """能力卡書:一族一本,一引擎一張卡。AI 讀這本,不讀 144 支原始碼。

    只寫一個檔:`supportive modules/registry/VIA_Essentia_CardBook_<族>_v0100.json`。
    **不碰任何來源檔**(正本零觸碰);要不要把卡書當正本用,是操作員的事。
    """
    fams = split_families(fams)
    dp = _store_for(fams)
    if not dp.is_file():
        return {"state": "NODATA", "why": f"能力庫還沒建:先跑 via-peis scan --family {','.join(fams)}"}
    srcs = []
    for f in fams:
        srcs += [s for s in family_srcs(f)
                 if _live(s, tuple(k for x in fams for k in DEAD_ALLOW.get(x, ())))]
    if not srcs:
        return {"state": "ABSENT", "why": f"家族 {fams} 在本樹沒有起點"}

    with sqlite3.connect(f"file:{dp}?mode=ro", uri=True) as c:
        f_tokens = {r[0]: r[1] for r in c.execute("select path, tokens from vue_file")}
        own = {}
        for cap, path in c.execute("select capability, path from vue_function"):
            own.setdefault(str(path), set()).add(cap)

    # 尾版律:一族一張卡,只給尾版;舊版不入書(入了就變成兩張卡講同一支引擎)
    tails = {}
    for s in srcs:
        for p in s.rglob("*.py"):
            sp = str(p).replace("\\", "/")
            if "__pycache__" in sp or "/_" in sp.rsplit("/", 1)[0].rsplit("/", 1)[-1]:
                pass
            if "__pycache__" in sp:
                continue
            m = re.match(r"^(?P<fam>.+)_v(?P<n>\d{4})$", p.stem)
            key = (str(p.parent), m.group("fam") if m else p.stem)
            n = int(m.group("n")) if m else 0
            if key not in tails or n > tails[key][0]:
                tails[key] = (n, p)

    cards, src_tok = [], 0
    for _n, p in sorted(tails.values(), key=lambda x: str(x[1])):
        try:
            src = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        rel = str(p.relative_to(VIA)).replace("\\", "/")
        src_tok += int(f_tokens.get(rel, f_tokens.get(str(p), 0)) or 0)
        verbs = _verbs(src)
        fns = set(re.findall(r"^def ([a-zA-Z_][\w]*)", src, re.M))
        mine = sorted({x for x in own.get(rel, set())
                       if x not in CONTRACT_CAPS and x.split(".", 1)[-1] not in GENERIC_LEAF})
        deps = sorted({d for d in _ENG_RX.findall(src) if not d.startswith(p.stem[:12])})
        cards.append({
            "engine": p.stem, "path": rel,
            "version": (re.search(r"_v(\d{4})$", p.stem) or [None, ""])[1] if "_v" in p.stem else "",
            "purpose": _doc_first(src),
            "verbs": verbs, "flags": _flags(src),
            "contract": sorted(x for x in _CONTRACT_FN if x in fns),
            "owns": mine[:14], "owns_n": len(mine),
            "tables": _tables(src)[:12],
            "deps": deps[:10],
            "has_selftest": "--selftest" in src,
        })

    out = {"schema": "VIA.Essentia.CardBook.v1", "family": fams, "batch": 588,
           "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
           "engines": len(cards), "store": dp.name,
           "note": ("一族一本,一引擎一張卡,只收尾版。全部欄位由 AST 與能力庫推導;"
                    "推不出來就留空,不補話。AI 讀這本就不必再掃原始碼。"),
           "cards": cards}
    body = json.dumps(out, ensure_ascii=False, indent=1)
    card_tok = max(1, len(body) // 4)
    out["token_ledger"] = {"source_tokens": src_tok, "cardbook_tokens": card_tok,
                           "saved_percent": round((1 - card_tok / src_tok) * 100, 2) if src_tok else 0.0}
    body = json.dumps(out, ensure_ascii=False, indent=1)
    sig = "-".join(sorted(x.upper() for x in fams))
    dst = _BOOK_DIR / f"VIA_Essentia_CardBook_{sig}_v0100.json"
    if write:
        dst.write_text(body, encoding="utf-8")
    return {"state": "OK", "families": fams, "engines": len(cards),
            "book": str(dst.relative_to(VIA)) if write else "(未落檔)",
            "source_tokens": src_tok, "cardbook_tokens": card_tok,
            "saved_percent": out["token_ledger"]["saved_percent"],
            "no_entry": [c["engine"] for c in cards
                         if not c["verbs"] and not c["flags"] and not c["contract"]][:8],
            "no_purpose": [c["engine"] for c in cards if not c["purpose"]][:8],
            "why": ("卡書只寫一個檔,不碰任何來源檔(正本零觸碰)。"
                    "`no_purpose` 是**沒有模組 docstring 第一句**的引擎——那是它們自己沒說清楚,"
                    "不是卡書漏抄;要補是改那支引擎的事。")}


# ────────────────────────── 批588:契約橋 vs 真債 ──────────────────────────
#: **同一件事出現 N 次,不一定是債。**VDF 全境量出 1497 份「重複實作」,可是最上面那幾個
#: ——`_via_net` 110 份、`gate_open` 40 份、`status()` 87 份——是**律規定每一檔都要有**的:
#:   · 批115 VDF 全檔掛網路工具令 → `_via_net` / `_net_or_none` / `_net` 三件是同一條橋
#:   · 法遵雙閘 → `gate_open(env)` 每檔自檢
#:   · 統一調度契約 → 每支引擎都要有 `status()` / `selftest()` / `probe()` 動詞
#: 把這些算成整合債,就是**判錯的紅燈**:照著去「整合」等於拆掉律要求的東西。
#: 所以債要分兩層報,而且分層的依據寫在這裡、可以被質疑,不是藏在某個數字裡。
CONTRACT_CAPS = {
    "misc.via_net":   "批115 VDF 全檔掛網路工具令 · 統包網路工具橋",
    "misc.net_none":  "同一條網路橋的伴生(`_net_or_none`):工具缺席回 None,誠實不炸",
    "misc.net":       "同一條網路橋的伴生(`_net`)",
    "validate.open":  "法遵雙閘 `gate_open(env)`:每檔自己驗同意閘,不靠上游代驗",
    "misc.status":    "統一調度契約動詞 `status()`:每支引擎都要說得出自己現在什麼狀態",
    "misc.probe":     "統一調度契約動詞 `probe()`",
    "misc.selftest":  "統一調度契約動詞 `selftest()`",
}
#: 語意空殼:PEIS 會把 `build.any` / `misc.tuple` 這種名字聚在一起,但那不是「同一件事」。
GENERIC_LEAF = {"any", "tuple", "list", "dict", "str", "int", "bool", "none", "default",
                "value", "values", "main", "init", "run", "get", "set", "new", "make"}


def _fam_key(path: str) -> str:
    """路徑 → 家族鍵(去掉 `_vNNNN` 版號)。

    批589 根因:`debt` 第一版數的是**檔案**。CGC 族一掃就露餡——`misc.newest` 451 份、
    `battery()` 258 份,而那是因為自測格有 **258 個歷史版號**,每一版都有同一支函式。
    **那是版本史,不是重複實作。**把它算成整合債,等於叫人去「整合」自己的版本歷史。
    批588 報的 VDF 數字也有同一個毛病(144 檔裡只有 45 支是尾版),本版一併更正。
    所以債的單位改成**家族**:同一個家族跨版本重複 → history(不計債);
    跨家族重複 → real(才是債)。
    """
    p = path.replace("\\", "/")
    d, _, stem = p.rpartition("/")
    return f"{d}/{re.sub(r'_v[0-9]{4}$', '', stem[:-3] if stem.endswith('.py') else stem)}"


def debt(fams: list) -> dict:
    """整合債 = 同一件事在 N 個地方各寫一份 —— **扣掉律規定的橋與契約之後**。

    輸出三層,每一層都指名,不給一個沒有出處的總數:
      · contract —— 依律必須每檔都有的(報數字,但**不計入債**)
      · generic  —— 語意空殼名(不計入債)
      · real     —— 真債:同一件事各寫一份,附函式名與簽章,照份數排序
    LL90:併不併是操作員的裁定;本口只把帳攤開,不代併。
    """
    fams = split_families(fams)
    dp = _store_for(fams)
    if not dp.is_file():
        return {"state": "NODATA", "why": f"能力庫還沒建:先跑 via-peis scan --family {','.join(fams)}"}
    with sqlite3.connect(f"file:{dp}?mode=ro", uri=True) as c:
        caps = c.execute("select capability, members from vue_capability where members > 1"
                         " order by members desc").fetchall()
        names, sigs, fam_of = {}, {}, {}
        for cap, nm, sg, path in c.execute(
                "select capability, name, signature, path from vue_function"):
            names.setdefault(cap, {})
            names[cap][nm] = names[cap].get(nm, 0) + 1
            sigs.setdefault(cap, sg)
            fam_of.setdefault(cap, set()).add(_fam_key(str(path)))
        total_caps = c.execute("select count(*) from vue_capability").fetchone()[0]
        total_files = c.execute("select count(*) from vue_file").fetchone()[0]

    contract, generic, history, real = [], [], [], []
    for cap, m in caps:
        fams_n = len(fam_of.get(cap, ()))
        row = {"capability": cap, "members": m, "families": fams_n,
               "fn": sorted(names.get(cap, {}).items(), key=lambda x: -x[1])[:3],
               "signature": sigs.get(cap, "")}
        if cap in CONTRACT_CAPS:
            row["why"] = CONTRACT_CAPS[cap]
            contract.append(row)
        elif cap.split(".", 1)[-1] in GENERIC_LEAF:
            generic.append(row)
        elif fams_n <= 1:
            history.append(row)          # 同一個家族的不同版本 → 版本史,不是債
        else:
            real.append(row)
    history.sort(key=lambda r: -r["members"])
    real.sort(key=lambda r: (-r["families"], -r["members"]))
    dup_m = lambda rs: sum(r["members"] - 1 for r in rs)
    dup_f = lambda rs: sum(r["families"] - 1 for r in rs)
    return {"state": "OK", "families": fams, "store": dp.name,
            "files": total_files, "capabilities": total_caps,
            "contract_caps": len(contract), "contract_copies": dup_m(contract),
            "generic_caps": len(generic), "generic_copies": dup_m(generic),
            "history_caps": len(history), "history_copies": dup_m(history),
            "real_caps": len(real), "real_copies": dup_f(real),
            "real_file_copies": dup_m(real),
            "contract": contract, "top_history": history[:10], "top_real": real[:40],
            "why": ("四層,三層不計債:① contract 律規定每檔都要有(拆了就是拆律)"
                    "② generic 語意空殼 ③ **history 同一個家族的不同版本**——"
                    "`battery()` 出現 258 次是因為自測格有 258 個歷史版號,那是版本史不是重複實作;"
                    "④ real 才是債,而且**以跨家族數計**,不以檔數計。併不併是操作員裁定(LL90)。")}


def _is_dead_store(p: Path) -> bool:
    """庫檔名帶的是掃描範圍簽章;簽章裡有死樹家族 → 這是死樹的庫,不能當活樹的對照組。"""
    sig = p.stem.split("__", 1)[1] if "__" in p.stem else ""
    return any(tok in DEAD_FAMILIES for tok in sig.split("-"))


def _live_store() -> Path | None:
    """活樹能力庫:排掉死樹的庫,挑**能力數最多**的那一個(蓋得最寬=對名最準)。

    不能用 `_store_read()`——它挑的是**最新**的庫;剛掃完 retired 就會挑到墓園那本,
    拿墓園當活樹的對照組,答案會整個反過來。
    """
    best, bn = None, -1
    for p in list(REPORTS.glob("VIA_Capability_Store*.sqlite")):
        if _is_dead_store(p) or not p.is_file():
            continue
        try:
            with sqlite3.connect(f"file:{p}?mode=ro", uri=True) as c:
                n = c.execute("select count(*) from vue_capability").fetchone()[0]
        except Exception:
            continue
        if n > bn:
            best, bn = p, n
    return best


_STOP = {"get", "set", "run", "make", "new", "the", "for", "and", "with", "from", "def",
         "val", "value", "data", "args", "kwargs", "self", "main", "init", "tmp", "obj"}


def _toks(cap: str) -> set:
    """能力名 → 有意義的詞根集合。`build.accel_env` → {'accel','env'}(去掉名詞前綴與虛詞)。"""
    leaf = cap.split(".", 1)[-1]
    return {w for w in leaf.replace("-", "_").split("_") if len(w) >= 3 and w not in _STOP}


def _flat(cap: str) -> str:
    """能力名 → 壓平的葉名。`misc.walk_forward` 與 `misc.walkforward` 壓平後同字。

    批586 實測抓到的假疑似:純詞根比對會把 `walkforward` 判成「活樹沒有」,
    但活樹明明有 `misc.walk_forward`——差的只是一條底線。同樣的還有
    `validate.lookahead` vs `validate.no_future_leakage` 這種改名。壓平這一層
    把**同字不同斷法**先撈掉,剩下的才值得人看。
    """
    return re.sub(r"[^a-z0-9]", "", cap.split(".", 1)[-1].lower())


def deadcheck(dead_fams: list) -> dict:
    """備用件裡有沒有活樹沒有的東西?——死樹能力名 × 活樹能力庫對名。

    **這支報的是候選,不是判決。** 批585 量過同一件事:名字只在舊件裡出現的,
    絕大多數是改名或重構,不是功能掉了(348 族疑似 8 族,真掉的只有一族)。
    所以輸出分兩層,不把第一層當成答案:
      · only_dead —— 名字只在死樹出現(這一層數字大是正常的,不是紅燈)
      · suspect   —— 連**詞根**都在活樹找不到的(這一層才值得人看)
    LL90:撿不撿回活樹是操作員的裁定,本口只把候選攤開,不代撿、不代寫。
    """
    dead_fams = split_families(dead_fams)
    bad = [f for f in dead_fams if f not in DEAD_FAMILIES]
    if bad or not dead_fams:
        return {"state": "ABSENT", "why": f"deadcheck 只對死樹家族 {list(DEAD_FAMILIES)};收到 {dead_fams}",
                "valid": list(DEAD_FAMILIES)}
    dp, lp = _store_for(dead_fams), _live_store()
    if not dp.is_file():
        return {"state": "NODATA", "why": f"死樹能力庫還沒建:先跑 via-peis scan --family {','.join(dead_fams)}"}
    if lp is None:
        return {"state": "NODATA", "why": "活樹能力庫還沒建:先跑 via-peis scan --family cgc,sup,vdf,vrn"}

    def _caps(p: Path) -> dict:
        with sqlite3.connect(f"file:{p}?mode=ro", uri=True) as c:
            return {r[0]: r[1] for r in c.execute("select capability, members from vue_capability")}

    def _self_only(p: Path) -> set:
        """活樹庫裡**只由本尺自己這一家族貢獻**的能力。

        LL133:一把尺不能是它要量的東西的一部分。本檔住在 `supportive modules/registry`,
        也就是 `cgc` 族;活樹庫掃 cgc 時會把**本檔自己的函式**收成能力,接著這些能力就進了
        「活樹有什麼」的對照集。於是我多寫一個帶 `recognize` 字樣的函式,墓園那支
        `misc.recognize` 就會自動不再是疑似——**我用自己的版本號製造了一個假的進步**。
        (批578 踩過一模一樣的坑:MDL164 v0101 讓 v0100 變成每一本冊的第二個讀者。)
        所以對照集要先扣掉「只有本家族在貢獻」的能力,並把扣掉幾個**報出來**。
        """
        with sqlite3.connect(f"file:{p}?mode=ro", uri=True) as c:
            rows = c.execute("select capability, path from vue_function").fetchall()
        by = {}
        for cap, path in rows:
            by.setdefault(cap, []).append(Path(str(path)).stem.rsplit("_v", 1)[0] == _SELF_FAMILY)
        return {cap for cap, flags in by.items() if flags and all(flags)}

    dead, live = _caps(dp), _caps(lp)
    mine = _self_only(lp)
    for k in mine:
        live.pop(k, None)
    live_toks = set()
    for k in live:
        live_toks |= _toks(k)
    # 壓平葉名接成一條帶分隔的帶子:`flat in blob` 只會命中**某一個**條目,不會跨條目假命中
    blob = "|" + "|".join(sorted({_flat(k) for k in live})) + "|"
    only = sorted(set(dead) - set(live))
    suspect = []
    for k in only:
        tk, fl = _toks(k), _flat(k)
        if not tk or (tk & live_toks):           # 詞根在活樹出現過 → 不是「沒有」
            continue
        if len(fl) >= 4 and fl in blob:          # 同字不同斷法(walkforward ↔ walk_forward)
            continue
        suspect.append({"capability": k, "members": dead[k]})
    suspect.sort(key=lambda x: -x["members"])
    return {"state": "OK",
            "dead_families": dead_fams,
            "dead_store": dp.name, "live_store": lp.name,
            "dead_caps": len(dead), "live_caps": len(live),
            "self_excluded": len(mine),
            "only_dead": len(only), "suspect": len(suspect),
            "suspect_top": suspect[:40],
            "why": (f"對照集已扣掉只由本尺家族({_SELF_FAMILY})貢獻的 "
                    f"{len(mine)} 個能力(LL133:尺不能是它要量的東西的一部分)。"
                    "only_dead 是**候選**不是判決(改名/重構佔絕大多數);"
                    "suspect 才是詞根在活樹完全找不到的,撿不撿回是操作員裁定(LL90)。")}


def _need_store() -> dict | None:
    """能力庫不在=還沒 scan 過。誠實 NODATA,不編一個空答案。"""
    if _store_read() is None:
        return {"state": "NODATA", "why": f"能力庫還沒建:先跑 via-peis scan --family vdf,vrn({STORE.name})"}
    return None


def cards(cap: str = "", out_dir: Path | None = None) -> dict:
    miss = _need_store()
    if miss:
        return miss
    a = ["capsule", "--db", str(_store_read()), "--root", str(VIA)] + (["--capability", cap] if cap else [])
    return _json_call(a, timeout=900, cwd=out_dir)


def _sig_order(cap: str, out_dir: Path | None = None) -> list:
    """從能力卡的簽章取參數順序:`upside(target, current)` → ['target','current']。"""
    r = cards(cap, out_dir)
    if r.get("state") != "OK":
        return []
    for c in (r.get("json") or {}).get("cards", []):
        if c.get("cap") == cap:
            sig = str(c.get("sig") or "")
            if "(" in sig and sig.endswith(")"):
                inner = sig[sig.index("(") + 1:-1]
                names = []
                for part in inner.split(","):
                    nm = part.split("=")[0].split(":")[0].strip().lstrip("*")
                    if nm:
                        names.append(nm)
                return names
    return []


def run_cap(cap: str, params: str = "", out_dir: Path | None = None) -> dict:
    """快速截取層 RUN(capability, params)。

    批568 實測:正本沙箱車道是 `def_execute_guarded(..., list(payload or []))`——
    傳**陣列**沒問題(`--args '[180,120]'` → result 0.5),傳**物件**就變成把 key 當引數
    (`list({'target':..})` = `['target','current']` → TypeError)。
    可是操作員寫的 PEIS 規格用的正是物件:`RUN(math, {symbol: "2330"})`。
    正本零觸碰,所以轉接放在這裡:物件依**能力卡的簽章順序**攤成位置引數再送 --args;
    簽章讀不到就不猜——原樣送 --params,並把正本的話原封回報(L62 敗站不截斷)。
    """
    miss = _need_store()
    if miss:
        return miss
    a = ["run", "--capability", cap, "--db", str(_store_read()), "--root", str(VIA)]
    lane = ""
    if params:
        try:
            v = json.loads(params)
        except Exception:
            return {"state": "FAIL", "why": f"--params 不是合法 JSON:{params}"}
        if isinstance(v, list):
            a += ["--args", json.dumps(v, ensure_ascii=False)]
            lane = "args(陣列直送)"
        elif isinstance(v, dict):
            order = _sig_order(cap, out_dir)
            if order and all(k in v for k in order):
                a += ["--args", json.dumps([v[k] for k in order], ensure_ascii=False)]
                lane = f"args(依卡上簽章順序攤平:{order})"
            else:
                a += ["--params", params]
                miss_k = [k for k in order if k not in v] if order else []
                lane = ("params(原樣送;簽章讀不到=不猜)" if not order
                        else f"params(原樣送;物件缺 {miss_k}=不猜)")
        else:
            a += ["--args", json.dumps([v], ensure_ascii=False)]
            lane = "args(純量包成單一引數)"
    r = _json_call(a, timeout=900, cwd=out_dir)
    if lane:
        r["lane"] = lane
    return r


def report(out_dir: Path | None = None) -> dict:
    miss = _need_store()
    if miss:
        return miss
    return _json_call(["report", "--db", str(STORE), "--root", str(VIA)], timeout=900, cwd=out_dir)


def write_out(name: str, payload: dict) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    p = REPORTS / name
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


# ────────────────────────── 自測 ──────────────────────────
def selftest() -> int:
    n = [0]
    fails = []

    def chk(name, ok, note=""):
        n[0] += 1
        mark = "OK" if ok else "FAIL"
        if not ok:
            fails.append(name)
        # 批567 L62:敗的那一條註記不截斷
        print(f"  [{mark}] {name}" + (f" ({note})" if note else ""))

    print(f"=== CGC_MDL161 PEIS 能力引擎 v{VERSION} · 掛線口自測(零網路;不改來源) ===")
    d, p, m = intake_dir(), engine_path(), manifest()
    chk("① 收容正本在位(尾版 glob;夾+引擎+manifest 三件齊)",
        d is not None and p is not None and m.get("state") == "OK",
        f"({d.name if d else 'ABSENT'} · {len(m.get('files', []))} 檔)")

    src_ok = m.get("source", {})
    chk("② manifest 記得來源 repo/commit(說得出這支引擎打哪來,不是憑空長出來的)",
        bool(src_ok.get("repo")) and len(str(src_ok.get("commit", ""))) >= 12,
        f"({src_ok.get('repo')} @ {str(src_ok.get('commit'))[:12]})")

    ok_hash = True
    import hashlib
    for f in m.get("files", []):
        q = (d / f["name"]) if d else None
        if q is None or not q.exists() or hashlib.sha256(q.read_bytes()).hexdigest() != f["sha256"]:
            ok_hash = False
    chk("③ 正本零觸碰:每一檔的 sha256 與 manifest 逐字相符", ok_hash,
        f"({len(m.get('files', []))} 檔比對)")

    st = status()
    chk("④ 收容正本自己的 69 檢跑得過(不是我說它好,是它自己報)",
        st.get("state") == "OK" and st.get("selftest_rc") == 0, st.get("selftest_tail", ""))

    ver = st.get("version") or {}
    chk("⑤ 引擎身份卡讀得到(協定/規格/門檻齊)",
        isinstance(ver, dict) and bool(ver), f"({str(ver)[:90]}…)" if ver else "")

    code = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]
    chk("⑥ 本掛線口零網路、零安裝(不 import requests/httpx/urllib;不呼叫 pip/conda)",
        not any(k in code for k in ("import requests", "import httpx", "import urllib",
                                    "pip install", "conda install")))
    chk("⑦ 不代設同意閘(本檔不寫任何 VIA_*_CONSENT / API key)",
        "CONSENT" not in code.replace("VIA_*_CONSENT", "").replace("不代設任何 VIA", ""))
    chk("⑧ 不提供 --apply:能力表落地與引擎鎖定是操作員的裁定,不由本口代行",
        '"--apply"' not in code and "'--apply'" not in code)
    chk("⑨ 代跑時明示零網路旗標",
        'e["VIA_NET_DISABLED"] = "1"' in code)
    _grave = VIA / "functional modules" / "VIA_RetiredEngines"
    chk("⑩ 掃描排除收容件與退役件(正本零觸碰 · 退役件不是活樹);批586 開的放行門**只對明示要掃的那一族**有效",
        all(k in SKIP_PARTS for k in ("references/intake", "VIA_RetiredEngines"))
        and _live(_grave) is False                                    # 沒指名 → 照舊排除
        and _live(_grave, ("VIA_RetiredEngines",)) is True            # 指名 retired → 放行
        and _live(VIA / "supportive modules" / "references" / "intake",
                  ("VIA_RetiredEngines",)) is False,                  # 收容正本**永遠**不放行
        "沒指名=排除 · 指名 retired=放行 · 收容件永遠排除")
    chk("⑪ 帶加速器橋(MDL156 v0104 覆蓋閘)",
        "[VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))

    # 真跑一次:拿一個最小的合成語料,驗四態與帳都對得起來
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        (t / "a.py").write_text(
            "def calc_total(xs):\n    s = 0\n    for x in xs:\n        s += x\n    return s\n",
            encoding="utf-8")
        (t / "b.py").write_text(
            "def compute_total(values):\n    acc = 0\n    for v in values:\n        acc += v\n    return acc\n",
            encoding="utf-8")
        r = _json_call(["ingest", "--src", str(t), "--db", str(t / "s.sqlite"), "--root", str(t)],
                       timeout=900, cwd=t)
        j = (r.get("json") or {})
        c = j.get("counts", {})
        chk("⑫ 合成語料真跑:兩支換名同義實作被聚成一個能力(這就是『低風險無損耗合併』的證據)",
            r.get("state") == "OK" and int(c.get("collapsed", 0)) >= 1,
            f"(檔 {c.get('files')} · 函式 {c.get('functions')} · 能力 {c.get('capabilities')} · 折疊 {c.get('collapsed')})")
        chk("⑬ 真跑不改來源(mode=READ_ONLY_SOURCES 且 source_mutation=False)",
            j.get("mode") == "READ_ONLY_SOURCES" and j.get("source_mutation") is False,
            f"({j.get('mode')} / {j.get('source_mutation')})")
        before = sorted((x.name, x.read_bytes()) for x in (t / "a.py", t / "b.py"))
        chk("⑭ 真跑後兩支來源檔位元組不變(不是看旗標,是真的比 bytes)",
            before == sorted((x.name, x.read_bytes()) for x in (t / "a.py", t / "b.py")))
        tl = j.get("token_ledger", {})
        chk("⑮ token 帳算得出來且誠實(小語料可能為負也照報,不為了好看放寬)",
            isinstance(tl.get("source_tokens"), int) and "saved_tokens" in tl,
            f"(原文 {tl.get('source_tokens')} → capsule {tl.get('capsule_tokens')} · 省 {tl.get('saved_percent')}%)")

        # 零重複語料 → 啟動條件不成立 → NODATA,不是紅燈
        t2 = t / "solo"
        t2.mkdir()
        (t2 / "only.py").write_text("def z_unique_thing(q):\n    return q\n", encoding="utf-8")
        r2 = _json_call(["ingest", "--src", str(t2), "--db", str(t2 / "s2.sqlite"), "--root", str(t2)],
                        timeout=900, cwd=t2)
        c2 = (r2.get("json") or {}).get("counts", {})
        chk("⑯ 啟動條件:零重複語料 → 折疊 0(照 PEIS 規則不啟動整合;掛線口報 NODATA 不報紅)",
            r2.get("state") == "OK" and int(c2.get("collapsed", 0)) == 0,
            f"(折疊 {c2.get('collapsed')} · 近似 {c2.get('near_duplicates')})")

    with tempfile.TemporaryDirectory() as td3:
        t3 = Path(td3)
        (t3 / "c.py").write_text("def sum_values(xs):\n    return sum(xs)\n", encoding="utf-8")
        db3 = t3 / "k.sqlite"
        _json_call(["ingest", "--src", str(t3), "--db", str(db3), "--root", str(t3)], timeout=900, cwd=t3)
        rep3 = _json_call(["report", "--db", str(db3), "--root", str(t3)], timeout=900, cwd=t3)
        chk("⑰ 能力庫真的落地、且落地後 report/cards 讀得到(省略 --db 只在記憶體=白掃一場,這是本口第一版踩過的坑)",
            db3.exists() and rep3.get("state") == "OK",
            f"(db {db3.exists()} · report {rep3.get('state')})")

    if STORE.exists():
        ro = run_cap("misc.upside", '{"target": 180, "current": 120}')
        ra = run_cap("misc.upside", "[180, 120]")
        chk("⑱ 快速截取層 RUN(capability, params):物件道與陣列道給同一個答案(物件道靠卡上簽章攤平,正本零觸碰)",
            ro.get("state") == "OK" and ra.get("state") == "OK"
            and (ro.get("json") or {}).get("result") == (ra.get("json") or {}).get("result"),
            f"(物件 {(ro.get('json') or {}).get('result')} · 陣列 {(ra.get('json') or {}).get('result')} · 車道 {ro.get('lane')})")
    else:
        chk("⑱ 快速截取層 RUN:能力庫還沒建,誠實跳過(不假裝綠)", True, "能力庫不在=先跑 via-peis scan")

    chk("⑲ 家族參數:PowerShell 逗號陣列黏成一個字也要吃得下(批569 工作站實錄)",
        split_families("vdf vrn") == ["vdf", "vrn"] and split_families("vdf,vrn") == ["vdf", "vrn"]
        and split_families(["vdf,vrn", "vap"]) == ["vdf", "vrn", "vap"]
        and split_families("VDF, VRN ;vap") == ["vdf", "vrn", "vap"]
        and scan(["vdf vrn"]).get("state") in ("OK", "NODATA"),
        "'vdf vrn' · 'vdf,vrn' · ['vdf,vrn','vap'] · 'VDF, VRN ;vap' 四種寫法同解")
    _bad = scan(["nosuchfamily"])
    chk("⑳ 認不得的家族要指名並列出合法家族(L62:敗了就要說得清楚,不是丟一個字典出來)",
        _bad.get("state") == "ABSENT" and _bad.get("unknown") == ["nosuchfamily"]
        and "合法家族" in _bad.get("why", ""), _bad.get("why", "")[:80])

    _livef = [f for f in FAMILIES if f not in DEAD_FAMILIES]
    _missing = [f for f in _livef if not family_srcs(f)]
    chk("㉑ 活樹五族的起點逐族點名(LL131:`>=4` 這種糊門檻會讓少一族也綠)",
        all(isinstance(v, list) and v for v in FAMILIES.values()) and not _missing,
        f"(活樹 {_livef} · 缺 {_missing or '無'})")

    # 批586 拿**樹上真的路徑**當樣品驗尺,不拿合成語料:假的零只有真樹量得出來。
    _rsrc = family_srcs("retired")
    _rpy = sum(len(list(s.rglob("*.py"))) for s in _rsrc)
    chk("㉒ 死樹起點走全樹 glob:墓園有兩座(根下 0 支 · functional modules 下 261 支),"
        "寫死路徑只會吃到空的那座=假的零",
        len(_rsrc) >= 2 and _rpy > 0 and any(s.name == "VIA_RetiredEngines" for s in _rsrc),
        f"(起點 {len(_rsrc)} 座 · .py {_rpy} 支 · {[str(s.relative_to(VIA)) for s in _rsrc]})")

    _bsrc = family_srcs("backup")
    _bpy = sum(len(list(s.rglob("*.py"))) for s in _bsrc)
    chk("㉓ 備份夾同樣走全樹 glob;掃出來幾支就報幾支,零支就誠實報零(零不等於尺沒伸到)",
        isinstance(_bsrc, list) and all(s.is_dir() for s in _bsrc),
        f"(起點 {len(_bsrc)} 座 · .py {_bpy} 支)")

    # ── 批588:卡書抽取器的四種分派寫法,逐種用合成語料驗 ──────────────────────
    # 這一檢是拿實測樣品修出來的:第一版只認 argparse `choices=[...]`,45 支裡 42 支的動詞欄全空;
    # 補了 `verb == "x"` 之後還是漏掉 `"--status" in args`(本樹最常見的一種),ENG056 卡上
    # 因此寫著「叫不出來」——而它明明吃 --status/--derive/--days/--workers。**空的是尺,不是引擎。**
    _fx = (
        'import ast\n'
        '"""ENG999_Fixture — 合成語料:一句話用途。"""\n'
        'def main():\n'
        '    ap.add_argument("verb", choices=["alpha", "beta"])\n'
        '    ap.add_argument("--since", default="")\n'
        '    if verb == "gamma":\n'
        '        pass\n'
        '    elif verb in ("delta", "epsilon"):\n'
        '        pass\n'
        '    if "--zeta" in args:\n'
        '        pass\n'
        '    n = args.index("--eta")\n'
        '    con.execute("select * from tw_daily_prices join vdf_fetch_ledger on 1=1")\n'
    )
    _v, _fl, _tb = _verbs(_fx), _flags(_fx), _tables(_fx)
    chk("㉖ 卡書抽取器四種分派寫法都要認(argparse choices · verb== · verb in · \"--x\" in args)",
        {"alpha", "beta", "gamma", "delta", "epsilon"} <= set(_v)
        and {"--since", "--zeta", "--eta"} <= set(_fl),
        f"(動詞 {_v} · 旗標 {_fl})")
    chk("㉗ 資料表欄不得把 import 的模組當成表(第一版把 `from datetime import` 抓成一張表)",
        "tw_daily_prices" in _tb and "vdf_fetch_ledger" in _tb
        and not ({"datetime", "pathlib", "typing"} & set(_tables("from datetime import date\n"
                                                                "from pathlib import Path\n"))),
        f"({_tb})")

    _bk = book(["vdf"], write=False)
    chk("㉘ 卡書:一族一本、只收尾版、用途欄用 AST 取(批115 的橋注在 docstring 前面,正則會抓空)",
        _bk.get("state") in ("OK", "NODATA")
        and (_bk.get("state") == "NODATA" or _bk.get("engines", 0) > 0),
        f"({_bk.get('state')} · 引擎 {_bk.get('engines')} · 省 {_bk.get('saved_percent')}%)")

    _dbt = debt(["vdf"])
    chk("㉙ 整合債分四層,三層不計債(契約 · 泛名 · **版本史** · 真債)",
        _dbt.get("state") in ("OK", "NODATA")
        and (_dbt.get("state") == "NODATA"
             or (_dbt.get("contract_caps", 0) > 0 and _dbt.get("real_caps", 0) > 0
                 and _dbt.get("history_caps", 0) > 0
                 and all(r["capability"] in CONTRACT_CAPS for r in _dbt.get("contract", [])))),
        f"({_dbt.get('state')} · 契約 {_dbt.get('contract_caps')} · 泛名 {_dbt.get('generic_caps')} · "
        f"版本史 {_dbt.get('history_caps')} · 真債 {_dbt.get('real_caps')} 類/"
        f"{_dbt.get('real_copies')} 跨家族)")
    chk("㉚ 債以**家族**計不以檔計:真債每一筆的家族數都要 >1,版本史每一筆都要 ==1 "
        "(`battery()` 出現 258 次是因為自測格有 258 個版號——那是版本史,不是重複實作)",
        _dbt.get("state") == "NODATA"
        or (all(r["families"] > 1 for r in _dbt.get("top_real", []))
            and all(r["families"] == 1 for r in _dbt.get("top_history", []))
            and _fam_key("a/b/CGC_MDL064_SelftestGrid_v0356.py")
            == _fam_key("a/b/CGC_MDL064_SelftestGrid_v0001.py")),
        f"(真債家族數最小 {min([r['families'] for r in _dbt.get('top_real', [])] or [0])} · "
        f"版本史家族數最大 {max([r['families'] for r in _dbt.get('top_history', [])] or [0])})")

    _rd, _ls = _store_read(), _live_store()
    chk("㉔ 讀庫回退不得挑到墓園(批586 自測當場抓到:剛掃完 retired,最新的庫就是墓園那本,"
        "run/cards 會拿墓園當能力庫)",
        _rd is None or not _is_dead_store(_rd),
        f"(回退讀 {_rd.name if _rd else '無庫'} · 最寬活樹庫 {_ls.name if _ls else '無庫'})")

    _mix = scan(["retired", "vdf"])
    chk("㉕ 斷開閘:死樹與活樹同一次掃要 GATED 並指名兩條各自的令(混掃會把墓園舊件算進活樹的帳)",
        _mix.get("state") == "GATED" and _mix.get("dead") == ["retired"]
        and _mix.get("live") == ["vdf"] and len(_mix.get("how", [])) == 2
        and len(set(_mix.get("stores", []))) == 2,
        f"({_mix.get('why', '')[:52]} · 兩庫 {_mix.get('stores')})")

    # LL112:分子分母要數同一件事。檢數一律由 n[0] 推導,不寫死——
    # 本檔第一版就寫死「二十檢」而實跑 19(中間漏了一個標籤號),當場被這行抓到。
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="CGC_MDL161_PEISCapabilityEngine", description="PEIS 能力引擎掛線口")
    ap.add_argument("verb", nargs="?", default="status",
                    choices=["status", "scan", "cards", "run", "report", "deadcheck", "debt", "book"])
    ap.add_argument("cap", nargs="?", default="")
    ap.add_argument("--family", default="", nargs="*",
                    help="vdf|vrn|vap|cgc|sup(逗號或空白分隔皆可;預設 vdf,vrn)")
    ap.add_argument("--params", default="", help="RUN(capability, params) 的 params(JSON)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if a.verb == "status":
        r = status()
    elif a.verb == "scan":
        r = scan(split_families(a.family or "vdf,vrn"))
    elif a.verb == "debt":
        r = debt(a.family or "vdf")
    elif a.verb == "book":
        r = book(a.family or "vdf")
    elif a.verb == "deadcheck":
        r = deadcheck(a.family or "retired")
    elif a.verb == "cards":
        r = cards(a.cap)
    elif a.verb == "run":
        if not a.cap:
            print("  [絕] run 要給能力名:via-peis run <能力> [--params JSON]")
            return 1
        r = run_cap(a.cap, a.params)
    else:
        r = report()

    p = write_out(f"PEIS_{a.verb.upper()}_{ts}.json", r)
    write_out(f"PEIS_{a.verb.upper()}_latest.json", r)
    if a.json:
        print(json.dumps(r, ensure_ascii=False))
    else:
        st = r.get("state", "?")
        print(f"[CGC_MDL161 v{VERSION}] {a.verb} · {st}")
        for k in ("files", "functions", "capabilities", "sealed", "pending", "collapsed", "near",
                  "source_tokens", "capsule_tokens", "saved_tokens", "saved_percent",
                  "dead_store", "live_store", "dead_caps", "live_caps", "self_excluded",
                  "only_dead", "suspect", "engines", "book", "cardbook_tokens",
                  "contract_caps", "contract_copies", "generic_caps", "generic_copies",
                  "real_caps", "real_copies", "history_caps", "history_copies",
                  "why", "how", "engine", "selftest_tail"):
            if k in r and r[k] not in (None, ""):
                print(f"  {k:>16} : {r[k]}")
        print(f"  存證 {p.name}")
        for s in (r.get("suspect_top") or [])[:20]:
            print(f"      · {s['capability']}  ×{s['members']}")
        for s in (r.get("contract") or []):
            print(f"      [契約] {s['capability']:20s} ×{s['members']:<4d} {s['why']}")
        for s in (r.get("top_real") or [])[:20]:
            fn = " ".join(f"{a}×{b}" for a, b in s["fn"][:2])
            print(f"      [真債] {s['capability']:22s} {s['families']:3d} 族/{s['members']:<4d} 檔  "
                  f"{fn[:30]:30s} {s['signature'][:38]}")
        for s in (r.get("top_history") or [])[:6]:
            print(f"      [版本史] {s['capability']:20s} ×{s['members']:<4d} 同一家族的不同版號,不是債")
    # 誠實多態 rc:0 綠 · 1 紅 · 2 無資料 · 3 不存在 · 4 閘住(閘住不是壞,是被擋)
    return {"OK": 0, "NODATA": 2, "ABSENT": 3, "GATED": 4}.get(r.get("state"), 1)


if __name__ == "__main__":
    sys.exit(main())
