/*
 * WIG Scoreboard
 *
 * Reads an Excel workbook and renders it as a scoreboard.
 *
 * Data source: by default the workbook deployed with the site at
 * data/scoreboard.xlsx. To pull from an external location instead
 * (e.g. Azure Blob Storage or a SharePoint direct-download link),
 * set DATA_URL to that URL. The host must allow CORS for this origin.
 *
 * Expected workbook layout:
 *   - Sheet "Scoreboard" (or the first sheet): one row per WIG with columns
 *       WIG | Owner | Metric | Start | Target | Current | Due Date
 *     Extra columns are rendered as-is in the details table.
 *   - Optional sheet "Settings": key/value pairs in columns A/B.
 *       Title    -> page title
 *       Subtitle -> page subtitle
 */

const DATA_URL = 'data/scoreboard.xlsx';

const KNOWN_COLUMNS = ['wig', 'owner', 'metric', 'start', 'target', 'current', 'due date'];

async function loadWorkbook(url) {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Could not fetch ${url} (HTTP ${res.status})`);
  const buf = await res.arrayBuffer();
  return XLSX.read(buf, { type: 'array', cellDates: true });
}

function sheetToRows(workbook, name) {
  const sheet = workbook.Sheets[name];
  if (!sheet) return null;
  return XLSX.utils.sheet_to_json(sheet, { defval: '' });
}

function applySettings(workbook) {
  const sheet = workbook.Sheets['Settings'];
  if (!sheet) return;
  const pairs = XLSX.utils.sheet_to_json(sheet, { header: 1 });
  for (const [key, value] of pairs) {
    if (!key || value === undefined) continue;
    const k = String(key).trim().toLowerCase();
    if (k === 'title') {
      document.getElementById('board-title').textContent = value;
      document.title = value;
    } else if (k === 'subtitle') {
      document.getElementById('board-subtitle').textContent = value;
    }
  }
}

function normalizeKeys(row) {
  const out = {};
  for (const [key, value] of Object.entries(row)) {
    out[key.trim().toLowerCase()] = value;
  }
  return out;
}

function toNumber(value) {
  if (typeof value === 'number') return value;
  const n = parseFloat(String(value).replace(/[%,$\s]/g, ''));
  return Number.isFinite(n) ? n : null;
}

function formatDate(value) {
  if (value instanceof Date) return value.toLocaleDateString();
  return String(value);
}

function progressPct(row) {
  const start = toNumber(row['start']) ?? 0;
  const target = toNumber(row['target']);
  const current = toNumber(row['current']);
  if (target === null || current === null || target === start) return null;
  const pct = ((current - start) / (target - start)) * 100;
  return Math.max(0, Math.min(100, Math.round(pct)));
}

function statusClass(pct) {
  if (pct === null) return 'status-unknown';
  if (pct >= 75) return 'status-green';
  if (pct >= 40) return 'status-yellow';
  return 'status-red';
}

function renderCard(row) {
  const pct = progressPct(row);
  const extras = Object.entries(row).filter(([k]) => !KNOWN_COLUMNS.includes(k));

  const card = document.createElement('article');
  card.className = `wig-card ${statusClass(pct)}`;
  card.innerHTML = `
    <h2 class="wig-name"></h2>
    <p class="wig-metric"></p>
    <div class="progress-track"><div class="progress-fill"></div></div>
    <div class="wig-numbers">
      <span class="current"></span>
      <span class="pct"></span>
      <span class="target"></span>
    </div>
    <dl class="wig-details"></dl>
  `;

  card.querySelector('.wig-name').textContent = row['wig'] || '(unnamed WIG)';
  card.querySelector('.wig-metric').textContent = row['metric'] || '';
  card.querySelector('.progress-fill').style.width = `${pct ?? 0}%`;
  card.querySelector('.current').textContent = row['current'] !== '' ? `Now: ${row['current']}` : '';
  card.querySelector('.pct').textContent = pct !== null ? `${pct}%` : '—';
  card.querySelector('.target').textContent = row['target'] !== '' ? `Goal: ${row['target']}` : '';

  const details = card.querySelector('.wig-details');
  const detailPairs = [
    ['Owner', row['owner']],
    ['Due', row['due date'] !== '' ? formatDate(row['due date']) : ''],
    ...extras.map(([k, v]) => [k.replace(/\b\w/g, c => c.toUpperCase()), v]),
  ];
  for (const [label, value] of detailPairs) {
    if (value === '' || value === undefined) continue;
    const dt = document.createElement('dt');
    dt.textContent = label;
    const dd = document.createElement('dd');
    dd.textContent = value instanceof Date ? formatDate(value) : String(value);
    details.append(dt, dd);
  }
  return card;
}

async function init() {
  const main = document.getElementById('scoreboard');
  document.getElementById('data-source').textContent = DATA_URL;
  try {
    const workbook = await loadWorkbook(DATA_URL);
    applySettings(workbook);

    const sheetName = workbook.SheetNames.includes('Scoreboard')
      ? 'Scoreboard'
      : workbook.SheetNames[0];
    const rows = (sheetToRows(workbook, sheetName) || []).map(normalizeKeys)
      .filter(r => Object.values(r).some(v => v !== ''));

    main.innerHTML = '';
    if (rows.length === 0) {
      main.innerHTML = '<p class="loading">The scoreboard sheet is empty.</p>';
      return;
    }
    for (const row of rows) main.appendChild(renderCard(row));

    document.getElementById('last-updated').textContent =
      `Loaded ${new Date().toLocaleString()}`;
  } catch (err) {
    main.innerHTML = `<p class="error">Failed to load scoreboard: ${err.message}</p>`;
  }
}

init();
