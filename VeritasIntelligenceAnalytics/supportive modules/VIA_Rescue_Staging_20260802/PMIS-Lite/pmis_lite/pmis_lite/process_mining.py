"""流程探勘（純 Python、離線、無 AGPL 依賴）。

從 SSOT 事件流反推「資料在真實世界走過哪條路」——不是理想劇本，是實況。
避開 pm4py（AGPL-3.0，商用有疑慮），自建 directly-follows graph：
  1. 事件序列化：records → (case, activity, time, resource)
  2. 主幹路徑發掘：directly-follows graph（誰接誰、幾次、平均耗時）
  3. 瓶頸熱力：哪段轉換等最久
  4. 自我返工環：同一階段自己繞圈 = 溝通斷層
  5. 合規比對：與行業標準序列對齊，抓「偷跑」與「時空回溯」

確定性規則，斷網無 AI 照跑。
"""
from __future__ import annotations

from datetime import datetime
from collections import defaultdict, Counter


def _parse_time(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00").split("+")[0])
    except Exception:
        try:
            return datetime.strptime(str(s)[:10], "%Y-%m-%d")
        except Exception:
            return None


def build_event_log(records, case_field="thread_id", activity_field="topic",
                    resource_field="actor"):
    """records → 事件序列。每案(case)依時間排序的 activity 軌跡。"""
    cases = defaultdict(list)
    for r in records:
        case = getattr(r, case_field, "") or getattr(r, "product", "") or "(未分案)"
        act = getattr(r, activity_field, "") or getattr(r, "status", "") or "(未標階段)"
        ts = _parse_time(getattr(r, "event_time", ""))
        res = getattr(r, resource_field, "") or ""
        cases[case].append({"activity": act, "ts": ts, "resource": res})
    # 每案依時間排序
    for c in cases:
        cases[c].sort(key=lambda e: (e["ts"] or datetime.min))
    return dict(cases)


def discover_dfg(event_log):
    """directly-follows graph：edge (a→b) 的次數與平均耗時（天）。"""
    freq = Counter()
    durs = defaultdict(list)
    activities = Counter()
    for case, events in event_log.items():
        for e in events:
            activities[e["activity"]] += 1
        for i in range(len(events) - 1):
            a, b = events[i]["activity"], events[i + 1]["activity"]
            freq[(a, b)] += 1
            ta, tb = events[i]["ts"], events[i + 1]["ts"]
            if ta and tb:
                durs[(a, b)].append((tb - ta).total_seconds() / 86400.0)
    edges = []
    for (a, b), n in freq.most_common():
        d = durs.get((a, b), [])
        avg = round(sum(d) / len(d), 2) if d else None
        edges.append({"from": a, "to": b, "count": n, "avg_days": avg})
    return {"activities": dict(activities), "edges": edges}


def find_bottlenecks(dfg, top=3):
    """平均耗時最久的轉換 = 卡點。"""
    timed = [e for e in dfg["edges"] if e["avg_days"] is not None]
    return sorted(timed, key=lambda e: e["avg_days"], reverse=True)[:top]


def find_rework(event_log):
    """自我返工環(a→a) 與重複造訪(同案同階段出現多次)。"""
    self_loops = Counter()
    revisits = []
    for case, events in event_log.items():
        acts = [e["activity"] for e in events]
        for i in range(len(acts) - 1):
            if acts[i] == acts[i + 1]:
                self_loops[acts[i]] += 1
        c = Counter(acts)
        for a, n in c.items():
            if n >= 2:
                revisits.append({"case": case, "activity": a, "times": n})
    return {"self_loops": dict(self_loops), "revisits": revisits}


def check_conformance(event_log, expected_sequence):
    """與行業標準序列對齊：抓偷跑(skip)與時空回溯(backward jump)。"""
    order = {a: i for i, a in enumerate(expected_sequence)}
    violations = []
    for case, events in event_log.items():
        seq = [e["activity"] for e in events if e["activity"] in order]
        for i in range(len(seq) - 1):
            ia, ib = order[seq[i]], order[seq[i + 1]]
            if ib < ia:
                violations.append({"case": case, "type": "時空回溯 backward",
                                   "detail": f"{seq[i]}→{seq[i+1]}"})
            elif ib - ia >= 2:
                skipped = expected_sequence[ia + 1:ib]
                violations.append({"case": case, "type": "偷跑 skip",
                                   "detail": f"{seq[i]}→{seq[i+1]}（跳過 {'/'.join(skipped)}）"})
    return violations


def mine(records, expected_sequence=None, case_field="thread_id", activity_field="topic"):
    """一次跑完流程探勘，回傳完整結果。"""
    log = build_event_log(records, case_field, activity_field)
    dfg = discover_dfg(log)
    result = {
        "cases": len(log), "activities": dfg["activities"], "dfg": dfg,
        "bottlenecks": find_bottlenecks(dfg), "rework": find_rework(log),
    }
    if expected_sequence:
        result["conformance"] = check_conformance(log, expected_sequence)
    return result


def render_svg(result, expected_sequence, title="流程探勘 · 實況路徑圖"):
    """把探勘結果畫成左→右分層流程圖（Visual Lock 風，離線 SVG）。
    瓶頸=紅粗線、返工=環、偷跑/回溯=紅虛線。"""
    acts = list(expected_sequence)
    for a in result["activities"]:
        if a not in acts:
            acts.append(a)
    col_x = {a: 120 + i * 165 for i, a in enumerate(acts)}
    cy = 210
    W = 120 + len(acts) * 165 + 60
    bott = result["bottlenecks"][0] if result["bottlenecks"] else None
    bott_key = (bott["from"], bott["to"]) if bott else None
    viol = {(v["case"],) for v in result.get("conformance", [])}  # noqa
    skip_pairs = set()
    for v in result.get("conformance", []):
        d = v["detail"].split("（")[0]
        if "→" in d:
            skip_pairs.add(tuple(d.split("→")))

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 380" width="{W}" height="380" font-family="DM Sans,Noto Sans TC,sans-serif">']
    svg.append(f'<rect width="{W}" height="380" fill="#f5f4f0"/>')
    svg.append(f'<text x="40" y="44" font-size="13" letter-spacing="2" fill="#9c9890">{title}</text>')
    svg.append(f'<line x1="40" y1="56" x2="{W-40}" y2="56" stroke="#4c78a8" stroke-width="2"/>')
    svg.append('<defs><marker id="ar" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#5a6b7a"/></marker>'
               '<marker id="arr" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#c96b5a"/></marker></defs>')

    # edges
    self_loops = result["rework"]["self_loops"]
    for e in result["dfg"]["edges"]:
        a, b = e["from"], e["to"]
        if a == b:
            continue
        x1, x2 = col_x.get(a), col_x.get(b)
        if x1 is None or x2 is None:
            continue
        is_bott = bott_key == (a, b)
        is_skip = (a, b) in skip_pairs
        w = min(6, 1 + e["count"])
        if is_skip:
            col, dash, mk = "#c96b5a", '4 3', "arr"
        elif is_bott:
            col, dash, mk = "#c96b5a", 'none', "ar"; w = 5
        else:
            col, dash, mk = "#5a6b7a", 'none', "ar"
        x1e, x2e = x1 + 52, x2 - 52
        arc = -60 if (is_skip or x2 < x1) else -34
        mx = (x1e + x2e) / 2
        svg.append(f'<path d="M{x1e},{cy} Q{mx},{cy+arc} {x2e},{cy}" fill="none" stroke="{col}" stroke-width="{w}" stroke-dasharray="{dash}" marker-end="url(#{mk})" opacity="0.85"/>')
        lbl = f'×{e["count"]}' + (f' · {e["avg_days"]}天' if e["avg_days"] is not None else '')
        svg.append(f'<text x="{mx}" y="{cy+arc-4}" font-size="10.5" text-anchor="middle" fill="{col}">{lbl}</text>')

    # nodes
    for a in acts:
        x = col_x[a]
        loop = self_loops.get(a, 0)
        svg.append(f'<rect x="{x-52}" y="{cy-26}" width="104" height="52" rx="6" fill="#fff" stroke="#4c78a8" stroke-width="2"/>')
        svg.append(f'<text x="{x}" y="{cy+2}" font-size="16" font-weight="700" text-anchor="middle" fill="#2b2a28">{a}</text>')
        svg.append(f'<text x="{x}" y="{cy+18}" font-size="9.5" text-anchor="middle" fill="#9c9890">{result["activities"].get(a,0)} 次</text>')
        if loop:
            svg.append(f'<path d="M{x-14},{cy-26} C{x-30},{cy-64} {x+30},{cy-64} {x+14},{cy-26}" fill="none" stroke="#c96b5a" stroke-width="2.5" marker-end="url(#arr)"/>')
            svg.append(f'<text x="{x}" y="{cy-58}" font-size="10" text-anchor="middle" fill="#c96b5a">返工×{loop}</text>')

    # legend
    y0 = 340
    svg.append(f'<text x="40" y="{y0}" font-size="11" fill="#9c9890">圖例：</text>')
    svg.append(f'<line x1="90" y1="{y0-4}" x2="120" y2="{y0-4}" stroke="#c96b5a" stroke-width="5"/><text x="126" y="{y0}" font-size="11" fill="#6b675f">瓶頸(最久)</text>')
    svg.append(f'<line x1="210" y1="{y0-4}" x2="240" y2="{y0-4}" stroke="#c96b5a" stroke-width="2" stroke-dasharray="4 3"/><text x="246" y="{y0}" font-size="11" fill="#6b675f">偷跑/回溯</text>')
    svg.append(f'<path d="M330,{y0-2} C324,{y0-14} 346,{y0-14} 340,{y0-2}" fill="none" stroke="#c96b5a" stroke-width="2"/><text x="352" y="{y0}" font-size="11" fill="#6b675f">自我返工環</text>')
    svg.append('</svg>')
    return "\n".join(svg)
