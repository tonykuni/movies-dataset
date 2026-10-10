#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL275_Z281TwinProbe v0100 — 無版號檔 × _v0100 版號雙胞的結構探針(Z281 移交前的交接測試)

操作員裁定(2026-10-10,PR #518):5 支無版號 .py(Z281 命名待逐支判定)各出內容不變的 `_v0100` 版號檔,
  讓中央元件冊(registry-sync 只登尾版家族)登得到;舊無版號檔仍有人引用就不搬,交接閘記「等 Z281 移交」。
本探針是**結構檢**(不是行為測試,照實標明):對每一對(無版號原檔, _v0100 雙胞)
  ① 雙胞存在且與原檔位元組相同(CRLF 正規化後)   ② 兩支都 ast.parse + compile 過(只編譯、不執行、不匯入)
  ③ 有 `if __name__ == "__main__"` 防護(匯入不會跑主程式)   ④ 加速器橋在;VDF 檔另要網路橋在
  ⑤ 不匯入 TA-Lib
行為正確性仍要靠各檔自己的測試;vrn_sample_reader 有自帶 --selftest,本探針只記「有」,不代跑(不以目前解譯器直派)。
只收 VCGC 呼叫。零網路。唯讀:不寫任何檔。
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

import ast
import hashlib
import os
import re
import sys
from pathlib import Path

ENGINE = "CGC_MDL275_Z281TwinProbe"
VERSION = "v0100"
VIA = Path(__file__).resolve().parents[2]

# 操作員 2026-10-10 裁定的 5 對(原檔 → 雙胞);新增要出新版號檔,不就地改
TWINS = (
    "functional modules/VDF/VDF_MDL001_TWEquityEngine.py",
    "functional modules/VDF/VDF_MDL201_GenerateFullRegistry.py",
    "functional modules/VDF/VDF_MDL303_RegistryActivation.py",
    "functional modules/VRN/financial_data_standardization.py",
    "functional modules/VRN/vrn_sample_reader.py",
)


def twin_of(rel: str) -> str:
    return rel[:-3] + "_v0100.py"


def _norm_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _compiles(path: Path) -> tuple[bool, str]:
    try:
        src = path.read_text(encoding="utf-8")
        compile(ast.parse(src, str(path)), str(path), "exec", dont_inherit=True)
        return True, ""
    except Exception as exc:  # noqa: BLE001 — 照實回報哪一支、什麼錯
        return False, f"{type(exc).__name__}: {exc}"


def _has_main_guard(src: str) -> bool:
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.If) and isinstance(node.test, ast.Compare):
            names = {getattr(n, "id", None) for n in ast.walk(node.test)} | {getattr(n, "value", None) for n in ast.walk(node.test)}
            if "__name__" in names and "__main__" in names:
                return True
    return False


def probe_pair(rel: str, via: Path = VIA) -> dict:
    orig, twin = via / rel, via / twin_of(rel)
    row = {"original": rel, "twin": twin_of(rel), "checks": {}}
    c = row["checks"]
    c["twin_identical"] = orig.is_file() and twin.is_file() and _norm_sha(orig) == _norm_sha(twin)
    ok_o, err_o = _compiles(orig) if orig.is_file() else (False, "absent")
    ok_t, err_t = _compiles(twin) if twin.is_file() else (False, "absent")
    c["compile"] = ok_o and ok_t
    row["compile_error"] = err_o or err_t
    src = twin.read_text(encoding="utf-8") if twin.is_file() else ""
    c["main_guard"] = bool(src) and _has_main_guard(src)
    c["accel_bridge"] = "[VIA:ACCEL-BRIDGE:v" in src
    c["net_bridge"] = ("[VIA:NET-BRIDGE:v" in src) if "/VDF/" in rel else True
    c["no_talib"] = not re.search(r"^\s*(import|from)\s+talib\b", src, re.M)
    row["own_selftest"] = "--selftest" in src
    row["pass"] = all(c.values())
    return row


def run(via: Path = VIA) -> list[dict]:
    return [probe_pair(rel, via) for rel in TWINS]


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    rows = run()
    for r in rows:
        bad = [k for k, v in r["checks"].items() if not v]
        chk(f"{Path(r['twin']).name}:雙胞同位元組 · 編譯 · __main__ 防護 · 橋 · 不碰 TA-Lib", r["pass"],
            ",".join(bad) + (f" · {r['compile_error']}" if r["compile_error"] else ""))
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "functional modules" / "VDF").mkdir(parents=True)
        a = t / "functional modules" / "VDF" / "X.py"
        # write_bytes:Windows 文字模式會把 "\r\n" 再轉成 "\r\r\n",夾具要逐位元組寫
        body = b"# [VIA:ACCEL-BRIDGE:v0100]\n# [VIA:NET-BRIDGE:v0100]\nx = 1\nif __name__ == '__main__':\n    pass\n"
        a.write_bytes(body)
        (t / "functional modules" / "VDF" / "X_v0100.py").write_bytes(body + b"y = 2\n")
        r = probe_pair("functional modules/VDF/X.py", t)
        chk("負控:雙胞內容不同 → twin_identical 判 FAIL", not r["checks"]["twin_identical"] and not r["pass"])
        (t / "functional modules" / "VDF" / "X_v0100.py").write_bytes(body.replace(b"\n", b"\r\n"))
        r = probe_pair("functional modules/VDF/X.py", t)
        chk("CRLF 簽出不算內容不同", r["checks"]["twin_identical"] and r["pass"])
    text = Path(__file__).read_text(encoding="utf-8")
    chk("本檔:加速器橋在(__future__ 之後)· 不寫檔 · 不以目前解譯器直派",
        "[VIA:ACCEL-BRIDGE:v0100]" in text and text.index("from __future__") < text.index("[VIA:ACCEL-BRIDGE")
        and "subprocess" not in text.split("def selftest")[0])
    passed = all(ok)
    print(f"[計] {ENGINE} {VERSION} 自測 {sum(ok)}/{len(ok)} · 結構檢(非行為測試)· {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[DENY] VCGC entry required")
        return 2
    if args[:1] == ["--selftest"]:
        return selftest()
    for r in run():
        print(f"[{'PASS' if r['pass'] else 'FAIL'}] {r['twin']} · {r['checks']} · 自帶自測 {r['own_selftest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
