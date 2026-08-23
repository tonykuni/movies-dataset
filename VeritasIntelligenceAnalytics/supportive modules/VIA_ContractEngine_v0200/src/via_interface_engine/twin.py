"""Digital-twin contract and UI-binding verification without live side effects."""

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

import html
import json
from copy import deepcopy
from html.parser import HTMLParser
from typing import Any, Mapping

from pydantic import BaseModel, Field, ValidationError

from .contracts import VIAOutputModel
from .registry import CommandDescriptor, VIACommandRegistry
from .ui import HTML_DOCUMENT_STYLE, SchemaToHTMLRenderer


class TwinCheck(VIAOutputModel):
    check_id: str
    module_name: str
    category: str
    expected: str
    actual: str
    status: str
    detail: str = ""


class TwinReport(VIAOutputModel):
    gate: str
    total: int
    passed: int
    failed: int
    checks: list[TwinCheck] = Field(default_factory=list)


class _FieldCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.fields: dict[str, dict[str, str | None]] = {}

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag not in {"input", "select", "textarea"}:
            return
        values = dict(attrs)
        name = values.get("name")
        if name:
            self.fields[name] = values


class VIADigitalTwinTester:
    """Derive deterministic valid/invalid cases directly from the SSOT schema."""

    def __init__(self, renderer: SchemaToHTMLRenderer | None = None) -> None:
        self._renderer = renderer or SchemaToHTMLRenderer()

    def run_registry(self, registry: VIACommandRegistry) -> TwinReport:
        checks: list[TwinCheck] = []
        for descriptor in registry.list_descriptors():
            checks.extend(self.run_descriptor(descriptor))
        failed = sum(item.status == "FAIL" for item in checks)
        passed = sum(item.status == "PASS" for item in checks)
        return TwinReport(
            gate="PASS" if failed == 0 else "HOLD_REMEDIATION_REQUIRED",
            total=len(checks),
            passed=passed,
            failed=failed,
            checks=checks,
        )

    def run_descriptor(self, descriptor: CommandDescriptor) -> list[TwinCheck]:
        schema = descriptor.input_model.model_json_schema()
        valid_payload = self._make_valid_payload(schema)
        checks: list[TwinCheck] = []
        checks.append(
            self._validate_case(
                descriptor,
                "VALID_BASELINE",
                valid_payload,
                should_pass=True,
            )
        )
        for case_id, payload in self._make_invalid_payloads(schema, valid_payload):
            checks.append(
                self._validate_case(
                    descriptor,
                    case_id,
                    payload,
                    should_pass=False,
                )
            )
        checks.extend(self._check_ui_binding(descriptor, schema))
        return checks

    def render_report_html(self, report: TwinReport) -> str:
        rows = []
        for check in report.checks:
            color = "#59a14f" if check.status == "PASS" else "#e15759"
            rows.append(
                "<tr>"
                f"<td>{html.escape(check.check_id)}</td>"
                f"<td>{html.escape(check.module_name)}</td>"
                f"<td>{html.escape(check.category)}</td>"
                f"<td>{html.escape(check.expected)}</td>"
                f"<td>{html.escape(check.actual)}</td>"
                f'<td style="color:{color};font-weight:700">{html.escape(check.status)}</td>'
                f"<td>{html.escape(check.detail)}</td>"
                "</tr>"
            )
        return f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Digital Twin Report</title><style>{HTML_DOCUMENT_STYLE}
table {{ width:100%; border-collapse:collapse; table-layout:fixed; }}
th,td {{ border:1px solid #d9e3ea; padding:6px; text-align:left; vertical-align:top; overflow-wrap:anywhere; }}
th {{ background:#dbe9f4; color:#2f4554; }}
</style></head><body><main class="via-shell"><header class="via-header">
<h1>VIA Digital Twin Contract Report</h1><p>Gate: {html.escape(report.gate)} · PASS {report.passed} · FAIL {report.failed}</p>
</header><section class="via-card"><table><thead><tr><th>Check</th><th>Module</th><th>Category</th><th>Expected</th><th>Actual</th><th>Status</th><th>Detail</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></section></main></body></html>"""

    @staticmethod
    def report_json(report: TwinReport) -> str:
        return json.dumps(
            report.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )

    def _validate_case(
        self,
        descriptor: CommandDescriptor,
        case_id: str,
        payload: Mapping[str, Any],
        *,
        should_pass: bool,
    ) -> TwinCheck:
        try:
            descriptor.input_model.model_validate(payload)
            actual_pass = True
            detail = ""
        except ValidationError as exc:
            actual_pass = False
            detail = "; ".join(
                f"{'.'.join(str(item) for item in error['loc'])}: {error['type']}"
                for error in exc.errors(include_url=False)
            )
        return TwinCheck(
            check_id=case_id,
            module_name=descriptor.manifest.name,
            category="CONTRACT",
            expected="ACCEPT" if should_pass else "REJECT",
            actual="ACCEPT" if actual_pass else "REJECT",
            status="PASS" if actual_pass == should_pass else "FAIL",
            detail=detail,
        )

    def _check_ui_binding(
        self,
        descriptor: CommandDescriptor,
        schema: Mapping[str, Any],
    ) -> list[TwinCheck]:
        collector = _FieldCollector()
        collector.feed(self._renderer.render_form(descriptor))
        required = set(schema.get("required", []))
        checks: list[TwinCheck] = []
        for field_name, field_schema in schema.get("properties", {}).items():
            attributes = collector.fields.get(field_name)
            present = attributes is not None
            checks.append(
                TwinCheck(
                    check_id=f"UI_FIELD_{field_name}",
                    module_name=descriptor.manifest.name,
                    category="UI_BINDING",
                    expected="PRESENT",
                    actual="PRESENT" if present else "MISSING",
                    status="PASS" if present else "FAIL",
                )
            )
            if present and field_name in required:
                actual_required = "required" in attributes
                checks.append(
                    TwinCheck(
                        check_id=f"UI_REQUIRED_{field_name}",
                        module_name=descriptor.manifest.name,
                        category="UI_BINDING",
                        expected="REQUIRED",
                        actual="REQUIRED" if actual_required else "OPTIONAL",
                        status="PASS" if actual_required else "FAIL",
                    )
                )
            if present:
                checks.extend(
                    self._check_constraint_attributes(
                        descriptor.manifest.name,
                        field_name,
                        field_schema,
                        attributes,
                    )
                )
        return checks

    @staticmethod
    def _check_constraint_attributes(
        module_name: str,
        field_name: str,
        schema: Mapping[str, Any],
        attributes: Mapping[str, str | None],
    ) -> list[TwinCheck]:
        mapping = {
            "minimum": "min",
            "maximum": "max",
            "minLength": "minlength",
            "maxLength": "maxlength",
            "pattern": "pattern",
        }
        checks: list[TwinCheck] = []
        for schema_name, html_name in mapping.items():
            if schema_name not in schema:
                continue
            expected = str(schema[schema_name])
            actual = str(attributes.get(html_name))
            checks.append(
                TwinCheck(
                    check_id=f"UI_CONSTRAINT_{field_name}_{html_name}",
                    module_name=module_name,
                    category="UI_CONSTRAINT",
                    expected=expected,
                    actual=actual,
                    status="PASS" if expected == actual else "FAIL",
                )
            )
        return checks

    def _make_valid_payload(self, schema: Mapping[str, Any]) -> dict[str, Any]:
        required = set(schema.get("required", []))
        payload: dict[str, Any] = {}
        for field_name, raw_schema in schema.get("properties", {}).items():
            field_schema = self._resolve_schema(raw_schema, schema)
            if field_name in required or "default" in field_schema:
                payload[field_name] = self._valid_value(field_schema)
        return payload

    def _make_invalid_payloads(
        self,
        schema: Mapping[str, Any],
        valid_payload: Mapping[str, Any],
    ) -> list[tuple[str, dict[str, Any]]]:
        cases: list[tuple[str, dict[str, Any]]] = []
        for field_name in schema.get("required", []):
            candidate = deepcopy(dict(valid_payload))
            candidate.pop(field_name, None)
            cases.append((f"MISSING_REQUIRED_{field_name}", candidate))

        for field_name, raw_schema in schema.get("properties", {}).items():
            field_schema = self._resolve_schema(raw_schema, schema)
            schema_type = field_schema.get("type")
            invalid_values: list[tuple[str, Any]] = []
            if "exclusiveMinimum" in field_schema:
                invalid_values.append(("EXCLUSIVE_MIN", field_schema["exclusiveMinimum"]))
            elif "minimum" in field_schema:
                invalid_values.append(("BELOW_MIN", field_schema["minimum"] - 1))
            if "exclusiveMaximum" in field_schema:
                invalid_values.append(("EXCLUSIVE_MAX", field_schema["exclusiveMaximum"]))
            elif "maximum" in field_schema:
                invalid_values.append(("ABOVE_MAX", field_schema["maximum"] + 1))
            if "minLength" in field_schema and field_schema["minLength"] > 0:
                invalid_values.append(("BELOW_MIN_LENGTH", "x" * (field_schema["minLength"] - 1)))
            if "maxLength" in field_schema:
                invalid_values.append(("ABOVE_MAX_LENGTH", "x" * (field_schema["maxLength"] + 1)))
            if "enum" in field_schema:
                invalid_values.append(("INVALID_ENUM", "__VIA_INVALID_ENUM__"))
            if schema_type in {"integer", "number"}:
                invalid_values.append(("INVALID_TYPE", "五百"))
            for suffix, invalid_value in invalid_values:
                candidate = deepcopy(dict(valid_payload))
                candidate[field_name] = invalid_value
                cases.append((f"{suffix}_{field_name}", candidate))

        extra = deepcopy(dict(valid_payload))
        extra["__via_unregistered_field__"] = True
        cases.append(("EXTRA_FIELD", extra))
        return cases

    def _valid_value(self, schema: Mapping[str, Any]) -> Any:
        if "default" in schema:
            return schema["default"]
        if "enum" in schema:
            return schema["enum"][0]
        schema_type = schema.get("type", "string")
        if schema_type == "integer":
            if "exclusiveMinimum" in schema:
                return int(schema["exclusiveMinimum"]) + 1
            return int(schema.get("minimum", 1))
        if schema_type == "number":
            if "exclusiveMinimum" in schema:
                return float(schema["exclusiveMinimum"]) + 1.0
            return float(schema.get("minimum", 1.0))
        if schema_type == "boolean":
            return True
        if schema_type == "array":
            minimum = int(schema.get("minItems", 0))
            item_schema = schema.get("items", {"type": "string"})
            return [self._valid_value(item_schema) for _ in range(minimum)]
        if schema_type == "object":
            return self._make_valid_payload(schema)
        minimum_length = max(1, int(schema.get("minLength", 1)))
        maximum_length = int(schema.get("maxLength", max(minimum_length, 8)))
        size = min(maximum_length, max(minimum_length, 4))
        return "V" * size

    @staticmethod
    def _resolve_schema(
        raw_schema: Mapping[str, Any],
        root_schema: Mapping[str, Any],
    ) -> dict[str, Any]:
        return SchemaToHTMLRenderer._resolve_property_schema(raw_schema, root_schema)

