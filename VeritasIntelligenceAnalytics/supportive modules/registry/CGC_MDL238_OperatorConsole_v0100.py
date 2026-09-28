#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL238_OperatorConsole v0100 — VCGC 生成的操作台引擎 + 格式鎖定的 HTML 模板(左輸入 · 右摘要 / 狀況 / 輸出 / 資料庫)

操作員 2026-09-28 R24:「GITHUB 中有模板做好 VCGC 生成一個引擎與模板 HTML U/I FORMAT 鎖定同步 左面板為輸入 VDF 只有增減過內外
個股財報 單季 累計 年度 起始時間 其他起始時間統一但可分群更改 族群為單位 VRN 只有將輸入文件位置 WINDOWS I/O 或拖曳式輸入
輸入摘要有去重功能 引擎狀況 運作摘要 後面是輸出統一為 PARQUET DUCKDB 管理 但資料庫管理允許你擷取資料」。

不另立尺(L05),每一塊問正主:
  版面鎖   VIA_UI_TemplateSSOT_v0100.json `dashboard`(批167 定案:左面板 260px · 表頭 38px · ≤768 上下疊 · 左面板可收合 ·
           Arial 11/10px · 面板 / 框 / 輸入框色)+ `status` 四燈色。CSS 全由冊值生成,零寫死;
           VIA_UI_FormatLock_v0100.json 釘這組值與模板骨架 sha —— 冊值或骨架一變,自測就紅,要操作員重鎖(template --lock)。
  輸入冊   VIA_InputConsole_Spec_v0100.json 的 `user` 段(CGC_MDL139 的冊);寫入只走 CGC_MDL139 apply_set
           (tw-add / tw-remove 國內 · intl-add / intl-remove INTL_FIN:<代碼> 國外 · fin-period 單季|累計|年度 · fin-from / fin-to ·
           group-start <群>:<日> · vrn-dir),changelog 與鏡寫 VDF_Input_Interface_Matrix 都照 MDL139 原樣。
  引擎狀況 VDF / VRN 鏈最新報告(CGC_MDL231 chain_states)· 燈鎖冊尾版 · 工具鎖冊(CGC_MDL233 pinned)· 全景側車流程閘。
  運作摘要 全景側車 SWEEP_SIDE_latest 每步 rc / 秒數 · 兩條鏈 tally · 輸入冊最近 changelog。
  資料家   CGC_MDL123 resolve_home / home_usable(parquet = 本體,duckdb = 管家:VIEW over read_parquet —— DataHome SSOT layout_contract)。
左面板只收三件(照令):① VDF 財報:國內 / 國外個股增減 · 單季 / 累計 / 年度 · 起迄年 · 起始日 ② 其他資料起始日:統一一個日,
  可按群(台股 · 總經 · 主動 ETF · 國際)各自改 ③ VRN:輸入文件位置(Windows 路徑 / via-vrnin 選夾)或拖曳。
輸入摘要去重:代碼 NFKC + 大寫正規化;同一批重複、已在冊的新增、不在冊的移除、國內國外兩邊都有、拖曳同名同大小 → 全部列出、只送一次。
輸出統一 Parquet:`parquet` 把資料家每本 .duckdb 每張表寫成 <家>/parquet/<庫>/<表>.parquet(zstd,讀回列數),
  管家 <家>/VIA_Parquet_Catalog.duckdb 每張表一個 VIEW;來源庫唯讀開、一個位元不動。預設乾跑,--apply 才寫。
資料庫擷取:`extract --view <庫>__<表> [--cols] [--date-col --start --end] [--where] [--limit] [--format parquet|csv]`,唯讀開管家,
  只允許 SELECT;結果落 VIA_Reports/operator_console/extract/。頁上的擷取面板組出同一句指令(複製即跑)。
頁面:`page` → VIA_Reports/operator_console/VIA_OperatorConsole_latest.html(帶資料);`template` → ui_support 的
  VIA_UI_OperatorConsole_Template_v0100.html(不帶資料的模板,已提交;鎖的就是它)。頁內 localStorage 存草稿、
  BroadcastChannel 多分頁同步(VIA_HTML_UI 標準);「匯出輸入包」→ JSON,`apply --file` 入冊。
只收 VCGC 呼叫(VIA_FROM_VCGC=YES)。零網路。寫冊只經 apply(預設乾跑,--apply 才寫)。
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
import html as _html
import importlib.util
import json
import os
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = VIA / "VIA_Reports"
OUT = REPORTS / "operator_console"
UIS = VIA / "supportive modules" / "ui_support"
TEMPLATE = UIS / "VIA_UI_OperatorConsole_Template_v0100.html"
PAGE = OUT / "VIA_OperatorConsole_latest.html"
LOCK_NEW = HERE / "VIA_UI_FormatLock_v0100.json"
ENGINE = Path(__file__).stem
OTHER_GROUPS = ("tw_equity", "macro", "etf", "intl")      # 「其他」起始日:統一一個日,可按群改
GROUP_ZH = {"tw_equity": "台股每日交易 · 籌碼", "macro": "總體經濟", "etf": "主動 ETF", "intl": "國際資訊", "financials": "財報"}
PERIODS = ("單季", "累計", "年度")
TW_RX = re.compile(r"^\d{4,6}[A-Z]?$")
INTL_RX = re.compile(r"^[\^A-Za-z0-9_.=\-]{1,24}$")
IDENT_RX = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
DATE_RX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LAMP = {"GREEN": "OK", "OK": "OK", "RED": "FAIL", "FAIL": "FAIL", "CRASH": "FAIL", "ABSENT": "SKIP", "NODATA": "SKIP",
        "AMBER": "SKIP", "YELLOW": "SKIP", "GATED": "UNTESTED", "SKIP": "UNTESTED"}


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


def _newest(folder: Path, pattern: str) -> Path | None:
    hits = [p for p in folder.glob(pattern) if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _json(path: Path | None):
    if not path or not Path(path).exists():
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def _e(v) -> str:
    return _html.escape("" if v is None else str(v))


_MODS: dict = {}


def mod(stem: str):
    """Newest version of a registry engine, loaded once (MDL139 input book · MDL231 chain states · MDL233 pins · MDL123 home)."""
    if stem not in _MODS:
        p = _newest(HERE, stem + "_v*.py")
        _MODS[stem] = _load(p, stem + "_for_" + ENGINE) if p else None
    return _MODS[stem]


# ---------------------------------------------------------------- format lock (TemplateSSOT dashboard → CSS; zero hard-coded style)
def tokens() -> dict:
    book = _json(_newest(HERE, "VIA_UI_TemplateSSOT_v*.json")) or {}
    d, st = book.get("dashboard") or {}, book.get("status") or {}
    keys = ("font_family", "font_pc_px", "font_mobile_px", "panel_w_px", "header_h_px", "breakpoint_px", "color_bg", "color_panel_bg",
            "color_border", "color_grid", "alert_bg", "input_border")
    out = {k: d.get(k) for k in keys}
    out.update({"status_" + k: v for k, v in st.items()})
    out["text"] = (book.get("palette") or {}).get("text")
    out["accent"] = (book.get("palette") or {}).get("accent")
    out["accent_text"] = (book.get("palette") or {}).get("accent_text")
    return out


def css(t: dict) -> str:
    return (f":root{{--pw:{t['panel_w_px']}px;--hh:{t['header_h_px']}px;--bg:{t['color_bg']};--pbg:{t['color_panel_bg']};"
            f"--bd:{t['color_border']};--grid:{t['color_grid']};--alert:{t['alert_bg']};--ib:{t['input_border']};--tx:{t['text']};"
            f"--ac:{t['accent']};--act:{t['accent_text']};--ok:{t['status_OK']};--fail:{t['status_FAIL']};--skip:{t['status_SKIP']};"
            f"--unt:{t['status_UNTESTED']}}}"
            f"*{{box-sizing:border-box}}html,body{{margin:0;height:100%}}"
            f"body{{font-family:{t['font_family']};font-size:{t['font_pc_px']}px;color:var(--tx);background:var(--bg)}}"
            ".wrap{display:flex;height:100vh}"
            "aside{width:var(--pw);min-width:var(--pw);background:var(--pbg);border-right:1px solid var(--bd);overflow:auto}"
            "aside.collapsed{width:0;min-width:0;overflow:hidden;border:0}"
            "main{flex:1;min-width:0;overflow:auto}"
            ".hd{height:var(--hh);display:flex;align-items:center;gap:8px;padding:0 10px;border-bottom:1px solid var(--bd);"
            "font-weight:bold;position:sticky;top:0;background:inherit;z-index:2}"
            "main>.hd{background:var(--bg)}"
            "aside section{padding:8px 10px;border-bottom:1px solid var(--bd)}aside h3,main h3{font-size:1.05em;margin:0 0 6px}"
            "label{display:block;margin:4px 0 2px}input,select,textarea{font:inherit;width:100%;border:1px solid var(--ib);"
            "border-radius:3px;padding:3px 5px;background:#fff}textarea{height:52px;resize:vertical}"
            ".row{display:flex;gap:6px;align-items:center}.row>*{flex:1}.chips{display:flex;flex-wrap:wrap;gap:3px;margin:4px 0}"
            ".chip{border:1px solid var(--bd);border-radius:10px;padding:0 6px;background:#fff;cursor:pointer}"
            ".chip.rm{text-decoration:line-through;color:var(--fail)}.chip.add{border-color:var(--ok);color:var(--ok)}"
            "button{font:inherit;border:1px solid var(--ac);background:var(--ac);color:var(--act);border-radius:3px;padding:3px 8px;"
            "cursor:pointer}button.alt{background:#fff;color:var(--ac)}"
            ".drop{border:1px dashed var(--ib);border-radius:4px;padding:10px;text-align:center;background:#fff}.drop.on{background:var(--alert)}"
            ".tabs{display:flex;gap:2px;padding:4px 8px;border-bottom:1px solid var(--bd);flex-wrap:wrap}"
            ".tabs button{background:#fff;color:var(--tx);border-color:var(--bd)}.tabs button.on{background:var(--ac);color:var(--act)}"
            ".pane{display:none;padding:8px 10px}.pane.on{display:block}"
            "table{border-collapse:collapse;width:100%;margin:4px 0 10px}th,td{border:1px solid var(--grid);padding:2px 5px;text-align:left;"
            "vertical-align:top}th{background:var(--pbg)}"
            ".l{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:3px}.l.OK{background:var(--ok)}"
            ".l.FAIL{background:var(--fail)}.l.SKIP{background:var(--skip)}.l.UNTESTED{background:var(--unt)}"
            ".note{opacity:.75}.warn{background:var(--alert);padding:4px 6px;border:1px solid var(--bd)}code{word-break:break-all}"
            f"@media(max-width:{t['breakpoint_px']}px){{body{{font-size:{t['font_mobile_px']}px}}.wrap{{display:block;height:auto}}"
            "aside{width:auto;min-width:0;border-right:0;border-bottom:1px solid var(--bd)}main{overflow:visible}}")


def skeleton_sha(text: str) -> str:
    """Sha of the page skeleton: the template with the embedded data block removed (format, not content)."""
    body = re.sub(r"<script id=\"ST\" type=\"application/json\">.*?</script>", "", text, flags=re.S)
    return hashlib.sha256(body.replace("\r\n", "\n").encode("utf-8")).hexdigest()[:16]


def format_lock(write: bool = False, page_text: str | None = None) -> dict:
    """GREEN = tokens and skeleton equal the lock; RED = drift (operator relocks with `template --lock`)."""
    t = tokens()
    p = _newest(HERE, "VIA_UI_FormatLock_v*.json")
    book = _json(p) or {}
    tpl = page_text if page_text is not None else (TEMPLATE.read_text(encoding="utf-8") if TEMPLATE.exists() else "")
    sha = skeleton_sha(tpl) if tpl else ""
    if write:
        book = {"schema": "VIA.UI.FormatLock.v1", "engine": ENGINE, "template": str(TEMPLATE.relative_to(VIA)),
                "source": "VIA_UI_TemplateSSOT_v0100.json#dashboard + #status", "tokens": t, "skeleton_sha": sha,
                "layout": "左面板(輸入)var(--pw) + 右主區(輸入摘要 · 引擎狀況 · 運作摘要 · 輸出 · 資料庫);左右表頭同高 var(--hh);"
                          "≤breakpoint 上下疊;左面板可收合",
                "rule": "樣式值只由 TemplateSSOT 生成;冊值或骨架一變 = RED,操作員確認後 template --lock 重鎖(新版號冊)",
                "locked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        (p or LOCK_NEW).write_text(json.dumps(book, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="")
    drift = [k for k, v in t.items() if (book.get("tokens") or {}).get(k) != v]
    state = "ABSENT" if not book else ("GREEN" if not drift and book.get("skeleton_sha") == sha else "RED")
    return {"state": state, "drift": drift, "sha": sha, "locked_sha": book.get("skeleton_sha"), "book": p.name if p else None}


# ---------------------------------------------------------------- inputs (MDL139 input book; writes only through its apply_set)
def norm_code(s) -> str:
    return unicodedata.normalize("NFKC", str(s or "")).strip().upper()


def split_codes(text) -> list:
    if isinstance(text, (list, tuple)):
        text = ",".join(map(str, text))
    return [c for c in (norm_code(x) for x in re.split(r"[\s,;、,;]+", str(text or ""))) if c]


def inputs_state() -> dict:
    m = mod("CGC_MDL139_InputConsole")
    spec = m.load_spec() if m else {}
    u = spec.get("user") or {}
    dom = m.tw_codes(spec) if m else []
    intl = m.intl_matrix(spec) if m else []
    foreign = [r["id"] for r in intl if r.get("section") == "INTL_FIN" and r.get("kind") == "ticker" and r.get("state") == "現有"]
    starts = dict(u.get("group_starts") or {})
    default = (spec.get("defaults") or {}).get("start") or ""
    vrn_in = ((spec.get("families") or {}).get("vrn") or {}).get("input") or {}
    fin = u.get("fin") or {}
    fm = []
    fmp = _newest(HERE / "VIA_NumberBooks", "VIA_NumberBook_FM_v*.jsonl")
    for line in (fmp.read_text(encoding="utf-8").splitlines() if fmp else []):
        if line.strip():
            fm.append(json.loads(line))
    have = {r["code"] for r in dom}
    cand_d = [{"code": (r.get("cols") or {}).get("ticker"), "name": r.get("name"), "market": (r.get("cols") or {}).get("exchange")}
              for r in fm if r.get("region") == "TW" and r.get("asset") == "EQT" and (r.get("cols") or {}).get("ticker") not in have]
    daily = [r["id"] for r in intl if r.get("section") == "INTL_DAILY" and r.get("kind") == "ticker"]
    fset = {norm_code(c) for c in foreign}
    cand_f = sorted({norm_code((r.get("cols") or {}).get("yfinance") or (r.get("cols") or {}).get("ticker"))
                     for r in fm if r.get("region") != "TW" and r.get("asset") in ("EQT", "ETF")} | {norm_code(c) for c in daily}) 
    cand_f = [c for c in cand_f if c and c not in fset]
    return {"domestic": [{"code": r["code"], "name": r.get("name"), "market": r.get("market"), "source": r.get("source")} for r in dom],
            "cand_domestic": sorted(cand_d, key=lambda r: r["code"] or ""), "cand_foreign": cand_f,
            "foreign": foreign, "period": {"當季": "單季"}.get(fin.get("period"), fin.get("period") or "年度"),
            "fin_from": fin.get("year_from") or "", "fin_to": fin.get("year_to") or "", "fin_start": starts.get("financials") or default,
            "default_start": default, "groups": [{"id": g, "zh": GROUP_ZH[g], "start": starts.get(g) or default} for g in OTHER_GROUPS],
            "vrn_dir": u.get("vrn_dir") or "", "vrn_incoming": vrn_in.get("incoming") or "",
            "changelog": (u.get("changelog") or [])[-10:], "book": "VIA_InputConsole_Spec_v0100.json", "ok": m is not None}


def dedup(packet: dict, state: dict) -> dict:
    """Input summary with dedup: every duplicate / no-op / conflict listed, each code sent once."""
    have_d = {r["code"] for r in state["domestic"]}
    have_f = {norm_code(c) for c in state["foreign"]}
    out = {"send": {}, "dropped": [], "invalid": [], "counts": {}}

    def one(key, codes, rx, have, add):
        seen, keep = set(), []
        for c in split_codes(codes):
            if c in seen:
                out["dropped"].append({"key": key, "code": c, "why": "同一批重複"})
                continue
            seen.add(c)
            if not rx.match(c):
                out["invalid"].append({"key": key, "code": c, "why": "代碼格式不合"})
            elif add and c in have:
                out["dropped"].append({"key": key, "code": c, "why": "已在冊(不重加)"})
            elif not add and c not in have:
                out["dropped"].append({"key": key, "code": c, "why": "不在冊(無從移除)"})
            else:
                keep.append(c)
        out["send"][key] = keep
    one("domestic_add", packet.get("domestic_add"), TW_RX, have_d, True)
    one("domestic_remove", packet.get("domestic_remove"), TW_RX, have_d, False)
    one("foreign_add", packet.get("foreign_add"), INTL_RX, have_f, True)
    one("foreign_remove", packet.get("foreign_remove"), INTL_RX, have_f, False)
    both = set(out["send"]["domestic_add"]) & set(out["send"]["foreign_add"])
    for c in sorted(both):
        out["dropped"].append({"key": "foreign_add", "code": c, "why": "國內國外兩邊都加(留國內)"})
    out["send"]["foreign_add"] = [c for c in out["send"]["foreign_add"] if c not in both]
    clash = set(out["send"]["domestic_add"]) & set(out["send"]["domestic_remove"])
    for c in sorted(clash):
        out["dropped"].append({"key": "domestic", "code": c, "why": "同一批又加又刪(兩個都不送)"})
    out["send"]["domestic_add"] = [c for c in out["send"]["domestic_add"] if c not in clash]
    out["send"]["domestic_remove"] = [c for c in out["send"]["domestic_remove"] if c not in clash]
    groups = {}
    unified = packet.get("start_all") or ""
    for g in OTHER_GROUPS:
        d = (packet.get("group_starts") or {}).get(g) or unified
        cur = next((x["start"] for x in state["groups"] if x["id"] == g), "")
        if d and (d == "latest" or DATE_RX.match(d)):
            if d == cur:
                out["dropped"].append({"key": "group_start", "code": g, "why": f"與冊上相同({d})"})
            else:
                groups[g] = d
        elif d:
            out["invalid"].append({"key": "group_start", "code": g, "why": f"日期格式不合({d})"})
    out["send"]["group_starts"] = groups
    files, fseen = [], set()
    for f in packet.get("vrn_files") or []:
        k = (str(f.get("name")), int(f.get("size") or 0))
        if k in fseen:
            out["dropped"].append({"key": "vrn_files", "code": k[0], "why": "拖曳同名同大小"})
            continue
        fseen.add(k)
        files.append({"name": k[0], "size": k[1]})
    out["send"]["vrn_files"] = files
    for k in ("period", "fin_from", "fin_to", "fin_start", "vrn_dir"):
        if packet.get(k):
            out["send"][k] = packet[k]
    out["counts"] = {k: len(v) if isinstance(v, (list, dict)) else 1 for k, v in out["send"].items()}
    out["counts"].update(dropped=len(out["dropped"]), invalid=len(out["invalid"]))
    return out


def to_ops(send: dict) -> dict:
    """Deduped packet → MDL139 apply_set keys (repeat keys get #n, as MDL139's own page does)."""
    ops, n = {}, {}

    def put(k, v):
        i = n.get(k, 0)
        ops[k + (f"#{i}" if i else "")] = v
        n[k] = i + 1
    for c in send.get("domestic_add") or []:
        put("tw-add", c)
    for c in send.get("domestic_remove") or []:
        put("tw-remove", c)
    for c in send.get("foreign_add") or []:
        put("intl-add", "INTL_FIN:" + c)
    for c in send.get("foreign_remove") or []:
        put("intl-remove", "INTL_FIN:" + c)
    if send.get("period"):
        put("fin-period", send["period"])
    if send.get("fin_from"):
        put("fin-from", send["fin_from"])
    if send.get("fin_to"):
        put("fin-to", send["fin_to"])
    if send.get("fin_start"):
        put("group-start", "financials:" + send["fin_start"])
    for g, d in (send.get("group_starts") or {}).items():
        put("group-start", f"{g}:{d}")
    if send.get("vrn_dir"):
        put("vrn-dir", send["vrn_dir"])
    return ops


def apply(packet: dict, write: bool = False) -> dict:
    m = mod("CGC_MDL139_InputConsole")
    state = inputs_state()
    summ = dedup(packet, state)
    ops = to_ops(summ["send"])
    res = {"summary": summ, "ops": ops, "apply": write, "notes": []}
    if not m:
        res["notes"] = ["FAIL:CGC_MDL139 尾版不在"]
        return res
    if ops and write:
        spec = m.load_spec()
        res["notes"] = m.apply_set(spec, ops)
        m.save_spec(spec)
    else:
        res["notes"] = ["DRY:乾跑,沒寫冊(--apply 才寫)" if ops else "NOOP:去重後沒有要送的改動"]
    return res


# ---------------------------------------------------------------- engine status · run summary
def engine_status() -> dict:
    m231 = mod("CGC_MDL231_MatrixPages")
    out = {"chains": [], "tools": [], "gate": "", "lock": {}}
    for fam, path, key in (("VDF", REPORTS / "vdf_chain" / "VDFCHAIN_latest.json", "id"),
                           ("VRN", REPORTS / "vrn_chain" / "VRNCHAIN_latest.json", "name")):
        doc = _json(path)
        states = m231.chain_states(doc, key) if (m231 and doc) else {}
        tally = {}
        for s in states.values():
            tally[s] = tally.get(s, 0) + 1
        bad = [f"{k}:{v}" for k, v in states.items() if v not in ("GREEN", "GATED")]
        out["chains"].append({"family": fam, "generated": (doc or {}).get("generated", "—"), "tally": tally, "not_green": bad[:12],
                              "lamp": "FAIL" if "RED" in tally or "CRASH" in tally else ("OK" if states and not bad else "SKIP")})
    act = mod("CGC_MDL233_ToolActivate")
    for fam in ("accelerator", "network"):
        p = act.pinned(fam) if act else None
        out["tools"].append({"family": fam, "file": p.name if p else "—", "lamp": "OK" if p else "FAIL"})
    side = _json(REPORTS / "sweep" / "SWEEP_SIDE_latest.json") or {}
    out["gate"] = (side.get("flow") or {}).get("line") if isinstance(side.get("flow"), dict) else str(side.get("flow") or "—")
    lb = _newest(HERE, "VIA_LampLock_v*.json")
    book = _json(lb) or {}
    out["lock"] = {"book": lb.name if lb else "—", "locked": len(book.get("locked") or []),
                   "nodes": sum(len(v) for v in (book.get("nodes") or {}).values()),
                   "open": sum(len(v) for v in (book.get("nodes_open") or {}).values())}
    return out


def run_summary(state: dict) -> dict:
    side = _json(REPORTS / "sweep" / "SWEEP_SIDE_latest.json") or {}
    steps = [{"id": s.get("id"), "title": s.get("title"), "rc": s.get("rc"), "sec": s.get("sec"), "at": s.get("started_utc")}
             for s in side.get("steps") or []]
    return {"ts": side.get("ts") or "—", "head": side.get("head") or "—", "steps": steps, "changelog": state.get("changelog") or []}


# ---------------------------------------------------------------- data home: Parquet unified, DuckDB manages (VIEW over read_parquet)
def data_home(override: str | None = None) -> tuple:
    if override:
        return Path(override), "--home"
    m = mod("CGC_MDL123_DataHome")
    if not m:
        return None, "CGC_MDL123 尾版不在"
    h, src = m.resolve_home(VIA)
    ok, why = m.home_usable(h)
    return (h, src) if ok else (None, f"資料家不可用:{why}({src})")


def _duckdb():
    try:
        import duckdb
        return duckdb
    except ImportError:
        return None


def _q(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def parquet_plan(home: Path) -> list:
    duckdb = _duckdb()
    rows = []
    if duckdb is None or home is None or not Path(home).exists():
        return rows
    dbs = sorted(p for p in Path(home).glob("*.duckdb") if p.name != "VIA_Parquet_Catalog.duckdb")
    dbs += sorted(p for p in Path(home).glob("*/*.duckdb") if p.parent.name != "parquet")
    for db in dbs:
        con = duckdb.connect(str(db), read_only=True)
        try:
            for (t,) in con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main' "
                                    "AND table_type='BASE TABLE' ORDER BY 1").fetchall():
                n = con.execute(f"SELECT COUNT(*) FROM {_q(t)}").fetchone()[0]
                out = Path(home) / "parquet" / db.stem / f"{t}.parquet"
                rows.append({"db": db.stem, "table": t, "rows": n, "src": str(db), "parquet": str(out), "view": f"{db.stem}__{t}",
                             "exists": out.exists()})
        finally:
            con.close()
    return rows


def parquet_apply(home: Path, plan: list) -> dict:
    duckdb = _duckdb()
    done, bad = [], []
    for r in plan:
        out = Path(r["parquet"])
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".parquet.part")
        con = duckdb.connect(r["src"], read_only=True)         # source store opened read-only: not one bit changes
        try:
            con.execute(f"COPY (SELECT * FROM {_q(r['table'])}) TO '{tmp.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        finally:
            con.close()
        back = duckdb.connect().execute(f"SELECT COUNT(*) FROM read_parquet('{tmp.as_posix()}')").fetchone()[0]
        if back != r["rows"]:
            bad.append({**r, "why": f"讀回 {back} ≠ {r['rows']}"})
            tmp.unlink()
            continue
        os.replace(tmp, out)
        done.append(r)
    cat = Path(home) / "VIA_Parquet_Catalog.duckdb"
    con = duckdb.connect(str(cat))
    try:
        con.execute("CREATE TABLE IF NOT EXISTS _via_catalog(view VARCHAR PRIMARY KEY, db VARCHAR, tbl VARCHAR, rows BIGINT, "
                    "parquet VARCHAR, updated_at VARCHAR)")
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for r in done:
            con.execute(f"CREATE OR REPLACE VIEW {_q(r['view'])} AS SELECT * FROM read_parquet('{Path(r['parquet']).as_posix()}')")
            con.execute("INSERT OR REPLACE INTO _via_catalog VALUES (?, ?, ?, ?, ?, ?)",
                        [r["view"], r["db"], r["table"], r["rows"], r["parquet"], stamp])
    finally:
        con.close()
    return {"written": len(done), "failed": bad, "catalog": str(cat)}


def catalog_views(home: Path | None, preview: int = 5) -> list:
    duckdb = _duckdb()
    cat = Path(home) / "VIA_Parquet_Catalog.duckdb" if home else None
    if duckdb is None or not cat or not cat.exists():
        return []
    con = duckdb.connect(str(cat), read_only=True)
    out = []
    try:
        for view, db, tbl, rows, pq, upd in con.execute("SELECT view, db, tbl, rows, parquet, updated_at FROM _via_catalog ORDER BY 1").fetchall():
            try:
                cols = [(c[0], c[1]) for c in con.execute(f"DESCRIBE {_q(view)}").fetchall()]
                sample = con.execute(f"SELECT * FROM {_q(view)} LIMIT {int(preview)}").fetchall()
                lamp = "OK"
            except Exception as exc:                          # the parquet under a view went missing: say so, keep listing
                cols, sample, lamp = [], [], "FAIL"
                upd = f"讀不到:{type(exc).__name__}"
            dcol = next((c for c, t in cols if c.lower() in ("date", "trade_date", "dt", "report_date")), "")
            rng = con.execute(f"SELECT MIN({_q(dcol)}), MAX({_q(dcol)}) FROM {_q(view)}").fetchone() if dcol and lamp == "OK" else None
            out.append({"view": view, "db": db, "table": tbl, "rows": rows, "parquet": pq, "updated_at": upd, "cols": cols,
                        "date_col": dcol, "range": [str(x) for x in rng] if rng else [], "sample": [[str(x) for x in s] for s in sample],
                        "lamp": lamp})
    finally:
        con.close()
    return out


def mdl228_catalog(home: Path | None, views: list | None = None) -> dict:
    """The Parquet catalog in the shape CGC_MDL228 export reads (dbs[] → tables[] with date_col / lo / hi)."""
    cat = Path(home) / "VIA_Parquet_Catalog.duckdb" if home else None
    views = views if views is not None else catalog_views(home, preview=0)
    return {"dbs": [{"name": cat.name, "path": str(cat), "tables": [
        {"table": v["view"], "date_col": v["date_col"], "lo": (v["range"] or [""])[0], "hi": (v["range"] or ["", ""])[-1],
         "rows": v["rows"]} for v in views]}]} if cat else {"dbs": []}


EXPORT_FORMATS = {"csv": "CSV · utf-8-sig(Excel 直開不亂碼)", "big5": "CSV · Big5 / cp950(舊系統;失真字照數)",
                  "gsheet": "Google Sheet 匯入 CSV · utf-8", "json": "JSON · utf-8", "md": "Markdown 表 · utf-8",
                  "parquet": "Parquet · zstd(全量最省)"}


def extract(home: Path, view: str, cols=None, start: str = "", end: str = "", fmt: str = "parquet", limit: int = 0,
            dry: bool = False) -> dict:
    """Pick a VIEW, tick columns, a date range and a format; the writing is CGC_MDL228 export (one writer: formats · encodings ·
    caps · read-back), reading the Parquet catalog read-only."""
    m228 = mod("CGC_MDL228_VIADBManager")
    if m228 is None:
        return {"state": "ABSENT", "why": "CGC_MDL228 尾版不在"}
    if fmt not in EXPORT_FORMATS:
        return {"state": "BAD_PARAM", "why": f"格式只收 {', '.join(EXPORT_FORMATS)}"}
    cat = mdl228_catalog(home)
    if not cat["dbs"] or not Path(cat["dbs"][0]["path"]).exists():
        return {"state": "ABSENT", "why": "管家庫不在:先 parquet --apply"}
    return m228.export(cat, cat["dbs"][0]["name"], view, cols or None, start, end, fmt, limit or None, dry, out=OUT)


# ---------------------------------------------------------------- page (template = same skeleton, no data)
# ---------------------------------------------------------------- the two folders (the only things the operator chooses; Windows dialog)
PATHS = OUT / "OPERATOR_PATHS.json"          # under VIA_Reports (git-ignored): machine-local, never a tracked file


def folders() -> dict:
    saved = _json(PATHS) or {}
    home, why = data_home(saved.get("data") or None)
    return {"system": saved.get("system") or str(VIA), "data": str(home) if home else (saved.get("data") or ""),
            "data_ok": home is not None and Path(home).exists(), "why": why, "saved": bool(saved),
            "picked_at": saved.get("picked_at", "")}


# ---------------------------------------------------------------- overview: one page, three colours
ORDER = {"FAIL": 0, "SKIP": 1, "UNTESTED": 2, "OK": 3}


def lock_regressions() -> dict:
    m = mod("CGC_MDL231_MatrixPages")
    try:
        base = m._PRIOR._PRIOR if hasattr(m, "_PRIOR") and hasattr(m._PRIOR, "_PRIOR") else m
        tail = base.sweep_tail()
        side = base._load_json(base.SIDE)
        rep = tail.build(side) if (tail and side) else {"sections": []}
        book, name = base.lock_book()
        lk = base.lock_check(book, base.lamp_states(rep.get("sections") or []), base.chain_states(base._load_json(base.VDF_CHAIN), "id"),
                             base.chain_states(base._load_json(base.VRN_CHAIN), "name"))
        return {"book": name, "regress": lk["regress"], "held": lk["held"], "add": lk["add"], "unmeasured": lk["unmeasured"]}
    except Exception as exc:
        return {"book": None, "regress": [], "held": 0, "add": [], "unmeasured": 0, "why": f"{type(exc).__name__}: {str(exc)[:80]}"}


def overview(d: dict) -> list:
    st, fl, fo = d.get("status") or {}, d.get("format_lock") or {}, d.get("folders") or {}
    rows = []
    gate = str(st.get("gate") or "")
    rows.append(("VCGC 流程閘", "OK" if "政策過" in gate else ("UNTESTED" if gate in ("", "—", "None") else "FAIL"), gate or "還沒跑全景實測", "p_run"))
    for c in st.get("chains") or []:
        rows.append((f"{c['family']} 鏈", c["lamp"], " · ".join(f"{k} {v}" for k, v in sorted(c["tally"].items())) or "沒有報告", "p_eng"))
    tools = st.get("tools") or []
    rows.append(("工具(加速器 · 網路)", "OK" if tools and all(x["lamp"] == "OK" for x in tools) else "FAIL",
                 " · ".join(f"{x['family']} {x['file']}" for x in tools), "p_eng"))
    lk = d.get("lock") or {}
    rows.append(("燈鎖(成功的鎖住)", "FAIL" if lk.get("regress") else ("OK" if lk.get("book") else "UNTESTED"),
                 (f"回歸 {len(lk['regress'])}:" + "、".join(lk["regress"][:4])) if lk.get("regress") else
                 f"守住 {lk.get('held', 0)} · 可加鎖 {len(lk.get('add') or [])} · {lk.get('book') or lk.get('why', '')}", "p_chk"))
    rows.append(("版面鎖", {"GREEN": "OK", "RED": "FAIL"}.get(fl.get("state"), "UNTESTED"), f"{fl.get('state')} · sha {fl.get('sha')}", "p_chk"))
    rows.append(("資料庫資料夾", "OK" if fo.get("data_ok") else "SKIP", fo.get("data") or fo.get("why") or "未選", "p_out"))
    plan = d.get("plan") or []
    done = sum(1 for r in plan if r["exists"])
    rows.append(("輸出統一 Parquet", "UNTESTED" if not plan else ("OK" if done == len(plan) else "SKIP"),
                 f"{done}/{len(plan)} 表已是 parquet" if plan else "資料家沒有庫(或未選)", "p_out"))
    views = d.get("views") or []
    rows.append(("DuckDB 管家", "UNTESTED" if not views else ("FAIL" if any(v["lamp"] != "OK" for v in views) else "OK"),
                 f"{len(views)} 個 VIEW · {sum(v['rows'] for v in views):,} 列" if views else "還沒建(parquet --apply)", "p_db"))
    inp = d.get("inputs") or {}
    last = (inp.get("changelog") or [{}])[-1]
    rows.append(("輸入冊", "OK" if inp.get("ok") else "FAIL",
                 f"國內 {len(inp.get('domestic') or [])} · 國外 {len(inp.get('foreign') or [])} · {inp.get('period')} · 最近改 {last.get('ts', '—')}", "p_sum"))
    return rows


# ---------------------------------------------------------------- page (template = same skeleton, no data)
_JS = r"""
(function(){
var ST=JSON.parse(document.getElementById('ST').textContent||'{}');var KEY='via-operator-console-draft';
var ch=null;try{ch=new BroadcastChannel('via-operator-console');}catch(e){}
function $(id){return document.getElementById(id);}
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function vals(sel,on){return [].slice.call(document.querySelectorAll(sel)).filter(function(i){return i.checked===on;}).map(function(i){return i.value;});}
var FILES=[];
function draft(){var g={};document.querySelectorAll('.gs').forEach(function(i){var id=i.getAttribute('data-g');var lt=$('gl_'+id);if(lt&&lt.checked)g[id]='latest';else if(i.value)g[id]=i.value;});
 return {domestic_add:vals('#cd input',true),domestic_remove:vals('#dd input',false),foreign_add:vals('#cf input',true),foreign_remove:vals('#df input',false),
  period:(document.querySelector('input[name=period]:checked')||{}).value||'',fin_from:$('fin_from').value,fin_to:$('fin_to').value,fin_start:$('fin_start').value,
  start_all:$('sa_latest').checked?'latest':$('start_all').value,group_starts:g,vrn_files:FILES};}
function restore(d){if(!d)return;var set=function(sel,list,on){var L={};(list||[]).forEach(function(c){L[c]=1;});document.querySelectorAll(sel).forEach(function(i){if(L[i.value])i.checked=on;});};
 set('#cd input',d.domestic_add,true);set('#dd input',d.domestic_remove,false);set('#cf input',d.foreign_add,true);set('#df input',d.foreign_remove,false);
 if(d.period){var r=document.querySelector('input[name=period][value="'+d.period+'"]');if(r)r.checked=true;}
 ['fin_from','fin_to','fin_start'].forEach(function(k){if(d[k])$(k).value=d[k];});if(d.start_all==='latest')$('sa_latest').checked=true;else if(d.start_all)$('start_all').value=d.start_all;
 document.querySelectorAll('.gs').forEach(function(i){var id=i.getAttribute('data-g');var v=(d.group_starts||{})[id];if(v==='latest')$('gl_'+id).checked=true;else if(v)i.value=v;});FILES=d.vrn_files||[];}
function save(){var d=draft();try{localStorage.setItem(KEY,JSON.stringify(d));}catch(e){}if(ch)ch.postMessage(d);summary();}
function summary(){var d=draft(),drop=[];var fs={},fk=[];(d.vrn_files||[]).forEach(function(f){var k=f.name+'|'+f.size;if(fs[k]){drop.push(['VRN 拖曳',f.name,'同名同大小']);return;}fs[k]=1;fk.push(f);});
 var gs={};(ST.inputs.groups||[]).forEach(function(g){var v=d.group_starts[g.id]||d.start_all;if(!v)return;if(v===g.start)drop.push(['其他群起始',g.zh,'與冊上相同('+v+')']);else gs[g.id]=v;});
 var fa=d.foreign_add.filter(function(c){if(d.domestic_add.indexOf(c)>=0){drop.push(['國外新增',c,'國內國外兩邊都勾(留國內)']);return false;}return true;});
 var rows=[['國內新增',d.domestic_add],['國內移除',d.domestic_remove],['國外新增',fa],['國外移除',d.foreign_remove],['財報期別',[d.period]],
  ['財報起迄年',[d.fin_from&&(d.fin_from+'–'+(d.fin_to||''))]],['財報起始日',[d.fin_start]],['其他群起始',Object.keys(gs).map(function(k){return k+':'+gs[k];})],['VRN 拖曳',fk.map(function(f){return f.name;})]];
 var h='<table><tr><th>項</th><th>要送(去重後)</th><th>數</th></tr>';rows.forEach(function(r){var v=(r[1]||[]).filter(Boolean);h+='<tr><td>'+r[0]+'</td><td>'+esc(v.join(', '))+'</td><td>'+v.length+'</td></tr>';});
 h+='</table><h3>去掉的('+drop.length+')</h3><table><tr><th>項</th><th>內容</th><th>為什麼</th></tr>'+drop.map(function(x){return '<tr><td>'+esc(x[0])+'</td><td>'+esc(x[1])+'</td><td>'+esc(x[2])+'</td></tr>';}).join('')+'</table>';
 $('sum').innerHTML=h;$('files').innerHTML=fk.map(function(f){return '<span class="chip">'+esc(f.name)+'</span>';}).join('');}
function exportPacket(){var d=draft();var b=new Blob([JSON.stringify(d,null,1)],{type:'application/json'});var a=document.createElement('a');a.href=URL.createObjectURL(b);
 a.download='via_operator_input.json';a.click();show(ST.cmd_apply);}
function show(t){$('cmd').textContent=t;try{navigator.clipboard.writeText(t);}catch(e){}}
function filt(inp){var q=inp.value.trim().toUpperCase();var box=$(inp.getAttribute('data-for'));box.querySelectorAll('label').forEach(function(l){l.style.display=(!q||l.textContent.toUpperCase().indexOf(q)>=0)?'':'none';});}
function tabs(){document.querySelectorAll('.tabs button').forEach(function(b){b.onclick=function(){go(b.getAttribute('data-p'));};});
 document.querySelectorAll('[data-go]').forEach(function(a){a.onclick=function(){go(a.getAttribute('data-go'));};});
 var t=null;try{t=localStorage.getItem(KEY+'-tab');}catch(e){}if(t&&$(t))go(t);}
function go(id){document.querySelectorAll('.tabs button').forEach(function(x){x.classList.toggle('on',x.getAttribute('data-p')===id);});
 document.querySelectorAll('.pane').forEach(function(p){p.classList.toggle('on',p.id===id);});try{localStorage.setItem(KEY+'-tab',id);}catch(e){}}
function xview(){var v=$('x_view').value;var info=(ST.views||[]).filter(function(x){return x.view===v;})[0];var h='';
 if(info){h=info.cols.map(function(c){return '<label class="ck"><input type="checkbox" class="xc" value="'+esc(c[0])+'" checked> '+esc(c[0])+' <span class="note">'+esc(c[1])+'</span></label>';}).join('');
  $('x_start').value=(info.range||[])[0]||'';$('x_end').value=(info.range||[])[1]||'';$('x_dates').style.display=info.date_col?'':'none';$('x_dcol').textContent=info.date_col||'';}
 $('x_cols').innerHTML=h;document.querySelectorAll('.xc').forEach(function(c){c.onchange=xcmd;});xcmd();}
function xcmd(){var v=$('x_view').value;if(!v){$('x_cmd').textContent='';return;}var cols=vals('.xc',true);var all=document.querySelectorAll('.xc').length;
 var c=[ST.cmd_extract,'--view',v];if(cols.length&&cols.length<all)c.push('--cols',cols.join(','));
 if($('x_dates').style.display!=='none'){if($('x_start').value)c.push('--start',$('x_start').value);if($('x_end').value)c.push('--end',$('x_end').value);}
 var f=(document.querySelector('input[name=xfmt]:checked')||{}).value||'parquet';c.push('--format',f);if($('x_limit').value)c.push('--limit',$('x_limit').value);$('x_cmd').textContent=c.join(' ');}
document.addEventListener('DOMContentLoaded',function(){var d=null;try{d=JSON.parse(localStorage.getItem(KEY)||'null');}catch(e){}restore(d);
 document.querySelectorAll('aside input,aside select').forEach(function(i){if(i.classList.contains('flt'))return;i.addEventListener('change',save);});
 document.querySelectorAll('input.flt').forEach(function(i){i.addEventListener('input',function(){filt(i);});});
 if(ch)ch.onmessage=function(ev){restore(ev.data);summary();};
 $('toggle').onclick=function(){$('side').classList.toggle('collapsed');};$('export').onclick=exportPacket;
 $('pick_dirs').onclick=function(){show(ST.cmd_pick_dirs);};$('pick_vrn').onclick=function(){show(ST.cmd_pick_vrn);};$('run_all').onclick=function(){show(ST.cmd_run_all);};
 var dz=$('drop');dz.ondragover=function(e){e.preventDefault();dz.classList.add('on');};dz.ondragleave=function(){dz.classList.remove('on');};
 dz.ondrop=function(e){e.preventDefault();dz.classList.remove('on');[].slice.call(e.dataTransfer.files||[]).forEach(function(f){FILES.push({name:f.name,size:f.size});});save();};
 $('pick').onchange=function(e){[].slice.call(e.target.files||[]).forEach(function(f){FILES.push({name:f.webkitRelativePath||f.name,size:f.size});});save();};
 $('clear_files').onclick=function(){FILES=[];save();};
 $('x_view').onchange=xview;['x_start','x_end','x_limit'].forEach(function(k){$(k).onchange=xcmd;});document.querySelectorAll('input[name=xfmt]').forEach(function(r){r.onchange=xcmd;});
 $('x_copy').onclick=function(){try{navigator.clipboard.writeText($('x_cmd').textContent);}catch(e){}};tabs();summary();xview();});
})();
"""


def _lamp(k: str, text: str = "") -> str:
    zh = {"OK": "綠", "SKIP": "黃", "FAIL": "紅", "UNTESTED": "灰"}.get(k, k)
    return f"<span class='l {_e(k)}'></span>{zh}{(' ' + _e(text)) if text else ''}"


def _box(bid: str, items: list, checked: bool) -> str:
    return (f"<input class='flt' data-for='{bid}' placeholder='篩選(可不填)'><div class='list' id='{bid}'>"
            + "".join(f"<label class='ck'><input type='checkbox' value='{_e(c)}'{' checked' if checked else ''}> {_e(c)} <span class='note'>{_e(n)}</span></label>"
                      for c, n in items) + "</div>")


def page_html(data: dict | None, t: dict) -> str:
    """One skeleton for the live page and the committed template (template = ST {} and empty lists)."""
    d = data or {}
    inp = d.get("inputs") or {"domestic": [], "foreign": [], "cand_domestic": [], "cand_foreign": [], "period": "年度",
                              "groups": [{"id": g, "zh": GROUP_ZH[g], "start": ""} for g in OTHER_GROUPS]}
    st, runs, views, fo = d.get("status") or {}, d.get("runs") or {}, d.get("views") or [], d.get("folders") or {}
    ov = overview(d) if data else []
    worst = min((r[1] for r in ov), key=lambda k: ORDER.get(k, 9)) if ov else "UNTESTED"
    this_year = datetime.now().year
    years = "".join(f"<option{' selected' if str(y) == str(sel) else ''}>{y}</option>" for sel in [None] for y in range(this_year, 1999, -1))
    yopt = lambda sel: "<option value=''>—</option>" + "".join(f"<option{' selected' if str(y) == str(sel) else ''}>{y}</option>" for y in range(this_year, 1999, -1))
    per = "".join(f"<label class='ck' style='display:inline-block'><input type='radio' name='period' value='{p}'{' checked' if inp.get('period') == p else ''}> {p}</label>"
                  for p in PERIODS)
    grp = "".join(f"<div class='row'><label style='flex:0 0 42%'>{_e(g['zh'])}<br><span class='note'>冊上 {_e(g['start'] or '—')}</span></label>"
                  f"<input type='date' class='gs' data-g='{_e(g['id'])}'><label class='ck' style='flex:0 0 22%'><input type='checkbox' id='gl_{_e(g['id'])}'> 最新</label></div>"
                  for g in inp["groups"])
    ovrows = "".join(f"<tr><td>{_lamp(k)}</td><td><a href='#' data-go='{tab}'>{_e(n)}</a></td><td>{_e(txt)}</td></tr>" for n, k, txt, tab in ov)
    chains = "".join(f"<tr><td>{_e(c['family'])}</td><td>{_lamp(c['lamp'], ' · '.join(f'{k} {v}' for k, v in sorted(c['tally'].items())))}</td>"
                     f"<td>{_e(c['generated'])}</td><td>{_e(', '.join(c['not_green']))}</td></tr>" for c in st.get("chains") or [])
    tools = "".join(f"<tr><td>{_e(x['family'])}</td><td>{_lamp(x['lamp'], x['file'])}</td></tr>" for x in st.get("tools") or [])
    lk, fl = d.get("lock") or {}, d.get("format_lock") or {}
    chk_rows = (f"<tr><td>燈鎖冊</td><td>{_e(lk.get('book'))}</td><td>守住 {_e(lk.get('held'))} · 未量 {_e(lk.get('unmeasured'))} · 可加鎖 {_e(', '.join(lk.get('add') or []))}</td></tr>"
                + "".join(f"<tr><td>{_lamp('FAIL')} 回歸</td><td colspan='2'>{_e(r)}</td></tr>" for r in lk.get("regress") or [])
                + f"<tr><td>版面鎖</td><td>{_lamp({'GREEN': 'OK', 'RED': 'FAIL'}.get(fl.get('state'), 'UNTESTED'), fl.get('state') or '')}</td>"
                  f"<td>{_e(fl.get('book'))} · 骨架 sha {_e(fl.get('sha'))} / 鎖 {_e(fl.get('locked_sha'))} · 漂移 {_e(', '.join(fl.get('drift') or []) or '0')}</td></tr>")
    steps = "".join(f"<tr><td>{_e(s['title'])}</td><td>{_lamp('OK' if s['rc'] == 0 else 'FAIL' if s['rc'] == 1 else 'SKIP', 'rc ' + str(s['rc']))}</td>"
                    f"<td>{_e(s['sec'])}s</td><td>{_e(s['at'])}</td></tr>" for s in runs.get("steps") or [])
    clog = "".join(f"<tr><td>{_e(c.get('ts'))}</td><td>{_e(json.dumps(c.get('ops'), ensure_ascii=False)[:160])}</td>"
                   f"<td>{_e('; '.join(c.get('notes') or [])[:160])}</td></tr>" for c in reversed(runs.get("changelog") or []))
    plan = d.get("plan") or []
    prow = "".join(f"<tr><td>{_e(r['db'])}</td><td>{_e(r['table'])}</td><td>{r['rows']:,}</td><td>{_lamp('OK' if r['exists'] else 'SKIP', '已是 parquet' if r['exists'] else '待寫')}</td>"
                   f"<td><code>{_e(r['parquet'])}</code></td></tr>" for r in plan)
    vrow = "".join(f"<tr><td>{_lamp(v['lamp'])}</td><td>{_e(v['view'])}</td><td>{v['rows']:,}</td><td>{_e(v['date_col'])} {_e(' → '.join(v['range']))}</td>"
                   f"<td>{len(v['cols'])}</td><td>{_e(v['updated_at'])}</td></tr>" for v in views)
    vopt = "<option value=''>(選一個)</option>" + "".join(f"<option>{_e(v['view'])}</option>" for v in views)
    fmts = "".join(f"<label class='ck'><input type='radio' name='xfmt' value='{k}'{' checked' if k == 'parquet' else ''}> {_e(v)}</label>" for k, v in EXPORT_FORMATS.items())
    samples = "".join(f"<h3>{_e(v['view'])}</h3><table><tr>{''.join('<th>' + _e(c) + '</th>' for c, _ in v['cols'])}</tr>"
                      + "".join("<tr>" + "".join(f"<td>{_e(x)}</td>" for x in s) + "</tr>" for s in v["sample"]) + "</table>" for v in views[:30])
    st_json = json.dumps({"inputs": {"groups": inp["groups"]}, "views": views, **{k: d.get(k, "") for k in (
        "cmd_apply", "cmd_pick_dirs", "cmd_pick_vrn", "cmd_run_all", "cmd_extract")}}, ensure_ascii=False).replace("</", "<\\/")
    dom = _box("dd", [(r["code"], f"{r.get('name') or ''} {r.get('market') or ''}") for r in inp["domestic"]], True)
    cdm = _box("cd", [(r["code"], f"{r.get('name') or ''} {r.get('market') or ''}") for r in inp.get("cand_domestic") or []], False)
    frn = _box("df", [(c, "") for c in inp["foreign"]], True)
    cfr = _box("cf", [(c, "") for c in inp.get("cand_foreign") or []], False)
    return ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>VIA 操作台</title><style>{css(t)}.list{{max-height:150px;overflow:auto;background:#fff;border:1px solid var(--bd);padding:2px 4px}}"
            ".ck{display:block;margin:1px 0}.ck input{width:auto}.big{font-size:1.4em;font-weight:bold}</style></head><body><div class='wrap'>"
            "<aside id='side'><div class='hd'>輸入(滑鼠即可)</div>"
            "<section><h3>⓪ 兩個資料夾(Windows 選夾)</h3>"
            f"<label>系統資料夾</label><input readonly value='{_e(fo.get('system'))}'><label>資料庫資料夾</label><input readonly value='{_e(fo.get('data'))}'>"
            f"<div class='note'>{_e(fo.get('why') or '')}</div><button class='alt' id='pick_dirs' type='button'>用 Windows 視窗選兩個資料夾</button></section>"
            "<section><h3>① VDF 財報 · 國內個股</h3><div class='note'>打勾 = 在冊;取消打勾 = 移除</div>" + dom
            + "<label>加入(勾選)</label>" + cdm + "</section>"
            "<section><h3>① VDF 財報 · 國外個股(INTL_FIN)</h3>" + frn + "<label>加入(勾選)</label>" + cfr
            + f"<label>期別</label><div>{per}</div><div class='row'><div><label>起年</label><select id='fin_from'>{yopt(inp.get('fin_from'))}</select></div>"
            f"<div><label>迄年</label><select id='fin_to'>{yopt(inp.get('fin_to'))}</select></div></div>"
            f"<label>財報起始日</label><input type='date' id='fin_start' value='{_e(inp.get('fin_start'))}'></section>"
            "<section><h3>② 其他資料起始日(統一 · 可按群改)</h3>"
            f"<div class='row'><input type='date' id='start_all'><label class='ck' style='flex:0 0 22%'><input type='checkbox' id='sa_latest'> 最新</label></div>"
            f"<div class='note'>冊預設 {_e(inp.get('default_start'))};下面按群改,空 = 用統一日</div>{grp}</section>"
            "<section><h3>③ VRN 輸入文件</h3>"
            f"<div class='note'>冊上位置:{_e(inp.get('vrn_dir') or '—')}</div><button class='alt' id='pick_vrn' type='button'>Windows 選夾 / 選檔</button>"
            "<div class='drop' id='drop' style='margin-top:6px'>或把報告檔拖到這裡<br><input type='file' id='pick' multiple style='margin-top:4px'></div>"
            "<div class='chips' id='files'></div><button class='alt' id='clear_files' type='button'>清空拖曳清單</button></section>"
            "<section><button id='export' type='button'>匯出輸入包</button> <button class='alt' id='run_all' type='button'>一鍵全跑指令</button>"
            "<div class='note' id='cmd' style='margin-top:4px'></div></section></aside>"
            f"<main><div class='hd'><button class='alt' id='toggle' type='button'>☰</button>VIA 操作台 · {_lamp(worst)} · "
            f"<span class='note'>{_e(d.get('built_at', '模板(無資料)'))} · {_e(ENGINE)}</span></div>"
            "<div class='tabs'><button class='on' data-p='p_ov'>總覽</button><button data-p='p_sum'>輸入摘要(去重)</button><button data-p='p_eng'>引擎狀況</button>"
            "<button data-p='p_run'>運作摘要</button><button data-p='p_chk'>驗證</button><button data-p='p_out'>輸出 · Parquet</button>"
            "<button data-p='p_db'>資料庫管理 · 擷取</button></div>"
            f"<div class='pane on' id='p_ov'><div class='big'>{_lamp(worst)}</div><table><tr><th>燈</th><th>項(點進詳細頁)</th><th>一句話</th></tr>{ovrows}</table></div>"
            "<div class='pane' id='p_sum'><div class='note'>左面板一動就重算;同一代碼只送一次;國內國外兩邊都勾留國內;與冊上相同的起始日不送;拖曳同名同大小只算一次。"
            "入冊時引擎再照同一律做一次(伺服端去重)。</div><div id='sum'></div></div>"
            f"<div class='pane' id='p_eng'><h3>鏈</h3><table><tr><th>家</th><th>燈</th><th>報告時間</th><th>非綠</th></tr>{chains}</table>"
            f"<h3>工具(鎖冊)</h3><table><tr><th>家族</th><th>檔</th></tr>{tools}</table><div class='note'>流程閘:{_e(st.get('gate') or '—')}</div></div>"
            f"<div class='pane' id='p_run'><h3>最近一次全景實測 {_e(runs.get('ts', '—'))} · HEAD {_e(runs.get('head', '—'))}</h3>"
            f"<table><tr><th>步</th><th>結果</th><th>秒</th><th>開始(UTC)</th></tr>{steps}</table>"
            f"<h3>輸入冊最近改動</h3><table><tr><th>時間</th><th>改動</th><th>結果</th></tr>{clog}</table></div>"
            f"<div class='pane' id='p_chk'><table><tr><th>項</th><th>態</th><th>內容</th></tr>{chk_rows}</table></div>"
            f"<div class='pane' id='p_out'><div class='note'>資料庫資料夾:{_e(fo.get('data') or '—')} · parquet = 本體(zstd,最省 token)· "
            "DuckDB 管家 VIA_Parquet_Catalog.duckdb 每表一個 VIEW · 來源庫唯讀開、一個位元不動</div>"
            f"<table><tr><th>庫</th><th>表</th><th>列</th><th>狀態</th><th>parquet</th></tr>{prow}</table></div>"
            f"<div class='pane' id='p_db'><h3>管家 VIEW({len(views)})</h3><table><tr><th>燈</th><th>VIEW</th><th>列</th><th>日期範圍</th><th>欄</th>"
            f"<th>更新</th></tr>{vrow}</table><h3>擷取資料</h3><label>表</label><select id='x_view'>{vopt}</select>"
            "<label>欄(勾選)</label><div class='list' id='x_cols'></div>"
            "<div id='x_dates'><label>時間區間(日期欄 <span id='x_dcol'></span>)</label><div class='row'><input type='date' id='x_start'><input type='date' id='x_end'></div></div>"
            f"<label>格式 · 編碼</label><div>{fmts}</div><label>上限列</label><select id='x_limit'><option value=''>全部(依格式上限)</option>"
            "<option>100</option><option>1000</option><option>10000</option><option>100000</option></select>"
            "<div class='warn' style='margin-top:6px'><code id='x_cmd'></code></div><button class='alt' id='x_copy' type='button'>複製擷取指令</button>"
            f"<h3>預覽(每表前 5 列)</h3>{samples}</div></main></div>"
            f"<script id=\"ST\" type=\"application/json\">{st_json}</script><script>{_JS}</script></body></html>")


def collect(home_override: str | None = None) -> dict:
    fo = folders()
    home = Path(home_override) if home_override else (Path(fo["data"]) if fo["data_ok"] else None)
    if home_override:
        fo = {**fo, "data": str(home), "data_ok": home.exists(), "why": "--home"}
    state = inputs_state()
    me = f"python \"{Path(__file__).relative_to(VIA)}\""
    ps = ".\\Invoke-VIA-OperatorConsole-v0100.ps1"
    return {"built_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "folders": fo, "inputs": state, "status": engine_status(),
            "runs": run_summary(state), "lock": lock_regressions(), "plan": parquet_plan(home) if home else [],
            "views": catalog_views(home) if home else [],
            "cmd_apply": f"{ps} -ApplyInput via_operator_input.json", "cmd_pick_dirs": f"{ps} -Pick", "cmd_pick_vrn": "via-vrnin",
            "cmd_run_all": ps, "cmd_extract": f"{me} extract" + (f" --home \"{home}\"" if home else "")}


def write_page(home_override: str | None = None) -> dict:
    t = tokens()
    data = collect(home_override)
    data["format_lock"] = format_lock()
    OUT.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(page_html(data, t), encoding="utf-8")
    ov = overview(data)
    return {"page": str(PAGE), "format_lock": data["format_lock"]["state"], "overview": {n: k for n, k, _, _ in ov},
            "domestic": len(data["inputs"]["domestic"]), "foreign": len(data["inputs"]["foreign"]), "views": len(data["views"]),
            "parquet_tables": len(data["plan"])}


def write_template(lock: bool = False) -> dict:
    text = page_html(None, tokens())
    TEMPLATE.write_text(text, encoding="utf-8", newline="")
    fl = format_lock(write=lock, page_text=text)
    return {"template": str(TEMPLATE.relative_to(VIA)), "sha": fl["sha"], "format_lock": fl["state"]}


def save_paths(system: str, data: str) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    rec = {"system": system, "data": data, "picked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
           "rule": "本機檔(VIA_Reports 不進 git);啟動器每次把 data 設成本行程的 VIA_DATA_HOME"}
    PATHS.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return rec


# ---------------------------------------------------------------- CLI
def _arg(args, name, default=""):
    return args[args.index(name) + 1] if name in args and args.index(name) + 1 < len(args) else default


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    verb = args[0] if args else "page"
    home = _arg(args, "--home") or None
    if verb == "page":
        r = write_page(home)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if r["format_lock"] == "GREEN" else 1
    if verb == "template":
        r = write_template(lock="--lock" in args)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if r["format_lock"] == "GREEN" else 1
    if verb == "lock":
        r = format_lock()
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if r["state"] == "GREEN" else 1
    if verb == "paths":
        if "--system" in args or "--data" in args:
            print(json.dumps(save_paths(_arg(args, "--system") or str(VIA), _arg(args, "--data")), ensure_ascii=False, indent=1))
        else:
            print(json.dumps(folders(), ensure_ascii=False, indent=1))
        return 0
    if verb in ("apply", "summary"):
        f = _arg(args, "--file")
        packet = _json(Path(f)) if f else {}
        if f and packet is None:
            print(f"讀不到輸入包:{f}")
            return 2
        r = apply(packet or {}, write=(verb == "apply" and "--apply" in args))
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0
    if verb == "status":
        d = collect(home)
        d["format_lock"] = format_lock()
        print(json.dumps([{"item": n, "lamp": k, "text": x} for n, k, x, _ in overview(d)], ensure_ascii=False, indent=1))
        return 0
    if verb in ("parquet", "extract"):
        h = Path(home) if home else (Path(folders()["data"]) if folders()["data_ok"] else None)
        if h is None:
            print(json.dumps({"state": "NODATA", "why": folders()["why"] or "資料庫資料夾未選(-Pick)"}, ensure_ascii=False))
            return 2
        if verb == "parquet":
            plan = parquet_plan(h)
            r = {"home": str(h), "tables": len(plan), "rows": sum(x["rows"] for x in plan), "apply": "--apply" in args}
            if "--apply" in args:
                r.update(parquet_apply(h, plan))
            print(json.dumps(r, ensure_ascii=False, indent=1))
            return 0 if not r.get("failed") else 1
        r = extract(h, _arg(args, "--view"), [c.strip() for c in _arg(args, "--cols").split(",") if c.strip()], _arg(args, "--start"),
                    _arg(args, "--end"), _arg(args, "--format", "parquet"), int(_arg(args, "--limit", "0") or 0), "--dry" in args)
        print(json.dumps(r, ensure_ascii=False, indent=1, default=str))
        return 0 if r.get("state") in ("OK", "PLAN") else 1
    print(__doc__)
    return 0


def selftest() -> int:
    import copy as _copy
    import tempfile
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    t = tokens()
    c = css(t)
    chk("① 版面值全由 TemplateSSOT dashboard 生成(260 · 38 · 768 · 11/10px · 面板 / 框 / 輸入框色 · 四燈)",
        all(str(t[k]) in c for k in ("panel_w_px", "header_h_px", "breakpoint_px", "color_panel_bg", "input_border", "status_OK")) and
        t["panel_w_px"] == 260 and t["header_h_px"] == 38 and t["breakpoint_px"] == 768, f"{t['panel_w_px']}/{t['header_h_px']}/{t['breakpoint_px']}")
    tpl = page_html(None, t)
    chk("② 左面板只收滑鼠:勾選 · 單選 · 下拉 · 日期選 · 拖曳;打字欄只剩篩選(可不填);兩個資料夾走 Windows 視窗",
        "<textarea" not in tpl and "type='date'" in tpl and "type='checkbox'" in tpl and "type='radio'" in tpl and "<select" in tpl and
        "id='pick_dirs'" in tpl and "id='drop'" in tpl and re.findall(r"<input(?![^>]*(?:type=['\"](?:date|checkbox|radio|file)['\"]|readonly|class='flt'))", tpl) == [])
    chk("③ 右區第一頁 = 總覽(三色燈),其後 輸入摘要 · 引擎 · 運作 · 驗證 · 輸出 · 資料庫;零外連",
        tpl.index("data-p='p_ov'") < tpl.index("data-p='p_sum'") < tpl.index("data-p='p_db'") and "class='pane on' id='p_ov'" in tpl
        and not re.search(r"(src|href)=['\"]https?://", tpl))
    state = {"domestic": [{"code": "2330"}, {"code": "2454"}], "foreign": ["NVDA"],
             "groups": [{"id": g, "zh": GROUP_ZH[g], "start": "2023-07-01"} for g in OTHER_GROUPS]}
    pk = {"domestic_add": ["2317", "２３１７", "2330", "6488"], "domestic_remove": ["9999", "2454"], "foreign_add": ["AAPL", "aapl", "NVDA", "6488"],
          "foreign_remove": ["TSLA"], "start_all": "2024-01-01", "group_starts": {"macro": "latest", "etf": "2023-07-01"},
          "vrn_files": [{"name": "a.pdf", "size": 10}, {"name": "a.pdf", "size": 10}, {"name": "b.pdf", "size": 3}], "period": "單季"}
    s = dedup(pk, state)
    why = {(d["key"], d["code"]): d["why"] for d in s["dropped"]}
    chk("④ 去重:全形半形同碼 · 已在冊 · 不在冊 · 國內國外重疊 · 拖曳同名同大小 · 與冊上相同的群日",
        s["send"]["domestic_add"] == ["2317", "6488"] and why[("domestic_add", "2317")] == "同一批重複" and
        why[("domestic_add", "2330")].startswith("已在冊") and why[("domestic_remove", "9999")].startswith("不在冊") and
        s["send"]["foreign_add"] == ["AAPL"] and why[("foreign_add", "6488")].startswith("國內國外") and
        len(s["send"]["vrn_files"]) == 2 and why[("group_start", "etf")].startswith("與冊上相同") and
        s["send"]["group_starts"] == {"tw_equity": "2024-01-01", "macro": "latest", "intl": "2024-01-01"}, json.dumps(s["counts"], ensure_ascii=False))
    ops = to_ops(s["send"])
    chk("⑤ 去重後照 CGC_MDL139 apply_set 的鍵送(重複鍵 #n;國外走 INTL_FIN;期別 · 群起始)",
        ops.get("tw-add") == "2317" and ops.get("tw-add#1") == "6488" and ops.get("intl-add") == "INTL_FIN:AAPL" and
        ops.get("fin-period") == "單季" and "macro:latest" in ops.values(), ", ".join(sorted(ops)))
    m139 = mod("CGC_MDL139_InputConsole")
    if m139:
        s2 = _copy.deepcopy(m139.load_spec())
        with tempfile.TemporaryDirectory() as td:
            notes = m139.apply_set(s2, ops, matrix_path=Path(td) / "matrix.json", mirror=False)
        good = [n for n in notes if n.startswith("OK")]
        chk("⑥ 真走 MDL139 apply_set(拷貝冊,不寫):國內 / 期別 / 群起始都收", len(good) >= 5 and not any(
            n.startswith("FAIL") and ("tw-add" in n or "fin-period" in n or "group-start" in n) for n in notes), f"OK {len(good)}")
    else:
        chk("⑥ 真走 MDL139 apply_set", False, "CGC_MDL139 尾版不在")
    duck = _duckdb()
    if duck is not None:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            con = duck.connect(str(home / "vdf_tw_market.duckdb"))
            con.execute("CREATE TABLE tw_daily_prices AS SELECT CAST(DATE '2024-01-01' + CAST(i AS INTEGER) AS DATE) AS date, "
                        "CASE WHEN i % 2 = 0 THEN '2330' ELSE '2454' END AS code, '台積電' AS name, 100 + i AS close FROM range(10) t(i)")
            con.close()
            before = hashlib.sha256((home / "vdf_tw_market.duckdb").read_bytes()).hexdigest()
            r = parquet_apply(home, parquet_plan(home))
            after = hashlib.sha256((home / "vdf_tw_market.duckdb").read_bytes()).hexdigest()
            views = catalog_views(home)
            chk("⑦ 輸出統一 Parquet(zstd,讀回列數)· DuckDB 管家每表一個 VIEW · 來源庫一個位元不動",
                r["written"] == 1 and not r["failed"] and (home / "parquet" / "vdf_tw_market" / "tw_daily_prices.parquet").exists() and
                views and views[0]["view"] == "vdf_tw_market__tw_daily_prices" and views[0]["rows"] == 10 and before == after,
                f"{views[0]['date_col'] if views else ''} {' → '.join(views[0]['range']) if views else ''}")
            global OUT
            keep = OUT
            OUT = home / "out"
            try:
                got = {f: extract(home, "vdf_tw_market__tw_daily_prices", ["date", "name", "close"], "2024-01-03", "2024-01-06", f)
                       for f in ("big5", "json", "md", "parquet")}
            finally:
                OUT = keep
            chk("⑧ 擷取交給 CGC_MDL228 export:勾欄 · 時間區間 · 格式 / 編碼(Big5 · JSON · MD · Parquet 讀回列數)",
                all(g.get("state") == "OK" and g.get("rows") == 4 and g.get("readback_rows") == 4 for g in got.values()),
                " · ".join(f"{k} {v.get('state')} {v.get('encoding')}" for k, v in got.items()))
    else:
        chk("⑦ 輸出統一 Parquet · DuckDB 管家", False, "duckdb 本境不在")
        chk("⑧ 擷取", False, "duckdb 本境不在")
    fl = format_lock()
    chk("⑨ 版面鎖:模板骨架 sha 與鎖冊一致(或尚未鎖 = ABSENT,由操作員 template --lock)", fl["state"] in ("GREEN", "ABSENT"),
        f"{fl['state']} · {fl['sha']} / {fl['locked_sha']}")
    ov = overview({"status": {"gate": "[流程] 政策過", "chains": [{"family": "VDF", "lamp": "OK", "tally": {"GREEN": 3}}], "tools": []},
                   "format_lock": {"state": "GREEN"}, "folders": {"data_ok": False}, "lock": {"regress": ["x"]}, "inputs": {"ok": True}})
    chk("⑩ 總覽三色:流程閘綠 · 鏈綠 · 燈鎖回歸紅 · 資料夾未選黃 · 還沒建 = 灰", {n: k for n, k, _, _ in ov}.get("燈鎖(成功的鎖住)") == "FAIL" and
        {n: k for n, k, _, _ in ov}.get("VCGC 流程閘") == "OK" and {n: k for n, k, _, _ in ov}.get("資料庫資料夾") == "SKIP" and
        {n: k for n, k, _, _ in ov}.get("DuckDB 管家") == "UNTESTED")
    chk("⑪ 不經 VCGC 就拒跑", os.environ.get("VIA_FROM_VCGC") == "YES" or main([]) == 2)
    ok = all(results)
    print(f"  {ENGINE} selftest {sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
