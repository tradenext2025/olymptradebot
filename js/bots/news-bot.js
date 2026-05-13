// ── NEWS BOT ALPHA — FULL ENGINE ──

function startNewsBot() {
  const cfg = {
    market:         document.getElementById('nw-market').value,
    contractFamily: document.getElementById('nw-contract-family').value,
    stake:          parseFloat(document.getElementById('nw-stake').value),
    mode:           document.getElementById('nw-mode').value,
    threshold:      parseFloat(document.getElementById('nw-threshold').value),
    delay:          parseInt(document.getElementById('nw-delay').value),
    duration:       parseInt(document.getElementById('nw-duration').value),
    takeProfit:     parseFloat(document.getElementById('nw-takeprofit').value),
    stopLoss:       parseFloat(document.getElementById('nw-stoploss').value),
    maxSpikes:      parseInt(document.getElementById('nw-maxspikes').value),
    cooldownTicks:  parseInt(document.getElementById('nw-cooldown').value),
    minConfidence:  parseInt(document.getElementById('nw-confidence').value),
    autoSwitch:     document.getElementById('nw-autoswitch').value === 'on'
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
    spikesDetected: 0,
    spikesThisHour: 0,
    hourTimer:      null,
    cooldown:       0,
    delayQueue:     [],
    delayCounter:   0,
    pendingSpike:   null,
    avgTickMove:    0,
    moveHistory:    []
  };

  // Reset spike counter every hour
  state.hourTimer = setInterval(() => {
    state.spikesThisHour = 0;
  }, 3600000);

  // ── SPIKE DETECTION ──
  function detectSpike(prev, curr) {
    if (!prev) return null;
    const move    = Math.abs(curr - prev);
    const movePct = (move / prev) * 100;

    // Update rolling average move
    state.moveHistory.push(movePct);
    if (state.moveHistory.length > 50) state.moveHistory.shift();
    const avgMove = state.moveHistory.reduce((a,b) => a+b, 0) /
                    state.moveHistory.length;

    // Dynamic threshold: spike must be Nx above average move
    const dynamicThresh = Math.max(cfg.threshold, avgMove * 3);

    if (movePct >= dynamicThresh) {
      return {
        direction: curr > prev ? 'UP' : 'DOWN',
        magnitude: movePct,
        avgMove:   avgMove,
        strength:  Math.min(Math.round((movePct / dynamicThresh) * 50 + 50), 100)
      };
    }
    return null;
  }

  // ── BUILD TRADE PARAMS ──
  function buildTradeParams(spike, signal) {
    const sym  = state.currentMarket;
    const base = { symbol: sym, stake: cfg.stake, duration: cfg.duration };

    // Determine rise/fall direction based on mode
    let rfType;
    if (cfg.mode === 'fade') {
      rfType = spike.direction === 'UP' ? 'PUT' : 'CALL';
    } else if (cfg.mode === 'follow') {
      rfType = spike.direction === 'UP' ? 'CALL' : 'PUT';
    } else {
      // Both — use RSI to decide
      const rsi = calcRSIFromBuf(state.tickPrices, 14);
      rfType = rsi < 50 ? 'CALL' : 'PUT';
    }

    switch(cfg.contractFamily) {
      case 'RISE_FALL':
        return { ...base, contract_type: rfType };

      case 'MATCHES': {
        const s = getSignal(sym, 'MATCHES');
        return { ...base, contract_type: s.type, barrier: String(s.digit) };
      }
      case 'EVEN_ODD': {
        // After spike, digits tend to be more random — use signal
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
        // After spike, touch is likely
        const barrier = spike.direction === 'UP'
          ? (last * 1.002).toFixed(2)
          : (last * 0.998).toFixed(2);
        return { ...base,
          contract_type: 'ONETOUCH',
          barrier
        };
      }
      default:
        return { ...base, contract_type: rfType };
    }
  }

  // ── LIMITS ──
  function checkLimits() {
    if (state.profit >= cfg.takeProfit) {
      showToast(`News Bot TP hit! +$${state.profit.toFixed(2)}`, 'success');
      stopBot('news');
      return false;
    }
    if (state.profit <= -cfg.stopLoss) {
      showToast(`News Bot SL hit! $${state.profit.toFixed(2)}`, 'error');
      stopBot('news');
      return false;
    }
    return true;
  }

  // ── EXECUTE TRADE AFTER DELAY ──
  function executeDelayedTrade(spike) {
    if (!state.running || state.tradeOpen) return;
    if (!checkLimits()) return;
    if (state.spikesThisHour >= cfg.maxSpikes) {
      showToast('News Bot: max spikes/hour reached', 'warn');
      return;
    }

    const signal = getSignal(state.currentMarket, cfg.contractFamily);
    if (!signal || signal.confidence < cfg.minConfidence) return;

    const params    = buildTradeParams(spike, signal);
    state.tradeOpen = true;

    placeTrade(params, (result) => {
      state.tradeOpen = false;
      if (result.error) {
        showToast('News Bot trade error: ' + result.error, 'error');
        state.cooldown = cfg.cooldownTicks;
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

      state.cooldown = cfg.cooldownTicks;

      logTrade('news', state.currentMarket,
        params.contract_type, params.stake,
        won ? 'won' : 'lost', result.profit);

      updateBotStats('news', {
        trades:    state.trades,
        wins:      state.wins,
        profit:    state.profit,
        spikes:    state.spikesDetected,
        tickSpeed: state.tickSpeed
      });

      checkLimits();
    });
  }

  // ── TICK HANDLER ──
  const tickHandler = (tick) => {
    const now  = Date.now();
    if (state.lastTickTime > 0) {
      state.tickSpeed = now - state.lastTickTime;
    }
    state.lastTickTime = now;
    state.tickCount++;

    const prev = state.tickPrices[state.tickPrices.length - 1] || null;
    state.tickPrices.push(tick.quote);
    if (state.tickPrices.length > 200) state.tickPrices.shift();

    if (state.cooldown > 0) state.cooldown--;

    // Delay queue countdown
    if (state.pendingSpike) {
      state.delayCounter++;
      if (state.delayCounter >= cfg.delay) {
        const spike = state.pendingSpike;
        state.pendingSpike   = null;
        state.delayCounter   = 0;
        if (state.cooldown === 0 && !state.tradeOpen) {
          executeDelayedTrade(spike);
        }
      }
    }

    // Update stats every tick
    updateBotStats('news', {
      trades:    state.trades,
      wins:      state.wins,
      profit:    state.profit,
      spikes:    state.spikesDetected,
      tickSpeed: state.tickSpeed
    });

    // Detect spike
    if (prev && state.cooldown === 0 && !state.pendingSpike) {
      const spike = detectSpike(prev, tick.quote);
      if (spike && spike.strength >= cfg.minConfidence) {
        state.spikesDetected++;
        state.spikesThisHour++;
        showToast(
          `⚡ Spike! ${spike.direction} ${spike.magnitude.toFixed(3)}% — ${MARKET_LABELS[state.currentMarket]}`,
          'warn'
        );

        if (cfg.delay === 0) {
          if (!state.tradeOpen) executeDelayedTrade(spike);
        } else {
          state.pendingSpike   = spike;
          state.delayCounter   = 0;
        }
      }
    }

    // Auto market switch every 60 ticks
    if (cfg.autoSwitch && state.tickCount % 60 === 0) {
      const best = getBestMarket();
      if (best.symbol &&
          best.symbol !== state.currentMarket &&
          best.score > (marketScores[state.currentMarket] || 0) + 20) {
        unsubscribeTicks(state.currentMarket, tickHandler);
        state.currentMarket  = best.symbol;
        state.tickPrices     = [];
        state.pendingSpike   = null;
        state.moveHistory    = [];
        subscribeTicks(best.symbol, tickHandler);
        showToast(
          `News Bot → ${MARKET_LABELS[best.symbol]} (score:${best.score})`,
          'success'
        );
      }
    }
  };

  subscribeTicks(cfg.market, tickHandler);
  initScannerBuffers();

  return {
    stop: () => {
      state.running = false;
      clearInterval(state.hourTimer);
      unsubscribeTicks(state.currentMarket, tickHandler);
    }
  };
}
