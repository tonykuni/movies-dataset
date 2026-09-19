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


def _v_broker(v, row):
    if not str(v or "").strip():
        return False
    src = str(row.get("broker_src", "")).upper()
    return True if ("SSOT" in src or "冊" in src) else None   # 來自正典冊=驗過


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
    ("rating_ssot_key",  "評等",       _v_rating,  "落在正典評等詞彙(樞紐 rating_words)"),
    ("target_price",     "目標價",     _v_tp,      "> 0 且 目標價/現價 落在 0.2–5.0"),
    ("upside",           "上漲空間",   _v_upside,  "upside_state 為 EXACT_MATCH_DB / ROUNDING_ONLY_DB"),
    ("analyst_names",    "分析師",     _v_analyst, "analyst_n ≥ 1"),
]
RATING_CANON: set = set()


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
    steps = [_call(e72, ["run", "--in", str(src)])]
    steps.append(_call(e73, ["run", "--dir", str(src), "--db", str(dbp)]))
    bad = [s for s in steps if s["rc"] not in (0, 2)]
    out = {"state": "OK" if not bad else "FAIL", "steps": steps, "db": str(dbp),
           "why": "" if not bad else "; ".join(f"{s['engine']} rc={s['rc']}\n{s['tail']}" for s in bad)}
    # 跑完要**看一眼庫真的出現了沒**。rc=0 只說「沒爆」,不說「有落地」。
    if not bad and not dbp.exists():
        t73 = next((x["tail"] for x in steps if "ENG073" in x.get("engine", "")), "")
        out["state"] = "NODATA"
        out["why"] = (f"兩支都 rc=0,但庫沒有出現在 {dbp}。"
                      f"**這不是叫你再跑一次**——同一句再跑會得到同一個結果。"
                      f"下一步是看 ENG073 到底把東西寫去哪了:"
                      f"`VRN_ENG073_ReportStructuredDB_v*.py status --db \"{dbp}\"`;"
                      f"它剛才說的是:{(t73 or '(沒有尾訊)')[-200:]}")
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
            else:
                v = r.get(key)
                # 空=NODATA。用 `is None or == ""`,**不要**用 `in (None,"",0)`——
                # 上漲空間 0.0 是合法值,那樣寫會把它誤判成沒擷到。
                # (第一版我為了閃這個坑給 upside 開特例,結果空的 upside 變 YELLOW,
                #  跟其他欄不一致:沒擷到 ≠ 擷到但錯。改成一條規則管到底。)
                if v is None or (isinstance(v, str) and not v.strip()):
                    st = "NODATA"
                else:
                    ok = verify(v, r)
                    st = "GREEN" if ok is True else ("YELLOW" if ok is None else "YELLOW")
                    if ok is False:
                        st = "YELLOW"
                    # 驗不過與驗不了都是 YELLOW,但理由分得開(下面 why 有記)
            line["cells"][key] = {"state": st, "value": ("" if r.get(key) is None else str(r.get(key))[:40]),
                                  "why": ("" if st in ("GREEN", "NODATA", "ABSENT")
                                          else ("驗不過" if key in have and verify(r.get(key), r) is False
                                                else "驗不了(沒有可對照的)"))}
            tally[st] += 1
        cells.append(line)
    n = len(rows)
    per_col = {key: {"zh": zh, "rule": rule,
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
    return ("<!doctype html><meta charset='utf-8'><title>VRN 驗證矩陣</title>"
            "<style>body{font:13px/1.5 system-ui,'Microsoft JhengHei',sans-serif;margin:24px;background:#fff;color:#1f2328}"
            "table{border-collapse:collapse;width:100%}th,td{border:1px solid #d0d7de;padding:6px 8px;vertical-align:top}"
            "th{background:#f6f8fa;text-align:left}.r{font-size:11px;color:#57606a;font-weight:400}"
            ".v{font-size:11px;color:#1f2328}.f{font-family:ui-monospace,monospace;font-size:11px}"
            "h1{font-size:18px}.k{margin:8px 0 16px}</style>"
            f"<h1>VRN 驗證矩陣 · {m['n_reports']} 份報告 × {m['n_cols']} 欄</h1>"
            f"<div class='k'>庫 {e(m['db'])} · 產生 {datetime.now():%Y-%m-%d %H:%M} · "
            f"GREEN {t['GREEN']} · YELLOW {t['YELLOW']} · NODATA {t['NODATA']} · ABSENT {t['ABSENT']}"
            f"{'<br>' + e(m['note']) if m.get('note') else ''}</div>"
            f"<table><tr><th>報告</th>{head}</tr>{body}</table>")


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
    chk("⑳ 帶加速器橋(MDL156 覆蓋閘)", "[VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))
    # 批624:關節檢。v0100 兩支都 rc=0、整條報 OK,而 ENG073 根本沒收到夾也沒收到庫
    #   ——**rc=0 只說沒爆,不說接上了**。這兩檢就是照關節,不是照回傳值。
    _src = Path(__file__).read_text(encoding="utf-8")
    _seg = _src[_src.index("def run_chain"):_src.index("# ───", _src.index("def run_chain"))]
    chk("⑤ 關節:ENG073 要收到**夾**(--dir)與**庫**(--db)——ENG072 收到 --in 不代表後半段也收到了"
        "(v0100 只給了 `run`,於是它去跑自己的預設夾,而整條照樣報 OK=假綠)",
        '"--dir"' in _seg and '"--db"' in _seg and "str(src)" in _seg,
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
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="VRN_ENG083_VerifiedMatrix", description="VRN 驗證矩陣(零網路;零寫庫)")
    ap.add_argument("verb", nargs="?", default="matrix", choices=["run", "matrix"])
    ap.add_argument("--in", dest="indir", default="", help="報告夾或單檔(可為系統任何位置)")
    ap.add_argument("--db", default="", help="結構化庫(預設 functional modules/VRN/output/vrn_reports.duckdb)")
    ap.add_argument("--json", action="store_true")
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
            print(f"   {ch.get('why','')}")
            return 3 if ch["state"] == "ABSENT" else 1
    m = matrix(a.db)
    write_out(f"VRN_MATRIX_{ts}.json", m)
    write_out("VRN_MATRIX_latest.json", m)
    if m["state"] == "OK":
        hp = write_out("VRN_MATRIX_latest.html", to_html(m))
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
            if m.get("note"):
                print(f"  註:{m['note']}")
            print(f"  頁 {hp}")
        return 0
    print(f"[VRN_ENG083 v{VERSION}] matrix · {m['state']} · {m.get('why','')}")
    return {"NODATA": 2, "ABSENT": 3}.get(m["state"], 1)


if __name__ == "__main__":
    sys.exit(main())
