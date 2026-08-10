# -*- coding: utf-8 -*-
r"""board_qa.py v0100 — 指揮板四層測試(操作員「unit/integration/system test + u/i sync」令)。

四層(逐層誠實 OK/FAIL/SKIP,缺工具=SKIP 不冒充):
  TIER 1 unit         板內純函數直測(esc/arr/fmt/t/gsBuild/pfStrip)— node vm
  TIER 2 integration  fixture DATA 全渲染 DOM 側效斷言(11 頁/流程帶/搜尋/M7)— node vm
  TIER 3 system       真瀏覽器旅程(分頁/搜尋/詳情窗/語言/零 pageerror)— node+playwright
  TIER 4 design-sync  U/I 與設計正本對齊:design/Veritas_WorkOps_v2_hlock.dc.html
                      (seal 4cb90a0bd31df637)之色票/字體/封印 — 純 Python 任何機器可跑
產物:out/board_qa_report.json。動態解析最新板;嚴禁寫死版號。
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKOPS = HERE.parent
OUT = WORKOPS / "out"
DESIGN = WORKOPS / "design" / "Veritas_WorkOps_v2_hlock.dc.html"
FIXTURE = HERE / "fixture_board_data.json"
DESIGN_SEAL16 = "4cb90a0bd31df637"

# 設計正本(Industry 設計系統)之核心角色 token — 於 tier_design 由 :root 動態抽取;
# 硬 FAIL 只掛封印與 accent 主色(板 v2 鎖實踐錨點);其餘 token 誠實記「對齊度+漂移清單」。
CORE_ROLES = ["--color-bg", "--color-surface", "--color-text", "--color-accent", "--color-accent-2"]

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def newest_board():
    cands = sorted(WORKOPS.glob("Invoke-VIA-WorkOps-CommandBoard-v0*.ps1"))
    return cands[-1] if cands else None


def extract(board_src):
    m = re.search(r"\$html = @'\n(.*?)\n'@", board_src, re.S)
    html = m.group(1) if m else ""
    mj = re.search(r"<script>\n(.*?)</script>", html, re.S)
    return html, (mj.group(1) if mj else "")


def _design_tokens(design):
    """設計正本 :root 動態抽 token(單一事實源 — 設計檔自己說了算)。"""
    m = re.search(r":root\s*\{(.*?)\n\}", design, re.S) or re.search(r":root\s*\{(.*?)\}", design, re.S)
    toks = {}
    if m:
        for name, val in re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", m.group(1)):
            toks[name] = val.strip()
    return toks


def tier_design(board_src):
    checks = []
    drift = []
    if not DESIGN.exists():
        return [("design 正本在位", False, "design/Veritas_WorkOps_v2_hlock.dc.html 缺席")], drift
    sha16 = hashlib.sha256(DESIGN.read_bytes()).hexdigest()[:16]
    checks.append(("design 封印驗真", sha16 == DESIGN_SEAL16,
                   "sha16 %s(板上封印 %s)" % (sha16, DESIGN_SEAL16)))
    checks.append(("板記載同一封印", DESIGN_SEAL16 in board_src, "視覺鎖 v2 錨定同一正本"))
    design = DESIGN.read_text(encoding="utf-8", errors="replace")
    toks = _design_tokens(design)
    checks.append(("design :root token 可抽取", len(toks) >= 10, "%d tokens" % len(toks)))
    accent = (toks.get("--color-accent") or "").lower()
    if accent.startswith("#"):
        checks.append(("accent 主色 %s 入板(v2 鎖實踐錨點)" % accent, accent in board_src.lower(), ""))
    # 其餘核心角色:誠實量對齊度 — 不硬 FAIL(板為既裁定視覺鎖;全面換裝=破鎖需操作員明示)
    n_hit = 0
    for role in CORE_ROLES:
        v = (toks.get(role) or "").lower()
        if v.startswith("#"):
            if v in board_src.lower():
                n_hit += 1
            else:
                drift.append("%s %s" % (role, v))
    checks.append(("核心角色對齊度(資訊性,漂移入報告)", True,
                   "%d/%d;漂移:%s" % (n_hit, len(CORE_ROLES), "、".join(drift) or "無")))
    fonts = [f for f in ("Barlow", "Barlow Condensed") if f in design]
    drift_fonts = [f for f in fonts if f not in board_src]
    checks.append(("字體對齊(資訊性)", True,
                   "設計用 %s;板未採 %s(板現行 JhengHei/DM Mono=既裁定)" %
                   ("、".join(fonts) or "—", "、".join(drift_fonts) or "無")))
    flow_ui = (WORKOPS.parent.parent / "supportive modules" / "VIA_FlowSystem" /
               "FlowSystem_v2" / "engines" / "flow_ui.py")
    if flow_ui.exists():
        fu = flow_ui.read_text(encoding="utf-8", errors="replace")
        hexes = set(h.lower() for h in re.findall(r"#[0-9a-fA-F]{6}", fu))
        board_hex = set(h.lower() for h in re.findall(r"#[0-9a-fA-F]{6}", board_src))
        inter = len(hexes & board_hex)
        checks.append(("FlowSystem UI 與板同語彙(≥6 共用色)", inter >= 6, "%d 共用色" % inter))
    return checks, drift


def run_node(script, *args):
    node = shutil.which("node")
    if not node:
        return None, "node 不在位(裝 Node.js 後重跑;本層誠實 SKIP)"
    r = subprocess.run([node, str(script), *[str(a) for a in args]],
                       capture_output=True, text=True, timeout=300)
    return r, None


def main():
    board = newest_board()
    if not board:
        print("[FAIL] CommandBoard 不在位")
        return 1
    print("[板] %s" % board.name)
    src = board.read_text(encoding="utf-8", errors="replace")
    html, js = extract(src)
    work = OUT / "qa_work"
    work.mkdir(parents=True, exist_ok=True)
    tiers = {}

    # TIER 1+2:node vm
    (work / "board_extracted.js").write_text(js, encoding="utf-8")
    r, skip = run_node(HERE / "board_qa_runner.mjs", work / "board_extracted.js", FIXTURE)
    if skip:
        tiers["unit_integration"] = {"r": "SKIP", "note": skip}
        print("[T1+2] SKIP — %s" % skip)
    else:
        print(r.stdout.rstrip())
        if r.stderr.strip():
            print(r.stderr.rstrip())
        tiers["unit_integration"] = {"r": "OK" if r.returncode == 0 else "FAIL",
                                     "note": (r.stdout.strip().splitlines() or [""])[-1]}

    # TIER 3:system(playwright;chromium 路徑可由環境 PW_CHROMIUM 指定)
    sample = work / "board_sample.html"
    sample.write_text(html.replace("__VIA_DATA__", FIXTURE.read_text(encoding="utf-8")),
                      encoding="utf-8")
    import os
    chrome = os.environ.get("PW_CHROMIUM", "")
    r, skip = run_node(HERE / "board_qa_system.mjs", sample, *((chrome,) if chrome else ()))
    if skip:
        tiers["system"] = {"r": "SKIP", "note": skip}
        print("[T3] SKIP — %s" % skip)
    elif r.returncode == 3:
        tiers["system"] = {"r": "SKIP", "note": "playwright 未安裝(npm i playwright)"}
        print("[T3] SKIP — playwright 未安裝")
    else:
        print(r.stdout.rstrip())
        if r.stderr.strip():
            print(r.stderr.rstrip())
        tiers["system"] = {"r": "OK" if r.returncode == 0 else "FAIL",
                           "note": (r.stdout.strip().splitlines() or [""])[-1]}

    # TIER 4:design-sync(純 Python;硬 FAIL=封印/accent,其餘誠實記漂移)
    checks, drift = tier_design(src)
    n_bad = sum(1 for _, ok, _ in checks if not ok)
    for name, ok, note in checks:
        print("%s DSN - %s%s" % ("ok " if ok else "FAIL", name, (" · " + note) if note else ""))
    tiers["design_sync"] = {"r": "OK" if n_bad == 0 else "FAIL",
                            "note": "%d/%d 過(漂移 %d 項入報告)" % (len(checks) - n_bad, len(checks), len(drift))}

    rep = {"ts": datetime.now().isoformat(timespec="seconds"), "version": "v0100",
           "board": board.name, "design_seal16": DESIGN_SEAL16, "tiers": tiers,
           "design_drift": drift,
           "drift_note": "板為既裁定視覺鎖(seal 錨定);全面換裝 Industry 色票/Barlow=破鎖重塑,需操作員明示裁定"}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "board_qa_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1),
                                              encoding="utf-8")
    n_fail = sum(1 for v in tiers.values() if v["r"] == "FAIL")
    n_skip = sum(1 for v in tiers.values() if v["r"] == "SKIP")
    print("=" * 56)
    print("[總結] BoardQA 四層:OK %d · SKIP %d(誠實列缺)· FAIL %d → out/board_qa_report.json"
          % (len(tiers) - n_fail - n_skip, n_skip, n_fail))
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
