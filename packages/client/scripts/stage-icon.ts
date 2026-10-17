import { mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// Public assets contain only the canonical icon; game definitions must be served
// through the API rather than copied into a second browser-authoritative catalog.
const root = join(dirname(fileURLToPath(import.meta.url)), "../../..");
const output = join(root, "packages/client/public/icon.svg");
await mkdir(dirname(output), { recursive: true });
await Bun.write(output, Bun.file(join(root, "icon.svg")));
