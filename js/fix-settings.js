// Fix contract selectors to show individual contract types
window.addEventListener('load', () => {
  const contractSelects = [
    'mg-contract-family',
    'rsi-contract-family', 
    'tr-contract-family',
    'nw-contract-family',
    'vc-contract-family'
  ];

  const options = `
    <optgroup label="── Rise / Fall ──">
      <option value="RISE_FALL_CALL">Rise (CALL)</option>
      <option value="RISE_FALL_PUT">Fall (PUT)</option>
      <option value="RISE_FALL_AUTO">Rise/Fall — Auto Signal</option>
    </optgroup>
    <optgroup label="── Matches / Differs ──">
      <option value="MATCHES_AUTO">Matches — Auto Digit</option>
      <option value="DIFFERS_AUTO">Differs — Auto Digit</option>
    </optgroup>
    <optgroup label="── Even / Odd ──">
      <option value="EVEN_ODD_AUTO">Even/Odd — Auto Signal</option>
      <option value="EVEN_ODD_EVEN">Even — Fixed</option>
      <option value="EVEN_ODD_ODD">Odd — Fixed</option>
    </optgroup>
    <optgroup label="── Over / Under ──">
      <option value="OVER_UNDER_AUTO">Over/Under — Auto Signal</option>
      <option value="OVER_UNDER_OVER">Over 4 — Fixed</option>
      <option value="OVER_UNDER_UNDER">Under 5 — Fixed</option>
    </optgroup>
    <optgroup label="── Touch / No Touch ──">
      <option value="TOUCH_AUTO">Touch/No Touch — Auto</option>
      <option value="TOUCH_TOUCH">One Touch — Fixed</option>
      <option value="TOUCH_NOTOUCH">No Touch — Fixed</option>
    </optgroup>
  `;

  contractSelects.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = options;
  });
});
