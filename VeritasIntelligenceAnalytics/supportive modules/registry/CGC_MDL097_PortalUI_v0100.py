#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL097_PortalUI — 使用者介面總入口 Portal(批222;操作員令)
====================================================================
操作員令:「一個 PowerShell 啟動,包含使用者介面的連結,完整的使用
介面初步版」→ 單一入口頁 VIA_UI_Portal_v0100.html:
  ①核心操作四頁卡(指揮台橋接版/同步狀態台=完成度儀表+擷取按鍵/
    樞紐/治理矩陣)——橋偵測:橋在=指揮台走 127.0.0.1:8765(按下
    直跑),無橋=誠實提示雙擊 VIA 啟橋+file 版連結後備
  ②分析頁卡(儀表板/晨報/系統五分頁/VAP 主控/SysMan)
  ③現役 UI 全冊(VIA_UI_* 尾版動態列表:名/大小/更新時間)
  連結=同夾相對路徑(RAW HTML 零依賴);零 CDN;10.5px 小字專業;
  auto-fit 自適應一頁。VIA.ps1 一鍵開此頁=一個 PowerShell 到全介面。
用法:python3 CGC_MDL097_PortalUI_v0100.py [--open] | --selftest
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

import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
UIDIR = VIA / "supportive modules" / "ui_support"
OUT = UIDIR / "VIA_UI_Portal_v0100.html"

CORE = [
    ("🎛️ 指揮台(按下直跑)", "VIA_UI_CommandDeck_v0100.html",
     "六任務卡+個股全景+RYG 矩陣;橋接中自動改走 127.0.0.1:8765"),
    ("📈 同步狀態台+完成度儀表", "VIA_UI_SyncStatus_v0100.html",
     "⓪ 完成度 DASHBOARD+擷取資料庫按鍵+接續完成方法+六矩陣"),
    ("🗂️ 系統樞紐(左面板母頁)", "VIA_UI_SystemHub_v0100.html",
     "五子系統導覽+開機⑨步+批次收官記錄"),
    ("🟩 治理矩陣(四分區七矩陣)", "VIA_UI_GovernanceMatrix_v0100.html",
     "沙盒綠燈率+Hydra 凍結+黃燈明細+VSM 六燈"),
]
ANALYSIS = [
    ("📊 儀表板(因子列)", "VIA_UI_Dashboard_v0100.html"),
    ("🌅 晨報 DailyBrief", "VIA_UI_DailyBrief_v0100.html"),
    ("🧪 系統五分頁", "VIA_UI_SystemTestPages_v0100.html"),
    ("🖥️ 系統主控台", "VIA_UI_SystemConsole_v0100.html"),
    ("📉 VAP 圖表主控", "VIA_UI_VAPConsole_v0100.html"),
    ("🗄️ 資料庫目錄+擷取細則", "VIA_UI_DataCatalog_v0100.html"),
    ("🌍 全球市場觀測(11 類)", "VIA_UI_GlobalMarkets_v0100.html"),
    ("📑 券商報告卡(結構化庫)", "VIA_UI_ReportCards_v0100.html"),
]


def _latest_pages() -> list[dict]:
    """現役 VIA_UI_* 尾版動態列表(同名多版=取尾版;嚴禁寫死版號)"""
    best: dict[str, Path] = {}
    for p in sorted(UIDIR.glob("VIA_UI_*.html")):
        stem = p.stem.rsplit("_v", 1)[0]
        best[stem] = p   # sorted=尾版覆蓋前版
    rows = []
    for stem, p in sorted(best.items()):
        st = p.stat()
        rows.append({"f": p.name, "kb": round(st.st_size / 1024, 1),
                     "ts": datetime.fromtimestamp(st.st_mtime)
                     .strftime("%m-%d %H:%M")})
    return rows


def render() -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    core = "".join(
        f"<a class='card' data-deck='{1 if 'CommandDeck' in f else 0}' "
        f"href='{f}'><b>{t}</b><span>{d}</span></a>"
        for t, f, d in CORE)
    ana = "".join(f"<a class='card sm' href='{f}'><b>{t}</b></a>"
                  for t, f in ANALYSIS)
    allp = "".join(
        f"<tr><td><a href='{r['f']}'>{r['f']}</a></td>"
        f"<td>{r['kb']}</td><td>{r['ts']}</td></tr>"
        for r in _latest_pages())
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA Portal · 使用者介面總入口</title>
<style>
:root{{--bg:#0b1220;--card:#111a2e;--line:#1e2a44;--tx:#c7d3e8;--dim:#7e8db0;
--ac:#4f8ef7}}
*{{box-sizing:border-box;margin:0}}
body{{background:var(--bg);color:var(--tx);font:10.5px/1.5 "Segoe UI",
"Noto Sans TC",sans-serif;padding:16px;max-width:1180px;margin:0 auto}}
h1{{font-size:15px;color:#e8eefb}}
.sub{{color:var(--dim);font-size:10px;margin:3px 0 12px}}
h2{{font-size:11.5px;color:var(--ac);margin:14px 0 6px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));
gap:8px}}
.card{{display:flex;flex-direction:column;gap:3px;background:var(--card);
border:1px solid var(--line);border-radius:8px;padding:10px 12px;
text-decoration:none;color:var(--tx)}}
.card:hover{{border-color:var(--ac)}}
.card b{{font-size:11.5px;color:#e8eefb}}
.card span{{color:var(--dim);font-size:9.5px}}
.card.sm{{padding:8px 12px}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;color:var(--dim);font-size:9.5px;
border-bottom:1px solid var(--line);padding:2px 6px 3px 0}}
td{{padding:2px 6px;border-bottom:1px dashed var(--line);
overflow-wrap:anywhere}}
td a{{color:var(--tx)}}
#lamp{{font-size:10px}}
</style></head><body>
<h1>VIA 使用者介面總入口(初步版)</h1>
<div class="sub">{ts} · 一個 PowerShell(雙擊 VIA)→本頁→全介面 ·
<span id="lamp">⏳ 橋偵測中…</span> · RAW HTML 零 CDN · 尾版動態列表</div>
<h2>① 核心操作</h2><div class="grid">{core}</div>
<h2>② 分析頁</h2><div class="grid">{ana}</div>
<h2>③ 現役 UI 全冊(VIA_UI_* 尾版)</h2>
<table><thead><tr><th>頁</th><th>KB</th><th>更新</th></tr></thead>
<tbody>{allp}</tbody></table>
<script>
/* 橋偵測:橋在=指揮台卡改走 127.0.0.1:8765(按下直跑版);
   無橋=誠實提示(file 版連結後備仍可看) */
fetch("http://127.0.0.1:8765/ping").then(r => r.json()).then(j => {{
  if (j && j.via === "deck-bridge") {{
    document.getElementById("lamp").textContent = "🟢 橋接中(指揮台=直跑版)";
    document.querySelectorAll("[data-deck='1']").forEach(
      a => a.href = "http://127.0.0.1:8765/");
  }}
}}).catch(() => {{
  document.getElementById("lamp").textContent =
    "⚪ 無橋(雙擊 VIA 啟橋;連結仍可瀏覽)";
}});
</script>
</body></html>"""


def run(open_after: bool = False) -> int:
    OUT.write_text(render(), encoding="utf-8")
    print(f"[UI] {OUT.name} · 總入口(核心 4+分析 5+全冊尾版動態)")
    if open_after:
        try:
            import webbrowser
            webbrowser.open(OUT.as_uri())
        except Exception:
            pass
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    rc = run()
    page = OUT.read_text(encoding="utf-8")
    chk("① 三區在頁(核心操作/分析頁/現役全冊)", rc == 0 and
        all(k in page for k in ("① 核心操作", "② 分析頁", "③ 現役 UI 全冊")))
    chk("② 核心四頁連結在位(指揮台/狀態台/樞紐/治理矩陣)",
        all(f in page for f in ("VIA_UI_CommandDeck_v0100.html",
                                "VIA_UI_SyncStatus_v0100.html",
                                "VIA_UI_SystemHub_v0100.html",
                                "VIA_UI_GovernanceMatrix_v0100.html")))
    chk("③ 全冊=尾版動態列表(嚴禁寫死版號;rsplit _v 取尾)",
        "_latest_pages" in src and "rsplit" in src
        and "<th>KB</th>" in page and "VIA_UI_Dashboard" in page)
    chk("④ 橋偵測誠實三態(🟢 直跑/⚪ 無橋提示;file 後備連結不失能)",
        "deck-bridge" in page and "無橋(雙擊 VIA 啟橋" in page)
    chk("⑤ 相對連結零依賴(同夾 href;無絕對本機路徑)",
        "C:\\\\" not in page and "file://" not in page)
    chk("⑥ 小字專業排版(10.5px+auto-fit+anywhere)",
        all(k in page for k in ("10.5px", "auto-fit", "anywhere")))
    chk("⑦ 零 CDN 零外鏈(無外部資源引用;唯一外呼=127.0.0.1 橋偵測)",
        all(k not in page for k in ('src="http', 'href="https', "@import")))
    chk("⑧ 零網路引擎+加速橋(生成純本地;無 http 庫)",
        all(("import " + k) not in src for k in ("requests", "httpx"))
        and "ACCEL-BRIDGE" in src)
    print(f"  [計] 八檢 OK {8 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 使用者介面總入口(CGC_MDL097)· 八檢自測(零網路)===")
        return selftest()
    return run(open_after="--open" in args)


if __name__ == "__main__":
    sys.exit(main())
