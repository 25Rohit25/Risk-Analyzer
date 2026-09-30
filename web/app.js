const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const state = { portfolio: null, briefing: null, forecast: [], page: 'overview', filter: 'all', search: '', project: null, signal: 'milestone' };
const paths = {
  overview: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
  portfolio: '<rect x="3" y="7" width="18" height="14" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 13h18"/>',
  briefing: '<path d="M6 3h9l4 4v14H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"/><path d="M14 3v5h5M8 12h8M8 16h8"/>',
  spark: '<path d="m12 2 1.6 6.4L20 10l-6.4 1.6L12 18l-1.6-6.4L4 10l6.4-1.6L12 2ZM19 18l.6 1.4L21 20l-1.4.6L19 22l-.6-1.4L17 20l1.4-.6L19 18Z"/>',
  impact: '<circle cx="12" cy="12" r="2"/><circle cx="4" cy="5" r="2"/><circle cx="20" cy="5" r="2"/><circle cx="4" cy="19" r="2"/><circle cx="20" cy="19" r="2"/><path d="m5.5 6.5 5 4M18.5 6.5l-5 4M5.5 17.5l5-4M18.5 17.5l-5-4"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m16 16 5 5"/>'
};
const icon = name => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || ''}</svg>`;
$$('[data-icon]').forEach(node => node.innerHTML = icon(node.dataset.icon));
const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const fmtDate = value => new Date(`${value}T12:00:00`).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
const money = (value,currency='USD') => new Intl.NumberFormat('en-US',{style:'currency',currency,maximumFractionDigits:0}).format(value || 0);
const badge = status => `<span class="status-badge ${status.replace(' ','-')}">${status === 'at risk' ? 'At risk' : status === 'on track' ? 'On track' : 'Critical'}</span>`;
const projectButton = project => `<button class="project-cell" data-project="${project.id}">${esc(project.name)}<small>${esc(project.client)}</small></button>`;

async function api(path, options = {}) {
  const isForm = options.body instanceof FormData;
  const response = await fetch(`/api${path}`, {...options, headers: isForm ? options.headers : {'Content-Type':'application/json',...(options.headers || {})}});
  let data;
  try { data = await response.json(); } catch { data = {}; }
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `Request failed (${response.status})`);
  return data;
}
function toast(message) { const node = $('#toast'); node.textContent = message; node.classList.add('visible'); clearTimeout(toast.timer); toast.timer = setTimeout(() => node.classList.remove('visible'), 3500); }
function showPage(page) {
  state.page = page;
  $$('.page').forEach(node => node.classList.toggle('active',node.id === `page-${page}`));
  $$('.nav-item').forEach(node => node.classList.toggle('active',node.dataset.page === page));
  $('#current-section').textContent = ({overview:'Overview',portfolio:'Portfolio',briefing:'Executive briefing',ask:'Ask intelligence',impact:'Change impact'})[page];
  window.scrollTo({top:0,behavior:'smooth'});
}

function renderOverview() {
  const data = state.portfolio;
  const priority = data.projects.find(project => project.risk.status === 'critical') || data.projects.find(project => project.risk.status === 'at risk');
  $('#overview-asof').textContent = `As of ${new Date().toLocaleDateString('en-US',{month:'long',day:'numeric',year:'numeric'})}`;
  const rows = data.projects.filter(p => p.risk.status !== 'on track').slice(0,5);
  const decisions = state.briefing.developments.slice(0,3);
  $('#overview-content').className = '';
  $('#overview-content').innerHTML = `
    <div class="overview-top"><div class="hero-health"><div><h2>Portfolio health at a glance</h2><p>Risk is calculated from delivery signals, with source evidence available for every finding.</p></div><div><div class="health-number">${data.total}<small>active initiatives</small></div><div class="health-track" aria-label="${data.on_track} on track, ${data.at_risk} at risk, ${data.critical} critical"><span class="track-good" style="width:${data.total ? data.on_track/data.total*100 : 0}%"></span><span class="track-warning" style="width:${data.total ? data.at_risk/data.total*100 : 0}%"></span><span class="track-critical" style="width:${data.total ? data.critical/data.total*100 : 0}%"></span></div><div class="health-legend"><span><i style="background:#72b89e"></i><b>${data.on_track}</b> on track</span><span><i style="background:#e3ab5d"></i><b>${data.at_risk}</b> at risk</span><span><i style="background:#db756e"></i><b>${data.critical}</b> critical</span></div></div></div>
    <div class="surface priority-card"><div><div class="section-caption">Highest priority</div>${priority ? `<h2>${esc(priority.name)}</h2><p>${esc(priority.risk.evidence[0]?.detail || 'This initiative needs review.')}</p><div class="priority-main"><strong>${priority.risk.score}</strong><span>risk score out of 100</span></div>` : '<h2>All clear</h2><p>No initiatives currently need escalation.</p>'}</div>${priority ? `<button class="button button-secondary" data-project="${priority.id}">Review initiative →</button>` : ''}</div></div>
    <div class="content-grid"><div class="surface table-surface"><div class="section-head"><h2>Needs attention</h2><button class="button button-ghost" data-go="portfolio">View portfolio →</button></div><div class="table-wrap"><table class="data-table"><thead><tr><th>Initiative</th><th>Risk</th><th>Owner</th><th>Status</th></tr></thead><tbody>${rows.length ? rows.map(p=>`<tr><td>${projectButton(p)}</td><td class="score-cell">${p.risk.score}/100</td><td class="owner-cell">${esc(p.owner)}</td><td>${badge(p.risk.status)}</td></tr>`).join('') : '<tr><td colspan="4" class="empty-data">No initiatives need attention.</td></tr>'}</tbody></table></div></div>
    <div class="right-stack"><div class="surface brief-preview"><div class="section-head"><h2>This week’s briefing</h2></div><p>Key delivery developments and management actions, ready to share.</p><div class="brief-line"><span>On track</span><strong>${data.on_track}</strong></div><div class="brief-line"><span>At risk</span><strong>${data.at_risk}</strong></div><div class="brief-line"><span>Critical</span><strong>${data.critical}</strong></div><button class="button button-secondary" data-go="briefing">Open briefing →</button></div><div class="surface decision-list"><h2>Key developments</h2>${decisions.length ? decisions.map(d=>`<div class="decision-item"><strong>${esc(d.project)}</strong><p>${esc(d.source.detail)}</p></div>`).join('') : '<p class="empty-data">No new risk developments.</p>'}</div></div></div>`;
}
function renderPortfolio() {
  const projects = state.portfolio.projects.filter(p => (state.filter === 'all' || p.risk.status === state.filter) &&
    `${p.name} ${p.client} ${p.owner}`.toLowerCase().includes(state.search));
  $('#portfolio-content').className = 'surface portfolio-table';
  $('#portfolio-content').innerHTML = `<div class="section-head"><h2>${projects.length} initiative${projects.length === 1 ? '' : 's'}</h2><small>Sorted by risk score</small></div><div class="table-wrap"><table class="data-table"><thead><tr><th>Initiative</th><th>Owner</th><th>Target date</th><th>Risk score</th><th>Status</th></tr></thead><tbody>${projects.length ? projects.map(p=>`<tr><td>${projectButton(p)}</td><td class="owner-cell">${esc(p.owner)}</td><td>${fmtDate(p.target_date)}</td><td class="score-cell">${p.risk.score}/100</td><td>${badge(p.risk.status)}</td></tr>`).join('') : '<tr><td colspan="5" class="empty-data">No initiatives match this view.</td></tr>'}</tbody></table></div>`;
}
function renderForecast() {
  const items = state.forecast.slice(0,3);
  $('#forecast-content').innerHTML = `<div class="surface forecast-panel"><div class="section-head"><h2>Milestones under pressure</h2><small>Overdue or behind expected progress within 14 days</small></div><div class="forecast-grid">${items.length ? items.map(item=>`<div class="forecast-item"><strong>${esc(item.title)}</strong><p>${esc(item.project)} · ${fmtDate(item.due_date)}</p><span class="status-badge ${item.classification === 'overdue' ? 'critical' : 'at-risk'}">${esc(item.classification)}</span> <button class="button button-ghost" data-project="${item.project_id}">Review →</button></div>`).join('') : '<p class="form-intro">No milestones currently under pressure.</p>'}</div></div>`;
}
function renderBriefing() {
  const brief = state.briefing, data = brief.summary;
  $('#briefing-content').className = '';
  $('#briefing-content').innerHTML = `<div class="brief-cover"><h2>Weekly executive brief</h2><p>Portfolio position · ${fmtDate(brief.as_of)} · Synthetic demonstration data</p><div class="brief-summary"><div><strong>${data.total}</strong><span>Active initiatives</span></div><div><strong>${data.on_track}</strong><span>On track</span></div><div><strong>${data.at_risk}</strong><span>At risk</span></div><div><strong>${data.critical}</strong><span>Critical</span></div></div></div><div class="brief-body"><div class="surface brief-section"><h2>Key developments</h2>${brief.developments.length ? brief.developments.map(d=>`<div class="development"><strong>${esc(d.project)}</strong><p>${esc(d.text)}</p><button class="button button-ghost" data-project="${d.project_id}">View source signal →</button></div>`).join('') : '<p>No material risk developments this week.</p>'}<h2 style="margin-top:28px">Recommended actions</h2><ul class="brief-actions">${brief.recommendations.map(r=>`<li><strong>${esc(r.project)}</strong>${esc(r.action)}</li>`).join('') || '<li>Continue monitoring delivery against the next checkpoints.</li>'}</ul></div><div class="surface brief-section"><h2>Management attention</h2>${brief.attention.length ? brief.attention.map(p=>`<div class="attention-item"><button class="project-cell" data-project="${p.id}">${esc(p.name)}</button>${badge(p.risk.status)}</div>`).join('') : '<p>No escalations are required.</p>'}<div class="source-list"><h3>How this brief is built</h3><p class="form-intro">Counts, findings, and actions are derived from milestone, blocker, KPI, dependency, budget, and note data. Risk scores do not come from the language model.</p></div></div></div>`;
}
async function refresh() {
  [state.portfolio,state.briefing,state.forecast] = await Promise.all([api('/portfolio'),api('/briefing'),api('/milestones/forecast')]);
  renderOverview(); renderPortfolio(); renderBriefing(); renderForecast();
  $('#ask-project').innerHTML = '<option value="">Entire portfolio</option>' + state.portfolio.projects.map(p=>`<option value="${p.id}">${esc(p.name)}</option>`).join('');
}
function detailSection(title, body) { return `<section class="detail-section"><h3>${title}</h3>${body}</section>`; }
function renderDrawer(project) {
  const risk = project.risk;
  const rows = (items, mapping, empty) => items.length ? `<div class="detail-list">${items.map(mapping).join('')}</div>` : `<p class="form-intro">${empty}</p>`;
  $('#drawer-content').innerHTML = `<div class="drawer-head"><div class="client">${esc(project.client)} · ${esc(project.owner)}</div><h2>${esc(project.name)}</h2><p>${esc(project.description)}</p><button class="icon-button close-drawer" id="close-drawer" aria-label="Close details">×</button></div><div class="drawer-body"><div class="risk-panel"><div class="risk-number">${risk.score}<small>/100</small></div><div>${badge(risk.status)}<p>Calculated from ${risk.evidence.length} evidence signal${risk.evidence.length === 1 ? '' : 's'}.</p></div></div>
  ${detailSection('Project profile',`<div class="detail-list"><div class="detail-row"><strong>Target date</strong><span>${fmtDate(project.target_date)}</span></div><div class="detail-row"><strong>Budget</strong><span>${money(project.budget,project.currency)}</span></div><div class="detail-row"><strong>Spend</strong><span>${money(project.spend,project.currency)}</span></div><div class="detail-row"><strong>Teams</strong><span>${esc(project.teams.join(', ') || 'Not set')}</span></div><div class="detail-row"><strong>Systems</strong><span>${esc(project.systems.join(', ') || 'Not set')}</span></div><div class="detail-row"><strong>Workflows</strong><span>${esc(project.workflows.join(', ') || 'Not set')}</span></div></div><form id="finance-form" class="signal-form"><div class="form-grid"><label>Budget<input name="budget" type="number" min="0" step="any" value="${project.budget}" required></label><label>Spend to date<input name="spend" type="number" min="0" step="any" value="${project.spend}" required></label></div><button class="button button-secondary" type="submit">Update financials</button></form>`)}
  ${detailSection('Score breakdown',`<div class="detail-list">${Object.entries(risk.contributions).filter(([,points])=>points>0).map(([name,points])=>`<div class="detail-row"><strong>${name === 'kpis' ? 'KPIs' : esc(name[0].toUpperCase()+name.slice(1))}</strong><span>+${points} points</span></div>`).join('') || '<p class="form-intro">No current contributions.</p>'}</div><p class="form-intro">Each category is capped before the total is calculated.</p>`)}
  ${detailSection('Risk evidence',risk.evidence.length ? risk.evidence.map(e=>`<div class="evidence-item"><span class="points">+${e.points} pts</span><strong>${esc(e.label)}</strong><p>${esc(e.detail)} · ${esc(e.type)} #${e.id}</p></div>`).join('') : '<p class="form-intro">No active risk signals.</p>')}
  ${detailSection('Recommended actions',risk.actions.map(a=>`<p class="action-item">${esc(a)}</p>`).join(''))}
  ${detailSection('Milestones',rows(project.milestones,m=>`<div class="detail-row"><strong>${esc(m.title)}</strong><span>${fmtDate(m.due_date)} · ${m.progress}% · ${esc(m.status)}</span></div>`,'No milestones recorded.'))}
  ${detailSection('KPIs',rows(project.kpis,k=>`<div class="detail-row"><strong>${esc(k.name)}</strong><span>${k.actual}${esc(k.unit)} / ${k.target}${esc(k.unit)} target${k.previous_actual == null ? '' : ` · prior ${k.previous_actual}${esc(k.unit)}`}</span></div>`,'No KPIs recorded.'))}
  ${detailSection('Blockers & dependencies',rows([...project.blockers.map(b=>({...b,kind:'blocker'})),...project.dependencies.map(d=>({...d,kind:'dependency'}))],item=>`<div class="detail-row"><strong>${esc(item.title || item.name)}</strong><span>${item.kind === 'blocker' ? `${esc(item.severity)} · ${item.resolved ? 'resolved' : `<button class="button button-ghost" data-resolve="${item.id}">Resolve</button>`}` : `${item.slipped_count} slips · ${item.resolved ? 'resolved' : 'open'}`}</span></div>`,'No blockers or dependencies recorded.'))}
  ${detailSection('Decisions',project.decisions.length ? project.decisions.map(d=>`<div class="project-note"><strong>${fmtDate(d.decided_at)}</strong><p>${esc(d.summary)}</p></div>`).join('') : '<p class="form-intro">No decisions recorded.</p>')}
  ${detailSection('Source library',project.documents.length ? project.documents.map(d=>`<div class="detail-row"><strong>${esc(d.title)}</strong><span>${esc(d.source_type)} · ${d.chunks} chunk${d.chunks === 1 ? '' : 's'}</span></div>`).join('') : '<p class="form-intro">No documents uploaded.</p>')}
  ${detailSection('Add delivery evidence',`<select class="signal-selector" id="signal-type" aria-label="Evidence type"><option value="milestone">Milestone</option><option value="blocker">Blocker</option><option value="dependency">Dependency</option><option value="kpi">KPI</option><option value="note">Meeting note</option><option value="decision">Decision</option><option value="document">Document text</option><option value="upload">Upload file</option></select><form class="signal-form" id="signal-form"></form>`)}</div>`;
  $('.risk-panel', $('#drawer-content')).insertAdjacentHTML('afterend','<div class="risk-explain"><button class="button button-secondary" data-explain="true">Explain this risk</button><div id="risk-explanation"></div></div>');
  $('#signal-type').value = state.signal;
  renderSignalForm();
}
const input = (label,name,type='text',extra='') => `<label>${label}<input name="${name}" type="${type}" required ${extra}></label>`;
function renderSignalForm() {
  const fields = {
    milestone: `${input('Milestone','title')}${input('Due date','due_date','date')}<div class="form-grid">${input('Progress %','progress','number','min="0" max="100" value="0"')}${input('Expected %','expected_progress','number','min="0" max="100" value="100"')}</div>`,
    blocker: `${input('Blocker','title')}<label>Severity<select name="severity"><option>high</option><option selected>medium</option><option>low</option></select></label>`,
    dependency: `${input('Dependency','name')}<div class="form-grid">${input('Team','team')}${input('System','system')}</div>${input('Times slipped','slipped_count','number','min="0" value="0"')}`,
    kpi: `${input('KPI name','name')}<div class="form-grid">${input('Actual','actual','number','step="any"')}${input('Target','target','number','step="any" min="0.00001"')}</div><div class="form-grid"><label>Previous actual <small>(optional)</small><input name="previous_actual" type="number" step="any"></label>${input('Unit','unit','text','value="%"')}</div><label>Good direction<select name="direction"><option value="higher">Higher</option><option value="lower">Lower</option></select></label>`,
    note: `${input('Meeting title','title')}<label>Notes<textarea name="body" rows="4" required></textarea></label><label>Signal<select name="signal"><option value="">Auto-detect</option><option>negative</option><option>neutral</option><option>positive</option></select></label>`,
    decision: '<label>Decision<textarea name="summary" rows="3" required></textarea></label>',
    document: `${input('Document title','title')}<label>Content<textarea name="content" rows="5" required minlength="10"></textarea></label>`,
    upload: '<label>PDF, TXT, MD, or CSV (max 5 MB)<input name="file" type="file" accept=".pdf,.txt,.md,.csv" required></label>'
  };
  $('#signal-form').innerHTML = fields[state.signal] + `<button class="button button-primary" type="submit">Add ${state.signal === 'upload' ? 'file' : state.signal === 'document' ? 'document' : 'evidence'}</button>`;
}
async function openDrawer(id) {
  try {
    state.project = await api(`/projects/${id}`); state.signal = 'milestone'; renderDrawer(state.project);
    $('#drawer-backdrop').hidden = false; $('#project-drawer').hidden = false;
    $('#close-drawer').focus(); document.body.style.overflow = 'hidden';
  } catch (error) { toast(error.message); }
}
function closeDrawer() { $('#drawer-backdrop').hidden = true; $('#project-drawer').hidden = true; document.body.style.overflow = ''; }
function openModal() { $('#modal-backdrop').hidden = false; $('#project-modal').hidden = false; document.body.style.overflow = 'hidden'; $('#project-form input[name=name]').focus(); }
function closeModal() { $('#modal-backdrop').hidden = true; $('#project-modal').hidden = true; document.body.style.overflow = ''; }
function listValue(value) { return value.split(',').map(x=>x.trim()).filter(Boolean); }

document.addEventListener('click', async event => {
  const nav = event.target.closest('[data-page]'); if (nav) showPage(nav.dataset.page);
  const go = event.target.closest('[data-go]'); if (go) showPage(go.dataset.go);
  const project = event.target.closest('[data-project]'); if (project) openDrawer(project.dataset.project);
  const prompt = event.target.closest('[data-prompt]'); if (prompt) { $('#ask-question').value = prompt.dataset.prompt; $('#ask-question').focus(); }
  const resolve = event.target.closest('[data-resolve]'); if (resolve) {
    try { await api(`/blockers/${resolve.dataset.resolve}/resolve`,{method:'PATCH'}); await refresh(); await openDrawer(state.project.id); toast('Blocker resolved and risk recalculated.'); } catch(error){ toast(error.message); }
  }
  const explain = event.target.closest('[data-explain]'); if (explain && state.project) {
    $('#risk-explanation').innerHTML='<div class="explanation-box">Preparing explanation…</div>';
    try { const result = await api(`/projects/${state.project.id}/explain`,{method:'POST'});
      $('#risk-explanation').innerHTML=`<div class="explanation-box">${esc(result.explanation)}<small>${esc(result.mode)} · score remains ${result.score}/100</small></div>`;
    } catch(error){ $('#risk-explanation').innerHTML=`<p class="error-message">${esc(error.message)}</p>`; }
  }
});
$$('.nav-item').forEach(node => node.querySelector('.nav-icon').innerHTML = icon(node.dataset.page === 'ask' ? 'spark' : node.dataset.page));
$('#new-project').addEventListener('click',openModal);
$('#close-modal').addEventListener('click',closeModal);
$('#cancel-project').addEventListener('click',closeModal);
$('#modal-backdrop').addEventListener('click',closeModal);
$('#drawer-backdrop').addEventListener('click',closeDrawer);
$('#project-drawer').addEventListener('click',event=>{ if (event.target.closest('#close-drawer')) closeDrawer(); });
document.addEventListener('keydown',event=>{ if(event.key === 'Escape'){ if(!$('#project-modal').hidden)closeModal(); else if(!$('#project-drawer').hidden)closeDrawer(); } });
$('#project-search').addEventListener('input',event=>{ state.search = event.target.value.toLowerCase().trim(); renderPortfolio(); });
$$('[data-filter]').forEach(button=>button.addEventListener('click',()=>{ state.filter = button.dataset.filter; $$('[data-filter]').forEach(x=>x.classList.toggle('selected',x===button)); renderPortfolio(); }));
$('#project-form').addEventListener('submit',async event=>{
  event.preventDefault(); const form = new FormData(event.currentTarget);
  const payload = Object.fromEntries(form.entries());
  payload.budget = Number(payload.budget); payload.spend = 0;
  for(const key of ['teams','systems','workflows']) payload[key] = listValue(payload[key] || '');
  try { const result = await api('/projects',{method:'POST',body:JSON.stringify(payload)}); closeModal(); event.currentTarget.reset(); await refresh(); showPage('portfolio'); openDrawer(result.id); toast('Initiative created. Add delivery evidence to calculate its risk.'); } catch(error){ toast(error.message); }
});
$('#project-drawer').addEventListener('change',event=>{ if(event.target.id === 'signal-type'){state.signal=event.target.value;renderSignalForm();} });
$('#project-drawer').addEventListener('submit',async event=>{
  if(event.target.id === 'finance-form') {
    event.preventDefault(); const form=new FormData(event.target), id=state.project.id;
    try { await api(`/projects/${id}`,{method:'PATCH',body:JSON.stringify({budget:Number(form.get('budget')),spend:Number(form.get('spend'))})});
      await refresh(); state.project=await api(`/projects/${id}`); renderDrawer(state.project); toast('Financials updated and risk recalculated.');
    } catch(error){toast(error.message);}
    return;
  }
  if(event.target.id !== 'signal-form') return;
  event.preventDefault(); const form = new FormData(event.target), id = state.project.id;
  try {
    if(state.signal === 'upload') await api(`/projects/${id}/upload`,{method:'POST',body:form});
    else {
      const payload = Object.fromEntries(form.entries());
      for(const key of ['progress','expected_progress','actual','target','slipped_count']) if(key in payload) payload[key]=Number(payload[key]);
      if('previous_actual' in payload) payload.previous_actual = payload.previous_actual === '' ? null : Number(payload.previous_actual);
      if(state.signal === 'note' && !payload.signal) payload.signal=null;
      await api(`/projects/${id}/${state.signal === 'kpi' ? 'kpis' : state.signal === 'dependency' ? 'dependencies' : state.signal === 'document' ? 'documents' : state.signal+'s'}`,{method:'POST',body:JSON.stringify(payload)});
    }
    await refresh(); state.project = await api(`/projects/${id}`); renderDrawer(state.project); toast('Evidence added and risk recalculated.');
  } catch(error){toast(error.message);}
});
$('#ask-form').addEventListener('submit',async event=>{
  event.preventDefault(); const result = $('#ask-result'); result.classList.remove('empty-panel'); result.innerHTML='<p class="form-intro">Searching source documents…</p>';
  try { const data = await api('/ask',{method:'POST',body:JSON.stringify({question:$('#ask-question').value,project_id:Number($('#ask-project').value)||null})});
    result.innerHTML=`<div class="mode-label">${esc(data.mode)}</div><h2>Answer</h2><div class="answer-text">${esc(data.answer)}</div><div class="source-list"><h3>Source evidence</h3>${data.sources.length ? data.sources.map((s,i)=>`<div class="source-item"><strong>[${i+1}] ${esc(s.project)} / ${esc(s.title)}</strong><p>${esc(s.excerpt)}</p></div>`).join('') : '<p class="form-intro">No matching documents.</p>'}</div>`;
  } catch(error){ result.innerHTML=`<p class="error-message">${esc(error.message)}</p>`; }
});
$('#impact-form').addEventListener('submit',async event=>{
  event.preventDefault(); const result=$('#impact-result');result.classList.remove('empty-panel');result.innerHTML='<p class="form-intro">Tracing affected evidence…</p>';
  try {const data=await api('/change-impact',{method:'POST',body:JSON.stringify({announcement:$('#impact-announcement').value})});
    const chips = list => list.length ? `<div class="chips">${list.map(x=>`<span class="chip">${esc(x)}</span>`).join('')}</div>` : '<p class="form-intro">No direct matches.</p>';
    result.innerHTML=`<div class="mode-label">Evidence-matched assessment</div><h2>${data.affected_projects.length} affected initiative${data.affected_projects.length===1?'':'s'}</h2><p class="form-intro">${esc(data.method)}</p><div class="impact-section"><h3>Affected teams</h3>${chips(data.affected_teams)}</div><div class="impact-section"><h3>Affected systems</h3>${chips(data.affected_systems)}</div><div class="impact-section"><h3>Affected workflows</h3>${chips(data.affected_workflows)}</div><div class="impact-section"><h3>Initiatives and matches</h3>${data.affected_projects.length ? data.affected_projects.map(p=>`<div class="impact-project"><button class="project-cell" data-project="${p.project_id}">${esc(p.project)}</button><small>Risk score ${p.risk_score}/100 · Matched ${p.matches.map(m=>esc(m.matched_terms.join(', '))).join('; ')}</small></div>`).join('') : '<p class="form-intro">No direct project or document match.</p>'}</div><div class="impact-section"><h3>High-risk dependencies</h3>${data.high_risk_dependencies.length ? data.high_risk_dependencies.map(d=>`<p class="action-item">${esc(d.name)} · ${esc(d.project)} · ${d.slipped_count} slips</p>`).join('') : '<p class="form-intro">None matched.</p>'}</div><div class="impact-section"><h3>Recommended change plan</h3><ol class="plain-list">${data.recommendations.map(r=>`<li>${esc(r)}</li>`).join('')}</ol></div>`;
    $$('.impact-project small',result).forEach((node,index)=>{
      const project=data.affected_projects[index];
      const fields=[...new Set(project.matches.filter(match=>match.type!=='document').map(match=>match.value))].slice(0,3);
      node.textContent=`Risk score ${project.risk_score}/100 · Matched ${fields.join(', ') || 'source document'}`;
    });
    $$('.impact-section .action-item',result).forEach(node=>{node.textContent=node.textContent.replace('1 slips','1 slip');});
  }catch(error){result.innerHTML=`<p class="error-message">${esc(error.message)}</p>`;}
});
$('#copy-brief').addEventListener('click',async()=>{
  const b=state.briefing,d=b.summary;
  const text=`WEEKLY EXECUTIVE BRIEF · ${fmtDate(b.as_of)}\n\n${d.total} Active Initiatives · ${d.on_track} On Track · ${d.at_risk} At Risk · ${d.critical} Critical\n\nKey Developments\n${b.developments.map(x=>'- '+x.text).join('\n')}\n\nManagement Attention\n${b.attention.map(x=>'- '+x.name+' ('+x.risk.status+')').join('\n')}\n\nRecommended Actions\n${b.recommendations.map(x=>'- '+x.project+': '+x.action).join('\n')}\n\nSynthetic demonstration data. Scores are deterministic.`;
  try{await navigator.clipboard.writeText(text);toast('Briefing copied to clipboard.');}catch{toast('Clipboard unavailable in this browser.');}
});
$('#today').textContent=new Date().toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric',year:'numeric'});
refresh().catch(error=>{toast(error.message);$$('.loading-state').forEach(node=>node.textContent='Could not load portfolio. Refresh the page after checking the API.');});
