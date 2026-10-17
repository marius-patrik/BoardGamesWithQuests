// First-party diagram viewer: rendering, accessible controls and pan/zoom.
const containers = [...document.querySelectorAll("[data-diagram-viewer]")];
// All Mermaid definitions are compiled to verified SVG assets during the
// documentation build. The browser has no dependency on third-party CDNs.

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
  let expanded = null;

  function openModal() {
    if (expanded) { expanded.close(); return; }
    if (!("showModal" in HTMLDialogElement.prototype)) return;

    const marker = document.createComment("image viewer position");
    root.before(marker);
    const dialog = document.createElement("dialog");
    dialog.className = "diagram-modal";
    dialog.setAttribute("aria-label", "Expanded image viewer");
    marker.after(dialog);
    dialog.append(root);
    root.classList.add("diagram-viewer--expanded");
    expanded = dialog;
    const expandButton = toolbar.querySelector('[aria-label="Expand image in modal"]');
    expandButton.textContent = "⤡";
    expandButton.setAttribute("aria-label", "Close expanded image");
    expandButton.title = "Close expanded image";

    dialog.addEventListener("close", () => {
      marker.replaceWith(root);
      root.classList.remove("diagram-viewer--expanded");
      dialog.remove();
      expanded = null;
      expandButton.textContent = "⛶";
      expandButton.setAttribute("aria-label", "Expand image in modal");
      expandButton.title = "Expand image in modal";
      requestAnimationFrame(fit);
      expandButton.focus();
    }, { once: true });
    dialog.addEventListener("click", event => {
      if (event.target !== dialog) return;
      const bounds = dialog.getBoundingClientRect();
      if (event.clientX < bounds.left || event.clientX > bounds.right ||
          event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
    });

    dialog.showModal();
    expandButton.focus();
    requestAnimationFrame(fit);
  }

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
    scale = clamp(Math.min((viewport.clientWidth - 32) / width, 1), .0005, 2);
    offsetX = (viewport.clientWidth - width * scale) / 2;
    // Tall UML diagrams must be legible at opening, not squeezed vertically.
    offsetY = height * scale > viewport.clientHeight ? 16 : (viewport.clientHeight - height * scale) / 2;
    paint();
  }
  function zoom(factor, x = viewport.clientWidth / 2, y = viewport.clientHeight / 2) {
    const next = clamp(scale * factor, .0005, 8);
    const ratio = next / scale;
    offsetX = x - (x - offsetX) * ratio;
    offsetY = y - (y - offsetY) * ratio;
    scale = next;
    paint();
  }
  for (const [text, action, caption] of [
    ["+", () => zoom(1.3), "Zoom in"],
    ["−", () => zoom(1 / 1.3), "Zoom out"],
    ["Fit width", fit, "Fit diagram to width"],
    ["100%", () => { scale = 1; offsetX = 16; offsetY = 16; paint(); }, "Original size"],
    ["⛶", openModal, "Expand image in modal"],
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
