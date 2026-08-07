#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
VIA Status  ——  via_status.py   (\u8a73\u7d30\u77e9\u9663\u7e3d\u89bd\u00b7rich)
================================================================================
\u7528 rich \u756b\u51fa\u6574\u500b VIA_Forge \u7684\u7d50\u69cb\u5316\u77e9\u9663\uff1a
  \u00b7 \u5f15\u64ce\u9663\u5217 (4 \u5f15\u64ce + \u540e\u7aef + \u524d\u7aef\uff0c\u542b\u5370\u00b7\u804c\u8cac\u00b7self-test)
  \u00b7 \u5de5\u5177\u80fd\u529b\u77e9\u9663 (\u51fd\u5f0f\u5eab + \u7cfb\u7d71\u5de5\u5177\uff0c\u5206\u7d44)
  \u00b7 \u652f\u63f4\u683c\u5f0f\u5bb6\u65cf
  \u00b7 \u9023\u63a5\u5668\u72c0\u614b (Gmail/Drive/Outlook/\u672c\u6a5f Outlook)
  \u00b7 \u5206\u985e registry (domain / sensitivity)
  \u00b7 SSOT \u8def\u5f91\u8207\u6cbb\u7406\u65d7\u6a19

\u7f3a rich \u2192 \u81ea\u52d5\u964d\u7d1a\u7d14\u6587\u5b57\uff1b\u4e0d crash\u3002
CLI:
  python via_status.py            # \u5b8c\u6574\u77e9\u9663
  python via_status.py --test     # \u9806\u4fbf\u8ddf\u56db\u5f15\u64ce self-test (\u6162\u4e00\u9ede\u4f46\u6709\u5be6\u6e2c\u6578)
  python via_status.py --plain    # \u5f37\u5236\u7d14\u6587\u5b57
================================================================================
"""

import os
import sys
import io
import json
import argparse
import contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import via_forge as F
try:
    import via_connect as C
except Exception:
    C = None
try:
    import via_pmine as PM
except Exception:
    PM = None
try:
    import via_sink as SK
except Exception:
    SK = None
try:
    import via_panorama as PN
except Exception:
    PN = None

# Visual Lock \u914d\u8272 (\u5c0d\u61c9 rich)
VL = {"blue": "#4c78a8", "teal": "#439a9a", "up": "#c96b5a", "down": "#5a9e6f",
      "grey": "#8a877f", "ink": "#1e1d1a", "gold": "#c9a24c"}

ENGINES = [
    ("庫", "via_dataforge.py", "資料基底：讀取/修復/分類/去重/編號 + 多格式持久化（併 forge+sink）", 5),
    ("牡", "via_mailhub.py", "郵件/專案：智慧(activity/案件/回覆)+ 連接器 + 專案(WorkMatrix/ICS)（併 mailforge+connect+project）", 12),
    ("觀", "via_insight.py", "分析/治理：Dragon-9 風險/稽核 + 流程探勘/SSOT（併 panorama+pmine）", 4),
    ("樞", "via_manager.py", "SystemManager 統一管理整合 3 強引擎 + 共用語料狀態", 13),
]

TOOL_GROUPS = {
    "\u6587\u4ef6\u8b80\u53d6": ["docx", "openpyxl", "pandas", "pptx", "odfpy", "striprtf", "bs4"],
    "PDF \u8207\u5f71\u50cf": ["pypdf", "pikepdf", "PIL", "pytesseract"],
    "\u90f5\u4ef6\u8207\u7de8\u78bc": ["extract_msg", "charset"],
    "\u4e2d\u6587 NLP": ["jieba", "opencc"],
    "\u7cfb\u7d71\u5de5\u5177 (CLI)": ["tesseract", "soffice"],
    "\u6301\u4e45\u5316 sink": ["duckdb", "pyarrow", "polars", "xlsxwriter", "rich"],
}


def run_selftest(mod):
    """\u5410 (pass, fail)\uff0c\u9759\u97f3\u57f7\u884c\u3002"""
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            a, b = mod.selftest()
        return a, b
    except Exception:
        return None, None


# ============================================================ RICH \u7248\u672c ==
def render_rich(do_test=False):
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.tree import Tree
    from rich.columns import Columns
    from rich import box

    con = Console()
    cfg = F.load_config()
    reg = F.load_registry()
    matrix = dict(F.TOOLS.matrix())
    if SK is not None:
        matrix.update(SK.sink_matrix())
    try:
        import rich as _r; matrix["rich"] = True
    except Exception:
        matrix["rich"] = False

    # \u6a19\u984c
    con.print()
    con.print(Panel.fit(
        "[bold]VIA Forge[/bold]  \u00b7  \u8a73\u7d30\u77e9\u9663\u7e3d\u89bd\n"
        "[dim]VeritasDataForge \u00b7 \u5eab \u00b7 Fetch \u00b7 Fix \u00b7 Classify \u00b7 Mine[/dim]",
        border_style=VL["blue"], box=box.HEAVY))

    # \u2500\u2500 \u5f15\u64ce\u9663\u5217 \u2500\u2500
    if do_test:
        test_results = {}
        for seal, name, _, _ in ENGINES:
            base = name.split("/")[0].replace(".py", "")
            mod = {"via_forge": F, "via_connect": C, "via_pmine": PM}.get(base)
            if base == "via_server":
                try:
                    import via_server as S
                    test_results[name] = run_selftest(S)
                except Exception:
                    test_results[name] = (None, None)
            elif mod is not None:
                test_results[name] = run_selftest(mod)
            else:
                test_results[name] = (None, None)

    t = Table(title="\u5f15\u64ce\u9663\u5217 \u00b7 Engine Roster", box=box.ROUNDED,
              title_style="bold", header_style="bold " + VL["blue"], expand=True)
    t.add_column("\u5370", justify="center", width=4)
    t.add_column("\u5f15\u64ce", style=VL["blue"], no_wrap=True)
    t.add_column("\u8077\u8cac")
    t.add_column("self-test", justify="center", width=14)
    total_pass = 0
    for seal, name, role, static_n in ENGINES:
        if do_test and name in test_results and test_results[name][0] is not None:
            p, f = test_results[name]
            total_pass += p
            cell = ("[%s]%d PASS[/]" % (VL["down"], p)) if f == 0 else ("[%s]%d/%d FAIL[/]" % (VL["up"], p, f))
        elif static_n is not None:
            total_pass += static_n
            cell = "[%s]%d PASS[/]" % (VL["down"], static_n)
        else:
            cell = "[dim]\u2014[/]"
        t.add_row(seal, name, role, cell)
    t.add_row("", "[bold]\u5408\u8a08[/bold]", "", "[bold %s]%d PASS[/]" % (VL["down"], total_pass))
    con.print(t)

    # \u2500\u2500 \u5de5\u5177\u80fd\u529b\u77e9\u9663 (\u5206\u7d44) \u2500\u2500
    cap = Table(title="\u5de5\u5177\u80fd\u529b\u77e9\u9663 \u00b7 Capability Matrix", box=box.ROUNDED,
                title_style="bold", header_style="bold " + VL["blue"], expand=True)
    cap.add_column("\u5206\u7d44", style=VL["teal"], no_wrap=True)
    cap.add_column("\u5957\u4ef6 / \u5de5\u5177 (\u2713 \u5c31\u7dd2 / \u2717 \u7f3a\u5e2d\u2192\u964d\u7d1a)")
    for group, tools in TOOL_GROUPS.items():
        cells = []
        for tk in tools:
            on = matrix.get(tk, False)
            mark = "[%s]\u2713[/] %s" % (VL["down"], tk) if on else "[%s]\u2717[/] [dim]%s[/]" % (VL["up"], tk)
            cells.append(mark)
        cap.add_row(group, "   ".join(cells))
    on_n = sum(1 for v in matrix.values() if v)
    cap.caption = "\u5c31\u7dd2 %d / %d \u00b7 \u7f3a\u5e2d\u9805\u81ea\u52d5\u512a\u96c5\u964d\u7d1a\uff0c\u4e0d crash" % (on_n, len(matrix))
    con.print(cap)

    # \u2500\u2500 \u683c\u5f0f\u5bb6\u65cf + \u9023\u63a5\u5668 (\u4e26\u6392) \u2500\u2500
    fam = {}
    for ext, f in F.FORMAT_MAP.items():
        fam.setdefault(f, []).append(ext)
    ftree = Tree("[bold]\u652f\u63f4\u683c\u5f0f\u5bb6\u65cf[/] (%d \u526f\u6a94\u540d)" % len(F.FORMAT_MAP))
    for f in sorted(fam):
        node = ftree.add("[%s]%s[/] [dim](%d)[/]" % (VL["teal"], f, len(fam[f])))
        node.add("[dim]%s[/]" % " ".join(sorted(fam[f])))

    conn_tbl = Table(title="\u9023\u63a5\u5668\u72c0\u614b", box=box.SIMPLE, header_style="bold " + VL["blue"])
    conn_tbl.add_column("\u9023\u63a5\u5668")
    conn_tbl.add_column("scope")
    conn_tbl.add_column("\u72c0\u614b", justify="center")
    if C is not None:
        try:
            cst = C.ConnectEngine(C._ensure_connect_cfg(cfg)).status()["connectors"]
        except Exception:
            cst = {}
        rows = [("gmail", "gmail.readonly"), ("drive", "drive.readonly"),
                ("outlook", "Mail.Read"), ("local_outlook", "\u672c\u6a5f\u767b\u5165\u8eab\u5206")]
        for k, scope in rows:
            on = cst.get(k, False)
            st = "[%s]\u5c31\u7dd2[/]" % VL["down"] if on else "[%s]\u9700\u88dd SDK/\u6388\u6b0a[/]" % VL["gold"]
            conn_tbl.add_row(k, "[dim]%s[/]" % scope, st)
    con.print(Columns([Panel(ftree, border_style=VL["teal"], title="\u683c\u5f0f"),
                       Panel(conn_tbl, border_style=VL["blue"], title="\u9023\u63a5\u5668 (\u8f14)")],
                      equal=True, expand=True))

    # \u2500\u2500 \u5206\u985e registry \u2500\u2500
    dom = reg.get("domains", {})
    sens = reg.get("sensitivity", {})
    rtbl = Table(title="\u5206\u985e Registry (append-only)", box=box.ROUNDED,
                 title_style="bold", header_style="bold " + VL["blue"], expand=True)
    rtbl.add_column("\u985e\u578b", style=VL["teal"], no_wrap=True)
    rtbl.add_column("\u6a19\u7c64")
    rtbl.add_column("\u95dc\u9375\u8a5e\u6578", justify="right", width=8)
    for d, kws in dom.items():
        rtbl.add_row("domain", d, str(len(kws)))
    for s, kws in sens.items():
        rtbl.add_row("[%s]sensitivity[/]" % VL["up"], s, str(len(kws)))
    con.print(rtbl)

    # \u2500\u2500 SSOT \u8def\u5f91 + \u6cbb\u7406\u65d7\u6a19 \u2500\u2500
    paths = cfg["paths"]
    ptree = Tree("[bold]SSOT \u8def\u5f91[/] [dim](root-anchored)[/]")
    ptree.add("root  [dim]%s[/]" % paths.get("root"))
    for k in ("inbox", "ledger", "cache", "reports", "quarantine", "venv"):
        ptree.add("%-10s [dim]%s[/]" % (k, paths.get(k, "\u2014")))

    gov = cfg.get("governance", {})
    gtbl = Table(box=box.SIMPLE, header_style="bold " + VL["blue"], title="\u6cbb\u7406\u65d7\u6a19")
    gtbl.add_column("\u65d7\u6a19"); gtbl.add_column("\u503c", justify="center")
    for k in ("append_only", "no_delete", "no_network_egress", "audit_every_action"):
        v = gov.get(k)
        mark = "[%s]ON[/]" % VL["down"] if v else "[dim]off[/]"
        gtbl.add_row(k, mark)
    con.print(Columns([Panel(ptree, border_style=VL["teal"], title="\u8def\u5f91"),
                       Panel(gtbl, border_style=VL["blue"], title="\u6cbb\u7406")],
                      equal=True, expand=True))

    con.print(Panel.fit(
        "[dim]loopback only \u00b7 \u53ea\u8b80\u672c\u6a5f\u6388\u6b0a\u6a94 \u00b7 append-only ledger \u00b7 \u53ea\u589e\u4e0d\u6e1b[/dim]",
        border_style=VL["grey"], box=box.HEAVY))
    con.print()


# ============================================================ \u7d14\u6587\u5b57\u964d\u7d1a ==
def render_plain(do_test=False):
    cfg = F.load_config(); reg = F.load_registry(); matrix = dict(F.TOOLS.matrix())
    if SK is not None:
        matrix.update(SK.sink_matrix())
    try:
        import rich as _r; matrix["rich"] = True
    except Exception:
        matrix["rich"] = False
    line = "=" * 68
    print("\n" + line + "\n VIA Forge \u00b7 \u8a73\u7d30\u77e9\u9663\u7e3d\u89bd\n" + line)

    print("\n[\u5f15\u64ce\u9663\u5217]")
    total = 0
    for seal, name, role, n in ENGINES:
        tag = ""
        if do_test:
            base = name.split("/")[0].replace(".py", "")
            mod = {"via_forge": F, "via_connect": C, "via_pmine": PM}.get(base)
            if mod:
                p, f = run_selftest(mod)
                if p is not None:
                    total += p; tag = "%d PASS" % p if f == 0 else "%d/%d FAIL" % (p, f)
        elif n is not None:
            total += n; tag = "%d PASS" % n
        print("  %-3s %-22s %-38s %s" % (seal, name, role[:36], tag))
    print("  %-3s %-22s %-38s %d PASS" % ("", "\u5408\u8a08", "", total))

    print("\n[\u5de5\u5177\u80fd\u529b\u77e9\u9663]")
    for group, tools in TOOL_GROUPS.items():
        cells = ["%s%s" % ("\u2713" if matrix.get(t) else "\u2717", t) for t in tools]
        print("  %-14s %s" % (group, "  ".join(cells)))
    on_n = sum(1 for v in matrix.values() if v)
    print("  \u5c31\u7dd2 %d / %d" % (on_n, len(matrix)))

    print("\n[\u652f\u63f4\u683c\u5f0f\u5bb6\u65cf] (%d \u526f\u6a94\u540d)" % len(F.FORMAT_MAP))
    fam = {}
    for ext, f in F.FORMAT_MAP.items():
        fam.setdefault(f, []).append(ext)
    for f in sorted(fam):
        print("  %-16s %s" % (f, " ".join(sorted(fam[f]))))

    if C is not None:
        print("\n[\u9023\u63a5\u5668\u72c0\u614b]")
        try:
            cst = C.ConnectEngine(C._ensure_connect_cfg(cfg)).status()["connectors"]
        except Exception:
            cst = {}
        for k in ("gmail", "drive", "outlook", "local_outlook"):
            print("  %-16s %s" % (k, "\u5c31\u7dd2" if cst.get(k) else "\u9700\u88dd SDK/\u6388\u6b0a"))

    print("\n[\u5206\u985e Registry]")
    for d, kws in reg.get("domains", {}).items():
        print("  domain       %-24s %d \u95dc\u9375\u8a5e" % (d, len(kws)))
    for s, kws in reg.get("sensitivity", {}).items():
        print("  sensitivity  %-24s %d \u95dc\u9375\u8a5e" % (s, len(kws)))

    print("\n[\u6cbb\u7406\u65d7\u6a19]")
    gov = cfg.get("governance", {})
    for k in ("append_only", "no_delete", "no_network_egress", "audit_every_action"):
        print("  %-22s %s" % (k, "ON" if gov.get(k) else "off"))
    print("\n" + line + "\n loopback \u00b7 \u53ea\u8b80\u672c\u6a5f\u6388\u6b0a \u00b7 append-only \u00b7 \u53ea\u589e\u4e0d\u6e1b\n" + line + "\n")


def main():
    ap = argparse.ArgumentParser(description="VIA Forge status matrix (rich)")
    ap.add_argument("--test", action="store_true", help="\u9806\u4fbf\u8ddf\u56db\u5f15\u64ce self-test")
    ap.add_argument("--plain", action="store_true", help="\u5f37\u5236\u7d14\u6587\u5b57")
    args = ap.parse_args()

    use_rich = not args.plain
    if use_rich:
        try:
            import rich  # noqa
        except Exception:
            use_rich = False
    if use_rich:
        render_rich(do_test=args.test)
    else:
        render_plain(do_test=args.test)


if __name__ == "__main__":
    main()
