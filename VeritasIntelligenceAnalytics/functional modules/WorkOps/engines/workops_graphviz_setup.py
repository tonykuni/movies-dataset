# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
# -*- coding: utf-8 -*-
# WorkOps Graphviz 可攜式取得器 v0100(ENG-021)— 免 winget / 免管理員 / user-scope
#
# 背景(操作員 2026/08/08 實機):winget 不存在,DFG 流程圖因缺 dot 而略過。
# 本工具依動態解析鐵律:查 Graphviz 官方 GitLab Releases API 取「最新版」
#   windows_10_cmake_Release_Graphviz-<ver>-win64.zip(嚴禁寫死版號)+ 其 .sha256,
#   下載 → sha256 逐位驗證 → 解壓至 engines\.graphviz\ → 定位 bin\dot.exe →
#   (Windows)dot -c 建外掛設定 + dot -V 實測版本。
# 治理:user-scope;不改系統 PATH、不碰登錄檔、無需管理員;.graphviz 不入版控
#   (.gitignore);engine_analytics 執行期自動偵測此處的 dot 並臨時接上 PATH。
# 誠實:逐步回報;下載與驗證失敗即停(不解壓未驗證之物);exit 0 成 / 1 敗。
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tempfile, urllib.request, zipfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent            # engines/
PORTABLE = HERE / ".graphviz"
API = "https://gitlab.com/api/v4/projects/4207231/releases?per_page=1"
ASSET_RE = re.compile(r"windows_10_cmake_Release_Graphviz-[\d.]+-win64\.zip$")


def find_portable_dot():
    for name in ("dot.exe", "dot"):
        hits = sorted(PORTABLE.glob("*/bin/" + name)) + sorted(PORTABLE.glob("bin/" + name))
        if hits:
            return hits[0]
    return None


def find_dot():
    p = find_portable_dot()
    if p:
        return p, "portable(engines\\.graphviz)"
    w = shutil.which("dot")
    if w:
        return Path(w), "PATH"
    return None, None


def http_get(url, to_file=None):
    req = urllib.request.Request(url, headers={"User-Agent": "VIA-WorkOps-GraphvizSetup/0100"})
    with urllib.request.urlopen(req, timeout=120) as r:
        if to_file is None:
            return r.read()
        n = 0
        with open(to_file, "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                n += len(chunk)
                print("\r  [下載] %.1f MB" % (n / 1048576), end="", file=sys.stderr, flush=True)
        print("", file=sys.stderr)
        return n


def verify_dot(dot):
    """Windows 實測 dot -c(建外掛設定,user-scope)+ dot -V;非 Windows 誠實略過執行。"""
    if os.name != "nt":
        return "跳過執行驗證(非 Windows 主機;檔案已就位,實測待操作員機)"
    try:
        subprocess.run([str(dot), "-c"], capture_output=True, timeout=120)
        r = subprocess.run([str(dot), "-V"], capture_output=True, text=True, timeout=60)
        ver = (r.stderr or r.stdout or "").strip()
        return ver if ver else "dot -V 無輸出"
    except Exception as e:
        return "執行驗證失敗:%s" % e


def cmd_status():
    dot, where = find_dot()
    if dot:
        print(json.dumps({"ok": True, "dot": str(dot), "where": where,
                          "verify": verify_dot(dot)}, ensure_ascii=False, indent=2))
        return 0
    print(json.dumps({"ok": False, "dot": None,
                      "hint": "跑 via-workops dotsetup install 取得可攜式 graphviz(免管理員)"},
                     ensure_ascii=False, indent=2))
    return 1


def cmd_install(force):
    existing = find_portable_dot()
    if existing and not force:
        print("[OK] 可攜式 dot 已在位:%s(--force 可重裝)· %s" % (existing, verify_dot(existing)))
        return 0
    print("[1/5] 查官方最新版(GitLab Releases API,動態)...")
    rel = json.loads(http_get(API).decode("utf-8"))[0]
    tag = rel.get("tag_name", "?")
    links = rel.get("assets", {}).get("links", [])
    asset = next((l for l in links if ASSET_RE.search(l.get("name", ""))), None)
    if not asset:
        print("[FAIL] 找不到 win64 Release ZIP 資產(版式變動?)— 誠實停止")
        return 1
    sha = next((l for l in links if l.get("name") == asset["name"] + ".sha256"), None)
    print("  最新版 %s · 資產 %s" % (tag, asset["name"]))
    with tempfile.TemporaryDirectory() as td:
        zpath = Path(td) / asset["name"]
        print("[2/5] 下載 %s ..." % asset["url"])
        http_get(asset["url"], zpath)
        print("[3/5] sha256 驗證...")
        if sha is None:
            print("[FAIL] 官方未附 .sha256 — 不解壓未驗證之物,誠實停止")
            return 1
        want = http_get(sha["url"]).decode("utf-8", "replace").split()[0].lower()
        h = hashlib.sha256()
        with open(zpath, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        got = h.hexdigest().lower()
        if got != want:
            print("[FAIL] sha256 不符(want=%s got=%s)— 檔案作廢,誠實停止" % (want[:16], got[:16]))
            return 1
        print("  sha256 符合(%s…)" % got[:16])
        print("[4/5] 解壓至 %s ..." % PORTABLE)
        if force and PORTABLE.exists():
            shutil.rmtree(PORTABLE)
        PORTABLE.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zpath) as z:
            root = PORTABLE.resolve()
            for m in z.namelist():           # 防 zip-slip:全部落在 .graphviz 內
                if not (root / m).resolve().is_relative_to(root):
                    print("[FAIL] ZIP 內含越界路徑(%s)— 誠實停止" % m)
                    return 1
            z.extractall(PORTABLE)
    dot = find_portable_dot()
    if not dot:
        print("[FAIL] 解壓後未找到 bin\\dot.exe — 誠實停止")
        return 1
    print("[5/5] 實測:%s" % verify_dot(dot))
    print("[總結] 可攜式 graphviz %s 就位:%s · analytics/deep 會自動接上(免重開終端、不動系統 PATH)" % (tag, dot))
    return 0


def main():
    ap = argparse.ArgumentParser(description="WorkOps Graphviz 可攜式取得器(免 winget/管理員;DFG 圖選配)")
    ap.add_argument("command", nargs="?", default="status", choices=["status", "install"],
                    help="預設 status;install=下載+驗證+解壓 user-scope 可攜版")
    ap.add_argument("--force", action="store_true", help="已在位仍重裝")
    a = ap.parse_args()
    try:
        return cmd_status() if a.command == "status" else cmd_install(a.force)
    except Exception as e:
        print("[FAIL] %s(網路受限時可手動:graphviz.org/download 下載 win64 ZIP 解壓到 %s)" % (e, PORTABLE))
        return 1


if __name__ == "__main__":
    sys.exit(main())
