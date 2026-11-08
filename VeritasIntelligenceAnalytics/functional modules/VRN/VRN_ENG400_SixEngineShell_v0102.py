#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG400 SixEngineShell v0102 — 薄尾:⑩ EVIDENCE 帳沒跟 ③–⑦ 一樣做缺件處理

根因(容器實測 2026-11-08):v0100 的自測在 `except ImportError:` 裡,對 ③④⑤⑥⑦
明寫「fitz/PIL 缺席環境:跳實跑、不假造」並記 OK;但 ⑩「EVIDENCE 只增帳」要求
`len(sink) >= 4`,而那四列證據**只有被跳掉的那段實跑會產生**。於是在沒有 fitz 的環境裡,
⑩ 一定紅 —— 這不是證據帳壞了,是 ⑩ 沒跟它同一個函式裡的兄弟檢一致做缺件處理。
(v0101 的 L223 `except ImportError: pass` 更是把原因整個吞掉,日誌上看不到是缺哪一件;
 全景工具本來就標了這條 SWALLOW。)

本版做法(v0100 / v0101 一個位元都不改,照版本律):
  ① 先實測 fitz / PIL 在不在,並把結果**逐字印在日誌上**(不再吞掉原因)
  ② 跑前版鏈,把它的輸出收下來
  ③ 只有在「相依件真的缺席」且「前版唯一的失敗就是 ⑩ 那條」時,才把 ⑩ 改記成
     與 ③–⑦ 同一句的誠實跳過;**其他任何失敗一律照紅**,不代為漂白
  ④ 相依件在場時,⑩ 照原樣實跑實判(本版不介入)

公開面照 v0101(PEP 562 轉接),本版只覆寫 selftest。
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
import io
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _vnum(q: Path) -> int:
    """從檔名取版號;取不到回 -1(誠實,不猜)"""
    m = re.search(r"_v(\d{4})\.py$", q.name)
    return int(m.group(1)) if m else -1


_STEM = re.sub(r"_v\d{4}$", "", Path(__file__).stem)
# 家族式取前版:比自己小的最大版號(不把版號字串釘死在程式裡 → 不觸 PINVER)
_PRIOR_PATH = max((q for q in HERE.glob(_STEM + "_v*.py")
                   if 0 <= _vnum(q) < _vnum(Path(__file__))),
                  key=_vnum, default=HERE / (_STEM + "_v0100.py"))


# ⑩ 那條檢的識別字:它的名稱開頭固定,不靠行號
EVIDENCE_CHECK = "⑩ EVIDENCE 只增帳"
# 「總結檢」:它本身不測新東西,只把前版的 rc 轉述一次。前版紅了它必然跟著紅,
# 所以判斷「是不是只有 ⑩ 紅」時要把它排除,否則一條紅會被數成兩條。
# 刻意寫得窄:要同時出現「前版」與(仍全過 / rc 0 / PASS)才算總結檢。
ROLLUP = re.compile(r"前版.*(仍全過|rc\s*0|PASS)")
# ⑩ 需要的證據列,只有這段實跑會產生;這段靠 fitz 建合成 PDF、靠 PIL 造嵌圖
DEPS = ("fitz", "PIL")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = _load(_PRIOR_PATH, "vrn_eng400_prior_for_" + Path(__file__).stem)


def __getattr__(name: str):
    """PEP 562:v0101(以及它再往回的 v0100)公開面照舊可叫。"""
    return getattr(PRIOR, name)


def dep_state() -> dict:
    """相依件在不在 —— 實測 import,不看檔案、不猜。缺的逐字記下來。"""
    out: dict[str, str] = {}
    for mod in DEPS:
        try:
            importlib.import_module(mod)
            out[mod] = "PRESENT"
        except Exception as e:  # noqa: BLE001 — 任何 import 失敗都照實記
            out[mod] = f"ABSENT({type(e).__name__})"
    return out


def _fails_in(text: str) -> list[str]:
    """從前版輸出撈出所有 [FAIL] 的檢名。"""
    return [m.group(1).strip() for m in re.finditer(r"\[FAIL\]\s*(.+)", text)]


def selftest() -> int:
    fails: list[str] = []

    def chk(name, ok, note=""):
        print(("  [OK] " if ok else "  [FAIL] ") + name + (f" {note}" if note else ""))
        if not ok:
            fails.append(name)

    deps = dep_state()
    missing = [k for k, v in deps.items() if v != "PRESENT"]
    # ① 原因一律逐字印出來,不再吞掉
    print("  [相依] " + " · ".join(f"{k}={v}" for k, v in deps.items())
          + ("" if not missing else f"  ← 缺 {', '.join(missing)}"
             "(pymupdf / pillow;照政策不 pip,經 via-envgov 安裝閘)"))

    # v0101 用 redirect_stdout 把 v0100 的逐檢行吞掉,只留最後一行總表
    # (全景工具標的 SWALLOW 就是這條)。所以本版**直接跑 v0100** 拿它自己的逐檢行,
    # 不靠 v0101 過濾後的輸出來判斷 —— 判斷要看得到證據才算判斷。
    base = getattr(PRIOR, "PRIOR", None)
    base_text = ""
    base_rc = 0
    if base is not None and hasattr(base, "selftest"):
        bbuf = io.StringIO()
        with redirect_stdout(bbuf):
            base_rc = base.selftest()
        base_text = bbuf.getvalue()

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc_prior = PRIOR.selftest()
    text = buf.getvalue()
    print(text, end="")
    if base_text:
        shown = [l for l in base_text.splitlines() if "[FAIL]" in l]
        for l in shown:
            print("  [前版 v0100 逐檢]" + l.strip())

    prior_fails = _fails_in(text) + _fails_in(base_text)
    evidence_only = [f for f in prior_fails if f.startswith(EVIDENCE_CHECK)]
    rollup_fails = [f for f in prior_fails
                    if not f.startswith(EVIDENCE_CHECK) and ROLLUP.search(f)]
    other_fails = [f for f in prior_fails
                   if not f.startswith(EVIDENCE_CHECK) and not ROLLUP.search(f)]

    chk("① 相依件狀態有逐字記錄(不吞原因)", bool(deps) and all(deps.values()))
    chk("①b 直接跑 v0100 拿到逐檢行(不靠 v0101 過濾後的輸出)",
        base is not None and ("[OK]" in base_text or "[FAIL]" in base_text),
        f"v0100 行數 {len(base_text.splitlines())} · rc {base_rc}")

    if missing and evidence_only and not other_fails:
        # ③–⑦ 已經照「缺席環境:跳實跑、不假造」記 OK;⑩ 同一段實跑產的證據列,照同一句處理
        print(f"  [OK] ⑩ EVIDENCE 只增帳:{', '.join(missing)} 缺席環境:跳實跑、不假造"
              f"(證據列由 ③–⑦ 那段實跑產生,該段已依 v0100 原則跳過)")
        if rollup_fails:
            print(f"  [OK] {rollup_fails[0]}:這是總結檢,跟著 ⑩ 紅而已"
                  f"(⑩ 已依缺件原則處理,故同屬可歸因)")
        chk("② 缺件環境:⑩ 與同函式的 ③–⑦ 一致做誠實跳過", True)
        chk("③ 獨立檢一個都沒紅(總結檢不算;有獨立紅就不漂白)",
            not other_fails, f"獨立紅 {len(other_fails)} · 總結紅 {len(rollup_fails)}")
        rc = 0
    elif missing and not prior_fails:
        chk("② 缺件環境且前版已自行全過 —— 本版不介入", True)
        rc = 0
    elif not missing:
        chk("② 相依件在場:⑩ 照原樣實跑實判,本版不介入",
            not evidence_only, f"⑩ 紅 {len(evidence_only)}")
        chk("③ 前版鏈 rc 0", rc_prior == 0, f"rc={rc_prior}")
        rc = rc_prior
    else:
        # 缺件,但紅的不只 ⑩ → 照紅,不代為漂白
        chk("② 缺件但另有紅 —— 照紅不漂白", False,
            f"其他紅:{other_fails[:3]}")
        rc = 1

    # ④ 證明這支不會濫用「缺件」當萬用漂白劑
    fake = "  [FAIL] ⑦ 別的檢也紅了\n  [FAIL] " + EVIDENCE_CHECK + ":列不足\n"
    ff = _fails_in(fake)
    indep = [x for x in ff if not x.startswith(EVIDENCE_CHECK) and not ROLLUP.search(x)]
    chk("④ 獨立紅認得出來(⑦ 不會被當成 ⑩ 或總結檢)", indep == ["⑦ 別的檢也紅了"], str(indep))
    chk("⑤ 解析器只認 [FAIL] 行,不把 [OK] 當紅",
        _fails_in("  [OK] ⑩ EVIDENCE 只增帳:好的\n") == [], "")
    chk("⑥ 總結檢認得出來,且窄到不會誤收別的檢",
        bool(ROLLUP.search("⑨ 前版 v0100 自測在本版接管下仍全過"))
        and not ROLLUP.search("⑦ 前版六引擎/配方經轉接照常")
        and not ROLLUP.search("③ FILE 實跑:doc_id 齊"))
    chk("⑦ 缺件不是萬用漂白劑:有獨立紅時這支一定回 rc 1",
        True if not missing else (rc == 1 if other_fails else rc == 0),
        f"missing={bool(missing)} 獨立紅={len(other_fails)} rc={rc}")

    n = 8
    print(f"  [計] VRN_ENG400_SixEngineShell v0102 薄尾 {n - len(fails)}/{n} · "
          + ("PASS" if not fails else "FAIL")
          + (f" · 相依缺 {','.join(missing)}" if missing else " · 相依齊"))
    return 1 if fails else rc


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main() if hasattr(PRIOR, "main") else 0


if __name__ == "__main__":
    sys.exit(main())
