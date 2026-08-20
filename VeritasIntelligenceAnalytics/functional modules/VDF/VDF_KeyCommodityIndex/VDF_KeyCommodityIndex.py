# -*- coding: utf-8 -*-
"""
def VDF_KeyCommodityIndex.py
def Free API commodity index + steel/cement plant damage-signal database.
"""

# =============================================================================
# def PARAMETERS AT TOP
# =============================================================================

import os
import re
import io
import json
import time
import math
import hashlib
import datetime as dt
from typing import Dict, List, Any, Optional, Tuple

def_PARAM_CONFIG_PATH = os.environ.get("VDF_KEYCOMMODITY_CONFIG", "")
def_PARAM_DEFAULT_TIMEOUT = 30
def_PARAM_USER_AGENT = "VeritasIntelligenceAnalytics/VDF_KeyCommodityIndex/1.0"

# =============================================================================
# def IMPORTS
# =============================================================================

import requests
import pandas as pd

try:
    import duckdb
except Exception:
    duckdb = None

# =============================================================================
# def BASIC UTILITIES
# =============================================================================

def def_log(level: str, message: str) -> None:
    ts = dt.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {message}", flush=True)

def def_read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def def_ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def def_sha12(value: str) -> str:
    return hashlib.sha256(str(value).encode("utf-8", errors="ignore")).hexdigest()[:12]

def def_now_utc() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def def_safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        s = str(x).strip()
        if s in ["", ".", "nan", "NaN", "None"]:
            return None
        return float(s)
    except Exception:
        return None

def def_clean_text(x: Any) -> str:
    if x is None:
        return ""
    s = str(x)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def def_http_get(url: str, params: Optional[Dict[str, Any]] = None, timeout: int = def_PARAM_DEFAULT_TIMEOUT) -> requests.Response:
    headers = {"User-Agent": def_PARAM_USER_AGENT}
    r = requests.get(url, params=params, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r

def def_http_post(url: str, data: Any = None, timeout: int = def_PARAM_DEFAULT_TIMEOUT) -> requests.Response:
    headers = {"User-Agent": def_PARAM_USER_AGENT}
    r = requests.post(url, data=data, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r

# =============================================================================
# def COMMODITY PRICE FETCHERS
# =============================================================================

def def_fetch_fred_series(series_id: str, code: str, name: str, group: str, unit: str, source: str, fred_template: str) -> pd.DataFrame:
    url = fred_template.replace("{SERIES_ID}", series_id)
    def_log("RUN", f"Fetching FRED series: {series_id} / {code}")
    r = def_http_get(url)
    df = pd.read_csv(io.StringIO(r.text))
    value_col = series_id
    if value_col not in df.columns:
        value_col = df.columns[-1]
    df = df.rename(columns={"DATE": "date", value_col: "value"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = df["value"].apply(def_safe_float)
    df = df.dropna(subset=["date", "value"]).copy()
    df["def_code"] = code
    df["def_name"] = name
    df["def_group"] = group
    df["def_series_id"] = series_id
    df["def_unit"] = unit
    df["def_source"] = source
    df["def_fetch_time_utc"] = def_now_utc()
    df = df[["date","def_code","def_name","def_group","def_series_id","value","def_unit","def_source","def_fetch_time_utc"]]
    return df

def def_enrich_price_features(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = []
    for code, g in df.sort_values("date").groupby("def_code"):
        x = g.copy()
        x["def_mom_pct"] = x["value"].pct_change(1) * 100.0
        x["def_yoy_pct"] = x["value"].pct_change(12) * 100.0
        x["def_ma_3m"] = x["value"].rolling(3, min_periods=1).mean()
        x["def_ma_12m"] = x["value"].rolling(12, min_periods=3).mean()
        x["def_vol_12m"] = x["value"].pct_change().rolling(12, min_periods=6).std() * math.sqrt(12)
        mean36 = x["value"].rolling(36, min_periods=12).mean()
        std36 = x["value"].rolling(36, min_periods=12).std()
        x["def_zscore_36m"] = (x["value"] - mean36) / std36
        out.append(x)
    return pd.concat(out, ignore_index=True)

def def_fetch_all_commodity_prices(config: Dict[str, Any]) -> pd.DataFrame:
    fred_template = config["def_free_api_sources"]["def_fred_csv"]
    frames = []
    for item in config["def_commodity_series"]:
        try:
            frames.append(def_fetch_fred_series(
                series_id=item["def_series_id"],
                code=item["def_code"],
                name=item["def_name"],
                group=item["def_group"],
                unit=item["def_unit"],
                source=item["def_source"],
                fred_template=fred_template
            ))
            time.sleep(float(config["def_runtime"].get("def_request_sleep_sec", 0.25)))
        except Exception as e:
            def_log("WARN", f"FRED failed for {item.get('def_series_id')}: {e}")
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    return def_enrich_price_features(df)

def def_build_key_commodity_index(price_df: pd.DataFrame) -> pd.DataFrame:
    if price_df.empty:
        return pd.DataFrame()
    z = price_df[["date","def_code","def_group","def_zscore_36m"]].dropna().copy()
    pivot = z.pivot_table(index="date", columns="def_group", values="def_zscore_36m", aggfunc="mean").reset_index()
    signal_cols = [c for c in pivot.columns if c != "date"]
    if not signal_cols:
        return pd.DataFrame()
    pivot["def_key_commodity_index_z"] = pivot[signal_cols].mean(axis=1)
    pivot["def_index_signal"] = pivot["def_key_commodity_index_z"].apply(
        lambda v: "HIGH_COST_PRESSURE" if v >= 1.0 else ("LOW_COST_PRESSURE" if v <= -1.0 else "NEUTRAL")
    )
    pivot["def_fetch_time_utc"] = def_now_utc()
    return pivot.sort_values("date").reset_index(drop=True)

# =============================================================================
# def ASSET SEED / DISCOVERY
# =============================================================================

def def_read_seed_assets(config: Dict[str, Any]) -> pd.DataFrame:
    seed_cfg = config.get("def_asset_seed_csv", {})
    paths = seed_cfg.get("def_local_paths", [])
    frames = []
    for path in paths:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path, encoding="utf-8-sig")
                df["def_source_layer"] = "seed_csv"
                frames.append(df)
                def_log("OK", f"Loaded seed asset CSV: {path}")
            except Exception as e:
                def_log("WARN", f"Cannot read seed CSV {path}: {e}")
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    return def_normalize_asset_df(df)

def def_overpass_query_for_country(country_iso2: str, asset_type: str, config: Dict[str, Any]) -> str:
    discover = config["def_asset_discovery"]
    if asset_type == "steel":
        regex = discover["def_steel_name_regex"]
        product_regex = "(steel|iron|blast furnace|metallurgical|rolling mill|EAF|DRI|HBI)"
    else:
        regex = discover["def_cement_name_regex"]
        product_regex = "(cement|clinker|lime|kiln|concrete)"

    query = f"""
[out:json][timeout:45];
area["ISO3166-1"="{country_iso2}"][admin_level=2]->.searchArea;
(
  nwr(area.searchArea)["name"~"{regex}",i];
  nwr(area.searchArea)["industrial"~"{product_regex}",i];
  nwr(area.searchArea)["product"~"{product_regex}",i];
  nwr(area.searchArea)["man_made"~"(works|plant)",i]["name"~"{regex}",i];
  nwr(area.searchArea)["landuse"="industrial"]["name"~"{regex}",i];
);
out center tags 250;
"""
    return query

def def_flatten_osm_element(el: Dict[str, Any], country_iso2: str, asset_type: str) -> Dict[str, Any]:
    tags = el.get("tags", {}) or {}
    lat = el.get("lat")
    lon = el.get("lon")
    if lat is None or lon is None:
        center = el.get("center", {}) or {}
        lat = center.get("lat")
        lon = center.get("lon")
    name = tags.get("name") or tags.get("operator") or tags.get("brand") or f"OSM_{el.get('type')}_{el.get('id')}"
    return {
        "asset_id": "osm_" + def_sha12(f"{el.get('type')}_{el.get('id')}_{asset_type}"),
        "asset_name": def_clean_text(name),
        "asset_type": asset_type,
        "country_iso2": country_iso2,
        "region": "",
        "latitude": def_safe_float(lat),
        "longitude": def_safe_float(lon),
        "capacity": None,
        "owner": def_clean_text(tags.get("operator") or tags.get("owner") or ""),
        "source_url": f"https://www.openstreetmap.org/{el.get('type')}/{el.get('id')}",
        "source_name": "OpenStreetMap Overpass",
        "source_raw_tags_json": json.dumps(tags, ensure_ascii=False),
        "def_source_layer": "overpass"
    }

def def_fetch_overpass_assets(config: Dict[str, Any]) -> pd.DataFrame:
    if not config["def_asset_discovery"].get("def_use_overpass", True):
        return pd.DataFrame()

    endpoint = config["def_free_api_sources"]["def_overpass"]
    all_countries = []
    for region_name, countries in config["def_regions"].items():
        for c in countries:
            all_countries.append((region_name.replace("def_", ""), c))
    unique_pairs = list(dict.fromkeys(all_countries))

    rows = []
    for region, country in unique_pairs:
        for asset_type in config["def_asset_discovery"].get("def_asset_types", ["steel","cement"]):
            try:
                q = def_overpass_query_for_country(country, asset_type, config)
                def_log("RUN", f"Overpass {country} / {asset_type}")
                r = def_http_post(endpoint, data={"data": q}, timeout=int(config["def_runtime"].get("def_request_timeout_sec", 30)) + 30)
                js = r.json()
                for el in js.get("elements", []):
                    row = def_flatten_osm_element(el, country, asset_type)
                    row["region"] = region
                    rows.append(row)
                time.sleep(float(config["def_runtime"].get("def_request_sleep_sec", 0.25)))
            except Exception as e:
                def_log("WARN", f"Overpass failed {country}/{asset_type}: {e}")

    if not rows:
        return pd.DataFrame()
    return def_normalize_asset_df(pd.DataFrame(rows))

def def_normalize_asset_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    col_defaults = {
        "asset_id": "",
        "asset_name": "",
        "asset_type": "",
        "country_iso2": "",
        "region": "",
        "latitude": None,
        "longitude": None,
        "capacity": None,
        "owner": "",
        "source_url": "",
        "source_name": "",
        "source_raw_tags_json": "",
        "def_source_layer": ""
    }
    for c, default in col_defaults.items():
        if c not in df.columns:
            df[c] = default

    df["asset_name"] = df["asset_name"].apply(def_clean_text)
    df["asset_type"] = df["asset_type"].apply(lambda x: def_clean_text(x).lower())
    df["country_iso2"] = df["country_iso2"].apply(lambda x: def_clean_text(x).upper())
    df["region"] = df["region"].apply(def_clean_text)
    df["latitude"] = df["latitude"].apply(def_safe_float)
    df["longitude"] = df["longitude"].apply(def_safe_float)
    df["asset_id"] = df.apply(
        lambda r: r["asset_id"] if def_clean_text(r["asset_id"]) else "asset_" + def_sha12(f"{r['asset_name']}_{r['asset_type']}_{r['country_iso2']}_{r['latitude']}_{r['longitude']}"),
        axis=1
    )
    df["def_fetch_time_utc"] = def_now_utc()
    df = df.drop_duplicates(subset=["asset_id"]).reset_index(drop=True)
    return df[list(col_defaults.keys()) + ["def_fetch_time_utc"]]

def def_build_asset_database(config: Dict[str, Any]) -> pd.DataFrame:
    frames = []
    seed = def_read_seed_assets(config)
    if not seed.empty:
        frames.append(seed)
    overpass = def_fetch_overpass_assets(config)
    if not overpass.empty:
        frames.append(overpass)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df = def_normalize_asset_df(df)
    df = df.drop_duplicates(subset=["asset_name","asset_type","country_iso2"], keep="first").reset_index(drop=True)
    return df

# =============================================================================
# def DAMAGE SIGNAL DETECTION
# =============================================================================

def def_make_gdelt_query(asset_name: str, asset_type: str, country_iso2: str, config: Dict[str, Any]) -> str:
    damage_terms = " OR ".join([f'"{k}"' for k in config["def_damage_detection"]["def_keywords_damage"][:24]])
    if asset_name and len(asset_name) >= 4:
        return f'"{asset_name}" ({damage_terms})'
    asset_terms = " OR ".join([f'"{k}"' for k in config["def_damage_detection"]["def_keywords_asset"]])
    return f'({asset_terms}) ({damage_terms}) "{country_iso2}"'

def def_fetch_gdelt_articles(query: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    endpoint = config["def_free_api_sources"]["def_gdelt_doc"]
    max_records = int(config["def_damage_detection"].get("def_gdelt_max_records_per_asset", 30))
    timespan = f"{int(config['def_runtime'].get('def_lookback_days', 45))}d"
    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": max_records,
        "sort": "datedesc",
        "timespan": timespan
    }
    try:
        r = def_http_get(endpoint, params=params, timeout=int(config["def_runtime"].get("def_request_timeout_sec", 30)))
        js = r.json()
        return js.get("articles", []) or []
    except Exception as e:
        def_log("WARN", f"GDELT failed: {e}")
        return []

def def_score_article(asset_name: str, article: Dict[str, Any], config: Dict[str, Any]) -> Tuple[int, List[str]]:
    title = def_clean_text(article.get("title", ""))
    url = def_clean_text(article.get("url", ""))
    domain = def_clean_text(article.get("domain", ""))
    text = f"{title} {url} {domain}".lower()
    asset_name_l = def_clean_text(asset_name).lower()
    score = 0
    hits = []

    if asset_name_l and asset_name_l in text:
        score += 35
        hits.append("asset_name")

    for kw in config["def_damage_detection"]["def_keywords_damage"]:
        if kw.lower() in text:
            score += 12
            hits.append(kw)

    strong_terms = ["damaged","destroyed","strike","attack","explosion","shutdown","halted","offline","停產","受損","攻擊","爆炸"]
    for kw in strong_terms:
        if kw.lower() in text:
            score += 10

    if "plant" in text or "mill" in text or "factory" in text or "cement" in text or "steel" in text:
        score += 10
        hits.append("industrial_asset_term")

    return min(score, 100), list(dict.fromkeys(hits))

def def_classify_signal(score: int, config: Dict[str, Any]) -> str:
    h = int(config["def_damage_detection"].get("def_high_signal_threshold", 70))
    m = int(config["def_damage_detection"].get("def_medium_signal_threshold", 40))
    l = int(config["def_damage_detection"].get("def_low_signal_threshold", 20))
    if score >= h:
        return "HIGH_SIGNAL_REVIEW"
    if score >= m:
        return "MEDIUM_SIGNAL"
    if score >= l:
        return "LOW_SIGNAL"
    return "NO_SIGNAL"

def def_scan_damage_for_assets(asset_df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    if asset_df.empty:
        return pd.DataFrame()

    max_assets = int(config["def_runtime"].get("def_max_assets_to_scan", 120))
    scan_df = asset_df.head(max_assets).copy()
    rows = []
    for idx, r in scan_df.iterrows():
        asset_name = def_clean_text(r.get("asset_name", ""))
        if len(asset_name) < 4:
            continue
        query = def_make_gdelt_query(asset_name, r.get("asset_type",""), r.get("country_iso2",""), config)
        def_log("RUN", f"GDELT damage scan {idx+1}/{len(scan_df)}: {asset_name}")
        articles = def_fetch_gdelt_articles(query, config)

        if not articles:
            rows.append({
                "asset_id": r["asset_id"],
                "asset_name": asset_name,
                "asset_type": r.get("asset_type",""),
                "country_iso2": r.get("country_iso2",""),
                "region": r.get("region",""),
                "def_signal_score": 0,
                "def_signal_class": "NO_SIGNAL",
                "def_signal_hits": "",
                "def_article_title": "",
                "def_article_url": "",
                "def_article_domain": "",
                "def_article_seen_date": "",
                "def_query": query,
                "def_fetch_time_utc": def_now_utc()
            })
        else:
            best = None
            best_score = -1
            best_hits = []
            for art in articles:
                score, hits = def_score_article(asset_name, art, config)
                if score > best_score:
                    best = art
                    best_score = score
                    best_hits = hits

            rows.append({
                "asset_id": r["asset_id"],
                "asset_name": asset_name,
                "asset_type": r.get("asset_type",""),
                "country_iso2": r.get("country_iso2",""),
                "region": r.get("region",""),
                "def_signal_score": int(best_score),
                "def_signal_class": def_classify_signal(int(best_score), config),
                "def_signal_hits": ";".join(best_hits),
                "def_article_title": def_clean_text(best.get("title","")) if best else "",
                "def_article_url": def_clean_text(best.get("url","")) if best else "",
                "def_article_domain": def_clean_text(best.get("domain","")) if best else "",
                "def_article_seen_date": def_clean_text(best.get("seendate","")) if best else "",
                "def_query": query,
                "def_fetch_time_utc": def_now_utc()
            })

        time.sleep(float(config["def_runtime"].get("def_request_sleep_sec", 0.25)))

    return pd.DataFrame(rows)

# =============================================================================
# def OUTPUT WRITERS
# =============================================================================

def def_write_table(df: pd.DataFrame, name: str, output_dir: str, config: Dict[str, Any]) -> Dict[str, str]:
    paths = {}
    if df is None:
        df = pd.DataFrame()
    def_ensure_dir(output_dir)

    if config["def_runtime"].get("def_write_csv", True):
        csv_path = os.path.join(output_dir, f"{name}.csv")
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        paths["csv"] = csv_path

    if config["def_runtime"].get("def_write_json", True):
        json_path = os.path.join(output_dir, f"{name}.json")
        df.to_json(json_path, orient="records", force_ascii=False, indent=2, date_format="iso")
        paths["json"] = json_path

    if config["def_runtime"].get("def_write_parquet", True):
        try:
            pq_path = os.path.join(output_dir, f"{name}.parquet")
            df.to_parquet(pq_path, index=False)
            paths["parquet"] = pq_path
        except Exception as e:
            def_log("WARN", f"Parquet write failed for {name}: {e}")

    return paths

def def_write_duckdb(tables: Dict[str, pd.DataFrame], output_dir: str) -> str:
    if duckdb is None:
        def_log("WARN", "duckdb package not installed; skipping DuckDB output.")
        return ""
    db_path = os.path.join(output_dir, "VDF_KeyCommodityIndex.duckdb")
    con = duckdb.connect(db_path)
    try:
        for name, df in tables.items():
            if df is None:
                df = pd.DataFrame()
            con.register("tmp_df", df)
            con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM tmp_df")
            con.unregister("tmp_df")
    finally:
        con.close()
    return db_path

def def_write_report(tables: Dict[str, pd.DataFrame], output_dir: str, config: Dict[str, Any], registry: Dict[str, Any]) -> str:
    report_path = os.path.join(output_dir, "VDF_KeyCommodityIndex_Report.html")
    latest_price = tables.get("commodity_prices", pd.DataFrame())
    damage = tables.get("plant_damage_signals", pd.DataFrame())

    price_tail_html = ""
    damage_html = ""

    if not latest_price.empty:
        tail = latest_price.sort_values("date").groupby("def_code").tail(1)
        price_tail_html = tail.to_html(index=False, escape=False)

    if not damage.empty:
        d = damage.sort_values("def_signal_score", ascending=False).head(50)
        damage_html = d.to_html(index=False, escape=False)

    html = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<title>VDF Key Commodity Index Report</title>
<style>
body {{ font-family: 'Noto Sans TC', 'Microsoft JhengHei', Arial, sans-serif; background:#f9f9f6; color:#1f2a2a; margin:28px; }}
h1,h2 {{ letter-spacing:.02em; }}
.card {{ background:white; border:1px solid #d9e2df; border-radius:16px; padding:18px; margin:18px 0; box-shadow:0 10px 30px rgba(20,40,40,.06); }}
table {{ border-collapse:collapse; width:100%; font-size:13px; }}
td,th {{ border-bottom:1px solid #e7eeeb; padding:7px; text-align:left; vertical-align:top; }}
th {{ background:#eef5f2; }}
.badge {{ display:inline-block; padding:4px 9px; border-radius:999px; background:#dfeee9; }}
</style>
</head>
<body>
<h1>def VDF Key Commodity Index</h1>
<div class="card">
<div class="badge">Generated: {def_now_utc()}</div>
<p>Commodity index + steel/cement plant damage-signal database. Signal status requires analyst review before trading decision.</p>
</div>
<div class="card"><h2>def Latest Commodity Prices</h2>{price_tail_html}</div>
<div class="card"><h2>def Top Damage Signals</h2>{damage_html}</div>
<div class="card"><h2>def Registry</h2><pre>{json.dumps(registry, ensure_ascii=False, indent=2)}</pre></div>
</body></html>"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)
    return report_path

def def_write_registry(registry: Dict[str, Any], output_dir: str) -> str:
    path = os.path.join(output_dir, "VDF_KeyCommodityIndex_registry.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    return path

# =============================================================================
# def MAIN
# =============================================================================

def def_main() -> None:
    config_path = def_PARAM_CONFIG_PATH
    if not config_path:
        raise RuntimeError("Missing config path. Set VDF_KEYCOMMODITY_CONFIG environment variable.")

    config = def_read_json(config_path)
    output_dir = config["def_system"]["def_output_dir"]
    cache_dir = config["def_system"]["def_cache_dir"]
    def_ensure_dir(output_dir)
    def_ensure_dir(cache_dir)

    def_log("RUN", "Fetching commodity prices.")
    commodity_prices = def_fetch_all_commodity_prices(config)
    key_index = def_build_key_commodity_index(commodity_prices)

    def_log("RUN", "Building steel/cement asset database.")
    plant_assets = def_build_asset_database(config)

    def_log("RUN", "Scanning damage signals via GDELT.")
    plant_damage_signals = def_scan_damage_for_assets(plant_assets, config)

    tables = {
        "commodity_prices": commodity_prices,
        "key_commodity_index": key_index,
        "plant_assets": plant_assets,
        "plant_damage_signals": plant_damage_signals
    }

    output_paths = {}
    for name, df in tables.items():
        output_paths[name] = def_write_table(df, name, output_dir, config)

    duckdb_path = ""
    if config["def_runtime"].get("def_write_duckdb", True):
        duckdb_path = def_write_duckdb(tables, output_dir)

    registry = {
        "def_status": "VDF_KEYCOMMODITY_INDEX_READY",
        "def_generated_utc": def_now_utc(),
        "def_config_path": config_path,
        "def_rows": {name: int(len(df)) if df is not None else 0 for name, df in tables.items()},
        "def_output_paths": output_paths,
        "def_duckdb_path": duckdb_path,
        "def_warning": "Damage signal is open-source signal, not final physical damage confirmation."
    }

    registry_path = def_write_registry(registry, output_dir)
    report_path = def_write_report(tables, output_dir, config, registry)

    def_log("OK", f"Registry: {registry_path}")
    def_log("OK", f"Report  : {report_path}")
    def_log("OK", "VDF_KeyCommodityIndex finished.")

if __name__ == "__main__":
    def_main()
