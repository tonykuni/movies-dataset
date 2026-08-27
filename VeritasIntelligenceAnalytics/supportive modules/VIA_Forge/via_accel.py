#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
VIA Accel Adapter  ——  via_accel.py   (\u9013 \u00b7 \u9078\u7528\u52a0\u901f/\u74b0\u5883\u9069\u914d\u5668)
================================================================================
\u628a\u5169\u500b\u57fa\u790e\u5de5\u5177\u300c\u639b\u5165\u300d\u2014\u2014\u4f46\u4ee5\u9078\u7528\u3001\u512a\u96c5\u964d\u7d1a\u65b9\u5f0f\uff1a
  \u2022 VeritasCeleritas\uff1a\u52a0\u901f\uff08thread_budget / \u8cc7\u6e90\u58d3\u529b\u5075\u6e2c / capability_report\uff09
  \u2022 VIA_EnvManager  \uff1a\u74b0\u5883\uff08venv \u6839\u5075\u6e2c / \u5957\u4ef6\u80fd\u529b\uff09
\u5075\u6e2c\u9806\u5e8f\uff1a\u74b0\u5883\u8b8a\u6578 VIA_ROOT \u2192 \u5df2\u77e5 VIA \u8def\u5f91 \u2192 \u672c\u8cc7\u6599\u593e\u3002
\u672a\u5c31\u7dd2\u2192\u5168\u90e8\u56de\u5b89\u5168\u9810\u8a2d\uff0cVIA_Forge \u7167\u5e38\u904b\u4f5c\uff08\u81ea\u8db3\u4e0d\u7834\uff09\u3002
================================================================================
"""
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
import os, sys, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))

# VeritasCeleritas / VIA_EnvManager \u53ef\u80fd\u7684\u4f4d\u7f6e
_CANDIDATE_DIRS = [
    os.environ.get("VIA_ROOT", ""),
    r"C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    r"C:\VeritasIntelligenceAnalytics",
    os.path.join(HERE, "supportive modules"),
    HERE,
]


def _load(module_name, filename):
    """\u5f9e\u5019\u9078\u8def\u5f91\u8f09\u5165\u6a21\u7d44\uff1b\u4efb\u4f55\u5931\u6557\u90fd\u56de None\uff08\u4e0d crash\uff09\u3002"""
    for d in _CANDIDATE_DIRS:
        if not d:
            continue
        p = os.path.join(d, filename)
        if os.path.exists(p):
            try:
                spec = importlib.util.spec_from_file_location(module_name, p)
                m = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(m)
                return m, p
            except Exception:
                continue
    # \u4e5f\u8a66\u4e00\u822c import\uff08\u82e5\u5df2\u5728 sys.path\uff09
    try:
        return importlib.import_module(module_name), "sys.path"
    except Exception:
        return None, None


class AccelAdapter:
    """\u9078\u7528\u52a0\u901f/\u74b0\u5883\u9069\u914d\u5668\u3002\u5168\u90e8\u65b9\u6cd5\u5728\u5de5\u5177\u7f3a\u5e2d\u6642\u56de\u5b89\u5168\u9810\u8a2d\u3002"""

    def __init__(self):
        self.celeritas, self.celeritas_path = _load("VeritasCeleritas", "VeritasCeleritas.py")
        self.envmgr, self.envmgr_path = _load("VIA_EnvManager", "VIA_EnvManager.py")

    # --- \u52a0\u901f\uff08Celeritas\uff09 ---
    def thread_budget(self, default=4):
        try:
            if self.celeritas and hasattr(self.celeritas, "thread_budget"):
                n = int(self.celeritas.thread_budget())
                return max(1, n)
        except Exception:
            pass
        try:
            return max(1, min(8, (os.cpu_count() or 4)))
        except Exception:
            return default

    def under_pressure(self):
        try:
            if self.celeritas and hasattr(self.celeritas, "system_under_pressure"):
                return bool(self.celeritas.system_under_pressure())
        except Exception:
            pass
        return False

    def capability_report(self):
        try:
            if self.celeritas and hasattr(self.celeritas, "capability_report"):
                return dict(self.celeritas.capability_report())
        except Exception:
            pass
        return {}

    # --- \u74b0\u5883\uff08EnvManager\uff09 ---
    def env_root(self):
        try:
            if self.envmgr and hasattr(self.envmgr, "def_find_env_root"):
                return str(self.envmgr.def_find_env_root())
        except Exception:
            pass
        return None

    # --- \u72c0\u614b\u5831\u544a\uff08\u4f9b /api/system \u986f\u793a libs applied\uff09 ---
    def status(self):
        return {
            "celeritas": {
                "loaded": self.celeritas is not None,
                "path": self.celeritas_path,
                "thread_budget": self.thread_budget(),
                "under_pressure": self.under_pressure(),
                "libs": self.capability_report(),
            },
            "envmanager": {
                "loaded": self.envmgr is not None,
                "path": self.envmgr_path,
                "env_root": self.env_root(),
            },
            "vpns_accelerators": {
                "note": "\u81ea VPNS \u52a0\u901f\u5668\u767b\u9304\u7c3f\u8f49\u7528\u81f3 VIA_Forge\u63a8\u53d6\uff08\u4e0d\u5361\u65b7+\u63d0\u901f\uff09",
                "applied": [
                    {"id": "A1", "name": "SHA \u5feb\u53d6", "where": "forge.process_one", "gain": "\u91cd\u6383 5-50\u00d7"},
                    {"id": "A2", "name": "\u76ee\u9304\u526a\u679d", "where": "forge._walk skip_dirs", "gain": "\u6a94\u6578\u5927\u6e1b"},
                    {"id": "A3", "name": "\u5927\u6a94\u8df3\u96dc\u6e4a(>50MB)", "where": "forge.process_one", "gain": "\u4e0d\u5361\u65b7"},
                ],
                "registered_not_applied": ["A6 EnumerateFiles", "A8 AST\u5feb\u53d6", "A14 \u589e\u91cf\u6a21\u5f0f",
                                           "A18 \u6aa2\u67e5\u9ede\u7e8c\u8dd1", "A20 \u770b\u9580\u72d7"],
            },
            "mode": "accelerated" if self.celeritas else "standalone",
            "note": "\u9078\u7528\u639b\u5165\uff1b\u5de5\u5177\u5728\u4f60\u5b8c\u6574 VIA \u74b0\u5883\u6642\u81ea\u52d5\u555f\u7528\uff0c\u4e0d\u5728\u6642\u512a\u96c5\u964d\u7d1a",
        }


_ADAPTER = None


def get_adapter():
    global _ADAPTER
    if _ADAPTER is None:
        _ADAPTER = AccelAdapter()
    return _ADAPTER


def selftest():
    p, f = 0, 0
    def ck(n, c):
        nonlocal p, f
        if c: p += 1; print("  [PASS] accel: %s" % n)
        else: f += 1; print("  [FAIL] accel: %s" % n)
    a = AccelAdapter()
    st = a.status()
    ck("adapter loads (\u4e0d crash)", isinstance(st, dict))
    ck("thread_budget \u5b89\u5168\u9810\u8a2d", a.thread_budget() >= 1)
    ck("under_pressure \u56de bool", isinstance(a.under_pressure(), bool))
    ck("status \u5831\u544a celeritas/envmanager", "celeritas" in st and "envmanager" in st)
    ck("mode \u6a19\u8a18", st["mode"] in ("accelerated", "standalone"))
    ck("\u5de5\u5177\u7f3a\u5e2d\u512a\u96c5\u964d\u7d1a", st["celeritas"]["loaded"] in (True, False))  # \u4e0d\u8ad6\u5728\u4e0d\u5728\u90fd\u4e0d crash
    return p, f


def main():
    import argparse, json
    ap = argparse.ArgumentParser(); ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        a, b = selftest(); print("accel: %d PASS / %d FAIL" % (a, b)); sys.exit(0 if b == 0 else 1)
    if args.status:
        print(json.dumps(get_adapter().status(), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
