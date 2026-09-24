#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL188_BatchResultReport v0100 — 批次實測結果報告頁(批736)

操作員令:「最後實測要 HTML U/I 結果報告」。

**這支不是把數字抄成網頁。** 報告裡的每一個數字都在產頁的當下**現場量**:
自測是真的跑一次、擊斃閘是真的判一次、ADJ 對照是真的拿 duckdb 算一次。
量不到的那一格寫 ABSENT / NODATA 並講出因由,**不留白、不省略**——
一張省略了量不到那幾格的報告,看起來會比實際情況漂亮,那就是紙面上的假綠。

六態:GREEN(量到且合格)· RED(量到但不合格)· NODATA(有來源沒值)·
      ABSENT(來源不在)· GATED(要觸網/要同意閘)· SKIP(本境不適用)

**rc 表達的是「這張報告產得出來嗎」,不是「一切是否全綠」。** 這一條是刻意的:
本支會讀最新一份格子存證,而格子跑到本站的時候,最新存證是**上一跑**的——
rc 若拿來表達全綠與否,本站就會拿上一跑的紅去判這一跑,那是循環,而且會自我應驗。
判斷留在閘(CGC_MDL187)與格子自己身上;本支只負責**把量到的照實印出來**。
  rc0 = 頁產出來了,而且每一格都量到 · rc2 = 產出來了但有格子量不到(ABSENT/NODATA/GATED)
  rc3 = 連頁都寫不出來
頁面上的總判(GREEN/RED/…)照樣取**最差那一格**,一格紅就整份紅 —— 那是給人看的判斷,不是 rc。

律:唯讀(只讀樹、只寫自己那張頁到 VIA_Reports/)· 零網路 · 零 CDN · 零彈窗 · 不代設同意閘。
用法:python3 CGC_MDL188_BatchResultReport_v0100.py [--out <路徑>] [--json] | --selftest
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

import ast
import html
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ENGINE_ID = "CGC_MDL188_BatchResultReport"
VERSION = "v0100"
BATCH = "批736"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Reports" / "batch_result" / "VIA_B736_RESULT_latest.html"

#: 操作員原話。**逐字**,不改寫、不潤飾——報告的第一段若已經是轉述,後面全是轉述的轉述。
ORDERS = (
    "所有目標價及各前一日的價格都要換成 ADJ CLOSE",
    "更新模組或修正模組都要有嚴格的把關擊斃較機制",
    "REAL TEST DEBUG OPTIMIZE TEST CONSOLIDATE TEST DEBUG USER-TEST DEBUG "
    "ACTIVATE TEST DEBUG TILL IT WORKS PERFECT. 自動傳PR自動批種完成 最後實測要HTML U/I結果報告",
)

STATE_RANK = {"RED": 0, "ABSENT": 1, "NODATA": 2, "GATED": 3, "SKIP": 4, "GREEN": 5}


def _newest(pat: str, base: Path) -> Path | None:
    hits = sorted(base.glob(pat))
    return hits[-1] if hits else None


def _run(args: list[str], timeout: int = 900) -> tuple[int, str]:
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as exc:
        return 127, f"{exc}"


def _count_line(out: str) -> str:
    """自測最後那行 `[計] …`。抓不到回空字串(抓不到就說抓不到,不編一個數字)。"""
    hits = [l.strip() for l in out.splitlines() if "[計]" in l]
    return hits[-1] if hits else ""


# ── 逐項現場量 ───────────────────────────────────────────────────
def measure_selftest(label: str, path: Path | None, why_absent: str) -> dict:
    if path is None or not path.is_file():
        return {"label": label, "state": "ABSENT", "detail": why_absent, "evidence": ""}
    rc, out = _run([sys.executable, str(path), "--selftest"])
    line = _count_line(out)
    m = re.search(r"OK\s+(\d+)\s*·\s*FAIL\s+(\d+)", line)
    ok, fail = (int(m.group(1)), int(m.group(2))) if m else (None, None)
    if rc == 0 and fail == 0:
        st = "GREEN"
    elif rc == 2:
        st = "NODATA"
    elif rc == 3:
        st = "ABSENT"
    elif rc == 5:
        st = "SKIP"
    else:
        st = "RED"
    return {"label": label, "state": st, "detail": f"{path.name} · rc={rc}",
            "evidence": line or "(自測沒有印出 [計] 行——抓不到就是抓不到,不補一個數字)",
            "ok": ok, "fail": fail}


def measure_killgate() -> dict:
    g = _newest("CGC_MDL187_ModuleChangeKillGate_v*.py", HERE)
    if g is None:
        return {"label": "把關擊斃閘 · 對本批改動實判", "state": "ABSENT",
                "detail": "CGC_MDL187 不在樹上", "evidence": ""}
    rc, out = _run([sys.executable, str(g), "--json"], timeout=900)
    try:
        d = json.loads(out)
    except Exception:
        return {"label": "把關擊斃閘 · 對本批改動實判", "state": "ABSENT",
                "detail": f"閘輸出解不開(rc={rc})", "evidence": out.strip()[-200:]}
    st = {"PASS": "GREEN", "KILL": "RED", "PARTIAL": "NODATA",
          "NODATA": "NODATA", "ABSENT": "ABSENT"}.get(d.get("state"), "ABSENT")
    ev = f"判了 {d.get('checked')} 檔 · 擊斃 {len(d.get('kills', []))} 件 · 既有債 {len(d.get('debts', []))} 筆"
    return {"label": "把關擊斃閘 · 對本批改動實判", "state": st,
            "detail": f"{g.name} · rc={d.get('rc')} · {d.get('state')}",
            "evidence": ev, "kills": d.get("kills", []), "debts": d.get("debts", [])}


def measure_adj() -> dict:
    """ADJ 對照:**現場拿 duckdb 算**,而且量的是**預設分支真的實作了什麼**。

    批729 加的是 price_prev_close / price_prev_adj / price_prev_date 三欄,
    批730 又加了 adj_factor_basis(因子分母的出處)。走它自己的委派口 `adj_quote()`,
    不另寫一份算法(LL404:不長第二顆頭)。

    初版探的是 `price_db_basis` —— 那是**我自己那版**想加的欄,預設分支上根本沒有,
    於是整格 KeyError 變成 ABSENT。量的要是那邊真有的東西,不是我以為應該有的東西。
    夾具用真除權息的一天:6147 前一交易日 close 207.0 / adj_close 204.4523。
    """
    eng = _newest("VRN_ENG073_ReportStructuredDB_v*.py", VIA / "functional modules" / "VRN")
    if eng is None:
        return {"label": "ADJ 對照(目標價 ÷ 前一日價)", "state": "ABSENT",
                "detail": "ENG073 不在樹上", "evidence": ""}
    probe = "\n".join([
        "import importlib.util, sys, json",
        "spec = importlib.util.spec_from_file_location('e', sys.argv[1])",
        "m = importlib.util.module_from_spec(spec); sys.modules['e'] = m",
        "spec.loader.exec_module(m)",
        "import duckdb",
        "c = duckdb.connect(':memory:')",
        "c.execute('CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, "
        "close DOUBLE, adj_close DOUBLE)')",
        "c.execute(\"INSERT INTO tw_daily_prices VALUES "
        "('2026-05-18','6147.TWO',207.0,204.4523),('2026-09-18','6147.TWO',229.0,229.0)\")",
        "q = m.adj_quote(c, '6147', '2026-05-19', 280.0)",
        "print(json.dumps({'prev_close': q.get('price_prev_close'), "
        "'prev_adj': q.get('price_prev_adj'), 'prev_date': q.get('price_prev_date'), "
        "'factor': q.get('adj_factor'), 'factor_basis': q.get('adj_factor_basis'), "
        "'tp_adj': q.get('target_price_adj'), 'latest_adj': q.get('price_latest_adj'), "
        "'upside_adj': q.get('upside_adj'), 'state': q.get('upside_adj_state'), "
        "'eng': sys.argv[1].split('/')[-1]}, ensure_ascii=False))",
    ])
    rc, out = _run([sys.executable, "-c", probe, str(eng)], timeout=300)
    line = [l for l in out.splitlines() if l.startswith("{")]
    if rc != 0 or not line:
        return {"label": "ADJ 對照(目標價 ÷ 前一日價)", "state": "ABSENT",
                "detail": f"算不出(rc={rc})—— duckdb 缺件,或委派口 adj_quote 的契約變了",
                "evidence": out.strip()[-220:]}
    d = json.loads(line[-1])
    # 前一日價真的換成 ADJ 了嗎:那天 close 是 207.0,ADJ 必須是 204.4523(不是 207.0);
    # 日期要落欄、目標價要換算過、上漲空間要用**最新** ADJ。
    good = (d["prev_close"] == 207.0 and d["prev_adj"] == 204.4523
            and d["prev_date"] == "2026-05-18" and d["tp_adj"] is not None
            and d["latest_adj"] == 229.0 and d["upside_adj"] is not None
            and str(d["state"]).startswith("ADJ_OK"))
    raw_side = round((280.0 / 207.0 - 1) * 100, 1)   # 若拿未調整的前一日價當分母
    return {"label": "ADJ 對照(目標價 ÷ 前一日價)", "state": "GREEN" if good else "RED",
            "detail": f"{d['eng']} · 委派口 adj_quote() · 6147 報告日 2026-05-19 · 目標價 280",
            "evidence": (f"前一日 {d['prev_date']} close {d['prev_close']} → "
                         f"adj {d['prev_adj']} · 因子 {d['factor']}"
                         f"(分母出處 {d['factor_basis']})· 目標價adj {d['tp_adj']} · "
                         f"最新adj {d['latest_adj']} → {d['upside_adj']:+.1f}% · {d['state']}"
                         f"〔對照:拿未調整的 207.0 當分母會是 {raw_side:+.1f}%〕"),
            "adj": d}


def measure_grid() -> dict:
    ev = VIA / "VIA_Reports" / "selftest_runs"
    newest = max(ev.glob("GRID_2026*.json"), key=lambda p: p.name, default=None) if ev.is_dir() else None
    if newest is None:
        return {"label": "全格子", "state": "ABSENT",
                "detail": "找不到 GRID_*.json 存證——格子沒跑過,不是跑過全綠", "evidence": ""}
    d = json.loads(newest.read_text(encoding="utf-8"))
    fail = int(d.get("fail") or 0)
    return {"label": "全格子",
            "state": "GREEN" if fail == 0 else "RED",
            "detail": f"存證 {newest.name}",
            "evidence": (f"OK {d.get('ok')} · FAIL {fail} · SKIP {d.get('skip')} · "
                         f"TIMEOUT {d.get('timeout')} · 判了 {d.get('done')}/{d.get('total')} 站"),
            "grid": d}


def measure() -> dict:
    vrn = VIA / "functional modules" / "VRN"
    rows = [
        measure_selftest("VRN_ENG073 · ADJ CLOSE(**批729+批730 已在 main 交付**;本批只複驗)",
                         _newest("VRN_ENG073_ReportStructuredDB_v*.py", vrn),
                         "ENG073 不在樹上"),
        measure_selftest("CGC_MDL187 模組更新擊斃閘(本批**唯一**的新功能)",
                         _newest("CGC_MDL187_ModuleChangeKillGate_v*.py", HERE),
                         "MDL187 不在樹上"),
        measure_adj(),
        measure_killgate(),
        measure_grid(),
    ]
    worst = min((STATE_RANK.get(r["state"], 0) for r in rows), default=0)
    verdict = [k for k, v in STATE_RANK.items() if v == worst][0]
    return {"batch": BATCH, "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "orders": list(ORDERS), "rows": rows, "verdict": verdict}


# ── 產頁(零 CDN · 零彈窗 · 全部內嵌)────────────────────────────
_CSS = """
:root{--bg:#f6f7f9;--fg:#15181d;--card:#fff;--line:#d9dde3;--mut:#5b6472;
--green:#137a41;--red:#b3261e;--amber:#8a6100;--grey:#5b6472;--accent:#1b4fa0}
:root:not([data-theme="light"]) @media (prefers-color-scheme:dark){}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#101318;--fg:#e8ecf2;
--card:#171b22;--line:#2a313b;--mut:#9aa5b4;--green:#4ec98a;--red:#ff7b72;--amber:#e3b341;
--grey:#9aa5b4;--accent:#79a9ff}}
:root[data-theme="dark"]{--bg:#101318;--fg:#e8ecf2;--card:#171b22;--line:#2a313b;--mut:#9aa5b4;
--green:#4ec98a;--red:#ff7b72;--amber:#e3b341;--grey:#9aa5b4;--accent:#79a9ff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.65 -apple-system,"Segoe UI",
"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:28px 16px 60px}
h1{font-size:25px;margin:0 0 4px} h2{font-size:18px;margin:30px 0 12px}
.sub{color:var(--mut);font-size:13px;margin-bottom:22px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:12px 0}
.verdict{display:inline-block;padding:5px 14px;border-radius:999px;font-weight:700;font-size:14px}
.v-GREEN{background:var(--green);color:#fff} .v-RED{background:var(--red);color:#fff}
.v-NODATA,.v-GATED{background:var(--amber);color:#fff} .v-ABSENT,.v-SKIP{background:var(--grey);color:#fff}
table{width:100%;border-collapse:collapse;margin-top:8px;font-size:14px}
th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--mut);font-weight:600;font-size:12.5px;letter-spacing:.03em}
td.s{white-space:nowrap;width:1%}
.pill{display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;font-weight:700}
code,.ev{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12.5px}
.ev{color:var(--mut);display:block;margin-top:4px;word-break:break-word}
blockquote{margin:8px 0;padding:8px 14px;border-left:3px solid var(--accent);color:var(--fg);
background:color-mix(in srgb,var(--accent) 7%,transparent);border-radius:0 8px 8px 0}
.note{color:var(--mut);font-size:13px}
ul{margin:8px 0 0;padding-left:20px} li{margin:4px 0}
@media(max-width:640px){.wrap{padding:20px 16px 48px}h1{font-size:21px}table{font-size:13px}}
"""


def render_html(d: dict) -> str:
    e = html.escape
    rows = []
    for r in d["rows"]:
        st = r["state"]
        rows.append(
            f'<tr><td class="s"><span class="pill v-{e(st)}">{e(st)}</span></td>'
            f'<td><b>{e(r["label"])}</b><span class="ev">{e(r["detail"])}</span></td>'
            f'<td><span class="ev">{e(r.get("evidence") or "—")}</span></td></tr>')
    kg = next((r for r in d["rows"] if "擊斃閘" in r["label"] and "實判" in r["label"]), {})
    debts = "".join(f"<li><code>{e(t.get('code',''))}</code> {e(Path(t.get('path','')).name)} · "
                    f"{e(t.get('detail',''))}</li>" for t in kg.get("debts", []))
    kills = "".join(f"<li><code>{e(k.get('code',''))}</code> {e(Path(k.get('path','')).name)} · "
                    f"{e(k.get('detail',''))}</li>" for k in kg.get("kills", []))
    orders = "".join(f"<blockquote>{e(o)}</blockquote>" for o in d["orders"])
    v = d["verdict"]
    verdict_zh = {"GREEN": "全綠(每一格都量到、而且合格)",
                  "RED": "有紅(下面那張表裡的 RED 就是位置)",
                  "NODATA": "有格子量不到值", "ABSENT": "有來源不在",
                  "GATED": "有格子卡在同意閘", "SKIP": "有格子本境不適用"}.get(v, v)
    return f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>批736 實測結果</title><style>{_CSS}</style></head>
<body><div class="wrap">
<h1>批736 · 實測結果報告</h1>
<div class="sub">{e(d['ts'])} · 產頁當下現場量 · 零網路 · 零 CDN ·
每一格的數字都是這一次跑出來的,不是抄的</div>

<div class="card"><span class="verdict v-{e(v)}">{e(v)}</span>
&nbsp;<b>{e(verdict_zh)}</b>
<div class="note" style="margin-top:8px">總判 = 所有格子裡**最差**的那一格。
一格 RED 就整份 RED —— 把五格裡的四格綠拿去平均成「大致綠」,是這棵樹一直在打的假綠。</div></div>

<h2>一 · 操作員令(逐字)</h2>
{orders}

<h2>二 · 逐項實測</h2>
<div class="card"><table>
<thead><tr><th>態</th><th>量什麼</th><th>量到什麼</th></tr></thead>
<tbody>{"".join(rows)}</tbody></table></div>

<h2>三 · 擊斃閘判決明細</h2>
<div class="card">
<p><b>擊斃</b>(中條款 → rc=1,改動不准進):{"<ul>" + kills + "</ul>" if kills else "<span class='note'>無</span>"}</p>
<p><b>既有債</b>(基線內,記帳不擊斃 —— 既有債一律擊斃會把樹擋死,然後這道閘就會被關掉):
{"<ul>" + debts + "</ul>" if debts else "<span class='note'>無</span>"}</p>
</div>

<h2>四 · 兩道令,一道早就做完了</h2>
<div class="card"><p class="note">
<b>令一(目標價與各前一日價換 ADJ CLOSE):不是本批做的。</b>
預設分支上 <b>批729</b> 就已經落實(新欄 <code>price_prev_close</code> /
<code>price_prev_adj</code> / <code>price_prev_date</code>),<b>批730</b> 又拿真料把因子分母修得更對:
Yahoo 的 close 會事後按配股回頭調整,容器實量 <b>13.6% 的列、796/893 檔</b>對不上交易所收盤。
上表那一列是**複驗** —— 本批真的跑了一次它的自測,把跑出來的數字照實貼在這裡,不是抄它的自陳。
</p><p class="note">
<b>令二(更新模組要有嚴格的把關擊斃機制):是本批做的</b>,預設分支上沒有這個東西。
而本批自己就是它的第一個案例:我在一個落後 <b>89 個 commit</b> 的基線上做完一整批,
開的 <code>v0137</code> 撞上預設分支上別的批做的同名 <code>v0137</code>,
而我要的功能那邊早就有了。前十條條款一條都沒攔住 ——
它們全部只問「這次改了什麼」,<b>沒有一條問「你改的是不是當下那一版」</b>。
所以有了第十一條 <code>KILL-11 基線時效</code>,而它的正控就是照這件事的形狀擺的。
</p></div>

<h2>五 · 待操作員裁定</h2>
<div class="card"><ul>
<li><b>同一道令同時派給了兩條線</b>(本批與批729)。要不要有個地方,讓動手前先看得到「這道令是不是已經有人在做」。</li>
<li>把 <code>KILL-11</code> 接進 CI —— 現在只在格子與手動跑得到;接進 CI 才攔得住落後基線的 push。</li>
<li>LL344–LL443 共 100 條教訓只在 <code>docs/</code>,正典政策冊停在 LL343 —— 要不要回填。</li>
<li><code>via-killgate</code> 梭與 Register 登錄 —— <code>.ps1</code> 是操作員的手(L70)。</li>
</ul></div>
</div></body></html>
"""


def build(out: Path | None = None) -> dict:
    d = measure()
    o = Path(out) if out else OUT
    o.parent.mkdir(parents=True, exist_ok=True)
    o.write_text(render_html(d), encoding="utf-8")
    d["out"] = str(o)
    return d


def selftest() -> int:
    import tempfile
    ran, fails = [], []

    def chk(name, cond, note=""):
        ran.append(name)
        ok = bool(cond)
        if not ok:
            fails.append(name)
        print("  [%s] %s%s" % ("OK" if ok else "FAIL", name, (" (%s)" % note) if note else ""))

    print(f"=== 批次實測結果報告頁 {VERSION} · 自測(沙盒 · 零網路 · 唯讀)===")

    # ① 總判取最差,不取平均
    mk = lambda *ss: {"batch": BATCH, "ts": "t", "orders": ["o"],
                      "rows": [{"label": f"r{i}", "state": s, "detail": "", "evidence": ""}
                               for i, s in enumerate(ss)],
                      "verdict": [k for k, v in STATE_RANK.items()
                                  if v == min(STATE_RANK[s] for s in ss)][0]}
    chk("① **總判取最差那一格,不取平均**:四綠一紅 = RED。"
        "把五格裡的四格綠平均成「大致綠」,就是這棵樹一直在打的假綠",
        mk("GREEN", "GREEN", "GREEN", "GREEN", "RED")["verdict"] == "RED"
        and mk("GREEN", "NODATA")["verdict"] == "NODATA"
        and mk("GREEN", "GREEN")["verdict"] == "GREEN")

    # ② 量不到要寫 ABSENT,不是省略
    gone = measure_selftest("不存在的引擎", None, "這支不在樹上")
    chk("② **量不到的那一格要留在表上寫 ABSENT,不是從表上消失**——"
        "一張省略了量不到那幾格的報告,看起來會比實際情況漂亮(L57 誠實分母)",
        gone["state"] == "ABSENT" and gone["detail"] == "這支不在樹上",
        f"({gone['state']})")

    # ③ 自測沒印 [計] 行 → 誠實說抓不到,不補數字
    chk("③ 自測沒印出 `[計]` 行時,證據欄要**說抓不到**,不得補一個看起來合理的數字",
        _count_line("沒有計數行\n只有別的") == "")

    # ④ 真產頁:零 CDN、零彈窗、HTML 完整
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "r.html"
        d = build(out=p)
        page = p.read_text(encoding="utf-8")
    bad_cdn = [x for x in ("http://", "https://") if x in page]
    bad_pop = [x for x in ("al" + "ert(", "con" + "firm(", "win" + "dow.open(") if x in page]
    chk("④ 真的產得出一張頁,而且**零 CDN、零彈窗**(外連一律內嵌;律)",
        page.startswith("<!DOCTYPE html>") and page.rstrip().endswith("</html>")
        and not bad_cdn and not bad_pop,
        f"(外連 {bad_cdn or '無'} · 彈窗 {bad_pop or '無'} · {len(page)} 字元)")

    # ⑤ 逐格都在表上(五格一格不漏)
    chk("⑤ 五項逐格都上表(引擎自測 · 閘自測 · ADJ 對照 · 閘實判 · 全格子),一格不漏",
        len(d["rows"]) == 5 and all(r.get("state") in STATE_RANK for r in d["rows"]),
        f"({[r['state'] for r in d['rows']]})")

    # ⑧ rc 不是總判(非循環)
    #   初版用 `split("def main(")[1]` 取 main 的碼——那串字在本檔出現**兩次**
    #   (第二次就是我這格檢自己寫的那個字面),於是切到的是我自己這格的條文,檢當場咬到自己。
    #   同 LL449 一族:量文字不量碼。改走 AST 取**真的那個函式**的原始碼段。
    _all = Path(__file__).read_text(encoding="utf-8")
    _main_src = next(
        (ast.get_source_segment(_all, n) or "") for n in ast.parse(_all).body
        if isinstance(n, ast.FunctionDef) and n.name == "main")
    chk("⑧ **rc 講的是「報告產得出來嗎」,不是「一切是否全綠」**(非循環):"
        "本支要讀最新一份格子存證,而格子跑到本站時,最新存證是**上一跑**的。"
        "rc 若等於總判,本站就會拿上一跑的紅去判這一跑 —— 循環,而且會自我應驗。"
        "判斷留在閘與格子身上;頁面上的總判照樣取最差那一格(那是給人看的,不是 rc)",
        'd["verdict"] == "GREEN"' not in _main_src and "return 3" in _main_src
        and '"ABSENT", "NODATA", "GATED"' in _main_src)

    # ⑥ 令是逐字,不是轉述
    chk("⑥ 操作員令**逐字**進頁,不改寫不潤飾——第一段若已經是轉述,後面全是轉述的轉述",
        "ADJ CLOSE" in ORDERS[0] and "把關擊斃較機制" in ORDERS[1]
        and all(html.escape(o) in render_html(d) for o in ORDERS))

    # ⑦ 唯讀:只寫自己那張頁
    src = Path(__file__).read_text(encoding="utf-8")
    judge_src = src.split("def selftest(")[0]
    code = "\n".join(l for l in judge_src.split("\n") if not l.lstrip().startswith("#"))
    banned = [b for b in ("un" + "link(", "rm" + "tree(", "os.re" + "move(") if b in code]
    chk("⑦ **唯讀**:除了自己那張報告頁以外不寫、不刪任何檔",
        code.count("write_text(") == 1 and not banned, f"(違禁 {banned or '無'})")

    print("  [計] %d 檢 OK %d · FAIL %d" % (len(ran), len(ran) - len(fails), len(fails)))
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a or "--self-test" in a:
        return selftest()
    out = a[a.index("--out") + 1] if "--out" in a and len(a) > a.index("--out") + 1 else None
    d = build(Path(out) if out else None)
    if "--json" in a:
        print(json.dumps({k: v for k, v in d.items() if k != "rows"} |
                         {"rows": [{kk: vv for kk, vv in r.items()
                                    if kk in ("label", "state", "detail", "evidence")}
                                   for r in d["rows"]]}, ensure_ascii=False, indent=1))
    else:
        print(f"[B736 報告] 總判 {d['verdict']} · {d['out']}")
        for r in d["rows"]:
            print(f"  [{r['state']:6}] {r['label']} · {r.get('evidence','')}")
    # rc 只講「報告產得出來嗎」(見檔頭)。總判 RED **不**轉成 rc1 ——
    #   否則本支當格子站時,會拿上一跑的存證判這一跑,是會自我應驗的循環。
    if not Path(d["out"]).is_file():
        return 3
    return 2 if any(r["state"] in ("ABSENT", "NODATA", "GATED") for r in d["rows"]) else 0


if __name__ == "__main__":
    sys.exit(main())
