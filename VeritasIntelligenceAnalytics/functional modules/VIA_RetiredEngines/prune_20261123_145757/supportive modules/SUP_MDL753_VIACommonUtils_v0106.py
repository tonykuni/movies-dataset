#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
SUP_MDL753_VIACommonUtils v0100 — VRN 共用小工具正典(批594)

批589 量到 VRN 是三族裡整合債最重的(890 類 / 2557 跨家族)。批594 取前幾大,
照 L75 先按行為分群(AST 正規化比骨架,不比長相):

  VRN 尾版 170 支 · 定義 **68 處** · 行為群 **18 群**(全部在模組層)

  `_cel_submit` 17 處 / 4 群   Celeritas 平行提交 + 退回直呼
  `_si`         17 處 / 4 群   安全 import(回模組或 None)
  `_hash8`      14 處 / 2 群   八碼雜湊(有 xxhash 就用,沒有就 sha256)
  `_jwrite`     14 處 / 3 群   寫 JSON —— **直接接批592 的 SUP_MDL752 正典**,不另造一支
  `_argval`      3 處 / 2 群   從 argv 取旗標值
  `_num`         2 處 / 2 群   逗號千分位字串 → float / None

分群之後兩件事值得先講:

**一、`_cel_submit` 的差別在「第二層退路」。**
6+2 處只試 `_CEL._LazyPool.submit`,5+4 處會再試 `_CEL.submit`。
兩者最後都退回 `fn(*args, **kw)`,所以**只有在「有 submit 但沒有 _LazyPool」時才分得出來**。
正典把它變成明示選項 `submit_fallback`,不擅自統一。

**二、`_si` 有一群用 bare `except:`。**
`except:` 連 `KeyboardInterrupt` / `SystemExit` 都吞。import 一個會 `sys.exit()` 的模組時,
這一群會把它吃掉當成「沒有這個模組」。**那是潛在缺陷,不是風格差異。**
正典提供 `catch_all=` 讓它等價遷移,**預設是 `except Exception`**;
要不要把那 7 處改成預設值,是操作員的裁定(LL90),本檔不代改。

v0102(批626)兩修一增:
  · `_celeritas()` **接回正典 SUP_MDL737**(批323 已修的那支);v0100/v0101
    自己那份少了 `sys.modules[name] = mod`,**每次都回 None**,於是
    `cel_submit` 全樹退回直呼 —— 加速器掛滿一棵樹,一次也沒真的並行過。
  · 候選序改用 L50 合規序(`accelerator/` 那本零 talib 排第一),並排掉 `_sha` 鏡像。
  · 新增 **L77 正典排除清單** `SCAN_EXCLUDE` / `scan_excluded()` / `frozen_dirs()`:
    會寫檔的掃描器一律吃這一份,不得各寫各的(批626 量到注入器少了四段)。

v0104→v0105(側線 2026-09-24;主線批號由併線的手指定 L25;操作員令「走檢查好 SSOT REGEX 同義字 邏輯庫 ·
全景式分析三回發現錯誤所在 · 不毀壞系統 · 不產生九頭龍風險」)只增不減,既有函式一字未動:
  · 新增 **期別時鐘**:`roc_to_iso()` 民國/西元/緊湊日期正本 · `period_lag()` 期別滯後 ·
    `date_columns()` 日期欄聯集 · `load_period_rules()` 讀 `registry/VIA_SSOT_PeriodRules_v*.json`。
    全景三回量到:「哪一欄是日期」全樹至少三份清單(MDL123 · MDL139 · ENG093)各缺一塊,
    月營收 ym=YYYYMM 在狀況頁量成 NODATA;財報 6/30(Q2 期末)被當日頻判 RED 86 日;
    凍結的鏡像庫舊表把籌碼/宏觀拉到 30 日 RED。規則寫在冊上,本檔只讀冊(冊外不另寫清單)。
  · `roc_to_iso` 以 VDF_ENG055_OmniFetch_v0111 的兩份私有版(`_iso_date` · `_roc_to_iso`)為語料,
    有效日期逐一零差異(自測 ㉖㉗);刻意不同的只有「不是真日期」那幾式(舊版照換成 2910-01-01 /
    2026-13-01,正本回 None 不猜),逐式具名在自測裡。全樹還有 79 份私有 +1911,照冊上帳逐支遷。
  · 自測 ⑨ 改平台中立:`nan_safe(Path('/a'))` 在 Windows 是 `\a`,舊檢寫死 `'/a'`
    → 工作站 2026-09-24 全格子「VRN 共用小工具正典十四檢 ⑨」紅就是這一檢自己錯,`nan_safe` 沒壞。

v0105→v0106(側線 2026-09-24 第二段;主線批號由併線的手指定 L25;操作員令「繼續完成」)只增不減,既有函式一字未動:
  · 新增 `fallback_date_columns(own)`:補位欄 = 冊上 corrected − 讀者自己那份 − record_only(照 corrected 序)。
    冊上 primary_first_rule 說「原份一欄都認不到才用聯集補」,可是 v0105 只給了聯集,差集留給每支讀者自己做——
    主控台 MDL139 · 架構冊 ENG073 · 之後六支都要做同一個差集,而且要記得跳過寫入時間戳(ts · snapshot_at · run_at)。
    一條規則九處自寫就是九頭龍的起點,所以差集收回正典,讀者只呼叫。
  · 第二次全樹普查(冊 date_columns.census):日期欄清單在 VDF/VIA 碼裡是**九份**,不是 v0100 冊上寫的兩份。
    corrected 尾端補六欄(portfolio_date 讓 ETF 持股兩表第一次量得到新鮮度);record_only 補 snapshot_at · run_at。
  · 自測 ㉞ 普查覆蓋(九份每一欄都在 corrected ∪ record_only,遷過來一欄都不丟)· 補位不含時間戳 ·
    與 MDL123 v0104 自己做的差集逐欄相同(兩處同答,不長第二種意見);**負控**:冊上塞一個假欄/把時間戳塞進 corrected,檢得出來。
  · `roc_to_iso` 八碼整串比對放寬到 19xx(v0105 只認 20xx)。v0105 ㉖ 宣告「`_iso_date` 認得的有效日期逐一零差異」,
    可是語料裡沒有 19xx 八碼——`_iso_date('19991231')` 給 1999-12-31,v0105 正本回 None。宣告沒被量到就不算數(LL439),
    語料補上、正本補上。只增:搜尋式(字串裡夾日期)照舊只認 20xx,免得把金額當日期。
  · 新增 `roc_to_iso_keep(s)`:認得的日期與 `roc_to_iso` 同答,認不出=回原值 `str(s).strip()`——VDF_ENG055 `_iso_date`
    的直通語意。收進正典是為了讓 ENG055 用**綁定**取代 def(VIA_LibCanon 律②;在呼叫端再包一層 def 家族數不會掉)。
    自測 ㉟ 把新舊兩份逐式分四類(同答 · 正規化=另一份舊版給過的同一個日期 · 拒絕不存在的日期=回原值 · 具名刻意不同),一式都不准落在四類外。
  · 新增 `roc_ym(v)`:民國年月(MOPS 月營收「資料年月」11507 · CBC 利率檔 11508)→ 'YYYYMM'。這個形狀全樹兩份
    (VDF_ENG063 `_roc_ym` · VDF_ENG055 L10 內嵌),v0105 正典沒有——實作照 ENG063 原文(它有月份與年份範圍檢查),
    自測 ㊱ 對 ENG063 原實作逐式零差異、對 ENG055 內嵌在有效輸入上同答(無效月份 11513 舊內嵌會造 2026-13-01,正典回 None)。

律:零網路;零安裝;正本零觸碰;`--selftest` 零網路且只在 tempfile 沙盒寫。
用法:python3 SUP_MDL753_VIACommonUtils_v0100.py --selftest
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
import importlib
import json as _json
import math
import re as _re
import sys
from datetime import date as _date
from pathlib import Path

VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]

#: 名字像但**不是同一件事**,不得併(照 SUP_MDL752 的慣例留名)。
NOT_SAME_THING = {
    "VRN.*.close(self)": "是類別的 property/method(取收盤價),不是檔案關閉,也不是共用小工具",
    "VRN.*.export_csv(self, out_dir)": "是類別方法,各自有自己的欄位與表頭,不是同一個 CSV 寫法",
    "VRN.*._cel_submit(fn, *args, **kw)":
        "**不得做成模組層綁定。**它讀的 `_CEL` / `_CEL_OK` 在檔頭是 `None` / `False`,"
        "真正的值是開機函式用 `global _CEL, _CEL_OK` **事後**填進去的——"
        "原版是**呼叫時**才讀,模組層綁定會在 **import 當下**把 `False` 凍住,"
        "開機之後永遠走不到 Celeritas 的池子。這跟批593 的可變預設值是同一族:"
        "**早綁了一個本來要晚讀的東西**。17 處,具名不遷。",
    "VRN_*.._argval(args, flag) 的有狀態那一版":
        "它讀寫模組層的 `_FLAG_OK_BARE` / `_BARE_FLAG_SEEN`,行為綁在那一支的狀態上;"
        "搬出來就不是同一件事。1 處,具名不遷。",
}


# ────────────────────────── 安全 import ──────────────────────────
def safe_import(name: str, *, catch_all: bool = False):
    """import 一個模組,失敗回 None。

    catch_all  True 用 bare `except:`(連 KeyboardInterrupt / SystemExit 都吞)。
               活樹有 7 處是這一種——**那是潛在缺陷**:import 一個會 `sys.exit()` 的模組時,
               它會被吃掉當成「沒有這個模組」。留這個選項只為**等價遷移**,
               預設是 `except Exception`;要不要改回預設值是操作員的裁定(LL90)。
    """
    if catch_all:
        try:
            return importlib.import_module(name)
        except BaseException:      # noqa: BLE001 — 就是要等價於活樹那 7 處的 bare except
            return None
    try:
        return importlib.import_module(name)
    except Exception:
        return None


# ────────────────────────── Celeritas 平行提交 ──────────────────────────
_CEL_CACHE: list = []

#: Celeritas 候選序(與 SUP_MDL737 同序=一把尺)。L50:`accelerator/` 那本是
#: 唯一零 talib 合規本,必須排第一;帶 talib 的兩本退居後位只作退路。
CEL_CANDIDATES = ("accelerator/VeritasCeleritas.py",
                  "VeritasCeleritas.py",
                  "50_Protection_Acceleration/VeritasCeleritas.py")


#: 上一次載入失敗的原因(誠實留痕;成功為空字串)。`cel_why()` 讀它。
_CEL_ERR: list = []


def _celeritas():
    """惰性載入正典 Celeritas;缺席回 None,**並把原因留在 `_CEL_ERR`**。

    批626 量到的事(v0100/v0101 的實況):本函式**每次都回 None**。

        SUP_MDL753._celeritas()  →  None   AttributeError: 'NoneType' object has no attribute '__dict__'
        SUP_MDL737.celeritas()   →  模組   _LazyPool 在位

    差別只有一行:`sys.modules[name] = mod` **要在 exec_module 之前**。
    Celeritas 裡有 dataclass,3.11+ 的 dataclass 在建類別時會去查
    `sys.modules[cls.__module__]`;沒先登記就查到 None,再取 `.__dict__`
    就是上面那個 AttributeError。批323 早就在 SUP_MDL737 修掉了,
    批594 把 17 處 `_cel_submit` 收進本正典時,**抄了形狀,漏了那一行**。

    後果不是「慢一點」,是 `cel_submit` 全數退回 `fn(*args, **kw)` ——
    正典裡那個池子**一次也沒被用到**,而且不會報錯(graceful 把它蓋住了)。

    所以 v0102 不自己再寫一份載入器(那就是第二把尺,LL133):
    **有 SUP_MDL737 就交給它**,本檔只留「MDL737 不在」時的退路,
    而退路也照 MDL737 的候選序(L50:accelerator/ 那本是唯一零 talib 合規本)
    與 sys.modules 登記律。
    """
    if _CEL_CACHE:
        return _CEL_CACHE[0]
    mod, why = None, ""
    # 一、正典道:SUP_MDL737(批323 已修;尾版律取最新)
    try:
        import importlib.util as _ilu
        p = Path(__file__).resolve()
        while p.parent != p:
            sm = p / "supportive modules"
            if sm.is_dir():
                hits = sorted(x for x in sm.glob("SUP_MDL737_SuperAccelModule_v*.py")
                              if "_sha" not in x.name)
                if hits:
                    _n = "SUP_MDL737_SuperAccelModule"
                    _sp = _ilu.spec_from_file_location(_n, hits[-1])
                    _m = _ilu.module_from_spec(_sp)
                    sys.modules.setdefault(_n, _m)
                    _sp.loader.exec_module(_m)
                    mod = _m.celeritas()
                    why = "" if mod is not None else f"MDL737 自陳:{_m._CEL.get('err', '')}"
                break
            p = p.parent
        else:
            why = "找不到 supportive modules"
    except Exception as exc:
        why = f"MDL737 道:{type(exc).__name__}: {str(exc)[:100]}"
    # 二、退路:MDL737 不在時自己載(候選序同 L50;登記 sys.modules 後 exec)
    if mod is None:
        p = Path(__file__).resolve()
        while p.parent != p:
            sm = p / "supportive modules"
            if sm.is_dir():
                import importlib.util as ilu
                for rel in CEL_CANDIDATES:
                    cand = sm / rel
                    if not cand.exists() or "_sha" in cand.name:
                        continue
                    name = "VeritasCeleritas_dyn"
                    try:
                        spec = ilu.spec_from_file_location(name, cand)
                        m2 = ilu.module_from_spec(spec)
                        sys.modules[name] = m2      # ← 這一行是批594 漏掉的那一行
                        spec.loader.exec_module(m2)
                        mod, why = m2, ""
                        break
                    except Exception as exc:
                        sys.modules.pop(name, None)
                        why = f"{cand.name}: {type(exc).__name__}: {str(exc)[:100]}"
                break
            p = p.parent
    _CEL_ERR.append(why)
    _CEL_CACHE.append(mod)
    return mod


def cel_why() -> str:
    """回上一次 `_celeritas()` 失敗的原因;沒載過回 `"(未載)"`,成功回 `""`。

    L87:加速器缺席可以,**不講原因的缺席等於假綠**。
    """
    if not _CEL_ERR:
        return "(未載)"
    return _CEL_ERR[0]


def cel_submit(fn, *args, _cel=None, _submit_fallback: bool = True, **kw):
    """把工作丟給 Celeritas 的暖執行緒池;拿不到就**直接呼叫**(graceful)。

    _cel             指定 Celeritas 模組(遷移現場沿用本檔原本的 `_CEL`);
                     不給就由正典自己找。給 None 且找不到 → 直呼。
    _submit_fallback True 時,`_LazyPool.submit` 不可用會再試 `_CEL.submit`。
                     活樹兩群的差別**只在這裡**,而且只有「有 submit 沒有 _LazyPool」時分得出來。
    """
    cel = _cel if _cel is not None else _celeritas()
    if cel is not None:
        pool = getattr(cel, "_LazyPool", None)
        if pool is not None:
            try:
                return pool.submit(fn, *args, **kw)
            except Exception:
                pass
        if _submit_fallback:
            sub = getattr(cel, "submit", None)
            if sub is not None:
                try:
                    return sub(fn, *args, **kw)
                except Exception:
                    pass
    return fn(*args, **kw)


# ────────────────── L77 掃描排除清單(批626 正典化) ──────────────────
#: L77(批594/597):**任何會寫檔的掃描器都要帶這張清單**。
#: 批626 量到 `via_accel_injector_v0100` 的 SKIP_FRAGS 少了 `references/intake`
#: 等四段 —— 那支只要跑 `--run` 就會寫進收容正本(正本零觸碰)。
#: 少一段就是一個破口,所以清單只能有一份,寫在這裡。
SCAN_EXCLUDE = (
    #: 批647:批647 正典 U/I TEMPLATE:byte-exact 正本,完整性由它自己的 manifest.json(223 筆 sha256)守;注入任何橋都會打破那份完整性,故正本零觸碰優先於全樹導入令。它的驗收走 `via-ui --check`(CGC_MDL160 template 車道),不走全樹雙橋
    "VIA_HTML_UI",
    "references/intake",   # 收容正本:帶 sha 冊,零觸碰
    "_superseded",         # 退役區
    "RetiredEngines",      # 退役引擎
    "_backup",             # 備份
    "SCOPE_COPY",          # 範圍副本
    "__pycache__",
    "node_modules",
    "site-packages",
    ".venv",
    "_vdf_envs",
    "quarantine",
    "_review_quarantine",
    "rename_runs",
    "_via_mother_root_reconciliation_runs",
    "VIA_Reports",         # 產物/存證
    "rollback",
    "_syntaxfix_",
    "evidence",
    "package_samples",
    "_inbox_to_classify",
)


def scan_excluded(rel: str) -> bool:
    """`rel` 是**相對樹根**的路徑字串;命中排除清單或檔名含 `_sha` 回 True。

    檔名含 `_sha` 另判(批597):`_sha` 只在**檔名**算鏡像標記,
    整串路徑比對會把 `.../foo_shard/bar.py` 這種也誤殺。
    """
    rp = str(rel).replace("\\", "/")
    if any(f in rp for f in SCAN_EXCLUDE):
        return True
    return "_sha" in rp.rsplit("/", 1)[-1]


def tail_files(root, suffix: str = ".py") -> list:
    """**尾版律**的正典實作:同一族只留版號最大的那一支。

    批631 量到的一個判準錯誤:把沒有版號的 `X.py` 當成**獨立一支**,
    於是 `X.py` 與 `X_v0102.py` 會**同時**被算成活件。
    實例:`VRN_ENG062_SummarizerV1.py` 旁邊就有 `_v0101` / `_v0102`
    ——那支沒版號的是**最早那一版**,不是另一支引擎。
    把它算成活件,掃出來的「債」裡就混著早就退役的東西,修它是白工。

    規則:沒版號 = 同族的**第 0 版**;族內取版號最大的。
    `_sha` 鏡像與 L77 排除清單一律先濾掉。
    """
    import re as _re
    root = Path(root)
    ver = _re.compile(r"^(.*)_v(\d{3,4})$")
    fam: dict = {}
    for q in root.rglob(f"*{suffix}"):
        try:
            rel = str(q.relative_to(root)).replace("\\", "/")
        except ValueError:
            continue
        if scan_excluded(rel):
            continue
        m = ver.match(q.stem)
        stem, num = (m.group(1), int(m.group(2))) if m else (q.stem, 0)
        fam.setdefault((str(q.parent), stem), []).append((num, q))
    out = []
    for v in fam.values():
        v.sort(key=lambda x: x[0])
        out.append(v[-1][1])
    return sorted(out)


def frozen_dirs(root) -> set:
    """批597:目錄內有指名自身 `.py` 的 MANIFEST=凍結,寫檔器不得動。回絕對路徑字串集合。"""
    root = Path(root)
    out = set()
    for mf in root.rglob("MANIFEST*.json"):
        try:
            rel = str(mf.relative_to(root)).replace("\\", "/")
        except ValueError:
            continue
        if scan_excluded(rel):
            continue
        try:
            if ".py" in mf.read_text(encoding="utf-8-sig", errors="ignore"):
                out.add(str(mf.parent))
        except Exception:
            continue
    return out


# ────────────────────────── 八碼雜湊 ──────────────────────────
def hash8(s: str, *, errors: str = "strict", prefer_xxhash: bool = True) -> str:
    """八碼大寫雜湊。有 xxhash 就用(快),沒有就 sha256 —— 兩條路**結果不同**,
    所以同一棵樹上有沒有裝 xxhash 會影響雜湊值。這是活樹本來就有的性質,不是本正典引入的;
    量出來的 14 處全是這個寫法,照原樣搬。

    errors        `s.encode()` 的錯誤處理。活樹 13 處用預設(`strict`),1 處用 `replace`。
                  兩者對一般字串同解。
    prefer_xxhash False = **永遠走 sha256**。`generic_layout_engine.hash8` 是這一種——
                  它根本沒有 xxhash 分支。在裝了 xxhash 的機器上,兩條路**雜湊值不一樣**;
                  把它併成預設值等於**悄悄改掉它產生的所有 id**。這個選項就是為了不吃掉這個差異。
    """
    xx = safe_import("xxhash") if prefer_xxhash else None
    if xx is not None:
        return xx.xxh64(s.encode()).hexdigest()[:8].upper()
    return hashlib.sha256(s.encode("utf-8", errors=errors)).hexdigest()[:8].upper()


# ────────────────────────── 數字與旗標 ──────────────────────────
def num(s, *, drop=(), positive: bool = False):
    """逗號千分位字串 → float;轉不動回 None(**不拋**,因為抽取器找不到數字時的常態就是 None)。

    批597 VDF 併入:VDF 尾版有五支 `_num`,**分群之後是五個群**,不是同一件事——
      · ENG055 / ENG057  純轉換 → 不用參數(語料 28 組零差異)
      · ENG056           哨兵清單含 **'nan'**;不加 `drop` 的話 `float('nan')` 會回 nan
                         而不是 None(語料量到 2 處差異)
      · ENG063 / ENG075  只收 **正數**;不加 `positive` 的話 '0' / '-inf' / 'nan'
                         全部會被放行(語料量到 8 處差異)
    把差異寫成參數,呼叫端看得見;寫死成「大家都一樣」就是遷出行為變更。

    drop      去逗號+strip 後命中這個集合就回 None(哨兵字串,例:`('', '--', 'nan')`)
    positive  True 時只收 `f > 0`(nan > 0 為 False,所以 nan 也會被擋掉)
    """
    try:
        f = float(str(s).replace(",", ""))
    except Exception:
        return None
    if drop and str(s).replace(",", "").strip() in drop:
        return None
    if positive and not (f > 0):
        return None
    return f


def argval(args: list, flag: str, default=None, *, as_path: bool = False,
           quiet: bool = False, dashdash: bool = False):
    """從 argv 取旗標值。缺值=**誠實 None,不 IndexError**(批425 慣例)。

    as_path  True 回 `Path`(活樹 2 處是這一種),False 回字串。
    quiet    True 不印提示。
    default  批597 VDF 併入:VDF 三支 `_arg(a, flag, default=None)` 允許**呼叫端給預設**,
             而且活樹**是位置參數在用**(`_arg(a, "--db", str(DB_TW))`),所以這裡也放在
             `*` 前面;原本的關鍵字呼叫一個都不會壞(多一個位置槽不會少掉關鍵字)。
             正典原本一律回 None——直接換就是遷出行為變更。預設值每次回**新的一份**
             (L76:可變預設值共享過一次,位元組比不出來)。
    dashdash 批597:VDF 那三支**不會**把 `--` 開頭的下一個 token 當成「沒有值」,
             正典會。誰對誰錯不在這裡裁定(LL90),差異寫成參數讓呼叫端選。
    """
    if flag not in args:
        return _fresh(default)
    i = args.index(flag) + 1
    if i >= len(args) or (not dashdash and str(args[i]).startswith("--")):
        if not quiet:
            print(f"[旗標] {flag} 後面沒有值=忽略(誠實提示,不當作預設)")
        return _fresh(default)
    return Path(args[i]) if as_path else args[i]


def nan_safe(o):
    """`json.dumps(default=…)` 用:NaN / Inf → None,其餘 `str()`。

    活樹 `_jwrite` 有 12 處用這個、2 處用純 `str`。**差別是真的**:
    純 `str` 會把 `nan` 寫成字串 `"nan"`,下游再讀回來就變成一個看起來有值的髒資料。
    """
    return None if isinstance(o, float) and (math.isnan(o) or math.isinf(o)) else str(o)



# ────────────────── 期別時鐘(側線 2026-09-24:民國日期正本 + 期別滯後) ──────────────────
#: 規則正本在冊上;本檔只讀冊。冊外不得另寫日期欄清單或期別換算(LL442:手寫清單前先找正本)。
PERIOD_RULES_GLOB = "VIA_SSOT_PeriodRules_v*.json"
_RULES_CACHE: dict = {}


def load_period_rules(path=None) -> dict:
    """讀期別規則正本(`registry/VIA_SSOT_PeriodRules_v*.json` 尾版)。缺席=**大聲拋**
    (VIA_LibCanon 律①:正典不在就別假裝有——靜默回預設值跟假綠是同一個病)。回傳值請當唯讀。"""
    if path is None:
        hits = sorted((Path(__file__).resolve().parent / "registry").glob(PERIOD_RULES_GLOB))
        if not hits:
            raise FileNotFoundError("[FAIL] 期別規則正本缺席:supportive modules/registry/" + PERIOD_RULES_GLOB)
        path = hits[-1]
    p = Path(path)
    key = (str(p), p.stat().st_mtime_ns)
    if key not in _RULES_CACHE:
        _RULES_CACHE.clear()
        _RULES_CACHE[key] = _json.loads(p.read_text(encoding="utf-8"))
    return _RULES_CACHE[key]


def date_columns(rules: dict | None = None) -> tuple:
    """日期欄聯集(冊上 corrected 序)。既有讀者請**先認自己原本那份、認不到才用這份補**
    (冊上 primary_first_rule:已量得到的表日期欄一個都不換——只增不減)。"""
    r = rules if rules is not None else load_period_rules()
    return tuple(r["date_columns"]["corrected"])


def fallback_date_columns(own=(), rules: dict | None = None) -> tuple:
    """v0106:補位欄——讀者自己那份一欄都認不到時,才依序試這幾欄(冊上 fallback_rule 的**唯一實作**)。
    = corrected − own − record_only,照 corrected 序;own 大小寫不計。
    寫入時間戳(record_only:ts · snapshot_at · run_at)不是資料日,補位一律不給。"""
    r = rules if rules is not None else load_period_rules()
    mine = {str(c).lower() for c in (own or ())}
    skip = {str(c).lower() for c in (r["date_columns"].get("record_only") or ())}
    return tuple(c for c in r["date_columns"]["corrected"] if c.lower() not in mine and c.lower() not in skip)


def _iso_or_none(y: int, m: int, d: int):
    try:
        return _date(y, m, d).isoformat()
    except ValueError:
        return None


def roc_to_iso(s):
    """民國/西元/緊湊日期字串 → `'YYYY-MM-DD'`;認不出或不是真日期=None(**不猜**)。

    先整串比對(ISO[含時間] · 七碼民國 0–119 年 · 八碼西元),再照 ENG055 `_roc_to_iso` 的搜尋序
    (字串裡夾著日期也認:115年09月23日 · 2025/9/12 · 115/09/23 · 20250912 · 1150913)。
    要保留原值的呼叫端寫 `roc_to_iso(v) or str(v)`——那是呼叫端的決定,不是本函式的。"""
    if s is None:
        return None
    t = str(s).strip()
    if not t:
        return None
    m = _re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})(?:[ T].*)?", t)
    if m:
        return _iso_or_none(int(m[1]), int(m[2]), int(m[3]))
    m = _re.fullmatch(r"([01]\d{2})(\d{2})(\d{2})", t)            # 七碼民國(TWSE openapi 出表日期 1150913)
    if m:
        return _iso_or_none(1911 + int(m[1]), int(m[2]), int(m[3]))
    m = _re.fullmatch(r"((?:19|20)\d{2})(\d{2})(\d{2})", t)       # 八碼西元(v0106:19xx 也認;v0105 只認 20xx)
    if m:
        return _iso_or_none(int(m[1]), int(m[2]), int(m[3]))
    m = _re.search(r"(\d{2,3})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", t)
    if m:
        return _iso_or_none(1911 + int(m[1]), int(m[2]), int(m[3]))
    m = _re.search(r"(?<!\d)(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})(?!\d)", t)
    if m:
        return _iso_or_none(int(m[1]), int(m[2]), int(m[3]))
    m = _re.search(r"(?<!\d)(\d{2,3})/(\d{1,2})/(\d{1,2})(?!\d)", t)
    if m:
        return _iso_or_none(1911 + int(m[1]), int(m[2]), int(m[3]))
    m = _re.search(r"(?<!\d)(20\d{6})(?!\d)", t)
    if m:
        d = m[1]
        return _iso_or_none(int(d[:4]), int(d[4:6]), int(d[6:]))
    m = _re.search(r"(?<!\d)(1[01]\d{5})(?!\d)", t)
    if m:
        d = m[1]
        return _iso_or_none(1911 + int(d[:3]), int(d[3:5]), int(d[5:]))
    return None


def roc_ym(v):
    """v0106:民國年月 '11507' → '202607'(字串裡的數字取出來,5 或 6 碼;月 1–12、民國 80–200 年);異常=None(**不猜**)。
    實作逐字取自 VDF_ENG063_MonthlyRevenue_v0105 `_roc_ym`(MOPS 月營收「資料年月」);自測 ㊱ 逐式零差異。"""
    d = "".join(ch for ch in str(v) if ch.isdigit())
    if len(d) not in (5, 6):
        return None
    y, m = int(d[:-2]), int(d[-2:])
    if not (1 <= m <= 12 and 80 <= y <= 200):
        return None
    return f"{y + 1911}{m:02d}"


def roc_to_iso_keep(s) -> str:
    """v0106:認得的日期與 `roc_to_iso` 同答;認不出(或不是真日期)=回原值 `str(s).strip()`。
    這是 VDF_ENG055 `_iso_date` 的直通語意(API 回來的欄位值認不出就原樣落表,不丟、不猜)。
    呼叫端用**綁定**:`_iso_date = _LIB.UTILS.roc_to_iso_keep`(VIA_LibCanon 律②)。"""
    return roc_to_iso(s) or str(s).strip()


def _add_months(y: int, m: int, k: int) -> tuple:
    t = y * 12 + (m - 1) + k
    return t // 12, t % 12 + 1


def _month_of(v: str):
    """月期別值 → (年, 月);認:YYYYMM · YYYY-MM · 任何 roc_to_iso 認得的日期 · 民國 115/08 · 115年8月。"""
    t = v.strip()
    m = _re.fullmatch(r"(\d{4})(\d{2})", t) or _re.fullmatch(r"(\d{4})-(\d{2})", t)
    if m and 1 <= int(m[2]) <= 12:
        return int(m[1]), int(m[2])
    iso = roc_to_iso(t)
    if iso:
        return int(iso[:4]), int(iso[5:7])
    m = _re.fullmatch(r"(\d{2,3})\s*(?:/|年)\s*(\d{1,2})\s*月?", t)
    if m and 1 <= int(m[2]) <= 12:
        return 1911 + int(m[1]), int(m[2])
    return None


_Q_ENDS = ((3, 31), (6, 30), (9, 30), (12, 31))


def _quarter_end(d):
    q = (d.month - 1) // 3
    return _date(d.year, *_Q_ENDS[q])


def _next_quarter_end(qe):
    q = _Q_ENDS.index((qe.month, qe.day))
    return _date(qe.year + (1 if q == 3 else 0), *_Q_ENDS[(q + 1) % 4])


def _quarter_due(qe, due_map: dict):
    rule = str(due_map[f"{qe.month:02d}-{qe.day:02d}"])
    year = qe.year + (1 if rule.startswith("+1y-") else 0)
    mm, dd = rule.replace("+1y-", "").split("-")
    return _date(year, int(mm), int(dd))


def period_lag(table: str, value, *, db: str = "", today=None, rules: dict | None = None) -> dict:
    """一張表的「最新值」→ 滯後判讀(多態,不是二元):
    LAG_DAYS(日頻:今天−最新日,與 v0105 之前各處算法一致)· PERIOD_DUE(月/季表:下一期法定期限已過幾天)·
    FROZEN(凍結庫/舊暫存表:照列不計燈)· LABEL(期別標籤)· UNPARSED(認不出,不猜)· EMPTY。
    回 {state, lag_days, iso, period, due, rule};規則全在冊上(load_period_rules)。"""
    r = rules if rules is not None else load_period_rules()
    today = today or _date.today()
    t = str(table or "")
    v = "" if value is None else str(value).strip()
    out = {"state": "", "lag_days": None, "iso": None, "period": "", "due": None, "rule": ""}
    fz = r.get("frozen") or {}
    if (db and fz.get("db_rx") and _re.search(fz["db_rx"], str(db))) or (fz.get("table_rx") and _re.search(fz["table_rx"], t)):
        out.update(state="FROZEN", rule="frozen", iso=roc_to_iso(v) if v else None)
        return out
    if not v:
        out["state"] = "EMPTY"
        return out
    for name, cad in (r.get("cadences") or {}).items():
        if not _re.search(cad["tables_rx"], t):
            continue
        if cad.get("period") == "month":
            ym = _month_of(v)
            if ym:
                ny, nm = _add_months(ym[0], ym[1], 1)
                dy, dm = _add_months(ny, nm, 1)
                due = _date(dy, dm, int(cad["due"]["next_month_day"]))
                out.update(state="PERIOD_DUE", period="month", rule=name, iso=f"{ym[0]:04d}-{ym[1]:02d}-01",
                           due=due.isoformat(), lag_days=max(0, (today - due).days))
                return out
        elif cad.get("period") == "quarter":
            iso = roc_to_iso(v)
            if iso:
                qe = _quarter_end(_date.fromisoformat(iso))
                due = _quarter_due(_next_quarter_end(qe), cad["due"])
                out.update(state="PERIOD_DUE", period="quarter", rule=name, iso=qe.isoformat(),
                           due=due.isoformat(), lag_days=max(0, (today - due).days))
                return out
        break                                   # 表對到期別規則但值認不出 → 往下誠實落 LABEL / UNPARSED
    if _re.fullmatch(r["value_shapes"]["LABEL"]["rx"], v):
        out["state"] = "LABEL"
        return out
    iso = roc_to_iso(v)
    if iso:
        out.update(state="LAG_DAYS", period="day", iso=iso, lag_days=(today - _date.fromisoformat(iso)).days)
        return out
    out["state"] = "UNPARSED"
    return out

def _fresh(v):
    """可變預設值每次回**新的一份**(L76 / LL147)。

    批597:`argval(default=...)` 讓呼叫端給預設值。如果直接把那個物件回出去,
    多個呼叫端拿到的是**同一個** list/dict,一邊 append 另一邊就跟著變——
    這正是批593 `bind_read(missing={})` 那個蟲,而且**位元組比對驗不出來**
    (差的是物件同一性,不是內容)。所以正典自己負責複製,不靠呼叫端記得。
    這一支是接 SUP_MDL752 的同名助手(綁定不另造),752 缺席就照 `_jsonio()` 那條路大聲拋。
    """
    return _jsonio()._fresh(v)


def _jsonio():
    """批592 的 JSON 讀寫正典;`_jwrite` 那 14 處直接接它,不另造一支。"""
    p = Path(__file__).resolve()
    while p.parent != p:
        hits = sorted((p / "supportive modules").glob("SUP_MDL752_VIAJsonIO_v*.py"))
        if hits:
            import importlib.util as ilu
            spec = ilu.spec_from_file_location("VIA_JSONIO", hits[-1])
            mod = ilu.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
        p = p.parent
    raise RuntimeError("[FAIL] JSON 讀寫正典缺席:supportive modules/SUP_MDL752_VIAJsonIO_v*.py")


def bind_jwrite(*, mkdir: bool = True, default=nan_safe, quiet_fail: bool = False):
    """回一個 `_jwrite(p, data)` 綁定,底下走 SUP_MDL752。

    mkdir       活樹 11 處**沒有** mkdir、3 處有。沒有 mkdir 時,父夾不在就會拋——
                那是原本的行為,照搬。
    quiet_fail  True 時吞掉例外回 False、成功回 True(活樹 1 處是這一種)。
    """
    js = _jsonio()

    def _w(p, data):
        if quiet_fail:
            try:
                js.write(p, data, indent=2, default=default, atomic=False, mkdir=mkdir)
                return True
            except Exception:
                return False
        js.write(p, data, indent=2, default=default, atomic=False, mkdir=mkdir)
        return None
    return _w


def bind_import(**kw):
    return lambda name: safe_import(name, **kw)


def bind_cel(**kw):
    return lambda fn, *a, **k: cel_submit(fn, *a, **kw, **k)


def bind_hash8(**kw):
    return lambda s: hash8(s, **kw)


def bind_argval(**kw):
    return lambda args, flag: argval(args, flag, **kw)


# ────────────────────────── 自測:逐群重放 ──────────────────────────
def selftest() -> int:
    import json
    import tempfile
    n, fails = [0], []

    def chk(label, ok, extra=""):
        n[0] += 1
        print(f"  [{'OK' if ok else 'FAIL'}] {label}" + (f" ({extra})" if extra else ""))
        if not ok:
            fails.append(label)

    import ast as _ast
    tree = _ast.parse(Path(__file__).read_text(encoding="utf-8"))
    mods = set()
    for nd in _ast.walk(tree):
        if isinstance(nd, _ast.Import):
            mods |= {a.name.split(".")[0] for a in nd.names}
        elif isinstance(nd, _ast.ImportFrom) and nd.module:
            mods.add(nd.module.split(".")[0])
    chk("① 零網路零安裝:語法樹裡沒有 requests/httpx/urllib/subprocess 的 import",
        not (mods & {"requests", "httpx", "urllib", "subprocess", "socket", "http"}),
        f"(import:{sorted(mods)})")
    chk("② 名字像但不是同一件事的具名在冊(close / export_csv 是類別方法;"
        "有狀態的那版 _argval 綁在模組狀態上)",
        len(NOT_SAME_THING) == 4 and all(len(v) > 20 for v in NOT_SAME_THING.values()))

    # ── L76 同族:早綁 vs 晚讀 ──────────────────────────────────────────
    # 批594 在**出貨前**抓到的:VRN 的 `_cel_submit` 讀的是開機函式事後用 global 填進去的值。
    # 這一檢用合成語料把那個陷阱演一次,免得下一次又有人把「晚讀」綁成「早綁」。
    _state = {"ok": False, "cel": None}
    _early = _CelFrozen = _state["cel"] if _state["ok"] else None      # ← 早綁:現在就取值
    _state.update(ok=True, cel="POOL")                                  # ← 開機函式事後才填
    _late = _state["cel"] if _state["ok"] else None
    chk("②之二 **早綁不等於晚讀**(L76 同族):import 當下取值會把開機前的狀態凍住;"
        "VRN `_cel_submit` 17 處就是這一種,具名不遷",
        _early is None and _late == "POOL"
        and "_cel_submit" in " ".join(NOT_SAME_THING),
        f"(早綁 {_early} · 晚讀 {_late})")

    # ── safe_import:四群 ──
    chk("③ safe_import:找得到回模組、找不到回 None",
        safe_import("json") is not None and safe_import("no_such_mod_zzz") is None)

    class _Boom:
        def __init__(self):
            raise SystemExit(3)
    chk("④ `catch_all=True` 才吞 BaseException(活樹 7 處是 bare `except:`——"
        "**那是潛在缺陷不是風格**:會把 `sys.exit()` 吃掉當成「沒有這個模組」)",
        _eats(lambda: safe_import("json", catch_all=True), SystemExit) is False
        and _raises_base(lambda: _si_probe(False)) and not _raises_base(lambda: _si_probe(True)),
        "合成模組在 import 時 sys.exit(3):catch_all=False 讓它拋 · True 吞掉回 None")

    # ── cel_submit:兩群(有沒有第二層退路)──
    class _P:
        @staticmethod
        def submit(fn, *a, **k):
            return ("pool", fn(*a, **k))

    class _CelBoth:
        _LazyPool = _P

        @staticmethod
        def submit(fn, *a, **k):
            return ("cel", fn(*a, **k))

    class _CelSubmitOnly:
        @staticmethod
        def submit(fn, *a, **k):
            return ("cel", fn(*a, **k))
    f = lambda x: x * 2                                          # noqa: E731
    # 批626:v0101 的這一檢最後一段寫成
    #     `... and cel_submit(f, 3, _cel=None) == 6 or cel_submit(f, 3, _cel=None) == ("pool", 6)`
    # 它綠,是因為 `_celeritas()` **壞著**:永遠回 None,所以 `_cel=None` 永遠直呼回 6。
    # 換句話說,**這盞燈是靠那個 bug 才亮的**——修好載入器它立刻紅。
    # (順帶:`A and B and C or D` 的優先序也不是作者想的那樣。)
    # 正寫法:真 Celeritas 在位就**必須**回 Future 且算出 6;不在位才回 6。
    _cel_live = _celeritas()
    _r5 = cel_submit(f, 3, _cel=None)
    _r5_ok = ((_r5.result() == 6) if hasattr(_r5, "result") else (_r5 == 6))
    chk("⑤ cel_submit:有 _LazyPool 就走它;**兩群的差別只在「有 submit 沒有 _LazyPool」時**;"
        "`_cel=None` 交給正典載入器——在位走池(回 Future)、缺席才直呼",
        cel_submit(f, 3, _cel=_CelBoth) == ("pool", 6)
        and cel_submit(f, 3, _cel=_CelSubmitOnly) == ("cel", 6)
        and cel_submit(f, 3, _cel=_CelSubmitOnly, _submit_fallback=False) == 6
        and _r5_ok
        and (hasattr(_r5, "result") if getattr(_cel_live, "_LazyPool", None) is not None else _r5 == 6),
        f"有池走池 · 無池有 submit:退路開=走 submit / 關=直呼 · _cel=None → {type(_r5).__name__}")

    # ── hash8:兩群 ──
    h = hash8("測試 abc")
    _sha = hashlib.sha256("測試 abc".encode()).hexdigest()[:8].upper()
    _has_xx = safe_import("xxhash") is not None
    chk("⑥ hash8:八碼大寫、同輸入同輸出、errors=replace 對一般字串同解",
        len(h) == 8 and h.isupper() and h == hash8("測試 abc")
        and h == hash8("測試 abc", errors="replace"), h)
    chk("⑥之二 `prefer_xxhash=False` **永遠走 sha256**(有一處根本沒有 xxhash 分支;"
        "把它併成預設值,等於在裝了 xxhash 的機器上悄悄改掉它產生的所有 id)",
        hash8("測試 abc", prefer_xxhash=False) == _sha
        and ((h != _sha) if _has_xx else (h == _sha)),
        f"(本機 xxhash {'在' if _has_xx else '不在'} · 預設 {h} · 強制 sha256 {_sha})")

    # ── num / argval ──
    chk("⑦ num:逗號千分位吃得下,轉不動回 None(**不拋**)",
        num("1,234.5") == 1234.5 and num("abc") is None and num(None) is None)
    chk("⑧ argval:缺值誠實 None 不 IndexError;下一個是旗標也算缺值;as_path 回 Path",
        argval(["--a", "x"], "--a", quiet=True) == "x"
        and argval(["--a"], "--a", quiet=True) is None
        and argval(["--a", "--b"], "--a", quiet=True) is None
        and argval(["--a", "p"], "--zz", quiet=True) is None
        and isinstance(argval(["--a", "p"], "--a", as_path=True, quiet=True), Path))
    chk("⑨ nan_safe:NaN/Inf → None(純 str 會寫成字串 \"nan\",下游讀回來是髒資料)",
        nan_safe(float("nan")) is None and nan_safe(float("inf")) is None
        and nan_safe(Path("/a")) == str(Path("/a")))      # v0105:平台中立(Windows 是 \\a;舊檢寫死 "/a" 在工作站自紅)

    # ── _jwrite 三群:逐群跟原始實作比**位元組** ──
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        payload = {"k": "值", "nan": float("nan"), "p": Path("/a")}

        def orig_nomkdir(p, data):
            Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=nan_safe),
                               encoding="utf-8")

        def orig_mkdir_str(p, data):
            Path(p).parent.mkdir(parents=True, exist_ok=True)
            Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str),
                               encoding="utf-8")
        bad = []
        for label, orig, canon, sub in (
                ("72717ae7ff·11處 無 mkdir · nan_safe", orig_nomkdir,
                 bind_jwrite(mkdir=False), "a"),
                ("57f48696c7·2處 有 mkdir · default=str", orig_mkdir_str,
                 bind_jwrite(mkdir=True, default=str), "b/c"),
                ("ea7ae6255d·1處 有 mkdir · nan_safe · 吞例外回 bool", orig_nomkdir,
                 bind_jwrite(mkdir=True, quiet_fail=True), "d/e")):
            pa, pb = t / f"{sub}_a.json", t / f"{sub}_b.json"
            pa.parent.mkdir(parents=True, exist_ok=True)
            orig(pa, payload)
            canon(pb, payload)
            if pa.read_bytes() != pb.read_bytes():
                bad.append(label)
        chk("⑩ **零損失(_jwrite)**:3 群逐群跟原始實作比**位元組**,並且底下走的是"
            "批592 的 SUP_MDL752 —— 不另造一支 JSON 寫法",
            not bad, "; ".join(bad) if bad else "位元組全同")
        chk("⑪ `quiet_fail=True` 真的吞:父夾不在也不拋,回 False",
            bind_jwrite(mkdir=False, quiet_fail=True)(t / "no" / "such" / "x.json", {}) is False)

    # ── LL147:綁定工廠不得共用可變狀態 ──
    b1, b2 = bind_argval(quiet=True), bind_argval(quiet=True)
    chk("⑫ 綁定工廠各自獨立(LL147/L76:批593 就是栽在工廠綁死一個可變物件上)",
        b1 is not b2 and b1(["--a", "1"], "--a") == "1" and b2(["--a", "2"], "--a") == "2")

    # ⑬ 批597 VDF `_num` 五群零損失 —— 對照組是**原實作逐字抄**
    #     (批592 教訓:對照組抄錯,證出來的零損失就是假的)
    def _c055(v):
        try:
            return float(str(v).replace(",", "")) if v not in (None, "", "--") else None
        except ValueError:
            return None

    def _c056(v):
        try:
            t = str(v).replace(",", "").strip()
            return float(t) if t not in ("", "--", "-", "None", "nan") else None
        except ValueError:
            return None

    def _c057(x):
        try:
            return float(str(x).replace(",", "").strip())
        except Exception:
            return None

    def _c063(v):
        try:
            f = float(str(v).replace(",", ""))
            return f if f > 0 else None
        except Exception:
            return None

    def _c075(v):
        try:
            f = float(str(v).replace(",", "").strip())
            return f if f > 0 else None
        except Exception:
            return None

    NCORP = [None, "", "--", "-", "None", "nan", "NaN", "inf", "-inf", " 1,234.5 ", "1,234",
             "0", "-3.5", "3.5", 0, -1, 2.5, True, False, [], {}, "abc", "1e3", "  ",
             "12,", ",12", float("nan"), float("inf")]
    NBIND = {"ENG055": {}, "ENG056": {"drop": ("", "--", "-", "None", "nan")},
             "ENG057": {}, "ENG063": {"positive": True}, "ENG075": {"positive": True}}
    NCTRL = {"ENG055": _c055, "ENG056": _c056, "ENG057": _c057,
             "ENG063": _c063, "ENG075": _c075}

    def _same(a, b):
        if isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
            return True
        return type(a) is type(b) and a == b

    def _call(fn, *a, **k):
        try:
            return ("OK", fn(*a, **k))
        except Exception as exc:
            return ("EXC", f"{type(exc).__name__}: {exc}")

    nbad = []
    for k_, ctrl in NCTRL.items():
        for v_ in NCORP:
            x, y = _call(ctrl, v_), _call(num, v_, **NBIND[k_])
            ok_ = x[0] == y[0] and (_same(x[1], y[1]) if x[0] == "OK" else x[1] == y[1])
            if not ok_:
                nbad.append(f"{k_} {v_!r}: 原 {x} ≠ 正典 {y}")
    chk("⑬ **零損失(num)**:VDF 五支 `_num` 分群後是**五個群**(兩支純轉換、一支哨兵含 "
        "'nan'、兩支只收正數),逐群綁參數 × 28 組語料逐一同解",
        not nbad, "; ".join(nbad[:2]) if nbad else
        f"{len(NCTRL)} 群 × {len(NCORP)} 組 = {len(NCTRL) * len(NCORP)} 全同")

    # ⑭ 批597 VDF `_arg` 三支(同一群)零損失 + 預設值不得共用
    def _carg(a, flag, default=None):
        if flag in a:
            i = a.index(flag)
            if i + 1 < len(a):
                return a[i + 1]
        return default

    ACORP = [(["--a", "1"], "--a"), (["--a"], "--a"), ([], "--a"), (["--a", "--b"], "--a"),
             (["x", "--a", "y", "--a", "z"], "--a"), (["--a", ""], "--a"), (["--a", "-5"], "--a")]
    abad = []
    for a_, f_ in ACORP:
        for d_ in (None, "D", 0):
            x = _call(_carg, list(a_), f_, d_)
            y = _call(argval, list(a_), f_, default=d_, quiet=True, dashdash=True)
            if x != y:
                abad.append(f"{a_} {f_} default={d_!r}: 原 {x} ≠ 正典 {y}")
    d1 = argval([], "--x", default=[])
    d2 = argval([], "--x", default=[])
    d1.append("髒")
    chk("⑭ **零損失(argval)**:VDF 三支 `_arg` 同一群,`default=` + `dashdash=True` "
        "逐組同解;且可變預設值**每次回新的一份**(L76:兩次拿到的不得是同一個物件)",
        not abad and d1 is not d2 and d2 == [],
        "; ".join(abad[:2]) if abad else f"{len(ACORP)}×3 全同 · 預設值獨立")

    # ── 批626 補四檢:正典自己的加速器道與 L77 排除清單 ──
    _CEL_CACHE.clear(); _CEL_ERR.clear()
    _cel = _celeritas()
    _tree_has = any((Path(__file__).resolve().parent / r).exists() for r in CEL_CANDIDATES)
    chk("⑰ Celeritas 載入器:樹上有本體就**必須**載得起來(批594 漏了 sys.modules 登記,"
        "v0100/v0101 這裡永遠是 None,而 graceful 把它蓋住不報錯)",
        (not _tree_has) or (_cel is not None),
        f"(樹上有本體={_tree_has} · 載到={_cel is not None} · why={cel_why()[:60]})")
    chk("⑱ 缺席必附理由(L87):載不到時 cel_why() 不得是空字串",
        (_cel is not None) or (cel_why() not in ("", "(未載)")),
        f"(why={cel_why()[:60]})")
    _pool = getattr(_cel, "_LazyPool", None) if _cel is not None else None
    _r = cel_submit(lambda x: x * 2, 21)
    chk("⑲ 池子在位就**真的送進池子**:cel_submit 回 Future 而不是算好的值"
        "(回值是算好的=退回直呼=加速器一次也沒用到)",
        (_pool is None) or hasattr(_r, "result"),
        f"(池子={_pool is not None} · 回傳={type(_r).__name__})")
    chk("⑳ 而且答案要對(平行不能換掉結果)",
        (_r.result() if hasattr(_r, "result") else _r) == 42)
    chk("㉑ L77 排除清單:四段破口全在(收容正本/退役/退役引擎/備份)",
        all(scan_excluded(f"{k}/x.py") for k in
            ("references/intake", "_superseded", "RetiredEngines", "_backup", "SCOPE_COPY")))
    chk("㉒ `_sha` 只算檔名(整串比對會誤殺 foo_shard/bar.py 這種活檔)",
        scan_excluded("a/b/x_sha1234.py") and not scan_excluded("a/foo_shard/bar.py"))
    chk("㉓ 活檔不得被排除(排除清單過寬=把要做的事做不到)",
        not scan_excluded("functional modules/VRN/VRN_ENG072_FirstPageText_v0135.py"))
    with tempfile.TemporaryDirectory() as _td:
        _rt = Path(_td); (_rt / "fam").mkdir()
        (_rt / "fam" / "MANIFEST_x.json").write_text('{"files":["a.py"]}', encoding="utf-8")
        (_rt / "fam" / "a.py").write_text("X=1\n", encoding="utf-8")
        (_rt / "open").mkdir(); (_rt / "open" / "b.py").write_text("Y=1\n", encoding="utf-8")
        for _n in ("Eng.py", "Eng_v0101.py", "Eng_v0102.py", "Solo.py", "Eng_sha99.py"):
            (_rt / _n).write_text("X=1\n", encoding="utf-8")
        # 自審:`_rt` 裡還有 ㉔ 那組凍結夾夾具(fam/a.py · open/b.py),
        #   直接比整份名單會把它們也算進來——**夾具共用一個夾子,斷言就要只看自己那一族**。
        _t3 = [x.name for x in tail_files(_rt) if x.name.startswith(("Eng", "Solo"))]
        chk("㉕ 尾版律:沒版號的 `Eng.py` 是同族第 0 版,不是另一支引擎"
            "(算成獨立一支的話,掃出來的債裡會混著早就退役的東西,修它是白工);"
            "`_sha` 鏡像不進名單",
            _t3 == ["Eng_v0102.py", "Solo.py"], str(_t3))
        _fz = frozen_dirs(_rt)
        chk("㉔ 批597 凍結夾:含指名自身 .py 的 MANIFEST 之夾認得出,沒 MANIFEST 的夾不誤凍",
            str(_rt / "fam") in _fz and str(_rt / "open") not in _fz, f"({len(_fz)} 夾)")
    # ── v0105(側線 2026-09-24):期別時鐘八檢 ──
    import re as _rx

    def _o055_iso(v):                                  # VDF_ENG055_OmniFetch_v0111._iso_date 原實作(語料對照用,逐字)
        t = str(v).strip()
        if _rx.fullmatch(r"\d{7}", t):
            return f"{1911 + int(t[:3]):04d}-{t[3:5]}-{t[5:]}"
        if _rx.fullmatch(r"\d{8}", t):
            return f"{t[:4]}-{t[4:6]}-{t[6:]}"
        return t

    def _o055_roc(s):                                  # VDF_ENG055_OmniFetch_v0111._roc_to_iso 原實作(逐字)
        t = str(s or "")
        m = _rx.search(r"(\d{2,3})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", t)
        if m:
            return f"{1911 + int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        m = _rx.search(r"(?<!\d)(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})(?!\d)", t)
        if m:
            return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        m = _rx.search(r"(?<!\d)(\d{2,3})/(\d{1,2})/(\d{1,2})(?!\d)", t)
        if m:
            return f"{1911 + int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        m = _rx.search(r"(?<!\d)(20\d{6})(?!\d)", t)
        if m:
            d = m.group(1)
            return f"{d[:4]}-{d[4:6]}-{d[6:]}"
        m = _rx.search(r"(?<!\d)(1[01]\d{5})(?!\d)", t)
        if m:
            d = m.group(1)
            return f"{1911 + int(d[:3])}-{d[3:5]}-{d[5:]}"
        return None

    def _real_iso(x):
        if not isinstance(x, str) or not _rx.fullmatch(r"\d{4}-\d{2}-\d{2}", x[:10]) or len(x) < 10:
            return None
        try:
            return _date.fromisoformat(x[:10]).isoformat()
        except ValueError:
            return None

    _corpus = ["1150824", "1150913", "0991231", "1000101", "20260824", "20260913", "2026-09-12",
               "2026-09-21 19:29:49", "114年09月12日", "114年9月2日", "114/09/12", "115/9/3", "2025/9/12",
               "2025.09.12", "20250912", "1140912", "出表日期:1150913", "資料日期 115/09/23", " 1150824 ",
               "Q3", "CY2026", "26Q4", "2027", "", "abc", "1151301", "1150230", "9990101", "2026-02-30",
               "20261301",
               # v0106 補語料(v0105 的「零差異」沒量到這幾式):八碼 19xx · 民國 ≥200 年 · 八碼年份 <1900 · 帶 T 的 ISO ·
               # TPEX 七字元斜線 115/9/3(舊 L12 內嵌轉法會切成 2026-/9-/3)· None
               "19991231", "20001231", "2150101", "18991231", "01010101", "2026-08-24T00:00:00", "115/9/3", None,
               " Q3 "]   # 認不出的直通值也要去頭尾空白(_iso_date 原文 str(v).strip())
    #: 刻意不同(正本回 None 不猜;舊版照換出一個荒謬年份的日期)——逐式具名,不是漏網
    _deliberate = {"9990101": "舊版 _iso_date 任意七碼照換成 2910-01-01;正本只認民國 0–199 年",
                   "2150101": "民國 215 年=2126;同上",
                   "18991231": "八碼年份 1899;正本八碼只認 1900–2099",
                   "01010101": "八碼年份 101;同上"}
    # 正本=兩份舊版的聯集:① `_iso_date` 認得的有效日期逐一相同 ② 正本認出的每一個日期,都是兩份舊版之一給過的
    #   (不長第三種意見);兩條之外只有具名的刻意不同。v0105 初稿把 ① 寫成「_iso_date 不認的一律 None」——
    #   那是錯的斷言(聯集本來就多認 _roc_to_iso 那幾式),第一次跑就紅,照 LL439 改的是斷言不是函式。
    _diff = [(_x, _real_iso(_o055_iso(_x)), roc_to_iso(_x)) for _x in _corpus
             if _real_iso(_o055_iso(_x)) and roc_to_iso(_x) != _real_iso(_o055_iso(_x)) and _x not in _deliberate]
    _third = [_x for _x in _corpus if roc_to_iso(_x)
              and roc_to_iso(_x) not in (_real_iso(_o055_iso(_x)), _real_iso(_o055_roc(_x)))]
    chk("㉖ roc_to_iso 對 ENG055 v0111 `_iso_date` 語料:它認得的有效日期逐一零差異;正本認出的日期都是兩份舊版之一給過的"
        f"(刻意不同 {len(_deliberate)} 式具名:{' · '.join(_deliberate)};v0106 八碼 19xx 補認)",
        not _diff and not _third and all(roc_to_iso(k) is None for k in _deliberate) and roc_to_iso("19991231") == "1999-12-31",
        f"({len(_corpus)} 式;差 {_diff[:3]} · 第三種 {_third})")
    _diff2 = [(_x, _real_iso(_o055_roc(_x)), roc_to_iso(_x)) for _x in _corpus
              if _real_iso(_o055_roc(_x)) and roc_to_iso(_x) != _real_iso(_o055_roc(_x))]
    _extra = [_x for _x in _corpus if roc_to_iso(_x) and not _real_iso(_o055_roc(_x))]
    chk("㉗ roc_to_iso 對 ENG055 v0111 `_roc_to_iso` 語料:舊版認得的有效日期逐一相同;多認的只有 ISO 帶時間/0 開頭七碼"
        "(v0106:外加另一份舊版 `_iso_date` 認得的同一日期——八碼 19xx;聯集,不是第三種意見)",
        not _diff2 and all(_x in {"2026-09-21 19:29:49", "0991231"} or _real_iso(_o055_iso(_x)) == roc_to_iso(_x) for _x in _extra),
        f"(差 {_diff2[:3]} · 多認 {_extra})")
    # ── v0106 ㉟:roc_to_iso_keep 對 ENG055 `_iso_date` 逐式四類(一式都不准落在四類外)──
    _cls: dict = {"同答": [], "正規化": [], "拒不存在的日期": [], "具名刻意": [], "類外": []}
    for _x in _corpus:
        _old, _new = _o055_iso(_x), roc_to_iso_keep(_x)
        if _new == _old:
            _cls["同答"].append(_x)
        elif _x in _deliberate:
            _cls["具名刻意"].append(_x)
        elif _old == str(_x).strip() and _new == _real_iso(_o055_roc(_x)):
            _cls["正規化"].append(_x)             # 舊 _iso_date 原樣直通、另一份舊版 _roc_to_iso 給過同一個日期(聯集,不長第三種意見)
        elif not _real_iso(_old) and _new == str(_x).strip():
            _cls["拒不存在的日期"].append(_x)      # 舊版照換出 2026-13-01 之類;新版原樣回(不造一個不存在的日期)
        else:
            _cls["類外"].append((_x, _old, _new))
    chk("㉟ roc_to_iso_keep 對 ENG055 `_iso_date`(ENG055 綁定前提):逐式四類——同答 · 正規化(另一份舊版給過的同一日期)· "
        "拒不存在的日期(回原值)· 具名刻意不同;類外 0;ENG055 現役形狀(民國七碼 · 八碼 · ISO)全在同答",
        not _cls["類外"] and {"1150824", "1150913", "20260824", "2026-09-12", " 1150824 "} <= set(_cls["同答"])
        and "115/9/3" in _cls["正規化"] and "1151301" in _cls["拒不存在的日期"],
        "(" + " · ".join(f"{k} {len(v)}" for k, v in _cls.items()) + f";類外 {_cls['類外'][:3]})")
    # ── v0106 ㊱:roc_ym 對 ENG063 `_roc_ym` 原實作逐式零差異;對 ENG055 L10 內嵌在有效輸入上同答 ──

    def _o063_ym(v):                                   # VDF_ENG063_MonthlyRevenue_v0105._roc_ym 原實作(逐字)
        d = "".join(ch for ch in str(v) if ch.isdigit())
        if len(d) not in (5, 6):
            return None
        y, m = int(d[:-2]), int(d[-2:])
        if not (1 <= m <= 12 and 80 <= y <= 200):
            return None
        return f"{y + 1911}{m:02d}"

    def _o055_cbc(ym):                                 # VDF_ENG055_OmniFetch_v0112 L10 CBC 內嵌(逐字;回 'YYYY-MM-01' 或跳過)
        ym = str(ym).strip()
        if not (ym.isdigit() and len(ym) == 5):
            return None
        year, month = 1911 + int(ym[:3]), int(ym[3:])
        return f"{year:04d}-{month:02d}-01"

    _ymc = ["11507", "11508", "11412", "10001", "09912", "115/07", "115年07月", " 11507 ", "202607", "1150",
            "11513", "11500", "00108", "20012", "bad", "", None, 11507, "11508.0"]
    _d63 = [(x, _o063_ym(x), roc_ym(x)) for x in _ymc if _o063_ym(x) != roc_ym(x)]
    #: 刻意不同(具名):民國 80 年(1991)以前——ENG063 原文的範圍;CBC 利率檔實際從民國 90 年起
    #  (ENG073 快照 2026-09-15:tw_rates_cbc 308 列 2001-01-01→2026-08-01),現役資料零影響
    _ym_deliberate = {"00108": "民國 1 年;ENG055 舊內嵌照換 1912-08-01,正典沿 ENG063 範圍 80–200 回 None"}
    _d55 = [(x, _o055_cbc(x), roc_ym(x)) for x in _ymc
            if _o055_cbc(x) and _real_iso(_o055_cbc(x)) and roc_ym(x) != _o055_cbc(x)[:4] + _o055_cbc(x)[5:7]
            and x not in _ym_deliberate]
    _bad55 = sorted(str(x) for x in _ymc if _o055_cbc(x) and not _real_iso(_o055_cbc(x)))
    chk("㊱ roc_ym(民國年月):對 ENG063 `_roc_ym` 原實作逐式零差異;對 ENG055 L10 內嵌在有效輸入上同答"
        "(刻意不同 1 式具名:00108 民國 80 年前);舊內嵌造出不存在日期的式子(11513 · 11500)正典回 None",
        not _d63 and not _d55 and roc_ym("11507") == "202607" and all(roc_ym(x) is None for x in _bad55) and "11513" in _bad55
        and all(roc_ym(k) is None for k in _ym_deliberate),
        f"({len(_ymc)} 式;差 ENG063 {_d63} · 差 ENG055 {_d55} · 舊內嵌造日 {_bad55})")

    with tempfile.TemporaryDirectory() as _pd:
        _book = Path(__file__).resolve().parent / "registry"
        _hits = sorted(_book.glob(PERIOD_RULES_GLOB))
        _r = load_period_rules(_hits[-1]) if _hits else None
        chk("㉘ 期別規則正本在冊(registry/VIA_SSOT_PeriodRules_v*.json)且讀得到;缺席=大聲拋(不回預設值假綠)",
            _r is not None and _raises_base(lambda: load_period_rules(Path(_pd) / "none.json")),
            _hits[-1].name if _hits else "缺")
        if _r is not None:
            _t = _date(2026, 9, 24)
            _a = period_lag("tw_monthly_revenue", "202608", today=_t, rules=_r)
            _b = period_lag("tw_monthly_revenue", "202608", today=_date(2026, 10, 25), rules=_r)
            _c = period_lag("tw_daily_prices", "202608", today=_t, rules=_r)
            chk("㉙ 月營收:202608 在 9/24=PERIOD_DUE 滯後 0(9 月營收 10/10 才到期);10/25 仍是 202608=15 日;"
                "**負控**:同一個值放在日頻表=UNPARSED(不猜成日期)",
                (_a["state"], _a["lag_days"], _a["due"]) == ("PERIOD_DUE", 0, "2026-10-10")
                and _b["lag_days"] == 15 and _c["state"] == "UNPARSED", f"({_a['state']} {_a['lag_days']} · {_b['lag_days']} · {_c['state']})")
            _q = period_lag("tw_financial", "2026-06-30", today=_t, rules=_r)
            _q2 = period_lag("tw_financial", "2026-06-30", today=_date(2026, 11, 20), rules=_r)
            _q4 = period_lag("tw_financial", "2025-12-31", today=_date(2026, 4, 1), rules=_r)
            _q3 = period_lag("tw_financial", "2026-09-30", today=_date(2027, 4, 5), rules=_r)
            # 跨年那一條(Q3 期末 → 下一期是年報,期限在**隔年** 3/31)是突變測試抓出來的漏測:
            #   把 +1y 拿掉,原本四式全綠——這一式補上之後才會紅(LL443:推理說有測到,量測說沒有)
            chk("㉚ 季報:6/30(Q2)在 9/24=滯後 0(Q3 11/14 才到期);11/20 仍 6/30=6 日;年報 12/31 的下一期 Q1 期限 5/15;"
                "9/30(Q3)的下一期是年報,期限跨到隔年 3/31",
                (_q["state"], _q["lag_days"], _q["due"]) == ("PERIOD_DUE", 0, "2026-11-14") and _q2["lag_days"] == 6
                and _q4["due"] == "2026-05-15" and _q4["lag_days"] == 0
                and (_q3["due"], _q3["lag_days"]) == ("2027-03-31", 5),
                f"({_q['due']} · {_q2['lag_days']} · {_q4['due']} · {_q3['due']} {_q3['lag_days']})")
            _f1 = period_lag("tw_chips_daily", "2026-08-25", db="vdf_tw_market_repo_a7752b3d.duckdb", today=_t, rules=_r)
            _f2 = period_lag("local_rest__gl__cross_macro", "2026-08-26", db="vdf_tw_market.duckdb", today=_t, rules=_r)
            _f3 = period_lag("tw_chip_inst", "2026-09-21", db="vdf_tw_market.duckdb", today=_t, rules=_r)
            chk("㉛ 凍結:鏡像庫(_repo_<hash>.duckdb)與 local_rest__ 舊暫存表=FROZEN 不計燈;**負控**:正典主庫 tw_chip_inst 照算 3 日",
                _f1["state"] == "FROZEN" and _f2["state"] == "FROZEN" and (_f3["state"], _f3["lag_days"]) == ("LAG_DAYS", 3),
                f"({_f1['state']} · {_f2['state']} · {_f3['state']} {_f3['lag_days']})")
            _d = [period_lag("x", v, today=_t, rules=_r) for v in ("2026-09-21", "2026-09-21 19:29:49", "1150913")]
            _old = (_t - _date.fromisoformat("2026-09-21")).days
            _lab = [period_lag("factset_earnings", v, today=_t, rules=_r)["state"] for v in ("Q3", "CY2026", "26Q4", "2027")]
            chk("㉜ 日頻零行為變更:ISO 最新日滯後=v0105 之前 ENG093 的算法(3 日);民國七碼也算得到(11 日);"
                "期別標籤=LABEL、空=EMPTY、亂字=UNPARSED",
                [x["lag_days"] for x in _d] == [_old, _old, 11] and _lab == ["LABEL"] * 4
                and period_lag("x", "", today=_t, rules=_r)["state"] == "EMPTY"
                and period_lag("x", "abc", today=_t, rules=_r)["state"] == "UNPARSED", f"({[x['lag_days'] for x in _d]} · {_lab})")
            _as_given = [c for cols in _r["date_columns"]["as_given"].values() for c in cols]
            _dc = date_columns(_r)
            chk("㉝ 日期欄聯集只增不減:兩份 as_given(MDL123 · MDL139)每一欄都在正本裡,且 ym 在(月營收三表靠它)",
                set(_as_given) <= set(_dc) and "ym" in _dc and len(set(_dc)) == len(_dc), f"({len(_dc)} 欄)")
            # ── v0106:補位差集收回正典(普查九份 · 時間戳不補 · 與 MDL123 v0104 同答 · 負控)──
            import copy as _copy
            _cen = _r["date_columns"]["census"]["in_scope"]
            _cover = set(_dc) | set(_r["date_columns"]["record_only"])
            _lost = {k: [c for c in v["cols"] if c.lower() not in _cover] for k, v in _cen.items()}
            _own123 = next(v["cols"] for k, v in _cen.items() if "CGC_MDL123_DataHome" in k)
            _fb123 = fallback_date_columns(_own123, _r)
            _v0104 = tuple(c for c in _dc if c not in _own123)          # MDL123 v0104 _extra_date_cols() 的算法原樣
            _own073 = next(v["cols"] for k, v in _cen.items() if "VDF_ENG073_DataArchitecture" in k)
            _fb073 = fallback_date_columns([c.upper() for c in _own073], _r)   # 大小寫不計
            _fetch_status = ["run_at", "etf_ticker", "status", "source_type", "holding_count", "portfolio_date", "errors"]  # VDF_ENG051 v0103 L2279 建表欄序原樣
            _pick = next((c for c in _fetch_status if c.lower() in _fb073), None)
            _bad = _copy.deepcopy(_r)
            _bad["date_columns"]["corrected"] = list(_bad["date_columns"]["corrected"]) + ["snapshot_at"]
            _bad["date_columns"]["census"]["in_scope"]["x.py:1"] = {"cols": ["date", "bogus_col"]}
            _bad_cover = set(_bad["date_columns"]["corrected"]) | set(_bad["date_columns"]["record_only"])
            _bad_lost = [c for v in _bad["date_columns"]["census"]["in_scope"].values() for c in v["cols"] if c.lower() not in _bad_cover]
            chk("㉞ 補位差集在正典:普查九份每一欄都在 corrected ∪ record_only(遷過來一欄不丟);補位不含寫入時間戳也不含自己那份;"
                "與 MDL123 v0104 自算差集逐欄相同;ENG051 fetch_status 補到 portfolio_date 不是 run_at;"
                "**負控**:冊上多塞假欄 bogus_col 抓得到、把 snapshot_at 塞進 corrected 補位照樣不給",
                len(_cen) == 9 and not any(_lost.values())
                and not (set(_fb073) & set(_r["date_columns"]["record_only"])) and not (set(c.lower() for c in _own073) & set(_fb073))
                and _fb123 == _v0104 and _pick == "portfolio_date"
                and _bad_lost == ["bogus_col"] and "snapshot_at" not in fallback_date_columns(_own073, _bad),
                f"(九份 {len(_cen)} · 丟欄 {sum(len(v) for v in _lost.values())} · ENG073 補位 {len(_fb073)} 欄 · 挑 {_pick} · 負控 {_bad_lost})")
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def _si_probe(catch_all: bool):
    """合成一個「import 時就 sys.exit()」的模組,證明 bare except 會把它吃掉。"""
    import tempfile
    import types
    d = tempfile.mkdtemp()
    name = "zz_boom_mod"
    Path(d, f"{name}.py").write_text("import sys\nsys.exit(3)\n", encoding="utf-8")
    sys.path.insert(0, d)
    sys.modules.pop(name, None)
    try:
        return safe_import(name, catch_all=catch_all)
    finally:
        sys.path.remove(d)
        sys.modules.pop(name, None)
        del types


def _raises_base(fn) -> bool:
    try:
        fn()
        return False
    except BaseException:
        return True


def _eats(fn, exc) -> bool:
    try:
        fn()
        return False
    except exc:
        return True


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print(f"=== VRN 共用小工具正典(SUP_MDL753 v{VERSION})· 自測(零網路;只在沙盒寫)"
              f"—— 檢數由 chk() 現場計,不寫死(寫死的數字會漂,漂了就是假的)===")
        return selftest()
    print(f"SUP_MDL753_VIACommonUtils v{VERSION} — VRN 共用小工具正典")
    print("  safe_import · cel_submit · hash8 · num · argval · nan_safe · bind_jwrite(→SUP_MDL752)")
    print(f"  不得併的:{sorted(NOT_SAME_THING)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
