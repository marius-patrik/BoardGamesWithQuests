/*
 * Omnis documentation theme behaviour.
 *
 * Three small things, no dependencies: the colour-scheme toggle, the mobile navigation, and search
 * over the index the search plugin already emits. Search is a scored substring match rather than a
 * bundled index library — the corpus here is a few dozen pages, and a full-text engine would be more
 * bytes than the documents it searches.
 */

(function () {
  "use strict";

  var root = document.documentElement;

  /* ── Colour scheme ──────────────────────────────────────────────────── */

  var toggle = document.querySelector("[data-theme-toggle]");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try {
        localStorage.setItem("docs-theme", next);
      } catch (e) {
        /* Private browsing: the choice simply does not persist. */
      }
    });
  }

  /* ── Mobile navigation ──────────────────────────────────────────────── */

  var navToggle = document.querySelector("[data-nav-toggle]");
  var sidebar = document.querySelector("[data-nav]");
  if (navToggle && sidebar) {
    navToggle.addEventListener("click", function () {
      sidebar.classList.toggle("is-open");
    });
    sidebar.addEventListener("click", function (event) {
      if (event.target.closest("a")) sidebar.classList.remove("is-open");
    });
  }

  /* ── Table of contents highlighting ─────────────────────────────────── */

  var tocLinks = Array.prototype.slice.call(document.querySelectorAll(".toc__list a"));
  if (tocLinks.length && "IntersectionObserver" in window) {
    var byId = {};
    tocLinks.forEach(function (link) {
      var id = decodeURIComponent(link.getAttribute("href") || "").replace(/^#/, "");
      if (id) byId[id] = link;
    });

    var visible = new Set();
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) visible.add(entry.target.id);
          else visible.delete(entry.target.id);
        });
        var first = tocLinks.find(function (link) {
          var id = decodeURIComponent(link.getAttribute("href") || "").replace(/^#/, "");
          return visible.has(id);
        });
        tocLinks.forEach(function (link) {
          link.classList.toggle("is-active", link === first);
        });
      },
      { rootMargin: "-80px 0px -70% 0px" }
    );

    Object.keys(byId).forEach(function (id) {
      var heading = document.getElementById(id);
      if (heading) observer.observe(heading);
    });
  }

  /* ── Search ─────────────────────────────────────────────────────────── */

  var input = document.getElementById("search-input");
  var panel = document.getElementById("search-results");
  if (!input || !panel) return;

  var baseEl = document.getElementById("search-base");
  var base = "";
  try {
    base = JSON.parse(baseEl.textContent) || "";
  } catch (e) {
    base = "";
  }
  if (base && base.slice(-1) !== "/") base += "/";

  var docs = null;
  var loading = false;
  var activeIndex = -1;

  function load() {
    if (docs || loading) return Promise.resolve();
    loading = true;
    return fetch(base + "search/search_index.json")
      .then(function (response) {
        return response.json();
      })
      .then(function (data) {
        docs = (data && data.docs) || [];
      })
      .catch(function () {
        docs = [];
      })
      .finally(function () {
        loading = false;
      });
  }

  function score(doc, needle) {
    var title = (doc.title || "").toLowerCase();
    var text = (doc.text || "").toLowerCase();
    if (title === needle) return 100;
    if (title.indexOf(needle) === 0) return 80;
    if (title.indexOf(needle) !== -1) return 60;
    var at = text.indexOf(needle);
    if (at !== -1) return 30 - Math.min(20, Math.floor(at / 200));
    return 0;
  }

  function excerpt(doc, needle) {
    var text = doc.text || "";
    var at = text.toLowerCase().indexOf(needle);
    if (at === -1) return text.slice(0, 140);
    var from = Math.max(0, at - 50);
    return (from > 0 ? "…" : "") + text.slice(from, from + 150);
  }

  function render(results) {
    activeIndex = -1;
    if (!results.length) {
      panel.innerHTML = '<div class="search-results__empty">No matches</div>';
      panel.hidden = false;
      return;
    }
    panel.innerHTML = results
      .map(function (doc) {
        return (
          '<a href="' +
          base +
          doc.location +
          '"><span class="search-results__title"></span>' +
          '<span class="search-results__text"></span></a>'
        );
      })
      .join("");
    // Assign text via textContent so document content can never inject markup.
    Array.prototype.forEach.call(panel.children, function (anchor, i) {
      anchor.children[0].textContent = results[i].title || results[i].location;
      anchor.children[1].textContent = results[i].excerpt;
    });
    panel.hidden = false;
  }

  function search() {
    var needle = input.value.trim().toLowerCase();
    if (needle.length < 2) {
      panel.hidden = true;
      return;
    }
    load().then(function () {
      var results = (docs || [])
        .map(function (doc) {
          return { doc: doc, rank: score(doc, needle) };
        })
        .filter(function (entry) {
          return entry.rank > 0;
        })
        .sort(function (a, b) {
          return b.rank - a.rank;
        })
        .slice(0, 8)
        .map(function (entry) {
          return {
            title: entry.doc.title,
            location: entry.doc.location,
            excerpt: excerpt(entry.doc, needle),
          };
        });
      render(results);
    });
  }

  input.addEventListener("input", search);
  input.addEventListener("focus", load);

  input.addEventListener("keydown", function (event) {
    var items = panel.querySelectorAll("a");
    if (event.key === "Escape") {
      panel.hidden = true;
      input.blur();
    } else if (event.key === "ArrowDown" && items.length) {
      event.preventDefault();
      activeIndex = (activeIndex + 1) % items.length;
    } else if (event.key === "ArrowUp" && items.length) {
      event.preventDefault();
      activeIndex = (activeIndex - 1 + items.length) % items.length;
    } else if (event.key === "Enter" && activeIndex >= 0 && items[activeIndex]) {
      event.preventDefault();
      window.location.href = items[activeIndex].href;
      return;
    } else {
      return;
    }
    Array.prototype.forEach.call(items, function (item, i) {
      item.classList.toggle("is-active", i === activeIndex);
    });
  });

  document.addEventListener("click", function (event) {
    if (!event.target.closest(".header__search")) panel.hidden = true;
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "/" && document.activeElement !== input) {
      var tag = (document.activeElement && document.activeElement.tagName) || "";
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      event.preventDefault();
      input.focus();
    }
  });
})();

/**
 * Repository and branch selectors. The selected value comes from the current URL, not
 * manifest.current (which describes the publisher, not the page a visitor is reading).
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

  // Both controls are functional even if a legacy site has no manifest.
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
