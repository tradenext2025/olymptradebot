// ── TRADE SELECTOR — 2 ROW SYSTEM ──

const ALL_MARKETS = [
  { val: 'R_10',      label: 'Volatility 10' },
  { val: 'R_25',      label: 'Volatility 25' },
  { val: 'R_50',      label: 'Volatility 50' },
  { val: 'R_75',      label: 'Volatility 75' },
  { val: 'R_100',     label: 'Volatility 100' },
  { val: 'BOOM1000',  label: 'Boom 1000' },
  { val: 'BOOM500',   label: 'Boom 500' },
  { val: 'CRASH1000', label: 'Crash 1000' },
  { val: 'CRASH500',  label: 'Crash 500' },
  { val: 'stpRNG',    label: 'Step Index' },
  { val: 'JD10',      label: 'Jump 10' },
  { val: 'JD25',      label: 'Jump 25' },
  { val: 'JD50',      label: 'Jump 50' },
  { val: 'JD75',      label: 'Jump 75' },
  { val: 'JD100',     label: 'Jump 100' },
  { val: 'RDBULL',    label: 'Range Break Bull' },
  { val: 'RDBEAR',    label: 'Range Break Bear' }
];

const CONTRACT_TYPES = [
  { val: 'CALL',       label: '📈 Rise',       color: '#00e5a0', group: 'Rise / Fall' },
  { val: 'PUT',        label: '📉 Fall',        color: '#ff4757', group: 'Rise / Fall' },
  { val: 'RF_AUTO',    label: '🤖 Auto R/F',    color: '#00b8ff', group: 'Rise / Fall' },
  { val: 'MATCHES',    label: '🎯 Matches',     color: '#a855f7', group: 'Matches / Differs' },
  { val: 'DIFFERS',    label: '❌ Differs',     color: '#a855f7', group: 'Matches / Differs' },
  { val: 'MD_AUTO',    label: '🤖 Auto M/D',    color: '#00b8ff', group: 'Matches / Differs' },
  { val: 'EVEN',       label: '2️⃣ Even',        color: '#f5a623', group: 'Even / Odd' },
  { val: 'ODD',        label: '1️⃣ Odd',         color: '#f5a623', group: 'Even / Odd' },
  { val: 'EO_AUTO',    label: '🤖 Auto E/O',    color: '#00b8ff', group: 'Even / Odd' },
  { val: 'DIGITOVER',  label: '⬆️ Over 4',      color: '#00e5a0', group: 'Over / Under' },
  { val: 'DIGITUNDER', label: '⬇️ Under 5',     color: '#ff4757', group: 'Over / Under' },
  { val: 'OU_AUTO',    label: '🤖 Auto O/U',    color: '#00b8ff', group: 'Over / Under' },
  { val: 'ONETOUCH',   label: '👆 Touch',       color: '#f5a623', group: 'Touch / No Touch' },
  { val: 'NOTOUCH',    label: '🚫 No Touch',    color: '#f5a623', group: 'Touch / No Touch' },
  { val: 'T_AUTO',     label: '🤖 Auto Touch',  color: '#00b8ff', group: 'Touch / No Touch' }
];

// Store each bot's current selection
const botSelections = {
  martingale: { market: 'R_75', contract: 'RF_AUTO' },
  rsi:        { market: 'R_75', contract: 'RF_AUTO' },
  trend:      { market: 'R_75', contract: 'RF_AUTO' },
  news:       { market: 'R_75', contract: 'RF_AUTO' },
  vcrusher:   { market: 'R_75', contract: 'RF_AUTO' }
};

function buildTradeSelector(botId) {
  const container = document.getElementById('trade-selector-' + botId);
  if (!container) return;

  const sel = botSelections[botId];

  // Group contract types
  const groups = {};
  CONTRACT_TYPES.forEach(c => {
    if (!groups[c.group]) groups[c.group] = [];
    groups[c.group].push(c);
  });

  container.innerHTML = `
    <div class="ts-wrap">

      <!-- ROW 1: MARKET -->
      <div class="ts-row">
        <div class="ts-row-label">📡 MARKET</div>
        <div class="ts-market-grid">
          ${ALL_MARKETS.map(m => `
            <button
              class="ts-market-btn ${sel.market === m.val ? 'active' : ''}"
              onclick="selectMarket('${botId}','${m.val}',this)">
              ${m.label}
            </button>
          `).join('')}
        </div>
      </div>

      <!-- ROW 2: CONTRACT TYPE -->
      <div class="ts-row">
        <div class="ts-row-label">⚡ CONTRACT TYPE</div>
        ${Object.entries(groups).map(([grp, types]) => `
          <div class="ts-group-label">${grp}</div>
          <div class="ts-contract-grid">
            ${types.map(c => `
              <button
                class="ts-contract-btn ${sel.contract === c.val ? 'active' : ''}"
                style="--btn-color:${c.color}"
                onclick="selectContract('${botId}','${c.val}',this)">
                ${c.label}
              </button>
            `).join('')}
          </div>
        `).join('')}
      </div>

      <!-- ACTIVE SELECTION DISPLAY -->
      <div class="ts-active-display" id="ts-display-${botId}">
        <span class="ts-active-icon">✅</span>
        <span class="ts-active-text">
          <b id="ts-market-label-${botId}">Volatility 75</b>
          &nbsp;→&nbsp;
          <b id="ts-contract-label-${botId}" style="color:#00b8ff">🤖 Auto R/F</b>
        </span>
      </div>

    </div>
  `;
}

function selectMarket(botId, val, btn) {
  botSelections[botId].market = val;
  // Update buttons
  btn.closest('.ts-market-grid').querySelectorAll('.ts-market-btn')
    .forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  // Update display
  const label = ALL_MARKETS.find(m => m.val === val)?.label || val;
  const el = document.getElementById('ts-market-label-' + botId);
  if (el) el.textContent = label;
  showToast(`Market → ${label}`, 'success');
}

function selectContract(botId, val, btn) {
  botSelections[botId].contract = val;
  // Update buttons
  btn.closest('.ts-contract-grid').querySelectorAll('.ts-contract-btn')
    .forEach(b => b.classList.remove('active'));
  // Also clear across all groups
  document.querySelectorAll(`#trade-selector-${botId} .ts-contract-btn`)
    .forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  // Update display
  const ct = CONTRACT_TYPES.find(c => c.val === val);
  const el = document.getElementById('ts-contract-label-' + botId);
  if (el) {
    el.textContent = ct?.label || val;
    el.style.color = ct?.color || 'var(--accent)';
  }
  showToast(`Contract → ${ct?.label || val}`, 'success');
}

function getBotSelection(botId) {
  return botSelections[botId] || { market: 'R_75', contract: 'RF_AUTO' };
}

// Resolve to actual Deriv contract_type string
function resolveContractType(val, signal) {
  if (val === 'RF_AUTO') return signal?.type || 'CALL';
  if (val === 'MD_AUTO') return signal?.type === 'PUT' ? 'DIFFERS' : 'MATCHES';
  if (val === 'EO_AUTO') return signal?.eoType || 'EVEN';
  if (val === 'OU_AUTO') return signal?.ouType === 'UNDER' ? 'DIGITUNDER' : 'DIGITOVER';
  if (val === 'T_AUTO')  return 'ONETOUCH';
  return val; // CALL, PUT, MATCHES, DIFFERS, EVEN, ODD, DIGITOVER, DIGITUNDER, ONETOUCH, NOTOUCH
}

function resolveContractFamily(val) {
  if (['CALL','PUT','RF_AUTO'].includes(val))              return 'RISE_FALL';
  if (['MATCHES','DIFFERS','MD_AUTO'].includes(val))       return 'MATCHES';
  if (['EVEN','ODD','EO_AUTO'].includes(val))              return 'EVEN_ODD';
  if (['DIGITOVER','DIGITUNDER','OU_AUTO'].includes(val))  return 'OVER_UNDER';
  if (['ONETOUCH','NOTOUCH','T_AUTO'].includes(val))       return 'TOUCH';
  return 'RISE_FALL';
}

window.addEventListener('load', () => {
  ['martingale','rsi','trend','news','vcrusher'].forEach(id => {
    buildTradeSelector(id);
  });
});
