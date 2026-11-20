# Companion to *Recurring patterns of worry in the World Risk Poll*

The two notebooks below contain the paper's explanations, analytical code and saved outputs. Run All uses supplied aggregate evidence and saved centres. Expensive searches and fitting remain off by default.

## Worry alone and comparisons with worry and harm

Open [wrp_shared_worry_only.ipynb](wrp_shared_worry_only.ipynb). It verifies the four recurring worry-only clusters in 2019, 2021, 2023 and 2025, compares them with the five worry–harm clusters, and replays the matched fits with the same worry questions and number of clusters. It reproduces [Figure 3](results/figure3_harm_by_worry.pdf), the original harm rates, the within-country contrasts and the fixed-model and rule checks in the 25 held-out countries. These checks are described in Supplementary Sections S4 and S7. Tables and the figure are saved in [results/](results/).

To verify the harm summaries from original survey answers, obtain the CSV files recorded in [assets/matched_harm_schedule.json](assets/matched_harm_schedule.json), put them in `paper/data/`, and set `RAW_WAVE_DIR` in the notebook if needed. Enable `RUN_SURVEY_REPLAY`. The notebook checks the survey file hashes and applies the recorded country splits and frozen models. The separate `RUN_MATCHED_FITS` switch repeats the matched fits using the original draws and seeds. Both switches are off by default.

## Worry and reported harm

Open [wrp_shared_five_clusters.ipynb](wrp_shared_five_clusters.ipynb). It checks the independently fitted seven-centre models and their fixed maps to five clusters, reproduces cross-wave agreement and individual-cluster recovery from all saved refit pairs, checks the common rules in each development population, and recalculates frequency changes under the fixed 2025 definition. The default run does not refit the clustering. Set `RUN_EXHAUSTIVE_SEARCH` to repeat the Boolean rule search.

The centre maps, split decisions and shared encodings were selected using development evidence across waves. Refits assess stability conditional on those choices. A combined five-cluster partition from seven centres differs from a direct fit with five centres.

## Environment

Use Python 3.11 or later. From this directory, install `requirements.txt` and open the notebooks in JupyterLab. The dependencies are NumPy, pandas, SciPy, scikit-learn, matplotlib, threadpoolctl and Jupyter. The root `requirements.txt` points to this same dependency list.

The checked environment uses Python 3.11, NumPy 1.26.4, pandas 3.0.3, SciPy 1.17.1, scikit-learn 1.8.0 and matplotlib 3.10.9. Saved-result replay is distinct from refitting on another software version. Optional refits can differ in floating-point details.

## Data and evidence

[assets/](assets/) contains the manifests, global answer-pattern counts and masses, fitted centres, fixed centre maps, condition catalogues, country splits, refit evidence and expected results required by these notebooks. Manifests check the retained inputs before calculation. Files recording the six- and five-cluster combinations document the selection of the five-cluster result in Supplementary Section S2.

[assets/data_sources.json](assets/data_sources.json) identifies the publisher's release, question coding and original CSV checksums. Obtain survey files separately from [Lloyd’s Register Foundation](https://github.com/lrfoundation/world_risk_poll_data). Use the recorded release rather than silently substituting newer data.

The supplied evidence contains aggregates and country-level split information. It excludes respondent identifiers, respondent-linked assignments, respondent-level survey weights and sampled respondent indices. Raw survey files and private fitting caches must stay outside publication.

## Website

The [World Worry Atlas](https://ionpetre.github.io/WRP-dataset/) provides the interactive presentation. Its source and ready-to-read data are in [../docs/](../docs/). The website can be served locally as a static site. The repository owner handles upload and publication.
