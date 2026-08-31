import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sourceRoot = path.join(projectRoot, "standalone");
const htmlPath = path.join(sourceRoot, "index.html");
const cssPath = path.join(sourceRoot, "styles.css");
const jsPath = path.join(sourceRoot, "app.js");
const outputPath = path.join(projectRoot, "public", "VIA_Taiwan_Active_ETF_Consensus_Standalone.html");

const html = fs.readFileSync(htmlPath, "utf8");
const css = fs.readFileSync(cssPath, "utf8");
const js = fs.readFileSync(jsPath, "utf8").replaceAll("</script", "<\\/script");

const bundled = html
  .replace('<link rel="stylesheet" href="styles.css">', `<style>\n${css}\n</style>`)
  .replace('<script src="app.js" defer></script>', `<script>\n${js}\n</script>`);

fs.writeFileSync(outputPath, bundled, "utf8");
console.log(outputPath);
