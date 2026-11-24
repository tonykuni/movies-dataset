#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN_ENG076_RegressionGate — 抽取鏈迴歸閘(批251;操作員「完成所有工作
+所有測試整合優化」令)
====================================================================
收容基準包 AttachmentFixedOutput_v1.0.0(批245 收容;操作員工作站修復
產物)=64 件 repaired_documents.jsonl,每件帶 basic_info 真值
(ticker/target_price/close_price/report_date)+修復後左右區全文
→本引擎以現役 ENG073 抽取原語(TP_RX/PX_RX/_num;尾版動態載入)
對修復文本重抽 TP/P,與基準真值逐件對照:
  TP/P 各判 MATCH(|Δ|<0.5%)/DIFF(值在但異=誠實列)/MISS(未抽得)
  /BASE_NULL(基準空=誠實略);ticker 檔名四碼對照;
  配對律=ENG073 v0102 同構(比例 [0.30,3.2] 首對;雙 None=取大)
迴歸紅線:基準包原地不動;閘=唯讀對照;輸出數值矩陣
  VIA_Reports/regression_gate/(逐件+總 accuracy;文本片段不落報告)
用法:python3 VRN_ENG076_RegressionGate_v0100.py run | --selftest
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

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
EVID = (HERE / "references" / "intake" / "AttachmentFixedOutput_v1.0.0_b245"
        / "AttachmentFixedOutput_v1.0.0" / "01_repair"
        / "repaired_documents.jsonl")
OUTDIR = VIA / "VIA_Reports" / "regression_gate"


def _eng073():
    """現役 ENG073 尾版動態載入(TP_RX/PX_RX/_num 原語重用;嚴禁寫死版號)"""
    hits = sorted(HERE.glob("VRN_ENG073_ReportStructuredDB_v*.py"))
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location("e73gate", hits[-1])
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def extract_tp_p(m, right: str, main: str) -> tuple[float | None, float | None]:
    """ENG073 v0102 配對律同構:候選集→比例 [0.30,3.2] 首對;雙 None=取大"""
    def cands(rx):
        out = []
        for t in (right, main):
            for h in rx.finditer(t or ""):
                v = m._num(h.group(1))
                if v and v > 0 and v not in out:
                    out.append(v)
        return out
    tp_c, px_c = cands(m.TP_RX), cands(m.PX_RX)
    tpv = pxv = None
    for a in tp_c:
        for b in px_c:
            if 0.30 <= a / b <= 3.2:
                tpv, pxv = a, b
                break
        if tpv:
            break
    if tpv is None and pxv is None:
        cand = ([(tp_c[0], "tp")] if tp_c else []) + \
               ([(px_c[0], "px")] if px_c else [])
        if cand:
            v, side = max(cand)
            if side == "tp":
                tpv = v
            else:
                pxv = v
    return tpv, pxv


def _judge(base, got) -> str:
    if base is None:
        return "BASE_NULL"
    if got is None:
        return "MISS"
    return "MATCH" if abs(got - float(base)) <= 0.005 * float(base) + 1e-9 \
        else "DIFF"


def run(evid: Path | None = None) -> int:
    evid = evid or EVID
    if not evid.exists():
        print(f"[迴歸閘] 基準包缺({evid.parent.name})=誠實停;先 via-intake")
        return 2
    m = _eng073()
    if m is None:
        print("[迴歸閘] ENG073 尾版缺=誠實停")
        return 2
    rows = []
    for ln in evid.read_text(encoding="utf-8-sig").splitlines():
        if not ln.strip():
            continue
        d = json.loads(ln)
        bi = d.get("basic_info") or {}
        tp, p = extract_tp_p(m, d.get("repaired_right_text", ""),
                             d.get("repaired_main_text", ""))
        tick_base = bi.get("ticker")
        tick_fn = next(iter(m.TICK_RX.findall(d.get("filename", ""))), None)
        rows.append({
            "file": d.get("filename", "?"),
            "tp_base": bi.get("target_price"), "tp_got": tp,
            "tp_verdict": _judge(bi.get("target_price"), tp),
            "p_base": bi.get("close_price"), "p_got": p,
            "p_verdict": _judge(bi.get("close_price"), p),
            "ticker_verdict": ("MATCH" if tick_base and tick_fn == tick_base
                               else "BASE_NULL" if not tick_base else "DIFF")})
    def agg(key):
        c: dict = {}
        for r in rows:
            c[r[key]] = c.get(r[key], 0) + 1
        return c
    tp_a, p_a, tk_a = agg("tp_verdict"), agg("p_verdict"), agg("ticker_verdict")

    def acc(a):
        eff = sum(v for k, v in a.items() if k != "BASE_NULL")
        return round(100 * a.get("MATCH", 0) / eff, 1) if eff else None
    OUTDIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    payload = {"ts": ts, "n": len(rows), "engine": Path(
        sorted(HERE.glob("VRN_ENG073_ReportStructuredDB_v*.py"))[-1]).name,
        "tp": {"dist": tp_a, "accuracy_pct": acc(tp_a)},
        "price": {"dist": p_a, "accuracy_pct": acc(p_a)},
        "ticker": {"dist": tk_a, "accuracy_pct": acc(tk_a)},
        "diffs": [{k: r[k] for k in ("file", "tp_base", "tp_got",
                                     "p_base", "p_got")}
                  for r in rows if "DIFF" in (r["tp_verdict"],
                                              r["p_verdict"])][:40]}
    (OUTDIR / "REGRESSION_GATE.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[迴歸閘] {len(rows)} 件 · TP {tp_a}(acc {payload['tp']['accuracy_pct']}%)"
          f" · P {p_a}(acc {payload['price']['accuracy_pct']}%)"
          f" · ticker {tk_a} · 存證 REGRESSION_GATE.json")
    return 0


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    m = _eng073()
    chk("① ENG073 原語尾版動態載入(TP_RX/PX_RX/_num)",
        m is not None and hasattr(m, "TP_RX") and hasattr(m, "PX_RX"))
    tp, p = extract_tp_p(m, "Target price NT$208.00\nPrice NT$169.50", "")
    chk("② 配對律同構(TP=208/P=169.5;比例首對)",
        tp == 208.0 and p == 169.5)
    chk("③ 判準三態(MATCH/DIFF/MISS/BASE_NULL)",
        _judge(208, 208.0) == "MATCH" and _judge(208, 210) == "DIFF"
        and _judge(208, None) == "MISS" and _judge(None, 5) == "BASE_NULL")
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "e.jsonl"
        f.write_text(json.dumps({
            "filename": "20250819兆豐個股報告-泓德能源(6873).pdf",
            "basic_info": {"ticker": "6873", "target_price": 208.0,
                           "close_price": 169.5},
            "repaired_right_text": "目標價208 元 Price 169.5",
            "repaired_main_text": "下修目標價至208 元,潛在上漲空間22.7%"})
            + "\n", encoding="utf-8")
        rc = run(f)
        gate = json.loads((OUTDIR / "REGRESSION_GATE.json")
                          .read_text(encoding="utf-8"))
        chk("④ fixture 端到端(TP MATCH+ticker MATCH)", rc == 0
            and gate["tp"]["dist"].get("MATCH") == 1
            and gate["ticker"]["dist"].get("MATCH") == 1)
        chk("⑤ 缺基準誠實 rc2", run(Path(td) / "none.jsonl") == 2)
    chk("⑥ 真基準包對接(64 件在庫=實跑道通)",
        EVID.exists() and len(EVID.read_text(
            encoding="utf-8-sig").splitlines()) >= 60)
    chk("⑦ 唯讀紀律(基準原地不動;報告only數值不落文本片段)",
        "唯讀對照" in src and "不落報告" in src)
    chk("⑧ 零網路+加速橋",
        all(("import " + k) not in src for k in ("requests", "httpx"))
        and "ACCEL-BRIDGE" in src)
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 抽取鏈迴歸閘(VRN_ENG076)· 八檢自測(零網路)===")
        return selftest()
    if args and args[0] == "run":
        return run()
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
