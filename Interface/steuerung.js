'use strict';
(() => {
  const el = id => document.getElementById(id);
  let token = '', lastState = null, signature = '', seenFinished = '', stopped = false;
  const titles = {reference:'Referenzanalyse',download:'Neue Daten sammeln',resume:'Abruf fortsetzen',
    prepare:'Daten prüfen',analyse:'Neue Daten analysieren',install:'FinBERT einrichten',timings:'Veröffentlichungszeiten speichern'};
  const localToday = new Date();
  const today = `${localToday.getFullYear()}-${String(localToday.getMonth()+1).padStart(2,'0')}-${String(localToday.getDate()).padStart(2,'0')}`;
  el('end').value = today; el('end').max = today;
  function enableControls() {
    const running = !lastState || lastState.job.status === 'running';
    document.querySelectorAll('.job-button').forEach(button => { button.disabled = running; });
    const selected = lastState?.datasets.find(item => item.id === el('dataset').value);
    ['resume','prepare','analyse','timings'].forEach(id => { el(id).disabled = running || !selected; });
    if (selected) {
      el('prepare').disabled ||= selected.status !== 'complete';
      el('analyse').disabled ||= selected.status !== 'complete' || !lastState.finbert;
      el('resume').disabled ||= selected.status === 'complete';
    }
    el('dataset-info').textContent = selected
      ? `${selected.label} · ${selected.status === 'complete' ? 'Abruf abgeschlossen' : 'Abruf unvollständig – kann fortgesetzt werden'}`
      : 'Noch kein neuer Datenbestand. Die Ausgangsdaten der Arbeit bleiben unverändert.';
    el('install').hidden = !!lastState?.finbert;
    el('finbert-state').textContent = lastState?.finbert
      ? 'FinBERT ist für neue Transkripte eingerichtet. Das Modell ist lokal vorhanden.'
      : 'Für neue Transkripte zuerst FinBERT einrichten. Python-Pakete und die festgelegte Modellversion werden aus dem Internet geladen (Modell ca. 439 MB).';
  }
  function options() {
    return {tickers:[...document.querySelectorAll('[name=ticker]:checked')].map(item => item.value),
      start:el('start').value,end:el('end').value,request_limit:Number(el('request-limit').value),pause_seconds:Number(el('request-pause').value)};
  }
  async function submit(action) {
    const body = {action, dataset:el('dataset').value, options:options()};
    if (action === 'download' && (!body.options.tickers.length || body.options.start > body.options.end)) {
      el('job-message').textContent = 'Unternehmen und einen gültigen Zeitraum auswählen.'; return;
    }
    if (['download','resume'].includes(action)) body.keys = {alpha_vantage:el('alpha-key').value,serpapi:el('serp-key').value};
    if (action === 'timings') body.csv = el('timing-csv').value;
    document.querySelectorAll('.job-button').forEach(button => { button.disabled = true; });
    try {
      const response = await fetch('/api/job', {method:'POST',headers:{'Content-Type':'application/json','X-Event-Token':token},body:JSON.stringify(body)});
      const result = await response.json();
      if (!response.ok) throw new Error(result.message);
      el('alpha-key').value = ''; el('serp-key').value = '';
      el('job-message').textContent = 'Auftrag gestartet.';
      await refresh();
    } catch (error) { el('job-message').textContent = error.message; enableControls(); }
  }
  function setRun(show = false) {
    const run = lastState?.runs.find(item => item.id === el('run').value);
    if (!run) return;
    window.setAnalysisFigures(run.figures.map(figure => ({...figure,image:figure.image+'?v='+encodeURIComponent(lastState.job.finished_at || 'initial')})), show);
    el('report').href = run.report;
  }
  async function refresh() {
    const response = await fetch('/api/state', {cache:'no-store'});
    if (!response.ok) throw new Error('Das lokale Analyseprogramm ist nicht erreichbar.');
    lastState = await response.json(); token = lastState.token;
    el('connection').classList.remove('error');
    el('connection').textContent = 'Lokales Analyseprogramm verbunden · eigenständige Kopie';
    const nextSignature = JSON.stringify([lastState.datasets,lastState.runs.map(run=>[run.id,run.label])]);
    if (signature !== nextSignature) {
      signature = nextSignature;
      const previousDataset = el('dataset').value, previousRun = el('run').value;
      el('dataset').replaceChildren();
      if (!lastState.datasets.length) el('dataset').add(new Option('Noch kein neuer Bestand',''));
      lastState.datasets.forEach(item => el('dataset').add(new Option(item.label,item.id)));
      if (lastState.datasets.some(item=>item.id===previousDataset)) el('dataset').value=previousDataset;
      el('run').replaceChildren();
      lastState.runs.forEach(item=>el('run').add(new Option(item.label,item.id)));
      if (lastState.runs.some(item=>item.id===previousRun)) el('run').value=previousRun;
      setRun();
    }
    const job = lastState.job;
    el('job-title').textContent = titles[job.action] || 'Bereit';
    el('job-status').textContent = {idle:'Bereit',running:'Läuft …',done:'Abgeschlossen',failed:'Nicht abgeschlossen'}[job.status];
    el('job-log').textContent = job.messages.join('\n');
    if (job.status === 'running') { el('job-message').textContent='Du kannst währenddessen die Grafiken ansehen.'; el('job-log').scrollTop=el('job-log').scrollHeight; }
    if (job.finished_at && seenFinished !== job.finished_at) {
      seenFinished=job.finished_at;
      el('job-message').textContent=job.result?.message || job.messages.at(-1) || 'Auftrag beendet.';
      if (job.result?.missing_times?.length) el('job-message').textContent += '\nOhne Veröffentlichungszeit: '+job.result.missing_times.join(', ');
      if (job.result?.bestand) { el('dataset').value=job.result.bestand; }
      if (job.result?.run) { el('run').value=job.result.run; setRun(true); }
    }
    enableControls();
  }
  async function poll() {
    if (stopped) return;
    try { await refresh(); }
    catch (error) {
      lastState = null; enableControls();
      el('connection').classList.add('error');
      el('connection').textContent='Nicht verbunden. START_INTERFACE.bat im Ordner dieser Kopie öffnen.';
    }
    setTimeout(poll, lastState?.job.status === 'running' ? 1500 : 5000);
  }
  ['reference','resume','prepare','analyse','install','timings'].forEach(id=>el(id).addEventListener('click',()=>submit(id)));
  el('download-form').addEventListener('submit',event=>{event.preventDefault();submit('download');});
  el('dataset').addEventListener('change',enableControls);
  el('run').addEventListener('change',()=>setRun(true));
  el('stop-server').addEventListener('click',async()=>{
    try {
      const response=await fetch('/api/stop',{method:'POST',headers:{'X-Event-Token':token}});
      const result=await response.json();
      if (!response.ok) throw new Error(result.message);
      stopped=true;lastState=null;enableControls();el('connection').textContent='Analyseprogramm beendet. Zum Neustart START_INTERFACE.bat öffnen.';
    } catch(error) {el('job-message').textContent=error.message;}
  });
  enableControls();
  if (location.protocol === 'file:') {
    el('connection').classList.add('error');
    el('connection').textContent='Für Berechnungen und Downloads START_INTERFACE.bat im Ordner dieser Kopie öffnen. Die Galerie ist auch hier sichtbar.';
  } else poll();
})();
