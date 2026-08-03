# -*- coding: utf-8 -*-
"""
def VDF_SentimentStrength_Router
Runs AAII Sentiment + CNN Fear & Greed Proxy + final blended sentiment strength.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from VDF_Engine_aaii_sentiment import def_fetch_aaii_sentiment
from VDF_Engine_cnn_fear_greed_proxy import def_build_cnn_fear_greed_proxy
from VDF_Engine_sentiment_strength import def_blend_scores


def def_read_json(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def def_write_json(obj: Any, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)


def def_safe_name(text: str) -> str:
    keep = []
    for ch in str(text):
        if ch.isalnum() or ch in ["_", "-", "."]:
            keep.append(ch)
        else:
            keep.append("_")
    return "".join(keep).strip("_")[:160]


def def_save_dataframe(df: pd.DataFrame, output_dir: str | Path, name: str) -> dict:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    safe = def_safe_name(name)
    csv_path = out_dir / f"{safe}.csv"
    parquet_path = out_dir / f"{safe}.parquet"

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    parquet_ok = False
    parquet_error = ""
    try:
        df.to_parquet(parquet_path, index=False)
        parquet_ok = True
    except Exception as exc:
        parquet_error = str(exc)

    return {
        "name": name,
        "rows": int(len(df)),
        "columns": list(map(str, df.columns)),
        "csv_path": str(csv_path),
        "parquet_path": str(parquet_path) if parquet_ok else "",
        "parquet_ok": parquet_ok,
        "parquet_error": parquet_error,
    }


def def_latest_numeric(df: pd.DataFrame, score_col: str, date_col: str = "def_date") -> dict:
    if df is None or df.empty or score_col not in df.columns:
        return {
            "date": None,
            "score": None,
        }

    work = df.copy()
    work[date_col] = pd.to_datetime(work[date_col], errors="coerce")
    work[score_col] = pd.to_numeric(work[score_col], errors="coerce")
    work = work.dropna(subset=[date_col, score_col]).sort_values(date_col)

    if work.empty:
        return {
            "date": None,
            "score": None,
        }

    row = work.iloc[-1]
    return {
        "date": row[date_col],
        "score": float(row[score_col]),
    }


def def_write_html_report(summary: dict, output_dir: str | Path) -> str:
    html_path = Path(output_dir) / "VDF_SentimentStrength_Report.html"

    latest = summary.get("latest", {})
    result_rows = summary.get("results", [])

    row_html = []
    for item in result_rows:
        status = item.get("status", "")
        name = item.get("name", "")
        msg = item.get("message", "")
        save = item.get("save", {})
        rows = save.get("rows", "")
        csv_path = save.get("csv_path", "")
        row_html.append(
            f"<tr><td>{name}</td><td>{status}</td><td>{rows}</td><td>{msg}</td><td>{csv_path}</td></tr>"
        )

    html = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VDF Sentiment Strength Report</title>
<style>
body {{
    font-family: "Noto Sans TC", "Microsoft JhengHei", Arial, sans-serif;
    margin: 32px;
    background: #f8faf9;
    color: #24323a;
}}
h1 {{ color: #008f7a; font-weight: 500; }}
.card {{
    background: white;
    border: 1px solid #d8e4e0;
    border-radius: 14px;
    padding: 18px 22px;
    margin: 16px 0;
    box-shadow: 0 8px 24px rgba(0,0,0,.05);
}}
.kpi {{
    display: grid;
    grid-template-columns: repeat(4, minmax(160px, 1fr));
    gap: 16px;
}}
.kpi div {{
    background: #ffffff;
    border-top: 4px solid #00a889;
    padding: 16px;
    border-radius: 12px;
}}
.big {{
    font-size: 36px;
    color: #536779;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    background: white;
}}
td, th {{
    padding: 10px;
    border-bottom: 1px solid #e5ece9;
    text-align: left;
}}
th {{ color: #006f61; }}
</style>
</head>
<body>
<h1>def VDF Sentiment Strength Report</h1>

<div class="kpi">
<div><b>Final Strength</b><br><span class="big">{latest.get("def_final_sentiment_strength", "")}</span></div>
<div><b>Final Class</b><br><span class="big">{latest.get("def_final_sentiment_class", "")}</span></div>
<div><b>CNN Proxy</b><br><span class="big">{latest.get("def_cnn_proxy_score", "")}</span></div>
<div><b>AAII</b><br><span class="big">{latest.get("def_aaii_sentiment_strength", "")}</span></div>
</div>

<div class="card">
<h2>def Run Matrix</h2>
<table>
<thead>
<tr><th>Name</th><th>Status</th><th>Rows</th><th>Message</th><th>CSV</th></tr>
</thead>
<tbody>
{''.join(row_html)}
</tbody>
</table>
</div>

<div class="card">
<h2>def Latest JSON</h2>
<pre>{json.dumps(latest, ensure_ascii=False, indent=2, default=str)}</pre>
</div>

</body>
</html>
"""

    html_path.write_text(html, encoding="utf-8")
    return str(html_path)


def def_run_router(input_json: str) -> dict:
    config = def_read_json(input_json)

    output_dir = Path(config["paths"]["output_dir"])
    log_dir = Path(config["paths"]["log_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    tasks = config.get("tasks", {})
    weights = config.get("blend_weights", {
        "cnn_proxy": 0.60,
        "aaii": 0.40,
    })

    results = []
    latest = {}

    aaii_df = None
    cnn_df = None

    if tasks.get("aaii", {}).get("enabled", True):
        try:
            aaii_df = def_fetch_aaii_sentiment(tasks.get("aaii", {}))
            save = def_save_dataframe(aaii_df, output_dir, "AAII_Sentiment_Strength")
            latest_aaii = def_latest_numeric(aaii_df, "def_aaii_sentiment_strength")
            latest["def_aaii_date"] = latest_aaii["date"]
            latest["def_aaii_sentiment_strength"] = latest_aaii["score"]
            results.append({
                "name": "AAII_SENTIMENT",
                "status": "OK",
                "message": "",
                "save": save,
            })
        except Exception as exc:
            results.append({
                "name": "AAII_SENTIMENT",
                "status": "FAIL",
                "message": str(exc),
            })

    if tasks.get("cnn_proxy", {}).get("enabled", True):
        try:
            cnn_df = def_build_cnn_fear_greed_proxy(tasks.get("cnn_proxy", {}))
            save = def_save_dataframe(cnn_df, output_dir, "CNN_Fear_Greed_Proxy_Strength")
            latest_cnn = def_latest_numeric(cnn_df, "def_cnn_proxy_score")
            latest["def_cnn_proxy_date"] = latest_cnn["date"]
            latest["def_cnn_proxy_score"] = latest_cnn["score"]

            if cnn_df is not None and not cnn_df.empty:
                latest_row = cnn_df.dropna(subset=["def_cnn_proxy_score"]).sort_values("def_date").iloc[-1]
                for col in [
                    "def_market_momentum_score",
                    "def_stock_price_strength_score",
                    "def_stock_price_breadth_proxy_score",
                    "def_put_call_proxy_score",
                    "def_market_volatility_score",
                    "def_safe_haven_demand_score",
                    "def_junk_bond_demand_score",
                    "def_cnn_proxy_class",
                ]:
                    if col in latest_row:
                        latest[col] = latest_row[col]

            results.append({
                "name": "CNN_FEAR_GREED_PROXY",
                "status": "OK",
                "message": "",
                "save": save,
            })
        except Exception as exc:
            results.append({
                "name": "CNN_FEAR_GREED_PROXY",
                "status": "FAIL",
                "message": str(exc),
            })

    blend = def_blend_scores([
        {
            "name": "cnn_proxy",
            "score": latest.get("def_cnn_proxy_score"),
            "weight": weights.get("cnn_proxy", 0.60),
        },
        {
            "name": "aaii",
            "score": latest.get("def_aaii_sentiment_strength"),
            "weight": weights.get("aaii", 0.40),
        },
    ])

    latest.update(blend)

    latest_df = pd.DataFrame([latest])
    latest_save = def_save_dataframe(latest_df, output_dir, "VDF_SentimentStrength_Latest")
    results.append({
        "name": "VDF_SENTIMENT_STRENGTH_LATEST",
        "status": "OK",
        "message": "",
        "save": latest_save,
    })

    summary = {
        "schema_version": "VDF_SentimentStrength_RunResult_v0100",
        "input_json": input_json,
        "output_dir": str(output_dir),
        "ok_count": len([x for x in results if x.get("status") == "OK"]),
        "fail_count": len([x for x in results if x.get("status") == "FAIL"]),
        "results": results,
        "latest": latest,
    }

    result_path = log_dir / "VDF_SentimentStrength_RunResult.json"
    latest_path = output_dir / "VDF_SentimentStrength_Latest.json"

    def_write_json(summary, result_path)
    def_write_json(latest, latest_path)

    html_path = def_write_html_report(summary, output_dir)
    summary["html_report"] = html_path
    def_write_json(summary, result_path)

    return summary


def def_main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", required=True)
    args = parser.parse_args()

    summary = def_run_router(args.input_json)

    print("=" * 80)
    print("def VDF SentimentStrength Run Complete")
    print("=" * 80)
    print(f"OK    : {summary['ok_count']}")
    print(f"FAIL  : {summary['fail_count']}")
    print(f"HTML  : {summary.get('html_report', '')}")
    print("LATEST:")
    print(json.dumps(summary.get("latest", {}), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    def_main()
