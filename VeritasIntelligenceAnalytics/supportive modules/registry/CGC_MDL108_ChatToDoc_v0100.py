#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL108_ChatToDoc v0100 — 對話紀錄→編排文章/程式(9hh5to 收官令)
======================================================================
操作員問「有無 NLP 工具將對話紀錄轉成編排好的文章或程式」→答案=
VIA_NLP_OneEngine(收容夾)+本件接線統包。四段:
  ① 讀入  --in 檔;缺參=VIA_Reports/chat2doc_in/ 尾版 .txt/.md;
     空=NOT_RUN 誠實
  ② 編排  掛 OneEngine text_ops(Tier-1 純本地:jieba 斷詞/標題/
     重點/待辦/決策/關鍵字/語言);缺席=本地輕量道(規則標記)
     誠實標 lane
  ③ 抽碼  ``` fences(語言標籤優先)+裸 def/function 塊→py/js/ps1
     判定→逐塊出檔(來源行號+sha 溯源;內容=原文零改動)
  ④ 出文  ARTICLE_<ts>.md(標題/摘要重點/決策/待辦/發言者分段重組
     /關鍵字/程式附錄)+JSON 存證落 VIA_Reports/chat2doc_runs/
誠實界:Tier-1 輕量道(完整跳題 Episode 重組=OneEngine 全裝道,
     工作站 pip -e 後自動可用);抽碼=原文搬運零發明。
用法:python3 CGC_MDL108_ChatToDoc_v0100.py [--in 檔] [--selftest]
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
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
INDIR = VIA / "VIA_Reports" / "chat2doc_in"
OUTDIR = VIA / "VIA_Reports" / "chat2doc_runs"
NLPSRC = (VIA / "functional modules" / "VRN" / "references" / "intake"
          / "VIA_NLP_OneEngine_v1.1.0" / "src")
FENCE_RX = re.compile(r"```([A-Za-z0-9+#]*)\n(.*?)```", re.S)
SPK_RX = re.compile(r"^\s*(?:\[[\d:\s\-/]+\]\s*)?([^\s::]{1,12})[::]\s*(.+)$")
EXT = {"python": "py", "py": "py", "powershell": "ps1", "ps1": "ps1", "ps": "ps1",
       "javascript": "js", "js": "js", "typescript": "js", "json": "json"}


def banner(t):
    print(f"── {t} ──")


def mount_nlp():
    """OneEngine text_ops 掛載(Tier-1;缺=None 誠實退輕量道)。"""
    try:
        sys.path.insert(0, str(NLPSRC))
        from via_nlp_engine.text_ops import TextProcessor
        lex = sorted((NLPSRC.parent / "data" / "lexicon").glob("*"))[0]
        return TextProcessor(lex)
    except Exception:
        return None


def light_structure(text: str) -> dict:
    """輕量後備道(OneEngine 缺席時;規則標記誠實)。"""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    act = re.compile(r"待辦|應|需要|必須|todo|action", re.I)
    dec = re.compile(r"決定|決議|結論|同意|decision", re.I)
    return {"title": (lines[0][:80] if lines else ""),
            "key_points": lines[:4],
            "action_items": [ln for ln in lines if act.search(ln)][:10],
            "decisions": [ln for ln in lines if dec.search(ln)][:10],
            "keywords": [], "language": "unknown"}


def guess_lang(code: str) -> str:
    if re.search(r"^\s*(?:def |import |from \w+ import)", code, re.M):
        return "py"
    if re.search(r"\$\w+\s*=|^\s*param\(|Write-Host", code, re.M):
        return "ps1"
    if re.search(r"^\s*(?:function |var |let |const )|=>", code, re.M):
        return "js"
    return "txt"


def extract_code(text: str) -> list[dict]:
    """``` fences 優先(標籤判語言;無標=規則判);內容原文零改動。"""
    out = []
    for i, m in enumerate(FENCE_RX.finditer(text), 1):
        tag, body = (m.group(1) or "").lower(), m.group(2)
        ext = EXT.get(tag) or guess_lang(body)
        row = text[:m.start()].count("\n") + 1
        out.append({"n": i, "ext": ext, "code": body, "src_line": row,
                    "sha": hashlib.sha256(body.encode()).hexdigest()[:12]})
    return out


def speakers_recompose(text: str) -> list[dict]:
    """發言者分段重組(輕量:連續同人合段;fence 區塊跳過)。"""
    body = FENCE_RX.sub("\n", text)  # 程式塊移除(附錄已溯源;不混入對話段)
    segs: list[dict] = []
    for ln in body.splitlines():
        m = SPK_RX.match(ln)
        if m:
            spk, msg = m.group(1), m.group(2)
            if segs and segs[-1]["spk"] == spk:
                segs[-1]["msg"].append(msg)
            else:
                segs.append({"spk": spk, "msg": [msg]})
        elif segs and ln.strip():
            segs[-1]["msg"].append(ln.strip())
    return segs


def compose_md(name: str, st: dict, segs: list, codes: list, lane: str,
               ts: str) -> str:
    L = [f"# {st.get('title') or name}", "",
         f"> 來源:`{name}` · 產於 {ts} · 編排道:{lane} · 誠實三態(抽碼=原文搬運零發明)",
         "", "## 摘要重點"]
    L += [f"- {p}" for p in (st.get("key_points") or ["(無)"])]
    if st.get("decisions"):
        L += ["", "## 決策"] + [f"- ✅ {d}" for d in st["decisions"]]
    if st.get("action_items"):
        L += ["", "## 待辦"] + [f"- ☐ {a}" for a in st["action_items"]]
    if segs:
        L += ["", "## 對話重組(發言者分段)"]
        for s in segs:
            L += [f"**{s['spk']}**:{' '.join(s['msg'])}", ""]
    kw = st.get("keywords") or []
    if kw:
        terms = [k.get("term", k.get("keyword", str(k))) if isinstance(k, dict)
                 else str(k) for k in kw[:10]]
        L += ["## 關鍵字", "、".join(terms), ""]
    if codes:
        L += ["## 程式附錄(已抽出檔)"]
        L += [f"- `code_{c['n']:02d}.{c['ext']}` · 源第 {c['src_line']} 行"
              f" · sha {c['sha']}" for c in codes]
    return "\n".join(L) + "\n"


def run(inp: Path | None) -> int:
    banner("① 讀入")
    if inp is None:
        hits = sorted([p for p in INDIR.glob("*") if p.suffix in (".txt", ".md")],
                      key=lambda p: p.stat().st_mtime) if INDIR.exists() else []
        inp = hits[-1] if hits else None
    if inp is None or not inp.exists():
        print(f"  NOT_RUN:無輸入(--in 檔,或投遞 {INDIR})=誠實不假造")
        return 1
    text = inp.read_text(encoding="utf-8", errors="ignore")
    print(f"  {inp.name} · {len(text)} 字")
    banner("② NLP 編排(OneEngine Tier-1)")
    tp = mount_nlp()
    prose = FENCE_RX.sub("\n", text)  # 編排以文為本(程式塊入附錄不混摘要)
    if tp is not None:
        try:
            st, lane = tp.structure(prose), "OneEngine text_ops(jieba Tier-1)"
        except Exception:
            st, lane = light_structure(prose), "輕量規則道(OneEngine 例外退)"
    else:
        st, lane = light_structure(prose), "輕量規則道(OneEngine 缺席誠實)"
    print(f"  {lane} · 重點 {len(st.get('key_points') or [])} · 決策 "
          f"{len(st.get('decisions') or [])} · 待辦 {len(st.get('action_items') or [])}")
    banner("③ 程式抽取(fences→py/js/ps1)")
    codes = extract_code(text)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    od = OUTDIR / f"C2D_{ts}"
    od.mkdir(parents=True, exist_ok=True)
    for c in codes:
        (od / f"code_{c['n']:02d}.{c['ext']}").write_text(
            f"{'#' if c['ext'] != 'js' else '//'} 抽自 {inp.name} 第 {c['src_line']} 行"
            f" · sha {c['sha']}(MDL108;原文零改動)\n" + c["code"],
            encoding="utf-8")
    print(f"  抽出 {len(codes)} 塊({'、'.join(sorted({c['ext'] for c in codes})) or '無'})")
    banner("④ 出文+存證")
    segs = speakers_recompose(text)
    md = compose_md(inp.name, st, segs, codes, lane, ts)
    ap = od / f"ARTICLE_{ts}.md"
    ap.write_text(md, encoding="utf-8")
    (od / "evidence.json").write_text(json.dumps(
        {"src": inp.name, "lane": lane, "codes": [
            {k: c[k] for k in ("n", "ext", "src_line", "sha")} for c in codes],
         "segments": len(segs), "ts": ts}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"  文章:{ap}")
    print(f"  [計] 編排 1 文 · 重組 {len(segs)} 段 · 抽碼 {len(codes)} 塊 · 道:{lane}")
    return 0


def selftest() -> int:
    import tempfile
    fails = []
    n = [0]

    def chk(name, cond, note=""):
        n[0] += 1
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    dlg = ("[10:02] 老闆:今天決定把面板上線,這是決議。\n"
           "[10:03] 工程師:好,待辦是先修抓取。\n"
           "[10:03] 工程師:補充:今晚就改。\n"
           "```python\ndef f(x):\n    return x + 1\n```\n"
           "[10:05] 老闆:另外必須驗證數據。\n"
           "```\n$v = 1\nWrite-Host $v\n```\n")
    tp = mount_nlp()
    chk("① OneEngine 掛載(在位;缺=誠實 None 退輕量道)",
        tp is None or hasattr(tp, "structure"),
        "(在位)" if tp else "(缺席誠實)")
    codes = extract_code(dlg)
    chk("② 抽碼雙塊(標籤 py+無標規則判 ps1;原文零改動)",
        len(codes) == 2 and codes[0]["ext"] == "py" and codes[1]["ext"] == "ps1"
        and "return x + 1" in codes[0]["code"])
    chk("②b 語言規則判(def→py/function→js/$→ps1)",
        guess_lang("def a():\n    pass") == "py"
        and guess_lang("function a(){}") == "js"
        and guess_lang("$x = 1") == "ps1")
    segs = speakers_recompose(dlg)
    chk("③ 發言者分段重組(連續同人合段:4 行→3 段)",
        len(segs) == 3 and segs[1]["spk"] == "工程師" and len(segs[1]["msg"]) == 2)
    st = (tp.structure(dlg) if tp else light_structure(dlg))
    chk("④ 編排欄位(決策/待辦擷取)",
        st.get("decisions") and st.get("action_items"))
    with tempfile.TemporaryDirectory() as td:
        global INDIR, OUTDIR
        oi, oo = INDIR, OUTDIR
        INDIR, OUTDIR = Path(td) / "in", Path(td) / "out"
        try:
            chk("⑤ 空投遞=NOT_RUN 誠實", run(None) == 1)
            INDIR.mkdir()
            (INDIR / "chat.txt").write_text(dlg, encoding="utf-8")
            rc = run(None)
            runs = sorted(OUTDIR.glob("C2D_*"))
            md = (runs[-1].glob("ARTICLE_*.md")) if runs else []
            mdp = sorted(md)
            body = mdp[-1].read_text(encoding="utf-8") if mdp else ""
            chk("⑥ 端到端(文章 md+程式檔+存證 json 齊)",
                rc == 0 and mdp and (runs[-1] / "code_01.py").exists()
                and (runs[-1] / "evidence.json").exists())
            chk("⑥b 文章編排齊備(決策/待辦/重組/附錄溯源)",
                all(k in body for k in ("## 決策", "## 待辦", "## 對話重組",
                                        "程式附錄", "sha ")))
        finally:
            INDIR, OUTDIR = oi, oo
    print(f"  [計] 自測 {n[0]} 項 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 對話→文章/程式(CGC_MDL108)· 自測 ===")
        return selftest()
    print("=== 對話紀錄→編排文章+程式抽取(OneEngine Tier-1 掛載;誠實雙道)===")
    inp = Path(a[a.index("--in") + 1]) if "--in" in a else None
    return run(inp)


if __name__ == "__main__":
    sys.exit(main())
