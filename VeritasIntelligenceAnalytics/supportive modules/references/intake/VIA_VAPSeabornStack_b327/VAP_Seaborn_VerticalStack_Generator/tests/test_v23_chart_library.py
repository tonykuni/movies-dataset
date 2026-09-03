from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from vap_chart_library import (
    CHART_LIBRARY_SCHEMA,
    CHART_LIBRARY_VERSION,
    append_library_chart,
    default_chart_library,
    delete_chart,
    get_chart_item,
    instantiate_chart,
    load_chart_library,
    save_chart_library,
    search_charts,
    upsert_chart,
    validate_chart_library,
    validate_chart_spec,
)


def chart_spec(
    chart_id: str = "price",
    chart_type: str = "line",
    title: str = "收盤價",
) -> dict[str, object]:
    return {
        "id": chart_id,
        "type": chart_type,
        "title": title,
        "x": "Date",
        "y": ["Adj Close"],
        "secondary_y": [],
        "height_ratio": 1.0,
        "line_width": 1.65,
        "alpha": 0.82,
    }


class VAPChartLibraryTests(unittest.TestCase):
    def test_missing_library_is_created_with_versioned_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gallery.json"
            library = load_chart_library(path)

            self.assertTrue(path.is_file())
            self.assertEqual(library["schema"], CHART_LIBRARY_SCHEMA)
            self.assertEqual(library["version"], CHART_LIBRARY_VERSION)
            self.assertEqual(library["items"], [])
            self.assertEqual(library["metadata"]["item_count"], 0)
            self.assertEqual(load_chart_library(path), library)

    def test_load_without_create_raises_for_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.json"
            with self.assertRaises(FileNotFoundError):
                load_chart_library(path, create=False)
            self.assertFalse(path.exists())

    def test_new_saves_get_unique_ids_and_do_not_mutate_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gallery.json"
            original = chart_spec()
            before = deepcopy(original)

            first = upsert_chart(
                path,
                original,
                name="價格趨勢",
                tags="股票, 價格,股票",
                description="Adjusted close",
            )
            second = upsert_chart(path, original, name="價格趨勢", tags=["股票"])

            self.assertEqual(original, before)
            self.assertEqual(first["id"], "價格趨勢")
            self.assertEqual(second["id"], "價格趨勢_2")
            self.assertEqual(first["tags"], ["股票", "價格"])
            self.assertEqual(first["chart_type"], "line")
            self.assertEqual(first["chart"], original)
            self.assertEqual(load_chart_library(path)["metadata"]["item_count"], 2)

    def test_explicit_item_id_overwrites_and_preserves_creation_time(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gallery.json"
            first = upsert_chart(
                path,
                chart_spec(),
                name="價格",
                item_id="price_template",
                metadata={"owner": "VAP"},
            )
            replacement_spec = chart_spec("volume", "bar", "成交量")
            replacement_spec["y"] = ["Volume"]
            replacement = upsert_chart(
                path,
                replacement_spec,
                name="量能",
                tags=["volume"],
                item_id="price_template",
                metadata={"owner": "VAP 2"},
            )

            library = load_chart_library(path)
            self.assertEqual(len(library["items"]), 1)
            self.assertEqual(replacement["id"], "price_template")
            self.assertEqual(replacement["chart_type"], "bar")
            self.assertEqual(replacement["metadata"]["created_at"], first["metadata"]["created_at"])
            self.assertEqual(replacement["metadata"]["owner"], "VAP 2")

    def test_search_combines_text_tags_and_chart_type(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gallery.json"
            upsert_chart(path, chart_spec(), name="價格走勢", tags=["股票", "核心"])
            upsert_chart(
                path,
                chart_spec("flow", "bar", "三大法人"),
                name="法人買賣超",
                description="Flow monitor",
                tags=["股票", "籌碼"],
            )
            upsert_chart(
                path,
                chart_spec("sales", "bar", "產品組合"),
                name="Sales mix",
                tags=["營運", "composition"],
            )

            self.assertEqual(len(search_charts(path, query="價格")), 1)
            self.assertEqual(len(search_charts(path, query="flow")), 1)
            self.assertEqual(len(search_charts(path, query="Date")), 3)
            result = search_charts(path, tags=["股票", "籌碼"], chart_type="BAR")
            self.assertEqual([item["name"] for item in result], ["法人買賣超"])
            self.assertEqual(search_charts(path, tags=["不存在"]), [])

    def test_instantiate_chart_uses_collision_free_id_and_lineage(self) -> None:
        library = default_chart_library()
        library["items"].append(
            {
                "id": "price_template",
                "name": "價格",
                "description": "",
                "tags": [],
                "chart_type": "line",
                "chart": chart_spec(),
                "metadata": {},
            }
        )
        item = get_chart_item(validate_chart_library(library), "price_template")
        instance = instantiate_chart(item, existing_ids=["price", "price_2"])

        self.assertEqual(instance["id"], "price_3")
        self.assertEqual(instance["gallery_item_id"], "price_template")
        self.assertEqual(instance["gallery_item_name"], "價格")
        self.assertNotIn("gallery_item_id", item["chart"])

    def test_append_library_chart_updates_stack_atomically_and_avoids_id_collision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            library_path = root / "gallery.json"
            config_path = root / "stack.json"
            item = upsert_chart(library_path, chart_spec(), name="價格")
            config_path.write_text(
                json.dumps(
                    {
                        "schema_version": "2.3",
                        "project": {},
                        "charts": [chart_spec()],
                        "metadata": {"created_at": "earlier"},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            appended = append_library_chart(config_path, library_path, item["id"])
            config = json.loads(config_path.read_text(encoding="utf-8"))

            self.assertEqual(appended["id"], "price_2")
            self.assertEqual([chart["id"] for chart in config["charts"]], ["price", "price_2"])
            self.assertIn("updated_at", config["metadata"])
            self.assertEqual(list(root.glob(".*.tmp")), [])

    def test_delete_returns_boolean_and_persists_item_count(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gallery.json"
            item = upsert_chart(path, chart_spec(), name="價格")
            self.assertTrue(delete_chart(path, item["id"]))
            self.assertFalse(delete_chart(path, item["id"]))
            self.assertEqual(load_chart_library(path)["metadata"]["item_count"], 0)

    def test_embedded_data_and_invalid_documents_are_rejected(self) -> None:
        embedded = chart_spec()
        embedded["data"] = [{"Date": "2026-01-01", "Close": 10}]
        with self.assertRaisesRegex(ValueError, "內嵌資料"):
            validate_chart_spec(embedded)
        rows = chart_spec()
        rows["records"] = [{"Close": 10}]
        with self.assertRaisesRegex(ValueError, "資料內容"):
            validate_chart_spec(rows)
        with self.assertRaisesRegex(ValueError, "type"):
            validate_chart_spec({"id": "empty", "type": ""})

        wrong_schema = default_chart_library()
        wrong_schema["schema"] = "legacy"
        with self.assertRaisesRegex(ValueError, "schema"):
            validate_chart_library(wrong_schema)

    def test_validation_failure_or_interrupted_write_keeps_previous_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gallery.json"
            load_chart_library(path)
            original_bytes = path.read_bytes()

            invalid = default_chart_library()
            invalid["version"] = "0"
            with self.assertRaisesRegex(ValueError, "version"):
                save_chart_library(path, invalid)
            self.assertEqual(path.read_bytes(), original_bytes)

            valid = default_chart_library()
            with patch("vap_chart_library.json.dump", side_effect=OSError("disk stopped")):
                with self.assertRaisesRegex(OSError, "disk stopped"):
                    save_chart_library(path, valid)
            self.assertEqual(path.read_bytes(), original_bytes)
            self.assertEqual(list(path.parent.glob(f".{path.name}.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
