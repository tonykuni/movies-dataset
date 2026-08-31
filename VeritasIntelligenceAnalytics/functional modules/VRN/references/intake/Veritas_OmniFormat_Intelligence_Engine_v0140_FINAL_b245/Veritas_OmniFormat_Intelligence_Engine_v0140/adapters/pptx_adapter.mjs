import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

async function loadArtifactTool() {
  try {
    return await import("@oai/artifact-tool");
  } catch (firstError) {
    const moduleRoot = process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES;
    if (!moduleRoot) throw firstError;
    return import(pathToFileURL(path.join(moduleRoot, "@oai", "artifact-tool", "dist", "artifact_tool.mjs")).href);
  }
}

const { Presentation, PresentationFile } = await loadArtifactTool();

const [irPath, outputPath, qaDir] = process.argv.slice(2);
if (!irPath || !outputPath || !qaDir) {
  throw new Error("Usage: pptx_adapter.mjs <ir.json> <output.pptx> <qa-dir>");
}

const ir = JSON.parse(await fs.readFile(irPath, "utf8"));
await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.mkdir(qaDir, { recursive: true });

const C = {
  ink: "#17212B",
  muted: "#65727F",
  line: "#D7E0E5",
  bg: "#F4F7F9",
  surface: "#FFFFFF",
  accent: "#0F5F73",
  accentSoft: "#DCEEF2",
  gold: "#A06B17",
  red: "#9B2C2C",
};
const W = 1280;
const H = 720;
const page = { left: 70, top: 52, width: 1140, height: 610 };

function addBox(slide, position, fill = C.surface, line = C.line, radius = "rounded-lg") {
  return slide.shapes.add({
    geometry: "roundRect",
    position,
    fill,
    line: { style: "solid", fill: line, width: 1 },
    borderRadius: radius,
  });
}

function addText(slide, text, position, style = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = String(text ?? "");
  shape.text.style = {
    fontSize: style.fontSize ?? 20,
    bold: style.bold ?? false,
    color: style.color ?? C.ink,
    fontFamily: style.fontFamily ?? "Aptos",
    alignment: style.alignment ?? "left",
    verticalAlignment: style.verticalAlignment ?? "middle",
  };
  return shape;
}

function addHeader(slide, eyebrow, title, pageNumber) {
  addText(slide, eyebrow, { left: page.left, top: page.top, width: 520, height: 24 }, { fontSize: 12, bold: true, color: C.accent });
  addText(slide, title, { left: page.left, top: page.top + 28, width: 980, height: 54 }, { fontSize: 34, bold: true });
  addText(slide, String(pageNumber).padStart(2, "0"), { left: 1150, top: 58, width: 60, height: 24 }, { fontSize: 12, bold: true, color: C.muted, alignment: "right" });
}

function addFooter(slide) {
  addText(slide, `VERITAS INTELLIGENCE ANALYTICS  ·  VOFIE ${ir.engine_version}`, { left: page.left, top: 680, width: 720, height: 18 }, { fontSize: 9, color: C.muted });
  addText(slide, ir.run_id, { left: 790, top: 680, width: 420, height: 18 }, { fontSize: 9, color: C.muted, alignment: "right" });
}

function addMetric(slide, x, y, width, label, value, accent = C.accent) {
  addBox(slide, { left: x, top: y, width, height: 112 }, C.surface, C.line);
  addText(slide, label, { left: x + 18, top: y + 15, width: width - 36, height: 24 }, { fontSize: 12, bold: true, color: C.muted });
  addText(slide, value, { left: x + 18, top: y + 43, width: width - 36, height: 48 }, { fontSize: 30, bold: true, color: accent });
}

const presentation = Presentation.create({ slideSize: { width: W, height: H } });

// 1 — Title
{
  const slide = presentation.slides.add();
  slide.background.fill = C.bg;
  addText(slide, "VERITAS INTELLIGENCE ANALYTICS", { left: 72, top: 70, width: 620, height: 28 }, { fontSize: 13, bold: true, color: C.accent });
  addText(slide, "OmniFormat\nIntelligence Engine", { left: 72, top: 145, width: 700, height: 190 }, { fontSize: 52, bold: true });
  addText(slide, "Read · Restructure · Generate", { left: 74, top: 356, width: 670, height: 44 }, { fontSize: 23, color: C.muted });
  addBox(slide, { left: 832, top: 134, width: 360, height: 338 }, C.surface, C.line, "rounded-xl");
  addText(slide, "ONE IR", { left: 868, top: 170, width: 286, height: 38 }, { fontSize: 15, bold: true, color: C.accent, alignment: "center" });
  addText(slide, "MD\nWORD\nPOWERPOINT\nEXCEL · CSV\nHTML · CSS · JS", { left: 868, top: 215, width: 286, height: 220 }, { fontSize: 25, bold: true, alignment: "center" });
  addText(slide, `Run ${ir.run_id}\n${ir.created_at}`, { left: 74, top: 566, width: 610, height: 58 }, { fontSize: 12, color: C.muted });
  addFooter(slide);
}

// 2 — Pipeline
{
  const slide = presentation.slides.add();
  slide.background.fill = C.bg;
  addHeader(slide, "SYSTEM ARCHITECTURE", "One canonical structure drives every output", 2);
  const steps = [
    ["01", "Read only", "Text · Office · HTML · Code"],
    ["02", "Universal IR", "Source · Topic · Component · Hash"],
    ["03", "Restructure", "Taxonomy · Duplicate mark · ST"],
    ["04", "Adapter", "MD · Office · Web Template"],
  ];
  for (let i = 0; i < steps.length; i += 1) {
    const x = page.left + i * 285;
    addBox(slide, { left: x, top: 190, width: 245, height: 270 }, C.surface, C.line);
    addText(slide, steps[i][0], { left: x + 20, top: 210, width: 80, height: 38 }, { fontSize: 17, bold: true, color: C.accent });
    addText(slide, steps[i][1], { left: x + 20, top: 270, width: 205, height: 58 }, { fontSize: 25, bold: true });
    addText(slide, steps[i][2], { left: x + 20, top: 350, width: 205, height: 74 }, { fontSize: 16, color: C.muted });
    if (i < steps.length - 1) addText(slide, "→", { left: x + 249, top: 300, width: 32, height: 40 }, { fontSize: 25, bold: true, color: C.accent, alignment: "center" });
  }
  addText(slide, "No source mutation · No source script execution · AI candidates only", { left: page.left, top: 518, width: page.width, height: 44 }, { fontSize: 20, bold: true, color: C.accent, alignment: "center" });
  addFooter(slide);
}

// 3 — Scope
{
  const slide = presentation.slides.add();
  slide.background.fill = C.bg;
  addHeader(slide, "SOURCE COVERAGE", "Four attachments become traceable content assets", 3);
  const codeUnits = ir.topics.reduce((sum, item) => sum + item.code_units.length, 0);
  const duplicateCount = ir.topics.filter((item) => item.duplicate_of).length;
  addMetric(slide, 70, 160, 250, "SOURCES", String(ir.source_records.length));
  addMetric(slide, 345, 160, 250, "TOPIC BLOCKS", String(ir.topics.length));
  addMetric(slide, 620, 160, 250, "CODE UNITS", String(codeUnits));
  addMetric(slide, 895, 160, 250, "DUPLICATES", String(duplicateCount), C.gold);
  const startY = 320;
  ir.source_records.slice(0, 6).forEach((source, index) => {
    const y = startY + index * 54;
    addText(slide, source.name, { left: 86, top: y, width: 610, height: 38 }, { fontSize: 16, bold: true });
    addText(slide, `${source.input_kind} · ${source.byte_size.toLocaleString()} bytes`, { left: 710, top: y, width: 260, height: 38 }, { fontSize: 14, color: C.muted });
    addText(slide, source.source_hash.slice(0, 16), { left: 984, top: y, width: 170, height: 38 }, { fontSize: 12, color: C.muted, alignment: "right", fontFamily: "Aptos Mono" });
  });
  addFooter(slide);
}

// 4 — Taxonomy chart
{
  const slide = presentation.slides.add();
  slide.background.fill = C.bg;
  addHeader(slide, "TOPIC TAXONOMY", "UI, code refactoring, and analysis dominate the source set", 4);
  const counts = new Map();
  for (const topic of ir.topics) counts.set(topic.category, (counts.get(topic.category) ?? 0) + 1);
  const ranked = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8);
  slide.charts.add("bar", {
    position: { left: 76, top: 160, width: 760, height: 430 },
    categories: ranked.map(([name]) => name),
    series: [{ name: "Topics", values: ranked.map(([, value]) => value), fill: C.accent }],
    hasLegend: false,
    dataLabels: { showValue: true, position: "outEnd" },
    yAxis: { majorGridlines: { style: "solid", fill: C.line, width: 1 } },
  });
  addBox(slide, { left: 875, top: 172, width: 300, height: 372 }, C.surface, C.line);
  addText(slide, "HOW TO READ", { left: 904, top: 198, width: 240, height: 30 }, { fontSize: 15, bold: true, color: C.accent });
  addText(slide, "Every topic retains source lines and a content hash. Categories affect routing, never source retention.\n\nDuplicates point to a canonical topic and remain in the IR.", { left: 904, top: 246, width: 240, height: 240 }, { fontSize: 17, color: C.ink });
  addFooter(slide);
}

// 5 — Polyglot
{
  const slide = presentation.slides.add();
  slide.background.fill = C.bg;
  addHeader(slide, "POLYGLOT COMPONENT IR", "Map components first; rewrite only after equivalence", 5);
  const langCounts = new Map();
  for (const topic of ir.topics) for (const unit of topic.code_units) langCounts.set(unit.language, (langCounts.get(unit.language) ?? 0) + 1);
  const ranked = [...langCounts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8);
  const maxValue = Math.max(1, ...ranked.map(([, value]) => value));
  ranked.forEach(([language, value], index) => {
    const y = 165 + index * 52;
    addText(slide, language, { left: 86, top: y, width: 150, height: 32 }, { fontSize: 16, bold: true });
    slide.shapes.add({ geometry: "roundRect", position: { left: 245, top: y + 5, width: 610, height: 22 }, fill: C.line, line: { style: "solid", fill: C.line, width: 0 }, borderRadius: "rounded-full" });
    slide.shapes.add({ geometry: "roundRect", position: { left: 245, top: y + 5, width: Math.max(8, 610 * value / maxValue), height: 22 }, fill: C.accent, line: { style: "solid", fill: C.accent, width: 0 }, borderRadius: "rounded-full" });
    addText(slide, value, { left: 870, top: y, width: 70, height: 32 }, { fontSize: 16, bold: true, color: C.accent, alignment: "right" });
  });
  addBox(slide, { left: 972, top: 170, width: 210, height: 350 }, C.surface, C.line);
  addText(slide, "EQUIVALENCE GATE", { left: 990, top: 200, width: 174, height: 34 }, { fontSize: 15, bold: true, color: C.accent, alignment: "center" });
  addText(slide, "AST / structure\nSignatures\nFixture replay\nZero mutation\n\nNo pass: HOLD", { left: 996, top: 260, width: 162, height: 210 }, { fontSize: 18, bold: true, alignment: "center" });
  addFooter(slide);
}

// 6 — QA
{
  const slide = presentation.slides.add();
  slide.background.fill = C.bg;
  addHeader(slide, "QUALITY & SECURITY", "Clean without deleting; generate without direct apply", 6);
  const items = [
    ["Source preservation", ir.quality.source_preservation, "BLAKE2s matches before and after"],
    ["Quarantined items", String(ir.quarantine.length), "Retained in the Universal IR"],
    ["Source scripts", "DENIED", "HTML scripts are never executed"],
    ["AI direct apply", "DENIED", "Candidates require equivalence tests"],
  ];
  items.forEach((item, index) => {
    const y = 160 + index * 105;
    addText(slide, item[0], { left: 92, top: y, width: 210, height: 44 }, { fontSize: 20, bold: true });
    addText(slide, item[1], { left: 330, top: y, width: 240, height: 44 }, { fontSize: 20, bold: true, color: item[1] === "FAIL" ? C.red : C.accent });
    addText(slide, item[2], { left: 605, top: y, width: 540, height: 44 }, { fontSize: 18, color: C.muted });
  });
  addFooter(slide);
}

// 7 — Close
{
  const slide = presentation.slides.add();
  slide.background.fill = C.accent;
  addText(slide, "VERITAS OMNIFORMAT", { left: 72, top: 70, width: 520, height: 28 }, { fontSize: 13, bold: true, color: "#DCEEF2" });
  addText(slide, "One Python entry.\nOne truthful structure for every format.", { left: 72, top: 155, width: 990, height: 170 }, { fontSize: 45, bold: true, color: "#FFFFFF" });
  addText(slide, "Add a reader or output tool by registering its Adapter and ST Profile. Existing inputs, IR, and quality gates remain unchanged.", { left: 74, top: 385, width: 910, height: 88 }, { fontSize: 22, color: "#DCEEF2" });
  addText(slide, `QUALITY GATE  ${ir.quality.gate}`, { left: 74, top: 560, width: 550, height: 44 }, { fontSize: 18, bold: true, color: "#FFFFFF" });
  addText(slide, ir.run_id, { left: 745, top: 560, width: 465, height: 44 }, { fontSize: 13, color: "#DCEEF2", alignment: "right", fontFamily: "Aptos Mono" });
}

for (const [index, slide] of presentation.slides.items.entries()) {
  const stem = `pptx-slide-${String(index + 1).padStart(2, "0")}`;
  const png = await presentation.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(path.join(qaDir, `${stem}.png`), new Uint8Array(await png.arrayBuffer()));
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(qaDir, `${stem}.layout.json`), await layout.text());
}
const montage = await presentation.export({ format: "webp", montage: true, scale: 1 });
await fs.writeFile(path.join(qaDir, "pptx-montage.webp"), new Uint8Array(await montage.arrayBuffer()));
const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(outputPath);
