# Country distances and maps across waves

The country explorer at `docs/countries-by-wave.html` extends the 2023 analysis to all seven independently frozen models. It defaults to the **2025 full worry–harm benchmark**. Select an earlier wave or the five-common-worry family to include 2019. Country distances and income patterns are two tabs of the same explorer. Year, family, distance, component, country set, selected country, map mode and list length can be linked through URL parameters.

## Results

The table uses all eligible countries in each wave, including the original held-out countries, as a **post-validation description**. It is not a new assessment of model transfer. Development-only views are also available. These country counts differ from the common development-country frames used for the separate cross-wave ensemble and prevalence comparisons.

| Wave | Questions | Countries | Eligible respondents | Clusters | Cluster/answer distance rank correlation | Same nearest country | Income-gap rho: clusters | Income-gap rho: answers |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2021 | Worry + harm | 121 | 117,678 | 4 | 0.749 | 12.4% | 0.224 | 0.374 |
| 2023 | Worry + harm | 142 | 137,460 | 5 | 0.824 | 18.3% | 0.247 | 0.298 |
| 2025 | Worry + harm | 140 | 134,702 | 6 | 0.842 | 15.0% | 0.267 | 0.317 |
| 2019 | Five common worries | 142 | 142,042 | 3 | 0.747 | 5.6% | 0.115 | 0.223 |
| 2021 | Five common worries | 121 | 121,167 | 3 | 0.739 | 16.5% | 0.184 | 0.306 |
| 2023 | Five common worries | 142 | 141,624 | 3 | 0.678 | 10.6% | 0.087 | 0.202 |
| 2025 | Five common worries | 140 | 138,355 | 3 | 0.675 | 9.3% | 0.118 | 0.240 |

The correlation compares all distinct unordered country pairs. Same-nearest is the fraction of countries with an identical nearest country under the two distances. Each country counts once. Income rho is Spearman correlation between a raw distance and the absolute gap between the four ordered income-group labels. Country pairs share countries, so no independent-pair significance tests are used.

The full models show stronger agreement between country-distance rankings than between exact nearest countries. The common-worry results show the same distinction. Neither summary is a substitute for the other: cluster proportions compress respondents' answers; original-answer marginals omit combinations within respondents.

## Country summaries and distances

Read the saved frozen labels and eligibility, then join original answers by respondent ID **and country**. Do not refit, relabel or change model selection. Normalize WGT to sum to one among the eligible respondents within each country. Use that same cohort and the same weights for all questions and cluster proportions in a model. Different model families can have different eligible respondents.

Let p_ca be the weighted share of country c in frozen cluster a. Hellinger distance is

    H(c,d) = sqrt(0.5 * sum_a (sqrt(p_ca) - sqrt(p_da))**2).

Cluster IDs belong to the selected model. The full models have four/five/six clusters in 2021/2023/2025; all common-worry models have three. A shared ID does not establish cross-wave correspondence.

For worry question j, let Q_cj(r) be its weighted probability in country c of the original category r (not/somewhat/very worried). Its total variation distance is

    TV_j(c,d) = 0.5 * sum_r abs(Q_cj(r) - Q_dj(r)).

Average across the six worry questions in full models, or the five common worries in worry-only models. For a binary harm indicator, total variation is exactly the absolute harm-prevalence gap. Average those gaps separately over seven personal-harm and seven known-person-harm indicators. In the full family,

    D(c,d) = alpha * D_W(c,d) + (1-alpha) * (D_S(c,d) + D_K(c,d)) / 2.

Each full model uses its own frozen alpha (2021: 0.5578217667703464; 2023: 0.5837857862168715; 2025: 0.625). Worry-only uses D = D_W. The middle-category coding q does not enter this marginal comparison. The original harm answer “both” gives personal=1 and known-person=1. Missing or special responses are never coded as no worry or no harm.

Full summaries store 18 worry-category probabilities and 14 harm prevalences. Common-worry summaries store 15 category probabilities. These are marginal probabilities, not independent clustering features. All raw distances are between zero and one. Ranks use unrounded distances and ISO3 to break exact ties. Component harm gaps multiplied by 100 are mean prevalence differences in percentage points.

## Fixed 2025 distance colours

For the new multiwave explorer only, set a positive reference to the median raw distance over all distinct unordered pairs of eligible 2025 countries (140 countries; 9,730 pairs), separately for each question family and metric. Show R = raw_distance / reference. Reuse this denominator for all earlier waves and for the development-only display; never recalibrate after selecting a country or subset.

- **full**: clusters = 0.2140587547330788; worry = 0.1960961911778192; personal = 0.04538328553111848; known = 0.08352995391347902; responses = 0.1510665508887961.
- **common_worry**: clusters = 0.1639068843813433; worry = 0.1924330707188191; responses = 0.1924330707188191.

The distance colour is L(min(1,max(0,R/2))), with L the piecewise-linear CIELAB interpolation through #4d85b1, #64a779, #ead46c, #df8b45 at positions 0, 1/3, 2/3, 1. Colour saturates at R=2; saved and displayed numbers do not. These are visual aids, not decision thresholds. Each metric/component has a different reference; component ratios cannot be added. Full-model alpha and cluster definitions differ across waves, so a common display reference does not make the underlying definitions identical.

**The archived 2023 pages retain their original B/E-derived reference constants.** No original country matrix, model, assignment, reference constant or historical map payload is replaced. The newly calculated 2023 full raw cluster and original-answer matrices reproduce the saved matrices to within 2e-14.

## Cluster-similarity overview colours

Write z_c = sqrt(p_c)/sqrt(2). Centre the country coordinates, compute an SVD, and retain the first two coordinates U[:, :2] * singular_values[:2]. For each axis, choose its sign so that its largest absolute right-singular loading is positive. This is the classical two-dimensional Euclidean/Hellinger projection. Save variance retained, Spearman correlation of projected vs exact pair distances, and sqrt(sum((exact-projected)**2) / sum(exact**2)).

Map the two coordinates to the CIELAB chromatic axes at lightness 67, initially multiplying by 55 / max_country_coordinate_norm. Repeatedly multiply the common factor by 0.95 until RGB channels stay in [3,252]. Overview colours are model-specific and **are not aligned across waves**. The overview is fixed over all eligible countries even when displaying the development subset. Nearest-country tables always use the exact full Hellinger distance. Geography is not an input to this projection.

## Income and regions

Use CountryIncomeLevel and GlobalRegion from each wave's source metadata. Four ordered income classes are displayed; unclassified countries remain on the map but are excluded from income calculations. Classifications can change between waves. Every distinct country pair has equal weight in a group cell; within-group cells omit self-pairs.

For overall original answers and cluster proportions, calculate Spearman correlation with absolute income-group gaps. Shuffle whole-country income labels 999 times with seed 20261029, first freely and then separately within each source region. Keep the distances fixed and preserve the respective income counts. The upper-tail fraction is (1 + number of permuted correlations >= observed) / 1000. These are conditional randomization checks, not causal effects; the within-region version preserves the region/income composition. Component views report descriptive rho without a new permutation check. No independent-pair p-value is computed.

The region outlines are unions of the countries assigned to the original source GlobalRegion in that wave. Geometry is the existing Natural Earth 110m geometry distributed with the original maps; small or absent polygons are shown as dots at existing Natural Earth label points. In each view, grey means outside the selected eligible country set, not zero worry or zero harm. Income maps have categorical colours, separate from the distance scale.

## Nearest-country sensitivity

Use 200 independent IID respondent bootstrap resamples within each country, with replacement, retaining their original WGT and saved frozen cluster labels. Recalculate country proportions and nearest neighbours jointly across countries. Record how often the original nearest country is still nearest. Seed: 20261029. This conditions on observed respondents and fixed definitions; it does not represent full survey-design uncertainty or clustering-refit stability. Original-answer distances remain descriptive without a new uncertainty analysis, as in the 2023 marginal-response extension.

## Source and verification

The complete implementation and results are embedded in each wave's editable `research_notebooks/wrp_YEAR_clustering_and_cluster_descriptions.ipynb` in the analysis workspace. Regeneration is off by default. There are no extra scientific source-code helpers required by those notebooks. Original notebook cells and frozen result snapshots are retained. The all-wave index is `course_artifacts/wrp_country_maps_all_waves/index.json`; each pinned output folder contains a provenance manifest, aggregate summaries, raw distance matrices, country metadata, cluster shares and conditional nearest-neighbour sensitivity tables.

`docs/data/country-waves.sources.json` records checksums of the checked aggregate payloads and their manifests. `scripts/export_country_wave_data.py --source-root /path/to/analysis/workspace` curates these saved aggregates without reading respondent rows. Without `--source-root`, it validates the public JSON and regenerates the offline script asset. It does not fit or assess models. The browser independently reconstructs raw distances from the probabilities and cluster shares; the matrix-download button exports unrounded raw distances for the selected country set and metric.

The public data contain country metadata and aggregate probabilities only. They contain no respondent records, IDs, linked answers or linked assignments. Public maps and tables work offline. See `country_waves_publication_audit.json` for numerical, preservation and browser checks.
