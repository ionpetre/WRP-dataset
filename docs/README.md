# Website

`index.html` is the plain-language introduction and main findings. `about.html` explains how to read the survey. `explore.html` provides technical cluster results; `countries-by-wave.html` provides all-surveyed-country maps and distances; `methods.html` defines the analysis and links the complete companion notebook.

All current analytical views load `data/paper-results.*` or `data/paper-country-results.*`, generated from `../paper/assets/` with `python ../scripts/export_paper_assets.py`. The exporter verifies source checksums and final model IDs. Current fixed-definition frequencies use the selected final 2025 seven/three models, not the archived six-cluster model.

Serve this directory with a static server to preview. The repository owner handles GitHub upload and publication. Legacy URLs redirect to corresponding current views. Historical benchmark content is retained outside this publication root under `../archive/historical_benchmarks/docs/` and is absent from current navigation.

All five pages share the same sticky navigation. Author/course information is prominent and consistent. The overview timeline, recurring-cluster shares and interactive trend chart reuse the published aggregates. `overview.js` reads the same data as the cluster explorer.

The overview shows every one of the seven worry–harm clusters. Literal Boolean rules are accompanied by restrained readings, precision and coverage. Its shares and rule scores use one 2025 reference population (90,395 complete respondents in 92 countries). `export_paper_assets.py` includes these verified scores from the companion’s rule-transfer table. The detailed explorer retains native-development reporting, explicitly identified on that page.
