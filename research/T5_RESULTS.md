# T5: primary five-profile model — 16 October 2026

Decision and scope. T5 is the approved primary model to take forward. The exact development reference is sealed, not refitted: k=5, q=0.41670089020376244, t=2.399802888616365, alpha=0.5837857862168715. T5_C0,...,T5_C4 preserve its stored centre order. B4/E8 and every historical result remain available as benchmarks. The publication profile explorer now defaults to T5. Country-distance pages retain historical B/E metrics, explicitly labelled; the manuscript and Week 6 remain unchanged.

Shallow explanations. All five country-grouped folds were used. With the two original-unit burden scores, depths 1/2/3 achieved mean balanced accuracies 32.7%, 46.0% and 51.2%. The additional trees supplied with all 20 original features achieved 36.8%, 54.0% and 67.9%; depth 5 reached 73.7%. At depth 3, broad known-person-harm recall was only 19.3%, despite high recall for lower worry. These trees capture useful patterns but do not nearly reconstruct the entire typology. The strongest single-feature rule uses water worry, with balanced accuracy 88.3%, precision 67.4% and recall 84.3%. This is an informative marker, not a near-unique cluster definition. A depth-1 multiclass tree has at most two leaves and depth 2 at most four: for five nonempty classes their balanced-accuracy ceilings are 40% and 80%. Low shallow scores alone therefore cannot prove complexity. No new automatic rejection cutoff was introduced. Ordinary greedy Gini trees were used; this does not rule out every possible optimized rule set or establish that the profiles are natural latent types. The fixed cluster labels were originally learned using all development countries, so this cross-validation assesses explanatory fidelity, not fully independent clustering generalization.

Transfer population. Apply the sealed centres to 27,972 complete respondents from all 29 held-out countries. The other 2,118 of 30,090 respondents remain unassigned because of missing profile responses. A separate ID-linked T5 handoff includes all 146,910 prepared respondents: 137,460 assigned and 9,450 excluded. Do not fill excluded labels, join by row order, or substitute T5 cluster numbers into B/E columns.

Prevalence. Development to held-out equal-country shares are: Lower worry 36.3% to 35.9%; Broad known-person harm 13.8% to 12.5%; Crime/weather worry 18.5% to 18.3%; Mental-health/traffic/weather worry 15.8% to 17.9%; Water/food worry 15.5% to 15.4%. Different prevalence is allowed and was not used to retune the model.

Profile identity. All 15/15 development-selected anchor directions remain positive in aggregate held-out data. Mean feature total variation within profiles ranges from 0.0083 to 0.0281; the largest single-feature difference is 0.0554. This measures original-category distribution shifts, not centroid distances, ARI, or a newly defined pass/fail score. Semantic retention partly follows from assigning people using these same features; it supports portability of this fixed description, not independent discovery of the same groups.

Assignment quality. Overall median distance changes by a factor 1.0048; median assignment margin changes from 0.1515 to 0.1524. The fraction beyond the assigned-profile development distance p95 changes from 4.95% to 5.69%. Flags identify less typical assigned responses, not unassigned cases, misclassification probabilities or an overall rejection rule.

Country limitations. The largest distance-flag fractions are Sierra Leone 18.8% (complete-response retention 78.7%); Namibia 16.9% (complete-response retention 94.4%); Somalia 16.7% (complete-response retention 82.9%). Global averages conceal these weaknesses. Country/profile tables include respondent counts and Kish weighted effective sizes; very small groups have uncertain conditional descriptions. For example, Sweden's water/food group contains only 15 respondents (Kish effective size 9.8), so its mean feature total variation of .200 is poorly estimated. Somalia's water/food group has mean feature total variation .225 with 173 respondents (effective size 138.8): this is a substantive country-specific shift that cannot simply be dismissed as a 15-person group. These examples qualify any claim that all five profile meanings reproduce equally well in every country. Complete-case selection may change apparent country profiles; the assessment does not establish representativeness of respondents excluded for missing answers.

Uncertainty and conclusion. The 1,000 country bootstrap intervals keep the model fixed and preserve relative survey weights within each sampled country. They describe variation over these 29 observed countries, not all-world sampling, respondent nonresponse, model fitting or parameter-selection uncertainty. The results support broad aggregate descriptive transfer of T5, with material country-specific qualifications. No automatic numerical transfer criterion had been specified; this is an analytical synthesis using the same diagnostic framework as the earlier B/E assessment. The held-out countries were previously examined for B/E and the new search was undertaken after those results were known. This must be reported as secondary transfer assessment, not pristine external confirmation. No new local-region clustering, independent held-out clustering or all-data refit was performed. T8 remains exploratory, not a co-equal main model.


## Evidence and reuse

- [Evaluation completion and publication scope](../course_artifacts/week05_t5_secondary_transfer/832b01713bc6b240/evaluation_finalization.json).
- [Week 5 workflow](../weekly_notebooks/week05_validate_frozen_profiles.ipynb): grid search, adaptive extension, fresh confirmation, profile review, selection, freeze and secondary transfer.
- [Exact readable model](../frozen_models/T5_models.json). Stored IDs are T5_C0 through T5_C4; never substitute them into B/E columns.
- [Transfer summary](../course_artifacts/week05_t5_secondary_transfer/832b01713bc6b240/profile_transfer_summary.csv).
- [Original held-out categories](../course_artifacts/week05_t5_secondary_transfer/832b01713bc6b240/heldout_original_category_profiles.csv).
- [Country quality and retention](../course_artifacts/week05_t5_secondary_transfer/832b01713bc6b240/heldout_country_quality_and_retention.csv).
- [Profile-level country shifts and sample sizes](../course_artifacts/week05_t5_secondary_transfer/832b01713bc6b240/heldout_profile_semantic_differences.csv).
- [Verification](../course_artifacts/week05_t5_secondary_transfer/832b01713bc6b240/verification.json).

![Profile prevalence](../course_artifacts/week05_t5_secondary_transfer/832b01713bc6b240/t5_prevalence_transfer.png)

![Original-response meaning](../course_artifacts/week05_t5_secondary_transfer/832b01713bc6b240/t5_original_response_transfer.png)

The public package intentionally excludes respondent-level handoffs, label arrays,
sampling indices and fit caches. Model centres alone permit assignment of complete
responses when survey data are supplied separately; no all-country refit is needed.
Country maps still show explicitly labelled historical B/E comparisons. Week 6
and the manuscript have not been migrated in this publication update.
