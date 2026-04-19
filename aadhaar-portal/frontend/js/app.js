/**
 * ================================================================
 * Aadhaar Analytics Portal — Application JavaScript
 * All dashboard logic: auth, API, charts, filters, export, demos
 * ================================================================
 */

/* ──────────────────────────────────────────────────────────────
   1. CONFIG & AUTH
   ────────────────────────────────────────────────────────────── */
const API   = 'http://localhost:8000/api';
const token = () => sessionStorage.getItem('token') || '';
const hdrs  = () => ({
  'Authorization': `Bearer ${token()}`,
  'Content-Type': 'application/json',
});

function requireAuth() {
  if (!token()) window.location.href = 'login.html';
}

function logout() {
  sessionStorage.clear();
  window.location.href = 'login.html';
}

/* ──────────────────────────────────────────────────────────────
   2. HELPERS
   ────────────────────────────────────────────────────────────── */
const fmt = n => Number(n).toLocaleString('en-IN');

/** Animated counter for KPI numbers */
function animateCounter(el, target, duration = 800) {
  const start = 0;
  const startTime = performance.now();
  function update(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);          // ease-out cubic
    const current = Math.floor(start + (target - start) * ease);
    el.textContent = fmt(current);
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

/* ──────────────────────────────────────────────────────────────
   3. PAGE NAVIGATION
   ────────────────────────────────────────────────────────────── */
const pageMeta = {
  live:        { title: 'Live Statistics',         crumb: 'Real-time enrolment & update metrics' },
  history:     { title: 'Past History',            crumb: 'Historical trend analysis & comparisons' },
  insights:    { title: 'Insights & Improvement',  crumb: 'Recommendations and biometric quality' },
  anomalies:   { title: 'Anomalies',               crumb: 'Detected irregularities in enrolment data' },
  methodology: { title: 'Methodology',             crumb: 'Framework, architecture & project overview' },
};

let activeCharts = {};

function destroyChart(id) {
  if (activeCharts[id]) {
    activeCharts[id].destroy();
    delete activeCharts[id];
  }
}

function showPage(id) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  const page = document.getElementById(`page-${id}`);
  const nav  = document.getElementById(`nav-${id}`);
  if (page) page.classList.add('active');
  if (nav)  nav.classList.add('active');

  document.getElementById('pageTitle').textContent = pageMeta[id]?.title || '';
  document.getElementById('pageCrumb').textContent = pageMeta[id]?.crumb || '';

  // Load data for the selected page
  if (id === 'live')      loadLiveStats();
  if (id === 'history')   loadHistory();
  if (id === 'insights')  loadInsights();
  if (id === 'anomalies') loadAnomalies();
}

/* ──────────────────────────────────────────────────────────────
   4. FILTERS
   ────────────────────────────────────────────────────────────── */
function initDateRange() {
  const today = new Date();
  const y     = today.getFullYear();
  document.getElementById('endDate').value   = today.toISOString().slice(0, 10);
  document.getElementById('startDate').value = `${y}-01-01`;
}

function applyFilters() {
  const active = document.querySelector('.nav-item.active');
  if (active) showPage(active.id.replace('nav-', ''));
}

function regionParam() {
  const v = document.getElementById('regionFilter').value;
  return v ? `&region_code=${v}` : '';
}

function appendRegion(url) {
  // Append region query param to a URL that may already have query params
  const rp = regionParam();
  if (!rp) return url;
  return url + (url.includes('?') ? rp : '?' + rp.slice(1));
}

async function loadRegions() {
  try {
    const res  = await fetch(`${API}/live/regions`, { headers: hdrs() });
    const data = await res.json();
    const sel  = document.getElementById('regionFilter');
    data.forEach(r => {
      const opt = document.createElement('option');
      opt.value       = r.region_code;
      opt.textContent = `${r.district_name}, ${r.state_name}`;
      sel.appendChild(opt);
    });
  } catch { /* Silently fail — demo mode */ }
}

/* ──────────────────────────────────────────────────────────────
   5. LIVE STATISTICS
   ────────────────────────────────────────────────────────────── */
async function loadLiveStats() {
  try {
    const daysDefault = 30;
    const useAllWhenEmpty = document.getElementById('useAllTime')?.checked;

    const summary = await fetch(appendRegion(`${API}/live/summary`), { headers: hdrs() }).then(r => r.json());

    const [gender, age, status, upd] = await Promise.all([
      fetch(appendRegion(`${API}/live/gender-split?days=${daysDefault}`), { headers: hdrs() }).then(r => r.json()),
      fetch(appendRegion(`${API}/live/age-split?days=${daysDefault}`),    { headers: hdrs() }).then(r => r.json()),
      fetch(appendRegion(`${API}/live/status-breakdown`),               { headers: hdrs() }).then(r => r.json()),
      fetch(appendRegion(`${API}/live/update-types?days=${daysDefault}`),                   { headers: hdrs() }).then(r => r.json()),
    ]);

    // If recent window is empty and user opted in, fetch all-time aggregates
    const recentEmpty = (
      (Array.isArray(gender) && gender.length === 0) ||
      (Array.isArray(age) && age.length === 0) ||
      (summary && summary.enrollments === 0)
    );

    if (recentEmpty && useAllWhenEmpty) {
      const [genderAll, ageAll, updAll] = await Promise.all([
        fetch(appendRegion(`${API}/live/gender-split?days=0`), { headers: hdrs() }).then(r => r.json()),
        fetch(appendRegion(`${API}/live/age-split?days=0`),    { headers: hdrs() }).then(r => r.json()),
        fetch(appendRegion(`${API}/live/update-types?days=0`), { headers: hdrs() }).then(r => r.json()),
      ]);
      renderKPIs(summary);
      renderGenderChart(genderAll);
      renderAgeChart(ageAll);
      renderStatusChart(status);
      renderUpdateTypeChart(updAll);
    } else {
      renderKPIs(summary);
      renderGenderChart(gender);
      renderAgeChart(age);
      renderStatusChart(status);
      renderUpdateTypeChart(upd);
    }
  } catch (e) {
    console.error(e);
    renderDemoData();
  }
}

function renderKPIs(s) {
  const grid = document.getElementById('kpiGrid');
  grid.innerHTML = `
    <div class="kpi-card blue" id="kpi-enrollments">
      <div class="kpi-label">Enrollments Today</div>
      <div class="kpi-value" data-target="${s.enrollments}">0</div>
      <span class="kpi-icon">📋</span>
      <div class="kpi-delta up">
        <span class="refresh-dot"></span> Live
      </div>
    </div>
    <div class="kpi-card orange" id="kpi-updates">
      <div class="kpi-label">Updates Today</div>
      <div class="kpi-value" data-target="${s.updates}">0</div>
      <span class="kpi-icon">✏️</span>
      <div class="kpi-delta up">
        <span class="refresh-dot"></span> Live
      </div>
    </div>
    <div class="kpi-card green" id="kpi-generated">
      <div class="kpi-label">Aadhaar Generated</div>
      <div class="kpi-value" data-target="${s.generated}">0</div>
      <span class="kpi-icon">🪪</span>
      <div class="kpi-delta up">↑ Today</div>
    </div>
    <div class="kpi-card amber" id="kpi-pending">
      <div class="kpi-label">Pending</div>
      <div class="kpi-value" data-target="${s.pending}">0</div>
      <span class="kpi-icon">⏳</span>
      <div class="kpi-delta">Awaiting verification</div>
    </div>
    <div class="kpi-card red" id="kpi-rejected">
      <div class="kpi-label">Rejected</div>
      <div class="kpi-value" data-target="${s.rejected}">0</div>
      <span class="kpi-icon">❌</span>
      <div class="kpi-delta down">Needs review</div>
    </div>`;

  // Animate counters
  grid.querySelectorAll('.kpi-value[data-target]').forEach(el => {
    animateCounter(el, parseInt(el.dataset.target));
  });
}

/* ──────────────────────────────────────────────────────────────
   6. CHART RENDERING
   ────────────────────────────────────────────────────────────── */

/* Consistent chart colour palette — enrolments=blue, updates=orange, generated=green */
const CHART_COLORS = {
  enrolment:  '#1e4d8c',
  update:     '#e8720c',
  generated:  '#138843',
  rejected:   '#c42b2b',
  pending:    '#f59e0b',
  male:       '#1e4d8c',
  female:     '#e8720c',
  other:      '#138843',
};

const PALETTE = ['#1e4d8c','#e8720c','#138843','#c42b2b','#f59e0b','#6d28d9','#4a90d9','#0f2140'];

const CHART_DEFAULTS = {
  font: { family: "'Inter', sans-serif" },
  color: '#6b7a90',
};

function chartBaseOpts(extra = {}) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { font: { family: "'Inter', sans-serif", size: 12 }, usePointStyle: true, padding: 16 },
      },
    },
    ...extra,
  };
}

/* Gender Doughnut */
function renderGenderChart(data) {
  destroyChart('gender');
  const ctx = document.getElementById('genderChart').getContext('2d');
  const genderColors = data.map(d => CHART_COLORS[d.gender.toLowerCase()] || PALETTE[0]);
  activeCharts['gender'] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: data.map(d => d.gender),
      datasets: [{
        data: data.map(d => d.count),
        backgroundColor: genderColors,
        borderWidth: 0,
        hoverOffset: 8,
      }],
    },
    options: {
      ...chartBaseOpts(),
      cutout: '65%',
      plugins: {
        legend: { position: 'bottom', labels: { font: CHART_DEFAULTS.font, usePointStyle: true, padding: 16 } },
      },
    },
  });
}

/* Age Group Bar */
function renderAgeChart(data) {
  destroyChart('age');
  const ctx = document.getElementById('ageChart').getContext('2d');
  activeCharts['age'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.map(d => d.age_group),
      datasets: [{
        label: 'Enrollments',
        data:  data.map(d => d.count),
        backgroundColor: CHART_COLORS.enrolment,
        borderRadius: 6,
        maxBarThickness: 48,
      }],
    },
    options: {
      ...chartBaseOpts(),
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,.04)' }, ticks: { font: CHART_DEFAULTS.font } },
        x: { grid: { display: false }, ticks: { font: CHART_DEFAULTS.font } },
      },
    },
  });
}

/* Enrollment Status Doughnut */
function renderStatusChart(data) {
  destroyChart('status');
  const ctx  = document.getElementById('statusChart').getContext('2d');
  const clrs = {
    Pending:   CHART_COLORS.pending,
    Verified:  CHART_COLORS.generated,
    Rejected:  CHART_COLORS.rejected,
    Generated: CHART_COLORS.enrolment,
  };
  activeCharts['status'] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: data.map(d => d.status),
      datasets: [{
        data: data.map(d => d.count),
        backgroundColor: data.map(d => clrs[d.status] || '#999'),
        borderWidth: 0,
      }],
    },
    options: {
      ...chartBaseOpts(),
      cutout: '60%',
      plugins: {
        legend: { position: 'bottom', labels: { font: CHART_DEFAULTS.font, usePointStyle: true, padding: 16 } },
      },
    },
  });
}

/* Update Types Bar */
function renderUpdateTypeChart(data) {
  destroyChart('updateType');
  const ctx = document.getElementById('updateChart').getContext('2d');
  activeCharts['updateType'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.map(d => d.type),
      datasets: [{
        label: 'Requests',
        data:  data.map(d => d.count),
        backgroundColor: CHART_COLORS.update,
        borderRadius: 6,
        maxBarThickness: 48,
      }],
    },
    options: {
      ...chartBaseOpts(),
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,.04)' }, ticks: { font: CHART_DEFAULTS.font } },
        x: { grid: { display: false }, ticks: { font: CHART_DEFAULTS.font } },
      },
    },
  });
}

/* ──────────────────────────────────────────────────────────────
   7. PAST HISTORY
   ────────────────────────────────────────────────────────────── */
async function loadHistory() {
  await Promise.all([loadMonthlyTrend(), loadRegionalComparison(), loadYoY()]);
}

async function initHistoryYears() {
  try {
    const data = await fetch(`${API}/history/yearly-growth`, { headers: hdrs() }).then(r => r.json());
    const sel = document.getElementById('yearSelect');
    if (!sel) return;
    sel.innerHTML = '';
    if (!Array.isArray(data) || data.length === 0) {
      const y = new Date().getFullYear();
      sel.innerHTML = `<option>${y}</option>`;
      return;
    }
    // Populate years (ascending) and select the latest
    data.sort((a, b) => a.year - b.year);
    data.forEach(d => {
      const opt = document.createElement('option');
      opt.value = d.year;
      opt.textContent = d.year;
      sel.appendChild(opt);
    });
    sel.value = data[data.length - 1].year;
  } catch (e) {
    // fallback: leave hard-coded values
  }
}

async function loadMonthlyTrend() {
  const year = document.getElementById('yearSelect').value;
  document.getElementById('histYear').textContent = `Year ${year}`;
  try {
    const data = await fetch(`${API}/history/monthly-trend?year=${year}${regionParam()}`, { headers: hdrs() }).then(r => r.json());
    renderMonthlyChart(data);
  } catch { renderDemoMonthly(); }
}

function renderMonthlyChart(data) {
  destroyChart('monthly');
  const ctx    = document.getElementById('monthlyChart').getContext('2d');
  const labels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const arr    = field => labels.map((_, i) => {
    const row = data.find(d => d.month === i + 1);
    return row ? row[field] : 0;
  });
  activeCharts['monthly'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Enrollments',
          data: arr('enrollments'),
          backgroundColor: CHART_COLORS.enrolment,
          borderRadius: 5,
          stack: 'a',
          maxBarThickness: 32,
        },
        {
          label: 'Updates',
          data: arr('updates'),
          backgroundColor: CHART_COLORS.update,
          borderRadius: 5,
          stack: 'b',
          maxBarThickness: 32,
        },
        {
          label: 'Generated',
          data: arr('generated'),
          type: 'line',
          borderColor: CHART_COLORS.generated,
          backgroundColor: 'transparent',
          pointBackgroundColor: CHART_COLORS.generated,
          tension: .4,
          borderWidth: 2,
          pointRadius: 3,
        },
      ],
    },
    options: {
      ...chartBaseOpts(),
      interaction: { mode: 'index' },
      plugins: { legend: { position: 'top', labels: { font: CHART_DEFAULTS.font, usePointStyle: true, padding: 14 } } },
      scales: {
        y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,.04)' }, ticks: { font: CHART_DEFAULTS.font } },
        x: { grid: { display: false }, ticks: { font: CHART_DEFAULTS.font } },
      },
    },
  });
}

async function loadYoY() {
  try {
    const data = await fetch(`${API}/history/yearly-growth`, { headers: hdrs() }).then(r => r.json());
    renderYoYChart(data);
  } catch { renderDemoYoY(); }
}

function renderYoYChart(data) {
  destroyChart('yoy');
  const ctx = document.getElementById('yoyChart').getContext('2d');
  activeCharts['yoy'] = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.map(d => d.year),
      datasets: [
        {
          label: 'Enrollments',
          data: data.map(d => d.enrollments),
          borderColor: CHART_COLORS.enrolment,
          backgroundColor: 'rgba(30,77,140,.08)',
          fill: true,
          tension: .4,
          borderWidth: 2,
          pointRadius: 4,
        },
        {
          label: 'Generated',
          data: data.map(d => d.generated),
          borderColor: CHART_COLORS.generated,
          backgroundColor: 'rgba(19,136,67,.06)',
          fill: true,
          tension: .4,
          borderWidth: 2,
          pointRadius: 4,
        },
      ],
    },
    options: {
      ...chartBaseOpts(),
      plugins: { legend: { position: 'top', labels: { font: CHART_DEFAULTS.font, usePointStyle: true, padding: 14 } } },
      scales: {
        y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,.04)' }, ticks: { font: CHART_DEFAULTS.font } },
        x: { grid: { display: false }, ticks: { font: CHART_DEFAULTS.font } },
      },
    },
  });
}

async function loadRegionalComparison() {
  const start = document.getElementById('startDate').value;
  const end   = document.getElementById('endDate').value;
  document.getElementById('rangeLabel').textContent = `${start} → ${end}`;
  try {
    const data = await fetch(`${API}/history/regional-comparison?start_date=${start}&end_date=${end}`, { headers: hdrs() }).then(r => r.json());
    renderRegionalTable(data);
  } catch { renderDemoRegional(); }
}

function renderRegionalTable(data) {
  const tbody = document.getElementById('regionalTbody');
  if (!data.length) {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:2rem;color:var(--text-secondary)">No data for this range.</td></tr>';
    return;
  }
  tbody.innerHTML = data.map((r, i) => `
    <tr>
      <td>${r.state}</td>
      <td>${r.district}</td>
      <td><strong>${fmt(r.enrollments)}</strong></td>
      <td>${fmt(r.updates)}</td>
      <td><span class="pill ${i < 3 ? 'green' : i < 7 ? 'orange' : 'gray'}">${i < 3 ? '↑ High' : i < 7 ? '→ Mid' : '↓ Low'}</span></td>
    </tr>`).join('');
}

/* ──────────────────────────────────────────────────────────────
   8. INSIGHTS
   ────────────────────────────────────────────────────────────── */
async function loadInsights() {
  try {
    const [ins, bio] = await Promise.all([
      fetch(`${API}/insights/recommendations`,  { headers: hdrs() }).then(r => r.json()),
      fetch(`${API}/insights/biometric-quality`, { headers: hdrs() }).then(r => r.json()),
    ]);
    renderInsights(ins.insights);
    renderQuality(bio);
    await loadUpdateHistoryChart();
  } catch { renderDemoInsights(); }
}

function renderInsights(list) {
  const icons = { High: '🔴', Medium: '🟠', Low: '🟢', Critical: '🟣' };
  document.getElementById('insightList').innerHTML = list.map(i => `
    <div class="insight-card">
      <div class="insight-icon ${i.severity.toLowerCase()}">${icons[i.severity] || '💡'}</div>
      <div class="insight-body">
        <div class="insight-category">${i.category}</div>
        <div class="insight-message">${i.message}</div>
      </div>
      <div class="insight-severity-badge">
        <span class="pill ${i.severity === 'High' || i.severity === 'Critical' ? 'red' : i.severity === 'Medium' ? 'orange' : 'green'}">${i.severity}</span>
      </div>
    </div>`).join('');
}

function renderQuality(bio) {
  const scores = [
    { label: 'Fingerprint Quality', val: bio.avg_fingerprint, color: CHART_COLORS.enrolment },
    { label: 'Iris Quality',        val: bio.avg_iris,        color: CHART_COLORS.update },
    { label: 'Photo Quality',       val: bio.avg_photo,       color: CHART_COLORS.generated },
  ];
  document.getElementById('qualityGrid').innerHTML = scores.map(s => `
    <div class="quality-card">
      <div class="quality-label">${s.label}</div>
      <div class="quality-score" style="color:${s.color}">${s.val}%</div>
      <div class="quality-bar-track">
        <div class="quality-bar-fill" style="width:${s.val}%;background:${s.color}"></div>
      </div>
    </div>`).join('');
}

async function loadUpdateHistoryChart() {
  const start = document.getElementById('startDate').value;
  const end   = document.getElementById('endDate').value;
  try {
    const data     = await fetch(`${API}/history/update-history?start_date=${start}&end_date=${end}`, { headers: hdrs() }).then(r => r.json());
    const types    = [...new Set(data.map(d => d.type))];
    const statuses = [...new Set(data.map(d => d.status))];
    destroyChart('updateHistory');
    const ctx    = document.getElementById('updateHistoryChart').getContext('2d');
    const colors = { Pending: CHART_COLORS.pending, Approved: CHART_COLORS.generated, Rejected: CHART_COLORS.rejected };
    activeCharts['updateHistory'] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: types,
        datasets: statuses.map((s, i) => ({
          label: s,
          data: types.map(t => {
            const row = data.find(d => d.type === t && d.status === s);
            return row ? row.count : 0;
          }),
          backgroundColor: colors[s] || PALETTE[i],
          borderRadius: 5,
          stack: 'a',
          maxBarThickness: 36,
        })),
      },
      options: {
        ...chartBaseOpts(),
        interaction: { mode: 'index' },
        plugins: { legend: { position: 'top', labels: { font: CHART_DEFAULTS.font, usePointStyle: true, padding: 14 } } },
        scales: {
          y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,.04)' }, ticks: { font: CHART_DEFAULTS.font } },
          x: { grid: { display: false }, ticks: { font: CHART_DEFAULTS.font } },
        },
      },
    });
  } catch { /* fail silently */ }
}

/* ──────────────────────────────────────────────────────────────
   9. ANOMALIES
   ────────────────────────────────────────────────────────────── */
async function loadAnomalies() {
  const sev = document.getElementById('severityFilter').value;
  try {
    const data = await fetch(`${API}/anomalies/list?resolved=false${sev ? '&severity=' + sev : ''}`, { headers: hdrs() }).then(r => r.json());
    renderAnomalyTable(data);
    document.getElementById('anomalyBadge').textContent = data.length;
    document.getElementById('totalAnomaly').textContent  = data.length;
    document.getElementById('critCount').textContent     = data.filter(d => d.severity === 'Critical').length;
    document.getElementById('highCount').textContent     = data.filter(d => d.severity === 'High').length;
  } catch { renderDemoAnomalies(); }
}

function renderAnomalyTable(data) {
  const tbody = document.getElementById('anomalyTbody');
  if (!data.length) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:2rem;color:var(--text-secondary)">No anomalies found.</td></tr>';
    return;
  }
  tbody.innerHTML = data.map(a => `
    <tr>
      <td>#${a.anomaly_id}</td>
      <td>${a.anomaly_type}</td>
      <td><span class="pill severity-${a.severity.toLowerCase()}">${a.severity}</span></td>
      <td>${a.region_code || '—'}</td>
      <td>${a.detected_on}</td>
      <td style="max-width:260px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${a.description || '—'}</td>
      <td><span class="pill ${a.resolved ? 'green' : 'red'}">${a.resolved ? 'Resolved' : 'Open'}</span></td>
    </tr>`).join('');
}

/* ──────────────────────────────────────────────────────────────
   10. CSV & PDF EXPORT
   ────────────────────────────────────────────────────────────── */
function exportCSV() {
  const activePage = document.querySelector('.page.active');
  const tbl = activePage ? activePage.querySelector('.tbl') : document.querySelector('.tbl');
  if (!tbl) return;

  const rows = [...tbl.querySelectorAll('tr')].map(tr =>
    [...tr.querySelectorAll('th,td')].map(td => `"${td.textContent.trim()}"`).join(',')
  );
  const blob = new Blob([rows.join('\n')], { type: 'text/csv' });
  const a    = document.createElement('a');
  a.href     = URL.createObjectURL(blob);
  a.download = `aadhaar-export-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
}

function exportPDF() {
  // Use browser print as a PDF-generation fallback
  window.print();
}

/* ──────────────────────────────────────────────────────────────
   11. DEMO DATA (fallbacks when backend is offline)
   ────────────────────────────────────────────────────────────── */
function renderDemoData() {
  renderKPIs({ enrollments: 12847, updates: 4231, generated: 11023, pending: 1824, rejected: 312 });
  renderGenderChart([
    { gender: 'Male',   count: 52310 },
    { gender: 'Female', count: 48760 },
    { gender: 'Other',  count: 930 },
  ]);
  renderAgeChart([
    { age_group: '0-18',  count: 18200 },
    { age_group: '19-35', count: 42100 },
    { age_group: '36-60', count: 31500 },
    { age_group: '60+',   count: 9200 },
  ]);
  renderStatusChart([
    { status: 'Generated', count: 98200 },
    { status: 'Verified',  count: 12300 },
    { status: 'Pending',   count: 5400 },
    { status: 'Rejected',  count: 2100 },
  ]);
  renderUpdateTypeChart([
    { type: 'Address',   count: 4200 },
    { type: 'Mobile',    count: 3100 },
    { type: 'Name',      count: 1800 },
    { type: 'Photo',     count: 1200 },
    { type: 'Biometric', count: 900 },
    { type: 'Email',     count: 600 },
    { type: 'DOB',       count: 300 },
  ]);
}

function renderDemoMonthly() {
  renderMonthlyChart([
    { month: 1,  enrollments: 8200,  updates: 2800, generated: 7500 },
    { month: 2,  enrollments: 7900,  updates: 2600, generated: 7200 },
    { month: 3,  enrollments: 9100,  updates: 3100, generated: 8400 },
    { month: 4,  enrollments: 10200, updates: 3400, generated: 9500 },
    { month: 5,  enrollments: 11000, updates: 3700, generated: 10100 },
    { month: 6,  enrollments: 12400, updates: 4100, generated: 11400 },
    { month: 7,  enrollments: 11800, updates: 3900, generated: 10900 },
    { month: 8,  enrollments: 13200, updates: 4400, generated: 12100 },
    { month: 9,  enrollments: 12700, updates: 4200, generated: 11700 },
    { month: 10, enrollments: 14100, updates: 4700, generated: 12900 },
    { month: 11, enrollments: 13500, updates: 4500, generated: 12400 },
    { month: 12, enrollments: 15000, updates: 5000, generated: 13800 },
  ]);
}

function renderDemoYoY() {
  renderYoYChart([
    { year: 2019, enrollments: 820000,  generated: 780000 },
    { year: 2020, enrollments: 950000,  generated: 910000 },
    { year: 2021, enrollments: 1100000, generated: 1060000 },
    { year: 2022, enrollments: 1280000, generated: 1230000 },
    { year: 2023, enrollments: 1400000, generated: 1350000 },
    { year: 2024, enrollments: 1420000, generated: 1380000 },
  ]);
}

function renderDemoRegional() {
  renderRegionalTable([
    { state: 'Maharashtra',   district: 'Mumbai',     enrollments: 284000, updates: 95000 },
    { state: 'Karnataka',     district: 'Bengaluru',  enrollments: 241000, updates: 82000 },
    { state: 'Tamil Nadu',    district: 'Chennai',    enrollments: 218000, updates: 74000 },
    { state: 'Maharashtra',   district: 'Pune',       enrollments: 196000, updates: 68000 },
    { state: 'Uttar Pradesh', district: 'Lucknow',    enrollments: 178000, updates: 61000 },
    { state: 'Delhi',         district: 'New Delhi',  enrollments: 165000, updates: 57000 },
    { state: 'Tamil Nadu',    district: 'Coimbatore', enrollments: 142000, updates: 49000 },
    { state: 'Karnataka',     district: 'Mysuru',     enrollments: 128000, updates: 44000 },
    { state: 'Maharashtra',   district: 'Nashik',     enrollments: 114000, updates: 39000 },
    { state: 'Uttar Pradesh', district: 'Agra',       enrollments: 98000,  updates: 34000 },
  ]);
}

function renderDemoInsights() {
  renderInsights([
    { category: 'Biometric Quality', severity: 'High',   message: '142 records have fingerprint quality below 60%. Recommend calibrating biometric scanners and retraining operators.' },
    { category: 'Rejection Rate',    severity: 'High',   message: 'Rejection rate in last 30 days is 12.4%. Review document validation rules and operator training.' },
    { category: 'Coverage Gap',      severity: 'Medium', message: 'No activity recorded in last 7 days for Agra (Uttar Pradesh). Consider deploying mobile enrollment camps.' },
    { category: 'Processing Backlog',severity: 'Medium', message: '328 enrollments pending for >3 days. Increase verification staff or automate document checks.' },
  ]);
  renderQuality({ avg_fingerprint: 73.4, avg_iris: 81.2, avg_photo: 88.6 });
}

function renderDemoAnomalies() {
  const demo = [
    { anomaly_id: 1, anomaly_type: 'Surge',     severity: 'Critical', region_code: 'MH-MUM', detected_on: '2024-11-14', description: 'Enrollment count 3× daily average — possible camp drive', resolved: false },
    { anomaly_id: 2, anomaly_type: 'Quality',    severity: 'High',     region_code: 'UP-AGR', detected_on: '2024-11-12', description: 'Avg fingerprint quality dropped below 50 for 3 consecutive days', resolved: false },
    { anomaly_id: 3, anomaly_type: 'Duplicate',  severity: 'High',     region_code: 'KA-BLR', detected_on: '2024-11-10', description: '18 potential duplicate demographic records detected', resolved: false },
    { anomaly_id: 4, anomaly_type: 'Drop',       severity: 'Medium',   region_code: 'TN-CBE', detected_on: '2024-11-09', description: 'Enrollments dropped 80% vs 7-day average', resolved: false },
    { anomaly_id: 5, anomaly_type: 'Mismatch',   severity: 'Low',      region_code: 'MH-PUN', detected_on: '2024-11-08', description: 'DOB mismatch between demographic and document scan in 6 records', resolved: true },
  ];
  renderAnomalyTable(demo);
  document.getElementById('anomalyBadge').textContent = 4;
  document.getElementById('totalAnomaly').textContent  = 4;
  document.getElementById('critCount').textContent     = 1;
  document.getElementById('highCount').textContent     = 2;
}

/* ──────────────────────────────────────────────────────────────
   12. INITIALIZATION
   ────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  // Restore user info from session
  const name = sessionStorage.getItem('fullName') || 'Admin';
  const role = sessionStorage.getItem('role')     || 'Analyst';
  const userNameEl   = document.getElementById('userName');
  const userRoleEl   = document.getElementById('userRole');
  const userAvatarEl = document.getElementById('userAvatar');
  if (userNameEl)   userNameEl.textContent   = name;
  if (userRoleEl)   userRoleEl.textContent   = role;
  if (userAvatarEl) userAvatarEl.textContent = name[0].toUpperCase();

  // Init date range
  initDateRange();

  // Load regions into filter dropdown
  loadRegions();

  // Populate history years based on available data
  initHistoryYears();

  // Load default page
  loadLiveStats();

  // Auto-refresh live stats every 60s
  setInterval(() => {
    const livePage = document.getElementById('page-live');
    if (livePage && livePage.classList.contains('active')) loadLiveStats();
  }, 60000);
});
