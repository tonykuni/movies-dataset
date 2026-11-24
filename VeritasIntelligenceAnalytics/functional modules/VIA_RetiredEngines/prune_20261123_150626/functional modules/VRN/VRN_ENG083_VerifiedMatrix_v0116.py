#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VRN_ENG083_VerifiedMatrix v0100 — 驗證矩陣(批569)

操作員令(批569):「VRN 用 `C:\測試樣本報告` 中的檔案實測,**看到顯示且驗證過的輸出用矩陣表示**」。

【矩陣的重點在「驗證過」三個字】
  「有值」不等於「對」。批554/562 燒過我三次:負控為了錯的理由過關、憑直覺挑的詞與實測零重疊。
  所以這張矩陣的每一格**不是「有沒有抓到」,是「抓到而且驗得過」**,而且每一欄的驗法都寫在檔裡、
  跑出來會逐欄印,操作員看得到我用什麼尺量。

【四態(每一格)】
  GREEN   擷到且**驗過**(該欄的驗法回真)
  YELLOW  擷到但**驗不過或驗不了**(有值,尺說不對;或沒有可驗的對照)
  NODATA  沒擷到(空值)——誠實,不是紅燈
  ABSENT  庫裡根本沒這一欄(引擎版本不合)

【批633:工作站 105 份實跑帶回來的三件】
  ① **上漲空間 105 格全 ABSENT,不是缺料,是我把欄名寫錯了。**
     正典表 `vrn_report_basic` 裡叫 `upside_report` / `upside_calc` / `upside_db` /
     `upside_state`——**從來沒有一欄叫 `upside`**。ABSENT 的定義就是「庫裡沒有這一欄」,
     而我先前把它讀成「VDF 價格庫沒料」。整欄 ABSENT 比一格紅更危險:
     它長得像「引擎版本不合」這種誠實態,不像「我打錯字」。
     更根的一層:**自測夾具自己造了一個 schema**(寫 `upside DOUBLE`、`close_price DOUBLE`),
     於是自測一路全綠,量的卻是一個不存在的庫。㊸ 釘欄位鍵、㊾ 釘夾具,兩邊都對回正典表。

  ② **第五盞燈 N/A(不適用)。**105 份裡股票代號 NODATA 48 格,而 ENG073 分出來的
     非個股報告剛好也是 48 份。那 48 格不是「沒擷到」,是「這種報告本來就沒有個股代號」。
     記成 NODATA,等於把一個**永遠補不起來的洞**算進缺料,可判率永遠到不了 100%,
     而看的人會以為那是還沒做完的工。
     N/A 只認 `VRN_MatrixApplicability_SSOT_v0100.json`,引擎不自己判;
     冊裡現在**只有一條**,而且是從 ENG073 自己的分類律推出來的
     (「有代號一律先算個股」⇒ 非個股 = 檔名裡沒有可驗證的代號),不是我的意見。
     其餘寫在 `pending_operator` 等裁定。**冊缺席 = 全部當適用**,不假造 N/A。
     而且:**不知道型別 ≠ 不適用**——`report_kind` 空的一列維持原判,
     寧可留一格誠實的 NODATA(我第一版就踩了這個,被舊夾具抓到)。

  ③ **兩個可判率都印。**N/A 留在分母裡,100% 是按定義做不到的數字;
     悄悄拿掉,比率又會憑空好看。所以全格與扣掉不適用兩個都給,N/A 幾格寫在旁邊。

  另:`VIA_NO_OPEN`(批378 全域零跳出律)與批632「自動跳出」是**兩條令在打架**。
  本器依較新較具體的那一條開頁,但**會把另一條在場這件事印出來**——
  悄悄蓋過一條還在生效的律,下一個人會找不到為什麼會彈窗。

【分頁式舉證頁(批632 操作員令)】
  操作員令:「測試完後自動跳出 HTML U/I 矩陣報告及所有結果及驗證狀態用燈號,字小低點較專業,
  舉證自動調節,給 AI 的詳細舉證放在 TAB 1、有按鍵轉換為 MD / JSON,
  TAB2 之後都結果詳情驗證狀態全部,燈號管理」。

  TAB1  給 AI 的舉證 —— Markdown / JSON 兩顆鍵切換,另有複製、下載。
        兩份都是**伺服端算一次再內嵌**,不是瀏覽器拿資料再算一次;
        各算一次的那一刻起,兩份就會開始各說各話。
        **舉證自動調節**:格數 ≤ 1200 給全量逐格;超過就收斂成只列非 GREEN 的格,
        並把「收斂了什麼、還有幾格沒列」寫進舉證本身——悄悄少給比給少了更糟。
  TAB2  矩陣(原本那一張,字級再降一級)
  TAB3  逐欄燈號(驗法 + 四態燈條 + 綠率)
  TAB4  逐格驗證(一格一列;可依燈號篩)
  TAB5  自我驗證(算式攤開:哪些裁決進分母、判對率與可判率怎麼來的)
  TAB6  燈號冊(這一頁每一個顏色的唯一出處)

【燈號管理】
  `LAMPS`(四盞燈:顏色/中文/意思)與 `VERDICTS`(五個裁決:掛哪盞燈、進不進分母)
  是全樹唯一出處。頁上的 CSS 色、圖例、燈條、篩選器**全部從這兩本長出來**。
  `in_denom` 那一欄是**真的被 `self_verify()` 讀的**,不是說明文字——
  自測 ㊵ 會把它翻一個,分母不跟著變就 FAIL。
  為什麼要這樣釘:批630B 燒過一次,退路悄悄換了一把尺(拿人話詞表量正典鍵),
  四份抽對的被判成黃燈,而**沒有人知道**。尺散在各處,就一定會長出第二把。

【零九頭龍】
  不自己再寫一條擷取鏈。`run` 只是**依序代跑現有正主**:
  VRN_ENG072(首頁三法 `run --in <檔或夾>`)→ VRN_ENG073(結構化入庫 `run --db`),
  然後讀它們落下的庫。要只看矩陣不重跑,用 `matrix --db <庫>`。

【紀律】
  · **零網路**:本器不觸網;代跑時明示 VIA_NET_DISABLED=1。
  · **正本零觸碰**:只讀庫,不改任何報告原件、不改任何引擎。
  · **零寫庫**:連線一律 read_only。沒有 --apply。
  · **零 CDN**:HTML 矩陣頁純本地,不外連。

用法:
  via-vrnmatrix run --in "C:\測試樣本報告" [--db <庫>]   整條鏈實跑後出矩陣
  via-vrnmatrix matrix [--db <庫>]                       只讀既有庫出矩陣(不重跑)
  via-vrnmatrix --selftest
  (批632:HTML **預設就自己跳出來**;要安靜用 `--no-open`。
   舉證深度用 `--evidence full|focus|auto`,預設 auto 自動調節。
   舉證另外落兩支檔:VRN_MATRIX_EVIDENCE.md 與 .json,跟頁上那兩顆鍵是同一份。)
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
import html as _html
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
REPORTS = VIA / "VIA_Reports" / "vrn" / "matrix"
DEFAULT_DB = VIA / "functional modules" / "VRN" / "output" / "vrn_reports.duckdb"


def resolve_db(db: str = "") -> dict:
    """**寫的人跟讀的人要指到同一個檔案。**回 `{path, why, heads}`。

    批655 操作員實機:ENG073 v0131 明明寫出了 `EXACT_MATCH_DB`(畫面上看得到),
    矩陣那一欄卻還是 **GREEN 0 · YELLOW 38 · NODATA 67 —— 跟上一跑一個數字都沒動**。
    根因不在尺(造一個帶 `_DB` 態的庫餵給 matrix,它給 GREEN 30,尺是好的),
    在**兩個人指到不同的檔案**:

      ENG073 `_resolve_db()` → 批490 資料家優先 → `VIA_DB_VDF_TW_MARKET` /
        `VIA_DATA_HOME` 底下的 **vdf_tw_market.duckdb**,`vrn_report_basic` 就寫在那裡
        (他的畫面第一行就印著 `[庫解析] 資料家目錄頁→…vdf_tw_market.duckdb`)
      ENG083 `DEFAULT_DB`   → **寫死** `functional modules/VRN/output/vrn_reports.duckdb`

    兩個都存在、兩個都有 `vrn_report_basic`,所以矩陣不會報錯 ——
    它只是**安靜地讀了一張舊表**。容器看不見這個洞:容器沒有資料家,
    兩條路解出同一個檔案,於是這個分歧從來沒有在這裡出現過。

    本函式**照 ENG073 的次序解**(資料家優先),並且把「另外還有幾個庫也有這張表」
    一起報出來 —— 第二顆頭要被看見,不是被猜(Zero-Hydra)。
    """
    out = {"path": None, "why": "", "heads": []}
    if db:
        out["path"] = Path(db)
        out["why"] = "呼叫端指定(--db)"
        return out
    cands: list[tuple[Path, str]] = []
    env_db = os.environ.get("VIA_DB_VDF_TW_MARKET")
    if env_db and Path(env_db).exists():
        cands.append((Path(env_db), "資料家目錄頁 VIA_DB_VDF_TW_MARKET(與 ENG073 同一條路)"))
    home = os.environ.get("VIA_DATA_HOME")
    if home and Path(home).exists():
        hp = Path(home)
        try:
            hits = ([hp] if (hp.is_file() and hp.name == "vdf_tw_market.duckdb")
                    else sorted(hp.rglob("vdf_tw_market.duckdb")) if hp.is_dir() else [])
            if hits:
                best = max(hits, key=lambda x: x.stat().st_mtime)
                cands.append((best, f"資料家 VIA_DATA_HOME 內最新的一本(共 {len(hits)} 本)"))
        except Exception:                                    # noqa: BLE001
            pass
    # 批657:**ENG073 的舊路徑鏈也要在候選裡。**
    #   批656 我只抄了它「資料家環境變數」那一半,結果容器(沒有環境變數)
    #   的候選裡根本沒有 mega 那一本 —— 而 ENG073 實測就是寫進那一本:
    #     [結構庫] vrn_report_basic 寫入 → …/VDF/output_hub/mega/vdf_tw_market.duckdb
    #   抄一半的解析,跟沒抄一樣;用它同一個常數位置,不要再自己記一份路徑。
    _mega = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
    if _mega.exists():
        cands.append((_mega, "VDF mega 價庫(ENG073 舊路徑鏈的落點;結構表也寫在這裡)"))
    if DEFAULT_DB.exists():
        cands.append((DEFAULT_DB, "VRN 舊路徑 output/vrn_reports.duckdb"))
    # 哪些候選真的有 vrn_report_basic?沒有那張表的不算一顆頭。
    # 批658:**同一個檔案被三條解析路徑重複列成「3 本」**——操作員實機:
    #   VIA_DB_VDF_TW_MARKET / VIA_DATA_HOME / mega 常數三條路解到同一個
    #   `C:\Users\tonyk\VIA System\…\vdf_tw_market.duckdb`,我的表就印「另有 3 本庫」。
    #   真的只有 2 本別的檔案。**第二顆頭的數字自己數錯,比不數還糟**(LL257 檢比到自己)。
    #   用解析後的真實路徑去重,理由合併成一行。
    _seen: dict[str, str] = {}
    _ded: list[tuple[Path, str]] = []
    for _p, _w in cands:
        try:
            _k = str(_p.resolve())
        except Exception:                                    # noqa: BLE001
            _k = str(_p)
        if _k in _seen:
            _seen[_k] += " / " + _w
            continue
        _seen[_k] = _w
        _ded.append((_p, _k))
    cands = [(_p, _seen[_k]) for _p, _k in _ded]
    live: list[dict] = []
    for pth, why in cands:
        try:
            import duckdb
            c = duckdb.connect(str(pth), read_only=True)
            n = c.execute("SELECT count(*) FROM vrn_report_basic").fetchone()[0]
            c.close()
            live.append({"path": str(pth), "why": why, "rows": int(n),
                         "mtime": pth.stat().st_mtime})
        except Exception:                                    # noqa: BLE001
            continue
    if not live:
        out["path"] = DEFAULT_DB
        out["why"] = "沒有任何候選庫有 vrn_report_basic(照舊路徑報缺)"
        return out
    # 批656 修正批655 我自己的次序:**不要靠固定次序猜哪一本才是新的**。
    #   批655 我把「資料家優先」寫死,理由是 ENG073 的 `_resolve_db()` 這樣解;
    #   但那支解的是**價表**(vdf_tw_market.duckdb),結構表落在哪一本要看當時的環境。
    #   固定次序一旦猜錯,就是把矩陣指到一本更舊的表——比原本的問題還糟。
    #   誠實的做法:在「真的有 vrn_report_basic」的候選裡**取最後被寫過的那一本**,
    #   並且把全部候選連同列數與時間一起印出來,讓人一眼看出有沒有第二顆頭。
    live.sort(key=lambda d: d["mtime"], reverse=True)
    out["path"] = Path(live[0]["path"])
    out["why"] = live[0]["why"] + "(候選中**最後被寫過**的一本)"
    out["heads"] = live
    return out




# ── 燈號正典(批632 操作員令「燈號管理」)────────────────────────────────
#   顏色、中文、意思、以及**哪一個裁決掛哪一盞燈**,全樹只有這一處。
#   為什麼要收成一本:批630B 燒過一次——退路 `_load_rating_canon()` 悄悄換了一把尺,
#   拿人話詞表量正典鍵,四份抽對的被判成黃燈(LL209)。尺散在各處,就會有第二把。
#   頁上的 CSS 顏色、圖例、逐欄燈條、逐格篩選器**全部從這裡長出來**,不另寫一份。
LAMPS = {
    "GREEN":  {"zh": "驗過",   "hex": "#1a7f37", "dot": "#2da44e",
               "mean": "擷到而且驗得過(該欄的驗法回真)"},
    "YELLOW": {"zh": "存疑",   "hex": "#9a6700", "dot": "#d4a72c",
               "mean": "擷到但驗不過,或驗不了(沒有可對照的)"},
    "NODATA": {"zh": "沒擷到", "hex": "#57606a", "dot": "#8c959f",
               "mean": "空值——誠實缺料,不是紅燈"},
    "ABSENT": {"zh": "欄缺席", "hex": "#8250df", "dot": "#a475f9",
               "mean": "庫裡根本沒這一欄(引擎版本不合,或**欄名寫錯了**)"},
    # 批633 第五盞。為什麼非有不可:工作站 105 份裡,股票代號 NODATA 48 格
    #   ——而 ENG073 分出來的非個股報告剛好也是 48 份。那 48 格不是「沒擷到」,
    #   是「這種報告本來就沒有個股代號」。記成 NODATA,等於把一個**永遠補不起來的洞**
    #   算進缺料,可判率就永遠到不了 100%,而看的人會以為那是還沒做完的工。
    "NA":     {"zh": "不適用", "hex": "#6e7781", "dot": "#c9d1d9",
               "mean": "這種報告本來就沒有這一欄(依適用性冊,不是引擎判的)"},
}
#   裁決冊。`in_denom` 就是判對率的分母資格——**這一欄是實際被讀的**,
#   不是說明文字:`self_verify()` 從這裡取分母,所以冊改了數字就會跟著改。
#   (寫死 `PASS+FAIL` 而冊上另外寫一句,就是冊與尺各說各話。)
VERDICTS = {
    "PASS":         {"lamp": "GREEN",  "zh": "驗過",                 "in_denom": True},
    "FAIL":         {"lamp": "YELLOW", "zh": "驗不過",               "in_denom": True},
    "UNVERIFIABLE": {"lamp": "YELLOW", "zh": "驗不了(沒有可對照的)", "in_denom": False},
    "NO_VALUE":     {"lamp": "NODATA", "zh": "沒擷到(空值)",        "in_denom": False},
    "NO_COLUMN":    {"lamp": "ABSENT", "zh": "庫裡沒這一欄",          "in_denom": False},
    "NOT_APPLICABLE": {"lamp": "NA", "zh": "不適用(依適用性冊)",     "in_denom": False},
}


APPLICABILITY = (VIA / "supportive modules" / "registry"
                 / "VRN_MatrixApplicability_SSOT_v0100.json")


def _applicability() -> list:
    """讀適用性冊。**冊缺席 = 全部當適用**(退回四態),不假造 N/A。

    為什麼不讓引擎自己判「產業報告沒有代號」:那是領域裁定。
    冊裡現在只有一條,而且是**從 ENG073 自己的分類律推出來的**
    (「有代號一律先算個股」⇒ 非個股 = 檔名裡沒有可驗證的代號),
    不是我的意見。其餘的寫在 `pending_operator` 等裁定(LL90 同族)。
    """
    try:
        d = json.loads(APPLICABILITY.read_text(encoding="utf-8-sig"))
        return list(d.get("rules") or [])
    except Exception:
        return []


def not_applicable(col: str, row: dict, rules: list) -> str:
    """這一格適不適用。回不適用的理由字串;適用回空字串。"""
    for r in rules:
        if r.get("column") != col:
            continue
        w = r.get("not_applicable_when") or {}
        ok = w.get("report_kind_not_in")
        if ok is None:
            continue
        kind = str(row.get("report_kind") or "").strip()
        # **不知道型別 ≠ 不適用。**空的 report_kind(舊庫沒這一欄、或分類器留白)
        #   落進 `not in [...]` 會是 True,於是整欄被判成不適用——
        #   那就是我自己冊上寫的「給多了 N/A 就是把真的缺料藏起來」。
        #   不知道就維持原判,寧可留一格誠實的 NODATA。
        if not kind:
            continue
        if kind not in ok:
            return f"{r['id']}:報告型別「{kind}」不是 {'/'.join(ok)}"
    return ""


def denom_verdicts() -> set:
    """判對率的分母有哪些裁決——**讀冊,不手抄**。"""
    return {k for k, v in VERDICTS.items() if v["in_denom"]}


# ── 每一欄的驗法(寫在這裡,跑出來會逐欄印;看得到我用什麼尺量)──────────────
#   verify(value, row) -> True(驗過) / False(驗不過) / None(驗不了,沒有可對照的)
def _v_ticker(v, row):
    s = str(v or "").strip()
    if not re.fullmatch(r"\d{4,6}[A-Z]?", s):
        return False
    stem = str(row.get("report_file", ""))
    return True if s in stem else None          # 檔名對得上=驗過;對不上=驗不了(不判錯)


def _v_date(v, row):
    s = str(v or "")[:10]
    try:
        d = datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return False
    return d <= datetime.now().date()            # 未來日=錯


#: 批628:券商「權威」詞彙——在**哪本冊**上查到的,不是走哪條路找到的。
#   CANON = 正典冊(VIA_Financial_Institution_SSOT);其餘是 overlay(操作員裁決的增補),
#   有來源但不是正典冊,所以黃燈不是綠燈。
_BROKER_AUTHORITY_GREEN = ("CANON", "SSOT", "冊")


def _v_broker(v, row):
    """券商欄:非空 + 來源標明**出自正典冊** = GREEN;有值沒權威 = YELLOW;空 = NODATA。

    批628 實測:81 份裡 `broker_src` 有 61 份是 `FILENAME_MAP`,券商欄 GREEN 0 · YELLOW 59。
    查下去發現那 61 份**全是正典冊命中**——overlay 在回傳前把 `src="CANON"` 改寫成
    `"FILENAME_MAP"`,把「在哪本冊上查到的」用「走哪條路找到的」蓋掉了。
    所以這裡不是加同義字能解決的,加一千條別名那一欄還是黃的。
    overlay v0102 起 `src` 長成 `FILENAME_MAP+CANON`,兩件事都在字串裡。
    """
    if not str(v or "").strip():
        return False
    src = str(row.get("broker_src", "")).upper()
    return True if any(a in src for a in _BROKER_AUTHORITY_GREEN) else None


def _v_rating(v, row):
    k = str(v or "").strip().upper()
    if not k:
        return False
    return k in RATING_CANON if RATING_CANON else None


def _v_tp(v, row):
    try:
        tp = float(v)
    except Exception:
        return False
    if tp <= 0:
        return False
    try:
        # 正典表裡的現價欄叫 `price`(另有 `price_db`);`close_price` 不是正典欄名,
        # 留在第一順位只是相容別的庫。批633 之前夾具寫的是 close_price,
        # 於是這個 fallback **從來沒有被自測走過**——夾具自己造的欄名擋住了真路。
        px = float(row.get("close_price") or row.get("price") or 0)
    except Exception:
        px = 0.0
    if px <= 0:
        return None                              # 沒有現價可對照=驗不了
    return 0.2 <= (tp / px) <= 5.0               # 目標價/現價落在合理帶=驗過


def _v_upside(v, row):
    st = str(row.get("upside_state", "")).upper()
    if not st:
        return None
    if st in ("EXACT_MATCH_DB", "ROUNDING_ONLY_DB"):
        return True                              # 重算對得上=真驗過
    if st == "FORMULA_MISMATCH_DB":
        return False
    return None                                  # DB_DERIVED:沒有對照,誠實驗不了


def _v_analyst(v, row):
    try:
        return int(row.get("analyst_n") or 0) >= 1
    except Exception:
        return False


COLUMNS = [
    ("ticker",           "股票代號",   _v_ticker,  "四到六碼且與檔名對得上"),
    ("report_date",      "報告日",     _v_date,    "解析得出且不是未來日"),
    ("broker_ssot_key",  "券商",       _v_broker,  "非空且來源標明出自正典冊"),
    # 批630B:驗法那一句要跟**真的用的那把尺**同名。v0107 寫「樞紐 rating_words」,
    #   而 `_load_rating_canon()` 是 rating_keys → rating_canon → rating_words 依序找;
    #   樞紐補上 rating_keys() 之後它其實量的是**鍵**不是詞。冊上寫錯尺的名字,
    #   下一個看矩陣的人就會拿錯的東西去對(這一句由 RATING_SRC 現場填)。
    ("rating_ssot_key",  "評等",       _v_rating,  "落在正典評等鍵(樞紐 {RATING_SRC})"),
    ("target_price",     "目標價",     _v_tp,      "> 0 且 目標價/現價 落在 0.2–5.0"),
    # 批633 工作站實錄:這一欄 **105 格全 ABSENT**,而我先前把它讀成「VDF 價格庫沒料」。
    #   不是。ABSENT 的定義就是**庫裡沒有這一欄**,而正典表 `vrn_report_basic` 裡
    #   叫 `upside_report` / `upside_calc` / `upside_db` / `upside_state`——
    #   **從來沒有一欄叫 `upside`**。我寫了一個不存在的欄名,於是整欄安靜地缺席。
    #   整欄 ABSENT 比一格紅更危險:它長得像「引擎版本不合」這種誠實態,
    #   不像「我打錯字」。㊸ 就是為了這個而立的。
    ("upside_calc",      "上漲空間",   _v_upside,  "upside_state 為 EXACT_MATCH_DB / ROUNDING_ONLY_DB"),
    ("analyst_names",    "分析師",     _v_analyst, "analyst_n ≥ 1"),
]
RATING_CANON: set = set()
RATING_SRC: str = "(未載)"      # 批630B:真的用了哪一把尺,現場填,不寫死


def _load_rating_canon() -> set:
    """向規則樞紐(SUP_MDL749)要正典評等詞彙;樞紐缺=回空集合,該欄一律標「驗不了」。"""
    try:
        import importlib.util
        d = VIA / "supportive modules" / "70_VRN_Rules"
        cands = sorted(d.glob("SUP_MDL749_VRNFieldRuleHub_v*.py"))
        if not cands:
            return set()
        spec = importlib.util.spec_from_file_location("_hub749", cands[-1])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for fn in ("rating_keys", "rating_canon", "rating_words"):
            if hasattr(mod, fn):
                out = getattr(mod, fn)()
                if not out:
                    continue          # 空的不算「有這把尺」,往下一把找
                globals()["RATING_SRC"] = fn
                if isinstance(out, dict):
                    return {str(x).upper() for x in out.values()} | {str(x).upper() for x in out}
                return {str(x).upper() for x in out}
    except Exception:
        return set()
    return set()


# ────────────────────────── 代跑現有正主(零九頭龍) ──────────────────────────
def _newest(pat: str, d: Path):
    c = sorted(d.glob(pat))
    return c[-1] if c else None


def _env():
    e = dict(os.environ)
    e["VIA_NET_DISABLED"] = "1"
    e["PYTHONUTF8"] = "1"
    e["PYTHONIOENCODING"] = "utf-8"
    return e


def _family_python(family: str = "vrn") -> str:
    """批658(L51 家族境律):派**別支引擎**要走匯流排拿家族 python,不是裸 `sys.executable`——
    本器跑在治理境、ENG072/ENG073 跑在 VRN 境,用本行程的 python 去跑它們,缺件時報的是
    「治理境沒有 pdfplumber」這種**判錯的紅燈**(L57)。
    匯流排不在 / 查不到 / 那條 python 不存在 → 退回本行程 python(graceful,零行為變更)。
    全景稽核 CGC_MDL158 的 SYSEXE 條就是抓這個,它自己的 `_bus_python()` 是同一寫法(L30 一個出處)。"""
    try:
        import importlib.util
        cand = sorted((VIA / "supportive modules" / "registry").glob("CGC_MDL148_EngineBus_v*.py"))
        if cand:
            spec = importlib.util.spec_from_file_location("bus_for_eng083", cand[-1])
            mod = importlib.util.module_from_spec(spec)
            sys.modules["bus_for_eng083"] = mod
            spec.loader.exec_module(mod)
            got = mod.python_for(family) or {}
            if got.get("python") and Path(got["python"]).exists():
                return str(got["python"])
    except Exception:
        pass
    return sys.executable


def _call(engine: Path, args: list, timeout: int = 3600) -> dict:
    r = subprocess.run([_family_python(), str(engine), *args], capture_output=True, text=True,
                       timeout=timeout, stdin=subprocess.DEVNULL, cwd=str(engine.parent), env=_env())
    tail = [l for l in (r.stdout + r.stderr).strip().splitlines() if l.strip()]
    # L62:敗了就給全文,不切
    return {"rc": r.returncode, "engine": engine.name,
            "tail": " / ".join(tail[-2:]) if r.returncode == 0 else "\n".join(tail)}


# 批625:誠實四態 → rc 的**唯一對照表**。新增態一定要在這裡登記,
#   否則自測 ㉒ 會當場點名(state 只活在畫面上=下游照 rc 判就會判錯)。
_RC_OF = {"OK": 0, "GREEN": 0, "RED": 1, "FAIL": 1, "NODATA": 2, "ABSENT": 3, "GATED": 4}


def _why_lines(tail: str, n: int = 2) -> str:
    """從一支引擎的輸出裡取**最後 n 行非空**當理由。

    批627b 實跑抓到(我自己在 v0104 造的):NODATA 的步驟 `tail` 是**整份輸出**
    (`_call` 對非 0 rc 不切,L62),我卻用 `[-200:]` 去切它——切到的是
    ENG072 橫幅裡的半句話:「…v0136.py:50);③ 只在 ② **跑了但零字**時才升階」。
    引擎的結論印在**最後**,所以按行取,不要按字元切;按字元切會把結論切成殘句。
    """
    lines = [x.strip() for x in str(tail or "").splitlines() if x.strip()]
    return " / ".join(lines[-n:]) if lines else "(沒有尾訊)"


def run_chain(in_dir: str, db: str = "") -> dict:
    vrn = VIA / "functional modules" / "VRN"
    e72 = _newest("VRN_ENG072_FirstPageText_v*.py", vrn)
    e73 = _newest("VRN_ENG073_ReportStructuredDB_v*.py", vrn)
    if e72 is None or e73 is None:
        return {"state": "ABSENT", "why": f"鏈上引擎缺:ENG072={bool(e72)} ENG073={bool(e73)}"}
    src = Path(in_dir)
    if not src.exists():
        return {"state": "ABSENT", "why": f"報告夾不在:{in_dir}(路徑照你機器上的實際位置給)"}
    # 批624 工作站實錄:`run --in "C:\測試樣本報告"` 印「鏈實跑 · OK」,
    #   接著 `matrix` 卻說「庫不在…先跑 via-vrnmatrix run --in <報告夾>」——**叫他做他剛做完的事**。
    #   拆開看,關節上有兩個洞,而且兩個都讓 OK 變成假的:
    #   (甲) ENG073 的旗標是 `--dir`,v0100 **一個都沒傳**:ENG072 收到了 `--in <他的夾>`,
    #        ENG073 卻去跑**它自己的預設夾**。那句「個股 42 · 產業 10 …」很可能根本不是他的檔。
    #        鏈的後半段看了別的輸入,前半段回 rc=0,於是整條報 OK ——**假綠**。
    #   (乙) 不給 `--db` 時兩邊各用各的預設:本件是
    #        `functional modules/VRN/output/vrn_reports.duckdb`,
    #        ENG073 是 `functional modules/VDF/output_hub/mega/vdf_tw_market.duckdb`。
    #        **兩個完全不同的檔**,所以 ENG073 就算寫了,matrix 也永遠讀不到。
    #   修法:庫在這裡**解析一次**,兩半都吃同一個;夾也明傳。
    dbp = Path(db) if db else DEFAULT_DB
    try:
        dbp.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    # ═══ 批627b:尾訊按行取不按字元切 + `[鏈因]` 穩定標記(實跑抓到)═══════
# ═══ 批627:rc=2 被當成「兩支都 rc=0」吞掉(見下方 run_chain 收尾)═══
# ═══ 批626:我在批624 把一個**對的預設**改成了**錯的明傳** ═══════════
    # 工作站實錄:`ENG073 rc=2 · [入庫] C:\測試樣本報告 無分區 sidecar`。
    # 我批624 看到 ENG073 收不到夾,就補了 `--dir <報告夾>`——**而我從來沒讀過 `--dir` 是什麼**。
    # 讀了才知道:
    #     ENG072  OUTDIR    = VIA_Reports/first_page_text   ← 分區 sidecar 寫這裡
    #     ENG073  ZONES_DIR = VIA_Reports/first_page_text   ← 它的 --dir **預設就是這裡**
    # 兩邊本來就對得上。`--dir` 指的是**分區 sidecar 夾**,不是 PDF 原始夾;
    # 我拿 PDF 夾去覆蓋它,`zdir.glob("*.json")` 當然一個都找不到。
    # **我把一個本來會動的預設,改成一個保證不會動的明傳**(LL180:假設欄位名=沒讀過那個檔)。
    # 所以這裡**不傳 --dir**:讓 ENG073 用它自己的預設。
    # 也不在這裡寫死 `VIA_Reports/first_page_text`——那等於把 ENG073 的知識抄一份過來(零 Hydra)。
    steps = [_call(e72, ["run", "--in", str(src)])]
    steps.append(_call(e73, ["run", "--db", str(dbp)]))
    # ═══ 批627:工作站實錄——`ENG073 rc=2`,而下一行說「兩支都 rc=0」 ═════
    # v0103 的 `bad` 把 rc=2 算成「不壞」(那是對的:NODATA 不是壞),
    # 然後 `if not bad` 那一支就把 rc=2 一起吞了,印出一句**它沒有量過的話**:
    #     VRN_ENG073_ReportStructuredDB_v0129.py rc=2 · [入庫] … 無分區 sidecar
    #     兩支都 rc=0,但庫沒有出現在 …            ← 上一行才剛印 rc=2
    # 兩個後果,第二個比較嚴重:
    #   (一)同一段輸出自相矛盾;
    #   (二)**它把真正的答案蓋掉了**。ENG073 說的是「我沒有料」,
    #        而這句話把人送去找「庫被寫到哪裡了」——去找一個根本沒被寫出來的檔。
    #        工作站就照著找了三輪,換了兩個庫,每一輪都得到同一個 NODATA。
    # 規矩:**狀態要從量到的 rc 長出來,不可以寫死在句子裡**(LL207/LL213 同族)。
    broken = [s for s in steps if s["rc"] not in (0, 2)]
    nodata = [s for s in steps if s["rc"] == 2]
    rcline = " · ".join(f"{s['engine'].split('_v')[0]} rc={s['rc']}" for s in steps)
    out = {"state": "OK" if not broken else "FAIL", "steps": steps, "db": str(dbp),
           "why": "" if not broken else "; ".join(f"{s['engine']} rc={s['rc']}\n{s['tail']}" for s in broken)}
    if not broken and nodata:
        # 鏈上有人誠實說「我沒有料」。那就是答案,不要再往下猜庫在哪
        # ——庫沒被寫出來,不是因為它寫到別的地方去了,是因為**根本沒有東西可寫**。
        out["state"] = "NODATA"
        out["why"] = (f"{rcline}。鏈上有站誠實回報 NODATA(=沒有料),"
                      f"**所以庫不會出現,換一個庫去讀也不會變出資料**。"
                      f"它說的是:"
                      + " | ".join(f"{s['engine']}:{_why_lines(s['tail'])}" for s in nodata))
    elif not broken and not dbp.exists():
        # 每一支都 rc=0(真的量過才這樣說),但庫沒落地。這一種才輪到找庫。
        t73 = next((x["tail"] for x in steps if "ENG073" in x.get("engine", "")), "")
        out["state"] = "NODATA"
        out["why"] = (f"{rcline}(每一支都 rc=0),但庫沒有出現在 {dbp}。"
                      f"**這不是叫你再跑一次**——同一句再跑會得到同一個結果。"
                      f"下一步是看 ENG073 到底把東西寫去哪了:"
                      f"`VRN_ENG073_ReportStructuredDB_v*.py status --db \"{dbp}\"`;"
                      f"它剛才說的是:{_why_lines(t73)}")
    return out


# ────────────────────────── 矩陣 ──────────────────────────
# 批656:**整欄零綠**時,要把那一欄底下的原始值分佈印出來。
#   操作員實機:ENG073 畫面上印著 `[EXACT_MATCH_DB]`(升級碼在 1503 行,
#   INSERT 在 1550 行 —— 升級確實在寫庫之前),而矩陣那一欄仍然 GREEN 0。
#   我批655 猜「兩本庫」,他這一跑的 candidates 讀 output/vrn_reports.duckdb
#   量到券商缺口 9+6=15,與 ENG073 的「券商正典鍵 90/105」完全吻合 ——
#   **矩陣讀的就是這一跑寫的那本庫,我猜錯了。**
#   所以這一次不再隔空猜(LL288):讓下一跑自己把答案印出來。
#   一欄零綠=不是缺料就是尺與值對不上,兩者只要看見**底下的原始值**就分得出來。
ZERO_GREEN_PROBE = {
    "upside_calc":     ("upside_state", "upside_report", "upside_db"),
    "rating_ssot_key": ("rating_raw",),
    "broker_ssot_key": ("broker",),
    "target_price":    ("price", "close_price"),
    "analyst_names":   ("analyst_n",),
}


def zero_green_probe(rows: list, col: str) -> list:
    """那一欄零綠時,它底下的原始值長什麼樣。回 `[(說明, [(值, 次數), …]), …]`。

    **直接從已經抓進記憶體的 rows 數**(不再開庫):那正是判燈用的同一份資料,
    第一版我拿 `con` 去查,而 `con` 在回傳前就 close 了 —— 印出來三行 ConnectionException。
    用同一份資料才不會出現「印的跟判的不是同一批」。
    """
    out = []
    for src in ZERO_GREEN_PROBE.get(col, ()):
        if not rows or src not in rows[0]:
            out.append((f"{src}(這一欄不在本次選取的欄位裡,或庫上沒有)", []))
            continue
        c: dict = {}
        for r in rows:
            v = r.get(src)
            k = "(NULL)" if v is None or v == "" else str(v)[:28]
            c[k] = c.get(k, 0) + 1
        out.append((src, sorted(c.items(), key=lambda kv: -kv[1])[:8]))
    return out


def candidates(db: str = "") -> dict:
    """認不出來的**原字串**,列出來給操作員裁定 —— 我不自己寫進正典(LL90)。

    批654 操作員令:「整合 SSOT REGEX 同義字 邏輯 參數 因子,只增不減去衝突」。
    矩陣量到的缺口裡混著**兩種完全不同的東西**,不分開就沒辦法治:

      **同義字缺口** —— 原字串抓到了,但正典冊查不到那個說法(例:`Reiterate Buy`)
                        → 補一個同義字就會好,而**裁定權在操作員**
      **抽取缺口**   —— 原字串根本沒抓到
                        → 那不是同義字的事,是上游抽取的事;補同義字一點用都沒有

    混在一起數,只會得到一個「評等 NODATA 35」這種沒有下一步的數字(L92)。
    本支唯讀開庫、零寫入、零網路;評等與券商的正典住在
    `VIA_Financial_Institution_SSOT_v0100.py`(READ_ONLY 正典),**本支一個字都不寫**。
    """
    out: dict[str, object] = {"state": "NODATA", "why": "", "db": "",
                              "rating": {"synonym": [], "extract_miss": 0},
                              "broker": {"synonym": [], "extract_miss": 0},
                              "analyst": {"extract_miss": 0, "sample": []}}
    _rd = resolve_db(db)
    p = _rd["path"]
    out["db"] = str(p)
    out["db_why"] = _rd["why"]
    out["db_heads"] = _rd["heads"]
    if not p.exists():
        out["state"] = "ABSENT"
        out["why"] = f"庫不在:{p}(先跑 ENG073)"
        return out
    try:
        import duckdb
    except Exception:
        out["state"] = "ABSENT"
        out["why"] = "本境沒有 duckdb 模組(不代裝;在工作站跑)"
        return out
    con = None
    try:
        con = duckdb.connect(str(p), read_only=True)       # 唯讀:零寫庫
        have = {r[0] for r in con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='vrn_report_basic'").fetchall()}
        if not have:
            out["why"] = "庫在但沒有 vrn_report_basic 表(鏈還沒跑過)"
            return out
        def grp(raw_col: str, key_col: str) -> tuple[list, int]:
            if raw_col not in have or key_col not in have:
                return [], 0
            rows = con.execute(
                f"SELECT COALESCE({raw_col},''), COUNT(*), MIN(report_file) "
                f"FROM vrn_report_basic WHERE COALESCE({key_col},'')='' GROUP BY 1 ORDER BY 2 DESC"
            ).fetchall()
            syn = [{"raw": r[0], "n": int(r[1]), "例": r[2]} for r in rows if str(r[0]).strip()]
            miss = sum(int(r[1]) for r in rows if not str(r[0]).strip())
            return syn, miss
        rs, rm = grp("rating_raw", "rating_ssot_key")
        bs, bm = grp("broker", "broker_ssot_key")
        out["rating"] = {"synonym": rs, "extract_miss": rm}
        out["broker"] = {"synonym": bs, "extract_miss": bm}
        if "analyst_n" in have:
            rows = con.execute(
                "SELECT report_file FROM vrn_report_basic "
                "WHERE COALESCE(analyst_n,0)=0 ORDER BY 1").fetchall()
            out["analyst"] = {"extract_miss": len(rows), "sample": [r[0] for r in rows[:5]]}
        out["state"] = "OK"
        out["why"] = "只列不寫:加字的裁定權在操作員(LL90)"
    except Exception as e:                                   # noqa: BLE001
        out["state"] = "ABSENT"
        out["why"] = f"開庫失敗:{type(e).__name__}: {e}"
    finally:
        if con is not None:
            con.close()
    return out


def matrix(db: str = "") -> dict:
    global RATING_CANON
    _rd = resolve_db(db)
    p = _rd["path"]
    if not p.exists():
        # 批624:修法句不准指回剛剛那一句(L92)。「沒跑過」和「跑過了但庫沒出現」
        #   是兩件事,給同一句話就是把人送回原地繞圈。
        ran = p.parent.exists() and any(p.parent.iterdir()) if p.parent.exists() else False
        why = (f"庫不在:{p}。" + (
            "夾子裡有東西但沒有這個庫——**鏈跑過了,東西沒落在這裡**;"
            f"用 `--db` 指到 ENG073 實際寫的那一個,或看 ENG073 的 status。"
            if ran else
            "這一層還沒跑過:`via-vrnmatrix run --in <報告夾>`(第一次要先有輸入)。"))
        return {"state": "ABSENT", "why": why}
    try:
        import duckdb
    except Exception:
        return {"state": "ABSENT", "why": "本境沒有 duckdb 模組(不代裝;在工作站跑)"}
    RATING_CANON = _load_rating_canon()
    con = None
    try:
        con = duckdb.connect(str(p), read_only=True)       # 唯讀:零寫庫
        have = {r[0] for r in con.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='vrn_report_basic'").fetchall()}
        if not have:
            return {"state": "NODATA", "why": "庫在但沒有 vrn_report_basic 表(鏈還沒跑過)"}
        cols = [c for c, *_ in COLUMNS if c in have]
        # `report_kind` 是批418 就寫進正典表的欄;適用性冊要靠它才判得出「不適用」。
        # 批656:零綠探針要看得到原始值,所以 upside_report / upside_db / rating_raw /
        #   broker 也一起選進來(只增不減:原本那些一個都沒拿掉)。
        #   不選進來的話,探針只能說「這一欄庫裡根本沒有」——那句話會騙人。
        extra = [c for c in ("report_file", "broker_src", "upside_state", "analyst_n",
                             "close_price", "price", "report_kind",
                             "upside_report", "upside_db", "rating_raw", "broker") if c in have]
        sel = ", ".join(f'"{c}"' for c in dict.fromkeys(["report_file"] + cols + extra))
        rows = [dict(zip([d[0] for d in con.description], r))
                for r in con.execute(f"SELECT {sel} FROM vrn_report_basic ORDER BY 1").fetchall()]
    except Exception as exc:
        return {"state": "FAIL", "why": f"{type(exc).__name__}: {exc}"}    # L62:不截斷
    finally:
        if con is not None:
            try:
                con.close()
            except Exception:
                pass
    if not rows:
        return {"state": "NODATA", "why": "vrn_report_basic 零列(鏈跑過但一件都沒入庫)"}

    # 批633:tally 的鍵**從燈號冊長出來**。寫死四個鍵,加第五盞燈的那一天
    #   它就會 KeyError,或更糟——安靜地漏掉一態(LL207 同族)。
    _rules = _applicability()
    cells, tally = [], {k: 0 for k in LAMPS}
    for r in rows:
        line = {"report": str(r.get("report_file", ""))[:60], "cells": {}}
        for key, zh, verify, rule in COLUMNS:
            _na = not_applicable(key, r, _rules)
            if key not in have:
                st = "ABSENT"
                verdict = "NO_COLUMN"
            elif _na:
                # **不適用要贏過空值**:這一格是空的,但它空得理所當然。
                # 先判 NODATA 再判 N/A,就等於把永遠補不起來的洞記成缺料。
                st = "NA"
                verdict = "NOT_APPLICABLE"
            else:
                v = r.get(key)
                # 空=NODATA。用 `is None or == ""`,**不要**用 `in (None,"",0)`——
                # 上漲空間 0.0 是合法值,那樣寫會把它誤判成沒擷到。
                # (第一版我為了閃這個坑給 upside 開特例,結果空的 upside 變 YELLOW,
                #  跟其他欄不一致:沒擷到 ≠ 擷到但錯。改成一條規則管到底。)
                if v is None or (isinstance(v, str) and not v.strip()):
                    st = "NODATA"
                    verdict = "NO_VALUE"
                else:
                    # 批630B:**只驗一次**。v0107 這裡叫了兩次 verify——
                    #   一次決定 state、一次決定 why。同一格量兩遍,
                    #   萬一尺有狀態(或只是慢),兩遍就可能給出不一樣的答案。
                    ok = verify(v, r)
                    st = "GREEN" if ok is True else "YELLOW"
                    verdict = "PASS" if ok is True else ("FAIL" if ok is False else "UNVERIFIABLE")
            # 批630B:**「驗不了」不是「判錯」**。
            #   v0107 把兩者都塞進 YELLOW(state 是正典四態,不動),
            #   但算判對率時它們被混在同一個分母裡——
            #   「沒有價格可對照」是**缺料**,算進判對率等於把 VDF 的帳記到 VRN 頭上,
            #   而且補了料那個比率會自己上升,看起來像「邏輯變準了」(LL225 再一層)。
            #   所以格子多記一個 `verdict`(PASS/FAIL/UNVERIFIABLE),
            #   state 維持四態給下游,判對率改用 verdict 算。只增不減。
            line["cells"][key] = {"state": st, "value": ("" if r.get(key) is None else str(r.get(key))[:40]),
                                  "verdict": verdict,
                                  "why": (_na if st == "NA"
                                          else "" if st in ("GREEN", "NODATA", "ABSENT")
                                          else ("驗不過" if verdict == "FAIL"
                                                else "驗不了(沒有可對照的)"))}
            tally[st] += 1
        cells.append(line)
    n = len(rows)
    # 批630B:驗法句裡的 {RATING_SRC} **現場填**成真的用了哪一把尺
    #   ——寫死一個名字,尺換了句子不會跟著換,那就是冊上寫錯尺的名字。
    per_col = {key: dict({"zh": zh, "rule": rule.replace("{RATING_SRC}", RATING_SRC)},
                         **{L: sum(1 for c in cells if c["cells"][key]["state"] == L)
                            for L in LAMPS})
               for key, zh, _v, rule in COLUMNS}
    # 批656:**整欄零綠**的那些欄,把它底下的原始值分佈一起帶回來。
    #   零綠只有兩種可能:缺料,或尺與值對不上。看一眼原始值就分得出來,
    #   不必再隔著網路來回猜(LL288)。
    zero_green = {}
    for key, zh, _v, _rule in COLUMNS:
        pc = per_col.get(key) or {}
        if pc.get("GREEN", 0) == 0 and (pc.get("YELLOW", 0) + pc.get("NODATA", 0)) > 0:
            try:
                zero_green[key] = {"zh": zh, "probe": zero_green_probe(rows, key)}
            except Exception:                                # noqa: BLE001
                zero_green[key] = {"zh": zh, "probe": []}
    return {"state": "OK", "db": str(p), "db_why": _rd["why"], "db_heads": _rd["heads"],
            "zero_green": zero_green,
            "n_reports": n, "n_cols": len(COLUMNS),
            "applicability_rules": len(_rules),
            "rating_canon_n": len(RATING_CANON),
            "note": ("評等欄的正典詞彙讀不到(樞紐缺)→ 該欄一律標驗不了,不假綠"
                     if not RATING_CANON else ""),
            "tally": tally, "per_col": per_col, "rows": cells}


def matrix_or_empty_rules() -> list:
    """回目前各欄的驗法句(已把 {RATING_SRC} 填掉);不碰庫,給自測用。"""
    return [{"rule": rule.replace("{RATING_SRC}", RATING_SRC)} for _k, _z, _v, rule in COLUMNS]


def self_verify(m: dict) -> dict:
    """頁上的數字**自己對自己**(操作員令「實際產出看結果是否符合自我驗證」)。

    三條都用同一份 rows 現場數出來,不是抄 tally 再印一遍——
    抄一遍只會證明「我抄對了」,證明不了那份 tally 是對的(LL112 分子分母同源)。
    """
    rows, cols = m.get("rows") or [], list(m.get("per_col") or {})
    cells = [r["cells"][k] for r in rows for k in cols if k in r["cells"]]
    live = {}
    for c in cells:
        live[c["state"]] = live.get(c["state"], 0) + 1
    tal = m.get("tally") or {}
    n_expect = len(rows) * len(cols)
    # 批630B:判對率的分母改用 verdict,不用 state。
    #   PASS/FAIL 才是「真的下過判斷」;UNVERIFIABLE(沒有可對照的)與
    #   NO_VALUE/NO_COLUMN 都是缺料,不進分母。
    vd = {}
    for c in cells:
        vd[c.get("verdict", "?")] = vd.get(c.get("verdict", "?"), 0) + 1
    # 批632:分母**讀裁決冊**(`VERDICTS[...]["in_denom"]`),不在這裡手抄一份 PASS+FAIL。
    #   手抄的那一份跟冊上那一句是兩把尺,冊改了尺不會跟著改——LL209 同族。
    _dn = denom_verdicts()
    judged = sum(c for k, c in vd.items() if k in _dn)
    out = {
        "n_cells": len(cells), "n_expect": n_expect,
        "shape_ok": len(cells) == n_expect,
        # 批633:這兩條**掃燈號冊**,不再手抄四個鍵。加第五盞燈的那一天,
        #   手抄的那一份會安靜地把它漏掉——而漏掉的那一態照樣印在畫面上,
        #   於是「四態重數符合」會在少數一態的情況下還是綠的(LL207 同族)。
        "tally_ok": all(live.get(k, 0) == tal.get(k, 0) for k in LAMPS),
        "sum_ok": sum(tal.get(k, 0) for k in LAMPS) == n_expect,
        "live": live,
        # **判對率不是 GREEN÷總格**。NODATA/ABSENT 是缺料,不是判錯;
        # 把缺料算進分母,補料就會「準確率上升」,那是把兩件事混成一個數字。
        "verdicts": vd,
        "hit_rate": (vd.get("PASS", 0) / judged * 100.0) if judged else None,
        "judged": judged,
        "cover_rate": (judged / n_expect * 100.0) if n_expect else None,
    }
    # 批633:**兩個可判率都要印**。N/A 是永遠補不起來的格,把它留在分母裡,
    #   100% 就是一個按定義做不到的數字;但把它悄悄拿掉,比率又會憑空好看起來。
    #   所以兩個都給,而且把 N/A 幾格寫在旁邊——**不許只印好看的那一個**。
    _na = sum(1 for c in cells if c.get("state") == "NA")
    _app = n_expect - _na
    out["n_na"] = _na
    out["n_applicable"] = _app
    out["cover_rate_applicable"] = (judged / _app * 100.0) if _app else None
    out["ok"] = out["shape_ok"] and out["tally_ok"] and out["sum_ok"]
    return out


def _flat_cells(m: dict) -> list:
    """把矩陣攤平成逐格清單:一格一列,帶報告/欄位/燈/裁決/值/理由。"""
    cols = m.get("per_col") or {}
    out = []
    for r in m.get("rows") or []:
        for key, v in cols.items():
            c = (r.get("cells") or {}).get(key)
            if c is None:
                continue
            out.append({"report": r.get("report", ""), "col": key, "zh": v["zh"],
                        "state": c["state"], "verdict": c.get("verdict", "?"),
                        "value": c.get("value", ""), "why": c.get("why", "")})
    return out


#   舉證自動調節的門檻。為什麼是格數不是報告數:448 格的頁人看得完,
#   4000 格的頁**貼給 AI 會先被截斷**,而截斷的是尾巴——尾巴往往正是壞掉的那幾格。
#   所以超過門檻就自己收斂成「只列非 GREEN」,而且**把收斂這件事寫在舉證裡**,
#   讀的人知道他手上這份是全量還是精要。悄悄少給,比給少了更糟。
EV_FULL_MAX = 1200
EV_HARD_MAX = 4000


def evidence(m: dict, mode: str = "auto") -> dict:
    """給 AI 的詳細舉證(批632 操作員令「給AI的詳細舉證放在 TAB 1」)。

    **舉證自動調節**:格數 ≤ EV_FULL_MAX 給全量逐格;超過就只列非 GREEN 的格
    (GREEN 的格用逐欄統計代表),並在 `depth` 裡說清楚收斂了什麼、剩幾格沒列。
    """
    sv = self_verify(m)
    flat = _flat_cells(m)
    n = len(flat)
    use = mode if mode in ("full", "focus") else ("full" if n <= EV_FULL_MAX else "focus")
    listed = flat if use == "full" else [c for c in flat if c["state"] != "GREEN"]
    cut = 0
    if len(listed) > EV_HARD_MAX:
        cut = len(listed) - EV_HARD_MAX
        listed = listed[:EV_HARD_MAX]
    why = ("全部 %d 格逐格列出(未超過 %d 格門檻)" % (n, EV_FULL_MAX) if use == "full"
           else "格數 %d 超過 %d,自動收斂成**只列非 GREEN 的 %d 格**;"
                "GREEN 的格以逐欄統計代表" % (n, EV_FULL_MAX, len(listed) + cut))
    if cut:
        why += "(再截去 %d 格,超過 %d 的硬上限)" % (cut, EV_HARD_MAX)
    gaps = sorted(
        ({"col": k, "zh": v["zh"], "rule": v["rule"],
          # N/A **不算缺口**:它是「這種報告本來就沒有這一欄」,不是還沒做完的工。
        "not_green": sum(v.get(L, 0) for L in LAMPS if L not in ("GREEN", "NA")),
          "YELLOW": v["YELLOW"], "NODATA": v["NODATA"], "ABSENT": v["ABSENT"]}
         for k, v in (m.get("per_col") or {}).items()),
        key=lambda x: -x["not_green"])
    return {
        "engine": "VRN_ENG083_VerifiedMatrix", "version": VERSION,
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "db": m.get("db", ""), "n_reports": m.get("n_reports", 0), "n_cols": m.get("n_cols", 0),
        "rating_src": RATING_SRC, "rating_canon_n": m.get("rating_canon_n", 0),
        "note": m.get("note", ""),
        "lamp_canon": LAMPS, "verdict_canon": VERDICTS,
        "denominator": sorted(denom_verdicts()),
        "applicability": {"rules": _applicability(), "n_na": sv.get("n_na", 0),
                          "book": str(APPLICABILITY.name),
                          "note": "N/A = 這種報告本來就沒有這一欄;不進任何分母,但兩個可判率都印出來"},
        "tally": m.get("tally", {}),
        "self_verify": sv,
        # 批633:逐欄統計**掃燈號冊**。手抄四個燈名,加第五盞的那天它會被悄悄丟掉
        #   ——TAB3 的燈條與綠率分母就會少一塊,而畫面上看不出來(LL207 同族)。
        "columns": [dict({"col": k, "zh": v["zh"], "rule": v["rule"]},
                         **{L: v.get(L, 0) for L in LAMPS})
                    for k, v in (m.get("per_col") or {}).items()],
        "gaps": gaps,
        "depth": {"mode": use, "why": why, "n_cells": n,
                  "n_listed": len(listed), "n_omitted": n - len(listed)},
        "cells": listed,
        "honest_notes": [
            "判對率 = PASS ÷(分母資格的裁決)。分母資格讀 `verdict_canon[*].in_denom`,不手抄。",
            "UNVERIFIABLE(驗不了)是**缺料不是判錯**,不進分母——混進去的話「補料」會假裝成「變準」。",
            "NODATA/ABSENT 同理:那是還沒擷到與庫裡沒這一欄,兩件事都不是判錯。",
            "要 100% 準確,**判對率與可判率兩個數字都得是 100%**;只看判對率會漏掉缺料那一半。",
        ],
    }


def ev_to_json(ev: dict) -> str:
    return json.dumps(ev, ensure_ascii=False, indent=1)


def ev_to_md(ev: dict) -> str:
    """同一份 `ev` 轉 Markdown。**MD 與 JSON 同源**——兩邊各算一次就會各說各話。"""
    sv = ev["self_verify"]
    hit = ("%.1f%%" % sv["hit_rate"]) if sv["hit_rate"] is not None else "—"
    cov = ("%.1f%%" % sv["cover_rate"]) if sv["cover_rate"] is not None else "—"
    L = []
    ap = L.append
    ap("# VRN 驗證矩陣舉證 · %s v%s" % (ev["engine"], ev["version"]))
    ap("")
    ap("- 產生:%s" % ev["generated"])
    ap("- 庫:`%s`" % ev["db"])
    ap("- 規模:%d 份報告 × %d 欄 = %d 格" % (ev["n_reports"], ev["n_cols"], ev["depth"]["n_cells"]))
    ap("- 評等尺:`%s`(正典詞 %d)" % (ev["rating_src"], ev["rating_canon_n"]))
    if ev.get("note"):
        ap("- 註:%s" % ev["note"])
    ap("- 舉證深度:**%s** —— %s" % (ev["depth"]["mode"], ev["depth"]["why"]))
    ap("")
    ap("## 燈號冊")
    ap("")
    ap("| 燈 | 中文 | 意思 |")
    ap("|---|---|---|")
    for k, v in ev["lamp_canon"].items():
        ap("| `%s` | %s | %s |" % (k, v["zh"], v["mean"]))
    ap("")
    ap("## 裁決冊(判對率分母:%s)" % " + ".join("`%s`" % x for x in ev["denominator"]))
    ap("")
    ap("| 裁決 | 掛哪一盞燈 | 中文 | 進分母 |")
    ap("|---|---|---|---|")
    for k, v in ev["verdict_canon"].items():
        ap("| `%s` | `%s` | %s | %s |" % (k, v["lamp"], v["zh"], "是" if v["in_denom"] else "否"))
    ap("")
    ap("## 自我驗證")
    ap("")
    ap("- 一致性:**%s**(形狀 %s · 四態重數 %s · 加總 %s)"
       % ("一致" if sv["ok"] else "對不起來",
          "✓" if sv["shape_ok"] else "✗",
          "✓" if sv["tally_ok"] else "✗",
          "✓" if sv["sum_ok"] else "✗"))
    ap("- 格子:%d / %d" % (sv["n_cells"], sv["n_expect"]))
    ap("- 四態:%s" % " · ".join("%s %d" % (k, ev["tally"].get(k, 0))
                                for k in ev["lamp_canon"]))
    ap("- 裁決:%s" % " · ".join("%s %d" % (k, v) for k, v in sorted(sv["verdicts"].items())))
    ap("- **判對率 %s** = PASS ÷ 分母 = %d / %d"
       % (hit, sv["verdicts"].get("PASS", 0), sv["judged"]))
    ap("- **可判率(全格)%s** = 分母 ÷ 總格 = %d / %d" % (cov, sv["judged"], sv["n_expect"]))
    if sv.get("n_na"):
        _ca = ("%.1f%%" % sv["cover_rate_applicable"]) if sv.get("cover_rate_applicable") is not None else "—"
        ap("- **可判率(扣掉不適用)%s** = %d / %d —— 不適用 %d 格是"
           "「這種報告本來就沒有這一欄」,永遠補不起來;**兩個都印,不許只印好看的那一個**"
           % (_ca, sv["judged"], sv["n_applicable"], sv["n_na"]))
    ap("")
    for t in ev["honest_notes"]:
        ap("> %s" % t)
    ap("")
    ap("## 逐欄")
    ap("")
    _L = list(ev["lamp_canon"])
    ap("| 欄位 | 驗法 | " + " | ".join(_L) + " |")
    ap("|---|---|" + "--:|" * len(_L))
    for c in ev["columns"]:
        ap("| %s (`%s`) | %s | %s |"
           % (c["zh"], c["col"], c["rule"].replace("|", "\\|"),
              " | ".join(str(c.get(L, 0)) for L in _L)))
    ap("")
    ap("## 缺口排序(非 GREEN 由多到少)")
    ap("")
    ap("| 欄位 | 非 GREEN | YELLOW | NODATA | ABSENT |")
    ap("|---|--:|--:|--:|--:|")
    for g in ev["gaps"]:
        ap("| %s | %d | %d | %d | %d |"
           % (g["zh"], g["not_green"], g["YELLOW"], g["NODATA"], g["ABSENT"]))
    ap("")
    ap("## 逐格(%d 列;%s)" % (ev["depth"]["n_listed"], ev["depth"]["why"]))
    ap("")
    ap("| 報告 | 欄位 | 燈 | 裁決 | 值 | 理由 |")
    ap("|---|---|---|---|---|---|")
    for c in ev["cells"]:
        ap("| `%s` | %s | `%s` | `%s` | %s | %s |"
           % (c["report"], c["zh"], c["state"], c["verdict"],
              str(c["value"]).replace("|", "\\|"), c["why"]))
    if ev["depth"]["n_omitted"]:
        ap("")
        ap("> 另有 %d 格未列(自動調節;見「舉證深度」)。" % ev["depth"]["n_omitted"])
    return "\n".join(L) + "\n"


# ── 頁面樣式(零 CDN;批630「字小一點」→ 批632「字小低點較專業」再降一級)────
_CSS = """
*{box-sizing:border-box}
body{font:10.5px/1.45 system-ui,'Microsoft JhengHei','Noto Sans TC',sans-serif;
margin:0;padding:10px 12px;background:#fff;color:#1f2328}
h1{font-size:13px;margin:0 0 4px;font-weight:600;letter-spacing:.2px}
.k{margin:0 0 8px;font-size:9.5px;color:#57606a}
.tabs{display:flex;gap:2px;border-bottom:1px solid #d0d7de;margin:0 0 8px;flex-wrap:wrap}
.tabs button{font:inherit;font-size:10px;padding:4px 10px;border:1px solid transparent;
border-bottom:none;background:none;color:#57606a;cursor:pointer;border-radius:4px 4px 0 0}
.tabs button:hover{background:#f6f8fa;color:#1f2328}
.tabs button[aria-selected=true]{background:#fff;border-color:#d0d7de;color:#0969da;
font-weight:600;margin-bottom:-1px}
.pane[hidden]{display:none}
.bar{display:flex;gap:6px;align-items:center;margin:0 0 6px;flex-wrap:wrap}
.bar button{font:inherit;font-size:10px;padding:3px 9px;border:1px solid #d0d7de;
background:#f6f8fa;border-radius:4px;cursor:pointer;color:#1f2328}
.bar button:hover{background:#eef1f4}
.bar button[aria-pressed=true]{background:#0969da;border-color:#0969da;color:#fff;font-weight:600}
.st{font-size:9.5px;color:#57606a;margin-left:4px}
pre.ev{margin:0;padding:8px 10px;border:1px solid #d0d7de;border-radius:4px;background:#f6f8fa;
font:10px/1.5 ui-monospace,'Cascadia Mono',Consolas,monospace;white-space:pre-wrap;
word-break:break-word;overflow:auto;max-height:calc(100vh - 150px)}
.wrap{overflow:auto;max-height:calc(100vh - 150px);border:1px solid #d0d7de;border-radius:4px}
table{border-collapse:separate;border-spacing:0;table-layout:auto;width:max-content;min-width:100%}
th,td{border-right:1px solid #d0d7de;border-bottom:1px solid #d0d7de;padding:3px 6px;
vertical-align:top;word-break:break-word;overflow-wrap:anywhere;max-width:280px}
th{background:#f6f8fa;text-align:left;position:sticky;top:0;z-index:3;font-size:10px;font-weight:600}
td:first-child,th:first-child{position:sticky;left:0;background:#fff;z-index:2;max-width:320px}
th:first-child{z-index:4;background:#f6f8fa}
tr:nth-child(even) td{background:#fbfcfd}
.r{font-size:9px;color:#57606a;font-weight:400;line-height:1.35}
.v{font-size:9.5px;color:#1f2328}
.f{font-family:ui-monospace,monospace;font-size:9.5px}
.sv{margin:0 0 8px;padding:6px 9px;border:1px solid #d0d7de;border-radius:4px;
background:#f6f8fa;font-size:10px}
.dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:4px;
vertical-align:middle}
.lb{display:inline-block;min-width:1px;height:8px;border-radius:2px;vertical-align:middle}
.lg{display:flex;gap:10px;flex-wrap:wrap;font-size:9.5px;color:#424a53;margin:0 0 8px}
td.n{text-align:right;font-variant-numeric:tabular-nums}
"""

_JS = """
function tab(i){document.querySelectorAll('.pane').forEach(function(p,j){p.hidden=(j!==i)});
document.querySelectorAll('.tabs button').forEach(function(b,j){
b.setAttribute('aria-selected',j===i?'true':'false')});}
function st(t){var s=document.getElementById('st');if(s){s.textContent=t;}}
function ev(k){['md','js'].forEach(function(x){
document.getElementById('ev-'+x).hidden=(x!==k);});
document.querySelectorAll('#evbar button[data-k]').forEach(function(b){
b.setAttribute('aria-pressed',b.dataset.k===k?'true':'false')});
st('目前顯示 '+(k==='md'?'Markdown':'JSON')+' · '+
document.getElementById('ev-'+k).textContent.length+' 字');}
function dl(k){var t=document.getElementById('ev-'+k).textContent;
var b=new Blob([t],{type:k==='md'?'text/markdown':'application/json'});
var a=document.createElement('a');a.href=URL.createObjectURL(b);
a.download='VRN_MATRIX_EVIDENCE.'+(k==='md'?'md':'json');a.click();
setTimeout(function(){URL.revokeObjectURL(a.href)},4000);st('已下載 '+a.download);}
function cp(k){var t=document.getElementById('ev-'+k).textContent;
if(navigator.clipboard){navigator.clipboard.writeText(t).then(
function(){st('已複製 '+t.length+' 字到剪貼簿')},
function(){st('瀏覽器擋下剪貼簿,請在框裡手動全選複製')});}
else{st('這個瀏覽器沒有剪貼簿介面,請手動全選複製')}}
function flt(s){var rows=document.querySelectorAll('#cellrows tr');var n=0;
rows.forEach(function(r){var on=(s==='ALL'||r.dataset.s===s);r.hidden=!on;if(on)n++;});
document.querySelectorAll('#fbar button').forEach(function(b){
b.setAttribute('aria-pressed',b.dataset.s===s?'true':'false')});
st('逐格:顯示 '+n+' 列'+(s==='ALL'?'(全部)':'(燈號 '+s+')'));}
"""


def _lampbar(v: dict, total: int) -> str:
    """一欄的燈條:四態按比例排。顏色**從燈號冊取**,不在這裡再寫一次色碼。"""
    if not total:
        return ""
    seg = ""
    for k, L in LAMPS.items():
        n = v.get(k, 0)
        if n:
            seg += ("<span class='lb' title='%s %d' style='width:%.2f%%;background:%s'></span>"
                    % (k, n, n * 100.0 / total, L["dot"]))
    return seg


def to_html(m: dict) -> str:
    """分頁式舉證頁(批632 操作員令)。

    TAB1 給 AI 的詳細舉證(可切 MD / JSON、可複製、可下載;**舉證自動調節**)
    TAB2 之後:矩陣 · 逐欄燈號 · 逐格驗證(可依燈號篩)· 自我驗證 · 燈號冊
    零 CDN、零彈窗(狀態寫在頁上那一行,不用 alert)、字級再降一級。
    """
    e = _html.escape
    ev = evidence(m)
    sv = ev["self_verify"]
    md_txt, js_txt = ev_to_md(ev), ev_to_json(ev)
    colr = {k: v["hex"] for k, v in LAMPS.items()}
    t = m["tally"]
    total = sum(t.get(k, 0) for k in LAMPS)
    _hit = ("%.1f%%" % sv["hit_rate"]) if sv["hit_rate"] is not None else "—"
    _cov = ("%.1f%%" % sv["cover_rate"]) if sv["cover_rate"] is not None else "—"
    _svc = "#1a7f37" if sv["ok"] else "#cf222e"

    legend = "".join(
        "<span><span class='dot' style='background:%s'></span>%s <b>%s</b> %d</span>"
        % (v["dot"], k, v["zh"], t.get(k, 0)) for k, v in LAMPS.items())

    # ── TAB1:給 AI 的舉證 ──────────────────────────────────────────────
    p1 = ("<div class='bar' id='evbar'>"
          "<button data-k='md' aria-pressed='true' onclick=\"ev('md')\">Markdown</button>"
          "<button data-k='js' aria-pressed='false' onclick=\"ev('js')\">JSON</button>"
          "<button onclick=\"cp(document.getElementById('ev-md').hidden?'js':'md')\">複製</button>"
          "<button onclick=\"dl(document.getElementById('ev-md').hidden?'js':'md')\">下載</button>"
          "<span class='st' id='st'>舉證深度 <b>%s</b> · %s</span></div>"
          "<pre class='ev' id='ev-md'>%s</pre>"
          "<pre class='ev' id='ev-js' hidden>%s</pre>"
          % (e(ev["depth"]["mode"]), e(ev["depth"]["why"]), e(md_txt), e(js_txt)))

    # ── TAB2:矩陣 ─────────────────────────────────────────────────────
    head = "".join("<th>%s<div class='r'>%s</div></th>" % (e(v["zh"]), e(v["rule"]))
                   for v in m["per_col"].values())
    body = ""
    for r in m["rows"]:
        tds = ""
        for key in m["per_col"]:
            c = r["cells"][key]
            tds += ("<td style='color:%s'><b>%s</b><div class='v'>%s</div>%s</td>"
                    % (colr[c["state"]], c["state"], e(c["value"]),
                       ("<div class='r'>%s</div>" % e(c["why"])) if c["why"] else ""))
        body += "<tr><td class='f'>%s</td>%s</tr>" % (e(r["report"]), tds)
    p2 = ("<div class='lg'>%s</div><div class='wrap'><table>"
          "<tr><th>報告</th>%s</tr>%s</table></div>" % (legend, head, body))

    # ── TAB3:逐欄燈號 ─────────────────────────────────────────────────
    rows3 = ""
    for c in ev["columns"]:
        n = sum(c.get(L, 0) for L in LAMPS)
        # 燈的欄位數**跟著燈號冊走**,不寫死四個 `%d`(寫死的那天加第五盞,
        #   它就會從畫面上消失,而表格看起來完全正常)。
        _cells = "".join("<td class='n' style='color:%s'>%d</td>"
                         % (colr[L], c.get(L, 0)) for L in LAMPS)
        # 綠率的分母**扣掉不適用**:一個產業報告沒有代號,不該讓那一欄的綠率變難看。
        _den = n - c.get("NA", 0)
        rows3 += ("<tr><td><b>%s</b><div class='r'>%s</div></td><td class='r'>%s</td>"
                  "<td style='min-width:130px'>%s</td>%s<td class='n'>%s</td></tr>"
                  % (e(c["zh"]), e(c["col"]), e(c["rule"]), _lampbar(c, n), _cells,
                     ("%.1f%%" % (c.get("GREEN", 0) * 100.0 / _den)) if _den else "—"))
    p3 = ("<div class='wrap'><table><tr><th>欄位</th><th>驗法(用的是哪一把尺)</th>"
          "<th>燈條</th>%s<th>綠率<div class='r'>分母扣掉不適用</div></th></tr>%s</table></div>"
          % ("".join("<th>%s</th>" % L for L in LAMPS), rows3))

    # ── TAB4:逐格驗證(依燈號篩)────────────────────────────────────────
    fb = "<button data-s='ALL' aria-pressed='true' onclick=\"flt('ALL')\">全部 %d</button>" % total
    for k, v in LAMPS.items():
        fb += ("<button data-s='%s' aria-pressed='false' onclick=\"flt('%s')\">"
               "<span class='dot' style='background:%s'></span>%s %d</button>"
               % (k, k, v["dot"], k, t.get(k, 0)))
    rows4 = ""
    for c in _flat_cells(m):
        vv = VERDICTS.get(c["verdict"], {})
        rows4 += ("<tr data-s='%s'><td class='f'>%s</td><td>%s</td>"
                  "<td style='color:%s'><span class='dot' style='background:%s'></span><b>%s</b></td>"
                  "<td class='r'>%s<div class='r'>%s</div></td>"
                  "<td class='v'>%s</td><td class='r'>%s</td></tr>"
                  % (c["state"], e(c["report"]), e(c["zh"]),
                     colr[c["state"]], LAMPS[c["state"]]["dot"], c["state"],
                     e(c["verdict"]), e(vv.get("zh", "")),
                     e(c["value"]), e(c["why"])))
    p4 = ("<div class='bar' id='fbar'>%s</div><div class='wrap'><table>"
          "<tr><th>報告</th><th>欄位</th><th>燈</th><th>裁決</th><th>值</th><th>理由</th></tr>"
          "<tbody id='cellrows'>%s</tbody></table></div>" % (fb, rows4))

    # ── TAB5:自我驗證(算式攤開)───────────────────────────────────────
    vd = "".join("<tr><td><code>%s</code></td><td>%s</td><td>%s</td><td class='n'>%d</td>"
                 "<td>%s</td></tr>"
                 % (k, VERDICTS.get(k, {}).get("lamp", "?"), e(VERDICTS.get(k, {}).get("zh", "")),
                    sv["verdicts"].get(k, 0),
                    "<b>進分母</b>" if VERDICTS.get(k, {}).get("in_denom") else "不進分母(缺料)")
                 for k in VERDICTS)
    p5 = ("<div class='sv'><b style='color:%s'>自我驗證 %s</b> · 格子 %d/%d(形狀%s)· "
          "四態逐格重數與抬頭%s · 加總%s</div>"
          "<div class='wrap'><table><tr><th>裁決</th><th>燈</th><th>中文</th><th>格數</th>"
          "<th>分母資格</th></tr>%s</table></div>"
          "<div class='sv'><b>判對率 %s</b> = PASS ÷ 分母 = %d / %d<br>"
          "<b>可判率(全格)%s</b> = 分母 ÷ 總格 = %d / %d%s<br>%s</div>"
          % (_svc, "一致" if sv["ok"] else "**對不起來**", sv["n_cells"], sv["n_expect"],
             "✓" if sv["shape_ok"] else "✗", "一致 ✓" if sv["tally_ok"] else "**不一致 ✗**",
             "✓" if sv["sum_ok"] else "✗", vd,
             _hit, sv["verdicts"].get("PASS", 0), sv["judged"],
             _cov, sv["judged"], sv["n_expect"],
             ("<br><b>可判率(扣掉不適用)%.1f%%</b> = %d / %d —— 不適用 %d 格是"
              "「這種報告本來就沒有這一欄」,永遠補不起來;<b>兩個都印</b>"
              % (sv["cover_rate_applicable"], sv["judged"], sv["n_applicable"], sv["n_na"])
              if sv.get("n_na") and sv.get("cover_rate_applicable") is not None else ""),
             "<br>".join(e(x) for x in ev["honest_notes"])))

    # ── TAB6:燈號冊(這一頁所有顏色的唯一出處)──────────────────────────
    lr = "".join("<tr><td><span class='dot' style='background:%s'></span><b style='color:%s'>%s</b></td>"
                 "<td>%s</td><td>%s</td><td class='n'>%d</td><td class='n'>%s</td>"
                 "<td class='r'>%s</td></tr>"
                 % (v["dot"], v["hex"], k, e(v["zh"]), e(v["mean"]), t.get(k, 0),
                    ("%.1f%%" % (t.get(k, 0) * 100.0 / total)) if total else "—",
                    " · ".join("<code>%s</code>" % q for q, w in VERDICTS.items()
                               if w["lamp"] == k))
                 for k, v in LAMPS.items())
    p6 = ("<div class='sv'>這一頁的每一個顏色、每一個燈名、每一條「哪個裁決掛哪盞燈」"
          "都從引擎裡的 <code>LAMPS</code> / <code>VERDICTS</code> 長出來,"
          "<b>頁上不另寫第二份色碼</b>。批630B 燒過一次:退路悄悄換了一把尺,"
          "四份抽對的被判成黃燈——尺散在各處就一定會有第二把。</div>"
          "<div class='wrap'><table><tr><th>燈</th><th>中文</th><th>意思</th><th>格數</th>"
          "<th>占比</th><th>掛在這盞燈的裁決</th></tr>%s</table></div>"
          "<div class='sv'>判對率的分母資格寫在裁決冊的 <code>in_denom</code> 欄,"
          "<b>而且是真的被讀的那一欄</b>(<code>self_verify()</code> 從冊取分母,"
          "不在程式裡手抄一份 PASS+FAIL)。冊改了,數字就跟著改。</div>" % lr)

    names = ["① 給 AI 的舉證", "② 矩陣", "③ 逐欄燈號", "④ 逐格驗證", "⑤ 自我驗證", "⑥ 燈號冊"]
    tabs = "".join("<button aria-selected='%s' onclick='tab(%d)'>%s</button>"
                   % ("true" if i == 0 else "false", i, nm) for i, nm in enumerate(names))
    panes = "".join("<div class='pane'%s>%s</div>" % ("" if i == 0 else " hidden", pp)
                    for i, pp in enumerate([p1, p2, p3, p4, p5, p6]))
    return ("<!doctype html><html lang='zh-Hant'><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>VRN 驗證矩陣</title><style>%s</style>"
            "<h1>VRN 驗證矩陣 · %d 份報告 × %d 欄 · 判對率 <span style='color:%s'>%s</span>"
            " · 可判率 %s</h1>"
            "<div class='k'>庫 %s · 產生 %s · 評等尺 %s%s</div>"
            "<div class='tabs'>%s</div>%s<script>%s</script></html>"
            % (_CSS, m["n_reports"], m["n_cols"], _svc, _hit, _cov,
               e(m["db"]), datetime.now().strftime("%Y-%m-%d %H:%M"), e(RATING_SRC),
               ("<br>" + e(m["note"])) if m.get("note") else "",
               tabs, panes, _JS))


def open_page(p: Path) -> str:
    """把頁**自動跳出來**(操作員令)。開不起來就誠實說,不假裝開了。

    不是彈窗:是把產好的本地檔交給作業系統開。無頭環境(容器/SSH)本來就沒得開,
    那要講出來——「我開了」而其實沒開,比沒開更糟。
    """
    import os
    import shutil as _sh
    import subprocess as _sp
    try:
        if os.name == "nt":
            os.startfile(str(p))          # noqa: S606  Windows 正路
            return f"已開:{p}"
        if sys.platform == "darwin":
            _sp.Popen(["open", str(p)], stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
            return f"已開:{p}"
        if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
            return f"無頭環境(沒有 DISPLAY)開不了瀏覽器,頁在:{p}"
        if not _sh.which("xdg-open"):
            return f"沒有 xdg-open,頁在:{p}"
        _sp.Popen(["xdg-open", str(p)], stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
        return f"已開:{p}"
    except Exception as exc:
        return f"開不起來({type(exc).__name__}),頁在:{p}"


def write_out(name: str, payload) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    p = REPORTS / name
    p.write_text(payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, indent=1),
                 encoding="utf-8")
    return p


# ────────────────────────── 自測 ──────────────────────────
def selftest() -> int:
    import tempfile
    n, fails = [0], []

    def chk(name, ok, note=""):
        n[0] += 1
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" ({note})" if note else ""))

    print(f"=== VRN_ENG083 驗證矩陣 v{VERSION} · 自測(零網路;零寫庫) ===")
    code = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]
    chk("① 零網路(不 import requests/httpx/urllib)",
        not any(k in code for k in ("import requests", "import httpx", "import urllib")))
    chk("② 零寫庫(read_only;無 CREATE/INSERT/UPDATE/DELETE)",
        "read_only=True" in code and not re.search(r"\b(CREATE|INSERT|UPDATE|DELETE)\s+TABLE", code))
    chk("③ 沒有 --apply(只讀只報)", '"--apply"' not in code and "'--apply'" not in code)
    chk("④ 零九頭龍:run 只代跑 ENG072/ENG073,不自己寫擷取",
        "VRN_ENG072_FirstPageText_v*.py" in code and "VRN_ENG073_ReportStructuredDB_v*.py" in code)
    chk("⑤ 零 CDN(頁不外連)", "<script src" not in code and "http://" not in to_html(
        {"per_col": {}, "rows": [], "tally": {"GREEN": 0, "YELLOW": 0, "NODATA": 0, "ABSENT": 0},
         "n_reports": 0, "n_cols": 0, "db": "x"}))
    chk("⑥ 每一欄都寫得出驗法(操作員看得到我用什麼尺量)",
        all(isinstance(rule, str) and len(rule) >= 6 for *_x, rule in COLUMNS), f"{len(COLUMNS)} 欄")
    chk("⑦ 庫不在=誠實 ABSENT 且講得出下一句",
        matrix(str(Path(tempfile.gettempdir()) / "no_such_db.duckdb"))["state"] == "ABSENT")

    # 合成庫:四態各一列,尺要分得開
    try:
        import duckdb
        with tempfile.TemporaryDirectory() as td:
            dbp = Path(td) / "m.duckdb"
            con = duckdb.connect(str(dbp))
            con.execute("""CREATE TABLE vrn_report_basic(
                report_file VARCHAR, ticker VARCHAR, report_date VARCHAR, broker_ssot_key VARCHAR,
                broker_src VARCHAR, rating_ssot_key VARCHAR, target_price DOUBLE, price DOUBLE,
                upside_calc DOUBLE, upside_state VARCHAR, analyst_names VARCHAR, analyst_n INTEGER,
                report_kind VARCHAR)""")
            # 批633:這個夾具原本寫 `upside DOUBLE`——**正典表裡從來沒有這一欄**。
            #   我自己造了一個 schema,於是自測永遠綠,而真庫裡那一欄叫 `upside_calc`。
            #   夾具不跟正典同源,量的就是一個不存在的庫(㊾ 現在釘這件事)。
            con.execute("""INSERT INTO vrn_report_basic VALUES
                ('2330_2026.pdf','2330','2026-09-01','FUBON','SSOT','BUY',900.0,600.0,0.5,'EXACT_MATCH_DB','王小明',1,'個股'),
                ('9999_x.pdf','9999','2099-01-01','','GUESS','NOTARATING',1.0,600.0,0.5,'FORMULA_MISMATCH_DB','',0,'個股'),
                ('empty.pdf',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL),
                ('產業_半導體.pdf',NULL,'2026-09-01','FUBON','SSOT','BUY',900.0,600.0,0.5,'EXACT_MATCH_DB','張三',1,'產業')""")
            con.close()
            m = matrix(str(dbp))
            chk("⑧ 矩陣讀得出四列", m["state"] == "OK" and m["n_reports"] == 4, f"{m.get('n_reports')} 列")
            g = {r["report"]: r["cells"] for r in m["rows"]}
            good = g["2330_2026.pdf"]
            chk("⑨ 好件:代號/報告日/券商/目標價/上漲空間/分析師 六欄 GREEN(每一欄都是被尺量過才綠)",
                all(good[k]["state"] == "GREEN" for k in
                    ("ticker", "report_date", "broker_ssot_key", "target_price", "upside_calc", "analyst_names")),
                str({k: good[k]["state"] for k in good}))
            bad = g["9999_x.pdf"]
            chk("⑩ 壞件:未來日 / 券商空 / 目標價比失真 / 重算對不上 —— 一律 YELLOW,不冒充 GREEN",
                bad["report_date"]["state"] == "YELLOW" and bad["target_price"]["state"] == "YELLOW"
                and bad["upside_calc"]["state"] == "YELLOW" and bad["broker_ssot_key"]["state"] == "NODATA",
                str({k: bad[k]["state"] for k in ("report_date", "target_price", "upside_calc", "broker_ssot_key")}))
            emp = g["empty.pdf"]
            chk("⑪ 空件:七欄**全部** NODATA,不冒充 YELLOW(沒擷到 ≠ 擷到但錯)",
                all(emp[k]["state"] == "NODATA" for k, *_ in COLUMNS),
                str({k: emp[k]["state"] for k in emp}))
            chk("⑫ 驗不過與驗不了的理由分得開(不是都寫『壞掉』)",
                bad["report_date"]["why"] == "驗不過"
                and any(c["cells"]["rating_ssot_key"]["why"] in ("驗不過", "驗不了(沒有可對照的)")
                        for c in m["rows"]),
                f"報告日「{bad['report_date']['why']}」")
            chk("⑬ 逐欄統計**各態**加起來等於列數(分子分母數同一件事;LL112。"
                "批633 起掃燈號冊,不手抄燈名——第五盞燈加進來那天,手抄的那份會少數一態)",
                all(sum(v[L] for L in LAMPS) == m["n_reports"] for v in m["per_col"].values()))
            # 批633:真庫上跑一次第五態,不是只在假 dict 上驗。
            ind = g["產業_半導體.pdf"]
            chk("⑭b 真庫上的第五態:產業報告的股票代號 = **NA 不適用**"
                "(它不是沒擷到,是這種報告本來就沒有個股代號);"
                "而 report_kind 空的那一列**維持 NODATA**——不知道型別不可以當不適用",
                ind["ticker"]["state"] == "NA"
                and ind["ticker"]["verdict"] == "NOT_APPLICABLE"
                and "NA-01" in ind["ticker"]["why"]
                and emp["ticker"]["state"] == "NODATA"
                and ind["target_price"]["state"] == "GREEN",
                f"(產業 ticker={ind['ticker']['state']} · 空 kind ticker={emp['ticker']['state']})")
            con2 = duckdb.connect(str(dbp))
            con2.execute("INSERT INTO vrn_report_basic VALUES "
                         "('zero.pdf','1101','2026-09-01','FUBON','SSOT','HOLD',600.0,600.0,"
                         "0.0,'EXACT_MATCH_DB','李四',1,'個股')")
            con2.close()
            mz = matrix(str(dbp))
            zc = {r["report"]: r["cells"] for r in mz["rows"]}["zero.pdf"]
            chk("⑯ 上漲空間 0.0 是合法值,不准被當成沒擷到(第一版的 `in (None,\"\",0)` 就是這個坑)",
                zc["upside_calc"]["state"] == "GREEN", f"upside={zc['upside_calc']['state']} 值 {zc['upside_calc']['value']}")
            before = dbp.stat().st_mtime
            matrix(str(dbp))
            chk("⑰ 唯讀:跑完庫檔 mtime 不變(比 bytes,不看旗標)", dbp.stat().st_mtime == before)
            h = to_html(m)
            p = write_out("VRN_MATRIX_selftest.html", h)
            chk("⑱ HTML 矩陣頁產得出、零 CDN、三列都在",
                p.exists() and "<script src" not in h and "2330_2026.pdf" in h and "empty.pdf" in h,
                f"{len(h)//1024} KB")
            try:
                p.unlink()
            except Exception:
                pass
    except ImportError:
        for i, nm in ((8, "矩陣"), (9, "好件"), (10, "壞件"), (11, "空件"), (12, "理由"),
                      (13, "統計"), (14, "唯讀"), (15, "HTML")):
            chk(f"⑧–⑮ {nm}:本境沒有 duckdb=誠實跳過(不代裝、不假綠)", True, "duckdb 缺席")
            break

    r = run_chain("Z:/沒有這個夾")
    chk("⑲ 報告夾不在=誠實 ABSENT 且把路徑講出來", r["state"] == "ABSENT" and "沒有這個夾" in r["why"])
    # ═══ 批627 補兩檢:狀態要從量到的 rc 長出來 ═════════════════════════
    _src27 = Path(__file__).read_text(encoding="utf-8")
    _seg27 = _src27[_src27.index("def run_chain"):_src27.index("# ───", _src27.index("def run_chain"))]
    # 自審(第一版就紅):`"兩支都 rc=0" not in _seg27` 抓到的是**我自己寫在上面那段註解裡
    # 引用的那句話**。源碼掃描的檢分不出註解和程式碼,就會對著自己的說明文字報紅
    # ——跟 LL212 是同一族(工具讀自己的原始碼,要先把不算數的那部分拿掉)。
    # 所以先用 tokenize 把 COMMENT 去掉再掃;字串字面量留著,因為那句話真的出現過在字串裡。
    def _nocomment(src: str) -> str:
        """只把 COMMENT 挖掉,**版面原樣保留**。

        自審之二:第一版用 `"\n".join(tok.string)` 重組,token 之間全塞進換行,
        `nodata:` 被拆成 `nodata` 和 `:` 兩行,底下那個 `.index("nodata:")` 當場 ValueError。
        去註解不等於重排版——要挖掉的只有註解那幾個字。
        """
        import io
        import tokenize as _tk
        lines = src.splitlines()
        cuts = {}
        try:
            for tok in _tk.generate_tokens(io.StringIO(src).readline):
                if tok.type == _tk.COMMENT:
                    r, c = tok.start
                    cuts[r - 1] = min(cuts.get(r - 1, 10 ** 9), c)
        except Exception:
            return src            # 切不乾淨就回原文(誠實:寧可誤紅,不可假綠)
        for i, c in cuts.items():
            if 0 <= i < len(lines):
                lines[i] = lines[i][:c]
        return "\n".join(lines)
    _code27 = _nocomment(_seg27)
    chk("㉓ 不准寫死「兩支都 rc=0」:那句話在工作站實錄裡**印在 `rc=2` 的下一行**。"
        "句子裡的 rc 一律由 steps 現場組(rcline),寫死的斷言會說出它沒量過的事",
        "兩支都 rc=0" not in _code27 and "rcline" in _code27,
        "run_chain 原始碼斷言(去註解後)")
    _fake = [{"engine": "VRN_ENG072_x_v0136.py", "rc": 0, "tail": "ok"},
             {"engine": "VRN_ENG073_y_v0129.py", "rc": 2, "tail": "[入庫] 無分區 sidecar"}]
    _broken = [s for s in _fake if s["rc"] not in (0, 2)]
    _nodata = [s for s in _fake if s["rc"] == 2]
    chk("㉔ 鏈上有人說 NODATA=**那就是答案**,不准再叫人去找庫在哪"
        "(庫沒被寫出來不是因為寫到別處,是因為沒有東西可寫;"
        "工作站照著找了三輪換了兩個庫,每一輪同一個 NODATA)",
        (not _broken) and bool(_nodata)
        and "換一個庫去讀也不會變出資料" in _code27
        and _code27.index("nodata:") < _code27.index("not dbp.exists()"),
        "NODATA 分支要排在找庫分支**前面**")
    chk("㉕ 尾訊按**行**取不按字元切:NODATA 的 tail 是整份輸出(L62 不切),"
        "用 `[-200:]` 切會切到橫幅裡的半句話——引擎的結論印在最後,所以取尾兩行",
        _why_lines("a\n\n  [結論] 沒有料\n") == "a / [結論] 沒有料"
        and _why_lines("a\n\n  [結論] 沒有料\n", n=1) == "[結論] 沒有料"   # 空行不算、行首空白要去掉
        and _why_lines("x" * 500) == "x" * 500
        and _why_lines("") == "(沒有尾訊)"
        and "[-200:]" not in _code27,
        f"({_why_lines('第一行' + chr(10) + '第二行' + chr(10) + '第三行')})")
    chk("㉖ `[鏈因]` 標記在位:下游用 grep 標記取理由,不用猜哪一行"
        "(v0102 啟動器用 `-match 'rc=\\d'` 撈,撈到橫幅半句話)",
        "[鏈因]" in _src27)
    chk("㉗ 批628 券商權威 vs 通道:`FILENAME_MAP` 只說走哪條路找到的,不算來源;"
        "`FILENAME_MAP+CANON` 才算出自正典冊(overlay v0101 把 CANON 改寫成 FILENAME_MAP,"
        "81 份裡 61 份被蓋掉,券商欄 GREEN 0 · YELLOW 59——加同義字治不了這個)",
        _v_broker("KGI", {"broker_src": "FILENAME_MAP"}) is None
        and _v_broker("KGI", {"broker_src": "FILENAME_MAP+CANON"}) is True
        and _v_broker("KGI", {"broker_src": "CANON"}) is True
        and _v_broker("KGI", {"broker_src": "OVERLAY_ALIAS"}) is None
        and _v_broker("", {"broker_src": "FILENAME_MAP+CANON"}) is False,
        "通道→YELLOW · 權威→GREEN · 空→NODATA")
    # ══ 批630 補四檢:頁的自我驗證與版面 ══════════════════════════
    _fake = {"n_reports": 2, "n_cols": 2, "db": "x",
             "per_col": {"a": {"zh": "甲", "rule": "r", "GREEN": 1, "YELLOW": 1, "NODATA": 0, "ABSENT": 0},
                         "b": {"zh": "乙", "rule": "r", "GREEN": 0, "YELLOW": 0, "NODATA": 1, "ABSENT": 1}},
             # 批630B:格子多了 `verdict`,判對率改用它算。批630A 的夾具沒有這個欄位,
             #   新碼一跑就 judged=0、hit_rate=None,當場 TypeError——
             #   **夾具要跟著契約走**,不然它量的是舊契約(LL219 同族)。
             "rows": [{"report": "p1", "cells": {"a": {"state": "GREEN", "verdict": "PASS", "value": "1", "why": ""},
                                                 "b": {"state": "NODATA", "verdict": "NO_VALUE", "value": "", "why": ""}}},
                      {"report": "p2", "cells": {"a": {"state": "YELLOW", "verdict": "FAIL", "value": "2", "why": "w"},
                                                 "b": {"state": "ABSENT", "verdict": "NO_COLUMN", "value": "", "why": ""}}}],
             "tally": {"GREEN": 1, "YELLOW": 1, "NODATA": 1, "ABSENT": 1}}
    _sv = self_verify(_fake)
    chk("㉘ 自我驗證是**現場重數**不是抄 tally:形狀、四態、加總三條都對得起來"
        "(抄一遍只證明我抄對了,證明不了那份 tally 是對的 LL112)",
        _sv["ok"] and _sv["n_cells"] == 4 and _sv["live"]["GREEN"] == 1, str(_sv["live"]))
    chk("㉙ 判對率**不把缺料算進分母**:2 格判得動(1 綠 1 黃)→ 50%,"
        "不是 1/4=25%——把 NODATA/ABSENT 混進分母,補料就會假裝成變準",
        abs(_sv["hit_rate"] - 50.0) < 1e-9 and _sv["judged"] == 2
        and abs(_sv["cover_rate"] - 50.0) < 1e-9,
        f"(判對率 {_sv['hit_rate']:.1f}% · 可判率 {_sv['cover_rate']:.1f}%)")
    _bad = {**_fake, "tally": {"GREEN": 9, "YELLOW": 1, "NODATA": 1, "ABSENT": 1}}
    chk("㉚ tally 被動過手腳要照得出來(自我驗證不是裝飾)",
        not self_verify(_bad)["ok"])
    _h = to_html(_fake)
    chk("㉛ 批630/632 版面令:字級再降一級(body 10.5px;批630 是 11px)· "
        "表格自動最佳化(table-layout:auto + width:max-content)· 儲存格自動換行(word-break)· "
        "表頭與第一欄 sticky · 零 CDN",
        "font:10.5px" in _h and "table-layout:auto" in _h and "width:max-content" in _h
        and "word-break:break-word" in _h and "position:sticky" in _h
        and "<script src" not in _h and "http://" not in _h and "https://" not in _h,
        f"({len(_h)} 字")
    # ══ 批630B 補二檢 ══════════════════════════════════════════════
    _c2 = {"state": "YELLOW", "verdict": "UNVERIFIABLE", "value": "1.0", "why": "驗不了(沒有可對照的)"}
    _c3 = {"state": "YELLOW", "verdict": "FAIL", "value": "9", "why": "驗不過"}
    _c1 = {"state": "GREEN", "verdict": "PASS", "value": "8", "why": ""}
    _m2 = {"n_reports": 1, "n_cols": 3, "db": "x",
           "per_col": {"a": {"zh": "甲", "rule": "r", "GREEN": 1, "YELLOW": 2, "NODATA": 0, "ABSENT": 0},
                       "b": {"zh": "乙", "rule": "r", "GREEN": 0, "YELLOW": 0, "NODATA": 0, "ABSENT": 0},
                       "c": {"zh": "丙", "rule": "r", "GREEN": 0, "YELLOW": 0, "NODATA": 0, "ABSENT": 0}},
           "rows": [{"report": "p", "cells": {"a": _c1, "b": _c2, "c": _c3}}],
           "tally": {"GREEN": 1, "YELLOW": 2, "NODATA": 0, "ABSENT": 0}}
    _s2 = self_verify(_m2)
    chk("㉜ 批630B **「驗不了」不算判錯**:1 PASS · 1 FAIL · 1 UNVERIFIABLE → "
        "判對率 = 1/2 = 50%(不是 1/3=33%),可判率 = 2/3。"
        "「沒有可對照的」是缺料,算進判對率等於把料的帳記到邏輯頭上,"
        "而且補了料那個比率會自己上升,看起來像邏輯變準了",
        abs(_s2["hit_rate"] - 50.0) < 1e-9 and _s2["judged"] == 2
        and abs(_s2["cover_rate"] - 200.0 / 3) < 1e-6,
        f"(判對率 {_s2['hit_rate']:.1f}% · 可判率 {_s2['cover_rate']:.1f}% · {_s2['verdicts']})")
    chk("㉝ 評等那一句的驗法要**跟真的用的那把尺同名**"
        "(樞紐補上 rating_keys() 之後,句子不能還寫 rating_words)",
        RATING_SRC in ("rating_keys", "rating_canon", "rating_words", "(未載)")
        and ("{RATING_SRC}" not in
             "".join(v["rule"] for v in matrix_or_empty_rules())),
        f"(實際用的尺:{RATING_SRC})")
    chk("⑳ 帶加速器橋(MDL156 覆蓋閘)", "[VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))
    # 批624:關節檢。v0100 兩支都 rc=0、整條報 OK,而 ENG073 根本沒收到夾也沒收到庫
    #   ——**rc=0 只說沒爆,不說接上了**。這兩檢就是照關節,不是照回傳值。
    _src = Path(__file__).read_text(encoding="utf-8")
    _seg = _src[_src.index("def run_chain"):_src.index("# ───", _src.index("def run_chain"))]
    chk("⑤ 關節:ENG073 收 **--db**(庫要同一個),但**不准**收 --dir"
        "——`--dir` 是**分區 sidecar 夾**(ENG073 的 ZONES_DIR 預設),不是 PDF 原始夾;"
        "批624 我拿 PDF 夾去覆蓋那個預設,`glob(\"*.json\")` 一個都找不到,"
        "工作站當場 `無分區 sidecar`。**把對的預設改成錯的明傳,比不傳更糟。**",
        '"--db"' in _seg and '"--dir"' not in _seg and "str(dbp)" in _seg,
        "run_chain 原始碼斷言")
    chk("⑥ 兩半吃同一個庫:庫在 run_chain **解析一次**再往下傳,"
        "不是兩邊各用各的預設(本件預設 VRN/output,ENG073 預設 VDF/output_hub——兩個不同的檔)",
        "dbp = Path(db) if db else DEFAULT_DB" in _seg and "str(dbp)" in _seg)
    with tempfile.TemporaryDirectory() as _td:
        _t = Path(_td)
        _a = matrix(str(_t / "nodir" / "x.duckdb"))          # 父夾不存在=還沒跑過
        (_t / "has").mkdir()
        (_t / "has" / "other.txt").write_text("x", encoding="utf-8")
        _b = matrix(str(_t / "has" / "x.duckdb"))            # 父夾有東西=跑過了但庫沒落這
        chk("⑦ 修法句不准指回剛剛那一句(L92):「還沒跑過」與「跑過了但庫沒出現」是兩件事,"
            "不能給同一句話把人送回原地繞圈(工作站實錄:他剛跑完 run,matrix 叫他去跑 run)",
            _a["state"] == "ABSENT" and _b["state"] == "ABSENT"
            and _a["why"] != _b["why"]
            and "還沒跑過" in _a["why"] and "沒落在這裡" in _b["why"]
            and "via-vrnmatrix run --in" not in _b["why"],
            "兩態兩句")
    # ㉒ 批625:**每一個產得出來的 state,都要接得到 rc**。
    #   v0101 加了 NODATA 卻沒接 rc,畫面印 NODATA、rc 回 1,下游照 rc 判就說「引擎壞了」。
    #   判準是量出來的:掃 run_chain/matrix 的原始碼,把所有 `"state": "X"` 與
    #   `["state"] = "X"` 的 X 撈出來,逐個問 _RC_OF 認不認得。
    import re as _re
    _src2 = Path(__file__).read_text(encoding="utf-8")
    _body = _src2[_src2.index("def run_chain"):_src2.index("def selftest")]
    _states = set(_re.findall(r'"state":\s*"([A-Z_]+)"', _body)) | \
              set(_re.findall(r'\["state"\]\s*=\s*"([A-Z_]+)"', _body))
    _miss = sorted(_states - set(_RC_OF))
    chk("㉒ 誠實四態要接得到 rc:每一個產得出來的 state 都在 _RC_OF 裡"
        "(加一個態不接 rc,那個態就只活在畫面上——下游照 rc 判會判錯)",
        not _miss and len(_states) >= 3,
        f"(產得出 {sorted(_states)} · 沒接 rc 的 {_miss or '無'})")

    # ══ 批632 補八檢:分頁式舉證頁與燈號管理 ═══════════════════════════
    _h2 = to_html(_m2)
    _ev2 = evidence(_m2)
    chk("㉞ 六個分頁都在,而且 **TAB1 是給 AI 的舉證**(操作員令指名的位置)",
        _h2.count("class='pane'") == 6 and _h2.index("① 給 AI 的舉證") < _h2.index("② 矩陣")
        and all(x in _h2 for x in ("③ 逐欄燈號", "④ 逐格驗證", "⑤ 自我驗證", "⑥ 燈號冊")),
        f"(分頁 {_h2.count(chr(39).join(['class=', 'pane', '']))} 塊")
    chk("㉟ TAB1 的 MD / JSON **內嵌在頁裡**(伺服端算一次),不是瀏覽器再算一次"
        "——兩邊各算一次就會各說各話;複製與下載都有鍵",
        "id='ev-md'" in _h2 and "id='ev-js'" in _h2
        and "function dl(" in _h2 and "function cp(" in _h2
        and "Markdown" in _h2 and ">JSON<" in _h2)
    _md2, _js2 = ev_to_md(_ev2), ev_to_json(_ev2)
    _hit2 = f"{_ev2['self_verify']['hit_rate']:.1f}%"
    chk("㊱ MD 與 JSON **同源**:同一份 ev 出兩種格式,判對率在兩邊是同一個數字"
        "(各算一次的話,補完料的那一刻兩份就會開始對不起來)",
        _hit2 in _md2 and json.loads(_js2)["self_verify"]["hit_rate"] == _ev2["self_verify"]["hit_rate"],
        f"(判對率 {_hit2}")
    # 夾具要**混著黃燈**:全綠的夾具跑 focus 會列 0 筆,那證不出「非 GREEN 的有被列出來」,
    #   只證得出「有東西被丟掉」——夾具沒造對,檢就在量別的東西(批630B 同一個坑)。
    _N, _Y = EV_FULL_MAX + 5, 7
    _big = {"n_reports": 1, "n_cols": 1, "db": "x",
            "per_col": {"a": {"zh": "甲", "rule": "r", "GREEN": _N - _Y,
                              "YELLOW": _Y, "NODATA": 0, "ABSENT": 0}},
            "tally": {"GREEN": _N - _Y, "YELLOW": _Y, "NODATA": 0, "ABSENT": 0},
            "rows": [{"report": f"r{i}", "cells": {"a": dict(_c3 if i < _Y else _c1)}}
                     for i in range(_N)]}
    _evb = evidence(_big)
    chk("㊲ **舉證自動調節**:格數超過門檻就收斂成只列非 GREEN,而且"
        "**把收斂這件事寫進舉證**(列出的 + 省略的 = 總格,不許悄悄少給)",
        _evb["depth"]["mode"] == "focus"
        and _evb["depth"]["n_listed"] + _evb["depth"]["n_omitted"] == _evb["depth"]["n_cells"]
        and _evb["depth"]["n_listed"] == _Y
        and all(c["state"] != "GREEN" for c in _evb["cells"])
        and "收斂" in _evb["depth"]["why"]
        and evidence(_m2)["depth"]["mode"] == "full",
        f"({_evb['depth']['n_cells']} 格 → 列 {_evb['depth']['n_listed']} · 省 {_evb['depth']['n_omitted']}")
    _tb = _src2[_src2.index("def to_html"):_src2.index("def open_page")]
    chk("㊳ 燈號冊是**這一頁所有顏色的唯一出處**:`to_html` 從 LAMPS 取色,"
        "不在頁裡再寫一份 state→色碼(批630B 就是退路悄悄換了一把尺,"
        "四份抽對的被判成黃燈)",
        'colr = {k: v["hex"] for k, v in LAMPS.items()}' in _tb
        and not re.search(r'"(GREEN|YELLOW|NODATA|ABSENT)":\s*"#', _tb))
    # 這裡**不能用正規式**:`verdict = "PASS" if ok else ("FAIL" if ... else "UNVERIFIABLE")`
    #   一行裡有三個答案,`verdict = "([A-Z_]+)"` 只看得到第一個。
    #   第一版我就是這樣寫的,檢是綠的,而它只掃到 PASS ——**檢自己假綠**。
    #   改走 AST:找到指派給 `verdict` / `st` 的節點,再走整棵運算式收所有字串。
    import ast as _ast
    _mt = next(f for f in _ast.walk(_ast.parse(_src2))
               if isinstance(f, _ast.FunctionDef) and f.name == "matrix")
    _vs, _ss = set(), set()
    for _nd in _ast.walk(_mt):
        _tgt = []
        if isinstance(_nd, _ast.Assign):
            _tgt = [t.id for t in _nd.targets if isinstance(t, _ast.Name)]
            _val = _nd.value
        elif isinstance(_nd, _ast.Dict):
            # **只收 `verdict`,不收 `state`**。`matrix()` 裡 `state` 這個鍵有**兩個命名空間**:
            #   引擎層 `{"state": "OK"/"NODATA"/"ABSENT"/"FAIL"}` 是回給 rc 的誠實四態(㉒ 在管),
            #   格子層 `{"state": st}` 才是燈。同一個鍵名、兩把尺——收在一起就會拿 rc 的態
            #   去問燈號冊,問出一堆「冊上沒有」。格子層的燈只從 `st = ...` 收。
            for _k, _v in zip(_nd.keys, _nd.values):
                if isinstance(_k, _ast.Constant) and _k.value == "verdict":
                    _vs |= {c.value for c in _ast.walk(_v)
                            if isinstance(c, _ast.Constant) and isinstance(c.value, str)}
            continue
        else:
            continue
        for _t in _tgt:
            if _t in ("verdict", "st"):
                (_vs if _t == "verdict" else _ss).update(
                    c.value for c in _ast.walk(_val)
                    if isinstance(c, _ast.Constant) and isinstance(c.value, str))
    _ss = {x for x in _ss if x.isupper()}
    chk("㊴ 每一個**產得出來**的裁決都在裁決冊、每一個燈都在燈號冊"
        "(加一個裁決不進冊,它就只活在程式裡——LL207 同族)。"
        "判準走 AST 不走正規式:`verdict = A if … else (B if … else C)` 一行三個答案,"
        "正規式只看得到第一個,**檢會自己假綠**。另外 `state` 這個鍵在 `matrix()` 裡有"
        "**兩個命名空間**——引擎層的誠實四態(接 rc,㉒ 在管)與格子層的燈;"
        "燈只從 `st = …` 收,混在一起就會拿 rc 的態去問燈號冊",
        len(_vs) >= 5 and not (_vs - set(VERDICTS))
        and len(_ss) >= 4 and not (_ss - set(LAMPS)),
        f"(裁決 {sorted(_vs)} · 燈 {sorted(_ss)}")
    _before = self_verify(_m2)["judged"]
    VERDICTS["UNVERIFIABLE"]["in_denom"] = True
    try:
        _after = self_verify(_m2)["judged"]
    finally:
        VERDICTS["UNVERIFIABLE"]["in_denom"] = False
    chk("㊵ 分母資格那一欄是**真的被讀的**,不是說明文字:把冊上的 in_denom 翻一個,"
        "判對率的分母就得跟著變(不變 = 程式裡另外手抄了一份 PASS+FAIL)",
        _after == _before + 1 and self_verify(_m2)["judged"] == _before,
        f"(翻之前 {_before} → 翻之後 {_after} → 還原 {self_verify(_m2)['judged']}")
    chk("㊶ 零彈窗(操作員長令):狀態寫在頁上那一行,不用 alert/confirm/prompt",
        not any(k in _h2 for k in ("alert(", "confirm(", "prompt(")))
    chk("㊷ 逐格分頁的燈號篩選器**跟燈號冊一樣多**(加一盞燈沒接篩選器,那盞燈就篩不到,"
        "等於它在頁上沒有管理)",
        _h2.count("data-s='") == len(LAMPS) + 1 + len(_flat_cells(_m2)),
        f"(按鍵 {len(LAMPS)} 盞 + 全部 1 · 列 {len(_flat_cells(_m2))}")

    # ══ 批633 補五檢:欄名對得上正典表 · 第五態不適用 ═══════════════════
    # ㊸ 這一檢是拿工作station 那 105 格全 ABSENT 換來的。
    #   我把欄位鍵寫成 `upside`,而正典表裡叫 `upside_calc`/`upside_state`。
    #   後果不是一格紅,是**整欄安靜缺席**——而且 ABSENT 長得像「引擎版本不合」
    #   這種誠實態,不像「我打錯字」。所以要有一道把兩邊的欄名對起來。
    _e73 = sorted((VIA / "functional modules" / "VRN").glob("VRN_ENG073_ReportStructuredDB_v*.py"))
    if not _e73:
        chk("㊸ 欄名要對得上 ENG073 的正典表", False, "ENG073 不在,對不起來(誠實 FAIL,不跳過)")
    else:
        _s73 = _e73[-1].read_text(encoding="utf-8")
        _blk = _s73[_s73.index("vrn_report_basic("):]
        _blk = _blk[:_blk.index('"""')]
        _schema = set(re.findall(r"([a-z_][a-z0-9_]*)\s+(?:VARCHAR|DOUBLE|INTEGER|BIGINT|BOOLEAN)",
                                 _blk, re.I))
        _tail73 = _s73[_s73.index("vrn_report_basic("):]
        _schema |= set(re.findall(r'"([a-z_][a-z0-9_]*)\s+(?:VARCHAR|DOUBLE|INTEGER|BIGINT|BOOLEAN)"',
                                  _tail73[:_tail73.index("def ", 200)] if "def " in _tail73[200:] else _tail73,
                                  re.I))
        _miss73 = [k for k, *_ in COLUMNS if k not in _schema]
        chk("㊸ 每一個欄位鍵都要真的在 ENG073 的正典表裡"
            "(寫一個不存在的欄名,整欄會**安靜地全 ABSENT**——而 ABSENT 長得像"
            "『引擎版本不合』這種誠實態,不像『我打錯字』。工作站 105 格就是這樣沒的)",
            not _miss73 and len(_schema) >= 15,
            f"(表上 {len(_schema)} 欄 · 對不上的 {_miss73 or '無'}")
    _rl = _applicability()
    chk("㊹ 適用性冊讀得到,而且規則是**推導來的**不是我說了算"
        "(唯一一條 NA-01 的依據是 ENG073 自己的分類律:有代號一律先算個股"
        "⇒ 非個股就是檔名裡沒有可驗證的代號)",
        len(_rl) >= 1 and all(r.get("basis") for r in _rl)
        and any(r["column"] == "ticker" for r in _rl),
        f"(規則 {len(_rl)} 條)")
    chk("㊺ 不適用只認冊:個股報告的代號**不得**被判成不適用;"
        "非個股報告的代號才是",
        not not_applicable("ticker", {"report_kind": "個股"}, _rl)
        and bool(not_applicable("ticker", {"report_kind": "產業"}, _rl))
        and not not_applicable("target_price", {"report_kind": "產業"}, _rl),
        not_applicable("ticker", {"report_kind": "產業"}, _rl))
    _sv_book = globals()["APPLICABILITY"]
    globals()["APPLICABILITY"] = Path(tempfile.gettempdir()) / "__no_such_book__.json"
    try:
        chk("㊻ 冊缺席 = **全部當適用**,不假造 N/A"
            "(給多了 N/A 就是把真的缺料藏起來,跟假綠同一種傷)",
            _applicability() == [] and not not_applicable("ticker", {"report_kind": "產業"}, []))
    finally:
        globals()["APPLICABILITY"] = _sv_book
    _c4 = {"state": "NA", "verdict": "NOT_APPLICABLE", "value": "", "why": "NA-01:報告型別「產業」不是 個股"}
    _m3 = {"n_reports": 1, "n_cols": 4, "db": "x",
           "per_col": {k: {"zh": k, "rule": "r", "GREEN": 0, "YELLOW": 0,
                           "NODATA": 0, "ABSENT": 0, "NA": 0} for k in "abcd"},
           "tally": {"GREEN": 1, "YELLOW": 1, "NODATA": 1, "ABSENT": 0, "NA": 1},
           "rows": [{"report": "r", "cells": {"a": dict(_c1), "b": dict(_c3),
                                              "c": {"state": "NODATA", "verdict": "NO_VALUE",
                                                    "value": "", "why": ""}, "d": dict(_c4)}}]}
    for k, st in zip("abcd", ("GREEN", "YELLOW", "NODATA", "NA")):
        _m3["per_col"][k][st] = 1
    _sv3 = self_verify(_m3)
    _h3 = to_html(_m3)
    chk("㊼ **兩個可判率都要印**:N/A 留在分母裡 100% 按定義做不到,"
        "悄悄拿掉又會憑空好看。所以全格與扣掉不適用兩個都給,N/A 幾格寫在旁邊",
        _sv3["n_na"] == 1 and _sv3["n_applicable"] == 3
        and abs(_sv3["cover_rate"] - 50.0) < 1e-9
        and abs(_sv3["cover_rate_applicable"] - 200.0 / 3) < 1e-9
        and "可判率(全格)" in _h3 and "可判率(扣掉不適用)" in _h3
        and _sv3["ok"],
        f"(全格 {_sv3['cover_rate']:.1f}% · 扣不適用 {_sv3['cover_rate_applicable']:.1f}% · N/A {_sv3['n_na']}")
    # ㊾ 夾具自己造 schema = 自測在量一個不存在的庫。批633 之前這個夾具寫 `upside DOUBLE`,
    #   而正典表叫 `upside_calc`——自測一路全綠,真庫上整欄 ABSENT 105 格。
    if _e73:
        _fx = _src2[_src2.index('CREATE TABLE vrn_report_basic('):]
        _fx = _fx[:_fx.index('""")')]
        _fxc = set(re.findall(r"([a-z_][a-z0-9_]*)\s+(?:VARCHAR|DOUBLE|INTEGER|BIGINT|BOOLEAN)",
                              _fx, re.I))
        _bad_fx = sorted(_fxc - _schema)
        chk("㊾ 自測夾具的表結構必須是 **ENG073 正典表的子集**"
            "(夾具自己造一個欄名,自測會一路全綠,而真庫上那一欄根本不存在"
            "——批633 之前就是這樣讓 105 格安靜 ABSENT 的)",
            not _bad_fx and len(_fxc) >= 10,
            f"(夾具 {len(_fxc)} 欄 · 正典表沒有的 {_bad_fx or '無'}")
    _svb = _src2[_src2.index("def self_verify"):_src2.index("def to_html")]
    chk("㊽ 四態重數與加總**掃燈號冊**,不手抄燈名"
        "(手抄那份在加第五盞燈的那天會安靜漏掉一態,而那一態照樣印在畫面上"
        "——於是『重數符合』在少數一態時還是綠的,LL207 同族)",
        'for k in LAMPS' in _svb
        and not re.search(r'\("GREEN",\s*"YELLOW",\s*"NODATA",\s*"ABSENT"\)', _svb))
    _ev3 = evidence(_m3)
    _md3 = ev_to_md(_ev3)
    chk("(51) 逐欄統計**每一盞燈都要帶到**:舉證的 columns、頁上 TAB3 的表頭、"
        "MD 的逐欄表,三處都得跟燈號冊一樣寬。加第五盞燈時我這三處原本都是寫死四個"
        "——燈條與綠率分母會少一塊,而表格看起來完全正常",
        all(all(L in c for L in LAMPS) for c in _ev3["columns"])
        and all(("<th>%s</th>" % L) in _h3 for L in LAMPS)
        and all(L in _md3.split("## 逐欄")[1].split("\n")[2] for L in LAMPS),
        f"(燈 {len(LAMPS)} 盞 · 欄 {len(_ev3['columns'])})")
    # 錨要釘**行首的定義**。第一版寫 `_src2.index("def main(")`,而這一行自己
    #   就帶著那串字,於是 index 先撞到我自己,切出來的「main」從這一檢開始算
    #   ——檢又一次比到自己(批632 的 ㊴ 同一族,這次是字串不是正則)。
    _mainsrc = _src2[_src2.index("\ndef main() -> int:"):]
    chk("(52) 畫面上的**態數不准寫死**:批633 加到五盞燈之後,"
        "`[自證]` 那一句還印「四態重數符合」——說四、數五,"
        "看的人會以為 N/A 沒被重數過。燈數一律 `len(LAMPS)` 現場數",
        "四態重數" not in _mainsrc and "{len(LAMPS)} 態重數" in _mainsrc)
    # ── (53) 批654:**兩種缺口合成一個數字,治法也會被合成一個** ──
    #   矩陣量到「評等 NODATA 35」,操作員的標準動作是「補同義字」。
    #   真的拆開數:**同義字缺口 0 · 抽取缺口 35** —— 補同義字一個都救不到。
    #   所以 candidates 必須把兩種分開:原字串抓到了但正典查不到(補字會好)
    #   vs 原字串根本沒抓到(補字一點用都沒有)。合在一起就是一個沒有下一步的數字(L92)。
    with tempfile.TemporaryDirectory() as _td654:
        _dbp = Path(_td654) / "c.duckdb"
        try:
            import duckdb as _dd654
            _c = _dd654.connect(str(_dbp))
            _c.execute("CREATE TABLE vrn_report_basic(report_file VARCHAR, rating_raw VARCHAR,"
                       " rating_ssot_key VARCHAR, broker VARCHAR, broker_ssot_key VARCHAR,"
                       " analyst_n INTEGER)")
            _c.execute("INSERT INTO vrn_report_basic VALUES "
                       "('a.pdf','Reiterate Buy','','GF','',1),"     # 同義字缺口(抓到了,冊上沒有)
                       "('b.pdf','Reiterate Buy','','GF','',0),"     # 同一種說法,要併成一筆
                       "('c.pdf','','','','',0)")                    # 抽取缺口(根本沒抓到)
            _c.close()
            _cand = candidates(str(_dbp))
            _rs = _cand["rating"]["synonym"]
            _ok654 = (_cand["state"] == "OK"
                      and len(_rs) == 1 and _rs[0]["raw"] == "Reiterate Buy" and _rs[0]["n"] == 2
                      and _cand["rating"]["extract_miss"] == 1
                      and _cand["broker"]["synonym"][0]["raw"] == "GF"
                      and _cand["broker"]["extract_miss"] == 1
                      and _cand["analyst"]["extract_miss"] == 2)
            _why654 = (f"(評等 同義字{len(_rs)}種/{_rs[0]['n'] if _rs else 0}份 · "
                       f"抽取缺{_cand['rating']['extract_miss']} · "
                       f"分析師缺{_cand['analyst']['extract_miss']})")
        except Exception as _e654:                             # noqa: BLE001
            _ok654, _why654 = False, f"{type(_e654).__name__}: {_e654}"
    chk("(53) **同義字缺口與抽取缺口要分開數**:原字串抓到了但正典查不到=補一個字就會好"
        "(裁定權在操作員 LL90);原字串根本沒抓到=補同義字一點用都沒有,那是上游的事。"
        "容器實測評等 NODATA 35 拆開來是 **同義字 0 · 抽取 35**——"
        "合成一個數字,治法就被合成一個",
        _ok654, _why654)
    # ── (54) 批655:**寫的人與讀的人指到不同檔案,矩陣不會報錯,只會讀一張舊表** ──
    #   操作員實機:ENG073 v0131 畫面上印出了 EXACT_MATCH_DB,矩陣那一欄卻
    #   GREEN 0 · YELLOW 38 · NODATA 67,**跟上一跑一個數字都沒動**。
    #   尺沒壞(把 `_DB` 態灌進一本庫餵給 matrix,它給 GREEN 30);
    #   壞的是庫路徑:ENG073 走批490 資料家優先解到 vdf_tw_market.duckdb,
    #   本器卻把 output/vrn_reports.duckdb 寫死。容器看不見——它沒有資料家,兩條路同檔。
    with tempfile.TemporaryDirectory() as _td655:
        _alt = Path(_td655) / "vdf_tw_market.duckdb"
        _ok655, _why655 = False, ""
        try:
            import duckdb as _dd655
            _c = _dd655.connect(str(_alt))
            _c.execute("CREATE TABLE vrn_report_basic(report_file VARCHAR)")
            _c.execute("INSERT INTO vrn_report_basic VALUES ('x.pdf'),('y.pdf')")
            _c.close()
            _old_env = os.environ.get("VIA_DB_VDF_TW_MARKET")
            os.environ["VIA_DB_VDF_TW_MARKET"] = str(_alt)
            try:
                _r655 = resolve_db()
                _explicit = resolve_db(str(_alt))
            finally:
                if _old_env is None:
                    os.environ.pop("VIA_DB_VDF_TW_MARKET", None)
                else:
                    os.environ["VIA_DB_VDF_TW_MARKET"] = _old_env
            _ok655 = (Path(_r655["path"]).name == "vdf_tw_market.duckdb"
                      and "資料家" in _r655["why"]
                      and len(_r655["heads"]) >= (2 if DEFAULT_DB.exists() else 1)
                      and Path(_explicit["path"]) == _alt and "--db" in _explicit["why"])
            _why655 = (f"(解到 {Path(_r655['path']).name} · 頭數 {len(_r655['heads'])} · "
                       f"理由 {_r655['why'][:22]})")
        except Exception as _e655:                            # noqa: BLE001
            _ok655, _why655 = False, f"{type(_e655).__name__}: {_e655}"
    chk("(54) **庫路徑要跟 ENG073 同一條路**(批490 資料家優先),而且"
        "「另外還有幾本庫也有 vrn_report_basic」要當場報出來 —— "
        "第二顆頭要被看見,不是被猜。寫的人與讀的人指到不同檔案時矩陣不會報錯,"
        "它只會安靜地讀一張舊表,於是修了也像沒修",
        _ok655, _why655)
    # ── (55) 批656:**整欄零綠時,要把底下的原始值分佈印出來** ──
    #   操作員實機:ENG073 畫面印著 `[EXACT_MATCH_DB]`,矩陣那一欄卻仍 GREEN 0。
    #   我批655 猜「兩本庫」,他的 candidates 讀 output/ 量到的券商缺口
    #   又與 ENG073 的 90/105 完全吻合 —— **我又隔空猜了一次**。
    #   停止再猜:零綠只有兩種可能(缺料 / 尺與值對不上),
    #   把該欄底下的原始值分佈印出來,一眼就分得開,而且是**判燈用的同一份 rows**。
    _rows655 = ([{"upside_calc": 1.0, "upside_state": "EXACT_MATCH", "upside_db": None}] * 3
                + [{"upside_calc": None, "upside_state": "MISSING_SOURCE", "upside_db": None}] * 2)
    _pb = zero_green_probe(_rows655, "upside_calc")
    _d = dict(_pb)
    _st = dict(_d.get("upside_state") or [])
    _dbv = dict(_d.get("upside_db") or [])
    _none = zero_green_probe([], "upside_calc")
    chk("(55) **整欄零綠要把底下的原始值分佈印出來**(缺料 vs 尺與值對不上,看一眼就分得開);"
        "而且要從**判燈用的同一份 rows** 數 —— 第一版我拿已經 close 掉的 con 去查,"
        "印出來三行 ConnectionException(印的跟判的不是同一批,那比不印還糟)",
        (_st.get("EXACT_MATCH") == 3 and _st.get("MISSING_SOURCE") == 2
         and _dbv.get("(NULL)") == 5
         and len(_none) == len(ZERO_GREEN_PROBE["upside_calc"])),
        f"(態 {_st} · 庫升幅 {_dbv} · 空 rows 回 {len(_none)} 項)")
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="VRN_ENG083_VerifiedMatrix", description="VRN 驗證矩陣(零網路;零寫庫)")
    ap.add_argument("verb", nargs="?", default="matrix", choices=["run", "matrix", "candidates"])
    ap.add_argument("--in", dest="indir", default="", help="報告夾或單檔(可為系統任何位置)")
    ap.add_argument("--db", default="", help="結構化庫(預設 functional modules/VRN/output/vrn_reports.duckdb)")
    ap.add_argument("--json", action="store_true")
    # 批632 操作員令「測試完後自動跳出 HTML U/I 矩陣報告」——**預設就開**。
    #   `--open` 留著不砍(啟動器與既有短令都在傳它,砍了是只減不增);
    #   要安靜就 `--no-open`,無頭環境本來就會誠實說開不了,不會假裝開了。
    ap.add_argument("--open", dest="do_open", action="store_true", default=True,
                    help="產完把 HTML 矩陣自動跳出來(預設就開;無頭環境會誠實說開不了)")
    ap.add_argument("--no-open", dest="do_open", action="store_false",
                    help="產完不要自動開頁(批632 之前的行為)")
    ap.add_argument("--evidence", choices=["auto", "full", "focus"], default="auto",
                    help="TAB1 舉證深度:auto 依格數自動調節(預設)· full 全量逐格 · focus 只列非 GREEN")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.verb == "candidates":
        c = candidates(a.db)
        if a.json:
            print(json.dumps(c, ensure_ascii=False, indent=2))
            return 0 if c["state"] == "OK" else 2
        print(f"[VRN_ENG083 v{VERSION}] 同義字候選 · {c['state']} · {c['why']}")
        print(f"  庫 {c['db']}")
        for fam, zh in (("rating", "評等"), ("broker", "券商")):
            d = c[fam]
            syn, miss = d["synonym"], d["extract_miss"]
            tot = sum(x["n"] for x in syn)
            print(f"  [{zh}] **同義字缺口 {tot} 份 / {len(syn)} 種說法** · 抽取缺口 {miss} 份")
            print("         同義字缺口=原字串抓到了但正典查不到 → 補一個字就會好,**裁定權在操作員**")
            print("         抽取缺口=原字串根本沒抓到 → 補同義字一點用都沒有,那是上游抽取的事")
            for x in syn[:12]:
                print(f"           {x['n']:>3} 份 · {x['raw'][:34]!r:38} 例:{str(x['例'])[:38]}")
            if syn:
                print("         [PENDING_OPERATOR] 要收的話收進 VIA_Financial_Institution_SSOT_v0100.py"
                      "(READ_ONLY 正典)—— **本支一個字都沒寫**")
        an = c["analyst"]
        print(f"  [分析師] 抽取缺口 {an['extract_miss']} 份(沒有原字串可收=不是同義字的事)")
        for x in an["sample"]:
            print(f"           {str(x)[:60]}")
        return 0 if c["state"] == "OK" else 2
    if a.selftest:
        return selftest()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if a.verb == "run":
        if not a.indir:
            print("  [絕] run 要給報告夾:via-vrnmatrix run --in \"C:\\測試樣本報告\"")
            return 1
        ch = run_chain(a.indir, a.db)
        print(f"[VRN_ENG083 v{VERSION}] 鏈實跑 · {ch['state']}")
        for s in ch.get("steps", []):
            print(f"   {s['engine']} rc={s['rc']} · {s['tail']}")
        if ch["state"] not in ("OK",):
            write_out(f"VRN_MATRIX_RUN_{ts}.json", ch)
            # 批627b:給下游一個**穩定標記**,不要讓它去猜哪一行是理由。
            # v0102 的啟動器用 `-match 'rc=\d'` 撈最後三行,撈到的是引擎橫幅的半句話。
            # 有標記就 grep 標記——這跟「有 rc 就別比字串」是同一條(LL207 族)。
            print(f"   [鏈因] {' '.join(str(ch.get('why', '')).split())}")
            # 批625 實跑抓到(我自己在批624 造的):v0101 新增了 NODATA 這一態,
            #   **卻沒有替它接 rc**——`return 3 if ABSENT else 1`,於是畫面印 NODATA、
            #   rc 回 1。下游(批625 的 VRN AUDIT 啟動器)照 rc 判,當場說「引擎自己壞了」。
            #   **加一個態就要接一個 rc,不然那個態只活在畫面上。**
            return _RC_OF.get(ch["state"], 1)
    m = matrix(a.db)
    write_out(f"VRN_MATRIX_{ts}.json", m)
    write_out("VRN_MATRIX_latest.json", m)
    if m["state"] == "OK":
        hp = write_out("VRN_MATRIX_latest.html", to_html(m))
        # 批632:舉證同時落 .md 與 .json 到檔。頁上那兩顆按鍵切的**就是這兩份**
        #   (伺服端算一次、內嵌進頁),不是瀏覽器再算一次——兩邊各算一次就會各說各話。
        _ev = evidence(m, a.evidence)
        mp = write_out("VRN_MATRIX_EVIDENCE.md", ev_to_md(_ev))
        jp = write_out("VRN_MATRIX_EVIDENCE.json", ev_to_json(_ev))
        _sv = self_verify(m)
        if a.json:
            print(json.dumps(m, ensure_ascii=False))
        else:
            w = max(len(v["zh"]) for v in m["per_col"].values()) + 2
            print(f"[VRN_ENG083 v{VERSION}] matrix · OK · {m['n_reports']} 份報告 × {m['n_cols']} 欄")
            # 批655:**讀的是哪一本庫,要印在臉上**。寫的人(ENG073,資料家優先)
            #   與讀的人(本器,舊路徑寫死)指到不同檔案時,矩陣不會報錯,
            #   它只會安靜地讀一張舊表 —— 數字一個都不動,而人以為修沒用。
            _zg = m.get("zero_green") or {}
            _hd = m.get("db_heads") or []
            print(f"  [庫] {m['db']}")
            print(f"       ← {m.get('db_why', '')}")
            if len(_hd) > 1:
                print(f"  [**第二顆頭**] 另有 {len(_hd) - 1} 本庫也有 vrn_report_basic —— "
                      "寫的人與讀的人可能指到不同檔案(Zero-Hydra:要被看見,不是被猜)")
                import datetime as _dt656
                for _h in _hd:
                    _ts = _dt656.datetime.fromtimestamp(_h["mtime"]).strftime("%Y-%m-%d %H:%M")
                    print(f"       {_h['rows']:>5} 列 · 最後寫於 {_ts} · {_h['why']}")
                    print(f"             {_h['path']}")
            for _k, _z in _zg.items():
                print(f"  [**整欄零綠**] {_z['zh']}({_k})—— 零綠只有兩種可能:"
                      "缺料,或尺與值對不上。底下的原始值分佈:")
                for _src, _vals in _z["probe"]:
                    if not _vals:
                        print(f"       {_src}")
                        continue
                    print(f"       {_src}:" + " · ".join(f"{_v}×{_n}" for _v, _n in _vals))
            print(f"  {'欄位':<{w}} {'驗法':<44} GREEN YELLOW NODATA ABSENT")
            for k, v in m["per_col"].items():
                print(f"  {v['zh']:<{w}} {v['rule']:<44} {v['GREEN']:>5} {v['YELLOW']:>6} "
                      f"{v['NODATA']:>6} {v['ABSENT']:>6}")
            t = m["tally"]
            print(f"  [計] 格子 {sum(t.values())} · "
                  + " · ".join(f"{k} {t.get(k, 0)}" for k in LAMPS)
                  + f"(誠實{len(LAMPS)}態;燈號冊 {len(LAMPS)} 盞)")
            if m.get("applicability_rules"):
                print(f"  [適用性] 冊 {APPLICABILITY.name} · 規則 {m['applicability_rules']} 條 · "
                      f"判成不適用 {_sv.get('n_na', 0)} 格"
                      f"(不適用=這種報告本來就沒有這一欄,**不是沒擷到**)")
            # 批630:結果印完**自己驗自己**(同一份 rows 現場重數,不抄 tally)
            # 批634:這一句寫死「四態」,而批633 已經是五盞燈——畫面上說四、
            #   實際數五,看的人會以為 N/A 沒被重數過。燈數改成現場數燈號冊。
            print(f"  [自證] {'一致' if _sv['ok'] else '**對不起來**'} · "
                  f"格子 {_sv['n_cells']}/{_sv['n_expect']} · {len(LAMPS)} 態重數"
                  f"{'符合' if _sv['tally_ok'] else '**不符合**'} · "
                  f"裁決 {dict(sorted(_sv['verdicts'].items()))}")
            if _sv["judged"]:
                # 批630B:這一句要說**它真的算了什麼**。分母是 PASS+FAIL(真的下過判斷的),
                #   不是 GREEN+YELLOW —— YELLOW 裡面混著「驗不了」,那是缺料。
                #   寫成 GREEN÷(GREEN+YELLOW) 而實際用 verdict 算,就是冊上寫錯尺的名字。
                _uv = _sv["verdicts"].get("UNVERIFIABLE", 0)
                print(f"  [判對率] {_sv['hit_rate']:.1f}% = PASS ÷(PASS+FAIL) = "
                      f"{_sv['verdicts'].get('PASS', 0)}/{_sv['judged']}"
                      + (f" · 另有 **{_uv} 格驗不了**(有值但沒有可對照的),"
                         f"它們在四態裡是 YELLOW,但**不進判對率的分母**"
                         f"——那是缺料不是判錯" if _uv else "")
                      + "(混進去的話,補料會假裝成變準)")
            else:
                print("  [判對率] 判得動的格 0,不算(沒有分母就不給比率)")
            if _sv["cover_rate"] is not None:
                print(f"  [可判率] 全格 {_sv['cover_rate']:.1f}% = {_sv['judged']}/{_sv['n_expect']}"
                      + (f" · 扣掉不適用 {_sv['cover_rate_applicable']:.1f}% = "
                         f"{_sv['judged']}/{_sv['n_applicable']}(不適用 {_sv['n_na']} 格"
                         f"——永遠補不起來的洞,留在分母裡 100% 按定義做不到;"
                         f"**但兩個都印,不許只印好看的那一個**)"
                         if _sv.get("n_na") and _sv.get("cover_rate_applicable") is not None else "")
                      + " —— **要 100% 準確,判對率與可判率都得是 100%**")
            if m.get("note"):
                print(f"  註:{m['note']}")
            print(f"  頁 {hp}")
            print(f"  [舉證] 深度 {_ev['depth']['mode']} · {_ev['depth']['why']}")
            print(f"         MD {mp}")
            print(f"         JSON {jp}")
            if getattr(a, "do_open", False):
                # 批633:這裡有**兩條令在打架**,不安靜蓋過去。
                #   批378 立了全域零跳出律(`.html` 預設程式是 VS Code,一開就彈),
                #   Register 在每個 VIA 視窗裡都會設 `VIA_NO_OPEN=1`;
                #   批632 操作員令則指名「測試完後自動跳出 HTML U/I 矩陣報告」。
                #   我依**較新且較具體**的那一條開,但要說出另一條在場——
                #   悄悄蓋過一條還在生效的律,下一個人會找不到為什麼會彈窗。
                if os.environ.get("VIA_NO_OPEN") == "1":
                    print("  [令衝突] 批378 全域零跳出律在場(VIA_NO_OPEN=1),"
                          "本頁依批632 操作員令**仍然開**(指名這一頁要自動跳出)。"
                          "要安靜:`--no-open`。要全域放行:`VIA_OPEN_PAGES=1`。")
                print(f"  [開頁] {open_page(hp)}")
        return 0
    print(f"[VRN_ENG083 v{VERSION}] matrix · {m['state']} · {m.get('why','')}")
    return {"NODATA": 2, "ABSENT": 3}.get(m["state"], 1)


if __name__ == "__main__":
    sys.exit(main())
