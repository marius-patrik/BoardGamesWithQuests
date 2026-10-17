/** Browser-level acceptance for the published documentation controls.
 *
 * Reuses the pinned Mermaid CLI's Chromium/Puppeteer installation, so the
 * documentation preview performs genuine user-visible interaction tests
 * without introducing another browser runtime or production dependency.
 */
import { createServer } from "node:http";
import { createRequire } from "node:module";
import { execFileSync } from "node:child_process";
import { readFile, stat } from "node:fs/promises";
import { join, resolve, relative, extname, sep } from "node:path";
import assert from "node:assert/strict";

const root = resolve("site");
const globalModules = execFileSync("npm", ["root", "-g"], { encoding: "utf8" }).trim();
const requireFromCli = createRequire(join(globalModules, "@mermaid-js/mermaid-cli/package.json"));
const puppeteer = requireFromCli("puppeteer");

const mime = {
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml",
  ".json": "application/json",
};

const server = createServer(async (request, response) => {
  try {
    const pathname = decodeURIComponent(new URL(request.url, "http://localhost").pathname);
    const target = resolve(root, "." + pathname, pathname.endsWith("/") ? "index.html" : "");
    const traversal = relative(root, target);
    if (traversal.startsWith("..") || traversal.startsWith(sep)) {
      response.writeHead(403).end();
      return;
    }
    const info = await stat(target);
    const file = info.isDirectory() ? join(target, "index.html") : target;
    response.writeHead(200, { "Content-Type": mime[extname(file)] || "application/octet-stream" });
    response.end(await readFile(file));
  } catch {
    response.writeHead(404).end();
  }
});

await new Promise(resolveReady => server.listen(0, "127.0.0.1", resolveReady));
const base = "http://127.0.0.1:" + server.address().port;
let browser;
try {
  browser = await puppeteer.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });
  const page = await browser.newPage();
  page.on("framenavigated", frame => {
    if (frame === page.mainFrame()) console.log("Document navigated:", frame.url());
  });
  await page.setViewport({ width: 1440, height: 900 });
  console.log("Checking centered/full-width layout");
  await page.goto(base + "/", { waitUntil: "load" });
  await page.waitForSelector("[data-layout-toggle]");

  // Switching the layout must resize the real reading pane, not the browser.
  const centered = await page.$eval(".content", el => el.getBoundingClientRect().width);
  await page.click("[data-layout-toggle]");
  const wide = await page.$eval(".content", el => el.getBoundingClientRect().width);
  assert(wide > centered + 70, "Full-width mode did not expand the actual reader");
  assert.equal(await page.$eval("html", el => el.dataset.layout), "wide");
  console.log("Checking layout persistence across page navigation");
  await page.goto(base + "/architecture/diagrams/implementation-uml/", { waitUntil: "load" });
  assert.equal(await page.$eval("html", el => el.dataset.layout), "wide", "Width mode was not saved");
  await page.click("[data-layout-toggle]");

  // Every section is an actual native disclosure with independently mutable state.
  console.log("Checking independently collapsible navigation groups");
  const group = await page.$("details[data-nav-section]");
  assert(group, "No collapsible sidebar sections were rendered");
  const initial = await group.evaluate(el => el.open);
  const summary = await page.$("details[data-nav-section] > summary");
  assert(summary, "No disclosure summary was rendered");
  await summary.click();
  assert.equal(await group.evaluate(el => el.open), !initial, "Section did not collapse");
  await summary.click();

  // Desktop hamburger must remove the left grid column, then restore it.
  console.log("Checking hamburger collapse");
  await page.click("[data-nav-toggle]");
  assert.equal(await page.$eval("html", el => el.dataset.navCollapsed), "true");
  await page.click("[data-nav-toggle]");
  assert.notEqual(await page.$eval("html", el => el.dataset.navCollapsed), "true");

  // The original image, rather than a fabricated Mermaid substitute, opens
  // as a full-viewport modal. Escape must return the same viewer to the page.
  console.log("Checking original image fullscreen modal");
  await page.goto(base + "/repository-files/agents/notes/images/GUI_mockup.svg/", {
    waitUntil: "load",
  });
  await page.waitForSelector('[aria-label="Expand image in modal"]');
  const inlineSize = await page.$eval(".diagram-viewer__viewport", el => el.getBoundingClientRect().width);
  await page.click('[aria-label="Expand image in modal"]');
  assert.equal(await page.$eval("dialog.diagram-modal", el => el.open), true);
  const expandedSize = await page.$eval(".diagram-modal .diagram-viewer__viewport", el => el.getBoundingClientRect().width);
  assert(expandedSize > inlineSize + 100, "Image modal did not expand beyond reading pane");
  await page.keyboard.press("Escape");
  await page.waitForFunction(() => !document.querySelector("dialog.diagram-modal"));
  assert(await page.$(".diagram-viewer__viewport"), "Image viewer was not restored after modal dismissal");

  // The generated implementation UML shares the same modal behavior.
  console.log("Checking generated implementation UML fullscreen modal");
  await page.goto(base + "/architecture/diagrams/implementation-uml/", {
    waitUntil: "load",
  });
  await page.waitForSelector('[aria-label="Expand image in modal"]');
  await page.click('[aria-label="Expand image in modal"]');
  assert.equal(await page.$eval("dialog.diagram-modal", el => el.open), true);
  await page.click('[aria-label="Close expanded image"]');
  await page.waitForFunction(() => !document.querySelector("dialog.diagram-modal"));
  console.log("Documentation layout, nested navigation and image/UML modals verified in Chromium");
} finally {
  await browser?.close();
  await new Promise(done => server.close(done));
}
