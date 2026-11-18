# Website

`index.html` is the plain-language introduction and main findings. `about.html` explains how to read the survey. `explore.html` provides technical cluster results; `countries-by-wave.html` provides development-country maps and distances; `methods.html` defines the analysis and links the complete companion notebook.

All current analytical views load `data/paper-results.*` or `data/paper-country-results.*`, generated from `../paper/assets/` with `python ../scripts/export_paper_assets.py`. The exporter verifies source checksums and final model IDs. Current fixed-definition frequencies use the selected final 2025 seven/three models, not the archived six-cluster model.

Serve this directory with a static server to preview. The repository owner handles GitHub upload and publication. Legacy URLs redirect to corresponding current views. Historical benchmark content is retained outside this publication root under `../archive/historical_benchmarks/docs/` and is absent from current navigation.
