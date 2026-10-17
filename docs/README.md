# T5 profiles and country comparisons

Open `index.html` for the five profiles, `countries.html` for country comparisons or `country-income.html` for income patterns. All three work offline and use country/profile aggregates only.

## One model, one allocation

Every page uses frozen T5. Overall original-response distance gives worry 58.38%, personal harm 20.81% and known-person harm 20.81%. There is no balanced-versus-worry-emphasized choice. Worry-only and harm-only views isolate components; they are not different clustering models.

**Original response distributions** compares the six worry-category distributions and 14 harm prevalences. **Frozen profile mixtures** compares proportions across the same five T5 profiles using Hellinger distance. The approximate overview is available only for profile mixtures; rankings use exact distances.

## Reading the scale

Values are raw distances divided by fixed calibration values: 0.1550977480973838 for overall original responses and 0.2218094853108838 for profile mixtures. Component reference values are 0.2019268502025546 for worry, 0.0500960004811531 for personal harm and 0.0872275415556315 for known-person harm. These are the previously fixed calibration values, not newly estimated T5 medians.

One means the fixed reference distance; two means twice that reference. Seven colour bands span zero to “2 or more”; numerical labels are uncapped. Changing country or scope never changes the denominator. A ratio is not a percentage of societal similarity. Component ratios use different denominators and therefore cannot be added.

Lists show 10, 20 or all available peers. Country comparisons rank the chosen component. On the income page, component choice changes the map; income-group matrices and neighbour lists remain the overall T5 comparison. The response/profile selector changes the type of summary, not the model.

## Interpretation

Profile cards show equal-country-weighted development shares. Selecting a card shows original worry distributions, separate personal/known-person harm and differences from respondents outside that profile. Display labels start at 1; stored profile IDs remain T5_C0–T5_C4.

Country maps show similarity in selected survey responses, not social equivalence. Marginal response distributions can hide different within-person combinations. Mixtures compress responses further. Exact nearest-neighbour ranks are uncertain; the conditional bootstraps do not cover survey-design or model-selection uncertainty.

## Rebuild and publish

`country-similarity-fragment.html` and `country-income-fragment.html` are the editable map fragments. Run `python .week05_build/rebuild_T5_pages.py` from the repository root to refresh the offline wrappers. The shared helper is `.week05_build/T5-response-distance-tools.js`. Keep the D3 dependency and licence under `docs/vendor/`.

GitHub Pages publishes `docs/`; supporting files outside it link to their GitHub repository pages. These links need internet access, unlike the embedded interactions.
