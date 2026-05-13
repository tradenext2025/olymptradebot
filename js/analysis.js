// ── ANALYSIS ENGINE ──

// Live price chart data
const priceChartData = [];
const MAX_PRICE_POINTS = 80;
let currentChartMarket = 'R_75';
let priceChartAnimFrame = null;

// ── LIVE PRICE CHART ──
function onAnalysisTick(tick) {
  if (tick.symbol !== currentChartMarket) return;
  priceChartData.push({ price: tick.quote, time: tick.epoch });
  if (priceChartData.length > MAX_PRICE_POINTS) priceChartData.shift();
  document.getElementById('livePriceDisplay').textContent = tick.quote.toFixed(4);
  drawPriceChart();
}

function switchChartMarket() {
  currentChartMarket = document.getElementById('chartMarket').value;
  priceChartData.length = 0;
  document.getElementById('livePriceDisplay').textContent = '──';
  drawPriceChart();
  if (isConnected) {
    subscribeTicks(currentChartMarket, onAnalysisTick);
  }
}

function drawPriceChart() {
  const canvas = document.getElementById('priceChart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W   = canvas.offsetWidth || 340;
  const H   = 180;
  canvas.width  = W;
  canvas.height = H;
  ctx.clearRect(0, 0, W, H);

  const data = priceChartData;
  if (data.length < 2) {
    ctx.fillStyle = '#1e2a35';
    ctx.font = '12px Space Mono, monospace';
    ctx.fillText('Waiting for price data...', W/2 - 90, H/2);
    return;
  }

  const prices = data.map(d => d.price);
  const min    = Math.min(...prices);
  const max    = Math.max(...prices);
  const range  = max - min || 0.0001;
  const pad    = { top: 16, bottom: 24, left: 8, right: 8 };
  const chartW = W - pad.left - pad.right;
  const chartH = H - pad.top - pad.bottom;
  const stepX  = chartW / (data.length - 1);

  const toX = i => pad.left + i * stepX;
  const toY = p => pad.top + chartH - ((p - min) / range) * chartH;

  // Grid lines
  ctx.strokeStyle = '#1e2a35';
  ctx.lineWidth   = 1;
  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (chartH / 4) * i;
    ctx.beginPath();
    ctx.moveTo(pad.left, y);
    ctx.lineTo(W - pad.right, y);
    ctx.stroke();
    const val = max - (range / 4) * i;
    ctx.fillStyle = '#3d5168';
    ctx.font = '9px Space Mono, monospace';
    ctx.fillText(val.toFixed(2), W - pad.right - 38, y - 2);
  }

  // Gradient fill
  const fillGrad = ctx.createLinearGradient(0, pad.top, 0, H - pad.bottom);
  fillGrad.addColorStop(0, 'rgba(0,229,160,0.18)');
  fillGrad.addColorStop(1, 'rgba(0,229,160,0)');

  ctx.beginPath();
  data.forEach((d, i) => {
    const x = toX(i);
    const y = toY(d.price);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.lineTo(toX(data.length - 1), H - pad.bottom);
  ctx.lineTo(toX(0), H - pad.bottom);
  ctx.closePath();
  ctx.fillStyle = fillGrad;
  ctx.fill();

  // Price line
  ctx.beginPath();
  data.forEach((d, i) => {
    const x = toX(i);
    const y = toY(d.price);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  const lineGrad = ctx.createLinearGradient(0, 0, W, 0);
  lineGrad.addColorStop(0, 'rgba(0,229,160,0.4)');
  lineGrad.addColorStop(1, '#00e5a0');
  ctx.strokeStyle = lineGrad;
  ctx.lineWidth   = 2;
  ctx.lineJoin    = 'round';
  ctx.stroke();

  // Last price dot
  const lastX = toX(data.length - 1);
  const lastY = toY(prices[prices.length - 1]);
  ctx.beginPath();
  ctx.arc(lastX, lastY, 4, 0, Math.PI * 2);
  ctx.fillStyle = '#00e5a0';
  ctx.fill();
  ctx.strokeStyle = '#080c10';
  ctx.lineWidth = 2;
  ctx.stroke();

  // Trade markers from log
  tradeLog.slice(0, 20).forEach(t => {
    if (t.market !== currentChartMarket) return;
    const color = t.result === 'won' ? '#00e5a0' : '#ff4757';
    const idx   = Math.max(0, data.length - 5);
    const x     = toX(idx);
    const y     = toY(prices[idx] || prices[prices.length-1]);
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
  });
}

// ── WIN/LOSS BAR CHART ──
function renderWLChart() {
  const canvas    = document.getElementById('wlChart');
  if (!canvas) return;
  const ctx       = canvas.getContext('2d');
  const botFilter = document.getElementById('wlBotFilter').value;
  const W         = canvas.offsetWidth || 340;
  const H         = 160;
  canvas.width    = W;
  canvas.height   = H;
  ctx.clearRect(0, 0, W, H);

  // Bucket last 20 trades into wins/losses per 5-trade group
  let filtered = botFilter === 'all'
    ? tradeLog
    : tradeLog.filter(t => t.botId === botFilter);

  filtered = filtered.slice(0, 40).reverse();

  if (filtered.length === 0) {
    ctx.fillStyle = '#3d5168';
    ctx.font = '12px Space Mono, monospace';
    ctx.fillText('No trade data yet', W/2 - 70, H/2);
    return;
  }

  // Group into chunks of 5
  const groups = [];
  for (let i = 0; i < filtered.length; i += 5) {
    const chunk = filtered.slice(i, i + 5);
    const wins  = chunk.filter(t => t.result === 'won').length;
    const loss  = chunk.length - wins;
    const pnl   = chunk.reduce((s, t) => s + t.pnl, 0);
    groups.push({ wins, loss, pnl, label: `#${Math.floor(i/5)+1}` });
  }

  const barW   = Math.min(32, (W - 40) / groups.length - 8);
  const maxVal = Math.max(...groups.map(g => Math.max(g.wins, g.loss)), 1);
  const chartH = H - 36;
  const startX = (W - (groups.length * (barW * 2 + 10))) / 2;

  groups.forEach((g, i) => {
    const x    = startX + i * (barW * 2 + 10);
    const winH = (g.wins / maxVal) * chartH;
    const losH = (g.loss / maxVal) * chartH;

    // Win bar
    const wg = ctx.createLinearGradient(0, chartH - winH + 8, 0, chartH + 8);
    wg.addColorStop(0, 'rgba(0,229,160,0.9)');
    wg.addColorStop(1, 'rgba(0,229,160,0.3)');
    ctx.fillStyle = wg;
    ctx.beginPath();
    ctx.roundRect(x, chartH - winH + 8, barW, winH, [3, 3, 0, 0]);
    ctx.fill();

    // Loss bar
    const lg = ctx.createLinearGradient(0, chartH - losH + 8, 0, chartH + 8);
    lg.addColorStop(0, 'rgba(255,71,87,0.9)');
    lg.addColorStop(1, 'rgba(255,71,87,0.3)');
    ctx.fillStyle = lg;
    ctx.beginPath();
    ctx.roundRect(x + barW + 2, chartH - losH + 8, barW, losH, [3, 3, 0, 0]);
    ctx.fill();

    // Label
    ctx.fillStyle = '#3d5168';
    ctx.font = '9px Space Mono, monospace';
    ctx.fillText(g.label, x + barW/2 - 6, H - 4);

    // Values
    ctx.fillStyle = '#00e5a0';
    ctx.font = '9px Space Mono, monospace';
    if (winH > 14) ctx.fillText(g.wins, x + 3, chartH - winH + 20);
    ctx.fillStyle = '#ff4757';
    if (losH > 14) ctx.fillText(g.loss, x + barW + 5, chartH - losH + 20);
  });

  // Legend
  ctx.fillStyle = '#00e5a0';
  ctx.fillRect(W - 80, 4, 10, 10);
  ctx.fillStyle = '#6b8099';
  ctx.font = '10px Syne, sans-serif';
  ctx.fillText('Win', W - 66, 13);
  ctx.fillStyle = '#ff4757';
  ctx.fillRect(W - 38, 4, 10, 10);
  ctx.fillStyle = '#6b8099';
  ctx.fillText('Loss', W - 24, 13);
}

// ── PERFORMANCE COMPARISON ──
function renderPerfComparison() {
  const container = document.getElementById('perfComparison');
  if (!container) return;

  const botList = [
    { id: 'martingale', name: 'Martingale' },
    { id: 'rsi',        name: 'RSI Scalper' },
    { id: 'trend',      name: 'Trend' },
    { id: 'news',       name: 'News Bot' },
    { id: 'vcrusher',   name: 'V-Crusher' }
  ];

  const stats = botList.map(b => {
    const trades = tradeLog.filter(t => t.botId === b.id);
    const wins   = trades.filter(t => t.result === 'won').length;
    const profit = trades.reduce((s, t) => s + t.pnl, 0);
    const wr     = trades.length > 0 ? Math.round((wins / trades.length) * 100) : 0;
    return { ...b, trades: trades.length, wins, profit, wr };
  });

  const maxProfit = Math.max(...stats.map(s => Math.abs(s.profit)), 1);

  container.innerHTML = stats.map(s => {
    const barPct = Math.abs(s.profit) / maxProfit * 100;
    const color  = s.profit >= 0 ? 'var(--green)' : 'var(--red)';
    const pStr   = (s.profit >= 0 ? '+' : '') + '$' + s.profit.toFixed(2);
    return `
      <div class="perf-row">
        <span class="perf-label">${s.name}</span>
        <div class="perf-bar-wrap">
          <div class="perf-bar" style="width:${barPct}%;background:${color}"></div>
        </div>
        <span class="perf-val" style="color:${color}">${pStr}</span>
      </div>
      <div class="perf-row" style="margin-top:-6px;margin-bottom:12px">
        <span class="perf-label" style="font-size:9px;color:var(--text3)">${s.trades} trades</span>
        <div class="perf-bar-wrap">
          <div class="perf-bar" style="width:${s.wr}%;background:var(--accent2)"></div>
        </div>
        <span class="perf-val" style="color:var(--accent2);font-size:10px">${s.wr}% WR</span>
      </div>
    `;
  }).join('');
}
