"""Contract-driven Schema-to-HTML renderer with stable semantic bindings."""

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
import re
from typing import Any, Mapping

from pydantic import BaseModel

from .config import (
    ALLOWED_UI_WIDGETS,
    DEFAULT_ENDPOINT_PREFIX,
    DEFAULT_SUBMIT_LABEL,
    DEFAULT_UI_LANGUAGE,
    DEFAULT_UI_TITLE,
)
from .registry import CommandDescriptor, VIACommandRegistry


HTML_DOCUMENT_STYLE = """
:root {
  color-scheme: light;
  --via-ink: #2f4554;
  --via-muted: #657786;
  --via-line: #d9e3ea;
  --via-panel: #ffffff;
  --via-bg: #f4f8fb;
  --via-blue: #4c78a8;
  --via-blue-soft: #dbe9f4;
  --via-green: #59a14f;
  --via-red: #e15759;
  --via-yellow: #f2cf5b;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--via-bg);
  color: var(--via-ink);
  font: 13px/1.45 Inter, "Noto Sans TC", "Segoe UI", sans-serif;
}
.via-shell { width: min(1180px, 96vw); margin: 24px auto; }
.via-header, .via-card {
  background: var(--via-panel);
  border: 1px solid var(--via-line);
  border-radius: 12px;
  box-shadow: 0 4px 18px rgba(76, 120, 168, .08);
}
.via-header { padding: 16px 18px; margin-bottom: 14px; }
.via-header h1 { margin: 0 0 4px; font-size: 20px; color: var(--via-blue); }
.via-header p { margin: 0; color: var(--via-muted); }
.via-grid { display: grid; gap: 14px; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }
.via-card { padding: 16px; min-width: 0; }
.via-card h2 { margin: 0 0 4px; font-size: 16px; overflow-wrap: anywhere; }
.via-meta { color: var(--via-muted); font-size: 11px; margin-bottom: 14px; overflow-wrap: anywhere; }
.via-field { margin: 0 0 12px; min-width: 0; }
.via-field label { display: block; font-weight: 650; margin-bottom: 4px; }
.via-help { color: var(--via-muted); font-size: 11px; margin: 4px 0 0; overflow-wrap: anywhere; }
.via-required { color: var(--via-red); }
input, select, textarea, button {
  width: 100%; border: 1px solid #bdccd7; border-radius: 7px;
  color: var(--via-ink); background: #fff; font: inherit;
}
input, select, textarea { padding: 8px 9px; }
textarea { min-height: 86px; resize: vertical; }
input[type="checkbox"] { width: auto; margin-right: 7px; }
input[type="color"] { min-height: 38px; padding: 3px; }
button { padding: 9px 12px; border-color: var(--via-blue); background: var(--via-blue); color: white; cursor: pointer; }
button:hover { filter: brightness(1.05); }
.via-result { margin-top: 10px; padding: 9px; border-radius: 7px; background: #eef5fa; white-space: pre-wrap; overflow-wrap: anywhere; min-height: 34px; }
.via-status { display: inline-block; padding: 2px 7px; border-radius: 999px; background: var(--via-blue-soft); font-size: 10px; }
@media (max-width: 620px) { .via-shell { width: 94vw; margin: 12px auto; } .via-grid { grid-template-columns: 1fr; } }
""".strip()


HTML_CLIENT_SCRIPT = r"""
document.addEventListener("submit", async (event) => {
  const form = event.target.closest("form[data-via-command]");
  if (!form) return;
  event.preventDefault();
  const result = document.getElementById(form.dataset.viaResultTarget);
  const payload = {};
  for (const field of form.elements) {
    if (!field.name || field.disabled || field.type === "submit") continue;
    const kind = field.dataset.viaJsonType || "string";
    if (kind === "boolean") payload[field.name] = Boolean(field.checked);
    else if (kind === "integer") payload[field.name] = Number.parseInt(field.value, 10);
    else if (kind === "number") payload[field.name] = Number.parseFloat(field.value);
    else if (kind === "array" || kind === "object") payload[field.name] = JSON.parse(field.value);
    else payload[field.name] = field.value;
  }
  result.textContent = "執行中…";
  try {
    const response = await fetch(form.action, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const body = await response.json();
    result.textContent = JSON.stringify(body, null, 2);
    result.dataset.viaStatus = response.ok ? "SUCCESS" : "REJECTED";
  } catch (error) {
    result.textContent = `連線失敗：${error.message}`;
    result.dataset.viaStatus = "ERROR";
  }
});
""".strip()


class SchemaToHTMLRenderer:
    """Render Pydantic JSON Schema into accessible, test-stable HTML."""

    def __init__(
        self,
        *,
        endpoint_prefix: str = DEFAULT_ENDPOINT_PREFIX,
        submit_label: str = DEFAULT_SUBMIT_LABEL,
    ) -> None:
        self._endpoint_prefix = endpoint_prefix.rstrip("/")
        self._submit_label = submit_label

    def render_form(self, descriptor: CommandDescriptor) -> str:
        schema = descriptor.input_model.model_json_schema()
        properties = schema.get("properties", {})
        required_fields = set(schema.get("required", []))
        command_name = descriptor.manifest.name
        result_id = f"via-result-{self._slug(command_name)}"
        fields = "\n".join(
            self._render_field(
                command_name,
                name,
                self._resolve_property_schema(field_schema, schema),
                name in required_fields,
            )
            for name, field_schema in properties.items()
        )
        endpoint = f"{self._endpoint_prefix}/{self._escape_path(command_name)}/execute"
        description = html.escape(descriptor.manifest.description or "Typed VIA command")
        version = html.escape(descriptor.manifest.version)
        subsystem = html.escape(descriptor.manifest.subsystem)
        resource_urn = html.escape(descriptor.resource_urn)
        return f"""
<section class="via-card" data-via-module="{html.escape(command_name)}" data-via-urn="{resource_urn}">
  <h2>{html.escape(command_name)}</h2>
  <div class="via-meta"><span class="via-status">{subsystem}</span> · v{version} · {resource_urn}<br>{description}</div>
  <form method="post" action="{html.escape(endpoint)}" data-via-command="{html.escape(command_name)}" data-via-urn="{resource_urn}" data-via-result-target="{result_id}">
    {fields}
    <button type="submit" data-via-action="submit" aria-label="{html.escape(self._submit_label)}">{html.escape(self._submit_label)}</button>
  </form>
  <pre id="{result_id}" class="via-result" role="status" aria-live="polite">尚未執行</pre>
</section>""".strip()

    def render_catalog_document(
        self,
        registry: VIACommandRegistry,
        *,
        title: str = DEFAULT_UI_TITLE,
        include_client_script: bool = True,
    ) -> str:
        forms = "\n".join(
            self.render_form(descriptor)
            for descriptor in registry.list_descriptors()
        )
        script = f"<script>{HTML_CLIENT_SCRIPT}</script>" if include_client_script else ""
        return f"""<!doctype html>
<html lang="{DEFAULT_UI_LANGUAGE}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>{HTML_DOCUMENT_STYLE}</style>
</head>
<body>
  <main class="via-shell">
    <header class="via-header">
      <h1>{html.escape(title)}</h1>
      <p>Contract-Driven UI · Pydantic Schema SSOT · Stable Semantic Selectors</p>
    </header>
    <div class="via-grid">{forms}</div>
  </main>
  {script}
</body>
</html>"""

    def _render_field(
        self,
        command_name: str,
        field_name: str,
        schema: Mapping[str, Any],
        required: bool,
    ) -> str:
        field_id = f"via-{self._slug(command_name)}-{self._slug(field_name)}"
        title = str(schema.get("title") or field_name.replace("_", " ").title())
        description = str(schema.get("description") or "")
        schema_type = str(schema.get("type") or "string")
        extra = schema.get("json_schema_extra") or {}
        widget = str(extra.get("ui_widget") or schema.get("ui_widget") or "auto")
        if widget not in ALLOWED_UI_WIDGETS:
            widget = "auto"
        widget = self._choose_widget(widget, schema_type, schema)
        required_attribute = " required" if required else ""
        required_mark = '<span class="via-required" aria-hidden="true">*</span>' if required else ""
        attributes = self._constraint_attributes(schema)
        default = schema.get("default")
        value_attribute = ""
        if default is not None and widget not in {"checkbox", "select", "textarea"}:
            value_attribute = f' value="{html.escape(str(default), quote=True)}"'

        if widget == "select":
            options = []
            for item in schema.get("enum", []):
                selected = " selected" if item == default else ""
                escaped = html.escape(str(item), quote=True)
                options.append(f'<option value="{escaped}"{selected}>{escaped}</option>')
            control = (
                f'<select id="{field_id}" name="{html.escape(field_name)}" '
                f'data-via-field="{html.escape(field_name)}" data-via-json-type="{schema_type}"'
                f'{required_attribute}>{"".join(options)}</select>'
            )
        elif widget == "textarea":
            initial = "" if default is None else html.escape(str(default))
            control = (
                f'<textarea id="{field_id}" name="{html.escape(field_name)}" '
                f'data-via-field="{html.escape(field_name)}" data-via-json-type="{schema_type}"'
                f'{required_attribute}{attributes}>{initial}</textarea>'
            )
        elif widget == "checkbox":
            checked = " checked" if bool(default) else ""
            control = (
                f'<input id="{field_id}" type="checkbox" name="{html.escape(field_name)}" '
                f'data-via-field="{html.escape(field_name)}" data-via-json-type="boolean"'
                f'{checked}{required_attribute}>'
            )
        else:
            input_type = widget if widget != "auto" else "text"
            control = (
                f'<input id="{field_id}" type="{html.escape(input_type)}" '
                f'name="{html.escape(field_name)}" data-via-field="{html.escape(field_name)}" '
                f'data-via-json-type="{schema_type}"{value_attribute}{required_attribute}{attributes}>'
            )

        help_text = f'<p class="via-help">{html.escape(description)}</p>' if description else ""
        label = "" if widget == "hidden" else (
            f'<label for="{field_id}">{html.escape(title)} {required_mark}</label>'
        )
        return f'<div class="via-field" data-via-field-wrap="{html.escape(field_name)}">{label}{control}{help_text}</div>'

    @staticmethod
    def _resolve_property_schema(
        property_schema: Mapping[str, Any],
        root_schema: Mapping[str, Any],
    ) -> dict[str, Any]:
        resolved = dict(property_schema)
        reference = resolved.get("$ref")
        if isinstance(reference, str) and reference.startswith("#/$defs/"):
            key = reference.split("/")[-1]
            resolved = dict(root_schema.get("$defs", {}).get(key, resolved))
        variants = resolved.get("anyOf")
        if isinstance(variants, list):
            non_null = [item for item in variants if item.get("type") != "null"]
            if len(non_null) == 1:
                merged = dict(non_null[0])
                for key in ("title", "description", "default", "json_schema_extra"):
                    if key in resolved:
                        merged[key] = resolved[key]
                resolved = merged
        return resolved

    @staticmethod
    def _choose_widget(widget: str, schema_type: str, schema: Mapping[str, Any]) -> str:
        if widget != "auto":
            return widget
        if "enum" in schema:
            return "select"
        if schema_type == "boolean":
            return "checkbox"
        if schema_type in {"number", "integer"}:
            return "number"
        if schema_type in {"array", "object"}:
            return "textarea"
        format_name = schema.get("format")
        if format_name == "email":
            return "email"
        if format_name == "date":
            return "date"
        if format_name == "date-time":
            return "datetime-local"
        if schema.get("maxLength", 0) and int(schema["maxLength"]) > 160:
            return "textarea"
        return "text"

    @staticmethod
    def _constraint_attributes(schema: Mapping[str, Any]) -> str:
        mapping = {
            "minimum": "min",
            "maximum": "max",
            "minLength": "minlength",
            "maxLength": "maxlength",
            "pattern": "pattern",
            "multipleOf": "step",
        }
        attributes: list[str] = []
        for schema_key, html_key in mapping.items():
            if schema_key in schema:
                value = html.escape(str(schema[schema_key]), quote=True)
                attributes.append(f' {html_key}="{value}"')
        if "exclusiveMinimum" in schema:
            value = schema["exclusiveMinimum"]
            step = 1 if schema.get("type") == "integer" else 0.000001
            attributes.append(f' min="{value + step}"')
        if "exclusiveMaximum" in schema:
            value = schema["exclusiveMaximum"]
            step = 1 if schema.get("type") == "integer" else 0.000001
            attributes.append(f' max="{value - step}"')
        return "".join(attributes)

    @staticmethod
    def _slug(value: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-").lower()
        return slug or "command"

    @staticmethod
    def _escape_path(value: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_.-]", "-", value)


def def_export_schema_json(model_type: type[BaseModel]) -> str:
    """Export deterministic UTF-8-friendly JSON Schema text."""

    return json.dumps(
        model_type.model_json_schema(),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
