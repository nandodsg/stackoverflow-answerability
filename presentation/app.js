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
    a.title = ch.dataset.title;
    li.appendChild(a);
    rail.appendChild(li);
  });
  var dots = rail.querySelectorAll("a");

  function setCurrent(i) {
    if (i === current && dots[i].getAttribute("aria-current") === "true") return;
    current = i;
    dots.forEach(function (d, k) { d.setAttribute("aria-current", k === i ? "true" : "false"); });
    counterNow.textContent = pad(i + 1);
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
  function go(i) {
    i = Math.max(0, Math.min(chapters.length - 1, i));
    chapters[i].scrollIntoView({ block: "start" });
    history.replaceState(null, "", "#" + chapters[i].id);
    heading = i;
    clearTimeout(headingTimer);
    headingTimer = setTimeout(function () { heading = null; }, 1200);
  }
  function here() { return heading === null ? current : heading; }
  // Keys keep their normal job where they matter: every key while typing SQL, and Space on a button or chip
  // (it presses them). Arrows still step even when a button was just clicked.
  var TYPING = /^(TEXTAREA|INPUT|SELECT)$/;
  var PRESSABLE = /^(BUTTON|SUMMARY)$/;
  document.addEventListener("keydown", function (e) {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
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

  chapters.forEach(function (ch) {
    var items = Array.prototype.slice.call(ch.querySelectorAll("[data-reveal], [data-stagger] > *"));
    var label = ch.querySelector(".eyebrow .label");
    var labelText = label ? label.textContent : "";
    var marks = ch.querySelectorAll(".mark");
    var counts = ch.querySelectorAll("[data-count]");

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
