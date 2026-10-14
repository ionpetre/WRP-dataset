# World Risk Poll: risk profiles and geographic validation

Research code and results from the 2026–2027 Machine Learning Project Course, maintained by Ion Petre. This repository records the work completed through Week 5 using the **2023 World Risk Poll**. It is a research record, not the original survey-data repository.

**Current conclusion:** Objective 1 is complete with qualified descriptive conclusions. Frozen K-means **B4** gives a balanced worry/harm description; **E8** gives a complementary, worry-focused description. Held-out-country results support their aggregate interpretation, but do not establish universal social types. Objectives 2–4 remain planned.

## Start here

- [Compare countries: worry and reported harm](https://ionpetre.github.io/WRP-dataset/) — select a country to find peers with similar responses, then examine worry, personal harm or known-person harm separately. Fixed median-relative colours allow comparisons across selected countries. [Offline page](docs/index.html).
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
| 3 | Curate data, freeze the country split and establish the weighted K-means baseline | [Week 3](weekly_notebooks/week03_prepare_the_2023_analysis_data_v16.ipynb) |
| 4 | Complete-case analysis, worry encodings and feature-block weights | [K-means experiments](weekly_notebooks/week04_complete_case_kmeans_worry_encodings_and_weights_final.ipynb) |
| 4 | GMM, Ward, average linkage and DBSCAN, with failures and stability checks | [Alternative methods](weekly_notebooks/week04_alternative_methods_gmm_ward_average_linkage_dbscan_final.ipynb) |
| 4 | Compare retained K-means solutions, overlaps and approximate refinement | [Partition comparisons](weekly_notebooks/week04_kmeans_retained_solutions_overlap_and_refinement_final.ipynb) |
| 5 | Regional analyses, model freeze, held-out transfer, country similarity and Objective 1 closure | [Week 5](weekly_notebooks/week05_regional_validation_and_objective1_finalization.ipynb) |

Notebook code and analytical explanations are retained. Stored execution outputs are cleared to prevent accidental publication of respondent previews; aggregate results and figures are published separately under `course_artifacts/`. Fully executed originals remain in the course workspace. No scientific models were refitted for publication.

## Results folders

The original experiment names and fingerprints are retained so notebook paths and recorded evidence remain traceable. Earlier experiments are **historical results**, not competing final specifications. See the [results guide](research/RESULTS.md) for the authoritative final folders.

`frozen_models/` contains the final centres, feature order, assignment thresholds and a readable JSON model export. `.week05_build/` contains the supplementary Week 5 implementations used by the notebook. `publication_manifest.json` records source and publication hashes.

The 14 October country-distance extension is in `course_artifacts/week05_country_response_distances_v1/e1ecf01551bcf2da/`. It compares the same complete-case respondents without refitting any profile model. The new distances and ranks are exploratory descriptions, not an additional untouched validation. The previous profile-mixture results remain available and are labelled separately.

Raw responses, respondent-level assignments, sampling indices and fit caches are not included. Obtain the survey data from [Lloyd’s Register Foundation](https://www.lrfoundation.org.uk/wrp/world-risk-poll-data), retain its attribution and terms, and follow the reproduction guide.

The existing repository [Apache 2.0 licence](LICENSE) is preserved for project code. Survey data and third-party components retain their own terms; see [attribution](research/DATA_AND_ATTRIBUTION.md).
