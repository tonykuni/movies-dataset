#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_Publish v0100 — 三本輸出冊的發布層:累計(只增不減 · 去重保留最新)→ parquet / CSV / Google Sheet → 雲端硬碟同步夾。

設計(操作員 2026-10-27):
① 累計:每輪輸出冊併入 publish/cumulative/<冊>.parquet · 主鍵去重(BasicInfo / Summary = FILENAME · FinancialData = FILENAME|ITEM|PERIOD_STD|PAGE|ZONE)· 保留最新 RUN_TS · 原值不刪
② 批次 + TEMP:duckdb 做合併去重(temp_directory = %TEMP%\\VIA_progress\\vrn2_publish · memory_limit 可設)· parquet 以 row group 分批寫 · 大於批次列數的 CSV 分批追加 · 記憶體不足自動溢寫
③ 格式提醒:CSV 用 UTF-8 BOM(Excel 直接開中文不亂碼)· 列數超過 Excel 上限 1,048,576 提醒 · Google Sheet 一張試算表 1,000 萬格上限 · 單次寫入分批 ≤ batch_rows
④ 雲端:自動偵測同步夾(OneDrive · Google Drive 桌面版 · Dropbox · iCloud)→ 複製累計檔到 <同步夾>\\VIA_VRN2_Publish\\ · VIA 根本來就在 OneDrive 內則已自動同步
⑤ Google Sheet:gspread + 服務帳戶 JSON(最少人工:① 建服務帳戶下載 JSON ② 把試算表分享給該帳戶 email ③ 在 U/I 選檔 + 貼網址)· 憑證自動在常見位置找 · 缺套件 / 缺憑證 / 沒分享 → 一行說明不猜
動詞:--publish [--v2 <夾>] [--dry] · --probe · --test · --config key=value … · --selftest
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import shutil
import sys
from pathlib import Path

VERSION = "v0100"
HERE = Path(__file__).resolve().parent
BOOKS = {"BasicInfo": ["FILENAME"], "Summary": ["FILENAME"], "FinancialData": ["FILENAME", "ITEM", "PERIOD_STD", "PAGE", "ZONE"]}
LIMITS = {"excel_rows": 1048576, "sheet_cells": 10000000, "sheet_batch_rows": 20000}
DEFAULT_CFG = {"book": "VRN2_Publish_Config", "version": "v0100", "formats": {"parquet": True, "csv": True, "google_sheet": False},
               "csv_encoding": "utf-8-sig", "batch_rows": 50000, "memory_limit": "512MB",
               "cloud": {"auto_detect": True, "extra_folders": [], "subfolder": "VIA_VRN2_Publish"},
               "google": {"credentials_json": "", "spreadsheet": "", "worksheet_prefix": "VRN2_", "mode": "append_dedup"},
               "last_result": {}}


def cfg_path() -> Path:
    return HERE / "SSOT" / "VRN2_Publish_Config_v0100.json"


def load_cfg() -> dict:
    p = cfg_path()
    if p.exists():
        try:
            c = json.loads(p.read_text(encoding="utf-8"))
            for k, v in DEFAULT_CFG.items():
                c.setdefault(k, v)
            return c
        except Exception:  # noqa: BLE001
            pass
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(DEFAULT_CFG, ensure_ascii=False, indent=1), encoding="utf-8")
    return json.loads(json.dumps(DEFAULT_CFG))


def save_cfg(c: dict) -> None:
    cfg_path().write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")


def set_cfg(pairs: list) -> dict:
    c = load_cfg()
    for kv in pairs:
        k, _, v = kv.partition("=")
        node = c; parts = k.split(".")
        for pk in parts[:-1]:
            node = node.setdefault(pk, {})
        node[parts[-1]] = {"true": True, "false": False}.get(v.lower(), v) if isinstance(v, str) else v
    save_cfg(c)
    return c


def temp_dir() -> Path:
    t = Path(os.environ.get("TEMP") or os.environ.get("TMP") or "/tmp") / "VIA_progress" / "vrn2_publish"
    t.mkdir(parents=True, exist_ok=True)
    return t


def detect_sync_folders(extra: list = None) -> list:
    home = Path(os.environ.get("USERPROFILE", str(Path.home())))
    cands = [("OneDrive", os.environ.get("OneDrive")), ("OneDrive", os.environ.get("OneDriveConsumer")), ("OneDrive 公司", os.environ.get("OneDriveCommercial")),
             ("Google Drive", "G:\\My Drive"), ("Google Drive", "G:\\我的雲端硬碟"), ("Google Drive", str(home / "Google Drive")), ("Google Drive", str(home / "My Drive")),
             ("Dropbox", str(home / "Dropbox")), ("iCloud", str(home / "iCloudDrive"))]
    out, seen = [], set()
    for kind, p in cands + [("自訂", x) for x in (extra or [])]:
        if p and Path(p).is_dir() and str(Path(p)).lower() not in seen:
            seen.add(str(Path(p)).lower()); out.append({"kind": kind, "path": str(Path(p))})
    return out


def find_credentials(cfg: dict) -> str:
    g = cfg.get("google") or {}
    if g.get("credentials_json") and Path(g["credentials_json"]).is_file():
        return g["credentials_json"]
    home = Path(os.environ.get("USERPROFILE", str(Path.home())))
    for p in [home / ".config" / "gspread" / "service_account.json", home / "AppData" / "Roaming" / "gspread" / "service_account.json"] + sorted((HERE.parent.parent / "secrets").glob("*.json") if (HERE.parent.parent / "secrets").is_dir() else []) + sorted((HERE / "secrets").glob("*.json") if (HERE / "secrets").is_dir() else []):
        try:
            if p.is_file() and json.loads(p.read_text(encoding="utf-8")).get("type") == "service_account":
                return str(p)
        except Exception:  # noqa: BLE001
            pass
    return ""


def _read_book(od: Path, name: str):
    import pandas as pd
    pq = od / ("VRN2_%s_latest.parquet" % name); js = od / ("VRN2_%s_latest.json" % name)
    if pq.exists():
        return pd.read_parquet(pq)
    if js.exists():
        rows = json.loads(js.read_text(encoding="utf-8"))
        return pd.DataFrame([{k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v) for k, v in r.items()} for r in rows])
    return None


def cumulate(v2: Path, cfg: dict, dry: bool = False) -> dict:
    """① ② 累計去重(duckdb · TEMP 溢寫)→ parquet(分批 row group)+ CSV(UTF-8 BOM · 分批追加)。"""
    import pandas as pd
    od = v2 / "output"; cd = v2 / "publish" / "cumulative"; cd.mkdir(parents=True, exist_ok=True)
    run_ts = _dt.datetime.now().isoformat(timespec="seconds")
    res, warns = {}, []
    try:
        import duckdb
    except Exception:  # noqa: BLE001
        duckdb = None
    for name, keys in BOOKS.items():
        df = _read_book(od, name)
        if df is None or not len(df):
            res[name] = {"new": 0, "total": None, "note": "本輪無此冊"}; continue
        df = df.copy(); df["RUN_TS"] = run_ts
        for k in keys:
            if k not in df.columns:
                df[k] = ""
        df = df.astype({c: "string" for c in df.columns if df[c].dtype == object})
        cum = cd / ("%s.parquet" % name)
        tmp = temp_dir() / ("%s_new_%s.parquet" % (name, os.getpid()))
        df.to_parquet(tmp, index=False)
        keyexpr = " || '|' || ".join("coalesce(cast(%s as varchar), '')" % k for k in keys)
        total = None
        if dry:
            res[name] = {"new": len(df), "total": "(dry)", "keys": keys}; continue
        if duckdb is not None:
            con = duckdb.connect()
            con.execute("SET temp_directory='%s'" % str(temp_dir()).replace("'", "''")); con.execute("SET memory_limit='%s'" % cfg.get("memory_limit", "512MB"))
            src = "read_parquet(['%s','%s'], union_by_name=true)" % (str(cum).replace("'", "''"), str(tmp).replace("'", "''")) if cum.exists() else "read_parquet('%s')" % str(tmp).replace("'", "''")
            out_tmp = temp_dir() / ("%s_merged_%s.parquet" % (name, os.getpid()))
            con.execute("COPY (SELECT * EXCLUDE(_k, _rn) FROM (SELECT *, %s AS _k, row_number() OVER (PARTITION BY %s ORDER BY RUN_TS DESC) AS _rn FROM %s) WHERE _rn = 1) TO '%s' (FORMAT PARQUET, ROW_GROUP_SIZE %d)" % (keyexpr, keyexpr, src, str(out_tmp).replace("'", "''"), int(cfg.get("batch_rows", 50000))))
            total = con.execute("SELECT count(*) FROM read_parquet('%s')" % str(out_tmp).replace("'", "''")).fetchone()[0]
            con.close()
            shutil.move(str(out_tmp), str(cum))
        else:                                                                 # 沒 duckdb:pandas 分批(小量可用)
            old = pd.read_parquet(cum) if cum.exists() else None
            allv = pd.concat([old, df], ignore_index=True) if old is not None else df
            allv = allv.sort_values("RUN_TS").drop_duplicates(subset=keys, keep="last")
            allv.to_parquet(cum, index=False); total = len(allv)
        if cfg.get("formats", {}).get("csv", True):
            csvp = cd / ("%s.csv" % name)
            n = 0
            if duckdb is not None:
                con = duckdb.connect(); con.execute("SET temp_directory='%s'" % str(temp_dir()).replace("'", "''"))
                rdr = con.execute("SELECT * FROM read_parquet('%s')" % str(cum).replace("'", "''"))
                first = True
                while True:
                    chunk = rdr.fetch_df_chunk(int(cfg.get("batch_rows", 50000)) // 1024 + 1)
                    if chunk is None or not len(chunk):
                        break
                    chunk.to_csv(csvp, mode="w" if first else "a", header=first, index=False, encoding=cfg.get("csv_encoding", "utf-8-sig")); first = False; n += len(chunk)
                con.close()
            else:
                pd.read_parquet(cum).to_csv(csvp, index=False, encoding=cfg.get("csv_encoding", "utf-8-sig")); n = total
            if total and total > LIMITS["excel_rows"]:
                warns.append("%s 累計 %d 列超過 Excel 上限 %d · CSV 仍完整 · Excel 開啟會截斷 · 請用 parquet / Power Query" % (name, total, LIMITS["excel_rows"]))
        res[name] = {"new": len(df), "total": total, "keys": keys, "parquet": str(cum)}
        try:
            tmp.unlink()
        except OSError:
            pass
    warns.append("CSV 編碼 UTF-8 BOM(Excel 直開中文不亂碼 · 舊系統若只收 Big5 需另轉)")
    return {"run_ts": run_ts, "books": res, "warnings": warns}


def push_cloud(v2: Path, cfg: dict, dry: bool = False) -> dict:
    cd = v2 / "publish" / "cumulative"
    cl = cfg.get("cloud") or {}
    folders = detect_sync_folders(cl.get("extra_folders")) if cl.get("auto_detect", True) else [{"kind": "自訂", "path": p} for p in cl.get("extra_folders") or []]
    done, note = [], []
    root = HERE.parent.parent
    inside = [f for f in folders if str(root).lower().startswith(f["path"].lower())]
    if inside:
        note.append("VIA 根在 %s 內 · 累計檔已自動同步(不另複製)" % inside[0]["kind"])
    for f in folders:
        if f in inside:
            continue
        dst = Path(f["path"]) / cl.get("subfolder", "VIA_VRN2_Publish")
        if dry:
            done.append({"kind": f["kind"], "to": str(dst), "dry": True}); continue
        try:
            dst.mkdir(parents=True, exist_ok=True)
            n = 0
            for p in cd.glob("*.*"):
                shutil.copy2(str(p), str(dst / p.name)); n += 1
            done.append({"kind": f["kind"], "to": str(dst), "files": n})
        except Exception as exc:  # noqa: BLE001
            done.append({"kind": f["kind"], "to": str(dst), "error": type(exc).__name__})
    if not folders:
        note.append("沒偵測到同步夾(OneDrive / Google Drive 桌面版 / Dropbox / iCloud)· 安裝任一桌面同步程式後會自動接上")
    return {"folders": folders, "copied": done, "notes": note}


def push_sheet(v2: Path, cfg: dict, dry: bool = False, client=None) -> dict:
    """⑤ Google Sheet:服務帳戶 · 去重追加 · 分批 · 格數上限檢查。client 可注入(自測)。"""
    import pandas as pd
    g = cfg.get("google") or {}
    if not (cfg.get("formats") or {}).get("google_sheet"):
        return {"status": "OFF", "note": "google_sheet 未啟用(U/I 發布設定勾選後啟用)"}
    sheet = (g.get("spreadsheet") or "").strip()
    if not sheet:
        return {"status": "NEED_INPUT", "note": "缺試算表網址或 ID(U/I 發布設定貼上)"}
    cred = find_credentials(cfg)
    if not cred and client is None:
        return {"status": "NEED_INPUT", "note": "缺服務帳戶憑證 JSON · 三步:① Google Cloud 建服務帳戶並下載 JSON ② 把試算表「共用」給該帳戶 email(JSON 裡 client_email)③ U/I 發布設定「選擇憑證檔」"}
    if client is None:
        try:
            import gspread
        except Exception:  # noqa: BLE001
            return {"status": "NEED_LIB", "note": "缺 gspread 套件(pip gspread · 交 VCGC 安裝)"}
        try:
            client = gspread.service_account(filename=cred)
        except Exception as exc:  # noqa: BLE001
            return {"status": "AUTH_FAIL", "note": "憑證讀取失敗 %s" % type(exc).__name__}
    m = re.search(r"/d/([A-Za-z0-9_-]{20,})", sheet)
    sid = m.group(1) if m else sheet
    try:
        ss = client.open_by_key(sid)
    except Exception as exc:  # noqa: BLE001
        return {"status": "OPEN_FAIL", "note": "打不開試算表 %s(多半是沒分享給服務帳戶 email · 或 ID 錯)" % type(exc).__name__}
    cd = v2 / "publish" / "cumulative"
    out = {"status": "OK", "sheets": {}}
    cells_total = 0
    for name, keys in BOOKS.items():
        p = cd / ("%s.parquet" % name)
        if not p.exists():
            continue
        df = pd.read_parquet(p).fillna("").astype(str)
        title = (g.get("worksheet_prefix") or "VRN2_") + name
        try:
            ws = ss.worksheet(title)
        except Exception:  # noqa: BLE001
            ws = None if dry else ss.add_worksheet(title=title, rows=max(100, len(df) + 10), cols=max(26, len(df.columns)))
        existing = []
        if ws is not None:
            try:
                existing = ws.get_all_values()
            except Exception:  # noqa: BLE001
                existing = []
        hdr = list(df.columns)
        key_of = lambda r: "|".join(str(r.get(k, "")) for k in keys)
        have = set()
        if existing and existing[0]:
            idx = {c: i for i, c in enumerate(existing[0])}
            for r in existing[1:]:
                have.add("|".join((r[idx[k]] if k in idx and idx[k] < len(r) else "") for k in keys))
        rows = [[r[c] for c in hdr] for r in df.to_dict("records") if key_of(r) not in have]
        cells = (len(rows) + (0 if existing else 1)) * len(hdr)
        cells_total += cells + sum(len(x) for x in existing)
        if cells_total > LIMITS["sheet_cells"]:
            out["sheets"][name] = {"appended": 0, "skipped_dup": len(df) - len(rows), "note": "超過 Google Sheet 1,000 萬格上限 · 停止 · 請改用 parquet 或另開試算表"}; out["status"] = "LIMIT"; break
        if dry or ws is None:
            out["sheets"][name] = {"would_append": len(rows), "skipped_dup": len(df) - len(rows), "dry": True}; continue
        if not existing:
            ws.append_row(hdr, value_input_option="RAW")
        bs = int(LIMITS["sheet_batch_rows"])
        for i in range(0, len(rows), bs):
            ws.append_rows(rows[i:i + bs], value_input_option="RAW")
        out["sheets"][name] = {"appended": len(rows), "skipped_dup": len(df) - len(rows), "batches": (len(rows) + bs - 1) // bs}
    return out


def publish(v2: Path, dry: bool = False, client=None) -> dict:
    cfg = load_cfg()
    r = {"version": VERSION, "ts": _dt.datetime.now().isoformat(timespec="seconds"), "dry": dry}
    r["cumulative"] = cumulate(v2, cfg, dry)
    r["cloud"] = push_cloud(v2, cfg, dry)
    r["google_sheet"] = push_sheet(v2, cfg, dry, client)
    cfg["last_result"] = {"ts": r["ts"], "books": {k: v.get("total") for k, v in r["cumulative"]["books"].items()}, "cloud": [c.get("kind") for c in r["cloud"]["copied"]], "google_sheet": r["google_sheet"].get("status"), "note": r["google_sheet"].get("note", "")}
    save_cfg(cfg)
    (v2 / "publish").mkdir(parents=True, exist_ok=True)
    (v2 / "publish" / "VRN2_Publish_latest.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    return r


def probe(v2: Path) -> dict:
    cfg = load_cfg()
    try:
        import gspread  # noqa: F401
        gs = "已裝"
    except Exception:  # noqa: BLE001
        gs = "未裝(交 VCGC:pip gspread)"
    try:
        import duckdb  # noqa: F401
        dk = "已裝"
    except Exception:  # noqa: BLE001
        dk = "未裝(退回 pandas 小量模式)"
    cred = find_credentials(cfg)
    return {"formats": cfg.get("formats"), "sync_folders": detect_sync_folders((cfg.get("cloud") or {}).get("extra_folders")), "gspread": gs, "duckdb": dk, "credentials": cred or "未找到", "spreadsheet": (cfg.get("google") or {}).get("spreadsheet") or "未填", "config": str(cfg_path()), "temp": str(temp_dir()), "last_result": cfg.get("last_result")}


class _FakeWS:
    def __init__(self, rows=None):
        self.rows = rows or []
    def get_all_values(self):
        return self.rows
    def append_row(self, r, **k):
        self.rows.append(list(r))
    def append_rows(self, rs, **k):
        self.rows.extend(list(x) for x in rs)


class _FakeSS:
    def __init__(self):
        self.ws = {}
    def worksheet(self, t):
        if t not in self.ws:
            raise KeyError(t)
        return self.ws[t]
    def add_worksheet(self, title, rows, cols):
        self.ws[title] = _FakeWS(); return self.ws[title]


class _FakeClient:
    def __init__(self):
        self.ss = _FakeSS()
    def open_by_key(self, k):
        return self.ss


def selftest() -> int:
    import tempfile
    import pandas as pd
    global HERE
    ok = 0
    td = Path(tempfile.mkdtemp()); HERE = td / "VRN"; (HERE / "SSOT").mkdir(parents=True)
    v2 = td / "v2"; od = v2 / "output"; od.mkdir(parents=True)
    pd.DataFrame([{"FILENAME": "a.pdf", "TICKER": "2330", "STATUS": "x"}, {"FILENAME": "b.pdf", "TICKER": "2317", "STATUS": "y"}]).to_parquet(od / "VRN2_BasicInfo_latest.parquet", index=False)
    pd.DataFrame([{"FILENAME": "a.pdf", "ITEM": "營收", "PERIOD_STD": "2025", "PAGE": 6, "ZONE": "P6·F·03·TB", "VALUE_NUM": 1.0}]).to_parquet(od / "VRN2_FinancialData_latest.parquet", index=False)
    r1 = publish(v2, dry=False, client=None)
    pd.DataFrame([{"FILENAME": "a.pdf", "TICKER": "2330", "STATUS": "x2"}, {"FILENAME": "c.pdf", "TICKER": "6488", "STATUS": "z"}]).to_parquet(od / "VRN2_BasicInfo_latest.parquet", index=False)
    r2 = publish(v2, dry=False, client=None)
    cum = pd.read_parquet(v2 / "publish" / "cumulative" / "BasicInfo.parquet")
    a = r1["cumulative"]["books"]["BasicInfo"]["total"] == 2 and r2["cumulative"]["books"]["BasicInfo"]["total"] == 3 and cum[cum.FILENAME == "a.pdf"].STATUS.iloc[0] == "x2" and (v2 / "publish" / "cumulative" / "BasicInfo.csv").read_bytes()[:3] == b"\xef\xbb\xbf"
    print("  [%s] 累計去重:第一輪 2 · 第二輪 3(a.pdf 更新為最新 · 原 b 保留)· CSV UTF-8 BOM" % ("OK" if a else "FAIL")); ok += int(a)
    b = any("Excel" in w or "BOM" in w for w in r2["cumulative"]["warnings"]) and r2["google_sheet"]["status"] == "OFF"
    print("  [%s] 格式提醒與 Google Sheet 預設關閉 %s" % ("OK" if b else "FAIL", r2["google_sheet"]["status"])); ok += int(b)
    cfg = set_cfg(["formats.google_sheet=true", "google.spreadsheet=https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789/edit"])
    fc = _FakeClient()
    s1 = push_sheet(v2, cfg, dry=False, client=fc); s2 = push_sheet(v2, cfg, dry=False, client=fc)
    c = s1["status"] == "OK" and s1["sheets"]["BasicInfo"]["appended"] == 3 and s2["sheets"]["BasicInfo"]["appended"] == 0 and s2["sheets"]["BasicInfo"]["skipped_dup"] == 3 and len(fc.ss.ws["VRN2_BasicInfo"].rows) == 4
    print("  [%s] Google Sheet(模擬):第一次追加 3 · 第二次全為重複 0 · 表頭 + 3 列" % ("OK" if c else "FAIL")); ok += int(c)
    cfg2 = set_cfg(["google.spreadsheet="]); s3 = push_sheet(v2, cfg2, client=None)
    d = s3["status"] == "NEED_INPUT"
    print("  [%s] 缺輸入時明說(NEED_INPUT · 不猜):%s" % ("OK" if d else "FAIL", s3["note"][:40])); ok += int(d)
    e = isinstance(probe(v2)["sync_folders"], list)
    print("  [%s] 探測同步夾 / 套件 / 憑證" % ("OK" if e else "FAIL")); ok += int(e)
    print("[計] VRN2_Publish %s 自測 %d/5 · %s" % (VERSION, ok, "PASS" if ok == 5 else "FAIL"))
    return 0 if ok == 5 else 1


def main(argv: list) -> int:
    def opt(k, d=None):
        return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    v2 = Path(opt("--v2", str(HERE.parent.parent / "VIA_Reports" / "vrn2")))
    if "--selftest" in argv:
        return selftest()
    if "--config" in argv:
        pairs = [a for a in argv[argv.index("--config") + 1:] if "=" in a and not a.startswith("--")]
        c = set_cfg(pairs); print("[計] 發布設定已更新 %s → %s" % (pairs, cfg_path())); return 0
    if "--probe" in argv or "--test" in argv:
        p = probe(v2)
        print("[計] 發布探測 · 格式 %s · 同步夾 %s · gspread %s · duckdb %s · 憑證 %s · 試算表 %s · 上次 %s" % (p["formats"], " / ".join("%s:%s" % (f["kind"], f["path"]) for f in p["sync_folders"]) or "無", p["gspread"], p["duckdb"], p["credentials"], p["spreadsheet"], p["last_result"]))
        if "--test" in argv:
            r = publish(v2, dry=True)
            print("[計] 發布試跑(dry)· 累計 %s · 雲端 %s · Google Sheet %s %s" % ({k: v.get("new") for k, v in r["cumulative"]["books"].items()}, [c.get("to") for c in r["cloud"]["copied"]], r["google_sheet"].get("status"), r["google_sheet"].get("note", "")[:120]))
        return 0
    if "--publish" in argv:
        r = publish(v2, dry="--dry" in argv)
        print("[計] 發布 · 累計 %s · 雲端 %s · Google Sheet %s %s · 提醒 %s" % ({k: (v.get("new"), v.get("total")) for k, v in r["cumulative"]["books"].items()}, [c.get("kind") for c in r["cloud"]["copied"]] or r["cloud"]["notes"], r["google_sheet"].get("status"), r["google_sheet"].get("note", "")[:100], " / ".join(r["cumulative"]["warnings"])[:200]))
        return 0
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
