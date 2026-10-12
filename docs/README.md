# Country-similarity maps

Open `index.html` locally in a browser, or use the repository’s GitHub Pages site when enabled. The file is self-contained and works offline. It includes aggregate country information only.

Select a country to inspect it. Choose **overview** for approximate two-dimensional colours, or **distance from selected country** for the original Hellinger distance. Toggle the original dataset-region outlines. The ranked country list can display 10, 20 or all other 141 countries, and always uses original distances rather than visual colour similarity.

The maps compare survey-weighted mixtures of the frozen B4/E8 profiles. They do not show individual respondents, local-model cluster IDs, population sizes, causal relationships or a newly adopted country typology. The overview compresses the geometry; use the list or exact-distance view for close comparisons.

`country-similarity-fragment.html` preserves the original editable interface. `index.html` is its offline standalone export, with D3 embedded and runtime boundary imports replaced by already embedded, verified geometry. The resize-loop repair is retained. Colour data and projection-quality diagnostics are in `../course_artifacts/week05_continuous_country_similarity_maps_v1/`.
