#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL014_ThreeCodeUniverse v0101 — 薄尾(v0100 一字不改):yfinance 代碼照市場 —— 上市 .TW · 上櫃 .TWO(+ V12)

實測找到(2026-11-15 容器 build · 種子冊):OUT-01 的上櫃股 6488 環球晶記成 yf_ticker 6488.TW。
v0100 classify(第 174 / 179 行)與 assemble(第 345 行)把個股 / 主動 ETF 的 yfinance 代碼一律接 .TW;
可是同一本冊 VDF_InputUniverse_SSOT 的 SRC-03 寫的是「yfinance ####.TW / .TWO」,價表也是「ticker 去 .TW / .TWO」——
上櫃股在 yfinance 是 ####.TWO,接成 .TW 抓不到(或抓到別的),下游(VRN-2 報表 · VQG 序列 · VAP 圖)拿到的代碼就錯。
Bloomberg 代碼照舊「#### TT」(只加 TT,不加 Equity)。
本版:
  ① assemble 後每列(個股 / 主動 ETF)照 market 改 yf 後綴:TWSE / 上市 → .TW · TPEX / TPEx / 上櫃 / OTC → .TWO;認不出的市場不動(不猜)。
  ② V12 yf 後綴照市場:不合 = RED · 市場認不出 = AMBER;燈照 v0100 的 RANK 律併入總燈。
  ③ classify 單一代號:個股查本機個股組(真相庫 / 種子冊)補市場再定後綴;info 同。
  指數列(IN-03 代理 ^TWII / ^TWOII)一字不動。
入口 / 動詞 / 輸出照 v0100(VDF System Manager 總控 VIA_FROM_VDFSM=YES 或 VCGC;classify | build [--apply] | info | plan | ui | --selftest)。
零網路 · 零安裝 · 不碰 TA-Lib · 同意閘不讀不寫 · 不寫環境。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本支零外呼,只用來報閘況。"""
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

import importlib.util
import json
import os
import re
import sys
import warnings
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL014_ThreeCodeUniverse"
TAG = _STEM + " v" + Path(__file__).stem.rsplit("_v", 1)[-1]


def _vnum_v0101(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0101(p) < _vnum_v0101(__file__)), key=_vnum_v0101)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
with warnings.catch_warnings():
    warnings.simplefilter("ignore", SyntaxWarning)
    _spec.loader.exec_module(PRIOR)
for _n, _v in vars(PRIOR).items():                     # 前版公開名稱全數轉接(TAILAPI)
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = _v


def __getattr__(name):
    """前版公開名稱(group_stock · plan_steps · ui_html …)一律轉接到 v0100。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


_ASSEMBLE_V0100, _VALIDATE_V0100, _CLASSIFY_V0100, _INFO_V0100 = PRIOR.assemble, PRIOR.validate, PRIOR.classify, PRIOR.info
_BUILD_V0100, _MAIN_V0100, _TAG_V0100 = PRIOR.build, PRIOR.main, PRIOR.TAG
TPEX_WORDS = ("TPEX", "OTC", "上櫃", "櫃買")
TWSE_WORDS = ("TWSE", "上市")


def yf_suffix(market) -> str | None:
    """冊 SRC-03:yfinance 代碼 ####.TW(上市)/ ####.TWO(上櫃)。市場認不出 = None(不猜)。"""
    m = str(market or "").strip().upper()
    if not m:
        return None
    if any(w.upper() in m for w in TPEX_WORDS):
        return ".TWO"
    if any(w.upper() in m for w in TWSE_WORDS):
        return ".TW"
    return None


def fix_yf(row: dict, group_key: str = "group") -> dict:
    """個股 / 主動 ETF 列:yf 後綴照市場改正;指數(代理代碼)與市場認不出的列不動。"""
    g = row.get(group_key) or row.get("type")
    if g not in ("IN-01", "IN-02") or not row.get("code"):
        return row
    suf = yf_suffix(row.get("market"))
    if suf:
        row["yf_ticker"] = str(row["code"]).strip().upper() + suf
    return row


def assemble(groups: list, inb: dict) -> list:
    """同 v0100 assemble(照冊 OUT-01 欄);yf 後綴照市場(v0100 一律 .TW,上櫃股在 yfinance 抓不到)。"""
    return [fix_yf(r) for r in _ASSEMBLE_V0100(groups, inb)]


def check_v12(rows: list) -> dict:
    """V12 yf 後綴照市場:上市 .TW · 上櫃 .TWO;不合 = RED;市場認不出 = AMBER(不猜)。"""
    bad, unknown, etf_conv = [], [], 0
    for r in rows:
        if r.get("group") not in ("IN-01", "IN-02") or not r.get("code"):
            continue
        suf = yf_suffix(r.get("market"))
        if suf is None and r.get("group") == "IN-02" and not str(r.get("market") or "").strip():
            etf_conv += 1                              # 冊 IN-02 沒寫市場;照 v0100 classify 的慣例(主動 ETF = 上市 .TW),不算認不出
            suf = ".TW"
        if suf is None:
            unknown.append(r.get("code"))
        elif r.get("yf_ticker") != str(r["code"]).strip().upper() + suf:
            bad.append("%s %s→%s" % (r.get("code"), r.get("market"), r.get("yf_ticker")))
    lamp = "RED" if bad else ("AMBER" if unknown else "GREEN")
    n_two = sum(1 for r in rows if str(r.get("yf_ticker", "")).endswith(".TWO"))
    return {"id": "V12", "name": "yf 後綴照市場(上市 .TW · 上櫃 .TWO;冊 SRC-03)", "lamp": lamp,
            "note": "上櫃 .TWO %d 檔 · 主動 ETF 市場欄空照 v0100 上市慣例 %d 檔 · 不合 %s · 市場認不出 %s"
                    % (n_two, etf_conv, bad[:5] or "[]", unknown[:5] or "[]")}


def validate(rows: list, groups: list, inb: dict) -> dict:
    v = _VALIDATE_V0100(rows, groups, inb)
    v["checks"].append(check_v12(rows))
    lamp = "GREEN"
    for c in v["checks"]:
        if PRIOR.RANK[c["lamp"]] > PRIOR.RANK[lamp]:
            lamp = c["lamp"]
    v["lamp"] = lamp
    return v


_STOCK_MARKET: dict = {}


def _stock_market(code: str, ins: dict) -> str:
    """單一代號的市場:查本機個股組(真相庫 / 種子冊);查不到 = 空(不猜)。"""
    if not _STOCK_MARKET:
        for r in PRIOR.group_stock(ins).get("rows") or []:
            _STOCK_MARKET[str(r.get("code", "")).strip()] = str(r.get("market") or "")
        _STOCK_MARKET.setdefault("__loaded__", "1")
    return _STOCK_MARKET.get(str(code).strip(), "")


def classify(code: str, ins: dict) -> dict:
    """同 v0100 classify;個股查得到市場就補上,yf 後綴照市場。"""
    r = _CLASSIFY_V0100(code, ins)
    if r.get("type") == "IN-01" and not r.get("market"):
        r["market"] = _stock_market(r.get("code", ""), ins)
    return fix_yf(r, "type")


def info(codes: list, here: Path = HERE) -> dict:
    out = _INFO_V0100(codes, here)
    for r in out.get("codes") or []:
        fix_yf(r, "type")
    out["engine"] = TAG
    return out


@contextmanager
def _installed():
    """一次呼叫期間:v0100 的 build / info / main 叫的 assemble · validate · classify · info = 本版;結束還原(v0100 自測照舊)。"""
    keep = (PRIOR.assemble, PRIOR.validate, PRIOR.classify, PRIOR.info, PRIOR.TAG)
    PRIOR.assemble, PRIOR.validate, PRIOR.classify, PRIOR.info, PRIOR.TAG = assemble, validate, classify, info, TAG
    try:
        yield
    finally:
        PRIOR.assemble, PRIOR.validate, PRIOR.classify, PRIOR.info, PRIOR.TAG = keep


def build(apply: bool = False, here: Path = HERE, out_root: Path | None = None) -> dict:
    with _installed():
        return _BUILD_V0100(apply, here, out_root)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    with _installed():
        return _MAIN_V0100(args)


# ---------------------------------------------------------------- 自測(零網路 · 只讀)
def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}")

    print(f"=== {TAG} · 薄尾自測(yf 後綴照市場;零網路 · 只讀)===")
    chk("① 後綴律:TWSE / 上市 → .TW · TPEX / TPEx / 上櫃 / OTC → .TWO · 認不出 / 空 → None(不猜)",
        yf_suffix("TWSE") == ".TW" and yf_suffix("上市") == ".TW" and yf_suffix("TPEX") == ".TWO" and yf_suffix("TPEx") == ".TWO"
        and yf_suffix("上櫃") == ".TWO" and yf_suffix("OTC") == ".TWO" and yf_suffix("") is None and yf_suffix("NYSE") is None)
    rows = [{"group": "IN-01", "code": "6488", "market": "TPEX", "yf_ticker": "6488.TW"},
            {"group": "IN-01", "code": "2330", "market": "TWSE", "yf_ticker": "2330.TW"},
            {"group": "IN-02", "code": "00981A", "market": "TWSE", "yf_ticker": "00981A.TW"},
            {"group": "IN-03", "code": "TPEX", "market": "TPEX", "yf_ticker": "^TWOII"},
            {"group": "IN-01", "code": "9999", "market": "", "yf_ticker": "9999.TW"}]
    v0 = check_v12(rows)
    fixed = [fix_yf(dict(r)) for r in rows]
    v1 = check_v12(fixed[:4])
    chk("② 重現 v0100:上櫃 6488 記成 6488.TW → V12 RED;改正後 6488.TWO · 上市 / 主動 ETF 照 .TW · 指數代理 ^TWOII 不動 · V12 GREEN",
        v0["lamp"] == "RED" and fixed[0]["yf_ticker"] == "6488.TWO" and fixed[1]["yf_ticker"] == "2330.TW"
        and fixed[2]["yf_ticker"] == "00981A.TW" and fixed[3]["yf_ticker"] == "^TWOII" and v1["lamp"] == "GREEN", (v0, v1))
    chk("③ 市場認不出 → yf 原樣 · V12 AMBER(不猜)", fixed[4]["yf_ticker"] == "9999.TW" and check_v12(fixed)["lamp"] == "AMBER")
    rep = build()
    two = [r for r in rep["rows"] if r.get("market") == "TPEX" and r.get("group") == "IN-01"]
    c12 = next((c for c in rep["checks"] if c["id"] == "V12"), {})
    unk = [r["code"] for r in rep["rows"] if r.get("group") == "IN-01" and yf_suffix(r.get("market")) is None]
    chk("④ 本機實建 OUT-01(%s · %d 列):上櫃 %d 檔全是 .TWO · V12 %s(主動 ETF 照上市慣例 · 市場認不出 %s 照實黃)· 總燈照 v0100 律(%s)· 報告記本版"
        % ("/".join(sorted({g['source'] for g in rep['groups']})), rep["count"], len(two), c12.get("lamp"), unk or "無", rep["lamp"]),
        rep["engine"] == TAG and all(r["yf_ticker"].endswith(".TWO") for r in two) and len(rep["checks"]) == 12
        and c12.get("lamp") == ("AMBER" if unk else "GREEN") and all(u in c12.get("note", "") for u in unk[:5])
        , c12)
    inb, _n, _f, _fn = PRIOR.load_books()
    ins = PRIOR.inputs_by_id(inb)
    with _installed():
        c1 = PRIOR.classify("6488", ins)
        c2 = PRIOR.classify("2330", ins)
    chk("⑤ classify:種子 / 真相裡查得到上櫃 6488 → 6488.TWO · 上市 2330 → 2330.TW(%s · %s)" % (c1.get("yf_ticker"), c2.get("yf_ticker")),
        c1.get("yf_ticker") == ("6488.TWO" if c1.get("market") else "6488.TW") and c2.get("yf_ticker") == "2330.TW", (c1, c2))
    chk("⑥ 換裝只在一次呼叫裡:平時 v0100 的 assemble / validate / classify / info / TAG 是它自己的(前版自測照舊)",
        PRIOR.assemble is _ASSEMBLE_V0100 and PRIOR.validate is _VALIDATE_V0100 and PRIOR.classify is _CLASSIFY_V0100
        and PRIOR.info is _INFO_V0100 and PRIOR.TAG == _TAG_V0100)
    text = Path(__file__).read_text(encoding="utf-8")
    body = text.split("def selftest", 1)[0]
    chk("⑦ 加速器橋 · 網路橋在;不碰 TA-Lib;同意閘不讀不寫;不匯入他系統程式;不寫環境",
        "[VIA:ACCEL-BRIDGE" in text and "[VIA:NET-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+(talib|CGC_|VRN_|VCGC)", text, re.M)
        and not re.search(r"environ[\[.][^\n]{0,16}VIA_(NET|SCRAPE)_CON" + "SENT", body) and not re.search(r"os\.environ\[[^\]]*\]\s*=(?!=)|os\.environ\.(pop|setdefault|update)\(", body))
    print(f"[計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    if not all(ok):
        return 1
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1":
        return 0
    rc = PRIOR.selftest()
    print(f"[計] {TAG} 前版鏈 rc {rc} · {'PASS' if rc == 0 else 'FAIL'}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
