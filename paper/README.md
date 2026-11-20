# Companion to *Recurring patterns of worry in the World Risk Poll*

The two notebooks below contain the paper's explanations, analytical code and saved outputs. Run All uses supplied aggregate evidence and saved centres. Expensive searches and fitting remain off by default.

## Worry alone and comparisons with worry and harm

Open [wrp_shared_worry_only.ipynb](wrp_shared_worry_only.ipynb). It verifies the four recurring worry-only clusters in 2019, 2021, 2023 and 2025, compares them with the five worry–harm clusters, and replays the matched fits with the same worry questions and number of clusters. It reproduces [Figure 3](results/figure3_harm_by_worry.pdf), the original harm rates, the within-country contrasts and the fixed-model and rule checks in the 25 held-out countries. These checks are described in Supplementary Sections S4 and S7. Tables and the figure are saved in [results/](results/). Its feature-influence section separately inspects the parent and child stages, verifies the role of the mean and reproduces original-question effects from the exact four-cluster assignment tree.

To verify the harm summaries from original survey answers, obtain the CSV files recorded in [assets/matched_harm_schedule.json](assets/matched_harm_schedule.json), put them in `paper/data/`, and set `RAW_WAVE_DIR` in the notebook if needed. Enable `RUN_SURVEY_REPLAY`. The notebook checks the survey file hashes and applies the recorded country splits and frozen models. The separate `RUN_MATCHED_FITS` switch repeats the matched fits using the original draws and seeds. Both switches are off by default.

## Worry and reported harm

Open [wrp_shared_five_clusters.ipynb](wrp_shared_five_clusters.ipynb). It checks the independently fitted seven-centre models and their fixed maps to five clusters, reproduces cross-wave agreement and individual-cluster recovery from all saved refit pairs, checks the common rules in each development population, and recalculates frequency changes under the fixed 2025 definition. The default run does not refit the clustering. It also reproduces the feature-influence checks in Supplementary Section S2: weighted separation by encoded coordinate, frozen-model coordinate omission, coherent original-answer randomisation, and mean omission on all 300 saved confirmation models. Set `RUN_EXHAUSTIVE_SEARCH` to repeat the Boolean rule search.

The centre maps, split decisions and shared encodings were selected using development evidence across waves. Refits assess stability conditional on those choices. A combined five-cluster partition from seven centres differs from a direct fit with five centres.

## Primary fitting and selection

Both notebooks contain the complete primary fitting code directly in their cells, alongside the saved primary results. The worry–harm notebook fits seven centres independently in each wave, reconstructs the original pilot/confirmation shortlist and tests the two declared merges. The worry-only notebook fits both parent and child stages, contains the complete parent and child candidate grids, and repeats the two independent confirmation batches. No course notebook or separately supplied source-code helper is required.

The default run verifies results from saved aggregate centres, including the primary confirmation scores and the uncentred comparison in Supplementary Section S2. The source schedules and settings are in [assets/primary_fitting_protocol.json](assets/primary_fitting_protocol.json), with the complete pilot and confirmation tables alongside it. Recorded implementation checks reproduced every adopted point assignment and 2,242 original native/resampling mass vectors.

- `RUN_PRIMARY_POINT_FITS` repeats the adopted point fits from supplied global pattern aggregates.
- `RUN_PRIMARY_REFITS` repeats the adopted confirmation fits from the original survey CSVs.
- `RUN_PRIMARY_SELECTION` repeats the declared primary candidate grids and confirmation selection.
- `RUN_RAW_SENSITIVITY_REFITS` repeats the reported controlled and strongest confirmed raw comparisons.
- `RUN_RAW_SELECTION` repeats the bounded raw-only search, screen, pilot, sealed shortlist and fresh confirmations.

All five switches are off by default. `PRIMARY_RAW_FOLDER` defaults to `paper/data/`; it should contain `WRP_2019.csv`, `WRP_2021.csv`, `WRP_2023.csv` and `WRP_2025.csv` from the recorded release. The primary protocol records the 2019 checksum as well as those for the later waves. The reader checks original CSV hashes, development-country splits, eligibility and aggregate masses before fitting. Recomputed aggregate results go to `results/`; the supplied model evidence is preserved. The full grid and resampling runs are substantially more expensive than reading the saved results.

## Environment

Use Python 3.11 or later. From this directory, install `requirements.txt` and open the notebooks in JupyterLab. The dependencies are NumPy, pandas, SciPy, scikit-learn, matplotlib, threadpoolctl and Jupyter. The root `requirements.txt` points to this same dependency list.

The checked environment uses Python 3.11, NumPy 1.26.4, pandas 3.0.3, SciPy 1.17.1, scikit-learn 1.8.0 and matplotlib 3.10.9. Saved-result replay is distinct from refitting on another software version. Optional refits can differ in floating-point details.

## Data and evidence

[assets/](assets/) contains the manifests, global answer-pattern counts and masses, fitted centres, fixed centre maps, condition catalogues, country splits, refit evidence and expected results required by these notebooks. Manifests check the retained inputs before calculation. The feature-importance manifest includes aggregate centres and fixed maps for the saved confirmation models; its harm-domain order is checked against the existing question catalogue. Files recording the six- and five-cluster combinations document the selection of the five-cluster result in Supplementary Section S2.

[assets/data_sources.json](assets/data_sources.json) identifies the publisher's release, question coding and original CSV checksums. Obtain survey files separately from [Lloyd’s Register Foundation](https://github.com/lrfoundation/world_risk_poll_data). Use the recorded release rather than silently substituting newer data.

The supplied evidence contains aggregates and country-level split information. It excludes respondent identifiers, respondent-linked assignments, respondent-level survey weights and sampled respondent indices. Raw survey files and private fitting caches must stay outside publication.

## Website

The [World Worry Atlas](https://ionpetre.github.io/WRP-dataset/) provides the interactive presentation. Its source and ready-to-read data are in [../docs/](../docs/). The website can be served locally as a static site. The repository owner handles upload and publication.
