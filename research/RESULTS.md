# Results

This public release presents the frozen five-profile model **WARM-5**. See [the full WARM-5 results and limitations](T5_RESULTS.md) and [the methods](METHODS.md).

| Profile ID | Description | Development share | Held-out share |
|---|---|---:|---:|
| T5_C0 | Lower worry | 36.3% | 35.9% |
| T5_C1 | Broad known-person harm | 13.8% | 12.5% |
| T5_C2 | Crime/weather worry | 18.5% | 18.3% |
| T5_C3 | Mental-health/traffic/weather worry | 15.8% | 17.9% |
| T5_C4 | Water/food worry | 15.5% | 15.4% |

Shares give each included country equal influence among complete-case respondents. They are not world-population prevalence.

## Main conclusions

- Development respondent ARI median/lower decile is 0.974/0.946; country values are 0.956/0.913. The weakest profile's country-test lower-decile Jaccard overlap is 0.943.
- All 15 defining contrasts retain their aggregate held-out direction. Mean per-feature category differences range from 0.008 to 0.028. Distance flags rise from 4.95% to 5.69%.
- Transfer is qualified by complete-case selection, small country/profile cells and country-specific weaknesses. The 29 countries are held out from T5 fitting and model selection. Worry coding and worry--harm allocation are optimized using only the 113 development countries; held-out responses and evaluation results do not enter that optimization.
- Of 135 regional reference fits and 5,228 stability fits, none failed computationally. Six coarser alternatives pass both full stability tests; no regional k=5 does so where full tests are available. WARM-5 is a common description, not a universal regional taxonomy.
- Mixture similarity only partly follows geography. The nearest country is in the same region for 23.9%, against an 8.1% random-peer reference.
- Income-gap rank correlation is 0.247 for mixtures and 0.298 for original responses, not evidence of causation.
- Week 6 held-out balanced accuracy is 0.261 and macro-F1 0.223. Prediction from external background variables remains weak.

## Explore and inspect

- [Five-profile explorer](../docs/index.html)
- [Country comparisons](../docs/countries.html)
- [Income patterns](../docs/country-income.html)
- [Exact WARM-5 model](../frozen_models/T5_models.json)
- [Profile transfer table](../course_artifacts/week05_t5_secondary_transfer/832b01713bc6b240/profile_transfer_summary.csv)
- [Regional stability and meanings](../course_artifacts/week05_T5_completion/70ee2f67e95369c5/supported_local_resolutions.csv)
- [Country geography summary](../course_artifacts/week05_T5_completion/70ee2f67e95369c5/countries/country_geography_summary.csv)

No clustering was refitted on all countries. Historical alternative-model records are excluded from this public release and preserved privately.
