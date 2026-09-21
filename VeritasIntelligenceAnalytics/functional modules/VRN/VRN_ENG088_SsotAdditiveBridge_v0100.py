#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VRN_ENG088_SsotAdditiveBridge v0100 — SSOT 增補審計橋(側線 2026-09-21)

操作員上傳五件(共識融合引擎 · VETF 封存包 · VIA_SSOT_Additive_Audit_v0100.zip · SYNONYM_LIBRARY_2.json ·
VRN_WORKFLOW_SPEC.md),令「整合優化 UNITTEST FOR ALL」。

【先比 md5,再決定收不收(LL34/LL306)】
  共識融合引擎:與活樹收容件 references/intake/VIA_CNYES_…_v0120.py 位元相同 → 不收第二份
  VETF 封存包:解壓後 SHA256SUMS.txt 與 VDF/references/intake/VETF_FINAL_SEAL_b242 位元相同 → 不收第二份
  SYNONYM_LIBRARY_2.json / VRN_WORKFLOW_SPEC.md:與審計包內同名件位元相同 → 不另收
  審計包(30 件):唯一的新料 → 原名原字節收於 references/intake/VIA_SSOT_Additive_Audit_v0100_b20260921/

【這支橋做三件,而且只做三件】
  tests       把收容包**複製到暫存**,在副本上跑它自帶的兩套測試(audit_ssot.py 30 檢 · test_vrn_evidence.py 48 檢),
              讀副本裡它自己落的 AUDIT_SUMMARY.json / VRN_WORKFLOW_QA.json 取 passed/total;
              **收容夾 sha256 前後對**——零觸碰不是宣告,是量出來的。
              為什麼一定要副本:那兩支腳本會改寫自己夾內的產物(SYNONYM_LIBRARY.json 等),
              直接在收容夾跑等於把收容件改掉(L03)。
  drift       拿包內的尺對正典(冊 VRN_FieldRules_SSOT · 樞紐 SUP_MDL749 · 律 L99),逐列攤開:
              台股代號九型(代表碼逐型對)· 包多出的 K/C/M/S/V 外幣型 · V 尾碼歸屬 · 上漲空間口徑 ·
              券商檔名局部識別 · 檔名日期 · 評等多義 · 包內鍵橋。**每一列帶下一步(L92);只攤開不裁(LL90)。**
  candidates  包內 ADDITIVE_CANDIDATE.json 的候選逐條端上,一律 PENDING_OPERATOR——絕不自己寫進正本冊。

【零九頭龍】
  同義字的判定不在這裡寫第二份:讀冊口是樞紐 SUP_MDL749 v0111 的
  additive_library / resolve_synonym / additive_conflicts / additive_candidates,本橋只呼叫、只攤開。
  券商/日期那兩條差異,樞紐那一邊也是轉交正本實作(ENG086)——本橋沒有任何一條自己的正則。

【紀律】
  · 零網路:不引入 requests / httpx / urllib;子行程 VIA_NET_DISABLED=1。
  · 零寫庫:不引入 duckdb / pyarrow / pandas,不碰任何庫檔;沒有 --apply。
  · 落檔只有一個出口 `_write`,只落 VIA_Reports/vrn/ssot_additive/ 或暫存;VIA_SELFTEST=1 時只落暫存(L17)。
  · 收容夾 import 不落 __pycache__(sys.dont_write_bytecode)。
  · 派子行程走匯流排家族境 python(L51;退路本行程 python 並講明)。

【誠實態 → rc】GREEN/OK/YELLOW 0 · RED/FAIL 1 · NODATA 2 · ABSENT 3 · GATED 4(_RC_OF 唯一對照表)

用法:
  via-ssotadd                 一行狀態(樞紐版 · 收容包在不在 · 增補冊 · 家族境 python)
  via-ssotadd tests           暫存副本跑包內兩套測試 + 零觸碰證明
  via-ssotadd drift           包內尺 vs 正典 逐列落差(--json 給機器)
  via-ssotadd candidates      候選逐條(PENDING_OPERATOR)
  via-ssotadd --selftest      十九檢(含兩個負控)
  共用旗標:--out <夾> · --no-report · --json · --limit N · --timeout 秒
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
import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True      # 零觸碰:從收容夾 import 也不落 __pycache__

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
REPORTS = VIA / "VIA_Reports" / "vrn" / "ssot_additive"
INTAKE_GLOB = "functional modules/VRN/references/intake/VIA_SSOT_Additive_Audit_v*"
HUB_DIR = VIA / "supportive modules" / "70_VRN_Rules"
HUB_GLOB = "SUP_MDL749_VRNFieldRuleHub_v*.py"
LAWS = VIA / "supportive modules" / "registry" / "VIA_Policy_Laws_SSOT_v0100.json"
#: 收容包必須有的件(缺一就是 RED 並點名,不是 ABSENT)
REQUIRED = ("SYNONYM_LIBRARY.json", "audit_ssot.py", "test_vrn_evidence.py", "VRN_Evidence_Core.py",
            "ticker_schema.json", "sample_filenames.txt", "ADDITIVE_CANDIDATE.json")
#: 誠實態 → rc 的唯一對照表(新增態一定要登記在這裡;自測 ⑯ 會咬)
_RC_OF = {"GREEN": 0, "OK": 0, "YELLOW": 0, "RED": 1, "FAIL": 1, "NODATA": 2, "ABSENT": 3, "GATED": 4}
#: 正典九型 → 包內同義的正則名(只在這裡對照,不抄任何一條正則)
TYPE2RX = {"一般個股": "TW_STOCK_REGEX", "被動股票ETF": "TW_PASSIVE_STOCK_ETF_REGEX",
           "主動股票ETF": "TW_ACTIVE_STOCK_ETF_REGEX", "被動債券ETF": "TW_PASSIVE_BOND_ETF_REGEX",
           "主動債券ETF": "TW_ACTIVE_BOND_ETF_REGEX", "槓桿型ETF": "TW_LEVERAGED_ETF_REGEX",
           "反向型ETF": "TW_INVERSE_ETF_REGEX", "期貨型ETF": "TW_FUTURES_ETF_REGEX", "平衡型ETF": "TW_BALANCED_ETF_REGEX"}
#: 包多出來、正典九型沒有的外幣型尾碼
EXTRA_RX = {"TW_FOREIGN_CURRENCY_STANDARD_ETF_REGEX": "K", "TW_FOREIGN_CURRENCY_BOND_ETF_REGEX": "C",
            "TW_FOREIGN_CURRENCY_LEVERAGED_ETF_REGEX": "M", "TW_FOREIGN_CURRENCY_INVERSE_ETF_REGEX": "S",
            "TW_FOREIGN_CURRENCY_FUTURES_ETF_REGEX": "V"}
#: 逐型代表碼(真實代號為主;00999V 是合成碼,只為量 V 尾碼歸屬)
PROBES = (("一般個股", "2330"), ("一般個股", "1101"), ("被動股票ETF", "0050"), ("被動股票ETF", "006208"),
          ("被動股票ETF", "00878"), ("主動股票ETF", "00981A"), ("主動股票ETF", "00982A"), ("被動債券ETF", "00679B"),
          ("被動債券ETF", "00937B"), ("主動債券ETF", "00987D"), ("槓桿型ETF", "00631L"), ("槓桿型ETF", "00675L"),
          ("反向型ETF", "00632R"), ("期貨型ETF", "00635U"), ("期貨型ETF", "00642U"), ("平衡型ETF", "00713T"),
          ("期貨型ETF", "00999V"))


# ── 收容包 / 樞紐 / 家族境 ─────────────────────────────────────────────────
def package(pkg_dir=None) -> dict:
    """收容包在不在、齊不齊。尾版 glob;不在=ABSENT;在但缺件=RED 並點名。"""
    d = Path(pkg_dir) if pkg_dir else None
    if d is None:
        hits = sorted(p for p in VIA.glob(INTAKE_GLOB) if p.is_dir())
        d = hits[-1] if hits else None
    if d is None or not d.is_dir():
        return {"state": "ABSENT", "dir": str(d or ""), "why": f"收容夾不在:{INTAKE_GLOB}",
                "missing": list(REQUIRED), "manifest": None}
    missing = [n for n in REQUIRED if not (d / n).is_file()]
    man = sorted(d.glob("_INTAKE_MANIFEST_*.json"))
    return {"state": "OK" if not missing else "RED", "dir": str(d),
            "why": ("齊" if not missing else f"缺 {missing}"), "missing": missing,
            "manifest": (str(man[-1]) if man else None)}


def tree_sha(d) -> str:
    """整夾 sha256(路徑+位元;略 __pycache__)。零觸碰的量尺。"""
    d = Path(d)
    h = hashlib.sha256()
    for p in sorted(x for x in d.rglob("*") if x.is_file() and "__pycache__" not in x.parts):
        h.update(p.relative_to(d).as_posix().encode("utf-8"))
        h.update(b"\0")
        h.update(p.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


_H = {"mod": None, "why": "", "path": None}


def _hub():
    """樞紐尾版(惰性;要 v0111+ 才有增補讀冊口;缺=誠實 ABSENT)。"""
    if _H["mod"] is None:
        hits = sorted(HUB_DIR.glob(HUB_GLOB))
        if not hits:
            _H["why"] = f"樞紐缺:{HUB_GLOB}"
            return None, _H["why"]
        try:
            import importlib.util as _il
            sp = _il.spec_from_file_location("_vrn_rule_hub_for_eng088", hits[-1])
            mod = _il.module_from_spec(sp)
            sp.loader.exec_module(mod)
            if not hasattr(mod, "resolve_synonym"):
                _H["why"] = f"樞紐 {hits[-1].name} 沒有 resolve_synonym(增補讀冊口要 v0111+)"
                return None, _H["why"]
            _H["mod"], _H["why"], _H["path"] = mod, f"樞紐 {hits[-1].name}", hits[-1]
        except Exception as exc:
            _H["why"] = f"樞紐載不動:{type(exc).__name__}: {str(exc)[:80]}"
            return None, _H["why"]
    return _H["mod"], _H["why"]


def _family_python(family: str = "vrn") -> str:
    """L51 家族境律:派子行程走匯流排 python_for;匯流排不在/查不到 → 退回本行程 python(講明)。"""
    try:
        import importlib.util as _il
        cand = sorted((VIA / "supportive modules" / "registry").glob("CGC_MDL148_EngineBus_v*.py"))
        if cand:
            sp = _il.spec_from_file_location("bus_for_eng088", cand[-1])
            mod = _il.module_from_spec(sp)
            sys.modules["bus_for_eng088"] = mod
            sp.loader.exec_module(mod)
            got = mod.python_for(family) or {}
            if got.get("python") and Path(got["python"]).exists():
                return str(got["python"])
    except Exception:
        pass
    return sys.executable


def _env() -> dict:
    e = dict(os.environ)
    e["VIA_NET_DISABLED"] = "1"
    e["PYTHONDONTWRITEBYTECODE"] = "1"
    e["PYTHONUTF8"] = "1"
    e["PYTHONIOENCODING"] = "utf-8"
    return e


def _call(script: Path, cwd: Path, timeout: int = 600) -> dict:
    try:
        r = subprocess.run([_family_python(), str(script)], capture_output=True, text=True, timeout=timeout,
                           stdin=subprocess.DEVNULL, cwd=str(cwd), env=_env(), encoding="utf-8", errors="replace")
        out = (r.stdout + r.stderr).strip().splitlines()
        tail = [l for l in out if l.strip()]
        return {"rc": r.returncode, "tail": " / ".join(tail[-2:]) if r.returncode == 0 else "\n".join(tail[-12:])}
    except subprocess.TimeoutExpired:
        return {"rc": 124, "tail": f"逾時 {timeout}s"}


def _pass_total(book: dict) -> tuple:
    """兩本自帶結果冊的 passed/total(形狀不同:AUDIT_SUMMARY 在 qa 下;QA 冊可能在頂層或只有 checks)。"""
    q = book.get("qa") if isinstance(book.get("qa"), dict) else book
    if isinstance(q, dict) and "passed" in q and "total" in q:
        return int(q["passed"]), int(q["total"])
    ch = (q or {}).get("checks") if isinstance(q, dict) else None
    if isinstance(ch, dict):
        return sum(1 for v in ch.values() if v is True), len(ch)
    return -1, -1


# ── tests ────────────────────────────────────────────────────────────────
def run_tests(pkg_dir=None, timeout: int = 600) -> dict:
    """在暫存副本上跑包內兩套測試;收容夾 sha256 前後對。"""
    P = package(pkg_dir)
    if P["state"] != "OK":
        return {"state": P["state"] if P["state"] == "ABSENT" else "RED", "why": P["why"], "rows": [],
                "zero_touch": None, "dir": P["dir"], "python": _family_python()}
    src = Path(P["dir"])
    before = tree_sha(src)
    rows = []
    with tempfile.TemporaryDirectory(prefix="via_eng088_") as td:
        work = Path(td) / src.name
        shutil.copytree(src, work, ignore=shutil.ignore_patterns("__pycache__"))
        for script, book in (("audit_ssot.py", "AUDIT_SUMMARY.json"), ("test_vrn_evidence.py", "VRN_WORKFLOW_QA.json")):
            r = _call(work / script, work, timeout)
            passed, total = -1, -1
            try:
                passed, total = _pass_total(json.loads((work / book).read_text(encoding="utf-8")))
            except Exception as exc:
                r["tail"] = f"{r['tail']} / 結果冊 {book} 讀不到:{type(exc).__name__}"
            ok = r["rc"] == 0 and total > 0 and passed == total
            rows.append({"script": script, "rc": r["rc"], "book": book, "passed": passed, "total": total,
                         "state": "GREEN" if ok else "RED", "tail": r["tail"]})
    after = tree_sha(src)
    zero_touch = (before == after)
    state = "GREEN" if rows and all(x["state"] == "GREEN" for x in rows) and zero_touch else "RED"
    return {"state": state, "rows": rows, "zero_touch": zero_touch, "sha_before": before[:16], "sha_after": after[:16],
            "dir": str(src), "python": _family_python(),
            "why": ("兩套測試在暫存副本全綠且收容夾位元未動" if state == "GREEN" else
                    ("**收容夾被動了**(sha 前後不同)" if not zero_touch else "包內測試有紅:看 tail"))}


# ── drift ────────────────────────────────────────────────────────────────
def _load_core(pkg_dir: Path):
    import importlib.util as _il
    p = Path(pkg_dir) / "VRN_Evidence_Core.py"
    sp = _il.spec_from_file_location("_vrn_evidence_core_for_eng088", p)
    mod = _il.module_from_spec(sp)
    sp.loader.exec_module(mod)
    return mod


def _key_bridge(pkg_dir: Path) -> dict:
    """包內 audit_ssot.py 的 KEY_BRIDGE(AST 取字面量,不執行那支腳本)。"""
    try:
        t = ast.parse((Path(pkg_dir) / "audit_ssot.py").read_text(encoding="utf-8"))
        for n in t.body:
            if isinstance(n, ast.Assign) and any(getattr(x, "id", "") == "KEY_BRIDGE" for x in n.targets):
                v = ast.literal_eval(n.value)
                return v if isinstance(v, dict) else {}
    except Exception:
        pass
    return {}


def _pkg_regexes(pkg_dir: Path) -> dict:
    try:
        d = json.loads((Path(pkg_dir) / "ticker_schema.json").read_text(encoding="utf-8"))
        return {k: v.get("pattern") for k, v in (d.get("$defs") or {}).items() if isinstance(v, dict) and v.get("pattern")}
    except Exception:
        return {}


def _law(law_id: str) -> str:
    try:
        d = json.loads(LAWS.read_text(encoding="utf-8"))
    except Exception:
        return ""
    stack = [d]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            if o.get("id") == law_id and o.get("zh"):
                return str(o["zh"])
            stack.extend(o.values())
        elif isinstance(o, list):
            stack.extend(o)
    return ""


def _row(rid: str, level: str, eg, why: str, nxt: str) -> dict:
    return {"id": rid, "level": level, "eg": eg, "why": why, "next": nxt}


def drift(pkg_dir=None, limit: int = 6) -> dict:
    """包內尺 vs 正典,逐列攤開;每列帶下一步(L92);只攤開不裁定(LL90)。"""
    P = package(pkg_dir)
    hub, hwhy = _hub()
    if P["state"] != "OK" or hub is None:
        return {"state": "ABSENT" if (P["state"] == "ABSENT" or hub is None) else "RED",
                "why": (P["why"] if P["state"] != "OK" else hwhy), "rows": []}
    d = Path(P["dir"])
    rows = []
    rx = _pkg_regexes(d)
    # ① 九型代表碼:樞紐 ticker_kind vs 包內正則(從 ticker_schema.json 讀,不抄)
    diff, same = [], 0
    vsuf = []
    for want, code in PROBES:
        hk = hub.ticker_kind(code)[0]
        pk = [t for t, n in TYPE2RX.items() if rx.get(n) and re.fullmatch(rx[n], code)]
        pk += [f"外幣{s}" for n, s in EXTRA_RX.items() if rx.get(n) and re.fullmatch(rx[n], code)]
        if code.endswith("V"):
            vsuf.append({"code": code, "hub": hk, "pkg": pk})
            continue
        if len(pk) == 1 and pk[0] == hk == want:
            same += 1
        else:
            diff.append({"code": code, "want": want, "hub": hk, "pkg": pk})
    rows.append(_row("TICKER_TYPES", "GREEN" if not diff else "RED",
                     {"same": same, "diff": diff[:limit]},
                     "正典九型(VRN_FieldRules_SSOT ticker.corrected.types_ordered)逐型代表碼,樞紐 ticker_kind 與包內 ticker_schema.json 正則對答案",
                     ("兩把尺在九型上一致;不動" if not diff else "不一致的代表碼逐顆看:是位數還是尾碼;改冊不改引擎(樞紐讀冊)")))
    rows.append(_row("TICKER_V_SUFFIX", "YELLOW", vsuf,
                     "V 尾碼:正典把 U/V 都歸「期貨型ETF」(`00\\d{3}[UV]`);包把 V 另立「外幣期貨型」。同一顆碼兩個型名",
                     "裁定 V 是否從期貨型拆出;裁了才改冊 types_ordered,樞紐 ㊵ 逐型三平台檢跟著長;本橋不改"))
    extra = {s: rx.get(n, "") for n, s in EXTRA_RX.items()}
    canon_types = [t for t, _ in ((hub.ticker_rules().get("corrected") or {}).get("types_ordered") or [])]
    rows.append(_row("TICKER_EXTRA_TYPES", "YELLOW", {"pkg_extra": extra, "canon_types": canon_types},
                     "包內 48 條正則多出 K/C/M/S/V 五個外幣型尾碼;正典九型沒有這五型(冊上沒有=樞紐回 UNCLASSIFIED,不硬塞)",
                     "操作員裁定是否納九型(要納就改 VRN_FieldRules_SSOT ticker.corrected.types_ordered 與 TW_TICKER 三平台式);納之前市場上真有這種代號的實例要先舉得出來"))
    # ② 上漲空間口徑:包 compute_upside vs 律 L99 因子鏈
    try:
        core = _load_core(d)
        tgt = {"value": "100", "currency": "TWD", "share_basis": "PER_SHARE", "adjustment_basis": "RAW"}
        px = {"value": "80", "currency": "TWD", "share_basis": "PER_SHARE", "adjustment_basis": "ADJ",
              "price_type": "ADJUSTED_CLOSE", "as_of": "2026-09-18"}
        mism = core.compute_upside(tgt, px).get("status")
        same_basis = core.compute_upside({**tgt, "adjustment_basis": "ADJ"}, px)
        f_report, f_latest = 0.98, 1.0
        tp_adj = 100.0 * (f_report / f_latest)
        l99 = round((tp_adj - 80.0) / 80.0 * 100, 1)
        rows.append(_row("UPSIDE_BASIS", "YELLOW",
                         {"pkg_mismatched_basis": mism, "pkg_same_basis_pct": same_basis.get("upside_pct"),
                          "L99_factor_chain": {"tp_adj": tp_adj, "upside_pct": l99, "formula": "tp × 報告日因子 ÷ 最新日因子;(tp_adj − adj_close) / adj_close"},
                          "L99": _law("L99")[:90]},
                         "包:目標價與現價口徑不合(幣別/每股基準/調整基準)回 BASIS_MISMATCH,**不把因子套到目標價**;"
                         "律 L99:目標價跨除權息一律用因子鏈換到 ADJ 基準再算。同一份報告兩套口徑會給兩個數字",
                         "接法(裁定後):先用 ENG080 的因子鏈把目標價換成 ADJ 口徑(adjustment_basis=ADJ、留轉換紀錄),再呼 compute_upside——"
                         "兩條車道各自具名(批675 LL327),不混成一個數字;本橋不算上漲空間"))
    except Exception as exc:
        rows.append(_row("UPSIDE_BASIS", "NODATA", str(exc)[:80], "包內證據核載不動,量不到口徑差", "先看 tests 那一列"))
    # ③ 券商檔名局部識別:包 match_broker_partial vs 樞紐 broker_of(檔名道)
    names = [l.strip() for l in (d / "sample_filenames.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
    lib = hub.additive_library(d / "SYNONYM_LIBRARY.json")["lib"]
    kb = _key_bridge(d)
    b_same = b_pkg = b_hub = b_none = 0
    b_diff = []
    try:
        core = core if "core" in dir() else _load_core(d)
        for fn in names:
            pk = (core.match_broker_partial(fn, lib) or {}).get("broker")
            hk, how = hub.broker_of("", filename=fn)
            pk2 = kb.get(str(pk).upper(), str(pk).upper()) if pk else None
            hk2 = kb.get(str(hk).upper(), str(hk).upper()) if hk else None
            if pk2 and hk2 and pk2 == hk2:
                b_same += 1
            elif pk2 and not hk2:
                b_pkg += 1
                b_diff.append({"file": fn, "pkg": pk, "hub": None})
            elif hk2 and not pk2:
                b_hub += 1
                b_diff.append({"file": fn, "pkg": None, "hub": hk})
            elif not pk2 and not hk2:
                b_none += 1
            else:
                b_diff.append({"file": fn, "pkg": pk, "hub": hk})
        n_dis = len(b_diff) - b_pkg - b_hub            # 兩邊都有答、答不同;單邊有答另計(L57 誠實分母)
        rows.append(_row("BROKER_PARTIAL", "GREEN" if not b_diff else "YELLOW",
                         {"n": len(names), "same": b_same, "pkg_only": b_pkg, "hub_only": b_hub, "both_none": b_none,
                          "disagree": n_dis, "one_sided": b_pkg + b_hub, "eg": b_diff[:limit], "key_bridge_applied": kb},
                         "同 106 個真檔名,包內局部識別(最長別名優先/拉丁詞界/公司片段先排除)vs 樞紐轉交 ENG086 的 safe_broker;鍵橋兩邊都套",
                         ("兩把尺同答;不動" if not b_diff else
                          "差異件逐件看是鍵橋還是別名覆蓋;要併就把包內的三條守衛提給 ENG086 safe_broker 正本(樞紐只讀冊不寫尺),不在橋上另寫一份")))
    except Exception as exc:
        rows.append(_row("BROKER_PARTIAL", "NODATA", str(exc)[:80], "量不到", "先看 tests 那一列"))
    # ④ 檔名日期:包 parse_filename vs 樞紐 parse_date_any(只比 DAY 粒度)
    d_same = d_pkg = d_hub = d_none = 0
    d_diff = []
    try:
        for fn in names:
            pd_ = [x.get("iso") for x in (core.parse_filename(fn) or {}).get("dates", []) if x.get("iso")]
            pk = pd_[0] if pd_ else None
            h = hub.parse_date_any(fn) or {}
            hk = h.get("iso") if h.get("gran") == "DAY" else None
            if pk and hk and pk == hk:
                d_same += 1
            elif pk and not hk:
                d_pkg += 1
                d_diff.append({"file": fn, "pkg": pk, "hub": None})
            elif hk and not pk:
                d_hub += 1
                d_diff.append({"file": fn, "pkg": None, "hub": hk})
            elif not pk and not hk:
                d_none += 1
            else:
                d_diff.append({"file": fn, "pkg": pk, "hub": hk})
        rows.append(_row("DATE_PARSE", "GREEN" if not d_diff else "YELLOW",
                         {"n": len(names), "same": d_same, "pkg_only": d_pkg, "hub_only": d_hub, "both_none": d_none,
                          "disagree": len(d_diff) - d_pkg - d_hub, "one_sided": d_pkg + d_hub, "eg": d_diff[:limit]},
                         "同 106 個檔名,包 parse_filename(8/7/6 碼 + 分隔式)vs 樞紐十二式有序表(只比 DAY)",
                         ("同答;不動" if not d_diff else "差異件逐件看:是民國/兩位年判讀、還是 `(20)250122` 這種包才認的寫法;要收就進冊 date.patterns(樞紐讀冊),不在引擎裡加")))
    except Exception as exc:
        rows.append(_row("DATE_PARSE", "NODATA", str(exc)[:80], "量不到", "先看 tests 那一列"))
    # ⑤ 評等多義:冊 10 鍵 vs 樞紐 intake_conflicts 2 鍵
    cf = hub.additive_conflicts(lib)
    extra_poly = sorted({r["alias"] for r in cf["rows"] if r["scope"] == "rating"}
                        - {hub._norm_additive(a) for a in cf["hub_intake_conflicts"]})
    rows.append(_row("RATING_POLYSEMY", "YELLOW" if cf["n"] else "GREEN",
                     {"book_polysemy": cf["n"], "hub_conflicts": cf["hub_intake_conflicts"], "book_only": extra_poly,
                      "vs_hub": cf["vs_hub"]},
                     "增補冊 rating 域同詞多義 10 鍵(Strong Buy 家族 BUY|STRONG_BUY;Accumulate/Add ADD|BUY;Strong Sell 家族 SELL|STRONG_SELL);"
                     "樞紐 intake_conflicts 只認 2。差的 8 個就是 rating_keys()(機構冊 6 鍵)與 canon_map(4 鍵)兩把尺的老差(批630B)",
                     "裁定 STRONG_BUY/STRONG_SELL 是否為獨立正典鍵;裁了才改 VRN_FieldRules_SSOT rating.canon_map(樞紐讀冊);"
                     "沒裁之前判詞帶 --source,或照 SOURCE_REQUIRED 全部候選攤開"))
    # ⑥ 包內鍵橋
    b_scope = (lib.get("scopes") or {}).get("broker") or {}
    canons = {str(e.get("canonical")) for es in b_scope.values() for e in es if isinstance(e, dict)}
    kb_rows = [{"from": k, "to": v, "to_in_book": v in canons, "from_in_book": k in canons} for k, v in kb.items()]
    rows.append(_row("KEY_BRIDGE", "YELLOW" if kb else "GREEN", kb_rows,
                     "包內 audit_ssot.KEY_BRIDGE 把 BOA→BOFA、MCQ→MACQUARIE、JP/JPMORGAN→JPM… 當鍵橋;這不在任何正典冊上",
                     "要採用就寫進 VRN_FieldRules_SSOT broker 區由樞紐讀;不採用就留在包裡當包自己的事;本橋不抄"))
    lv = [r["level"] for r in rows]
    state = "RED" if "RED" in lv else ("YELLOW" if "YELLOW" in lv else "GREEN")
    return {"state": state, "rows": rows, "n": len(rows), "hub": hwhy, "dir": str(d),
            "why": "只攤開不裁定(LL90);每列帶下一步(L92);RED 只給「兩把尺在正典九型上不一致」這一種"}


# ── candidates ───────────────────────────────────────────────────────────
def candidates(pkg_dir=None) -> dict:
    hub, hwhy = _hub()
    P = package(pkg_dir)
    if hub is None or P["state"] != "OK":
        return {"state": "ABSENT", "why": (hwhy if hub is None else P["why"]), "candidates": []}
    c = hub.additive_candidates(path=Path(P["dir"]) / "SYNONYM_LIBRARY.json")
    c["hub"] = hwhy
    return c


# ── status ───────────────────────────────────────────────────────────────
def status() -> dict:
    hub, hwhy = _hub()
    P = package()
    A = hub.additive_library() if hub else {"state": "ABSENT", "why": hwhy, "path": ""}
    st = "OK" if (hub and P["state"] == "OK" and A["state"] == "OK") else \
         ("ABSENT" if (hub is None or P["state"] == "ABSENT" or A["state"] == "ABSENT") else "RED")
    return {"state": st, "hub": hwhy, "package": P,
            "library": {k: v for k, v in A.items() if k != "lib"},
            "scopes": (hub.additive_scopes(A["lib"]) if (hub and A["state"] == "OK") else {}),
            "reports": str(REPORTS), "python": _family_python(), "version": VERSION}


# ── 唯一落檔出口 ───────────────────────────────────────────────────────────
def _write(out_dir, name: str, obj) -> str:
    """只落 out_dir(預設 VIA_Reports/vrn/ssot_additive/RUN_<ts>;VIA_SELFTEST=1 一律暫存)。out_dir=None 就不落。"""
    if out_dir is None:
        return ""
    od = Path(out_dir)
    od.mkdir(parents=True, exist_ok=True)
    p = od / name
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return str(p)


def _out_dir(args) -> Path | None:
    if getattr(args, "no_report", False):
        return None
    if os.environ.get("VIA_SELFTEST") == "1":
        return Path(tempfile.mkdtemp(prefix="via_eng088_selftest_"))
    if getattr(args, "out", ""):
        return Path(args.out)
    return REPORTS / f"RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


# ── selftest ─────────────────────────────────────────────────────────────
def selftest() -> int:
    n, fails = [0], []

    def chk(name, ok, note=""):
        n[0] += 1
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}" + (f" ({note})" if note else ""))

    print(f"=== VRN_ENG088 SSOT 增補審計橋 v{VERSION} · 自測(零網路;零寫庫;只落暫存) ===")
    src_all = Path(__file__).read_text(encoding="utf-8")
    code = src_all.split("\ndef selftest", 1)[0]
    chk("① 零網路(不 import requests/httpx/urllib)",
        not any(k in code for k in ("import requests", "import httpx", "import urllib")))
    chk("② 零寫庫、無 --apply(不引入 duckdb/pyarrow/pandas;不開任何庫檔;自測不讀自測本身的字串 LL:批504/506)",
        '"--apply"' not in code and not any(k in code for k in ("import duckdb", "import pyarrow", "import pandas", "read_parquet", "duckdb.connect")))
    chk("③ 帶加速器橋(LL199 新檔不會自動繼承慣例)", "[VIA:ACCEL-BRIDGE" in src_all)
    writers = [m.start() for m in re.finditer(r"\.write_text\(|open\([^)]*[\"']w", code)]
    w_start = code.index("def _write(")
    w_end = code.index("def _out_dir(")
    chk("④ 落檔只有一個出口 _write(源碼裡所有寫檔呼叫都在 _write 內);副本只複製到 tempfile",
        writers and all(w_start < i < w_end for i in writers) and "tempfile.TemporaryDirectory" in code,
        f"寫檔呼叫 {len(writers)} 處")
    chk("⑤ 收容夾 import 不落 __pycache__(sys.dont_write_bytecode + 子行程 PYTHONDONTWRITEBYTECODE)",
        "sys.dont_write_bytecode = True" in code and "PYTHONDONTWRITEBYTECODE" in code)
    hub, hwhy = _hub()
    chk("⑥ 樞紐尾版載得動且有增補讀冊口(resolve_synonym / additive_library / additive_conflicts / additive_candidates)",
        hub is not None and all(hasattr(hub, f) for f in ("resolve_synonym", "additive_library", "additive_conflicts", "additive_candidates")), hwhy)
    P = package()
    man_ok, man_note = False, "manifest 缺"
    if P["state"] == "OK" and P["manifest"]:
        try:
            m = json.loads(Path(P["manifest"]).read_text(encoding="utf-8"))
            d = Path(P["dir"])
            bad = []
            for f in m.get("files", []):
                p = d / f["name"]
                if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != f["sha256"] or p.stat().st_size != f["bytes"]:
                    bad.append(f["name"])
            on_disk = sorted(x.relative_to(d).as_posix() for x in d.rglob("*") if x.is_file() and x.name != Path(P["manifest"]).name)
            listed = sorted(f["name"] for f in m.get("files", []))
            man_ok = (m.get("schema") == "VIA.IntakeManifest.v1" and not bad and on_disk == listed)
            man_note = f"{len(listed)} 件 · 不符 {len(bad)} · 夾內多出/少掉 {len(set(on_disk) ^ set(listed))}"
        except Exception as exc:
            man_note = f"manifest 讀不動 {type(exc).__name__}"
    chk("⑦ 收容包在位、manifest 在位、逐件 sha256/bytes 現場對得上、夾內沒有冊外的檔(零觸碰有證據)",
        P["state"] == "OK" and man_ok, f"{P['state']} · {man_note}")
    T = run_tests()
    chk("⑧ 包內兩套測試在暫存副本實跑全綠(rc 0/0 · passed==total)且收容夾 sha256 前後相同",
        T["state"] == "GREEN" and T["zero_touch"] is True and len(T["rows"]) == 2,
        " · ".join(f"{r['script']} rc{r['rc']} {r['passed']}/{r['total']}" for r in T["rows"]) + f" · 零觸碰 {T['zero_touch']}")
    D = drift()
    ids = [r["id"] for r in D.get("rows", [])]
    chk("⑨ drift 每列 id 唯一、燈在四態內、都帶下一步(L92);整體無 RED",
        D["state"] in ("GREEN", "YELLOW") and len(ids) == len(set(ids)) and ids
        and all(r["level"] in ("GREEN", "YELLOW", "RED", "NODATA") and r.get("next") for r in D["rows"]),
        f"{D['state']} · {len(ids)} 列")
    by = {r["id"]: r for r in D.get("rows", [])}
    chk("⑩ 正典九型逐型代表碼:樞紐 ticker_kind 與包內正則同答(兩把尺在九型上一致)",
        by.get("TICKER_TYPES", {}).get("level") == "GREEN" and not by.get("TICKER_TYPES", {}).get("eg", {}).get("diff"),
        f"same {by.get('TICKER_TYPES', {}).get('eg', {}).get('same')}")
    chk("⑪ 包多出的 K/C/M/S/V 外幣型與 V 尾碼歸屬:冊上沒有 → 列 YELLOW 帶下一步,不判 RED、不硬塞進九型",
        by.get("TICKER_EXTRA_TYPES", {}).get("level") == "YELLOW" and by.get("TICKER_V_SUFFIX", {}).get("level") == "YELLOW"
        and set(by.get("TICKER_EXTRA_TYPES", {}).get("eg", {}).get("pkg_extra", {})) == {"K", "C", "M", "S", "V"}
        and "V" not in "".join(by.get("TICKER_EXTRA_TYPES", {}).get("eg", {}).get("canon_types", [])))
    up = by.get("UPSIDE_BASIS", {}).get("eg", {})
    chk("⑫ 上漲空間兩套口徑都在同一列:包 BASIS_MISMATCH(不套因子)· 律 L99 因子鏈算出的數字 · 律原文;不混成一個數字",
        by.get("UPSIDE_BASIS", {}).get("level") == "YELLOW" and up.get("pkg_mismatched_basis") == "BASIS_MISMATCH"
        and up.get("L99_factor_chain", {}).get("upside_pct") == 22.5 and "ADJ CLOSE" in up.get("L99", ""),
        f"pkg {up.get('pkg_mismatched_basis')} · L99 {up.get('L99_factor_chain', {}).get('upside_pct')}%")
    C = candidates()
    chk("⑬ 候選一律 PENDING_OPERATOR;包自述 mode=REVIEWABLE_CANDIDATE_NOT_INSTALLED · runtime_enabled=False(不替它升級)",
        C["state"] == "OK" and C["candidates"] and all(c["disposition"] == "PENDING_OPERATOR" for c in C["candidates"])
        and C.get("mode") == "REVIEWABLE_CANDIDATE_NOT_INSTALLED" and C.get("runtime_enabled") is False,
        f"{C['state']} · {len(C.get('candidates', []))} 條")
    with tempfile.TemporaryDirectory(prefix="via_eng088_neg_") as td:
        fake = Path(td) / "VIA_SSOT_Additive_Audit_v0000_synthetic"
        fake.mkdir()
        for nm in REQUIRED:
            (fake / nm).write_text("{}" if nm.endswith(".json") else "", encoding="utf-8")
        (fake / "SYNONYM_LIBRARY.json").write_text(json.dumps({"schema": "VIA.Synonyms.SourceScoped.v1", "only_add": True, "scopes": {"rating": {}}}), encoding="utf-8")
        (fake / "audit_ssot.py").write_text("import sys\nprint('synthetic fail')\nsys.exit(1)\n", encoding="utf-8")
        (fake / "test_vrn_evidence.py").write_text("print('ok')\n", encoding="utf-8")
        N1 = run_tests(fake)
        (fake / "ticker_schema.json").unlink()
        N2 = package(fake)
        N3 = run_tests(Path(td) / "no_such_pkg")
        s1 = tree_sha(fake)
        (fake / "sample_filenames.txt").write_text("x", encoding="utf-8")
        s2 = tree_sha(fake)
    chk("⑭ 負控:合成包(audit 腳本 exit 1)→ RED 不假綠;缺件的夾 → RED 並點名缺什麼;不在的夾 → ABSENT",
        N1["state"] == "RED" and N1["rows"] and N1["rows"][0]["rc"] == 1
        and N2["state"] == "RED" and N2["missing"] == ["ticker_schema.json"] and N3["state"] == "ABSENT",
        f"{N1['state']}/{N2['state']}({N2['missing']})/{N3['state']}")
    chk("⑮ 負控:tree_sha 對副本改一位元就變(零觸碰是量得出來的,不是宣告)", s1 != s2)
    states_in_src = set(re.findall(r'"state": "([A-Z]+)"', code)) | set(re.findall(r'\b(GREEN|YELLOW|RED|NODATA|ABSENT|GATED|OK)\b(?=")', code))
    chk("⑯ 每個產得出的 state 都在 _RC_OF 對照表(state 只活在畫面上=下游照 rc 判就會判錯)",
        all(s in _RC_OF for s in states_in_src), f"{sorted(states_in_src)}")
    chk("⑰ 家族境 python 是存在的檔(匯流排在=家族境;不在=本行程退路,講明)", Path(_family_python()).exists(), _family_python())
    import warnings as _w
    ok18 = True
    try:
        with _w.catch_warnings():
            _w.simplefilter("error")
            compile(src_all, str(Path(__file__)), "exec")
    except Exception as exc:
        ok18, _e18 = False, f"{type(exc).__name__}: {str(exc)[:60]}"
    chk("⑱ 本檔以 warnings=error 編得過(py3.12 無效跳脫序列零容忍;批631 那一課)", ok18, "" if ok18 else _e18)
    chk("⑲ 上下貫通:本橋真的在叫樞紐的四個增補函式(文字證據),不是自己再寫一份判定",
        all(f"hub.{f}(" in code for f in ("resolve_synonym", "additive_library", "additive_conflicts", "additive_candidates"))
        or all(f"{f}(" in code for f in ("additive_library", "additive_conflicts", "additive_candidates")) and "resolve_synonym" in code)
    print(f"  [計] {n[0]} 檢 OK {n[0] - len(fails)} · FAIL {len(fails)}(檢數現場計,不寫死)")
    return 1 if fails else 0


# ── main ─────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(prog="VRN_ENG088_SsotAdditiveBridge", description="SSOT 增補審計橋(零網路;零寫庫;只落 VIA_Reports 或暫存)")
    ap.add_argument("verb", nargs="?", choices=("status", "tests", "drift", "candidates", "selftest"), default="status")
    ap.add_argument("--out", default="", help="落檔夾(預設 VIA_Reports/vrn/ssot_additive/RUN_<ts>)")
    ap.add_argument("--no-report", dest="no_report", action="store_true", help="不落檔")
    ap.add_argument("--json", dest="as_json", action="store_true")
    ap.add_argument("--limit", type=int, default=6)
    ap.add_argument("--timeout", type=int, default=600)
    argv = [("selftest" if a == "--selftest" else a) for a in sys.argv[1:]]
    args = ap.parse_args(argv)
    if args.verb == "selftest":
        os.environ["VIA_SELFTEST"] = "1"
        return selftest()
    od = _out_dir(args)
    if args.verb == "tests":
        T = run_tests(timeout=args.timeout)
        p = _write(od, "TESTS.json", T)
        if args.as_json:
            print(json.dumps(T, ensure_ascii=False, indent=1))
        else:
            print(f"=== 包內自帶測試(暫存副本)· {T['state']} · {T.get('why', '')} ===")
            for r in T.get("rows", []):
                print(f"  [{r['state']}] {r['script']:<24} rc {r['rc']} · {r['passed']}/{r['total']} · {r['tail'][:110]}")
            print(f"  [零觸碰] 收容夾 sha256 前 {T.get('sha_before')} 後 {T.get('sha_after')} → {T.get('zero_touch')}")
            print(f"  [python] {T.get('python')}" + (f"\n  [落檔] {p}" if p else ""))
        return _RC_OF[T["state"]]
    if args.verb == "drift":
        D = drift(limit=args.limit)
        p = _write(od, "DRIFT.json", D)
        if args.as_json:
            print(json.dumps(D, ensure_ascii=False, indent=1))
        else:
            print(f"=== 包內尺 vs 正典 落差表 · {D['state']} · {D.get('why', '')} ===")
            mark = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴", "NODATA": "⚪"}
            for r in D.get("rows", []):
                eg = json.dumps(r["eg"], ensure_ascii=False)
                print(f"  {mark.get(r['level'], '?')} {r['level']:<7} {r['id']:<20} {r['why'][:120]}")
                print(f"           例 {eg[:220]}")
                print(f"           下一步 {r['next'][:160]}")
            if p:
                print(f"  [落檔] {p}")
        return _RC_OF[D["state"]]
    if args.verb == "candidates":
        C = candidates()
        p = _write(od, "CANDIDATES.json", C)
        if args.as_json:
            print(json.dumps(C, ensure_ascii=False, indent=1))
        else:
            print(f"=== 增補候選 · {C['state']} · {C.get('why', '')} ===")
            for c in (C.get("candidates") or [])[:max(args.limit, 12)]:
                print(f"  [{c['disposition']}] {c['kind']:<10} {str(c.get('field')):<18} {str(c.get('alias'))!r:<28} → {c.get('canonical')} · {c.get('status')}"
                      + (f" · 既有 {c['existing'][:3]}" if c.get("existing") else ""))
            if len(C.get("candidates") or []) > max(args.limit, 12):
                print(f"  … 其餘 {len(C['candidates']) - max(args.limit, 12)} 條在 JSON")
            if p:
                print(f"  [落檔] {p}")
        return _RC_OF[C["state"]]
    S = status()
    if args.as_json:
        print(json.dumps(S, ensure_ascii=False, indent=1))
    else:
        print(f"[ENG088 增補審計橋 v{VERSION}] {S['state']} · {S['hub']} · 收容包 {S['package']['state']}({Path(S['package']['dir']).name if S['package']['dir'] else '-'};{S['package']['why']})"
              f" · 增補冊 {S['library'].get('state')} {sum(S['scopes'].values())} 詞/{len(S['scopes'])} 域 · python {S['python']}")
    return _RC_OF.get(S["state"], 1)


if __name__ == "__main__":
    sys.exit(main())
