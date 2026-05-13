// ── TRADE MODE SELECTOR ──
// Each bot has a visual tab bar to pick exactly what to trade

const botTradeMode = {
  martingale: { family: 'RISE_FALL', type: 'AUTO', digit: null },
  rsi:        { family: 'RISE_FALL', type: 'AUTO', digit: null },
  trend:      { family: 'RISE_FALL', type: 'AUTO', digit: null },
  news:       { family: 'RISE_FALL', type: 'AUTO', digit: null },
  vcrusher:   { family: 'RISE_FALL', type: 'AUTO', digit: null }
};

const tradeModes = [
  { id: 'rf',     label: '📈 Rise',     family: 'RISE_FALL',  type: 'CALL',       cls: 'active-call' },
  { id: 'rf2',    label: '📉 Fall',     family: 'RISE_FALL',  type: 'PUT',        cls: 'active-put' },
  { id: 'rfauto', label: '🤖 Auto R/F', family: 'RISE_FALL',  type: 'AUTO',       cls: 'active-auto' },
  { id: 'mat',    label: '🎯 Matches',  family: 'MATCHES',    type: 'MATCHES',    cls: 'active-digit' },
  { id: 'dif',    label: '❌ Differs',  family: 'MATCHES',    type: 'DIFFERS',    cls: 'active-digit' },
  { id: 'eve',    label: '2️⃣ Even',     family: 'EVEN_ODD',   type: 'EVEN',       cls: 'active-even' },
  { id: 'odd',    label: '1️⃣ Odd',      family: 'EVEN_ODD',   type: 'ODD',        cls: 'active-even' },
  { id: 'eoauto', label: '🤖 Auto E/O', family: 'EVEN_ODD',   type: 'AUTO',       cls: 'active-auto' },
  { id: 'ov',     label: '⬆ Over',     family: 'OVER_UNDER', type: 'DIGITOVER',  cls: 'active-digit' },
  { id: 'un',     label: '⬇ Under',    family: 'OVER_UNDER', type: 'DIGITUNDER', cls: 'active-digit' },
  { id: 'ouauto', label: '🤖 Auto O/U', family: 'OVER_UNDER', type: 'AUTO',       cls: 'active-auto' },
  { id: 'tch',    label: '👆 Touch',    family: 'TOUCH',      type: 'ONETOUCH',   cls: 'active-touch' },
  { id: 'ntch',   label: '🚫 No Touch', family: 'TOUCH',      type: 'NOTOUCH',    cls: 'active-touch' },
  { id: 'tauto',  label: '🤖 Auto T',   family: 'TOUCH',      type: 'AUTO',       cls: 'active-auto' }
];

function buildTradeModeBar(botId) {
  const container = document.getElementById('trade-mode-' + botId);
  if (!container) return;

  container.innerHTML = `
    <div class="trade-mode-bar">
      <label>⚡ WHAT TO TRADE</label>
      ${tradeModes.map(m => `
        <button
          class="mode-btn ${botTradeMode[botId].type === m.type && botTradeMode[botId].family === m.family ? m.cls : ''}"
          onclick="setTradeMode('${botId}','${m.family}','${m.type}','${m.cls}')"
          title="${m.label}">
          ${m.label}
        </button>
      `).join('')}
    </div>
    <div class="active-trade-display">
      <span class="active-trade-label">Trading:</span>
      <span class="active-trade-type" id="active-type-${botId}" style="color:var(--green)">
        AUTO Rise/Fall
      </span>
      <span class="active-trade-market" id="active-market-${botId}">
        Volatility 75
      </span>
    </div>
  `;
}

function setTradeMode(botId, family, type, cls) {
  botTradeMode[botId].family = family;
  botTradeMode[botId].type   = type;

  // Update button styles
  const bar = document.getElementById('trade-mode-' + botId);
  if (!bar) return;
  bar.querySelectorAll('.mode-btn').forEach(btn => {
    btn.className = 'mode-btn';
  });
  // Highlight selected
  const clicked = event.target;
  clicked.className = 'mode-btn ' + cls;

  // Update display
  const displayEl = document.getElementById('active-type-' + botId);
  const colors = {
    'active-call':  'var(--green)',
    'active-put':   'var(--red)',
    'active-digit': 'var(--blue)',
    'active-even':  'var(--purple)',
    'active-touch': 'var(--warn)',
    'active-auto':  'var(--accent)'
  };

  const labels = {
    'CALL':       '📈 Rise (CALL)',
    'PUT':        '📉 Fall (PUT)',
    'AUTO':       `🤖 Auto — ${family.replace('_',' ')}`,
    'MATCHES':    '🎯 Matches Digit',
    'DIFFERS':    '❌ Differs Digit',
    'EVEN':       '2️⃣ Even',
    'ODD':        '1️⃣ Odd',
    'DIGITOVER':  '⬆ Over 4',
    'DIGITUNDER': '⬇ Under 5',
    'ONETOUCH':   '👆 One Touch',
    'NOTOUCH':    '🚫 No Touch'
  };

  if (displayEl) {
    displayEl.textContent = labels[type] || type;
    displayEl.style.color = colors[cls] || 'var(--green)';
  }

  showToast(`${botId}: Trading ${labels[type] || type}`, 'success');
}

function getBotTradeMode(botId) {
  return botTradeMode[botId] || { family: 'RISE_FALL', type: 'AUTO' };
}

// Update market display
function updateTradeModeMarket(botId, marketSym) {
  const el = document.getElementById('active-market-' + botId);
  if (el) el.textContent = MARKET_LABELS[marketSym] || marketSym;
}

window.addEventListener('load', () => {
  Object.keys(botTradeMode).forEach(id => buildTradeModeBar(id));
});
