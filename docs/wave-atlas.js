/* Display the published aggregate results. Fits are reproduced in the companion notebook. */
(() => {
  'use strict';
  const report = window.WRP_SHARED_FIVE;
  const el = id => document.getElementById(id);
  const years = [2021, 2023, 2025];
  if (!report) {
    el('aw-clusters').textContent = 'The aggregate results could not be loaded.';
    return;
  }

  const names = report.names;
  const models = years.map(year => report.models['full_' + year]);
  const percent = (value, digits = 1) => (100 * value).toFixed(digits) + '%';
  const esc = value => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
  const domains = ['Food','Water','Crime','Severe weather','Traffic','Mental health','Work'];
  const descriptions = [
    'Very high worry about traffic, crime and severe weather is common in this cluster. Water and mental-health worries are less prominent.',
    'Water and food stand out. In all three surveys, a large majority of this cluster said they were very worried about water and food.',
    'Almost everyone in this cluster is very worried about mental health. Very high worry about traffic is also common.',
    'Across several areas of life, members often report serious harm to someone they know. These reports are much more common than reports of harm to themselves.',
    'Members rarely choose “very worried” across the six topics. Food can still be a very high worry for some members.',
  ];
  const tabs = ['explore', 'compare'];
  const state = { view: 'explore', cluster: 0, earlier: 2021 };

  function table(caption, headers, rows) {
    const head = headers.map(text => '<th scope="col">' + esc(text) + '</th>').join('');
    const body = rows.map(([name, ...values]) => '<tr><th scope="row">' + esc(name) + '</th>' +
      values.map(value => '<td>' + esc(value) + '</td>').join('') + '</tr>').join('');
    return '<table class="atlas-simple-table"><caption>' + esc(caption) +
      '</caption><thead><tr>' + head + '</tr></thead><tbody>' + body + '</tbody></table>';
  }

  function save() {
    const url = new URL(location.href);
    url.searchParams.set('view', state.view);
    url.searchParams.set('cluster', state.cluster);
    if (state.view === 'compare') url.searchParams.set('earlier', state.earlier);
    try { history.replaceState(null, '', url); } catch (error) { /* file browsing may restrict URL updates */ }
  }

  function restore() {
    const query = new URLSearchParams(location.search);
    state.view = query.get('view') === 'compare' ? 'compare' : 'explore';
    const index = Number(query.get('cluster'));
    state.cluster = Number.isInteger(index) && index >= 0 && index < names.length ? index : 0;
    state.earlier = Number(query.get('earlier')) === 2023 ? 2023 : 2021;
  }

  function showCluster(index) {
    state.cluster = index;
    el('aw-clusters').querySelectorAll('button').forEach((button,i) =>
      button.setAttribute('aria-pressed', String(i === index)));
    const clusters = models.map(model => model.clusters[index]);
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
      '<div class="atlas-columns atlas-result-head"><div><h2>' + esc(names[index]) +
      '</h2><p class="atlas-rule-prose">' + esc(descriptions[index]) +
      '</p></div><div><h3>Share in each survey’s analysis sample</h3><dl class="atlas-scores">' +
      size + '</dl></div></div>' +
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

  function showMatrix() {
    const earlier = state.earlier;
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
    el('aw-earlier').value = state.earlier;
    showMatrix();
  }

  function changeView(view) {
    state.view = view;
    for (const key of tabs) {
      const active = key === view;
      el('aw-' + key).hidden = !active;
      const button = el('aw-tab-' + key);
      button.setAttribute('aria-selected', String(active));
      button.tabIndex = active ? 0 : -1;
    }
  }

  el('aw-clusters').innerHTML = names.map((name,i) =>
    '<button type="button" style="--pattern:' + esc(report.colors[i]) + '">' + esc(name) + '</button>').join('');
  el('aw-clusters').querySelectorAll('button').forEach((button,i) => button.addEventListener('click', () => {
    showCluster(i);
    save();
  }));
  tabs.forEach(key => el('aw-tab-' + key).addEventListener('click', () => {
    changeView(key);
    save();
  }));
  el('aw-earlier').addEventListener('change', event => {
    state.earlier = Number(event.target.value);
    showMatrix();
    save();
  });
  document.querySelector('[role="tablist"]').addEventListener('keydown', event => {
    const key = event.key;
    if (!['ArrowLeft','ArrowRight','Home','End'].includes(key)) return;
    event.preventDefault();
    const next = key === 'Home' ? 'explore' : key === 'End' ? 'compare' : tabs.find(view => view !== state.view);
    el('aw-tab-' + next).click();
    el('aw-tab-' + next).focus();
  });
  function render() {
    restore();
    changeView(state.view);
    showCluster(state.cluster);
    showEvidence();
  }
  window.addEventListener('popstate', render);
  render();
})();
