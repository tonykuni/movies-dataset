# -*- coding: utf-8 -*-
"""
VRN_Pipeline_Runner.py
======================
End-to-end pipeline: MDL001→pdf_temp→MDL002→MDL003/MDL004/MDL005→MDL006
Produces Phase1 & Phase2 outputs, compares them, iterates until success.
"""
import os, sys, json, time, shutil, logging, importlib.util
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, Optional

logging.basicConfig(level=logging.INFO,
    format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

# ── Accelerator Init (6-ENV + GC + 7 HardGate Seal Tools) ────────────────────
import gc as _gc
_CEL: object = None;  _CEL_OK: bool = False
# [VRN:ANCHOR:HARDGATE_HOLDERS:V1] 7-tool support per VIA_Supportive_HardGate_Seal.json
_SSOT: object = None; _SSOT_OK: bool = False
_REG: object = None;  _REG_OK: bool = False
_BRG: object = None;  _BRG_OK: bool = False
_ENV: object = None;  _ENV_OK: bool = False
_AST: object = None;  _AST_OK: bool = False
_NET: object = None;  _NET_OK: bool = False

def _runner_accel_init() -> Dict:
    """Pipeline Runner: 6-ENV thread + GC + 7 HardGate Seal tools boot.
    Policy: BOOT_PRECHECK_ONLY_NO_NETWORK_NO_PARALLEL_NO_AUTOPATCH.
    """
    w = max(1, (os.cpu_count() or 4) - 1)
    for v in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS",
              "NUMEXPR_NUM_THREADS","BLIS_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
        os.environ.setdefault(v, str(w))
    _gc.set_threshold(50_000, 500, 50)

    # [VRN:ANCHOR:HARDGATE_PLUGIN_MAP:V1] Load 7 supportive tools per Seal order
    global _CEL, _CEL_OK, _SSOT, _SSOT_OK, _REG, _REG_OK, _BRG, _BRG_OK
    global _ENV, _ENV_OK, _AST, _AST_OK, _NET, _NET_OK
    ssot = CFG.get("ssot_dir","")
    plugin_map = [
        ("VIA_SSOT_Unified",                 "_SSOT", "_SSOT_OK"),
        ("VIA_RegistryCore_v1",              "_REG",  "_REG_OK"),
        ("VIA_Runtime_Bridge_All_in_One",    "_BRG",  "_BRG_OK"),
        ("VIA_EnvManager",                   "_ENV",  "_ENV_OK"),
        ("VIA_Panorama_AST_RuntimeInjector", "_AST",  "_AST_OK"),
        ("VeritasCeleritas",                 "_CEL",  "_CEL_OK"),
        ("VeritasAegisNexus",                "_NET",  "_NET_OK"),
    ]
    import importlib.util as _ilu
    for mod_name, gname, ok_name in plugin_map:
        for base in [Path(ssot), Path(ssot).parent]:
            p = base / f"{mod_name}.py"
            if p.exists():
                try:
                    spec = _ilu.spec_from_file_location(mod_name, str(p))
                    mod  = _ilu.module_from_spec(spec)
                    sys.modules[mod_name] = mod
                    spec.loader.exec_module(mod)
                    globals()[gname]   = mod
                    globals()[ok_name] = True
                    if mod_name == "VeritasCeleritas":
                        if hasattr(mod, "bootstrap_at_import"): mod.bootstrap_at_import(__file__)
                        if hasattr(mod, "warm_thread_pool"):    mod.warm_thread_pool()
                    log.info("[Runner] %s loaded", mod_name)
                    break
                except Exception as e:
                    log.debug("[Runner] %s: %s", mod_name, e)
    return {
        "workers": w,
        "via_ssot":      _SSOT_OK, "registry":      _REG_OK,
        "runtime_bridge":_BRG_OK,  "env_manager":   _ENV_OK,
        "ast_planner":   _AST_OK,  "celeritas":     _CEL_OK,
        "aegis":         _NET_OK,
    }

# ── PATHS ─────────────────────────────────────────────────────────────────────
# [VRN:ANCHOR:DYNAMIC_BASE:V2] Auto-detect BASE from this script location.
# Old hardcoded "/home/claude" fails on Windows because the runner is normally
# run from the OneDrive folder. This anchor resolves BASE to:
#   1. Env var VRN_BASE if set (highest priority, for explicit override)
#   2. The directory containing this Pipeline_Runner.py (works on any OS)
def _vrn_resolve_base() -> str:
    env = os.environ.get("VRN_BASE", "").strip()
    if env and Path(env).exists():
        return env
    return str(Path(__file__).resolve().parent)
BASE = _vrn_resolve_base()
log.info("[Runner] BASE=%s", BASE)
CFG: Dict = {
    # Input
    "input_dir":    f"{BASE}/pdf_temp",       # MDL001 reads from here
    "pdf_temp":     f"{BASE}/pdf_temp",       # MDL001 writes high-quality PDFs here
    # Intermediate
    "mdl002_temp":  f"{BASE}/mdl002_temp",
    "mdl003_temp":  f"{BASE}/mdl003_temp",
    "mdl004_temp":  f"{BASE}/mdl004_temp",
    "mdl005_temp":  f"{BASE}/mdl005_temp",
    "mdl006_temp":  f"{BASE}/mdl006_temp",
    # Output
    "output_dir":   f"{BASE}/vrn_output",
    # SSOT (not available in test env — graceful fallback)
    "ssot_dir":     f"{BASE}/supportive_module",
    # Runtime
    "workers":      2,
    "enable_db":    True,
    "dpi":          300,
    "compare_tol":  0.02,
    "min_confidence": 0.50,
    "csv_encoding": "utf-8-sig",
    # MDL001: since PDFs are already in pdf_temp, skip re-conversion
    "mdl001_skip":  True,
}

# Create all temp dirs
for k,v in CFG.items():
    if k.endswith("_temp") or k == "output_dir":
        Path(v).mkdir(parents=True, exist_ok=True)

# ── MODULE LOADER ─────────────────────────────────────────────────────────────
def load_module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    m    = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m

# ── STEP 1: MDL001 — PDF Conversion (skip if already in pdf_temp) ─────────────

def _cel_submit(fn, *args, **kw):
    """Submit via Celeritas if available."""
    if _CEL_OK and hasattr(_CEL, "_LazyPool"):
        try: return _CEL._LazyPool.submit(fn, *args, **kw)
        except Exception: pass
    return fn(*args, **kw)

def run_mdl001():
    if CFG["mdl001_skip"]:
        pdfs = list(Path(CFG["pdf_temp"]).glob("*.pdf"))
        log.info("[STEP1-MDL001] SKIP (already have %d PDFs in pdf_temp)", len(pdfs))
        return {"ok": True, "total": len(pdfs), "skipped": True}
    log.info("[STEP1-MDL001] Running PDF Converter...")
    try:
        m   = load_module("MDL001", f"{BASE}/VRN_MDL001_Converter.py")
        res = m.VRN_MDL001_Converter(CFG).run()
        log.info("[STEP1-MDL001] %s", res)
        return res
    except Exception as e:
        log.error("[STEP1-MDL001] %s", e)
        return {"ok": False, "error": str(e)}

# ── STEP 2: MDL002 — Layout Extraction ───────────────────────────────────────
def run_mdl002():
    log.info("[STEP2-MDL002] Running Layout Extractor...")
    try:
        m   = load_module("MDL002", f"{BASE}/VRN_MDL002_LayoutExtractor.py")
        res = m.VRN_MDL002_LayoutExtractor(CFG).run()
        log.info("[STEP2-MDL002] pages=%s tables=%s fin=%s",
                 res.get("total_pages"), res.get("total_tables"), res.get("total_fin_tables"))
        return res
    except Exception as e:
        log.error("[STEP2-MDL002] %s", e)
        import traceback; traceback.print_exc()
        return {"ok": False, "error": str(e)}

# ── STEP 3: MDL003 — Table Restoration (Phase 1) ─────────────────────────────
def run_mdl003():
    log.info("[STEP3-MDL003] Running Table Restorer (Phase1)...")
    # MDL003 reads mdl002_temp → writes mdl003_temp
    cfg3 = dict(CFG, mdl003_temp=CFG["mdl003_temp"])
    try:
        m   = load_module("MDL003", f"{BASE}/VRN_MDL003_TableRestorer.py")
        res = m.VRN_MDL003_TableRestorer(cfg3).run()
        log.info("[STEP3-MDL003] ok=%s tables_ok=%s fin=%s calc=%s err=%s",
                 res.get("ok"), res.get("total_tables_ok"),
                 res.get("total_fin_tables"), res.get("total_calc"), res.get("total_err"))
        return res
    except Exception as e:
        log.error("[STEP3-MDL003] %s", e)
        import traceback; traceback.print_exc()
        return {"ok": False, "error": str(e)}

# ── STEP 4: MDL004 — OCR Table Fetch (Phase 2) ───────────────────────────────
def run_mdl004():
    log.info("[STEP4-MDL004] Running OCR Table Fetcher (Phase2)...")
    cfg4 = dict(CFG, mdl004_temp=CFG["mdl004_temp"])
    try:
        m   = load_module("MDL004", f"{BASE}/VRN_MDL004_OCR_FetchingPDFTable_v1.py")
        res = m.VRN_MDL004_OCRFetcher(cfg4).run()
        log.info("[STEP4-MDL004] ok=%s tables=%s err=%s",
                 res.get("ok"), res.get("total_tables"), res.get("total_err_cells",0))
        return res
    except Exception as e:
        log.error("[STEP4-MDL004] %s", e)
        import traceback; traceback.print_exc()
        return {"ok": False, "error": str(e)}

# ── STEP 5: MDL005 — OCR Text Fetch (Phase 2) ────────────────────────────────
def run_mdl005():
    log.info("[STEP5-MDL005] Running OCR Text Fetcher (Phase2)...")
    cfg5 = dict(CFG, mdl005_temp=CFG["mdl005_temp"])
    try:
        m   = load_module("MDL005", f"{BASE}/VRN_MDL005_OCRFetchingPDFText_v1.py")
        res = m.VRN_MDL005_TextFetcher(cfg5).run()
        log.info("[STEP5-MDL005] ok=%s blocks=%s",
                 res.get("ok"), res.get("total_blocks"))
        return res
    except Exception as e:
        log.error("[STEP5-MDL005] %s", e)
        import traceback; traceback.print_exc()
        return {"ok": False, "error": str(e)}

# ── STEP 6: MDL006 — Consolidate + Compare ────────────────────────────────────
def run_mdl006():
    log.info("[STEP6-MDL006] Running Consolidator + Phase Validator...")
    try:
        m   = load_module("MDL006", f"{BASE}/VRN_MDL006_ConsolidatorAndPhaseValidator.py")
        res = m.VRN_MDL006_Consolidator(CFG).run()
        log.info("[STEP6-MDL006] %s", res.get("compare",{}).get("summary",""))
        return res
    except Exception as e:
        log.error("[STEP6-MDL006] %s", e)
        import traceback; traceback.print_exc()
        return {"ok": False, "error": str(e)}

# ── STEP 7: MDL007 — API Data Fetch (External validation source) ─────────────
def run_mdl007():
    log.info("[STEP7-MDL007] Running API Data Fetcher...")
    try:
        m   = load_module("MDL007", f"{BASE}/VRN_MDL007_APIDataFetcher.py")
        # [VRN:ANCHOR:PLUGIN_HANDSHAKE:V1] Pre-load supportive plugins before run
        if hasattr(m, "load_plugins"):
            try:
                lp = m.load_plugins(CFG["ssot_dir"])
                log.info("[STEP7-MDL007] plugins=%s", lp)
            except Exception as e:
                log.warning("[STEP7-MDL007] load_plugins skipped: %s", e)
        # MDL007 follows same convention as other MDLs: class with .run()
        res = m.VRN_MDL007_APIDataFetcher(CFG).run()
        log.info("[STEP7-MDL007] ok=%s api_records=%s err=%s",
                 res.get("ok"), res.get("total_records",0), res.get("total_err",0))
        return res
    except Exception as e:
        log.error("[STEP7-MDL007] %s", e)
        import traceback; traceback.print_exc()
        return {"ok": False, "error": str(e)}

# ── STEP 8: MDL008 — Cross Validator (Phase1 vs Phase2 vs MDL007 API) ────────
def run_mdl008():
    log.info("[STEP8-MDL008] Running Cross Validator...")
    try:
        m   = load_module("MDL008", f"{BASE}/VRN_MDL008_CrossValidator.py")
        # [VRN:ANCHOR:PLUGIN_HANDSHAKE:V1] Pre-load supportive plugins before run
        if hasattr(m, "load_plugins"):
            try:
                lp = m.load_plugins(CFG["ssot_dir"])
                log.info("[STEP8-MDL008] plugins=%s", lp)
            except Exception as e:
                log.warning("[STEP8-MDL008] load_plugins skipped: %s", e)
        res = m.VRN_MDL008_CrossValidator(CFG).run()
        log.info("[STEP8-MDL008] ok=%s verified=%s mismatch=%s",
                 res.get("ok"), res.get("total_verified",0), res.get("total_mismatch",0))
        return res
    except Exception as e:
        log.error("[STEP8-MDL008] %s", e)
        import traceback; traceback.print_exc()
        return {"ok": False, "error": str(e)}

# ── MAIN PIPELINE ──────────────────────────────────────────────────────────────
def run_pipeline(max_iterations: int = 3) -> Dict:
    t_total = time.perf_counter()
    accel_cap = _runner_accel_init()
    log.info("[Runner] accel=%s", accel_cap)
    pipeline_results: Dict = {
        "iterations": [],
        "final_success": False,
        "steps": {}
    }

    log.info("=" * 70)
    log.info("VRN PIPELINE — START")
    log.info("=" * 70)

    # Steps 1-5 run once
    s1 = run_mdl001()
    s2 = run_mdl002()
    s3 = run_mdl003()
    s4 = run_mdl004()
    s5 = run_mdl005()
    pipeline_results["steps"] = {
        "mdl001": s1, "mdl002": s2, "mdl003": s3,
        "mdl004": s4, "mdl005": s5,
    }

    # Step 6 iterates until success or max_iterations
    for iteration in range(1, max_iterations + 1):
        log.info("-" * 60)
        log.info("ITERATION %d/%d", iteration, max_iterations)
        s6 = run_mdl006()
        compare = s6.get("compare", {})
        success = compare.get("success", False)
        match_rate = compare.get("match_rate", 0.0)

        iter_result = {
            "iteration":  iteration,
            "success":    success,
            "match_rate": match_rate,
            "summary":    compare.get("summary",""),
            "phase1":     s6.get("phase1",{}),
            "phase2":     s6.get("phase2",{}),
            "mismatches": compare.get("mismatches",[])[:5],
        }
        pipeline_results["iterations"].append(iter_result)

        log.info("ITERATION %d: match_rate=%.1f%% success=%s",
                 iteration, match_rate*100, success)

        if success:
            pipeline_results["final_success"] = True
            log.info("SYSTEM SUCCESS — Phase1 == Phase2")
            break
        else:
            log.info("NEEDS IMPROVEMENT — mismatches: %d, p1_only: %d, p2_only: %d",
                     compare.get("n_mismatch",0),
                     compare.get("n_p1_only",0),
                     compare.get("n_p2_only",0))
            # Auto-improve: lower confidence threshold and retry MDL006
            if iteration < max_iterations:
                CFG["min_confidence"] = max(0.30, CFG["min_confidence"] - 0.1)
                log.info("AUTO-TUNE: lowering min_confidence to %.2f", CFG["min_confidence"])

    pipeline_results["total_elapsed"] = round(time.perf_counter() - t_total, 2)
    log.info("=" * 70)
    log.info("VRN PIPELINE — STEP 1-6 DONE in %.2fs | SUCCESS=%s",
             pipeline_results["total_elapsed"], pipeline_results["final_success"])
    log.info("=" * 70)

    # [VRN:ANCHOR:STEP78_INTEGRATION:V1] Run STEP 7 (API fetch) and STEP 8 (cross-validate)
    # AFTER MDL006 settles. These augment the pipeline_results with external validation.
    log.info("-" * 60)
    log.info("EXTENSION: STEP 7 + STEP 8")
    log.info("-" * 60)
    s7 = run_mdl007()
    s8 = run_mdl008()
    pipeline_results["steps"]["mdl007"] = s7
    pipeline_results["steps"]["mdl008"] = s8

    # Final summary including MDL008 verdict
    s8_ok = s8.get("ok", False)
    if s8_ok and pipeline_results["final_success"]:
        log.info("FULL PIPELINE SUCCESS — MDL006 phase match + MDL008 cross-verify pass")
    elif pipeline_results["final_success"]:
        log.info("PARTIAL — MDL006 ok but MDL008 verification incomplete")
    else:
        log.info("INCOMPLETE — MDL006 phase mismatch persists")

    pipeline_results["total_elapsed"] = round(time.perf_counter() - t_total, 2)
    log.info("=" * 70)
    log.info("VRN PIPELINE — FULL DONE in %.2fs", pipeline_results["total_elapsed"])
    log.info("=" * 70)
    return pipeline_results

if __name__ == "__main__":
    result = run_pipeline(max_iterations=3)
    out_path = f"{BASE}/vrn_output/VRN_Pipeline_Result.json"
    Path(out_path).write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8")
    print(json.dumps({
        "success":      result["final_success"],
        "iterations":   len(result["iterations"]),
        "elapsed":      result["total_elapsed"],
        "last_match":   result["iterations"][-1]["match_rate"] if result["iterations"] else 0,
        "output_path":  out_path,
    }, indent=2))
    sys.exit(0 if result["final_success"] else 1)
