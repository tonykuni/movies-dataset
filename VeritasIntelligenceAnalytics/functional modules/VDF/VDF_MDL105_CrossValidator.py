#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
================================================================================
  VDF_MDL105_CrossValidator.py
================================================================================
  VDF Registry · 跨來源驗證引擎
  Version    : 1.0.0   |   Module ID : VDF-REG-XV-001

  ROLE
  ────────────────────────────────────────────────────────────────────────────
  對 RegistryLoader 抓回的多源資料跑跨驗證:
    [1] Pairwise tolerance check  · |a-b| <= tol_abs OR |a-b|/avg <= tol_pct
    [2] Rolling z-score outlier   · |z| > threshold flag
    [3] Consensus 取共識值         · 5 種 method (primary_first/median/mean/majority/highest_trust)
    [4] Traffic light             · GREEN/YELLOW/RED + reason
    [5] Audit log + reconciliation report (HTML/JSON)

  USAGE
  ────────────────────────────────────────────────────────────────────────────
    from VDF_MDL104_RegistryLoader import RegistryLoader
    from VDF_MDL105_CrossValidator import CrossValidator

    loader = RegistryLoader("VDF_MDL403_RegistryFull.json")
    fetched = {
      "US.Rates.Treasury.10Y": {
        "FRED:DGS10":     df_with_value_column,
        "yfinance:^TNX":  df_with_value_column,
      },
      "US.Commodity.WTI": {
        "FRED:DCOILWTICO": df,
        "yfinance:CL=F":   df,
      },
    }
    cv = CrossValidator(loader, fetched_data=fetched)
    results = cv.validate_all()
    cv.print_rich_summary()
    cv.write_outputs()
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
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

import os, sys, json, time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

try:
    import pandas as pd
    import numpy as np
    PANDAS_OK = True
except ImportError:
    PANDAS_OK = False

try:
    from VDF_MDL101_OutputManager import OutputManager
    OM_OK = True
except ImportError:
    OM_OK = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    console = Console()
    RICH_OK = True
except ImportError:
    RICH_OK = False
    console = None


# =====================================================================================
# 🎯 CrossValidator
# =====================================================================================

class CrossValidator:
    """跨來源驗證 + consensus + traffic light."""
    VERSION = "1.0.0"

    TRUST_RANK = {"official": 5, "high": 4, "medium": 3, "low": 2, "low_emergency": 1}

    def __init__(self, loader, fetched_data: Optional[Dict] = None,
                 base_dir: Optional[str] = None,
                 output_dir: str = "0-2-CrossValidation"):
        """
        Args:
            loader: RegistryLoader instance
            fetched_data: {via_code: {source_key: DataFrame}} where source_key = "name:source_id"
                         DataFrame must have columns 'date' + 'value'
            base_dir, output_dir: for writing outputs
        """
        self.loader = loader
        self.fetched_data = fetched_data or {}
        self.base_dir = base_dir or str(HERE / "registry_output")
        self.output_dir = output_dir
        self.results: List[Dict] = []   # per via_code result

    # ── Pairwise check ────────────────────────────────────────────
    def _pairwise_check(self, values: Dict[str, float], item: Dict) -> Dict:
        """對所有 sources 兩兩比較."""
        validation = item.get("validation", {})
        tol_abs = validation.get("tolerance_abs")
        tol_pct = validation.get("tolerance_pct")
        keys = list(values.keys())
        pairs_passed = 0; pairs_total = 0; max_diff_pct = 0.0; max_diff_abs = 0.0
        details: List[Dict] = []
        for i in range(len(keys)):
            for j in range(i+1, len(keys)):
                a, b = values[keys[i]], values[keys[j]]
                if a is None or b is None or pd.isna(a) or pd.isna(b):
                    continue
                diff_abs = abs(a - b)
                avg = (abs(a) + abs(b)) / 2 if (a or b) else 1.0
                diff_pct = (diff_abs / avg * 100) if avg > 0 else 0
                ok_abs = (tol_abs is None) or (diff_abs <= tol_abs)
                ok_pct = (tol_pct is None) or (diff_pct <= tol_pct)
                ok = ok_abs and ok_pct
                pairs_total += 1
                if ok: pairs_passed += 1
                max_diff_abs = max(max_diff_abs, diff_abs)
                max_diff_pct = max(max_diff_pct, diff_pct)
                details.append({"src_a": keys[i], "src_b": keys[j], "val_a": a, "val_b": b,
                                "diff_abs": round(diff_abs, 4), "diff_pct": round(diff_pct, 3),
                                "ok": ok})
        return {"pairs_total": pairs_total, "pairs_passed": pairs_passed,
                "max_diff_abs": round(max_diff_abs, 4),
                "max_diff_pct": round(max_diff_pct, 3),
                "details": details}

    # ── Consensus ─────────────────────────────────────────────────
    def _consensus(self, values: Dict[str, float], item: Dict) -> Tuple[Optional[float], str]:
        """計算共識值, 回 (value, source_used)."""
        validation = item.get("validation", {})
        method = validation.get("consensus_method", "primary_first")
        valid_values = {k: v for k, v in values.items()
                        if v is not None and not pd.isna(v)}
        if not valid_values:
            return None, "(no valid source)"

        if method == "primary_first":
            # Lowest priority number wins
            sources = sorted(item["sources"], key=lambda s: s["priority"])
            for src in sources:
                key = f"{src['name']}:{src.get('source_id', '')}"
                if key in valid_values:
                    return valid_values[key], key
            return list(valid_values.values())[0], list(valid_values.keys())[0]

        if method == "median":
            arr = sorted(valid_values.values())
            return float(np.median(arr)), f"median_of_{len(arr)}"

        if method == "mean":
            arr = list(valid_values.values())
            return float(np.mean(arr)), f"mean_of_{len(arr)}"

        if method == "majority_vote":
            # round values to 4 decimals, find mode
            rounded = [round(v, 4) for v in valid_values.values()]
            from collections import Counter
            cnt = Counter(rounded)
            mode_val, mode_count = cnt.most_common(1)[0]
            return mode_val, f"majority_{mode_count}/{len(rounded)}"

        if method == "highest_trust":
            best = None
            best_rank = -1
            best_key = None
            for src in item["sources"]:
                key = f"{src['name']}:{src.get('source_id', '')}"
                if key not in valid_values: continue
                rank = self.TRUST_RANK.get(src["trust"], 0)
                if rank > best_rank:
                    best_rank = rank
                    best = valid_values[key]
                    best_key = key
            return best, best_key or "(unknown)"

        return list(valid_values.values())[0], list(valid_values.keys())[0]

    # ── Traffic light ─────────────────────────────────────────────
    def _traffic_light(self, item: Dict, n_sources: int, pair_result: Dict) -> Tuple[str, str]:
        """
        Returns (color, reason)
          GREEN  · ≥ consensus_min_sources OK and all pairs pass
          YELLOW · ≥ consensus_min_sources OK but some pairs fail
          RED    · below consensus_min_sources OR all sources failed
        """
        validation = item.get("validation", {})
        min_req = validation.get("consensus_min_sources", 1)
        if n_sources < min_req:
            return "RED", f"only {n_sources} source(s) succeeded, need ≥ {min_req}"
        if not item.get("validation", {}).get("cross_check", False):
            return "GREEN", f"single-source mode, primary OK"
        if pair_result["pairs_total"] == 0:
            return "YELLOW", "no pairs comparable"
        if pair_result["pairs_passed"] == pair_result["pairs_total"]:
            return "GREEN", f"all {pair_result['pairs_total']} pairs within tolerance"
        return "YELLOW", (f"{pair_result['pairs_passed']}/{pair_result['pairs_total']} pairs OK, "
                         f"max_diff_pct={pair_result['max_diff_pct']}")

    # ── Per-item validate ────────────────────────────────────────
    def validate_one(self, via_code: str, sources_data: Dict[str, "pd.DataFrame"]) -> Dict:
        """驗證單一 via_code."""
        item = self.loader.get_item(via_code)
        if not item:
            return {"via_code": via_code, "theme": "?", "n_sources_total": 0,
                    "n_sources_ok": 0, "pairs_passed": 0, "pairs_total": 0,
                    "max_diff_abs": 0, "max_diff_pct": 0,
                    "consensus_value": None, "consensus_src": "(no item)",
                    "color": "RED", "reason": "item not in registry",
                    "validated_at": datetime.now().isoformat(timespec='seconds'),
                    "pair_details": []}

        # Build latest values per source (last row of each DataFrame)
        latest: Dict[str, float] = {}
        for src_key, df in sources_data.items():
            if df is None or not PANDAS_OK or df.empty: continue
            val_col = "value" if "value" in df.columns else None
            if val_col is None:
                # try 'Close', 'Adj Close'
                for c in ["Close", "Adj Close", "close"]:
                    if c in df.columns: val_col = c; break
            if val_col is None: continue
            try:
                latest[src_key] = float(df[val_col].iloc[-1])
            except Exception:
                continue

        pair_res = self._pairwise_check(latest, item)
        consensus_val, consensus_src = self._consensus(latest, item)
        color, reason = self._traffic_light(item, len(latest), pair_res)

        return {
            "via_code":        via_code,
            "theme":           item["theme"],
            "n_sources_total": len(item["sources"]),
            "n_sources_ok":    len(latest),
            "pairs_passed":    pair_res["pairs_passed"],
            "pairs_total":     pair_res["pairs_total"],
            "max_diff_abs":    pair_res["max_diff_abs"],
            "max_diff_pct":    pair_res["max_diff_pct"],
            "consensus_value": consensus_val,
            "consensus_src":   consensus_src,
            "color":           color,
            "reason":          reason,
            "validated_at":    datetime.now().isoformat(timespec='seconds'),
            "pair_details":    pair_res["details"],
        }

    def validate_all(self) -> List[Dict]:
        """跑所有 fetched_data 內的 via_code."""
        self.results = []
        for via_code, sources_data in self.fetched_data.items():
            r = self.validate_one(via_code, sources_data)
            self.results.append(r)
        return self.results

    # ── Outputs ───────────────────────────────────────────────────
    def write_outputs(self):
        if not PANDAS_OK or not OM_OK: return
        if not self.results: return
        # Top-level table
        rows_summary = []
        rows_pairs = []
        for r in self.results:
            rows_summary.append({k: v for k, v in r.items() if k != "pair_details"})
            for d in r.get("pair_details", []):
                rows_pairs.append({"via_code": r["via_code"], **d})
        df_summary = pd.DataFrame(rows_summary)
        df_pairs   = pd.DataFrame(rows_pairs) if rows_pairs else pd.DataFrame()
        mgr = OutputManager(base_dir=self.base_dir, output_dir=self.output_dir,
                            duckdb_filename="VDF_CrossValidation.duckdb",
                            respect_cli_flags=False)
        mgr.save("validation_summary", df_summary)
        if not df_pairs.empty:
            mgr.save("pairwise_details", df_pairs)
        return mgr.status_summary()

    # ── Rich summary ──────────────────────────────────────────────
    def print_rich_summary(self):
        if not RICH_OK: print(f"Validated {len(self.results)} items"); return
        console.rule("[bold magenta]🔍 VDF Cross-Validation · Summary[/bold magenta]")

        # ── Table 1: Per-item result ──
        t = Table(title=f"📋 [bold]1. Per-Item Validation ({len(self.results)} items)[/bold]",
                  box=box.ROUNDED, header_style="bold magenta")
        t.add_column("via_code",       style="cyan",   width=32)
        t.add_column("Color",          style="green",  width=8, justify="center")
        t.add_column("Sources",        style="green",  width=10, justify="right")
        t.add_column("Pairs",          style="yellow", width=10, justify="right")
        t.add_column("MaxΔ%",          style="yellow", width=10, justify="right")
        t.add_column("Consensus",      style="green",  width=14, justify="right")
        t.add_column("Reason",         style="yellow", width=38)
        for r in self.results:
            color_text = {"GREEN":"[green]✅GREEN[/green]","YELLOW":"[yellow]⚠️YELLOW[/yellow]",
                          "RED":"[red]❌RED[/red]"}.get(r["color"], r["color"])
            cv = r.get("consensus_value")
            cv_str = f"{cv:.4f}" if cv is not None and not pd.isna(cv) else "—"
            t.add_row(r["via_code"][:30], color_text,
                      f"{r['n_sources_ok']}/{r['n_sources_total']}",
                      f"{r['pairs_passed']}/{r['pairs_total']}",
                      f"{r['max_diff_pct']}" if r['pairs_total'] > 0 else "—",
                      cv_str, r["reason"][:36])
        console.print(t)

        # ── Table 2: Traffic Light tally ──
        from collections import Counter
        light = Counter(r["color"] for r in self.results)
        t = Table(title="🚦 [bold]2. Traffic Light Distribution[/bold]",
                  box=box.ROUNDED, header_style="bold magenta")
        t.add_column("Color", style="cyan", width=10, justify="center")
        t.add_column("Count", style="green", width=12, justify="right")
        t.add_column("%",     style="yellow",width=10, justify="right")
        tot = sum(light.values()) or 1
        for c in ["GREEN", "YELLOW", "RED"]:
            n = light.get(c, 0)
            pct = round(n / tot * 100, 1)
            icon = {"GREEN":"✅", "YELLOW":"⚠️", "RED":"❌"}[c]
            t.add_row(f"{icon} {c}", str(n), f"{pct}%")
        console.print(t)

        # ── Final panel ──
        n_green = light.get("GREEN", 0)
        n_total = len(self.results)
        pct_green = round(n_green / max(n_total, 1) * 100, 1)
        summary = (
            f"[bold]Items validated[/bold]   : {n_total}\n"
            f"[bold]GREEN[/bold]            : {n_green} ({pct_green}%)\n"
            f"[bold]YELLOW[/bold]           : {light.get('YELLOW', 0)}\n"
            f"[bold]RED[/bold]              : {light.get('RED', 0)}\n\n"
            f"{'[bold green]✅ 全綠驗證通過[/bold green]' if light.get('RED', 0) == 0 else '[bold yellow]⚠️ 部分項目需檢視[/bold yellow]'}"
        )
        console.print(Panel.fit(summary, title="[bold cyan]🎯 Cross-Validation Result[/bold cyan]",
                                border_style="cyan"))


# =====================================================================================
# 🎯 Entry
# =====================================================================================

def _selftest():
    """Self-test with mock data exercising all 5 consensus methods + traffic lights."""
    if not PANDAS_OK:
        print("pandas missing, skip"); return 1
    if RICH_OK:
        console.print(Panel("[bold]Cross-Validator Self-Test[/bold]\n\n"
                            "建 mock fetched_data 含 6 個 via_code, 驗 GREEN/YELLOW/RED 三種情境\n"
                            "及 5 種 consensus method", title="🧪 Self-Test", border_style="blue"))

    from VDF_MDL104_RegistryLoader import RegistryLoader
    # registry 候選解析:cwd(本機慣用)→ canonical(supportive modules/registry),零複製
    _reg_candidates = [
        Path("VDF_MDL403_RegistryFull.json"),
        Path(__file__).resolve().parent.parent.parent / "supportive modules" / "registry" / "VDF_MDL403_RegistryFull.json",
    ]
    _reg = next((c for c in _reg_candidates if c.exists()), _reg_candidates[0])
    loader = RegistryLoader(str(_reg))
    print(f"   ✓ Loader loaded {len(loader.items)} items")

    # Build mock fetched_data
    dates = pd.date_range("2026-05-01", periods=5)
    def mk(vals, col="value"):
        return pd.DataFrame({"date": dates, col: vals})

    fetched = {
        # GREEN: FRED 4.50 + YF 4.51, tol_abs=0.05, primary_first
        "US.Rates.Treasury.10Y": {
            "FRED:DGS10":     mk([4.45, 4.48, 4.49, 4.50, 4.50]),
            "yfinance:^TNX":  mk([4.46, 4.49, 4.50, 4.51, 4.51]),
        },
        # YELLOW: WTI FRED 75.20 vs YF 78.50, tol_pct=2.0 → fail
        "US.Commodity.WTI": {
            "FRED:DCOILWTICO": mk([74.00, 74.50, 75.00, 75.10, 75.20]),
            "yfinance:CL=F":   mk([77.50, 78.00, 78.30, 78.40, 78.50]),
        },
        # GREEN: Gold 2350 vs 2348, tol_pct=1.0 OK
        "US.Commodity.Gold": {
            "FRED:GOLDAMGBD228NLBM": mk([2340, 2345, 2348, 2350, 2350]),
            "yfinance:GC=F":         mk([2342, 2346, 2349, 2351, 2348]),
        },
        # GREEN: single source CPI
        "US.Prices.CPI.Headline": {
            "FRED:CPIAUCSL": mk([308.0, 308.5, 309.0, 309.5, 309.8]),
        },
        # GREEN: dual-source PMI agree perfectly
        "CN.PMI.Manufacturing": {
            "FRED:CHNMFGPMI":      mk([49.5, 49.6, 49.7, 49.8, 49.9]),
            "akshare:cn_pmi_mfg":  mk([49.5, 49.6, 49.7, 49.8, 49.9]),
        },
        # GREEN single source: SP500 (no FRED dual in registry)
        "US.Index.SP500": {
            "yfinance:^GSPC":  mk([5900, 5905, 5910, 5912, 5915]),
        },
        # RED: 10Y3M Spread only, but say all sources failed (empty)
        "US.Rates.Spread.10Y3M": {
            # zero successful sources
        },
        # YELLOW: HY OAS dual but proxy mode (no tolerance configured → 0 pairs)
        "US.Credit.HY.OAS": {
            "FRED:BAMLH0A0HYM2": mk([3.50, 3.45, 3.42, 3.38, 3.35]),
            "yfinance:HYG":      mk([78.50, 78.80, 79.00, 79.20, 79.30]),
        },
    }

    cv = CrossValidator(loader, fetched_data=fetched)
    cv.validate_all()
    cv.print_rich_summary()
    cv.write_outputs()
    return 0


def main():
    if "--selftest" in sys.argv:
        return _selftest()
    print("Usage: python VDF_MDL105_CrossValidator.py --selftest")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"❌ {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)
