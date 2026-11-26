#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL284_SSOTSchemaRegistry v0100 — VCGC 檢查 VIA_SSOT_Schema_Registry(共享 SSOT 冊索引);只檢查,不跑業務

操作員 2026-11-26:「將SSOT管理系統與現在整合抓近來使用 自動完成」「用VCGC節省TOKEN工具完成」。
來源:隔離分支 isolated/date-ticker-regex-ssot-20261126@e0eddce 的 VIA Schema Registry + 自適應介面 SSOT + 18 本知識冊,
  收進 supportive modules/ssot/knowledge/。冊名改 VIA_SSOT_Schema_Registry(主線已有同名 VIA_Schema_Registry_v0100 =
  資料表 schema drift 守門基線,CGC_MDL092 寫死讀取;用途不同 → 新家族,不蓋)。
自適應介面(VIA_Adaptive_Interface_SSOT):各系統只引用 schema_id@version 與「結構卡」,不內嵌對方邏輯;VCGC 只做檢查與閘門。
  本工具的結構卡 = 鎖冊上的省 Token 工具(VIA_ToolVersion_Lock 的 token 那一支)`read` 產出的骨架卡,指紋 = 它的 etag。
動詞(唯讀;不出網;不寫任何冊):
  check [--json]           冊上每筆實測:檔在不在 · JSON 能不能解析 · 檔內 schema_id / version 與冊上相同 · 相容模式合法 ·
                           結構卡指紋;另列知識夾裡沒登冊的 SSOT。燈:缺檔 / 解析不過 = 紅 · 對不上 / 未登 / 卡取不到 = 黃 · 全過 = 綠。
                           收據(只有代碼 · 版號 · 指紋 · 燈,不含冊內容)→ VIA_Reports/vcgc/ssot_registry/SSOT_REGISTRY_CHECK_latest.json
  card <schema_id[@ver]>   印那一本的結構卡(消費方式:取卡,不讀全文)
  list                     冊上 schema_id@version · 相容模式 · 路徑
  --selftest
冊上原本自報的 vcgc_checked 一律以 check 的收據為準(冊上不自報)。rc:綠 0 · 黃 2 · 紅 1。零 TA-Lib · 不設同意閘。
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

import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ENGINE = "CGC_MDL284_SSOTSchemaRegistry_v0100"
VERSION = "v0100"
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
KNOW_REL = Path("supportive modules") / "ssot" / "knowledge"
REG_GLOB = "VIA_SSOT_Schema_Registry_v[0-9][0-9][0-9][0-9].json"
OUT_REL = Path("VIA_Reports") / "vcgc" / "ssot_registry"
VERBS = ("check", "card", "list", "--selftest")
_RANK = {0: 0, 2: 1, 1: 2}


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def registry_path(via: Path = VIA):
    hits = sorted((via / KNOW_REL).glob(REG_GLOB), key=_vnum)
    return hits[-1] if hits else None


def token_tool(via: Path = VIA):
    """鎖冊上的省 Token 工具(VIA_ToolVersion_Lock 的 token.path,相對倉根)。"""
    try:
        lock = json.loads((via / "supportive modules" / "registry" / "VIA_ToolVersion_Lock_v0100.json").read_text(encoding="utf-8"))
        p = via.parent / lock["token"]["path"]
        return p if p.is_file() else None
    except (OSError, ValueError, KeyError, TypeError):
        return None


def card(path: Path, via: Path = VIA) -> dict:
    """結構卡 + 指紋:叫省 Token 工具 `read`(只讀;不回全文)。"""
    t = token_tool(via)
    if t is None:
        return {"ok": False, "why": "省 Token 工具不在(鎖冊 token.path)", "etag": None, "card": ""}
    try:
        r = subprocess.run([sys.executable, str(t), "read", str(path)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120, cwd=str(via.parent))
    except subprocess.TimeoutExpired:
        return {"ok": False, "why": "read 逾時", "etag": None, "card": ""}
    out = r.stdout or ""
    m = re.search(r"etag=([0-9a-f]{8,})", out)
    return {"ok": r.returncode == 0 and bool(m), "why": "" if m else "卡上沒有 etag", "etag": m.group(1) if m else None,
            "card": "\n".join(ln for ln in out.splitlines() if not ln.startswith("[token 帳]"))}


def worse(*rcs) -> int:
    return max((r if r in _RANK else 1 for r in rcs), key=lambda r: _RANK[r], default=0)


def check(via: Path = VIA, with_cards: bool = True) -> dict:
    reg = registry_path(via)
    if reg is None:
        return {"tool": ENGINE, "lamp": "RED", "rc": 1, "why": f"{KNOW_REL}/{REG_GLOB} 不在", "rows": [], "unregistered": []}
    try:
        book = json.loads(reg.read_text(encoding="utf-8"))
    except ValueError as e:
        return {"tool": ENGINE, "lamp": "RED", "rc": 1, "why": f"冊解析不過:{e}", "rows": [], "unregistered": []}
    modes = set((book.get("compatibility_modes") or {}).keys()) or {"backward", "forward", "full", "none"}
    rows, rc, seen = [], 0, set()
    for e in book.get("entries") or []:
        sid, ver, rel = e.get("schema_id"), e.get("version"), e.get("path") or ""
        p = via / rel
        row = {"schema_id": sid, "version": ver, "path": rel, "compatibility": e.get("compatibility")}
        if not p.is_file():
            row.update(lamp="RED", why="檔不在")
        else:
            seen.add(p.resolve())
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except ValueError as ex:
                row.update(lamp="RED", why=f"JSON 解析不過:{str(ex)[:80]}")
                d = None
            if d is not None:
                own = (d.get("schema_id"), d.get("version"))
                issues = []
                if own != (sid, ver):
                    issues.append(f"檔內是 {own[0]}@{own[1]}")
                if e.get("compatibility") not in modes:
                    issues.append(f"相容模式 {e.get('compatibility')!r} 不在 {sorted(modes)}")
                if with_cards:
                    c = card(p, via)
                    row["etag"] = c["etag"]
                    if not c["ok"]:
                        issues.append("結構卡取不到:" + c["why"])
                row.update(lamp="YELLOW" if issues else "GREEN", why=" · ".join(issues))
        rc = worse(rc, {"GREEN": 0, "YELLOW": 2}.get(row["lamp"], 1))
        rows.append(row)
    unreg, history = [], []
    reg_ver = {}                                      # schema_id → 冊上登的最大版號(數字)
    for e in book.get("entries") or []:
        m = re.match(r"v(\d{4})$", str(e.get("version") or ""))
        if m:
            reg_ver[e.get("schema_id")] = max(reg_ver.get(e.get("schema_id"), -1), int(m.group(1)))
    for p in sorted((via / KNOW_REL).rglob("*.json")):
        if p.resolve() in seen or p.resolve() == reg.resolve():
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            sid = d.get("schema_id") if isinstance(d, dict) else None
            fv = d.get("version") if isinstance(d, dict) else None
        except ValueError:
            sid, fv = None, None
        m = re.match(r"v(\d{4})$", str(fv or ""))
        item = {"path": str(p.relative_to(via)), "schema_id": sid, "version": fv}
        older = sid in reg_ver and m is not None and int(m.group(1)) < reg_ver[sid]
        (history if older else unreg).append(item)   # 只有「比冊上登的版號舊」才算歷史版;同號 / 更新 / 讀不到版號都算未登(PR #762 Codex P2)
    if unreg:
        rc = worse(rc, 2)
    lamp = {0: "GREEN", 2: "YELLOW", 1: "RED"}[rc]
    return {"tool": ENGINE, "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "registry": reg.name,
            "lamp": lamp, "rc": rc, "entries": len(rows), "green": sum(r["lamp"] == "GREEN" for r in rows),
            "rows": rows, "unregistered": unreg, "history": history}


def write_receipt(res: dict, via: Path = VIA) -> Path:
    out = via / OUT_REL
    out.mkdir(parents=True, exist_ok=True)
    keep = {k: v for k, v in res.items() if k != "rows"}
    keep["rows"] = [{k: r.get(k) for k in ("schema_id", "version", "compatibility", "lamp", "why", "etag")} for r in res.get("rows", [])]
    p = out / "SSOT_REGISTRY_CHECK_latest.json"
    p.write_text(json.dumps(keep, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[0] in ("-h", "help"):
        print(__doc__)
        return 0
    if a[0] in ("--selftest", "selftest"):
        return selftest()
    if a[0] == "list":
        reg = registry_path()
        book = json.loads(reg.read_text(encoding="utf-8")) if reg else {}
        for e in book.get("entries") or []:
            print(f"{e.get('schema_id')}@{e.get('version')} · {e.get('compatibility')} · {e.get('path')}")
        return 0 if reg else 1
    if a[0] == "card" and len(a) > 1:
        sid, _, ver = a[1].partition("@")
        reg = registry_path()
        book = json.loads(reg.read_text(encoding="utf-8")) if reg else {}
        hit = [e for e in book.get("entries") or [] if e.get("schema_id") == sid and (not ver or e.get("version") == ver)]
        if not hit:
            print(f"[RED] 冊上沒有 {a[1]}")
            return 1
        c = card(VIA / hit[-1]["path"])
        print(c["card"] or f"[黃] {c['why']}")
        return 0 if c["ok"] else 2
    if a[0] == "check":
        res = check()
        p = write_receipt(res)
        if "--json" in a:
            print(json.dumps({k: v for k, v in res.items()}, ensure_ascii=False, indent=1))
        else:
            for r in res["rows"]:
                print(f"  [{r['lamp']:<6}] {r['schema_id']}@{r['version']} · {r.get('compatibility')}" + (f" · {r['why']}" if r.get("why") else ""))
            for u in res["unregistered"]:
                print(f"  [YELLOW] 未登冊 · {u['path']}" + (f"(schema_id {u['schema_id']})" if u.get("schema_id") else ""))
            print(f"[{ENGINE}] {res['lamp']} · 冊 {res.get('registry')} · 登 {res['entries']} 本 · 綠 {res.get('green', 0)} · "
                  f"未登 {len(res['unregistered'])} · 歷史版 {len(res.get('history', []))} · 收據 {p.relative_to(VIA)}")
        return res["rc"]
    print(f"[RED] 不認得的動詞;動詞:{' · '.join(VERBS)}")
    return 1


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("① 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("② 省 Token 工具在(鎖冊 token.path)", token_tool() is not None)
    with tempfile.TemporaryDirectory() as td:
        via = Path(td) / "VIA"
        kn = via / KNOW_REL
        kn.mkdir(parents=True)
        (kn / "A_SSOT_v0100.json").write_text(json.dumps({"schema_id": "A_SSOT", "version": "v0100", "x": 1}), encoding="utf-8")
        (kn / "B_SSOT_v0101.json").write_text(json.dumps({"schema_id": "B_SSOT", "version": "v0101"}), encoding="utf-8")
        (kn / "C_SSOT_v0100.json").write_text("{bad json", encoding="utf-8")
        (kn / "D_SSOT_v0100.json").write_text(json.dumps({"schema_id": "D_SSOT", "version": "v0100"}), encoding="utf-8")
        (kn / "A_SSOT_v0099.json").write_text(json.dumps({"schema_id": "A_SSOT", "version": "v0099"}), encoding="utf-8")
        (kn / "A_SSOT_v0101.json").write_text(json.dumps({"schema_id": "A_SSOT", "version": "v0101"}), encoding="utf-8")
        reg = {"schema_id": "VIA_SSOT_Schema_Registry", "version": "v0100", "compatibility_modes": {"backward": "", "full": ""},
               "entries": [{"schema_id": "A_SSOT", "version": "v0100", "path": str(KNOW_REL / "A_SSOT_v0100.json"), "compatibility": "backward"},
                           {"schema_id": "B_SSOT", "version": "v0100", "path": str(KNOW_REL / "B_SSOT_v0101.json"), "compatibility": "backward"},
                           {"schema_id": "C_SSOT", "version": "v0100", "path": str(KNOW_REL / "C_SSOT_v0100.json"), "compatibility": "full"},
                           {"schema_id": "E_SSOT", "version": "v0100", "path": str(KNOW_REL / "E_SSOT_v0100.json"), "compatibility": "backward"}]}
        (kn / "VIA_SSOT_Schema_Registry_v0100.json").write_text(json.dumps(reg), encoding="utf-8")
        res = check(via, with_cards=False)
        lamps = {r["schema_id"]: r["lamp"] for r in res["rows"]}
        chk("③ 實測燈:A 綠 · B 檔內版號不同 = 黃 · C 解析不過 = 紅 · E 檔不在 = 紅 · 總燈紅 rc 1",
            lamps == {"A_SSOT": "GREEN", "B_SSOT": "YELLOW", "C_SSOT": "RED", "E_SSOT": "RED"} and res["rc"] == 1, lamps)
        chk("④ 未登冊:D 與 A 的新版 v0101(升版沒登冊照樣黃)· 只有比冊上舊的 A v0099 列歷史(Codex P2)",
            sorted((u["schema_id"], u["version"]) for u in res["unregistered"]) == [("A_SSOT", "v0101"), ("D_SSOT", "v0100")]
            and [(h["schema_id"], h["version"]) for h in res["history"]] == [("A_SSOT", "v0099")], (res["unregistered"], res["history"]))
        c = card(kn / "A_SSOT_v0100.json")
        chk("⑤ 結構卡經省 Token 工具 read:有 etag 指紋 · 卡上是結構不是全文", c["ok"] and c["etag"] and "schema_id" in c["card"], c)
        rp = write_receipt(check(via, with_cards=True), via)
        txt = rp.read_text(encoding="utf-8")
        chk("⑥ 收據只有代碼 · 版號 · 燈 · 指紋(不含冊內容 'x': 1)· 寫在暫存樹的 VIA_Reports", rp.is_file() and '"x"' not in txt
            and "A_SSOT" in txt and str(td) in str(rp), rp)
        chk("⑦ 找不到冊 = 紅 rc 1(不冒充綠)", check(Path(td) / "nowhere")["rc"] == 1)
    real = check(VIA, with_cards=False)
    chk("⑧ 真倉:冊在、能解析、至少登 10 本(收進主線的 VIA_SSOT_Schema_Registry)", real.get("registry") and real["entries"] >= 10, real.get("why"))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 檔面:第 3 行加速器標記 · 零 TA-Lib · 不設同意閘 · 不出網(無 requests / urllib / socket 匯入)",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE")
        and not re.search(r"^\s*(import|from)\s+(talib|requests|urllib|socket|http)", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    print(f"[selftest] {'GREEN' if all(ok) else 'RED'} · {sum(ok)}/{len(ok)} · {ENGINE}", flush=True)
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
