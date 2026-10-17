# World Risk Poll: risk profiles and geographic validation

Research code and results from the 2026–2027 Machine Learning Project Course, maintained by Ion Petre. This repository records the work completed through Week 5 using the **2023 World Risk Poll**. It is a research record, not the original survey-data repository.

**Current conclusion (16 October 2026):** T5 is the primary five-profile description after development-only optimization of worry coding and worry–harm allocation. Its secondary held-out assessment supports broad aggregate transfer, with important country-specific limitations. B4/E8 remain historical benchmarks. See [T5 results and limitations](research/T5_RESULTS.md). Week 6 is an earlier B/E prediction draft, not a T5 evaluation.

For this update, upload the contents of this `github_publication` folder to the
repository root, preserving its directories and hidden source folders. Do not
upload the parent course folder, raw data, respondent assignments or fit caches.
The local package has not been committed or pushed. The T5 profile explorer is
in `docs/index.html`; country-distance pages intentionally retain clearly labelled
historical B/E comparisons. Current audit records are `publication_audit.json`
and `publication_profile_test.json`.

## Start here

- [Explore response profiles](https://ionpetre.github.io/WRP-dataset/) — inspect the primary five-profile model and historical four- and eight-profile solutions, original worry and harm responses, distinctive contrasts and respondent overlaps. Includes stability and held-out evidence. [Offline page](docs/index.html).
- [Compare countries: worry and reported harm](https://ionpetre.github.io/WRP-dataset/countries.html) — select a country to find peers with similar responses, then examine worry, personal harm or known-person harm separately. Fixed median-relative colours allow comparisons across selected countries. [Offline page](docs/countries.html).
- [Explore response patterns by country income](https://ionpetre.github.io/WRP-dataset/country-income.html) — inspect income-group maps and compare responses within and between income groups. Income provides context; it is not an input to country similarity. [Offline page](docs/country-income.html).
- [Project objectives](research/OBJECTIVES.md)
- [Results and interpretation](research/RESULTS.md)
- [Methods, encodings and validation](research/METHODS.md)
- [Reproduction and data requirements](research/REPRODUCING.md)
- [Publication scope and attribution](research/DATA_AND_ATTRIBUTION.md)

## Weekly code

| Week | Purpose | Notebook |
|---|---|---|
| 1 | Understand the 2023 data and develop research questions | [Week 1](weekly_notebooks/week01_understand_2023_and_develop_questions.ipynb) |
| 2 | Define the research design and objectives | [Week 2](weekly_notebooks/week02_define_the_research_design.ipynb) |
| 3 | Curate data and establish the baseline | [Week 3](weekly_notebooks/week03_prepare_2023_data_and_kmeans.ipynb) |
| 4 | Compare encodings, block allocation and clustering methods | [Week 4](weekly_notebooks/week04_profile_robustness_and_selection.ipynb) |
| 5 | Optimize t/alpha, confirm, review, select T5, freeze and assess transfer | [Week 5](weekly_notebooks/week05_validate_frozen_profiles.ipynb) |
| 6 | Earlier B/E prediction draft; not yet migrated to T5 | [Week 6](weekly_notebooks/week06_predicting_frozen_risk_profile_membership.ipynb) |

Notebook code and analytical explanations are retained. Stored execution outputs are cleared to prevent accidental publication of respondent previews; aggregate results and figures are published separately under `course_artifacts/`. Fully executed originals remain in the course workspace. No scientific models were refitted for publication.

## Results folders

The original experiment names and fingerprints are retained so notebook paths and recorded evidence remain traceable. Earlier experiments are **historical results**, not competing final specifications. See the [results guide](research/RESULTS.md) for the authoritative final folders.

`frozen_models/T5_models.json` contains the primary model; `models.json` retains historical B/E. `frozen_models/` contains the stored centres, feature order, assignment thresholds and a readable JSON model export. `.week05_build/` contains the supplementary Week 5 implementations used by the notebook. `publication_manifest.json` records source and publication hashes.

The 14 October country-distance extension is in `course_artifacts/week05_country_response_distances_v1/e1ecf01551bcf2da/`. It compares the same complete-case respondents without refitting any profile model. The new distances and ranks are exploratory descriptions, not an additional untouched validation. The previous profile-mixture results remain available and are labelled separately.

Raw responses, respondent-level assignments, sampling indices and fit caches are not included. Obtain the survey data from [Lloyd’s Register Foundation](https://www.lrfoundation.org.uk/wrp/world-risk-poll-data), retain its attribution and terms, and follow the reproduction guide.

The existing repository [Apache 2.0 licence](LICENSE) is preserved for project code. Survey data and third-party components retain their own terms; see [attribution](research/DATA_AND_ATTRIBUTION.md).
