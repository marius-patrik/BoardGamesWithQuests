/** End-to-end browser checks against the actual emitted documentation artifact.
 * No PRD path, image filename, UML class, or fixed diagram count is assumed.
 * Uses the Chromium runtime already installed for the Mermaid compiler.
 */
import { createServer } from "node:http";
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { readFile, readdir, stat } from "node:fs/promises";
import { join, resolve, relative, extname, sep } from "node:path";
import assert from "node:assert/strict";

const root = resolve("site");
const modules = execFileSync("npm", ["root", "-g"], { encoding: "utf8" }).trim();
const requireFromCli = createRequire(join(modules, "@mermaid-js/mermaid-cli/package.json"));
const puppeteer = requireFromCli("puppeteer");

const mime = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".svg": "image/svg+xml",
  ".json": "application/json",
};

const server = createServer(async (request, response) => {
  try {
    const pathname = decodeURIComponent(new URL(request.url, "http://localhost").pathname);
    const target = resolve(root, "." + pathname, pathname.endsWith("/") ? "index.html" : "");
    const rel = relative(root, target);
    if (rel.startsWith("..") || rel.startsWith(sep)) {
      response.writeHead(403).end();
      return;
    }
    const file = (await stat(target)).isDirectory() ? join(target, "index.html") : target;
    response.writeHead(200, { "Content-Type": mime[extname(file)] || "application/octet-stream" });
    response.end(await readFile(file));
  } catch {
    response.writeHead(404).end();
  }
});

async function htmlPages(dir) {
  const result = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) result.push(...await htmlPages(path));
    else if (entry.name === "index.html") result.push(path);
  }
  return result;
}

await new Promise(ok => server.listen(0, "127.0.0.1", ok));
const base = "http://127.0.0.1:" + server.address().port;
let browser;
try {
  browser = await puppeteer.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });
  const homepage = await page.goto(base + "/", { waitUntil: "load" });
  assert.equal(homepage.status(), 200, "The generated documentation home page is not served");

  // UI contract: layout, preference persistence, navigation and theme.
  await page.waitForSelector("[data-layout-toggle]");
  const centered = await page.$eval(".content", el => el.getBoundingClientRect().width);
  await page.click("[data-layout-toggle]");
  const expanded = await page.$eval(".content", el => el.getBoundingClientRect().width);
  assert(expanded > centered + 70, "Full-width toggle did not expand the reading pane");
  await page.reload({ waitUntil: "load" });
  assert.equal(await page.$eval("html", el => el.dataset.layout), "wide");
  await page.click("[data-layout-toggle]");
  await page.click("[data-nav-toggle]");
  assert.equal(await page.$eval("html", el => el.dataset.navCollapsed), "true");
  await page.click("[data-nav-toggle]");
  assert.notEqual(await page.$eval("html", el => el.dataset.navCollapsed), "true");

  const disclosure = await page.$("details[data-nav-section]");
  if (disclosure) {
    const original = await disclosure.evaluate(el => el.open);
    await disclosure.$("summary").then(summary => summary.click());
    assert.equal(await disclosure.evaluate(el => el.open), !original);
  }
  const color = await page.$eval("html", el => el.dataset.theme);
  await page.click("[data-theme-toggle]");
  assert.notEqual(await page.$eval("html", el => el.dataset.theme), color);
  await page.click("[data-theme-toggle]");

  // Discover a genuine rendered diagram page; no particular document needs to exist.
  let viewerPage = null;
  for (const candidate of await htmlPages(root)) {
    const html = await readFile(candidate, "utf8");
    if (html.includes("data-diagram-viewer") && html.includes("Rendered Mermaid architecture diagram")) {
      viewerPage = candidate;
      break;
    }
  }

  if (viewerPage) {
    const location = relative(root, viewerPage).split(sep).map(encodeURIComponent).join("/");
    const rendered = await page.goto(base + "/" + location, { waitUntil: "load" });
    assert.equal(rendered.status(), 200);
    await page.waitForSelector('[aria-label="Expand image in modal"]');
    assert(await page.$("[data-diagram-viewer] img"), "Rendered diagram is missing its SVG image");
    const before = await page.$eval(".diagram-viewer__zoom-label", el => el.textContent);
    await page.click('[aria-label="Zoom in"]');
    const after = await page.$eval(".diagram-viewer__zoom-label", el => el.textContent);
    assert.notEqual(after, before, "Zoom control did not change diagram scale");
    await page.click('[aria-label="Expand image in modal"]');
    assert.equal(await page.$eval("dialog.diagram-modal", el => el.open), true);
    await page.keyboard.press("Escape");
    await page.waitForFunction(() => !document.querySelector("dialog.diagram-modal"));
    assert(await page.$(".diagram-viewer__viewport"), "Diagram viewer was not restored");
  } else {
    console.log("No published diagrams in this checkout: skipping viewer interaction.");
  }

  console.log("Documentation layout, navigation, theme and discovered diagram interactions passed.");
} finally {
  await browser?.close();
  await new Promise(done => server.close(done));
}
