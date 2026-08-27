#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VAP_ENG005_TemplateRunner — 圖表模板跑器(批123;via-vaptpl)
====================================================================
操作員令:「各類圖形的組合及規格的事先設定及隨時可更改的彈性;
模板保存;協助導入資料庫資料自動更新功能」。
冊:VAP_Template_Registry(glob 最新版;append-only)。
機制:
  ① 事先設定 — 模板=kind+data 綁定+params 冊存。
  ② 隨時可改 — --set k=v(dot 路徑)覆寫本次渲染,不回寫冊;
     --save-as <新名> 把覆寫後規格另存新模板(append-only)。
  ③ 自動更新 — 渲染即重讀資料來源(rawwide/duckdb/parquet 最新檔),
     零快取;資料換新=圖自動換新。
  ④ 渲染分派 — dual/series/stack/panels → ENG001 Autoplot 最新版
     (SVG 理印,複用 --sql/--transform/--bands 全能力);
     corrheat → seaborn(圖規鎖:diverging·center 0);
     ta_overlay → ENG004 TA 工廠家族+matplotlib;
     map → leaflet 自足 HTML(adv/map 型)。
用法:
  via-vaptpl --list
  via-vaptpl --render twii_gspc_dual [--set params.left=SOX]
  via-vaptpl --render all
  via-vaptpl --render <tpl> --set ... --save-as <新名>
  via-vaptpl --selftest        → 十檢(在庫資料零網路)
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

import copy
import importlib.util
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent          # VAP/engine
VAP = HERE.parent
VIA = VAP.parent.parent
RUNS = VIA / "VIA_Reports" / "vap_tpl_runs"
REG_GLOB = "VAP_Template_Registry_v*.json"


def load_registry(reg_path: Path | None = None) -> tuple[dict, Path]:
    if reg_path is not None:
        return json.loads(reg_path.read_text(encoding="utf-8-sig")), reg_path
    hits = sorted((VAP / "spec").glob(REG_GLOB))
    if not hits:
        raise FileNotFoundError("模板冊缺(VAP_Template_Registry_v*.json)")
    return json.loads(hits[-1].read_text(encoding="utf-8-sig")), hits[-1]


def latest_engine(pattern: str) -> Path | None:
    hits = sorted(HERE.glob(pattern))
    return hits[-1] if hits else None


def apply_sets(tpl: dict, sets: list[str]) -> dict:
    """--set a.b=v dot 路徑覆寫(隨時可改彈性;不回寫冊)"""
    out = copy.deepcopy(tpl)
    for kv in sets:
        if "=" not in kv:
            continue
        key, val = kv.split("=", 1)
        try:
            val = json.loads(val)   # 數字/布林/JSON 陣列自動轉型
        except Exception:
            pass                    # 純字串原樣
        node = out
        parts = key.split(".")
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = val
    return out


def resolve_data_path(tpl: dict) -> Path:
    """渲染即重解析資料檔(自動更新:零快取,永遠讀最新)"""
    p = Path(tpl["data"]["path"])
    return p if p.is_absolute() else VAP / p


def load_frame(tpl: dict):
    import pandas as pd
    dp = resolve_data_path(tpl)
    if dp.suffix == ".parquet":
        df = pd.read_parquet(dp)
    else:
        df = pd.DataFrame(json.loads(dp.read_text(encoding="utf-8-sig")))
    x = tpl["data"].get("x", "date")
    if x in df.columns:
        df = df.set_index(x)
        df.index = pd.to_datetime(df.index)
    return df.sort_index()


def _setup_cjk_font():
    """CJK 字型解析(容器=WenQuanYi;工作站=JhengHei/Noto);缺=誠實降級不豆腐化標題"""
    try:
        import matplotlib
        from matplotlib import font_manager
        have = {f.name for f in font_manager.fontManager.ttflist}
        for cand in ("Microsoft JhengHei", "Noto Sans CJK TC", "WenQuanYi Zen Hei"):
            if cand in have:
                matplotlib.rcParams["font.family"] = ["sans-serif"]
                matplotlib.rcParams["font.sans-serif"] = [cand, "DejaVu Sans"]
                matplotlib.rcParams["axes.unicode_minus"] = False
                return cand
    except Exception:
        pass
    return None


# ── 渲染道 ───────────────────────────────────────────────────────
def render_eng001(tpl: dict, out_dir: Path) -> tuple[str, str]:
    eng = latest_engine("VAP_ENG001_AutoplotEngineChartlib_v*.py")
    if eng is None:
        return "FAIL", "ENG001 Autoplot 缺"
    prm = tpl["params"]
    args = [sys.executable, str(eng), "--base", str(VIA),
            "--db", str(resolve_data_path(tpl)),
            "--table", tpl["data"]["table"], "--x", tpl["data"].get("x", "date"),
            "--out", str(out_dir)]
    kind = tpl["kind"]
    if kind == "dual":
        args += ["--left", prm["left"], "--right", prm["right"],
                 "--left-form", prm.get("left_form", "bar"),
                 "--right-form", prm.get("right_form", "line")]
    elif kind == "series":
        args += ["--series", prm["series"]]
        if prm.get("transform"):
            args += ["--transform", prm["transform"]]
    elif kind == "stack":
        args += ["--series", prm["series"], "--stackchart", prm.get("mode", "sarea")]
    elif kind == "panels":
        args += ["--panels", prm["panels"]]
    else:
        return "FAIL", f"ENG001 不支援 kind={kind}"
    if prm.get("bands"):
        args += ["--bands", prm["bands"]]
    if tpl.get("sql"):
        args += ["--sql", tpl["sql"]]
    r = subprocess.run(args, capture_output=True, text=True, timeout=600)
    made = [p.name for p in out_dir.glob("*.html")]
    if r.returncode == 0 and made:
        return "OK", f"ENG001({eng.name})→ {len(made)} 頁"
    return "FAIL", (r.stderr or r.stdout).strip()[-140:]


def render_corrheat(tpl: dict, out_dir: Path) -> tuple[str, str]:
    import matplotlib
    matplotlib.use("Agg")
    _setup_cjk_font()
    import matplotlib.pyplot as plt
    import seaborn as sns
    prm = tpl["params"]
    df = load_frame(tpl)
    cols = [c for c in prm["columns"] if c in df.columns]
    if len(cols) < 2:
        return "FAIL", "相關欄不足 2"
    sub = df[cols].ffill().tail(int(prm.get("lookback", 240)))
    mat = (sub.pct_change() if prm.get("on", "returns") == "returns" else sub).corr()
    fig, ax = plt.subplots(figsize=(1.1 * len(cols) + 2, 0.9 * len(cols) + 2))
    sns.heatmap(mat, annot=True, fmt=".2f", center=0.0, vmin=-1, vmax=1,
                cmap=sns.color_palette("RdBu_r", 15), square=True,
                linewidths=0.5, cbar_kws={"shrink": 0.8}, ax=ax)  # 圖規鎖:diverging 15·zmid 0
    ax.set_title(f"{tpl.get('zh', tpl['name'])} · lookback {prm.get('lookback', 240)}d"
                 f" · {prm.get('on', 'returns')}", fontsize=11)
    fig.tight_layout()
    out = out_dir / f"{tpl['name']}.png"
    fig.savefig(out, dpi=110)
    plt.close(fig)
    return "OK", f"{out.name}({out.stat().st_size // 1024}KB · {len(cols)}×{len(cols)})"


def _load_ta_module():
    eng = latest_engine("VAP_ENG004_TAFactory_v*.py")
    if eng is None:
        return None
    spec = importlib.util.spec_from_file_location("vap_ta_dyn", eng)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def render_ta_overlay(tpl: dict, out_dir: Path) -> tuple[str, str]:
    import matplotlib
    matplotlib.use("Agg")
    _setup_cjk_font()
    import matplotlib.pyplot as plt
    ta = _load_ta_module()
    if ta is None:
        return "FAIL", "ENG004 TA 工廠缺"
    prm = tpl["params"]
    df = load_frame(tpl)
    col = prm["instrument"]
    if col not in df.columns:
        return "FAIL", f"欄缺 {col}"
    px = df[col].ffill().tail(int(prm.get("lookback", 720)))
    sma = ta.close_family()["SMA"]
    fig, ax = plt.subplots(figsize=(12, 5.4))
    ax.plot(px.index, px.values, lw=1.4, label=col, zorder=3)
    for n in prm.get("periods", [20, 60, 240]):
        line = sma(px, int(n))
        ax.plot(line.index, line.values, lw=0.9, alpha=0.85, label=f"SMA{n}")
    ax.legend(loc="upper left", fontsize=9, ncols=4)
    ax.grid(alpha=0.25)
    ax.set_title(f"{tpl.get('zh', tpl['name'])} · 週期輪 {prm.get('periods')}", fontsize=11)
    fig.tight_layout()
    out = out_dir / f"{tpl['name']}.png"
    fig.savefig(out, dpi=110)
    plt.close(fig)
    return "OK", f"{out.name}({out.stat().st_size // 1024}KB)"


def render_map(tpl: dict, out_dir: Path) -> tuple[str, str]:
    """adv/map 型:leaflet 自足 HTML;數據=渲染時自資料庫取最新值+Δ"""
    prm = tpl["params"]
    df = load_frame(tpl)
    dd = int(prm.get("delta_days", 5))
    marks = []
    for m in prm.get("markers", []):
        col = m["col"]
        if col not in df.columns:
            continue
        s = df[col].ffill().dropna()
        if s.empty:
            continue
        last = float(s.iloc[-1])
        prev = float(s.iloc[-1 - dd]) if len(s) > dd else last
        chg = (last / prev - 1) * 100 if prev else 0.0
        marks.append({"label": m["label"], "lat": m["lat"], "lon": m["lon"],
                      "value": round(last, 2), "chg": round(chg, 2),
                      "asof": str(s.index[-1])[:10]})
    if not marks:
        return "FAIL", "零可繪標記"
    html = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>{tpl.get('zh', tpl['name'])}</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>html,body,#map{{height:100%;margin:0}}
.lbl{{font:12px/1.4 'Microsoft JhengHei',sans-serif}}</style></head><body>
<div id="map"></div><script>
// 地圖 × 數據(批123;圖磚由工作站瀏覽器連線載入;數據=產頁時最新庫值)
const M = {json.dumps(marks, ensure_ascii=False)};
const map = L.map('map').setView([25, 60], 2);
L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
  {{attribution: '&copy; OpenStreetMap'}}).addTo(map);
for (const m of M) {{
  const up = m.chg >= 0;
  L.circleMarker([m.lat, m.lon], {{radius: 9, color: up ? '#0a7d43' : '#b3282d',
      fillOpacity: .75}}).addTo(map)
    .bindPopup(`<div class="lbl"><b>${{m.label}}</b><br>值 ${{m.value}}` +
               ` · ${{m.chg >= 0 ? '+' : ''}}${{m.chg}}% / {dd}d<br>截至 ${{m.asof}}</div>`);
}}
</script></body></html>"""
    out = out_dir / f"{tpl['name']}.html"
    out.write_text(html, encoding="utf-8")
    return "OK", f"{out.name}({len(marks)} 標記;圖磚候工作站瀏覽器)"


RENDERERS = {"dual": render_eng001, "series": render_eng001, "stack": render_eng001,
             "panels": render_eng001, "corrheat": render_corrheat,
             "ta_overlay": render_ta_overlay, "map": render_map}


def render(names: list[str], sets: list[str], save_as: str | None,
           reg_path: Path | None = None, out_root: Path | None = None) -> int:
    reg, rp = load_registry(reg_path)
    idx = {t["name"]: t for t in reg["templates"]}
    targets = list(idx) if names == ["all"] else names
    missing = [n for n in targets if n not in idx]
    if missing:
        print(f"[FAIL] 模板不在冊:{','.join(missing)}(--list 可查)")
        return 1
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = (out_root or RUNS) / f"TPLRUN_{ts}"
    results = []
    for n in targets:
        tpl = apply_sets(idx[n], sets)      # 隨時可改:覆寫本次,不回寫冊
        od = run_dir / n
        od.mkdir(parents=True, exist_ok=True)
        fn = RENDERERS.get(tpl["kind"])
        if fn is None:
            results.append((n, "SKIP", f"kind 未支援 {tpl['kind']}"))
            continue
        try:
            state, note = fn(tpl, od)
        except Exception as exc:
            state, note = "FAIL", str(exc)[:120]
        results.append((n, state, note))
        print(f"  [{state}] {n:<22} {note}")
        if save_as and state == "OK" and len(targets) == 1:
            newt = copy.deepcopy(tpl)
            newt["name"] = save_as
            newt["saved_from"] = n
            reg["templates"].append(newt)   # append-only 另存
            reg.setdefault("changelog", []).append(
                {"ts": ts[:8], "op": "SAVE_AS", "note": f"{n} --set 覆寫後另存 {save_as}"})
            rp.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  [存] 模板另存 {save_as} → {rp.name}(append-only)")
    n_ok = sum(1 for _, s, _ in results if s == "OK")
    n_fail = sum(1 for _, s, _ in results if s == "FAIL")
    (run_dir / "run.json").write_text(json.dumps(
        {"schema": "vap.tplrun.v1", "ts": ts, "sets": sets,
         "results": [{"name": a, "state": b, "note": c} for a, b, c in results]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [計] 模板 {len(results)} · OK {n_ok} · FAIL {n_fail} · 存 {run_dir}")
    return 1 if n_fail else 0


def cmd_list() -> int:
    reg, rp = load_registry()
    print(f"=== VAP 模板冊 {rp.name} · {len(reg['templates'])} 模板(渲染即重讀資料=自動更新)===")
    for t in reg["templates"]:
        print(f"  {t['name']:<22} [{t['kind']:<10}] {t.get('zh', '')} · 圖規 {t.get('chart_ref', '')}")
    print("  用法:--render <名|all> [--set params.k=v ...] [--save-as 新名]")
    return 0


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    reg, rp = load_registry()
    # ① 冊在位:schema+append-only 政策+六種子
    chk("① 模板冊(schema+append-only+6 種子)",
        reg["schema"] == "vap-template-registry-v1" and "append-only" in reg["policy"]
        and len(reg["templates"]) >= 6)
    kinds = {t["kind"] for t in reg["templates"]}
    chk("② 六 kind 齊(dual/stack/panels/corrheat/ta_overlay/map)",
        {"dual", "stack", "panels", "corrheat", "ta_overlay", "map"} <= kinds)
    # ③ --set dot 覆寫(不動原冊)
    t0 = next(t for t in reg["templates"] if t["name"] == "twii_gspc_dual")
    t1 = apply_sets(t0, ["params.left=SOX", "params.lookback=100"])
    chk("③ --set 覆寫(left=SOX·原冊不動)",
        t1["params"]["left"] == "SOX" and t1["params"]["lookback"] == 100
        and t0["params"]["left"] == "TWII")
    with tempfile.TemporaryDirectory() as td:
        sand = Path(td)
        # ④ dual 渲染(ENG001 複用)
        rc = render(["twii_gspc_dual"], [], None, out_root=sand / "r4")
        pages = list((sand / "r4").rglob("*.html"))
        chk("④ dual 渲染(ENG001 SVG 頁)", rc == 0 and len(pages) >= 1)
        # ⑤ stack+panels 渲染
        rc = render(["unemp_duration_stack", "rates_panels"], [], None, out_root=sand / "r5")
        chk("⑤ stack+panels 渲染", rc == 0
            and len(list((sand / "r5").rglob("*.html"))) >= 2)
        # ⑥ corrheat(seaborn diverging·值域)
        rc = render(["macro_corrheat"], [], None, out_root=sand / "r6")
        pngs = list((sand / "r6").rglob("*.png"))
        chk("⑥ 相關熱力圖 png", rc == 0 and pngs and pngs[0].stat().st_size > 10000)
        # ⑦ ta_overlay(ENG004 SMA 週期輪)
        rc = render(["twii_ta_overlay"], [], None, out_root=sand / "r7")
        pngs = list((sand / "r7").rglob("*.png"))
        chk("⑦ TA 疊圖 png(ENG004 家族)", rc == 0 and pngs and pngs[0].stat().st_size > 10000)
        # ⑧ map(leaflet 標記數)
        rc = render(["world_indices_map"], [], None, out_root=sand / "r8")
        hts = list((sand / "r8").rglob("*.html"))
        ok8 = rc == 0 and hts
        if ok8:
            h = hts[0].read_text(encoding="utf-8")
            ok8 = "leaflet" in h and h.count('"label"') >= 6
        chk("⑧ 地圖×數據(leaflet+≥6 標記)", bool(ok8))
        # ⑨ 自動更新=渲染即重讀(資料檔換新→圖值換新)
        import pandas as pd
        alt = sand / "alt.json"
        alt.write_text(json.dumps(
            [{"date": f"2026-01-{d:02d}", "TWII": 100.0 + d, "GSPC": 200.0 + d}
             for d in range(1, 21)]), encoding="utf-8")
        t9 = apply_sets(t0, [f"data.path={json.dumps(str(alt))}"])
        df9 = load_frame(t9)
        chk("⑨ 渲染即重讀(換資料檔=取新值)",
            abs(float(df9["TWII"].iloc[-1]) - 120.0) < 1e-9 and len(df9) == 20)
        # ⑩ --save-as append-only(沙盒冊副本;原冊零觸碰)
        regcopy = sand / "VAP_Template_Registry_v0100.json"
        regcopy.write_text(rp.read_text(encoding="utf-8-sig"), encoding="utf-8")
        rc = render(["macro_corrheat"], ["params.lookback=60"], "corrheat_60d",
                    reg_path=regcopy, out_root=sand / "r10")
        reg2, _ = load_registry(regcopy)
        saved = next((t for t in reg2["templates"] if t["name"] == "corrheat_60d"), None)
        reg_now, _ = load_registry()
        chk("⑩ --save-as 另存(沙盒冊+1·params 帶覆寫·正冊不動)",
            rc == 0 and saved is not None and saved["params"]["lookback"] == 60
            and saved["saved_from"] == "macro_corrheat"
            and len(reg_now["templates"]) == len(reg["templates"]))
    n = 10 - len(fails)
    print(f"  [計] 十檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== VAP ENG005 模板跑器 · 十檢自測(在庫資料零網路)===")
        return selftest()
    if "--list" in args or not args:
        return cmd_list()
    names, sets, save_as = [], [], None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--render" and i + 1 < len(args):
            names = [x for x in args[i + 1].split(",") if x]
            i += 2
        elif a == "--set" and i + 1 < len(args):
            sets.append(args[i + 1])
            i += 2
        elif a == "--save-as" and i + 1 < len(args):
            save_as = args[i + 1]
            i += 2
        else:
            i += 1
    if not names:
        return cmd_list()
    print(f"=== VAP 模板渲染(批123)· {','.join(names)} · 覆寫 {len(sets)} 項 ===")
    return render(names, sets, save_as)


if __name__ == "__main__":
    sys.exit(main())
