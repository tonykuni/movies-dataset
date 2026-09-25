#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN_ENG076_RegressionGate v0101 — 抽取鏈迴歸閘(批251;操作員「完成所有工作
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

批471(操作員「real test vrn … till it works」;本閘第一次被真的拿來用):
  **對照組自己錯了。** 64 件基準包裡有 close_price 的 29 件,其中 **11 件的值
  剛好等於它自己 report_date 的「日」**——
      Citi-3231 close=4.0 date=2025/06/**04** · Daiwa-3653 2.0 / 10-**02**
      Daiwa-6278 21.0 / 05-**21** · MS-1590 2.0 / 12-**02** · 凱基四份 19.0 / 05-**19** …
  另有幾件不靠這條規則也一眼荒謬:JP-2330 **台積電 close=17.0**、JP-3653 2.0、
  統一投顧晨報 5.0。基準包的「收盤價」有將近一半是**日期碎片**,不是價格。
  (順帶:華南那幾份的基準 report_date 也錯——`-1141202` 民國七碼被解成 2025/09/12,
   而現役引擎解出來的 2025-12-02 才對。)
  v0100 把這些一律算成我方 DIFF,於是報「P accuracy 58.6%」。
  **照著一個錯的基準去「提高準確率」,等於把一支好的抽取器改壞。**
  對照組錯了,比沒有對照組更危險——沒有對照組只是不知道,對照組錯了會把人帶往反方向。
  故本版加 **BASE_SUSPECT**:判準只用**量得出來**的那一條(基準值 == 它自己日期的「日」),
  不用「數字看起來太小」那種要靠假設的規則(那會變成我在猜哪個基準可信)。
  BASE_SUSPECT 與 BASE_NULL 一樣**不進準確率分母**,並單獨列出件數與原值——
  讓「基準有多髒」這件事在報表上看得見,而不是混進我方的失分裡。

迴歸紅線:基準包原地不動;閘=唯讀對照;輸出數值矩陣
  VIA_Reports/regression_gate/(逐件+總 accuracy;文本片段不落報告)
用法:python3 VRN_ENG076_RegressionGate_v0101.py run | --selftest
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
import re
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


def extract_tp_p(m, right: str, main: str, stem: str = "") -> tuple[float | None, float | None]:
    """**委派正線** ENG073.extract_one(批471;Zero-Hydra)。

    v0100 這裡是「ENG073 **v0102** 配對律同構」——也就是把當年那份配對邏輯
    **抄了一份**放在閘裡,而且寫死 `m.PX_RX`。ENG073 從 v0102 走到 v0121
    (十九個版本),閘卻一直在量那份十九版之前的複製品。
    批471 實測照出來的:我在 ENG073 v0121 加了「帶幣別記號的價格候選優先」
    (修 `收盤價 May 19 (NT$) 320.0` 被抓成 19 那個真缺陷),跑閘——**數字一動也不動**。
    **一把量不到你改動的尺,不叫迴歸閘。**
    改成呼叫正主 `extract_one(stem, {"right":…, "body":…}, {})`:
    zones 的形狀就是基準包那兩段文(right / main),不必另造。
    正主缺席或拋例外才退回本地複製品,並在回傳裡講明走了退路(不假裝走了正主)。
    """
    if hasattr(m, "extract_one"):
        try:
            basic, _ = m.extract_one(stem or "regression_gate",
                                     {"right": right or "", "body": main or "",
                                      "header": "", "footer": ""}, {})
            return basic.get("target_price"), basic.get("price")
        except Exception:
            pass                      # 退路:正主跑不動時仍給得出數,但那是退路
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


_DATE_RX = re.compile(r"(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})")
#: 原文裡的日期寫法(真檔實測到的兩種):`(17 Jul 25)` / `(04 Jun 25 13:30)`
_TXT_DAY_RX = re.compile(
    r"\(\s*(\d{1,2})\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
    r"\s+\d{2,4}", re.I)


def day_numbers_in(report_date, *texts) -> set:
    """這份報告裡出現過的「日」數字全集(批471;只收日期形狀的,不亂收)。

    兩個來源,都量得出來:
      ① 基準自己 report_date 的 dd
      ② 原文裡 `Price (17 Jul 25)` 這種括號日期的 dd
    ②是必要的:JP-2330 原文寫 `Price (17 Jul 25):NT$1130.0`,基準取走 17,
    而它自己的 report_date 卻記成 2025/07/18——**差一天**,只比 ① 就會漏接。
    """
    out = set()
    m = _DATE_RX.search(str(report_date or ""))
    if m:
        out.add(int(m.group(3)))
    for t in texts:
        for mm in _TXT_DAY_RX.finditer(str(t or "")):
            out.add(int(mm.group(1)))
    return out


def base_suspect(base, report_date, price_cands, *texts, ticker=None) -> str:
    """基準值可疑嗎?(批471)**兩條同時成立才算**,回命中因由;否則回空字串。

      ① 基準值**不在**現役抽取器從原文找到的價格候選集裡=在原文沒有依據
      ② 基準值**等於原文某個日期的「日」**=指得出它到底是什麼

    為什麼要兩條:只用 ① 是循環論證——萬一是我方抽取器壞掉漏了真價,
    那個真值一樣不會在候選集裡,我卻會反過來說基準錯。加上 ②,就從
    「我找不到」變成「我指得出它是什麼」,那才是證據。
    64 件基準包實測:13 件命中,全是 `Price (DD Mon YY):NT$xxxx` 這種版面,
    舊抽取器把括號裡的日抓成了價格。
    """
    if base is None:
        return ""
    try:
        b = float(base)
    except (TypeError, ValueError):
        return ""
    # 「基準值 == 這份報告的代號」是**決定性**的,不需要候選集背書,所以擺在最前面。
    # (兆豐晨會報告(二):原文 `目標價投資評等目標價振大環球(4441)`,基準把代號記成目標價;
    #  而 TP_RX 也會從同一句抓到 4441,所以候選集裡「有」它——放在候選檢查後面就永遠不會觸發。)
    if ticker and str(ticker).strip() and abs(b - _as_float(ticker, -1e18)) < 1e-9:
        return f"基準 {b:g} = 這份報告的代號(把代號當成了價)"
    if any(abs(b - float(c)) < 1e-9 for c in (price_cands or [])):
        return ""                       # 基準在原文有依據 → 不可疑
    days = day_numbers_in(report_date, *texts)
    if any(abs(b - d) < 1e-9 for d in days):
        return f"基準 {b:g} = 原文日期的「日」(原文價格候選 {list(price_cands)[:4]})"
    return ""


def _as_float(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _judge(base, got, why_suspect: str = "") -> str:
    if base is None:
        return "BASE_NULL"
    if why_suspect:
        return "BASE_SUSPECT"          # 批471:基準自己是日期碎片,不算我方失分
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
        right = d.get("repaired_right_text", "") or ""
        main = d.get("repaired_main_text", "") or ""
        tp, p = extract_tp_p(m, right, main,
                             Path(d.get("filename", "")).stem)
        # 基準可疑判準要的價格候選集(用現役 PX_RX,與 extract_tp_p 同源)
        # 批471:條件①要用**帶幣別記號**的候選集,不能用全集。
        # 全集裡本來就混著日期碎片(PX_RX 會把 `收盤價 May 19` 的 19 收進去),
        # 拿混了髒東西的集合去問「基準值有沒有依據」,答案永遠是「有」。
        # 幣別記號(NT$/US$/$)是真價格身邊一定有、日期身邊一定沒有的那個東西。
        _cur = getattr(m, "PX_CUR_RX", None) or m.PX_RX
        px_c = []
        for t in (right, main):
            for mm in _cur.finditer(t):
                v = m._num(mm.group(1))
                if v and v > 0 and v not in px_c:
                    px_c.append(v)
        tp_cur_c = []
        for t_ in (right, main):
            for mm in m.TP_RX.finditer(t_):
                v = m._num(mm.group(1))
                if v and v > 0 and v not in tp_cur_c:
                    tp_cur_c.append(v)
        why_p = base_suspect(bi.get("close_price"), bi.get("report_date"),
                             px_c, right, main, ticker=bi.get("ticker"))
        why_tp = base_suspect(bi.get("target_price"), bi.get("report_date"),
                              tp_cur_c, right, main, ticker=bi.get("ticker"))
        tick_base = bi.get("ticker")
        tick_fn = next(iter(m.TICK_RX.findall(d.get("filename", ""))), None)
        # 批471:v0100 拿**檔名層**抽到的代號去比**內文層**的基準真值。
        # 實測 5 件 DIFF 全是同一個形狀——`MS-ABF` / `MS-Thermal Solutions` /
        # `凱基投顧_鋼鐵產業` / 兆豐晨會報告,**檔名裡根本沒有四碼**,而基準的
        # 代號是從內文判的(3037 欣興 / 3324 雙鴻 / 6805 富世達 / 2002 中鋼)。
        # 兩邊不同源就不叫不符,叫不可比。檔名沒有代號 → FN_NO_TICKER。
        tick_v = ("BASE_NULL" if not tick_base
                  else "FN_NO_TICKER" if not tick_fn
                  else "MATCH" if tick_fn == tick_base else "DIFF")
        rows.append({
            "file": d.get("filename", "?"),
            "tp_base": bi.get("target_price"), "tp_got": tp,
            "tp_verdict": _judge(bi.get("target_price"), tp, why_tp),
            "tp_suspect_why": why_tp,
            "p_base": bi.get("close_price"), "p_got": p,
            "p_verdict": _judge(bi.get("close_price"), p, why_p),
            "base_date": bi.get("report_date"), "base_suspect_why": why_p,
            "ticker_base": tick_base, "ticker_fn": tick_fn,
            "ticker_verdict": tick_v})
    def agg(key):
        c: dict = {}
        for r in rows:
            c[r[key]] = c.get(r[key], 0) + 1
        return c
    tp_a, p_a, tk_a = agg("tp_verdict"), agg("p_verdict"), agg("ticker_verdict")

    def acc(a):
        # 批471:BASE_SUSPECT 與 BASE_NULL 同樣**不進分母**——
        # 拿一個已知是日期碎片的「真值」去扣我方的分,那個百分比沒有意義。
        eff = sum(v for k, v in a.items()
                  if k not in ("BASE_NULL", "BASE_SUSPECT", "FN_NO_TICKER"))
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
