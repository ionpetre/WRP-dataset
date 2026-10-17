# Reading and reproducing the research

## Update: primary T5 model

The 16 October development extension selects T5 as the primary model. See [T5 evidence, parameters and secondary-validation limitations](T5_RESULTS.md). B4/E8 findings below remain historical evidence, not the current primary-model decision.

The current Week 5 notebook contains the optimization, confirmation, profile
review, T5 selection and secondary transfer in Sections 1–5. Appendix A retains
the original B/E analyses. Section numbers 32–34 mentioned in the historical
map-development notes below refer to the earlier notebook, not the current
weekly layout. Run `.week05_build/export_response_profiles.py` to rebuild the
primary T5 explorer from public aggregate tables; no survey data are needed.

## What works without survey data

Read the Markdown guides, inspect aggregate CSV tables and figures, and open `docs/index.html` in a browser to explore the frozen respondent profiles. Country comparisons are in `docs/countries.html`; income patterns are in `docs/country-income.html`. The standalone maps include their country data, boundary geometry and D3 dependency; all three pages work offline and do not need ChatGPT. Source fragments are preserved separately. The profile explorer uses only existing aggregate profile, stability, transfer and overlap tables; its exporter checks that overlap marginals match the frozen profile shares.

The publication does not rerun any scientific fitting. `publication_manifest.json` links published files to original source hashes. Some path strings are sanitized and notebook outputs are cleared, so publication hashes can differ from original artifact hashes. Historical manifests describe the original local execution; missing protected inputs are not evidence of corruption in this deliberately restricted public package.

### Reproduce the new country distances without microdata

The new folder publishes survey-weighted feature/category probabilities, not individual answers. `response_map_payload.json` encodes the same 46 probabilities per country as little-endian float64 values; the CSV makes them readable. The browser reconstructs all five matrices from these aggregates, checked against saved matrices.

From the repository root:

```sh
python .week05_build/test_country_response_distances.py
python .week05_build/test_country_distance_normalization.py
python .week05_build/test_country_median_scaling.py
python .week05_build/test_research_page_links.py
python .week05_build/export_country_response_maps.py --output course_artifacts/week05_country_response_distances_v1/e1ecf01551bcf2da
```

The test checks matrices, allocations, percentile pools, triangle inequalities and USA/Finland comparisons. The exporter regenerates both offline pages from aggregate data and editable templates, without raw responses, fitting or network access. Keep `docs/vendor/d3.min.js` and its licence. Week 5 section 32 reads and verifies saved aggregates, with recomputation disabled by default.

Week 5 section 33 documents fixed diameter normalization. `country_distance_normalization.py` regenerates its separate normalized CSVs and manifest from the original aggregate matrices; it needs no microdata or fitting. Its test checks fixed full-country denominators, the shared B/E scale, symmetry, triangle inequalities and invariant values across display scopes. The map helper independently reconstructs the same maxima from aggregate probabilities, with browser checks against saved results. Raw results are not overwritten.

Section 34 supersedes that display with median-relative scaling. `country_median_scaling.py` regenerates uncapped matrices, examples and colour-ceiling summaries from the same aggregates. Its test verifies pooled/component medians, reciprocal symmetry, scope invariance and values above two. Editable header and stylesheet sources are `.week05_build/research-page-header.html` and `research-page-style.css`; the portable exporter applies them while preserving the offline runtime. No hosting, commit or push is performed by export.

Rebuilding the original weighted aggregates requires protected curated inputs and the recorded freeze seal. `country_response_distances.py` records input fingerprints in a separate result context, validates cohort counts and, when available, checks the protected assignment registry; it never fits profiles. The saved-result reporting cell checks available inputs against the recorded fingerprints. Aggregate-only reconstruction cannot independently verify original individual weights or cohort IDs.

## Python environment

Use Python 3.11 and create a dedicated environment:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
jupyter lab
```

Open notebooks from the repository root or `weekly_notebooks/`. The tested scientific environment used Python 3.11.15, NumPy 1.26.4, pandas 3.0.3, scikit-learn 1.8.0, SciPy 1.17.1 and joblib 1.5.3. These versions are recorded for provenance, not a guarantee that every platform has identical numerical behaviour.

## Full scientific replay requires separate inputs

Obtain the 2023 release and dictionary from Lloyd’s Register Foundation. Use the release fingerprint documented in the Week 3 split record to establish whether it matches the original analysis; newer harmonized releases must not silently replace an older input while claiming an exact replay. The local source release is identified as `LRF_WAVE_3_WITH_INDICES_FOR_PUBLIC_RELEASE_10082024_v2.sav`. The course notebooks use the curated `23_wrp/WRP_2023.*` inputs and `WRP_2023_data_dictionary.csv`; inspect their loading cells for required formats.

Run the data-understanding and curation stages first. Reuse the published frozen country allocation, rather than generating a new one. Regenerate the protected development/held-out data and sampling/fit caches locally. Do not commit these generated files. The public aggregate tables alone cannot reconstruct respondent-level labels, missing responses or individual survey weights.

Run notebooks in their research sequence. The final Week 4 complete-case notebook is the source of B/E reference caches used by Week 5. Some expensive stages have execution switches saved as false; enabling them is an explicit new computation. Fingerprint checks intentionally reject mismatched data/design/caches. Failed reference and repetition records are part of the report; do not delete them or lower thresholds to make a replay pass.

Week 5 includes read-only reporting of the original freeze/transfer and supplemental modules in `.week05_build/`. A complete cache-based replay needs protected local files that this repository deliberately excludes, including `references.joblib`, fit caches, respondent assignments and sealed-package files. The public package is an inspection and reproduction-source release, **not a zero-input one-click reproduction bundle**.

## Frozen assignment without executable model files

`frozen_models/models.json` contains only the inspected centres, specifications, feature order, descriptions and development distance thresholds. Use `frozen_models/public_assignment.py` to load this readable export, then the original assignment functions to encode complete respondents and assign them. Loading this JSON does not verify the original private freeze seal; `publication_manifest.json` records its source bundle hash. Never load untrusted pickle/joblib files from third parties.

Model IDs are preserved: B clusters 0–3 and E clusters 0–7. The transform produces 21 coordinates from 20 complete observed features. Missing-feature respondents must remain unassigned. The assignment module does not fit, select k or retune thresholds.

## Protected outputs and future validation

Keep raw and curated survey data, fit caches, ID-linked handoffs and country-subsample indices outside version control. The supplied `.gitignore` prevents the standard sensitive formats and cache paths from being added accidentally; it is not a substitute for reviewing a commit.

The held-out countries were opened only after the original B4/E8 freeze. They are now used evidence, not an untouched test set for newly redesigned models. Do not rerun selection on them, claim a full-data refit inherits this validation, or call the post-validation country-similarity maps an independent confirmation.


For primary T5 assignments, `load_public_models()` defaults to `T5_models.json`. Use `load_public_models(filename="models.json")` for historical B/E. Public notebooks have outputs cleared and require private data/caches for full replay; no claim of zero-input reproduction is made.
