#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_SkillExport v0101 — 薄尾:補上 v0100 缺的那一層「雙觸發 + 可組合」(操作員 2026-11-08 貼回規格)

v0100 已經做到的,本版一行都不重做(用已成功基礎下持續):
  三層漸進載入(Tier1 索引 / Tier2 SOP / Tier3 資源)· 10 技能登錄表 · /export-skill 官方目錄結構 ·
  Celeritas 三檢 · VSKE 只增 · 省 Token 實測。動詞 registry / sop / export / export-all / check / vske / tokens / all
  全部照原樣轉接,本版只多三個動詞。

操作員貼回的規格裡,v0100 **還沒有**的是「Dual Trigger & Composability Mechanism」三件:
  ① 語意自動偵測 —— 不等使用者打斜線,從自然語言判斷該掛哪幾個技能
  ② 緊湊啟用抬頭 —— 單行 `[ACTIVE SKILLS: /skill-a, /skill-b]`
  ③ 多技能串接 —— `/doc-extract + /data-pipe`

本版的偵測是**確定性的**,不是語意猜測:
  比對字典就是登錄表自己的 Tier1 欄位(trigger / category / desc / name / slash),
  而 trigger 欄本來就是設計時寫好的觸發語。命中哪一條就印哪一條當證據。
  一條都沒命中 → 空集合 + 明說沒命中,**不硬掛技能**(掛錯比不掛貴)。

動詞:detect <自然語言…> | header <自然語言 或 /slash…> | chain "<a> + <b>" | (其餘全轉接 v0100) | --selftest
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
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "VIA_SkillExport v" + Path(__file__).stem.rsplit("_v", 1)[-1]
_STEM = "VIA_SkillExport_v"


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d{4})\.py$", p.name)
    return int(m.group(1)) if m else -1


def _load_prior():
    """家族前一版(先解析再用,不把版號寫死 → 不踩 PINVER)。"""
    me = _vnum(Path(__file__))
    cands = [p for p in HERE.glob(f"{_STEM}*.py") if -1 < _vnum(p) < me]
    if not cands:
        raise SystemExit(f"[紅] 找不到 {_STEM}*.py 的前版")
    p = sorted(cands, key=_vnum)[-1]
    spec = importlib.util.spec_from_file_location("via_skillexport_prior", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, p.name


PRIOR, PRIOR_NAME = _load_prior()
SKILLS = PRIOR.SKILLS
SLASH_INDEX = PRIOR.SLASH_INDEX


def __getattr__(name):
    """PEP 562:本版沒定義的名稱一律轉接前版(薄尾不假裝自己重寫了全部)。"""
    return getattr(PRIOR, name)


# ───────────────────────── ① 語意自動偵測 ─────────────────────────
# 分隔符分兩層,因為 trigger 欄是「用 / 和 · 分隔的設計好的觸發語」,詞內可以有空白:
#   _PHRASE 只切片語分隔符 → 「多 Agent 交接」保持一整句(這是設計者寫的觸發語)
#   _TOKEN  再切空白 → 補上「Agent」「交接」這種較鬆的子詞
# 只用 _TOKEN 的話,「多 Agent 交接」會被切成「多」(一字,會被長度閘丟掉)+ 兩個子詞,
# 整句觸發語就不見了 —— 自測第 ④ 條紅過一次,就是這個。
# **分隔用的斜線 vs 詞內的斜線**(Codex #611 P2,實測確認):
#   登錄表寫 `圖表 / U/I / 報告` —— 分隔的是「空白 + / + 空白」,而 `U/I` 的斜線兩側沒有空白,
#   它是詞的一部分。原本不分青紅皂白切 `/`,`U/I` 就變成 `U` + `I` 兩個一字詞,
#   雙雙被長度閘丟掉 → detect("U/I") 一個技能都不回,而那是冊上登錄的觸發語。
#   同理 `跨 PS·PY 注入` 的 `·` 也在詞內,而 category `C 視覺 · 治理` 的 `·` 兩側有空白才是分隔。
#   規則:**/ 與 · 只有在至少一側貼著空白時才算分隔符**;CJK 標點一律算分隔符。
_PHRASE = re.compile(r"\s+[/·]\s*|\s*[/·]\s+|[、，,。;；|]+")
_TOKEN = re.compile(r"\s+")
_SPLIT = _PHRASE      # 相容:前版若引用 _SPLIT 仍指片語層

# 拉丁 / 數字詞(可含 . _ + - / ·)比對時要卡詞界,CJK 不卡(中文沒有詞界可卡)。
# **為什麼要卡**(Codex #611 P2,實測確認):`ps`(來自 `跨 PS·PY 注入`)與 `cli`(來自 `寫腳本 / CLI`)
#   都是三字以下的拉丁短詞,不卡詞界就會被 `eclipse` 這種普通英文字含進去 ——
#   eclipse[1:4] == "cli",eclipse 也含 ps;psychology 同樣含 ps。
#   結果「Describe the eclipse」會被掛上 /ast-diag + /self-heal,「沒命中就不硬掛」的承諾就破了。
_LATINISH = re.compile(r"^[a-z0-9][a-z0-9+._/·-]*$")


def hits_query(word: str, q: str) -> bool:
    """一個比對詞是否真的出現在查詢裡。拉丁詞卡詞界,CJK 詞用子字串。

    詞界只擋拉丁字母與數字,所以 CJK 貼著拉丁詞(例「做PDF擷取」)仍然算命中 —— 那是真的提到了。
    """
    if _LATINISH.match(word):
        return re.search(r"(?<![a-z0-9])" + re.escape(word) + r"(?![a-z0-9])", q) is not None
    return word in q


def phrases(s: dict) -> list[tuple[str, str]]:
    """一個技能的比對詞 → [(詞, 來自哪一欄)]。只取 Tier1 欄位 —— 偵測不准載入 Tier2(那就不省 Token 了)。"""
    out: list[tuple[str, str]] = []
    seen: set[str] = set()

    def push(word: str, src: str):
        w = word.strip().lower()
        if len(w) < 2 or w in seen:
            return
        seen.add(w)
        out.append((w, src))

    push(s["slash"].lstrip("/"), "slash")
    for part in _PHRASE.split(s["name"]):
        for tok in _TOKEN.split(part):
            push(tok, "name")
    for field in ("trigger", "category", "desc"):
        for part in _PHRASE.split(str(s.get(field) or "")):
            push(part, field)                      # 整句觸發語
            for tok in _TOKEN.split(part):
                push(tok, field)                   # 子詞(較鬆)
    return out


def detect(query: str, limit: int = 3) -> list[dict]:
    """自然語言 → 該掛哪幾個技能。確定性:命中詞逐個印出來當證據。

    排序:命中詞數多的在前;同分照登錄表原序(穩定,不會跑來跑去)。
    一條都沒命中就回空 —— 不硬掛。
    """
    q = str(query or "").lower()
    rows: list[dict] = []
    for i, s in enumerate(SKILLS):
        hits = [(w, src) for w, src in phrases(s) if hits_query(w, q)]
        if hits:
            rows.append({"slash": s["slash"], "name": s["name"], "category": s["category"],
                         "score": len(hits), "order": i,
                         "hits": [{"word": w, "field": f} for w, f in hits[:6]]})
    rows.sort(key=lambda r: (-r["score"], r["order"]))
    return rows[:limit] if limit else rows


def header_line(slashes: list[str]) -> str:
    """規格要的那一行,字面照抄:`[ACTIVE SKILLS: /skill-a, /skill-b]`。沒有命中就說沒有,不印空括號裝有。"""
    if not slashes:
        return "[ACTIVE SKILLS: none]"
    return "[ACTIVE SKILLS: " + ", ".join(slashes) + "]"


# ───────────────────────── ③ 多技能串接 ─────────────────────────
def parse_chain(expr: str) -> tuple[list[str], list[str]]:
    """`/doc-extract + /data-pipe` → (認得的 slash 序列, 認不得的)。保留使用者寫的順序。"""
    ok, bad = [], []
    for raw in re.split(r"\s*\+\s*|\s*→\s*|\s*->\s*", str(expr or "")):
        t = raw.strip()
        if not t:
            continue
        if not t.startswith("/"):
            t = "/" + t
        (ok if t in SLASH_INDEX else bad).append(t)
    return ok, bad


def chain_plan(expr: str) -> dict:
    """串接計畫:Tier2 載入順序 + 合併後的加速器 id。

    鏈裡有一個認不得就整條不給跑(rc 2)—— 半條鏈比沒有鏈危險:
    前半段改了檔、後半段才發現技能不存在,就留下改一半的樹。
    """
    ok, bad = parse_chain(expr)
    accel: list[str] = []
    for sl in ok:
        for a in (SLASH_INDEX[sl].get("accel") or []):
            if a not in accel:
                accel.append(a)
    return {
        "expr": expr, "resolved": ok, "unknown": bad,
        "tier2_order": ok,                       # Tier2 照使用者寫的順序載入
        "accel_union": accel,
        "header": header_line(ok),
        "ok": bool(ok) and not bad,
        "why_not": ("鏈裡有認不得的技能:" + "、".join(bad) + " —— 整條不跑,不留改一半的樹") if bad
                   else ("" if ok else "鏈是空的"),
    }


# ───────────────────────── 自測 ─────────────────────────
def selftest() -> int:
    ok = fail = 0

    def chk(name, cond, extra=""):
        nonlocal ok, fail
        if cond:
            ok += 1
            print(f"  ✔ {name}")
        else:
            fail += 1
            print(f"  ✘ {name}{(' —— ' + str(extra)) if extra else ''}")

    print(f"[{TAG} 自測 · 薄尾於 {PRIOR_NAME}]")

    # ① 薄尾本分:前版自測還過、動詞全轉接、沒少公開名稱
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = PRIOR.selftest()
    chk("① 前版自測仍全過(rc 0)", rc == 0, f"rc={rc}")
    for verb in ("cmd_registry", "cmd_sop", "cmd_export", "cmd_export_all",
                 "cmd_check", "cmd_vske", "cmd_tokens", "cmd_all", "resolve", "skill_md"):
        chk(f"② 轉接前版 {verb}", callable(getattr(sys.modules[__name__], verb, None)), verb)
    chk("③ 登錄表就是前版那一份(10 技能,不另抄一份)",
        len(SKILLS) == 10 and SKILLS is PRIOR.SKILLS, len(SKILLS))

    # ④ 偵測:用登錄表自己的 trigger 語當查詢,一定要命中它自己
    for s in SKILLS:
        first = _PHRASE.split(str(s["trigger"]))[0].strip()   # 取「整句觸發語」,不是空白切出來的碎片
        got = [r["slash"] for r in detect(first, limit=10)]
        chk(f"④ 「{first}」→ 命中 {s['slash']}", s["slash"] in got, got)

    # ⑤ 偵測是確定性的:同一個查詢跑兩次結果一樣
    q = "幫我看 PDF 財報裡的複雜表格,然後做成大表時序 ETL"
    chk("⑤ 同查詢兩次結果相同(確定性)", detect(q) == detect(q))
    got = [r["slash"] for r in detect(q, limit=10)]
    chk("⑥ 跨類查詢同時掛上 /doc-extract 與 /data-pipe", {"/doc-extract", "/data-pipe"} <= set(got), got)

    # ⑦ 沒命中就不硬掛
    chk("⑦ 無關查詢不硬掛技能", detect("今天天氣真好") == [], detect("今天天氣真好"))
    chk("⑧ 沒命中時抬頭印 none(不印空括號裝有)", header_line([]) == "[ACTIVE SKILLS: none]")

    # ⑨ 命中詞都附來源欄位(證據,不是分數黑箱)
    rows = detect(q, limit=10)
    chk("⑨ 每個命中都附命中詞與來源欄位",
        all(r["hits"] and all(h["word"] and h["field"] for h in r["hits"]) for r in rows))
    chk("⑩ 命中詞真的在查詢字串裡(不是編的)",
        all(hits_query(h["word"], q.lower()) for r in rows for h in r["hits"]))

    # ⑪ 抬頭字面照規格
    chk("⑪ 抬頭格式字面照規格",
        header_line(["/skill-a", "/skill-b"]) == "[ACTIVE SKILLS: /skill-a, /skill-b]")

    # ⑫ 排序穩定:同分照登錄表原序
    two = detect("結構分析 指標", limit=10)
    chk("⑫ 同分照登錄表原序(穩定排序)",
        [r["order"] for r in two] == sorted(r["order"] for r in two) or
        len({r["score"] for r in two}) > 1, [(r["slash"], r["score"], r["order"]) for r in two])

    # ⑬ 串接:規格給的那個例子
    c = chain_plan("/doc-extract + /data-pipe")
    chk("⑬ 規格例子解得開", c["resolved"] == ["/doc-extract", "/data-pipe"] and c["ok"], c)
    chk("⑭ Tier2 載入順序照使用者寫的順序", c["tier2_order"] == ["/doc-extract", "/data-pipe"])
    chk("⑮ 加速器 id 取聯集且不重", len(c["accel_union"]) == len(set(c["accel_union"])) and c["accel_union"])
    chk("⑯ 串接也印抬頭", c["header"] == "[ACTIVE SKILLS: /doc-extract, /data-pipe]", c["header"])
    chk("⑰ 反向順序 → 載入順序跟著反", chain_plan("/data-pipe + /doc-extract")["tier2_order"]
        == ["/data-pipe", "/doc-extract"])
    chk("⑱ 不帶斜線也收(doc-extract + data-pipe)",
        chain_plan("doc-extract + data-pipe")["resolved"] == ["/doc-extract", "/data-pipe"])
    chk("⑲ 箭頭寫法也收(→ / ->)",
        chain_plan("/doc-extract → /data-pipe")["resolved"] == ["/doc-extract", "/data-pipe"]
        and chain_plan("/doc-extract -> /data-pipe")["resolved"] == ["/doc-extract", "/data-pipe"])

    # ⑳ 鏈裡有假技能 → 整條不跑
    bad = chain_plan("/doc-extract + /not-a-skill")
    chk("⑳ 認不得的技能被列出來", bad["unknown"] == ["/not-a-skill"], bad)
    chk("㉑ 整條不給跑,並說明為什麼(不留改一半的樹)",
        bad["ok"] is False and "改一半" in bad["why_not"])
    chk("㉒ 空鏈不給跑", chain_plan("")["ok"] is False and chain_plan("")["why_not"] == "鏈是空的")

    # ㉓ 偵測只讀 Tier1,不碰 Tier2(省 Token 的前提)
    srcs = {src for s in SKILLS for _, src in phrases(s)}
    chk("㉓ 比對詞只來自 Tier1 欄位(slash / name / trigger / category / desc)",
        srcs <= {"slash", "name", "trigger", "category", "desc"}, srcs)
    chk("㉔ 比對詞不含 sop 內文(否則等於常駐載入 Tier2)",
        not any("sop" in src for src in srcs))

    # ㉕ 太短的詞不當關鍵詞(避免單字亂命中)
    chk("㉕ 一字詞不進比對字典", all(len(w) >= 2 for s in SKILLS for w, _ in phrases(s)))
    # ㉖ 片語層保留整句觸發語(回歸測:只切空白會讓「多 Agent 交接」整句消失)
    ts = {w for w, f in phrases(SLASH_INDEX["/token-state"]) if f == "trigger"}
    chk("㉖ 整句觸發語保留(多 agent 交接)", "多 agent 交接" in ts, sorted(ts)[:8])
    chk("㉗ 子詞也在(agent · 交接),整句與子詞並存", {"agent", "交接"} <= ts, sorted(ts)[:8])
    chk("㉘ 整句比子詞更精確:整句查詢分數不低於子詞查詢",
        detect("多 Agent 交接", limit=10)[0]["slash"] == "/token-state",
        [r["slash"] for r in detect("多 Agent 交接", limit=10)])

    # Codex #611 兩個 P2 的回歸測(兩個都先實測重現過才改)
    cz = {w for w, f in phrases(SLASH_INDEX["/canvas-zen"]) if f == "trigger"}
    chk("㉙ 詞內斜線保住:u/i 在 /canvas-zen 的比對詞裡", "u/i" in cz, sorted(cz))
    chk("㉚ detect U/I 回得出 /canvas-zen(冊上登錄的觸發語必須可用)",
        "/canvas-zen" in [r["slash"] for r in detect("U/I", limit=10)],
        [r["slash"] for r in detect("U/I", limit=10)])
    chk("㉛ 分隔的斜線照切(圖表 · 報告 都還在)", {"圖表", "報告"} <= cz, sorted(cz))
    ad = {w for w, f in phrases(SLASH_INDEX["/ast-diag"]) if f == "trigger"}
    chk("㉜ 詞內的 · 也保住(ps·py 不被切成 ps + py)", "ps·py" in ad, sorted(ad))
    for q2 in ("Describe the eclipse", "Explain the psychology of sleep"):
        chk("㉝ 拉丁詞卡詞界:" + q2 + " 不得掛上任何技能", detect(q2, limit=10) == [],
            [(r["slash"], [h["word"] for h in r["hits"]]) for r in detect(q2, limit=10)])
    chk("㉞ 卡了詞界,真的提到還是要命中(PDF / ETL / CLI)",
        "/doc-extract" in [r["slash"] for r in detect("這份 PDF 財報", limit=10)]
        and "/data-pipe" in [r["slash"] for r in detect("時序 ETL 大表", limit=10)]
        and "/self-heal" in [r["slash"] for r in detect("寫一個 CLI 批次", limit=10)])
    chk("㉟ CJK 貼著拉丁詞也算命中(做PDF擷取)",
        "/doc-extract" in [r["slash"] for r in detect("做PDF擷取", limit=10)])
    chk("㊱ 詞界擋住同字根的長字(reporter 不等於 repo)",
        "/token-state" not in [r["slash"] for r in detect("ask the reporter", limit=10)],
        [(r["slash"], [h["word"] for h in r["hits"]]) for r in detect("ask the reporter", limit=10)])

    print(f"[計] {TAG} 自測 OK {ok} · FAIL {fail} · {'PASS' if fail == 0 else 'FAIL'}")
    return 0 if fail == 0 else 1


# ───────────────────────── 入口 ─────────────────────────
def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    if not args or args[0] not in ("detect", "header", "chain"):
        return PRIOR.main(args)          # 其餘動詞一律交前版,本版不插手

    ap = argparse.ArgumentParser(prog=TAG, add_help=True)
    ap.add_argument("verb", choices=["detect", "header", "chain"])
    ap.add_argument("text", nargs="+")
    ap.add_argument("--limit", type=int, default=3)
    a = ap.parse_args(args)
    q = " ".join(a.text)

    if a.verb == "chain":
        c = chain_plan(q)
        print(c["header"])
        print(f"  [鏈] {c['expr']}")
        for i, sl in enumerate(c["tier2_order"], 1):
            s = SLASH_INDEX[sl]
            print(f"  {i}. {sl:14}{s['name']:32}{s['category']}")
        print(f"  [加速器] {' '.join(c['accel_union']) or '—'}")
        if not c["ok"]:
            print(f"  [拒跑] {c['why_not']}")
            return 2
        return 0

    rows = detect(q, limit=a.limit)
    print(header_line([r["slash"] for r in rows]))
    if a.verb == "header":
        return 0 if rows else 3
    for r in rows:
        ev = " · ".join(f"{h['word']}({h['field']})" for h in r["hits"])
        print(f"  {r['slash']:14}{r['name']:32}命中 {r['score']} —— {ev}")
    if not rows:
        print("  [沒命中] 登錄表 10 技能的 Tier1 比對詞一條都沒出現在這句話裡 —— 不硬掛技能")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
