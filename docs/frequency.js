/* Fixed-definition frequency comparison in the shared survey countries. */
(() => {
  'use strict';
  const result = window.WRP_SHARED_FIVE;
  const select = document.getElementById('overview-cluster');
  if (!result || !select) return;
  const years = [2021, 2023, 2025];
  function render() {
    const cluster = Number(select.value);
    const values = years.map(year => result.shares[year][cluster]);
    const name = result.names[cluster];
    document.getElementById('overview-trend-title').textContent = name;
    const bars = document.getElementById('overview-bars');
    bars.setAttribute('aria-label', name + ': ' + values.map((v, i) => (100*v).toFixed(2) + '% in ' + years[i]).join(', ') + '.');
    bars.innerHTML = values.map((v,i) => '<div class="aw-overview-column"><div class="aw-overview-bar" style="height:' +
      (100*v/.4) + '%"><strong>' + (100*v).toFixed(2) + '%</strong></div><span>' + years[i] + '</span></div>').join('');
    const change = 100 * (values[2] - values[0]);
    const direction = change >= 0 ? 'increased' : 'decreased';
    document.getElementById('overview-change').textContent = 'The share ' + direction + ' by ' +
      Math.abs(change).toFixed(2) + ' percentage points from ' + years[0] + ' to ' + years[2] + '.';
  }
  select.addEventListener('change', render);
  render();
})();
