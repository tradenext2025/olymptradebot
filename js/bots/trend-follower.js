// ── TREND FOLLOWER BOT — FULL ENGINE ──

function startTrendFollower() {
  const cfg = {
    market:         document.getElementById('tr-market').value,
    contractFamily: document.getElementById('tr-contract-family').value,
    stake:          parseFloat(document.getElementById('tr-stake').value),
    emaFast:        parseInt(document.getElementById('tr-ema-fast').value),
    emaSlow:        parseInt(document.getElementById('tr-ema-slow').value),
    minADX:         parseInt(document.getElementById('tr-adx').value),
    duration:       parseInt(document.getElementById('tr-duration').value),
    takeProfit:     parseFloat(document.getElementById('tr-takeprofit').value),
    stopLoss:       parseFloat(document.getElementById('tr-stoploss').value),
    breakout:       document.getElementById('tr-breakout').value,
    reentry:        document.getElementById('tr-reentry').value,
    minConfidence:  parseInt(document.getElementById('tr-confidence').value),
    autoSwitch:     document.getElementById('tr-autoswitch').value === 'on'
  };

  const state = {
    running:        true,
    trades:         0,
    wins:           0,
    profit:         0,
    tradeOpen:      false,
    currentMarket:  cfg.market,
    tickPrices:     [],
    tickCount:      0,
    lastTickTime:   0,
    tickSpeed:      0,
    lastEmaFast:    null,
    lastEmaSlow:    null,
    crossover:      null,
    trendDir:       '--',
    cooldown:       0,
    waitCrossover:  false,
    lastResult:     null
  };

  // ── TREND DETECTION ──
  function detectTrend() {
    const prices = state.tickPrices;
    if (prices.length < cfg.emaSlow + 5) return null;

    const emaF   = calcEMA(prices, cfg.emaFast);
    const emaS   = calcEMA(prices, cfg.emaSlow);
    const adx    = calcADX(prices, 14);
    const boll   = calcBollinger(prices, 20);
    const last   = prices[prices.length-1];

    // Detect crossover
    let crossoverSignal = null;
    if (state.lastEmaFast !== null && state.lastEmaSlow !== null) {
      const wasBullish = state.lastEmaFast > state.lastEmaSlow;
      const isBullish  = emaF > emaS;
      if (!wasBullish && isBullish)  crossoverSignal = 'CALL';
      if (wasBullish  && !isBullish) crossoverSignal = 'PUT';
    }

    state.lastEmaFast = emaF;
    state.lastEmaSlow = emaS;

    // Trend direction
    state.trendDir = emaF > emaS ? '▲ UP' : '▼ DOWN';

    // ADX filter
    if (adx < cfg.minADX) return null;

    // Breakout filter
    if (cfg.breakout === 'on') {
      const squeeze = boll.std / boll.mid < 0.005;
      const breakingUp   = last > boll.upper;
      const breakingDown = last < boll.lower;
      if (!breakingUp && !breakingDown) return null;
    }

    // Confidence score
    let confidence = 0;
    if (emaF > emaS)  confidence += 35;
    else              confidence += 35;
    if (adx > 40)     confidence += 30;
    else if (adx > cfg.minADX) confidence += 15;
    if (crossoverSignal) confidence += 35;

    const direction = emaF > emaS ? 'CALL' : 'PUT';

    return {
      type:         direction,
      crossover:    crossoverSignal,
      emaFast:      emaF,
      emaSlow:      emaS,
      adx:          adx,
      confidence:   Math.min(confidence, 100)
    };
  }

  // ── BUILD TRADE PARAMS ──
  function buildTradeParams(signal) {
    const sym  = state.currentMarket;
    const base = { symbol: sym, stake: cfg.stake, duration: cfg.duration };

    switch(cfg.contractFamily) {
      case 'RISE_FALL':
        return { ...base, contract_type: signal.type };

      case 'MATCHES': {
        const s = getSignal(sym, 'MATCHES');
        return { ...base, contract_type: s.type, barrier: String(s.digit) };
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
      showToast(`Trend Follower TP hit! +$${state.profit.toFixed(2)}`, 'success');
      stopBot('trend');
      return false;
    }
    if (state.profit <= -cfg.stopLoss) {
      showToast(`Trend Follower SL hit! $${state.profit.toFixed(2)}`, 'error');
      stopBot('trend');
      return false;
    }
    return true;
  }

  // ── RE-ENTRY LOGIC ──
  function canReenter(result) {
    if (cfg.reentry === 'immediate') return true;
    if (cfg.reentry === 'cooldown') {
      state.cooldown = 5;
      return false;
    }
    if (cfg.reentry === 'wait') {
      if (!result.won) {
        state.waitCrossover = true;
        return false;
      }
      return true;
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
    if (state.tickPrices.length > 300) state.tickPrices.shift();

    if (state.cooldown > 0) state.cooldown--;

    // Update stats every tick
    updateBotStats('trend', {
      trades:    state.trades,
      wins:      state.wins,
      profit:    state.profit,
      trend:     state.trendDir,
      tickSpeed: state.tickSpeed
    });

    // Auto market switch every 50 ticks
    if (cfg.autoSwitch && state.tickCount % 50 === 0) {
      const best = getBestMarket();
      if (best.symbol &&
          best.symbol !== state.currentMarket &&
          best.score > (marketScores[state.currentMarket] || 0) + 20) {
        unsubscribeTicks(state.currentMarket, tickHandler);
        state.currentMarket = best.symbol;
        state.tickPrices    = [];
        state.lastEmaFast   = null;
        state.lastEmaSlow   = null;
        state.waitCrossover = false;
        subscribeTicks(best.symbol, tickHandler);
        showToast(
          `Trend → ${MARKET_LABELS[best.symbol]} (score:${best.score})`,
          'success'
        );
      }
    }

    // Attempt trade
    if (!state.tradeOpen &&
        state.cooldown === 0 &&
        !state.waitCrossover &&
        state.running) {
      const signal = detectTrend();
      if (signal && signal.confidence >= cfg.minConfidence) {
        // If waiting for crossover, only trade on actual crossover
        if (state.waitCrossover && !signal.crossover) return;
        state.waitCrossover = false;
        attemptTrade(signal);
      }
    }

    // Reset waitCrossover when new crossover detected
    if (state.waitCrossover) {
      const signal = detectTrend();
      if (signal && signal.crossover) {
        state.waitCrossover = false;
      }
    }
  };

  // ── TRADE ──
  function attemptTrade(signal) {
    if (!state.running || state.tradeOpen) return;
    if (!checkLimits()) return;

    const params    = buildTradeParams(signal);
    state.tradeOpen = true;

    placeTrade(params, (result) => {
      state.tradeOpen = false;
      if (result.error) {
        showToast('Trend trade error: ' + result.error, 'error');
        state.cooldown = 5;
        return;
      }

      state.trades++;
      const won = result.won;
      if (won) {
        state.wins++;
        state.profit = parseFloat((state.profit + result.profit).toFixed(2));
      } else {
        state.profit = parseFloat((state.profit + result.profit).toFixed(2));
      }

      state.lastResult = { won };

      logTrade('trend', state.currentMarket,
        params.contract_type, params.stake,
        won ? 'won' : 'lost', result.profit);

      updateBotStats('trend', {
        trades:    state.trades,
        wins:      state.wins,
        profit:    state.profit,
        trend:     state.trendDir,
        tickSpeed: state.tickSpeed
      });

      canReenter(result);
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
