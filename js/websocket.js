// ── DERIV WEBSOCKET ENGINE ──
const DERIV_WS_URL = 'wss://ws.binaryws.com/websockets/v3?app_id=1089';

let ws = null;
let apiToken = '';
let isConnected = false;
let reconnectTimer = null;
let reconnectAttempts = 0;
const MAX_RECONNECT = 5;

// Tick subscribers: { symbol: [callbacks] }
const tickSubscribers = {};
// Contract subscribers: { contractId: callback }
const contractSubscribers = {};
// Pending requests: { reqId: callback }
const pendingRequests = {};
let reqId = 1;

function getReqId() { return reqId++; }

// ── CONNECT ──
function connectDeriv() {
  apiToken = document.getElementById('apiTokenInput').value.trim();
  if (!apiToken) {
    showToast('Please enter your Deriv API token', 'error');
    return;
  }
  if (ws && ws.readyState === WebSocket.OPEN) {
    showToast('Already connected', 'warn');
    return;
  }
  setConnStatus('connecting');
  ws = new WebSocket(DERIV_WS_URL);

  ws.onopen = () => {
    reconnectAttempts = 0;
    authorize();
  };

  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    handleMessage(msg);
  };

  ws.onerror = () => {
    setConnStatus('disconnected');
    showToast('WebSocket error', 'error');
  };

  ws.onclose = () => {
    isConnected = false;
    setConnStatus('disconnected');
    showToast('Disconnected from Deriv', 'warn');
    killAllBots();
    tryReconnect();
  };
}

// ── AUTHORIZE ──
function authorize() {
  send({ authorize: apiToken, req_id: getReqId() }, (resp) => {
    if (resp.error) {
      showToast('Auth failed: ' + resp.error.message, 'error');
      setConnStatus('disconnected');
      ws.close();
      return;
    }
    isConnected = true;
    setConnStatus('connected');
    showToast('Connected as ' + resp.authorize.loginid, 'success');
    fetchBalance();
    document.getElementById('connectBtn').textContent = 'Connected';
    // Start ticker subscriptions
    subscribeTickerBar();
  });
}

// ── SEND ──
function send(payload, callback) {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    showToast('Not connected to Deriv', 'error');
    return;
  }
  if (callback && payload.req_id) {
    pendingRequests[payload.req_id] = callback;
  }
  ws.send(JSON.stringify(payload));
}

// ── MESSAGE ROUTER ──
function handleMessage(msg) {
  // Pending request callbacks
  if (msg.req_id && pendingRequests[msg.req_id]) {
    const cb = pendingRequests[msg.req_id];
    delete pendingRequests[msg.req_id];
    cb(msg);
    return;
  }

  // Tick stream
  if (msg.msg_type === 'tick') {
    const sym = msg.tick.symbol;
    const tick = {
      symbol: sym,
      quote: msg.tick.quote,
      epoch: msg.tick.epoch
    };
    updateTickerBar(sym, tick.quote);
    if (tickSubscribers[sym]) {
      tickSubscribers[sym].forEach(cb => cb(tick));
    }
    handleBalanceUpdate(msg);
  // Analysis live chart
    if (typeof onAnalysisTick === 'function') onAnalysisTick(tick);
    return;
  }

  // Contract updates
  if (msg.msg_type === 'proposal_open_contract') {
    const poc = msg.proposal_open_contract;
    if (poc && contractSubscribers[poc.contract_id]) {
      contractSubscribers[poc.contract_id](poc);
    }
    return;
  }

  // Buy response
  if (msg.msg_type === 'buy') {
    if (msg.req_id && pendingRequests[msg.req_id]) {
      pendingRequests[msg.req_id](msg);
      delete pendingRequests[msg.req_id];
    }
    return;
  }
}

// ── SUBSCRIBE TICKS ──
function subscribeTicks(symbol, callback) {
  if (!tickSubscribers[symbol]) {
    tickSubscribers[symbol] = [];
    const id = getReqId();
    send({ ticks: symbol, subscribe: 1, req_id: id });
  }
  tickSubscribers[symbol].push(callback);
}

function unsubscribeTicks(symbol, callback) {
  if (!tickSubscribers[symbol]) return;
  tickSubscribers[symbol] = tickSubscribers[symbol].filter(cb => cb !== callback);
}

// ── GET PRICE PROPOSAL ──
function getProposal(params, callback) {
  const id = getReqId();
  const payload = {
    proposal: 1,
    req_id: id,
    amount: params.amount,
    basis: 'stake',
    contract_type: params.contract_type,
    currency: 'USD',
    duration: params.duration,
    duration_unit: 't',
    symbol: params.symbol
  };
  send(payload, callback);
}

// ── BUY CONTRACT ──
function buyContract(proposalId, price, callback) {
  const id = getReqId();
  send({ buy: proposalId, price: price, req_id: id }, callback);
}

// ── SUBSCRIBE TO OPEN CONTRACT ──
function subscribeContract(contractId, callback) {
  contractSubscribers[contractId] = callback;
  send({
    proposal_open_contract: 1,
    contract_id: contractId,
    subscribe: 1,
    req_id: getReqId()
  });
}

function unsubscribeContract(contractId) {
  delete contractSubscribers[contractId];
}

// ── FULL TRADE FLOW ──
// Bots call this: placeTrade({ symbol, contract_type, stake, duration }, callback)
// callback({ won, profit, payout, entry, exit })
function placeTrade(params, callback) {
  if (!isConnected) {
    showToast('Not connected — cannot place trade', 'error');
    return;
  }
  getProposal({
    symbol: params.symbol,
    contract_type: params.contract_type,
    amount: params.stake,
    duration: params.duration
  }, (propResp) => {
    if (propResp.error) {
      showToast('Proposal error: ' + propResp.error.message, 'error');
      callback({ error: propResp.error.message });
      return;
    }
    const proposalId = propResp.proposal.id;
    const askPrice   = propResp.proposal.ask_price;

    buyContract(proposalId, askPrice, (buyResp) => {
      if (buyResp.error) {
        showToast('Buy error: ' + buyResp.error.message, 'error');
        callback({ error: buyResp.error.message });
        return;
      }
      const contractId = buyResp.buy.contract_id;
      const entrySpot  = buyResp.buy.start_time;

      subscribeContract(contractId, (poc) => {
        if (poc.is_sold) {
          unsubscribeContract(contractId);
          const won    = poc.profit >= 0;
          const profit = parseFloat(poc.profit.toFixed(2));
          callback({
            won,
            profit,
            payout: poc.payout,
            entry:  poc.entry_spot,
            exit:   poc.exit_tick
          });
        }
      });
    });
  });
}

// ── TICKER BAR ──
const tickerSymbols = {
  'R_75':     'tick-V75',
  'R_100':    'tick-V100',
  'RDBULL':   'tick-RBREAK',
  'stpRNG':   'tick-STEP',
  'BOOM1000': 'tick-BOOM',
  'CRASH1000':'tick-CRASH'
};
const tickerSymbolsB = {
  'R_75':     'tick-V75b',
  'R_100':    'tick-V100b',
  'RDBULL':   'tick-RBREAKb',
  'stpRNG':   'tick-STEPb',
  'BOOM1000': 'tick-BOOMb',
  'CRASH1000':'tick-CRASHb'
};

const lastPrices = {};

function subscribeTickerBar() {
  const syms = ['R_75','R_100','BOOM1000','CRASH1000'];
  syms.forEach(sym => {
    subscribeTicks(sym, (tick) => {
      updateTickerBar(sym, tick.quote);
    });
  });
}

function updateTickerBar(sym, price) {
  const prev = lastPrices[sym];
  const dir  = prev ? (price > prev ? 'up' : price < prev ? 'down' : '') : '';
  lastPrices[sym] = price;

  const label = {
    'R_75':     'V75',
    'R_100':    'V100',
    'BOOM1000': 'Boom 1000',
    'CRASH1000':'Crash 1000',
    'RDBULL':   'Range Break',
    'stpRNG':   'Step Index'
  }[sym] || sym;

  const arrow = dir === 'up' ? ' ▲' : dir === 'down' ? ' ▼' : ' ──';
  const text  = `${label} ${price.toFixed(2)}${arrow}`;

  [tickerSymbols, tickerSymbolsB].forEach(map => {
    if (map[sym]) {
      const el = document.getElementById(map[sym]);
      if (el) {
        el.textContent = text;
        el.className = 'tick ' + dir;
      }
    }
  });
}

// ── RECONNECT ──
function tryReconnect() {
  if (reconnectAttempts >= MAX_RECONNECT) {
    showToast('Max reconnect attempts reached', 'error');
    return;
  }
  reconnectAttempts++;
  const delay = reconnectAttempts * 3000;
  showToast(`Reconnecting in ${delay/1000}s... (${reconnectAttempts}/${MAX_RECONNECT})`, 'warn');
  reconnectTimer = setTimeout(() => {
    if (apiToken) connectDeriv();
  }, delay);
}

// ── STATUS UI ──
function setConnStatus(status) {
  const dot   = document.getElementById('connDot');
  const label = document.getElementById('connLabel');
  const btn   = document.getElementById('connectBtn');
  dot.className = 'dot ' + status;
  if (status === 'connected') {
    label.textContent = 'Connected';
    btn.textContent   = 'Connected ✓';
    btn.style.background = 'var(--green)';
  } else if (status === 'connecting') {
    label.textContent = 'Connecting...';
    btn.textContent   = 'Connecting...';
    btn.style.background = 'var(--warn)';
  } else {
    label.textContent = 'Disconnected';
    btn.textContent   = 'Connect';
    btn.style.background = 'var(--accent)';
  }
}

// ── BALANCE DISPLAY ──
function fetchBalance() {
  send({ balance: 1, subscribe: 1, req_id: getReqId() }, (resp) => {
    if (resp.error) return;
    const bal      = resp.balance.balance.toFixed(2);
    const currency = resp.balance.currency;
    const input    = document.getElementById('apiTokenInput');
    const btn      = document.getElementById('connectBtn');
    if (input) {
      input.type        = 'text';
      input.value       = `${currency} ${bal}`;
      input.style.color = '#00e5a0';
      input.readOnly    = true;
    }
    if (btn) {
      btn.textContent        = 'Connected ✓';
      btn.style.background   = 'var(--green)';
      btn.style.color        = '#000';
    }
  });
}

// ── BALANCE UPDATE FROM STREAM ──
function handleBalanceUpdate(msg) {
  if (msg.msg_type !== 'balance') return;
  const bal      = msg.balance.balance.toFixed(2);
  const currency = msg.balance.currency;
  const input    = document.getElementById('apiTokenInput');
  if (input && input.readOnly) {
    input.value = `${currency} ${bal}`;
  }
}
