#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_VCGC_ApplyRun v0103 — 薄尾:新增 K 道「三系統收尾實測」(VCGC 功能實測 · VDF 實冊輸出 · VRN 冊式資料夾實冊輸出)

操作員 2026-11-20 17:16:「VCGC功能整理實測收尾  VDF實冊輸出收尾  VRN冊式資料夾 實冊輸出驗證無誤收尾」。
K 道只呼叫各系統「自己的」既有入口(VDF / VRN 走自己的管理器與引擎、不帶 VCGC 旗;L123 互不干涉),
VCGC 只讀它們自報的收據;不改 VDF / VRN 任何檔、不出網(擷取不在這一道)。
  K-VCGC-functions   主控台 functions(功能卡整理)
  K-VCGC-handoff     主控台 handoff check(交接閘)
  K-VCGC-test        主控台 test --quick(全功能串測)
  K-VCGC-omniroute   CGC_SystemManager omniroute(MCP 實跑握手)
  K-VDF-closeout     VDF 管理器 closeout(自己的收尾收據)
  K-VDF-universe     VDF_ENG090 universe(名單欄位齊不齊)
  K-VDF-revenue      VDF_ENG090 revenue(月營收涵蓋 · 缺哪幾個月)
  K-VDF-datascope    VDF_ENG240 run --start 2021-01-01(每張表起訖 · 起始日前 · 重複 · 名單外 · 未分類)
  K-VRN-closeout     VRN-2 管理器 closeout(自己的收尾收據)
  K-VRN-outbook      讀 VRN-2 自報的輸出冊收據 VIA_Reports/vrn2/VRN2_OutBook_latest.json(只讀):
                     有收據且 gaps 空 = 綠 · 有缺項 = 紅(列出缺哪份缺哪欄)· 沒有收據 = 黃(還沒在主機跑過 VRN-2)
收尾燈照 REQ240 第五柱:每格綠或灰而且主機實跑才算收尾成功;容器跑的一律標容器。其餘全部照 v0102 / v0101 / v0100。
用法:python VIA_VCGC_ApplyRun_v0103.py run --only K [--no-open] · outbook [--via <VIA 夾>] · --selftest
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
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VIA_VCGC_ApplyRun"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0103", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE                        # v0100:run() / main() / GROUPS 都在這一層
VERSION = "v0103"
TAG = "VIA_VCGC_ApplyRun " + VERSION
OUTBOOK = "VIA_Reports/vrn2/VRN2_OutBook_latest.json"


def __getattr__(name):
    return getattr(PRIOR, name)


def outbook(via: Path) -> tuple[int, str]:
    """只讀 VRN-2 自報的輸出冊收據;回 (rc, 一行)。rc:0 綠 · 2 黃(沒收據 / 讀不懂)· 1 紅(有缺項)。"""
    p = via / OUTBOOK
    if not p.is_file():
        return 2, "[K-VRN-outbook] 黃 · 沒有 %s(這台還沒跑過 VRN-2 驗收;主機跑 ActivateVRN-2 後再看)" % OUTBOOK
    try:
        b = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return 2, "[K-VRN-outbook] 黃 · 收據讀不懂:%s" % type(e).__name__
    done, gaps = b.get("complete") or [], b.get("gaps") or {}
    if isinstance(gaps, list):
        gaps = {str(i): g for i, g in enumerate(gaps)}
    if gaps:
        show = " · ".join("%s:%s" % (k, ",".join(map(str, v)) if isinstance(v, list) else v) for k, v in list(gaps.items())[:8])
        return 1, "[K-VRN-outbook] 紅 · 齊全 %d 份 · 缺項 %d 份 → %s" % (len(done), len(gaps), show[:600])
    if not done:
        return 2, "[K-VRN-outbook] 黃 · 收據在但 0 份齊全(沒有輸出)"
    return 0, "[K-VRN-outbook] 綠 · 輸出冊 %d 份全部齊全 · 缺項 0" % len(done)


def plan(via: Path, only: list[str]):
    g, notes = _PREV_PLAN(via, [x for x in only if x != "K"])
    if "K" in only:
        reg = via / "supportive modules" / "registry"
        V = BASE.tail(reg, "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py")
        SM = BASE.tail(reg, "CGC_SystemManager_v*.py")
        VD = BASE.tail(via / "functional modules/VDF", "VDF_SystemManager_v*.py")
        VR = BASE.tail(via / "functional modules/VRN", "VRN_SystemManager_v*.py")
        cov = BASE.tail(via / "functional modules/VDF/engine", "VDF_ENG090_DataCoverageGate_v*.py")
        scope = BASE.tail(via / "functional modules/VDF/engine", "VDF_ENG240_DataScopeMatrix_v*.py")
        k = [BASE.Step("K", "K-VCGC-functions", V, ["functions"], 300),
             BASE.Step("K", "K-VCGC-handoff", V, ["handoff", "check"], 900),
             BASE.Step("K", "K-VCGC-test", V, ["test", "--quick"], 1800),
             BASE.Step("K", "K-VCGC-omniroute", SM, ["omniroute"], 300),
             BASE.Step("K", "K-VDF-closeout", VD, ["closeout"], 1200, own=True),
             BASE.Step("K", "K-VDF-universe", cov, ["universe"], 600, own=True),
             BASE.Step("K", "K-VDF-revenue", cov, ["revenue"], 600, own=True),
             BASE.Step("K", "K-VDF-datascope", scope, ["run", "--start", "2021-01-01", "--no-html"], 1800, own=True),
             BASE.Step("K", "K-VRN-closeout", VR, ["closeout"], 1200, own=True),
             BASE.Step("K", "K-VRN-outbook", Path(__file__).resolve(), ["outbook", "--via", str(via)], 60, own=True)]
        g["K"] = k
        notes.append("[K] 收尾燈照 REQ240 第五柱:綠或灰 + 主機實跑才算收尾成功;VDF 2021-01-01 起的實冊與 VRN 輸出冊只有主機有資料")
    return g, notes


def run_step(st, via, logdir, beat):
    """VDF_ENG090 這類引擎缺庫時印「… · ABSENT」再回 3(不是行首 [ABSENT]);照燈規則缺件 = 黃,不當真紅。"""
    st = _PREV_RUN_STEP(st, via, logdir, beat)
    if st.rc == 3 and st.lamp == "紅":
        try:
            text = (Path(logdir) / ("%s_%s.out" % (st.gid, st.name))).read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        if re.search(r"(^|[\s·\[])ABSENT\b", text):
            st.lamp = "黃"
            st.hits = (st.hits or []) + ["結束碼 3 且自報 ABSENT(缺件 / 沒有庫)→ 照規則算黃"]
    return st


_PREV_RUN_STEP = BASE.run_step
BASE.run_step = run_step
_PREV_PLAN = BASE.plan                   # = v0102 的 plan
BASE.plan = plan
if "K" not in BASE.GROUPS:
    BASE.GROUPS = tuple(BASE.GROUPS) + ("K",)
BASE.ZH.setdefault("K", "三系統收尾實測")
BASE.VERSION, BASE.TAG = VERSION, TAG


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:300]) if note and not cond else ""))

    print("=== %s 薄尾自測(前版鏈另跑)===" % TAG)
    with tempfile.TemporaryDirectory(prefix="ar103_") as td:
        via = Path(td)
        r0 = outbook(via)
        (via / "VIA_Reports/vrn2").mkdir(parents=True)
        p = via / OUTBOOK
        p.write_text(json.dumps({"complete": ["a.pdf", "b.pdf"], "gaps": {}}), encoding="utf-8")
        r1 = outbook(via)
        p.write_text(json.dumps({"complete": ["a.pdf"], "gaps": {"b.pdf": ["TARGET_PRICE", "EPS"]}}), encoding="utf-8")
        r2 = outbook(via)
        p.write_text("{壞", encoding="utf-8")
        r3 = outbook(via)
        chk("① 輸出冊收據:沒有 = 黃 · 全齊 = 綠 · 有缺項 = 紅並列出缺哪份缺哪欄 · 壞檔 = 黃(不丟例外)",
            r0[0] == 2 and r1[0] == 0 and r2[0] == 1 and "b.pdf:TARGET_PRICE,EPS" in r2[1] and r3[0] == 2, (r0, r1, r2, r3))
        lg = via / "logs"
        lg.mkdir()
        ent = via / "e.py"
        ent.write_text("print('[VDF_ENG090 v0106] universe · ABSENT')\nraise SystemExit(3)\n", encoding="utf-8")
        bad = via / "f.py"
        bad.write_text("raise SystemExit(3)\n", encoding="utf-8")
        s1 = run_step(BASE.Step("K", "a", ent, [], 30, own=True), via, lg, lambda *_: None)
        s2 = run_step(BASE.Step("K", "b", bad, [], 30, own=True), via, lg, lambda *_: None)
        chk("②b 結束碼 3 + 自報 ABSENT = 黃 · 結束碼 3 沒說原因 = 紅", s1.lamp == "黃" and s2.lamp == "紅", (s1.lamp, s2.lamp))
        for x in (ent, bad):
            x.unlink()
        for x in lg.iterdir():
            x.unlink()
        lg.rmdir()
        chk("② 讀收據零寫入(只讀 VRN-2 自報)", sorted(x.name for x in via.rglob("*") if x.is_file()) == ["VRN2_OutBook_latest.json"])
    via = BASE.find_via(HERE)
    if via is None:
        chk("③ 找不到 VIA 夾:跳過 = 黃", False)
    else:
        g, notes = BASE.plan(via, ["K"])
        kn = [s.name for s in g.get("K", [])]
        own = {s.name for s in g.get("K", []) if s.own}
        chk("③ K 道十步 · VDF / VRN 一律走自己的入口(不帶 VCGC 旗)· VCGC 四步帶旗 · --only K 認得",
            len(kn) == 10 and own == {n for n in kn if not n.startswith("K-VCGC")} and "K" in BASE.GROUPS and "K" in BASE.ZH and list(g) == ["K"], kn)
        miss = [s.name for s in g["K"] if s.entry is None or not Path(s.entry).is_file()]
        chk("④ K 道每一步的入口檔都在這棵樹上", not miss, miss)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 加速器橋在 · 不碰 TA-Lib · 不寫同意閘 · 沒有色碼", "[VIA:ACCEL-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and "environ[\"VIA_NET" + "_CONSENT\"] =" not in src and not re.search(r"#[0-9a-fA-F]{6}\b", src))
    BASE.plan = _PREV_PLAN               # 前版自測核「計畫走它自己那一層」→ 換裝卸下再跑
    try:
        rc_prior = PRIOR.selftest()
    finally:
        BASE.plan = plan
    chk("⑥ 前版 %s 自測照過" % PRIOR_PATH.stem, rc_prior == 0, rc_prior)
    good = all(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if good else "FAIL", TAG, sum(ok), len(ok)))
    return 0 if good else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a == ["--selftest"]:
        return selftest()
    if a[:1] == ["outbook"]:
        via = Path(a[a.index("--via") + 1]) if "--via" in a and a.index("--via") + 1 < len(a) else BASE.find_via(HERE)
        if via is None:
            print("[K-VRN-outbook] 黃 · 找不到 VIA 夾")
            return 2
        rc, line = outbook(via)
        print(line)
        return rc
    return BASE.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
