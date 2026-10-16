// Network scene for the Even and Hub-heavy network pages, drawn with Cytoscape.js.
//
// The network and every outbreak come from the Python app (fmd_sim/webapp.py),
// which runs the same model as the experiment. This file only draws them.
//
// Timing rule (same as the model): a farm infected on day d spreads the disease
// on days d+1 ... d+D and is removed on day d+D.

(function () {
  "use strict";

  var root = document.querySelector(".graph-page");
  var NAME = root.dataset.network;
  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var tip = document.getElementById("tip");
  var hint = document.getElementById("hint");
  var container = document.getElementById("cy");

  if (window.cytoscapeFcose) cytoscape.use(window.cytoscapeFcose);

  var cy = null, net = null;
  var outbreak = null;                 // current outbreak from the server
  var pathKey = {};                    // link id -> direction, for links the disease travelled along
  var curve = [];                      // infected farms on each whole day
  var t = 0, playing = false, speed = 10, shownDay = -1;
  var linkMode = "infected", showPath = true, hover = -1;
  var colours = {};

  // ------------------------------------------------------------------ helpers
  function D() { return net ? net.days_infectious : 14; }
  function fmt(x, n) { return Number(x).toFixed(n); }
  function edgeId(a, b) { return a < b ? "e" + a + "_" + b : "e" + b + "_" + a; }

  // 0 = healthy, 1 = infected, 2 = removed
  function stateAt(i, day) {
    if (!outbreak) return 0;
    var d = outbreak.infection_day[i];
    if (d < 0 || day < d) return 0;
    return day < d + D() ? 1 : 2;
  }

  function readColours() {
    var cs = getComputedStyle(document.documentElement);
    ["--s", "--i", "--r", "--edge", "--edge-hot", "--path", "--ink", "--muted", "--line"].forEach(function (n) {
      colours[n] = cs.getPropertyValue(n).trim();
    });
  }

  // ------------------------------------------------------------------ style
  function buildStyle() {
    var c = colours;
    return [
      { selector: "node", style: {
          "background-color": c["--s"],
          "width": "data(size)", "height": "data(size)",
          "border-width": 0,
          "transition-property": "background-color, opacity",
          "transition-duration": reduceMotion ? "0s" : "0.25s" } },
      { selector: "node.i", style: {
          "background-color": c["--i"],
          "underlay-color": c["--i"], "underlay-padding": 7, "underlay-opacity": 0.28, "underlay-shape": "ellipse" } },
      { selector: "node.r", style: { "background-color": c["--r"] } },
      { selector: "node.new", style: { "border-width": 6, "border-color": c["--i"], "border-opacity": 0.45 } },
      { selector: "node.seed", style: { "border-width": 4, "border-color": c["--ink"], "border-opacity": 1 } },
      { selector: "node.hovered", style: { "border-width": 3, "border-color": c["--ink"], "border-opacity": 1 } },
      { selector: "node.faded", style: { "opacity": 0.15 } },

      { selector: "edge", style: {
          "display": "none", "width": 1, "line-color": c["--edge"], "opacity": 0.35,
          "curve-style": "haystack", "haystack-radius": 0 } },
      { selector: "edge.shown", style: { "display": "element" } },
      { selector: "edge.hot", style: { "line-color": c["--edge-hot"], "opacity": 0.45, "width": 1.1 } },
      { selector: "edge.path", style: {
          "display": "element", "line-color": c["--path"], "opacity": 0.95, "width": 2.6,
          "curve-style": "straight", "arrow-scale": 0.9 } },
      { selector: "edge.path.fwd", style: { "target-arrow-shape": "triangle", "target-arrow-color": c["--path"] } },
      { selector: "edge.path.rev", style: { "source-arrow-shape": "triangle", "source-arrow-color": c["--path"] } },
      { selector: "edge.focus", style: { "display": "element", "line-color": c["--ink"], "opacity": 0.85, "width": 1.8 } },
      { selector: "edge.faded", style: { "opacity": 0.06 } },
    ];
  }

  // ------------------------------------------------------------------ states
  // Recompute every farm's and link's look for the current day, link mode and hover.
  function render() {
    if (!cy) return;
    var day = Math.floor(t);
    var st = new Array(net.n);
    for (var i = 0; i < net.n; i++) st[i] = stateAt(i, day);
    var nbr = null;
    if (hover >= 0) { nbr = {}; nbr[hover] = true; cy.getElementById(String(hover)).neighborhood("node").forEach(function (n) { nbr[+n.id()] = true; }); }

    cy.batch(function () {
      cy.nodes().forEach(function (n) {
        var i = +n.id(), cls = [["s", "i", "r"][st[i]]];
        if (outbreak) {
          if (i === outbreak.seed) cls.push("seed");
          if (outbreak.infection_day[i] === day && day > 0) cls.push("new");
        }
        if (i === hover) cls.push("hovered");
        if (nbr && !nbr[i]) cls.push("faded");
        n.classes(cls);
      });
      cy.edges().forEach(function (e) {
        var a = +e.data("source"), b = +e.data("target"), cls = [];
        var hot = st[a] === 1 || st[b] === 1;
        if (linkMode === "all" || (linkMode === "infected" && hot)) cls.push("shown");
        if (hot && linkMode !== "off") cls.push("hot");
        var p = pathKey[e.id()];
        if (showPath && p && p.day <= day) cls.push("path", p.dir);
        if (hover >= 0) {
          if (a === hover || b === hover) cls.push("focus");
          else cls.push("faded");
        }
        e.classes(cls);
      });
    });
    shownDay = day;
    updatePanel(st);
  }

  // ------------------------------------------------------------------ panel
  var Tslider = document.getElementById("T"), Tout = document.getElementById("T-out");
  var readout = document.getElementById("readout"), verdict = document.getElementById("verdict");
  var startBtn = document.getElementById("start"), playBtn = document.getElementById("play");
  var restartBtn = document.getElementById("restart"), daySlider = document.getElementById("day");
  var dayOut = document.getElementById("day-out"), counts = document.getElementById("counts");
  var curveCanvas = document.getElementById("curve"), outcome = document.getElementById("outcome");
  var Tchip = document.getElementById("T-chip");

  // ------------------------------------------------------------------ details menu
  var drawer = document.getElementById("drawer"), menuBtn = document.getElementById("menu-btn");
  function setDrawer(open, focusTarget) {
    drawer.classList.toggle("open", open);
    drawer.setAttribute("aria-hidden", open ? "false" : "true");
    menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
    Tchip.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) {
      drawCurve();
      (focusTarget || document.getElementById("drawer-close")).focus();
    } else {
      menuBtn.focus();
    }
  }
  menuBtn.addEventListener("click", function () { setDrawer(!drawer.classList.contains("open")); });
  Tchip.addEventListener("click", function () { setDrawer(true, Tslider); });
  document.getElementById("drawer-close").addEventListener("click", function () { setDrawer(false); });
  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape" && drawer.classList.contains("open")) setDrawer(false);
  });

  function showStats() {
    var rows = [
      ["Farms", net.n],
      ["Average links per farm ⟨k⟩", fmt(net.mean_k, 2)],
      ["Fewest links", net.min_k],
      ["Busiest farm", net.max_k + " links"],
      ["Average of squared links ⟨k²⟩", fmt(net.mean_k2, 1)],
      ["Further farms reached", fmt(net.excess_degree, 2)],
      ["Threshold from theory, T<sub>c</sub>", fmt(net.threshold_T, 3)],
    ];
    document.getElementById("stats").innerHTML = rows.map(function (r) {
      return "<dt>" + r[0] + "</dt><dd>" + r[1] + "</dd>";
    }).join("");
  }

  function showContagion() {
    var T = parseFloat(Tslider.value), Dd = D();
    var p = 1 - Math.pow(1 - T, 1 / Dd);
    var R0 = T * net.excess_degree;
    Tout.textContent = fmt(T, 3);
    Tchip.textContent = "T = " + fmt(T, 3) + ", R₀ = " + fmt(R0, 2);
    readout.innerHTML = "Daily chance of passing it on along one link: <b>" + fmt(100 * p, 2) + "%</b> for " + Dd + " days.<br>" +
      "R₀ = T × further farms reached = " + fmt(T, 3) + " × " + fmt(net.excess_degree, 2) + " = <b>" + fmt(R0, 2) + "</b>";
    verdict.textContent = R0 < 1
      ? "R₀ is below 1, so outbreaks on this network usually fizzle out."
      : "R₀ is above 1, so a big outbreak is possible. It can still die out early by chance.";
  }

  function drawCurve() {
    var r = curveCanvas.getBoundingClientRect(), d = window.devicePixelRatio || 1;
    curveCanvas.width = Math.round(r.width * d); curveCanvas.height = Math.round(r.height * d);
    var c = curveCanvas.getContext("2d");
    c.setTransform(d, 0, 0, d, 0, 0);
    c.clearRect(0, 0, r.width, r.height);
    var bottom = r.height - 16, top = 4, w = r.width - 4;
    c.strokeStyle = colours["--line"]; c.lineWidth = 1;
    c.beginPath(); c.moveTo(2, bottom + 0.5); c.lineTo(w + 2, bottom + 0.5); c.stroke();
    c.fillStyle = colours["--muted"]; c.font = "11px Atkinson Hyperlegible, Arial, sans-serif";
    c.fillText("Infected farms over time", 4, r.height - 3);
    if (!outbreak || !curve.length) return;
    var maxI = Math.max(1, Math.max.apply(null, curve)), n = Math.max(1, curve.length - 1);
    c.beginPath(); c.moveTo(2, bottom);
    curve.forEach(function (v, day) { c.lineTo(2 + (day / n) * w, bottom - (v / maxI) * (bottom - top)); });
    c.lineTo(2 + w, bottom); c.closePath();
    c.globalAlpha = 0.4; c.fillStyle = colours["--i"]; c.fill(); c.globalAlpha = 1;
    var x = 2 + (t / n) * w;
    c.strokeStyle = colours["--ink"]; c.lineWidth = 1.5;
    c.beginPath(); c.moveTo(x, top); c.lineTo(x, bottom); c.stroke();
  }

  function updatePanel(st) {
    var c = [0, 0, 0];
    st.forEach(function (s) { c[s]++; });
    counts.innerHTML =
      "<span><span class='dot s'></span>Healthy<b>" + c[0] + "</b></span>" +
      "<span><span class='dot i'></span>Infected<b>" + c[1] + "</b></span>" +
      "<span><span class='dot r'></span>Removed<b>" + c[2] + "</b></span>";
    dayOut.textContent = Math.floor(t) + (outbreak ? " of " + outbreak.duration : "");
    daySlider.value = Math.floor(t);
    playBtn.textContent = playing ? "Pause" : "Play";
    if (outbreak) {
      var o = outbreak, s = "Started at farm " + o.seed + " (" + net.degree[o.seed] + " links) with T = " + fmt(o.T, 3) + ".";
      if (t >= o.duration) {
        s += " In the end " + Math.round(o.final_size * 100) + "% of farms were infected, over " + o.duration + " days.";
        if (o.final_size * net.n <= 3) s += " It fizzled out almost straight away.";
      }
      outcome.textContent = s;
    }
    drawCurve();
  }

  // ------------------------------------------------------------------ outbreak
  function startOutbreak(seed) {
    var T = parseFloat(Tslider.value);
    startBtn.disabled = true;
    fetch("/api/outbreak", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ network: NAME, T: T, seed: seed === undefined ? null : seed }),
    }).then(function (r) { return r.json().then(function (j) { return { ok: r.ok, body: j }; }); })
      .then(function (res) {
        startBtn.disabled = false;
        if (!res.ok) { outcome.textContent = res.body.error || "Could not start the outbreak."; return; }
        outbreak = res.body;
        pathKey = {};
        outbreak.infected_by.forEach(function (src, farm) {
          if (src < 0) return;
          pathKey[edgeId(src, farm)] = { day: outbreak.infection_day[farm], dir: src < farm ? "fwd" : "rev" };
        });
        curve = [];
        for (var day = 0; day <= outbreak.duration; day++) {
          var c = 0;
          for (var i = 0; i < net.n; i++) if (stateAt(i, day) === 1) c++;
          curve.push(c);
        }
        t = 0; playing = true;
        hint.hidden = true;
        [playBtn, restartBtn, daySlider].forEach(function (el) { el.disabled = false; });
        daySlider.max = outbreak.duration;
        render();
      })
      .catch(function () {
        startBtn.disabled = false;
        outcome.textContent = "Could not reach the app. Check that python app.py is still running.";
      });
  }

  var last = null;
  function frame(now) {
    if (last === null) last = now;
    var dt = Math.min(0.25, (now - last) / 1000);   // keeps playback speed right even if the computer draws slowly
    last = now;
    if (playing && outbreak) {
      t += dt * speed;
      if (t >= outbreak.duration) { t = outbreak.duration; playing = false; render(); }
      else if (Math.floor(t) !== shownDay) render();
      else drawCurve();
    }
    requestAnimationFrame(frame);
  }

  // ------------------------------------------------------------------ layout
  function runLayout(randomize) {
    var layout = cy.layout({
      name: window.cytoscapeFcose ? "fcose" : "cose",
      quality: "proof",
      randomize: randomize,
      animate: !reduceMotion,
      animationDuration: 700,
      fit: true, padding: 40,
      nodeRepulsion: function (n) { return 6000 + n.data("degree") * 700; },
      idealEdgeLength: function () { return 85; },
      edgeElasticity: function () { return 0.25; },
      nodeSeparation: 80,
      gravity: 0.12, gravityRange: 4.0,
      numIter: 3000,
      packComponents: true, tile: true,
    });
    layout.run();
  }

  // ------------------------------------------------------------------ controls
  Tslider.addEventListener("input", showContagion);
  startBtn.addEventListener("click", function () { startOutbreak(); });
  playBtn.addEventListener("click", function () {
    if (!outbreak) return;
    if (!playing && t >= outbreak.duration) t = 0;
    playing = !playing; render();
  });
  restartBtn.addEventListener("click", function () { t = 0; playing = true; render(); });
  daySlider.addEventListener("input", function () { t = parseFloat(daySlider.value); playing = false; render(); });
  document.querySelectorAll("#speed button").forEach(function (b) {
    b.addEventListener("click", function () {
      speed = parseFloat(b.dataset.speed);
      document.querySelectorAll("#speed button").forEach(function (o) { o.setAttribute("aria-pressed", o === b ? "true" : "false"); });
    });
  });
  document.querySelectorAll("#links button").forEach(function (b) {
    b.addEventListener("click", function () {
      linkMode = b.dataset.links;
      document.querySelectorAll("#links button").forEach(function (o) { o.setAttribute("aria-pressed", o === b ? "true" : "false"); });
      render();
    });
  });
  document.getElementById("show-path").addEventListener("change", function (ev) { showPath = ev.target.checked; render(); });
  document.getElementById("relayout").addEventListener("click", function () { if (cy) runLayout(true); });
  document.getElementById("zoom-in").addEventListener("click", function () { zoomBy(1.3); });
  document.getElementById("zoom-out").addEventListener("click", function () { zoomBy(1 / 1.3); });
  document.getElementById("zoom-fit").addEventListener("click", function () { if (cy) cy.animate({ fit: { padding: 40 } }, { duration: reduceMotion ? 0 : 300 }); });
  function zoomBy(f) {
    if (!cy) return;
    cy.zoom({ level: cy.zoom() * f, renderedPosition: { x: container.clientWidth / 2, y: container.clientHeight / 2 } });
  }
  document.addEventListener("keydown", function (ev) {
    if (ev.code !== "Space" || !outbreak) return;
    var tag = (document.activeElement && document.activeElement.tagName) || "";
    if (tag === "INPUT" || tag === "BUTTON" || tag === "SELECT") return;
    ev.preventDefault(); playBtn.click();
  });

  // ------------------------------------------------------------------ hover details
  function showTip(i, pos) {
    var text = "Farm " + i + ": " + net.degree[i] + " links (highlighted).";
    if (outbreak) {
      var day = Math.floor(t), s = stateAt(i, day), d = outbreak.infection_day[i], src = outbreak.infected_by[i];
      if (i === outbreak.seed) text += " The outbreak started here.";
      else if (d >= 0 && d <= day) text += " Infected on day " + d + (src >= 0 ? ", caught it from farm " + src + "." : ".");
      text += s === 0 ? " Healthy." : s === 1 ? " Infected now." : " Removed.";
    } else {
      text += " Click to start an outbreak here.";
    }
    tip.textContent = text;
    tip.style.display = "block";
    var W = root.clientWidth, H = root.clientHeight;
    var x = Math.min(pos.x + 14, W - tip.offsetWidth - 6), y = pos.y + 16;
    if (y + tip.offsetHeight > H - 6) y = pos.y - tip.offsetHeight - 10;
    tip.style.left = Math.max(6, x) + "px"; tip.style.top = Math.max(6, y) + "px";
  }

  // ------------------------------------------------------------------ keep the network clear of the controls
  // The drawing area sits between the top controls and the bottom bar, so no farm
  // is ever hidden behind a button. It adjusts when the window or bar changes size.
  var topBox = document.querySelector(".top-left"), bottomBox = document.querySelector(".bottom");
  function placeGraph() {
    var top = topBox.offsetTop + topBox.offsetHeight + 8;
    var bottom = root.clientHeight - bottomBox.offsetTop + 8;
    container.style.top = top + "px";
    container.style.bottom = bottom + "px";
    if (cy) cy.resize();
  }
  new ResizeObserver(placeGraph).observe(root);
  new ResizeObserver(placeGraph).observe(bottomBox);
  new ResizeObserver(placeGraph).observe(topBox);
  placeGraph();

  // ------------------------------------------------------------------ start
  readColours();
  fetch("/api/network/" + NAME).then(function (r) { return r.json(); }).then(function (data) {
    net = data;
    var W = container.clientWidth, H = container.clientHeight;
    var elements = [];
    data.x.forEach(function (x, i) {
      // The same size rule on both pages, so a farm with 10 links looks the same size on each.
      elements.push({ group: "nodes", data: { id: String(i), degree: data.degree[i], size: 9 + 1.05 * data.degree[i] },
                      position: { x: x * W, y: data.y[i] * H } });
    });
    data.edges.forEach(function (e) {
      elements.push({ group: "edges", data: { id: edgeId(e[0], e[1]), source: String(e[0]), target: String(e[1]) } });
    });

    cy = cytoscape({
      container: container,
      elements: elements,
      style: buildStyle(),
      layout: { name: "preset", fit: true, padding: 40 },
      minZoom: 0.1, maxZoom: 8,
      boxSelectionEnabled: false,
      autounselectify: true,
    });

    cy.on("tap", "node", function (ev) { startOutbreak(+ev.target.id()); });
    cy.on("mouseover", "node", function (ev) {
      hover = +ev.target.id(); render(); showTip(hover, ev.renderedPosition);
      container.style.cursor = "pointer";
    });
    cy.on("mousemove", "node", function (ev) { if (hover >= 0) showTip(hover, ev.renderedPosition); });
    cy.on("mouseout", "node", function () { hover = -1; tip.style.display = "none"; render(); container.style.cursor = ""; });
    cy.on("grab", "node", function () { tip.style.display = "none"; });

    document.getElementById("loading").hidden = true;
    showStats(); showContagion(); render();
    runLayout(false);
    requestAnimationFrame(frame);

    if (window.matchMedia) {
      window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
        readColours(); cy.style(buildStyle()); render();
      });
    }
  }).catch(function (err) {
    document.getElementById("loading").textContent = "Could not load the network. Check that python app.py is still running.";
    if (window.console) console.error(err);
  });
})();
