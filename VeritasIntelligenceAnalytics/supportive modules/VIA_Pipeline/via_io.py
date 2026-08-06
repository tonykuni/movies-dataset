#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_io.py  —  VIA 統一 I/O 與編碼層
================================================================================
解決 Windows / 繁體中文 的編碼亂碼,並把輸入(themes dict/list JSON、運行期資料)
與輸出(JSON / Parquet / CSV / DuckDB / Google Sheet)統一掉。

編碼政策(根因:Excel 預設系統 ANSI=cp950/Big5,而 pandas/Parquet/DuckDB/Sheets/Web
皆 UTF-8 → 不一致就亂碼):
  • 一律以 UTF-8 儲存。
  • JSON 一律 ensure_ascii=False、encoding='utf-8'(否則中文變 \\uXXXX)。
  • 給人看、會用 Excel 打開的 CSV → 寫 UTF-8-with-BOM(utf-8-sig),Excel 才認得 UTF-8。
  • Parquet / DuckDB / Google Sheet 原生 UTF-8,無須 BOM。
  • 讀檔自動級聯:utf-8-sig → utf-8 → cp950 → big5 → latin-1。
  • PowerShell 7 預設 UTF-8(無 BOM);Export/Out-File 請加 -Encoding utf8;要進 Excel 用本層的 BOM CSV。

依賴:pandas(必要);pyarrow(parquet)、duckdb、gspread+google-auth(各自選用,缺了會跳過並提示)。
執行自檢:python via_io.py --selftest      # 繁中往返所有格式,驗證不亂碼
"""
import sys, json, argparse, datetime as dt
from pathlib import Path
import pandas as pd

READ_ENCODINGS = ["utf-8-sig", "utf-8", "cp950", "big5", "latin-1"]


# ── 輸入:themes(dict 或 list 的 JSON)→ 正規化 {theme: [tickers]} ───────────
def load_themes(src):
    """src 可為:.json 路徑 / dict / list。回正規化 dict[str, list[str]]。
    支援形態:
      {"CPO":["2330","3008"], ...}
      [{"name":"CPO","members":["2330",...]}, ...]
      [["CPO","2330","3008"], ["BBU","1234"]]
      ["2330","2454"]                     → {"GROUP":[...]}(無題材的扁平清單)
    """
    if isinstance(src, (str, Path)):
        src = read_json(src)
    out = {}
    if isinstance(src, dict):
        for k, v in src.items():
            out[str(k)] = [str(x) for x in (v if isinstance(v, (list, tuple)) else [v])]
    elif isinstance(src, list):
        if src and isinstance(src[0], dict):                       # [{name, members}]
            for d in src:
                name = str(d.get("name") or d.get("theme") or d.get("group"))
                mem = d.get("members") or d.get("tickers") or d.get("list") or []
                out[name] = [str(x) for x in mem]
        elif src and isinstance(src[0], (list, tuple)):            # [["name","t1",...]]
            for row in src:
                out[str(row[0])] = [str(x) for x in row[1:]]
        else:                                                      # 扁平 ["2330",...]
            out["GROUP"] = [str(x) for x in src]
    else:
        raise ValueError("themes 形態不支援(需 dict / list / json 路徑)")
    out = {k: v for k, v in out.items() if v}
    if not out:
        raise ValueError("themes 解析後為空")
    return out


# ── 讀:JSON / 表格(csv/parquet/json/duckdb),自動處理編碼 ──────────────────
def read_json(path):
    p = Path(path)
    for enc in READ_ENCODINGS:
        try:
            return json.loads(p.read_text(encoding=enc))
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise UnicodeError(f"{path}:所有編碼皆無法解碼 {READ_ENCODINGS}")


def _read_csv_smart(path, **kw):
    last = None
    for enc in READ_ENCODINGS:
        try:
            df = pd.read_csv(path, encoding=enc, **kw)
            print(f"   [io] CSV 以 {enc} 讀入:{path}")
            return df
        except (UnicodeDecodeError, UnicodeError) as e:
            last = e
    raise UnicodeError(f"{path}:CSV 無法以 {READ_ENCODINGS} 解碼:{last}")


def read_table(src, index_col=0, parse_dates=True, **kw):
    """src 副檔名分流;DuckDB 用 'file.duckdb::table' 或 'file.duckdb::SELECT ...'。"""
    s = str(src)
    if "::" in s and s.split("::")[0].endswith((".duckdb", ".db")):
        dbf, q = s.split("::", 1)
        try:
            import duckdb
        except ImportError:
            raise RuntimeError("讀 DuckDB 需 pip install duckdb")
        con = duckdb.connect(dbf, read_only=True)
        sql = q if q.strip().lower().startswith("select") else f"SELECT * FROM {q}"
        df = con.execute(sql).fetch_df(); con.close()
        return df
    ext = Path(s).suffix.lower()
    if ext in (".parquet", ".pq"):
        return pd.read_parquet(s)                                  # pyarrow 原生 UTF-8
    if ext == ".json":
        return pd.DataFrame(read_json(s))
    # 預設 CSV
    return _read_csv_smart(s, index_col=index_col, parse_dates=parse_dates, **kw)


# ── 寫:JSON / CSV / Parquet / DuckDB / Google Sheet(編碼統一) ──────────────
def write_json(obj, path):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2,
                                     default=str), encoding="utf-8")
    return str(path)


def write_csv(df, path, for_excel=True):
    """for_excel=True → utf-8-sig(BOM),Excel 雙擊正確顯示繁中;False → 純 utf-8。"""
    enc = "utf-8-sig" if for_excel else "utf-8"
    df.to_csv(path, encoding=enc, index=True)
    return str(path)


def write_parquet(df, path):
    try:
        df.to_parquet(path, index=True)                            # 需 pyarrow
        return str(path)
    except Exception as e:
        print(f"   [io] 跳過 Parquet(需 pip install pyarrow):{e}")
        return None


def write_duckdb(df, path, table="via_output"):
    try:
        import duckdb
    except ImportError:
        print("   [io] 跳過 DuckDB(需 pip install duckdb)"); return None
    con = duckdb.connect(str(path))
    con.register("_df", df.reset_index())
    con.execute(f'CREATE OR REPLACE TABLE "{table}" AS SELECT * FROM _df')
    con.close()
    return f"{path}::{table}"


def to_gsheet(df, spreadsheet, worksheet="Sheet1", creds_json=None):
    """Google Sheet 透過 API 原生 UTF-8(傳 Python str 即可,無編碼問題)。
    需:pip install gspread google-auth;creds_json=服務帳戶金鑰路徑,並把試算表分享給該帳戶 email。"""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        print("   [io] 跳過 Google Sheet(需 pip install gspread google-auth)"); return None
    if not creds_json:
        print("   [io] 跳過 Google Sheet:未提供 creds_json 服務帳戶金鑰"); return None
    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
    gc = gspread.authorize(Credentials.from_service_account_file(creds_json, scopes=scopes))
    sh = gc.open_by_key(spreadsheet) if len(str(spreadsheet)) > 30 else gc.open(spreadsheet)
    try:
        ws = sh.worksheet(worksheet)
    except Exception:
        ws = sh.add_worksheet(worksheet, rows=str(len(df) + 10), cols=str(len(df.columns) + 5))
    d = df.reset_index()
    ws.clear()
    ws.update([list(map(str, d.columns))] + d.astype(object).where(pd.notna(d), "").values.tolist())
    return f"gsheet://{spreadsheet}/{worksheet}"


def export_all(df, basepath, formats=("json", "csv", "parquet", "duckdb"),
               for_excel=True, duckdb_table="via_output", gsheet=None):
    """df → 多格式;basepath 不含副檔名。gsheet=dict(spreadsheet,worksheet,creds_json)。"""
    base = Path(basepath); base.parent.mkdir(parents=True, exist_ok=True)
    written = {}
    if "json" in formats:
        written["json"] = write_json(
            {"columns": list(df.columns), "index": [str(i) for i in df.index],
             "records": df.reset_index().astype(object).where(pd.notna(df.reset_index()), None).to_dict("records")},
            base.with_suffix(".json"))
    if "csv" in formats:
        written["csv"] = write_csv(df, base.with_suffix(".csv"), for_excel)
    if "parquet" in formats:
        written["parquet"] = write_parquet(df, base.with_suffix(".parquet"))
    if "duckdb" in formats:
        written["duckdb"] = write_duckdb(df, base.with_suffix(".duckdb"), duckdb_table)
    if gsheet:
        written["gsheet"] = to_gsheet(df, **gsheet)
    return {k: v for k, v in written.items() if v}


# ── 編碼自檢:繁中往返所有格式 ───────────────────────────────────────────────
def encoding_selftest(tmp="/tmp/via_io_selftest"):
    df = pd.DataFrame(
        {"族群": ["共封裝光學", "電池備援", "散熱液冷"],
         "領導者": ["台積電", "技嘉", "奇鋐"],
         "角色": ["領導者", "同業", "落後者"],
         "rs": [12.3, -4.5, 0.0]},
    ).set_index("族群")
    print("原始繁中樣本:\n", df, "\n")
    Path(tmp).parent.mkdir(parents=True, exist_ok=True)
    paths = export_all(df, tmp, for_excel=True)
    print("寫出:", paths, "\n")
    ok = {}
    # JSON
    j = read_json(Path(tmp).with_suffix(".json"))
    ok["json"] = "台積電" in json.dumps(j, ensure_ascii=False)
    # CSV(utf-8-sig)
    d2 = _read_csv_smart(Path(tmp).with_suffix(".csv"), index_col=0)
    ok["csv_utf8sig"] = "奇鋐" in "".join(map(str, d2.values.ravel())) and "領導者" in "".join(d2.columns) + str(d2.index.name)
    # Parquet
    pq = Path(tmp).with_suffix(".parquet")
    ok["parquet"] = (pq.exists() and "技嘉" in "".join(map(str, pd.read_parquet(pq).values.ravel()))) if pq.exists() else None
    # DuckDB
    try:
        import duckdb
        dbf = Path(tmp).with_suffix(".duckdb")
        if dbf.exists():
            con = duckdb.connect(str(dbf), read_only=True)
            txt = "".join(map(str, con.execute('SELECT * FROM via_output').fetch_df().values.ravel()))
            con.close(); ok["duckdb"] = "散熱液冷" in txt
    except ImportError:
        ok["duckdb"] = None
    print("往返驗證(True=繁中保留,None=未安裝該套件略過):")
    for k, v in ok.items():
        print(f"   {k:14s} {'PASS' if v else ('skip' if v is None else 'FAIL')}")
    bad = [k for k, v in ok.items() if v is False]
    print("\n結論:", "全部格式繁中無亂碼 ✓" if not bad else f"有亂碼:{bad}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--themes", help="themes json 路徑;印出正規化結果")
    a = ap.parse_args()
    if a.themes:
        print(json.dumps(load_themes(a.themes), ensure_ascii=False, indent=2))
    if a.selftest or not a.themes:
        encoding_selftest()


if __name__ == "__main__":
    main()
