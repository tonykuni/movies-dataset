#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_ENG232_TWIndexOfficial v0102 — 薄尾:櫃買指數改走櫃買中心現行官方端點 · 兩個指數各自接續 · 長區間按月寫庫並出聲。

2026-11-18 容器開閘實測(空庫):
  ① 庫裡只有加權(TAIEX),櫃買(TPEX)一列都沒有。收容件用的櫃買行情端點
     tpex.org.tw/web/stock/aftertrading/daily_market_statistics/dmsRpt.php 現在回 404 頁 → 沒有收盤 → 整列被丟。
  ② v0101 的增量起點要「兩個指數都有」才接續;櫃買永遠沒有 → 每次都從 BOOT(2023-01-01)重抓加權。
  ③ 一次抓整段、抓完才寫庫、中間不出一行;擷取系統每支 1800 秒上限一到就收掉(rc 124)→ 庫裡零列 → 下次又重來。
  三件加起來:加權、櫃買指數每日量價這一項在新機器上永遠補不完,在已有加權資料的機器上每天白抓三年。
本版(v0101 · v0100 · 收容件一字不動):
  ① 櫃買指數改抓櫃買中心現行官方端點(按月,每月 2 次請求):
       www/zh-tw/indexInfo/inx(開市 · 最高 · 最低 · 收市)+ www/zh-tw/afterTrading/tradingIndex(成交張數 · 金額(仟元))。
     單位統一成與加權相同:volume = 成交張數 × 1000(股)· turnover = 金額(仟元)× 1000(元)。外呼照舊只經統包網路工具(雙閘在工具裡)。
  ② 兩個指數各自算增量起點(各自庫內最新日的隔天;沒有的那個從 BOOT)。已有的那個不重抓。
  ③ 先抓櫃買(每月寫庫並印一行,整段一兩分鐘),再抓加權(收容件,照前版;區間超過 45 天就按月切段、每段寫庫並印一行)。
     被收掉也沒關係:下一次從庫裡最後一天的隔天接著抓。
  ④ 收容件每天還會去打已經 404 的舊端點:同一個端點這一輪從沒成功過、又連兩次拿不到 JSON,這一輪就不再打它
     (不是寫死名單;成功過的端點偶爾空一次照樣繼續打;端點恢復就自動恢復)。
不代設同意閘;不改收容件;欄位照 OUT-05。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本檔自己不連網,連網的是回補本體。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG232_TWIndexOfficial"
ENGINE_TAG = Path(__file__).stem
CHUNK_OVER_DAYS = 45
TPEX_INX = "https://www.tpex.org.tw/www/zh-tw/indexInfo/inx"
TPEX_TRD = "https://www.tpex.org.tw/www/zh-tw/afterTrading/tradingIndex"
TPEX_NOTE = "櫃買中心 indexInfo/inx + afterTrading/tradingIndex;量 = 成交張數×1000 · 值 = 金額(仟元)×1000"
DEAD_AFTER = 2


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("_vdf_eng232_prior_for_" + ENGINE_TAG, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.PRIOR                       # v0100:DB_IDX · TABLE · KEYS · _NetHttp · net_tool · count · _LIB
_PRIOR_RUN = PRIOR.run
BOOT = PRIOR.BOOT


def __getattr__(name):
    return getattr(PRIOR, name)


def month_chunks(start: str, end: str) -> list:
    """[start, end] 切成一個月一段(頭尾不重疊、不漏日)。"""
    a, b = date.fromisoformat(start), date.fromisoformat(end)
    out, cur = [], a
    while cur <= b:
        nxt = (cur.replace(day=1) + timedelta(days=32)).replace(day=1)
        last = min(b, nxt - timedelta(days=1))
        out.append((cur.isoformat(), last.isoformat()))
        cur = last + timedelta(days=1)
    return out


def starts(db=None) -> dict:
    """各指數自己的增量起點:庫內最新日的隔天;庫裡沒有 = BOOT。"""
    c = BASE.count(db or BASE.DB_IDX)
    return {k: ((date.fromisoformat(str(c[k][2])[:10]) + timedelta(days=1)).isoformat() if k in c else BOOT) for k in ("TAIEX", "TPEX")}


def _f(v):
    try:
        return None if v in (None, "", "--", "---") else float(str(v).replace(",", "").replace("+", "").strip())
    except (TypeError, ValueError):
        return None


def _iso(d: str) -> str | None:
    """西元 2023/01/03 或民國 115/11/02 → 2026-11-02。"""
    m = re.match(r"^\s*(\d{2,4})/(\d{1,2})/(\d{1,2})\s*$", str(d or ""))
    if not m:
        return None
    y = int(m.group(1))
    y = y + 1911 if y < 1911 else y
    try:
        return date(y, int(m.group(2)), int(m.group(3))).isoformat()
    except ValueError:
        return None


def _table(j: dict) -> list:
    t = (j or {}).get("tables") or []
    return (t[0].get("data") or []) if t and isinstance(t[0], dict) else []


def tpex_month_rows(http, y: int, m: int) -> list:
    """櫃買指數一個月的列(OUT-05 欄位);兩個端點任一個沒回資料就照實少欄,不假填。"""
    q = {"date": "%04d/%02d/01" % (y, m), "response": "json"}
    ohlc = {}
    for r in _table(http.get_json(TPEX_INX, q)):
        d = _iso(r[0]) if r else None
        if d and len(r) >= 5 and _f(r[4]) is not None:
            ohlc[d] = (_f(r[1]), _f(r[2]), _f(r[3]), _f(r[4]))
    vol = {}
    for r in _table(http.get_json(TPEX_TRD, q)):
        d = _iso(r[0]) if r else None
        if d and len(r) >= 5:
            lots, thousand = _f(r[1]), _f(r[2])
            vol[d] = (None if lots is None else lots * 1000.0, None if thousand is None else thousand * 1000.0, _f(r[4]))
    rows = []
    for d in sorted(ohlc):
        o, h, lo, c = ohlc[d]
        v, t, close2 = vol.get(d, (None, None, None))
        note = TPEX_NOTE if d in vol else TPEX_NOTE + ";這一天量值端點沒回"
        if close2 is not None and abs(close2 - c) > 0.011:
            note += ";兩端點收盤不同 %.2f / %.2f(取 inx)" % (c, close2)
        rows.append({"date": d, "index_code": "TPEX", "index_name": "櫃買指數", "open": o, "low": lo, "high": h, "close": c,
                     "volume": v, "turnover": t, "inst_foreign_net": None, "inst_trust_net": None, "inst_dealer_net": None,
                     "source": "TPEX 官方", "note": note})
    return rows


class _SkipDead:
    """包住前版的 get_json:同一個端點(網址不含參數)這一輪從沒成功過、又連續 DEAD_AFTER 次拿不到 JSON,這一輪就不再打。
    成功過的端點偶爾空一兩次照樣繼續打(不因為一時限流就少抓欄位);每輪重算,端點恢復就自動恢復。"""

    def __init__(self, cls):
        self.cls, self.orig, self.miss, self.hit, self.skipped = cls, cls.get_json, {}, {}, {}

    def __enter__(self):
        outer = self

        def get_json(inst, url, params=None, timeout=30):
            key = str(url).split("?")[0]
            if outer.hit.get(key, 0) == 0 and outer.miss.get(key, 0) >= DEAD_AFTER:
                outer.skipped[key] = outer.skipped.get(key, 0) + 1
                return {}
            r = outer.orig(inst, url, params, timeout)
            if r:
                outer.hit[key] = outer.hit.get(key, 0) + 1
                outer.miss[key] = 0
            else:
                outer.miss[key] = outer.miss.get(key, 0) + 1
            return r

        self.cls.get_json = get_json
        return self

    def __exit__(self, *exc):
        self.cls.get_json = self.orig
        return False


def _write(db, rows: list) -> int:
    if not rows:
        return 0
    Path(db).parent.mkdir(parents=True, exist_ok=True)
    new, _total = BASE._LIB.UTILS.upsert_rows(db, BASE.TABLE, rows, BASE.KEYS, counts=True)
    return int(new)


def run(start=None, end=None, net=None, db=None, dry: bool = False, inner=None, http=None, echo=print, sleep=None) -> dict:
    inner = inner or _PRIOR_RUN
    db = db or BASE.DB_IDX
    end_s = end or date.today().isoformat()
    st = {"TAIEX": start, "TPEX": start} if start else starts(db)
    res = {"state": "OK", "start": min(st.values()), "end": end_s, "fetched": 0, "added": 0, "calls": 0, "incremental": not start,
           "by_index": {"TAIEX": {"start": st["TAIEX"], "added": 0, "state": "UP_TO_DATE"}, "TPEX": {"start": st["TPEX"], "added": 0, "state": "UP_TO_DATE"}}}
    if all(s > end_s for s in st.values()):
        res.update(state="UP_TO_DATE", note="兩個指數都已到最新日;零外呼")
        return res
    net = net if net is not None else (BASE.net_tool() if http is None else None)
    if http is None:
        if net is None or not hasattr(net, "curl_bytes"):
            res.update(state="FAIL", note="網路工具缺(要 SUP_MDL740 的 curl_bytes)")
            return res
        BASE._NetHttp.net = net
    # ── 櫃買先抓(櫃買中心現行官方端點;按月,整段一兩分鐘):不排在加權後面,空庫起跑時不會被加權的長補抓卡住
    if st["TPEX"] <= end_s:
        try:
            h = http if http is not None else BASE._NetHttp()
            months = month_chunks(st["TPEX"], end_s)
            if len(months) > 1:
                echo("  [TW 指數] 櫃買 %s → %s 共 %d 個月(現行官方端點;每月寫庫)" % (st["TPEX"], end_s, len(months)), flush=True)
            got_any = False
            for i, (a, b) in enumerate(months, 1):
                y, m = int(a[:4]), int(a[5:7])
                rows = [r for r in tpex_month_rows(h, y, m) if a <= r["date"] <= b]
                new = 0 if dry else _write(db, rows)
                got_any = got_any or bool(rows)
                res["fetched"] += len(rows)
                res["added"] += new
                res["calls"] += 2
                res["by_index"]["TPEX"]["added"] += new
                if len(months) > 1:
                    echo("  [TW 指數] 櫃買 月 %d/%d %s · 列 %d · 新增 %d" % (i, len(months), a[:7], len(rows), new), flush=True)
                if sleep is not None and i < len(months):
                    sleep(0.3)
            res["by_index"]["TPEX"]["state"] = "OK" if got_any else "EMPTY"
        except BASE.GateDenied as exc:
            res["by_index"]["TPEX"]["state"] = "DENY"
            res.update(state="DENY", note=str(exc))
            return res
    # ── 加權(收容件;照前版;長區間按月切段,每段寫庫)
    if st["TAIEX"] <= end_s:
        span = (date.fromisoformat(end_s) - date.fromisoformat(st["TAIEX"])).days
        chunks = month_chunks(st["TAIEX"], end_s) if span > CHUNK_OVER_DAYS else [(st["TAIEX"], end_s)]
        if len(chunks) > 1:
            echo("  [TW 指數] 加權 %s → %s 共 %d 段(按月;每段寫庫)" % (st["TAIEX"], end_s, len(chunks)), flush=True)
        with _SkipDead(BASE._NetHttp) as guard:
            for i, (a, b) in enumerate(chunks, 1):
                r = inner(a, b, net=net, db=db, dry=dry)
                for k in ("fetched", "added", "calls"):
                    res[k] += int(r.get(k) or 0)
                res["by_index"]["TAIEX"]["added"] += int(r.get("added") or 0)
                res["by_index"]["TAIEX"]["state"] = r.get("state")
                if len(chunks) > 1:
                    echo("  [TW 指數] 加權 段 %d/%d %s → %s · %s · 新增 %s" % (i, len(chunks), a, b, r.get("state"), r.get("added", 0)), flush=True)
                if r.get("state") not in ("OK", "EMPTY", "UP_TO_DATE"):
                    res.update(state=r.get("state") or "FAIL", stopped_at="TAIEX " + a, note=r.get("note") or r.get("why") or "")
                    return res
        if guard.skipped:
            res["dead_endpoints"] = {k.split("tpex.org.tw")[-1].split("twse.com.tw")[-1]: n for k, n in guard.skipped.items()}
    states = {v["state"] for v in res["by_index"].values()}
    if states <= {"EMPTY", "UP_TO_DATE"} and res["fetched"] == 0:
        res["state"] = "EMPTY" if "EMPTY" in states else "UP_TO_DATE"
    if dry:
        res["note"] = "--dry:不寫庫"
    return res


PRIOR.run = run          # 前版 main 以模組全域叫 run()


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if not BASE._allowed():
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "只經 VCGC(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
        return 2
    verb = next((x for x in a if not x.startswith("-")), "status")
    if verb == "status":
        c = BASE.count()
        s = starts()
        print("  [TW 指數] %s · %s · " % (BASE.DB_IDX.name, BASE.TABLE) + (" · ".join("%s %s 列 %s → %s" % (k, n, lo, hi) for k, (n, lo, hi) in c.items()) or "空")
              + " · 下一個增量起點 加權 %s · 櫃買 %s" % (s["TAIEX"], s["TPEX"]))
        return 0 if all(k in c for k in ("TAIEX", "TPEX")) else 2
    if verb == "run":
        import time as _time
        r = run(BASE._arg(a, "--start"), BASE._arg(a, "--end"), dry="--dry" in a, sleep=_time.sleep)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return {"OK": 0, "UP_TO_DATE": 0, "DENY": 4, "EMPTY": 2}.get(r["state"], 1)
    return PRIOR.main(argv)


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))

    quiet = lambda *x, **k: None  # noqa: E731
    print("=== %s 薄尾自測(櫃買現行端點 · 各自接續 · 按月寫庫;零網路;庫只在暫存夾)===" % ENGINE_TAG)
    ch = month_chunks("2022-07-15", "2022-10-03")
    chk("① 按月切段:頭尾不重疊、不漏日", ch == [("2022-07-15", "2022-07-31"), ("2022-08-01", "2022-08-31"), ("2022-09-01", "2022-09-30"), ("2022-10-01", "2022-10-03")])
    chk("② 日期:西元與民國都轉成 ISO;數字去千分位;空值不假填", _iso("2023/01/03") == "2023-01-03" and _iso("115/11/02") == "2026-11-02" and _iso("x") is None
        and _f("154,820,241") == 154820241.0 and _f("--") is None and _f(369.24) == 369.24)

    class FakeHttp:
        def __init__(self, drop_trd=False, deny=False):
            self.urls, self.drop_trd, self.deny = [], drop_trd, deny

        def get_json(self, url, params=None, timeout=30):
            self.urls.append((url, (params or {}).get("date")))
            if self.deny:
                raise BASE.GateDenied("同意閘沒開")
            ym = (params or {}).get("date", "")[:7]
            y, m = int(ym[:4]), int(ym[5:7])
            if url == TPEX_INX:
                return {"stat": "ok", "tables": [{"fields": ["日期", "開市", "最高", "最低", "收市", "漲/跌"],
                        "data": [["%04d/%02d/02" % (y, m), "368.22", "373.28", "362.18", "369.24", "-1.02"], ["%04d/%02d/03" % (y, m), "366.75", "366.75", "345.25", "345.52", "-23.72"]]}]}
            if url == TPEX_TRD and not self.drop_trd:
                return {"stat": "ok", "tables": [{"fields": ["日期", "成交張數", "金額(仟元)", "筆數", "櫃買指數", "漲/跌"],
                        "data": [["%d/%02d/02" % (y - 1911, m), "687,422", "154,820,241", "685,524", 369.24, -1.02], ["%d/%02d/03" % (y - 1911, m), "1,044,296", "197,177,872", "1,119,456", 345.52, -23.72]]}]}
            return {}

    rows = tpex_month_rows(FakeHttp(), 2026, 11)
    chk("③ 櫃買一個月:開高低收來自 inx;量 = 成交張數×1000(股)· 值 = 仟元×1000(元);欄位 = OUT-05",
        len(rows) == 2 and rows[0]["date"] == "2026-11-02" and (rows[0]["open"], rows[0]["high"], rows[0]["low"], rows[0]["close"]) == (368.22, 373.28, 362.18, 369.24)
        and rows[0]["volume"] == 687422000.0 and rows[0]["turnover"] == 154820241000.0 and rows[0]["index_code"] == "TPEX" and rows[0]["source"] == "TPEX 官方",
        "%s 量 %s 值 %s" % (rows[0]["date"], rows[0]["volume"], rows[0]["turnover"]) if rows else "0 列")
    r_drop = tpex_month_rows(FakeHttp(drop_trd=True), 2026, 11)
    chk("④ 量值端點沒回:收盤照寫、量值留空並在 note 寫明(不假填)", len(r_drop) == 2 and r_drop[0]["volume"] is None and "沒回" in r_drop[0]["note"])
    try:
        import duckdb
    except ImportError:
        duckdb = None
    if duckdb is None:
        chk("⑤ duckdb 在(不在就量不到寫庫)", False, "沒有 duckdb:SKIP 不是綠")
    else:
        with tempfile.TemporaryDirectory(prefix="eng232_v0102_") as td:
            db = Path(td) / "idx.duckdb"
            taiex_calls, lines = [], []

            def fake_taiex(a, b, net=None, db=None, dry=False):
                taiex_calls.append((a, b))
                n = _write(db, [{"date": b, "index_code": "TAIEX", "index_name": "發行量加權股價指數", "open": 1.0, "low": 1.0, "high": 1.0, "close": 1.0, "volume": 1.0,
                                 "turnover": 1.0, "inst_foreign_net": None, "inst_trust_net": None, "inst_dealer_net": None, "source": "TWSE 官方", "note": ""}])
                return {"state": "OK", "fetched": 1, "added": n, "calls": 3}

            fh = FakeHttp()
            r = run("2026-08-01", "2026-11-18", inner=fake_taiex, http=fh, db=db, echo=lambda *x, **k: lines.append(x[0]))
            c = BASE.count(db)
            chk("⑤ 空庫長區間:加權 4 段 + 櫃買 4 個月都寫庫、每段一行;兩個指數都在庫裡", r["state"] == "OK" and len(taiex_calls) == 4 and len(fh.urls) == 8
                and c.get("TAIEX", (0,))[0] == 4 and c.get("TPEX", (0,))[0] == 8 and sum(1 for x in lines if "段 " in x or "月 " in x) == 8, "%s · %d 行" % ({k: v[0] for k, v in c.items()}, len(lines)))
            s2 = starts(db)
            chk("⑥ 各自接續:加權從它自己最新日的隔天 · 櫃買從它自己最新日的隔天(不再因為缺一個就回 BOOT)", s2 == {"TAIEX": "2026-11-19", "TPEX": "2026-11-04"}, s2)
            taiex_calls.clear()
            fh2 = FakeHttp()
            r2 = run(None, "2026-11-18", inner=fake_taiex, http=fh2, db=db, echo=quiet)
            chk("⑦ 增量:加權已到最新 → 零呼叫;櫃買只補它缺的那一段;重跑同鍵不重插", taiex_calls == [] and len(fh2.urls) == 2 and r2["by_index"]["TAIEX"]["state"] == "UP_TO_DATE"
                and r2["added"] == 0 and BASE.count(db)["TPEX"][0] == 8, "新增 %d" % r2["added"])
            r3 = run("2026-11-01", "2026-11-18", inner=fake_taiex, http=FakeHttp(deny=True), db=Path(td) / "deny.duckdb", echo=quiet)
            chk("⑧ 同意閘沒開:DENY、櫃買零寫入", r3["state"] == "DENY" and "TPEX" not in BASE.count(Path(td) / "deny.duckdb"))
            only = Path(td) / "only_taiex.duckdb"
            _write(only, [{"date": "2026-11-17", "index_code": "TAIEX", "index_name": "發行量加權股價指數", "open": 1.0, "low": 1.0, "high": 1.0, "close": 1.0, "volume": 1.0, "turnover": 1.0,
                           "inst_foreign_net": None, "inst_trust_net": None, "inst_dealer_net": None, "source": "TWSE 官方", "note": ""}])
            chk("⑨ 負控:只有加權的庫,前版的增量起點是 BOOT(每天白抓三年);本版加權從隔天接、只有櫃買從 BOOT",
                PRIOR.next_start(only) == BOOT and starts(only) == {"TAIEX": "2026-11-18", "TPEX": BOOT}, starts(only))

    class H:
        n = {}

        def get_json(self, url, params=None, timeout=30):
            H.n[url] = H.n.get(url, 0) + 1
            if "flaky" in url:
                return {"ok": 1} if H.n[url] in (1, 5, 6) else {}
            return {} if "dead" in url else {"ok": 1}

    with _SkipDead(H) as g:
        h = H()
        got = [h.get_json("https://x/dead.php", {"d": i}) for i in range(6)] + [h.get_json("https://x/live", {"d": i}) for i in range(3)]
        flaky = [bool(h.get_json("https://x/flaky", {"d": i})) for i in range(6)]
    chk("⑩ 從沒成功過又連兩次拿不到 JSON 的端點這一輪不再打(6 次只真打 2 次);成功過的端點空幾次照樣繼續打;離開後還原",
        H.n == {"https://x/dead.php": 2, "https://x/live": 3, "https://x/flaky": 6} and g.skipped == {"https://x/dead.php": 4}
        and got[6:] == [{"ok": 1}] * 3 and flaky == [True, False, False, False, True, True]
        and "outer" not in getattr(H.get_json, "__code__", type("c", (), {"co_freevars": ()})).co_freevars, H.n)
    chk("⑪ 裝進前版:前版 main 叫到的就是本版的 run", PRIOR.run is run and callable(_PRIOR_RUN))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑫ 加速器橋真的匯入 · 網路工具橋在 · 外呼只經前版的網路替身 · 不含本機路徑 · 不寫同意值",
        "import VIA_SuperAccel_Module as VIA_ACCEL" in src and "via_net_unified_v*.py" in src and ("url" + "open(") not in src and ("req" + "uests.") not in src
        and ("C:" + "\\Users") not in src and ("_CONSENT\"] " + "=") not in src)
    PRIOR.run = _PRIOR_RUN
    try:
        rc = PRIOR.selftest()
    finally:
        PRIOR.run = run
    chk("⑬ 前版自測照過", rc == 0, "rc %s" % rc)
    good = all(ok)
    print("[計] %s 本版 %d/%d · %s" % (ENGINE_TAG, sum(ok), len(ok), "PASS" if good else "FAIL"))
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
