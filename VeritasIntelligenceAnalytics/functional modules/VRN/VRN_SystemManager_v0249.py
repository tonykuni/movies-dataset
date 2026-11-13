#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN-2 SystemManager v0249 — 薄尾(前版 = v0248)。發布層接進主流程與 U/I(操作員 2026-10-27)。

① 輸出冊之後自動發布:VRN2_Publish(最新版)--publish → 累計 parquet / CSV(UTF-8 BOM)/ Google Sheet(啟用時)/ 雲端同步夾 · 結果一行進貼包 · 不擋完成
② 左側面板加「發布設定」區:格式勾選 · 選擇憑證檔 / 雲端夾(Windows 選擇器)· 試算表網址貼上即存 · 測試連線 · 立即發布 · 顯示目前設定與上次結果(靜態頁 · 走 vrn2://)
③ 容量 / 編碼提醒直接顯示在面板(Excel 1,048,576 列 · Google Sheet 1,000 萬格 · CSV UTF-8 BOM)
不改 v0248 / 另一線任何函式。
"""
from __future__ import annotations

import hashlib
import html
import importlib.util
import inspect
import json
import subprocess
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "v0249"
DISPLAY_NAME = "VRN-2 SystemManager"
PRIOR_NAME = "VRN_SystemManager_v0248.py"
PRIOR_PATH = HERE / PRIOR_NAME
if not PRIOR_PATH.exists():
    raise FileNotFoundError("前版 %s 不在 · v0249 不接" % PRIOR_NAME)
_spec = importlib.util.spec_from_file_location("vrn_manager_prior_for_v0249", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _name, _value in vars(PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value


def _rebind(fn):
    return types.FunctionType(fn.__code__, globals(), fn.__name__, fn.__defaults__, fn.__closure__)


def _pub_engine():
    c = sorted(HERE.glob("VRN2_Publish_v[0-9][0-9][0-9][0-9].py"))
    return c[-1] if c else None


def _pub_cfg() -> dict:
    try:
        return json.loads((HERE / "SSOT" / "VRN2_Publish_Config_v0100.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def publish_section_html(v2) -> str:
    """② 發布設定區(靜態 · 按鈕走 vrn2:// · 網址輸入由 JS 組成 vrn2://publish-config?google.spreadsheet=…)。"""
    c = _pub_cfg(); f = c.get("formats") or {}; g = c.get("google") or {}; last = c.get("last_result") or {}
    ui_txt = ""
    try:
        ui_txt = (Path(v2) / "publish" / "VRN2_Publish_UI_latest.txt").read_text(encoding="utf-8")[-400:]
    except Exception:  # noqa: BLE001
        pass
    b = "display:block;margin:4px 0;padding:6px 8px;border:1px solid #cbd5e1;border-radius:6px;background:#f8fafc;color:#111;text-decoration:none;font-size:12px"
    chk = lambda k: "checked" if f.get(k) else ""
    return ("<div style='font-weight:700;margin:10px 0 6px'>發布設定(累計 → 格式 → 雲端)</div>"
            "<div style='font-size:12px'><label><input type='checkbox' id='pf_parquet' %s> parquet(累計 · 推薦)</label><br>"
            "<label><input type='checkbox' id='pf_csv' %s> CSV(UTF-8 BOM · Excel 上限 1,048,576 列)</label><br>"
            "<label><input type='checkbox' id='pf_gs' %s> Google Sheet(1,000 萬格上限 · 需憑證 + 分享)</label></div>"
            "<a style=\"%s\" href='#' onclick=\"location.href='vrn2://publish-config?formats.parquet='+document.getElementById('pf_parquet').checked+'&formats.csv='+document.getElementById('pf_csv').checked+'&formats.google_sheet='+document.getElementById('pf_gs').checked;return false\">💾 存格式設定</a>"
            "<a style=\"%s\" href='vrn2://publish-pick-cred'>🔑 選擇 Google 憑證檔(服務帳戶 JSON)</a>"
            "<input id='pf_sheet' placeholder='貼上試算表網址' value=\"%s\" style='width:100%%;font-size:12px;padding:5px;border:1px solid #cbd5e1;border-radius:6px;margin:4px 0'>"
            "<a style=\"%s\" href='#' onclick=\"location.href='vrn2://publish-config?google.spreadsheet='+encodeURIComponent(document.getElementById('pf_sheet').value)+'&formats.google_sheet=true';return false\">📎 存試算表網址</a>"
            "<a style=\"%s\" href='vrn2://publish-pick-folder'>☁ 加入雲端同步夾(OneDrive / Google Drive / Dropbox …)</a>"
            "<a style=\"%s\" href='vrn2://publish-test'>🧪 測試連線(dry)</a>"
            "<a style=\"%s;background:#e8f5e9;font-weight:700\" href='vrn2://publish'>⬆ 立即發布</a>"
            "<div style='color:#6b7280;font-size:11px;margin-top:4px'>憑證 %s · 試算表 %s · 上次 %s</div>"
            "<pre style='white-space:pre-wrap;font-size:10px;color:#475569;max-height:90px;overflow:auto'>%s</pre>"
            "<div style='color:#6b7280;font-size:11px'>Google 三步:① Cloud 建服務帳戶下載 JSON ② 試算表共用給 JSON 的 client_email ③ 上面選檔 + 貼網址 → 測試 → 發布。重跑時自動累計(去重保留最新 · 原值不刪)。</div>") % (
        chk("parquet"), chk("csv"), chk("google_sheet"), b, b, html.escape(g.get("spreadsheet") or "", quote=True), b, b, b, b,
        html.escape(Path(g.get("credentials_json") or "").name or "未設", quote=True), "已填" if g.get("spreadsheet") else "未填", html.escape(json.dumps(last, ensure_ascii=False)[:120], quote=True), html.escape(ui_txt))


def _ui_panel_html(v2):
    base = PRIOR._ui_panel_html(v2)
    marker = "<div style='color:#6b7280;font-size:11px;margin-top:8px'>按鈕走 vrn2://"
    sec = publish_section_html(v2)
    return base.replace(marker, sec + marker, 1) if marker in base else base + sec


def _out_books(res, acc, st, v2):
    basic, fin, summ, gaps, made = PRIOR._out_books(res, acc, st, v2)
    try:
        eng = _pub_engine()
        if eng:
            r = subprocess.run([sys.executable, "-W", "ignore", str(eng), "--publish", "--v2", str(v2)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800, cwd=str(HERE))
            line = next((l for l in (r.stdout + r.stderr).splitlines() if l.strip().startswith("[計] 發布")), "")
            print("  " + (line.strip() if line else "[計] 發布未回報 rc %d" % r.returncode)[:400], flush=True)
        else:
            print("  [計] 發布引擎未落地(VRN2_Publish_v####.py)", flush=True)
    except Exception as exc:  # noqa: BLE001
        print("  [計] 發布未完成 %s" % type(exc).__name__, flush=True)
    return basic, fin, summ, gaps, made


def completion(*args, **kwargs):
    result = PRIOR.completion(*args, **kwargs)
    try:
        result["manager"] = "%s %s" % (DISPLAY_NAME, TAG)
    except Exception:  # noqa: BLE001
        pass
    return result


_MY_SIG = hashlib.sha1(inspect.getsource(publish_section_html).encode("utf-8")).hexdigest()[:12]
for _n in ("_base_acceptance", "_acc_parallel", "_acc_shard_main", "_acc_one", "_acc_one_core", "_acc_basic", "acceptance", "_acc_sig", "_native_vrn2", "vrn2", "_idem_check", "main", "_success_register", "_out_html"):
    globals()[_n] = _rebind(getattr(PRIOR, _n))


def selftest() -> int:
    ok = [0, 0]
    def chk(name, cond):
        ok[0 if cond else 1] += 1
        print("  [%s] %s" % ("OK" if cond else "FAIL", name))
    import tempfile
    h = publish_section_html(Path(tempfile.mkdtemp()))
    chk("⓪ v0249 發布設定區:5 個 vrn2:// 動作 %s · 容量提醒 %s" % (all(x in h for x in ("vrn2://publish-pick-cred", "vrn2://publish-pick-folder", "vrn2://publish-test", "vrn2://publish'", "publish-config")), "1,048,576" in h and "1,000 萬格" in h),
        all(x in h for x in ("vrn2://publish-pick-cred", "vrn2://publish-pick-folder", "vrn2://publish-test", "vrn2://publish'", "publish-config")) and "1,048,576" in h)
    chk("⓪ v0249 綁定:vrn2 內部 _out_books / _ui_panel_html / completion 走本版 %s %s %s" % (_native_vrn2.__globals__["_out_books"] is _out_books, _native_vrn2.__globals__["_ui_panel_html"] is _ui_panel_html, _native_vrn2.__globals__["completion"] is completion),
        _native_vrn2.__globals__["_out_books"] is _out_books and _native_vrn2.__globals__["_ui_panel_html"] is _ui_panel_html and _native_vrn2.__globals__["completion"] is completion)
    chk("⓪ v0249 發布引擎 %s" % (_pub_engine().name if _pub_engine() else "未落地"), bool(_pub_engine()))
    import os
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") != "1":
        print("          ── 前版鏈(v0248)自測 ──")
        rc = PRIOR.selftest()
        chk("③ 前版鏈 v0248 自測 rc %s" % rc, rc == 0)
    p, f = ok
    print("[計] VRN-2 SystemManager v0249(VRN_SystemManager_v0249.py)自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main(sys.argv[1:]))
