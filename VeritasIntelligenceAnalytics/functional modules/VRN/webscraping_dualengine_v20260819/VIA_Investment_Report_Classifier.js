"use strict";
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const SSOT_PATH = path.join(__dirname, "VIA_Investment_Report_Type_SSOT.json");

function defLoadReportTypeSsot(target = SSOT_PATH) {
  const data = JSON.parse(fs.readFileSync(target, "utf8"));
  if (!data.types || !data.types[data.default_type]) throw new Error("INVALID_REPORT_TYPE_SSOT");
  return data;
}
function defNormalize(value) { return String(value || "").replace(/\s+/g, " ").trim().toUpperCase(); }
function defClassifyInvestmentReport(title, content = "", ssot = defLoadReportTypeSsot()) {
  const titleNorm = defNormalize(title), contentHead = defNormalize(content.slice(0, 3000)); const candidates = [];
  for (const [code, spec] of Object.entries(ssot.types)) {
    const evidence = [];
    for (const pattern of spec.patterns || []) {
      const regex = new RegExp(pattern, "i");
      if (regex.test(titleNorm)) evidence.push(`TITLE:${pattern}`);
      else if (regex.test(contentHead)) evidence.push(`CONTENT:${pattern}`);
    }
    if (evidence.length) {
      const titleHits = evidence.filter(x => x.startsWith("TITLE:")).length;
      candidates.push({ code, priority: spec.priority || 0, score: (spec.priority || 0) + titleHits * 25 + (evidence.length - titleHits) * 8, evidence });
    }
  }
  candidates.sort((a, b) => b.score - a.score || b.priority - a.priority || a.code.localeCompare(b.code));
  const winner = candidates[0] || { code: ssot.default_type, evidence: ["NO_RULE_MATCH"] };
  const spec = ssot.types[winner.code];
  const titleHits = winner.evidence.filter(x => x.startsWith("TITLE:")).length;
  const contentHits = winner.evidence.filter(x => x.startsWith("CONTENT:")).length;
  return { report_type_code: winner.code, report_type_zh: spec.zh, report_type_en: spec.en, report_scope: spec.scope,
    confidence: candidates.length ? Math.min(0.99, 0.55 + titleHits * 0.12 + contentHits * 0.06) : 0.20,
    evidence: winner.evidence, classifier_version: ssot.schema_version };
}
function defSplitMorningBrief(title, content, parentUrl = "", ssot = defLoadReportTypeSsot()) {
  if (defClassifyInvestmentReport(title, content, ssot).report_type_code !== "DAILY_MORNING_BRIEF") return [];
  const found = [];
  for (const pattern of ssot.morning_section_patterns || []) {
    const flags = pattern.startsWith("(?m)") ? "gmi" : "gi"; const source = pattern.replace(/^\(\?m\)/, ""); const regex = new RegExp(source, flags); let match;
    while ((match = regex.exec(content)) !== null) found.push({ start: match.index, end: regex.lastIndex, heading: match[0].trim() });
  }
  const matches = [...new Map(found.map(x => [`${x.start}:${x.end}`, x])).values()].sort((a, b) => a.start - b.start); const sections = [];
  matches.forEach((item, index) => {
    const body = content.slice(item.end, matches[index + 1]?.start ?? content.length).trim(); if (body.length < 40) return;
    let classification = defClassifyInvestmentReport(item.heading, body, ssot);
    if (["UNCLASSIFIED_RESEARCH", "DAILY_MORNING_BRIEF"].includes(classification.report_type_code)) {
      const memo = ssot.types.RESEARCH_MEMO; classification = { report_type_code: "RESEARCH_MEMO", report_type_zh: memo.zh,
        report_type_en: memo.en, report_scope: memo.scope, confidence: 0.65,
        evidence: ["PARENT_DAILY_MORNING_BRIEF", "SECTION_BOUNDARY"], classifier_version: ssot.schema_version };
    }
    const ticker = item.heading.match(/(?<!\d)(\d{4})(?:\.(?:TWO|TW)|\s+TT)?(?!\d)/i)?.[1] || "";
    const childId = crypto.createHash("sha256").update(`${parentUrl}|${index}|${item.heading}`).digest("hex");
    sections.push({ child_id: childId, parent_url: parentUrl, section_index: index, heading: item.heading, ticker_raw: ticker, content: body, classification });
  });
  return sections;
}
module.exports = { defLoadReportTypeSsot, defClassifyInvestmentReport, defSplitMorningBrief };
