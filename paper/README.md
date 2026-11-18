# Reproducible clustering companion

Open **wrp_cross_wave_clustering.ipynb**. It contains the narrative, all analytical code and saved results in one editable notebook. Run all cells from this directory after installing `requirements.txt`.

The default run checks the aggregate inputs against their manifest, assigns stored models, reproduces all 3,310 candidate comparisons and resolution rankings, the principal conditional-refit distributions, all 259 native rule scores, rule transfer, final fixed-definition frequencies, figures and country summaries. It starts no clustering fits. The saved results are in `results/`; scientific figures are supplied as vector PDF and PNG.

## Main findings

- The independently fitted seven-cluster models in 2021, 2023 and 2025 have point ARI 0.95–0.96. Four clusters recur more strongly under refitting; the remaining three have weaker recovery.
- The later-wave five-worry models have identical three-way point assignment functions on all 243 complete patterns. Occasional confirmation refits differ.
- No equally robust shared grouping was established across all four waves including 2019.

2025 supplies the reporting reference. These settings were generated independently within waves, then selected jointly using development evidence. This is not independent validation of the complete selection procedure. Earlier frozen six-cluster 2025 and five-cluster 2023 models remain unchanged alternatives with their own evidence.

## Inputs and optional fitting

`assets/` contains global answer-pattern counts and masses, stored centres, metadata, country aggregates and verification targets. It contains no respondent identifiers, respondent-linked assignments or respondent-level weights. Country split files identify countries only. `manifest.json` records input checksums.

Original survey files are obtained separately from [Lloyd’s Register Foundation](https://github.com/lrfoundation/world_risk_poll_data), at the release recorded in `assets/data_sources.json`. The notebook explains their coding, order and paths. Do not substitute a newer release silently.

Optional rule enumeration and fitting are included inline and switched off. Fitting requires the original survey data. It evaluates the complete recorded candidate catalogue and includes screening, sealing, fresh confirmation and extraction of every passing setting’s rules. The historical adaptive TPE proposals are supplied as a fixed catalogue; this notebook does not regenerate Optuna’s proposal stream or promise bitwise reproduction of old fits on different library versions. The notebook distinguishes reuse of stored fits from new optional fits.

The runtime check used Python 3.11, NumPy 1.26.4, pandas 3.0.3, SciPy 1.17.1 and scikit-learn 1.8. Default execution passed with `KMeans.fit` disabled. Optional exhaustive rule enumeration reproduced all ten selected 2025 formulas and scores; fitting and confirmation code was checked on synthetic data.

## Website and historical work

`../docs/index.html` is the nontechnical overview; `explore.html` and `countries-by-wave.html` show detailed results. `../scripts/export_paper_assets.py` validates and exports the same model aggregates for those pages.

Historical website versions are outside the published site in `../archive/historical_benchmarks/`. Older prediction experiments remain supplementary archived work, documented in `../archive/README.md`. They are not required by this clustering companion.
