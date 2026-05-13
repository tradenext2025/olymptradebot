// ── GLOBAL MARKET SCANNER & SIGNAL ENGINE ──

const MARKET_LABELS = {
  R_10:      'Volatility 10',
  R_25:      'Volatility 25',
  R_50:      'Volatility 50',
  R_75:      'Volatility 75',
  R_100:     'Volatility 100',
  BOOM1000:  'Boom 1000',
  BOOM500:   'Boom 500',
  CRASH1000: 'Crash 1000',
  CRASH500:  'Crash 500',
  stpRNG:    'Step Index',
  JD10:      'Jump 10',
  JD25:      'Jump 25',
  JD50:      'Jump 50',
  JD75:      'Jump 75',
  JD100:     'Jump 100',
  RDBULL:    'Range Break Bull',
  RDBEAR:    'Range Break Bear'
};

// Per-market tick buffers
const marketBuffers = {};
const marketTickTimes = {};
const marketScores = {};

// User watchlist (set by settings)
let userWatchlist = ['R_75', 'R_100', 'R_50'];

function setWatchlist(list) {
  userWatchlist = list;
  initScannerBuffers();
}

function initScannerBuffers() {
  userWatchlist.forEach(sym => {
    if (!marketBuffers[sym]) {
      marketBuffers[sym]   = [];
      marketTickTimes[sym] = [];
      marketScores[sym]    = 0;
      subscribeTicks(sym, (tick) => onScannerTick(sym, tick));
    }
  });
}

function onScannerTick(sym, tick) {
  const buf = marketBuffers[sym];
  buf.push(tick.quote);
  if (buf.length > 200) buf.shift();

  const now = Date.now();
  marketTickTimes[sym] = marketTickTimes[sym] || [];
  marketTickTimes[sym].push(now);
  if (marketTickTimes[sym].length > 20) marketTickTimes[sym].shift();

  // Rescore every 10 ticks
  if (buf.length % 10 === 0) {
    marketScores[sym] = scoreMarket(sym);
  }
}

// ── TICK SPEED ──
function getTickSpeed(sym) {
  const times = marketTickTimes[sym];
  if (!times || times.length < 2) return null;
  const diffs = [];
  for (let i = 1; i < times.length; i++) {
    diffs.push(times[i] - times[i-1]);
  }
  const avg = diffs.reduce((a,b) => a+b, 0) / diffs.length;
  return Math.round(avg); // ms per tick
}

// ── MARKET SCORER ──
// Returns 0-100 score: higher = better trading conditions
function scoreMarket(sym) {
  const buf = marketBuffers[sym];
  if (buf.length < 20) return 0;

  let score = 0;

  // 1. Volatility score (we want some, not too much)
  const atr = calcATR(buf, 14);
  const pct  = (atr / buf[buf.length-1]) * 100;
  if (pct > 0.05 && pct < 2.0) score += 30;
  else if (pct >= 2.0)          score += 10;
  else                           score += 5;

  // 2. Trend clarity (EMA separation)
  const emaF = calcEMA(buf, 9);
  const emaS = calcEMA(buf, 21);
  const sep   = Math.abs(emaF - emaS) / emaS * 100;
  if (sep > 0.02) score += 25;
  else            score += 10;

  // 3. RSI not stuck in middle
  const rsi = calcRSIFromBuf(buf, 14);
  if (rsi < 35 || rsi > 65) score += 25;
  else if (rsi < 45 || rsi > 55) score += 12;
  else score += 0;

  // 4. Tick speed (faster = more opportunities)
  const speed = getTickSpeed(sym);
  if (speed && speed < 500)       score += 20;
  else if (speed && speed < 1500) score += 10;
  else                            score += 5;

  return Math.min(score, 100);
}

// ── BEST MARKET ──
function getBestMarket() {
  let best = null, bestScore = -1;
  userWatchlist.forEach(sym => {
    const s = marketScores[sym] || 0;
    if (s > bestScore) { bestScore = s; best = sym; }
  });
  return { symbol: best, score: bestScore };
}

// ── SIGNAL ENGINE ──
// Returns best signal for given contract type family
function getSignal(sym, contractFamily) {
  const buf = marketBuffers[sym];
  if (!buf || buf.length < 30) return null;

  switch(contractFamily) {
    case 'RISE_FALL':    return signalRiseFall(buf);
    case 'MATCHES':      return signalMatchesDiffers(buf);
    case 'EVEN_ODD':     return signalEvenOdd(buf);
    case 'OVER_UNDER':   return signalOverUnder(buf);
    case 'TOUCH':        return signalTouch(buf);
    default:             return signalRiseFall(buf);
  }
}

function signalRiseFall(buf) {
  const rsi  = calcRSIFromBuf(buf, 14);
  const emaF = calcEMA(buf, 9);
  const emaS = calcEMA(buf, 21);
  const last = buf[buf.length-1];
  const prev = buf[buf.length-2];

  let score = 0, direction = null;

  // RSI signal
  if (rsi < 30)      { score += 40; direction = 'CALL'; }
  else if (rsi > 70) { score += 40; direction = 'PUT'; }
  else if (rsi < 45) { score += 20; direction = 'CALL'; }
  else if (rsi > 55) { score += 20; direction = 'PUT'; }

  // EMA crossover
  if (emaF > emaS) {
    score += 30;
    if (!direction || direction === 'CALL') direction = 'CALL';
  } else {
    score += 30;
    if (!direction || direction === 'PUT') direction = 'PUT';
  }

  // Momentum
  const momentum = last - buf[buf.length-5];
  if (momentum > 0 && direction === 'CALL') score += 30;
  if (momentum < 0 && direction === 'PUT')  score += 30;

  return { type: direction, confidence: Math.min(score, 100) };
}

function signalMatchesDiffers(buf) {
  // Predict last digit
  const lastDigits = buf.slice(-20).map(p => {
    const s = p.toFixed(2);
    return parseInt(s[s.length-1]);
  });
  const freq = Array(10).fill(0);
  lastDigits.forEach(d => freq[d]++);
  const minDigit = freq.indexOf(Math.min(...freq));
  const maxDigit = freq.indexOf(Math.max(...freq));

  // DIFFERS on most frequent digit (likely to not repeat)
  // MATCHES on least frequent digit (due for appearance)
  return {
    type:       'DIFFERS',
    digit:      maxDigit,
    altType:    'MATCHES',
    altDigit:   minDigit,
    confidence: 60 + Math.round((Math.max(...freq) / 20) * 40)
  };
}

function signalEvenOdd(buf) {
  const lastDigits = buf.slice(-30).map(p => {
    const s = p.toFixed(2);
    return parseInt(s[s.length-1]);
  });
  const evens = lastDigits.filter(d => d % 2 === 0).length;
  const odds  = lastDigits.length - evens;
  // Predict opposite of dominant recent
  const type  = evens > odds ? 'ODD' : 'EVEN';
  const conf  = 50 + Math.round(Math.abs(evens - odds) / lastDigits.length * 50);
  return { type, confidence: conf };
}

function signalOverUnder(buf) {
  const last = buf[buf.length-1];
  const s    = last.toFixed(2);
  const d    = parseInt(s[s.length-1]);
  // Over 4 or Under 5 based on last 20 digit average
  const digits = buf.slice(-20).map(p => {
    const ps = p.toFixed(2);
    return parseInt(ps[ps.length-1]);
  });
  const avg = digits.reduce((a,b) => a+b, 0) / digits.length;
  const type = avg > 4.5 ? 'UNDER' : 'OVER';
  const conf = 50 + Math.round(Math.abs(avg - 4.5) * 10);
  return { type, barrier: 4, confidence: Math.min(conf, 90) };
}

function signalTouch(buf) {
  const atr  = calcATR(buf, 14);
  const last = buf[buf.length-1];
  const rsi  = calcRSIFromBuf(buf, 14);
  // Touch: high volatility expected
  // No Touch: low volatility expected
  const type = atr / last > 0.005 ? 'TOUCH' : 'NOTOUCH';
  return { type, confidence: 60 };
}

// ── MATH HELPERS ──
function calcEMA(prices, period) {
  if (prices.length < period) return prices[prices.length-1];
  const k = 2 / (period + 1);
  let ema  = prices.slice(0, period).reduce((a,b) => a+b, 0) / period;
  for (let i = period; i < prices.length; i++) {
    ema = prices[i] * k + ema * (1 - k);
  }
  return ema;
}

function calcRSIFromBuf(prices, period = 14) {
  if (prices.length < period + 1) return 50;
  let gains = 0, losses = 0;
  for (let i = prices.length - period; i < prices.length; i++) {
    const diff = prices[i] - prices[i-1];
    if (diff > 0) gains  += diff;
    else          losses -= diff;
  }
  const ag = gains / period;
  const al = losses / period;
  if (al === 0) return 100;
  return 100 - (100 / (1 + ag/al));
}

function calcATR(prices, period = 14) {
  if (prices.length < period + 1) return 0;
  const trs = [];
  for (let i = 1; i < prices.length; i++) {
    trs.push(Math.abs(prices[i] - prices[i-1]));
  }
  return trs.slice(-period).reduce((a,b) => a+b, 0) / period;
}

function calcBollinger(prices, period = 20) {
  if (prices.length < period) return { upper: 0, lower: 0, mid: 0 };
  const slice = prices.slice(-period);
  const mid   = slice.reduce((a,b) => a+b, 0) / period;
  const std   = Math.sqrt(slice.map(p => (p-mid)**2).reduce((a,b) => a+b, 0) / period);
  return { upper: mid + 2*std, lower: mid - 2*std, mid, std };
}

function calcADX(prices, period = 14) {
  if (prices.length < period * 2) return 0;
  // Simplified ADX using price direction changes
  let trending = 0;
  for (let i = prices.length - period; i < prices.length; i++) {
    const prev2 = prices[i-2] || prices[i-1];
    if ((prices[i] > prices[i-1] && prices[i-1] > prev2) ||
        (prices[i] < prices[i-1] && prices[i-1] < prev2)) {
      trending++;
    }
  }
  return Math.round((trending / period) * 100);
}

// ── WATCHLIST SETTINGS UI ──
function buildWatchlistUI(containerId) {
  const all = Object.keys(MARKET_LABELS);
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = `
    <div style="font-size:10px;color:var(--text2);margin-bottom:6px;text-transform:uppercase;letter-spacing:1px">
      Scanner Watchlist
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:6px">
      ${all.map(sym => `
        <label style="display:flex;align-items:center;gap:4px;font-size:11px;
          background:var(--surface2);border:1px solid var(--border2);
          padding:4px 8px;border-radius:20px;cursor:pointer">
          <input type="checkbox" value="${sym}"
            ${userWatchlist.includes(sym) ? 'checked' : ''}
            onchange="updateWatchlist()"
            style="accent-color:var(--accent)"/>
          ${MARKET_LABELS[sym]}
        </label>
      `).join('')}
    </div>
    <div style="margin-top:8px;font-size:10px;color:var(--text3)">
      Scanner scores each market every 10 ticks · Auto-switches to highest scoring market
    </div>
  `;
}

function updateWatchlist() {
  const checked = [...document.querySelectorAll('[onchange="updateWatchlist()"]:checked')];
  userWatchlist = checked.map(el => el.value);
  if (userWatchlist.length === 0) {
    userWatchlist = ['R_75'];
    showToast('Need at least 1 market in watchlist', 'warn');
  }
  initScannerBuffers();
  showToast(`Watchlist updated: ${userWatchlist.length} markets`, 'success');
}

// Init on load
window.addEventListener('load', () => {
  setTimeout(initScannerBuffers, 500);
});

// ── RESOLVE CONTRACT FAMILY FROM SELECTION ──
function resolveContractFamily(val) {
  if (val.startsWith('RISE_FALL')) return 'RISE_FALL';
  if (val.startsWith('MATCHES') || val.startsWith('DIFFERS')) return 'MATCHES';
  if (val.startsWith('EVEN_ODD')) return 'EVEN_ODD';
  if (val.startsWith('OVER_UNDER')) return 'OVER_UNDER';
  if (val.startsWith('TOUCH')) return 'TOUCH';
  return 'RISE_FALL';
}

// ── RESOLVE EXACT CONTRACT TYPE ──
function resolveContractType(val, signal) {
  // Rise/Fall
  if (val === 'RISE_FALL_CALL') return 'CALL';
  if (val === 'RISE_FALL_PUT')  return 'PUT';
  if (val === 'RISE_FALL_AUTO') return signal && signal.type ? signal.type : 'CALL';

  // Matches/Differs
  if (val === 'MATCHES_AUTO')  return 'MATCHES';
  if (val === 'DIFFERS_AUTO')  return 'DIFFERS';

  // Even/Odd
  if (val === 'EVEN_ODD_AUTO') return signal && signal.eoType ? signal.eoType : 'EVEN';
  if (val === 'EVEN_ODD_EVEN') return 'EVEN';
  if (val === 'EVEN_ODD_ODD')  return 'ODD';

  // Over/Under
  if (val === 'OVER_UNDER_AUTO')  return signal && signal.ouType === 'UNDER' ? 'DIGITUNDER' : 'DIGITOVER';
  if (val === 'OVER_UNDER_OVER')  return 'DIGITOVER';
  if (val === 'OVER_UNDER_UNDER') return 'DIGITUNDER';

  // Touch
  if (val === 'TOUCH_AUTO')    return 'ONETOUCH';
  if (val === 'TOUCH_TOUCH')   return 'ONETOUCH';
  if (val === 'TOUCH_NOTOUCH') return 'NOTOUCH';

  return 'CALL';
}
