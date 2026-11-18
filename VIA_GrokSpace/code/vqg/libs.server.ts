import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import type { LibDef } from "./registry";

const modules = fileURLToPath(new URL("../../../node_modules/", import.meta.url));

export type LibraryNote = {
  id: string;
  package: string;
  license: string;
  role: string;
  expands: string;
  version: string;
  status: "看得到" | "看不到";
};

function versionOf(name: string): string {
  const file = join(modules, ...name.split("/"), "package.json");
  if (!existsSync(file)) return "未安裝";
  const parsed = JSON.parse(readFileSync(file, "utf8")) as { version?: string };
  return parsed.version ?? "未標版本";
}

export function resolveLibraries(defs: LibDef[]): LibraryNote[] {
  return defs.map((def) => {
    const version = versionOf(def.package);
    return { ...def, version, status: version === "未安裝" ? "看不到" : "看得到" };
  });
}
