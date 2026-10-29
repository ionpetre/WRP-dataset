# Clusters across World Risk Poll waves

The Atlas now shows seven independently selected models. **The frozen 2025 full worry–harm model, WRP2025_K6, is the primary benchmark.** The original 2023 WARM-5/stored T5 model remains unchanged.

## Two input families

- **Worry + harm:** six worries (food, water, crime, severe weather, traffic and mental health), plus seven personal and seven known-person harm indicators. Available for 2021, 2023 and 2025.
- **Worry only:** the five common worries (food, water, crime, severe weather and mental health). Available for 2019, 2021, 2023 and 2025. These are separate fitted models, not a component view of the full models.

Personal harm concerns the respondent. Known-person harm concerns someone personally known. A report of both makes both indicators true; the indicators remain separate. Full models retain all fourteen harm indicators.

Only substantive, complete answers for the selected family are eligible. Missing, unknown and refused answers are not recoded as no worry or no harm. Each wave's full development-country population is used for its own cluster cards. Countries have equal total fitting/reporting influence, preserving relative survey weights within each eligible country. These summaries are not world-population shares.

| Wave | Input family | Clusters | Development respondents | Countries |
|---|---|---:|---:|---:|
| 2019 | Worry only | 3 | 114,428 | 114 |
| 2021 | Worry + harm | 4 | 93,548 | 96 |
| 2021 | Worry only | 3 | 96,196 | 96 |
| 2023 | Worry + harm | 5 | 109,488 | 113 |
| 2023 | Worry only | 3 | 112,753 | 113 |
| 2025 | Worry + harm | 6 | 107,507 | 111 |
| 2025 | Worry only | 3 | 110,436 | 111 |

Models were chosen using their own development evidence. The 2023 cluster count, centres and settings were not imposed on other waves. All benchmark transformations and centres were frozen before their original held-out assessments, with no all-country refit. Numeric cluster IDs are local to each model.

## Numerical representation

Worry levels not/somewhat/very are represented by 0/q/1, equivalently 0/1/t divided by t. For d worry answers x, let m be their mean. Full models transform answers to

\[
z=\left[\sqrt{\alpha/6}(x-m\mathbf1),\ \sqrt{\alpha/6}\,m,\ \sqrt{(1-\alpha)/14}\,h\right],
\]

where d=6 and h contains all fourteen personal/known-person harm flags. Common-worry models instead use d=5 and the vector \(5^{-1/2}[x-m\mathbf1,m]\). The centred part retains which risks concern a respondent relative to their other answers; the separate mean retains overall worry with reduced influence. No empirical variance standardization or respondent-level PCA is applied.

Weighted K-means minimizes \(\sum_i w_i\min_a\|z_i-\mu_a\|^2\). Prediction uses the nearest stored centre, with stored centre order resolving exact ties. The numerical allocation controls distance coefficients, not an observed share of variance.

| Wave | Inputs | k | t = 1/q | Worry allocation alpha |
|---|---|---:|---:|---:|
| 2019 | Worry only | 3 | 2.127266 | No harm block |
| 2021 | Worry only | 3 | 1.337746 | No harm block |
| 2021 | Full | 4 | 1.812715 | 0.557822 |
| 2023 | Worry only | 3 | 1.428571 | No harm block |
| 2023 | Full | 5 | 2.399803 | 0.583786 |
| 2025 | Worry only | 3 | 1.252097 | No harm block |
| 2025 | Full | 6 | 2.400000 | 0.625000 |

## Compare frequencies: keep the 2025 definition fixed

The paired bars apply the **original frozen 2025 model** to each wave's own respondents. Full comparisons use the same 92 development countries in 2021–2025; worry-only comparisons use the same 90 in 2019–2025. Country shares preserve relative survey weights and are averaged with equal country influence.

A difference is the 2025 share minus the earlier share, in percentage points. This compares an unchanged definition. It does not compare similarly named independently fitted clusters or track the same individuals. Comparison shares can differ from the 2025 overview cards because the comparison uses fewer countries.

## Compare definitions: keep the reference answers fixed

The optional overlap table gives the same observed 2025 answers to both original frozen models, each using its own coding and centres. It uses 90,395 full respondents in 92 countries, or 91,249 worry-only respondents in 90 countries. Each cell is the country/survey-weighted percentage of an earlier cluster assigned to a particular 2025 cluster. Unrounded rows sum to 100%; rounding can change displayed sums slightly. Cluster IDs are not matched by number.

The original models retain their original fitting countries. A separate experiment refits the selected settings on the common country frame. It uses 100 respondent subsamples, 100 stratified country subsamples and 20 initialization-only runs per wave/family: 1,540 fits. Each fit uses twenty K-means initializations; selected settings and cluster counts stay fixed. The site shows the country-subsampling results.

Within-wave ARI compares all 4,950 pairs of distinct runs. Cross-wave ARI compares all 10,000 run combinations. Every run assigns the same 2025 reference respondents. Dots are medians and intervals are the 10th–90th percentiles. They describe fitting variation, not independent replications or confidence intervals. The distributions condition on the selected settings; they do not rerun the complete adaptive selection procedure.

ARI is the ordinary respondent-count adjusted Rand index. It is invariant to label names and permits different cluster counts. It is not survey-weighted percentage agreement. The overlap table uses country/survey weights instead. Larger ARI means closer partitions, with 1 indicating equality up to labels.

The independent full models can disagree at their selected finer resolutions while sharing a close coarse partition. For example, the independently best original three-cluster 2021 and 2025 alternatives give matched-country-refit ARI 0.963 on 2025 respondents. They are sensitivity results, not replacements for the selected four- and six-cluster benchmarks.

## Existing 2023 analyses

The detailed WARM-5 explorer, country comparisons and income analyses remain available, labelled **2023**. They use the original T5 centres, assignments, distance formulas and calibration constants. They have not been rerun with 2025 labels. Historical research files, code keys and filenames retain their original identities.

## Aggregate data and reproduction

- `docs/data/wave-results.json`: all public values used by the new explorer.
- `docs/data/wave-results.sources.json`: exact source paths and SHA-256 checksums, population/weighting conventions and the verified ensemble context.
- `scripts/export_wave_atlas_data.py`: creates the browser data asset from the public JSON. With `--source-root /path/to/analysis/workspace`, it independently exports the aggregate source tables and checks the selected specifications.
- `docs/wave-atlas.js` and `docs/wave-atlas.css`: native, editable browser code. There is no browser-side fitting or server requirement.

The export does not read respondent rows, refit models or repeat held-out assessment. No respondent records, survey-weight vectors or respondent-linked assignments are added to this release. The previous publication audits remain dated historical records; the current web update is recorded in `wave_atlas_publication_audit.json`.

The survey source is Lloyd's Register Foundation's [official World Risk Poll data](https://github.com/lrfoundation/world_risk_poll_data). The analysis uses the pinned release snapshot identified in the full research record. Attribute the survey separately from this analysis. Method references include [Hubert and Arabie (1985)](https://doi.org/10.1007/BF01908075) for ARI and [von Luxburg (2010)](https://doi.org/10.1561/2200000008) for clustering stability.
