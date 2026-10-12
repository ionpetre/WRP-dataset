# Reading and reproducing the research

## What works without survey data

Read the Markdown guides, inspect aggregate CSV tables and figures, and open `docs/index.html` in a browser. The standalone map includes its country data, boundary geometry and D3 dependency; it makes no survey-data request and does not need ChatGPT. Its source fragment is preserved separately.

The publication does not rerun any scientific fitting. `publication_manifest.json` links published files to original source hashes. Some path strings are sanitized and notebook outputs are cleared, so publication hashes can differ from original artifact hashes. Historical manifests describe the original local execution; missing protected inputs are not evidence of corruption in this deliberately restricted public package.

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
