#!/usr/bin/env node
"use strict";

// VIA JavaScript Web Scraping Engine: governed Playwright + Readability lane.
// Legal research only. No CAPTCHA bypass, fingerprint evasion, or access-control bypass.

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { URL } = require("url");
const { defClassifyInvestmentReport, defSplitMorningBrief } = require("./VIA_Investment_Report_Classifier.js");
const { defCompliancePayload, defValidateConsent } = require("./VIA_WebScraping_Compliance.js");

const ENGINE_NAME = "VIA WebScraping Playwright JavaScript Engine";
const ENGINE_VERSION = "1.0.0";
const DEFAULT_TIMEOUT_MS = 30000;
const DEFAULT_DELAY_MS = 1500;
const DEFAULT_MAX_PAGES = 100;
const DEFAULT_MAX_DEPTH = 2;
const BLOCK_RE = /captcha|verify you are human|access denied|unusual traffic|cloudflare.*challenge/i;
const TRACKING_RE = /^(utm_|fbclid$|gclid$|ref$)/i;

function defHasModule(name) {
  try { require.resolve(name); return true; } catch (_) { return false; }
}

function defCapabilities() {
  const groups = {
    browser: ["playwright", "puppeteer", "crawlee"],
    http: ["undici", "axios", "got"],
    dom: ["jsdom", "cheerio", "linkedom", "parse5"],
    extraction: ["@mozilla/readability", "node-html-markdown", "metascraper", "extruct-js"],
    validation: ["ajv", "zod"],
    storage: ["better-sqlite3", "duckdb", "parquetjs-lite"],
    operations: ["p-limit", "bottleneck", "p-retry", "ora"]
    ,compliance: ["robots-parser", "@open-policy-agent/opa-wasm", "ajv", "validator", "libphonenumber-js", "sanitize-html"]
  };
  return Object.fromEntries(Object.entries(groups).map(([group, names]) => [group,
    Object.fromEntries(names.map(name => [name, { available: defHasModule(name) }]))]));
}

function defNormalizeUrl(value, base = undefined) {
  try {
    const url = new URL(value, base);
    if (!["http:", "https:"].includes(url.protocol)) return "";
    url.hash = "";
    [...url.searchParams.keys()].forEach(key => { if (TRACKING_RE.test(key)) url.searchParams.delete(key); });
    url.searchParams.sort();
    return url.toString();
  } catch (_) { return ""; }
}

function defSameScope(candidate, seeds, allowSubdomains = true) {
  const host = new URL(candidate).hostname.toLowerCase();
  return seeds.some(seed => {
    const seedHost = new URL(seed).hostname.toLowerCase();
    return host === seedHost || (allowSubdomains && host.endsWith(`.${seedHost}`));
  });
}

function defSleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
function defHash(value) { return crypto.createHash("sha256").update(value, "utf8").digest("hex"); }
function defAtomicJson(target, value) {
  const temp = `${target}.tmp`;
  fs.writeFileSync(temp, JSON.stringify(value, null, 2), "utf8");
  fs.renameSync(temp, target);
}

async function defRobotsAllowed(targetUrl, userAgent) {
  if (!defHasModule("robots-parser")) return { allowed: false, reason: "ROBOTS_PARSER_MISSING_FAIL_CLOSED" };
  const robotsParser = require("robots-parser");
  const url = new URL(targetUrl);
  const robotsUrl = `${url.protocol}//${url.host}/robots.txt`;
  try {
    const response = await fetch(robotsUrl, { headers: { "user-agent": userAgent } });
    if (!response.ok) return { allowed: false, reason: `ROBOTS_HTTP_${response.status}` };
    const robots = robotsParser(robotsUrl, await response.text());
    return { allowed: robots.isAllowed(targetUrl, userAgent) !== false, reason: "ROBOTS_CHECKED" };
  } catch (error) { return { allowed: false, reason: `ROBOTS_ERROR:${error.message}` }; }
}

function defExtract(html, pageUrl, statusCode, networkJson, piiMode = "partial") {
  const { JSDOM } = require("jsdom");
  const { Readability } = require("@mozilla/readability");
  const dom = new JSDOM(html, { url: pageUrl });
  const document = dom.window.document;
  const meta = key => document.querySelector(`meta[name="${key}"],meta[property="${key}"]`)?.content?.trim() || "";
  const canonical = defNormalizeUrl(document.querySelector('link[rel="canonical"]')?.href || pageUrl, pageUrl);
  const jsonLd = [...document.querySelectorAll('script[type="application/ld+json"]')].flatMap(node => {
    try { const value = JSON.parse(node.textContent); return Array.isArray(value) ? value : [value]; } catch (_) { return []; }
  });
  const firstJsonValue = keys => {
    const visit = value => {
      if (!value || typeof value !== "object") return "";
      for (const key of keys) if (value[key]) return typeof value[key] === "object" ? (value[key].name || "") : String(value[key]);
      for (const child of Object.values(value)) { const found = Array.isArray(child) ? child.map(visit).find(Boolean) : visit(child); if (found) return found; }
      return "";
    };
    return jsonLd.map(visit).find(Boolean) || "";
  };
  const readable = new Readability(document.cloneNode(true)).parse();
  const text = (readable?.textContent || document.body?.textContent || "").replace(/\s+/g, " ").trim();
  const title = meta("og:title") || firstJsonValue(["headline", "name"]) || readable?.title || document.title || "";
  const findings = [];
  if (statusCode >= 400) findings.push(`HTTP_STATUS=${statusCode}`);
  if (!title) findings.push("TITLE_MISSING");
  if (text.length < 80) findings.push("CONTENT_TOO_SHORT");
  if (BLOCK_RE.test(`${title} ${text.slice(0, 3000)}`)) findings.push("BLOCKED_REVIEW_REQUIRED");
  const complianceResult = defCompliancePayload(text, piiMode);
  const isTermsPage = /(?:terms|conditions|legal|服務條款|使用條款)/i.test(pageUrl);
  if (!isTermsPage) complianceResult.compliance.terms_scan = { risk: "NOT_SCANNED_NON_TERMS_PAGE", score: 0, evidence: [], legal_review_required: false, disclaimer: "Automated ToS screening is not a legal opinion." };
  else if (complianceResult.compliance.terms_scan.legal_review_required) findings.push("TOS_PROHIBITION_REVIEW_REQUIRED");
  const safeText = complianceResult.text;
  const reportClassification = defClassifyInvestmentReport(title, safeText);
  const reportSections = defSplitMorningBrief(title, safeText, pageUrl);
  return {
    url: pageUrl, canonical_url: canonical, status_code: statusCode,
    fetched_at_utc: new Date().toISOString(), backend: "playwright-js", title,
    author: meta("author") || firstJsonValue(["author", "creator"]),
    published_at: meta("article:published_time") || firstJsonValue(["datePublished", "dateCreated"]),
    modified_at: meta("article:modified_time") || firstJsonValue(["dateModified"]),
    publisher: firstJsonValue(["publisher"]), description: meta("description") || meta("og:description"),
    text: safeText, content_sha256: defHash(safeText), word_count: safeText.split(/\s+/).filter(Boolean).length,
    links: [...document.querySelectorAll("a[href]")].map(a => defNormalizeUrl(a.href, pageUrl)).filter(Boolean),
    json_ld: jsonLd, network_json: networkJson,
    report_classification: reportClassification, report_sections: reportSections,
    compliance: complianceResult.compliance,
    quality_gate: findings.length ? "REVIEW_REQUIRED" : "PASS", findings
  };
}

async function defRun(config) {
  const consentFindings = defValidateConsent(config.consentToken, config.purpose, config.authorizationBasis);
  if (consentFindings.length) throw new Error(`COMPLIANCE_CONSENT_FAIL_CLOSED:${JSON.stringify(consentFindings)}`);
  for (const required of ["playwright", "jsdom", "@mozilla/readability", "robots-parser"]) {
    if (!defHasModule(required)) throw new Error(`REQUIRED_MODULE_MISSING:${required}`);
  }
  const { chromium, firefox, webkit } = require("playwright");
  const browserType = { chromium, firefox, webkit }[config.browser];
  const browser = await browserType.launch({ headless: config.headless });
  const context = await browser.newContext({ userAgent: config.userAgent });
  const queue = config.urls.map(url => [defNormalizeUrl(url), 0]).filter(x => x[0]);
  const visited = new Set(); const hashes = new Set(); const results = []; const failed = {};
  try {
    while (queue.length && results.length < config.maxPages) {
      const [url, depth] = queue.shift();
      if (visited.has(url) || depth > config.maxDepth || !defSameScope(url, config.urls, config.allowSubdomains)) continue;
      visited.add(url);
      const robots = await defRobotsAllowed(url, config.userAgent);
      if (!robots.allowed) { failed[url] = robots.reason; continue; }
      await defSleep(config.delayMs);
      const page = await context.newPage(); const networkJson = [];
      page.on("response", async response => {
        if ((response.headers()["content-type"] || "").includes("application/json")) {
          try { networkJson.push({ url: response.url(), status: response.status(), data: await response.json() }); } catch (_) {}
        }
      });
      try {
        const response = await page.goto(url, { waitUntil: config.waitUntil, timeout: config.timeoutMs });
        if (config.waitSelector) await page.waitForSelector(config.waitSelector, { timeout: config.timeoutMs });
        for (const selector of config.clickSelectors) await page.locator(selector).first().click({ timeout: 5000 });
        const html = await page.content(); const finalUrl = defNormalizeUrl(page.url());
        const item = defExtract(html, finalUrl, response?.status() || 0, networkJson, config.piiMode);
        if (!hashes.has(item.content_sha256)) { hashes.add(item.content_sha256); results.push(item); }
        const termsLinks = item.links.filter(link => /(?:terms|conditions|legal|服務條款|使用條款)/i.test(link));
        const normalLinks = item.links.filter(link => !termsLinks.includes(link));
        for (const link of termsLinks.reverse()) if (!visited.has(link)) queue.unshift([link, depth + 1]);
        for (const link of normalLinks) if (!visited.has(link)) queue.push([link, depth + 1]);
        if (item.findings.includes("TOS_PROHIBITION_REVIEW_REQUIRED")) { failed[url] = "TOS_PROHIBITION_REVIEW_REQUIRED"; break; }
      } catch (error) { failed[url] = error.message; }
      finally { await page.close(); }
      defAtomicJson(path.join(config.outputDir, "checkpoint.json"), { pending: queue, visited: [...visited], failed });
    }
  } finally { await context.close(); await browser.close(); }
  const jsonl = path.join(config.outputDir, "pages.jsonl");
  fs.writeFileSync(jsonl, results.map(row => JSON.stringify(row)).join("\n") + (results.length ? "\n" : ""), "utf8");
  const summary = { engine: ENGINE_NAME, version: ENGINE_VERSION, saved_pages: results.length, visited: visited.size,
    failed, outputs: { jsonl }, gate: Object.keys(failed).length ? "COMPLETED_WITH_FINDINGS" : "PASS" };
  defAtomicJson(path.join(config.outputDir, "result.json"), summary); return summary;
}

function defParseArgs(argv) {
  const config = { urls: [], outputDir: "via_webscraping_js_output", browser: "chromium", headless: true,
    maxPages: DEFAULT_MAX_PAGES, maxDepth: DEFAULT_MAX_DEPTH, delayMs: DEFAULT_DELAY_MS,
    timeoutMs: DEFAULT_TIMEOUT_MS, waitUntil: "domcontentloaded", waitSelector: "", clickSelectors: [],
    allowSubdomains: true, userAgent: "VIA-ResearchBot/1.0 (+local governed research crawler)", consentToken: "", purpose: "", authorizationBasis: "", piiMode: "partial" };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (/^https?:\/\//.test(arg)) config.urls.push(arg);
    else if (arg === "--output-dir") config.outputDir = argv[++i];
    else if (arg === "--browser") config.browser = argv[++i];
    else if (arg === "--max-pages") config.maxPages = Math.max(1, Number(argv[++i]));
    else if (arg === "--max-depth") config.maxDepth = Math.max(0, Number(argv[++i]));
    else if (arg === "--delay") config.delayMs = Math.max(0, Number(argv[++i]) * 1000);
    else if (arg === "--wait-selector") config.waitSelector = argv[++i];
    else if (arg === "--click") config.clickSelectors.push(argv[++i]);
    else if (arg === "--headed") config.headless = false;
    else if (arg === "--consent-token") config.consentToken = argv[++i];
    else if (arg === "--purpose") config.purpose = argv[++i];
    else if (arg === "--authorization-basis") config.authorizationBasis = argv[++i];
    else if (arg === "--pii-mode") config.piiMode = argv[++i];
  }
  return config;
}

function defSelfTest() {
  for (const required of ["playwright", "jsdom", "@mozilla/readability", "robots-parser"]) {
    if (typeof defHasModule(required) !== "boolean") throw new Error("CAPABILITY_TEST_FAILED");
  }
  if (defNormalizeUrl("https://example.com/a?utm_source=x&b=2") !== "https://example.com/a?b=2") throw new Error("URL_TEST_FAILED");
  if (!defSameScope("https://sub.example.com/a", ["https://example.com"], true)) throw new Error("SCOPE_TEST_FAILED");
  console.log("def JS_SELF_TEST: PASS");
}

async function defMain() {
  const argv = process.argv.slice(2);
  if (argv.includes("--list-capabilities")) { console.log(JSON.stringify(defCapabilities(), null, 2)); return; }
  if (argv.includes("--self-test")) { defSelfTest(); if (!argv.some(x => /^https?:\/\//.test(x))) return; }
  const config = defParseArgs(argv); fs.mkdirSync(config.outputDir, { recursive: true });
  if (!config.urls.length) throw new Error("NO_VALID_URL");
  console.log(JSON.stringify(await defRun(config), null, 2));
}

defMain().catch(error => { console.error(`def ERROR: ${error.message}`); process.exitCode = 1; });
