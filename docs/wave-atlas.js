/* Display the published aggregate results. Fits are reproduced in the companion notebook. */
(() => {
  'use strict';
  const report = window.WRP_SHARED_FIVE;
  const el = id => document.getElementById(id);
  const years = [2021, 2023, 2025];
  const query = new URLSearchParams(location.search);
  const cluster = query.get('cluster');
  const card = [...document.querySelectorAll('[data-cluster]')]
    .find(link => link.dataset.cluster === cluster);
  const compare = query.get('view') === 'compare';
  if (!compare && !card) return;

  const panel = el(compare ? 'aw-compare' : 'aw-explore');
  panel.dataset.atlasCurrent = '';
  if (!report) {
    const message = document.createElement('p');
    message.textContent = 'The aggregate results could not be loaded.';
    panel.append(message);
    return;
  }

  const names = report.names;
  const percent = (value, digits = 1) => (100 * value).toFixed(digits) + '%';
  const esc = value => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
  const domains = ['Food','Water','Crime','Severe weather','Traffic','Mental health','Work'];

  function table(caption, headers, rows) {
    const head = headers.map(text => '<th scope="col">' + esc(text) + '</th>').join('');
    const body = rows.map(([name, ...values]) => '<tr><th scope="row">' + esc(name) + '</th>' +
      values.map(value => '<td>' + esc(value) + '</td>').join('') + '</tr>').join('');
    return '<table class="atlas-simple-table"><caption>' + esc(caption) +
      '</caption><thead><tr>' + head + '</tr></thead><tbody>' + body + '</tbody></table>';
  }

  function showCluster(index, description) {
    const clusters = years.map(year => report.models['full_' + year].clusters[index]);
    const rules = years.map(year => report.commonRuleScores[year][index]);
    const rule = rules[0];
    const size = clusters.map((cluster,i) => '<div><dt>' + years[i] + '</dt><dd>' + percent(cluster.share) + '</dd></div>').join('');
    const ruleDescription = index === 4
      ? 'Food can be rated at any level. The five other worries are all below “very worried.”'
      : rule.reading;
    const worried = domains.slice(0,6).map((name,i) =>
      [name, ...clusters.map(c => percent(c.worry[i][2]))]);
    const harm = domains.map((name,i) =>
      [name, ...clusters.map(c => percent(c.harm[0][i]) + ' / ' + percent(c.harm[1][i]))]);
    const performance = years.map((year,i) =>
      [year, percent(rules[i].precision,2), percent(rules[i].coverage,2)]);
    const fullWorry = domains.slice(0,6).flatMap((name,i) =>
      ['Not worried','Somewhat worried','Very worried'].map((level,j) =>
        [name + ' · ' + level,...clusters.map(c => percent(c.worry[i][j]))]));
    el('aw-detail').innerHTML =
      '<header class="atlas-page-head"><h1>' + esc(names[index]) +
      '</h1><p class="atlas-deck">' + esc(description) +
      '</p></header><div class="atlas-result-head"><h2>Share in each survey’s analysis sample</h2><dl class="atlas-scores">' +
      size + '</dl></div>' +
      '<div class="atlas-columns"><div class="aw-matrix-scroll">' +
      table('Share who answered “very worried”', ['Topic', ...years], worried) +
      '</div><div class="aw-matrix-scroll">' +
      table('Reported harm to self / to someone known', ['Topic', ...years], harm) + '</div></div>' +
      '<details><summary>Read the exact rule and its scores</summary><p>' + esc(ruleDescription) +
      '</p><p class="atlas-rule-literal">' +
      esc(rule.text) + '</p><p>K counts harm domains involving someone known. V counts very-worried answers. “Not very worried” includes both not worried and somewhat worried.</p>' +
      table('How the same rule describes this cluster', ['Survey', 'Precision', 'Coverage'], performance) +
      '</details><details><summary>See all three worry response levels</summary><div class="aw-matrix-scroll">' +
      table('Worry answers within the selected cluster', ['Topic and answer', ...years], fullWorry) + '</div></details>';
  }

  function showMatrix(earlier) {
    const overlap = report.overlap['full_' + earlier];
    const rows = overlap.map((row,i) => [names[i], ...row.map(value => percent(value))]);
    el('aw-overlap-note').textContent = 'Each row shows how one cluster from the ' + earlier +
      ' fit was assigned by the 2025 fit on the same respondents. Rows sum to 100% before rounding.';
    el('aw-matrix').innerHTML = table(earlier + ' and 2025 membership overlap', ['Cluster', ...names], rows);
  }

  function showEvidence() {
    const agreement = report.pointPairs.map(row =>
      [row.year_a + ' and ' + row.year_b, row.ARI.toFixed(3), percent(row.weighted_agreement,2)]);
    el('aw-point').innerHTML = table('Agreement between fitted models', ['Survey pair', 'ARI', 'Weighted agreement'], agreement);
    const refits = report.crossARI.map(row =>
      [row.year_a + '–' + row.year_b + ' · ' + row.test, row.p10.toFixed(3), row.median.toFixed(3), row.p90.toFixed(3)]);
    el('aw-stability').innerHTML = table('ARI across repeated fits', ['Pair and subsample', '10th', 'Median', '90th'], refits);
    el('aw-recovery').innerHTML = table('Recovery of individual clusters', ['Cluster', 'Lowest score'],
      names.map((name,i) => [name,report.recovery[i].toFixed(3)]));
  }

  if (compare) {
    showEvidence();
    const select = el('aw-earlier');
    select.value = query.get('earlier') === '2023' ? '2023' : '2021';
    showMatrix(select.value);
    select.addEventListener('change', () => {
      showMatrix(select.value);
      const url = new URL(location.href);
      url.searchParams.set('earlier', select.value);
      try { history.replaceState(null, '', url); } catch (error) { /* file browsing may restrict URL updates */ }
    });
    document.title = 'Worry–harm recurrence · World Worry Atlas';
  } else {
    showCluster(Number(cluster), card.querySelector('span').textContent);
    document.title = names[Number(cluster)] + ' · World Worry Atlas';
  }
})();
