import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

Error.stackTraceLimit = 2;
process.on("uncaughtException", (error) => {
  process.stderr.write(`VOFIE_XLSX_ERROR: ${error?.message ?? String(error)}\n`);
  process.exitCode = 1;
});
process.on("unhandledRejection", (error) => {
  process.stderr.write(`VOFIE_XLSX_REJECTION: ${error?.message ?? String(error)}\n`);
  process.exitCode = 1;
});

async function loadArtifactTool() {
  try {
    return await import("@oai/artifact-tool");
  } catch (firstError) {
    const moduleRoot = process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES;
    if (!moduleRoot) throw firstError;
    return import(pathToFileURL(path.join(moduleRoot, "@oai", "artifact-tool", "dist", "artifact_tool.mjs")).href);
  }
}

const { SpreadsheetFile, Workbook } = await loadArtifactTool();

const [irPath, outputPath, qaDir] = process.argv.slice(2);
if (!irPath || !outputPath || !qaDir) {
  throw new Error("Usage: xlsx_adapter.mjs <ir.json> <output.xlsx> <qa-dir>");
}

const ir = JSON.parse(await fs.readFile(irPath, "utf8"));
await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.mkdir(qaDir, { recursive: true });

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");
const topics = workbook.worksheets.add("Topic Matrix");
const sources = workbook.worksheets.add("Sources");
const capabilities = workbook.worksheets.add("ST Capabilities");
const uiqa = workbook.worksheets.add("UI QA");
const readme = workbook.worksheets.add("Readme");

const C = { accent: "#0F5F73", accentSoft: "#DCEEF2", ink: "#17212B", muted: "#65727F", line: "#D7E0E5", bg: "#F4F7F9", white: "#FFFFFF", gold: "#A06B17", redSoft: "#FCE8E6" };
const titleFormat = { fill: C.accent, font: { bold: true, color: C.white, size: 18 }, verticalAlignment: "center" };
const sectionFormat = { fill: C.accentSoft, font: { bold: true, color: C.ink }, verticalAlignment: "center" };
const headerFormat = { fill: "#E9F0F3", font: { bold: true, color: C.ink }, borders: { preset: "outside", style: "thin", color: C.line }, verticalAlignment: "center", wrapText: true };
const bodyBorder = { insideHorizontal: { style: "thin", color: C.line }, bottom: { style: "thin", color: C.line } };

function setup(sheet) {
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(4);
}

for (const sheet of [summary, topics, sources, capabilities, uiqa, readme]) setup(sheet);

// Readme
readme.getRange("A1:H2").merge();
readme.getRange("A1").values = [["VERITAS OMNIFORMAT INTELLIGENCE ENGINE"]];
readme.getRange("A1:H2").format = titleFormat;
readme.getRange("A4:B10").values = [
  ["Workbook", "Veritas VOFIE Structured Output"],
  ["Version", ir.engine_version],
  ["Run ID", ir.run_id],
  ["Quality Gate", ir.quality.gate],
  ["Source policy", "READ ONLY / NEW ARTIFACTS ONLY"],
  ["Duplicate policy", "MARK AND RETAIN"],
  ["AI policy", "CANDIDATE ONLY / NO DIRECT APPLY"],
];
readme.getRange("A4:A10").format = sectionFormat;
readme.getRange("A4:B10").format.borders = bodyBorder;
readme.getRange("A1:H10").format.columnWidth = 18;
readme.getRange("B4:B10").format.columnWidth = 42;

// Sources
sources.getRange("A1:G2").merge();
sources.getRange("A1").values = [["SOURCE REGISTRY"]];
sources.getRange("A1:G2").format = titleFormat;
const sourceRows = ir.source_records.map((item) => [item.source_id, item.name, item.input_kind, item.encoding, item.byte_size, item.source_hash, item.path]);
sources.getRange("A4:G4").values = [["Source ID", "Name", "Kind", "Encoding", "Bytes", "BLAKE2s", "Original Path"]];
sources.getRange("A4:G4").format = headerFormat;
if (sourceRows.length) {
  sources.getRangeByIndexes(4, 0, sourceRows.length, 7).values = sourceRows;
  sources.getRangeByIndexes(4, 0, sourceRows.length, 7).format.borders = bodyBorder;
  sources.getRangeByIndexes(4, 4, sourceRows.length, 1).format.numberFormat = "#,##0";
}
sources.getRange(`A1:G${sourceRows.length + 4}`).format.columnWidth = 18;
sources.getRange(`B1:B${sourceRows.length + 4}`).format.columnWidth = 34;
sources.getRange(`F1:F${sourceRows.length + 4}`).format.columnWidth = 34;
sources.getRange(`G1:G${sourceRows.length + 4}`).format.columnWidth = 48;
sources.freezePanes.freezeRows(4);

// Topic Matrix
topics.getRange("A1:N2").merge();
topics.getRange("A1").values = [["TOPIC MATRIX"]];
topics.getRange("A1:N2").format = titleFormat;
const topicHeaders = ["Topic ID", "Source ID", "Source", "Order", "Heading", "Category", "Tags", "Start", "End", "Duplicate Of", "Code Units", "Content Hash", "Excerpt", "Is Duplicate"];
topics.getRange("A4:N4").values = [topicHeaders];
topics.getRange("A4:N4").format = headerFormat;
const sourceNames = Object.fromEntries(ir.source_records.map((item) => [item.source_id, item.name]));
const topicRows = ir.topics.map((item) => [
  item.topic_id, item.source_id, sourceNames[item.source_id], item.order, item.heading, item.category,
  item.tags.join("; "), item.source_start_line, item.source_end_line, item.duplicate_of ?? "",
  item.code_units.length, item.content_hash, item.content.replace(/[`*_>#]/g, "").replace(/\s+/g, " ").slice(0, 1000), null,
]);
if (topicRows.length) {
  topics.getRangeByIndexes(4, 0, topicRows.length, topicHeaders.length).values = topicRows;
  topics.getRangeByIndexes(4, 0, topicRows.length, topicHeaders.length).format = { borders: bodyBorder, wrapText: true, verticalAlignment: "top" };
  topics.getRangeByIndexes(4, 3, topicRows.length, 1).format.numberFormat = "0";
  topics.getRangeByIndexes(4, 7, topicRows.length, 4).format.numberFormat = "0";
  topics.getRangeByIndexes(4, 9, topicRows.length, 1).conditionalFormats.add("notContainsBlanks", { format: { fill: "#FFF2CC", font: { color: C.gold } } });
  topics.getRange("N5").formulas = [["=IF(LEN(J5)>0,1,0)"]];
  topics.getRange(`N5:N${topicRows.length + 4}`).fillDown();
  topics.tables.add(`A4:N${topicRows.length + 4}`, true, "VOFIETopics").style = "TableStyleMedium2";
}
topics.getRange(`A1:N${topicRows.length + 4}`).format.columnWidth = 15;
topics.getRange(`C1:C${topicRows.length + 4}`).format.columnWidth = 30;
topics.getRange(`E1:E${topicRows.length + 4}`).format.columnWidth = 42;
topics.getRange(`F1:F${topicRows.length + 4}`).format.columnWidth = 23;
topics.getRange(`G1:G${topicRows.length + 4}`).format.columnWidth = 36;
topics.getRange(`L1:L${topicRows.length + 4}`).format.columnWidth = 28;
topics.getRange(`M1:M${topicRows.length + 4}`).format.columnWidth = 64;
topics.getRange(`N1:N${topicRows.length + 4}`).format.columnWidth = 13;
topics.freezePanes.freezeRows(4);

// ST Capabilities
capabilities.getRange("A1:F2").merge();
capabilities.getRange("A1").values = [["ST CAPABILITY ASSURANCE MATRIX"]];
capabilities.getRange("A1:F2").format = titleFormat;
capabilities.getRange("A4:F4").values = [["ST ID", "Action", "Baseline Position", "Flexibility", "Test", "Note"]];
capabilities.getRange("A4:F4").format = headerFormat;
const capabilityNotes = {
  detect_and_read: "Read-only source with pre/post hash verification.",
  topic_segment: "Every topic carries source lines and a content hash.",
  code_component_ir: "Polyglot components are documented in Markdown.",
  markdown_emit: "All outputs share the Markdown / IR canonical layer.",
  office_emit: "Office adapters preserve source traceability.",
  web_template_emit: "Three local files; no CDN; no source script execution.",
  audit_chain: "Every output event extends the hash chain.",
  vsis_bridge: "Use VSIS 1.2 when present; deterministic fallback otherwise.",
  ui_spec_extract: "Preserve both content and UI-spec lanes.",
  state_machine: "Separate UI events from state transitions.",
  interaction_graph: "Trace component, event, and target relationships.",
  test_cases: "At least one case for every interactive component.",
  usability: "Check labels, feedback, and keyboard paths.",
  accessibility: "Check semantics, ARIA, contrast, and focus.",
  security: "Never execute source scripts or trust external resources.",
  layout_optimize: "Responsive desktop and mobile geometry.",
  component_refactor: "Candidate only; never overwrite source UI.",
  performance: "Local-first resource and rendering budgets.",
  responsive: "Single- and multi-column breakpoint rules.",
  dark_mode: "Light by default; system dark-mode support.",
  telemetry: "Local, anonymous, opt-in, and disabled by default.",
};
const capabilityRows = ir.capability_profiles.map((item) => [item.st_id, item.action, item.position, item.flexibility, item.test, capabilityNotes[item.action] ?? item.note]);
if (capabilityRows.length) {
  capabilities.getRangeByIndexes(4, 0, capabilityRows.length, 6).values = capabilityRows;
  capabilities.getRangeByIndexes(4, 0, capabilityRows.length, 6).format = { borders: bodyBorder, wrapText: true, verticalAlignment: "top" };
  capabilities.tables.add(`A4:F${capabilityRows.length + 4}`, true, "VOFIECapabilities").style = "TableStyleMedium2";
}
capabilities.getRange(`A1:F${capabilityRows.length + 4}`).format.columnWidth = 24;
capabilities.getRange(`F1:F${capabilityRows.length + 4}`).format.columnWidth = 48;

// UI QA
uiqa.getRange("A1:E2").merge();
uiqa.getRange("A1").values = [["UI QUALITY ASSURANCE"]];
uiqa.getRange("A1:E2").format = titleFormat;
uiqa.getRange("A4:E4").values = [["Kind", "Rule / Test", "Component", "Severity / Action", "Result"]];
uiqa.getRange("A4:E4").format = headerFormat;
const qaRows = [];
for (const item of ir.ui_spec.security_findings) qaRows.push(["Security", item.rule, item.source_id, item.severity, "SOURCE NOT EXECUTED"]);
for (const item of ir.ui_spec.accessibility_findings) qaRows.push(["Accessibility", item.rule, item.component.id || item.component.name || item.component.tag, item.severity, "REVIEW"]);
for (const item of ir.ui_spec.test_cases) qaRows.push(["Test Case", item.test_id, item.component, item.action, item.expected]);
if (!qaRows.length) qaRows.push(["Summary", "No extracted HTML controls", "—", "INFO", "PASS"]);
uiqa.getRangeByIndexes(4, 0, qaRows.length, 5).values = qaRows;
uiqa.getRangeByIndexes(4, 0, qaRows.length, 5).format = { borders: bodyBorder, wrapText: true, verticalAlignment: "top" };
uiqa.getRange(`A1:E${qaRows.length + 4}`).format.columnWidth = 24;
uiqa.getRange(`E1:E${qaRows.length + 4}`).format.columnWidth = 44;

// Summary + formula-backed KPI and category chart
summary.getRange("A1:H2").merge();
summary.getRange("A1").values = [["VERITAS VOFIE — STRUCTURED SUMMARY"]];
summary.getRange("A1:H2").format = titleFormat;
summary.getRange("A4:B4").values = [["Metric", "Value"]];
summary.getRange("A4:B4").format = headerFormat;
summary.getRange("A5:A10").values = [["Sources"], ["Topics"], ["Code Units"], ["Duplicates"], ["Quarantine"], ["Quality Gate"]];
summary.getRange("B5:B10").formulas = [
  [`=COUNTA(Sources!B5:B${sourceRows.length + 4})`],
  [`=COUNTA('Topic Matrix'!A5:A${topicRows.length + 4})`],
  [`=SUM('Topic Matrix'!K5:K${topicRows.length + 4})`],
  [`=SUM('Topic Matrix'!N5:N${topicRows.length + 4})`],
  [`=${ir.quarantine.length}`],
  [`="${String(ir.quality.gate).replaceAll('"', '""')}"`],
];
summary.getRange("A5:A10").format = sectionFormat;
summary.getRange("A4:B10").format.borders = bodyBorder;
summary.getRange("B5:B9").format.numberFormat = "#,##0";
const categoryCounts = new Map();
for (const item of ir.topics) categoryCounts.set(item.category, (categoryCounts.get(item.category) ?? 0) + 1);
const categoryRows = [...categoryCounts.keys()].sort().map((category) => [category]);
summary.getRange("D4:E4").values = [["Category", "Topics"]];
summary.getRange("D4:E4").format = headerFormat;
if (categoryRows.length) {
  summary.getRangeByIndexes(4, 3, categoryRows.length, 1).values = categoryRows;
  const formulas = categoryRows.map((_, index) => [`=COUNTIF('Topic Matrix'!F$5:F$${topicRows.length + 4},D${index + 5})`]);
  summary.getRangeByIndexes(4, 4, formulas.length, 1).formulas = formulas;
  summary.getRangeByIndexes(4, 3, categoryRows.length, 2).format.borders = bodyBorder;
  const chart = summary.charts.add("bar", summary.getRange(`D4:E${categoryRows.length + 4}`));
  chart.title = "Topics by Category";
  chart.hasLegend = false;
  chart.yAxis = { numberFormatCode: "0" };
  chart.setPosition("G4", "N20");
}
summary.getRange(`A1:E${Math.max(10, categoryRows.length + 4)}`).format.columnWidth = 22;
summary.getRange(`A1:A${Math.max(10, categoryRows.length + 4)}`).format.columnWidth = 26;
summary.freezePanes.freezeRows(4);

const inspect = await workbook.inspect({ kind: "workbook,sheet,table,formula,drawing", maxChars: 12000, tableMaxRows: 8, tableMaxCols: 8 });
await fs.writeFile(path.join(qaDir, "xlsx-inspect.ndjson"), inspect.ndjson, "utf8");
const errorInspect = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 100 }, maxChars: 5000 });
await fs.writeFile(path.join(qaDir, "xlsx-formula-errors.ndjson"), errorInspect.ndjson, "utf8");

const previewRanges = {
  "Summary": "A1:N22",
  "Topic Matrix": `A1:N${Math.min(topicRows.length + 4, 28)}`,
  "Sources": `A1:G${Math.min(sourceRows.length + 4, 20)}`,
  "ST Capabilities": `A1:F${Math.min(capabilityRows.length + 4, 30)}`,
  "UI QA": `A1:E${Math.min(qaRows.length + 4, 30)}`,
  "Readme": "A1:H12",
};
for (const sheet of [summary, topics, sources, capabilities, uiqa, readme]) {
  const preview = await workbook.render({ sheetName: sheet.name, range: previewRanges[sheet.name], autoCrop: "all", scale: 1, format: "png" });
  const safeName = sheet.name.replaceAll(/[^A-Za-z0-9_-]/g, "_");
  await fs.writeFile(path.join(qaDir, `xlsx-${safeName}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);
