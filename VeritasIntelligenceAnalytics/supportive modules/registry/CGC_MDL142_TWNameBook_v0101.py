#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL142_TWNameBook v0101 — 台股名稱正典冊(批465 立;批468 加 refresh)
====================================================================
操作員令:「VDF 有用四碼台股代碼去擷取 TWSE/TPEX/MOPS 每日更新的全台股清單,
名稱統一從這裡更新。」

先查再造(量到的,不是猜的):
  · 全倉**沒有**代碼↔名稱的正典解析器。VRN_TW01_TickerBridge 做的是「從文字
    找代碼」,不是名稱解析,而且它還寫死 C:\\Users\\tonyk\\OneDrive\\Desktop\\VRN\\…
  · 庫裡有**兩張**清單表,而且名稱樣態完全不同:
      tw_listings            891 列 · **全名**「茂生農經股份有限公司」
                             · industry 只有代碼 '33' · isin 空  → 殘缺
      tw_listings_industry 1,978 列 · 四碼 code + **簡稱**「台積電」
                             · market TWSE 1,088 / TPEX 890
                             · industry_name「半導體業」· yf_ticker  → **正典**
  · 這不是學術差別。研究報告寫的是**簡稱**;拿全名冊去比對報告文字,
    一個字都不會命中——ENG067 的③⑤兩盞紅燈就是這麼來的(批465b 實錄)。
  · 全樹盤點:**19 支尾版引擎**仍引用 tw_listings(非 _industry)。
    其中有些是**寫入方**(VDF_ENG052/ENG081 維護那張表),不能一律改讀;
    所以本件只立**一本共用的冊**,不代任何引擎改綁——誰要換,誰自己換。

冊的取數次序(正典優先,與批402 網路正典令同律):
  ① DuckDB tw_listings_industry(VDF 每日 TWSE/TPEX/MOPS)          ← 正典
  ② VRN_TWRoster_Offline_v*.json(同一張表的落盤;離線/無庫時可用)  ← 退路
  ③ DuckDB tw_listings 的全名(**只補**①②沒有的鍵)                ← 補充
  三條都空 → 誠實回空冊並講出每一條為什麼空,不假裝有冊。

介面(給別的引擎綁,不要各自再寫一份):
    book()                → {code: {"name","market","industry","yf","src"}}
    name_of("2330")       → "台積電"        (查不到回 "")
    code_of("台積電")     → "2330"          (簡稱/全名/台↔臺變體都認)
    scan_names()          → {出現在文字裡就算命中的名字: code}
    provenance()          → 每一條來源答了幾家、為什麼沒答
批468 追令(操作員:「用 VDF 自動更新清單功能去抓取」):
  本冊原本只**讀**庫;庫裡那張表新不新它管不著。加 `refresh` 動詞,
  **委派 VDF 正主更新器**把清單抓新:
    VDF_ENG055_OmniFetch_v*.py(尾版 glob)的 **L1 listings 車道**
    · openapi.twse.com.tw/v1/opendata/t187ap03_L(上市)
    · tpex.org.tw/openapi/v1/mopsfin_t187ap03_O(上櫃)
    → upsert 進 tw_listings_industry(鍵 code+market)
  Zero-Hydra:**本件不自己抓**,一行網路碼都不寫,全交給正主。
  **同意閘絕不代設**:VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 由操作員自己開;
  沒開就 fail-closed 誠實停,把該設什麼、在哪設講清楚,不代勞、不繞道。
用法:python3 CGC_MDL142_TWNameBook_v0101.py [show 2330] [refresh [--apply]] | --selftest
紀律:唯讀(絕不寫庫)、零網路、零發明(冊內命中才回)、誠實三態。
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

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
#: VDF 正典庫(唯讀)
DB_TW = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
#: 同一張表的落盤(離線退路);尾版律 glob
ROSTER_DIR = VIA / "functional modules" / "VRN"
ROSTER_GLOB = "VRN_TWRoster_Offline_v*.json"
#: 正典表名 —— 操作員令指的就是這張
CANON_TABLE = "tw_listings_industry"
#: 殘缺表(全名);只拿來補①②沒有的鍵
LEGACY_TABLE = "tw_listings"

_BOOK: dict | None = None
_PROV: list = []


def _alt_forms(name: str) -> set:
    """台↔臺 這種正字漂移的同義形(QA 實錘:norm「臺積電」對冊名「台積電」失配)。"""
    out = {name}
    if "台" in name:
        out.add(name.replace("台", "臺"))
    if "臺" in name:
        out.add(name.replace("臺", "台"))
    return {x for x in out if x}


def _from_db(table: str) -> tuple[dict, str]:
    """唯讀取一張清單表。回 ({code: row}, 因由);因由非空=沒答出來。"""
    if not DB_TW.exists():
        return {}, f"庫不在({DB_TW.name})"
    try:
        import duckdb
    except Exception as exc:
        return {}, f"duckdb 缺({type(exc).__name__})"
    try:
        con = duckdb.connect(str(DB_TW), read_only=True)
    except Exception as exc:
        return {}, f"庫開不了 {type(exc).__name__}:{str(exc)[:60]}"
    try:
        cols = [c[0] for c in con.execute(f'DESCRIBE "{table}"').fetchall()]
        has = lambda c: c in cols          # noqa: E731
        sel = ["code", "name"]
        sel += ["market"] if has("market") else []
        sel += ["industry_name"] if has("industry_name") else (["industry"] if has("industry") else [])
        sel += ["yf_ticker"] if has("yf_ticker") else []
        rows = con.execute(f'SELECT {", ".join(sel)} FROM "{table}"').fetchall()
    except Exception as exc:
        con.close()
        return {}, f"{table} 讀不到 {type(exc).__name__}:{str(exc)[:60]}"
    con.close()
    out = {}
    for r in rows:
        d = dict(zip(sel, r))
        code = str(d.get("code") or "").strip()
        name = str(d.get("name") or "").strip()
        if not code or not name:
            continue
        out[code] = {
            "name": name,
            "market": str(d.get("market") or ""),
            "industry": str(d.get("industry_name") or d.get("industry") or ""),
            "yf": str(d.get("yf_ticker") or ""),
        }
    return out, ("" if out else f"{table} 零列")


def _from_roster() -> tuple[dict, str]:
    hits = sorted(ROSTER_DIR.glob(ROSTER_GLOB))
    if not hits:
        return {}, f"無落盤({ROSTER_GLOB})"
    p = hits[-1]
    try:
        j = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return {}, f"{p.name} 讀取失敗 {type(exc).__name__}"
    out = {}
    for code, meta in (j.get("codes") or {}).items():
        nm = str((meta or {}).get("name") or "").strip()
        if not nm:
            continue
        out[str(code).strip()] = {
            "name": nm,
            "market": str((meta or {}).get("market") or ""),
            "industry": str((meta or {}).get("industry") or ""),
            "yf": str((meta or {}).get("yf") or ""),
        }
    return out, ("" if out else f"{p.name} 零筆")


def book(force: bool = False) -> dict:
    """名稱正典冊。正典優先 → 落盤退路 → 全名補位;每一家標得出 src。"""
    global _BOOK, _PROV
    if _BOOK is not None and not force:
        return _BOOK
    b: dict = {}
    prov = []

    canon, why1 = _from_db(CANON_TABLE)
    for code, row in canon.items():
        b[code] = dict(row, src=f"DuckDB {CANON_TABLE}")
    prov.append(("① 正典 DuckDB " + CANON_TABLE, len(canon), why1))

    rost, why2 = _from_roster()
    n2 = 0
    for code, row in rost.items():
        if code not in b:
            b[code] = dict(row, src="落盤 " + ROSTER_GLOB)
            n2 += 1
    prov.append(("② 落盤 " + ROSTER_GLOB, n2, why2))

    leg, why3 = _from_db(LEGACY_TABLE)
    n3 = 0
    for code, row in leg.items():
        if code not in b:
            b[code] = dict(row, src=f"DuckDB {LEGACY_TABLE}(全名補位)")
            n3 += 1
    prov.append((f"③ 補位 DuckDB {LEGACY_TABLE}", n3, why3))

    _BOOK, _PROV = b, prov
    return b


def provenance() -> list:
    book()
    return list(_PROV)


def name_of(code: str) -> str:
    return (book().get(str(code).strip()) or {}).get("name", "")


def code_of(name: str) -> str:
    """簡稱/全名/台↔臺變體都認;查不到回 ""(零發明)。"""
    q = str(name or "").strip()
    if not q:
        return ""
    idx = scan_names()
    return idx.get(q, "")


def scan_names() -> dict:
    """{可在文字中命中的名字: code}。含台↔臺變體;長度<2 的不收(雜訊)。"""
    out = {}
    for code, row in book().items():
        for v in _alt_forms(row["name"]):
            if len(v) >= 2:
                out.setdefault(v, code)
    return out


def refresh(apply: bool = False) -> int:
    """委派 VDF 正主更新器把全台股清單抓新(批468 操作員令)。

    誠實三態:
      同意閘未開 → 不跑、不繞道、不代設,印出該設什麼(fail-closed)
      更新器缺席 → 誠實停並說缺哪一支
      跑完       → 印出**前後列數差**,差 0 也照實說(「跑了但沒變」也是資訊)
    """
    import os
    eng = sorted((VIA / "functional modules" / "VDF" / "engine")
                 .glob("VDF_ENG055_OmniFetch_v*.py"))
    if not eng:
        print("  [FAIL] 正主更新器缺席:VDF_ENG055_OmniFetch_v*.py"
              "(本件不自己抓=Zero-Hydra;沒有正主就誠實停)")
        return 2
    tail = eng[-1]
    gate_net = os.environ.get("VIA_NET_CONSENT")
    gate_scr = os.environ.get("VIA_SCRAPE_CONSENT")
    n_before, _ = _from_db(CANON_TABLE)
    print(f"  [前] {CANON_TABLE} {len(n_before)} 檔 · 更新器 {tail.name} · L1 listings 車道")
    if gate_net != "YES" or gate_scr != "YES":
        print("  [FAIL-CLOSED] 同意閘未開,**不代設也不繞道**。"
              f"現況 VIA_NET_CONSENT={gate_net!r} · VIA_SCRAPE_CONSENT={gate_scr!r}")
        print("     要抓就由操作員自己開(本窗有效,不寫進設定):")
        print('       $env:VIA_NET_CONSENT="YES"; $env:VIA_SCRAPE_CONSENT="YES"')
        print(f'       python "{tail.name}" run --lane L1')
        print("     來源:openapi.twse.com.tw/v1/opendata/t187ap03_L(上市)"
              " + tpex.org.tw/openapi/v1/mopsfin_t187ap03_O(上櫃)")
        return 3
    if not apply:
        print("  [PLAN] 同意閘已開;加 --apply 才真的呼叫更新器(預設不動手)")
        return 0
    import subprocess
    print(f"  [RUN] 委派 {tail.name} run --lane L1")
    r = subprocess.run([sys.executable, str(tail), "run", "--lane", "L1"],
                       cwd=str(tail.parent), text=True, encoding="utf-8",
                       errors="replace", capture_output=True, timeout=900)
    for ln in (r.stdout or "").splitlines()[-12:]:
        print("    " + ln)
    if r.returncode != 0:
        print(f"  [FAIL] 更新器 rc={r.returncode} · {((r.stderr or '').strip().splitlines() or [''])[-1][:120]}")
        return r.returncode
    n_after, _ = _from_db(CANON_TABLE)
    d = len(n_after) - len(n_before)
    print(f"  [後] {CANON_TABLE} {len(n_after)} 檔(前 {len(n_before)} · 差 {d:+d})"
          + ("" if d else " —— 跑了但列數沒變(清單本來就是最新;這也是資訊)"))
    book(force=True)
    return 0


def status() -> dict:
    b = book()
    return {
        "n": len(b),
        "canon_table": CANON_TABLE,
        "db": str(DB_TW),
        "db_exists": DB_TW.exists(),
        "provenance": [{"source": s, "n": n, "why": w} for s, n, w in provenance()],
        "scan_keys": len(scan_names()),
    }


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    done, fails = [], []

    def chk(name, cond, note=""):
        done.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    b = book(force=True)
    prov = provenance()
    chk("① 正典優先:tw_listings_industry(VDF 每日 TWSE/TPEX/MOPS 四碼全清單)排第一,"
        "落盤次之,全名表只補位(操作員令「名稱統一從這裡更新」)",
        prov[0][0].endswith(CANON_TABLE) and "落盤" in prov[1][0]
        and LEGACY_TABLE in prov[2][0],
        f"({' · '.join(f'{s}={n}家' + (f'({w})' if w else '') for s, n, w in prov)})")

    chk("② 冊非空且四碼為主(1,978 家量級;TWSE+TPEX)",
        len(b) >= 500 and sum(1 for c in b if len(c) == 4) >= int(len(b) * 0.9),
        f"({len(b)} 家 · 四碼 {sum(1 for c in b if len(c) == 4)})")

    # 對照組:兩張表的名稱樣態真的不同——這是①存在的理由
    canon, _ = _from_db(CANON_TABLE)
    leg, _ = _from_db(LEGACY_TABLE)
    short_hit = canon.get("2330", {}).get("name", "")
    long_sample = next((v["name"] for v in leg.values() if len(v["name"]) >= 8), "")
    chk("③ **兩張表名稱樣態不同**才是根:正典表 2330=簡稱,殘缺表存全名"
        "(樣本「…股份有限公司」)。研究報告寫簡稱,拿全名冊比對文字一個字都不會命中"
        "——ENG067 ③⑤ 兩盞紅燈就是這麼來的",
        (short_hit == "台積電" or not canon) and ("股份有限公司" in long_sample or not leg),
        f"(正典 2330='{short_hit}' · 殘缺表樣本='{long_sample[:18]}')")

    chk("④ name_of / code_of 往返(2330↔台積電;2454↔聯發科)",
        name_of("2330") == "台積電" and code_of("台積電") == "2330"
        and name_of("2454") == "聯發科" and code_of("聯發科") == "2454",
        f"(2330→{name_of('2330')} · 台積電→{code_of('台積電')})")

    chk("⑤ 台↔臺 正字漂移同義收斂(QA 實錘:norm「臺積電」對冊名「台積電」失配)",
        code_of("臺積電") == "2330" and "臺積電" in scan_names(),
        f"(臺積電→{code_of('臺積電')})")

    chk("⑥ 零發明:冊外一律回空字串,不猜不編",
        name_of("9999") == "" and code_of("宇宙電子") == "" and code_of("") == "",
        "(冊外→空)")

    chk("⑦ 唯讀律:本件絕不寫庫(零 INSERT/UPDATE/CREATE/DELETE,連線一律 read_only)",
        all(k not in _SRC_BODY.upper() for k in ("INSERT ", "UPDATE ", "CREATE TABLE", "DELETE "))
        and "read_only=True" in _SRC_BODY,
        "(本體零寫入語句)")

    n_canon = prov[0][1]
    chk("⑧ 誠實三態:每一條來源答了幾家、沒答的講出為什麼;三條都空回空冊不假裝",
        all(isinstance(w, str) for _, _, w in prov)
        and (n_canon > 0 or prov[0][2] != ""),
        f"(①{'答 ' + str(n_canon) + ' 家' if n_canon else '空:' + (prov[0][2] or '?')})")

    chk("⑨ Zero-Hydra:本件只立**一本共用冊**,不代任何引擎改綁。全樹 19 支尾版仍引用"
        " tw_listings,其中 VDF_ENG052/ENG081 是那張表的**寫入方**,一律改讀會弄壞它們"
        "——誰要換誰自己換,這件事要由操作員裁",
        "不代任何引擎改綁" in _SRC_BODY and "寫入方" in _SRC_BODY, "(立場在檔)")

    import os as _os142
    _g1, _g2 = _os142.environ.get("VIA_NET_CONSENT"), _os142.environ.get("VIA_SCRAPE_CONSENT")
    _eng142 = sorted((VIA / "functional modules" / "VDF" / "engine")
                     .glob("VDF_ENG055_OmniFetch_v*.py"))
    _rc142 = refresh(apply=False)
    chk("⑩ `refresh` **委派 VDF 正主更新器**抓新清單(操作員令「用 VDF 自動更新清單"
        "功能去抓取」):VDF_ENG055_OmniFetch 尾版的 L1 listings 車道 → "
        "openapi.twse.com.tw t187ap03_L + tpex mopsfin_t187ap03_O → upsert "
        "tw_listings_industry。本件**一行網路碼都不寫**",
        len(_eng142) >= 1 and "VDF_ENG055_OmniFetch_v*.py" in _SRC_BODY
        and "requests" not in _SRC_BODY and "urlopen" not in _SRC_BODY,
        f"(正主 {len(_eng142)} 版 · 尾版 {_eng142[-1].name if _eng142 else '缺'}"
        " · 本件零網路碼)")

    chk("⑪ **同意閘絕不代設**:閘未開就 fail-closed(rc=3)、印出該設什麼與來源網址,"
        "不代勞不繞道;閘開了也要 --apply 才真的動手(預設只出計畫)",
        (_rc142 == 3 if (_g1 != "YES" or _g2 != "YES") else _rc142 == 0)
        and "FAIL-CLOSED" in _SRC_BODY and "不代設也不繞道" in _SRC_BODY
        and 'os.environ["VIA_NET_CONSENT"]' not in _SRC_BODY,
        f"(本境閘 NET={_g1!r}/SCRAPE={_g2!r} → refresh rc={_rc142};零代設)")

    print(f"  [計] 十一檢({len(done)} 檢) OK {len(done) - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


_SRC_BODY = Path(__file__).read_text(encoding="utf-8").split("def selftest")[0]


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 台股名稱正典冊(CGC_MDL142 v0101)· 十一檢自測(零網路;唯讀)===")
        return selftest()
    if args and args[0] == "refresh":
        return refresh(apply="--apply" in args)
    if args and args[0] == "show" and len(args) > 1:
        q = args[1]
        row = book().get(q)
        if row:
            print(f"{q} → {row['name']} · {row['market']} · {row['industry']} · {row['yf']} · 源 {row['src']}")
        else:
            c = code_of(q)
            print(f"{q} → {('代碼 ' + c + ' · ' + name_of(c)) if c else '冊內查無(零發明)'}")
        return 0
    print(json.dumps(status(), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
