#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""Offline evidence matrix; no command-execution HTTP server. [VIA:ACCEL-BRIDGE]"""
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

MAX_VISIBLE_ROWS = 600

import collections
import json
import re
from pathlib import Path

UI_BOOK_GLOB = "VIA_UI_Template_SSOT_v*.json"
# 本頁用到的鎖定 token(名稱取自 VIA_UI_Template_SSOT 尾版的 tokens 節;值一律讀冊,本檔不放任何顏色 / 字體值)。
UI_TOKEN_NAMES = ("bg", "panel", "line", "txt", "dim", "acc", "head", "head-txt", "zebra", "chip", "seal", "font", "fs",
                  "fs-title", "fs-h", "fs-note", "lh", "w-bold", "radius", "lamp-green", "lamp-yellow", "lamp-red", "lamp-gray")
_SAFE_TOKEN = re.compile(r"[#\w\s\",.()%\-]{1,200}")


def load_ui_tokens(registry=None):
    """讀視覺鎖定冊(registry 的 VIA_UI_Template_SSOT 尾版)→ (tokens, 冊名)。冊不在或讀不到 → ({}, None):頁面不上色、照實標 ABSENT。"""
    folder = Path(registry) if registry else Path(__file__).resolve().parents[2] / "registry"
    def vnum(q):
        m = re.search(r"_v(\d+)\.json$", q.name)
        return int(m.group(1)) if m else -1
    try:
        book = max(folder.glob(UI_BOOK_GLOB), key=vnum)
        tokens = json.loads(book.read_text(encoding="utf-8")).get("tokens") or {}
    except (ValueError, OSError):
        return {}, None
    picked = {k: str(tokens[k]) for k in UI_TOKEN_NAMES if isinstance(tokens.get(k), str) and _SAFE_TOKEN.fullmatch(str(tokens[k]))}
    return picked, book.name


def root_css(tokens):
    return ":root{" + ";".join(f"--{k}:{v}" for k, v in tokens.items()) + "}" if tokens else ""


def matrices(snapshot, tools, round_number, delta=None):
    errors, hydra, comparison = [], [], []
    for row in snapshot["files"]:
        if row["status"] == "ERROR":
            errors.append({"root": row["root_id"], "path": row["path"], "error": row.get("error"), "line": row.get("error_line"), "decision": "SOURCE_REVIEW_ONLY"})
        for issue in row.get("issues", []):
            target = hydra if issue["kind"] in ("DUPLICATE_DEFINITION", "DYNAMIC_EXECUTION") else errors
            target.append({"root": row["root_id"], "path": row["path"], **issue})
    errors.extend(snapshot["issues"])
    for name in sorted({r["system"] for r in snapshot["files"]}):
        rows = [r for r in snapshot["files"] if r["system"] == name]
        comparison.append({"system": name, "files": len(rows), "python_parsed": sum(r["status"] == "PARSED" for r in rows), "errors": sum(r["status"] == "ERROR" for r in rows), "runtime": "NOT_EXECUTED"})
    tool_rows = [{k: r[k] for k in ("id", "name", "status", "verb", "purpose", "next")} for r in tools]
    return [
        {"id": "M01", "name": "工具缺口", "rows": tool_rows},
        {"id": "M02", "name": "Error Matrix", "rows": errors},
        {"id": "M03", "name": "Optimization Matrix", "rows": [
            {"action": "reuse", "description": "既有 VCGC token / MCP / DuckDB / SkillExport 沿用", "status": "SOURCE_CONFIRMED_HOST_PENDING"},
            {"action": "context", "description": "AST 短卡 + 字元預算 + 檔案雜湊", "status": "IMPLEMENTED"},
            {"action": "cache", "description": "每輪重新讀取雜湊；內容未變沿用解析結果", "hits": snapshot["quantity"]["cache_hits"]}]},
        {"id": "M04", "name": "Hydra Risk Matrix", "rows": hydra},
        {"id": "M05", "name": "Dependency Matrix", "rows": snapshot["edges"]},
        {"id": "M06", "name": "Fix Order Matrix", "rows": [
            {"order": 1, "class": "PARALLEL_FIXABLE", "action": "唯讀來源盤點、契約、重複 ID 檢查", "state": "COMPLETED_FOR_SELECTED_INPUTS"},
            {"order": 2, "class": "SEQUENCE_DEPENDENT", "action": "鎖版 → 註冊提案 → 中央編號 → 原生 manager 測試", "state": "HOST_PENDING"},
            {"order": 3, "class": "MULTI_SUBSYSTEM", "action": "VRN-1 / VRN-2 / VDF / VAP 只讀收據，各自驗證", "state": "NOT_EXECUTED"}]},
        {"id": "M07", "name": "Quantity Validation", "rows": [{**snapshot["quantity"], "round": round_number, "changed_files": (delta or {}).get("count"), "ast_scope": "Python only"}]},
        {"id": "M08", "name": "SSOT Comparison", "rows": [{"proposal_id": t["id"], "central_ssot_id": "PENDING", "decision": "PRESERVE_NATIVE_NUMBERS", "evidence": t["evidence"]} for t in tools]},
        {"id": "M09", "name": "Multi-System Comparison", "rows": comparison},
    ]


def render(snapshot, tools, round_number, delta=None):
    all_matrices = matrices(snapshot, tools, round_number, delta)
    payload = {"round": round_number, "status": snapshot["status"], "quantity": snapshot["quantity"],
               "fingerprint": snapshot["input_fingerprint"], "matrices": [dict(m, total=len(m["rows"]), rows=m["rows"][:MAX_VISIBLE_ROWS]) for m in all_matrices]}
    serialized = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    tokens, book = load_ui_tokens()
    return (TEMPLATE.replace("__TOKENS__", root_css(tokens)).replace("__UIBOOK__", book or "ABSENT")
            .replace("__PAYLOAD__", serialized))


TEMPLATE = '''<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="via-ui-tokens" content="__UIBOOK__">
<title>VCGC · Tool Modules · Evidence Matrix</title>
<style>
__TOKENS__
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font-family:var(--font);font-size:var(--fs);line-height:var(--lh)}header{display:flex;gap:18px;align-items:center;padding:24px 3%;background:var(--head);color:var(--head-txt);border-bottom:1px solid var(--line)}.logo{border:1px solid var(--seal);color:var(--seal);font-size:38px;padding:3px 14px}h1{font-size:var(--fs-title);margin:0;letter-spacing:2px}header p{margin:3px 0;color:var(--dim)}main{padding:22px 3%}.eyebrow{font-size:var(--fs-note);color:var(--seal);letter-spacing:2px}.notice{padding:12px 15px;border-left:3px solid var(--lamp-yellow);background:var(--chip);margin-bottom:18px}.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:18px 0}.stat{padding:15px;background:var(--panel);border:1px solid var(--line);border-radius:var(--radius)}.stat strong{display:block;font-size:28px;font-weight:var(--w-bold);color:var(--acc)}.stat span{color:var(--dim)}nav{display:flex;flex-wrap:wrap;gap:7px;margin:20px 0}button,input{font:inherit;border:1px solid var(--line);border-radius:var(--radius);color:var(--txt);background:var(--panel);padding:8px 11px}button{cursor:pointer}button.active,button:hover{border-color:var(--acc);font-weight:var(--w-bold)}input{width:min(420px,100%)}.toolbar{display:flex;gap:12px;flex-wrap:wrap;align-items:center;justify-content:space-between}.tablewrap{overflow:auto;max-height:65vh;border:1px solid var(--line);border-radius:var(--radius);margin-top:13px}table{border-collapse:collapse;width:100%;min-width:750px;background:var(--panel)}th{position:sticky;top:0;text-align:left;background:var(--head);color:var(--head-txt);font-weight:var(--w-bold)}td,th{padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top}td{overflow-wrap:anywhere;max-width:440px}tr:hover td{background:var(--zebra)}.red::before,.yellow::before,.green::before{content:"\\25CF\\00A0"}.red::before{color:var(--lamp-red)}.yellow::before{color:var(--lamp-yellow)}.green::before{color:var(--lamp-green)}.muted{color:var(--dim)}footer{color:var(--dim);font-size:var(--fs-note);margin-top:14px;overflow-wrap:anywhere}h2{font-size:var(--fs-h);font-weight:var(--w-bold);margin:0}button:focus-visible,input:focus-visible{outline:2px solid var(--acc);outline-offset:3px}@media(max-width:650px){header{padding:18px 4%}h1{letter-spacing:1px}.stats{grid-template-columns:repeat(2,1fr)}main{padding:17px 4%}.stat strong{font-size:24px}}
</style></head><body><header><div class="logo" aria-label="理">理</div><div><h1>VERITAS INTELLIGENCE ANALYTICS</h1><p class="eyebrow">VCGC · MODULAR TOOL GOVERNANCE</p><p>AST 分類 · 穩定編號 · 動詞短卡 · 來源證據</p></div></header>
<main><div class="notice"><strong id="lamp"></strong> · 已選來源靜態檢查。主機啟用、中央發號及外部工具接通均需實機收據。此頁可篩選與查看證據，沒有執行系統命令的按鈕。</div>
<div class="stats" id="stats"></div><nav id="tabs" aria-label="矩陣選擇"></nav><div class="toolbar"><h2 id="title"></h2><input id="search" aria-label="搜尋矩陣" placeholder="輸入工具、編號、功能或狀態…"><button id="download">下載本頁證據 JSON</button></div><p class="muted" id="count"></p><div class="tablewrap"><table><thead id="thead"></thead><tbody id="tbody"></tbody></table></div><footer id="foot"></footer></main>
<script id="data" type="application/json">__PAYLOAD__</script><script>
'use strict';const state=JSON.parse(document.getElementById('data').textContent);let current=0;
const text=v=>v==null?'—':typeof v==='object'?JSON.stringify(v):String(v);
const cell=(tag,v)=>{const e=document.createElement(tag);e.textContent=text(v);return e};
document.getElementById('lamp').textContent='YELLOW · 第 '+state.round+' 輪 · 正式接入待驗';document.getElementById('lamp').className='yellow';
if(state.status==='RED'){document.getElementById('lamp').textContent='RED · 靜態檢查發現阻擋項';document.getElementById('lamp').className='red'}
[['來源檔案',state.quantity.recorded],['Python 已解析',state.quantity.parsed],['AST 節點',state.quantity.nodes],['錯誤 / 未讀取',state.quantity.errors]].forEach(([label,value])=>{const d=document.createElement('div');d.className='stat';d.append(cell('strong',value),cell('span',label));document.getElementById('stats').append(d)});
state.matrices.forEach((m,i)=>{const b=cell('button',m.id+' '+m.name);b.addEventListener('click',()=>{current=i;document.getElementById('search').value='';draw()});document.getElementById('tabs').append(b)});
function draw(){const m=state.matrices[current],q=document.getElementById('search').value.toLowerCase();const rows=m.rows.filter(r=>JSON.stringify(r).toLowerCase().includes(q));document.getElementById('title').textContent=m.name;document.querySelectorAll('#tabs button').forEach((b,i)=>{b.classList.toggle('active',i===current);b.setAttribute('aria-pressed',String(i===current))});const cols=[...new Set(m.rows.flatMap(r=>Object.keys(r)))];const head=document.getElementById('thead'),body=document.getElementById('tbody');head.replaceChildren();body.replaceChildren();const hr=document.createElement('tr');cols.forEach(c=>hr.append(cell('th',c)));head.append(hr);rows.forEach(r=>{const tr=document.createElement('tr');cols.forEach(c=>tr.append(cell('td',r[c])));body.append(tr)});if(!rows.length){const tr=document.createElement('tr'),td=cell('td','目前沒有符合項目；空表不代表未執行項目已通過。');td.colSpan=Math.max(cols.length,1);tr.append(td);body.append(tr)}document.getElementById('count').textContent='篩選 '+rows.length+' ／ 本頁 '+m.rows.length+' ／ 完整 '+m.total+' 筆。完整 AST 與矩陣保存在同輪 JSON。';document.getElementById('foot').textContent='INPUT SHA256 · '+state.fingerprint+' · 顯示的是實際來源檢查資料，不包含推估 Token 節省率。'}
document.getElementById('search').addEventListener('input',draw);document.getElementById('download').addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(state,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='VCGC_Matrix_Evidence.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)});draw();
</script></body></html>'''
