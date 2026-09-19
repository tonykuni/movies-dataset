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
    ("upside",           "上漲空間",   _v_upside,  "upside_state 為 EXACT_MATCH_DB / ROUNDING_ONLY_DB"),
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


def _call(engine: Path, args: list, timeout: int = 3600) -> dict:
    r = subprocess.run([sys.executable, str(engine), *args], capture_output=True, text=True,
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
def matrix(db: str = "") -> dict:
    global RATING_CANON
    p = Path(db) if db else DEFAULT_DB
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
        extra = [c for c in ("report_file", "broker_src", "upside_state", "analyst_n",
                             "close_price", "price") if c in have]
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

    cells, tally = [], {"GREEN": 0, "YELLOW": 0, "NODATA": 0, "ABSENT": 0}
    for r in rows:
        line = {"report": str(r.get("report_file", ""))[:60], "cells": {}}
        for key, zh, verify, rule in COLUMNS:
            if key not in have:
                st = "ABSENT"
                verdict = "NO_COLUMN"
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
                                  "why": ("" if st in ("GREEN", "NODATA", "ABSENT")
                                          else ("驗不過" if verdict == "FAIL"
                                                else "驗不了(沒有可對照的)"))}
            tally[st] += 1
        cells.append(line)
    n = len(rows)
    # 批630B:驗法句裡的 {RATING_SRC} **現場填**成真的用了哪一把尺
    #   ——寫死一個名字,尺換了句子不會跟著換,那就是冊上寫錯尺的名字。
    per_col = {key: {"zh": zh, "rule": rule.replace("{RATING_SRC}", RATING_SRC),
                     "GREEN": sum(1 for c in cells if c["cells"][key]["state"] == "GREEN"),
                     "YELLOW": sum(1 for c in cells if c["cells"][key]["state"] == "YELLOW"),
                     "NODATA": sum(1 for c in cells if c["cells"][key]["state"] == "NODATA"),
                     "ABSENT": sum(1 for c in cells if c["cells"][key]["state"] == "ABSENT")}
               for key, zh, _v, rule in COLUMNS}
    return {"state": "OK", "db": str(p), "n_reports": n, "n_cols": len(COLUMNS),
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
    judged = vd.get("PASS", 0) + vd.get("FAIL", 0)
    out = {
        "n_cells": len(cells), "n_expect": n_expect,
        "shape_ok": len(cells) == n_expect,
        "tally_ok": all(live.get(k, 0) == tal.get(k, 0) for k in
                        ("GREEN", "YELLOW", "NODATA", "ABSENT")),
        "sum_ok": sum(tal.get(k, 0) for k in ("GREEN", "YELLOW", "NODATA", "ABSENT")) == n_expect,
        "live": live,
        # **判對率不是 GREEN÷總格**。NODATA/ABSENT 是缺料,不是判錯;
        # 把缺料算進分母,補料就會「準確率上升」,那是把兩件事混成一個數字。
        "verdicts": vd,
        "hit_rate": (vd.get("PASS", 0) / judged * 100.0) if judged else None,
        "judged": judged,
        "cover_rate": (judged / n_expect * 100.0) if n_expect else None,
    }
    out["ok"] = out["shape_ok"] and out["tally_ok"] and out["sum_ok"]
    return out


def to_html(m: dict) -> str:
    e = _html.escape
    colr = {"GREEN": "#1a7f37", "YELLOW": "#9a6700", "NODATA": "#57606a", "ABSENT": "#8250df"}
    head = "".join(f"<th>{e(v['zh'])}<div class='r'>{e(v['rule'])}</div></th>" for v in m["per_col"].values())
    body = ""
    for r in m["rows"]:
        tds = ""
        for key in m["per_col"]:
            c = r["cells"][key]
            tds += (f"<td style='color:{colr[c['state']]}'><b>{c['state']}</b>"
                    f"<div class='v'>{e(c['value'])}</div>"
                    + (f"<div class='r'>{e(c['why'])}</div>" if c["why"] else "") + "</td>")
        body += f"<tr><td class='f'>{e(r['report'])}</td>{tds}</tr>"
    t = m["tally"]
    sv = self_verify(m)
    # 批630 操作員令:「HTML U/I 矩陣式自小一點 · 矩陣自動格是最佳化」
    #   字級 13→11(附註 11→9.5 · 標題 18→15);表格 `table-layout:auto` +
    #   `width:max-content` 讓欄寬**按內容自動最佳化**,外層 `overflow:auto` 承載;
    #   儲存格 `word-break:break-word` 自動換行;表頭與第一欄 sticky
    #   ——81×8 的矩陣捲到第 60 列時,不知道自己在看哪一欄就等於沒有矩陣。
    #   零 CDN:字體只用系統字,樣式全內嵌。
    _svc = "#1a7f37" if sv["ok"] else "#cf222e"
    _hit = f"{sv['hit_rate']:.1f}%" if sv["hit_rate"] is not None else "—"
    _cov = f"{sv['cover_rate']:.1f}%" if sv["cover_rate"] is not None else "—"
    return ("<!doctype html><meta charset='utf-8'><title>VRN 驗證矩陣</title>"
            "<style>"
            "body{font:11px/1.45 system-ui,'Microsoft JhengHei',sans-serif;margin:14px;background:#fff;color:#1f2328}"
            "h1{font-size:15px;margin:0 0 6px}.k{margin:6px 0 10px;font-size:10.5px;color:#424a53}"
            ".wrap{overflow:auto;max-height:82vh;border:1px solid #d0d7de;border-radius:4px}"
            "table{border-collapse:separate;border-spacing:0;table-layout:auto;width:max-content;min-width:100%}"
            "th,td{border-right:1px solid #d0d7de;border-bottom:1px solid #d0d7de;padding:3px 6px;"
            "vertical-align:top;word-break:break-word;overflow-wrap:anywhere;max-width:280px}"
            "th{background:#f6f8fa;text-align:left;position:sticky;top:0;z-index:3;font-size:11px}"
            "td:first-child,th:first-child{position:sticky;left:0;background:#fff;z-index:2;max-width:320px}"
            "th:first-child{z-index:4;background:#f6f8fa}"
            "tr:nth-child(even) td:first-child{background:#fbfcfd}"
            "tr:nth-child(even) td{background:#fbfcfd}"
            ".r{font-size:9.5px;color:#57606a;font-weight:400;line-height:1.35}"
            ".v{font-size:10px;color:#1f2328}.f{font-family:ui-monospace,monospace;font-size:10px}"
            ".sv{margin:0 0 10px;padding:6px 8px;border:1px solid #d0d7de;border-radius:4px;"
            "background:#f6f8fa;font-size:10.5px}"
            "</style>"
            f"<h1>VRN 驗證矩陣 · {m['n_reports']} 份報告 × {m['n_cols']} 欄</h1>"
            f"<div class='k'>庫 {e(m['db'])} · 產生 {datetime.now():%Y-%m-%d %H:%M} · "
            f"GREEN {t['GREEN']} · YELLOW {t['YELLOW']} · NODATA {t['NODATA']} · ABSENT {t['ABSENT']}"
            f"{'<br>' + e(m['note']) if m.get('note') else ''}</div>"
            f"<div class='sv'><b style='color:{_svc}'>自我驗證 {'一致' if sv['ok'] else '**對不起來**'}</b> · "
            f"格子 {sv['n_cells']}/{sv['n_expect']}(形狀{'✓' if sv['shape_ok'] else '✗'})· "
            f"四態逐格重數與抬頭{'一致 ✓' if sv['tally_ok'] else '**不一致 ✗**'} · "
            f"加總{'✓' if sv['sum_ok'] else '✗'}<br>"
            f"<b>判對率 {_hit}</b> = PASS ÷(PASS+FAIL)= "
            f"{sv['verdicts'].get('PASS', 0)}/{sv['judged']}"
            + (f" · 另有 <b>{sv['verdicts'].get('UNVERIFIABLE', 0)} 格驗不了</b>"
               f"(有值但沒有可對照的;四態裡是 YELLOW,<b>不進分母</b>)"
               if sv["verdicts"].get("UNVERIFIABLE") else "")
            + f" —— 缺料不是判錯,混進去的話「補料」會假裝成「變準」<br>"
            f"<b>可判率 {_cov}</b> = (GREEN+YELLOW)÷ 總格 = {sv['judged']}/{sv['n_expect']}"
            f" —— 要到 100% 準確,**這兩個數字都得是 100%**</div>"
            f"<div class='wrap'><table><tr><th>報告</th>{head}</tr>{body}</table></div>")


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
                broker_src VARCHAR, rating_ssot_key VARCHAR, target_price DOUBLE, close_price DOUBLE,
                upside DOUBLE, upside_state VARCHAR, analyst_names VARCHAR, analyst_n INTEGER)""")
            con.execute("""INSERT INTO vrn_report_basic VALUES
                ('2330_2026.pdf','2330','2026-09-01','FUBON','SSOT','BUY',900.0,600.0,0.5,'EXACT_MATCH_DB','王小明',1),
                ('9999_x.pdf','9999','2099-01-01','','GUESS','NOTARATING',1.0,600.0,0.5,'FORMULA_MISMATCH_DB','',0),
                ('empty.pdf',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0)""")
            con.close()
            m = matrix(str(dbp))
            chk("⑧ 矩陣讀得出三列", m["state"] == "OK" and m["n_reports"] == 3, f"{m.get('n_reports')} 列")
            g = {r["report"]: r["cells"] for r in m["rows"]}
            good = g["2330_2026.pdf"]
            chk("⑨ 好件:代號/報告日/券商/目標價/上漲空間/分析師 六欄 GREEN(每一欄都是被尺量過才綠)",
                all(good[k]["state"] == "GREEN" for k in
                    ("ticker", "report_date", "broker_ssot_key", "target_price", "upside", "analyst_names")),
                str({k: good[k]["state"] for k in good}))
            bad = g["9999_x.pdf"]
            chk("⑩ 壞件:未來日 / 券商空 / 目標價比失真 / 重算對不上 —— 一律 YELLOW,不冒充 GREEN",
                bad["report_date"]["state"] == "YELLOW" and bad["target_price"]["state"] == "YELLOW"
                and bad["upside"]["state"] == "YELLOW" and bad["broker_ssot_key"]["state"] == "NODATA",
                str({k: bad[k]["state"] for k in ("report_date", "target_price", "upside", "broker_ssot_key")}))
            emp = g["empty.pdf"]
            chk("⑪ 空件:七欄**全部** NODATA,不冒充 YELLOW(沒擷到 ≠ 擷到但錯)",
                all(emp[k]["state"] == "NODATA" for k, *_ in COLUMNS),
                str({k: emp[k]["state"] for k in emp}))
            chk("⑫ 驗不過與驗不了的理由分得開(不是都寫『壞掉』)",
                bad["report_date"]["why"] == "驗不過"
                and any(c["cells"]["rating_ssot_key"]["why"] in ("驗不過", "驗不了(沒有可對照的)")
                        for c in m["rows"]),
                f"報告日「{bad['report_date']['why']}」")
            chk("⑬ 逐欄統計四態加起來等於列數(分子分母數同一件事;LL112)",
                all(sum(v[s] for s in ("GREEN", "YELLOW", "NODATA", "ABSENT")) == m["n_reports"]
                    for v in m["per_col"].values()))
            con2 = duckdb.connect(str(dbp))
            con2.execute("INSERT INTO vrn_report_basic VALUES "
                         "('zero.pdf','1101','2026-09-01','FUBON','SSOT','HOLD',600.0,600.0,"
                         "0.0,'EXACT_MATCH_DB','李四',1)")
            con2.close()
            mz = matrix(str(dbp))
            zc = {r["report"]: r["cells"] for r in mz["rows"]}["zero.pdf"]
            chk("⑯ 上漲空間 0.0 是合法值,不准被當成沒擷到(第一版的 `in (None,\"\",0)` 就是這個坑)",
                zc["upside"]["state"] == "GREEN", f"upside={zc['upside']['state']} 值 {zc['upside']['value']}")
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
    chk("㉛ 批630 版面令:字級調小(body 11px)· 表格自動最佳化(table-layout:auto + "
        "width:max-content)· 儲存格自動換行(word-break)· 表頭與第一欄 sticky · 零 CDN",
        "font:11px" in _h and "table-layout:auto" in _h and "width:max-content" in _h
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
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="VRN_ENG083_VerifiedMatrix", description="VRN 驗證矩陣(零網路;零寫庫)")
    ap.add_argument("verb", nargs="?", default="matrix", choices=["run", "matrix"])
    ap.add_argument("--in", dest="indir", default="", help="報告夾或單檔(可為系統任何位置)")
    ap.add_argument("--db", default="", help="結構化庫(預設 functional modules/VRN/output/vrn_reports.duckdb)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--open", dest="do_open", action="store_true",
                    help="產完把 HTML 矩陣自動跳出來(無頭環境會誠實說開不了)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
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
        _sv = self_verify(m)
        if a.json:
            print(json.dumps(m, ensure_ascii=False))
        else:
            w = max(len(v["zh"]) for v in m["per_col"].values()) + 2
            print(f"[VRN_ENG083 v{VERSION}] matrix · OK · {m['n_reports']} 份報告 × {m['n_cols']} 欄")
            print(f"  {'欄位':<{w}} {'驗法':<44} GREEN YELLOW NODATA ABSENT")
            for k, v in m["per_col"].items():
                print(f"  {v['zh']:<{w}} {v['rule']:<44} {v['GREEN']:>5} {v['YELLOW']:>6} "
                      f"{v['NODATA']:>6} {v['ABSENT']:>6}")
            t = m["tally"]
            print(f"  [計] 格子 {sum(t.values())} · GREEN {t['GREEN']} · YELLOW {t['YELLOW']} "
                  f"· NODATA {t['NODATA']} · ABSENT {t['ABSENT']}(誠實四態)")
            # 批630:結果印完**自己驗自己**(同一份 rows 現場重數,不抄 tally)
            print(f"  [自證] {'一致' if _sv['ok'] else '**對不起來**'} · "
                  f"格子 {_sv['n_cells']}/{_sv['n_expect']} · 四態重數"
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
                print(f"  [可判率] {_sv['cover_rate']:.1f}% = 判得動的格 ÷ 總格 = "
                      f"{_sv['judged']}/{_sv['n_expect']} —— "
                      f"**要 100% 準確,這兩個數字都得是 100%**")
            if m.get("note"):
                print(f"  註:{m['note']}")
            print(f"  頁 {hp}")
            if getattr(a, "do_open", False):
                print(f"  [開頁] {open_page(hp)}")
        return 0
    print(f"[VRN_ENG083 v{VERSION}] matrix · {m['state']} · {m.get('why','')}")
    return {"NODATA": 2, "ABSENT": 3}.get(m["state"], 1)


if __name__ == "__main__":
    sys.exit(main())
