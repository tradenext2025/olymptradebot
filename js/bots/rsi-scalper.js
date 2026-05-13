// ── RSI SCALPER BOT — FULL ENGINE ──

function startRSIScalper() {
  const cfg = {
    market:         document.getElementById('rsi-market').value,
    contractFamily: document.getElementById('rsi-contract-family').value,
    stake:          parseFloat(document.getElementById('rsi-stake').value),
    period:         parseInt(document.getElementById('rsi-period').value),
    oversold:       parseInt(document.getElementById('rsi-oversold').value),
    overbought:     parseInt(document.getElementById('rsi-overbought').value),
    duration:       parseInt(document.getElementById('rsi-duration').value),
    takeProfit:     parseFloat(document.getElementById('rsi-takeprofit').value),
    stopLoss:       parseFloat(document.getElementById('rsi-stoploss').value),
    confirmTicks:   parseInt(document.getElementById('rsi-confirm').value),
    dynamic:        document.getElementById('rsi-dynamic').value,
    minConfidence:  parseInt(document.getElementById('rsi-confidence').value),
    autoSwitch:     document.getElementById('rsi-autoswitch').value === 'on'
  };

  const state = {
    running:       true,
    trades:        0,
    wins:          0,
    profit:        0,
    tradeOpen:     false,
    currentMarket: cfg.market,
    tickPrices:    [],
    tickCount:     0,
    lastTickTime:  0,
    tickSpeed:     0,
    confirmCount:  0,
    pendingSignal: null,
    rsiValue:      50,
    cooldown:      0
  };

  // ── DYNAMIC STAKE ──
  function calcStake() {
    if (cfg.dynamic === 'fixed') return cfg.stake;
    if (cfg.dynamic === 'rsi') {
      // Stronger RSI deviation = bigger stake
      const dev = Math.abs(state.rsiValue - 50);
      const mult = 1 + (dev / 50);
      return parseFloat(Math.min(cfg.stake * mult, cfg.stake * 3).toFixed(2));
    }
    if (cfg.dynamic === 'winrate') {
      const wr = state.trades > 0 ? state.wins / state.trades : 0.5;
      const mult = 0.5 + wr;
      return parseFloat(Math.min(cfg.stake * mult, cfg.stake * 2).toFixed(2));
    }
    return cfg.stake;
  }

  // ── BUILD TRADE PARAMS ──
  function buildTradeParams(signal) {
    const sym   = state.currentMarket;
    const stake = calcStake();
    const base  = { symbol: sym, stake, duration: cfg.duration };

    switch(cfg.contractFamily) {
      case 'RISE_FALL':
        return { ...base, contract_type: signal.type || 'CALL' };

      case 'MATCHES': {
        const s = getSignal(sym, 'MATCHES');
        return { ...base,
          contract_type: s.type,
          barrier: String(s.digit)
        };
      }
      case 'EVEN_ODD': {
        const s = getSignal(sym, 'EVEN_ODD');
        return { ...base, contract_type: s.type };
      }
      case 'OVER_UNDER': {
        const s = getSignal(sym, 'OVER_UNDER');
        return { ...base,
          contract_type: s.type === 'OVER' ? 'DIGITOVER' : 'DIGITUNDER',
          barrier: String(s.barrier || 4)
        };
      }
      case 'TOUCH': {
        const buf  = marketBuffers[sym] || [];
        const last = buf[buf.length-1] || 1;
        const s    = getSignal(sym, 'TOUCH');
        return { ...base,
          contract_type: s.type === 'TOUCH' ? 'ONETOUCH' : 'NOTOUCH',
          barrier: (last * 1.003).toFixed(2)
        };
      }
      default:
        return { ...base, contract_type: 'CALL' };
    }
  }

  // ── LIMITS ──
  function checkLimits() {
    if (state.profit >= cfg.takeProfit) {
      showToast(`RSI Scalper TP hit! +$${state.profit.toFixed(2)}`, 'success');
      stopBot('rsi');
      return false;
    }
    if (state.profit <= -cfg.stopLoss) {
      showToast(`RSI Scalper SL hit! $${state.profit.toFixed(2)}`, 'error');
      stopBot('rsi');
      return false;
    }
    return true;
  }

  // ── TICK HANDLER ──
  const tickHandler = (tick) => {
    const now = Date.now();
    if (state.lastTickTime > 0) {
      state.tickSpeed = now - state.lastTickTime;
    }
    state.lastTickTime = now;
    state.tickCount++;

    state.tickPrices.push(tick.quote);
    if (state.tickPrices.length > 200) state.tickPrices.shift();

    // Update RSI display every tick
    if (state.tickPrices.length >= cfg.period + 1) {
      state.rsiValue = calcRSIFromBuf(state.tickPrices, cfg.period);
      updateBotStats('rsi', {
        trades:    state.trades,
        wins:      state.wins,
        profit:    state.profit,
        rsiValue:  state.rsiValue,
        tickSpeed: state.tickSpeed
      });
    }

    // Signal confirmation logic
    if (cfg.contractFamily === 'RISE_FALL') {
      const sig = getSignal(state.currentMarket, 'RISE_FALL');
      if (sig && sig.confidence >= cfg.minConfidence) {
        if (!state.pendingSignal) {
          state.pendingSignal  = sig;
          state.confirmCount   = 1;
        } else if (state.pendingSignal.type === sig.type) {
          state.confirmCount++;
        } else {
          // Signal flipped — reset
          state.pendingSignal = sig;
          state.confirmCount  = 1;
        }
      } else {
        state.pendingSignal = null;
        state.confirmCount  = 0;
      }
    }

    // Cooldown countdown
    if (state.cooldown > 0) state.cooldown--;

    // Auto market switch every 40 ticks
    if (cfg.autoSwitch && state.tickCount % 40 === 0) {
      const best = getBestMarket();
      if (best.symbol &&
          best.symbol !== state.currentMarket &&
          best.score > (marketScores[state.currentMarket] || 0) + 20) {
        unsubscribeTicks(state.currentMarket, tickHandler);
        state.currentMarket = best.symbol;
        state.tickPrices    = [];
        state.pendingSignal = null;
        state.confirmCount  = 0;
        subscribeTicks(best.symbol, tickHandler);
        showToast(
          `RSI Scalper → ${MARKET_LABELS[best.symbol]} (score:${best.score})`,
          'success'
        );
      }
    }

    // Attempt trade if confirmed and no cooldown
    if (!state.tradeOpen &&
        state.cooldown === 0 &&
        state.confirmCount >= cfg.confirmTicks &&
        state.running) {
      attemptTrade();
    }
  };

  // ── TRADE ──
  function attemptTrade() {
    if (!state.running || state.tradeOpen) return;
    if (!checkLimits()) return;

    // Override: check global signal confidence
    const signal = state.pendingSignal ||
                   getSignal(state.currentMarket, cfg.contractFamily);
    if (!signal || signal.confidence < cfg.minConfidence) return;

    const params    = buildTradeParams(signal);
    state.tradeOpen = true;
    state.pendingSignal = null;
    state.confirmCount  = 0;

    placeTrade(params, (result) => {
      state.tradeOpen = false;
      if (result.error) {
        showToast('RSI trade error: ' + result.error, 'error');
        state.cooldown = 5;
        return;
      }

      state.trades++;
      if (result.won) {
        state.wins++;
        state.profit = parseFloat((state.profit + result.profit).toFixed(2));
        state.cooldown = 2;
      } else {
        state.profit = parseFloat((state.profit + result.profit).toFixed(2));
        state.cooldown = 3;
      }

      logTrade('rsi', state.currentMarket,
        params.contract_type, params.stake,
        result.won ? 'won' : 'lost', result.profit);

      updateBotStats('rsi', {
        trades:    state.trades,
        wins:      state.wins,
        profit:    state.profit,
        rsiValue:  state.rsiValue,
        tickSpeed: state.tickSpeed
      });

      checkLimits();
    });
  }

  subscribeTicks(cfg.market, tickHandler);
  initScannerBuffers();

  return {
    stop: () => {
      state.running = false;
      unsubscribeTicks(state.currentMarket, tickHandler);
    }
  };
}
