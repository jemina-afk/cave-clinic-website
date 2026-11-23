/* CAVE Clinic — interactions. No libraries. */
(function () {
  "use strict";
  var doc = document.documentElement;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };
  var clamp = function (v, a, b) { return Math.min(b, Math.max(a, v)); };

  /* ---------- Session storage helpers (try/catch for private mode) ---------- */
  function sGet(k) { try { return window.sessionStorage.getItem(k); } catch (e) { return null; } }
  function sSet(k, v) { try { window.sessionStorage.setItem(k, v); } catch (e) { /* ignore */ } }

  /* ---------- White-veil page transitions ---------- */
  var veil = $(".veil");
  function liftVeil() {
    if (!veil) return;
    requestAnimationFrame(function () {
      doc.classList.remove("veil-start");
      veil.classList.remove("is-on");
    });
  }
  window.addEventListener("pageshow", liftVeil);
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[href]");
    if (!a || !veil || e.defaultPrevented) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
    if (a.target === "_blank" || a.hasAttribute("download")) return;
    var url = new URL(a.href, location.href);
    if (url.origin !== location.origin) return;
    if (url.pathname === location.pathname && url.hash) return; // same-page anchor
    if (/^(mailto|tel):/.test(a.getAttribute("href"))) return;
    e.preventDefault();
    veil.classList.add("is-on");
    setTimeout(function () { location.href = a.href; }, reduce ? 300 : 500);
  });

  /* ---------- First-visit intro ---------- */
  var intro = $(".intro");
  var heroSettle = $(".hero-media .settle");
  function startHero() { if (heroSettle) requestAnimationFrame(function () { heroSettle.classList.add("is-in"); }); }
  if (intro) {
    if (reduce || sGet("cave-intro")) {
      intro.remove();
      startHero();
    } else {
      sSet("cave-intro", "1");
      intro.hidden = false;
      document.body.style.overflow = "hidden";
      var letters = $$(".l", intro);
      var done = false;
      var timers = [];
      var finish = function () {
        if (done) return; done = true;
        timers.forEach(clearTimeout);
        letters.forEach(function (l) { l.classList.add("is-in"); });
        intro.classList.add("is-leaving");
        document.body.style.overflow = "";
        startHero();
        setTimeout(function () { intro.remove(); }, 950);
        window.removeEventListener("keydown", finish);
      };
      letters.forEach(function (l, i) { timers.push(setTimeout(function () { l.classList.add("is-in"); }, 200 + i * 80)); });
      timers.push(setTimeout(finish, 200 + letters.length * 80 + 600 + 400));
      intro.addEventListener("click", finish);
      window.addEventListener("keydown", finish);
    }
  } else {
    startHero();
  }

  /* ---------- Header ---------- */
  var header = $(".header");
  var hasHero = !!$(".hero");
  function onScrollHeader() {
    if (!header) return;
    var y = window.scrollY;
    header.classList.toggle("is-scrolled", y > 80);
    header.classList.toggle("is-solid", !hasHero || y > 80);
  }
  onScrollHeader();
  window.addEventListener("scroll", onScrollHeader, { passive: true });

  /* ---------- Mobile menu ---------- */
  var menu = $(".menu");
  var menuBtn = $(".menu-btn");
  if (menu && menuBtn) {
    var closeBtn = $(".menu-close", menu);
    var openMenu = function () {
      menu.hidden = false;
      menu.classList.add("is-open");
      menuBtn.setAttribute("aria-expanded", "true");
      document.body.style.overflow = "hidden";
      $$(".menu-links li", menu).forEach(function (li, i) { li.style.transitionDelay = (reduce ? 0 : 120 + i * 80) + "ms"; });
      closeBtn.focus({ preventScroll: true });
    };
    var closeMenu = function () {
      menu.classList.remove("is-open");
      menuBtn.setAttribute("aria-expanded", "false");
      document.body.style.overflow = "";
      setTimeout(function () { if (!menu.classList.contains("is-open")) menu.hidden = true; }, 500);
      menuBtn.focus();
    };
    menuBtn.addEventListener("click", openMenu);
    closeBtn.addEventListener("click", closeMenu);
    menu.addEventListener("keydown", function (e) { if (e.key === "Escape") closeMenu(); trapFocus(e, menu); });
  }

  function trapFocus(e, root) {
    if (e.key !== "Tab") return;
    var f = $$('a[href], button:not([disabled]), video[controls], [tabindex]:not([tabindex="-1"])', root).filter(function (el) { return el.offsetParent !== null || el === document.activeElement; });
    if (!f.length) return;
    var first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }

  /* ---------- Reveals ---------- */
  $$("[data-stagger]").forEach(function (group) {
    $$(".reveal, .clip", group).forEach(function (el, i) { el.style.setProperty("--d", (i * 100) + "ms"); });
  });
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("is-in"); io.unobserve(en.target); }
      });
    }, { threshold: 0.15 });
    $$(".reveal, .clip").forEach(function (el) { io.observe(el); });
  } else {
    $$(".reveal, .clip").forEach(function (el) { el.classList.add("is-in"); });
  }

  /* ---------- Video helpers: hide placeholder text if a video loads ---------- */
  $$("video[data-autoplay]").forEach(function (v) {
    if (reduce) { v.removeAttribute("autoplay"); v.pause && v.pause(); return; }
    var p = v.play && v.play();
    if (p && p.catch) p.catch(function () { /* autoplay blocked or no source: poster/placeholder stays */ });
  });

  /* ---------- Full-screen video player (dialog) ---------- */
  var dialog = $("#video-dialog");
  var lastFocus = null;
  function openDialog(src, title) {
    if (!dialog) return;
    lastFocus = document.activeElement;
    var v = $("video", dialog);
    var ph = $(".ph", dialog);
    $("#video-dialog-title", dialog).textContent = title || "Clinic film";
    if (src) {
      v.src = src; v.muted = false;
      v.hidden = false;
      var p = v.play(); if (p && p.catch) p.catch(function () {});
      v.onerror = function () { v.hidden = true; ph.hidden = false; };
      ph.hidden = true;
    }
    dialog.hidden = false;
    dialog.classList.add("is-open");
    document.body.style.overflow = "hidden";
    $(".dialog-close", dialog).focus({ preventScroll: true });
  }
  function closeDialog() {
    if (!dialog) return;
    var v = $("video", dialog);
    v.pause();
    dialog.classList.remove("is-open");
    document.body.style.overflow = "";
    setTimeout(function () { dialog.hidden = true; }, 500);
    if (lastFocus) lastFocus.focus();
  }
  if (dialog) {
    $(".dialog-close", dialog).addEventListener("click", closeDialog);
    dialog.addEventListener("click", function (e) { if (e.target === dialog) closeDialog(); });
    dialog.addEventListener("keydown", function (e) { trapFocus(e, dialog); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && dialog.classList.contains("is-open")) closeDialog(); });
    $$("[data-play]").forEach(function (b) {
      b.addEventListener("click", function () { openDialog(b.getAttribute("data-play"), b.getAttribute("data-title")); });
    });
  }

  /* ---------- Step inside walkthrough ---------- */
  var walk = $(".walk");
  if (walk) {
    var track = $(".walk-track", walk);
    var frames = $$(".walk-frame", walk);
    var pin = $(".walk-pin", walk);
    var sticky = $(".walk-sticky", walk);
    var bar = $(".walk-bar i", walk);
    var count = $(".walk-count", walk);
    var dots = $$(".walk-dots button", walk);
    var mode = "";
    var distance = 0;
    var pad = function (n) { return (n < 10 ? "0" : "") + n; };

    var setMode = function () {
      var m = reduce ? "stack" : (window.innerWidth >= 900 ? "pinned" : "swipe");
      if (m !== mode) {
        walk.classList.remove("is-pinned", "is-swipe", "is-stack");
        walk.classList.add("is-" + m);
        mode = m;
        track.style.transform = "";
        pin.style.height = "";
        frames.forEach(function (f) { var s = $(".settle", f); if (s) s.style.transform = ""; });
      }
      if (mode === "pinned") {
        distance = Math.max(0, track.scrollWidth - window.innerWidth);
        pin.style.height = (window.innerHeight + distance) + "px";
        update();
      }
    };
    var current = 0;
    var update = function () {
      if (mode !== "pinned") return;
      var top = pin.getBoundingClientRect().top;
      var prog = distance ? clamp(-top / distance, 0, 1) : 0;
      track.style.transform = "translate3d(" + (-prog * distance) + "px,0,0)";
      bar.style.transform = "scaleX(" + prog + ")";
      var vw = window.innerWidth;
      var best = 0, bestD = Infinity;
      frames.forEach(function (f, i) {
        var r = f.getBoundingClientRect();
        var c = r.left + r.width / 2;
        var d = Math.abs(c - vw / 2);
        if (d < bestD) { bestD = d; best = i; }
        var s = $(".settle", f);
        if (s) s.style.transform = "scale(" + (1 + 0.06 * clamp(d / vw, 0, 1)) + ")";
      });
      current = best;
      count.textContent = pad(best + 1) + " / " + pad(frames.length);
    };
    var goTo = function (i) {
      i = clamp(i, 0, frames.length - 1);
      if (mode === "pinned") {
        var pinTop = pin.getBoundingClientRect().top + window.scrollY;
        var f = frames[i];
        var target = clamp(f.offsetLeft - parseFloat(getComputedStyle(track).paddingLeft), 0, distance);
        window.scrollTo({ top: pinTop + target, behavior: reduce ? "auto" : "smooth" });
      } else if (mode === "swipe") {
        track.scrollTo({ left: frames[i].offsetLeft - track.offsetLeft - parseFloat(getComputedStyle(track).paddingLeft), behavior: "smooth" });
      }
    };
    frames.forEach(function (f, i) {
      f.addEventListener("focus", function () {
        if (sticky) sticky.scrollLeft = 0; // stop the browser scrolling the clipped container
        if (mode === "pinned") { goTo(i); }
      });
      f.addEventListener("keydown", function (e) {
        if (e.target !== f) return;
        if (e.key === "ArrowRight" || e.key === "ArrowDown") { e.preventDefault(); if (frames[i + 1]) { frames[i + 1].focus({ preventScroll: true }); goTo(i + 1); } }
        if (e.key === "ArrowLeft" || e.key === "ArrowUp") { e.preventDefault(); if (frames[i - 1]) { frames[i - 1].focus({ preventScroll: true }); goTo(i - 1); } }
      });
    });
    dots.forEach(function (d, i) { d.addEventListener("click", function () { goTo(i); }); });
    track.addEventListener("scroll", function () {
      if (mode !== "swipe") return;
      var w = frames[0].getBoundingClientRect().width + 16;
      var i = clamp(Math.round(track.scrollLeft / w), 0, frames.length - 1);
      dots.forEach(function (d, j) { d.setAttribute("aria-current", j === i ? "true" : "false"); });
    }, { passive: true });
    setMode();
    window.addEventListener("resize", setMode);
    window.addEventListener("load", setMode);
    window.addEventListener("scroll", function () { requestAnimationFrame(update); }, { passive: true });
  }

  /* ---------- Facial harmony explorer ---------- */
  $$(".explorer").forEach(function (ex) {
    var spots = $$(".hotspot", ex);
    var info = $(".explorer-info", ex);
    var list = $(".areas ul", ex);
    var note = $(".areas .note", ex);
    var chosen = [];
    var show = function (b) {
      spots.forEach(function (s) { s.classList.toggle("is-preview", s === b); });
      info.innerHTML = '<span class="label">Area</span><h3 class="h3">' + b.dataset.name + "</h3><p>" + b.dataset.desc + "</p>";
    };
    var render = function () {
      list.innerHTML = chosen.length ? chosen.map(function (n) { return "<li>" + n + "</li>"; }).join("") : '<li class="empty">Tap an area to add it.</li>';
    };
    spots.forEach(function (b) {
      b.addEventListener("mouseenter", function () { show(b); });
      b.addEventListener("focus", function () { show(b); });
      b.addEventListener("click", function () {
        show(b);
        var n = b.dataset.name;
        var on = b.getAttribute("aria-pressed") === "true";
        if (on) {
          chosen = chosen.filter(function (x) { return x !== n; });
          b.setAttribute("aria-pressed", "false");
          note.textContent = "";
        } else if (chosen.length >= 3) {
          note.textContent = "Up to 3 areas. Remove one to add another.";
        } else {
          chosen.push(n);
          b.setAttribute("aria-pressed", "true");
          note.textContent = "";
        }
        render();
      });
    });
    render();

    // Package scale: radio group with roving tabindex
    var stops = $$(".scale-stop", ex);
    var msg = $(".scale-msg", ex);
    var select = function (i, focus) {
      stops.forEach(function (s, j) {
        s.setAttribute("aria-checked", j === i ? "true" : "false");
        s.tabIndex = j === i ? 0 : -1;
      });
      if (focus) stops[i].focus();
      msg.textContent = stops[i].dataset.name + ": up to 3 areas from lips, nose, cheeks, chin and jaw.";
    };
    stops.forEach(function (s, i) {
      s.addEventListener("click", function () { select(i, false); });
      s.addEventListener("keydown", function (e) {
        var k = e.key, n = stops.length;
        if (k === "ArrowRight" || k === "ArrowDown") { e.preventDefault(); select((i + 1) % n, true); }
        if (k === "ArrowLeft" || k === "ArrowUp") { e.preventDefault(); select((i - 1 + n) % n, true); }
        if (k === " " || k === "Enter") { e.preventDefault(); select(i, false); }
      });
    });
  });

  /* ---------- Before / after sliders ---------- */
  $$(".ba").forEach(function (ba) {
    var handle = $(".ba-handle", ba);
    var pos = 50;
    var set = function (p) {
      pos = clamp(Math.round(p), 0, 100);
      ba.style.setProperty("--pos", pos + "%");
      handle.setAttribute("aria-valuenow", pos);
      handle.setAttribute("aria-valuetext", pos + "% after image shown");
    };
    var fromEvent = function (e) {
      var r = ba.getBoundingClientRect();
      set(((e.clientX - r.left) / r.width) * 100);
    };
    var dragging = false;
    ba.addEventListener("pointerdown", function (e) {
      dragging = true; ba.classList.remove("is-gliding");
      ba.setPointerCapture && ba.setPointerCapture(e.pointerId);
      fromEvent(e);
    });
    ba.addEventListener("pointermove", function (e) { if (dragging) fromEvent(e); });
    ba.addEventListener("pointerup", function () { dragging = false; });
    ba.addEventListener("pointercancel", function () { dragging = false; });
    handle.addEventListener("keydown", function (e) {
      var step = e.shiftKey ? 10 : 2;
      if (e.key === "ArrowLeft" || e.key === "ArrowDown") { e.preventDefault(); set(pos - step); }
      if (e.key === "ArrowRight" || e.key === "ArrowUp") { e.preventDefault(); set(pos + step); }
      if (e.key === "Home") { e.preventDefault(); set(0); }
      if (e.key === "End") { e.preventDefault(); set(100); }
    });
    set(50);
    // One gentle glide 50 → 40 → 50 when it first enters view
    if (!reduce && "IntersectionObserver" in window) {
      var o = new IntersectionObserver(function (en) {
        if (!en[0].isIntersecting) return;
        o.disconnect();
        ba.classList.add("is-gliding");
        setTimeout(function () { if (!dragging) set(40); }, 300);
        setTimeout(function () { if (!dragging) set(50); }, 1300);
        setTimeout(function () { ba.classList.remove("is-gliding"); }, 2300);
      }, { threshold: 0.5 });
      o.observe(ba);
    }
  });

  /* ---------- Cursor image preview (desktop only) ---------- */
  var preview = $(".cursor-preview");
  if (preview && finePointer && !reduce) {
    var inner = $(".inner", preview);
    var tx = 0, ty = 0, x = 0, y = 0, raf = null, active = false;
    var loop = function () {
      x += (tx - x) * 0.15; y += (ty - y) * 0.15;
      preview.style.transform = "translate3d(" + (x + 24) + "px," + (y - 175) + "px,0)";
      raf = (active || Math.abs(tx - x) > 0.5) ? requestAnimationFrame(loop) : null;
    };
    $$("[data-preview]").forEach(function (row) {
      row.addEventListener("mouseenter", function (e) {
        var src = row.getAttribute("data-preview");
        var lbl = row.getAttribute("data-preview-label") || "";
        inner.innerHTML = src
          ? '<img src="' + src + '" alt="" loading="lazy" decoding="async">'
          : '<div class="ph"><span>' + lbl + "</span></div>";
        if (!active) { x = tx = e.clientX; y = ty = e.clientY; }
        active = true; preview.classList.add("is-on");
        if (!raf) raf = requestAnimationFrame(loop);
      });
      row.addEventListener("mousemove", function (e) { tx = e.clientX; ty = e.clientY; });
      row.addEventListener("mouseleave", function () { active = false; preview.classList.remove("is-on"); });
    });
  } else if (preview) {
    preview.remove();
  }

  /* ---------- Testimonials ---------- */
  $$(".quotes").forEach(function (q) {
    var items = $$(".quote", q);
    var dots = $$(".quote-dots button", q);
    var i = 0, timer = null, paused = false;
    var go = function (n) {
      i = (n + items.length) % items.length;
      items.forEach(function (it, j) { it.classList.toggle("is-active", j === i); it.setAttribute("aria-hidden", j === i ? "false" : "true"); });
      dots.forEach(function (d, j) { d.setAttribute("aria-current", j === i ? "true" : "false"); });
    };
    var start = function () { stop(); if (!paused) timer = setInterval(function () { go(i + 1); }, 7000); };
    var stop = function () { if (timer) clearInterval(timer); timer = null; };
    dots.forEach(function (d, j) { d.addEventListener("click", function () { go(j); start(); }); });
    q.addEventListener("mouseenter", function () { paused = true; stop(); });
    q.addEventListener("mouseleave", function () { paused = false; start(); });
    q.addEventListener("focusin", function () { paused = true; stop(); });
    q.addEventListener("focusout", function () { paused = false; start(); });
    go(0); start();
  });

  /* ---------- Today at CAVE ---------- */
  var locs = window.CAVE_LOCATIONS || [];
  $$("[data-today]").forEach(function (el) {
    var d = new Date().getDay(); // 0 = Sunday
    var here = locs.filter(function (l) { return l.days.indexOf(d) > -1; })[0];
    el.textContent = here ? here.today : "Closed today, book online any time";
  });

  /* ---------- Mobile sticky bar ---------- */
  var sbar = $(".sticky-bar");
  var footer = $(".footer");
  if (sbar) {
    var heroEl = $(".hero") || $(".page-hero");
    var tick = function () {
      var afterHero = heroEl ? heroEl.getBoundingClientRect().bottom < 0 : window.scrollY > 400;
      var overFooter = footer ? footer.getBoundingClientRect().top < window.innerHeight : false;
      sbar.classList.toggle("is-on", afterHero && !overFooter);

    };
    tick();
    window.addEventListener("scroll", tick, { passive: true });
  }

  /* ---------- Smooth anchor scroll (respecting reduced motion) ---------- */
  $$('a[href^="#"]').forEach(function (a) {
    a.addEventListener("click", function (e) {
      var id = a.getAttribute("href").slice(1);
      var t = id && document.getElementById(id);
      if (!t) return;
      e.preventDefault();
      var off = parseFloat(getComputedStyle(t).scrollMarginTop) || 80;
      window.scrollTo({ top: t.getBoundingClientRect().top + window.scrollY - off, behavior: reduce ? "auto" : "smooth" });
      history.replaceState(null, "", "#" + id);
    });
  });

  /* ---------- Filters: results gallery and practitioner filter ---------- */
  $$("[data-filter-group]").forEach(function (group) {
    var target = document.getElementById(group.getAttribute("data-filter-group"));
    var attr = group.getAttribute("data-filter-attr") || "data-cat";
    var btns = $$("button", group);
    btns.forEach(function (b) {
      b.addEventListener("click", function () {
        var v = b.getAttribute("data-value");
        btns.forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
        $$("[" + attr + "]", target).forEach(function (it) {
          var vals = it.getAttribute(attr).split(" ");
          it.classList.toggle("is-hidden", v !== "all" && vals.indexOf(v) === -1);
        });
        // hide empty categories (treatments menu)
        $$(".menu-cat", target).forEach(function (cat) {
          var rows = $$("[" + attr + "]", cat);
          if (!rows.length) return;
          cat.classList.toggle("is-hidden", rows.every(function (r) { return r.classList.contains("is-hidden"); }));
        });
        var live = group.parentNode.querySelector("[data-filter-live]") || $("[data-filter-live]");
        if (live) live.textContent = "Showing " + b.textContent.trim().toLowerCase();
      });
    });
    // Pre-select from ?practitioner=paris
    var param = group.getAttribute("data-param");
    if (param) {
      var q = new URLSearchParams(location.search).get(param);
      var pre = q && btns.filter(function (b) { return b.getAttribute("data-value") === q; })[0];
      if (pre) pre.click();
    }
  });

  /* ---------- Sticky category bar: active state ---------- */
  var catbar = $(".catbar");
  if (catbar && "IntersectionObserver" in window) {
    var links = $$(".catbar-cats a", catbar);
    var co = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        links.forEach(function (l) {
          var on = l.getAttribute("href") === "#" + en.target.id;
          l.classList.toggle("is-active", on);
          if (on) l.scrollIntoView({ block: "nearest", inline: "nearest" });
        });
      });
    }, { rootMargin: "-40% 0px -55% 0px" });
    $$(".menu-cat").forEach(function (c) { co.observe(c); });
  }

  /* ---------- Forms (front-end validation; connect to a form service to send) ---------- */
  $$("form[data-form]").forEach(function (f) {
    var msg = $(".form-msg", f);
    f.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!f.checkValidity()) {
        var bad = $(":invalid", f);
        msg.className = "form-msg err";
        msg.textContent = "Please complete the highlighted fields and tick the consent box.";
        if (bad) bad.focus();
        return;
      }
      var action = f.getAttribute("action");
      var ok = function () { msg.className = "form-msg"; msg.textContent = f.getAttribute("data-success"); f.reset(); };
      if (action && action !== "#") {
        fetch(action, { method: "POST", body: new FormData(f), headers: { Accept: "application/json" } })
          .then(function (r) { if (r.ok) ok(); else throw new Error(); })
          .catch(function () { msg.className = "form-msg err"; msg.textContent = "Sorry, that didn't send. Please call 07534 455144."; });
      } else {
        ok();
      }
    });
  });
})();
