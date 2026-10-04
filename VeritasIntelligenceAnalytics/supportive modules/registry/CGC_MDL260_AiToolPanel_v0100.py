# -*- coding: utf-8 -*-
"""CGC_MDL260 AiToolPanel v0100 — AI 支援工具統一登記冊 + HTML 管理面板 + AI 引導卡。
三動詞 (只讀工具本體, 只寫自家冊與報告):
  guide : 印給 AI 的引導卡 (後來的 AI 先讀這張, 知道有哪些工具、怎麼呼叫、走什麼閘)。
  html  : 掃註冊冊 + VCGC 鎖冊 -> VIA_Reports/aiverb/AI_Tools_Panel.html 統一呈現 (預設動詞)。
  check : 對每支已登記 py 工具跑 --selftest (看門狗限時) -> 活體燈寫回面板狀態。
登記冊 VIA_AiTools_Registry_v0100.json: 只增合併 (既有列不刪, 同 id 以新資訊補欄)。
自適應模板: 同目錄放 VIA_AiTools_Panel_TEMPLATE.html 即自動套用 (佔位: {{NOW}} {{ROWS}}
{{LOCKS}} {{GUIDE}} {{TOOLS_JSON}}); 缺佔位不炸, 模板沒到位用內建 Visual-Lock 版。
用法: python CGC_MDL260_AiToolPanel_v0100.py [guide|html|check] [--no-open]
自測: python CGC_MDL260_AiToolPanel_v0100.py --selftest
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

import html as html_mod
import json
import os
import subprocess
import sys
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = Path(os.environ.get("VIA_ROOT", HERE.parent.parent))
REGISTRY_BOOK = HERE / "VIA_AiTools_Registry_v0100.json"
LOCK_BOOK = HERE / "VIA_ToolVersion_Lock_v0100.json"
OUT_DIR_DEFAULT = VIA / "VIA_Reports" / "aiverb"
TEMPLATE_FILE = HERE / "VIA_AiTools_Panel_TEMPLATE.html"
CHECK_SEC = 120

# 內建種子: VCO 家族 (首次建冊用; 之後以冊為準, 只增)
SEED = [
    {"id": "CGC_MDL257", "name": "AiVerbLadder", "category": "VCO·梯次",
     "file": "supportive modules/registry/CGC_MDL257_AiVerbLadder_v0100.py",
     "usage": "python <檔> <引擎.py> step|status|reset [--userok 備註] [--approve]",
     "note": "13 段一步一閘 (TEST/DEBUG/OPTIMIZE/CONSOLIDATE/USER-TEST/ACTIVATE); 人工兩閘不可代按"},
    {"id": "CGC_MDL258", "name": "TempAccel", "category": "VCO·加速器",
     "file": "supportive modules/registry/CGC_MDL258_TempAccel_v0100.py",
     "usage": "TempAccel(chunk_rows=...).feed/flush/reduce; CLI: --selftest | stats",
     "note": "TEMP 換記憶體 (純 stdlib); 梯次完訓 sha256=320f52946ead4eb6"},
    {"id": "CGC_MDL259", "name": "AiVerbBridge", "category": "VCO·動詞橋",
     "file": "supportive modules/registry/CGC_MDL259_AiVerbBridge_v0100.py",
     "usage": "python <檔> classify|paste|lesson|round ... (經 Invoke-VIA-AiVerb-v0108.ps1)",
     "note": "原 MDL256, 與 SubsystemBundle 撞號改 259 (重號 0 律)"},
    {"id": "PS-AIVERB", "name": "Invoke-VIA-AiVerb", "category": "VCO·通道",
     "file": "Invoke-VIA-AiVerb-v0108.ps1",
     "usage": "pwsh -File <檔> -Ladder <引擎.py> [-UserOk 備註] [-Approve] [-LadderStatus]",
     "note": "base64 argv + daemon 看門狗; $Args 自動變數蟲已修"},
]


def _load_registry() -> dict:
    """讀登記冊; 不在就以種子建冊 (只增, 永不刪列)。"""
    if REGISTRY_BOOK.exists():
        try:
            return json.loads(REGISTRY_BOOK.read_text(encoding="utf-8"))
        except ValueError as exc:
            return {"version": "0100", "tools": SEED, "rebuilt": str(exc)}
    return {"version": "0100", "generated": dt.datetime.now().isoformat(), "tools": list(SEED)}


def _save_registry(book: dict) -> None:
    """落冊 (原子寫)。"""
    tmp = REGISTRY_BOOK.with_suffix(".tmp")
    tmp.write_text(json.dumps(book, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, REGISTRY_BOOK)


def register(entry: dict) -> dict:
    """只增登記: 同 id 補欄不刪列, 新 id 追加。"""
    book = _load_registry()
    for row in book["tools"]:
        if row.get("id") == entry.get("id"):
            for key, value in entry.items():
                row.setdefault(key, value)
            _save_registry(book)
            return book
    book["tools"].append(entry)
    _save_registry(book)
    return book


def locked_tools() -> list:
    """VCGC 鎖冊六席 (token/nlp/加速器...) — 只讀列出, 版本以鎖冊為準。"""
    if not LOCK_BOOK.exists():
        return []
    try:
        data = json.loads(LOCK_BOOK.read_text(encoding="utf-8"))
    except ValueError:
        return []
    out = []
    for slot, info in data.items():
        if isinstance(info, dict) and "path" in info:
            out.append({"slot": slot, "path": info["path"],
                        "exists": (VIA.parent / info["path"]).exists() or (VIA / info["path"]).exists()
                        or Path(info["path"]).exists()})
    return out


def check_tools(book: dict) -> dict:
    """活體燈: 逐支 py 工具跑 --selftest (限時); PASS/FAIL/SKIP(非py或缺檔)。"""
    lamps = {}
    for row in book["tools"]:
        path = VIA / row["file"]
        if not path.exists() or path.suffix != ".py":
            lamps[row["id"]] = "SKIP"
            continue
        if path.resolve() == Path(__file__).resolve():
            lamps[row["id"]] = "SELF-SKIP"  # 防遞迴: 面板不自測自己 (套娃蟲)
            continue
        try:
            proc = subprocess.run([sys.executable, str(path), "--selftest"],
                                  capture_output=True, text=True, timeout=CHECK_SEC)
            lamps[row["id"]] = "PASS" if proc.returncode == 0 else "FAIL"
        except subprocess.TimeoutExpired:
            lamps[row["id"]] = "TIMEOUT"
    return lamps


def guide_text(book: dict) -> str:
    """AI 引導卡: 後來的 AI 先讀這張再動手。"""
    lines = ["[AI 支援工具引導卡 · VCO] 先讀冊再動手; 一步一閘; 人工閘不可代按",
             "  登記冊: supportive modules/registry/VIA_AiTools_Registry_v0100.json (只增)",
             "  統一面板: python CGC_MDL260_AiToolPanel_v0100.py html -> VIA_Reports/aiverb/AI_Tools_Panel.html"]
    for row in book["tools"]:
        lines.append("  %-12s %-14s %s" % (row["id"], row["name"], row["usage"]))
        lines.append("  %12s └ %s" % ("", row["note"]))
    lines.append("  省 Token 讀檔: 照 CLAUDE.md token 卡 (read/slice/digest/pack/chain/brief), 不整檔讀")
    lines.append("  引擎要改: 走梯次 (MDL257) 完訓; 置換上位走 promote 白名單+回滾; 啟用只記帳")
    return "\n".join(lines)


def render_html(book: dict, lamps: dict | None = None) -> str:
    """統一呈現: 登記冊 + 鎖冊 + 活體燈 (Visual-Lock 風)。"""
    lamps = lamps or {}
    esc = html_mod.escape

    def lamp(tool_id):
        value = lamps.get(tool_id, "—")
        color = {"PASS": "#5a9e6f", "FAIL": "#b5443a", "TIMEOUT": "#b5443a",
                 "SKIP": "#8a857c"}.get(value, "#8a857c")
        return "<span class='pill' style='background:%s'>%s</span>" % (color, esc(value))

    rows = "".join(
        "<tr><td class='mono'>%s</td><td>%s</td><td>%s</td><td class='mono'>%s</td>"
        "<td class='mono'>%s</td><td>%s</td><td>%s</td></tr>"
        % (esc(r["id"]), esc(r["name"]), esc(r["category"]), esc(r["file"]),
           esc(r["usage"]), esc(r["note"]), lamp(r["id"])) for r in book["tools"])
    locks = "".join(
        "<tr><td class='mono'>%s</td><td class='mono'>%s</td><td>%s</td></tr>"
        % (esc(t["slot"]), esc(t["path"]),
           "<span class='pill' style='background:%s'>%s</span>"
           % (("#5a9e6f", "在") if t["exists"] else ("#b5443a", "缺"))) for t in locked_tools())
    data_json = json.dumps({"tools": book["tools"], "lamps": lamps,
                            "locks": locked_tools()}, ensure_ascii=False)
    if TEMPLATE_FILE.exists():  # 自適應: 模板到位自動吻合
        page = TEMPLATE_FILE.read_text(encoding="utf-8")
        for key, value in (("{{NOW}}", dt.datetime.now().strftime("%Y/%m/%d %H:%M")),
                           ("{{ROWS}}", rows), ("{{LOCKS}}", locks),
                           ("{{GUIDE}}", esc(guide_text(book))), ("{{TOOLS_JSON}}", data_json)):
            page = page.replace(key, value)
        return page
    return """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><title>AI Tools Panel</title><style>
:root{--bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--hair:#dbd9d3}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:"DM Sans","Microsoft JhengHei",sans-serif;padding:26px;max-width:1150px;margin:0 auto}
.mono{font-family:"DM Mono",monospace;font-size:11px}
h1{font-size:20px;display:flex;gap:12px;align-items:center}
.seal{background:#439a9a;color:#fff;width:40px;height:40px;border-radius:3px;display:inline-flex;align-items:center;justify-content:center;font-size:19px}
.sub{font-family:"DM Mono",monospace;font-size:11px;color:#8a877f;margin:4px 0 14px 52px}
.strip{height:4px;border-radius:2px;background:linear-gradient(90deg,#b5443a,#d08343,#c9a13a,#7ba86a,#4d8f63);margin-bottom:18px}
h2{font-size:12px;font-family:"DM Mono",monospace;letter-spacing:2px;color:#555;margin:20px 0 8px;text-transform:uppercase}
table{width:100%;border-collapse:collapse;background:var(--paper);border:1px solid var(--hair);font-size:12px}
th{font-family:"DM Mono",monospace;font-size:10px;text-align:left;padding:7px 9px;border-bottom:1px solid var(--hair);color:#666}
td{padding:6px 9px;border-bottom:1px solid var(--hair);vertical-align:top}tr:last-child td{border-bottom:none}
.pill{color:#fff;font-size:10px;font-family:"DM Mono",monospace;padding:2px 8px;border-radius:2px}
.card{background:var(--paper);border:1px solid var(--hair);border-left:5px solid #439a9a;border-radius:3px;padding:12px 16px;font-size:12px;line-height:1.8;margin-bottom:14px}
footer{margin-top:22px;font-size:10px;color:#999;font-family:"DM Mono",monospace;text-align:center}
</style></head><body>
<h1><span class="seal">具</span> AI 支援工具統一面板 — VeritasCodingOptimizer</h1>
<div class="sub">{{NOW}} · 登記冊只增 · 燈 = --selftest 活體 · 人工閘不可代按</div>
<div class="strip"></div>
<div class="card"><b>給後來 AI 的三句話</b>: ① 先讀登記冊再動手, 不整檔讀原始碼 (token 卡 read/slice);
② 引擎要改走梯次 (MDL257) 一步一閘完訓, USER-TEST/ACTIVATE 兩閘等人; ③ 置換上位只走 promote, 啟用只記帳。
指令: <span class="mono">python CGC_MDL260_AiToolPanel_v0100.py guide</span></div>
<h2>VCO 登記冊 (VIA_AiTools_Registry_v0100.json)</h2>
<table><tr><th>編號</th><th>名稱</th><th>類別</th><th>檔</th><th>用法</th><th>備註</th><th>燈</th></tr>{{ROWS}}</table>
<h2>VCGC 鎖冊工具席 (版本以鎖冊為準 · 換版走 via-vcgc tools activate)</h2>
<table><tr><th>席位</th><th>鎖定路徑</th><th>檔</th></tr>{{LOCKS}}</table>
<footer>CGC_MDL260_AiToolPanel v0100 · 只讀工具本體 · 只寫自家冊與報告 · 冊只增</footer>
</body></html>""".replace("{{NOW}}", dt.datetime.now().strftime("%Y/%m/%d %H:%M")) \
                 .replace("{{ROWS}}", rows).replace("{{LOCKS}}", locks)


def build_panel(do_check: bool = False, out_dir: Path | None = None) -> Path:
    """出面板 HTML (+ 狀態 json); do_check=True 加活體燈。"""
    book = _load_registry()
    _save_registry(book)  # 首次建冊落地
    lamps = check_tools(book) if do_check else {}
    out = out_dir or OUT_DIR_DEFAULT
    out.mkdir(parents=True, exist_ok=True)
    page = out / "AI_Tools_Panel.html"
    page.write_text(render_html(book, lamps), encoding="utf-8")
    (out / "AI_Tools_Panel_state.json").write_text(
        json.dumps({"ts": dt.datetime.now().isoformat(), "lamps": lamps,
                    "tools": [r["id"] for r in book["tools"]]}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return page


def selftest() -> int:
    """自測: 建冊/只增合併/引導卡/HTML/活體燈 (以自己當受測工具)。"""
    import tempfile
    global REGISTRY_BOOK
    passed = failed = 0

    def ck(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
            print("  [OK] %s" % name)
        else:
            failed += 1
            print("  [FAIL] %s" % name)

    keep = REGISTRY_BOOK
    box = Path(tempfile.mkdtemp())
    REGISTRY_BOOK = box / "VIA_AiTools_Registry_v0100.json"
    try:
        book = _load_registry()
        ck("① 種子建冊 4 席", len(book["tools"]) == 4)
        register({"id": "X-TEST", "name": "Stub", "category": "測試",
                  "file": "nope.py", "usage": "-", "note": "-"})
        register({"id": "X-TEST", "name": "Stub", "category": "測試",
                  "file": "nope.py", "usage": "-", "note": "改寫嘗試應不覆蓋"})
        book = _load_registry()
        ck("② 只增: 同 id 不重複列", sum(1 for r in book["tools"] if r["id"] == "X-TEST") == 1)
        ck("③ 只增: 既有欄不被覆蓋", [r for r in book["tools"] if r["id"] == "X-TEST"][0]["note"] == "-")
        text = guide_text(book)
        ck("④ 引導卡含梯次與閘語", "一步一閘" in text and "MDL257" in text)
        page = build_panel(do_check=False, out_dir=box / "reports")
        ck("⑤ 面板 HTML 落地", page.exists() and "AI 支援工具統一面板" in page.read_text(encoding="utf-8"))
        stub = box / "stub_tool.py"
        stub.write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
        lamps = check_tools({"tools": [
            {"id": "STUB", "file": os.path.relpath(stub, VIA)},
            {"id": "SELF", "file": os.path.relpath(__file__, VIA)}]})
        ck("⑥ 活體燈 + 防遞迴 (STUB=PASS, SELF=SELF-SKIP)",
           lamps.get("STUB") == "PASS" and lamps.get("SELF") == "SELF-SKIP")
        ck("⑦ 鎖冊讀取 graceful", isinstance(locked_tools(), list))
        global TEMPLATE_FILE
        keep_tpl = TEMPLATE_FILE
        TEMPLATE_FILE = box / "VIA_AiTools_Panel_TEMPLATE.html"
        TEMPLATE_FILE.write_text("<html><body><h1>自訂模板</h1>{{ROWS}}<pre>{{TOOLS_JSON}}</pre></body></html>",
                                 encoding="utf-8")
        page2 = build_panel(do_check=False, out_dir=box / "reports2")
        text2 = page2.read_text(encoding="utf-8")
        ck("⑧ 自適應模板自動吻合 (佔位換資料)", "自訂模板" in text2 and "CGC_MDL257" in text2 and "{{ROWS}}" not in text2)
        TEMPLATE_FILE = keep_tpl
    finally:
        REGISTRY_BOOK = keep
    print("[計] CGC_MDL260_AiToolPanel_v0100 自測 %d/%d · %s"
          % (passed, passed + failed, "PASS" if failed == 0 else "FAIL"))
    return 0 if failed == 0 else 1


def main() -> None:
    """CLI 入口。"""
    argv = sys.argv[1:]
    if "--selftest" in argv:
        sys.exit(selftest())
    verb = argv[0] if argv and not argv[0].startswith("-") else "html"
    if verb == "guide":
        print(guide_text(_load_registry()))
        return
    if verb == "check":
        page = build_panel(do_check=True)
        print("[面板] 活體燈完成 → %s" % page)
        return
    page = build_panel(do_check=False)
    print("[面板] 已產出 → %s (活體燈: 加 check)" % page)


if __name__ == "__main__":
    main()
