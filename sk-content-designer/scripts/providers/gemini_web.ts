import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const currentDir = dirname(fileURLToPath(import.meta.url));
const vendorMain = resolve(
  currentDir,
  "../../../../../vendors/mirrors/baoyu-skills/skills/baoyu-danger-gemini-web/scripts/main.ts",
);

if (!existsSync(vendorMain)) {
  console.error(`Missing Gemini Web vendor script: ${vendorMain}`);
  process.exit(2);
}

const result = Bun.spawnSync({
  cmd: [process.execPath, vendorMain, ...process.argv.slice(2)],
  stdin: "inherit",
  stdout: "inherit",
  stderr: "inherit",
});

process.exit(result.exitCode ?? 1);
