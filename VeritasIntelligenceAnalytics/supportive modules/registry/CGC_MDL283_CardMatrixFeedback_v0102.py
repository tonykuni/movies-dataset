#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL283_CardMatrixFeedback v0102 — 薄尾(v0101 · v0100 一字不動):把現況矩陣新增的偵測區塊併進卡片與矩陣,並標明這一輪在哪種機器跑。

操作員 2026-11-17:「現況矩陣偵測還有哪方面沒管理到的請完善測試」。
  ① 預設來源(CGC_MDL282 尾版)若有 sec_extra,就把它回傳的通用項目併進來:號冊全類 · 號冊待辦 · 衝突登記 · 收據契約 · 測試分級 ·
     橋覆蓋 · 環境套件 · 資料庫 · 版本線 · 執行環境 · 管理面覆蓋。兩段篩選、對帳、成功鎖、更新回饋都照舊,新項目一樣每項恰有一個去向。
     來源沒有 sec_extra(只有 v0100)或 --in 外部項目冊時,行為跟 v0101 相同。
  ② 回饋包多一行 [主機]:Windows 主機 / 容器。容器跑的系統級綠不算主機實測,這一行讓讀的人(與動作主力 AI)不會把它當主機綠。
  ③ 回饋包多一行 [沒管到]:管理面覆蓋裡還是灰的面向,逐個點名。
動詞與旗標同 v0101。唯讀;只寫 VIA_Reports/vcgc。不發號 · 不裝套件 · 不連網 · 不載 TA-Lib。
呼叫  VIA_FROM_VCGC=YES python3 CGC_MDL149_…_vNNNN.py run CGC_MDL283_CardMatrixFeedback run --actor claude
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

import importlib.util
import platform
import shutil
import sys
import tempfile
from pathlib import Path

ENGINE = "CGC_MDL283_CardMatrixFeedback_v0102"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "CGC_MDL283_CardMatrixFeedback_v0101.py"
_PRIOR_FILE = HERE / PRIOR_NAME
_spec = importlib.util.spec_from_file_location("CGC_MDL283_CardMatrixFeedback_v0101", _PRIOR_FILE)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["CGC_MDL283_CardMatrixFeedback_v0101"] = PRIOR
_spec.loader.exec_module(PRIOR)
P0 = PRIOR.PRIOR          # v0100 本體(run 用它的全域名呼叫 assemble / write_out)
CTX = PRIOR.CTX
PRIOR.ENGINE = P0.ENGINE = ENGINE
_O = {"assemble": P0.assemble, "write_out": P0.write_out}   # 此刻指到 v0101 的包裝
STATE = {"gaps": [], "extra_n": 0, "extra_note": ""}


def monitor(via: Path):
    """載 CGC_MDL282 尾版;有 sec_extra 才用。"""
    p = P0.tail(via / "supportive modules" / "registry", "CGC_MDL282_LocalMonitor", ".py")
    return P0.load_py(p) if p else None


def host_line() -> str:
    import os
    win = platform.system() == "Windows"
    box = os.path.exists("/.dockerenv") or bool(os.environ.get("CLAUDE_CODE_REMOTE") or os.environ.get("CODESPACES"))
    return "[主機] Windows 主機實跑" if win else "[主機] %s%s · 這一輪的綠不算主機實測" % (platform.system(), "(容器)" if box else "")


def assemble(raw, source, prev, budget=300, peer=None):
    raw = list(raw)
    STATE.update(gaps=[], extra_n=0, extra_note="")
    if CTX.get("extras") and CTX.get("via") is not None:
        try:
            m = monitor(CTX["via"])
            if m is not None and hasattr(m, "sec_extra"):
                extra = m.sec_extra(CTX["via"])
                raw += extra
                STATE["extra_n"] = len(extra)
                STATE["gaps"] = [it["title"] for it in extra if it.get("section") == "管理面覆蓋" and it.get("lamp") == "x"]
            else:
                STATE["extra_note"] = "來源引擎沒有延伸偵測(只有五個區塊)"
        except Exception as e:  # 延伸偵測壞了不能拖垮基本矩陣,但要講出來
            STATE["extra_note"] = "延伸偵測出錯(%s: %s),這一輪只有基本區塊" % (type(e).__name__, P0.cut(e, 80))
    res = _O["assemble"](raw, source, prev, budget, peer)
    if STATE["extra_note"].startswith("延伸偵測出錯") and res["lamp"] == "g":
        res["lamp"] = "y"
    return res


def write_out(out: Path, res, pack, page, slug):
    extra = [host_line()]
    if STATE["extra_n"]:
        extra.append("[沒管到] 管理面覆蓋還是灰的 %d 個:%s" % (len(STATE["gaps"]), "、".join(STATE["gaps"]) or "沒有"))
    if STATE["extra_note"]:
        extra.append("[註] " + STATE["extra_note"])
    return _O["write_out"](out, res, pack[:2] + extra + pack[2:], page, slug)


P0.assemble, P0.write_out = assemble, write_out


def __getattr__(name):  # 薄尾轉接
    return getattr(PRIOR, name)


def selftest() -> int:
    fails = []

    def chk(name, cond, got=None):
        print("  [%s] %s%s" % ("過" if cond else "敗", name, "" if cond else " · 得到 %r" % (got,)), flush=True)
        if not cond:
            fails.append(name)
    saved = dict(CTX)
    chk("v0101(含 v0100)的自測在本版掛上後仍全過", PRIOR.selftest() == 0)
    tmp = Path(tempfile.mkdtemp(prefix="via_cmf102_st_"))
    global monitor
    real = monitor
    try:
        class Stub:
            @staticmethod
            def sec_extra(via):
                return [{"section": "衝突登記", "system": "VCGC", "lamp": "r", "id": "CONFLICT-00009", "title": "CONFLICT-00009", "detail": "OPEN · 待裁", "needs": True},
                        {"section": "管理面覆蓋", "system": "VCGC", "lamp": "x", "id": "備份", "title": "備份", "detail": "還沒管到 · 沒有來源"},
                        {"section": "管理面覆蓋", "system": "VCGC", "lamp": "g", "id": "衝突", "title": "衝突", "detail": "有來源"}]
        base = [{"section": "系統", "system": "VDF", "lamp": "g", "id": "VDF", "title": "VDF 入口", "detail": "實跑 rc 0"}]
        CTX.update(via=tmp, out=tmp, extras=True, famkey=True, lock=None, src="", actor="chatgpt")
        monitor = lambda via: Stub
        r = assemble(base, "自測來源", None, 300)
        k = {it["key"]: it for it in r["items"]}
        chk("延伸項目併進矩陣、分流照舊、對帳相符", "衝突登記|VCGC|CONFLICT-00009" in k and k["衝突登記|VCGC|CONFLICT-00009"]["cls"] == "DECIDE" and r["ok"], r["checks"])
        chk("灰的管理面記下來點名", STATE["gaps"] == ["備份"], STATE["gaps"])
        pk = write_out(tmp, r, list(r["head"]), lambda p: P0.render(r, P0.cards_of(r), p, "", "自測", "自測"), "st")
        chk("回饋包有 [主機] 與 [沒管到] 兩行,主力照記", any(x.startswith("[主機]") for x in pk) and any(x.startswith("[沒管到] 管理面覆蓋還是灰的 1 個:備份") for x in pk) and any(x.startswith("[主力] chatgpt") for x in pk))
        chk("不是 Windows 時寫明不算主機實測", platform.system() == "Windows" or "不算主機實測" in host_line())
        monitor = lambda via: object()
        r2 = assemble(base, "自測來源", None, 300)
        chk("來源沒有延伸偵測:照 v0101 行為並註明", sum(1 for it in r2["items"] if not it.get("gone")) == len(base) + 20 + 1 and "只有五個區塊" in STATE["extra_note"], (len(r2["items"]), STATE["extra_note"]))
        chk("上一輪鎖過的延伸項目這一輪沒了,照樣報退步", any(it.get("gone") and it["cls"] == "REG" for it in r2["items"]))

        def boom(via):
            raise RuntimeError("壞了")
        monitor = boom
        r3 = assemble(base, "自測來源", None, 300)
        chk("延伸偵測出錯:基本矩陣照出、綠降黃、原因寫進註", r3["ok"] and r3["lamp"] in ("y", "r") and "延伸偵測出錯(RuntimeError" in STATE["extra_note"], (r3["lamp"], STATE["extra_note"]))
        CTX.update(extras=False)
        r4 = assemble(base, "外部項目冊", None, 300)
        chk("--in 外部項目冊不混進 VCGC 的延伸項目", len(r4["items"]) == 1 and STATE["extra_n"] == 0)
    finally:
        monitor = real
        shutil.rmtree(str(tmp), ignore_errors=True)
        CTX.clear()
        CTX.update(saved)
    print("[selftest] %s · %d 敗 · %s" % ("GREEN" if not fails else "RED", len(fails), ENGINE), flush=True)
    return 0 if not fails else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    verb = args[0] if args and not args[0].startswith("-") else ("selftest" if "--selftest" in args else "run")
    if verb == "selftest":
        return selftest()
    if verb == "version":
        print("%s · %s(薄尾,前版 %s)" % (Path(__file__).name, ENGINE, PRIOR_NAME))
        return 0
    if verb == "spec":
        print(__doc__)
    return PRIOR.main(args)


if __name__ == "__main__":
    sys.exit(main())
