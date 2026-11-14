#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SUP_MDL744_NLPApplicationHub v0103 — v0102 薄尾(v0102 一字不動):詞庫找不到就到尾版收容包內的既有位置找,TextProcessor 才掛得起來。

實錄(2026-11-13 容器全量實跑 VRN_SystemManager v0265 test:VRN_ENG087 FAIL「TextProcessor 正規化」):
  ENG087 期望 '台積電 2330 買進, 需求強勁。'(正主會在半形逗號後補空白),實得 '買進,需求'(純 stdlib NFKC)。
根因(逐層追到底):
  ① 尾版收容件已是 VIA_NLP_OneEngine_v1.9.0(語意序最大),v0102 到「尾版夾/data/lexicon/ssot_lexicon.json」找詞庫;
  ② v1.9.0 包的詞庫放在 embedded_sources/legacy/data/lexicon/(v1.1.0~v1.8.0 都在 data/lexicon/;七份 sha256 全同 9201144e…);
  ③ 找不到 → v0102 改呼 TextProcessor(None) → v1.9.0 的 TextProcessor 一定要路徑 → TypeError 被吞 → tp = None;
  ④ nfkc 退回 stdlib(逗號後不補空白)、summarize 回 ABSENT(要 tp)→ ENG087 紅、本橋自測 ⑥ 紅、⑫ 只得 ABSENT。
本版只換 text_processor():詞庫找法 = 尾版夾/data/lexicon/ssot_lexicon.json → 尾版夾內任何 data/lexicon/ssot_lexicon.json(路徑排序取第一);
  兩者都沒有才照 v0102 試無詞庫建構;建構失敗原因照實存起來(lexicon_why())不再只剩 None。收容件一位元不動、不複製、不寫檔。
另:v0102 自測 ①② 把「尾版 = Application_System v1.8.0」寫死(v1.9.0 收容後永遠紅)→ 本版 ①′②′ 改成動態:
  掛的就是語意序最大那一版、跨兩家族候選都在、語意序 ≥ 字母序。其餘十檢照 v0102 跑照印。
VRN 支援模組;零網路 · 不用 TA-Lib · 不寫同意閘 · 不裝套件。用法同 v0102:status | roster | delta | demo | summarize … | --selftest | --json
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
# [VIA:NET-BRIDGE] 留名:本版不出網

import contextlib
import importlib.util
import io
import re
import sys
from pathlib import Path

VERSION = "v0103"
HERE = Path(__file__).resolve().parent
_STEM = "SUP_MDL744_NLPApplicationHub"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_v0103", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_LEX_WHY = {"why": ""}


def __getattr__(name):
    return getattr(PRIOR, name)


def lexicon_path(mount_dir) -> Path | None:
    """尾版夾/data/lexicon/ssot_lexicon.json → 尾版夾內任一 data/lexicon/ssot_lexicon.json(路徑排序取第一)→ None。"""
    if not mount_dir:
        return None
    d = Path(mount_dir)
    direct = d / PRIOR.LEXICON_REL
    if direct.is_file():
        return direct
    hits = sorted(p for p in d.rglob("ssot_lexicon.json")
                  if p.is_file() and p.parent.name == "lexicon" and p.parent.parent.name == "data")
    return hits[0] if hits else None


def lexicon_why() -> str:
    return _LEX_WHY["why"]


def text_processor():
    """TextProcessor 單例(同 v0102,只差詞庫找法 + 失敗原因照實存)。"""
    if "tp" in PRIOR._CACHE:
        return PRIOR._CACHE["tp"]
    tp, why = None, ""
    mod = PRIOR._sub("text_ops")
    m = PRIOR.mount()
    if mod is None or not m.get("dir"):
        why = "text_ops 模組或收容件不在(%s)" % m.get("state")
    else:
        lex = lexicon_path(m["dir"])
        try:
            tp = mod.TextProcessor(lex) if lex is not None else mod.TextProcessor(None)
            if lex is not None and lex != Path(m["dir"]) / PRIOR.LEXICON_REL:
                why = "詞庫取自包內 %s(尾版夾 data/lexicon 沒有)" % lex.relative_to(m["dir"]).as_posix()
        except Exception as exc:  # noqa: BLE001 — 照實存原因,不再只剩 None
            tp, why = None, "TextProcessor 建不起來(%s: %s;詞庫 %s)" % (type(exc).__name__, str(exc)[:80], lex)
    _LEX_WHY["why"] = why
    PRIOR._CACHE["tp"] = tp
    return tp


PRIOR.text_processor = text_processor      # v0102 的 nfkc / summarize / segments 用模組全域名 → 換成本版


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    print("=== %s %s · 薄尾自測(詞庫退路 + ①②動態;其餘十檢照 v0102)===" % (PRIOR.MODULE_ID, VERSION), flush=True)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = PRIOR.selftest()
    out = buf.getvalue()
    print(out, end="")
    fails = [ln.strip() for ln in out.splitlines() if "[FAIL]" in ln]
    stale = [ln for ln in fails if ln.startswith("[FAIL] ①") or ln.startswith("[FAIL] ②")]
    other = [ln for ln in fails if ln not in stale]
    m = PRIOR.mount()
    cands = PRIOR.roots()
    sem = PRIOR.newest()
    alpha = sorted(cands, key=lambda p: p.name)[-1] if cands else None
    chk("①′ 掛的就是語意序最大那一版(VERIFIED · 版號 = newest() 動態,不寫死)",
        m.get("state") == "VERIFIED" and sem is not None and m.get("version") == ".".join(map(str, PRIOR._ver(sem))), "%s · %s" % (m.get("state"), m.get("version")))
    fams = {p.name.split("_v")[0] for p in cands}
    chk("②′ 跨兩家族候選都在 · 語意序 ≥ 字母序(字母序陷阱另由 ③ 驗)",
        {"VIA_NLP_OneEngine", "VIA_NLP_Application_System"} <= fams and sem is not None and alpha is not None and PRIOR._ver(sem) >= PRIOR._ver(alpha),
        "候選 %d · 語意序 %s · 字母序 %s" % (len(cands), sem.name if sem else "-", alpha.name if alpha else "-"))
    tp = text_processor()
    chk("⑬ TextProcessor 掛得起來(詞庫退路)· 失敗會說原因", tp is not None, lexicon_why() or "尾版夾 data/lexicon 直接命中")
    chk("⑭ ENG087 判別句:'台積電 2330 買進，需求強勁。' → 半形逗號後補空白(走正主,不是 stdlib)",
        PRIOR.nfkc("台積電 2330 買進，需求強勁。風險為匯率波動。") == "台積電 2330 買進, 需求強勁。風險為匯率波動。")
    sm = PRIOR.summarize("台積電今年營收成長。毛利率維持高檔。風險為匯率波動。", 2)
    chk("⑮ 證據型摘要不再因 tp 缺席回 ABSENT(OK/EMPTY · 有點就帶 source_span)",
        sm.get("state") in ("OK", "EMPTY") and all(isinstance(p.get("source_span"), dict) for p in sm.get("points", [])), sm.get("state"))
    chk("⑯ v0102 十二檢:除了寫死尾版 v1.8.0 的 ①② 以外全過", not other, " · ".join(x[:60] for x in other) or "rc %s · 只紅寫死項 %d" % (rc, len(stale)))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑰ 不寫檔 · 不出網 · 不用 TA-Lib · 不寫同意閘", not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib)", src, re.M)
        and ".write_text(" not in src.split("def selftest")[0] and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src))
    n = sum(ok)
    print("  [計] %s %s 薄尾 %d/%d · 合計 %s" % (PRIOR.MODULE_ID, VERSION, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
