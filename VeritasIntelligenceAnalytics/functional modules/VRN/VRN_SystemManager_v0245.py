#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN-2 SystemManager v0245 — 薄尾(前版 = v0244 · 兩線合併點之後第一版)。

v0245(第 53 輪實證 · 兆豐切割 / 四重點):
① 分析師中文名:首頁「研究員:邱岳霖」「分析師:」「撰稿」「Analyst:」右側的名字 → 基本資料 ANALYST(原本只從 Email 推英文名 · 兆豐沒 Email → 空)
② 兆豐「基本資料」一格多值:收盤價 / 股本 / 市值 / 持股 從同一格文字抓(只補 ANALYST 旁的註記 · 不改年度數據冊)
③ 四重點不足 4 點(Note / 未評等 / 快訊)→ 從首頁本文依位置平均取句子補滿 4 點 · POINT_SOURCE 標「本文平均取 n 點」· 摘要冊重寫 · 缺項「四重點 x/4」解除
④ 驗收 / 分片全部重綁本版(與 v0244 同法)· 指紋含本版 · 完成判定管理器名稱 v0245
不改 v0244 / 另一線任何函式。
"""
from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import re
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "v0245"
DISPLAY_NAME = "VRN-2 SystemManager"
PRIOR_NAME = "VRN_SystemManager_v0244.py"
PRIOR_PATH = HERE / PRIOR_NAME
if not PRIOR_PATH.exists():
    raise FileNotFoundError("前版 %s 不在 · v0245 不接" % PRIOR_NAME)
_spec = importlib.util.spec_from_file_location("vrn_manager_prior_for_v0245", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

for _name, _value in vars(PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def _rebind(fn):
    return types.FunctionType(fn.__code__, globals(), fn.__name__, fn.__defaults__, fn.__closure__)


# ===== 1. 分析師中文名(研究員 / 分析師 / 撰稿 / Analyst 右側) =====
_AN_LABEL = re.compile(r"(?:研究員|分析師|研究人員|撰稿人?|撰寫人?|Analysts?|Research Analyst)\s*[:：]\s*([\u4e00-\u9fa5]{2,4}(?:\s*[、,，/]\s*[\u4e00-\u9fa5]{2,4}){0,3}|[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})")
_AN_STOP = {"分析師", "研究員", "資料來源", "投資評等", "目標價"}


def _an_names(text: str) -> list:
    out = []
    for m in _AN_LABEL.finditer(text or ""):
        for n in re.split(r"\s*[、,，/]\s*", m.group(1)):
            n = n.strip()
            if n and n not in _AN_STOP and n not in out:
                out.append(n)
    return out[:4]


_acc_basic_prior = PRIOR._acc_basic


def _acc_basic(r: dict, pdf) -> tuple:
    """v0245:先跑 v0244 的雙讀 · 分析師為空時從首頁文字補中文名(兆豐 研究員:邱岳霖 等)。"""
    lamp, st = _acc_basic_prior(r, pdf)
    try:
        if isinstance(st, dict) and not st.get("analysts"):
            zs = [z for pg in r.get("pages") or [] if pg.get("pno") == 1 for z in pg.get("zones", [])]
            ta = "\n".join([x.get("text", "") for z in zs for x in (z.get("records") or []) if isinstance(x, dict)] + [" ".join(c for c in row if c) for z in zs for row in (z.get("rows") or [])])
            names = _an_names(ta)
            if names:
                st["analysts"] = names
                st["analyst_src"] = "首頁標籤(研究員 / 分析師)"
                lamp = (lamp[0], "%s · 分析師(標籤) %s" % (lamp[1], "、".join(names)))
    except Exception:  # noqa: BLE001
        pass
    return lamp, st


# ===== 2. 四重點不足 → 本文平均取 =====
_SENT_SPLIT = re.compile(r"[。；;]\s*|\n+|\s*[➢•▪►◆■●]\s*")
_SENT_SKIP = re.compile(r"免責|僅供參考|本公司|法律責任|資料來源|不負|轉載|Disclosure|disclaimer|研究員\s*[:：]|報告日期|分析師\s*[:：]|^\W*$")


def _body_sentences(rec: dict) -> list:
    zs = [z for pg in rec.get("pages") or [] if pg.get("pno") == 1 for z in pg.get("zones", [])]
    texts = [x.get("text", "") for z in zs if "·TX" in str(z.get("id", "")) for x in (z.get("records") or []) if isinstance(x, dict)]
    out = []
    for t in texts:
        for s in _SENT_SPLIT.split(t):
            s = s.strip(" ,，、")
            if 15 <= len(s) <= 160 and not _SENT_SKIP.search(s) and s not in out:
                out.append(s)
    return out


def _fill_points(row: dict, rec: dict) -> int:
    have = [row.get("POINT_%d" % i) or "" for i in range(1, 5)]
    need = sum(1 for p in have if not p)
    if need == 0 or need == 4 and not rec:
        return 0
    sents = [s for s in _body_sentences(rec or {}) if not any(s[:20] in p for p in have if p)]
    if not sents:
        return 0
    n = len(sents)
    picks = []
    for i in range(min(need, n)):                                           # 每個等分區段取中點 · 不重複
        idx = min(n - 1, int((i + 0.5) * n / min(need, n)))
        if sents[idx] not in picks:
            picks.append(sents[idx])
    k = 0
    for i in range(4):
        if not have[i] and picks:
            row["POINT_%d" % (i + 1)] = picks.pop(0)
            k += 1
    if k:
        row["POINTS_OK"] = sum(1 for i in range(1, 5) if row.get("POINT_%d" % i))
        row["POINT_SOURCE"] = "本文平均取 %d 點(無評等段落)" % k
    return k


def _out_books(res, acc, st, v2):
    basic, fin, summ, gaps, made = PRIOR._out_books(res, acc, st, v2)
    try:
        byf = {r_.get("file"): r_ for r_ in (res or []) if isinstance(r_, dict)}
        filled = 0
        for row in summ:
            if (row.get("POINTS_OK") or 0) < 4:
                row.setdefault("POINT_SOURCE", "")
                filled += _fill_points(row, byf.get(row.get("FILENAME"), {}))
            else:
                row.setdefault("POINT_SOURCE", "")
        if filled:
            full = {row["FILENAME"][:28] for row in summ if (row.get("POINTS_OK") or 0) >= 4}
            ng = []
            for g in gaps:
                gs = str(g)
                f, _, miss = gs.partition(":")
                if f in full and "四重點" in miss:
                    miss2 = "、".join(x for x in miss.split("、") if "四重點" not in x)
                    if not miss2:
                        continue
                    gs = f + ":" + miss2
                ng.append(gs)
            gaps[:] = ng
            _rewrite_book(Path(v2) / "output", "Summary", summ)
            print("  [計] v0245 四重點補滿:本文平均取 %d 點 · 摘要冊重寫" % filled, flush=True)
    except Exception as exc:  # noqa: BLE001
        print("  [計] v0245 四重點補滿未完成 %s" % type(exc).__name__, flush=True)
    return basic, fin, summ, gaps, made


# ===== 3. 驗收 / 分片重綁本版(與 v0244 同法)· 指紋含本版 =====
_MY_SIG = hashlib.sha1("|".join(inspect.getsource(f) for f in (_acc_basic, _an_names, _fill_points, _body_sentences)).encode("utf-8")).hexdigest()[:12]
for _n in ("_base_acceptance", "_acc_parallel", "_acc_shard_main", "_acc_one", "_acc_one_core", "acceptance", "_acc_sig", "_native_vrn2", "vrn2", "_idem_check", "main", "_success_register"):
    globals()[_n] = _rebind(getattr(PRIOR, _n))


def completion(*args, **kwargs):
    result = PRIOR.completion(*args, **kwargs)
    try:
        result["manager"] = "%s %s" % (DISPLAY_NAME, TAG)
    except Exception:  # noqa: BLE001
        pass
    return result


# ===== 4. 自測 =====
def selftest() -> int:
    ok = [0, 0]
    def chk(name, cond):
        ok[0 if cond else 1] += 1
        print("  [%s] %s" % ("OK" if cond else "FAIL", name))
    nm = _an_names("報告日期:2025.08.19 研究員:邱岳霖\n分析師：王小明、李大華 Analyst: John Doe")
    chk("⓪ v0245 分析師標籤 %s" % nm, nm == ["邱岳霖", "王小明", "李大華", "John Doe"])
    rec = {"file": "x.pdf", "pages": [{"pno": 1, "zones": [{"id": "P1·M·10·TX", "records": [{"text": "➢ 太陽能進度遠遠落後，同時持續擴張使費用上升，Q2 EPS 0.7 元，低於預期。➢ H1 營運動能低於預期，且 7 月天災影響施工進度，2025 年下修。➢ 國內外業務雙管齊下，2026 年 EPS 13 元。➢ 本資料僅供參考，本公司不負法律責任。"}]}]}]}
    row = {"FILENAME": "x.pdf", "POINT_1": "維持目標價", "POINT_2": "", "POINT_3": "", "POINT_4": "", "POINTS_OK": 1}
    k = _fill_points(row, rec)
    chk("⓪ v0245 四重點平均取 %d 點 → POINTS_OK %s · 免責不入 %s · %s" % (k, row["POINTS_OK"], all("僅供參考" not in (row.get("POINT_%d" % i) or "") for i in range(1, 5)), row.get("POINT_SOURCE")),
        k == 3 and row["POINTS_OK"] == 4 and all("僅供參考" not in (row.get("POINT_%d" % i) or "") for i in range(1, 5)))
    chk("⓪ v0245 綁定:acceptance / _acc_parallel / _acc_shard_main / _acc_one / _acc_one_core 全綁本版 %s · _acc_one_core 用本版 _acc_basic %s · 指紋含本版 %s · 分片腳本 = 本檔 %s" % (
        all(f.__globals__ is globals() for f in (_base_acceptance, _acc_parallel, _acc_shard_main, _acc_one, _acc_one_core)), _acc_one_core.__globals__["_acc_basic"] is _acc_basic, _acc_sig() != PRIOR._acc_sig(), _acc_parallel.__globals__.get("__file__") == __file__),
        all(f.__globals__ is globals() for f in (_base_acceptance, _acc_parallel, _acc_shard_main, _acc_one, _acc_one_core)) and _acc_one_core.__globals__["_acc_basic"] is _acc_basic and _acc_sig() != PRIOR._acc_sig() and _acc_parallel.__globals__.get("__file__") == __file__)
    chk("⓪ v0245 vrn2 內部 _out_books / acceptance / completion 走本版 %s %s %s" % (_native_vrn2.__globals__["_out_books"] is _out_books, _native_vrn2.__globals__["acceptance"] is acceptance, _native_vrn2.__globals__["completion"] is completion),
        _native_vrn2.__globals__["_out_books"] is _out_books and _native_vrn2.__globals__["acceptance"] is acceptance and _native_vrn2.__globals__["completion"] is completion)
    import os
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") != "1":
        print("          ── 前版鏈(v0244)自測 ──")
        rc = PRIOR.selftest()
        chk("③ 前版鏈 v0244 自測 rc %s" % rc, rc == 0)
    p, f = ok
    print("[計] VRN-2 SystemManager v0245(VRN_SystemManager_v0245.py)自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main(sys.argv[1:]))
