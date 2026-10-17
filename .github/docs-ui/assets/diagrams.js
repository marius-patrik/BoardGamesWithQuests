// First-party diagram viewer: rendering, accessible controls and pan/zoom.
const containers = [...document.querySelectorAll("[data-diagram-viewer]")];
const mermaids = [...document.querySelectorAll("[data-diagram-viewer] .mermaid")];

if (mermaids.length) {
  try {
    const { default: mermaid } = await import("https://cdn.jsdelivr.net/npm/mermaid@11.12.2/dist/mermaid.esm.min.mjs");
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: "strict",
      theme: document.documentElement.dataset.theme === "light" ? "default" : "dark",
      flowchart: { useMaxWidth: false, htmlLabels: false },
    });
    await mermaid.run({ nodes: mermaids });
    for (const svg of document.querySelectorAll("[data-diagram-viewer] .mermaid svg")) {
      const width = svg.viewBox?.baseVal?.width;
      const height = svg.viewBox?.baseVal?.height;
      if (width > 0 && height > 0) {
        svg.style.width = Math.ceil(width) + "px";
        svg.style.height = Math.ceil(height) + "px";
      }
      svg.setAttribute("role", "img");
      svg.setAttribute("aria-label", "Rendered architecture diagram");
    }
  } catch (error) {
    console.error("Unable to render architecture diagram", error);
    for (const source of mermaids) {
      const message = document.createElement("p");
      message.className = "diagram-viewer__error";
      message.setAttribute("role", "alert");
      message.textContent = "The diagram could not be rendered. Open the Mermaid source using the repository link.";
      source.replaceWith(message);
    }
  }
}

function attachViewer(root) {
  const viewport = root.querySelector(".diagram-viewer__viewport");
  const canvas = root.querySelector(".diagram-viewer__canvas");
  const graphic = canvas.querySelector("svg, img");
  if (!graphic) return;
  const toolbar = document.createElement("div");
  toolbar.className = "diagram-viewer__toolbar";
  const label = document.createElement("span");
  label.className = "diagram-viewer__zoom-label";
  let scale = 1, offsetX = 0, offsetY = 0;
  const clamp = (value, lower, upper) => Math.min(upper, Math.max(lower, value));
  const paint = () => {
    canvas.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scale})`;
    label.textContent = Math.round(scale * 100) + "%";
  };
  const dimensions = () => {
    if (graphic instanceof SVGElement) {
      const box = graphic.viewBox?.baseVal;
      return [box?.width || graphic.getBoundingClientRect().width, box?.height || graphic.getBoundingClientRect().height];
    }
    return [graphic.naturalWidth || graphic.width, graphic.naturalHeight || graphic.height];
  };
  function fit() {
    const [width, height] = dimensions();
    if (!width || !height || !viewport.clientWidth) return;
    scale = clamp(Math.min((viewport.clientWidth - 32) / width, (viewport.clientHeight - 32) / height, 1), .01, 1);
    offsetX = (viewport.clientWidth - width * scale) / 2;
    offsetY = (viewport.clientHeight - height * scale) / 2;
    paint();
  }
  function zoom(factor, x = viewport.clientWidth / 2, y = viewport.clientHeight / 2) {
    const next = clamp(scale * factor, .01, 8);
    const ratio = next / scale;
    offsetX = x - (x - offsetX) * ratio;
    offsetY = y - (y - offsetY) * ratio;
    scale = next;
    paint();
  }
  for (const [text, action, caption] of [
    ["+", () => zoom(1.3), "Zoom in"],
    ["−", () => zoom(1 / 1.3), "Zoom out"],
    ["Fit", fit, "Fit diagram to viewport"],
    ["100%", () => { scale = 1; offsetX = 16; offsetY = 16; paint(); }, "Original size"],
  ]) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = text;
    button.setAttribute("aria-label", caption);
    button.addEventListener("click", action);
    toolbar.append(button);
  }
  toolbar.append(label);
  root.prepend(toolbar);
  viewport.addEventListener("wheel", (event) => {
    event.preventDefault();
    const box = viewport.getBoundingClientRect();
    zoom(event.deltaY < 0 ? 1.15 : 1 / 1.15, event.clientX - box.left, event.clientY - box.top);
  }, { passive: false });
  let dragged = null;
  viewport.addEventListener("pointerdown", event => {
    if (event.button !== 0) return;
    dragged = { id: event.pointerId, x: event.clientX, y: event.clientY };
    viewport.setPointerCapture(event.pointerId);
    viewport.classList.add("is-dragging");
  });
  viewport.addEventListener("pointermove", event => {
    if (!dragged || event.pointerId !== dragged.id) return;
    offsetX += event.clientX - dragged.x;
    offsetY += event.clientY - dragged.y;
    dragged.x = event.clientX;
    dragged.y = event.clientY;
    paint();
  });
  const stopDrag = () => { dragged = null; viewport.classList.remove("is-dragging"); };
  viewport.addEventListener("pointerup", stopDrag);
  viewport.addEventListener("pointercancel", stopDrag);
  viewport.addEventListener("keydown", event => {
    if (event.key === "+" || event.key === "=") { event.preventDefault(); zoom(1.3); }
    else if (event.key === "-") { event.preventDefault(); zoom(1 / 1.3); }
    else if (event.key === "Home") { event.preventDefault(); fit(); }
    else if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(event.key)) {
      event.preventDefault();
      if (event.key === "ArrowUp") offsetY += 50;
      if (event.key === "ArrowDown") offsetY -= 50;
      if (event.key === "ArrowLeft") offsetX += 50;
      if (event.key === "ArrowRight") offsetX -= 50;
      paint();
    }
  });
  if (graphic instanceof HTMLImageElement && !graphic.complete) {
    graphic.addEventListener("load", fit, { once: true });
  } else fit();
  if (graphic instanceof HTMLImageElement) {
    graphic.addEventListener("error", () => {
      const msg = document.createElement("p");
      msg.className = "diagram-viewer__error";
      msg.setAttribute("role", "alert");
      msg.textContent = "SVG could not be loaded from the published documentation assets.";
      viewport.replaceChildren(msg);
    }, { once: true });
  }
  new ResizeObserver(fit).observe(viewport);
}

for (const container of containers) attachViewer(container);
