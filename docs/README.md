# The all-wave Worry–Harm Atlas

Open `index.html` to explore all seven wave/family models. It defaults to the original frozen 2025 full worry–harm benchmark. The two tabs are **Explore a wave** and **Compare with 2025**.

## Browser files

- `index.html`: semantic page shell.
- `wave-atlas.css`: responsive layout and light/dark appearance.
- `wave-atlas.js`: year/family/cluster controls, fixed-definition paired bars, optional overlap tables and refit-ARI ranges.
- `data/wave-results.json`: the public aggregate payload.
- `data/wave-results.js`: the same payload as a script asset, so the page also works through `file://` without a server.
- `data/wave-results.sources.json`: source checksums and scientific conventions.
- `methods.html`, `wave-methods.js`: the local methods and downloads page.

Selected view, question family, wave, cluster and earlier comparison wave are encoded in the URL. Unsupported parameters fall back to valid models. 2019 is available only for the five-common-worry family. There are no fitting controls and no browser-side clustering.

Run `python scripts/export_wave_atlas_data.py` from the repository root to rebuild the browser asset from the public JSON. With `--source-root /path/to/analysis/workspace`, the exporter reads pinned aggregate CSV/JSON files, checks their selected specifications and writes the public payload and provenance. It does not read respondent rows, refit models or reopen held-out assessment.

## Scientific scope

The wave cards describe each independently selected model's own complete development population. Full worry–harm has four/five/six clusters in 2021/2023/2025. Common worry has three in every wave from 2019 onward. IDs remain model-specific.

The main comparison holds the original 2025 model fixed and applies it to each wave's own respondents in 92 full or 90 common-worry development countries. Shares use equal-country/survey weights. The optional overlap table holds the 2025 reference answers fixed and compares original frozen assignments. The ARI ranges use separate matched-country refits; they use respondent counts and describe procedure variation, not confidence intervals. See `methods.html` and `research/ALL_WAVES.md`.

## Historical 2023 pages

`2023-clusters.html` preserves the original detailed WARM-5 explorer and its section anchors. `response-profiles-fragment.html` retains its historical source name. The summary-chart helper `.week05_build/add_T5_summary_charts.py` now writes to `2023-clusters.html`, not the all-wave home page.

`countries.html` and `country-income.html` remain **2023 T5 analyses**. Their embedded models, response summaries, distance calculations, calibration constants and map interactions are unchanged. Their outer navigation labels their scope and links back to the all-wave explorer.

The editable fragments are `country-similarity-fragment.html` and `country-income-fragment.html`. Run `python .week05_build/rebuild_T5_pages.py` from the repository root to refresh those wrappers. Keep the existing D3 dependency and licence under `vendor/`.

Original-response distance retains worry 58.38%, personal harm 20.81% and known-person harm 20.81%. It is a comparison of marginal response distributions, distinct from Hellinger distance between the five T5 cluster proportions. Component views isolate parts of this original 2023 comparison; they do not fit different models.

The display calibration constants are unchanged: overall original responses 0.1550977480973838; cluster proportions 0.2218094853108838; worry 0.2019268502025546; personal harm 0.0500960004811531; known-person harm 0.0872275415556315. Raw distance divided by the corresponding reference gives the displayed ratio. Numbers are uncapped; colours saturate at two. Changing country or scope never changes the denominator. These ratios are not percentages of societal similarity.

GitHub Pages publishes this directory. New interactive charts and local methods work offline; external source links require internet access.
