# -*- coding: utf-8 -*-
# WorkOps EnvManager 橋 v0100(ENG-020)— 讓平台中央環境治理核心管到 WorkOps 的 .venv_pm
#
# 背景(操作員 2026/08/08 指示):「用 VIA_EnvManager.py 來試試能否成功安裝」。
#   實測:EnvManager 的環境根目錄候選寫死於 C:\Users\tonyk\envs 等四處,看不到
#   engines\.venv_pm,plan-install 必回 NO_HEALTHY_MANAGED_ENV_AVAILABLE。
# 本橋作法(正本不就地修改):動態尋找 supportive modules\VIA_EnvManager.py,
#   importlib 載入後「執行期」覆蓋其模組層參數 —
#   1) 環境根目錄 → .venv_pm 的上層(engines\),使 gatekeeper 能發現並健檢該 venv
#   2) 全部輸出檔 → WorkOps\out\envmanager\(決策/健康/SSOT/歷史 JSON 落 WorkOps 屬地)
#   3) def_path_to_python → 跨平台(Windows Scripts\python.exe / POSIX bin/python),
#      使容器 QA 與操作員機同一條路
#   4) 核心庫快照縮至 WorkOps 相關(pip/numpy/pandas)— 避免 26 支探針拖慢 setup
# 之後走 EnvManager 原生機制:def_plan_install_request(決策)→ 取其 pip 版
#   executable_commands(install + pip check)執行;--wheels-only 時在 install 後
#   注入 --only-binary=:all:(維持 WorkOps 輪限守則;EnvManager 命令產生器不支援
#   額外 pip 參數,故由橋注入,不改正本)。
# 誠實:決策與逐命令結果全印;blocked=exit 2、執行失敗=exit 1、成功=exit 0。
import argparse, importlib.util, json, os, sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent          # engines/


def find_envmanager():
    """由 engines/ 向上找 supportive modules/VIA_EnvManager.py(動態,不寫死絕對路徑)。"""
    probe = HERE
    while probe.parent != probe:
        cand = probe / "supportive modules" / "VIA_EnvManager.py"
        if cand.is_file():
            return cand
        probe = probe.parent
    return None


def load_envmanager(em_path, venv_dir, outdir):
    spec = importlib.util.spec_from_file_location("VIA_EnvManager_workops", str(em_path))
    em = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = em   # dataclass 需在 sys.modules 找得到宿主模組
    spec.loader.exec_module(em)

    # (1) 治理範圍 → venv 上層(engines\),gatekeeper 據此發現 .venv_pm
    em.def_PARAM_ENV_ROOT_CANDIDATES = [venv_dir.parent]
    # (2) 輸出全落 WorkOps 屬地
    outdir.mkdir(parents=True, exist_ok=True)
    em.def_PARAM_OUTPUT_DIR = outdir
    for name in ("SSOT_JSON", "HISTORY_JSONL", "HEALTH_JSON", "HTML_REPORT",
                 "COMMAND_PLAN_JSON", "INSTALL_REQUEST_JSON", "INSTALL_PLAN_JSON",
                 "INSTALL_DECISION_JSON", "CONFLICT_JSON"):
        attr = "def_PARAM_" + name
        old = getattr(em, attr)
        setattr(em, attr, outdir / Path(str(old)).name)
    # (3) 跨平台 python 定位(Windows / POSIX 皆可健檢與執行)
    def _path_to_python(env_path):
        for cand in (env_path / "Scripts" / "python.exe", env_path / "bin" / "python"):
            if cand.exists():
                return cand
        return env_path / "Scripts" / "python.exe"
    em.def_path_to_python = _path_to_python
    # (4) 快照縮至 WorkOps 相關,健檢不拖速
    em.def_PARAM_SNAPSHOT_LIBS = ["pip", "numpy", "pandas"]
    return em


def cmd_health(em, venv_dir):
    result = em.def_scan_all_envs()
    rows = em.def_read_json_safe(em.def_PARAM_HEALTH_JSON, {}).get("envs", [])
    mine = next((r for r in rows if r.get("env_name") == venv_dir.name), None)
    print(json.dumps({
        "ok": bool(mine),
        "venv": str(venv_dir),
        "status": (mine or {}).get("status", "NOT_FOUND"),
        "package_count": (mine or {}).get("package_count", 0),
        "pip_check_ok": (mine or {}).get("pip_check_ok"),
        "summary": result.get("summary"),
        "health_json": result.get("health_json"),
    }, ensure_ascii=False, indent=2))
    return 0 if mine else 2


def cmd_plan(em, venv_dir, package, version):
    payload = em.def_plan_install_request(package, requested_version=version,
                                          reason="workops pmsetup", preferred_env=venv_dir.name)
    d = payload.get("decision", {})
    print(json.dumps({
        "package": package + version,
        "approved": d.get("approved"),
        "blocked_reason": d.get("blocked_reason", ""),
        "risk_level": d.get("risk_level"),
        "target_env": d.get("target_env"),
        "target_python": d.get("target_python"),
        "decision_json": str(em.def_PARAM_INSTALL_DECISION_JSON),
    }, ensure_ascii=False, indent=2))
    return 0 if d.get("approved") else 2


def cmd_install(em, venv_dir, package, version, wheels_only):
    payload = em.def_plan_install_request(package, requested_version=version,
                                          reason="workops pmsetup", preferred_env=venv_dir.name)
    d = payload.get("decision", {})
    if not d.get("approved"):
        print(json.dumps({"package": package + version, "approved": False,
                          "blocked_reason": d.get("blocked_reason", "")}, ensure_ascii=False))
        return 2
    # EnvManager 產生之 pip 版命令(install + pip check);--wheels-only 由橋注入
    cmds = [c for c in d.get("executable_commands", [])
            if len(c) >= 3 and c[1:3] == ["-m", "pip"]][-2:]
    if wheels_only:
        cmds = [(c[:4] + ["--only-binary=:all:"] + c[4:]) if "install" in c else c for c in cmds]
    results = []
    for c in cmds:
        r = em.def_run_subprocess(c, timeout=1800)
        results.append({"command": c, "ok": r.get("ok"), "returncode": r.get("returncode"),
                        "stderr_tail": (r.get("stderr") or "")[-400:]})
        if not r.get("ok"):
            break
    all_ok = bool(results) and all(r["ok"] for r in results) and len(results) == len(cmds)
    payload["executed"] = True
    payload["execution_results"] = results
    em.def_write_json(em.def_PARAM_INSTALL_DECISION_JSON, payload)
    print(json.dumps({"package": package + version, "approved": True, "installed": all_ok,
                      "strategy": d.get("strategy"), "target_env": d.get("target_env"),
                      "wheels_only": wheels_only, "steps": results,
                      "decision_json": str(em.def_PARAM_INSTALL_DECISION_JSON)},
                     ensure_ascii=False, indent=2))
    return 0 if all_ok else 1


def main():
    ap = argparse.ArgumentParser(description="WorkOps × VIA_EnvManager 橋:讓中央環境治理管到 .venv_pm")
    ap.add_argument("command", choices=["health", "plan", "install"])
    ap.add_argument("package", nargs="?", default="")
    ap.add_argument("version", nargs="?", default="", help="版本尾綴,如 <3 或 ==2.7.23.3")
    ap.add_argument("--venv", default=str(HERE / ".venv_pm"), help="目標 venv(預設 engines/.venv_pm)")
    ap.add_argument("--outdir", default="", help="EnvManager 輸出落點(預設 WorkOps/out/envmanager)")
    ap.add_argument("--wheels-only", action="store_true", help="install 時注入 --only-binary=:all:")
    a = ap.parse_args()

    venv_dir = Path(a.venv).resolve()
    outdir = Path(a.outdir).resolve() if a.outdir else (HERE.parent / "out" / "envmanager")
    em_path = find_envmanager()
    if em_path is None:
        print(json.dumps({"ok": False, "error": "VIA_EnvManager.py 未找到(supportive modules)"}, ensure_ascii=False))
        return 3
    if not venv_dir.is_dir():
        print(json.dumps({"ok": False, "error": "venv 不存在:%s(先跑 pmsetup 建立)" % venv_dir}, ensure_ascii=False))
        return 3
    em = load_envmanager(em_path, venv_dir, outdir)
    print("[橋] EnvManager=%s · 治理範圍=%s · 輸出=%s" % (em_path, venv_dir, outdir))
    if a.command == "health":
        return cmd_health(em, venv_dir)
    if a.command == "plan":
        if not a.package:
            print(json.dumps({"ok": False, "error": "plan 需要套件名"}, ensure_ascii=False)); return 3
        return cmd_plan(em, venv_dir, a.package, a.version)
    if not a.package:
        print(json.dumps({"ok": False, "error": "install 需要套件名"}, ensure_ascii=False)); return 3
    return cmd_install(em, venv_dir, a.package, a.version, a.wheels_only)


if __name__ == "__main__":
    sys.exit(main())
