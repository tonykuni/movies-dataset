#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { unified } from "unified";
import remarkParse from "remark-parse";
import remarkGfm from "remark-gfm";
import remarkFrontmatter from "remark-frontmatter";
import { fromMarkdown } from "mdast-util-from-markdown";
import GithubSlugger from "github-slugger";

const TOC_START = "<!-- markdown-editing-engine:toc:start -->";
const TOC_END = "<!-- markdown-editing-engine:toc:end -->";
const ACTIONS = new Set(["signature", "validate", "toc", "index"]);

function defSha256(value) {
  return crypto.createHash("sha256").update(value, "utf8").digest("hex");
}

function defNormalizeForSignature(source) {
  return source.replace(/^\uFEFF/, "").replace(/^(#{1,6})(?=[^#\s])/gm, "$1 ");
}

function defSemanticText(value) {
  return value.replace(/\s+/gu, "");
}

function defParse(source) {
  const parser = unified().use(remarkParse).use(remarkGfm).use(remarkFrontmatter, ["yaml", "toml"]);
  const tree = parser.parse(source);
  fromMarkdown(source);
  return tree;
}

function defNodeText(node) {
  if (typeof node.value === "string") return node.value;
  if (!Array.isArray(node.children)) return "";
  return node.children.map(defNodeText).join("");
}

function defWalk(node, visit) {
  visit(node);
  if (Array.isArray(node.children)) {
    for (const child of node.children) defWalk(child, visit);
  }
}

function defSignature(source) {
  const tree = defParse(defNormalizeForSignature(source));
  const signature = {
    headings: [],
    links: [],
    images: [],
    codeBlocks: [],
    inlineCode: [],
    frontmatter: [],
    html: [],
    textContentHash: "",
    parser: "remark-gfm+mdast-util-from-markdown",
  };
  const textValues = [];
  defWalk(tree, (node) => {
    if (node.type === "heading") signature.headings.push({ depth: node.depth, text: defNodeText(node) });
    if (node.type === "link") signature.links.push({ text: defNodeText(node), url: node.url, title: node.title ?? null });
    if (node.type === "image") signature.images.push({ text: node.alt ?? "", url: node.url, title: node.title ?? null });
    if (node.type === "code") signature.codeBlocks.push({ lang: node.lang ?? "", meta: node.meta ?? "", hash: defSha256(node.value) });
    if (node.type === "inlineCode") signature.inlineCode.push(node.value);
    if (node.type === "yaml" || node.type === "toml") signature.frontmatter.push(defSha256(node.value));
    if (node.type === "html") signature.html.push(defSha256(node.value));
    if (node.type === "text") textValues.push(node.value);
  });
  signature.textContentHash = defSha256(defSemanticText(textValues.join("\u241e")));
  return signature;
}

function defHeadingRecords(tree) {
  const slugger = new GithubSlugger();
  const records = [];
  defWalk(tree, (node) => {
    if (node.type !== "heading") return;
    const text = defNodeText(node).trim();
    records.push({ depth: node.depth, text, slug: slugger.slug(text), endLine: node.position?.end?.line ?? 1 });
  });
  return records;
}

function defTocBlock(records) {
  const included = records.filter((record, index) => !(index === 0 && record.depth === 1) && record.depth >= 2);
  const minimumDepth = included.length ? Math.min(...included.map((item) => item.depth)) : 2;
  const lines = included.map((item) => `${"  ".repeat(Math.max(0, item.depth - minimumDepth))}- [${item.text}](#${item.slug})`);
  return [TOC_START, "", "## 目錄", "", ...lines, "", TOC_END].join("\n");
}

function defApplyToc(source) {
  const start = source.indexOf(TOC_START);
  const end = source.indexOf(TOC_END);
  let headingSource = source;
  if (start >= 0 && end > start) {
    headingSource = `${source.slice(0, start)}${source.slice(end + TOC_END.length)}`;
  }
  const tree = defParse(defNormalizeForSignature(headingSource));
  const records = defHeadingRecords(tree);
  const block = defTocBlock(records);
  if (start >= 0 && end > start) {
    return `${source.slice(0, start)}${block}${source.slice(end + TOC_END.length)}`;
  }
  const firstHeading = records[0];
  if (!firstHeading) return `${block}\n\n${source}`;
  const lines = source.split(/\r?\n/);
  const insertionIndex = Math.min(lines.length, firstHeading.endLine);
  lines.splice(insertionIndex, 0, "", block, "");
  return lines.join("\n").replace(/\n{4,}/g, "\n\n\n");
}

function defIndex(source, inputPath) {
  const signature = defSignature(source);
  return {
    source: path.resolve(inputPath),
    sha256: defSha256(source),
    generatedAt: new Date().toISOString(),
    ...signature,
  };
}

function defMain() {
  const [action, inputPath, outputPath] = process.argv.slice(2);
  if (!ACTIONS.has(action) || !inputPath) {
    throw new Error("Usage: ast_reorganizer.mjs <signature|validate|toc|index> <input.md> [output.json]");
  }
  const source = fs.readFileSync(inputPath, "utf8");
  if (action === "signature") {
    process.stdout.write(`${JSON.stringify(defSignature(source))}\n`);
    return;
  }
  if (action === "validate") {
    const signature = defSignature(source);
    process.stdout.write(`${JSON.stringify({ ok: true, parser: signature.parser })}\n`);
    return;
  }
  if (action === "toc") {
    const updated = defApplyToc(source);
    fs.writeFileSync(inputPath, updated.endsWith("\n") ? updated : `${updated}\n`, "utf8");
    process.stdout.write(`${JSON.stringify({ ok: true, changed: updated !== source })}\n`);
    return;
  }
  const indexPayload = defIndex(source, inputPath);
  if (outputPath) fs.writeFileSync(outputPath, `${JSON.stringify(indexPayload, null, 2)}\n`, "utf8");
  else process.stdout.write(`${JSON.stringify(indexPayload, null, 2)}\n`);
}

try {
  defMain();
} catch (error) {
  process.stderr.write(`${error.stack ?? error.message}\n`);
  process.exitCode = 2;
}
