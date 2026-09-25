import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

test("VIA-Ingest-2023.ps1 is paste-safe COPY_ONLY 2023→latest fail-closed", () => {
  const t = readFileSync("scripts/VIA-Ingest-2023.ps1", "utf8");
  assert.match(t, /COPY_ONLY/);
  assert.match(t, /\$StartYear = 2023/);
  assert.match(t, /VIA_db_part1_prices/);
  assert.match(t, /VIA_db_part2_chips/);
  assert.match(t, /VIA_db_part3_rest/);
  assert.match(t, /Github\\movies-dataset\\data\\vdf/);
  assert.match(t, /akshare_call SKIP/);
  assert.match(t, /union_by_name=false/);
  assert.match(t, /不刪原件/);
  assert.match(t, /不可關閉/);
  assert.doesNotMatch(t, /param\(/);
  assert.doesNotMatch(t, /conda remove|pip uninstall|Stop-Process|Remove-Item/i);
  assert.doesNotMatch(t, /union_by_name=true/);
  assert.doesNotMatch(t, /VIA_FRED_KEY.*=.*[0-9a-fA-F]{32}/);
});

test("VIA-Ingest-2023.cmd launches pwsh and never runs PS syntax in cmd", () => {
  const t = readFileSync("scripts/VIA-Ingest-2023.cmd", "utf8");
  assert.match(t, /pwsh -NoLogo -NoExit/);
  assert.match(t, /Github\\VIA-Ingest-2023.ps1/);
  assert.doesNotMatch(t, /\$args -contains/);
  assert.doesNotMatch(t, /conda remove|pip uninstall|Stop-Process/i);
});
