# Reading and reproducing the WARM-5 results

## Without survey data

Open `docs/index.html`, `docs/countries.html` or `docs/country-income.html`. They work offline, including their controls, embedded aggregate data, map boundaries and D3 dependency. Supporting repository links require internet access.

The profile explorer shows only WARM-5. Map code reconstructs original-response distances from 32 country-level values: 18 category probabilities for the six worry questions and 14 harm prevalences. For binary harm, total variation is the absolute prevalence difference; the complementary no-harm probability need not be stored. This is a lossless storage simplification, not a change to clustering or distances. The overall allocation is always worry 58.38%, personal harm 20.81%, known-person harm 20.81%.

Edit the map fragments under `docs/` and run:

```sh
python .week05_build/rebuild_T5_pages.py
```

This refreshes the offline wrappers; it does not refit clustering or change aggregate inputs. Exact matrices are also published under `course_artifacts/week05_T5_completion/70ee2f67e95369c5/countries/`.

The compact inputs are available as a [32-value country summary CSV](../course_artifacts/week05_T5_completion/70ee2f67e95369c5/countries/T5_country_response_summary32.csv) and [map-input JSON](../course_artifacts/week05_T5_completion/70ee2f67e95369c5/countries/T5_country_response_summary32.json). Each row describes one country, not one respondent. Historical full category tables remain valid: they also list the complementary no-harm probabilities, which current distance calculations do not need.

## Assign WARM-5 to separately supplied survey responses

`frozen_models/T5_models.json` contains the exact stored centres, feature order, recoding information, profile names and development distance thresholds. `frozen_models/public_assignment.py` loads this readable model and assigns complete responses without fitting. Do not load third-party executable pickle/joblib files.

Use unique `WPID_RANDOM` identifiers to join assignments. Require substantive answers to all six worry and seven original harm questions; this gives 20 separate worry/personal/known-person features. Missing-feature respondents remain unassigned. Preserve T5_C0–T5_C4 and stored centre order. Never substitute row position for an ID join or refit on all countries.

## Python and inputs

Use Python 3.11 with `requirements.txt`. The tested scientific environment used Python 3.11.15, NumPy 1.26.4, pandas 3.0.3, scikit-learn 1.8.0, SciPy 1.17.1 and joblib 1.5.3. Exact numerical reproducibility can depend on the platform and runtime.

Obtain the 2023 data and dictionary from Lloyd's Register Foundation. The original source release was `LRF_WAVE_3_WITH_INDICES_FOR_PUBLIC_RELEASE_10082024_v2.sav`; the course uses curated `23_wrp/WRP_2023.*` inputs. A newer harmonized release must not silently replace that input while claiming exact replay. Reuse `course_artifacts/week03_country_split.csv`, rather than drawing another split.

The Week 3 notebook prepares the data. The Week 5 notebook shows the WARM-5 feature transform, ordinary weighted K-means declaration, fixed-centre assignment, regional prevalence and country distances. Expensive search, stability, explanation and transfer summaries read saved tables. The Week 6 notebook contains the WARM-5 prediction implementation.

This release deliberately excludes historical alternative-model records and original search runners. Published selection tables are restricted views; the complete original history and private sampling/fit caches remain in the course archive. Full scientific replay needs those original inputs, records and runtime: this is not a zero-input, one-click reproduction bundle. Do not interpret omitted historical records as evidence that no alternatives were tested.

## Validation and privacy

The 29 countries are held out from T5 fitting and model selection. Worry coding and worry--harm allocation are optimized using only the 113 development countries; held-out responses and evaluation results do not enter that optimization. All-country maps are descriptive extensions. A full-data refit would create a different model and would not inherit this validation.

Raw/curated responses, respondent-linked assignments, executable fits and sampling indices are excluded. Notebook outputs are cleared; aggregate tables and figures are supplied separately. `publication_manifest.json` records source/publication hashes and modified public views. Aggregate publication is not a formal disclosure-risk certification; some country/profile cells are small.
