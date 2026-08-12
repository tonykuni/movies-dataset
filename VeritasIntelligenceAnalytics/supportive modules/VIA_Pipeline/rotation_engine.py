# -*- coding: utf-8 -*-
# rotation_engine.py v0100(ENG-024)— via-pipe 同伴檔補齊:族群輪動引擎整合轉接
#
# 背景(操作員 2026/08/08 整合去重優化令):via_pipeline.py 自歸家日起等待同伴檔
#   rotation_engine.py(介面:rebase100/log_ret/debeta/classify_and_prune/make_demo/
#   THEMES/MARKET_COL/CORR_KEEP)。操作員上傳之族群輪動資金流引擎經 hash 鑑識
#   與庫內 VDF/engine/candidates/sector_rotation_capital_flow_engine.py 逐位元組相同
#   (正本已在庫)。本檔為「轉接層」:
#   1) 去重 — 台股族群對照表(VIA_TAXONOMY_V1_1)不複製,以 AST 靜態抽取自候選正本
#      (不執行其 import,免 statsmodels/sklearn 依賴;正本不就地修改)
#   2) 方法論 — 剔除濫竽充數採候選之 PC1 共動法(此處以 numpy SVD 實作,零額外依賴;
#      LEADER 永留;|corr(PC1)| < CORR_KEEP 者剔)
#   3) 介面 — 完全符合 via_pipeline 期望;CORR_KEEP 為模組層可調(自演化搜尋用)
# 誠實:候選正本缺席時 THEMES 為空並於 make_demo 明確報錯,不偽造族群。

# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:START] =====
# 接橋補丁 v2(2026-08-12 令:引擎統一導入 輔助/加速器/網路/自動編號;
#  導入一律 bridge-first 過橋;graceful 全退化 — 缺席零影響;
#  不 eager 導入 Runtime_Bridge/EnvManager 重件)
import sys as _via_sys
from pathlib import Path as _via_Path

def _via_bootstrap_support_paths():
    try:
        _self = _via_Path(__file__).resolve()
        roots = [_self.parent]
        p = _self.parent
        for _ in range(4):
            p = p.parent
            roots.append(p)
        for root in roots:
            for name in ("supportive_module", "supportive modules"):
                sup = root / name
                if sup.is_dir():
                    s = str(sup)
                    if s not in _via_sys.path:
                        _via_sys.path.insert(0, s)
    except Exception:
        pass

_via_bootstrap_support_paths()
try:
    from VRN_SupportBridge import BRIDGE as _VIA_BRIDGE
    _VIA_HAS_BRIDGE = True
except Exception:
    _VIA_BRIDGE = None
    _VIA_HAS_BRIDGE = False

def _via_load(_name):
    # 統一導入閘:先過橋(輔助性工具),橋缺退直導,再缺落 None(graceful)
    try:
        if _VIA_BRIDGE is not None:
            for _fn in ("load", "get", "require"):
                _f = getattr(_VIA_BRIDGE, _fn, None)
                if callable(_f):
                    try:
                        _m = _f(_name)
                    except Exception:
                        _m = None
                    if _m is not None:
                        return _m
    except Exception:
        pass
    try:
        return __import__(_name)
    except Exception:
        return None

_VIA_SSOT = _via_load("VIA_SSOT_Unified")
_VIA_AEGIS = _via_load("VeritasAegisNexus")
_VIA_CELERITAS = _via_load("VeritasCeleritas")
_VIA_ACCEL = _via_load("VIA_SuperAccel_Module")   # 加速器(工作站候上傳;graceful)
_VIA_NET = _via_load("VIA_NetSupport")            # 網路支援模組
_VIA_REGCORE = _via_load("VIA_RegistryCore_v1")   # 自動編號核心(工作站候上傳;graceful)
try:
    if _VIA_REGCORE is not None:  # 自動編號:標準介面任一,全護欄不擲例外
        for _fn in ("auto_register", "ensure_code", "register_module"):
            _f = getattr(_VIA_REGCORE, _fn, None)
            if callable(_f):
                _f(__file__)
                break
except Exception:
    pass
# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:END] =====

import ast
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent                     # VIA_Pipeline/
CANDIDATE = (HERE.parents[1] / "functional modules" / "VDF" / "engine"
             / "candidates" / "sector_rotation_capital_flow_engine.py")

MARKET_COL = "MARKET"
CORR_KEEP = 0.3        # via_pipeline 自演化會動態覆寫(RE.CORR_KEEP = ...)


def _extract_taxonomy(path):
    """AST 靜態抽取 VIA_TAXONOMY_V1_1(不執行候選檔,不受其重依賴影響)。"""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name) and tgt.id == "VIA_TAXONOMY_V1_1":
                        return ast.literal_eval(node.value)
    except Exception:
        pass
    return {}


_TAX = _extract_taxonomy(CANDIDATE) if CANDIDATE.exists() else {}
THEMES = {k: [x["ticker"] for x in v] for k, v in _TAX.items()}
_ROLES = {x["ticker"]: x["role"] for v in _TAX.values() for x in v}


def rebase100(px, base_date):
    """全欄以基準日=100 重定基(基準日缺值欄以首個有效值代)。"""
    base = px.loc[base_date] if base_date in px.index else px.iloc[0]
    base = base.replace(0, np.nan).fillna(px.bfill().iloc[0])
    return px.div(base) * 100.0


def log_ret(x):
    """對數收益率(DataFrame 或 Series;0/缺值安全)。"""
    x = x.replace(0, np.nan)
    return np.log(x / x.shift(1)).dropna(how="all")


def debeta(ret, mkt):
    """逐欄去市場 β(候選引擎之族群純化前置:去大盤共同因子)。"""
    mkt = mkt.reindex(ret.index)
    var = float(mkt.var())
    out = {}
    for c in ret.columns:
        beta = (ret[c].cov(mkt) / var) if var and np.isfinite(var) else 0.0
        out[c] = ret[c] - beta * mkt
    return pd.DataFrame(out, index=ret.index)


def classify_and_prune(names, sig, reb):
    """候選引擎 PC1 共動法剔除:|corr(個股, 族群PC1)| >= CORR_KEEP 者留;
    LEADER 永留(角色自候選正本);樣本不足時全留(誠實不硬剔)。
    回傳 (classification: {ticker: CORE|PRUNED}, kept: [ticker], detail: {ticker: corr})。"""
    cols = [n for n in names if n in sig.columns]
    detail = {}
    if len(cols) < 2:
        return {c: "CORE" for c in cols}, list(cols), detail
    sub = sig[cols].dropna()
    if len(sub) < 5:
        return {c: "CORE" for c in cols}, list(cols), detail
    X = (sub - sub.mean()).values
    try:
        u, s, _vt = np.linalg.svd(X, full_matrices=False)
        pc1 = pd.Series(u[:, 0] * s[0], index=sub.index)
    except Exception:
        pc1 = sub.mean(axis=1)
    cl, kept = {}, []
    for c in cols:
        corr = float(sub[c].corr(pc1))
        detail[c] = round(corr, 4) if np.isfinite(corr) else 0.0
        keep = (_ROLES.get(c) == "LEADER") or (np.isfinite(corr) and abs(corr) >= CORR_KEEP)
        cl[c] = "CORE" if keep else "PRUNED"
        if keep:
            kept.append(c)
    return cl, kept, detail


def make_demo(days=400, seed=2026):
    """決定性示範行情:族群共動因子 + 偽濫竽充數雜訊股(候選引擎生成法)+ MARKET 欄。"""
    if not THEMES:
        raise RuntimeError("族群正本缺席:%s(VIA_TAXONOMY_V1_1 抽取失敗)" % CANDIDATE)
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end="2026-07-28", periods=days)
    mfac = rng.normal(0.0004, 0.010, days)
    data = {}
    for _th, names in THEMES.items():
        gfac = mfac + rng.normal(0.0008, 0.015, days)
        for t in names:
            if t in data:
                continue
            if _ROLES.get(t) == "LAGGARD" and rng.random() > 0.5:
                r = rng.normal(-0.0004, 0.020, days)     # 偽·濫竽充數:與族群脫鉤
            else:
                r = gfac * rng.uniform(0.7, 1.3) + rng.normal(0, 0.008, days)
            data[t] = 100.0 * np.exp(np.cumsum(r))
    data[MARKET_COL] = 100.0 * np.exp(np.cumsum(mfac))
    px = pd.DataFrame(data, index=dates)
    return px, {"themes": THEMES}


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    print("rotation_engine v0100 自檢:")
    print("  族群 %d 組 / 成員 %d 檔(正本:%s)" % (len(THEMES), len(_ROLES), CANDIDATE.name))
    px, _meta = make_demo(days=120)
    reb = rebase100(px, px.index[0])
    ret = log_ret(px.drop(columns=[MARKET_COL]))
    sig = debeta(ret, log_ret(px[MARKET_COL]))
    n_kept = n_pruned = 0
    for th, names in THEMES.items():
        cl, kept, det = classify_and_prune(names, sig, reb)
        n_kept += len(kept)
        n_pruned += sum(1 for v in cl.values() if v == "PRUNED")
        print("  %s:留 %d / 剔 %d" % (th, len(kept), sum(1 for v in cl.values() if v == "PRUNED")))
    print("  合計:留 %d · 剔 %d(CORR_KEEP=%.2f;LEADER 永留)" % (n_kept, n_pruned, CORR_KEEP))
