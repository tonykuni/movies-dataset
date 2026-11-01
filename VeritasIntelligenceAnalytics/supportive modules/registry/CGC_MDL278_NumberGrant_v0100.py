#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL278_NumberGrant v0100 — VCGC 核號:讀子系統(VDF · VRN-2)的核號請求 → 偵測三系統衝突 → 無衝突給號 → 三系統共用帳本

操作員政策(2026-10-29;2026-11-01 重申):「SSOT REGEX 同義字 邏輯 政策等由 VDF VRN 生成 · 經 VCGC 檢測後無衝突給予編號 · VDF VRN 自動擷取編號 ·
  若有衝突由我跟 AI 解決後 VCGC 檢測無誤後給予編號及更新修正內容 · 子系統自動識別編號及更新內容 · 三個系統的 SSOT REGEX 同義字 政策 邏輯的帳本是相同的」。
這是 VCGC 自己的模組(四系統對等,L123):只讀子系統的請求檔,不寫 VDF / VRN-2 的任何檔;子系統各自用自己的 SSOTSync apply 讀核發冊補號。
  check(預設,零寫):蒐集請求 → 列可核發 · 衝突 · 沿用帳本號。
  grant --apply:寫 supportive modules/registry/VCGC_NUMBER_GRANT_latest.json({grants:{鍵與暫編號: 核發號}, conflicts:[{key, with, why}]};
       內容沒變不重寫)+ 共用帳本 VIA_SharedSSOT_Ledger_v0100.jsonl(只增:新號 · 新擁有者)。
  請求檔:<VIA>/functional modules/*/contract/*_NUMBER_REQUEST_latest.json(VDF · VRN2 …)· <VIA>/VCGC/contract/(VCGC 自己提的)。
  衝突(不給號,等人判):① 同一別名在不同系統 / 帳本對到不同統一路徑 ② 同一個鍵兩邊指紋不同 ③ 子系統自報的自撞 ④ 已核發的號內容被改了
     (修好後重跑 grant;帳本號永不改、不回收)。
  同內容同類(正則原文 · 別名對照 · 參數值 · 無內容時用指紋)= 同一個號 → 三系統共用一本帳。號格式 VIA-<類>-####(類照請求的 vcgc_kind)。
零網路;不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib。
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

import datetime
import hashlib
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
ENGINE = "CGC_MDL278_NumberGrant"
TAG = "v" + Path(__file__).stem.rsplit("_v", 1)[-1]
GRANT_NAME = "VCGC_NUMBER_GRANT_latest.json"
LEDGER_NAME = "VIA_SharedSSOT_Ledger_v0100.jsonl"


def now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _sha16(s) -> str:
    return hashlib.sha256(str(s).encode("utf-8")).hexdigest()[:16]


def request_files(via: Path = VIA) -> list:
    out = sorted((via / "functional modules").glob("*/contract/*_NUMBER_REQUEST_latest.json"))
    out += sorted((via / "VCGC" / "contract").glob("*_NUMBER_REQUEST_latest.json")) if (via / "VCGC" / "contract").is_dir() else []
    return out


def _rel(f, via: Path) -> str:
    """VIA 樹內相對路徑(正斜線):核發冊入版控,不寫本機絕對路徑(工作站 / 容器同一份)。"""
    try:
        return Path(f).resolve().relative_to(Path(via).resolve()).as_posix()
    except ValueError:
        return Path(f).name


def load_requests(via: Path = VIA) -> list:
    reqs = []
    for f in request_files(via):
        try:
            r = json.loads(f.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            reqs.append({"from": f.parent.parent.name, "file": str(f), "error": "%s: %s" % (type(exc).__name__, exc), "items": []})
            continue
        items = list(r.get("ssot_items") or []) + list(r.get("program_items") or [])
        # 舊格式(只有 pending 號、沒有 ssot_items 的類 / 指紋 / 內容):不核號 — 沒內容就無從偵測衝突,也可能是引擎號(引擎歸 CGC_MDL237 編號冊)
        legacy = [] if items else [x for x in (r.get("pending") or []) if isinstance(x, str)]
        reqs.append({"from": r.get("from") or f.parent.parent.name, "file": str(f), "items": items, "legacy": legacy, "self_conflicts": r.get("self_conflicts") or []})
    return reqs


def content_id(it: dict) -> str:
    """同內容同類 = 同一個號:正則看原文 · 別名看「別名=統一路徑」· 參數看「名=值」· 冊 / 程式看(系統 · 鍵 · 指紋)。"""
    k, c = it.get("vcgc_kind") or it.get("kind") or "SSOT", it.get("content")
    if k == "RGX" and isinstance(c, str):
        return "RGX:" + _sha16(c)
    if k == "SYN" and isinstance(c, dict) and c.get("alias"):
        return "SYN:" + _sha16("%s=%s" % (str(c["alias"]).upper(), c.get("canonical")))
    if k == "PRMT" and isinstance(c, dict) and c.get("name"):
        return "PRMT:" + _sha16("%s=%s" % (c["name"], json.dumps(c.get("value"), ensure_ascii=False, sort_keys=True)))
    return "%s:%s:%s" % (k, it.get("_sys"), it.get("key")) if k in ("SSOT", "PLCY") else "%s:%s" % (k, it.get("fingerprint") or _sha16(it.get("key")))


LEDGER_BAD: list = []      # 上一次讀帳本時壞掉的列號(照實報,不默吞;帳本只增,不就地修)


def read_ledger(path: Path) -> list:
    rows = []
    LEDGER_BAD.clear()
    if path.is_file():
        for i, ln in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not ln.strip():
                continue
            try:
                rows.append(json.loads(ln))
            except ValueError:
                LEDGER_BAD.append(i)
    return rows


def plan(via: Path = VIA, ledger_path: Path | None = None) -> dict:
    ledger_path = Path(ledger_path or (HERE / LEDGER_NAME))
    led = read_ledger(ledger_path)
    by_cid, by_key, used = {}, {}, {}
    for r in led:
        if r.get("cid") and r.get("no"):
            by_cid.setdefault(r["cid"], r["no"])
        for o in r.get("owners") or []:
            by_key[(o.get("system"), o.get("key"))] = {"no": r["no"], "cid": r.get("cid")}
        m = re.match(r"VIA-([A-Z]+)-(\d{4,})$", str(r.get("no") or ""))
        if m:
            used[m.group(1)] = max(used.get(m.group(1), 0), int(m.group(2)))
    syn_led = {}
    for r in led:
        c = r.get("content")
        if r.get("kind") == "SYN" and isinstance(c, dict) and c.get("alias"):
            syn_led.setdefault(str(c["alias"]).upper(), (c.get("canonical"), r["no"]))
    reqs = load_requests(via)
    items = []
    for rq in reqs:
        for it in rq["items"]:
            if not isinstance(it, dict) or not it.get("key"):
                continue
            it = dict(it, _sys=rq["from"])
            it["_cid"] = content_id(it)
            items.append(it)
    conflicts, bad = [], set()

    def conflict(it, with_, why):
        conflicts.append({"key": it["key"], "system": it["_sys"], "proposed_no": it.get("proposed_no"), "with": with_, "why": why})
        bad.add((it["_sys"], it["key"]))
    syn_now = {}
    for it in items:
        c = it.get("content")
        if (it.get("vcgc_kind") or it.get("kind")) == "SYN" and isinstance(c, dict) and c.get("alias"):
            a = str(c["alias"]).upper()
            if a in syn_led and syn_led[a][0] != c.get("canonical"):
                conflict(it, "帳本 %s" % syn_led[a][1], "別名 %s 帳本是 %s,這裡是 %s" % (a, syn_led[a][0], c.get("canonical")))
            syn_now.setdefault(a, []).append(it)
    for a, its in syn_now.items():
        cans = {i["content"].get("canonical") for i in its}
        if len(cans) > 1:
            for i in its:
                others = sorted({"%s:%s" % (j["_sys"], j["content"].get("canonical")) for j in its if j is not i})
                conflict(i, " / ".join(others), "同一別名 %s 對到不同統一路徑 %s" % (a, " / ".join(sorted(map(str, cans)))))
    keymap = {}
    for it in items:
        keymap.setdefault(it["key"], []).append(it)
    for k, its in keymap.items():
        fps = {i.get("fingerprint") for i in its}
        if len({i["_sys"] for i in its}) > 1 and len(fps) > 1:
            for i in its:
                conflict(i, " / ".join(sorted({j["_sys"] for j in its if j is not i})), "同一個鍵兩邊內容(指紋)不同")
    for rq in reqs:
        for sc in rq.get("self_conflicts") or []:
            it = next((i for i in items if i["_sys"] == rq["from"] and i["key"] == sc.get("key")), None)
            if it:
                conflict(it, rq["from"] + "(自撞)", sc.get("why") or "子系統自報自撞")
    for it in items:
        prev = by_key.get((it["_sys"], it["key"]))
        if prev and prev.get("cid") and prev["cid"] != it["_cid"] and (it["_sys"], it["key"]) not in bad:
            conflict(it, "帳本 %s" % prev["no"], "已核發 %s 的內容改了 → 待人判(沿用 %s 或改提新鍵)" % (prev["no"], prev["no"]))
    grants, new_rows, reused = {}, [], 0
    new_cid = {}
    for it in sorted(items, key=lambda x: (x["_sys"], x["key"])):
        if (it["_sys"], it["key"]) in bad:
            continue
        prev = by_key.get((it["_sys"], it["key"]))
        no = (prev or {}).get("no") or by_cid.get(it["_cid"]) or new_cid.get(it["_cid"])
        if no:
            reused += 1 if (prev or by_cid.get(it["_cid"])) else 0
        else:
            kind = it.get("vcgc_kind") or "SSOT"
            used[kind] = used.get(kind, 0) + 1
            no = "VIA-%s-%04d" % (kind, used[kind])
            new_cid[it["_cid"]] = no
        grants[it["key"]] = no
        if it.get("proposed_no"):
            grants[it["proposed_no"]] = no
        if not prev:
            new_rows.append({"no": no, "cid": it["_cid"], "kind": it.get("vcgc_kind"), "content": it.get("content"), "owners": [
                {"system": it["_sys"], "key": it["key"], "proposed_no": it.get("proposed_no"), "src": it.get("src")}], "granted_at": now(), "by": "%s %s" % (ENGINE, TAG)})
    return {"requests": [{"from": r["from"], "file": r["file"], "items": len(r["items"]), "legacy": len(r.get("legacy") or []), "error": r.get("error")} for r in reqs],
            "items": len(items),
            "grants": grants, "conflicts": conflicts, "new_rows": new_rows, "reused": reused, "ledger": str(ledger_path), "ledger_rows": len(led)}


def grant(via: Path = VIA, apply: bool = False, grant_path: Path | None = None, ledger_path: Path | None = None) -> dict:
    p = plan(via, ledger_path)
    gp = Path(grant_path or (HERE / GRANT_NAME))
    old = {}
    if gp.is_file():
        try:
            old = json.loads(gp.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            old = {}
    merged = dict(old.get("grants") or {})
    for r in read_ledger(Path(p["ledger"])):                 # 核發冊可由共用帳本重建(帳本 = 正本;請求檔只放未核號的)
        for o in r.get("owners") or []:
            for k in (o.get("key"), o.get("proposed_no")):
                if k and r.get("no"):
                    merged[k] = r["no"]
    merged.update(p["grants"])
    srcs = sorted(_rel(r["file"], via) for r in p["requests"])
    body = {"grants": dict(sorted(merged.items())), "conflicts": p["conflicts"]}
    changed = (body["grants"] != (old.get("grants") or {}) or body["conflicts"] != (old.get("conflicts") or [])
               or srcs != (old.get("sources") or []))
    lamp = "YELLOW" if (p["conflicts"] or LEDGER_BAD or any(r.get("legacy") or r.get("error") for r in p["requests"])) else "GREEN"
    if apply:
        if changed:
            gp.parent.mkdir(parents=True, exist_ok=True)
            gp.write_text(json.dumps(dict({"schema": "VIA.VCGC.NumberGrant.v1", "engine": "%s %s" % (ENGINE, TAG), "ts": now(),
                                           "rule": "VCGC 偵測三系統衝突後核發;同內容同類同一個號(共用帳本 %s);號永不改、不回收;conflicts 修好後重跑" % LEDGER_NAME,
                                           "sources": srcs}, **body), ensure_ascii=False, indent=1), encoding="utf-8")
        if p["new_rows"]:
            lp = Path(p["ledger"])
            with open(lp, "a", encoding="utf-8") as fh:
                for r in p["new_rows"]:
                    fh.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    line = "[VCGC 核號] %s · 請求 %d 份(%s)· 條目 %d · 給號 %d(沿用 %d · 新號 %d)· 衝突 %d · 帳本 %d → %d 列%s · %s" % (
        lamp, len(p["requests"]), " · ".join("%s %d%s%s" % (r["from"], r["items"], " · 舊格式 %d 號不核(待升 SSOTSync 格式)" % r["legacy"] if r.get("legacy") else "",
                                                       " · 讀不到 %s" % r["error"] if r.get("error") else "") for r in p["requests"]) or "無", p["items"],
        len({k for k in p["grants"] if not re.match(r"^[A-Z0-9]+-[A-Z]+-\d{4}$", k)}), p["reused"], len({r["no"] for r in p["new_rows"]}),
        len(p["conflicts"]), p["ledger_rows"], p["ledger_rows"] + (len(p["new_rows"]) if apply else 0),
        (" · 帳本壞列 %s(不就地修,待人判)" % LEDGER_BAD[:5]) if LEDGER_BAD else "",
        ("寫入核發冊" if changed else "核發冊不變") if apply else "乾跑(--apply 才寫)")
    return dict(p, lamp=lamp, changed=changed, applied=apply, grant_file=str(gp), line=line)


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    verb = a[0] if a and not a[0].startswith("--") else "check"
    if verb not in ("check", "grant"):
        print("用法:python %s check | grant [--apply] [--json] · --selftest" % Path(__file__).name)
        return 2
    r = grant(apply=(verb == "grant" and "--apply" in a))
    if "--json" in a:
        print(json.dumps({k: v for k, v in r.items() if k != "new_rows"}, ensure_ascii=False, indent=1, default=str))
    else:
        print(r["line"])
        for c in r["conflicts"][:20]:
            print("  [衝突] %s · %s · 對 %s · %s" % (c["system"], c["key"], c["with"], c["why"]))
    return 0


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print("=== %s %s · 自測(兩系統請求 → 衝突 → 給號 → 帳本 → 再跑不改號)===" % (ENGINE, TAG))
    tmp = Path(tempfile.mkdtemp(prefix="vcgc_ng278_"))
    try:
        via = tmp / "VIA"
        reg = via / "supportive modules" / "registry"
        reg.mkdir(parents=True)

        def req(sys_, folder, items, self_c=None):
            d = via / "functional modules" / folder / "contract"
            d.mkdir(parents=True, exist_ok=True)
            (d / ("%s_NUMBER_REQUEST_latest.json" % folder)).write_text(json.dumps({"from": sys_, "ssot_items": items, "self_conflicts": self_c or []},
                                                                                     ensure_ascii=False), encoding="utf-8")
        rx = {"kind": "REGEX", "vcgc_kind": "RGX", "content": "^[1-9]\\d{3}$", "fingerprint": "f1"}
        req("VDF", "VDF", [dict(rx, key="VDF:RGX:a", proposed_no="VDF-RGX-0001"),
                           {"key": "VDF:SYN:START_DATE", "kind": "SYN", "vcgc_kind": "SYN", "content": {"alias": "START_DATE", "canonical": "time.start_date"},
                            "proposed_no": "VDF-SYN-0001", "fingerprint": "s1"},
                           {"key": "VDF:SYN:TIMEOUT", "kind": "SYN", "vcgc_kind": "SYN", "content": {"alias": "TIMEOUT", "canonical": "fetch.timeout_s"},
                            "proposed_no": "VDF-SYN-0002", "fingerprint": "s2"},
                           {"key": "VDF:SSOT:VDF_X_SSOT", "kind": "SSOT", "vcgc_kind": "SSOT", "proposed_no": "VDF-SSOT-0001", "fingerprint": "b1"}])
        req("VRN-2", "VRN2", [dict(rx, key="REGEX|ticker", proposed_no="VRN2-REGEX-0003"),
                              {"key": "SYN|timeout", "kind": "SYN", "vcgc_kind": "SYN", "content": {"alias": "timeout", "canonical": "http.timeout"},
                               "proposed_no": "VRN2-SYN-0001", "fingerprint": "s9"}])
        r = grant(via, apply=True, grant_path=reg / GRANT_NAME, ledger_path=reg / LEDGER_NAME)
        g = r["grants"]
        chk("① 同一條正則(VDF 與 VRN-2 都提)= 同一個號 %s(三系統共用帳本)· 鍵與暫編號都對得到" % g.get("VDF:RGX:a"),
            g.get("VDF:RGX:a") and g.get("VDF:RGX:a") == g.get("REGEX|ticker") == g.get("VDF-RGX-0001") == g.get("VRN2-REGEX-0003"))
        ck = {(c["system"], c["key"]) for c in r["conflicts"]}
        chk("② 衝突:同一別名 TIMEOUT 在 VDF 對 fetch.timeout_s、VRN-2 對 http.timeout → 兩邊都不給號、列待人判(含對方)",
            ("VDF", "VDF:SYN:TIMEOUT") in ck and ("VRN-2", "SYN|timeout") in ck and "VDF:SYN:TIMEOUT" not in g, r["conflicts"])
        chk("③ 沒衝突的照給:START_DATE · VDF 自己的冊(號格式 VIA-<類>-####)", re.match(r"VIA-SYN-\d{4}$", g.get("VDF:SYN:START_DATE") or "")
            and re.match(r"VIA-SSOT-\d{4}$", g.get("VDF:SSOT:VDF_X_SSOT") or ""))
        gf = json.loads((reg / GRANT_NAME).read_text(encoding="utf-8"))
        led = read_ledger(reg / LEDGER_NAME)
        rx_row = next(x for x in led if x["no"] == g["VDF:RGX:a"])
        chk("④ 核發冊格式同 VRN-2 apply 讀法({grants, conflicts})· 帳本每個擁有者一列(同內容的 VDF / VRN-2 兩列共用同一個號)", isinstance(gf.get("grants"), dict)
            and isinstance(gf.get("conflicts"), list) and len({x["no"] for x in led}) == len(led) - 1 and len([x for x in led if x["no"] == rx_row["no"]]) == 2)
        mt = (reg / GRANT_NAME).stat().st_mtime_ns
        r2 = grant(via, apply=True, grant_path=reg / GRANT_NAME, ledger_path=reg / LEDGER_NAME)
        chk("⑤ 再跑一次:號不變 · 帳本不加 · 核發冊內容沒變不重寫", r2["grants"] == g and not r2["new_rows"] and not r2["changed"] and (reg / GRANT_NAME).stat().st_mtime_ns == mt)
        req("VRN-2", "VRN2", [dict(rx, key="REGEX|ticker", proposed_no="VRN2-REGEX-0003"),
                              {"key": "SYN|timeout", "kind": "SYN", "vcgc_kind": "SYN", "content": {"alias": "timeout", "canonical": "fetch.timeout_s"},
                               "proposed_no": "VRN2-SYN-0001", "fingerprint": "s9b"}])
        r3 = grant(via, apply=True, grant_path=reg / GRANT_NAME, ledger_path=reg / LEDGER_NAME)
        chk("⑥ 人 + AI 把 VRN-2 的別名改成同一個統一路徑 → 衝突解除 · 兩邊拿到同一個號 %s" % r3["grants"].get("VDF:SYN:TIMEOUT"),
            not r3["conflicts"] and r3["grants"].get("VDF:SYN:TIMEOUT") == r3["grants"].get("SYN|timeout") and r3["grants"].get("VDF:SYN:TIMEOUT"))
        req("VDF", "VDF", [{"key": "VDF:SYN:START_DATE", "kind": "SYN", "vcgc_kind": "SYN", "content": {"alias": "START_DATE", "canonical": "time.begin"},
                            "proposed_no": "VDF-SYN-0001", "fingerprint": "s1b"}])
        r4 = grant(via, apply=False, grant_path=reg / GRANT_NAME, ledger_path=reg / LEDGER_NAME)
        chk("⑦ 已核發的內容改了(START_DATE → time.begin)→ 衝突待人判(帳本號不改、不回收)· 乾跑零寫",
            any(c["key"] == "VDF:SYN:START_DATE" for c in r4["conflicts"]) and not r4["applied"])
        (reg / GRANT_NAME).unlink()
        for q in (via / "functional modules").glob("*/contract/*_NUMBER_REQUEST_latest.json"):
            q.unlink()
        r6 = grant(via, apply=True, grant_path=reg / GRANT_NAME, ledger_path=reg / LEDGER_NAME)
        g6 = json.loads((reg / GRANT_NAME).read_text(encoding="utf-8"))
        chk("⑦a 核發冊刪了、請求都已核號(空)→ 由共用帳本重建,號一個不少 · 來源記相對路徑(不寫本機絕對路徑)",
            g6["grants"].get("VDF:SYN:TIMEOUT") == r3["grants"].get("VDF:SYN:TIMEOUT") and g6["grants"].get("VRN2-REGEX-0003") == g.get("VRN2-REGEX-0003")
            and not any(str(x).startswith(("/", "\\")) or ":" in str(x)[:3] for x in g6.get("sources") or []) and r6["changed"], g6.get("sources"))
        (via / "functional modules" / "VRN" / "contract").mkdir(parents=True, exist_ok=True)
        (via / "functional modules" / "VRN" / "contract" / "VRN_NUMBER_REQUEST_latest.json").write_text(
            json.dumps({"from": "VRN", "pending": ["VRN-E-0001", "VRN-B-0002"]}), encoding="utf-8")
        r5 = grant(via, apply=False, grant_path=reg / GRANT_NAME, ledger_path=reg / LEDGER_NAME)
        chk("⑦b 舊格式請求(只有 pending 號、沒內容)→ 不核號 · 黃燈 · 一行寫明「舊格式 2 號不核」",
            "VRN-E-0001" not in r5["grants"] and r5["lamp"] == "YELLOW" and "舊格式 2 號不核" in r5["line"], r5["line"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    writes = re.findall(r"(\w+)\.write_text\(|open\((\w+), \"a\"", body)
    chk("⑧ VCGC 自己的模組:寫檔點只有核發冊(gp)與共用帳本(lp)· 子系統的請求檔只讀 · 加速器橋在 · 零網路 · 同意閘不讀不寫 · %s" % writes,
        sorted(w[0] or w[1] for w in writes) == ["gp", "lp"] and "VIA:ACCEL-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+(requests|httpx|urllib\.request|VDF_|VRN_)", src, re.M) and "CONSENT" not in body)
    print("[計] %s_%s 自測 %d/%d · %s" % (ENGINE, TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
