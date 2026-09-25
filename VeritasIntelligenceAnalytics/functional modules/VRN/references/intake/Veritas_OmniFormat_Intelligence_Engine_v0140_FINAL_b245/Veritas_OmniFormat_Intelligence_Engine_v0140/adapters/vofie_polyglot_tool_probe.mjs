#!/usr/bin/env node
/** Veritas VOFIE v1.2 JavaScript CPU tool bridge. Read-only and dependency-free. */

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import vm from "node:vm";


// ---------------------------------------------------------------------------
// 0. Parameters and immutable policy
// ---------------------------------------------------------------------------

const BRIDGE_CONTRACT = "veritas.vofie-javascript-tool-bridge/1.2";
const EXPECTED_TOOL_COUNT = 20;
const SOURCE_POLICY = "READ_ONLY_NO_DELETE_NO_MOVE_NO_CANONICAL_MUTATION";
const LOCAL_BIN_SEGMENTS = ["node_modules", ".bin"];
const WINDOWS_EXTENSIONS = [".cmd", ".exe", ".bat", ".ps1", ""];
const POSIX_EXTENSIONS = [""];


// ---------------------------------------------------------------------------
// 1. Argument parsing
// ---------------------------------------------------------------------------

function parseArguments(argv) {
  const options = { catalog: "", target: "", report: "", selfTest: false };
  for (let index = 0; index < argv.length; index += 1) {
    const item = argv[index];
    if (item === "--catalog") options.catalog = argv[++index] ?? "";
    else if (item === "--target") options.target = argv[++index] ?? "";
    else if (item === "--report") options.report = argv[++index] ?? "";
    else if (item === "--self-test") options.selfTest = true;
    else throw new Error(`Unknown argument: ${item}`);
  }
  return options;
}


// ---------------------------------------------------------------------------
// 2. Catalog and filesystem detection
// ---------------------------------------------------------------------------

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function validateCatalog(catalog) {
  const rows = catalog.javascript_top20;
  const ids = new Set(rows?.map((row) => row.tool_id));
  const ranks = rows?.map((row) => row.rank).sort((a, b) => a - b) ?? [];
  const expectedRanks = Array.from({ length: EXPECTED_TOOL_COUNT }, (_, index) => index + 1);
  const pass = Array.isArray(rows)
    && rows.length === EXPECTED_TOOL_COUNT
    && ids.size === EXPECTED_TOOL_COUNT
    && JSON.stringify(ranks) === JSON.stringify(expectedRanks)
    && rows.every((row) => row.cpu_supported === true && row.license && row.fallback);
  return { gate: pass ? "PASS" : "FAIL", tool_count: rows?.length ?? 0, unique_ids: ids.size };
}

function executableExtensions() {
  return process.platform === "win32" ? WINDOWS_EXTENSIONS : POSIX_EXTENSIONS;
}

function isExecutable(filePath) {
  try {
    fs.accessSync(filePath, fs.constants.X_OK);
    return fs.statSync(filePath).isFile();
  } catch {
    return false;
  }
}

function resolveCommand(command, projectRoot) {
  if (!command) return "";
  const candidates = [];
  const localBin = path.join(projectRoot, ...LOCAL_BIN_SEGMENTS);
  for (const extension of executableExtensions()) candidates.push(path.join(localBin, `${command}${extension}`));
  for (const directory of (process.env.PATH ?? "").split(path.delimiter).filter(Boolean)) {
    for (const extension of executableExtensions()) candidates.push(path.join(directory, `${command}${extension}`));
  }
  return candidates.find(isExecutable) ?? "";
}

function detectNodePackage(packageName, projectRoot) {
  if (!packageName) return "";
  const packagePath = path.join(projectRoot, "node_modules", ...packageName.split("/"), "package.json");
  return fs.existsSync(packagePath) ? packagePath : "";
}

function detectTools(catalog, projectRoot) {
  return catalog.javascript_top20.map((tool) => {
    const commandPath = resolveCommand(tool.command, projectRoot);
    const packagePath = detectNodePackage(tool.package, projectRoot);
    const builtinNode = tool.tool_id === "JS-TOOL-001" ? process.execPath : "";
    const resolved = builtinNode || commandPath || packagePath;
    return {
      tool_id: tool.tool_id,
      rank: tool.rank,
      name: tool.name,
      status: resolved ? "AVAILABLE" : "NOT_INSTALLED",
      resolved_path: resolved,
      fallback: tool.fallback,
      source_mutated: false,
    };
  });
}


// ---------------------------------------------------------------------------
// 3. Safe syntax and structure checks
// ---------------------------------------------------------------------------

function structuralScan(text) {
  const stack = [];
  const pairs = { ")": "(", "]": "[", "}": "{" };
  const openers = new Set(Object.values(pairs));
  let quote = "";
  let escaped = false;
  for (const character of text) {
    if (escaped) {
      escaped = false;
      continue;
    }
    if (quote && character === "\\") {
      escaped = true;
      continue;
    }
    if (quote) {
      if (character === quote) quote = "";
      continue;
    }
    if (["'", "\"", "`"].includes(character)) {
      quote = character;
      continue;
    }
    if (openers.has(character)) stack.push(character);
    else if (pairs[character]) {
      if (stack.pop() !== pairs[character]) return { gate: "FAIL", reason: `unbalanced ${character}` };
    }
  }
  return { gate: stack.length === 0 && !quote ? "PASS" : "FAIL", reason: stack.length ? "unclosed bracket" : quote ? "unclosed quote" : "" };
}

function checkTarget(targetPath) {
  if (!targetPath) return { status: "SKIP", reason: "NO_TARGET" };
  const resolved = path.resolve(targetPath);
  const before = fs.statSync(resolved).size;
  const content = fs.readFileSync(resolved, "utf8");
  const structural = structuralScan(content);
  let parser = { gate: "SKIP", reason: "extension not directly supported by vm.Script" };
  if ([".js", ".cjs"].includes(path.extname(resolved).toLowerCase())) {
    try {
      new vm.Script(content, { filename: resolved });
      parser = { gate: "PASS", reason: "" };
    } catch (error) {
      parser = { gate: "FAIL", reason: String(error.message ?? error) };
    }
  }
  const after = fs.statSync(resolved).size;
  return { status: structural.gate === "PASS" && parser.gate !== "FAIL" && before === after ? "PASS" : "FAIL", structural, parser, source_mutated: before !== after };
}


// ---------------------------------------------------------------------------
// 4. Report and self-test
// ---------------------------------------------------------------------------

function runSelfTest() {
  const valid = structuralScan("function ok(value) { return [value]; }");
  const invalid = structuralScan("function broken( {");
  let parserPass = false;
  try {
    new vm.Script("const answer = 42;");
    parserPass = true;
  } catch {
    parserPass = false;
  }
  const passed = valid.gate === "PASS" && invalid.gate === "FAIL" && parserPass;
  return { gate: passed ? "PASS" : "FAIL", passed: passed ? 3 : 0, failed: passed ? 0 : 1 };
}

function buildReport(catalog, projectRoot, targetPath) {
  const catalogCheck = validateCatalog(catalog);
  const tools = detectTools(catalog, projectRoot);
  const target = checkTarget(targetPath);
  const gate = catalogCheck.gate === "PASS" && target.status !== "FAIL" ? "PASS" : "FAIL";
  return {
    contract: BRIDGE_CONTRACT,
    gate,
    cpu: { architecture: os.arch(), logical_cores: os.cpus().length, supported: true },
    source_policy: SOURCE_POLICY,
    catalog: catalogCheck,
    summary: {
      total: tools.length,
      available: tools.filter((tool) => tool.status === "AVAILABLE").length,
      not_installed: tools.filter((tool) => tool.status === "NOT_INSTALLED").length,
    },
    tools,
    target,
  };
}

function writeReport(reportPath, payload) {
  const resolved = path.resolve(reportPath);
  fs.mkdirSync(path.dirname(resolved), { recursive: true });
  fs.writeFileSync(resolved, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

function main() {
  const options = parseArguments(process.argv.slice(2));
  if (options.selfTest) {
    const result = runSelfTest();
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    return result.gate === "PASS" ? 0 : 1;
  }
  if (!options.catalog) throw new Error("--catalog is required unless --self-test is used");
  const catalogPath = path.resolve(options.catalog);
  const catalog = readJson(catalogPath);
  const projectRoot = path.dirname(path.dirname(catalogPath));
  const report = buildReport(catalog, projectRoot, options.target);
  if (options.report) writeReport(options.report, report);
  process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
  return report.gate === "PASS" ? 0 : 1;
}

process.exitCode = main();

