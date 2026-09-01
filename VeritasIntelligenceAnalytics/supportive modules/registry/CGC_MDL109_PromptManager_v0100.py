#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL109_PromptManager — Prompt 儲存管理(批265;操作員令)
====================================================================
操作員令:「Prompt Management 也是儲存功能之一」——中央治理主控台
左欄功能之一:提示詞冊(儲存/版本/取用)。
律(全承平台紀律):
  ①冊=VIA_PromptLibrary_v0100.json(append-only 只增不減零刪除)
  ②hash 定生死:同 id 同 sha256=SKIP_IDENTICAL 冪等;同 id 異 sha=
    新版遞增,舊版標 SUPERSEDED(本文保留=可回溯,不刪)
  ③新 id=version 1 ACTIVE
  ④UI=VIA_UI_PromptManager_v0100.html(手機單欄;逐冊展開+一鍵
    複製;零 CDN;Portal 尾版自收)
  ⑤空冊=誠實 0 筆候存件(不假種子)
用法:python3 CGC_MDL109_PromptManager_v0100.py run
      | add --id <id> --title <題> (--file <路徑> | --text <文>)
            [--tags a,b] [--lib <冊路徑>]
      | list | get <id> | --selftest
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

import hashlib
import html
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
LIB = HERE / "VIA_PromptLibrary_v0100.json"
OUT_UI = (VIA / "supportive modules" / "ui_support"
          / "VIA_UI_PromptManager_v0100.html")


def _load(lib: Path) -> dict:
    if lib.exists():
        return json.loads(lib.read_text(encoding="utf-8"))
    return {"schema": "prompt-library-v1", "prompts": []}


def _save(lib: Path, d: dict) -> None:
    lib.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                   encoding="utf-8")


def add(pid: str, title: str, text: str, tags: list[str],
        lib: Path = LIB) -> str:
    """hash 定生死:同 id 同 sha=SKIP;異 sha=新版+舊標 SUPERSEDED"""
    d = _load(lib)
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    same = [p for p in d["prompts"] if p["id"] == pid]
    if any(p["sha256"] == sha for p in same):
        return "SKIP_IDENTICAL"
    for p in same:
        if p["state"] == "ACTIVE":
            p["state"] = "SUPERSEDED"          # 本文保留=只增不減
    d["prompts"].append({
        "id": pid, "title": title, "version": len(same) + 1,
        "state": "ACTIVE", "tags": tags, "sha256": sha,
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "chars": len(text), "text": text})
    _save(lib, d)
    return f"ADDED_v{len(same) + 1}"


def render(lib: Path = LIB) -> str:
    d = _load(lib)
    by_id: dict = {}
    for p in d["prompts"]:
        by_id.setdefault(p["id"], []).append(p)
    cards = []
    for pid, vers in by_id.items():
        act = next((p for p in reversed(vers) if p["state"] == "ACTIVE"),
                   vers[-1])
        tags = " ".join(f'<span class="tag">{html.escape(t)}</span>'
                        for t in act.get("tags", []))
        cards.append(
            f'<details class="card"><summary><b>{html.escape(act["title"])}'
            f'</b> <code>{html.escape(pid)}</code> {tags}'
            f'<small>v{act["version"]} · {act["ts"]} · {act["chars"]} 字 · '
            f'歷史 {len(vers)} 版</small></summary>'
            f'<pre id="p_{html.escape(pid)}">{html.escape(act["text"])}</pre>'
            f'<button onclick="cp(\'p_{html.escape(pid)}\',this)">複製全文'
            "</button></details>")
    body = "".join(cards) if cards else \
        ('<p class="empty">冊內 0 筆=誠實空冊候存件。存入:<br>'
         "<code>via-prompt add --id 名 --title 題 --file 檔.txt</code>"
         "(或指揮台 prompts 任務)</p>")
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA Prompt 管理冊</title><style>
:root{{--bg:#f3f5f7;--panel:#fff;--line:#dce2e8;--text:#1f2933;
--muted:#6b7785;--blue:#4c78a8}}
@media (prefers-color-scheme: dark){{:root{{--bg:#10151b;--panel:#171e26;
--line:#2a333d;--text:#dbe3ea;--muted:#8a97a5;--blue:#7ba3cc}}}}
body{{background:var(--bg);color:var(--text);margin:0 auto;
font:13px/1.55 "Segoe UI","Noto Sans TC",sans-serif;padding:16px;
max-width:860px}}
h1{{font-size:16px}}.sub{{color:var(--muted);font-size:11px}}
.card{{background:var(--panel);border:1px solid var(--line);
border-radius:8px;margin:8px 0;padding:8px 12px}}
summary{{cursor:pointer}}summary small{{display:block;color:var(--muted)}}
code{{color:var(--blue);font-size:11px}}
.tag{{font-size:9px;background:var(--line);border-radius:999px;
padding:1px 7px;color:var(--muted)}}
pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:var(--bg);
border:1px solid var(--line);border-radius:6px;padding:10px;
font-size:11.5px;max-height:360px;overflow:auto}}
button{{border:1px solid var(--line);background:var(--panel);
color:var(--blue);border-radius:6px;padding:5px 14px;cursor:pointer}}
.empty{{color:var(--muted)}}</style></head><body>
<h1>Prompt 管理冊(批265)</h1>
<div class="sub">append-only 只增不減 · hash 定生死冪等 · 異文=新版+
舊標 SUPERSEDED 本文保留 · 冊={len(d["prompts"])} 筆 /
{len(by_id)} 個 id · {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
{body}
<script>
function cp(id,btn){{const t=document.getElementById(id).textContent;
navigator.clipboard.writeText(t).then(()=>{{btn.textContent="已複製 ✓";
setTimeout(()=>btn.textContent="複製全文",1500);}})
.catch(()=>{{btn.textContent="複製失敗(請手動選取)"}});}}
</script></body></html>"""


def run(lib: Path = LIB, ui: Path = OUT_UI) -> int:
    ui.write_text(render(lib), encoding="utf-8")
    d = _load(lib)
    print(f"[Prompt冊] {len(d['prompts'])} 筆 · {ui.name}")
    return 0


def _arg(args: list, key: str) -> str | None:
    return args[args.index(key) + 1] if key in args \
        and args.index(key) + 1 < len(args) else None


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as td:
        tlib = Path(td) / "lib.json"
        tui = Path(td) / "ui.html"
        r1 = add("t1", "測題", "本文A", ["tag1"], tlib)
        r2 = add("t1", "測題", "本文A", ["tag1"], tlib)
        chk("① 新增+hash 冪等(重複=SKIP_IDENTICAL)",
            r1 == "ADDED_v1" and r2 == "SKIP_IDENTICAL")
        r3 = add("t1", "測題", "本文B", [], tlib)
        d = _load(tlib)
        v1 = next(p for p in d["prompts"] if p["version"] == 1)
        chk("② 異文=新版+舊標 SUPERSEDED 本文保留(只增不減)",
            r3 == "ADDED_v2" and v1["state"] == "SUPERSEDED"
            and v1["text"] == "本文A" and len(d["prompts"]) == 2)
        run(tlib, tui)
        page = tui.read_text(encoding="utf-8")
        chk("③ UI 產出(最新版入卡+複製鍵+歷史版數)",
            "本文B" in page and "歷史 2 版" in page
            and "navigator.clipboard" in page)
        chk("④ 空冊誠實(0 筆訊息非假卡)",
            "誠實空冊候存件" in render(Path(td) / "none.json"))
        chk("⑤ 零 CDN+零網路", 'src="http' not in page
            and all(("import " + k) not in src
                    for k in ("requests", "httpx", "urllib")))
        chk("⑥ 正冊 append-only 紀律宣告+加速橋",
            "append-only" in src and "ACCEL-BRIDGE" in src)
    rc_real = run()                            # 正冊 UI 同步刷新
    chk("⑦ 正冊 UI 刷新 rc0", rc_real == 0)
    print(f"  [計] 七檢 OK {7 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== Prompt 儲存管理(CGC_MDL109)· 七檢自測(零網路)===")
        return selftest()
    lib = Path(_arg(a, "--lib")) if _arg(a, "--lib") else LIB
    if a and a[0] == "add":
        pid, title = _arg(a, "--id"), _arg(a, "--title")
        f, t = _arg(a, "--file"), _arg(a, "--text")
        if not (pid and title and (f or t)):
            print("[Prompt冊] 需 --id --title 與 --file 或 --text=誠實停")
            return 2
        text = Path(f).read_text(encoding="utf-8") if f else t
        tags = (_arg(a, "--tags") or "").split(",") if _arg(a, "--tags") \
            else []
        r = add(pid, title, text, [x for x in tags if x], lib)
        print(f"[Prompt冊] {pid} → {r}")
        return run(lib)
    if a and a[0] == "list":
        d = _load(lib)
        for p in d["prompts"]:
            print(f"  {p['id']} v{p['version']} [{p['state']}] "
                  f"{p['title']}({p['chars']} 字 · {p['ts']})")
        print(f"[Prompt冊] 共 {len(d['prompts'])} 筆")
        return 0
    if a and a[0] == "get":
        pid = a[1] if len(a) > 1 else ""
        d = _load(lib)
        hits = [p for p in d["prompts"]
                if p["id"] == pid and p["state"] == "ACTIVE"]
        if not hits:
            print(f"[Prompt冊] {pid} 無 ACTIVE 版=誠實空")
            return 2
        print(hits[-1]["text"])
        return 0
    return run(lib)


if __name__ == "__main__":
    sys.exit(main())
