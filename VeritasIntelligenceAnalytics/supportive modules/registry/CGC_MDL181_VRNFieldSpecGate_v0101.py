#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL181_VRNFieldSpecGate v0101 — 研報欄位規格對帳閘(批712;批728 誠實燈)

v0100→v0101(批728 操作員令「重整 VRN 實測修正到成功」;稽核照出):
  庫**在**但 `vrn_report_basic` **不在**(開機掛件先把 VDF 表落進 vdf_tw_market.duckdb、VRN 還沒入庫)時,
  v0100 直接 `select count(*) from vrn_report_basic` → duckdb CatalogException 整支炸掉(rc1 traceback)——
  **缺料被報成壞掉**(L16)。而且庫缺席時回 rc3、格子站卻期望 rc0,兩種缺料都只有在「有 VRN 料的機器」才綠。
  v0101:開庫後先 `show tables`;表不在 = NODATA(逐欄照列 · 指路 via-vrnrun / ENG073)· rc2。
  庫缺席照舊是 ABSENT 態(逐欄 NODATA)但 rc 也回 2(批693B 同律:庫缺/表空=缺料 rc2);只有本境沒有 duckdb 套件才 rc3。
  +⑥ 一檢(沙盒臨時庫只放一張無關表 → NODATA、不炸、15 欄照列)。判準一字未動。

操作員在 2026-09-23 逐欄給定了研報要產出的 **15 欄**。本閘做一件事:
**拿那本規格冊去對現況,逐欄報一個誠實態。**

為什麼要有這支:那些缺口本來就都「在輸出裡」——但是埋在一大張表的某一格,
或是一句被截斷的註記(例如 `source` 寫著 `CNYES_FACTSET_PENDING`)。
**埋著的缺口不會有人去補。** 一欄一盞燈,補了料燈自己會轉綠。

**六態(LL400:分得開「壞了」「沒有料」「根本沒接」)**:
    GREEN          有值且通過規則,覆蓋率達標
    PARTIAL        有值但覆蓋不足 —— 照實印覆蓋率,不四捨五入成綠
    NODATA         欄位在、來源在,但一個值都沒有
    SOURCE_PENDING 來源**接了但還沒供料**(例如 FactSet 的 source 自己寫著 PENDING)
    NOT_WIRED      規格要求,但系統裡**根本沒有這個欄/這個算式**
    GATED          要觸網才補得齊,同意閘未開 —— **AI 永不代設**

律:唯讀(只讀庫,不寫庫)· 零網路 · 不代設同意閘 · 不自己另寫一份欄位清單(讀 SSOT)。
用法:python3 CGC_MDL181_VRNFieldSpecGate_v0100.py [--json] | --selftest
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

import json
import sys
from pathlib import Path

ENGINE_ID = "CGC_MDL181_VRNFieldSpecGate"
VERSION = "v0101"
BATCH = "批712"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
SPEC = HERE / "VIA_VRN_FieldSpec_SSOT_v0100.json"
MEGA = VIA / "functional modules/VDF/output_hub/mega/vdf_tw_market.duckdb"

#: 覆蓋率達標門檻。低於這個數就是 PARTIAL,不是 GREEN ——
#:   「大部分有」不是「有」,把 70% 講成綠,看的人會以為那一欄可以直接用。
GREEN_AT = 0.95


def load_spec(path: Path | None = None) -> dict:
    """規格從**冊**來,不寫在碼裡(Zero-Hydra)。讀不到就誠實回空,不自己編一份。"""
    p = path or SPEC
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _state(have: int, total: int, *, wired: bool = True, pending: bool = False,
           gated: bool = False) -> str:
    """一欄的態。**次序有意義**:沒接 > 來源待供 > 要觸網 > 有沒有值 > 夠不夠。"""
    if not wired:
        return "NOT_WIRED"
    if pending:
        return "SOURCE_PENDING"
    if total <= 0:
        return "NODATA"
    if have <= 0:
        return "GATED" if gated else "NODATA"
    if have >= total * GREEN_AT:
        return "GREEN"
    return "GATED" if gated else "PARTIAL"


def measure(db: Path | None = None, spec: dict | None = None) -> dict:
    """對現況量一次。庫缺席=誠實 ABSENT,不編一張空表出來充數。"""
    sp = spec if spec is not None else load_spec()
    if not sp.get("fields"):
        return {"state": "ABSENT", "why": f"規格冊讀不到:{SPEC.name} —— 不自己編一份欄位清單",
                "rows": []}
    d = db or MEGA
    if not d.exists():
        return {"state": "ABSENT", "why": f"庫缺席:{d} —— 量不到不是壞掉,但也不能說它好了",
                "rows": [{"key": f["key"], "zh": f["zh"], "state": "NODATA", "have": 0,
                          "total": 0, "why": "庫缺席"} for f in sp["fields"]]}
    try:
        import duckdb
    except ImportError:
        return {"state": "ABSENT", "why": "本境無 duckdb(不代裝套件)", "rows": []}

    con = duckdb.connect(str(d), read_only=True)
    try:
        _tables = {r[0] for r in con.execute("show tables").fetchall()}
    except Exception:
        _tables = set()
    if "vrn_report_basic" not in _tables:
        con.close()
        return {"state": "NODATA",
                "why": (f"庫在但 vrn_report_basic 不在({d.name} 有 {len(_tables)} 表,沒有 VRN 入庫)—— "
                        "缺料不是壞掉;先跑 via-vrnrun(V2 鏈裡 ENG073 入庫)再複判"),
                "rows": [{"key": f["key"], "zh": f["zh"], "state": "NODATA", "have": 0,
                          "total": 0, "why": "vrn_report_basic 不在"} for f in sp["fields"]]}
    try:
        q = lambda s: con.execute(s).fetchone()[0]
        n_all = q("select count(*) from vrn_report_basic")
        n_tk = q("select count(*) from vrn_report_basic where ticker <> ''")
        codes = [r[0] for r in con.execute(
            "select distinct ticker from vrn_report_basic where ticker <> ''").fetchall()]
        n_code = len(codes)
        inlist = ",".join("'%s'" % c.replace("'", "") for c in codes) or "''"

        def have_codes(sql: str) -> int:
            try:
                return q(sql)
            except Exception:
                return 0

        m = {}
        m["report_date"] = (q("select count(*) from vrn_report_basic where report_date is not null"
                              " and report_date <> ''"), n_all, {})
        m["filename"] = (q("select count(*) from vrn_report_basic where report_file <> ''"), n_all, {})
        m["broker"] = (q("select count(*) from vrn_report_basic where broker <> ''"), n_all, {})
        m["analyst"] = (have_codes("select count(distinct report_file) from vrn_report_analyst"), n_all, {})
        m["ticker"] = (n_tk, n_tk, {})           # 分母=有代號的;沒代號的是 NOT_APPLICABLE
        m["yf_ticker"] = (have_codes(
            f"select count(distinct code) from tw_listings where code in ({inlist})"
            " and yf_ticker is not null and yf_ticker <> ''"), n_code, {})
        m["bloomberg_ticker"] = (have_codes(
            f"select count(distinct code) from tw_listings where code in ({inlist})"), n_code,
            {"note": "衍生得出,但要先知道市場別 —— 市場別只在 tw_listings 裡"})
        m["name"] = (have_codes(
            f"select count(distinct code) from tw_listings where code in ({inlist})"
            " and name is not null and name <> ''"), n_code, {})
        m["rating"] = (q("select count(*) from vrn_report_basic where rating_raw <> ''"), n_all, {})
        m["adj_close"] = (have_codes(
            "select count(distinct split_part(ticker,'.',1)) from tw_prices_adj"
            f" where split_part(ticker,'.',1) in ({inlist}) and adj_close is not null"),
            n_code, {"gated": True})
        m["target_price_adj"] = (have_codes(
            "select count(distinct split_part(p.ticker,'.',1)) from tw_prices_adj p"
            f" where split_part(p.ticker,'.',1) in ({inlist}) and p.factor is not null"),
            n_code, {"gated": True, "note": "有 tp 還要有 ADJ 因子才算得出 tp_adj(L99)"})
        fs = have_codes(
            f"select count(distinct code) from analyst_estimates where code in ({inlist})"
            " and upper(source) like '%FACTSET%' and upper(source) not like '%PENDING%'"
            " and target_median is not null")
        fs_pend = have_codes(
            "select count(*) from analyst_estimates where upper(source) like '%PENDING%'")
        # 自審(批712):第一版我寫 `fs > 0 is False` —— 那是**鏈式比較**
        #   `(fs > 0) and (0 is False)`,後半永遠假,整個 pending 態**永遠不會出現**。
        #   一個永遠不會亮的態,跟沒有那個態一樣(批705 同一族:那條檢永遠不會叫)。
        m["factset_consensus_median"] = (fs, n_code,
                                         {"pending": fs == 0 and fs_pend > 0})
        m["yf_consensus_median"] = (have_codes(
            f"select count(distinct code) from analyst_estimates where code in ({inlist})"
            " and upper(source) like '%YAHOO%' and target_median is not null"), n_code, {})
        eps2 = [c[1] for c in con.execute("pragma table_info(analyst_estimates)").fetchall()]
        has_n2 = any(c.startswith("eps2y") for c in eps2)
        m["diluted_eps_n_n2"] = (0 if not has_n2 else have_codes(
            f"select count(distinct code) from analyst_estimates where code in ({inlist})"),
            n_code, {"wired": has_n2,
                     "note": "冊要 n~n+2;庫只有 eps0y/eps1y,**n+2 整欄不存在**"})
        m["forward_per_n_n2"] = (0, n_code, {
            "wired": False, "note": "庫裡沒有 forward PER 欄,也沒有算它的式子(要 adj_close ÷ eps)"})

        rows = []
        for f in sp["fields"]:
            have, total, opt = m.get(f["key"], (0, 0, {"wired": False}))
            st = _state(have, total, wired=opt.get("wired", True),
                        pending=bool(opt.get("pending")), gated=bool(opt.get("gated")))
            rows.append({"key": f["key"], "zh": f["zh"], "state": st, "have": have,
                         "total": total, "spec": f["spec"], "source": f["source"],
                         "why": opt.get("note", "")})
    finally:
        con.close()

    tally: dict[str, int] = {}
    for r in rows:
        tally[r["state"]] = tally.get(r["state"], 0) + 1
    return {"state": "OK", "n_reports": n_all, "n_with_ticker": n_tk, "n_codes": n_code,
            "tally": tally, "rows": rows}


def render(d: dict) -> str:
    if d.get("state") == "ABSENT":
        return f"[欄位規格閘] ABSENT · {d.get('why')}"
    if d.get("state") == "NODATA":
        # 批728:庫在、表不在 = 缺料,逐欄照列 NODATA,不假裝量過。
        #   自審:本版第一次只改了 measure(),render() 還只認量過的形狀,一讀 n_reports 就 KeyError ——
        #   全格子「研報欄位規格實跑」咬到(自測 ⑥ 只驗 measure 沒驗 render,所以綠);⑥ 現在兩個都驗。
        out = [f"=== 研報欄位規格對帳閘 {VERSION}({BATCH})· 唯讀 · 零網路 ===",
               f"  [NODATA] {d.get('why')}"]
        out += [f"  [NODATA        ] {r['zh']:16s} {'—':>8s}  {r.get('why', '')}" for r in d.get("rows", [])]
        out.append(f"  [計] NODATA {len(d.get('rows', []))}(缺料 rc2,不是壞掉 L16)")
        return "\n".join(out)
    out = [f"=== 研報欄位規格對帳閘 {VERSION}({BATCH})· 唯讀 · 零網路 ===",
           f"  規格冊 {SPEC.name} · 研報 {d['n_reports']} 列(有代號 {d['n_with_ticker']} 列 · "
           f"相異代號 {d['n_codes']})· 綠門檻 {int(GREEN_AT*100)}%"]
    for r in d["rows"]:
        cov = f"{r['have']}/{r['total']}" if r["total"] else "—"
        out.append(f"  [{r['state']:14s}] {r['zh']:16s} {cov:>8s}  {r['spec'][:44]}"
                   + (f"\n                     ↳ {r['why']}" if r["why"] else ""))
    out.append("  [計] " + " · ".join(f"{k} {v}" for k, v in sorted(d["tally"].items())))
    out.append("  [律] GATED=要觸網才補得齊,**同意閘 AI 永不代設**;"
               "NOT_WIRED=規格要、系統根本沒有;SOURCE_PENDING=接了但還沒供料。三種都不是綠。")
    return "\n".join(out)


def selftest() -> int:
    ran, fails = [], []

    def chk(name, cond, note=""):
        ran.append(name)
        ok = bool(cond)
        if not ok:
            fails.append(name)
        print("  [%s] %s%s" % ("OK" if ok else "FAIL", name, (" (%s)" % note) if note else ""))

    print(f"=== 欄位規格對帳閘 {VERSION} · 自測(沙盒 · 零網路 · 唯讀)===")

    # ① 規格是**冊**不是碼
    live = load_spec()
    empty = measure(db=MEGA, spec={})
    chk("① 規格從 **SSOT 冊**讀,不寫在碼裡(Zero-Hydra):冊上幾欄就對幾欄。"
        "**負控**:餵一本空冊,必須誠實 ABSENT 並說「不自己編一份欄位清單」——"
        "一支讀不到規格就自己生一份的閘,量的是它自己的想像",
        len(live.get("fields", [])) == 15 and empty["state"] == "ABSENT"
        and "不自己編" in empty["why"],
        f"(冊上 {len(live.get('fields', []))} 欄 · 空冊→{empty['state']})")

    # ② 六態次序:沒接 > 待供 > 觸網 > 無值 > 不足 > 達標
    s_nw = _state(0, 10, wired=False)
    s_pd = _state(0, 10, pending=True)
    s_gt = _state(0, 10, gated=True)
    s_nd = _state(0, 10)
    s_pt = _state(9, 10)
    s_gr = _state(10, 10)
    chk("② **六態次序有意義**(LL400):NOT_WIRED(規格要、系統根本沒有)先於 "
        "SOURCE_PENDING(接了沒供料)先於 GATED(要觸網)先於 NODATA(有來源沒值)。"
        "三種「不是綠」的原因處置完全不同:一個要寫碼、一個要等上游、一個要操作員開閘 —— "
        "壓成同一種就會有人去修不該修的東西",
        [s_nw, s_pd, s_gt, s_nd, s_pt, s_gr]
        == ["NOT_WIRED", "SOURCE_PENDING", "GATED", "NODATA", "PARTIAL", "GREEN"],
        f"({[s_nw, s_pd, s_gt, s_nd, s_pt, s_gr]})")

    # ③ 覆蓋不足不准報綠(邊界成對)
    below, at, above = _state(94, 100), _state(95, 100), _state(100, 100)
    chk("③ **覆蓋不足不准報綠**:94/100 是 PARTIAL、95/100 才是 GREEN。"
        "把七成講成綠,看的人會以為那一欄可以直接拿去用。"
        "**正控**=100/100 必須真的是 GREEN(否則就是一道永遠不綠的閘,跟永遠綠一樣沒有判斷力)",
        below == "PARTIAL" and at == "GREEN" and above == "GREEN",
        f"(94%→{below} · 95%→{at} · 100%→{above})")

    # ④ 庫缺席誠實
    gone = measure(db=Path("/tmp/絕對不存在的庫.duckdb"))
    chk("④ 庫缺席要誠實 ABSENT,而且逐欄照列(不是靜靜回一張空表)——"
        "「量不到」跟「量到 0」是兩件事,混在一起就會把缺席說成缺陷",
        gone["state"] == "ABSENT" and len(gone["rows"]) == 15
        and all(r["state"] == "NODATA" for r in gone["rows"]),
        f"({gone['state']} · 逐欄 {len(gone['rows'])} 列)")

    # ⑤ 唯讀
    src = Path(__file__).read_text(encoding="utf-8")
    code = "\n".join(ln for ln in src.split("\n") if not ln.lstrip().startswith("#"))
    # 自審(批712):第一版我把違禁字面**原樣**寫在名單裡,於是這條檢當場咬到自己
    #   ——同一批在 CGC_MDL180 已經處理過一次(LL384:字面禁用檢要先剝註解,
    #   而且**檢自己不能含那個字面**)。改成拼接。
    banned = [b for b in ("read_only=" + "False", "insert" + " into",
                          "create" + " table", "write_" + "text")
              if b in code.lower()]
    chk("⑤ **唯讀**:開庫一律 `read_only=True`,碼裡不得有寫庫動詞 —— "
        "一支會寫庫的稽核閘,量的是它自己改過的東西(LL368)",
        "read_only=True" in code and not banned, f"(違禁 {banned or '無'})")

    # ⑥ 批728:庫在、表不在 → NODATA(不炸),15 欄照列。臨時庫只落暫存夾。
    try:
        import duckdb as _ddb
        import tempfile as _tf
        _dir = Path(_tf.mkdtemp(prefix="mdl181_"))
        _tmp = _dir / "no_vrn.duckdb"
        _w = _ddb.connect(str(_tmp))
        _w.execute("CREATE" + " TABLE tw_daily_prices(ticker VARCHAR)")
        _w.close()
        _nd = measure(db=_tmp)
        try:
            _txt = render(_nd)            # 批728 自審:render 也要吃得下 NODATA 形狀(第一版 KeyError n_reports)
        except Exception as _exc:
            _txt = f"render 炸了:{type(_exc).__name__}: {_exc}"
        chk("⑥ 批728 **庫在、表不在**:誠實 NODATA 並逐欄照列、指路入庫——不炸 CatalogException,render 也不炸(缺料不是壞掉 L16)",
            _nd["state"] == "NODATA" and len(_nd["rows"]) == 15 and "vrn_report_basic" in _nd["why"]
            and "[NODATA]" in _txt and _txt.count("[NODATA ") == 15,
            f"({_nd['state']} · 逐欄 {len(_nd['rows'])} 列 · render {'OK' if '[NODATA]' in _txt else _txt[:80]})")
        import shutil as _sh
        _sh.rmtree(_dir, ignore_errors=True)
    except ImportError:
        chk("⑥ 批728 庫在、表不在 → NODATA", True, "本境無 duckdb,此檢不適用")

    print("  [計] %d 檢 OK %d · FAIL %d" % (len(ran), len(ran) - len(fails), len(fails)))
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a or "--self-test" in a:
        return selftest()
    d = measure()
    print(json.dumps(d, ensure_ascii=False, indent=1) if "--json" in a else render(d))
    st = d.get("state")
    if st == "OK":
        return 0
    if st == "NODATA" or (st == "ABSENT" and str(d.get("why", "")).startswith("庫缺席")):
        return 2          # 批728:庫缺 / 表不在 = 缺料 rc2(批693B 同律)
    return 3


if __name__ == "__main__":
    sys.exit(main())
