"use strict";
/* Uganda Airlines Flight Data Explorer — Sep/Oct 2026 dataset.
   Data comes from data.json (built by build_data.py from this repo). */

const $ = s => document.querySelector(s);
const PUNCT_CLASS = { "early": "d-early", "on time": "d-ontime",
                      "delayed": "d-delayed", "heavily delayed": "d-heavily" };

let DATA = null;
let state = { month: "all", q: "", origin: "", dest: "", tail: "",
              punct: "", from: "", to: "" };
let filtered = [];
let selected = null;          // selected flight object
let playTimer = null, playPos = 0;

/* ---------- map setup ---------- */
const map = L.map("map", { worldCopyJump: true }).setView([8, 28], 4);
const darkTiles = L.tileLayer(
  "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
  { attribution: "&copy; OpenStreetMap contributors &copy; CARTO", subdomains: "abcd", maxZoom: 19 });
const osmTiles = L.tileLayer(
  "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
  { attribution: "&copy; OpenStreetMap contributors", maxZoom: 19 });
darkTiles.addTo(map);
L.control.layers({ "Dark": darkTiles, "Streets": osmTiles }, null,
                 { position: "topleft" }).addTo(map);

const routeLayer = L.layerGroup().addTo(map);
const airportLayer = L.layerGroup().addTo(map);
const trackLayer = L.layerGroup().addTo(map);
const fixLayer = L.layerGroup().addTo(map);

const FIX_COLORS = { fix: "#7dd3fc", navaid: "#f6b73c", location: "#94a3b8", coord_fix: "#64748b" };
function renderWaypoints() {
  fixLayer.clearLayers();
  if (!DATA || !$("#lyrFixes").checked) return;
  for (const w of DATA.waypoints) {
    L.circleMarker([w.lat, w.lon], {
      radius: w.kind === "fix" ? 2.2 : 3,
      color: FIX_COLORS[w.kind] || "#7dd3fc", weight: 1,
      fillColor: FIX_COLORS[w.kind] || "#7dd3fc", fillOpacity: 0.7,
    }).addTo(fixLayer)
      .bindTooltip(`${w.name} · ${w.kind}`, { direction: "top" });
  }
}
let planeMarker = null;

const aptByCode = {};
function apt(code) { return aptByCode[code] || { lat: 0, lon: 0, name: code }; }

/* curve a route slightly so A->B and B->A are both visible */
function arcPoints(a, b) {
  const lat1 = a.lat, lon1 = a.lon, lat2 = b.lat, lon2 = b.lon;
  const mx = (lat1 + lat2) / 2, my = (lon1 + lon2) / 2;
  const dx = lat2 - lat1, dy = lon2 - lon1;
  const dist = Math.hypot(dx, dy) || 1;
  const bend = Math.min(0.22 * dist, 6);
  const cx = mx - dy / dist * bend, cy = my + dx / dist * bend;
  const pts = [];
  for (let i = 0; i <= 40; i++) {
    const t = i / 40, u = 1 - t;
    pts.push([u * u * lat1 + 2 * u * t * cx + t * t * lat2,
              u * u * lon1 + 2 * u * t * cy + t * t * lon2]);
  }
  return pts;
}

function routeColor(o, d) {
  if (o === "EBB") return "#38bdf8";
  if (d === "EBB") return "#f6b73c";
  return "#a78bfa";
}

/* ---------- filtering ---------- */
function applyFilters() {
  filtered = DATA.flights.filter(f =>
    (state.month === "all" || f.month === state.month) &&
    (!state.origin || f.origin === state.origin) &&
    (!state.dest || f.dest === state.dest) &&
    (!state.tail || f.tail === state.tail) &&
    (!state.punct || f.punctuality === state.punct) &&
    (!state.from || f.date >= state.from) &&
    (!state.to || f.date <= state.to) &&
    (!state.q || (f.flight + " " + f.callsign).toUpperCase().includes(state.q)));
  renderAll();
}

function renderAll() {
  renderStats(); renderRoutes(); renderAirports(); renderFlightList(); renderDaily();
}

/* ---------- sidebar renders ---------- */
function renderStats() {
  const tails = new Set(filtered.map(f => f.tail).filter(Boolean)).size;
  const routes = new Set(filtered.map(f => f.origin + "-" + f.dest)).size;
  const delays = filtered.map(f => f.dep_delay).filter(v => v !== null)
                         .sort((a, b) => a - b);
  const med = delays.length ? delays[Math.floor(delays.length / 2)] : "–";
  $("#statCards").innerHTML = [
    [filtered.length, "flights"], [routes, "routes"],
    [tails, "tails"], [(med > 0 ? "+" : "") + med + (med === "–" ? "" : " min"), "median delay"],
  ].map(([v, l]) => `<div class="stat"><b>${v}</b><span>${l}</span></div>`).join("");
}

function aggregateRoutes(list) {
  const m = new Map();
  for (const f of list) {
    const k = f.origin + "→" + f.dest;
    m.set(k, (m.get(k) || 0) + 1);
  }
  return [...m.entries()].map(([k, count]) => {
    const [origin, dest] = k.split("→");
    return { origin, dest, count };
  }).sort((a, b) => b.count - a.count);
}

function renderRoutes() {
  routeLayer.clearLayers();
  if (!$("#lyrRoutes").checked) return;
  for (const r of aggregateRoutes(filtered)) {
    const line = L.polyline(arcPoints(apt(r.origin), apt(r.dest)), {
      color: routeColor(r.origin, r.dest),
      weight: 1 + Math.sqrt(r.count) * 0.55,
      opacity: 0.55,
    }).addTo(routeLayer);
    line.bindTooltip(`${r.origin} → ${r.dest} · ${r.count} flights`,
                     { sticky: true });
    line.on("click", () => {
      state.origin = r.origin; state.dest = r.dest;
      $("#fOrigin").value = r.origin; $("#fDest").value = r.dest;
      applyFilters();
    });
  }
}

function renderAirports() {
  airportLayer.clearLayers();
  if (!$("#lyrAirports").checked && !$("#lyrNotam").checked) return;
  const local = {};
  for (const f of filtered) {
    local[f.origin] = local[f.origin] || { out: 0, inn: 0 };
    local[f.dest] = local[f.dest] || { out: 0, inn: 0 };
    local[f.origin].out++; local[f.dest].inn++;
  }
  for (const a of DATA.airports) {
    const mov = (local[a.iata]?.out || 0) + (local[a.iata]?.inn || 0);
    if ($("#lyrAirports").checked) {
      const c = L.circleMarker([a.lat, a.lon], {
        radius: 5 + Math.sqrt(a.movements) * 0.9,
        color: "#f6b73c", weight: 1.5, fillColor: "#f6b73c", fillOpacity: 0.35,
      }).addTo(airportLayer);
      c.bindTooltip(`<b>${a.iata}</b> ${a.name}`, { direction: "top", offset: [0, -6],
                    className: "apt-label", permanent: true, opacity: 0.9 });
      c.on("click", () => showAirport(a.iata));
    }
    const n = (DATA.notams[a.iata] || []).length;
    if ($("#lyrNotam").checked && n) {
      L.marker([a.lat, a.lon], {
        icon: L.divIcon({ className: "", html: `<div class="notam-badge">${n}</div>`,
                          iconSize: [20, 20],
                          iconAnchor: [-8, 14]
                        }),
        interactive: false,
      }).addTo(airportLayer);
    }
  }
}

function fmtDelay(f) {
  if (f.dep_delay === null) return "";
  const cls = PUNCT_CLASS[f.punctuality] || "";
  const sign = f.dep_delay > 0 ? "+" : "";
  return `<span class="dchip ${cls}">${sign}${f.dep_delay}m dep</span>`;
}

function renderFlightList() {
  $("#flightCount").textContent = filtered.length + " shown";
  const el = $("#flightList");
  const show = filtered.slice(0, 400);
  el.innerHTML = show.map(f => `
    <button class="flight ${selected && selected.id === f.id ? "sel" : ""}" data-id="${f.id}">
      <span class="r1"><span>${f.flight} · ${f.origin}→${f.dest}</span>${fmtDelay(f)}</span>
      <span class="r2"><span>${f.date} · ${f.dep_utc.slice(11, 16)}Z</span>
      <span>${f.tail || "tail n/a"} · ${f.air_min} min</span></span>
    </button>`).join("") ||
    `<p class="hint">No flights match these filters.</p>`;
  el.querySelectorAll(".flight").forEach(b =>
    b.addEventListener("click", () =>
      selectFlight(DATA.flights.find(f => f.id === b.dataset.id), true)));
  if (filtered.length > show.length)
    el.innerHTML += `<p class="hint">…and ${filtered.length - show.length} more — narrow the filters to see them.</p>`;
}

function renderDaily() {
  const days = new Map();
  for (const f of filtered) days.set(f.date, (days.get(f.date) || 0) + 1);
  const all = DATA.daily.map(d => [d.date, days.get(d.date) || 0]);
  const cv = $("#dailyChart"), ctx = cv.getContext("2d");
  const W = cv.width = cv.clientWidth * 2, H = cv.height = 180;
  ctx.clearRect(0, 0, W, H);
  const max = Math.max(...all.map(d => d[1]), 1);
  const bw = W / all.length;
  all.forEach(([date, n], i) => {
    const h = (n / max) * (H - 18);
    ctx.fillStyle = date.startsWith("2026-10") ? "#f6b73c" : "#38bdf8";
    ctx.fillRect(i * bw + 1, H - 14 - h, bw - 2, h);
  });
  ctx.fillStyle = "#93a4c4"; ctx.font = "17px system-ui";
  ctx.fillText(all[0]?.[0] || "", 2, H - 1);
  const last = all[all.length - 1]?.[0] || "";
  ctx.fillText(last, W - ctx.measureText(last).width - 2, H - 1);
  $("#dailyHint").textContent =
    `Peak day: ${all.reduce((a, b) => b[1] > (a?.[1] || 0) ? b : a, null)?.join(" · ") || "–"} flights. Gold = October, blue = September.`;
}

/* ---------- flight selection & replay ---------- */
function bearing(p1, p2) {
  const dLon = (p2[1] - p1[1]) * Math.PI / 180;
  const y = Math.sin(dLon) * Math.cos(p2[0] * Math.PI / 180);
  const x = Math.cos(p1[0] * Math.PI / 180) * Math.sin(p2[0] * Math.PI / 180) -
            Math.sin(p1[0] * Math.PI / 180) * Math.cos(p2[0] * Math.PI / 180) * Math.cos(dLon);
  return (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
}

function selectFlight(f, fly) {
  selected = f; stopPlay(); playPos = 0;
  trackLayer.clearLayers();
  document.querySelectorAll(".flight").forEach(b =>
    b.classList.toggle("sel", b.dataset.id === f.id));
  if (f.path.length > 1) {
    L.polyline(f.path.map(p => [p[0], p[1]]),
               { color: "#f6b73c", weight: 3, opacity: 0.95 }).addTo(trackLayer);
    for (const [p, lab] of [[f.path[0], "takeoff"], [f.path[f.path.length - 1], "landing"]])
      L.circleMarker([p[0], p[1]], { radius: 5, color: "#fff", weight: 2,
        fillColor: "#d21034", fillOpacity: 1 }).addTo(trackLayer)
        .bindTooltip(`${f.flight} ${lab}`, { direction: "top" });
    planeMarker = L.marker([f.path[0][0], f.path[0][1]], {
      icon: L.divIcon({ className: "", html: `<div class="plane-icon" id="planeIcon">✈</div>`,
                        iconSize: [26, 26], iconAnchor: [13, 13] }),
      interactive: false, zIndexOffset: 1000,
    }).addTo(trackLayer);
    if (fly) map.flyToBounds(L.latLngBounds(f.path.map(p => [p[0], p[1]])).pad(0.15),
                             { duration: 0.8 });
  }
  $("#flightBar").classList.remove("hidden");
  $("#fbFlight").textContent = `${f.flight} ${f.origin}→${f.dest} · ${f.date}`;
  updateReplayUI();
  showFlightDetail(f);
}

function updateReplayUI() {
  const f = selected; if (!f || !f.path.length) return;
  const i = Math.min(Math.floor(playPos), f.path.length - 1);
  const p = f.path[i];
  const icon = document.getElementById("planeIcon");
  if (planeMarker) {
    planeMarker.setLatLng([p[0], p[1]]);
    if (icon && f.path[i + 1])
      icon.style.transform = `rotate(${bearing(p, f.path[i + 1]) - 45}deg)`;
  }
  $("#scrub").value = Math.round(playPos / Math.max(f.path.length - 1, 1) * 1000);
  $("#fbReadout").textContent =
    `${p[0].toFixed(3)}, ${p[1].toFixed(3)} · ${p[2].toLocaleString()} ft · ${p[3]} kt`;
  drawProfile();
}

function drawProfile() {
  const f = selected; if (!f || f.path.length < 2) return;
  let cv = document.getElementById("profile");
  if (!cv) return;
  const ctx = cv.getContext("2d");
  const W = cv.width = cv.clientWidth * 2, H = cv.height = 130;
  ctx.clearRect(0, 0, W, H);
  const maxAlt = Math.max(...f.path.map(p => p[2]), 1000);
  ctx.beginPath();
  f.path.forEach((p, i) => {
    const x = i / (f.path.length - 1) * W, y = H - 8 - (p[2] / maxAlt) * (H - 22);
    i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
  });
  ctx.strokeStyle = "#f6b73c"; ctx.lineWidth = 2.5; ctx.stroke();
  ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath();
  ctx.fillStyle = "rgba(246,183,60,.15)"; ctx.fill();
  const i = Math.min(Math.floor(playPos), f.path.length - 1);
  ctx.fillStyle = "#fff";
  ctx.beginPath();
  ctx.arc(i / (f.path.length - 1) * W, H - 8 - (f.path[i][2] / maxAlt) * (H - 22), 5, 0, 7);
  ctx.fill();
  ctx.fillStyle = "#93a4c4"; ctx.font = "16px system-ui";
  ctx.fillText(`max ${maxAlt.toLocaleString()} ft`, 6, 18);
}

function stopPlay() {
  if (playTimer) cancelAnimationFrame(playTimer), playTimer = null;
  $("#playBtn").textContent = "▶";
}
function togglePlay() {
  if (!selected) return;
  if (playTimer) return stopPlay();
  $("#playBtn").textContent = "❚❚";
  let last = performance.now();
  const stepFn = now => {
    const dt = (now - last) / 1000; last = now;
    playPos += dt * 6 * Number($("#speed").value);
    if (playPos >= selected.path.length - 1) {
      playPos = selected.path.length - 1; updateReplayUI(); return stopPlay();
    }
    updateReplayUI();
    playTimer = requestAnimationFrame(stepFn);
  };
  playTimer = requestAnimationFrame(stepFn);
}

/* ---------- detail panels ---------- */
function delayText(v) {
  if (v === null) return "–";
  return (v > 0 ? "+" : "") + v + " min";
}

function notamHtml(code) {
  const rows = DATA.notams[code] || [];
  if (!rows.length) return `<p class="hint">No notices in the 2026-10-20 snapshot for ${code}.</p>`;
  return rows.slice(0, 12).map(n => `
    <div class="notam">
      <div class="nhead"><b>${n.id}</b><span>${n.category}</span></div>
      <div class="nhead"><span>${n.from} → ${n.to}${n.schedule ? " · " + n.schedule : ""} UTC</span></div>
      <p>${n.text}</p>
    </div>`).join("") +
    (rows.length > 12 ? `<p class="hint">…and ${rows.length - 12} more in notams.csv.</p>` : "");
}

function showFlightDetail(f) {
  const d = $("#detail");
  d.classList.remove("hidden");
  d.innerHTML = `
    <button class="close" onclick="closeDetail()">✕</button>
    <h3>${f.flight} <span class="tag">${f.callsign}</span></h3>
    <div class="sub">${apt(f.origin).name} (${f.origin}) → ${apt(f.dest).name} (${f.dest}) · ${f.date}</div>
    <table>
      <tr><td class="k">Aircraft</td><td>${f.tail || "not recorded"}</td></tr>
      <tr><td class="k">Takeoff (UTC)</td><td>${f.dep_utc}</td></tr>
      <tr><td class="k">Landing (UTC)</td><td>${f.arr_utc}</td></tr>
      <tr><td class="k">Air time</td><td>${f.air_min} min · ${f.fixes} track fixes</td></tr>
      <tr><td class="k">Departure delay*</td><td>${delayText(f.dep_delay)} ${f.punctuality ? `<span class="dchip ${PUNCT_CLASS[f.punctuality]}">${f.punctuality}</span>` : ""}</td></tr>
      <tr><td class="k">Arrival delay*</td><td>${delayText(f.arr_delay)}</td></tr>
      <tr><td class="k">Runways (EBB end)</td><td>${[f.dep_rwy && "dep " + f.dep_rwy, f.arr_rwy && "arr " + f.arr_rwy].filter(Boolean).join(" · ") || "–"}</td></tr>
      <tr><td class="k">Weather codes</td><td>${[f.dep_wx, f.arr_wx].filter(Boolean).join(" · ") || "none reported"}</td></tr>
      <tr><td class="k">Fixes passed (≤3 nm)</td><td>${f.fixes_passed && f.fixes_passed.length ? f.fixes_passed.join(" → ") : "none listed nearby"}</td></tr>
    </table>
    <p class="hint">* vs FTA plan STD/STA; takeoff-based, includes taxi-out.</p>
    <h4>Altitude profile — drag the replay slider below</h4>
    <canvas id="profile" height="65" style="width:100%"></canvas>
    <h4>NOTAMs at ${f.origin} (snapshot 2026-10-20)</h4>
    ${notamHtml(f.origin)}
    <h4>NOTAMs at ${f.dest}</h4>
    ${notamHtml(f.dest)}`;
  drawProfile();
}

function showAirport(code) {
  const a = apt(code);
  const out = DATA.flights.filter(f => f.origin === code);
  const inn = DATA.flights.filter(f => f.dest === code);
  const top = aggregateRoutes([...out, ...inn]).slice(0, 6);
  const d = $("#detail");
  d.classList.remove("hidden");
  d.innerHTML = `
    <button class="close" onclick="closeDetail()">✕</button>
    <h3>${code} — ${a.name}</h3>
    <div class="sub">${a.icao} · ${a.lat.toFixed(3)}, ${a.lon.toFixed(3)}</div>
    <table>
      <tr><td class="k">Departures (dataset)</td><td>${out.length}</td></tr>
      <tr><td class="k">Arrivals (dataset)</td><td>${inn.length}</td></tr>
      <tr><td class="k">NOTAMs in snapshot</td><td>${(DATA.notams[code] || []).length}</td></tr>
    </table>
    <h4>Busiest routes touching ${code}</h4>
    <table>${top.map(r => `<tr><td>${r.origin} → ${r.dest}</td><td style="text-align:right">${r.count}</td></tr>`).join("")}</table>
    <h4>NOTAMs (snapshot 2026-10-20)</h4>
    ${notamHtml(code)}`;
}

function closeDetail() {
  $("#detail").classList.add("hidden");
  selected = null; stopPlay();
  trackLayer.clearLayers();
  $("#flightBar").classList.add("hidden");
  renderFlightList();
}
window.closeDetail = closeDetail;

/* ---------- wire up controls ---------- */
function fillSelects() {
  const codes = DATA.airports.map(a => a.iata).sort();
  for (const id of ["#fOrigin", "#fDest"])
    $(id).innerHTML = `<option value="">All airports</option>` +
      codes.map(c => `<option>${c}</option>`).join("");
  const tails = [...new Set(DATA.flights.map(f => f.tail).filter(Boolean))].sort();
  $("#fTail").innerHTML = `<option value="">All tails</option>` +
    tails.map(t => `<option>${t}</option>`).join("");
  const [p0, p1] = DATA.stats.period;
  for (const id of ["#dFrom", "#dTo"]) { $(id).min = p0; $(id).max = p1; }
}

document.querySelectorAll(".monthswitch button").forEach(b =>
  b.addEventListener("click", () => {
    document.querySelectorAll(".monthswitch button")
      .forEach(x => x.classList.toggle("active", x === b));
    state.month = b.dataset.month;
    applyFilters();
  }));
$("#q").addEventListener("input", e => { state.q = e.target.value.trim().toUpperCase(); applyFilters(); });
$("#fOrigin").addEventListener("change", e => { state.origin = e.target.value; applyFilters(); });
$("#fDest").addEventListener("change", e => { state.dest = e.target.value; applyFilters(); });
$("#fTail").addEventListener("change", e => { state.tail = e.target.value; applyFilters(); });
$("#fPunct").addEventListener("change", e => { state.punct = e.target.value; applyFilters(); });
$("#dFrom").addEventListener("change", e => { state.from = e.target.value; applyFilters(); });
$("#dTo").addEventListener("change", e => { state.to = e.target.value; applyFilters(); });
for (const id of ["#lyrRoutes", "#lyrAirports", "#lyrNotam"])
  $(id).addEventListener("change", renderAll);
$("#lyrFixes").addEventListener("change", renderWaypoints);
$("#reset").addEventListener("click", () => {
  state = { month: "all", q: "", origin: "", dest: "", tail: "", punct: "", from: "", to: "" };
  for (const id of ["#q", "#fOrigin", "#fDest", "#fTail", "#fPunct", "#dFrom", "#dTo"])
    $(id).value = "";
  document.querySelectorAll(".monthswitch button")
    .forEach(x => x.classList.toggle("active", x.dataset.month === "all"));
  applyFilters();
});
$("#playBtn").addEventListener("click", togglePlay);
$("#closeFlight").addEventListener("click", closeDetail);
$("#scrub").addEventListener("input", e => {
  if (!selected) return;
  stopPlay();
  playPos = Number(e.target.value) / 1000 * (selected.path.length - 1);
  updateReplayUI();
});
document.addEventListener("keydown", e => { if (e.key === "Escape") closeDetail(); });

/* top routes list */
function renderTopRoutes() {
  $("#topRoutes").innerHTML = aggregateRoutes(filtered).slice(0, 10).map(r => `
    <li data-o="${r.origin}" data-d="${r.dest}">
      <span class="rc">${r.origin} → ${r.dest}</span><b>${r.count}</b></li>`).join("");
  document.querySelectorAll("#topRoutes li").forEach(li =>
    li.addEventListener("click", () => {
      state.origin = li.dataset.o; state.dest = li.dataset.d;
      $("#fOrigin").value = state.origin; $("#fDest").value = state.dest;
      applyFilters();
    }));
}
const _renderAll = renderAll;
renderAll = function () { _renderAll(); renderTopRoutes(); };

/* ---------- boot ---------- */
fetch("data.json")
  .then(r => r.json())
  .then(d => {
    DATA = d;
    for (const a of d.airports) aptByCode[a.iata] = a;
    fillSelects();
    filtered = d.flights;
    renderAll();
    const pts = d.airports.map(a => [a.lat, a.lon]);
    map.flyToBounds(L.latLngBounds(pts).pad(0.08), { duration: 0.6 });
  })
  .catch(err => {
    document.querySelector(".sidebar").innerHTML =
      `<section class="panel"><h2>Could not load data.json</h2>
       <p class="hint">${err}. Run <code>python3 website/build_data.py</code>
       and serve this folder over HTTP.</p></section>`;
  });
