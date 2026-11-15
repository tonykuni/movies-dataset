#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL014_WorkstationSync v0103 — 薄尾:VDF 資料接點不論 git 怎麼報都不算工作樹髒 · v0101 自測的平台前提照實改判

工作站實跑(2026-11-15 11:33 · 操作員 PowerShell):v0102 自測 6/7 —— ⑦「前版 v0101 自測 rc 0」FAIL;v0101 10/11 —— ⑤ FAIL。
v0101-⑤ 同時要兩件事:(a) v0101 的量法看工作樹是乾淨的;(b) v0100 的舊量法「會把接點算成髒」。
(b) 是平台前提:Linux 的 git 把符號連結當檔案 → .gitignore 的 `output_hub/`(結尾斜線只擋資料夾)擋不到 → 舊量法算髒;
Windows 的 git 若把目錄接點當資料夾 → `output_hub/` 擋得到 → 舊量法本來就不算髒 → (b) 不成立 → ⑤ FAIL,
但同步本身沒有錯(工作樹確實乾淨)。v0102-⑦ 只是轉述 v0101 的結果。
本版(v0100 / v0101 / v0102 一字不動):
  ① 濾接點的行更寬:接點本身(有無結尾斜線 · 有無引號 · 反斜線)與接點底下的檔都不算髒
     —— 不論 git 把接點當檔、當資料夾、還是走進去列檔(換在 v0101 模組的 _not_link_lines;v0101 survey 與 v0102 _dirty_now 都經它)。
  ② 自測當場量本機 git 怎麼報接點:暫存倉 + 用 v0101 的 make_link 真接一個 + 同樣的 .gitignore 寫法,
     印出 git status 原文與判定「列出(Linux 樣)」或「藏起(被 .gitignore 擋掉)」。
  ③ 前版鏈:rc 0 → 過;rc ≠ 0 且 FAIL 只有 v0101-⑤ / v0102-⑦,而本機量到「藏起」→ 判平台前提不成立,照實寫明、本項算過;
     其他任何 FAIL → 照實 FAIL。
用法同 v0102(工作站 PowerShell 或 cmd,站在 VDF 工作樹裡):
  python "VeritasIntelligenceAnalytics\\functional modules\\VDF\\VDF_MDL014_WorkstationSync_v0103.py" --apply
VDF 自己的模組:不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib;不裝套件、不寫環境變數;git 走本機憑證;從不 force、從不推 main。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====


import contextlib
import importlib.util
import io
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent                     # …/functional modules/VDF
_STEM = "VDF_MDL014_WorkstationSync"
TAG = "%s v%s" % (_STEM, Path(__file__).stem.rsplit("_v", 1)[-1])


def _vnum_v0103(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0103(p) < _vnum_v0103(__file__)), key=_vnum_v0103)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0101 = PRIOR.PRIOR                                        # _not_link_lines · make_link · DATA_LINKS_V0101 · survey 在它身上
V0100 = PRIOR.V0100                                        # 本體:git · VIA_DIR
git = V0100.git
_NOT_LINK_V0101 = V0101._not_link_lines
_NEXT_CMD_V0102 = V0101._next_cmd                          # v0102 換上去的那支(印 v0102 檔名)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _status_path(ln: str) -> str:
    """porcelain 一行 → 路徑(去狀態欄 · 改名取新名 · 去引號 · 反斜線轉正 · 去結尾斜線)。"""
    p = ln[3:] if len(ln) > 3 and ln[2] == " " else (ln.split(None, 1)[-1] if ln.strip() else "")
    if " -> " in p:
        p = p.split(" -> ", 1)[1]
    return p.strip().strip('"').replace("\\", "/").rstrip("/")


def link_paths() -> set:
    return {(V0100.VIA_DIR + "/" + rel).replace("\\", "/").rstrip("/") for rel in V0101.DATA_LINKS_V0101}


def not_link_lines(lines: list, links=None) -> list:
    """去掉接點本身與接點底下的行(不論 git 把接點當檔、當資料夾、還是走進去列檔)。"""
    links = link_paths() if links is None else links
    return [ln for ln in lines if not any(_status_path(ln) == lk or _status_path(ln).startswith(lk + "/") for lk in links)]


def _next_cmd(a) -> str:
    """預演印的 NEXT 指向本版(PR 649 Codex P2:照 v0102 的 NEXT 跑 --apply 會起一支沒有本版濾法的新行程)。"""
    return _NEXT_CMD_V0102(a).replace(PRIOR_PATH.name, Path(__file__).name, 1)


def _install_v0103():
    V0101._not_link_lines = not_link_lines
    V0101._next_cmd = _next_cmd


def _uninstall_v0103():
    V0101._not_link_lines = _NOT_LINK_V0101
    V0101._next_cmd = _NEXT_CMD_V0102


_install_v0103()


def probe_link_style() -> dict:
    """暫存倉 + 真接點(v0101 make_link,本機平台)+ `x/output_hub/` 的 .gitignore → git 怎麼報這個接點。"""
    td = Path(tempfile.mkdtemp(prefix="vdf_mdl014c_"))
    try:
        repo, src = td / "repo", td / "real_hub"
        repo.mkdir()
        src.mkdir()
        (src / "probe.txt").write_text("真資料", encoding="utf-8")
        git(["init", "-q"], repo)
        (repo / ".gitignore").write_text("x/output_hub/\n", encoding="utf-8")
        (repo / "x").mkdir()
        made = V0101.make_link(repo / "x" / "output_hub", src, True)
        lines = [ln for ln in git(["status", "--porcelain", "--untracked-files=all"], repo).splitlines() if ln.strip()]
        listed = [ln for ln in lines if _status_path(ln) == "x/output_hub" or _status_path(ln).startswith("x/output_hub/")]
        left = [ln for ln in not_link_lines(lines, {"x/output_hub"}) if _status_path(ln).startswith("x/")]
        return {"made": made, "lines": lines, "style": "listed" if listed else "hidden", "clean": not left, "err": ""}
    except Exception as exc:                                # 量不到 = 照實說(本項 FAIL),不冒充
        return {"made": "", "lines": [], "style": "unknown", "clean": False, "err": "%s: %s" % (type(exc).__name__, str(exc)[:200])}
    finally:
        shutil.rmtree(td, ignore_errors=True)


def premise_only(prc: int, fails: list, style: str, clean: bool) -> bool:
    """前版鏈 rc ≠ 0 時:FAIL 只有 v0101-⑤(與轉述它的 v0102-⑦)且本機 git 把接點藏起、本版量法乾淨 → 只差平台前提。"""
    return (prc != 0 and bool(fails) and any("v0101-⑤" in x for x in fails)
            and all(("v0101-⑤" in x) or ("v0102-⑦" in x) for x in fails) and style == "hidden" and clean)


class _Tee(io.StringIO):
    def __init__(self, out):
        super().__init__()
        self._out = out

    def write(self, s):
        self._out.write(s)
        return super().write(s)

    def flush(self):
        self._out.flush()


def selftest() -> int:
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name, flush=True)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""), flush=True)

    print("=== %s · 薄尾自測(接點不算髒 · 本機 git 怎麼報接點 · 前版鏈)===" % TAG, flush=True)
    hub, fetch = sorted(link_paths())[0], sorted(link_paths())[-1]
    lines = ["?? " + hub, "?? " + hub + "/", '?? "' + hub + '/probe.txt"', "?? " + fetch.replace("/", "\\") + "\\x.json",
             " M " + V0100.VIA_DIR + "/functional modules/VDF/other.py", "?? " + hub + "_old/x.txt"]
    kept = not_link_lines(lines)
    chk("① 接點本身 / 結尾斜線 / 引號 / 反斜線 / 接點底下的檔都濾掉;別的髒檔與名字只是開頭相同的夾照算",
        kept == [lines[4], lines[5]], kept)
    pr = probe_link_style()
    print("    本機 git 報接點:%s · 接點 %s · status 原文 %s%s" % (
        {"listed": "列出(像 Linux 的符號連結)", "hidden": "藏起(被 .gitignore 的 output_hub/ 擋掉)"}.get(pr["style"], "量不到"),
        pr["made"][:40], pr["lines"][:6], (" · " + pr["err"]) if pr["err"] else ""), flush=True)
    chk("② 本機真接一個接點:接得上 · git 不論怎麼報,本版量法都乾淨", pr["style"] in ("listed", "hidden") and pr["clean"] and "已接上" in pr["made"], pr)
    chk("③ 換裝在位:v0101 的 _not_link_lines = 本版(v0101 survey 與 v0102 _dirty_now 都經它)",
        V0101._not_link_lines is not_link_lines and PRIOR._not_link_lines is not_link_lines)
    import argparse
    ns = argparse.Namespace(case=["vdf_case", "x y"], repo=None, worktree=None, remote="origin", no_link_data=True)
    nxt = V0101._next_cmd(ns)
    chk("⑦ 預演的 NEXT 指向本版(%s)· 參數照 v0101 重組只多 --apply · run 的標籤是本版" % Path(__file__).name,
        Path(__file__).name in nxt and PRIOR_PATH.name not in nxt and nxt.endswith(" --apply") and '--case "x y"' in nxt
        and "--no-link-data" in nxt and V0101._next_cmd is _next_cmd and run.__module__ == __name__, nxt)
    src = Path(__file__).read_text(encoding="utf-8")
    head = src.split("def " + "selftest", 1)[0]
    imports = re.findall(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", src, re.M)
    chk("④ 三橋在 · 不匯入他系統程式 · 不碰 TA-Lib · 同意閘不寫 · 不寫環境變數",
        all(t in src for t in ("[VIA:ACCEL-BRIDGE:v0100]", "[VIA:NET-BRIDGE:v0100]", "[VIA:LIB-BRIDGE:v0100]"))
        and not [x for x in imports if x.startswith(("CGC_", "VRN_", "VRN2_", "VCGC"))]
        and not re.search(r"^\s*(import|from)\s+" + "talib", src, re.M)
        and not re.search(r"\[[\"']VIA_(NET|SCRAPE)_" + r"CONSENT[\"']\]\s*=(?!=)", src)
        and not re.search(r"os\.environ\[[^\]]+\]\s*=(?!=)|os\.environ\.(update|pop|setdefault)\(|" + "put" + "env", head))
    print("  ── 前版鏈自測(VIA_SKIP_PRIOR_SELFTEST=1 略過)──", flush=True)
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1":
        prc, fails = 0, []
    else:
        tee = _Tee(sys.stdout)
        _uninstall_v0103()                                  # 前版自測看它自己的
        try:
            with contextlib.redirect_stdout(tee):
                prc = PRIOR.selftest()
        finally:
            _install_v0103()
        fails = [ln.strip() for ln in tee.getvalue().splitlines() if "[FAIL]" in ln]
    if prc == 0:
        chk("⑤ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, True)
    else:
        chk("⑤ 前版鏈 rc %s:只差 v0101-⑤ 的平台前提(本機 git 把接點藏起 → v0100 舊量法本來就不算髒),同步行為無誤 → 改判通過" % prc,
            premise_only(prc, fails, pr["style"], pr["clean"]), {"style": pr["style"], "fails": fails[:4]})
    w5, w7, other = "[FAIL] v0101-⑤ 接點不算工作樹髒 …", "[FAIL] v0102-⑦ 前版 … rc 0", "[FAIL] v0101-③ 執行 …"
    chk("⑥ 改判只認平台前提:Windows 樣(藏起 + 只差 ⑤/⑦)→ 過;另有別的 FAIL · 本機是列出 · 量法不乾淨 · 沒有 FAIL 行 → 都不過",
        premise_only(1, [w5, w7], "hidden", True) and not premise_only(1, [w5, w7, other], "hidden", True)
        and not premise_only(1, [w5, w7], "listed", True) and not premise_only(1, [w5, w7], "hidden", False)
        and not premise_only(1, [], "hidden", True) and not premise_only(1, [w7], "hidden", True) and not premise_only(0, [w5], "hidden", True))
    print("  [計] %s 薄尾 %d/%d · %s" % (TAG, p, p + f, "PASS" if not f else "FAIL"), flush=True)
    return 0 if not f else 1


def run(argv=None, here: Path = HERE) -> int:
    """v0102 的流程(收據 · 停得乾淨照舊),標籤換本版。"""
    keep = PRIOR.TAG
    PRIOR.TAG = TAG
    try:
        return PRIOR.run(argv, here)
    finally:
        PRIOR.TAG = keep


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    return run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
