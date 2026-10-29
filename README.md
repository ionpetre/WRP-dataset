# The Worry–Harm Atlas

Explore respondent **clusters across the 2019, 2021, 2023 and 2025 World Risk Poll waves**. The latest full worry–harm model, **WRP2025_K6**, is the primary benchmark. Each wave was selected from its own development evidence; the original 2023 WARM-5/stored T5 model is preserved.

Research code and results from the 2026–2027 Machine Learning Project Course, maintained by Ion Petre. The interactive website uses aggregate results only.

## Explore the results

- [Explore all waves](https://ionpetre.github.io/WRP-dataset/) — choose a wave, inspect its clusters, or compare earlier waves with fixed 2025 definitions. [Offline page](docs/index.html).
- [Methods and data](https://ionpetre.github.io/WRP-dataset/methods.html) — populations, weighting, model comparisons and downloads.
- [Detailed 2023 WARM-5 results](https://ionpetre.github.io/WRP-dataset/2023-clusters.html) — the preserved single-wave explorer, regional frequencies and original validation evidence.
- [Country comparisons · 2023](https://ionpetre.github.io/WRP-dataset/countries.html) — original answer distributions or proportions across the same five T5 clusters.
- [Income patterns · 2023](https://ionpetre.github.io/WRP-dataset/country-income.html) — country comparisons within and between income groups.

## What the wave selector changes

**Worry + harm** uses six worries and fourteen separate personal/known-person harm indicators. The selected full models have four clusters in 2021, five in 2023 and six in 2025.

**Worry only** uses five common worry questions and includes 2019. Each wave independently selects three clusters. It is a separate family of fitted models, not an isolated component of the full model.

Numeric IDs belong to their own model. C0 in one wave need not mean C0 in another. The cards use each model's own development population. Countries have equal total influence, preserving relative survey weights within each eligible country. These are not world-population shares.

## Two different comparisons

The simple paired-bar view holds the original frozen **2025 definitions fixed** and assigns each wave's own respondents in common countries. It compares shares under an unchanged definition: 92 countries for full worry–harm, 90 for common worry. Independent cross-sections do not provide individual transitions.

The optional overlap table instead holds the **2025 reference answers fixed** and assigns them with two original frozen models. A separate country-subsampling comparison shows within-wave and cross-wave ARI distributions from repeated fits on common country frames. ARI uses respondent counts; the overlap table and shares use country/survey weights. Percentile ranges describe fitting variation, not confidence intervals.

The complete record is in [all-wave methods](research/ALL_WAVES.md). Coarser alternatives can agree closely even when the selected finer models differ; the comparison does not establish a single universal partition.

## Data and website source

- [Aggregate values](docs/data/wave-results.json) and [source checksums](docs/data/wave-results.sources.json).
- `docs/index.html`, `docs/wave-atlas.css`, `docs/wave-atlas.js`: native, editable website source.
- `scripts/export_wave_atlas_data.py`: checks the public JSON and rebuilds its offline-compatible browser asset. With `--source-root`, it exports the verified aggregate tables from the complete analysis workspace.

The new web export performs no model fitting or held-out reassessment. It adds no respondent records, survey-weight vectors, respondent-linked assignments or private fit caches. Obtain survey data separately from [Lloyd's Register Foundation](https://github.com/lrfoundation/world_risk_poll_data). Published aggregates retain the survey's attribution and applicable data terms; the repository's [Apache 2.0 licence](LICENSE) covers project code.

## Preserved 2023 code and results

The country and income pages remain specific to the original **WARM-5**, stored as `T5`. Its numerical coding, allocation, centres, cluster IDs, assignment code and country-distance calculations are unchanged. Historical source filenames and code keys are retained.

| Week | Purpose | Notebook |
|---|---|---|
| 1 | Understand the 2023 data | [Week 1](weekly_notebooks/week01_understand_2023_and_develop_questions.ipynb) |
| 2 | Define the research objectives | [Week 2](weekly_notebooks/week02_define_the_research_design.ipynb) |
| 3 | Curate data and establish the baseline | [Week 3](weekly_notebooks/week03_prepare_2023_data_and_kmeans.ipynb) |
| 5 | Select, freeze and validate WARM-5; compare regions and countries | [Week 5](weekly_notebooks/week05_validate_frozen_profiles.ipynb) |
| 6 | Predict frozen WARM-5 membership | [Week 6](weekly_notebooks/week06_predicting_frozen_risk_profile_membership.ipynb) |

The original [T5 results](research/T5_RESULTS.md), [mathematical methods](research/METHODS.md), [reproduction guide](research/REPRODUCING.md), centre bundle and publication audits retain their historical scope. The current website update is recorded in `wave_atlas_publication_audit.json`. The seven-model web export does not imply that those older notebooks were rerun or changed into multiwave analyses.

## Rebuild and publish

From this repository root, run `python scripts/export_wave_atlas_data.py` to rebuild the browser data from the public aggregate JSON. To export fresh copies of the pinned aggregate sources, use `python scripts/export_wave_atlas_data.py --source-root /path/to/analysis/workspace`.

GitHub Pages publishes `docs/` from `main`. The new explorer works offline, including its data, comparisons and local methods page. Supporting external repository links need internet access. The editable historical map fragments remain in `docs/`; their rebuilding instructions are in [the website guide](docs/README.md).
