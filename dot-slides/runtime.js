/* dot-slides runtime — vanilla JS, classic script, works from file://.
 *
 * Reads slide data from `window.__SLIDES__` (injected by build_presentation.py)
 * and animates the SVG viewBox between the bounding boxes of each slide's
 * target element. Two deck modes share the runtime:
 *
 *   • linear   — flat list, ←/→ step the index by ±1.
 *   • branched — tree with a spine + side-branches; ← / → walk the spine,
 *                ↓ / ↑ walk into & out of branches (DFS order).
 *
 * Mode is determined by `window.__SLIDES__.mode`.
 */
(() => {
  "use strict";

  // ─── Pure helpers ───────────────────────────────────────────────────

  function readViewBox(svg) {
    const raw = (svg.getAttribute("viewBox") || "").trim().split(/\s+/).map(Number);
    if (raw.length !== 4 || raw.some(Number.isNaN)) return null;
    return raw;
  }

  function pad(vb, fx, fy) {
    const px = vb[2] * fx, py = vb[3] * fy;
    return [vb[0] - px, vb[1] - py, vb[2] + 2 * px, vb[3] + 2 * py];
  }

  function easeInOut(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  function lerpVB(from, to, k) {
    return from.map((v, i) => v + (to[i] - v) * k);
  }

  function bboxInUserSpace(svg, el) {
    const ctm = svg.getScreenCTM();
    if (!ctm) return null;
    const inv = ctm.inverse();
    const r = el.getBoundingClientRect();
    const p1 = svg.createSVGPoint(); p1.x = r.left;  p1.y = r.top;
    const p2 = svg.createSVGPoint(); p2.x = r.right; p2.y = r.bottom;
    const a = p1.matrixTransform(inv), b = p2.matrixTransform(inv);
    const x = Math.min(a.x, b.x), y = Math.min(a.y, b.y);
    const w = Math.abs(b.x - a.x), h = Math.abs(b.y - a.y);
    return (w > 0 && h > 0) ? [x, y, w, h] : null;
  }

  function elByTitle(svg, title) {
    if (!title) return null;
    for (const el of svg.querySelectorAll("title")) {
      if (el.textContent.trim() === title) return el.parentNode;
    }
    return null;
  }

  function ownTitle(g) {
    const t = g.querySelector(":scope > title");
    return t ? t.textContent.trim() : null;
  }

  // Edge classes that are part of the narrative (never faded). `seq` is the
  // legacy linear-mode narrative class; `spine` and `branch` are the new
  // branched-deck navigation edges.
  const NARRATIVE_EDGE_CLASSES = ["seq", "spine", "branch"];

  function isNarrativeEdge(g) {
    return NARRATIVE_EDGE_CLASSES.some(c => g.classList.contains(c));
  }

  // For every node element, return the set of slide indices that "own" it:
  // the slide whose <title> matches the node, plus any cluster-slide whose
  // bbox contains the node. (Graphviz emits clusters as siblings of their
  // member nodes, not as parents — so containment is geometric, not DOM.)
  function buildSlideOwnership(svg, resolved) {
    const slideOf = new Map();
    resolved.forEach((r, i) => { if (r.target) slideOf.set(r.target, i); });

    const clusters = [];
    for (const g of svg.querySelectorAll("g.cluster")) {
      const title = ownTitle(g);
      if (title === null) continue;
      const idx = slideOf.get(title);
      if (idx === undefined) continue;
      clusters.push({ idx, box: g.getBBox() });
    }

    const owners = new Map();
    function add(title, idx) {
      let set = owners.get(title);
      if (!set) { set = new Set(); owners.set(title, set); }
      set.add(idx);
    }

    for (const g of svg.querySelectorAll("g.node")) {
      const title = ownTitle(g);
      if (title === null) continue;
      const own = slideOf.get(title);
      if (own !== undefined) add(title, own);
      const b = g.getBBox();
      const cx = b.x + b.width / 2, cy = b.y + b.height / 2;
      for (const c of clusters) {
        if (cx >= c.box.x && cx <= c.box.x + c.box.width &&
            cy >= c.box.y && cy <= c.box.y + c.box.height) {
          add(title, c.idx);
        }
      }
    }
    return owners;
  }

  // Each edge resolved to its endpoint slide-sets and whether it's narrative.
  function classifyEdges(svg, ownership) {
    const out = [];
    for (const g of svg.querySelectorAll("g.edge")) {
      const title = ownTitle(g);
      if (title === null) continue;
      const i = title.indexOf("->");
      if (i < 0) continue;
      const src = title.slice(0, i).trim();
      const tgt = title.slice(i + 2).trim();
      out.push({
        el: g,
        sourceSlides: ownership.get(src) || new Set(),
        targetSlides: ownership.get(tgt) || new Set(),
        isNarrative: isNarrativeEdge(g),
      });
    }
    return out;
  }

  function targetVB(svg, resolved, origVB) {
    if (!resolved.el) return origVB.slice();
    const vb = bboxInUserSpace(svg, resolved.el);
    return vb ? pad(vb, 0.08, 0.10) : origVB.slice();
  }

  // ─── Side-effecting steps ───────────────────────────────────────────

  function prepareSvg(svg) {
    svg.removeAttribute("width");
    svg.removeAttribute("height");
    svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
  }

  function resolveSlides(svg, slides) {
    return slides.map(s => ({ ...s, el: elByTitle(svg, s.target) }));
  }

  function showMissing(missing) {
    if (!missing.length) return;
    const w = document.getElementById("warn");
    w.style.display = "block";
    w.textContent = "Missing slide targets: " + missing.join(", ");
    console.warn("presentation: missing slide targets", missing);
  }

  // Fade narrative edges? No — they always stay full opacity. Fade
  // relational edges that don't touch the current slide. Overview slides
  // (first and last) un-fade everything.
  function updateEdgeVisibility(edges, idx, lastIdx) {
    const isOverview = idx === 0 || idx === lastIdx;
    for (const e of edges) {
      const touches = e.sourceSlides.has(idx) || e.targetSlides.has(idx);
      const fade = !isOverview && !touches && !e.isNarrative;
      e.el.classList.toggle("dot-slide-edge-faded", fade);
    }
  }

  function makeAnimator(svg, getCurrent, setCurrent) {
    let frame = 0;
    return function animate(to, ms) {
      cancelAnimationFrame(frame);
      const from = getCurrent().slice();
      const t0 = performance.now();
      function step(now) {
        const t = Math.min(1, (now - t0) / ms);
        const vb = lerpVB(from, to, easeInOut(t));
        svg.setAttribute("viewBox", vb.join(" "));
        setCurrent(vb);
        if (t < 1) frame = requestAnimationFrame(step);
      }
      frame = requestAnimationFrame(step);
    };
  }

  // ─── Mode-specific navigation ───────────────────────────────────────

  function linearNav(slides) {
    const lastIdx = slides.length - 1;
    const spineIndices = slides
      .map((s, i) => (s.kind === "linear" ? i : -1))
      .filter(i => i >= 0);
    return {
      lastIdx,
      spineIndices,
      handle(key, idx) {
        if (key === "ArrowRight" || key === " " || key === "PageDown" || key === "ArrowDown") {
          return Math.min(lastIdx, idx + 1);
        }
        if (key === "ArrowLeft" || key === "PageUp" || key === "ArrowUp") {
          return Math.max(0, idx - 1);
        }
        if (key === "Home" || key === "0" || key === "Escape") return 0;
        if (key === "End") return lastIdx;
        if (/^[1-9]$/.test(key)) {
          const n = parseInt(key, 10);
          return n < spineIndices.length ? spineIndices[n - 1] : idx;
        }
        return idx;
      },
    };
  }

  function branchedNav(slides) {
    const lastIdx = slides.length - 1;
    const spineIndices = slides
      .map((s, i) => (s.kind === "spine" ? i : -1))
      .filter(i => i >= 0);
    return {
      lastIdx,
      spineIndices,
      handle(key, idx) {
        const s = slides[idx];
        if (key === "ArrowRight" || key === " " || key === "PageDown") {
          return typeof s.spineNext === "number" ? s.spineNext : idx;
        }
        if (key === "ArrowLeft" || key === "PageUp") {
          return typeof s.spinePrev === "number" ? s.spinePrev : idx;
        }
        if (key === "ArrowDown") {
          return typeof s.branchNext === "number" ? s.branchNext : idx;
        }
        if (key === "ArrowUp") {
          return typeof s.branchPrev === "number" ? s.branchPrev : idx;
        }
        if (key === "Home" || key === "0" || key === "Escape") return 0;
        if (key === "End") return lastIdx;
        if (/^[1-9]$/.test(key)) {
          const n = parseInt(key, 10);
          return n <= spineIndices.length ? spineIndices[n - 1] : idx;
        }
        return idx;
      },
    };
  }

  function updateHintForMode(mode) {
    const hint = document.getElementById("hint");
    if (!hint) return;
    if (mode === "branched") {
      hint.innerHTML =
        '<kbd>→</kbd> spine next · <kbd>←</kbd> spine prev · ' +
        '<kbd>↓</kbd> branch in/forward · <kbd>↑</kbd> branch back · ' +
        '<kbd>Home</kbd> overview · <kbd>End</kbd> last · ' +
        '<kbd>1</kbd>–<kbd>9</kbd> spine jump · ' +
        '<kbd>H</kbd> hide chrome · <kbd>F</kbd> fullscreen';
    }
    // Linear mode keeps the markup from the template untouched.
  }

  function bindNavigation(show) {
    document.addEventListener("keydown", e => {
      const k = e.key;
      if (k === "h" || k === "H") {
        document.body.classList.toggle("hide-chrome");
        return;
      }
      if (k === "f" || k === "F") {
        if (!document.fullscreenElement) document.documentElement.requestFullscreen();
        else document.exitFullscreen();
        return;
      }
      // All navigation keys go through show(); preventDefault for
      // arrows / space / paging so the browser doesn't scroll instead.
      const navKeys = new Set([
        "ArrowRight", "ArrowLeft", "ArrowUp", "ArrowDown",
        " ", "PageDown", "PageUp",
        "Home", "End", "Escape", "0",
      ]);
      if (navKeys.has(k) || /^[1-9]$/.test(k)) {
        e.preventDefault();
        show(k);
      }
    });

    document.addEventListener("click", e => {
      if (e.target.closest("#overlay, #hint, #warn")) return;
      show(e.clientX > window.innerWidth / 2 ? "ArrowRight" : "ArrowLeft");
    });
  }

  // ─── Wire-up ────────────────────────────────────────────────────────

  const svg = document.querySelector("#svg-host svg");
  if (!svg) return;

  const data = window.__SLIDES__ || { mode: "linear", slides: [] };
  const mode = data.mode || "linear";
  const slides = data.slides || [];

  document.getElementById("title").textContent = window.__TITLE__ || "Overview";

  const origVB = readViewBox(svg);
  if (!origVB) { console.error("presentation: SVG has no usable viewBox"); return; }
  prepareSvg(svg);

  const resolved = resolveSlides(svg, slides);
  const missing = slides
    .map((s, i) => (s.target && !resolved[i].el) ? s.target : null)
    .filter(Boolean);
  showMissing(missing);

  let current = origVB.slice();
  const animate = makeAnimator(svg, () => current, vb => { current = vb; });

  const titleEl = document.getElementById("title");
  const counterEl = document.getElementById("counter");
  const nav = mode === "branched" ? branchedNav(slides) : linearNav(slides);
  updateHintForMode(mode);

  let idx = 0;
  let edges = [];

  function counterFor(i) {
    const s = slides[i];
    if (!s) return "";
    if (s.kind === "overview") {
      return i === 0 ? `0 / ${nav.spineIndices.length}`
                     : `${nav.spineIndices.length} / ${nav.spineIndices.length}`;
    }
    if (s.kind === "linear") {
      const pos = nav.spineIndices.indexOf(i);
      return `${pos + 1} / ${nav.spineIndices.length}`;
    }
    if (s.kind === "spine") {
      return `${parseInt(s.number, 10)} / ${nav.spineIndices.length}`;
    }
    if (s.kind === "branch") {
      return s.number;
    }
    return "";
  }

  function show(key) {
    if (typeof key === "number") {
      idx = Math.max(0, Math.min(nav.lastIdx, key));
    } else {
      idx = nav.handle(key, idx);
      idx = Math.max(0, Math.min(nav.lastIdx, idx));
    }
    const s = slides[idx];
    titleEl.textContent = s.label || "Overview";
    counterEl.textContent = counterFor(idx);
    animate(targetVB(svg, resolved[idx], origVB), 650);
    updateEdgeVisibility(edges, idx, nav.lastIdx);
  }

  console.log(
    "presentation: mode=%s, %d slides, %d resolved, %d missing",
    mode,
    slides.length,
    resolved.filter(s => !s.target || s.el).length,
    missing.length,
  );

  requestAnimationFrame(() => {
    // bbox math needs the SVG laid out — defer to the first frame.
    edges = classifyEdges(svg, buildSlideOwnership(svg, resolved));
    show(0);
  });
  bindNavigation(show);
})();
