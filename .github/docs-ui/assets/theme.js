/**
 * Repository and branch selectors. The selected value comes from the current URL, not
 * the manifest publisher metadata.
 * Compute the shared site root from the absolute CSS URL; it works on nested pages
 * and in PR/branch previews alike. Every navigation target is a published site URL.
 */
(function () {
  "use strict";

  var controls = document.querySelector("[data-switcher]");
  var css = document.querySelector('link[rel="stylesheet"][href*="assets/theme.css"]');
  if (!controls || !css) return;

  var cssUrl = new URL(css.href, window.location.href);
  var buildRoot = cssUrl.href.replace(/assets\/theme\.css(?:[?#].*)?$/, "");
  var siteRoot = buildRoot.replace(/(?:pr-\d+|branch\/[^/]+)\/$/, "");
  var manifestUrl = new URL("versions.json", siteRoot).href;
  var projectSelect = controls.querySelector("[data-switcher-projects]");
  var versionSelect = controls.querySelector("[data-switcher-versions]");
  var activePath = buildRoot.slice(siteRoot.length).replace(/\/$/, "");
  var activeLabel = activePath.startsWith("pr-")
    ? "PR #" + activePath.slice(3)
    : activePath.startsWith("branch/")
    ? activePath.slice("branch/".length)
    : "main";
  // Show the correct build immediately, before the manifest is fetched.
  versionSelect.options[0].textContent = activeLabel;

  function normalizedSite(value) {
    try {
      var url = new URL(value, siteRoot);
      return url.origin.toLowerCase() + url.pathname.replace(/\/*$/, "/").toLowerCase();
    } catch (error) {
      return "";
    }
  }

  function populate(select, entries, selected) {
    select.replaceChildren();
    entries.forEach(function (entry) {
      var option = document.createElement("option");
      option.textContent = entry.name;
      option.value = entry.url;
      option.selected = entry.id === selected;
      select.appendChild(option);
    });
  }

  // Both controls are functional even if a site has no manifest.
  populate(projectSelect, [
    { name: controls.dataset.siteName, url: siteRoot, id: "this" }
  ], "this");
  projectSelect.addEventListener("change", function () {
    if (projectSelect.value) window.location.assign(projectSelect.value);
  });
  versionSelect.addEventListener("change", function () {
    if (versionSelect.value) window.location.assign(versionSelect.value);
  });

  fetch(manifestUrl, { cache: "no-store" })
    .then(function (response) {
      if (!response.ok) throw new Error("No published build manifest");
      return response.json();
    })
    .then(function (manifest) {
      var versionList = (manifest.versions || []).filter(function (entry) {
        return typeof entry.path === "string" && typeof entry.name === "string";
      }).map(function (entry) {
        return {
          name: entry.name,
          path: entry.path.replace(/^\/+|\/+$/g, ""),
          id: entry.path.replace(/^\/+|\/+$/g, ""),
          url: new URL(entry.path ? entry.path.replace(/^\/+|\/+$/g, "") + "/" : "./", siteRoot).href
        };
      });

      // CSS locates the current build even on deep pages or when a newly
      // published preview has not reached the root manifest yet.
      if (!versionList.some(function (entry) { return entry.id === activePath; })) {
        versionList.push({ name: activeLabel, path: activePath, id: activePath, url: buildRoot });
      }
      populate(versionSelect, versionList, activePath);

      var projects = (manifest.projects || []).filter(function (entry) {
        return entry && typeof entry.name === "string" && typeof entry.url === "string";
      }).map(function (entry) {
        return { name: entry.name, url: new URL(entry.url, siteRoot).href, id: normalizedSite(entry.url) };
      });
      var current = normalizedSite(siteRoot);
      if (!projects.some(function (entry) { return entry.id === current; })) {
        projects.unshift({ name: controls.dataset.siteName, url: siteRoot, id: current });
      }
      populate(projectSelect, projects, current);
    })
    .catch(function () {
      // Continue showing the correct current repository rather than a broken control.
    });
})();
