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

import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENGINE_PATH = PROJECT_ROOT / "functional modules" / "VRN" / "engine" / "VRN_PanoramaProbe.py"
CATALOG_TS = PROJECT_ROOT / "src" / "lib" / "via" / "catalog.ts"


def def_load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PROBE = def_load_module("vrn_panorama_probe", ENGINE_PATH)
CATALOG_TS = getattr(PROBE, "APP_ROOT", PROJECT_ROOT) / "src" / "lib" / "via" / "catalog.ts"   # 母倉:讀收容副本(批728)
ROSTER = PROBE.def_load_roster()
KNOWLEDGE = PROBE.Knowledge()
ENV = PROBE.def_probe_environment()


class RosterContractTests(unittest.TestCase):
    def test_roster_is_the_mother_64(self) -> None:
        self.assertEqual(len(ROSTER), 64)
        self.assertEqual(len(set(ROSTER)), 64)
        self.assertIn("華南投顧-2637-慧洋-KY-1141202.pdf", ROSTER)

    def test_stage_table_mirrors_console_pipeline(self) -> None:
        text = CATALOG_TS.read_text(encoding="utf-8")
        pairs = re.findall(r'\{ id: "(S\d{2})", name: "([A-Z_]+)", title: "([^"]+)" \}', text)
        self.assertEqual([(p[0], p[1], p[2]) for p in pairs], list(PROBE.STAGES))

    def test_known_names_mirror_typescript_expectations(self) -> None:
        a = PROBE.def_parse_contract("華南投顧-2637-慧洋-KY-1141202.pdf", KNOWLEDGE)
        self.assertEqual(a["ticker"], "2637")
        self.assertEqual(a["report_date"], "2025-12-02")
        self.assertEqual(a["date_kind"], "roc7")
        self.assertEqual(a["broker_abbr"], "HNSC")
        b = PROBE.def_parse_contract("3014TT-20231005.pdf", KNOWLEDGE)
        self.assertEqual(b["ticker"], "3014")
        self.assertEqual(b["bloomberg"], "3014 TT")
        self.assertTrue(b["ticker_recovered"])
        c = PROBE.def_parse_contract("瑞基(4171,NR_未評等)-CTBC251208.pdf", KNOWLEDGE)
        self.assertEqual(c["ticker"], "4171")
        self.assertEqual(c["report_date"], "2025-12-08")
        self.assertEqual(c["broker_abbr"], "CTBC")
        self.assertEqual(c["rating_cat"], "NOT_RATED")
        d = PROBE.def_parse_contract("【國泰證期研究部】神達(3706 TT)-初次評等買進(+30.4_)-大顯神威，營運騰達-20250822.pdf", KNOWLEDGE)
        self.assertEqual(d["ticker"], "3706")
        self.assertEqual(d["ticker_kind"], "bloomberg")
        self.assertEqual(d["report_date"], "2025-08-22")
        self.assertEqual(d["report_type"], "INITIATION")
        self.assertEqual(d["rating_cat"], "BUY")
        e = PROBE.def_parse_contract("晶心科(6533,N,中立)-CTBC251208.pdf", KNOWLEDGE)
        self.assertEqual(e["rating_cat"], "HOLD")
        f = PROBE.def_parse_contract("投資早報251209.pdf", KNOWLEDGE)
        self.assertEqual(f["report_date"], "2025-12-09")
        self.assertTrue(f["non_stock"])

    def test_year_band_tokens_are_not_tickers(self) -> None:
        for name in (
            "第一場 2026年投資大趨勢 - 華南投顧 -1141201.pdf",
            "第二場 2026海外投資展望 - 華南永昌海外商品部.pdf",
            "第三場 AI潮流下展望2026半導體產業趨勢 - 陳子昂.pdf",
        ):
            contract = PROBE.def_parse_contract(name, KNOWLEDGE)
            self.assertEqual(contract["ticker"], "", name)
            self.assertTrue(contract["non_stock"], name)
        ordinal = PROBE.def_parse_contract("第一場 2026年投資大趨勢 - 華南投顧 -1141201.pdf", KNOWLEDGE)
        self.assertEqual(ordinal["broker_abbr"], "HNSC")

    def test_risk_distribution_stock_green_nonstock_yellow(self) -> None:
        risks = [PROBE.def_parse_contract(n, KNOWLEDGE)["risk"] for n in ROSTER]
        self.assertEqual(risks.count("RED"), 0)
        self.assertGreaterEqual(risks.count("GREEN"), 30)
        self.assertGreaterEqual(risks.count("YELLOW"), 8)
        morning = PROBE.def_parse_contract("20251205兆豐晨會報告(一)-當日新聞與重要訊息評論.pdf", KNOWLEDGE)
        self.assertTrue(morning["non_stock"])
        self.assertEqual(morning["broker_abbr"], "MKC")
        self.assertEqual(PROBE.def_parse_contract("華南投顧-2606-裕民-1141202.pdf", KNOWLEDGE)["broker_abbr"], "HNSC")

    def test_foreign_prefix_brokers(self) -> None:
        expect = {
            "GS-1590 20251203.pdf": "GS",
            "MS-3665 20251202.pdf": "MS",
            "JP-2330 20250718.pdf": "JPM",
            "Citi-3231 20250604.pdf": "CITI",
            "CLST-6669 20251001.pdf": "CLSA",
            "Daiwa-6278 20260521.pdf": "DAI",
            "MQ-1560 20260520.pdf": "MAQ",
            "UBS-Asia Hardware Insights 20251205.pdf": "UBS",
        }
        for name, abbr in expect.items():
            self.assertEqual(PROBE.def_parse_contract(name, KNOWLEDGE)["broker_abbr"], abbr, name)


class StageTests(unittest.TestCase):
    def test_without_bytes_every_file_is_blocked_at_s02_but_contract_runs(self) -> None:
        names = ROSTER[:6]
        report = PROBE.def_run(names, None, ENV, KNOWLEDGE, "unit")
        self.assertEqual(report["count"], 6)
        for item in report["files"]:
            self.assertEqual(item["stuck_step"], "S02")
            self.assertEqual(item["stuck_kind"], "BLOCKED")
            self.assertEqual(item["stages"]["S07"]["status"], "SKIP")
            self.assertEqual(len(item["letters"]), 10)
        first = next(f for f in report["files"] if f["name"] == "華南投顧-2637-慧洋-KY-1141202.pdf")
        self.assertIn("2637", first["stages"]["S06"]["detail"])
        codes = [rc["code"] for rc in report["root_causes"]]
        self.assertIn("RC1_NO_BYTES", codes)
        self.assertIn("RC6_NLP_GATE", codes)
        self.assertEqual(report["verdict"], "AMBER")

    def test_bytes_change_s02_s04_and_dedup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            good = "GS-2317 20251205.pdf"
            twin = "GS-2317 20251205 (copy).pdf"
            zero = "MS-2308 20251128.pdf"
            fake = "JP-2330 20250718.pdf"
            memo = "華南投顧-3038-全台-Memo-20251209.docx"
            (root / good).write_bytes(b"%PDF-1.4\n%fake body\n" * 10)
            (root / twin).write_bytes(b"%PDF-1.4\n%fake body\n" * 10)
            (root / zero).write_bytes(b"")
            (root / fake).write_bytes(b"hello, not a pdf")
            (root / memo).write_bytes(b"PK\x03\x04" + b"\x00" * 64)
            names = [good, twin, zero, fake, memo]
            report = PROBE.def_run(names, root, ENV, KNOWLEDGE, "unit")
            by_name = {f["name"]: f for f in report["files"]}
            self.assertEqual(by_name[good]["stages"]["S02"]["status"], "OK")
            self.assertEqual(by_name[good]["stages"]["S04"]["status"], "OK")
            self.assertEqual(by_name[twin]["stages"]["S03"]["status"], "WARN")
            self.assertIn("dupOf", by_name[twin]["stages"]["S03"]["detail"])
            self.assertEqual(by_name[zero]["stages"]["S02"]["status"], "FAIL")
            self.assertEqual(by_name[zero]["stuck_step"], "S02")
            self.assertEqual(by_name[fake]["stages"]["S04"]["status"], "FAIL")
            self.assertEqual(by_name[fake]["stuck_step"], "S04")
            self.assertIn("markitdown", by_name[memo]["stages"]["S04"]["detail"])
            self.assertEqual(report["verdict"], "RED")
            self.assertEqual(report["root_causes"][0]["code"], "RC0_FAIL")
            self.assertNotIn("RC1_NO_BYTES", [rc["code"] for rc in report["root_causes"]])

    def test_json_html_and_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            listing = root / "names.txt"
            listing.write_text("\n".join(ROSTER[:3]) + "\n", encoding="utf-8")
            out_json = root / "out.json"
            out_html = root / "out.html"
            code = PROBE.main(["--names", str(listing), "--json", str(out_json), "--html", str(out_html), "--quiet"])
            self.assertEqual(code, 0)
            payload = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["count"], 3)
            self.assertEqual([s["id"] for s in payload["stages"]], list(PROBE.STAGE_IDS))
            page = out_html.read_text(encoding="utf-8")
            for name in ROSTER[:3]:
                self.assertIn(name, page)
            text = PROBE.def_render_console(payload)
            self.assertIn("逐件矩陣", text)

    def test_environment_probe_reports_repo_facts(self) -> None:
        self.assertEqual(ENV["vrn_tree"], "PRESENT")
        self.assertEqual(ENV["modules"]["MDL006"]["status"], "PRESENT")
        self.assertEqual(ENV["modules"]["MDL006"]["syntax"], "OK")
        self.assertIn("MDL003", ENV["modules"])
        self.assertIn("markitdown", ENV["deps"])
        self.assertIn("bridge_marker", ENV["accel"])
        self.assertEqual(ENV["ssot"]["VRN_Broker_Dict_v0100.json"], "PRESENT")


class ReadinessGateTests(unittest.TestCase):
    """Review follow-ups: readiness needs compiling modules, every required SSOT, and passing byte/format gates."""

    @staticmethod
    def def_ready_env() -> dict:
        import copy
        env = copy.deepcopy(ENV)
        for key in PROBE.S08_MODULES + PROBE.S09_MODULES + PROBE.S10_MODULES:
            env["modules"][key] = {"stage": key, "pattern": "", "status": "PRESENT", "path": "fixture/" + key + ".py", "syntax": "OK"}
        for dep in PROBE.TABLE_DEPS:
            env["deps"].setdefault(dep, {})["available"] = True
        for key in list(env["ssot"]):
            env["ssot"][key] = "PRESENT"
        return env

    def def_probe(self, env: dict, name: str, path: Path | None) -> dict:
        contract = PROBE.def_parse_contract(name, KNOWLEDGE)
        return PROBE.def_probe_file(name, path, env, contract, {})

    def test_fully_provisioned_pdf_is_ready_through_s10(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vrn-ready-") as temporary:
            pdf = Path(temporary) / "GS-2317 20251205.pdf"
            pdf.write_bytes(b"%PDF-1.4\n%synthetic\n")
            result = self.def_probe(self.def_ready_env(), pdf.name, pdf)
        self.assertEqual([result["stages"][s]["status"] for s in ("S08", "S09", "S10")], ["READY", "READY", "READY"])

    def test_syntax_broken_module_blocks_the_stage(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vrn-syntax-") as temporary:
            pdf = Path(temporary) / "GS-2317 20251205.pdf"
            pdf.write_bytes(b"%PDF-1.4\n%synthetic\n")
            env = self.def_ready_env()
            env["modules"]["MDL003"]["syntax"] = "FAIL SyntaxError"
            result = self.def_probe(env, pdf.name, pdf)
            self.assertEqual(result["stages"]["S08"]["status"], "BLOCKED")
            self.assertIn("MDL003(FAIL SyntaxError)", result["stages"]["S08"]["detail"])
            self.assertEqual(result["stages"]["S09"]["status"], "BLOCKED")
            env = self.def_ready_env()
            env["modules"]["MDL006"]["syntax"] = "FAIL SyntaxError"
            result = self.def_probe(env, pdf.name, pdf)
            self.assertEqual(result["stages"]["S08"]["status"], "READY")
            self.assertEqual(result["stages"]["S09"]["status"], "BLOCKED")
            self.assertEqual(result["stages"]["S10"]["status"], "BLOCKED")
            env = self.def_ready_env()
            for key in PROBE.S10_MODULES:
                env["modules"][key]["syntax"] = "FAIL SyntaxError"
            result = self.def_probe(env, pdf.name, pdf)
            self.assertEqual(result["stages"]["S10"]["status"], "BLOCKED")

    def test_missing_required_ssot_blocks_s09(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vrn-ssot-") as temporary:
            pdf = Path(temporary) / "GS-2317 20251205.pdf"
            pdf.write_bytes(b"%PDF-1.4\n%synthetic\n")
            env = self.def_ready_env()
            env["ssot"]["VRN_Broker_Dict_v0100.json"] = "ABSENT"
            result = self.def_probe(env, pdf.name, pdf)
        self.assertEqual(result["stages"]["S08"]["status"], "READY")
        self.assertEqual(result["stages"]["S09"]["status"], "BLOCKED")
        self.assertIn("VRN_Broker_Dict_v0100.json", result["stages"]["S09"]["detail"])
        self.assertEqual(result["stages"]["S10"]["status"], "BLOCKED")

    def test_zero_bytes_or_bad_magic_blocks_s08(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vrn-bytes-") as temporary:
            empty = Path(temporary) / "GS-2317 20251205.pdf"
            empty.write_bytes(b"")
            result = self.def_probe(self.def_ready_env(), empty.name, empty)
            self.assertEqual(result["stages"]["S02"]["status"], "FAIL")
            self.assertEqual(result["stages"]["S08"]["status"], "BLOCKED")
            self.assertIn("S02", result["stages"]["S08"]["detail"])
            fake = Path(temporary) / "GS-2382 20231012.pdf"
            fake.write_bytes(b"this is not a pdf at all\n")
            result = self.def_probe(self.def_ready_env(), fake.name, fake)
            self.assertEqual(result["stages"]["S04"]["status"], "FAIL")
            self.assertEqual(result["stages"]["S08"]["status"], "BLOCKED")
            self.assertEqual(result["stages"]["S09"]["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
