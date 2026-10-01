#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_Panorama v0104 — 交接閘(AI STATE gate)· 工作流冊流程圖(Flow SSOT)(薄尾;前版 v0103 → v0102 → v0101 → 本體 v0100)

操作員(側線 2026-10-01):「每次 AI 接續進行之前動作都會漏且新舊版本亂掉,GitHub 紀錄難道無用,對話紀錄難道無用」
  「1 to 2 用適合的工具導入視覺化 plotly dashboard 顯示」
VIA 的「AI 狀態唯一事實來源」早就有了:docs/handoff/HANDOFF_latest.json(交接快照)+ 需求冊 + 工作流冊。缺的是「收尾沒寫也沒有燈」。
本版把它變成會亮燈的閘(只讀,不改任何冊):
  ① 交接閘:交接快照之後落後幾個提交 · 快照幾小時 · 這段期間改過的程式(.py/.ps1)有沒有被需求冊或工作流冊點名。
     紅 = 有程式沒登記 · 或落後 > 30 提交 · 或快照 > 48 小時又有新提交;黃 = 有落後;綠 = 快照之後沒有新提交。
     燈變化記成教訓(S:交接閘);每個 VCGC 動作那行 [監控] 提示直接帶上交接閘,下一個 AI 一進場就看到上一手漏了什麼。
  ② 工作流冊流程圖:networkx 建圖(驗無環 · 拓撲分層)+ Plotly 畫(本機免費;沒裝 Graphviz / Mermaid 也能畫):
     每條工作流一列、每一步一個節點;顏色 = 該步引擎在不在樹上 × 該工作流回指需求的最差狀態(COVERED/RECORDED 綠 · PARTIAL 黃 · MISSING 紅)。
  ③ 需求冊總表(Plotly 長條)· 交接待辦依狀態 · 建議指令(登需求冊 → handoff test → registry-sync → 編號 → SDD → handoff checkpoint)。
動詞:state(≤ 10 行卡)· 其餘同前版(watch / dashboard / sync / autostart / lessons / scan …)。
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

import contextlib
import fnmatch
import html as _html
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR_NAME = "VIA_Panorama_v0103.py"  # 釘名:前版;不自己取尾版
_spec = importlib.util.spec_from_file_location("VIA_Panorama_v0103", HERE / PRIOR_NAME)
V103 = importlib.util.module_from_spec(_spec)
sys.modules["VIA_Panorama_v0103"] = V103
_spec.loader.exec_module(V103)
V102, V101, BASE = V103.V102, V103.V101, V103.BASE
PRIOR = V103
globals().update({k: v for k, v in vars(V103).items() if not k.startswith("_") and k not in ("main", "selftest", "VERSION", "ENGINE", "HERE", "PRIOR", "PRIOR_NAME")})


def __getattr__(name: str):
    """PEP 562:本版沒有的名稱轉給前版 v0103(再往下 v0102 → v0101 → 本體 v0100)。"""
    try:
        return getattr(V103, name)
    except AttributeError:
        raise AttributeError(f"{__name__} 與前版都沒有 {name}") from None


VERSION = "v0104"
ENGINE = Path(__file__).stem
GATE = "state_gate_latest.json"
REQ_GLOB = "supportive modules/registry/VIA_Requirements_SSOT_v*.json"
WKF_GLOB = "supportive modules/registry/VIA_Workflow_VCGC_SSOT_v*.json"
HANDOFF = "docs/handoff/HANDOFF_latest.json"
CODE_EXT = (".py", ".ps1", ".psm1")
SKIP_PARTS = ("VIA_Reports", "VIA_NumberBooks", "tests", "__pycache__")
MAX_BEHIND, MAX_AGE_H = 30, 48
REQ_LAMP = {"COVERED": "GREEN", "RECORDED": "GREEN", "PARTIAL": "YELLOW", "MISSING": "RED"}


# ───────────────────────── 交接閘 ─────────────────────────

def _tail(root: Path, pattern: str) -> Path | None:
    hits = sorted(root.glob(pattern))
    return hits[-1] if hits else None


def _family(stem: str) -> str:
    return re.sub(r"[_-]v\d{3,4}$", "", stem)


def state_gate(root: Path) -> dict:
    """只讀:交接快照 × git × 需求冊 × 工作流冊。root = VIA 樹根(有 docs/handoff)。"""
    res = {"ts": BASE.now_utc(), "lamp": "ABSENT", "why": []}
    hp = root / HANDOFF
    try:
        ho = json.loads(hp.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        res["why"].append(f"交接快照讀不到:{type(e).__name__}")
        return res
    at = str(ho.get("at") or "")
    res.update(handoff_at=at, handoff_lamp=ho.get("lamp"), closeout=ho.get("closeout_lamp"),
               pending=[{"id": p.get("id"), "state": p.get("state"), "owner": p.get("owner"), "topic": p.get("topic"), "next": p.get("next")}
                        for p in ho.get("pending") or []])
    try:
        t_at = datetime.fromisoformat(at)
        res["age_h"] = round((datetime.now(timezone.utc) - t_at).total_seconds() / 3600, 1)
    except ValueError:
        res["why"].append("交接快照時間格式不對")
        res["age_h"] = None
    rc, out, _ = BASE.git(root, "log", f"--since={at}", "--name-only", "--format=@@%h|%cI|%s", "HEAD")
    commits, changed, cur = [], set(), None
    for ln in (out.splitlines() if rc == 0 else []):
        if ln.startswith("@@") and ln.count("|") >= 2:
            sha, cat, subj = ln[2:].split("|", 2)
            cur = {"sha": sha, "at": cat[:19], "subject": subj[:90], "files": []}
            commits.append(cur)
        elif ln.strip() and cur is not None:
            cur["files"].append(ln.strip())
    # 收尾記帳提交(只動交接冊 / 只增帳 .jsonl)不算落後:checkpoint 本身一定在快照時間之後提交
    real = [c for c in commits if any("docs/handoff/" not in f and not f.endswith(".jsonl") for f in c["files"])]
    for c in real:
        changed.update(c["files"])
    changed = sorted(changed)
    res["behind"] = len(real)
    res["bookkeeping"] = len(commits) - len(real)
    res["commits"] = [{k: c[k] for k in ("sha", "at", "subject")} for c in real[:40]]
    top = Path(BASE.git(root, "rev-parse", "--show-toplevel")[1].strip() or root)
    rel_root = os.path.relpath(root, top).replace("\\", "/")
    code = []
    for p in changed:
        rp = p[len(rel_root) + 1:] if rel_root not in (".", "") and p.startswith(rel_root + "/") else p
        if rp.endswith(CODE_EXT) and not any(s in rp.split("/") for s in SKIP_PARTS) and (root / rp).exists():
            code.append(rp)
    reqf, wkf = _tail(root, REQ_GLOB), _tail(root, WKF_GLOB)
    books = ""
    for f in (reqf, wkf):
        try:
            books += f.read_text(encoding="utf-8") if f else ""
        except OSError as e:
            res["why"].append(f"冊讀不到:{e}")
    fams = sorted({_family(Path(p).stem) for p in code})
    unreg = [f for f in fams if f not in books]
    res.update(changed_code=len(code), families=len(fams), unregistered=unreg, req_book=reqf.name if reqf else None,
               wkf_book=wkf.name if wkf else None)
    # 同步到 GitHub:本機有沒推上 origin 的提交(沒有上游 = 沒量,不假綠)
    rc_u, up, _ = BASE.git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if rc_u == 0 and up.strip():
        rc_c, cnt, _ = BASE.git(root, "rev-list", "--count", f"{up.strip()}..HEAD")
        res["unpushed"] = int(cnt.strip()) if rc_c == 0 and cnt.strip().isdigit() else None
        res["upstream"] = up.strip()
    else:
        res["unpushed"], res["upstream"] = None, None
    try:
        rq = json.loads(reqf.read_text(encoding="utf-8")) if reqf else {}
        res["req_tally"] = rq.get("tally") or {}
        res["req_open"] = [{"code": r["code"], "status": r["status"], "topic": str(r.get("topic", ""))[:60], "hand": str(r.get("hand", ""))[:40]}
                           for r in rq.get("requirements", []) if r.get("status") in ("PARTIAL", "MISSING")]
    except (OSError, ValueError) as e:
        res["why"].append(f"需求冊壞:{e}")
    if unreg:
        lamp = "RED"
        res["why"].append(f"{len(unreg)} 支改過的程式沒被需求冊 / 工作流冊點名")
    elif res["behind"] > MAX_BEHIND or (res["behind"] and (res.get("age_h") or 0) > MAX_AGE_H):
        lamp = "RED"
        res["why"].append(f"落後 {res['behind']} 提交 · 快照 {res.get('age_h')} 小時(上限 {MAX_BEHIND} 提交 / {MAX_AGE_H} 小時)")
    elif res["behind"]:
        lamp = "YELLOW"
        res["why"].append(f"交接快照之後有 {res['behind']} 個提交還沒 checkpoint")
    else:
        lamp = "GREEN"
    if res.get("unpushed"):
        lamp = BASE.worst([lamp, "YELLOW"])
        res["why"].append(f"{res['unpushed']} 個提交還沒推上 {res['upstream']}")
    elif res.get("upstream") is None:
        res["why"].append("沒有上游分支:GitHub 同步沒量")
    res["lamp"] = lamp
    res["next"] = [] if lamp == "GREEN" else (
        (["登需求冊 / 工作流冊(新版號):" + " · ".join(unreg[:6])] if unreg else [])
        + ["via-vcgc handoff check", "via-vcgc handoff test <受影響 case>", "via-vcgc registry-sync → --apply(同意閘)",
           "via-vcgc run CGC_MDL237_NumberingSystem --apply --scope → audit", "via-vcgc run CGC_MDL245_SDDValidator check",
           "via-vcgc handoff checkpoint"]) + ([f"git push(還有 {res['unpushed']} 個提交沒推上 {res['upstream']})"] if res.get("unpushed") else [])
    return res


def gate_line(g: dict) -> str:
    if g.get("lamp") == "ABSENT":
        return "交接閘 ABSENT(" + " · ".join(g.get("why") or []) + ")"
    s = f"交接閘 {g['lamp']} · 落後 {g.get('behind', 0)} 提交 · 快照 {g.get('age_h')}h"
    if g.get("unpushed"):
        s += f" · 未推 {g['unpushed']}"
    if g.get("unregistered"):
        s += f" · 未登 {len(g['unregistered'])} 支({' · '.join(g['unregistered'][:3])}{' …' if len(g['unregistered']) > 3 else ''})"
    return s


# ───────────────────────── 工作流冊流程圖(networkx × Plotly)──────────────────────────

def workflow_graph(root: Path) -> dict:
    wkf, reqf = _tail(root, WKF_GLOB), _tail(root, REQ_GLOB)
    if not wkf:
        return {"lamp": "ABSENT", "why": "工作流冊不在"}
    try:
        w = json.loads(wkf.read_text(encoding="utf-8"))
        rq = {r["code"]: r.get("status") for r in json.loads(reqf.read_text(encoding="utf-8")).get("requirements", [])} if reqf else {}
    except (OSError, ValueError) as e:
        return {"lamp": "ABSENT", "why": f"冊讀不到:{e}"}
    nx = V102.lib("networkx")
    nodes, edges = [], []
    for row, wf in enumerate(w.get("workflows", [])):
        reqs = (wf.get("spec") or {}).get("requirements") or []
        lamps = [REQ_LAMP.get(rq.get(c), "NODATA") for c in reqs] or ["NODATA"]
        wl = BASE.worst(lamps)
        nodes.append({"id": wf["code"], "row": row, "kind": "wkf", "label": wf.get("alias", wf["code"]), "lamp": wl,
                      "hover": f"{wf['code']} · {wf.get('name', '')}<br>需求 " + ", ".join(f"{c}:{rq.get(c, '?')}" for c in reqs)})
        prev = wf["code"]
        for st in wf.get("steps", []):
            raw = st.get("engine") or []
            engs = [x for x in ([raw] if isinstance(raw, str) else list(raw)) if isinstance(x, str) and x]  # 冊裡有字串也有清單
            missing = [x for x in engs if not any(True for _ in root.glob(x))]
            has = bool(engs) and not missing
            sl = wl if has else ("RED" if engs else "NODATA")
            names = " · ".join(Path(x).name for x in engs) or "—"
            nodes.append({"id": st["code"], "row": row, "kind": "stp", "label": st.get("alias", ""), "lamp": sl,
                          "hover": f"{st['code']} · {st.get('name', '')}<br>引擎 {names} {'在樹上' if has else ('不在:' + ' · '.join(Path(x).name for x in missing) if engs else '—')}"
                                   f" · 動詞 {st.get('verb', '')}"})
            edges.append((prev, st["code"]))
            prev = st["code"]
    layer = {}
    acyclic = True
    if nx is not None:
        g = nx.DiGraph()
        g.add_nodes_from(n["id"] for n in nodes)
        g.add_edges_from(edges)
        acyclic = nx.is_directed_acyclic_graph(g)
        if acyclic:
            for i, gen in enumerate(nx.topological_generations(g)):
                for nid in gen:
                    layer[nid] = i
    if not layer:  # 缺 networkx 或有環:退回列內序號
        for n in nodes:
            layer[n["id"]] = 0 if n["kind"] == "wkf" else int(re.search(r"STP(\d+)", n["id"]).group(1)) if re.search(r"STP(\d+)", n["id"]) else 1
    for n in nodes:
        n["x"], n["y"] = layer[n["id"]], -n["row"]
    bad = sum(1 for n in nodes if n["kind"] == "stp" and n["lamp"] == "RED")
    return {"lamp": "RED" if bad or not acyclic else BASE.worst(n["lamp"] for n in nodes if n["kind"] == "wkf"),
            "book": wkf.name, "nodes": nodes, "edges": edges, "acyclic": acyclic, "workflows": len(w.get("workflows", [])),
            "steps": sum(1 for n in nodes if n["kind"] == "stp"), "engine_missing": bad,
            "layout": "networkx topological_generations" if nx is not None and acyclic else "列內序號(退路)"}


def workflow_fig(wg: dict) -> dict:
    S = V101.STATUS
    pos = {n["id"]: (n["x"], n["y"]) for n in wg.get("nodes", [])}
    ex, ey = [], []
    for a, b in wg.get("edges", []):
        ex += [pos[a][0], pos[b][0], None]
        ey += [pos[a][1], pos[b][1], None]
    data = [{"type": "scatter", "mode": "lines", "x": ex, "y": ey, "line": {"color": "#c3c2b7", "width": 1}, "hoverinfo": "skip", "showlegend": False}]
    for kind, sym, size in (("wkf", "square", 13), ("stp", "circle", 11)):
        ns = [n for n in wg.get("nodes", []) if n["kind"] == kind]
        data.append({"type": "scatter", "mode": "markers+text", "x": [n["x"] for n in ns], "y": [n["y"] for n in ns],
                     "text": [n["label"][:14] for n in ns], "textposition": "bottom center", "textfont": {"size": 8, "color": "#52514e"},
                     "marker": {"symbol": sym, "size": size, "color": [S.get(n["lamp"], "#b9b8b2") for n in ns], "line": {"color": "#fcfcfb", "width": 2}},
                     "customdata": [n["hover"] for n in ns], "hovertemplate": "%{customdata}<extra></extra>", "showlegend": False})
    rows = max((-n["y"] for n in wg.get("nodes", [])), default=0) + 1
    lay = {"margin": {"l": 8, "r": 8, "t": 4, "b": 4}, "paper_bgcolor": "#fcfcfb", "plot_bgcolor": "#fcfcfb", "height": 40 + rows * 34,
           "xaxis": {"visible": False}, "yaxis": {"visible": False}, "font": {"size": 9}}
    return {"data": data, "layout": lay}


def tally_fig(g: dict) -> dict:
    t = g.get("req_tally") or {}
    keys = [k for k in ("COVERED", "RECORDED", "PARTIAL", "MISSING") if k in t]
    S = V101.STATUS
    return {"data": [{"type": "bar", "orientation": "h", "y": keys, "x": [t[k] for k in keys], "text": [str(t[k]) for k in keys],
                      "textposition": "outside", "cliponaxis": False, "textfont": {"size": 9, "color": "#52514e"},
                      "marker": {"color": [S[REQ_LAMP[k]] for k in keys]}, "hovertemplate": "%{y} %{x} 條<extra></extra>"}],
            "layout": {"margin": {"l": 70, "r": 30, "t": 4, "b": 20}, "paper_bgcolor": "#fcfcfb", "plot_bgcolor": "#fcfcfb", "height": 140,
                       "font": {"size": 10, "color": "#52514e"}, "bargap": 0.35, "xaxis": {"gridcolor": "#e1e0d9", "rangemode": "tozero"},
                       "yaxis": {"autorange": "reversed"}}}


# ───────────────────────── 儀表板加卡 ─────────────────────────

def gate_cards(g: dict, wg: dict) -> tuple:
    e = _html.escape
    pill, tbl = V101.pill, V101.tbl
    kv = [{"項": "交接快照", "lamp": g.get("handoff_lamp") or "NODATA", "值": f"{str(g.get('handoff_at', ''))[:19]} · {g.get('age_h')} 小時前"},
          {"項": "落後提交", "lamp": "GREEN" if not g.get("behind") else ("RED" if g.get("behind", 0) > MAX_BEHIND else "YELLOW"),
           "值": f"{g.get('behind', 0)} 個(上限 {MAX_BEHIND})"},
          {"項": "改過的程式", "lamp": "RED" if g.get("unregistered") else "GREEN",
           "值": f"{g.get('changed_code', 0)} 檔 · {g.get('families', 0)} 族 · 未登 {len(g.get('unregistered') or [])}"},
          {"項": "同步 GitHub", "lamp": "ABSENT" if g.get("upstream") is None else ("YELLOW" if g.get("unpushed") else "GREEN"),
           "值": f"未推 {g.get('unpushed')} · 上游 {g.get('upstream') or '沒有'}"},
          {"項": "驗收 closeout", "lamp": g.get("closeout") or "NODATA", "值": "交接綠 ≠ 驗收"}]
    unreg = "".join(f"<li class='mono'>{e(u)}</li>" for u in (g.get("unregistered") or [])[:20]) or "<li>(無)</li>"
    nxt = "".join(f"<li class='mono'>{e(n)}</li>" for n in g.get("next") or []) or "<li>交接閘綠:沒有要補的</li>"
    commits = [{"sha": c["sha"], "時間": c["at"][5:16].replace("T", " "), "訊息": c["subject"]} for c in (g.get("commits") or [])[:15]]
    by = {}
    for p in g.get("pending") or []:
        by[p.get("state")] = by.get(p.get("state"), 0) + 1
    ropen = [{"code": r["code"], "狀態": r["status"], "主題": r["topic"], "誰": r["hand"]} for r in g.get("req_open") or []]
    html = ("<div class='grid'>"
            f"<div class='card'><h2>AI STATE · 交接閘 {pill(g.get('lamp'))}<span class='c'>{e(' · '.join(g.get('why') or []))[:120]}</span></h2>"
            + tbl(["項", "lamp", "值"], kv, widths=["96px", "84px", "auto"])
            + f"<div class='meta' style='margin:6px 0 2px'>沒被需求冊 / 工作流冊點名的程式族</div><ul style='margin:0 0 0 16px;padding:0;overflow-wrap:anywhere'>{unreg}</ul>"
            + f"<div class='meta' style='margin:6px 0 2px'>收尾要補的(照 VCGC 必用順序)</div><ol style='margin:0 0 0 18px;padding:0;overflow-wrap:anywhere'>{nxt}</ol></div>"
            f"<div class='card'><h2>需求冊總表<span class='c'>{e(str(g.get('req_book') or ''))}</span></h2><div id='fig_req' class='plot' style='height:140px'></div>"
            + f"<div class='meta' style='margin:4px 0 2px'>未完成需求(PARTIAL / MISSING)· 交接待辦 " + " · ".join(f"{e(str(k))} {v}" for k, v in sorted(by.items())) + "</div>"
            + tbl(["code", "狀態", "主題", "誰"], ropen, lamp_cols=(), widths=["100px", "70px", "auto", "30%"]) + "</div>"
            f"<div class='card'><h2>交接快照之後的提交<span class='c'>{g.get('behind', 0)} 個</span></h2>"
            + tbl(["sha", "時間", "訊息"], commits, lamp_cols=(), widths=["70px", "88px", "auto"]) + "</div>"
            "</div>"
            f"<div class='card' style='margin-bottom:8px'><h2>工作流冊流程圖(Flow SSOT){pill(wg.get('lamp'))}<span class='c'>"
            f"{e(str(wg.get('book', '')))} · {wg.get('workflows', 0)} 條 · {wg.get('steps', 0)} 步 · 引擎不在 {wg.get('engine_missing', 0)} · "
            f"{'無環' if wg.get('acyclic', True) else '有環'} · 排版 {e(str(wg.get('layout', '')))} · ■ 工作流 ● 步</span></h2><div id='fig_wkf'></div></div>")
    js = ("<script>(function(){var F={req:" + json.dumps(tally_fig(g), ensure_ascii=False) + ",wkf:" + json.dumps(workflow_fig(wg), ensure_ascii=False) + "};"
          "for(var k in F){var el=document.getElementById('fig_'+k);if(!el)continue;if(window.Plotly){Plotly.newPlot(el,F[k].data,F[k].layout,"
          "{displayModeBar:false,responsive:true})}else{el.innerHTML=\"<div class='nop'>沒有 Plotly</div>\"}}})();</script>")
    return html, js


def add_gate_cards(out: Path, g: dict, wg: dict) -> None:
    page_p = out / V101.PAGE_NAME
    try:
        page = page_p.read_text(encoding="utf-8")
    except OSError:
        return
    html, js = gate_cards(g, wg)
    i = page.find("<div class='grid'>")
    page = (page[:i] + html + page[i:]) if i > 0 else page.replace("<footer>", html + "<footer>", 1)  # KPI 列正下方、AUTO SYNC 之前
    page = page.replace("</body>", js + "</body>", 1).replace(f"VIA_Panorama {V103.VERSION}(前版 v0102", f"VIA_Panorama {VERSION}(前版 v0103 · v0102", 1)
    tmp = out / (V101.PAGE_NAME + ".tmp")
    tmp.write_text(page, encoding="utf-8")
    tmp.replace(page_p)


# ───────────────────────── 動詞 ─────────────────────────

def _via_root(rep: dict | None) -> Path | None:
    if rep and rep.get("source") == "local" and (Path(rep["target"]) / HANDOFF).is_file():
        return Path(rep["target"])
    v = BASE.via_root()
    return v if v and (v / HANDOFF).is_file() else None


def gate_round(out: Path) -> dict | None:
    rep = V102._latest(out)
    root = _via_root(rep)
    if root is None:
        return None
    g = state_gate(root)
    try:
        old = json.loads((out / GATE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        old = None
    tmp = out / (GATE + ".tmp")
    tmp.write_text(json.dumps(g, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(out / GATE)
    if old and old.get("lamp") != g["lamp"] and rep:
        bad = ("RED", "YELLOW", "ABSENT")
        kind = "FIXED" if old["lamp"] in bad and g["lamp"] not in bad else ("NEW" if g["lamp"] in bad and old["lamp"] not in bad else
                                                                            ("ESCALATED" if BASE.SEVER.get(g["lamp"], 0) > BASE.SEVER.get(old["lamp"], 0) else "EASED"))
        V102.append_lessons(out, [{"ts": BASE.now_utc(), "run": f"gate-{g['ts']}", "target_key": rep.get("target_key"), "target": rep.get("target"),
                                   "sha16": rep.get("sha16"), "etag": rep.get("etag"), "section": "S", "sig": "state-gate", "kind": kind,
                                   "key": "S:交接閘", "from": old["lamp"], "to": g["lamp"], "note": gate_line(g)[:80]}])
    add_gate_cards(out, g, workflow_graph(root))
    return g


_V103_ROUND = V103.one_round


def one_round(target: str | None, opts: dict, out: Path, interval: int, state: dict) -> tuple:
    rc, line = _V103_ROUND(target, opts, out, interval, state)
    g = gate_round(out)
    return rc, line + (f"  {gate_line(g)}" if g else "")


def autostart(target: str | None, opts: dict) -> int:
    """同 v0103,但背景監控起的是本版;[監控] 那一行直接帶交接閘(一行,VCGC 只轉印第一行)。"""
    out = V101.resolve_out(target, opts)
    rec = V103.touch(out, opts.get("from") or "manual")
    pid = V103.watcher_pid(out)
    if pid:
        head = f"[監控] 背景全景監控中 pid {pid} · 觸碰 {rec['verb']}"
    else:
        argv = [sys.executable, str(Path(__file__).resolve()), "watch", "--autosync", "--interval", str(int(opts.get("interval") or 30)),
                "--idle", str(int(opts.get("idle") or 1800))]
        if target:
            argv.insert(3, target)
        for k in ("profile", "scope", "out"):
            if opts.get(k):
                argv += [f"--{k}", str(opts[k])]
        env = {**os.environ, V103.ACTIVE_ENV: "1", "VIA_NO_OPEN": "1"}
        kw = {"creationflags": 0x00000008 | 0x00000200} if os.name == "nt" else {"start_new_session": True}
        with open(out / "watch.out", "a", encoding="utf-8") as log:
            p = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=env, close_fds=True, **kw)
        (out / V103.PIDF).write_text(json.dumps({"pid": p.pid, "ts": BASE.now_utc(), "argv": argv[2:]}, ensure_ascii=False), encoding="utf-8")
        if os.name == "nt" and os.environ.get("VIA_NO_OPEN") != "1":
            try:
                os.startfile(str(out / V101.PAGE_NAME))  # noqa: S606 — 只開本機報告頁
            except OSError as e:
                BASE.note(f"開頁失敗:{e}")
        head = f"[監控] 已在背景起全景監控 pid {p.pid} · 閒置 {argv[argv.index('--idle') + 1]} 秒自停"
    root = _via_root(V102._latest(out))
    gate = gate_line(state_gate(root)) if root else "交接閘 ABSENT(不是 VIA 樹)"
    print(f"{head} · {gate} · 頁 {out / V101.PAGE_NAME}")
    return 0


def state_verb(target: str | None, opts: dict) -> int:
    out = V101.resolve_out(target, opts)
    root = _via_root(V102._latest(out)) or (Path(target) if target and (Path(target) / HANDOFF).is_file() else None)
    if root is None:
        print(f"[{ENGINE} state] 交接閘 ABSENT:找不到 {HANDOFF}")
        return 2
    g = state_gate(root)
    wg = workflow_graph(root)
    t = g.get("req_tally") or {}
    lines = [f"[{ENGINE} state] {gate_line(g)}",
             f"  交接快照 {str(g.get('handoff_at', ''))[:19]} · 交接 {g.get('handoff_lamp')} · 驗收 {g.get('closeout')} · 待辦 {len(g.get('pending') or [])}",
             f"  需求冊 {g.get('req_book')} · " + " · ".join(f"{k} {v}" for k, v in t.items()),
             f"  工作流冊 {wg.get('book')} · {wg.get('workflows', 0)} 條 {wg.get('steps', 0)} 步 · 引擎不在 {wg.get('engine_missing', 0)} · {wg.get('lamp')}"]
    lines += [f"  下一步 {n}" for n in (g.get("next") or [])[:5]]
    print("\n".join(lines[:10]))
    return 0 if g["lamp"] == "GREEN" else (1 if g["lamp"] == "RED" else 2)


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a and a[0] in ("--selftest", "selftest"):
        return selftest()
    V103.one_round = one_round  # 前版 watch / dashboard 走本版的一輪(多交接閘)
    V103.ENGINE = ENGINE        # 前版動詞印的名字 = 實際執行的本版
    if a and a[0] in ("autostart", "state"):
        opts, target = V103._opts(a[1:])
        return (autostart if a[0] == "autostart" else state_verb)(target, opts)
    return V103.main(a)


# ───────────────────────── 自測 ─────────────────────────

def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  {'✓' if cond else '✗'} {name}" + (f" · {note}" if note and not cond else ""))
    print(f"=== {ENGINE} 自測(薄尾;先跑前版 v0103 → v0102 → v0101 → 本體 v0100)===")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        prc = V103.selftest()
    chk("前版 v0103(含 v0102 · v0101 · v0100)自測", prc == 0, (buf.getvalue().strip().splitlines() or [""])[-1])
    miss = [k for k in vars(V103) if not k.startswith("_") and k not in globals()]
    chk("尾版不少公開名稱(TAILAPI)", not miss, " · ".join(miss[:5]))
    tmp = Path(tempfile.mkdtemp(prefix="via_pan104_"))
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}

    def g(*a):
        return subprocess.run(["git", *a], cwd=str(tmp / "v"), capture_output=True, env=env)
    try:
        v = tmp / "v"
        (v / "docs" / "handoff").mkdir(parents=True)
        (v / "supportive modules" / "registry").mkdir(parents=True)
        reg = v / "supportive modules" / "registry"
        (reg / "VIA_Requirements_SSOT_v0100.json").write_text(json.dumps({"tally": {"COVERED": 1, "PARTIAL": 1}, "requirements": [
            {"code": "X-REQ001", "status": "COVERED", "topic": "a", "homes": ["X-WKF001"]},
            {"code": "X-REQ002", "status": "PARTIAL", "topic": "b", "hand": "AI", "homes": ["X-WKF001"]}]}, ensure_ascii=False), encoding="utf-8")
        (reg / "VIA_Workflow_VCGC_SSOT_v0100.json").write_text(json.dumps({"workflows": [
            {"code": "X-WKF001", "alias": "flow", "name": "f", "spec": {"requirements": ["X-REQ001", "X-REQ002"]}, "steps": [
                {"code": "X-WKF001-STP001", "alias": "a", "engine": "supportive modules/registry/Known_Engine_v*.py", "verb": "x"},
                {"code": "X-WKF001-STP002", "alias": "b", "engine": ["supportive modules/registry/Known_Engine_v*.py",
                                                                       "supportive modules/registry/Ghost_Engine_v*.py"], "verb": "y"}]}]},
            ensure_ascii=False), encoding="utf-8")
        (reg / "Known_Engine_v0100.py").write_text('"""k"""\n', encoding="utf-8")
        g("init", "-q", "-b", "main")
        g("add", ".")
        g("commit", "-q", "-m", "base")
        time.sleep(1.1)
        (v / "docs" / "handoff" / "HANDOFF_latest.json").write_text(json.dumps({"at": BASE.now_utc(), "lamp": "GREEN", "closeout_lamp": "YELLOW",
                                                                                "pending": [{"id": "P1", "state": "PARTIAL"}]}), encoding="utf-8")
        g("add", ".")
        g("commit", "-q", "-m", "checkpoint")
        g0 = state_gate(v)
        chk("交接閘:checkpoint 收尾提交本身不算落後 = GREEN", g0["lamp"] == "GREEN" and g0["behind"] == 0 and g0["bookkeeping"] == 1, json.dumps({k: g0.get(k) for k in ("lamp", "behind", "why")}, ensure_ascii=False))
        time.sleep(1.1)
        (reg / "Known_Engine_v0101.py").write_text('"""k2"""\n', encoding="utf-8")
        g("add", ".")
        g("commit", "-q", "-m", "known change")
        g1 = state_gate(v)
        chk("交接閘:有落後但程式都已登記 = YELLOW", g1["lamp"] == "YELLOW" and not g1["unregistered"], json.dumps({k: g1.get(k) for k in ("lamp", "behind", "unregistered")}, ensure_ascii=False))
        (reg / "Stray_Module_v0100.py").write_text('"""s"""\n', encoding="utf-8")
        g("add", ".")
        g("commit", "-q", "-m", "stray")
        g2 = state_gate(v)
        chk("交接閘:改過的程式沒被冊點名 = RED · 列出族名 · 給收尾指令", g2["lamp"] == "RED" and g2["unregistered"] == ["Stray_Module"]
            and any("handoff checkpoint" in n for n in g2["next"]), json.dumps({k: g2.get(k) for k in ("lamp", "unregistered")}, ensure_ascii=False))
        chk("同步 GitHub:沒有上游 = 沒量(None)不假綠", g2.get("upstream") is None and g2.get("unpushed") is None
            and any("沒有上游" in w for w in g2["why"]))
        bare = tmp / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], capture_output=True, env=env)
        g("remote", "add", "origin", str(bare))
        g("push", "-q", "-u", "origin", "main")
        (reg / "Known_Engine_v0102.py").write_text('"""k3"""\n', encoding="utf-8")
        g("add", ".")
        g("commit", "-q", "-m", "local only")
        g3 = state_gate(v)
        chk("同步 GitHub:本機領先上游 1 = 未推 1 · 收尾指令帶 git push", g3.get("unpushed") == 1 and any("git push" in n for n in g3["next"])
            and "未推 1" in gate_line(g3), json.dumps({k: g3.get(k) for k in ("unpushed", "upstream", "lamp")}, ensure_ascii=False))
        wg = workflow_graph(v)
        st = {n["id"]: n["lamp"] for n in wg["nodes"]}
        chk("工作流圖:networkx 無環分層 · 引擎在 = 跟需求最差(PARTIAL 黃)· 引擎清單缺一支 = 紅", wg["acyclic"] and st["X-WKF001"] == "YELLOW"
            and st["X-WKF001-STP001"] == "YELLOW" and st["X-WKF001-STP002"] == "RED" and wg["engine_missing"] == 1
            and [n["x"] for n in wg["nodes"]] == [0, 1, 2], json.dumps(st, ensure_ascii=False))
        f = workflow_fig(wg)
        chk("Plotly 圖:邊一條線 + 工作流 / 步兩組節點 · hover 帶引擎與需求", len(f["data"]) == 3 and "Ghost_Engine" in json.dumps(f, ensure_ascii=False)
            and "X-REQ002:PARTIAL" in json.dumps(f, ensure_ascii=False))
        out = tmp / "out"
        out.mkdir()
        (out / V101.PAGE_NAME).write_text("<html><body><div class='kpis'></div><div class='grid'>x</div><footer>VIA_Panorama v0103(前版 v0102 x</footer></body></html>", encoding="utf-8")
        add_gate_cards(out, g2, wg)
        page = (out / V101.PAGE_NAME).read_text(encoding="utf-8")
        chk("儀表板:交接閘卡 · 需求冊總表 · 提交表 · 工作流圖 插在 KPI 下方", all(x in page for x in ("AI STATE · 交接閘", "fig_req", "fig_wkf", "Stray_Module"))
            and page.index("AI STATE") < page.index(">x<"))
        chk("gate_line 一行(給 VCGC [監控] 提示)", "\n" not in gate_line(g2) and "未登 1 支" in gate_line(g2))
        before = subprocess.run(["git", "status", "--porcelain"], cwd=str(v), capture_output=True, text=True).stdout
        state_gate(v)
        workflow_graph(v)
        chk("只讀:跑完目標 git 工作樹沒變", before == subprocess.run(["git", "status", "--porcelain"], cwd=str(v), capture_output=True, text=True).stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"  {ENGINE} selftest {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
