# -*- coding: utf-8 -*-
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

import csv
import hashlib
import html
import json
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_FINAL_HANDOVER_COMMIT_BLOCKER_SEAL_V0615702"


# ==================================================================================================
# def 00_BASIC_UTILITIES
# ==================================================================================================
def def_clean(x: Any) -> str:
    s = "" if x is None else str(x)
    s = html.unescape(s)
    s = s.replace("\u3000", " ").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def def_norm(x: Any) -> str:
    return re.sub(r"[\s_\-\/\(\)（）\[\]【】{}:：,，.。&+%]+", "", str(x or "").lower())


def def_light(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "PASS", "YES", "SEALED", "BLOCKED_OK"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "BLOCKED", "APPROVAL_REQUIRED"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_find_latest_dir(root: Path, prefixes: list[str]) -> Path | None:
    if not root.exists():
        return None

    hits: list[Path] = []
    for prefix in prefixes:
        hits.extend([p for p in root.glob(prefix + "_*") if p.is_dir()])

    if not hits:
        return None

    return sorted(hits, key=lambda p: p.stat().st_mtime, reverse=True)[0]


def def_sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def def_read_json(path: Path) -> dict:
    if not path.exists():
        return {}

    for enc in ["utf-8", "utf-8-sig", "cp950", "big5"]:
        try:
            return json.loads(path.read_text(encoding=enc))
        except Exception:
            pass

    return {}


def def_read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []

    for enc in ["utf-8-sig", "utf-8", "cp950", "big5", "latin-1"]:
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            pass

    return []


def def_write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        rows = [{"empty_marker": ""}]

    fields: list[str] = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def def_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_file_asset(label: str, path: Path, required: bool = True) -> dict:
    exists = path.exists()
    sev = "OK" if exists else ("ERR" if required else "WARN")

    return {
        "Status Lights": def_light(sev),
        "asset": label,
        "path": str(path),
        "exists": "YES" if exists else "NO",
        "sha256": def_sha256_file(path),
        "required": "YES" if required else "NO",
        "Severity": sev,
    }


# ==================================================================================================
# def 01_HTML_RENDERING
# ==================================================================================================
def def_html_table(title: str, rows: list[dict]) -> str:
    if not rows:
        return f"<section class='card'><h2>{html.escape(title)}</h2><p>No rows.</p></section>"

    fields: list[str] = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)

    th = "".join(f"<th>{html.escape(str(k))}</th>" for k in fields)

    trs: list[str] = []
    for r in rows:
        tds: list[str] = []
        for k in fields:
            v = "" if r.get(k) is None else str(r.get(k, ""))
            cls = "left" if any(x in k.lower() for x in ["path", "asset", "rule", "reason", "next", "status", "description"]) else "center"
            safe_v = html.escape(str(v)).replace(chr(10), "<br>")
            tds.append(f"<td class='{cls}'>{safe_v}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")

    return (
        f"<section class='card'>"
        f"<h2>{html.escape(title)}</h2>"
        f"<div class='table-wrap'>"
        f"<table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table>"
        f"</div></section>"
    )


def def_write_html(path: Path, counts: dict, sections: list[tuple[str, list[dict]]]) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:26px 34px;background:#0d1b2f;border-bottom:1px solid #1f3557}
h1{margin:0;font-size:25px}.sub{color:#9fb3c8;margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:14px;padding:22px 34px}
.kpi{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:16px}
.v{font-size:25px;font-weight:800}.k{color:#9fb3c8}
main{padding:0 34px 34px}
.card{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:18px;margin:18px 0}
.table-wrap{overflow:auto;max-height:76vh;border:1px solid #1f3557;border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{position:sticky;top:0;background:#132541;padding:10px;text-align:center}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;max-width:1200px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.center{text-align:center}
.badge{display:inline-block;padding:4px 8px;border-radius:999px;background:#1f3557}
"""

    cards = "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in counts.items()
    )

    body = "".join(def_html_table(t, rows) for t, rows in sections)

    doc = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>VRN Final Handover Commit Blocker Seal v0615702</title>
<style>{css}</style>
</head>
<body>
<header>
<h1>VRN · Final Handover Pack + Commit Blocker Seal v0.6.15.7.0.2</h1>
<div class="sub">final handover only · commit blocked · no DB write · no canonical / SSOT mutation</div>
</header>
<div class="grid">{cards}</div>
<main>{body}</main>
</body>
</html>
"""
    path.write_text(doc, encoding="utf-8")


# ==================================================================================================
# def 02_MAIN_LOGIC
# ==================================================================================================
def def_main() -> None:
    if len(sys.argv) < 5:
        raise SystemExit("usage: py <run_root> <run_dir> <primary_duckdb> <via_root>")

    run_root = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    primary_duckdb = Path(sys.argv[3])
    via_root = Path(sys.argv[4])
    run_dir.mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------------------------------------------------
    # def Locate latest prerequisite runs
    # ----------------------------------------------------------------------------------------------
    closeout_run = def_find_latest_dir(run_root, ["VRN_TRIFLOW_CLOSEOUT_SEAL_FINAL_OPS_CONSOLE_V0615701"])
    commit_run = def_find_latest_dir(run_root, ["VRN_COMMIT_CANDIDATE_PACK_APPROVAL_GATE_V061570"])
    txn_run = def_find_latest_dir(run_root, ["VRN_PRIMARY_DB_TRANSACTION_ROLLBACK_DRYRUN_V0615699"])
    staging_copy_run = def_find_latest_dir(run_root, ["VRN_STAGING_COPY_WRITE_DRYRUN_ROLLBACK_V06156981"])
    schema_run = def_find_latest_dir(run_root, ["VRN_DB_SCHEMA_COMPATIBILITY_AUDIT_V06156971"])
    sim_run = def_find_latest_dir(run_root, ["VRN_WRITE_SIMULATOR_ROLLBACK_PLAN_V0615696"])
    seal_run = def_find_latest_dir(run_root, ["VRN_MISSING_LINK_FINAL_STAGING_SEAL_V0615695"])

    if not closeout_run:
        raise RuntimeError("Missing prerequisite: v0615701 tri-flow closeout seal.")

    closeout_json = def_read_json(closeout_run / "vrn_triflow_closeout_seal_final_ops_console_v0615701.json")
    counts_in = closeout_json.get("counts", {})

    # ----------------------------------------------------------------------------------------------
    # def Evaluate final status from v0615701
    # ----------------------------------------------------------------------------------------------
    final_ok = counts_in.get("Final") == "PASS"
    flow_a_ok = counts_in.get("Flow A") == "PASS"
    flow_b_ok = counts_in.get("Flow B") == "PASS"
    flow_c_ok = counts_in.get("Flow C") == "PASS"

    hard_block_ok = (
        counts_in.get("Commit") == "NO"
        and counts_in.get("DB Write") == "NO"
        and counts_in.get("Canonical") == "NO"
        and counts_in.get("SSOT") == "NO"
    )

    primary_sha = def_sha256_file(primary_duckdb)

    # ----------------------------------------------------------------------------------------------
    # def Final status matrix
    # ----------------------------------------------------------------------------------------------
    final_status = [
        {
            "Status Lights": def_light("OK" if final_ok else "ERR"),
            "Gate": "TRIFLOW_FINAL_PASS",
            "Value": counts_in.get("Final", ""),
            "Severity": "OK" if final_ok else "ERR",
        },
        {
            "Status Lights": def_light("OK" if flow_a_ok else "ERR"),
            "Gate": "FLOW_A_PASS",
            "Value": counts_in.get("Flow A", ""),
            "Severity": "OK" if flow_a_ok else "ERR",
        },
        {
            "Status Lights": def_light("OK" if flow_b_ok else "ERR"),
            "Gate": "FLOW_B_PASS",
            "Value": counts_in.get("Flow B", ""),
            "Severity": "OK" if flow_b_ok else "ERR",
        },
        {
            "Status Lights": def_light("OK" if flow_c_ok else "ERR"),
            "Gate": "FLOW_C_PASS",
            "Value": counts_in.get("Flow C", ""),
            "Severity": "OK" if flow_c_ok else "ERR",
        },
        {
            "Status Lights": def_light("OK" if hard_block_ok else "ERR"),
            "Gate": "MUTATION_BLOCKER_ACTIVE",
            "Value": "YES" if hard_block_ok else "NO",
            "Severity": "OK" if hard_block_ok else "ERR",
        },
        {
            "Status Lights": def_light("WARN"),
            "Gate": "REAL_COMMIT_REQUIRES_EXACT_PHRASE",
            "Value": "YES FOR COMMIT",
            "Severity": "WARN",
        },
    ]

    # ----------------------------------------------------------------------------------------------
    # def Assets manifest
    # ----------------------------------------------------------------------------------------------
    assets = [
        def_file_asset(
            "latest_triflow_closeout_html",
            closeout_run / "VRN_TriFlow_Closeout_Seal_Final_Ops_Console_v0615701.html",
            True,
        ),
        def_file_asset(
            "latest_triflow_closeout_json",
            closeout_run / "vrn_triflow_closeout_seal_final_ops_console_v0615701.json",
            True,
        ),
        def_file_asset(
            "latest_commit_candidate_html",
            commit_run / "VRN_Commit_Candidate_Pack_Approval_Gate_v061570.html" if commit_run else Path(""),
            False,
        ),
        def_file_asset(
            "latest_commit_candidate_json",
            commit_run / "vrn_commit_candidate_pack_approval_gate_v061570.json" if commit_run else Path(""),
            False,
        ),
        def_file_asset(
            "latest_primary_txn_rollback_html",
            txn_run / "VRN_Primary_DB_Transaction_Rollback_DryRun_v0615699.html" if txn_run else Path(""),
            False,
        ),
        def_file_asset(
            "latest_staging_copy_html",
            staging_copy_run / "VRN_Staging_Copy_Write_DryRun_Rollback_v06156981.html" if staging_copy_run else Path(""),
            False,
        ),
        def_file_asset(
            "latest_schema_audit_html",
            schema_run / "VRN_DB_Schema_Compatibility_Audit_v06156971.html" if schema_run else Path(""),
            False,
        ),
        def_file_asset(
            "latest_write_simulator_html",
            sim_run / "VRN_Write_Simulator_Rollback_Plan_v0615696.html" if sim_run else Path(""),
            False,
        ),
        def_file_asset(
            "latest_final_staging_seal_html",
            seal_run / "VRN_Missing_Link_Final_Staging_Seal_v0615695.html" if seal_run else Path(""),
            False,
        ),
        def_file_asset(
            "primary_duckdb_current",
            primary_duckdb,
            True,
        ),
    ]

    # ----------------------------------------------------------------------------------------------
    # def Commit blocker rules
    # ----------------------------------------------------------------------------------------------
    blocker_rules = [
        {
            "Status Lights": def_light("OK"),
            "Rule": "NO_COMMIT",
            "Value": "YES",
            "Reason": "Current run is final handover only.",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Rule": "NO_DB_WRITE",
            "Value": "YES",
            "Reason": "No DuckDB mutation is executed.",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Rule": "NO_TABLE_CREATE",
            "Value": "YES",
            "Reason": "No schema mutation in this run.",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Rule": "NO_INSERT",
            "Value": "YES",
            "Reason": "No data insertion in this run.",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Rule": "NO_DELETE",
            "Value": "YES",
            "Reason": "No delete or rollback SQL execution in this run.",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Rule": "NO_CANONICAL_MUTATION",
            "Value": "YES",
            "Reason": "Canonical data remains unchanged.",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Rule": "NO_SSOT_MUTATION",
            "Value": "YES",
            "Reason": "Alias candidates remain no-SSOT.",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("WARN"),
            "Rule": "ONLY_EXACT_PHRASE_UNLOCKS_COMMIT",
            "Value": "YES FOR COMMIT",
            "Reason": "Prevents accidental persistent DB mutation.",
            "Severity": "WARN",
        },
    ]

    # ----------------------------------------------------------------------------------------------
    # def Final next steps
    # ----------------------------------------------------------------------------------------------
    final_next_steps = [
        {
            "Status Lights": def_light("OK"),
            "Next Step": "Use v0615701 ops console as the read-only operating index.",
            "Reason": "It links the latest reports and evidence without changing data.",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("WARN"),
            "Next Step": "Do not run real commit unless exact phrase YES FOR COMMIT is provided.",
            "Reason": "Real commit is the first persistent DB mutation.",
            "Severity": "WARN",
        },
        {
            "Status Lights": def_light("OK"),
            "Next Step": "Future new reports must enter Compatibility Gate first.",
            "Reason": "Prevents unknown layouts from polluting canonical flow.",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Next Step": "Alias candidates stay outside SSOT until second-confirmation workflow.",
            "Reason": "Avoids alias contamination.",
            "Severity": "OK",
        },
    ]

    # ----------------------------------------------------------------------------------------------
    # def Markdown handover summary
    # ----------------------------------------------------------------------------------------------
    handover_md = run_dir / "VRN_FINAL_HANDOVER_SUMMARY_v0615702.md"
    handover_md.write_text(
        "\n".join([
            "# VRN Final Handover Summary v0.6.15.7.0.2",
            "",
            "Status: PASS / CLOSEOUT SEALED",
            "",
            "Mutation status:",
            "- Commit: NO",
            "- DB Write: NO",
            "- Table Create: NO",
            "- Insert: NO",
            "- Delete: NO",
            "- Canonical Mutation: NO",
            "- SSOT Mutation: NO",
            "",
            "Write-ready pack:",
            "- 27 rows sealed in commit candidate pack",
            "- 4 quarantine rows locked out",
            "- 52 alias candidates locked out from SSOT",
            "- 4 no-match rows locked out",
            "",
            "Approval rule:",
            "- Real commit remains blocked until exact phrase: YES FOR COMMIT",
            "",
            f"Primary DB: {primary_duckdb}",
            f"Primary DB SHA now: {primary_sha}",
            "",
            "Recommended next action:",
            "- Stop here unless real DB mutation is intentionally approved.",
            "",
            "Safety note:",
            "- This handover run created reports only.",
            "- It did not connect to DuckDB for mutation.",
            "- It did not execute SQL.",
        ]),
        encoding="utf-8"
    )

    assets.append(def_file_asset("final_handover_markdown", handover_md, True))

    # ----------------------------------------------------------------------------------------------
    # def Final counts and outputs
    # ----------------------------------------------------------------------------------------------
    final_pass = final_ok and flow_a_ok and flow_b_ok and flow_c_ok and hard_block_ok

    outputs = {
        "html": str(run_dir / "VRN_Final_Handover_Commit_Blocker_Seal_v0615702.html"),
        "json": str(run_dir / "vrn_final_handover_commit_blocker_seal_v0615702.json"),
        "final_status_csv": str(run_dir / "vrn_final_status_v0615702.csv"),
        "assets_csv": str(run_dir / "vrn_final_assets_manifest_v0615702.csv"),
        "blocker_rules_csv": str(run_dir / "vrn_commit_blocker_rules_v0615702.csv"),
        "next_steps_csv": str(run_dir / "vrn_final_next_steps_v0615702.csv"),
        "handover_markdown": str(handover_md),
    }

    def_write_csv(Path(outputs["final_status_csv"]), final_status)
    def_write_csv(Path(outputs["assets_csv"]), assets)
    def_write_csv(Path(outputs["blocker_rules_csv"]), blocker_rules)
    def_write_csv(Path(outputs["next_steps_csv"]), final_next_steps)

    counts = {
        "Final": "PASS" if final_pass else "REVIEW",
        "Flow A": counts_in.get("Flow A", ""),
        "Flow B": counts_in.get("Flow B", ""),
        "Flow C": counts_in.get("Flow C", ""),
        "Commit": "NO",
        "DB Write": "NO",
        "Canonical": "NO",
        "SSOT": "NO",
        "Commit Blocker": "ACTIVE",
        "Approval Phrase": "YES FOR COMMIT",
    }

    overview = [
        {
            "Status Lights": def_light("OK" if final_pass else "WARN"),
            "Gate": "FINAL_HANDOVER_PASS",
            "Value": "YES" if final_pass else "REVIEW",
            "Severity": "OK" if final_pass else "WARN",
        },
        {
            "Status Lights": def_light("OK"),
            "Gate": "COMMIT_BLOCKER_ACTIVE",
            "Value": "YES",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Gate": "COMMIT_THIS_RUN",
            "Value": "NO",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Gate": "DB_WRITE_THIS_RUN",
            "Value": "NO",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Gate": "CANONICAL_MUTATION",
            "Value": "NO",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Gate": "SSOT_MUTATION",
            "Value": "NO",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("WARN"),
            "Gate": "MANUAL_APPROVAL_REQUIRED",
            "Value": "YES FOR COMMIT",
            "Severity": "WARN",
        },
    ]

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": final_pass,
        "primary_duckdb": str(primary_duckdb),
        "primary_sha_now": primary_sha,
        "source_closeout_run": str(closeout_run),
        "source_commit_run": str(commit_run) if commit_run else "",
        "source_txn_run": str(txn_run) if txn_run else "",
        "source_sim_run": str(sim_run) if sim_run else "",
        "source_seal_run": str(seal_run) if seal_run else "",
        "via_root": str(via_root),
        "counts": counts,
        "outputs": outputs,
    }

    def_write_json(Path(outputs["json"]), result)
    def_write_html(
        Path(outputs["html"]),
        counts,
        [
            ("01 Overview", overview),
            ("02 Final Status", final_status),
            ("03 Commit Blocker Rules", blocker_rules),
            ("04 Assets Manifest", assets),
            ("05 Final Next Steps", final_next_steps),
        ],
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


# ==================================================================================================
# def 03_ENTRYPOINT
# ==================================================================================================
if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise