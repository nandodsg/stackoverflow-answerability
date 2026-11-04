/* Page behaviour: chapter stepping, progress rail, and the GSAP motion layer.
   Rules: the page is fully readable without this file (no-JS), without GSAP (CDN blocked) and with reduced motion.
   Stepping is a plain smooth scroll to the next chapter (CSS `scroll-behavior`), never scroll-jacking. */
(function () {
  "use strict";

  var chapters = Array.prototype.slice.call(document.querySelectorAll(".chapter"));
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var current = 0;

  var pad = function (n) { return (n < 10 ? "0" : "") + n; };

  /* ---------- rail + counter ---------- */
  var rail = document.getElementById("rail");
  var counterNow = document.getElementById("counter-now");
  var counterTotal = document.getElementById("counter-total");
  var fill = document.querySelector(".progress-fill");
  counterTotal.textContent = pad(chapters.length);

  chapters.forEach(function (ch, i) {
    var li = document.createElement("li");
    var a = document.createElement("a");
    a.href = "#" + ch.id;
    a.setAttribute("aria-label", pad(i + 1) + " " + ch.dataset.title);
    a.style.setProperty("--sec", getComputedStyle(ch).getPropertyValue("--sec"));
    li.appendChild(a);
    // hover / focus label: the chapter's eyebrow text in the eyebrow's own colour (a sibling of the dot, so the
    // current dot's scale doesn't grow it)
    var eyebrow = ch.querySelector(".eyebrow");
    var tip = document.createElement("span");
    tip.className = "rail-tip";
    tip.setAttribute("aria-hidden", "true");
    tip.textContent = eyebrow ? eyebrow.querySelector(".label").textContent : ch.dataset.title;
    if (eyebrow) tip.style.color = getComputedStyle(eyebrow).color;
    li.appendChild(tip);
    rail.appendChild(li);
  });
  var dots = rail.querySelectorAll("a");

  function setCurrent(i) {
    if (i === current && dots[i].getAttribute("aria-current") === "true") return;
    current = i;
    dots.forEach(function (d, k) { d.setAttribute("aria-current", k === i ? "true" : "false"); });
    counterNow.textContent = pad(i + 1);
    document.documentElement.style.setProperty("--sec-now", getComputedStyle(chapters[i]).getPropertyValue("--sec"));
  }

  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      ticking = false;
      var max = document.documentElement.scrollHeight - window.innerHeight;
      fill.style.transform = "scaleX(" + (max > 0 ? Math.min(1, window.scrollY / max) : 0) + ")";
      // current chapter = the last one whose top has passed 40% of the viewport
      var line = window.innerHeight * 0.4, idx = 0;
      chapters.forEach(function (ch, k) { if (ch.getBoundingClientRect().top <= line) idx = k; });
      setCurrent(idx);
    });
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll);
  onScroll();

  /* ---------- keyboard stepping ---------- */
  // While a smooth scroll is still travelling, `current` (read from the scroll position) lags behind, so quick key
  // presses count from the chapter we are heading to. The memory expires once the scroll has had time to land.
  var heading = null, headingTimer = null;
  // set by the motion layer below: the wipe into a chapter marked data-wipe (slides 2, 6, 10 and 13), stepping forward one
  // chapter; it calls jump() while the page is covered
  var transition = null;
  function go(i) {
    i = Math.max(0, Math.min(chapters.length - 1, i));
    var from = here();
    var special = !!transition && i === from + 1 && chapters[i].hasAttribute("data-wipe");
    var jump = function () {
      chapters[i].scrollIntoView({ block: "start", behavior: special ? "instant" : "auto" });
      history.replaceState(null, "", "#" + chapters[i].id);
    };
    heading = i;
    clearTimeout(headingTimer);
    headingTimer = setTimeout(function () { heading = null; }, special ? 1800 : 1200);
    if (special) transition(i, jump); else jump();
  }
  // links to a chapter ("Start", the rail dots) step through the same transition
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest('a[href^="#"]');
    if (!a || e.ctrlKey || e.metaKey || e.shiftKey) return;
    var target = document.getElementById(a.getAttribute("href").slice(1));
    var idx = chapters.indexOf(target);
    if (idx < 0) return;
    e.preventDefault();
    go(idx);
  });
  function here() { return heading === null ? current : heading; }
  // Keys keep their normal job where they matter: every key while typing SQL, and Space on a button or chip
  // (it presses them). Arrows still step even when a button was just clicked.
  var TYPING = /^(TEXTAREA|INPUT|SELECT)$/;
  var PRESSABLE = /^(BUTTON|SUMMARY)$/;
  document.addEventListener("keydown", function (e) {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (document.querySelector("dialog[open]")) return; // an open EDA dialog keeps the keys (Esc closes it)
    if (TYPING.test(e.target.tagName) || e.target.isContentEditable) return;
    var k = e.key;
    if (k === " " && PRESSABLE.test(e.target.tagName)) return;
    if (k === "ArrowRight" || k === "ArrowDown" || k === "PageDown" || (k === " " && !e.shiftKey)) go(here() + 1);
    else if (k === "ArrowLeft" || k === "ArrowUp" || k === "PageUp" || (k === " " && e.shiftKey)) go(here() - 1);
    else if (k === "Home") go(0);
    else if (k === "End") go(chapters.length - 1);
    else return;
    e.preventDefault();
  });

  /* ---------- count-up (also used by the SQL panel for its bound number) ---------- */
  function countUp(el, to, decimals) {
    decimals = decimals || 0;
    var fmt = function (n) { return n.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals }); };
    if (!window.gsap || reduced || !isFinite(to)) { el.textContent = isFinite(to) ? fmt(to) : String(to); return; }
    var o = { n: 0 };
    gsap.to(o, { n: to, duration: 1.2, ease: "power2.out", onUpdate: function () { el.textContent = fmt(o.n); } });
  }
  window.presentation = { countUp: countUp, reduced: reduced };

  /* ---------- architecture guards: a button highlights where tests, caps or leakage checks attach ---------- */
  // Pressing the active button again clears the highlight. Works without GSAP (it only flips data-show).
  document.querySelectorAll("[data-arch]").forEach(function (arch) {
    var buttons = arch.querySelectorAll("[data-guard]");
    buttons.forEach(function (b) {
      b.addEventListener("click", function () {
        var on = arch.dataset.show !== b.dataset.guard;
        arch.dataset.show = on ? b.dataset.guard : "";
        buttons.forEach(function (x) { x.setAttribute("aria-pressed", on && x === b ? "true" : "false"); });
      });
    });
  });

  /* ---------- slide 9: the view buttons swap tables and pipeline; the key buttons follow one key ---------- */
  // Without JS both views show (the hiding rule needs html.js). Pressing the active key again clears it.
  document.querySelectorAll("[data-views]").forEach(function (box) {
    var buttons = box.querySelectorAll("[data-view-btn]");
    buttons.forEach(function (b) {
      b.addEventListener("click", function () {
        box.dataset.view = b.dataset.viewBtn;
        buttons.forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      });
    });
  });
  document.querySelectorAll("[data-dm]").forEach(function (dm) {
    var buttons = dm.querySelectorAll("[data-key]");
    buttons.forEach(function (b) {
      b.addEventListener("click", function () {
        var on = dm.dataset.show !== b.dataset.key;
        dm.dataset.show = on ? b.dataset.key : "";
        buttons.forEach(function (x) { x.setAttribute("aria-pressed", on && x === b ? "true" : "false"); });
      });
    });
  });

  /* ---------- EDA details: each decision's button opens its modal dialog ---------- */
  // Esc closes a dialog natively; the × button and a click on the dimmed backdrop close it too. A trigger inside an
  // open dialog (P1's "How we know" → D2) opens the new one on top, so closing it goes back to the first; a dialog
  // already open further down is reopened on top. data-row opens the dialog at that row (P1's Method, Evidence,
  // Guard and Cost buttons).
  document.querySelectorAll("[data-dialog]").forEach(function (b) {
    var dialog = document.getElementById(b.dataset.dialog);
    if (!dialog || !dialog.showModal) { b.hidden = true; return; }
    b.addEventListener("click", function () {
      if (dialog.open) dialog.close();
      dialog.showModal();
      var row = b.dataset.row && document.getElementById(b.dataset.row);
      dialog.scrollTop = row ? row.offsetTop - 16 : 0;
    });
  });
  document.querySelectorAll("dialog.eda").forEach(function (dialog) {
    dialog.querySelector(".eda-close").addEventListener("click", function () { dialog.close(); });
    dialog.addEventListener("click", function (e) { if (e.target === dialog) dialog.close(); });
    // A link to another slide (D4 → D5) closes every open dialog first, so the page can scroll there; Ctrl/Cmd or
    // Shift + click opens it in a new tab or window and leaves the dialogs as they are.
    dialog.querySelectorAll('a[href^="#"]').forEach(function (a) {
      a.addEventListener("click", function (e) {
        if (e.ctrlKey || e.metaKey || e.shiftKey) return;
        document.querySelectorAll("dialog[open]").forEach(function (d) { d.close(); });
      });
    });
  });

  /* ---------- motion layer ---------- */
  if (!window.gsap || !window.ScrollTrigger || reduced) return;
  gsap.registerPlugin(ScrollTrigger);

  // Wrap the "{" and "}" of each eyebrow in a span, so they can draw in around the typed label.
  document.querySelectorAll(".chapter .eyebrow").forEach(function (eb) {
    Array.prototype.slice.call(eb.childNodes).forEach(function (node) {
      if (node.nodeType !== 3) return;
      var m = node.textContent.match(/^(\s*)([{}])(\s*)$/);
      if (!m) return;
      var span = document.createElement("span");
      span.className = "br";
      span.textContent = m[2];
      node.replaceWith(m[1], span, m[3]);
    });
  });

  /* The wipe, into each chapter that opens a part (the problem, slide 2; how we solved it, slide 6; the answers,
     slide 10; the final remarks, slide 13): a panel in the part's colour wipes across from the left carrying the part's name, the scroll jumps
     underneath, and the panel leaves to the right. The name is the value of data-wipe when it has one (slide 10,
     whose title stays "P1 · …" for the rail), otherwise the chapter's title. Every other step is the plain smooth
     scroll. A repeated press while it runs is ignored. */
  var wipe = document.createElement("div");
  wipe.className = "wipe";
  wipe.setAttribute("aria-hidden", "true");
  var wipeLabel = document.createElement("span");
  wipeLabel.className = "wipe-label";
  wipe.appendChild(wipeLabel);
  document.body.appendChild(wipe);
  var wiping = false;

  transition = function (i, jump) {
    if (wiping) return;
    wiping = true;
    document.body.classList.add("wiping");
    wipeLabel.textContent = chapters[i].dataset.wipe || chapters[i].dataset.title;
    wipe.style.background = getComputedStyle(chapters[i]).getPropertyValue("--accent");
    gsap.set(wipe, { display: "flex", clipPath: "inset(0% 100% 0% 0%)" });
    gsap.set(wipeLabel, { opacity: 0, x: -60 });
    gsap.timeline({ onComplete: function () { gsap.set(wipe, { display: "none" }); wiping = false; document.body.classList.remove("wiping"); } })
      .to(wipe, { clipPath: "inset(0% 0% 0% 0%)", duration: 0.6, ease: "power4.inOut" })
      .to(wipeLabel, { opacity: 1, x: 0, duration: 0.5, ease: "power3.out" }, "-=0.25")
      .add(jump)
      .to({}, { duration: 0.35 })
      .to(wipe, { clipPath: "inset(0% 0% 0% 100%)", duration: 0.6, ease: "power4.inOut" });
  };

  chapters.forEach(function (ch) {
    var items = Array.prototype.slice.call(ch.querySelectorAll("[data-reveal], [data-stagger] > *"));
    var label = ch.querySelector(".eyebrow .label");
    var labelText = label ? label.textContent : "";
    var marks = ch.querySelectorAll(".mark");
    var counts = ch.querySelectorAll("[data-count]");
    var titleLines = ch.querySelectorAll(".line-in");
    gsap.set(titleLines, { yPercent: 115 });

    var braces = ch.querySelectorAll(".eyebrow .br");
    gsap.set(items, { opacity: 0, y: 24 });
    // the eyebrow itself is one of the reveal items; its braces start further out and close in on the label
    gsap.set(braces, { opacity: 0, x: function (i) { return i === 0 ? -14 : 14; } });
    if (label) label.textContent = "";
    gsap.set(marks, { "--sweep": "0%" });
    counts.forEach(function (c) { c.textContent = "0"; });

    ScrollTrigger.create({
      trigger: ch, start: "top 65%", once: true,
      onEnter: function () {
        gsap.to(items, { opacity: 1, y: 0, duration: 0.7, ease: "power3.out", stagger: 0.08 });
        gsap.to(titleLines, { yPercent: 0, duration: 1.1, ease: "power4.out", stagger: 0.14, delay: 0.1 });
        gsap.to(braces, { opacity: 1, x: 0, duration: 0.6, ease: "power3.out", delay: 0.15 });
        if (label) {
          var t = { n: 0 };
          gsap.to(t, { n: labelText.length, duration: labelText.length * 0.03, ease: "none", delay: 0.2,
            onUpdate: function () { label.textContent = labelText.slice(0, Math.round(t.n)); } });
        }
        gsap.to(marks, { "--sweep": "100%", duration: 0.8, ease: "power2.out", delay: 0.6, stagger: 0.15 });
        counts.forEach(function (c) { countUp(c, parseFloat(c.dataset.count), parseInt(c.dataset.decimals || "0", 10)); });
      }
    });
  });
})();
