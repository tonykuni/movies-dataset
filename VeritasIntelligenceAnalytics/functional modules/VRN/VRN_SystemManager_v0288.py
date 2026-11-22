#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0288 — 薄尾(v0287 以前一字不動):help 不再印 v0269 原生處理器的舊表頭

  操作員 2026-11-22:「hide the v0269 help block」。v0287 的 help 先印現役尾版一行,接著把 v0269 原生處理器的 help 原樣貼上:
      VRN_SystemManager v0269 · VRN 自己的入口(…)          ← 舊版號表頭(看起來像現役是 v0269)
        標準動詞(本版):help · version · …                    ← 「本版」指 v0269
        其餘動詞:原樣轉交前版 VRN_SystemManager_v0268.py;…   ← 舊轉交說明(現役鏈是 v0288 → … → v0269 → v0268)
  本版只改 help 的這一段:拿掉 v0269 表頭與舊轉交句,「標準動詞(本版)」改「標準動詞」,換一句不帶版號的轉交說明;
  rc 說明 · v0278 synchronizer 段 · v0270 以後加的動詞表照 v0287。動詞一個都不少(help 涵蓋檢查照 v0286 的尺)。
  version / health / verbs 照 v0287 的做法,只是鏈頭改成本版(現役尾版 = 本版、鏈從本版算起);其餘動詞一律交給 v0287。
  零網路 · 不碰 TA-Lib · 不讀寫同意閘 · 不替別的系統設入口旗標。自測:python VRN_SystemManager_v0288.py --selftest
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import contextlib
import importlib.util
import io
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VRN_SystemManager"
TAG = "VRN_SystemManager v0288"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0288", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
NATIVE = PRIOR.NATIVE
NATIVE_FLOOR = PRIOR.NATIVE_FLOOR
OLD_HEAD_RE = re.compile(r"^VRN_SystemManager v\d{4} · VRN 自己的入口")
OLD_FORWARD_RE = re.compile(r"^\s*其餘動詞:原樣轉交前版 VRN_SystemManager_v\d{4}\.py")


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


_PRIOR_CHAIN = PRIOR.chain_modules                  # v0287 原本的鏈(呼叫期間 PRIOR.chain_modules 會被換成本版的,所以先留住)


def chain_modules() -> list:
    return [sys.modules[__name__]] + _PRIOR_CHAIN()


def chain_report() -> dict:
    return PRIOR.PRIOR.chain_report(chain_modules())


def verb_table() -> list:
    return PRIOR.PRIOR.verb_table(chain_modules())


def _capture(fn, *a):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = fn(*a)
    return rc, buf.getvalue()


@contextlib.contextmanager
def _as_head():
    """v0287 的 version / health / help / verbs 原樣沿用,只在呼叫期間把它的鏈頭、TAG、檔名換成本版(用完還原;v0287 檔一字不動)。"""
    keep = {k: getattr(PRIOR, k) for k in ("TAG", "chain_modules", "chain_report", "verb_table")}
    PRIOR.TAG = TAG                                  # 檔名 / 前版路徑不換:鏈檢查靠每個模組自己的檔名認版
    PRIOR.chain_modules, PRIOR.chain_report, PRIOR.verb_table = chain_modules, chain_report, verb_table
    try:
        yield
    finally:
        for k, v in keep.items():
            setattr(PRIOR, k, v)


def clean_native_help(text: str) -> str:
    """只改第一個「──」段之前(v0269 原生處理器自己的那一塊):拿掉舊版號表頭與舊轉交句;其餘一行不動。"""
    out, head_done = [], False
    for ln in text.splitlines():
        if not head_done and ln.lstrip().startswith("──"):
            head_done = True
        if not head_done:
            if OLD_HEAD_RE.match(ln):
                continue
            if OLD_FORWARD_RE.match(ln):
                out.append("  舊動詞:鏈底原生處理器原樣轉交更舊的版(子行程);標準動詞加 --legacy 看前版原樣輸出")
                continue
            ln = ln.replace("標準動詞(本版):", "標準動詞:")
        out.append(ln)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def cmd_help() -> int:
    with _as_head():
        rc, out = _capture(PRIOR.cmd_help)
    first, _, rest = out.partition("\n")
    print(first)
    print(clean_native_help(rest), end="")
    return rc


def live_tail() -> dict:
    return {"manager": Path(__file__).name, "version": "v%04d" % _vnum(__file__), "sha256": PRIOR.PRIOR._file_sha(Path(__file__)),
            "prior": PRIOR_PATH.name, "native_handler": "v%04d" % NATIVE_FLOOR}


def cmd_version(args=()) -> int:
    """照 v0287:--json 是前版原生處理器的 JSON 加 live_tail / chain;文字第一行標現役尾版 + 整條鏈,接著前版原生處理器那一行。"""
    import json
    cr = chain_report()
    tail = live_tail()
    if "--json" in args:
        with _as_head():
            rc, body, text = PRIOR._prior_json(["version", "--json"])
        body = dict(body) if isinstance(body, dict) else {"prior_text": text}
        body["live_tail"] = tail
        body["chain"] = {"count": cr["count"], "complete": not cr["bad"], "bad": cr["bad"], "versions": [r["version"] for r in cr["rows"]]}
        print(json.dumps(body, ensure_ascii=False, indent=1))
        return 1 if cr["bad"] else rc
    print("[%s] VRN · 現役尾版 %s · sha %s · 鏈 %d 版(%s → v%04d 原生處理器)· %s" % (
        TAG, tail["manager"], tail["sha256"][:12], cr["count"], cr["tail"], NATIVE_FLOOR,
        "鏈完整" if not cr["bad"] else "鏈有問題:" + ";".join(cr["bad"][:3])))
    rc, out = _capture(NATIVE.main, ["version"])
    for ln in out.splitlines():
        print("  前版原生處理器 · " + ln)
    return 1 if cr["bad"] else rc


def cmd_health(args) -> int:
    """v0287 的 health 原樣跑(鏈從本版算起、判決行標本版);--json 時 live_tail 改標本版。"""
    import json
    with _as_head():
        rc, out = _capture(PRIOR.cmd_health, args)
    if "--json" in args:
        try:
            body = json.loads(out)
        except ValueError:
            print(out, end="")
            return rc
        body["live_tail"] = {"manager": Path(__file__).name, "version": "v%04d" % _vnum(__file__)}
        print(json.dumps(body, ensure_ascii=False, indent=1))
        return rc
    print(out, end="")
    return rc


def cmd_verbs(args) -> int:
    with _as_head():
        return PRIOR.cmd_verbs(args)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    if not args or args[:1] == ["help"]:
        return cmd_help()
    if args[:1] == ["version"] and "--legacy" not in args:
        return cmd_version(args[1:])
    if args[:1] == ["health"] and "--legacy" not in args:
        return cmd_health(args[1:])
    if args[:1] == ["verbs"]:
        return cmd_verbs(args[1:])
    return PRIOR.main(args)


def selftest() -> int:
    import json
    import os
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)

    # v0287 / v0286 的自測假設自己是磁碟上最新那一版:測 v0287 時給 v0286 的 chain_report 看「到 v0287 為止」的版名清單,測完換回。
    base = PRIOR.PRIOR
    real_cr = base.chain_report
    with tempfile.TemporaryDirectory(prefix="via_vrn288_fam_") as fam:
        for p in HERE.glob(FAMILY + "_v*.py"):
            if 0 <= _vnum(p) <= _vnum(PRIOR_PATH):
                (Path(fam) / p.name).write_text("", encoding="utf-8")
        base.chain_report = lambda mods=None, family_dir=None: real_cr(mods, fam if family_dir is None else family_dir)
        try:
            rc0, out0 = _capture(PRIOR.selftest)
        finally:
            base.chain_report = real_cr
    print(f"=== {TAG} · 薄尾自測(help 不印 v0269 舊表頭 · 動詞不少 · 鏈頭 = 本版;零網路)===")
    chk("⓪ 直接前版 %s 自測過(v0287 原封不動)" % PRIOR_PATH.name, rc0 == 0, out0[-300:])
    _, help_out = _capture(cmd_help)
    table = verb_table()
    chk("① help 第一行標本版", help_out.startswith(TAG), help_out[:120])
    chk("② help 不再出現 v0269 舊表頭與「轉交前版 v0268」舊句", not re.search(r"VRN_SystemManager v0269 · VRN 自己的入口|轉交前版 VRN_SystemManager_v0268", help_out),
        [ln for ln in help_out.splitlines() if "v0269" in ln or "v0268" in ln][:3])
    miss = base.help_coverage(help_out, table)
    chk("③ 每個動詞仍列得到(help 涵蓋 = v0286 的尺)", not miss, miss)
    chk("④ 標準動詞行 · rc 行 · v0278 synchronizer 段 · v0270 以後動詞表都還在",
        "  標準動詞:help · version" in help_out and "  rc:0 綠" in help_out and "v0278 synchronizer" in help_out and "v0270 以後加的動詞" in help_out)
    fake = "VRN_SystemManager v0269 · VRN 自己的入口(x)\n  標準動詞(本版):help · a\n  其餘動詞:原樣轉交前版 VRN_SystemManager_v0268.py;y\n  rc:0\n  ── z\n  標準動詞(本版):留\n"
    chk("⑤ 只改第一個「──」段之前;段後一行不動", clean_native_help(fake) ==
        "  標準動詞:help · a\n  舊動詞:鏈底原生處理器原樣轉交更舊的版(子行程);標準動詞加 --legacy 看前版原樣輸出\n  rc:0\n  ── z\n  標準動詞(本版):留\n")
    with tempfile.TemporaryDirectory(prefix="via_vrn288_") as td:
        keep = os.environ.get("VIA_VRN_SCAN_CACHE")
        os.environ["VIA_VRN_SCAN_CACHE"] = str(Path(td) / "cache.json")
        try:
            rvj, vj = _capture(cmd_version, ["--json"])
            rhj, hj = _capture(cmd_health, ["--json"])
            rv, vout = _capture(cmd_version, [])
        finally:
            if keep is None:
                os.environ.pop("VIA_VRN_SCAN_CACHE", None)
            else:
                os.environ["VIA_VRN_SCAN_CACHE"] = keep
    try:
        vjd, hjd = json.loads(vj), json.loads(hj)
    except ValueError:
        vjd, hjd = {}, {}
    chk("⑥ version --json:合法 JSON · live_tail = v0288 · 鏈完整且從本版算起",
        rvj == 0 and vjd.get("live_tail", {}).get("version") == "v0288" and vjd.get("chain", {}).get("complete") is True
        and (vjd.get("chain", {}).get("versions") or [None])[0] == "v0288", vj[:200])
    chk("⑦ version 文字:第一行標本版 v0288", rv == 0 and vout.startswith("[%s] VRN · 現役尾版 VRN_SystemManager_v0288.py" % TAG), vout[:200])
    chk("⑧ health --json:合法 JSON · 真樹綠 · 鏈完整 · help 不漏",
        rhj == 0 and hjd.get("lamp") == "GREEN" and hjd.get("chain", {}).get("complete") is True and hjd.get("help_missing") == []
        and hjd.get("live_tail", {}).get("version") == "v0288", {k: hjd.get(k) for k in ("lamp", "red", "yellow")})
    got = {r["verb"]: r["top"] for r in table}
    chk("⑨ verbs:help / version / health / verbs 最新處理版 = v0288", all(got.get(v) == "v0288" for v in ("help", "version", "health", "verbs")), got)
    chk("⑩ 呼叫完 v0287 的名字都還原(TAG · 鏈頭)", PRIOR.TAG == "VRN_SystemManager v0287" and PRIOR.chain_modules is _PRIOR_CHAIN
        and PRIOR.chain_modules()[0] is PRIOR)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    peer = [k for k in ("VIA_FROM_VCGC", "VIA_FROM_VDFSM") if re.search(r"environ(?:\[[\"']%s[\"']\]\s*=|\.setdefault\([\"']%s)" % (k, k), body)]
    chk("⑪ 系統獨立:不替別的系統設入口旗標 · 加速器橋在 · 不碰 TA-Lib · 不出網",
        not peer and "[VIA:ACCEL-BRIDGE:v0100]" in src and "talib" not in body.lower()
        and not re.search(r"^\s*(import|from)\s+(requests|urllib|socket|http)\b", src, re.M))
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑫ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), "%d 支" % len(pub))
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
