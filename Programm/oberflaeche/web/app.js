"use strict";
let state, token, config, lastJob = "", loading = false;
const $ = id => document.getElementById(id);
const fields = {start:"start", end:"end", benchmark:"benchmark", return_type:"return-type", covariance:"covariance", request_limit:"request-limit", pause_seconds:"pause", sentiment_method:"sentiment-method"};
const flags = {abs_sue_for_abs_car:"abs-sue",fixed_effects:"fixed-effects", winsorize:"winsorize", only_amc:"only-amc", robustness:"robustness", abs_car_robustness:"abs-robustness", download_transcripts:"download-transcripts", download_trends:"download-trends"};
function notify(message) { $("notification").textContent = message; $("notification").hidden = !message; }
function tab(name) {
  document.body.classList.toggle("results-view", name === "results");
  document.querySelectorAll("[data-panel]").forEach(node => node.classList.toggle("active", node.dataset.panel === name));
  document.querySelectorAll("[data-tab]").forEach(node => node.classList.toggle("active", node.dataset.tab === name));
}
function option(select, value, label) { const node = document.createElement("option"); node.value = value; node.textContent = label; select.append(node); }
function fill() {
  config = structuredClone(state.config);
  Object.entries(fields).forEach(([key,id]) => $(id).value = config[key]);
  Object.entries(flags).forEach(([key,id]) => $(id).checked = config[key]);
  $("tickers").value = config.tickers.join(", ");
  $("window-start").value = config.window[0]; $("window-end").value = config.window[1];
  $("est-start").value = config.estimation[0]; $("est-end").value = config.estimation[1];
  document.querySelectorAll("[name=predictor]").forEach(node => node.checked = config.predictors.includes(node.value));
  $("import-path").value ||= state.import_default;
  companies(); stocks();
}
function stocks() {
  const chosen = config.bestand;
  $("bestand").replaceChildren(); option($("bestand"), "", "Zuerst Daten importieren oder sammeln");
  state.bestaende.forEach(item => option($("bestand"), item.id, `${item.art === "import" ? "Import" : "Download"} · ${item.created_at.replace("T", " ").slice(0,16)}${item.ereignisse === null ? "" : " · " + item.ereignisse + " Ereignisse"}`));
  $("bestand").value = state.bestaende.some(item => item.id === chosen) ? chosen : config.bestand;
  stockInfo();
}
function stockInfo() {
  const item = state.bestaende.find(item => item.id === $("bestand").value);
  $("bestand-info").textContent = item ? `${item.aufbereitet ? "Aufbereitet" : "Rohdaten"}${item.berechnet ? " · Kennzahlen vorhanden" : ""}${item.download_status === "incomplete" ? " · Download unvollständig, später fortsetzen" : ""}. Bei veränderten Einstellungen erneut aufbereiten und berechnen.` : "Noch kein Datenbestand ausgewählt.";
}
function companies() {
  $("company-settings").replaceChildren();
  const tickers = $("tickers").value.toUpperCase().split(/[,;\s]+/).filter(Boolean);
  [...new Set(tickers)].forEach(ticker => {
    const container = document.createElement("div"); container.className = "two company"; container.dataset.ticker = ticker;
    const queryLabel = document.createElement("label"); queryLabel.textContent = ticker + " · Suchbegriff";
    const query = document.createElement("input"); query.className = "query"; query.value = config.queries[ticker] || ticker + " stock"; queryLabel.append(query);
    const monthLabel = document.createElement("label"); monthLabel.textContent = "Geschäftsjahresende (Monat)";
    const month = document.createElement("input"); month.type = "number"; month.min = 1; month.max = 12; month.className = "month"; month.value = config.fiscal_year_end[ticker] || 12; monthLabel.append(month);
    container.append(queryLabel, monthLabel); $("company-settings").append(container);
  });
}
function readConfig() {
  const result = structuredClone(config);
  Object.entries(fields).forEach(([key,id]) => result[key] = $(id).value);
  result.benchmark = result.benchmark.trim().toUpperCase();
  result.request_limit = Number(result.request_limit); result.pause_seconds = Number(result.pause_seconds);
  Object.entries(flags).forEach(([key,id]) => result[key] = $(id).checked);
  result.bestand = $("bestand").value;
  result.tickers = [...new Set($("tickers").value.toUpperCase().split(/[,;\s]+/).filter(Boolean))];
  result.window = [Number($("window-start").value), Number($("window-end").value)];
  result.estimation = [Number($("est-start").value), Number($("est-end").value)];
  result.predictors = [...document.querySelectorAll("[name=predictor]:checked")].map(node => node.value);
  document.querySelectorAll(".company").forEach(node => {
    result.queries[node.dataset.ticker] = node.querySelector(".query").value.trim();
    result.fiscal_year_end[node.dataset.ticker] = Number(node.querySelector(".month").value);
  });
  return result;
}
async function post(path, payload) {
  const response = await fetch(path, {method:"POST", headers:{"Content-Type":"application/json", "X-Event-Token":token}, body:JSON.stringify(payload)});
  const result = await response.json();
  if (!response.ok) throw new Error(result.message || "Vorgang fehlgeschlagen.");
  return result;
}
async function action(name) {
  try {
    notify(""); config = readConfig();
    await post("/api/job", {action:name, config, source:$("import-path").value.trim(), keys:{alpha_vantage:$("av-key").value.trim(), serpapi:$("serp-key").value.trim()}});
    $("av-key").value = ""; $("serp-key").value = "";
    await refresh();
  } catch (error) { notify(error.message); }
}
function analyses() {
  const chosen = $("analysis").value;
  $("analysis").replaceChildren(); option($("analysis"), "", "Auswertung wählen");
  const methods = {sentence:"FinBERT · Sätze", lc_sentence:"finbert-lc · Sätze", lc_context:"finbert-lc · Kontext"};
  state.analysen.forEach(item => option($("analysis"), item.id, `${item.created_at.replace("T", " ").slice(0,16)} · ${item.n} Ereignisse · ${methods[item.sentiment_method] || methods.sentence}`));
  $("analysis").value = state.analysen.some(item => item.id === chosen) ? chosen : state.analysen[0]?.id || "";
  report();
}
function report() {
  const id = $("analysis").value;
  $("result-links").replaceChildren(); $("report").hidden = !id; $("result-empty").hidden = !!id;
  if (!id) { $("report").removeAttribute("src"); return; }
  const base = "/dateien/ergebnisse/" + encodeURIComponent(id) + "/";
  const source = base + "Bericht/bericht.html?embed=1";
  if ($("report").getAttribute("src") !== source) $("report").src = source;
  const links = {"Gesamten Bericht öffnen ↗":"Bericht/bericht.html"};
  const comparison = (state.vergleiche || []).find(item => Object.values(item.analysen).includes(id));
  if (comparison) links["Sentimentvergleich öffnen ↗"] = "../" + encodeURIComponent(comparison.id) + "/bericht.html";
  const selected = state.analysen.find(item => item.id === id);
  if (selected?.jamovi) {
    links["Übersichtliche CSV · Excel"] = "Uebersichtliche_Daten.csv";
    links["Daten für jamovi"] = "Jamovi_Daten.csv";
    links["Variablen erklärt"] = "Jamovi_Anleitung.md";
  }
  Object.entries(links).forEach(([label,file]) => { const a = document.createElement("a"); a.className = "secondary"; a.href = base + file; a.textContent = label; if (file.endsWith(".html")) { a.target = "_blank"; a.rel = "noreferrer"; } else a.download = file; $("result-links").append(a); });
}
async function refresh(first=false) {
  if (loading) return;
  loading = true;
  try {
    const response = await fetch("/api/state"); if (!response.ok) throw new Error("Oberfläche nicht erreichbar.");
    state = await response.json(); token = state.token;
    const job = state.job, running = job.status === "running";
    const jobKey = `${job.started_at || ""}|${job.status}`;
    if (first || (jobKey !== lastJob && ["done", "failed"].includes(job.status))) fill();
    $("job").hidden = job.status === "idle";
    $("job").className = "job " + (job.status === "failed" ? "failed" : running ? "" : "done");
    const names = {import:"Datenimport", download:"Datenakquise", resume:"Download fortsetzen", process:"Datenverarbeitung", finbert:"Textbewertung", calculate:"Berechnung", regression:"Regression", all:"Gesamte Analyse", sentiment_compare:"Vergleich der Sentimentverfahren"};
    $("job-title").textContent = names[job.action] || "";
    $("job-message").textContent = running ? "Läuft …" : job.status === "failed" ? "Gestoppt – Hinweis beachten" : "Abgeschlossen";
    $("job-log").textContent = (job.messages || []).join("\n");
    document.querySelectorAll("[data-action], #all, #save").forEach(node => node.disabled = running);
    if (jobKey !== lastJob || first) {
      analyses();
      if (job.status === "done" && job.result?.ordner) { $("analysis").value = job.result.ordner; report(); tab("results"); }
      if (job.status === "failed") notify(job.result?.message || "Vorgang fehlgeschlagen.");
      lastJob = jobKey;
    }
  } catch(error) { notify(error.message + " START_INTERFACE.bat muss geöffnet bleiben."); }
  finally { loading = false; }
}
document.querySelectorAll("[data-tab]").forEach(node => node.addEventListener("click", () => tab(node.dataset.tab)));
document.querySelectorAll("[data-switch]").forEach(node => node.addEventListener("click", () => tab(node.dataset.switch)));
document.querySelectorAll("[data-action]").forEach(node => node.addEventListener("click", () => action(node.dataset.action)));
$("company-refresh").addEventListener("click", companies);
$("analysis").addEventListener("change", report); $("bestand").addEventListener("change", stockInfo);
$("save").addEventListener("click", async () => { try { config = readConfig(); await post("/api/config", {config}); notify("Einstellungen gespeichert."); } catch(error) { notify(error.message); } });
window.addEventListener("message", event => {
  if (event.origin !== location.origin || event.source !== $("report").contentWindow || event.data?.type !== "event-study-height") return;
  const height = Number(event.data.height);
  if (Number.isFinite(height) && height > 0) $("report").style.height = Math.ceil(height + 16) + "px";
});
if (location.hash === "#ergebnisse") tab("results");
refresh(true); setInterval(() => refresh(), 1800);
