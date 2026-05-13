// ── MAIN APP CONTROLLER ──

const tradeLog = [];

const bots = {
  martingale: { name: 'Martingale',  running: false, instance: null },
  rsi:        { name: 'RSI Scalper', running: false, instance: null },
  trend:      { name: 'Trend',       running: false, instance: null },
  news:       { name: 'News Bot',    running: false, instance: null },
  vcrusher:   { name: 'V-Crusher',   running: false, instance: null }
};

// ── TAB SWITCHING ──
function showTab(tab) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));
  document.getElementById('tab-' + tab).classList.add('active');
  const btns = document.querySelectorAll('.nav-btn');
  if (tab === 'bots')     btns[0].classList.add('active');
  if (tab === 'analysis') btns[1].classList.add('active');
    setTimeout(() => {
      renderWLChart();
      renderPerfComparison();
      renderTradeLog();
    }, 100);
  }
}

// ── SETTINGS TOGGLE ──
function toggleSettings(botId) {
  const panel = document.getElementById('settings-' + botId);
  panel.classList.toggle('open');
}

// ── BOT TOGGLE ──
function toggleBot(botId) {
  if (!isConnected) {
    showToast('Connect to Deriv first!', 'error');
    return;
  }
  if (bots[botId].running) stopBot(botId);
  else                      startBot(botId);
}

function startBot(botId) {
  bots[botId].running = true;
  updateBotUI(botId, 'running');
  switch(botId) {
    case 'martingale': bots[botId].instance = startMartingale();        break;
    case 'rsi':        bots[botId].instance = startRSIScalper();        break;
    case 'trend':      bots[botId].instance = startTrendFollower();     break;
    case 'news':       bots[botId].instance = startNewsBot();           break;
    case 'vcrusher':   bots[botId].instance = startVolatilityCrusher(); break;
  }
  showToast(bots[botId].name + ' started ▶', 'success');
  updateGlobalStats();
}

function stopBot(botId) {
  bots[botId].running = false;
  if (bots[botId].instance && bots[botId].instance.stop) {
    bots[botId].instance.stop();
  }
  bots[botId].instance = null;
  updateBotUI(botId, 'stopped');
  showToast(bots[botId].name + ' stopped ■', 'warn');
  updateGlobalStats();
}

// ── KILL ALL ──
function killAllBots() {
  Object.keys(bots).forEach(id => {
    if (bots[id].running) stopBot(id);
  });
  showToast('⚡ ALL BOTS STOPPED', 'error');
}

// ── BOT UI ──
function updateBotUI(botId, status) {
  const card  = document.getElementById('card-' + botId);
  const badge = document.getElementById('badge-' + botId);
  const btn   = document.getElementById('run-' + botId);
  if (!card || !badge || !btn) return;
  card.className  = 'bot-card ' + status;
  badge.className = 'bot-badge ' + status;
  badge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
  if (status === 'running') {
    btn.textContent = '■ Stop';
    btn.classList.add('running');
  } else {
    btn.textContent = '▶ Run';
    btn.classList.remove('running');
  }
}

// ── GLOBAL STATS ──
function updateGlobalStats() {
  const activeCount = Object.values(bots).filter(b => b.running).length;
  const total  = tradeLog.length;
  const pnl    = tradeLog.reduce((s, t) => s + t.pnl, 0);
  const wins   = tradeLog.filter(t => t.result === 'won').length;
  const wr     = total > 0 ? Math.round((wins / total) * 100) : 0;

  document.getElementById('activeBotCount').textContent = activeCount;
  document.getElementById('totalTrades').textContent    = total;
  document.getElementById('avgWinRate').textContent     = wr + '%';

  const pnlEl = document.getElementById('totalPnl');
  pnlEl.textContent  = (pnl >= 0 ? '+' : '') + '$' + pnl.toFixed(2);
  pnlEl.style.color  = pnl >= 0 ? 'var(--green)' : 'var(--red)';
}

// ── LOG TRADE ──
function logTrade(botId, market, contractType, stake, result, pnl) {
  tradeLog.unshift({
    time: new Date().toLocaleTimeString(),
    bot:  bots[botId] ? bots[botId].name : botId,
    botId, market, contractType, stake, result, pnl
  });
  if (tradeLog.length > 500) tradeLog.pop();
  updateGlobalStats();
  addMiniChartPoint(botId, pnl);

  // Live update analysis if tab open
  const analysisTab = document.getElementById('tab-analysis');
  if (analysisTab && analysisTab.classList.contains('active')) {
    renderTradeLog();
    renderWLChart();
    renderPerfComparison();
  }
}

// ── MINI CHART ──
const miniChartData = {
  martingale: [], rsi: [], trend: [], news: [], vcrusher: []
};

function addMiniChartPoint(botId, pnl) {
  if (!miniChartData[botId]) return;
  miniChartData[botId].push(pnl);
  if (miniChartData[botId].length > 50) miniChartData[botId].shift();
  drawMiniChart(botId);
}

function drawMiniChart(botId) {
  const canvas = document.getElementById('chart-' + botId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W   = canvas.offsetWidth || 300;
  const H   = 50;
  canvas.width  = W;
  canvas.height = H;
  ctx.clearRect(0, 0, W, H);

  const data = miniChartData[botId];
  if (data.length < 2) return;

  // Cumulative P&L
  const cum = [];
  let sum = 0;
  data.forEach(v => { sum += v; cum.push(sum); });

  const min   = Math.min(...cum);
  const max   = Math.max(...cum);
  const range = max - min || 1;
  const stepX = W / (cum.length - 1);

  ctx.beginPath();
  cum.forEach((v, i) => {
    const x = i * stepX;
    const y = H - ((v - min) / range) * (H - 8) - 4;
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });

  const last = cum[cum.length - 1];
  const grad = ctx.createLinearGradient(0, 0, W, 0);
  if (last >= 0) {
    grad.addColorStop(0, 'rgba(0,229,160,0.2)');
    grad.addColorStop(1, '#00e5a0');
  } else {
    grad.addColorStop(0, 'rgba(255,71,87,0.2)');
    grad.addColorStop(1, '#ff4757');
  }
  ctx.strokeStyle = grad;
  ctx.lineWidth   = 1.5;
  ctx.stroke();
}

// ── UPDATE BOT STATS ──
function updateBotStats(botId, stats) {
  const prefix = {
    martingale: 'mg',
    rsi:        'rsi',
    trend:      'tr',
    news:       'nw',
    vcrusher:   'vc'
  }[botId];
  if (!prefix) return;

  const set = (id, val, cls) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = val;
    if (cls) el.className = 'stat-val ' + cls;
  };

  const wr = stats.trades > 0
    ? Math.round((stats.wins / stats.trades) * 100) : 0;
  const profit = stats.profit || 0;

  set(prefix + '-trades', stats.trades || 0);
  set(prefix + '-winrate', wr + '%', wr >= 50 ? 'green' : 'red');
  set(prefix + '-profit',
    (profit >= 0 ? '+' : '') + '$' + profit.toFixed(2),
    profit >= 0 ? 'green' : 'red'
  );

  // Tick speed
  if (stats.tickSpeed) {
    const spEl = document.getElementById(prefix + '-tickspeed');
    if (spEl) spEl.textContent = stats.tickSpeed + ' ms';
  }

  // Bot-specific
  if (botId === 'martingale' && stats.streak !== undefined)
    set('mg-streak', stats.streak);
  if (botId === 'rsi' && stats.rsiValue !== undefined)
    set('rsi-rsivalue', stats.rsiValue.toFixed(1), 'blue');
  if (botId === 'trend' && stats.trend !== undefined)
    set('tr-trend', stats.trend, 'blue');
  if (botId === 'news' && stats.spikes !== undefined)
    set('nw-spikes', stats.spikes, 'warn');
  if (botId === 'vcrusher' && stats.atr !== undefined)
    set('vc-atr', stats.atr.toFixed(5), 'blue');
}

// ── TRADE LOG ──
function renderTradeLog() {
  const tbody     = document.getElementById('tradeLogBody');
  const botFilter = document.getElementById('logBotFilter').value;
  const resFilter = document.getElementById('logResultFilter').value;
  if (!tbody) return;

  let filtered = tradeLog;
  if (botFilter !== 'all') filtered = filtered.filter(t => t.botId === botFilter);
  if (resFilter !== 'all') filtered = filtered.filter(t => t.result === resFilter);

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="empty-log">No trades match filter.</td></tr>';
    return;
  }

  tbody.innerHTML = filtered.map(t => `
    <tr>
      <td>${t.time}</td>
      <td>${t.bot}</td>
      <td>${t.market}</td>
      <td>${t.contractType}</td>
      <td>$${parseFloat(t.stake).toFixed(2)}</td>
      <td class="${t.result}">${t.result.toUpperCase()}</td>
      <td class="${t.pnl >= 0 ? 'won' : 'lost'}">
        ${t.pnl >= 0 ? '+' : ''}$${parseFloat(t.pnl).toFixed(2)}
      </td>
    </tr>
  `).join('');
}

function clearLog() {
  tradeLog.length = 0;
  renderTradeLog();
  updateGlobalStats();
  showToast('Trade log cleared', 'warn');
}

// ── TOAST ──
function showToast(msg, type = 'success') {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className   = 'toast ' + type;
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity    = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ── INIT ──
window.addEventListener('load', () => {
  // Build watchlist UI
  buildWatchlistUI('watchlistUI');
  // Draw empty mini charts
  Object.keys(miniChartData).forEach(id => drawMiniChart(id));
  renderPerfComparison();
  renderTradeLog();

  // Add tick speed style
  const style = document.createElement('style');
  style.textContent = `
    .tick-speed-bar {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
      padding: 4px 8px;
      background: var(--surface2);
      border-radius: 5px;
      border: 1px solid var(--border);
    }
    .tick-speed-lbl {
      font-size: 10px;
      color: var(--text3);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .tick-speed-val {
      font-family: 'Space Mono', monospace;
      font-size: 11px;
      color: var(--accent2);
      font-weight: 700;
    }
  `;
  document.head.appendChild(style);
});

// ── STRATEGY LOGIC TAB ──
let slMarketCount = 0;
let slOrCount = 0;

function slToggle(cb) {
  const row = cb.closest('.sl-toggle-row');
  const val = row.querySelector('.sl-val');
  if (!val) return;
  val.textContent = cb.checked ? 'ACTIVE' : 'DISABLED';
  val.style.color = cb.checked ? '#00c853' : '#f44336';
}

function slAddVolatility(sel, chipId) {
  if (!sel.value) return;
  const area = document.getElementById(chipId);
  const chip = document.createElement('span');
  chip.style.cssText = 'display:inline-flex;align-items:center;background:#1e293b;border-radius:20px;padding:5px 12px;font-size:12px;color:#00d4aa;gap:6px;margin:3px;';
  chip.innerHTML = sel.value + ' <span onclick="this.parentElement.remove()" style="cursor:pointer;color:#888;">✕</span>';
  area.appendChild(chip);
  sel.value = '';
}

function slMakeCondition(type) {
  const isAnd = type === 'and';
  const id = 'sl_' + Date.now();
  const div = document.createElement('div');
  div.style.cssText = 'background:#0f172a;border-radius:10px;padding:14px;margin:12px 0;border:1px solid #1e293b;';
  div.innerHTML = `
    <div style="color:${isAnd ? '#a78bfa' : '#00d4aa'};font-weight:800;font-size:12px;letter-spacing:1px;border-bottom:1px solid #1e293b;padding-bottom:8px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;">
      ${isAnd ? 'AND CONDITION' : 'CONDITION'}
      <button onclick="this.closest('div[data-cond]').remove()" style="background:none;border:none;color:#f44336;font-size:18px;cursor:pointer;">🗑</button>
    </div>
    <div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;margin-bottom:5px;">ALGORITHM</div>
    <div style="display:flex;gap:8px;align-items:center;">
      <select style="flex:1;background:#1e293b;border:1px solid #334155;border-radius:8px;padding:9px;color:#e2e8f0;font-size:13px;">
        <option>LDP</option><option>MDP</option><option>RSI</option><option>MACD</option><option>STREAK</option><option>RANDOM</option>
      </select>
      <button style="background:#1565c0;color:#fff;border:none;border-radius:50%;width:26px;height:26px;font-size:12px;cursor:pointer;">i</button>
    </div>
    <div style="display:flex;gap:8px;margin-top:10px;align-items:flex-end;">
      <div style="background:#1e293b;border:1px solid #334155;border-radius:10px;padding:8px 10px;min-width:90px;">
        <div style="font-size:9px;color:#64748b;font-weight:700;letter-spacing:0.8px;">STRICT</div>
        <div style="font-size:11px;font-weight:700;color:#00c853;" id="sv${id}">ACTIVE</div>
        <label style="position:relative;display:inline-block;width:40px;height:22px;margin-top:4px;">
          <input type="checkbox" checked onchange="document.getElementById('sv${id}').textContent=this.checked?'ACTIVE':'DISABLED';document.getElementById('sv${id}').style.color=this.checked?'#00c853':'#f44336';" style="opacity:0;width:0;height:0;">
          <span style="position:absolute;top:0;left:0;right:0;bottom:0;background:#00c853;border-radius:22px;transition:0.3s;cursor:pointer;"></span>
        </label>
      </div>
      <div style="flex:1;">
        <div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;margin-bottom:4px;">IF LAST</div>
        <input type="number" value="3" min="1" style="width:100%;background:#1e293b;border:1px solid #334155;border-radius:8px;padding:9px;color:#e2e8f0;font-size:13px;">
      </div>
      <div style="flex:1;">
        <div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;margin-bottom:4px;">DIGITS IS</div>
        <select style="width:100%;background:#1e293b;border:1px solid #334155;border-radius:8px;padding:9px;color:#e2e8f0;font-size:13px;">
          <option>UNDER</option><option>OVER</option><option>EVEN</option><option>ODD</option><option>MATCHES</option><option>DIFFERS</option>
        </select>
      </div>
    </div>
    <div style="display:flex;gap:8px;margin-top:10px;">
      <div style="flex:1;">
        <div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;margin-bottom:4px;">STAKE</div>
        <input type="number" value="8" style="width:100%;background:#1e293b;border:1px solid #334155;border-radius:8px;padding:9px;color:#e2e8f0;font-size:13px;">
      </div>
      <div style="flex:1;">
        <div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;margin-bottom:4px;">RECOVERY LIMIT</div>
        <input type="number" value="0" style="width:100%;background:#1e293b;border:1px solid #334155;border-radius:8px;padding:9px;color:#e2e8f0;font-size:13px;">
      </div>
    </div>
  `;
  div.setAttribute('data-cond', '1');
  return div;
}

function slAddOrGroup(containerId) {
  slOrCount++;
  const container = document.getElementById(containerId);
  const group = document.createElement('div');
  group.style.cssText = 'border:2px dashed #2563eb;border-radius:14px;padding:12px;margin-bottom:14px;position:relative;';
  const badge = document.createElement('div');
  badge.style.cssText = 'position:absolute;top:-12px;left:12px;background:#0f172a;color:#fff;font-size:11px;font-weight:700;padding:2px 10px;border-radius:6px;border:1px solid #2563eb;';
  badge.textContent = 'OR GROUP #' + slOrCount;
  group.appendChild(badge);
  group.appendChild(slMakeCondition('condition'));
  const andBtn = document.createElement('button');
  andBtn.style.cssText = 'background:none;border:none;color:#2563eb;font-size:12px;font-weight:700;cursor:pointer;padding:8px 4px 0;display:flex;align-items:center;gap:4px;';
  andBtn.textContent = '+ ADD AND LOGIC';
  andBtn.onclick = () => group.insertBefore(slMakeCondition('and'), andBtn);
  group.appendChild(andBtn);
  container.appendChild(group);
}

function slAddMarket() {
  slMarketCount++;
  const n = slMarketCount;
  const container = document.getElementById('sl-markets-container');
  const mDiv = document.createElement('div');
  mDiv.id = 'sl-market-' + n;
  mDiv.style.cssText = 'background:#1a2332;border-radius:14px;margin-bottom:14px;overflow:hidden;border:1px solid #1e293b;';
  const chipId = 'sl-chips-' + n;
  const orId = 'sl-or-' + n;
  mDiv.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;padding:14px 16px;background:#162032;cursor:pointer;" onclick="this.nextElementSibling.style.display=this.nextElementSibling.style.display==='none'?'block':'none'">
      <span style="font-weight:800;font-size:14px;color:#e2e8f0;">▲ MARKET${n}</span>
      <button onclick="event.stopPropagation();if(confirm('Remove market?'))this.closest('[id^=sl-market]').remove();" style="background:none;border:none;color:#64748b;font-size:20px;cursor:pointer;">✕</button>
    </div>
    <div style="padding:14px;">
      <div style="font-weight:800;font-size:12px;color:#94a3b8;letter-spacing:0.8px;margin-bottom:10px;">📊 MARKET VOLATILITIES</div>
      <div class="sl-toggle-row" style="background:#0f172a;border-radius:10px;padding:12px 14px;display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
        <div><div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;">GLOBAL SHARED</div><div class="sl-val" style="font-size:12px;font-weight:700;color:#f44336;">DISABLED</div></div>
        <label style="position:relative;display:inline-block;width:46px;height:26px;"><input type="checkbox" onchange="slToggle(this)" style="opacity:0;width:0;height:0;"><span style="position:absolute;top:0;left:0;right:0;bottom:0;background:#334155;border-radius:26px;cursor:pointer;transition:0.3s;"></span></label>
      </div>
      <div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;margin:8px 0 4px;">ADD VOLATILITY</div>
      <select onchange="slAddVolatility(this,'${chipId}')" style="width:100%;background:#1e293b;border:1px solid #334155;border-radius:8px;padding:9px;color:#94a3b8;font-size:13px;">
        <option value="">Select a Volatility...</option>
        <option>Volatility 10</option><option>Volatility 25</option><option>Volatility 50</option><option>Volatility 75</option><option>Volatility 100</option><option>Volatility 10 (1s)</option><option>Volatility 25 (1s)</option><option>Volatility 50 (1s)</option><option>Volatility 75 (1s)</option><option>Volatility 100 (1s)</option>
        <option>Boom 1000</option><option>Boom 500</option><option>Crash 1000</option><option>Crash 500</option>
        <option>Step Index</option><option>Jump 10</option><option>Jump 25</option><option>Jump 50</option><option>Jump 75</option><option>Jump 100</option>
        <option>Range Break Bull</option><option>Range Break Bear</option>
      </select>
      <div id="${chipId}" style="border:1.5px dashed #334155;border-radius:10px;padding:8px;min-height:38px;display:flex;flex-wrap:wrap;gap:4px;margin-top:6px;"></div>
      <div class="sl-toggle-row" style="background:#0f172a;border-radius:10px;padding:12px 14px;display:flex;align-items:center;justify-content:space-between;margin-top:8px;">
        <div><div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;">VOLATILITY SWITCHER</div><div class="sl-val" style="font-size:12px;font-weight:700;color:#f44336;">DISABLED</div></div>
        <label style="position:relative;display:inline-block;width:46px;height:26px;"><input type="checkbox" onchange="slToggle(this)" style="opacity:0;width:0;height:0;"><span style="position:absolute;top:0;left:0;right:0;bottom:0;background:#334155;border-radius:26px;cursor:pointer;transition:0.3s;"></span></label>
      </div>

      <div style="font-weight:800;font-size:12px;color:#94a3b8;letter-spacing:0.8px;margin:14px 0 8px;border-top:1px solid #1e293b;padding-top:10px;">⚡ TRADE DEFINITION</div>
      <div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;margin-bottom:4px;">CONTRACT TYPE</div>
      <select style="width:100%;background:#1e293b;border:1px solid #334155;border-radius:8px;padding:9px;color:#e2e8f0;font-size:13px;margin-bottom:8px;">
        <option>OVER</option><option>UNDER</option><option>EVEN</option><option>ODD</option><option>RISE</option><option>FALL</option><option>MATCHES</option><option>DIFFERS</option>
      </select>
      <div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;margin-bottom:4px;">PREDICTION</div>
      <input type="number" value="3" min="0" max="9" style="width:100%;background:#1e293b;border:1px solid #334155;border-radius:8px;padding:9px;color:#e2e8f0;font-size:13px;margin-bottom:8px;">
      <div class="sl-toggle-row" style="background:#0f172a;border-radius:10px;padding:12px 14px;display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
        <div><div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;">ADVANCED SETTINGS</div><div class="sl-val" style="font-size:12px;font-weight:700;color:#f44336;">DISABLED</div></div>
        <label style="position:relative;display:inline-block;width:46px;height:26px;"><input type="checkbox" onchange="slToggle(this)" style="opacity:0;width:0;height:0;"><span style="position:absolute;top:0;left:0;right:0;bottom:0;background:#334155;border-radius:26px;cursor:pointer;transition:0.3s;"></span></label>
      </div>
      <div class="sl-toggle-row" style="background:#0f172a;border-radius:10px;padding:12px 14px;display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
        <div><div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;">RANDOM SETTINGS</div><div class="sl-val" style="font-size:12px;font-weight:700;color:#f44336;">DISABLED</div></div>
        <label style="position:relative;display:inline-block;width:46px;height:26px;"><input type="checkbox" onchange="slToggle(this)" style="opacity:0;width:0;height:0;"><span style="position:absolute;top:0;left:0;right:0;bottom:0;background:#334155;border-radius:26px;cursor:pointer;transition:0.3s;"></span></label>
      </div>
      <div class="sl-toggle-row" style="background:#0f172a;border-radius:10px;padding:12px 14px;display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
        <div><div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;">ANALYSIS INJECT CONTRACT</div><div class="sl-val" style="font-size:12px;font-weight:700;color:#f44336;">DISABLED</div></div>
        <label style="position:relative;display:inline-block;width:46px;height:26px;"><input type="checkbox" onchange="slToggle(this)" style="opacity:0;width:0;height:0;"><span style="position:absolute;top:0;left:0;right:0;bottom:0;background:#334155;border-radius:26px;cursor:pointer;transition:0.3s;"></span></label>
      </div>
      <div style="display:flex;gap:8px;margin-top:8px;">
        <div style="flex:1;"><div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;margin-bottom:4px;">DURATION</div><input type="number" value="1" min="1" style="width:100%;background:#1e293b;border:1px solid #334155;border-radius:8px;padding:9px;color:#e2e8f0;font-size:13px;"></div>
        <div style="flex:1;"><div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;margin-bottom:4px;">UNIT</div><button style="width:100%;background:#00bcd4;color:#fff;border:none;border-radius:8px;padding:10px;font-weight:800;font-size:13px;cursor:pointer;">TICKS</button></div>
      </div>

      <div style="font-weight:800;font-size:12px;color:#94a3b8;letter-spacing:0.8px;margin:14px 0 8px;border-top:1px solid #1e293b;padding-top:10px;">🛡 RISK MANAGER</div>
      <div class="sl-toggle-row" style="background:#0f172a;border-radius:10px;padding:12px 14px;display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
        <div><div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;">GLOBAL SHARED</div><div class="sl-val" style="font-size:12px;font-weight:700;color:#f44336;">DISABLED</div></div>
        <label style="position:relative;display:inline-block;width:46px;height:26px;"><input type="checkbox" onchange="slToggle(this)" style="opacity:0;width:0;height:0;"><span style="position:absolute;top:0;left:0;right:0;bottom:0;background:#334155;border-radius:26px;cursor:pointer;transition:0.3s;"></span></label>
      </div>
      <div class="sl-toggle-row" style="background:#0f172a;border-radius:10px;padding:12px 14px;display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
        <div><div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;">INJECT RISK MANAGER</div><div class="sl-val" style="font-size:12px;font-weight:700;color:#f44336;">DISABLED</div></div>
        <label style="position:relative;display:inline-block;width:46px;height:26px;"><input type="checkbox" onchange="slToggle(this)" style="opacity:0;width:0;height:0;"><span style="position:absolute;top:0;left:0;right:0;bottom:0;background:#334155;border-radius:26px;cursor:pointer;transition:0.3s;"></span></label>
      </div>
      <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px;">
        <input type="text" value="Martingale" style="flex:1;background:#1e293b;border:1px solid #334155;border-radius:8px;padding:9px;color:#e2e8f0;font-size:13px;">
        <button style="background:#1565c0;color:#fff;border:none;border-radius:50%;width:28px;height:28px;font-size:12px;cursor:pointer;">i</button>
      </div>
      <div class="sl-toggle-row" style="background:#0f172a;border-radius:10px;padding:12px 14px;display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
        <div><div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;">RISK MANAGER</div><div class="sl-val" style="font-size:12px;font-weight:700;color:#00c853;">ACTIVE</div></div>
        <label style="position:relative;display:inline-block;width:46px;height:26px;"><input type="checkbox" checked onchange="slToggle(this)" style="opacity:0;width:0;height:0;"><span style="position:absolute;top:0;left:0;right:0;bottom:0;background:#00c853;border-radius:26px;cursor:pointer;transition:0.3s;"></span></label>
      </div>
      <div class="sl-toggle-row" style="background:#0f172a;border-radius:10px;padding:12px 14px;display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
        <div><div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;">ONLOSE</div><div class="sl-val" style="font-size:12px;font-weight:700;color:#00c853;">ACTIVE</div></div>
        <label style="position:relative;display:inline-block;width:46px;height:26px;"><input type="checkbox" checked onchange="slToggle(this)" style="opacity:0;width:0;height:0;"><span style="position:absolute;top:0;left:0;right:0;bottom:0;background:#00c853;border-radius:26px;cursor:pointer;transition:0.3s;"></span></label>
      </div>
      <div style="display:flex;gap:8px;margin-bottom:8px;">
        <div style="flex:1;"><div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;margin-bottom:4px;">ACTIVATE LIMIT</div><input type="number" value="1" style="width:100%;background:#1e293b;border:1px solid #334155;border-radius:8px;padding:9px;color:#e2e8f0;font-size:13px;"></div>
        <div style="flex:1;"><div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;margin-bottom:4px;">DEACTIVATE LIMIT</div><input type="number" value="100" style="width:100%;background:#1e293b;border:1px solid #334155;border-radius:8px;padding:9px;color:#e2e8f0;font-size:13px;"></div>
      </div>
      <div style="display:flex;gap:8px;margin-bottom:8px;">
        <div style="flex:1;"><div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;margin-bottom:4px;">MULTIPLIER</div><input type="number" value="2" style="width:100%;background:#1e293b;border:1px solid #334155;border-radius:8px;padding:9px;color:#e2e8f0;font-size:13px;"></div>
        <div style="flex:1;"><div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;margin-bottom:4px;">STAKE</div><input type="number" value="10" style="width:100%;background:#1e293b;border:1px solid #334155;border-radius:8px;padding:9px;color:#e2e8f0;font-size:13px;"></div>
      </div>

      <div style="font-weight:800;font-size:12px;color:#94a3b8;letter-spacing:0.8px;margin:14px 0 8px;border-top:1px solid #1e293b;padding-top:10px;">👆 VIRTUAL HOOK</div>

      <div style="font-weight:800;font-size:12px;color:#94a3b8;letter-spacing:0.8px;margin:14px 0 8px;border-top:1px solid #1e293b;padding-top:10px;">💡 STRATEGY LOGIC</div>
      <div class="sl-toggle-row" style="background:#0f172a;border-radius:10px;padding:12px 14px;display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
        <div><div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;">GLOBAL SHARED</div><div class="sl-val" style="font-size:12px;font-weight:700;color:#f44336;">DISABLED</div></div>
        <label style="position:relative;display:inline-block;width:46px;height:26px;"><input type="checkbox" onchange="slToggle(this)" style="opacity:0;width:0;height:0;"><span style="position:absolute;top:0;left:0;right:0;bottom:0;background:#334155;border-radius:26px;cursor:pointer;transition:0.3s;"></span></label>
      </div>
      <div class="sl-toggle-row" style="background:#0f172a;border-radius:10px;padding:12px 14px;display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
        <div><div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:0.8px;">STRATEGY</div><div class="sl-val" style="font-size:12px;font-weight:700;color:#00c853;">ACTIVE</div></div>
        <label style="position:relative;display:inline-block;width:46px;height:26px;"><input type="checkbox" checked onchange="slToggle(this)" style="opacity:0;width:0;height:0;"><span style="position:absolute;top:0;left:0;right:0;bottom:0;background:#00c853;border-radius:26px;cursor:pointer;transition:0.3s;"></span></label>
      </div>
      <div id="${orId}"></div>
      <button onclick="slAddOrGroup('${orId}')" style="background:#f5a623;color:#fff;border:none;border:none;border-radius:24px;padding:11px 22px;font-weight:800;font-size:13px;cursor:pointer;display:flex;align-items:center;gap:6px;margin:8px auto;">+ ADD OR GROUP</button>
      <div style="background:#1e293b;border-radius:10px;padding:14px;display:flex;align-items:center;gap:8px;font-weight:700;font-size:13px;color:#a78bfa;margin-top:8px;">⚡ POST-SIGNAL SEQUENCE</div>
    </div>
  `;
  container.appendChild(mDiv);
}
let slRunInterval = null;

function slToggleRun() {
  slIsRunning = !slIsRunning;
  const btn = document.getElementById('sl-run-btn');
  const status = document.getElementById('sl-run-status');
  if (slIsRunning) {
    btn.style.background = '#f44336';
    btn.textContent = '⏹ Stop';
    status.textContent = 'Strategy is running...';
    status.style.color = '#00c853';
    slSimulateTrade();
    slRunInterval = setInterval(slSimulateTrade, 4000);
  } else {
    btn.style.background = '#00c853';
    btn.textContent = '▶ Run';
    status.textContent = 'Strategy stopped';
    status.style.color = '#f44336';
    clearInterval(slRunInterval);
  }
}

function slSimulateTrade() {
  const types = ['OVER', 'UNDER', 'EVEN', 'ODD'];
  const markets = ['V10', 'V25', 'V50', 'V75', 'V100', 'Boom 1000', 'Crash 1000'];
  const won = Math.random() > 0.45;
  const stake = 0.35;
  const pnl = won ? +(stake * 0.057).toFixed(3) : -stake;
  const entry = (Math.random() * 1000 + 100).toFixed(2);
  const trade = {
    time: new Date().toLocaleTimeString(),
    market: markets[Math.floor(Math.random() * markets.length)],
    type: types[Math.floor(Math.random() * types.length)],
    entry: entry,
    exit: entry,
    stake: stake,
    pnl: pnl,
    won: won
  };
  slTradeHistory.unshift(trade);
  if (slTradeHistory.length > 50) slTradeHistory.pop();
  slRenderHistory();
  slUpdateSummary();
}

function slUpdateSummary() {
  const total = slTradeHistory.length;
  const wins = slTradeHistory.filter(t => t.won).length;
  const pnl = slTradeHistory.reduce((s, t) => s + t.pnl, 0);
  const wr = total ? Math.round((wins / total) * 100) : 0;
  const el = id => document.getElementById(id);
  if (el('sl-stat-trades')) el('sl-stat-trades').textContent = total;
  if (el('sl-stat-wr')) el('sl-stat-wr').textContent = wr + '%';
  if (el('sl-stat-pnl')) {
    el('sl-stat-pnl').textContent = (pnl >= 0 ? '+' : '') + '$' + pnl.toFixed(2);
    el('sl-stat-pnl').style.color = pnl >= 0 ? '#00c853' : '#f44336';
  }
  if (el('sl-stat-wins')) el('sl-stat-wins').textContent = wins;
  if (el('sl-stat-losses')) el('sl-stat-losses').textContent = total - wins;
  const totalStake = slTradeHistory.reduce((s, t) => s + t.stake, 0);
  const totalPayout = slTradeHistory.filter(t => t.won).reduce((s, t) => s + t.stake + t.pnl, 0);
  if (el('sl-stat-stake')) el('sl-stat-stake').textContent = '$' + totalStake.toFixed(2);
  if (el('sl-stat-payout')) el('sl-stat-payout').textContent = '$' + totalPayout.toFixed(2);
  if (el('sl-stat-runs')) el('sl-stat-runs').textContent = total;
}

function slRenderHistory() {
  const tbody = document.getElementById('sl-history-tbody');
  if (!tbody) return;
  tbody.innerHTML = slTradeHistory.map(t => `
    <tr style="border-bottom:1px solid #1e293b;">
      <td style="padding:8px 6px;font-size:11px;color:#94a3b8;">${t.time}</td>
      <td style="padding:8px 6px;font-size:11px;color:#e2e8f0;">${t.market}</td>
      <td style="padding:8px 6px;font-size:11px;color:#e2e8f0;">${t.type}</td>
      <td style="padding:8px 6px;font-size:11px;color:#e2e8f0;">${t.entry}</td>
      <td style="padding:8px 6px;font-size:11px;color:#e2e8f0;">$${t.stake}</td>
      <td style="padding:8px 6px;font-size:12px;font-weight:700;color:${t.won ? '#00c853' : '#f44336'};">${t.won ? '+' : ''}$${t.pnl.toFixed(3)}</td>
      <td style="padding:8px 6px;"><span style="background:${t.won ? '#052e16' : '#2d0a0a'};color:${t.won ? '#00c853' : '#f44336'};border-radius:6px;padding:2px 8px;font-size:10px;font-weight:700;">${t.won ? 'WIN' : 'LOSS'}</span></td>
    </tr>
  `).join('');
}

function slClearHistory() {
  slTradeHistory = [];
  slRenderHistory();
  slUpdateSummary();
}
