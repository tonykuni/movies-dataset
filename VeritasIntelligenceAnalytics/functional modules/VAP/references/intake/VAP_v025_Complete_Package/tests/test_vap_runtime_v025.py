import hashlib
import importlib.util
import json
import sqlite3
import sys
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_FILE = PACKAGE_ROOT / "runtime" / "vap_data_runtime_v025.py"
SPEC = importlib.util.spec_from_file_location("vap_runtime_v025", RUNTIME_FILE)
vap = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = vap
SPEC.loader.exec_module(vap)


class RuntimeFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for name in ("config", "data", "state", "output", "logs", "ui"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self.csv_path = self.root / "data" / "market.csv"
        self.csv_path.write_text(
            "date,close,volume,return_pct\n2026-01-01,10,100,1\n2026-01-02,,,-1\n2026-01-03,12,120,2\n",
            encoding="utf-8",
        )
        self.config_path = self.root / "config" / "runtime.json"
        self.manifest_path = self.root / "config" / "vdf.json"
        self.config = {
            "schema": "VIA-VAP-RUNTIME-CONFIG/1.0",
            "version": "v025",
            "host": "127.0.0.1",
            "port": 8765,
            "openBrowser": False,
            "syncConnectOnStart": False,
            "maxRows": 5000,
            "maxBodyBytes": 1048576,
            "allowedRoots": [str(self.root)],
            "allowedHosts": ["127.0.0.1"],
            "imageDirectory": "output/saved_images",
            "vdfGateway": {"required": True, "manifest": str(self.manifest_path)},
            "sources": [
                {
                    "id": "SOURCE-CSV",
                    "vdfContractId": "VDF-CSV-v1",
                    "alias": "MARKET",
                    "engine": "CSV",
                    "location": str(self.csv_path),
                    "table": "market",
                    "enabled": True,
                }
            ],
        }
        self.manifest = {
            "schema": "VIA-VDF-VAP-CONNECTION-MANIFEST/1.0",
            "version": "v025",
            "connections": [
                {
                    "contractId": "VDF-CSV-v1",
                    "sourceId": "SOURCE-CSV",
                    "state": "AUTHORIZED",
                    "readOnly": True,
                    "engine": "CSV",
                    "assetClass": "OTHER",
                }
            ],
        }
        self.write_contracts()

    def tearDown(self):
        self.temp.cleanup()

    def write_contracts(self):
        for connection in self.manifest.get("connections", []):
            payload = {key: value for key, value in connection.items() if key != "fingerprint"}
            connection["fingerprint"] = vap.def_sha256_text(vap.def_canonical_json(payload))
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")

    def runtime(self):
        return vap.CatalogRuntime(self.root, self.config_path)

    def test_refresh_incremental_and_cache(self):
        runtime = self.runtime()
        first = runtime.refresh("R-1", ["ALL"], "INCREMENTAL")
        self.assertEqual(len(first.tables), 1)
        self.assertEqual(first.tables[0]["runtime"]["vdfAuthorized"], True)
        self.assertEqual(first.tables[0]["rows"][1]["close"], "10")
        self.assertEqual(first.tables[0]["rows"][1]["volume"], 0)
        second = runtime.refresh("R-2", ["ALL"], "INCREMENTAL")
        self.assertEqual(second.tables[0]["runtime"]["refreshStatus"], "UNCHANGED")
        self.assertTrue(runtime.cache_path.exists())
        self.assertTrue(runtime.checkpoint_path.exists())

    def test_partial_refresh_preserves_other_source(self):
        other = self.root / "data" / "other.json"
        other.write_text(json.dumps([{"date": "a", "value": 1}, {"date": "b", "value": 2}, {"date": "c", "value": 3}]), encoding="utf-8")
        self.config["sources"].append({"id": "SOURCE-JSON", "vdfContractId": "VDF-JSON-v1", "alias": "OTHER", "engine": "JSON", "location": str(other), "enabled": True})
        self.manifest["connections"].append({"contractId": "VDF-JSON-v1", "sourceId": "SOURCE-JSON", "state": "AUTHORIZED", "readOnly": True, "engine": "JSON", "assetClass": "OTHER"})
        self.write_contracts()
        runtime = self.runtime()
        self.assertEqual(len(runtime.refresh("R-ALL", ["ALL"], "FULL").tables), 2)
        names = {table["name"] for table in runtime.refresh("R-ONE", ["SOURCE-CSV"], "INCREMENTAL").tables}
        self.assertEqual(names, {"market", "other"})

    def test_vdf_gate_rejects_unapproved_source(self):
        self.manifest["connections"][0]["state"] = "DRAFT"
        self.write_contracts()
        result = self.runtime().refresh("R-DENY", ["ALL"], "FULL")
        self.assertEqual(result.tables, [])
        self.assertIn("VDF_AUTHORIZATION_REQUIRED", result.errors[0]["message"])

    def test_stock_adjusted_price_and_talib_evidence_gate(self):
        stock = self.root / "data" / "stock.csv"
        stock.write_text("date,adjClose,close,volume\n2026-01-01,10,9,100\n2026-01-02,11,10,110\n2026-01-03,12,11,120\n", encoding="utf-8")
        self.config["sources"] = [{"id": "STOCK-1", "vdfContractId": "VDF-STOCK-v1", "alias": "STOCK", "engine": "CSV", "location": str(stock), "enabled": True}]
        self.manifest["connections"] = [{
            "contractId": "VDF-STOCK-v1", "sourceId": "STOCK-1", "state": "AUTHORIZED", "readOnly": True,
            "engine": "CSV", "assetClass": "STOCK", "adjustedPriceField": "adjClose",
            "taLibEvidence": {"engine": "TA-Lib", "status": "PASS", "priceInput": "adjClose"},
        }]
        self.write_contracts()
        table = self.runtime().refresh("R-STOCK", ["ALL"], "FULL").tables[0]
        self.assertIn("adjClose", table["numeric"])
        self.assertNotIn("close", table["numeric"])
        self.assertEqual(table["runtime"]["adjustedPriceField"], "adjClose")
        self.assertEqual(table["runtime"]["taLibEvidence"]["status"], "PASS")

    def test_stock_without_talib_evidence_is_rejected(self):
        self.manifest["connections"][0].update({"assetClass": "STOCK", "adjustedPriceField": "adjClose", "taLibEvidence": {"engine": "TA-Lib", "status": "PENDING"}})
        self.write_contracts()
        result = self.runtime().refresh("R-STOCK-FAIL", ["ALL"], "FULL")
        self.assertEqual(result.tables, [])
        self.assertIn("VDF_TALIB_EVIDENCE_REQUIRED", result.errors[0]["message"])

    def test_sqlite_adapter_is_read_only(self):
        database = self.root / "data" / "market.sqlite"
        with sqlite3.connect(database) as connection:
            connection.execute("CREATE TABLE prices(date TEXT, value REAL)")
            connection.executemany("INSERT INTO prices VALUES(?,?)", [("a", 1), ("b", 2), ("c", 3)])
        rows = vap.def_read_sqlite(database, "prices", 10)[0][1]
        self.assertEqual([row["value"] for row in rows], [1.0, 2.0, 3.0])
        self.assertEqual(sqlite3.connect(database).execute("SELECT COUNT(*) FROM prices").fetchone()[0], 3)

    def test_path_allowlist_rejects_escape(self):
        with self.assertRaises(PermissionError):
            vap.def_resolve_allowed_path("/etc/passwd", [str(self.root)])

    def test_governed_svg_filesystem_save_and_tamper_detection(self):
        runtime = self.runtime()
        chart = {"title": "A", "labels": ["a", "b", "c"], "lv": [1, 2, 3]}
        svg = '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0L1 1"/></svg>'
        fingerprint = vap.def_sha256_text(vap.def_canonical_json({"schema": vap.IMAGE_SCHEMA, "chartRecord": chart, "svgMarkup": svg}))
        payload = {"schema": vap.IMAGE_SCHEMA, "id": "VAP-IMG-TEST001", "chartRecord": chart, "svgMarkup": svg, "fingerprint": fingerprint}
        self.assertEqual(runtime.save_image(payload)["status"], "SAVED")
        self.assertEqual(runtime.save_image(payload)["status"], "EXISTS")
        self.assertTrue((runtime.image_root / "VAP-IMG-TEST001.svg").exists())
        with self.assertRaises(ValueError):
            runtime.save_image({**payload, "id": "VAP-IMG-TEST002", "fingerprint": "0" * 64})
        with self.assertRaises(ValueError):
            runtime.save_image({**payload, "id": "VAP-IMG-TEST003", "svgMarkup": "<svg><script>alert(1)</script></svg>", "fingerprint": ""})

    def test_http_health_refresh_catalog_and_images(self):
        runtime = self.runtime()
        server = ThreadingHTTPServer(("127.0.0.1", 0), vap.def_make_handler(runtime))
        runtime.config["port"] = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            health = json.loads(urllib.request.urlopen(base + "/api/health").read())
            self.assertEqual(health["vdfGateway"]["status"], "READY")
            request = urllib.request.Request(base + "/api/refresh", data=json.dumps({"requestId": "HTTP-R1", "targets": ["ALL"], "mode": "INCREMENTAL"}).encode(), headers={"Content-Type": "application/json"}, method="POST")
            response = json.loads(urllib.request.urlopen(request).read())
            self.assertEqual(response["status"], "UPDATED")
            catalog = json.loads(urllib.request.urlopen(base + "/api/catalog").read())
            self.assertEqual(len(catalog["tables"]), 1)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
