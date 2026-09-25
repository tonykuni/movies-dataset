import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import { INGEST_PS_REL, ingestRunCommand } from "./via-ingest-ps.ts";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "../../..");

test("mother ingest script is COPY_ONLY 2023→latest, fail-closed, never deletes", () => {
  const ps1 = readFileSync(join(ROOT, INGEST_PS_REL), "utf8");
  assert.match(ps1, /StartYear = 2023/);
  assert.match(ps1, /VIA_db_part1_prices/);
  assert.match(ps1, /VIA_db_part2_chips/);
  assert.match(ps1, /VIA_db_part3_rest/);
  assert.match(ps1, /Github\\movies-dataset\\data\\vdf/);
  assert.match(ps1, /COPY_ONLY/);
  assert.match(ps1, /不刪原件/);
  assert.match(ps1, /VIA_NET/);
  assert.match(ps1, /akshare|AKShare|AK SKIP/i);
  assert.match(ps1, /union_by_name=false/);
  assert.match(ps1, /COMPRESSION ZSTD/);
  assert.match(ps1, /不可關閉/);
  assert.doesNotMatch(ps1, /conda remove|pip uninstall|Remove-Item -Recurse/);
  assert.doesNotMatch(ps1, /FRED_KEY\s*=\s*'[0-9a-fA-F]{32}'/);
  const cmd = ingestRunCommand();
  assert.match(cmd, /VIA-CmdMatrix\.ps1/);
  assert.match(cmd, /禁網/);
  assert.match(cmd, /via-matrix/);
  assert.match(cmd, /via-enter/);
  assert.match(cmd, /via-ingest/);
});
