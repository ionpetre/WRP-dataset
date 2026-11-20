# World Worry Atlas — paper companion

This repository accompanies *Recurring patterns of worry in the World Risk Poll*. It contains the paper's analytical notebooks, saved aggregate evidence and the World Worry Atlas website. The World Risk Poll is produced by Lloyd’s Register Foundation and conducted by Gallup. [Official survey data and documentation](https://github.com/lrfoundation/world_risk_poll_data).

## Explore the findings

- [World Worry Atlas](https://ionpetre.github.io/WRP-dataset/) introduces the survey and the recurring patterns of worry.
- [Clusters](https://ionpetre.github.io/WRP-dataset/explore.html) presents worry alone in 2019–2025 and worry with reported harm in 2021–2025.
- [Country comparisons](https://ionpetre.github.io/WRP-dataset/countries-by-wave.html) shows maps, distances and changes in cluster shares.
- [Income and education](https://ionpetre.github.io/WRP-dataset/background.html) compares cluster shares and separates reports of personal and known-person harm.

## Reproduce the paper

There are two companion notebooks, each with explanations, code and saved outputs:

- [Worry alone and its comparison with worry and harm](paper/wrp_shared_worry_only.ipynb) verifies the four-wave clustering, the matched fits, Figure 3 and the held-out-country checks.
- [Worry and reported harm](paper/wrp_shared_five_clusters.ipynb) verifies the five-cluster recurrence, common Boolean descriptions, changes in frequency and feature influence. Both notebooks distinguish encoded-coordinate sensitivity from original-question influence.

[Reproduction instructions](paper/README.md) describe the dependencies, supplied evidence and optional calculations. Default execution uses saved aggregate evidence and centres. Original survey records are obtained separately from the publisher.

The `paper/` folder contains the companion and its evidence. The `docs/` folder contains the website. Combined percentages give countries equal influence and concern respondents with complete required answers. They are not world-population shares.

## Author and course

Project lead and course lecturer: **Ion Petre**, University of Turku. The work developed through the **Machine Learning Project Course, 2026–2027**. Survey attribution does not imply endorsement of this analysis.
