# WARM-5 profiles and country comparisons

Open `index.html` for the five profiles, `countries.html` for country comparisons or `country-income.html` for income patterns. All three work offline and use country/profile aggregates only.

The profile page also includes the three overview plots from the Week 6 slides: regional profile frequencies, development versus held-out frequencies, and personal versus known-person harm. Exact percentages are available in expandable tables. Regional bars use all 142 countries and the same frozen global centres. Harm bars average the seven domain prevalences; they do not measure the proportion reporting any harm.

## One model, one allocation

Every page uses frozen WARM-5. Overall original-response distance gives worry 58.38%, personal harm 20.81% and known-person harm 20.81%. There is no balanced-versus-worry-emphasized choice. Worry-only and harm-only views isolate components; they are not different clustering models.

**Original response distributions** compares survey-weighted answers question by question: the not/somewhat/very-worried percentages for each worry and the personal/known-person harm percentages for each harm domain. Similar totals can hide different combinations of answers within the same people.

**Cluster proportions (Hellinger)** compares each country's five survey-weighted WARM-5 cluster shares. Countries with identical shares have distance zero even if answers differ within those clusters. This can give different nearest countries from the original-response comparison. The approximate overview is available only for cluster proportions; rankings use exact distances.

Both comparison pages show an expanded explanation directly below the controls. It updates with the selected distance, response component and map view. The explanation includes what is compared, what the summary leaves out, how to read the reference-relative numbers, and which distance applies to the map, matrix and nearest-country list. It is visible without opening a tooltip or help menu.

## Reading the scale

Values are raw distances divided by fixed calibration values: 0.1550977480973838 for overall original responses and 0.2218094853108838 for profile mixtures. Component reference values are 0.2019268502025546 for worry, 0.0500960004811531 for personal harm and 0.0872275415556315 for known-person harm. These are the previously fixed calibration values, not newly estimated WARM-5 medians.

One means the fixed reference distance; two means twice that reference. A continuous colour gradient spans zero to “2 or more”; numerical labels are uncapped. Values above two share the endpoint colour. Changing country or scope never changes the denominator. A ratio is not a percentage of societal similarity. Component ratios use different denominators and therefore cannot be added. Income-group colours remain categorical, and the approximate profile-mixture overview retains its separate two-dimensional colour scheme.

Lists show 10, 20 or all available peers. Country comparisons rank the chosen component. On the income page, component choice changes the map; income-group matrices and neighbour lists remain the overall WARM-5 comparison. The response/profile selector changes the type of summary, not the model.

## Interpretation

Profile cards show equal-country-weighted development shares. Selecting a card shows original worry distributions, separate personal/known-person harm and differences from respondents outside that profile. Display labels start at 1; stored profile IDs remain T5_C0–T5_C4.

Country maps show similarity in selected survey responses, not social equivalence. Marginal response distributions can hide different within-person combinations. Mixtures compress responses further. Exact nearest-neighbour ranks are uncertain; the conditional bootstraps do not cover survey-design or model-selection uncertainty.

## Rebuild and publish

`country-similarity-fragment.html` and `country-income-fragment.html` are the editable map fragments. Run `python .week05_build/rebuild_T5_pages.py` from the repository root to refresh the offline wrappers. The shared helper is `.week05_build/T5-response-distance-tools.js`. Keep the D3 dependency and licence under `docs/vendor/`.

Run `python .week05_build/add_T5_summary_charts.py` to rebuild the three overview plots from the embedded profile aggregates and the saved regional frequencies. This updates `index.html` and `response-profiles-fragment.html`, without fitting a model. The profile page has no external chart dependencies.

GitHub Pages publishes `docs/`; supporting files outside it link to their GitHub repository pages. These links need internet access, unlike the embedded interactions.
