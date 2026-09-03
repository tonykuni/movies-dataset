#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA MasterControl / DeckServer 零外網契約測試(b305 Codex 原件 adapt 版;批338:路徑改尾版律,原件於 intake 零觸碰)。

測試不改寫 repository 內的 HTML；所有產生器寫檔驗證都隔離在暫存目錄。
瀏覽器幾何、焦點、佇列時序與 file:// 降級另由 Playwright 驗證。
"""
from __future__ import annotations

import errno
import hashlib
import http.client
import importlib.util
import inspect
import io
import json
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from html.parser import HTMLParser
from pathlib import Path, PureWindowsPath
from unittest import mock


REG = Path(__file__).resolve().parent.parent  # tests/ 下一層(批338 收容 adapt 版)
VIA = REG.parent.parent
MANAGER_PATH = sorted(VIA.glob("VIA_SYSTEM_MANAGER_v*.py"))[-1]  # 尾版律(原件寫死 v0108)
MASTER_HTML = (VIA / "supportive modules" / "ui_support" /
               "VIA_UI_MasterControl_v0100.html")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"無法載入模組：{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def latest_deck_path() -> Path:
    hits = sorted(REG.glob("CGC_MDL095_DeckServer_v*.py"))
    if not hits:
        raise RuntimeError("DeckServer 正本缺失")
    return hits[-1]


class ContractParser(HTMLParser):
    """擷取驗收需要的 DOM 契約，不取代真瀏覽器測試。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.roles: list[str] = []
        self.labels: set[str] = set()

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"])
        if values.get("role"):
            self.roles.append(values["role"])
        if tag == "label" and values.get("for"):
            self.labels.add(values["for"])


def normalized_generated_page(page: str) -> str:
    """排除唯一非決定性欄位，讓 committed artifact 可做 freshness 比對。"""
    # 批338b(CI 實錄):Plotly 就緒分頁依 VIA_UI_StdDashboard(日更再生類,不入 git)在位與否分支,
    # 追蹤頁與 runner 產出必然不同→比對前中性化該分頁(其餘全文嚴格比對)
    import re as _re
    page = _re.sub(r'(<section class="tab-panel" id="panel-plotly"[^>]*>).*?(</section>)',
                   r"\1[PLOTLY-PANEL-NEUTRALIZED]\2", page, flags=_re.S)
    page = re.sub(
        r'(<div class="snapshot"><span>畫面產生時間</span><b>).*?(</b></div>)',
        r"\1__GENERATED_AT__\2", page, flags=re.S)
    return page.replace("\r\n", "\n")


class MasterControlContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path_snapshot = sys.path[:]
        cls.addClassCleanup(
            lambda: sys.path.__setitem__(slice(None), path_snapshot))
        cls.manager = load_module(MANAGER_PATH, "via_manager_v0108_contract")
        cls.deck_path = latest_deck_path()
        cls.deck = load_module(cls.deck_path, "via_deck_contract")
        cls.atlas = cls.manager.do_list(do_print=False)
        cls.tasks = cls.deck.task_registry()
        cls.page = cls.manager._build_page(cls.atlas, cls.tasks)

    def test_01_v0114_inventory_counts_and_unique_ids(self):
        self.assertRegex(self.deck_path.name, r"_v01\d\d\.py$")  # 批338:尾版律(原件 v0114)
        engines = self.manager._engine_rows(self.atlas)
        modules = self.manager._module_rows(self.atlas)
        # 批338:盤點數只增不減(原件寫死 32/194/85);唯一性維持嚴格
        self.assertGreaterEqual(len(self.tasks), 32)
        self.assertGreaterEqual(len(engines), 194)
        self.assertEqual(len({row["identifier"] for row in engines}), len(engines))
        self.assertGreaterEqual(sum(row["state_class"] == "surveyed" for row in engines), 76)
        self.assertGreaterEqual(sum(row["state_class"] == "retired" for row in engines), 118)
        self.assertGreaterEqual(len(modules), 85)

    def test_02_dom_ids_roles_labels_and_drawer_controls(self):
        parser = ContractParser()
        parser.feed(self.page)
        self.assertEqual(len(parser.ids), len(set(parser.ids)))
        self.assertEqual(parser.roles.count("tab"), 7)
        self.assertEqual(parser.roles.count("tabpanel"), 7)
        self.assertTrue({"task", "codes", "dateStart", "dateEnd",
                         "categories", "catalogSearch"}.issubset(parser.labels))
        self.assertIn('id="railBackdrop"', self.page)
        self.assertRegex(
            self.page,
            r'id="railToggle"[^>]+aria-controls="controlRail"[^>]+'
            r'aria-label="[^"]+"[^>]+aria-expanded="true"')

    def test_03_all_operational_controls_are_in_left_rail(self):
        rail = self.page[self.page.index('<aside class="control-rail"'):
                         self.page.index("</aside>")]
        expected = (
            "task", "codes", "dateStart", "dateEnd", "categories",
            "runOneButton", "pingButton", "saveParamsButton",
            "resetParamsButton", "runBatchButton", "drop", "filePicker",
            "catalogSearch", "showTechnicalIds",
        )
        for element_id in expected:
            self.assertIn(f'id="{element_id}"', rail)
        self.assertNotIn('id="task"', self.page[self.page.index("<main "):])

    def test_04_task_metadata_drives_minimal_inputs(self):
        for token in ('data-codes="true"', 'data-range="true"',
                      'data-cats="true"', "updateParameterVisibility",
                      "selectedTaskContract", "syncInputSummary"):
            self.assertIn(token, self.page)

    def test_05_primary_names_hide_program_identifiers(self):
        self.assertGreaterEqual(len(self.manager.TASK_FORMAL_NAMES), 32)  # 批338:任務冊只增不減(原件寫死 32)
        for key, meta in self.tasks.items():
            label = self.manager._formal_task_name(key, meta.get("zh", key))
            self.assertNotEqual(label.casefold(), key.casefold())
            self.assertFalse(label.casefold().startswith(key.casefold() + " "))
        for table_id, expected in (("engineTable", 194), ("moduleTable", 85)):  # 批338:只增不減=下限
            match = re.search(
                rf'<table[^>]+id="{table_id}".*?</table>', self.page, re.S)
            self.assertIsNotNone(match)
            names = [re.sub(r"<.*?>", "", value)
                     for value in re.findall(r'<tr[^>]*><td>(.*?)</td>',
                                             match.group(), re.S)]
            self.assertGreaterEqual(len(names), expected)
            self.assertFalse([name for name in names if re.search(
                r"(?:ENG|MDL)\d+|[A-Za-z]{2,}_[A-Za-z0-9_]+", name)])
        candidate_ids = re.findall(r"候核序號 ([EM]\d{3})", self.page)
        self.assertTrue(candidate_ids)
        self.assertEqual(len(candidate_ids), len(set(candidate_ids)),
                         "每個未核定名稱必須有唯一 E/M 候核序號")

    def test_06_fixed_shell_drawer_and_responsive_contract(self):
        css = self.manager.MCSS
        js = self.manager.APPJS
        for token in (".app-header{position:fixed", ".app-footer{position:fixed",
                      ".control-rail{position:fixed", "[hidden]{display:none",
                      "@media(max-width:768px)", "overflow-x:hidden",
                      ":focus-visible", ".rail-backdrop"):
            self.assertIn(token, css)
        self.assertIn("inert", js)
        self.assertIn("Escape", js)
        self.assertIn("railBackdrop", js)

    def test_07_status_rendering_is_encoded_and_truthful(self):
        self.assertNotIn("innerHTML", self.manager.STATUSJS)
        self.assertNotIn("innerHTML", self.manager.DROPJS)
        self.assertIn("textContent", self.manager.STATUSJS)
        self.assertIn("連線尚未檢測", self.page)
        self.assertNotIn("MANAGER · LIVE", self.page)
        self.assertIn("資料過期", self.manager.STATUSJS)
        self.assertIn("markStatusRowsStale", self.manager.STATUSJS)

    def test_08_mutations_use_json_post_csrf_and_run_id(self):
        app = self.manager.APPJS
        drop = self.manager.DROPJS
        self.assertIn('<meta name="via-csrf" content="">', self.page)
        self.assertNotIn('API_BASE+"/run?"', app)
        self.assertRegex(app, r'/run["\']\s*,\s*\{[^}]*method\s*:\s*["\']POST')
        self.assertIn("X-VIA-CSRF", app)
        self.assertIn("application/json", app)
        self.assertIn("run_id", app)
        self.assertIn("X-VIA-CSRF", drop)
        self.assertIn("file:", app)
        self.assertIn("preview", app.lower())

    def test_09_plotly_is_local_or_honestly_degraded(self):
        has_local = 'id="plotlyFrame"' in self.page
        has_empty = 'id="plotlyEmpty"' in self.page
        self.assertNotEqual(has_local, has_empty)
        self.assertNotRegex(self.page, r'<(?:script|link)[^>]+https?://')
        if has_empty:
            self.assertIn("本頁不顯示模擬行情或假圖", self.page)

    def test_10_generator_writes_only_to_temporary_directory(self):
        old_out = self.manager.OUT
        old_template = self.manager.TEMPLATE_OUT
        try:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.manager.OUT = root / "MasterControl.html"
                self.manager.TEMPLATE_OUT = root / "EditableTemplate.html"
                self.assertEqual(self.manager.do_template(force=True), 0)
                self.manager.TEMPLATE_OUT.write_text(
                    self.manager.TEMPLATE_OUT.read_text(encoding="utf-8") +
                    "\n<!-- USER-DESIGN-PRESERVE -->\n", encoding="utf-8")
                before = hashlib.sha256(
                    self.manager.TEMPLATE_OUT.read_bytes()).hexdigest()
                self.assertEqual(self.manager.do_ui(open_after=False), 0)
                after = hashlib.sha256(
                    self.manager.TEMPLATE_OUT.read_bytes()).hexdigest()
                self.assertEqual(before, after)
                self.assertTrue(self.manager.OUT.exists())
                self.assertIn("USER-DESIGN-PRESERVE",
                              self.manager.TEMPLATE_OUT.read_text(encoding="utf-8"))
        finally:
            self.manager.OUT = old_out
            self.manager.TEMPLATE_OUT = old_template

    def test_11_committed_page_matches_generator(self):
        committed = MASTER_HTML.read_text(encoding="utf-8")
        self.assertEqual(normalized_generated_page(committed),
                         normalized_generated_page(self.page),
                         "tracked MasterControl 與正主管理器輸出不同步")

    def test_12_inline_javascript_parses_without_open_temp_handle(self):
        scripts = re.findall(r"<script>(.*?)</script>", self.page, re.S)
        self.assertEqual(len(scripts), 1)
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "master-control-inline.js"
            script.write_text(scripts[0], encoding="utf-8")
            result = subprocess.run(["node", "--check", str(script)],
                                    capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_13_sync_preserves_worktree_and_status_selftest_is_isolated(self):
        powershell = (VIA / "VIA.ps1").read_text(encoding="utf-8")
        self.assertNotRegex(
            powershell, r"git\s+-C\s+\$VIA\s+(?:checkout\s+--\s+\"supportive|reset\s+--hard|clean)\b")  # 批338:禁整夾/硬重置/清除;檔級再生頁還原(排除可編輯模板)=許
        self.assertIn("stash push --include-untracked", powershell)
        self.assertIn("stash apply --index $stashHash", powershell)

        sync_path = sorted(REG.glob("CGC_MDL096_SyncStatus_v*.py"))[-1]
        sync = load_module(sync_path, "via_sync_status_contract")
        gather_source = inspect.getsource(sync.gather_git)
        self.assertNotRegex(gather_source, r'["\'](?:checkout|pull)["\']')
        self.assertIn('"fetch"', gather_source)
        before = (hashlib.sha256(sync.OUT.read_bytes()).hexdigest()
                  if sync.OUT.exists() else None)
        # 此處只驗證 selftest 的寫入隔離；其產品斷言由 SyncStatus 自己負責。
        with redirect_stdout(io.StringIO()):
            sync.selftest()
        after = (hashlib.sha256(sync.OUT.read_bytes()).hexdigest()
                 if sync.OUT.exists() else None)
        self.assertEqual(before, after, "SyncStatus selftest 不得改寫 tracked OUT")

    def test_14_deck_v0114_source_contract(self):
        source = self.deck_path.read_text(encoding="utf-8")
        self.assertNotIn("Access-Control-Allow-Origin", source)
        self.assertIn("/master", inspect.getsource(self.deck.H.do_GET))
        self.assertIn("X-VIA-CSRF", source)
        self.assertIn("CSRF_TOKEN", source)
        self.assertIn('"run_id"', inspect.getsource(self.deck.start_task))
        self.assertIn('"run_id"', inspect.getsource(self.deck.status_all))

    def test_15_windows_intake_names_and_hardlink_failure_are_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            intake_root = root / "reserved"
            for name in ("AUX...txt", "COM¹.txt", "LPT².log", "CON",
                         "con.txt", "NUL.tar.gz"):
                self.assertTrue(PureWindowsPath(name).is_reserved(), name)
                receipt = self.deck._intake_save(name, b"blocked", intake_root)
                self.assertFalse(receipt.get("ok"), name)
                self.assertEqual(receipt.get("kind"), "invalid_name", name)
            self.assertFalse(intake_root.exists(),
                             "保留裝置名必須在建立收件資料夾前拒絕")
            self.assertFalse(PureWindowsPath(
                self.deck._safe_filename("COM10.txt")).is_reserved())

            publish_root = root / "hardlink-unsupported"
            failure = OSError(errno.ENOTSUP, "contract: hard-link unsupported")
            with mock.patch.object(self.deck.os, "link", side_effect=failure):
                receipt = self.deck._intake_save(
                    "safe.txt", b"must-not-publish", publish_root)
            self.assertFalse(receipt.get("ok"))
            self.assertEqual(receipt.get("kind"), "publish_failed")
            self.assertIsInstance(receipt.get("err"), str)
            self.assertEqual(list(publish_root.iterdir()), [],
                             "hard-link 不支援時不得留下半成品")


class DeckHTTPContractTests(unittest.TestCase):
    """用暫存 MasterControl 與假 start_task 驗證 HTTP 安全封套。"""

    @classmethod
    def setUpClass(cls):
        path_snapshot = sys.path[:]
        cls.addClassCleanup(
            lambda: sys.path.__setitem__(slice(None), path_snapshot))
        cls.deck = load_module(latest_deck_path(), "via_deck_http_contract")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.master = Path(self.temporary.name) / "MasterControl.html"
        self.master.write_text(
            '<!doctype html><html><head><meta name="via-csrf" content="">'
            '</head><body>contract</body></html>', encoding="utf-8")
        self.original = {
            "MASTER_UI": self.deck.MASTER_UI,
            "CSRF_TOKEN": self.deck.CSRF_TOKEN,
            "start_task": self.deck.start_task,
        }
        self.addCleanup(self._restore_deck_globals)
        self.calls = []

        def fake_start_task(*args, **kwargs):
            self.calls.append((args, kwargs))
            return {
                "ok": True,
                "run_id": "run-contract-001",
                "accepted_params": dict(zip(
                    ("task", "codes", "start", "end", "cats"), args)),
            }

        self.deck.MASTER_UI = self.master
        self.deck.CSRF_TOKEN = "contract-csrf-token"
        self.deck.start_task = fake_start_task
        self.server = self.deck.ThreadingHTTPServer(("127.0.0.1", 0), self.deck.H)
        self.thread = None
        self.addCleanup(self._close_server)
        self.port = self.server.server_address[1]
        self.origin = f"http://127.0.0.1:{self.port}"
        self.server.trusted_origin = self.origin
        self.server.csrf_token = "contract-csrf-token"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def _restore_deck_globals(self):
        for key, value in self.original.items():
            setattr(self.deck, key, value)

    def _close_server(self):
        if self.thread is not None and self.thread.is_alive():
            self.server.shutdown()
        self.server.server_close()
        if self.thread is not None:
            self.thread.join(timeout=3)
            self.assertFalse(self.thread.is_alive(), "HTTP 測試執行緒未停止")

    def request(self, method, path, payload=None, headers=None):
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request_headers = dict(headers or {})
        if body is not None:
            request_headers.setdefault("Content-Type", "application/json")
            request_headers["Content-Length"] = str(len(body))
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request(method, path, body=body, headers=request_headers)
            response = connection.getresponse()
            raw = response.read()
            return response.status, dict(response.getheaders()), raw
        finally:
            connection.close()

    def trusted_headers(self):
        return {
            "Origin": self.origin,
            "Sec-Fetch-Site": "same-origin",
            "X-VIA-CSRF": "contract-csrf-token",
        }

    def test_20_master_injects_token_and_security_headers(self):
        source_before = self.master.read_bytes()
        status, headers, raw = self.request("GET", "/master")
        text = raw.decode("utf-8")
        self.assertEqual(status, 200)
        self.assertIn('<meta name="via-csrf" content="contract-csrf-token">', text)
        self.assertNotIn('<meta name="via-csrf" content="">', text)
        self.assertIn("Content-Security-Policy", headers)
        self.assertNotIn("Access-Control-Allow-Origin", headers)
        self.assertEqual(self.master.read_bytes(), source_before,
                         "權杖只能注入 HTTP 回應副本，不得改寫 HTML 正本")

    def test_21_get_run_and_cross_site_preflight_are_rejected(self):
        headers = {}
        for path in sorted(self.deck.BLOCKED_MUTATION_GETS):
            status, headers, _ = self.request("GET", path + "?probe=1")
            self.assertEqual(status, 405, path)
        self.assertEqual(self.calls, [])
        self.assertNotIn("Access-Control-Allow-Origin", headers)
        status, _, _ = self.request("OPTIONS", "/run")
        self.assertEqual(status, 403)
        self.assertEqual(self.calls, [])

    def test_22_post_run_requires_origin_and_csrf(self):
        payload = {"task": "boot"}
        status, _, _ = self.request("POST", "/run", payload)
        self.assertEqual(status, 403)
        bad = self.trusted_headers()
        bad["Origin"] = "https://attacker.invalid"
        status, _, _ = self.request("POST", "/run", payload, bad)
        self.assertEqual(status, 403)
        bad = self.trusted_headers()
        bad["X-VIA-CSRF"] = "wrong-token"
        status, _, _ = self.request("POST", "/run", payload, bad)
        self.assertEqual(status, 403)
        bad = self.trusted_headers()
        bad.pop("Sec-Fetch-Site")
        status, _, _ = self.request("POST", "/run", payload, bad)
        self.assertEqual(status, 403)
        bad = self.trusted_headers()
        bad["Sec-Fetch-Site"] = "cross-site"
        status, _, _ = self.request("POST", "/run", payload, bad)
        self.assertEqual(status, 403)
        status, _, _ = self.request(
            "POST", "/run?legacy=boot", payload, self.trusted_headers())
        self.assertEqual(status, 400)
        status, _, _ = self.request(
            "GET", "/master", headers={"Host": "attacker.invalid"})
        self.assertEqual(status, 421)
        self.assertEqual(self.calls, [])

    def test_23_valid_post_preserves_parameters_and_run_id(self):
        payload = {"task": "global", "codes": "",
                   "start": "2026-08-01", "end": "2026-08-31",
                   "cats": "idx,etf"}
        status, headers, raw = self.request(
            "POST", "/run", payload, self.trusted_headers())
        result = json.loads(raw)
        self.assertEqual(status, 202)
        self.assertEqual(result["run_id"], "run-contract-001")
        self.assertEqual(result["accepted_params"], payload)
        self.assertEqual(set(result), {"ok", "run_id", "accepted_params"})
        self.assertEqual(len(self.calls), 1)
        args, _ = self.calls[0]
        self.assertEqual(args, ("global", "", "2026-08-01",
                                "2026-08-31", "idx,etf"))
        self.assertNotIn("Access-Control-Allow-Origin", headers)


if __name__ == "__main__":
    unittest.main(verbosity=2)
