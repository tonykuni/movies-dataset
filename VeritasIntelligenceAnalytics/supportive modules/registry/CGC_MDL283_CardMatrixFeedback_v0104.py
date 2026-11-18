#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL283_CardMatrixFeedback v0104 — 薄尾(v0103 · v0102 · v0101 · v0100 一字不動):Windows 主機上頁面樣式不掉。

為什麼:頁面的樣式要先核「釘住的 token 冊」雜湊才套。v0100 直接拿檔案位元組算;Windows 上 git 預設把行尾換成 CRLF,
同一本冊多出「行數」個位元組,雜湊對不上 → 頁面被判成「token 冊與鎖的雜湊不符」而不套樣式。那是判錯,不是冊被改。
(倉的教訓:跨平台位元組,算雜湊前先統一成 LF;自測放一份 CRLF 檔。)
本版只改兩處,其餘照 v0103:
  ① template():算 token 冊雜湊前先把 CRLF 換成 LF;冊真的被改過仍然照實判紅、不套樣式。
  ② 收據 STATUS_latest.json 的 version 寫本版(v0103 寫死成 v0103)。
唯讀倉;不發號 · 不裝套件 · 不連網 · 不載 TA-Lib。動詞與旗標同 v0103。
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
import importlib.util
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ENGINE = "CGC_MDL283_CardMatrixFeedback_v0104"
VERSION = "v0104"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "CGC_MDL283_CardMatrixFeedback_v0103.py"
_PRIOR_FILE = HERE / PRIOR_NAME
_spec = importlib.util.spec_from_file_location("CGC_MDL283_CardMatrixFeedback_v0103", _PRIOR_FILE)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules["CGC_MDL283_CardMatrixFeedback_v0103"] = PRIOR
_spec.loader.exec_module(PRIOR)
P0 = PRIOR.P0               # v0100 本體(run 用它的全域名呼叫 template / write_out)
PRIOR.ENGINE = PRIOR.PRIOR.ENGINE = PRIOR.P1.ENGINE = P0.ENGINE = ENGINE
PRIOR.MANIFEST["engine"] = ENGINE
_O = {"write_out": P0.write_out}   # 此刻指到 v0103 的包裝


def lf_sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def template(via: Path):
    """回 (css 全文, 狀態說明, 燈)。同 v0100,但 token 冊的雜湊先統一成 LF 再算。"""
    reg = Path(via) / "supportive modules" / "registry"
    lock = P0.tail(reg, "VIA_UI_WorkPlatform_TemplateLock", ".json")
    if lock is None:
        return "", "模板鎖冊不在(頁面不套樣式)", "x"
    try:
        b = json.loads(lock.read_text(encoding="utf-8"))
        css = b["css"]
        if hashlib.sha256(css.encode("utf-8")).hexdigest() != b.get("css_sha256"):
            return "", "%s 的 css 與鎖的雜湊不符(頁面不套樣式)" % lock.name, "r"
        tf = b["tokens_from"]
        tb = reg / ("%s_%s.json" % (tf["family"], tf["pinned"]))
        if not tb.exists():
            return "", "釘住的 token 冊 %s 不在(頁面不套樣式)" % tb.name, "r"
        if lf_sha(tb) != tf.get("sha256"):
            return "", "token 冊 %s 與鎖的雜湊不符(頁面不套樣式)" % tb.name, "r"
        tokens = json.loads(tb.read_text(encoding="utf-8"))["tokens"]
        root = ":root{" + ";".join("--%s:%s" % (k, v) for k, v in tokens.items() if "<" not in str(v) and "}" not in str(v)) + "}"
        return root + "\n" + css, "%s · token %s" % (lock.stem, tb.stem), "g"
    except (OSError, ValueError, KeyError, TypeError) as e:
        return "", "模板讀不到(%s)" % type(e).__name__, "r"


def write_out(out: Path, res, pack, page, slug):
    final = _O["write_out"](out, res, pack, page, slug)
    p = Path(out) / "STATUS_latest.json"
    try:
        rec = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return final                    # v0103 沒寫出收據:不補一份假的
    if rec.get("version") != VERSION:
        rec["version"] = VERSION
        tmp = p.with_name(p.name + ".%d.tmp" % os.getpid())
        tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(str(tmp), str(p))
    return final


P0.template, P0.write_out = template, write_out


def __getattr__(name):  # 薄尾轉接
    return getattr(PRIOR, name)


def selftest() -> int:
    fails = []

    def chk(name, cond, got=None):
        print("  [%s] %s%s" % ("過" if cond else "敗", name, "" if cond else " · 得到 %r" % (got,)), flush=True)
        if not cond:
            fails.append(name)
    chk("v0103(含前版鏈)的自測在本版掛上後仍全過", PRIOR.selftest() == 0)
    reg = HERE
    lock = P0.tail(reg, "VIA_UI_WorkPlatform_TemplateLock", ".json")
    chk("真倉:模板鎖冊在", lock is not None)
    tmp = Path(tempfile.mkdtemp(prefix="via_cmf104_st_"))
    try:
        if lock is not None:
            b = json.loads(lock.read_text(encoding="utf-8"))
            tb = reg / ("%s_%s.json" % (b["tokens_from"]["family"], b["tokens_from"]["pinned"]))
            for tag, conv in (("lf", lambda x: x.replace(b"\r\n", b"\n")), ("crlf", lambda x: x.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))):
                via = tmp / tag
                r2 = via / "supportive modules" / "registry"
                r2.mkdir(parents=True)
                (r2 / lock.name).write_bytes(conv(lock.read_bytes()))
                (r2 / tb.name).write_bytes(conv(tb.read_bytes()))
                css, note, lamp = template(via)
                chk("token 冊行尾是 %s:照樣核過並套樣式" % tag.upper(), lamp == "g" and css.startswith(":root{") and "--lamp-green" in css, (lamp, note))
            crlf = tmp / "crlf" / "supportive modules" / "registry" / tb.name
            chk("自測用的 CRLF 檔真的是 CRLF,而且 v0100 的算法會把它判錯", b"\r\n" in crlf.read_bytes() and hashlib.sha256(crlf.read_bytes()).hexdigest() != b["tokens_from"]["sha256"])
            crlf.write_bytes(crlf.read_bytes().replace(b"#16a34a", b"#16a34b"))
            css, note, lamp = template(tmp / "crlf")
            chk("token 冊內容真的被改:仍判紅、不套樣式", lamp == "r" and css == "" and "雜湊不符" in note, (lamp, note))
            (tmp / "crlf" / "supportive modules" / "registry" / lock.name).unlink()
            chk("鎖冊不在:灰、不套樣式", template(tmp / "crlf")[2] == "x")
        out = tmp / "out"
        out.mkdir()
        raw = [{"section": "系統", "system": "VCGC", "lamp": "y", "id": "a", "title": "a", "detail": "待看"}, {"section": "系統", "system": "VDF", "lamp": "g", "id": "b", "title": "b", "detail": "好"}]
        r = P0.assemble(raw, "自測", None)
        write_out(out, r, list(r["head"]), lambda p: P0.render(r, P0.cards_of(r), p, "", "自測", "自測"), "st")
        rec = json.loads((out / "STATUS_latest.json").read_text(encoding="utf-8"))
        chk("收據的 version 與 engine 都是本版", rec.get("version") == VERSION and rec.get("engine") == ENGINE, (rec.get("version"), rec.get("engine")))
        chk("收據其餘欄位還在(lamp · summary · at · checks)", all(k in rec for k in ("lamp", "summary", "at", "checks")), sorted(rec)[:8])
        chk("沒留下暫存檔", not list(out.glob("*.tmp")))
    finally:
        shutil.rmtree(str(tmp), ignore_errors=True)
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
    return PRIOR.main(args)


if __name__ == "__main__":
    sys.exit(main())
