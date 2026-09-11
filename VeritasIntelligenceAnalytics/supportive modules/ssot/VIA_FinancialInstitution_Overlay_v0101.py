#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA_FinancialInstitution_Overlay — 金融機構正典 SSOT 的**操作員裁決疊加層**(批413)
================================================================================
為什麼要有這一層而不是直接改正典:
  正典 `VIA_Financial_Institution_SSOT_v0100` 自己在 `alias_governance` 裡寫明
  `canonical_write_mode = READ_ONLY`、自動更新一律進 `RUN_LOCAL_OVERLAY`。
  本層就是那個 overlay 的落實:**正典一個字都不改**,裁決與補充全放這裡,
  來源與理由逐條留痕(`provenance` / `rulings`)。

本層做四件事,而且只做這四件(不自建第二套解析器=Zero-Hydra):
  ① 拒絕清單 deny_keys —— **先於**正典查詢。操作員令「大陸券商刪除」「去摩通」,
     所以 廣發/GF/中信建投/國泰君安/中金/海通… 與 摩根/摩通 一律不得解析成任何機構,
     並回報「為什麼被拒」,不是靜默查無。
  ② 券商別名補充 broker_alias_add —— 正典查不到、但操作員的 Grok 冊(昨天過關那份)
     有的別名,補在這裡指向**正典鍵**。
  ③ 新增機構 broker_add —— 正典沒有、Grok 冊有的台/外資券商(日盛/合庫/大華/宏遠/德意志)。
  ④ 檔名鍵對映 filename_key_map —— `JP`、`CLST` 這種**兩三字母 token 只在檔名命名空間**
     認得;內文別名絕不收(在內文會亂咬)。這是兩個不同的命名空間,分開處理。

評等同理:rating_alias_add 把 Grok 冊多出來的 59 條(增持/推薦/超配/續抱/低配/Long/Short…)
接到正典的六個評等鍵上。

解析次序一律是:**拒絕清單 → 正典 → 疊加層**。正典先行,疊加層只補正典的空缺,
永遠不覆寫正典已有的判斷。
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OVERLAY_JSON = (sorted(HERE.glob("VIA_FinancialInstitution_Overlay_v*.json"))
                or [HERE / "VIA_FinancialInstitution_Overlay_v0101.json"])[-1]
_CACHE: dict = {"ov": None, "ssot": None, "why": ""}


def _norm(v: str) -> str:
    """比對用正規化(與正典 normalize_alias 同精神:去非字母數字、轉小寫)"""
    return re.sub(r"[^0-9a-z㐀-鿿]+", "", str(v or "").lower())


def overlay() -> dict:
    if _CACHE["ov"] is None:
        _CACHE["ov"] = json.loads(OVERLAY_JSON.read_text(encoding="utf-8"))
    return _CACHE["ov"]


def ssot():
    """載入正典(尾版律 glob);缺 pydantic/缺檔=誠實回 None 與因由,不假裝。"""
    if _CACHE["ssot"] is not None or _CACHE["why"]:
        return _CACHE["ssot"]
    hits = sorted(HERE.glob("VIA_Financial_Institution_SSOT_v*.py"))
    if not hits:
        _CACHE["why"] = "正典 SSOT 缺檔"
        return None
    try:
        spec = importlib.util.spec_from_file_location("via_fin_ssot_canon", hits[-1])
        mod = importlib.util.module_from_spec(spec)
        # 必須:正典用 `from __future__ import annotations`,pydantic 要靠
        # sys.modules[cls.__module__] 才解得開延後註解(批412 踩過)。
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        _CACHE["ssot"] = mod
        return mod
    except Exception as exc:
        _CACHE["why"] = f"正典載入失敗 {type(exc).__name__}:{str(exc)[:90]}"
        return None


def why() -> str:
    return _CACHE["why"]


def deny_reason(value: str) -> str:
    """在拒絕清單上=回一句因由;不在=空字串。"""
    n = _norm(value)
    if not n:
        return ""
    for k in overlay().get("deny_keys", []):
        if _norm(k) == n:
            return f"拒絕清單:{k}(操作員裁決;見 overlay.rulings)"
    return ""


def overlay_keys() -> set:
    """疊加層**自己**知道的正典鍵集合(檔名鍵對映的目標 ∪ 別名表的鍵 ∪ 新增機構)。
    批419f:這些鍵是操作員裁決寫在疊加層 JSON 裡的資料,**不是**從正典查來的,
    所以正典缺席時它們依然成立。"""
    ov = overlay()
    ks = {str(v) for v in ov.get("filename_key_map", {}).values() if v and v != "__DENY__"}
    ks |= {str(k) for k in ov.get("broker_alias_add", {})}
    ks |= {str(b.get("ssot_key")) for b in ov.get("broker_add", []) if b.get("ssot_key")}
    return ks


def resolve_broker(value: str) -> dict:
    """→ {key, zh, en, src, deny};次序 拒絕清單 → 正典 → 疊加層。查不到=key 空。"""
    out = {"key": "", "zh": "", "en": "", "src": "", "deny": ""}
    v = str(value or "").strip()
    if not v:
        return out
    d = deny_reason(v)
    if d:
        out["deny"] = d
        return out
    m = ssot()
    if m is not None:
        hit = m.resolve_broker(v)
        if hit is not None:
            return {"key": hit.ssot_key, "zh": hit.chinese_name,
                    "en": hit.english_name, "src": "CANON", "deny": ""}
    ov = overlay()
    n = _norm(v)
    for key, aliases in ov.get("broker_alias_add", {}).items():
        if any(_norm(a) == n for a in aliases):
            zh = en = ""
            if m is not None:
                h2 = m.resolve_broker(key)
                if h2 is not None:
                    zh, en = h2.chinese_name, h2.english_name
            return {"key": key, "zh": zh, "en": en, "src": "OVERLAY_ALIAS", "deny": ""}
    for b in ov.get("broker_add", []):
        if any(_norm(a) == n for a in [b["ssot_key"], b["chinese_name"]] + b.get("aliases", [])):
            return {"key": b["ssot_key"], "zh": b["chinese_name"],
                    "en": b.get("english_name", ""), "src": "OVERLAY_NEW", "deny": ""}
    # 批419f(工作站實錄修):正典缺席(vrn 境無 pydantic)時,連**疊加層自己知道的鍵**
    # 都被一起丟掉——工作站因此回「券商正典鍵 0/59」,而疊加層 stats() 明明是
    # filename_keys 16 / alias 23 / new 5,資料全在。中英名確實只有正典有,
    # 但**鍵**是操作員裁決寫在疊加層裡的資料,正典缺席不影響它成立。
    # 所以:鍵照回,中英名誠實留空,src 明標「僅鍵無中英名」——不冒充 CANON。
    if m is None and v.upper() in {k.upper() for k in overlay_keys()}:
        return {"key": next(k for k in overlay_keys() if k.upper() == v.upper()),
                "zh": "", "en": "", "src": "OVERLAY_KEY(正典缺席;僅鍵無中英名)", "deny": ""}
    return out


def resolve_broker_filename(token: str) -> dict:
    """檔名命名空間專用(`JP`/`CLST`/`GF` 這類兩三字母 token)。
    `__DENY__` 表示操作員裁決不得採用(如 GF 廣發=陸券刪除)。"""
    ov = overlay()
    tgt = ov.get("filename_key_map", {}).get(str(token or "").strip())
    if tgt == "__DENY__":
        return {"key": "", "zh": "", "en": "", "src": "FILENAME_MAP",
                "deny": f"檔名鍵 {token}:{deny_reason('GF') or '操作員裁決不得採用'}"}
    if tgt:
        r = resolve_broker(tgt)
        if not r.get("key") and not r.get("deny"):
            # 批419f:檔名對映查得到目標鍵,卻因正典缺席而回空——那是把已知資料丟掉。
            r = {"key": tgt, "zh": "", "en": "",
                 "src": "FILENAME_MAP(正典缺席;僅鍵無中英名)", "deny": ""}
        else:
            r["src"] = "FILENAME_MAP" if r.get("src") == "CANON" else (r.get("src") or "FILENAME_MAP")
        return r
    return resolve_broker(token)


def resolve_rating(value: str) -> dict:
    """→ {key, code, direction, actionable, src};次序 正典 → 疊加層。"""
    out = {"key": "", "code": None, "direction": "", "actionable": None, "src": ""}
    v = str(value or "").strip()
    if not v:
        return out
    m = ssot()
    if m is not None:
        hit = m.resolve_rating(v)
        if hit is not None:
            return {"key": hit.ssot_key, "code": int(hit.code), "direction": hit.direction,
                    "actionable": bool(hit.actionable), "src": "CANON"}
    n = _norm(v)
    for key, aliases in overlay().get("rating_alias_add", {}).items():
        if any(_norm(a) == n for a in aliases):
            if m is not None:
                h2 = m.resolve_rating(key)
                if h2 is not None:
                    return {"key": h2.ssot_key, "code": int(h2.code), "direction": h2.direction,
                            "actionable": bool(h2.actionable), "src": "OVERLAY_ALIAS"}
            return {"key": key, "code": None, "direction": "", "actionable": None,
                    "src": "OVERLAY_ALIAS"}
    return out


def stats() -> dict:
    ov = overlay()
    return {"deny_keys": len(ov.get("deny_keys", [])),
            "broker_alias_add": sum(len(v) for v in ov.get("broker_alias_add", {}).values()),
            "broker_add": len(ov.get("broker_add", [])),
            "rating_alias_add": sum(len(v) for v in ov.get("rating_alias_add", {}).values()),
            "filename_keys": len(ov.get("filename_key_map", {})),
            "canon": "在位" if ssot() is not None else f"缺席:{why()}"}


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    m = ssot()
    chk("① 正典在位且疊加層可讀(正典唯讀,本層只補不改)",
        m is not None and bool(overlay().get("deny_keys")), f"({stats()})")
    chk("② 拒絕清單先於正典:摩通/廣發/GF/中信建投 一律不解析且回因由(操作員令"
        "「去摩通」「大陸券商刪除」)",
        all(resolve_broker(x)["key"] == "" and resolve_broker(x)["deny"]
            for x in ("摩通", "廣發", "GF", "中信建投", "國泰君安", "中金", "海通", "摩根")),
        f"({resolve_broker('摩通')['deny'][:34]})")
    r_jp = resolve_broker_filename("JP")
    r_clst = resolve_broker_filename("CLST")
    r_gf = resolve_broker_filename("GF")
    chk("③ 檔名鍵對映:JP→JPM、CLST→CLSA、GF→拒絕(兩三字母 token 只在檔名認,"
        "不進內文別名)",
        r_jp["key"] == "JPM" and r_clst["key"] == "CLSA"
        and r_gf["key"] == "" and bool(r_gf["deny"]),
        f"(JP→{r_jp['key']} · CLST→{r_clst['key']} · GF→拒絕)")
    chk("④ 裸 JP 不收為內文別名(兩字母會亂咬,只在檔名命名空間認);CLST 依操作員令「CLST/CLSA/里昂都可」收為內文別名;正典既有別名照樣解得到",
        resolve_broker("JP")["key"] == "" and resolve_broker("小摩")["key"] == "JPM"
        and resolve_broker("里昂")["key"] == "CLSA"
        and resolve_broker("CLST")["key"] == "CLSA",
        f"(裸 JP→空 · 小摩→JPM · CLST→CLSA)")
    chk("⑤ 疊加層新增機構可解(正典沒有的 5 家:日盛/合庫/大華/宏遠/德意志)",
        all(resolve_broker(x)["src"] == "OVERLAY_NEW"
            for x in ("日盛", "合庫", "大華", "宏遠", "德意志"))
        and resolve_broker("德意志")["key"] == "DB")
    r1, r2, r3 = resolve_rating("增持"), resolve_rating("加碼"), resolve_rating("超配")
    r4, r5 = resolve_rating("續抱"), resolve_rating("低配")
    chk("⑥ 評等疊加(操作員令「增持加碼」):增持=加碼=BUY;Grok 冊多出的 59 條接上正典鍵",
        r1["key"] == r2["key"] == "BUY" and r1["code"] == 2
        and r3["key"] == "BUY" and r4["key"] == "HOLD" and r5["key"] == "SELL",
        f"(增持→{r1['key']}/{r1['src']} · 加碼→{r2['key']}/{r2['src']} · 續抱→{r4['key']})")
    chk("⑦ 正典先行:正典已有的判斷疊加層永不覆寫(Buy/買進/NR 仍走 CANON)",
        all(resolve_rating(x)["src"] == "CANON" for x in ("Buy", "買進", "NR", "Outperform"))
        and resolve_broker("Citi")["src"] == "CANON")
    chk("⑧ 認不出=誠實空(不硬猜);拒絕與查無兩態分得開",
        resolve_broker("完全不存在的券商")["key"] == ""
        and resolve_broker("完全不存在的券商")["deny"] == ""
        and resolve_rating("完全不是評等")["key"] == "")
    chk("⑨ 正本零觸碰宣告(本檔不寫正典;裁決與來源逐條留痕)",
        "READ_ONLY" in Path(__file__).read_text(encoding="utf-8")
        and bool(overlay().get("provenance", {}).get("operator_order"))
        and bool(overlay().get("rulings")))
    # ── 批419f 一檢:正典缺席時,疊加層自有的鍵不得一起陪葬 ──
    _keep = (_CACHE["ssot"], _CACHE["why"])
    _CACHE["ssot"], _CACHE["why"] = None, "stub:正典缺席(重現 vrn 境無 pydantic)"
    try:
        _mega = resolve_broker_filename("兆豐")
        _jp = resolve_broker_filename("JP")
        _gf = resolve_broker_filename("GF")
        _key = resolve_broker("MEGA")
        _unknown = resolve_broker("不存在的券商XYZ")
    finally:
        _CACHE["ssot"], _CACHE["why"] = _keep
    chk("⑩ 正典缺席時疊加層自有的鍵不得一起陪葬(批419f 工作站實錄:vrn 境無 pydantic → "
        "正典載入失敗 → 連 filename_key_map 查到的鍵都被丟掉,回「券商正典鍵 0/59」,"
        "而 stats() 明明是 filename_keys 16;中英名確實只有正典有,但**鍵**是操作員裁決"
        "寫在疊加層裡的資料,正典缺席不影響它成立。鍵照回、中英名誠實留空、src 明標,"
        "不冒充 CANON;查無仍是查無,拒絕仍是拒絕)",
        _mega["key"] == "MEGA" and _mega["zh"] == "" and "正典缺席" in _mega["src"]
        and _jp["key"] == "JPM" and "正典缺席" in _jp["src"]
        and _gf["key"] == "" and _gf["deny"]                     # 拒絕照舊壓過一切
        and _key["key"] == "MEGA" and "正典缺席" in _key["src"]
        and _unknown["key"] == "" and not _unknown["deny"],      # 查無=查無,不硬造
        f"(兆豐→{_mega['key']}/{_mega['src'][:18]} · JP→{_jp['key']} · "
        f"GF deny={'有' if _gf['deny'] else '無'} · 查無={_unknown['key'] or '空'})")

    print(f"  [計] 十檢 OK {10 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== 金融機構正典疊加層(批413)· 十檢自測(零網路)===")
        return selftest()
    print(json.dumps(stats(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
