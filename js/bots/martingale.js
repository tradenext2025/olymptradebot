// ── MARTINGALE PRO BOT — FULL ENGINE ──

function startMartingale() {
  const cfg = {
    market:        document.getElementById('mg-market').value,
    contractFamily:document.getElementById('mg-contract-family').value,
    stake:         parseFloat(document.getElementById('mg-stake').value),
    multiplier:    parseFloat(document.getElementById('mg-multiplier').value),
    duration:      parseInt(document.getElementById('mg-duration').value),
    maxStake:      parseFloat(document.getElementById('mg-maxstake').value),
    takeProfit:    parseFloat(document.getElementById('mg-takeprofit').value),
    stopLoss:      parseFloat(document.getElementById('mg-stoploss').value),
    maxStreak:     parseInt(document.getElementById('mg-maxstreak').value),
    recovery:      document.getElementById('mg-recovery').value,
    minConfidence: parseInt(document.getElementById('mg-confidence').value),
    autoSwitch:    document.getElementById('mg-autoswitch').value === 'on'
  };

  const state = {
    running:      true,
    trades:       0,
    wins:         0,
    profit:       0,
    streak:       0,
    currentStake: cfg.stake,
    paused:       false,
    pauseTicks:   0,
    fibIndex:     0,
    tradeOpen:    false,
    currentMarket:cfg.market,
    lastScanTime: 0,
    tickCount:    0,
    lastTickTime: 0,
    tickSpeed:    0
  };

  const fibStakes = [1,1,2,3,5,8,13,21].map(f =>
    parseFloat(Math.min(cfg.stake * f, cfg.maxStake).toFixed(2))
  );

  // ── TICK HANDLER ──
  const tickHandler = (tick) => {
    const now = Date.now();
    if (state.lastTickTime > 0) {
      state.tickSpeed = now - state.lastTickTime;
    }
    state.lastTickTime = now;
    state.tickCount++;

    // Update tick speed display
    updateBotStats('martingale', {
      trades:    state.trades,
      wins:      state.wins,
      profit:    state.profit,
      streak:    state.streak,
      tickSpeed: state.tickSpeed
    });

    // Scan for better market every 30 ticks
    if (cfg.autoSwitch && state.tickCount % 30 === 0) {
      const best = getBestMarket();
      if (best.symbol &&
          best.symbol !== state.currentMarket &&
          best.score > (marketScores[state.currentMarket] || 0) + 20) {
        switchMarket(best.symbol, best.score);
      }
    }
  };

  function switchMarket(newSym, score) {
    unsubscribeTicks(state.currentMarket, tickHandler);
    state.currentMarket = newSym;
    subscribeTicks(newSym, tickHandler);
    showToast(
      `Martingale → ${MARKET_LABELS[newSym]} (score:${score})`, 'success'
    );
  }

  // ── STAKE LOGIC ──
  function getNextStake() {
    if (cfg.recovery === 'fibonacci') {
      return fibStakes[Math.min(state.fibIndex, fibStakes.length-1)];
    }
    if (cfg.recovery === 'double' || cfg.recovery === 'custom') {
      return parseFloat(
        Math.min(state.currentStake * cfg.multiplier, cfg.maxStake).toFixed(2)
      );
    }
    return cfg.stake;
  }

  // ── WIN / LOSS ──
  function onWin(profit) {
    state.wins++;
    state.profit       = parseFloat((state.profit + profit).toFixed(2));
    state.streak       = 0;
    state.fibIndex     = 0;
    state.currentStake = cfg.stake;
    state.paused       = false;
  }

  function onLoss(loss) {
    state.profit = parseFloat((state.profit + loss).toFixed(2));
    state.streak++;
    state.fibIndex++;
    state.currentStake = getNextStake();
    if (state.streak >= cfg.maxStreak) {
      state.paused     = true;
      state.pauseTicks = 3;
      showToast('Martingale: max streak — pausing 3 ticks', 'warn');
    }
  }

  // ── LIMITS ──
  function checkLimits() {
    if (state.profit >= cfg.takeProfit) {
      showToast(`Martingale TP hit! +$${state.profit.toFixed(2)}`, 'success');
      stopBot('martingale');
      return false;
    }
    if (state.profit <= -cfg.stopLoss) {
      showToast(`Martingale SL hit! $${state.profit.toFixed(2)}`, 'error');
      stopBot('martingale');
      return false;
    }
    return true;
  }

  // ── BUILD TRADE PARAMS ──
  function buildTradeParams(signal) {
    const sym = state.currentMarket;
    const stake = state.streak === 0 ? cfg.stake : getNextStake();
    const base = {
      symbol:   sym,
      stake:    stake,
      duration: cfg.duration
    };

    switch(cfg.contractFamily) {
      case 'RISE_FALL':
        return { ...base,
          contract_type: signal.type || 'CALL'
        };
      case 'MATCHES':
        return { ...base,
          contract_type: signal.type || 'DIFFERS',
          barrier: String(signal.digit || 0)
        };
      case 'EVEN_ODD':
        return { ...base,
          contract_type: signal.type || 'EVEN'
        };
      case 'OVER_UNDER':
        return { ...base,
          contract_type: signal.type === 'OVER' ? 'DIGITOVER' : 'DIGITUNDER',
          barrier: String(signal.barrier || 4)
        };
      case 'TOUCH':
        return { ...base,
          contract_type: signal.type === 'TOUCH' ? 'ONETOUCH' : 'NOTOUCH',
          barrier: String((
            marketBuffers[sym][marketBuffers[sym].length-1] * 1.002
          ).toFixed(2))
        };
      default:
        return { ...base, contract_type: 'CALL' };
    }
  }

  // ── MAIN CYCLE ──
  function runCycle() {
    if (!state.running || !bots.martingale.running) return;
    if (state.tradeOpen) return;

    if (state.paused) {
      state.pauseTicks--;
      if (state.pauseTicks <= 0) {
        state.paused       = false;
        state.streak       = 0;
        state.currentStake = cfg.stake;
      }
      setTimeout(runCycle, 1500);
      return;
    }

    if (!checkLimits()) return;

    // Get signal
    const signal = getSignal(state.currentMarket, cfg.contractFamily);
    if (!signal || signal.confidence < cfg.minConfidence) {
      setTimeout(runCycle, 1000);
      return;
    }

    const params = buildTradeParams(signal);
    state.tradeOpen = true;

    placeTrade(params, (result) => {
      state.tradeOpen = false;
      if (result.error) {
        showToast('Martingale trade error: ' + result.error, 'error');
        setTimeout(runCycle, 3000);
        return;
      }

      state.trades++;
      if (result.won) onWin(result.profit);
      else            onLoss(result.profit);

      logTrade('martingale', state.currentMarket,
        params.contract_type, params.stake,
        result.won ? 'won' : 'lost', result.profit);

      updateBotStats('martingale', {
        trades: state.trades, wins: state.wins,
        profit: state.profit, streak: state.streak,
        tickSpeed: state.tickSpeed
      });

      if (!checkLimits()) return;
      if (state.running && bots.martingale.running) {
        setTimeout(runCycle, 800);
      }
    });
  }

  subscribeTicks(cfg.market, tickHandler);
  initScannerBuffers();
  setTimeout(runCycle, 2500);

  return {
    stop: () => {
      state.running = false;
      unsubscribeTicks(state.currentMarket, tickHandler);
    }
  };
}
