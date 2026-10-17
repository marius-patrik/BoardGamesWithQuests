import { readdir, mkdir } from "node:fs/promises";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "../../..");
const publicDir = join(here, "../public");
await mkdir(join(publicDir, "config"), { recursive: true });
await Bun.write(join(publicDir, "icon.svg"), Bun.file(join(root, "icon.svg")));
const files = (await readdir(join(root, "config"))).filter((file) => file.endsWith(".json")).sort();
const catalog = [];
for (const file of files) {
  const data = await Bun.file(join(root, "config", file)).json();
  catalog.push({ file, id: data.name, title: data.title, board: data.board && { rows: data.board.rows, columns: data.board.columns } });
  await Bun.write(join(publicDir, "config", file), JSON.stringify(data));
}
await Bun.write(join(publicDir, "config", "catalog.json"), JSON.stringify(catalog));
