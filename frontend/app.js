const API = 'http://127.0.0.1:8000';

// ── Auto-resize inquiry textarea to fit content ──
const inquiryEl = document.getElementById('inquiryInput');
if (inquiryEl) {
  const autoResizeInquiry = () => {
    inquiryEl.style.height = 'auto';
    inquiryEl.style.height = inquiryEl.scrollHeight + 'px';
  };
  ['input', 'change'].forEach(ev =>
    inquiryEl.addEventListener(ev, autoResizeInquiry)
  );
  // Ensure correct size on initial load if there's prefilled text
  autoResizeInquiry();
}

// ── Icons ──
const SVG = {
  copy: `<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="7" y="7" width="10" height="10" rx="2"/><path d="M4 13V5a2 2 0 012-2h8"/></svg>`,
  check: `<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 10l4 4 8-8"/></svg>`,
  upload: `<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 3v10M6 9l4 4 4-4"/><path d="M3 15v1a2 2 0 002 2h10a2 2 0 002-2v-1"/></svg>`,
  home: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9.5L12 3l9 6.5V20a1 1 0 01-1 1H4a1 1 0 01-1-1V9.5z"/><path d="M9 21V12h6v9"/></svg>`,
};

// ── Toast ──
let toastTimer;
function showToast(msg, type = '') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast show ' + type;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.className = 'toast'; }, 2800);
}

// ── Copy helper ──
function copyText(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.innerHTML;
    btn.innerHTML = SVG.check;
    btn.style.color = 'var(--green)';
    btn.style.borderColor = 'var(--green)';
    setTimeout(() => {
      btn.innerHTML = orig;
      btn.style.color = '';
      btn.style.borderColor = '';
    }, 1500);
  });
}

// ── Apply highlights to message text ──
function applyHighlights(text, ranges) {
  if (!ranges || ranges.length === 0) return escapeHtml(text);

  // Merge overlapping ranges
  const sorted = [...ranges].sort((a, b) => a.start - b.start);
  const merged = [];
  for (const r of sorted) {
    if (merged.length && r.start <= merged[merged.length-1].end) {
      merged[merged.length-1].end = Math.max(merged[merged.length-1].end, r.end);
    } else {
      merged.push({...r});
    }
  }

  let result = '';
  let cursor = 0;
  for (const r of merged) {
    if (r.start > cursor) result += escapeHtml(text.slice(cursor, r.start));
    result += `<mark class="highlight">${escapeHtml(text.slice(r.start, r.end))}</mark>`;
    cursor = r.end;
  }
  result += escapeHtml(text.slice(cursor));
  return result;
}

function escapeHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function formatValue(v) {
  if (v === null || v === undefined || v === '') return '—';
  return String(v);
}

function getOrganizedDetailsRows(listing) {
  return [
    { label: 'Price', value: listing.price ? `${listing.price} ${listing.currency || ''}`.trim() : '—' },
    { label: 'Beds', value: formatValue(listing.bedrooms) },
    { label: 'City', value: formatValue(listing.city) },
    { label: 'Deal', value: formatValue(listing.transaction_type) },
    { label: 'Type', value: formatValue(listing.property_type) },
    // { 
    //   label: 'District', 
    //   value: (listing.district !== undefined && listing.district !== null && listing.district !== '') 
    //     ? formatValue(listing.district) 
    //     : '—' 
    // },
  

    
    
    ...(listing.district !== undefined && listing.district !== null && listing.district !== ''
      ? [{ label: 'District', value: formatValue(listing.district) }]
      : []
    ),
    ...(listing.compound_name !== undefined && listing.compound_name !== null && listing.compound_name !== ''&& listing.compound_name !=listing.district
      ? [{ label: 'Compund', value: formatValue(listing.compound_name) }]
      : []
    ),

  ];
}

function buildOrganizedDetailsTable(rows) {
  return rows.map(r => `
    <div class="details-row">
      <div class="details-key">${escapeHtml(r.label)}</div>
      <div class="details-val">${escapeHtml(r.value)}</div>
    </div>
  `).join('');
}

function buildOrganizedDetailsText(rows) {
  return rows.map(r => `${r.label}: ${r.value}`).join('\n');
}


// ── Progress polling ──
let progressPollTimer = null;

async function pollProgress(onDone) {
  const bar = document.getElementById('progressBar');
  const label = document.getElementById('progressLabel');
  const stage = document.getElementById('uploadStage');

  const tick = async () => {
    try {
      const res = await fetch(API + '/progress');
      const data = await res.json();
      const { current, total, message } = data;
      
      if (total > 0) {
        stage.textContent = 'Extracting listings…';
        const pct = Math.round((current / total) * 100);
        bar.style.width = pct + '%';
        label.textContent = `Batch ${current} of ${total} — ${pct}%`;

        if (data.done) {
          bar.style.width = '100%';
          label.textContent = 'Done!';
          clearInterval(progressPollTimer);
          progressPollTimer = null;
          setTimeout(onDone, 600);
          return;
      }
      } else {
        stage.textContent = message || 'Uploading…';
        bar.style.width = '1%';
        label.textContent = 'Waiting for pipeline…';
      }
    } catch {
      // backend not responding yet — keep waiting
    }
  };

  await tick();
  progressPollTimer = setInterval(tick, 800);
}

function resetProgressUI() {
  document.getElementById('progressBar').style.width = '0%';
  document.getElementById('progressLabel').textContent = 'Starting…';
  document.getElementById('uploadStage').textContent = 'Uploading…';
}

// ── Render cards ──
function renderCards(listings) {
  const grid = document.getElementById('cardsGrid');
  const count = document.getElementById('resultsCount');

  if (!listings.length) {
    count.innerHTML = '';
    grid.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1">
        <div class="empty-icon">${SVG.home}</div>
        <div class="empty-title">No listings found</div>
        <div class="empty-sub">Import a WhatsApp chat file or adjust your filters to see listings here.</div>
      </div>`;
    return;
  }

  count.innerHTML = `<strong>${listings.length}</strong> listing${listings.length !== 1 ? 's' : ''} found`;

  grid.innerHTML = listings.map((l, i) => {
    const msg = l.ad_snippet || '';
    const originalMsg = l.original_message || '';
    const highlighted = applyHighlights(msg, l.highlight_ranges);
    const organizedRows = getOrganizedDetailsRows(l);
    const organizedTable = buildOrganizedDetailsTable(organizedRows);
    const organizedText = buildOrganizedDetailsText(organizedRows);

    return `
    <div class="card" style="animation-delay:${Math.min(i * 0.04, 0.3)}s">
      <div class="card-meta">
        <div class="meta-left">
          <div class="sender-row">
            <span class="sender-num">${escapeHtml(l.sender || '—')}</span>
            <button class="copy-btn-sm" title="Copy sender" data-copy="${escapeHtml(l.sender || '')}">${SVG.copy}</button>
          </div>
          <div class="date-row">
            <span class="send-date">${escapeHtml(l.date || '—')}</span>            
          </div>
        </div>
      </div>

      <div class="card-view-toggle" role="tablist" aria-label="Listing card view">
        <button class="view-toggle-btn active" data-view="details" type="button">Organized Details</button>
        <button class="view-toggle-btn" data-view="message" type="button">Ad Snippet</button>
        <button class="view-toggle-btn" data-view="original" type="button">Original Message</button>
      </div>

      <div class="card-view-content">
          <button
      class="btn-copy-floating"
      data-copy="${escapeHtml(organizedText)}"
      data-message-copy="${escapeHtml(msg)}"
      data-details-copy="${escapeHtml(organizedText)}"
      data-original-copy="${escapeHtml(originalMsg)}"
    >
      ${SVG.copy}
    </button>
        <div class="details-table" data-view-panel="details">${organizedTable}</div>
        <div class="message-bubble hidden" data-view-panel="message">${highlighted}</div>
        <div class="message-bubble hidden" data-view-panel="original">${escapeHtml(originalMsg)}</div>
      </div>

      <div class="card-footer">

      </div>
    </div>`;
  }).join('');

  // Bind copy buttons
  grid.querySelectorAll('[data-copy]').forEach(btn => {
    btn.addEventListener('click', () => copyText(btn.dataset.copy, btn));
  });

  grid.querySelectorAll('.card').forEach(card => {
    const toggleBtns = card.querySelectorAll('.view-toggle-btn');
    const panels = card.querySelectorAll('[data-view-panel]');
    const copyBtn = card.querySelector('.btn-copy-floating');

    toggleBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const view = btn.dataset.view;
        toggleBtns.forEach(b => b.classList.toggle('active', b === btn));
        panels.forEach(panel => {
          panel.classList.toggle('hidden', panel.dataset.viewPanel !== view);
        });
        if (copyBtn) {
          copyBtn.dataset.copy = view === 'details'
            ? copyBtn.dataset.detailsCopy || ''
            : view === 'message'
              ? copyBtn.dataset.messageCopy || ''
              : copyBtn.dataset.originalCopy || '';
        }
      });
    });
  });
}

// ── Fetch listings ──
async function fetchListings(params = {}) {
  const url = new URL(API + '/listings');
  Object.entries(params).forEach(([k, v]) => { if (v !== '' && v != null) url.searchParams.set(k, v); });
  try {
    const res = await fetch(url);
    const data = await res.json();
    renderCards(data.listings || []);
  } catch {
    showToast('Could not connect to backend. Is it running?', 'error');
    renderCards([]);
  }
}

// ── Fetch cities for filter ──
async function loadCities() {
  try {
    const res = await fetch(API + '/cities');
    const data = await res.json();
    const sel = document.getElementById('f-city');
    (data.cities || []).forEach(c => {
      const o = document.createElement('option');
      o.value = c; o.textContent = c;
      sel.appendChild(o);
    });
  } catch {}
}

// ── Search ──
function getFilters() {
  return {
    price_min: document.getElementById('f-price-min').value,
    price_max: document.getElementById('f-price-max').value,
    bedrooms:  document.getElementById('f-bedrooms').value,
    city:      document.getElementById('f-city').value,
    transaction_type: document.getElementById('f-transaction').value,
    property_type:    document.getElementById('f-proptype').value,
  };
}

let autoFilterDebounceTimer;
function fetchListingsWithCurrentFilters() {
  fetchListings(getFilters());
}

function queueAutoFilterFetch(delayMs = 250) {
  clearTimeout(autoFilterDebounceTimer);
  autoFilterDebounceTimer = setTimeout(fetchListingsWithCurrentFilters, delayMs);
}

['f-price-min', 'f-price-max'].forEach(id => {
  document.getElementById(id).addEventListener('input', () => queueAutoFilterFetch(250));
});

['f-bedrooms', 'f-city', 'f-transaction', 'f-proptype'].forEach(id => {
  document.getElementById(id).addEventListener('change', fetchListingsWithCurrentFilters);
});

document.getElementById('resetBtn').addEventListener('click', () => {
  clearTimeout(autoFilterDebounceTimer);
  ['f-price-min','f-price-max'].forEach(id => document.getElementById(id).value = '');
  ['f-bedrooms','f-city','f-transaction','f-proptype'].forEach(id => document.getElementById(id).value = '');
  fetchListings();
});

// ── Import ──
document.getElementById('importBtn').addEventListener('click', () => {
  document.getElementById('file-input').click();
});


document.getElementById('file-input').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  e.target.value = '';

  resetProgressUI();  // ← this resets the DOM

  // ← reset the server file FIRST, wait for it, then start polling
  try {
    await fetch(API + '/reset-progress', { method: 'POST' });
  } catch {}

  const overlay = document.getElementById('uploadOverlay');
  overlay.classList.add('active');

  pollProgress(async () => {
    overlay.classList.remove('active');
    showToast('Chat imported successfully!', 'success');
    await loadCities();
    await fetchListings();
  });

  try {
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch(API + '/upload', { method: 'POST', body: fd });
    const data = await res.json();
    if (!res.ok) {
      clearInterval(progressPollTimer);
      progressPollTimer = null;
      overlay.classList.remove('active');
      showToast(data.detail || 'Upload failed.', 'error');
    }
  } catch {
    clearInterval(progressPollTimer);
    progressPollTimer = null;
    overlay.classList.remove('active');
    showToast('Could not connect to backend.', 'error');
  }
});

// ── Init ──
(async () => {
  await loadCities();
  await fetchListings();
})();

// ── [PLACEHOLDER] Parse Inquiry → Auto-fill filters ──
// When the user pastes a WhatsApp message into #inquiryInput and clicks Apply,
// this function should:
//   1. Send the message text to a backend endpoint (e.g. POST /parse-inquiry)
//   2. Receive extracted filter values (price_min, price_max, bedrooms, city, etc.)
//   3. Populate the filter inputs with those values
//   4. Automatically call fetchListings(getFilters())
//
// document.querySelector('.btn-inquiry').addEventListener('click', async () => {
//   const text = document.getElementById('inquiryInput').value.trim();
//   if (!text) return;
//   const res = await fetch(API + '/parse-inquiry', {
//     method: 'POST',
//     headers: { 'Content-Type': 'application/json' },
//     body: JSON.stringify({ message: text })
//   });
//   const filters = await res.json(); // { price_min, price_max, bedrooms, city, ... }
//   // TODO: populate filter inputs from filters object
//   // TODO: fetchListings(filters);
// });
