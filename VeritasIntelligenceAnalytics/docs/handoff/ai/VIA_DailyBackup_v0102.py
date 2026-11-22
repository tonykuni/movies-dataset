#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_DailyBackup v0102 — 薄尾(v0101 以前一字不動):備份儲存 Graphify 與 OmniRoute

  操作員 2026-11-22:「備份儲存 GRAPHIY OMNIROUTE」。
  v0100 / v0101 只把 Graphify 收據當旁證(有 / 無),圖本身與 OmniRoute 設定都沒進備份;兩者都在 VIA_Reports(git 忽略),
  換機器 / 清夾就沒了。本版在既有每日備份上多兩個範圍(照舊:只讀來源 · 備份夾只增 · zip + SHA256SUMS + MANIFEST):
    GRAPHIFY   各系統自己的引擎關係圖 VIA_Reports/**/<SYS>_GRAPH_latest.json(VRN · VDF 管理器的 graphify 動詞產出)
               + 桌機 Graphify(graphifyy · 只解析程式碼 · 離線)的收據 VIA_Reports/graphify/VIA_Graphify_latest.json
               + 每個系統的 graphify-out/graph.json · GRAPH_REPORT.md(graph.html 是看圖頁、可由 graph.json 重生,不收)
    OMNIROUTE  各系統自己的 MCP 路由設定 VIA_Reports/**/<SYS>_OmniRoute_latest.json(VRN · VDF · VCGC 的 omniroute 動詞產出)
               (只是設定片段:指令路徑 · 工具清單;OmniRoute 程式本身與它家目錄的設定 / 金鑰不碰、不收)
  單檔上限從 40 MB 提到 256 MB(Graphify 的 graph.json 大;VIA_BACKUP_MAX_MB 可改);超過照舊列 too_large,不默默丟。
  本版不跑 graphify / omniroute(各系統自己的入口跑:VRN / VDF 管理器 graphify · omniroute,VCGC CGC_SystemManager omniroute,
  桌機 Graphify 照 via_graphify_v0101 的開機行);只把已產出的檔備起來。不出網 · 不起子行程。
用法同 v0100:python VIA_DailyBackup_v0102.py backup | check | --selftest
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
import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path

VERSION = "v0102"
HERE = Path(__file__).resolve().parent
FAMILY = "VIA_DailyBackup"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0102", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.PRIOR                                    # v0100:SCOPE · MAX_FILE_BYTES · do_backup 在這一版的模組全域
ENGINE = "VIA_DailyBackup " + VERSION
_BASE_SCOPE, _BASE_MAX, _BASE_ENGINE = dict(BASE.SCOPE), BASE.MAX_FILE_BYTES, BASE.ENGINE

EXTRA_SCOPE = {
    "GRAPHIFY": {"tail": ["VIA_Reports/graphify/VIA_Graphify_latest.json"],
                 "all": ["VIA_Reports/**/*_GRAPH_latest.json",
                         "VIA_Reports/graphify/*/graphify-out/graph.json",
                         "VIA_Reports/graphify/*/graphify-out/GRAPH_REPORT.md"]},
    "OMNIROUTE": {"all": ["VIA_Reports/**/*_OmniRoute_latest.json"]},
}


def max_bytes() -> int:
    try:
        mb = float(os.environ.get("VIA_BACKUP_MAX_MB") or 256)
    except ValueError:
        mb = 256.0
    return max(_BASE_MAX, int(mb * 1024 * 1024))


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def install():
    PRIOR.install()                                    # v0101:check 不對「沒有可驗證的檔」亮綠
    BASE.SCOPE = {**_BASE_SCOPE, **EXTRA_SCOPE}         # v0100 do_backup 讀模組全域 SCOPE → 多兩個範圍
    BASE.MAX_FILE_BYTES = max_bytes()
    BASE.ENGINE = ENGINE


def selftest() -> int:
    import tempfile
    BASE.SCOPE, BASE.MAX_FILE_BYTES, BASE.ENGINE = dict(_BASE_SCOPE), _BASE_MAX, _BASE_ENGINE   # 前版自測照前版的範圍跑
    rc = PRIOR.selftest()
    install()
    ok = []

    def chk(n, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", n, (" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    with tempfile.TemporaryDirectory(prefix="via_bk102_") as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        rep = via / "VIA_Reports"
        files = {
            "vrn2/manager/graph/VRN_GRAPH_latest.json": '{"system":"VRN","nodes":["a"]}',
            "vdf/manager/graph/VDF_GRAPH_latest.json": '{"system":"VDF","nodes":["b"]}',
            "graphify/VIA_Graphify_latest.json": '{"tool":"VIA_Graphify","version":"v0101"}',
            "graphify/VRN/graphify-out/graph.json": '{"nodes":[1,2,3]}',
            "graphify/VRN/graphify-out/GRAPH_REPORT.md": "# report\n",
            "graphify/VRN/graphify-out/graph.html": "<html></html>",
            "vrn2/manager/omniroute/VRN_OmniRoute_latest.json": '{"system":"VRN","routes":{}}',
            "vdf/manager/omniroute/VDF_OmniRoute_latest.json": '{"system":"VDF","routes":{}}',
            "vcgc/omniroute/VCGC_OmniRoute_latest.json": '{"system":"VCGC","routes":{}}',
        }
        for rel, text in files.items():
            p = rep / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        pol = via / "supportive modules" / "registry" / "VIA_Policy_Laws_SSOT_v0100.json"
        pol.parent.mkdir(parents=True)
        pol.write_text("{}", encoding="utf-8")
        out, md = via / BASE.BACKUP_ROOT_REL, via / BASE.MANIFEST_DIR_REL
        man = BASE.do_backup(via, out, md)
        sysm = man.get("systems", {})
        g = [e["path"] for e in sysm.get("GRAPHIFY", {}).get("files", []) if "sha256" in e]
        o = [e["path"] for e in sysm.get("OMNIROUTE", {}).get("files", []) if "sha256" in e]
        chk("① GRAPHIFY 範圍:兩系統的 *_GRAPH_latest · 桌機 Graphify 收據 · graph.json · GRAPH_REPORT.md 都進備份(graph.html 不收)",
            len(g) == 5 and not any(x.endswith("graph.html") for x in g) and any(x.endswith("VIA_Graphify_latest.json") for x in g), g)
        chk("② OMNIROUTE 範圍:VRN · VDF · VCGC 三份路由設定都進備份", len(o) == 3 and all(any(s in x for x in o) for s in ("VRN_", "VDF_", "VCGC_")), o)
        zips = sorted(out.rglob("GRAPHIFY.zip"))
        import zipfile
        with zipfile.ZipFile(zips[-1]) as z:
            sums = z.read("SHA256SUMS.txt").decode("utf-8") if "SHA256SUMS.txt" in z.namelist() else ""
            names = z.namelist()
        chk("③ zip 真的有檔(不是只有清單)", any(n.endswith("graph.json") for n in names), names[:6])
        chk("④ 原本的系統範圍照收(前版的冊沒少)", set(_BASE_SCOPE) <= set(sysm), sorted(sysm))
        res = BASE.do_check(via, out, md)
        chk("⑤ 剛備完 check 不紅(各檔 sha 對得上)", res.get("lamp") in ("GREEN", "YELLOW"), res.get("meaning", "")[:160])
        (rep / "vrn2/manager/omniroute/VRN_OmniRoute_latest.json").write_text('{"system":"VRN","routes":{"x":1}}', encoding="utf-8")
        res2 = BASE.do_check(via, out, md)
        chk("⑥ 路由設定變了 → check 不再綠並點名", res2.get("lamp") != "GREEN" and "VRN_OmniRoute_latest.json" in json.dumps(res2, ensure_ascii=False), res2.get("meaning", "")[:160])
        keep = os.environ.get("VIA_BACKUP_MAX_MB")
        os.environ["VIA_BACKUP_MAX_MB"] = "0.00001"
        try:
            install()
            big = rep / "graphify/VDF/graphify-out/graph.json"
            big.parent.mkdir(parents=True, exist_ok=True)
            big.write_text("x" * (_BASE_MAX + 10), encoding="utf-8")
            time.sleep(1.1)                                                # 備份夾以秒為名
            man2 = BASE.do_backup(via, out, md)
        finally:
            if keep is None:
                os.environ.pop("VIA_BACKUP_MAX_MB", None)
            else:
                os.environ["VIA_BACKUP_MAX_MB"] = keep
            install()
        tl = [e for e in man2["systems"]["GRAPHIFY"]["files"] if e.get("skipped") == "too_large"]
        chk("⑦ 超過上限照舊列 too_large(不默默丟)· 上限不低於前版 40 MB", len(tl) == 1 and "VDF" in tl[0]["path"], tl)
    chk("⑧ 預設上限 256 MB · VIA_BACKUP_MAX_MB 可改", max_bytes() == 256 * 1024 * 1024 or os.environ.get("VIA_BACKUP_MAX_MB"))
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑨ 加速器橋在 · 不出網 · 不起子行程 · 不碰 TA-Lib", "[VIA:ACCEL-BRIDGE:v0100]" in src and "subprocess" not in body
        and not re.search(r"^\s*(import|from)\s+(requests|urllib|socket|http)\b", src, re.M) and "talib" not in body.lower())
    bad = len(ok) - sum(ok)
    print("[%s] VIA_DailyBackup %s --selftest · 本版 %d 項 · 不過 %d(v0101 rc %d)" % ("PASS" if not bad and rc == 0 else "FAIL", VERSION, len(ok), bad, rc), flush=True)
    return 0 if not bad and rc == 0 else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv or argv[:1] == ["selftest"]:
        return selftest()
    install()
    return BASE.main(argv)


if __name__ == "__main__":
    sys.exit(main())
