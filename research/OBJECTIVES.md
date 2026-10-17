# Research objectives

The project studies whether patterns of worry and experienced harm form useful, reproducible descriptions of people’s risk profiles. The present analysis uses one survey wave: 2023. Cross-wave replication is a possible later extension, not part of the completed validation.

## Objective 1 — Discover and validate risk profiles

Construct profiles from six ordered worry questions and seven harm-domain questions. Keep demographic characteristics and country identity out of the clustering. Compare reasonable encodings, harm representations, feature-block weights and clustering methods. Check stability, substantive meaning, geographic variation and transfer to countries not used in model development.

The intended output is a frozen specification: response recoding, eligibility, transformations, weighting, algorithm, number of clusters, centres and assignment rule. Report what the profiles capture beyond total worry and total harm, and where they fail to provide a stable or geographically consistent description.

**Status:** completed through Week 5. WARM-5 is frozen, with explicit limitations. Regional refits are diagnostic; no replacement geographical grouping or country typology was adopted.

## Objective 2 — Predict membership in the frozen profiles

Predict the fixed profile labels using demographic and socioeconomic characteristics, discrimination, social and institutional support, financial resilience and measured country context. Exclude the worry/harm features used to define the labels: otherwise this would largely reconstruct the clustering rule rather than explain membership from external characteristics.

Compare an interpretable baseline with a nonlinear model. Keep countries together in validation folds, fit data-dependent preprocessing inside each training fold and avoid unrestricted country identifiers. Report overall and per-profile performance, class imbalance and geographic variation. Excluded incomplete respondents do not silently acquire profile labels.

**Status:** first WARM-5 prediction analysis completed through Week 6; held-out balanced accuracy is 0.261 and macro-F1 0.223. This is an initial predictive analysis, not strong individual prediction.

## Objective 3 — Test whether profiles add practical value

Choose an external outcome that was not used to form the profiles and is not a direct restatement of worry or harm. On the same eligible respondents and validation splits, compare background predictors alone; background plus overall worry/harm; background plus profiles; background plus both; and background plus the individual risk features.

This tests whether profiles provide a useful summary or additional predictive information. It does not establish a causal effect of belonging to a profile. This objective can use observed frozen labels directly and does not require Objective 2 to succeed first.

**Status:** planned; not completed in this release.

## Objective 4 — Predict worry across domains

Select ordered worry outcomes and compare nested predictor sets: background/context, matching-domain harm, other-domain harm, discrimination/support and, where appropriate, climate/disaster characteristics for severe-weather worry. Use country-grouped validation and report which associations generalize.

Treat the results as predictive associations, not causal explanations. A later-wave analysis requires a separate audit of question wording, response categories and country coverage before waves are combined.

**Status:** planned; not completed in this release.
