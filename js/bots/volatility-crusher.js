// ── VOLATILITY CRUSHER BOT — FULL ENGINE ──

function startVolatilityCrusher() {
  const cfg = {
    market:         document.getElementById('vc-market').value,
    contractFamily: document.getElementById('vc-contract-family').value,
    strategy:       document.getElementById('vc-strategy').value,
    stake:          parseFloat(document.getElementById('vc-stake').value),
    atrPeriod:      parseInt(document.getElementById('vc-atr-period').value),
    atrMult:        parseFloat(document.getElementById('vc-atr-mult').value),
    digitLen:       parseInt(document.getElementById('vc-digit-len').value),
    duration:       parseInt(document.getElementById('vc-duration').value),
    takeProfit:     parseFloat(document.getElementById('vc-takeprofit').value),
    stopLoss:       parseFloat(document.getElementById('vc-stoploss').value),
    smartSizing:    document.getElementById('vc-smart').value,
    minConfidence:  parseInt(document.getElementById('vc-confidence').value),
    autoSwitch:     document.getElementById('vc-autoswitch').value === 'on'
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
    atrValue:      0,
    cooldown:      0,
    digitHistory:  [],
    momentumBuf:   [],
    lastSignals:   { atr: null, digit: null, momentum: null }
  };

  // ── KELLY CRITERION STAKE ──
  function kellyStake() {
    if (state.trades < 10) return cfg.stake;
    const wr   = state.wins / state.trades;
    const lose = 1 - wr;
    // Kelly: f = (bp - q) / b where b=payout ratio~0.95, p=winrate, q=lossrate
    const b    = 0.95;
    const kelly = (b * wr - lose) / b;
    const frac  = Math.max(0.1, Math.min(kelly * 0.5, 0.3)); // half-kelly capped at 30%
    return parseFloat(Math.max(cfg.stake, cfg.stake * (1 + frac)).toFixed(2));
  }

  function calcStake() {
    if (cfg.smartSizing === 'kelly')  return kellyStake();
    if (cfg.smartSizing === 'atr') {
      // Scale stake inversely with ATR — lower ATR = bigger stake
      const norm = Math.min(state.atrValue / (state.tickPrices[state.tickPrices.length-1] || 1), 0.02);
      const mult = 1 + (1 - norm / 0.02);
      return parseFloat(Math.min(cfg.stake * mult, cfg.stake * 2).toFixed(2));
    }
    return cfg.stake;
  }

  // ── ATR BAND SIGNAL ──
  function signalATRBand() {
    const prices = state.tickPrices;
    if (prices.length < cfg.atrPeriod + 5) return null;

    const atr  = calcATR(prices, cfg.atrPeriod);
    const last = prices[prices.length - 1];
    const mid  = calcEMA(prices, cfg.atrPeriod);
    state.atrValue = atr;

    const upper = mid + atr * cfg.atrMult;
    const lower = mid - atr * cfg.atrMult;

    let type = null, confidence = 0;

    if (last <= lower) {
      type = 'CALL'; // bounce up from lower band
      confidence = 60 + Math.round(((lower - last) / atr) * 40);
    } else if (last >= upper) {
      type = 'PUT'; // bounce down from upper band
      confidence = 60 + Math.round(((last - upper) / atr) * 40);
    }

    if (!type) return null;
    return { type, confidence: Math.min(confidence, 95), atr };
  }

  // ── DIGIT PATTERN SIGNAL ──
  function signalDigitPattern() {
    const prices = state.tickPrices;
    if (prices.length < cfg.digitLen + 5) return null;

    // Extract last digits
    const digits = prices.slice(-50).map(p => {
      const s = p.toFixed(2);
      return parseInt(s[s.length - 1]);
    });
    state.digitHistory = digits;

    // Frequency analysis
    const freq = Array(10).fill(0);
    digits.forEach(d => freq[d]++);

    // Find overdue digit (least frequent)
    const minFreq  = Math.min(...freq);
    const maxFreq  = Math.max(...freq);
    const minDigit = freq.indexOf(minFreq);
    const maxDigit = freq.indexOf(maxFreq);

    // Pattern: last N digits
    const recent = digits.slice(-cfg.digitLen);
    const recentFreq = Array(10).fill(0);
    recent.forEach(d => recentFreq[d]++);

    // Detect repeat pattern
    const lastDigit = digits[digits.length - 1];
    const repeatCount = recent.filter(d => d === lastDigit).length;

    // High repeat = DIFFERS signal
    // Low recent digit = MATCHES signal
    let type, digit, confidence;

    if (repeatCount >= Math.floor(cfg.digitLen * 0.4)) {
      type       = 'DIFFERS';
      digit      = lastDigit;
      confidence = 55 + Math.round((repeatCount / cfg.digitLen) * 40);
    } else {
      type       = 'MATCHES';
      digit      = minDigit;
      confidence = 55 + Math.round(((digits.length - minFreq) / digits.length) * 40);
    }

    // Even/Odd bias
    const evenCount = recent.filter(d => d % 2 === 0).length;
    const oddCount  = recent.length - evenCount;
    const eoType    = evenCount > oddCount ? 'ODD' : 'EVEN';
    const eoConf    = 50 + Math.round(Math.abs(evenCount - oddCount) / recent.length * 50);

    // Over/Under bias
    const overCount  = recent.filter(d => d > 4).length;
    const underCount = recent.length - overCount;
    const ouType     = overCount > underCount ? 'UNDER' : 'OVER';
    const ouConf     = 50 + Math.round(Math.abs(overCount - underCount) / recent.length * 50);

    return {
      type, digit,
      confidence: Math.min(confidence, 95),
      eoType, eoConf,
      ouType, ouConf,
      lastDigit, minDigit, maxDigit
    };
  }

  // ── MOMENTUM BURST SIGNAL ──
  function signalMomentum() {
    const prices = state.tickPrices;
    if (prices.length < 10) return null;

    const recent = prices.slice(-6);
    let upCount = 0, downCount = 0;
    for (let i = 1; i < recent.length; i++) {
      if (recent[i] > recent[i-1])      upCount++;
      else if (recent[i] < recent[i-1]) downCount++;
    }

    const rsi = calcRSIFromBuf(prices, 14);
    let type = null, confidence = 0;

    if (upCount >= 3 && rsi < 70) {
      type       = 'CALL';
      confidence = 55 + upCount * 8;
    } else if (downCount >= 3 && rsi > 30) {
      type       = 'PUT';
      confidence = 55 + downCount * 8;
    }

    if (!type) return null;
    return { type, confidence: Math.min(confidence, 90), upCount, downCount };
  }

  // ── HYBRID VOTE ──
  function signalHybrid() {
    const atr  = signalATRBand();
    const dig  = signalDigitPattern();
    const mom  = signalMomentum();

    state.lastSignals = { atr, digit: dig, momentum: mom };

    const votes = [];
    if (atr && atr.confidence >= cfg.minConfidence)  votes.push(atr);
    if (mom && mom.confidence >= cfg.minConfidence)  votes.push(mom);

    // Need 2 out of 3 agreement for RISE_FALL
    if (votes.length >= 2) {
      const callVotes = votes.filter(v => v.type === 'CALL').length;
      const putVotes  = votes.filter(v => v.type === 'PUT').length;
      if (callVotes >= 2) return { type: 'CALL', confidence: 85, source: 'hybrid' };
      if (putVotes  >= 2) return { type: 'PUT',  confidence: 85, source: 'hybrid' };
    }

    // Fall back to digit for digit-based contracts
    if (dig && dig.confidence >= cfg.minConfidence) return dig;
    return null;
  }

  // ── GET ACTIVE SIGNAL ──
  function getActiveSignal() {
    switch(cfg.strategy) {
      case 'atr':      return signalATRBand();
      case 'digit':    return signalDigitPattern();
      case 'momentum': return signalMomentum();
      case 'hybrid':   return signalHybrid();
      default:         return signalATRBand();
    }
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
        const s = signal.digit !== undefined ? signal :
                  getSignal(sym, 'MATCHES');
        return { ...base,
          contract_type: s.type || 'DIFFERS',
          barrier: String(s.digit !== undefined ? s.digit : 0)
        };
      }
      case 'EVEN_ODD': {
        const type = signal.eoType || getSignal(sym, 'EVEN_ODD').type;
        return { ...base, contract_type: type };
      }
      case 'OVER_UNDER': {
        const type = signal.ouType || 'OVER';
        return { ...base,
          contract_type: type === 'OVER' ? 'DIGITOVER' : 'DIGITUNDER',
          barrier: '4'
        };
      }
      case 'TOUCH': {
        const buf  = marketBuffers[sym] || [];
        const last = buf[buf.length-1] || 1;
        const atr  = state.atrValue || 0.001;
        return { ...base,
          contract_type: 'ONETOUCH',
          barrier: (last + atr * 1.5).toFixed(2)
        };
      }
      default:
        return { ...base, contract_type: signal.type || 'CALL' };
    }
  }

  // ── LIMITS ──
  function checkLimits() {
    if (state.profit >= cfg.takeProfit) {
      showToast(`V-Crusher TP hit! +$${state.profit.toFixed(2)}`, 'success');
      stopBot('vcrusher');
      return false;
    }
    if (state.profit <= -cfg.stopLoss) {
      showToast(`V-Crusher SL hit! $${state.profit.toFixed(2)}`, 'error');
      stopBot('vcrusher');
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
    if (state.tickPrices.length > 300) state.tickPrices.shift();

    if (state.cooldown > 0) state.cooldown--;

    // Update ATR display every tick
    if (state.tickPrices.length > cfg.atrPeriod) {
      state.atrValue = calcATR(state.tickPrices, cfg.atrPeriod);
    }

    updateBotStats('vcrusher', {
      trades:    state.trades,
      wins:      state.wins,
      profit:    state.profit,
      atr:       state.atrValue,
      tickSpeed: state.tickSpeed
    });

    // Auto market switch every 40 ticks
    if (cfg.autoSwitch && state.tickCount % 40 === 0) {
      const best = getBestMarket();
      if (best.symbol &&
          best.symbol !== state.currentMarket &&
          best.score > (marketScores[state.currentMarket] || 0) + 20) {
        unsubscribeTicks(state.currentMarket, tickHandler);
        state.currentMarket = best.symbol;
        state.tickPrices    = [];
        state.digitHistory  = [];
        subscribeTicks(best.symbol, tickHandler);
        showToast(
          `V-Crusher → ${MARKET_LABELS[best.symbol]} (score:${best.score})`,
          'success'
        );
      }
    }

    // Attempt trade
    if (!state.tradeOpen &&
        state.cooldown === 0 &&
        state.running &&
        state.tickPrices.length > 30) {
      const signal = getActiveSignal();
      if (signal && signal.confidence >= cfg.minConfidence) {
        attemptTrade(signal);
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
        showToast('V-Crusher error: ' + result.error, 'error');
        state.cooldown = 5;
        return;
      }

      state.trades++;
      const won = result.won;
      if (won) {
        state.wins++;
        state.profit = parseFloat((state.profit + result.profit).toFixed(2));
        state.cooldown = 1;
      } else {
        state.profit = parseFloat((state.profit + result.profit).toFixed(2));
        state.cooldown = 3;
      }

      logTrade('vcrusher', state.currentMarket,
        params.contract_type, params.stake,
        won ? 'won' : 'lost', result.profit);

      updateBotStats('vcrusher', {
        trades:    state.trades,
        wins:      state.wins,
        profit:    state.profit,
        atr:       state.atrValue,
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
