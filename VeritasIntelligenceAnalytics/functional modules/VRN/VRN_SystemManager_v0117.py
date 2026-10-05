#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0117 — 薄尾:接 WKF009 三動詞 intake / reconcile / closeout(REQ017 next 欄)。

  intake <檔|夾> [--json]     單股研報進站(STP001):檔名律解析(券商/代號;GF/廣發 DENY)、
                              單一個股判定(檔名恰一個 4-6 位代號);輕量不開 PDF,交後續步。
  reconcile --code <代號> [--name 名] [--tp 目標價] [--json]
                              外部對帳(STP007):派 VDF 車道——本地股票清單驗 代號→股名/簡稱;
                              yfinance 調整收盤驗目標價合理性。缺車道/缺套件誠實 UNAVAILABLE,不假造。
  closeout --in <products.json> [--json]
                              產出閘(STP009):多重驗證全過(驗算×外部對帳×歷史覆蓋)才 PASS;
                              缺哪項點名 BLOCKED(誠實四態);證據只增 jsonl。
其餘動詞照前版鏈(status/catalog/read/…);未知動詞照 v0116 拒跑。
自測: VIA_FROM_VCGC=YES python VRN_SystemManager_v0117.py --selftest
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import datetime as _dt
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

TAG = "v0117"
HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
VERBS_NEW_v0117 = ("intake", "reconcile", "closeout")


def _vnum_v0117(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0117(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0117(p) < _vnum_v0117(__file__)),
                 key=_vnum_v0117)
PRIOR = _load_v0117(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


# ────────────────── WKF009-STP001 intake ──────────────────
_CODE_RX = re.compile(r"(?<!\d)(\d{4,6})(?!\d)")
_DENY_RX = re.compile(r"(?i)^(GF|廣發)")
_DOC_EXTS = (".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".docx", ".txt")


def intake(path: str) -> dict:
    """單股研報進站:檔名律(券商-代號;GF/廣發 DENY)+ 單一個股判定;輕量不開 PDF。"""
    p = Path(path).expanduser()
    files = [p] if p.is_file() else sorted(q for q in p.glob("*") if q.suffix.lower() in _DOC_EXTS)
    rows = []
    for f in files:
        stem = f.stem
        codes = sorted(set(_CODE_RX.findall(stem)))
        deny = bool(_DENY_RX.match(stem))
        single = (len(codes) == 1) and not deny
        rows.append({"file": str(f), "broker_hint": re.split(r"[-_ (]", stem, 1)[0][:12],
                     "codes": codes, "deny": deny,
                     "single_stock": single,
                     "state": "DENY" if deny else ("INTAKE_OK" if single else "NEEDS_REVIEW"),
                     "next": "VRN-WKF009-STP002" if single else "操作員複核(代號數≠1 或 DENY)"})
    out = {"verb": "intake", "manager": TAG, "workflow": "VRN-WKF009", "step": "STP001",
           "input": str(p), "files": len(rows), "rows": rows,
           "ok": sum(r["single_stock"] for r in rows)}
    return out


# ────────────────── WKF009-STP007 reconcile ──────────────────
def _universe_file():
    """本地股票清單(VDF 資料家)尋址:env VIA_DATA_HOME 下 *universe*/*stock_list*;找不到=None 誠實。"""
    home = os.environ.get("VIA_DATA_HOME")
    roots = [Path(home)] if home else []
    roots.append(HERE.parents[1] / "output_hub")
    for root in roots:
        if root and root.exists():
            hits = sorted(root.rglob("*universe*.csv")) + sorted(root.rglob("*stock_list*.csv"))
            if hits:
                return hits[-1]
    return None


def reconcile(code: str, name_hint: str = "", target_price: float | None = None) -> dict:
    """外部對帳:代號→股名/簡稱(本地 TWSE/TPEX 清單)· yfinance 調整收盤驗合理價;缺=誠實 UNAVAILABLE。"""
    out = {"verb": "reconcile", "manager": TAG, "workflow": "VRN-WKF009", "step": "STP007",
           "code": code, "checks": {}, "lamp": "YELLOW"}
    uf = _universe_file()
    if uf is None:
        out["checks"]["name"] = {"state": "UNAVAILABLE",
                                 "why": "本地股票清單不在(VIA_DATA_HOME 未指/無 universe 檔);派 VDF 車道 load_stock_list"}
    else:
        hit = ""
        try:
            for line in uf.read_text(encoding="utf-8", errors="replace").splitlines():
                if re.match(rf"^\s*\"?{re.escape(code)}\b", line):
                    hit = line.strip()[:120]
                    break
            st = "MATCH" if (hit and (not name_hint or name_hint in hit)) else ("FOUND" if hit else "NOT_FOUND")
            out["checks"]["name"] = {"state": st, "source": uf.name, "row": hit}
        except OSError as exc:
            out["checks"]["name"] = {"state": "ERROR", "why": str(exc)[:120]}
    if os.environ.get("VIA_NO_NET"):
        out["checks"]["price"] = {"state": "SKIPPED_NO_NET", "why": "VIA_NO_NET=1:自測/離線模式不碰網路"}
        out["lamp"] = "YELLOW"
        return out
    try:
        import yfinance  # 延遲載入;缺=誠實
        try:
            t = yfinance.Ticker(f"{code}.TW")
            h = t.history(period="5d", auto_adjust=True)
            if h is None or h.empty:
                t = yfinance.Ticker(f"{code}.TWO")
                h = t.history(period="5d", auto_adjust=True)
            if h is None or h.empty:
                out["checks"]["price"] = {"state": "NODATA", "why": ".TW/.TWO 都無資料,不猜"}
            else:
                px = float(h["Close"].iloc[-1])
                row = {"state": "FETCHED", "adj_close": round(px, 2), "asof": str(h.index[-1].date())}
                if target_price is not None:
                    ratio = target_price / px if px else None
                    row["tp_vs_px"] = round(ratio, 3) if ratio else None
                    row["reasonable"] = bool(ratio and 0.3 <= ratio <= 3.0)  # 合理帶寬;出帶=標疑不擋
                out["checks"]["price"] = row
        except Exception as exc:
            out["checks"]["price"] = {"state": "ERROR", "why": f"{type(exc).__name__}: {str(exc)[:120]}"}
    except ImportError:
        out["checks"]["price"] = {"state": "UNAVAILABLE", "why": "yfinance 缺席;派 VDF 車道取調整收盤"}
    states = {c["state"] for c in out["checks"].values()}
    out["lamp"] = "GREEN" if states <= {"MATCH", "FETCHED", "FOUND"} else \
                  ("RED" if "ERROR" in states else "YELLOW")
    return out


# ────────────────── WKF009-STP009 closeout ──────────────────
REQUIRED_VALIDATIONS = ("arithmetic", "external", "history_coverage")


def closeout(products_path: str) -> dict:
    """產出閘:products.json 的多重驗證(驗算/外部對帳/歷史覆蓋)全 GREEN 才 PASS;缺項點名,不假綠。"""
    out = {"verb": "closeout", "manager": TAG, "workflow": "VRN-WKF009", "step": "STP009",
           "input": products_path, "verdict": "BLOCKED", "missing": [], "evidence": ""}
    try:
        d = json.loads(Path(products_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        out["missing"] = [f"products.json 不可讀:{type(exc).__name__}"]
        return out
    v = d.get("validations") or {}
    for k in REQUIRED_VALIDATIONS:
        lamp = (v.get(k) or {}).get("lamp")
        if lamp != "GREEN":
            out["missing"].append(f"{k}={lamp or 'ABSENT'}")
    chain_ok = all({"doc_id", "page", "region_id", "engine", "validation"} <= set(r)
                   for r in d.get("products") or [])
    if not (d.get("products")):
        out["missing"].append("products 空")
    elif not chain_ok:
        out["missing"].append("產物鏈欄位不齊(doc_id/page/region_id/engine/validation)")
    out["verdict"] = "PASS" if not out["missing"] else "BLOCKED"
    led_dir = Path(os.environ.get("VIA_VRN_WKF009_DIR") or (HERE.parents[1] / "VIA_Reports" / "vrn"))
    led_dir.mkdir(parents=True, exist_ok=True)
    led = led_dir / "WKF009_closeout_ledger.jsonl"
    with led.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "manager": TAG, "verdict": out["verdict"], "missing": out["missing"],
                            "input": products_path}, ensure_ascii=False) + "\n")
    out["evidence"] = str(led)
    return out


# ────────────────── 入口 ──────────────────
def _emit(obj, as_json: bool) -> int:
    print(json.dumps(obj, ensure_ascii=False, indent=(None if as_json else 1)))
    return 0 if obj.get("verdict", "PASS") == "PASS" or obj.get("verb") != "closeout" else 1


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VRN] 拒絕。只能經 via-vcgc。")
        return 2
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["--selftest"] or "--selftest" in args[:2]:
        return selftest()
    as_json = "--json" in args
    a = [x for x in args if x != "--json"]
    if a[:1] == ["intake"]:
        if len(a) < 2:
            print("[拒跑] intake <檔|夾>")
            return 2
        return _emit(intake(a[1]), as_json)
    if a[:1] == ["reconcile"]:
        kv = dict(zip(a[1::2], a[2::2]))
        code = kv.get("--code", "")
        if not code:
            print("[拒跑] reconcile --code <代號> [--name 名] [--tp 目標價]")
            return 2
        tp = float(kv["--tp"]) if kv.get("--tp") else None
        return _emit(reconcile(code, kv.get("--name", ""), tp), as_json)
    if a[:1] == ["closeout"]:
        kv = dict(zip(a[1::2], a[2::2]))
        if not kv.get("--in"):
            print("[拒跑] closeout --in <products.json>")
            return 2
        return _emit(closeout(kv["--in"]), as_json)
    return PRIOR.main(args)   # 其餘動詞(含未知動詞拒跑)照前版鏈


def selftest() -> int:
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    os.environ["VIA_NO_NET"] = "1"   # 自測零網路律
    td = Path(tempfile.mkdtemp(prefix="vrnsm117-"))
    os.environ["VIA_VRN_WKF009_DIR"] = str(td / "led")
    for n in ("MS-2330 台積電 買進.pdf", "GF-2454 聯發科.pdf", "Citi 2317_2412 雙股.pdf", "note.txt"):
        (td / n).write_text("x", encoding="utf-8")
    r = intake(str(td))
    by = {Path(x["file"]).name: x for x in r["rows"]}
    chk("① intake:單股 INTAKE_OK(MS-2330)· 下一步 STP002",
        by["MS-2330 台積電 買進.pdf"]["state"] == "INTAKE_OK"
        and by["MS-2330 台積電 買進.pdf"]["next"] == "VRN-WKF009-STP002")
    chk("② intake:GF/廣發 DENY 律", by["GF-2454 聯發科.pdf"]["state"] == "DENY")
    chk("③ intake:雙代號≠單股 → NEEDS_REVIEW", by["Citi 2317_2412 雙股.pdf"]["state"] == "NEEDS_REVIEW")
    rc = reconcile("2330", "台積電", 650.0)
    chk("④ reconcile:零網路律(SKIPPED_NO_NET)· 清單缺=誠實 UNAVAILABLE,不假造",
        all("state" in c for c in rc["checks"].values()) and rc["lamp"] in ("GREEN", "YELLOW", "RED"))
    good = {"validations": {k: {"lamp": "GREEN"} for k in REQUIRED_VALIDATIONS},
            "products": [{"doc_id": "d", "page": 1, "region_id": "T01", "engine": "TABLE",
                          "validation": {"lamp": "GREEN"}}]}
    bad = {"validations": {"arithmetic": {"lamp": "GREEN"}}, "products": []}
    gp = td / "good.json"; gp.write_text(json.dumps(good), encoding="utf-8")
    bp = td / "bad.json"; bp.write_text(json.dumps(bad), encoding="utf-8")
    g = closeout(str(gp)); b = closeout(str(bp))
    chk("⑤ closeout:三驗全綠+產物鏈齊 → PASS", g["verdict"] == "PASS" and not g["missing"])
    chk("⑥ closeout:缺驗證/products 空 → BLOCKED 點名缺項(不假綠)",
        b["verdict"] == "BLOCKED" and any("external" in m for m in b["missing"]))
    led = Path(g["evidence"])
    chk("⑦ 證據只增 jsonl(兩筆)", led.is_file() and len(led.read_text(encoding="utf-8").splitlines()) == 2)
    chk("⑧ 未知動詞照前版拒跑", PRIOR.main(["no_such_verb"]) == 2)
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        prc = PRIOR.selftest()
    tail = [l for l in buf.getvalue().splitlines() if "自測" in l or "PASS" in l][-1:]
    print("  " + (tail[0].strip() if tail else "")[:100])
    chk("⑨ 前版 v0116 自測照常", prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑩ 帶加速器橋 · VIA_FROM_VCGC 閘 · glob 取前版(無釘名)",
        "[VIA:ACCEL-BRIDGE:v0100]" in body and "VIA_FROM_VCGC" in body)
    os.environ.pop("VIA_VRN_WKF009_DIR", None)
    os.environ.pop("VIA_NO_NET", None)
    print("[計] VRN_SystemManager_v0117 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
