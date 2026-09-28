#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG230_ForwardValuation v0100 — 指數 Forward PER / EPS 唯一正主(兩支附件整合:A 的廣度 × B 的嚴謹)

操作員 2026-09-28:「FACTSET 對指數 S&P 500 都有公布 FORWARD EARNING 在新聞稿,顧可以倒這兩個附件實測一下,各有優劣,
則整合唯一,從 VCGC 去登錄編號,加入加速器及網路工具,實測優化修正使用」。

兩支附件原位元收在 references/intake/VIA_ForwardValuation_b20260928(MANIFEST 記 sha;本支只載入、在記憶體裡補丁,不改原檔):
  A = via_fwdper_free4_fetch v001   廣度:FactSet 文章 · S&P DJI sp-500-eps-est.xlsx · MSCI 8 指數 · 日經 予想PER + trailing PBR ·
                                    日頻長表 · 可比組(MSCI_NTM / US_CONSENSUS / JP_COMPANY)· 證據欄 · 八道口徑閘。
      缺點:FactSet 只一條 regex;直接 urllib 外呼、yfinance 後備也直連(繞過同意閘)。
  B = forward_valuation_vintage v2.2 嚴謹:FactSet 文章正規化 + 抽取信心度 + 截止日判定(date-only / approximate 不得直升)·
                                    point-in-time vintage · 不外洩未來 · 只增不覆寫。缺點:只 FactSet 一源;pandas 3.x merge_asof 精度 bug。

整合(本支):
  ① A 負責抓四源(外呼一律改走統包網路工具 SUP_MDL740 尾版 curl_bytes:雙閘在工具裡,閘沒開 = DENY 零外呼;yfinance 後備封掉)
  ② FactSet 那一條用 B 的解析器複核 A 抓回來的同一份原文:
       B ready 且與 A 差 ≤ 發布增量 → 保留 A 的值,旗標 B_CONFIRMED:<狀態>
       B ready 但與 A 不符           → 兩邊都不採:值清空、證據 Pending、旗標 A_B_CONFLICT(不挑一邊、不平均)
       B 要複核(date-only/低信心…) → 值清空、Pending、旗標 B_GATE:<狀態>(B 的「只有完整截止對齊才升格」)
       原文是 PDF(B 不讀 PDF)       → 保留 A 的值,旗標 B_UNCHECKED_PDF(照實標,不假裝複核過)
  ③ B 的 pandas 3.x 精度 bug 在載入時補(兩邊日期統一 datetime64[ns]);B 的 vintage / 重建 / 比對函式原樣可用(module B)
  ④ 入庫走正典 VIA_LibCanon.UTILS.upsert_rows:vdf_global_market.duckdb
       fwd_valuation_daily  鍵 date+index+source+metric+method+as_of_source(每個 vintage 各留一列 = point-in-time,只增不覆寫)
       fwd_valuation_factset_candidates  鍵 raw_document_hash(B 的候選全欄,含信心度與截止狀態)
     Pending(沒有值)的列只進 CSV / 稽核,不進庫。
  ⑤ 輸出:VIA_Reports/fwdval/(A 的 CSV / parquet / HTML / 稽核 JSON)+ 本支 FWDVAL_latest.json

用法(經 VCGC;VIA_FROM_VCGC=YES):
  python VDF_ENG230_ForwardValuation_v0100.py status
  python VDF_ENG230_ForwardValuation_v0100.py run [--days 400] [--dry]
  python VDF_ENG230_ForwardValuation_v0100.py --selftest       # A 23 檢 + B 20 檢(補丁後)+ 整合檢;零外呼
非投資建議。forward 一律 Estimated_ThirdParty / Inferred,抓不到 = Pending,不杜撰。
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
# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import contextlib
import dataclasses
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
INTAKE = VDF / "references" / "intake" / "VIA_ForwardValuation_b20260928"
OUT_DB = VDF / "output_hub" / "mega" / "vdf_global_market.duckdb"
OUT_DIR = VIA / "VIA_Reports" / "fwdval"
T_DAILY = "fwd_valuation_daily"
T_CAND = "fwd_valuation_factset_candidates"
K_DAILY = ["date", "index", "source", "metric", "method", "as_of_source"]
ENGINE_TAG = "VDF_ENG230_ForwardValuation_v" + Path(__file__).stem.rsplit("_v", 1)[-1]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def manifest_ok() -> tuple:
    """收容件位元沒被動過(對 MANIFEST 的 sha)。回 (ok, 說明)。"""
    mf = INTAKE / "MANIFEST.json"
    if not mf.is_file():
        return False, "MANIFEST 不在"
    m = json.loads(mf.read_text(encoding="utf-8"))
    bad = [n for n, f in (m.get("files") or {}).items()
           if not (INTAKE / n).is_file() or hashlib.sha256((INTAKE / n).read_bytes()).hexdigest() != f.get("sha256")]
    return (not bad), ("原位元相符" if not bad else "被改過或不在:" + ", ".join(bad))


A = _load(INTAKE / "via_fwdper_free4_fetch.py", "vdf_eng230_src_a_free4")
B = _load(INTAKE / "forward_valuation_vintage_v2_2.py", "vdf_eng230_src_b_vintage")

# ---- 補丁 ③:B 的 pandas 3.x merge_asof 精度(不改原檔,只換記憶體裡這一支)
_B_PREP = B._prepare_asof_inputs


def _prepare_asof_inputs_ns(observations, anchors, entity_column):
    obs, anc = _B_PREP(observations, anchors, entity_column)
    obs["observation_date"] = obs["observation_date"].astype("datetime64[ns]")
    for c in ("available_from_date", "source_as_of_date"):
        anc[c] = anc[c].astype("datetime64[ns]")
    return obs, anc


B._prepare_asof_inputs = _prepare_asof_inputs_ns


def net_tool():
    hits = sorted((VIA / "supportive modules" / "network").glob("SUP_MDL740_NetUnified_v*.py"))
    return _load(hits[-1], "via_net_for_eng230") if hits else None


class VIANetTransport(A.Transport):
    """A 的 Transport 換成統包網路工具:每一趟都走 curl_bytes(雙閘);原文留在 bodies 給 B 複核。"""

    def __init__(self, net, timeout=25):
        super().__init__(timeout=timeout, tries=1)
        self.net, self.bodies, self.denied = net, {}, 0

    def get(self, url: str, binary=False):
        if self.net is None or not hasattr(self.net, "curl_bytes"):
            self.log.append((url, "ERR", "網路工具缺 curl_bytes"))
            raise RuntimeError("網路工具缺(要 SUP_MDL740 v0114+)")
        rb = self.net.curl_bytes(url, headers=dict(A.UA), timeout=self.timeout, follow=True)
        st = rb.get("state")
        if st == "DENY":
            self.denied += 1
            self.log.append((url, "DENY", 0))
            raise RuntimeError("DENY:同意閘沒開 " + url)
        if st != "OK":
            self.log.append((url, "ERR", str(rb.get("note", ""))[:80]))
            raise RuntimeError(f"{st} {url}")
        data = rb.get("data") or b""
        self.bodies[url] = data
        self.log.append((url, "OK", len(data)))
        return data if binary else data.decode("utf-8", "replace")


@contextlib.contextmanager
def _no_direct_yfinance():
    """A 的價格後備會 import yfinance 直連(繞過同意閘)→ 執行期間封掉,結束還原。"""
    had = "yfinance" in sys.modules
    keep = sys.modules.get("yfinance")
    sys.modules["yfinance"] = None          # import yfinance → ImportError → A 照實回空
    try:
        yield
    finally:
        if had:
            sys.modules["yfinance"] = keep
        else:
            sys.modules.pop("yfinance", None)


def factset_gate(rows: list, bodies: dict, retrieved: datetime | None = None) -> dict:
    """② 用 B 複核 A 的 FactSet 列。就地改 rows;回 {status, candidate, action}。"""
    fs = [r for r in rows if r.source == "FACTSET"]
    direct = next((r for r in fs if r.metric == "FWD_PER" and r.method == "DIRECT" and r.value is not None), None)
    if direct is None:
        return {"action": "NONE", "status": "A 沒抓到 FactSet", "candidate": None}
    body = bodies.get(direct.source_url)
    if body is None:
        return {"action": "UNCHECKED", "status": "原文不在(沒經本支傳輸層)", "candidate": None}
    if body[:4] == b"%PDF":
        for r in fs:
            r.quality_flag = (r.quality_flag + "|B_UNCHECKED_PDF").strip("|")
        return {"action": "UNCHECKED_PDF", "status": "B 不讀 PDF;保留 A 值並標明", "candidate": None}
    try:
        doc = B.extract_factset_article_document(index_id="SP500", source_url=direct.source_url,
                                                 raw_html=body.decode("utf-8", "replace"),
                                                 retrieved_ts_utc=retrieved or datetime.now(timezone.utc))
        cand = B.parse_factset_forward_valuation(doc)
    except ValueError as e:
        # B 拒收(頁不是 S&P 500 / 沒發布時間時 B 自己的時序檢查會拋 —— 見 MANIFEST known_issues)→ 不升格
        flag = "B_REJECT:" + str(e)[:60]
        for r in fs:
            r.value, r.evidence, r.quality_flag = None, "Pending", flag
        return {"action": "GATE", "status": flag, "candidate": None}
    st = cand.extraction_status
    ready = st.startswith("ready")
    tol = max(float(cand.published_forward_pe_increment or 0.1), 0.1) + 1e-9
    agree = ready and cand.published_forward_pe is not None and abs(cand.published_forward_pe - float(direct.value)) <= tol
    if agree:
        action, flag = "CONFIRMED", f"B_CONFIRMED:{st}"
        for r in fs:
            r.quality_flag = (r.quality_flag + "|" + flag).strip("|")
    else:
        action = "CONFLICT" if ready else "GATE"
        flag = f"A_B_CONFLICT:A={direct.value}/B={cand.published_forward_pe}" if ready else f"B_GATE:{st}"
        for r in fs:
            r.value, r.evidence, r.quality_flag = None, "Pending", flag
    return {"action": action, "status": st, "candidate": cand, "confidence": cand.extraction_confidence}


def _cand_row(c) -> dict:
    d = dataclasses.asdict(c)
    for k, v in list(d.items()):
        if isinstance(v, (datetime, date)):
            d[k] = v.isoformat()
        elif isinstance(v, tuple):
            d[k] = json.dumps(list(v), ensure_ascii=False)
    d.pop("raw_html", None)
    return d


def persist(rows: list, gate: dict, db: Path = OUT_DB) -> dict:
    """④ 只存有值的列(Pending 不進庫);每個 vintage 各留一列(鍵含 as_of_source)。"""
    keep = [dataclasses.asdict(r) for r in rows if r.value is not None]
    out = {"daily_new": 0, "daily_total": 0, "cand_new": 0}
    if keep:
        db.parent.mkdir(parents=True, exist_ok=True)
        n, t = _LIB.UTILS.upsert_rows(db, T_DAILY, keep, K_DAILY, counts=True)
        out.update(daily_new=int(n), daily_total=int(t))
    if gate.get("candidate") is not None:
        db.parent.mkdir(parents=True, exist_ok=True)
        n, _t = _LIB.UTILS.upsert_rows(db, T_CAND, [_cand_row(gate["candidate"])], ["raw_document_hash"], counts=True)
        out["cand_new"] = int(n)
    return out


def run(days: int = 400, net=None, db: Path = OUT_DB, out_dir: Path = OUT_DIR, dry: bool = False, tp=None) -> dict:
    ok, why = manifest_ok()
    if not ok:
        return {"engine": ENGINE_TAG, "state": "RED", "why": "收容件 " + why}
    tp = tp or VIANetTransport(net if net is not None else net_tool())
    with _no_direct_yfinance():
        rows, gates, paths = A.run(tp, days, str(out_dir), open_html=False)
    gate = factset_gate(rows, getattr(tp, "bodies", {}))
    gates = A.gate(rows)                      # 複核後再過一次 A 的八道口徑閘
    valued = [r for r in rows if r.value is not None]
    stored = {"daily_new": 0, "daily_total": 0, "cand_new": 0} if dry else persist(rows, gate, db)
    by_src = {}
    for r in rows:
        s = by_src.setdefault(r.source, {"rows": 0, "valued": 0, "pending": 0})
        s["rows"] += 1
        s["valued"] += r.value is not None
        s["pending"] += r.evidence == "Pending"
    denied = getattr(tp, "denied", 0)
    state = "DENY" if denied and not [r for r in valued if r.source != "STOOQ/YF"] else ("OK" if all(g[1] for g in gates) else "RED")
    rep = {"engine": ENGINE_TAG, "state": state, "rows": len(rows), "valued": len(valued), "by_source": by_src,
           "factset_gate": {k: v for k, v in gate.items() if k != "candidate"}, "gates": [[n, ok, m] for n, ok, m in gates],
           "stored": stored, "dry": dry, "denied": denied, "outputs": paths,
           "transport": [list(x) for x in getattr(tp, "log", [])][-40:]}
    out_dir.mkdir(parents=True, exist_ok=True)
    (Path(out_dir) / "FWDVAL_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return rep


def status(db: Path = OUT_DB) -> dict:
    if not Path(db).is_file():
        return {"state": "NODATA", "why": f"{db.name} 不在"}
    import duckdb
    con = duckdb.connect(str(db), read_only=True)
    try:
        tabs = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        if T_DAILY not in tabs:
            return {"state": "NODATA", "why": f"{T_DAILY} 還沒建(先 run;同意閘是你的手)"}
        rows = con.execute(f'SELECT source, "index", metric, COUNT(*), MAX(date) FROM "{T_DAILY}" GROUP BY 1,2,3 ORDER BY 1,2,3').fetchall()
        return {"state": "OK", "series": [list(r) for r in rows]}
    finally:
        con.close()


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "只經 VCGC(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
        return 2
    verb = next((x for x in a if not x.startswith("-")), "status")
    if verb == "status":
        s = status()
        print(json.dumps(s, ensure_ascii=False, indent=1))
        return 0 if s["state"] == "OK" else 2
    if verb == "run":
        days = int(a[a.index("--days") + 1]) if "--days" in a and a.index("--days") + 1 < len(a) else 400
        r = run(days=days, dry="--dry" in a)
        print(json.dumps({k: r[k] for k in ("state", "rows", "valued", "by_source", "factset_gate", "stored", "denied") if k in r}, ensure_ascii=False, indent=1, default=str))
        print(f"  [FwdVal] {r['state']} · 列 {r.get('rows')} · 有值 {r.get('valued')} · FactSet {r.get('factset_gate', {}).get('action')} · 新增 {r.get('stored', {}).get('daily_new')}"
              f" · 報告 {OUT_DIR / 'FWDVAL_latest.json'}")
        return {"OK": 0, "DENY": 4}.get(r["state"], 1)
    print(__doc__)
    return 2


# ---------------------------------------------------------------- 自測(零外呼:假網路工具 + 暫存庫)
class _FakeNet:
    def __init__(self, table: dict, deny: bool = False):
        self.table, self.deny, self.calls = table, deny, []

    def curl_bytes(self, url, headers=None, timeout=30, follow=True):
        self.calls.append(url)
        if self.deny:
            return {"state": "DENY", "note": "gate"}
        for k, v in self.table.items():
            if k in url:
                return {"state": "OK", "data": v if isinstance(v, bytes) else v.encode("utf-8")}
        return {"state": "FAIL", "note": "no fixture"}


def _fixtures(article: str) -> dict:
    today = A.TODAY
    from datetime import timedelta
    px = "Date,Open,High,Low,Close,Volume\n" + "\n".join(
        f"{(today - timedelta(days=i)).isoformat()},1,1,1,{6900 - i},1" for i in range(40, -1, -1) if (today - timedelta(days=i)).weekday() < 5)
    return {"stooq.com/q/d/l/?s=^spx": px, "stooq.com/q/d/l/?s=^nkx": px.replace("69", "48"),
            "insight.factset.com/topic": '<a href="https://insight.factset.com/sp-500-earnings-season-update-sep-2026">x</a>',
            "sp-500-earnings-season-update": article}


def selftest() -> int:
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    ok, why = manifest_ok()
    chk("① 兩支收容件原位元相符(本支只載入、記憶體補丁)", ok, why)
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as td:
        os.chdir(td)
        try:
            with _no_direct_yfinance():
                ra = A.selftest()
        finally:
            os.chdir(cwd)
    chk("② 附件 A 自測(23 檢)原樣通過", ra == 0)
    rb = B.run_self_test()
    chk("③ 附件 B 自測在補丁後通過(原檔在 pandas 3.x 會 MergeError)", rb.get("status") == "pass", f"{len(rb.get('tests', {}))} 項")
    chk("④ 補丁只換記憶體:收容原檔仍含原寫法", 'pd.to_datetime(obs["observation_date"])\n' in (INTAKE / "forward_valuation_vintage_v2_2.py").read_text(encoding="utf-8"))
    ready_article = """<html><head><title>S&amp;P 500 Earnings Season Update</title>
      <meta property="article:published_time" content="2026-09-26T12:00:00+00:00"></head><body>
      <p>On September 25, the forward 12-month P/E ratio for the S&amp;P 500 was 22.4. This forward 12-month P/E ratio
      was based on a closing price of 6,860.00 and a forward 12-month EPS estimate of $306.25.</p></body></html>"""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        fake = _FakeNet(_fixtures(ready_article))
        r = run(days=30, net=fake, db=td / "gl.duckdb", out_dir=td / "out")
        fg = r["factset_gate"]
        chk("⑤ A 抓 → B 複核:完整截止對齊的文章 = B_CONFIRMED,A 值保留", fg["action"] == "CONFIRMED" and r["by_source"]["FACTSET"]["valued"] >= 1,
            f"{fg['action']} · {fg['status']} · conf {fg.get('confidence')}")
        chk("⑥ 外呼全走統包工具(假工具收到每一趟;沒有直連)", len(fake.calls) >= 3 and r["stored"]["daily_new"] > 0, f"{len(fake.calls)} 趟 · 新增 {r['stored']['daily_new']}")
        r2 = run(days=30, net=fake, db=td / "gl.duckdb", out_dir=td / "out")
        chk("⑦ 正典 upsert 冪等:再跑一次新增 0(每個 vintage 一列)", r2["stored"]["daily_new"] == 0 and r2["stored"]["daily_total"] == r["stored"]["daily_total"],
            f"{r['stored']['daily_total']} → {r2['stored']['daily_total']}")
        dateonly = ready_article.replace('<meta property="article:published_time" content="2026-09-26T12:00:00+00:00">', "").replace("On September 25, the", "The")
        r3 = run(days=30, net=_FakeNet(_fixtures(dateonly)), db=td / "g3.duckdb", out_dir=td / "o3")
        chk("⑧ B 拒收 / 要複核(沒有發布時間)→ FactSet 列全改 Pending、值清空,不進庫", r3["factset_gate"]["action"] == "GATE"
            and r3["by_source"]["FACTSET"]["valued"] == 0, f"{r3['factset_gate']['action']} · {r3['factset_gate']['status']}")
        conflict = ready_article.replace("was 22.4.", "was 22.4.").replace("The forward", "The forward")
        tp = VIANetTransport(_FakeNet(_fixtures(conflict)))
        rows = [A.R(date="2026-09-25", as_of_source="2026-09-25", index="S&P 500", source="FACTSET", metric="FWD_PER", value=25.0, unit="x",
                    method="DIRECT", basis="NTM_CONSENSUS", comparable_group="US_CONSENSUS", evidence="Estimated_ThirdParty",
                    staleness_days=0, quality_flag="OK", source_url="https://insight.factset.com/sp-500-earnings-season-update-sep-2026")]
        tp.bodies[rows[0].source_url] = ready_article.encode()
        g = factset_gate(rows, tp.bodies)
        chk("⑨ A=25.0 · B=22.4 不符 → A_B_CONFLICT,兩邊都不採(不挑、不平均)", g["action"] == "CONFLICT" and rows[0].value is None and rows[0].evidence == "Pending", rows[0].quality_flag)
        deny = _FakeNet({}, deny=True)
        r4 = run(days=30, net=deny, db=td / "g4.duckdb", out_dir=td / "o4")
        chk("⑩ 同意閘沒開 = DENY:零寫入、庫沒建", r4["state"] == "DENY" and not (td / "g4.duckdb").exists(), f"denied {r4['denied']}")
        chk("⑪ 八道口徑閘複核後仍全過", all(x[1] for x in r["gates"]), " · ".join(x[0] for x in r["gates"] if not x[1]) or "8/8")
        with _no_direct_yfinance():
            try:
                import yfinance  # noqa: F401
                blocked = False
            except ImportError:
                blocked = True
        chk("⑫ 執行期間 yfinance 直連被封(結束還原)", blocked and sys.modules.get("yfinance", "gone") is not None)
    keep = os.environ.pop("VIA_FROM_VCGC", None)
    denied = main(["status"]) == 2
    if keep is not None:
        os.environ["VIA_FROM_VCGC"] = keep
    chk("⑬ 不經 VCGC 就拒跑", denied)
    ok = all(results)
    print(f"  [計] {ENGINE_TAG} 自測 {sum(results)}/{len(results)} · {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
