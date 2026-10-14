# Country-similarity maps

Open `index.html` or `country-income.html` locally, or use GitHub Pages when enabled. Both pages are self-contained and work offline, with aggregate country information only.

The default **Original response distributions** compares worry-category distributions and separate personal/known-person harm prevalence. Inspect the overall B allocation (50/25/25), E allocation (75/12.5/12.5), or each component. **Frozen profile mixtures (Hellinger)** preserves historical B4/E8 comparisons. **Overview** is an approximate two-dimensional view available only for profile mixtures. Original dataset-region outlines remain unchanged.

Seven equal-width colour bands span zero (the selected country) to its maximum distance among displayed peers. Legends/tooltips retain raw values. Combine components before display normalization; colours never determine ranks or income analyses and cannot be compared across references, allocations, components or scopes. Income categories and mean-distance heatmaps keep separate scales.

Lists show 10, 20 or all peers, ranked by unrounded distance. `TV` means total variation; `H` historical Hellinger; `P` the pair-distance percentile in the displayed scope (lower is closer), not a p-value or confidence measure. Worry mismatch is mean feature total variation ×100; harm gaps are mean absolute prevalence differences in percentage points. The main map ranks the selected component; component lists also give overall distances. The income page's two lists and income summaries always use overall B/E allocations; component selection changes the map only. Family selection changes all comparisons together.

These maps describe selected responses, not societal equivalence or a new country typology. No profile models were refitted. Equal response marginals can hide different within-person combinations; exact ranks are descriptive, without newly computed rank uncertainty.

`country-similarity-fragment.html` and `country-income-fragment.html` are editable sources. `.week05_build/` contains templates, distance helper and portable exporter. Offline pages embed D3 and verified geometry, retaining the resize-loop repair. Keep the D3 licence. New probabilities/results are in `../course_artifacts/week05_country_response_distances_v1/e1ecf01551bcf2da/`; historical projection diagnostics remain in `../course_artifacts/week05_continuous_country_similarity_maps_v1/`. The reproduction guide explains aggregate-only testing and page regeneration without microdata or clustering.
