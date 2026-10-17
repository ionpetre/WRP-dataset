# World Risk Poll: five worry and harm profiles

Research code and results from the 2026–2027 Machine Learning Project Course, maintained by Ion Petre. This release presents **T5**, the frozen five-profile model of the 2023 World Risk Poll.

T5 has one specification: worry coding 0 / 1 / 2.399802888616365, followed by division by that top value; worry allocation **58.38%**, personal harm **20.81%**, and known-person harm **20.81%**. These are nominal allocations in the feature geometry, not measured percentages of each respondent's distance. There is no alternative balanced or worry-emphasized model in this release.

## Explore the results

- [Response profiles](https://ionpetre.github.io/WRP-dataset/) — the five profiles, their original worry and harm answers, prevalence and validation evidence. [Offline page](docs/index.html).
- [Compare countries](https://ionpetre.github.io/WRP-dataset/countries.html) — compare original answer distributions or proportions across the same five profiles. [Offline page](docs/countries.html).
- [Income patterns](https://ionpetre.github.io/WRP-dataset/country-income.html) — compare country responses within and between income groups. [Offline page](docs/country-income.html).
- [Results and limitations](research/T5_RESULTS.md)
- [Methods and mathematical definitions](research/METHODS.md)
- [Research objectives](research/OBJECTIVES.md)
- [Reproduction and data requirements](research/REPRODUCING.md)
- [Data attribution](research/DATA_AND_ATTRIBUTION.md)

Component maps isolate worry, personal harm or known-person harm. They are not separately fitted clusterings. The two country-comparison summaries answer different questions: original categories retain marginal answer detail; five profile proportions compress it. Neither measures general societal similarity.

## Current evidence

Development stability is strong: respondent ARI median/lower decile 0.974/0.946; country values 0.956/0.913. Secondary held-out assessment supports aggregate descriptive transfer, with country-specific limitations. Independent regional fits do not support five stable groups everywhere: six coarser alternatives pass both full tests. T5 is a useful common global description, not proof of five universal social types.

Week 6 predicts T5 membership from external variables. Held-out balanced accuracy is 0.261 and macro-F1 0.223; individual prediction remains weak.

## Code

| Week | Purpose | Notebook |
|---|---|---|
| 1 | Understand the 2023 data | [Week 1](weekly_notebooks/week01_understand_2023_and_develop_questions.ipynb) |
| 2 | Define the research objectives | [Week 2](weekly_notebooks/week02_define_the_research_design.ipynb) |
| 3 | Curate data and establish the baseline | [Week 3](weekly_notebooks/week03_prepare_2023_data_and_kmeans.ipynb) |
| 5 | Select, freeze and validate T5; compare regions and countries | [Week 5](weekly_notebooks/week05_validate_frozen_profiles.ipynb) |
| 6 | Predict frozen T5 membership | [Week 6](weekly_notebooks/week06_predicting_frozen_risk_profile_membership.ipynb) |

Historical alternative-model notebooks and records are excluded from this public release and preserved in the private course archive. Published selection tables retain the tuned candidate comparisons, without historical benchmark rows. This is a T5-focused subset of the research, not a claim that no alternatives were tested.

Notebook outputs are cleared; aggregates and figures are under `course_artifacts/`. `frozen_models/T5_models.json` contains readable centres and assignment information. Original responses, respondent-linked assignments, fit caches and sampling indices are not published. Obtain the survey data separately from [Lloyd's Register Foundation](https://www.lrfoundation.org.uk/wrp/world-risk-poll-data).

## Update GitHub

Upload the contents of this folder to the repository root, preserving directories. **Also remove the previously published files that are absent from this release:** adding or replacing files through GitHub's upload interface does not delete old files. Do not upload the parent course folder or private archive. Nothing has been committed or pushed from this workspace.

GitHub Pages should publish `docs/`. All three pages work offline. Supporting repository links need internet access.

The repository's [Apache 2.0 licence](LICENSE) is retained for project code; survey data and third-party components keep their own terms.
