// Settings page: send the settings to the app, start a run, and show progress.

(function () {
  "use strict";

  var form = document.getElementById("settings");
  var runBtn = document.getElementById("run");
  var estimate = document.getElementById("estimate");
  var progress = document.getElementById("progress");
  var fill = document.getElementById("fill");
  var msg = document.getElementById("progress-msg");
  var secondsPerRun = parseFloat(form.dataset.secondsPerRun);
  var inputs = Array.prototype.slice.call(form.querySelectorAll("[data-kind]"));
  var polling = null;

  function values() {
    var v = {};
    inputs.forEach(function (el) {
      v[el.name] = el.dataset.kind === "bool" ? el.checked : el.value;
    });
    return v;
  }

  function updateEstimate() {
    var v = values();
    var runs = parseFloat(v.runs_per_setting) * parseFloat(v.T_steps) * 2;
    var secs = runs * secondsPerRun * (parseFloat(v.n_farms) / 300);
    if (!isFinite(secs) || secs <= 0) { estimate.textContent = ""; return; }
    var text = secs < 90 ? "about " + Math.max(1, Math.round(secs)) + " seconds" : "about " + Math.round(secs / 60) + " minutes";
    estimate.textContent = Math.round(runs).toLocaleString() + " outbreaks to simulate, " + text + ".";
  }

  function clearErrors() {
    form.querySelectorAll(".error").forEach(function (e) { e.textContent = ""; });
    form.querySelectorAll(".field.invalid").forEach(function (f) { f.classList.remove("invalid"); });
  }

  function showErrors(errors) {
    var first = null;
    Object.keys(errors).forEach(function (key) {
      var box = document.getElementById("e-" + key);
      if (box) box.textContent = errors[key];
      var field = form.querySelector('.field[data-key="' + key + '"]');
      if (field) { field.classList.add("invalid"); if (!first) first = field.querySelector("[data-kind]"); }
    });
    if (first) first.focus();
  }

  function setRunning(running) {
    runBtn.disabled = running;
    runBtn.textContent = running ? "Running..." : "Run simulation";
    inputs.forEach(function (el) { el.disabled = running; });
    document.getElementById("reset").disabled = running;
  }

  function poll() {
    fetch("/api/status").then(function (r) { return r.json(); }).then(function (s) {
      if (s.state === "running") {
        progress.hidden = false; setRunning(true);
        fill.style.width = Math.round(100 * s.progress) + "%";
        msg.textContent = s.message;
        polling = setTimeout(poll, 500);
      } else if (s.state === "done") {
        setRunning(false); fill.style.width = "100%";
        msg.innerHTML = s.message + ' See the <a href="/report">report</a>, or watch outbreaks on the new <a href="/even">even</a> and <a href="/hub">hub-heavy</a> networks.';
      } else if (s.state === "error") {
        setRunning(false); fill.style.width = "0";
        msg.textContent = s.message;
      }
    }).catch(function () {
      setRunning(false);
      msg.textContent = "Could not reach the app. Check that python app.py is still running.";
    });
  }

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    clearErrors();
    fetch("/api/run", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(values()),
    }).then(function (r) { return r.json().then(function (j) { return { ok: r.ok, body: j }; }); })
      .then(function (res) {
        if (!res.ok) { showErrors(res.body.errors || { _: "The run could not start." }); return; }
        progress.hidden = false; fill.style.width = "0"; msg.textContent = "Starting...";
        setRunning(true); clearTimeout(polling); poll();
      })
      .catch(function () { showErrors({ _: "Could not reach the app. Check that python app.py is still running." }); });
  });

  document.getElementById("reset").addEventListener("click", function () {
    inputs.forEach(function (el) {
      if (el.dataset.kind === "bool") el.checked = el.dataset.default === "true";
      else el.value = el.dataset.default;
    });
    clearErrors(); updateEstimate();
  });

  inputs.forEach(function (el) { el.addEventListener("input", updateEstimate); });
  updateEstimate();
  poll();   // if a run is already going (for example after a page refresh), show it
})();
