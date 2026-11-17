#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL283_CardMatrixFeedback v0100 — 對內工作平台:卡片摘要 · 矩陣明細 · 給 AI 的回饋兩段篩選(只摺不丟)。

操作員 2026-11-17:「現況矩陣作為對內工作平台視覺化鎖定模板;摘要用卡片、詳細用矩陣;篩選給 AI 回饋的部分再篩選;寧可完善不可遺漏;建立這個機制引擎」。

  run       讀項目(預設:CGC_MDL282_LocalMonitor 的五個區塊;或 --in <項目冊.json>)→ 兩段篩選 → 卡片 + 矩陣頁 / 回饋包 / 完整去向冊 / 只增帳
  selftest  合成項目 · 不碰真倉
  spec      印出篩選機制
  version
旗標  --in <json>  --out <夾>  --budget <行數,預設 300>  --no-open

第一段(選;六條任一命中就入選,寧可多選):
  S1 紅 · S2 黃 · S3 跟上一輪比有變(燈變 / 新出現 / 不見)· S4 要人裁(衝突 / 待確認 / 待批准)· S5 退步(上一輪綠、這一輪不是)· S6 灰而且是缺證據
第二段(再篩;只改形式,不縮範圍):
  分流 退步 > 真紅 > 待裁 > 環境 > 中斷 > 黃 > 缺證據 > 變動 → 同因併組(列數量與例子)→ 依優先排序 →
  超過行數預算時逐級摺疊(併組門檻 3→2 → 低優先類別改成每區塊一行 → 每類一行),任何一級都不丟項目
不遺漏的保證:每個項目恰有一個去向 —— 逐列 / 併組:<組號> / 只計數:<桶>;全部寫進 FEEDBACK_FULL_latest.jsonl 並對帳,
  「應掃 = 已掃 + 略過」「入選 = 逐列 + 併組 + 只計數」「卡片合計 = 矩陣列數」有一條對不上就整包亮紅。
邊界  唯讀:不改任何冊、收據、他系統檔;輸出只寫 VIA_Reports/vcgc(倉裡已忽略);不發號 · 不裝套件 · 不連網 · 不載 TA-Lib。
版面  只取 VIA_UI_WorkPlatform_TemplateLock 尾版的 css 與它釘住的 VIA_UI_Template_SSOT token;本檔不帶任何色值。
其他系統  VDF / VRN-2 / VQG / VAP 各自把自己的項目寫成項目冊(items: section · system · lamp · id · title · detail · ver · at · needs),
  用 --in 餵進來即可;本引擎不讀也不改他系統內部。
rc    0 綠 · 2 黃 · 1 紅(對帳不符也是 1)
呼叫  VIA_FROM_VCGC=YES python3 CGC_MDL149_…_vNNNN.py run CGC_MDL283_CardMatrixFeedback run
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

import datetime as _dt
import hashlib
import html
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ENGINE = "CGC_MDL283_CardMatrixFeedback_v0100"
VER_RX = re.compile(r"[-_]v(\d{4})(?=\.[A-Za-z0-9]+$)")
LN = {"g": "綠", "y": "黃", "r": "紅", "x": "灰"}
SEV = {"r": 0, "y": 1, "g": 2, "x": 3}
CLASSES = [("REG", "退步", "r"), ("TRUE", "真紅", "r"), ("DECIDE", "待裁", "y"), ("ENV", "環境", "y"),
           ("INT", "中斷", "y"), ("YEL", "黃", "y"), ("NOEV", "缺證據", "x"), ("CHG", "變動", "x")]
CN = {c: n for c, n, _ in CLASSES}
PRI = {c: i for i, (c, _, _) in enumerate(CLASSES)}
# 判別式只看「狀態說明」,不看項目名稱(名稱裡的 conflict / proxy / timeout 不是狀態)
INT_RX = re.compile(r"逾時|中斷|被打斷|沒跑完|timed out|TIMEOUT|rc\s*=?\s*124\b")
ENV_RX = re.compile(r"ModuleNotFound|ImportError|No module named|沒裝|缺套件|缺依賴|I/O error|Errno|PermissionError|網路不通|認證失敗|環境紅|磁碟不足|記憶體不足")
NEED_RX = re.compile(r"衝突|待裁|待確認|待批准|需批准|要你裁|NEED_APPROVAL|CONFLICT[_-]")
FAIL_RX = re.compile(r"rc\s*=?\s*(?!0\b|124\b)\d+|Traceback|verdict = RED|檔不在")
NOEV_RX = re.compile(r"沒有收據|沒有證據|沒有實測|還沒跑|沒跑過|未量|待補")
RULES = [("S1", "紅"), ("S2", "黃"), ("S3", "跟上一輪比有變(燈變 / 新出現 / 不見)"), ("S4", "要人裁(衝突 / 待確認 / 待批准)"),
         ("S5", "退步(上一輪綠、這一輪不是)"), ("S6", "灰而且是缺證據")]


def accel_status() -> str:
    """覆蓋率以生效計:標記在 + 執行時載得到才算。"""
    if VIA_ACCEL is None:
        return "沒掛到(走標準庫)"
    return "已掛 · accel_map " + ("可用" if hasattr(VIA_ACCEL, "accel_map") else "不在")


def pmap(fn, items):
    """平行 map(加速器 accel_map;缺席或出錯退回序跑)。保序。"""
    items = list(items)
    if VIA_ACCEL is not None and hasattr(VIA_ACCEL, "accel_map") and len(items) > 1:
        try:
            out = VIA_ACCEL.accel_map(fn, items)
            if len(out) == len(items) and all(ok for ok, _ in out):
                return [r for _, r in out]
        except Exception as e:
            print("[pmap] 加速器平行失敗(%s)→ 序跑" % type(e).__name__, flush=True)
    return [fn(x) for x in items]


def E(s) -> str:
    return html.escape(str(s), quote=True)


def cut(s, n=200) -> str:
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[: n - 1] + "…"


def worst(lamps) -> str:
    ls = [x for x in lamps if x in ("r", "y", "g")]
    return min(ls, key=lambda c: SEV[c]) if ls else "x"


def norm_lamp(v) -> str:
    s = str(v or "").strip().lower()
    return {"green": "g", "綠": "g", "g": "g", "ok": "g", "yellow": "y", "黃": "y", "y": "y", "red": "r", "紅": "r", "r": "r"}.get(s, "x")


def find_via(arg: str = ""):
    if arg and (Path(arg) / "supportive modules" / "registry").is_dir():
        return Path(arg)
    for up in Path(__file__).resolve().parents:
        if (up / "supportive modules" / "registry").is_dir():
            return up
    return None


def tail(reg: Path, stem: str, ext: str):
    best = None
    for p in reg.glob(stem + "_v*" + ext):
        m = VER_RX.search(p.name)
        if m and (best is None or int(m.group(1)) > best[0]):
            best = (int(m.group(1)), p)
    return best[1] if best else None


def load_py(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------- 項目 ----------------
def normalize(raw):
    """回 (items, skipped)。每個項目補齊欄位並給一個不重複的 key;不是 dict 的列進略過清單(照實點名)。"""
    items, skipped, seen = [], [], {}
    for i, r in enumerate(raw):
        if not isinstance(r, dict):
            skipped.append("第 %d 列不是物件:%s" % (i + 1, cut(r, 60)))
            continue
        it = {"section": str(r.get("section") or "未分區"), "system": str(r.get("system") or "—"), "lamp": norm_lamp(r.get("lamp")),
              "id": str(r.get("id") or ""), "title": str(r.get("title") or r.get("id") or "(沒有名稱)"), "detail": str(r.get("detail") or ""),
              "ver": str(r.get("ver") or ""), "at": str(r.get("at") or ""), "needs": bool(r.get("needs")), "gone": False}
        base = "%s|%s|%s" % (it["section"], it["system"], it["id"] or it["title"])
        seen[base] = seen.get(base, 0) + 1
        it["key"] = base if seen[base] == 1 else "%s#%d" % (base, seen[base])
        items.append(it)
    return items, skipped


def from_localmonitor(via: Path):
    """沿用 CGC_MDL282_LocalMonitor 的五個區塊函式(不另寫掃描器);回 (原始項目, 來源說明)。"""
    reg = via / "supportive modules" / "registry"
    p = tail(reg, "CGC_MDL282_LocalMonitor", ".py")
    if p is None:
        return [], "CGC_MDL282_LocalMonitor 不在"
    m = load_py(p)
    tails, _ = m.scan_tails(via)
    jobs = {"S": lambda: m.sec_systems(via), "T": lambda: m.sec_tools(via, tails, False), "P": lambda: m.sec_params(via),
            "G": lambda: m.sec_engines(via, tails), "R": lambda: m.sec_receipts(via)[0]}
    res = dict(zip(jobs, pmap(lambda k: jobs[k](), list(jobs))))
    out = []
    for r in res["S"]:
        out.append({"section": "系統", "system": r["sys"], "lamp": r["lamp"], "id": r["sys"], "title": "%s 入口 %s" % (r["sys"], r.get("tail") or ""),
                    "ver": r.get("number") or "", "at": r.get("at") or "", "detail": "實跑 %s · 憲法 %s%s" % (r.get("run_txt"), r.get("con_txt"), (" · " + r["note"]) if r.get("note") else "")})
    for r in res["T"]:
        out.append({"section": "工具", "system": "VCGC", "lamp": r["lamp"], "id": r["tool"], "title": r["tool"], "ver": r.get("ver") or "",
                    "at": r.get("at") or "", "detail": "%s · %s" % (r.get("role"), r.get("state"))})
    for r in res["P"]:
        rid = r.get("id") if r.get("id") not in (None, "", "—") else r.get("name")
        out.append({"section": "參數", "system": r["sys"], "lamp": r["lamp"], "id": rid, "title": r.get("name") or rid, "ver": r.get("ver") or "", "at": r.get("at") or "",
                    "detail": " · ".join(x for x in (r.get("cls"), ("值 " + cut(r.get("value"), 60)) if r.get("value") else "", r.get("mut"), r.get("why")) if x and x != "—")})
    for r in res["G"]:
        out.append({"section": "模組引擎", "system": r[1], "lamp": r[0], "id": r[3] or r[4], "title": "%s(%s)" % (r[4], r[2]), "ver": r[5], "at": r[8], "detail": r[7]})
    for r in res["R"]:
        up = r["file"].upper()
        sysn = next((s for s in ("VDF", "VRN", "VQG", "VAP") if s in up), "VCGC")
        out.append({"section": "收據", "system": sysn, "lamp": r["lamp"], "id": r["file"], "title": r["file"], "at": r.get("at") or "", "detail": r.get("state") or ""})
    return out, "%s 的五個區塊" % p.stem


# ---------------- 第一段:選 ----------------
def stage1(items, prev):
    """六條任一命中就入選。prev = 上一輪 {key: 燈};None = 沒有上一輪。會把『上一輪有、這一輪不見』補成項目。"""
    now = {it["key"] for it in items}
    if prev is not None:
        for k in sorted(set(prev) - now):
            sec, sysn, name = (k.split("|", 2) + ["", ""])[:3]
            items.append({"section": sec or "未分區", "system": sysn or "—", "lamp": "r" if prev[k] == "g" else "x", "id": name, "title": name or k, "ver": "", "at": "",
                          "detail": "上一輪有、這一輪不見(上一輪%s)" % LN.get(prev[k], "灰"), "needs": False, "gone": True, "key": k, "was": prev[k]})
    for it in items:
        rules, lamp, text = [], it["lamp"], it["detail"]
        if it.get("gone"):
            rules.append("S3")
            if it.get("was") == "g":
                rules.append("S5")
        else:
            if lamp == "r":
                rules.append("S1")
            if lamp == "y":
                rules.append("S2")
            if prev is not None:
                was = prev.get(it["key"])
                if was is None or was != lamp:
                    rules.append("S3")
                    it["was"] = was
                if was == "g" and lamp != "g":
                    rules.append("S5")
            if it["needs"] or (lamp != "g" and NEED_RX.search(text)):  # 綠列只認明講的 needs,不靠字眼
                rules.append("S4")
            if lamp == "x" and NOEV_RX.search(text):
                rules.append("S6")
        it["rules"] = rules
        it["selected"] = bool(rules)
    return items


# ---------------- 第二段:再篩 ----------------
def classify(it, peer=None) -> str:
    text, lamp, rules = it["detail"], it["lamp"], it["rules"]
    it["also"] = ""
    if "S5" in rules:
        return "REG"
    if lamp in ("r", "y"):
        if "S4" in rules:
            if lamp == "r" and FAIL_RX.search(text):  # 同時有實跑失敗:主類算真紅,另註也待裁
                it["also"] = "待裁"
                return "TRUE"
            return "DECIDE"
        if INT_RX.search(text):
            return "INT"
        if ENV_RX.search(text) or (peer is not None and peer.search(text)):
            return "ENV"
        return "TRUE" if lamp == "r" else "YEL"
    if "S6" in rules:
        return "NOEV"
    if "S4" in rules:
        return "DECIDE"
    return "CHG"


def cause_of(it) -> str:
    s = re.split(r"[;;::(]", it["detail"] or it["title"], maxsplit=1)[0]
    s = re.sub(r"值 [^·]+", "值 *", s)
    s = re.sub(r"\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?", "<時>", s)
    s = re.sub(r"v\d{4}", "v#", s)
    s = re.sub(r"\b[0-9a-f]{7,}\b", "#", s)
    s = re.sub(r"\d+(\.\d+)?", "#", s)
    return cut(s, 48)


def stage2(items, budget=300, peer=None):
    """分流 → 併組 → 排序 → 超量逐級摺疊。回 (行, 層級, 統計);每個項目寫上 cls 與 disp。"""
    sel = [it for it in items if it["selected"]]
    for it in sel:
        it["cls"] = classify(it, peer)
        it["cause"] = cause_of(it)
    for it in items:
        if not it["selected"]:
            it["cls"] = ""
            it["also"] = ""
            it["disp"] = "只計數:未入選|%s/%s" % (it["section"], LN[it["lamp"]])

    def build(fold_min, collapse, per_class):
        lines, stat = [], {"listed": 0, "grouped": 0, "counted": 0, "groups": 0}
        gno = 0
        for cls, cname, _ in CLASSES:
            mem = [it for it in sel if it["cls"] == cls]
            if not mem:
                continue
            if per_class:
                for it in mem:
                    it["disp"] = "只計數:%s" % cname
                stat["counted"] += len(mem)
                lines.append("[%s] ×%d(各系統各區塊合計;細項在矩陣與完整去向冊)" % (cname, len(mem)))
                continue
            if cls in collapse:
                buckets = {}
                for it in mem:
                    buckets.setdefault((it["system"], it["section"]), []).append(it)
                for (sysn, sec), b in sorted(buckets.items(), key=lambda kv: (-len(kv[1]), kv[0])):
                    for it in b:
                        it["disp"] = "只計數:%s|%s/%s" % (cname, sysn, sec)
                    stat["counted"] += len(b)
                    lines.append("[%s] %s/%s ×%d(細項在矩陣與完整去向冊)" % (cname, sysn, sec, len(b)))
                continue
            groups = {}
            for it in mem:
                groups.setdefault((it["system"], it["section"], it["cause"]), []).append(it)
            for (sysn, sec, cause), g in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
                if len(g) >= fold_min:
                    gno += 1
                    gid = "G%03d" % gno
                    for it in g:
                        it["disp"] = "併組:%s" % gid
                    stat["grouped"] += len(g)
                    stat["groups"] += 1
                    ex = ", ".join(cut(it["id"] or it["title"], 40) for it in g[:3])
                    lines.append("[%s] %s %s/%s ×%d · %s · 例 %s%s" % (cname, gid, sysn, sec, len(g), cause, ex, " …" if len(g) > 3 else ""))
                else:
                    for it in g:
                        it["disp"] = "逐列"
                        stat["listed"] += 1
                        was = ("(上一輪%s)" % LN.get(it.get("was"), "沒有")) if "S3" in it["rules"] and not it.get("gone") else ""
                        tag = "" if cls in ("TRUE", "YEL") else "[%s]" % LN[it["lamp"]]
                        lines.append("[%s]%s %s/%s · %s%s · %s%s%s" % (cname, tag, it["system"], it["section"], cut(it["title"], 70), (" " + it["ver"]) if it["ver"] else "",
                                                                   cut(it["detail"], 130), was, (" · 也屬 " + it["also"]) if it.get("also") else ""))
        return lines, stat
    order = [c for c, _, _ in reversed(CLASSES)]
    plans = [(3, set(), False), (2, set(), False)] + [(2, set(order[: i + 1]), False) for i in range(len(order))] + [(2, set(), True)]
    for level, (fm, col, pc) in enumerate(plans):
        lines, stat = build(fm, col, pc)
        if len(lines) <= budget or level == len(plans) - 1:
            return lines, level, stat


# ---------------- 對帳 · 卡片 · 回饋包 ----------------
def assemble(raw, source, prev, budget=300, peer=None):
    items, skipped = normalize(raw)
    n_now = len(items)
    items = stage1(items, prev)
    body, level, stat = stage2(items, max(8, budget - 14 - len({it["section"] for it in items})), peer)
    sel = [it for it in items if it["selected"]]
    uns = [it for it in items if not it["selected"]]
    by_cls = {c: sum(1 for it in sel if it["cls"] == c) for c, _, _ in CLASSES}
    sections = {}
    for it in items:
        d = sections.setdefault(it["section"], {"g": 0, "y": 0, "r": 0, "x": 0})
        d[it["lamp"]] += 1
    checks = {
        "應掃 = 已掃 + 略過": len(raw) == n_now + len(skipped),
        "入選 = 逐列 + 併組 + 只計數": len(sel) == stat["listed"] + stat["grouped"] + stat["counted"],
        "入選 = 各類別合計": len(sel) == sum(by_cls.values()),
        "卡片合計 = 矩陣列數": sum(sum(d.values()) for d in sections.values()) == len(items),
        "每個項目恰有一個去向": all(it.get("disp") for it in items) and len({it["key"] for it in items}) == len(items),
    }
    ok = all(checks.values())
    if not ok or by_cls["REG"] or by_cls["TRUE"]:
        lamp = "r"
    elif any(by_cls[c] for c in ("DECIDE", "ENV", "INT", "YEL", "NOEV")) or skipped:
        lamp = "y"
    else:
        lamp = "g"
    why = ("對帳不符:" + "、".join(k for k, v in checks.items() if not v)) if not ok else \
        (" · ".join("%s %d" % (CN[c], by_cls[c]) for c, _, _ in CLASSES if by_cls[c]) or "沒有入選項目")
    if by_cls["REG"]:
        nxt = "先看退步 %d 項(上一輪綠、這一輪不是),再處理真紅 %d 項。" % (by_cls["REG"], by_cls["TRUE"])
    elif by_cls["TRUE"]:
        nxt = "真紅 %d 項要 AI 出薄尾新版(先看併組最大的那幾組)。" % by_cls["TRUE"]
    elif by_cls["DECIDE"]:
        nxt = "有 %d 項等你裁,裁完再跑一次。" % by_cls["DECIDE"]
    elif by_cls["ENV"] or by_cls["INT"]:
        nxt = "環境 %d · 中斷 %d:先排環境、重跑,不修碼。" % (by_cls["ENV"], by_cls["INT"])
    elif by_cls["YEL"] or by_cls["NOEV"]:
        nxt = "沒有紅;黃 %d · 缺證據 %d 要補實測或收據。" % (by_cls["YEL"], by_cls["NOEV"])
    else:
        nxt = "沒有要 AI 處理的項目。"
    stamp = _dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
    P = ["# %s · %s · 來源 %s" % (ENGINE, stamp, source),
         "[判定] %s · %s" % ({"g": "GREEN", "y": "YELLOW", "r": "RED"}[lamp], why),
         "[三數] 應掃 %d · 已掃 %d · 略過 %d%s" % (len(raw), n_now, len(skipped), (":" + cut(";".join(skipped), 200)) if skipped else ""),
         "[對帳] %s · 入選 %d = 逐列 %d + 併組 %d(%d 組)+ 只計數 %d · 未入選 %d(綠 %d · 灰 %d)· 矩陣 %d 列(含不見 %d)· 摺疊層級 %d" % (
             "相符" if ok else "不符", len(sel), stat["listed"], stat["grouped"], stat["groups"], stat["counted"], len(uns),
             sum(1 for it in uns if it["lamp"] == "g"), sum(1 for it in uns if it["lamp"] == "x"), len(items), len(items) - n_now, level),
         "[卡片] " + " · ".join("%s %d" % (CN[c], by_cls[c]) for c, _, _ in CLASSES)]
    P += ["[區塊] %s:紅 %d · 黃 %d · 綠 %d · 灰 %d" % (s, d["r"], d["y"], d["g"], d["x"]) for s, d in sections.items()]
    P += body
    return {"items": items, "skipped": skipped, "lamp": lamp, "why": why, "next": nxt, "level": level, "stat": stat, "by_cls": by_cls,
            "sections": sections, "checks": checks, "ok": ok, "head": P, "stamp": stamp, "source": source, "n_raw": len(raw), "n_now": n_now,
            "prev": prev is not None}


def cards_of(res):
    out = []
    sel = [it for it in res["items"] if it["selected"]]
    for c, name, col in CLASSES:
        n = res["by_cls"][c]
        top = {}
        for it in sel:
            if it["cls"] == c:
                k = "%s/%s · %s" % (it["system"], it["section"], it["cause"])
                top[k] = top.get(k, 0) + 1
        if n:
            k, v = max(top.items(), key=lambda kv: kv[1])
            reason, lamp = ("%d 項各自不同,看矩陣" % n if v == 1 else "最大宗 %d:%s" % (v, cut(k, 34))), col
        else:
            reason, lamp = ("沒有上一輪可比" if c in ("REG", "CHG") and not res["prev"] else "沒有"), ("x" if c in ("REG", "CHG") and not res["prev"] else "g")
        out.append({"kind": "cls", "key": name, "lamp": lamp, "n": n, "label": name, "reason": reason})
    for s, d in res["sections"].items():
        out.append({"kind": "sec", "key": s, "lamp": worst([k for k in "ryg" if d[k]]), "n": sum(d.values()), "label": s,
                    "reason": "紅 %d · 黃 %d · 綠 %d · 灰 %d" % (d["r"], d["y"], d["g"], d["x"])})
    return out


# ---------------- 頁面(鎖定模板) ----------------
def template(via: Path):
    """回 (css 全文, 狀態說明, 燈)。css 與 token 都只從冊來;冊不在或雜湊不符就不套樣式並照實說。"""
    reg = via / "supportive modules" / "registry"
    lock = tail(reg, "VIA_UI_WorkPlatform_TemplateLock", ".json")
    if lock is None:
        return "", "模板鎖冊不在(頁面不套樣式)", "x"
    try:
        b = json.loads(lock.read_text(encoding="utf-8"))
        css = b["css"]
        if hashlib.sha256(css.encode("utf-8")).hexdigest() != b.get("css_sha256"):
            return "", "%s 的 css 與鎖的雜湊不符(頁面不套樣式)" % lock.name, "r"
        tf = b["tokens_from"]
        tb = reg / ("%s_%s.json" % (tf["family"], tf["pinned"]))
        if not tb.exists():
            return "", "釘住的 token 冊 %s 不在(頁面不套樣式)" % tb.name, "r"
        if hashlib.sha256(tb.read_bytes()).hexdigest() != tf.get("sha256"):
            return "", "token 冊 %s 與鎖的雜湊不符(頁面不套樣式)" % tb.name, "r"
        tokens = json.loads(tb.read_text(encoding="utf-8"))["tokens"]
        root = ":root{" + ";".join("--%s:%s" % (k, v) for k, v in tokens.items() if "<" not in str(v) and "}" not in str(v)) + "}"
        return root + "\n" + css, "%s · token %s" % (lock.stem, tb.stem), "g"
    except (OSError, ValueError, KeyError, TypeError) as e:
        return "", "模板讀不到(%s)" % type(e).__name__, "r"


JS = r"""(function(){var D=JSON.parse(document.getElementById('d').textContent),LN={g:'綠',y:'黃',r:'紅',x:'灰'},shown=200,cf=null;
function $(i){return document.getElementById(i)}function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function opts(id,col){var s={},o='<option value="">全部</option>';D.forEach(function(r){s[col===7?r[col].split('+')[0]:r[col]]=1});Object.keys(s).sort().forEach(function(k){if(k)o+='<option>'+esc(k)+'</option>'});$(id).innerHTML=o}
function pick(){var a=$('fs').value,b=$('fb').value,l=$('fl').value,c=$('fc').value,q=$('fq').value.toLowerCase();return D.filter(function(r){
return(!a||r[1]===a)&&(!b||r[2]===b)&&(!l||r[0]===l)&&(!c||r[7].split('+')[0]===c)&&(!q||r.join(' ').toLowerCase().indexOf(q)>=0)})}
function draw(){var a=pick(),h='';for(var i=0;i<Math.min(a.length,shown);i++){var r=a[i];h+='<tr><td class="l"><span class="lamp '+r[0]+'">'+LN[r[0]]+'</span></td><td class="k">'+esc(r[1])+'</td><td class="n">'+esc(r[2])+'</td><td>'+esc(r[3])+'</td><td class="mono n">'+esc(r[4])+'</td><td>'+esc(r[5])+'</td><td class="mono n">'+esc(r[6])+'</td><td class="n">'+esc(r[7])+'</td><td class="n">'+esc(r[8])+'</td></tr>'}
$('tb').innerHTML=h||'<tr><td class="l"><span class="lamp x">灰</span></td><td colspan="8">沒有符合的列</td></tr>';$('cnt').textContent='符合 '+a.length+' / 共 '+D.length+' 列,顯示 '+Math.min(a.length,shown);
$('more').hidden=a.length<=shown}
opts('fs',1);opts('fb',2);opts('fc',7);['fs','fb','fl','fc'].forEach(function(i){$(i).onchange=function(){shown=200;draw()}});$('fq').oninput=function(){shown=200;draw()};
$('more').onclick=function(){shown+=400;draw()};$('clr').onclick=function(){['fs','fb','fl','fc','fq'].forEach(function(i){$(i).value=''});press(null);shown=200;draw()};
function press(b){[].forEach.call(document.querySelectorAll('.kc'),function(k){k.setAttribute('aria-pressed',k===b?'true':'false')})}
[].forEach.call(document.querySelectorAll('.kc'),function(k){k.onclick=function(){var on=k.getAttribute('aria-pressed')==='true';['fs','fb','fl','fc','fq'].forEach(function(i){$(i).value=''});
if(on){press(null)}else{press(k);$(k.dataset.kind==='cls'?'fc':'fb').value=k.dataset.key}shown=200;draw();$('mx').scrollIntoView({block:'nearest'})}});
$('cp').onclick=function(){var t=$('pk').textContent;function done(){$('cp').textContent='已複製'}if(navigator.clipboard){navigator.clipboard.writeText(t).then(done,sel)}else{sel()}
function sel(){var r=document.createRange();r.selectNodeContents($('pk'));var s=getSelection();s.removeAllRanges();s.addRange(r)}};draw()})();"""


def render(res, cards, pack, css, tpl_note, accel) -> str:
    data = [[it["lamp"], it["system"], it["section"], it["title"], it["ver"], cut(it["detail"], 260), it["at"], CN.get(it["cls"], "未入選") + (("+" + it["also"]) if it.get("also") else ""), it["disp"]] for it in res["items"]]
    order = {n: i for i, (_, n, _) in enumerate(CLASSES)}
    data.sort(key=lambda r: (order.get(r[7].split("+")[0], 99), SEV[r[0]], r[1], r[2], r[3]))
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")

    def card(c):
        return ('<button type="button" class="kc" aria-pressed="false" data-kind="%s" data-key="%s"><span class="kl"><span class="lamp %s">%s</span>%s</span>'
                '<span class="kn">%d</span><span class="kr">%s</span></button>') % (c["kind"], E(c["key"]), c["lamp"], LN[c["lamp"]], E(c["label"]), c["n"], E(c["reason"]))
    rules = "".join("<tr><td class=\"l\">%s</td><td>%s</td></tr>" % (E(k), E(v)) for k, v in RULES)
    chk = "".join('<tr><td class="l"><span class="lamp %s">%s</span></td><td>%s</td></tr>' % ("g" if v else "r", "綠" if v else "紅", E(k)) for k, v in res["checks"].items())
    return ('<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            "<title>VIA 工作平台 · 卡片與矩陣</title><style>%s</style></head><body><div class=\"wrap\">"
            '<header><div class="caps">VIA · 對內工作平台</div><h1>卡片摘要 · 矩陣明細 · AI 回饋</h1>'
            '<div class="note">%s · 來源 %s · 模板 %s · 加速器 %s · %s</div></header>'
            '<div class="verdict"><span class="lamp %s">%s</span><b>%s</b><span>%s</span></div>'
            '<h2>① 摘要(點卡片 = 篩矩陣)</h2><div class="cards">%s</div><div class="cards">%s</div>'
            '<section class="card"><h2>② 給 AI 的回饋包</h2><div class="note">應掃 %d · 已掃 %d · 略過 %d · 摺疊層級 %d · %d 行</div>'
            '<div class="bar"><button type="button" id="cp">複製回饋包</button></div><pre class="pack" id="pk">%s</pre></section>'
            '<section class="card" id="mx"><h2>③ 矩陣(每一列都有去向)</h2><div class="bar"><label>系統<select id="fs"></select></label><label>區塊<select id="fb"></select></label>'
            '<label>燈<select id="fl"><option value="">全部</option><option value="r">紅</option><option value="y">黃</option><option value="g">綠</option><option value="x">灰</option></select></label>'
            '<label>類別<select id="fc"></select></label><label>找字<input id="fq" type="search"></label><button type="button" id="clr">清除篩選</button></div>'
            '<div class="note num" id="cnt"></div><div class="box"><table><thead><tr><th class="l">燈</th><th>系統</th><th>區塊</th><th>項目</th><th>版本</th><th>狀態說明</th><th>時間</th><th>類別</th><th>去向</th></tr></thead>'
            '<tbody id="tb"></tbody></table></div><div class="bar"><button type="button" id="more" hidden>再顯示 400 列</button></div></section>'
            '<section class="card"><h2>④ 篩選機制與對帳</h2><div class="note">第一段六條任一命中就入選;第二段分流、併組、排序,超過行數只摺不丟。</div>'
            '<div class="scroll"><table><thead><tr><th class="l">條</th><th>第一段:入選條件</th></tr></thead><tbody>%s</tbody></table></div>'
            '<div class="scroll"><table><thead><tr><th class="l">燈</th><th>對帳</th></tr></thead><tbody>%s</tbody></table></div></section>'
            '</div><script type="application/json" id="d">%s</script><script>%s</script></body></html>') % (
        css, E(res["stamp"]), E(res["source"]), E(tpl_note), E(accel), E(ENGINE), res["lamp"], LN[res["lamp"]], E(res["why"]), E("NEXT: " + res["next"]),
        "".join(card(c) for c in cards if c["kind"] == "cls"), "".join(card(c) for c in cards if c["kind"] == "sec"),
        res["n_raw"], res["n_now"], len(res["skipped"]), res["level"], len(pack), E("\n".join(pack)), rules, chk, blob, JS)


# ---------------- 執行 ----------------
def peer_pattern(via: Path):
    """沿用 CGC_MDL259_AiVerbBridge 的環境判別式(有就加用;沒有就只用自帶的)。"""
    try:
        p = tail(via / "supportive modules" / "registry", "CGC_MDL259_AiVerbBridge", ".py")
        pat = getattr(load_py(p), "ENV_PAT", None) if p else None
        return (pat, "沿用 %s 的環境判別式" % p.stem) if pat is not None else (None, "自帶判別式")
    except Exception as e:
        return None, "自帶判別式(%s 載不到:%s)" % ("CGC_MDL259", type(e).__name__)


def write_out(out: Path, res, pack, page, slug):
    out.mkdir(parents=True, exist_ok=True)
    full = "\n".join(json.dumps({k: it.get(k) for k in ("key", "section", "system", "lamp", "title", "ver", "at", "detail", "rules", "cls", "disp")}, ensure_ascii=False)
                     for it in res["items"]) + "\n"
    sha = hashlib.sha256(full.encode("utf-8")).hexdigest()
    pack = pack + ["[完整] FEEDBACK_FULL_latest.jsonl · %d 列 · sha256 %s(每一列都有去向;包裡沒逐列的都在這)" % (len(res["items"]), sha[:16]),
                   "NEXT: " + res["next"]]
    (out / "FEEDBACK_FULL_latest.jsonl").write_text(full, encoding="utf-8")
    (out / "FEEDBACK_latest.txt").write_text("\n".join(pack) + "\n", encoding="utf-8")
    (out / "WORKPLATFORM_latest.html").write_text(page(pack), encoding="utf-8")
    rec = {"engine": ENGINE, "stamp": res["stamp"], "source": res["source"], "lamp": res["lamp"], "why": res["why"], "next": res["next"],
           "three": {"should": res["n_raw"], "done": res["n_now"], "skipped": res["skipped"]}, "stat": res["stat"], "level": res["level"],
           "by_class": {CN[c]: n for c, n in res["by_cls"].items()}, "sections": res["sections"], "checks": res["checks"], "pack_lines": len(pack), "full_sha256": sha}
    (out / "FEEDBACK_latest.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    if res["ok"]:  # 對帳相符才更新快照,免得壞的一輪變成下一輪的基準
        (out / ("FEEDBACK_SNAPSHOT_%s.json" % slug)).write_text(json.dumps({it["key"]: it["lamp"] for it in res["items"] if not it.get("gone")}, ensure_ascii=False), encoding="utf-8")
    with open(str(out / "feedback_ledger.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({k: rec[k] for k in ("engine", "stamp", "source", "lamp", "three", "stat", "level", "by_class", "full_sha256")}, ensure_ascii=False) + "\n")
    return pack


def run(via: Path, out: Path, src: str, budget: int, no_open: bool) -> int:
    print("[1/5] 讀項目 10%", flush=True)
    if src:
        doc = json.loads(Path(src).read_text(encoding="utf-8"))
        raw, source = (doc.get("items") or [], str(doc.get("source") or Path(src).name)) if isinstance(doc, dict) else (doc, Path(src).name)
    else:
        raw, source = from_localmonitor(via)
    slug = re.sub(r"[^\w.-]+", "_", source)[:60] or "default"
    snap = out / ("FEEDBACK_SNAPSHOT_%s.json" % slug)
    prev = None
    if snap.exists():
        try:
            prev = json.loads(snap.read_text(encoding="utf-8"))
        except ValueError:
            prev = None
    print("[2/5] 第一段與第二段 45%", flush=True)
    peer, peer_note = peer_pattern(via)
    res = assemble(raw, source, prev, budget, peer)
    print("[3/5] 模板 60%", flush=True)
    css, tpl_note, tpl_lamp = template(via)
    accel = accel_status()
    pack = res["head"] + ["[機制] 第一段六條任一命中入選 · 第二段分流→併組→排序→只摺不丟 · %s · 上一輪 %s · 模板 %s(%s)· 加速器 %s" % (
        peer_note, "有" if res["prev"] else "沒有(這一輪不比變動)", tpl_note, LN[tpl_lamp], accel)]
    if tpl_lamp == "r":
        res["lamp"] = "r"
        res["why"] = "模板鎖不符 · " + res["why"]
        pack[1] = "[判定] RED · " + res["why"]
    cards = cards_of(res)
    print("[4/5] 寫出 80%", flush=True)
    pack = write_out(out, res, pack, lambda p: render(res, cards, p, css, tpl_note, accel), slug)
    print("[5/5] 完成 100%", flush=True)
    for line in pack[:6] + pack[-2:]:
        print(line, flush=True)
    page = out / "WORKPLATFORM_latest.html"
    print("[U/I] %s" % page, flush=True)
    if not no_open and not os.environ.get("VIA_NO_OPEN"):
        try:
            import webbrowser
            webbrowser.open(page.resolve().as_uri())
        except Exception as e:
            print("[U/I] 開不起來(%s),請手動開上面那個檔" % type(e).__name__, flush=True)
    return {"g": 0, "y": 2, "r": 1}[res["lamp"]]


def selftest() -> int:
    fails = []

    def chk(name, cond, got=None):
        print("  [%s] %s%s" % ("過" if cond else "敗", name, "" if cond else " · 得到 %r" % (got,)), flush=True)
        if not cond:
            fails.append(name)
    raw = [{"section": "系統", "system": "VDF", "lamp": "RED", "id": "VDF", "title": "VDF 入口", "detail": "憲法 CONFLICT_OPEN · 衝突 3"},
           {"section": "系統", "system": "VCGC", "lamp": "r", "id": "VCGC", "title": "VCGC 入口", "detail": "實跑 rc 124 · 900 秒沒跑完"},
           {"section": "工具", "system": "VCGC", "lamp": "r", "id": "polars", "title": "polars", "detail": "ModuleNotFoundError: No module named polars"},
           {"section": "工具", "system": "VCGC", "lamp": "x", "id": "frame", "title": "frame", "detail": "檔在 · 沒有實測收據"},
           {"section": "工具", "system": "VCGC", "lamp": "x", "id": "opt", "title": "可選庫", "detail": "沒裝也照跑"},
           {"section": "工具", "system": "VCGC", "lamp": "g", "id": "<\u002fscript><b>x", "title": "<\u002fscript><b>x", "detail": "正常"},
           {"section": "模組引擎", "system": "VCGC", "lamp": "g", "id": "guard", "title": "via_conflict_guard timeout proxy", "detail": "已註冊"},
           {"section": "系統", "system": "VQG", "lamp": "r", "id": "VQG", "title": "VQG 入口", "detail": "實跑 rc 1 · 憲法 CONFLICT_OPEN"},
           "不是物件的一列"]
    raw += [{"section": "模組引擎", "system": "VRN", "lamp": "r", "id": "VIA-VRN-ENG%03d" % i, "title": "VRN_ENG%03d" % i, "ver": "v0100",
             "detail": "號冊有列但檔不在,也沒標退役 · 2026-10-%02d" % (i % 28 + 1)} for i in range(39)]
    raw += [{"section": "模組引擎", "system": "VDF", "lamp": "y", "id": "VIA-VDF-MDL%03d" % i, "title": "VDF_MDL%03d" % i, "detail": "檔案尾版 v%04d 未註冊" % (100 + i)} for i in range(60)]
    raw += [{"section": "模組引擎", "system": "VCGC", "lamp": "g", "id": "VIA-VCGC-MDL%04d" % i, "title": "CGC_MDL%03d" % i, "detail": "已註冊"} for i in range(400)]
    raw += [{"section": "參數", "system": "VCGC", "lamp": "y", "id": "p%d" % i, "title": "參數 %d" % i, "detail": "各自不同的原因 %s" % chr(0x4e00 + i * 7)} for i in range(30)]
    raw.append({"section": "參數", "system": "VCGC", "lamp": "y", "id": "p0", "title": "參數 0 重複鍵", "detail": "同鍵第二筆"})
    res = assemble(raw, "selftest", None, 300)
    it = {x["key"]: x for x in res["items"]}
    chk("對帳五條都相符", res["ok"], res["checks"])
    chk("三數:應掃 539 = 已掃 538 + 略過 1", (res["n_raw"], res["n_now"], len(res["skipped"])) == (539, 538, 1), (res["n_raw"], res["n_now"], res["skipped"]))
    chk("分流:待裁 / 中斷 / 環境 / 缺證據", (it["系統|VDF|VDF"]["cls"], it["系統|VCGC|VCGC"]["cls"], it["工具|VCGC|polars"]["cls"], it["工具|VCGC|frame"]["cls"]) == ("DECIDE", "INT", "ENV", "NOEV"))
    chk("名稱帶 conflict / timeout / proxy 的綠列不被誤選", not it["模組引擎|VCGC|guard"]["selected"])
    chk("實跑失敗又有衝突:主類真紅、另註待裁", it["系統|VQG|VQG"]["cls"] == "TRUE" and it["系統|VQG|VQG"]["also"] == "待裁")
    chk("沒證據字樣的灰與綠不入選但有去向", not it["工具|VCGC|opt"]["selected"] and it["工具|VCGC|opt"]["disp"].startswith("只計數:未入選"))
    chk("同因 39 支真紅併成一組(日期與編號不拆組)", res["by_cls"]["TRUE"] == 40 and len({x["disp"] for x in res["items"] if x["cls"] == "TRUE" and x["section"] == "模組引擎"}) == 1)
    chk("重複鍵各自保留", "參數|VCGC|p0#2" in it and len(it) == len(res["items"]))
    chk("卡片數字等於矩陣列數", sum(c["n"] for c in cards_of(res) if c["kind"] == "sec") == len(res["items"]) and sum(c["n"] for c in cards_of(res) if c["kind"] == "cls") == sum(1 for x in res["items"] if x["selected"]))
    chk("第一輪:退步與變動卡亮灰並說沒有上一輪", [c["lamp"] for c in cards_of(res) if c["key"] in ("退步", "變動")] == ["x", "x"])
    body = len(res["head"])
    chk("300 行預算內", body <= 300 and res["level"] == 0, (body, res["level"]))
    small = assemble(raw, "selftest", None, 30)
    chk("預算 30 行:摺疊層級上升、行數守住、對帳仍相符、沒有項目消失", small["level"] > 0 and len(small["head"]) <= 30 and small["ok"] and len(small["items"]) == len(res["items"]), (small["level"], len(small["head"])))
    chk("摺疊後高優先仍逐列或併組,低優先才只計數", it and all(not x["disp"].startswith("只計數") for x in small["items"] if x["cls"] in ("DECIDE", "INT", "ENV")), small["level"])
    tiny = assemble(raw, "selftest", None, 1)
    lines3, _, st3 = stage2(tiny["items"], 3)
    chk("預算小到極端:每類一行也不丟", tiny["ok"] and st3["counted"] == sum(tiny["by_cls"].values()) and len(lines3) == sum(1 for v in tiny["by_cls"].values() if v), (len(lines3), st3))
    prev = {x["key"]: x["lamp"] for x in res["items"]}
    prev["模組引擎|VCGC|VIA-VCGC-MDL9999"] = "g"            # 上一輪綠、這一輪不見
    prev["模組引擎|VDF|VIA-VDF-MDL000"] = "g"               # 上一輪綠、這一輪黃
    prev.pop("模組引擎|VCGC|VIA-VCGC-MDL0001")              # 這一輪新出現(綠)
    two = assemble(raw, "selftest", prev, 300)
    t = {x["key"]: x for x in two["items"]}
    chk("退步:綠變黃與綠後不見都抓到", two["by_cls"]["REG"] == 2 and t["模組引擎|VCGC|VIA-VCGC-MDL9999"]["gone"] and t["模組引擎|VDF|VIA-VDF-MDL000"]["cls"] == "REG", two["by_cls"])
    chk("新出現的綠歸變動、不見的列進矩陣", t["模組引擎|VCGC|VIA-VCGC-MDL0001"]["cls"] == "CHG" and len(two["items"]) == len(res["items"]) + 1 and two["ok"])
    chk("有退步時判定紅且 NEXT 先講退步", two["lamp"] == "r" and "退步" in two["next"])
    again = assemble(raw, "selftest", None, 300)
    chk("同輸入同結果(去掉時間行)", again["head"][1:] == res["head"][1:])
    tmp = Path(tempfile.mkdtemp(prefix="via_cmf_st_"))
    try:
        via = find_via()
        css, note, tl = template(via) if via else ("", "倉不在", "x")
        pack = write_out(tmp, res, list(res["head"]), lambda p: render(res, cards_of(res), p, css, note, accel_status()), "selftest")
        page = (tmp / "WORKPLATFORM_latest.html").read_text(encoding="utf-8")
        full = (tmp / "FEEDBACK_FULL_latest.jsonl").read_text(encoding="utf-8").splitlines()
        chk("完整去向冊一列一個項目、每列有去向", len(full) == len(res["items"]) and all(json.loads(x)["disp"] for x in full))
        chk("回饋包末行 NEXT、倒數第二行指向完整冊", pack[-1].startswith("NEXT:") and pack[-2].startswith("[完整]"))
        chk("頁面:資料裡的 </script> 不會破頁", page.count("</script>") == 2 and "<b>x" not in page.split('id="d">')[1].split("</script>")[0])
        chk("頁面:本檔不帶色值,樣式全來自鎖冊", (tl == "g" and "var(--lamp-green)" in page) or tl != "g", note)
        chk("模板鎖與 token 冊雜湊相符", tl == "g", note)
        chk("快照寫出供下一輪比", (tmp / "FEEDBACK_SNAPSHOT_selftest.json").exists())
        src = Path(__file__).read_text(encoding="utf-8")
        chk("引擎原始碼沒有色碼", not re.search(r"#[0-9a-fA-F]{6}\b", src.replace("\\u", "")))
    finally:
        import shutil
        shutil.rmtree(str(tmp), ignore_errors=True)
    print("[selftest] %s · %d 敗 · 加速器 %s" % ("GREEN" if not fails else "RED", len(fails), accel_status()), flush=True)
    return 0 if not fails else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    def opt(name):
        if name in args:
            i = args.index(name)
            return args[i + 1] if i + 1 < len(args) else ""
        return ""
    verb = args[0] if args and not args[0].startswith("-") else ("selftest" if "--selftest" in args else "run")
    if verb == "selftest":
        return selftest()
    if verb == "version":
        print("%s · %s" % (Path(__file__).name, ENGINE))
        return 0
    if verb == "spec":
        print(__doc__)
        return 0
    if verb != "run":
        print("動詞:run · selftest · spec · version")
        return 2
    via = find_via(opt("--root"))
    if via is None:
        print("[紅] 找不到 VIA 夾")
        return 3
    out = Path(opt("--out")) if opt("--out") else via / "VIA_Reports" / "vcgc"
    try:
        budget = int(opt("--budget") or 300)
    except ValueError:
        budget = 300
    return run(via, out, opt("--in"), budget, "--no-open" in args)


if __name__ == "__main__":
    sys.exit(main())
