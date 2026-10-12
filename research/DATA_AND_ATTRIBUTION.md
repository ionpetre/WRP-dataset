# Publication scope and attribution

## Included and excluded

This release includes seven current Week 1–5 notebooks, supporting Week 5 code, aggregate tables, aggregate figures, frozen model centres/specifications and country-level map data. Earlier aggregate experiments are retained under their original folders to document the research sequence, including failures. Obsolete notebook versions are not republished.

It excludes raw/curated respondent records, survey-response previews, ID-linked assignments, individual weights, sampled respondent indices and fit-cache objects. Stored notebook execution outputs are cleared; analytical text remains. Original executed notebooks, immutable seals and private handoffs are preserved locally and were not changed by publication.

Some country/profile aggregates have small sample sizes. Counts, effective sample sizes and uncertainty warnings must be considered when interpreting them. They are descriptive research diagnostics, not precise estimates for small groups or instructions to identify individuals. Neither the project licence nor this release grants a new licence for the underlying survey microdata.

## Survey source

Credit **Lloyd’s Register Foundation World Risk Poll**, with survey data collected by Gallup. Obtain data and applicable citation/terms from the [official data page](https://www.lrfoundation.org.uk/wrp/world-risk-poll-data) or [official data repository](https://github.com/lrfoundation/world_risk_poll_data). The Foundation describes the data as available for reuse with attribution. This analysis concerns the 2023 wave; the exact local release fingerprint is recorded in the Week 3 split provenance. A later harmonized source is not necessarily byte-identical to that release.

This project is independent analysis for teaching and research, not an official Foundation/Gallup publication or endorsement. Report dates and interview dates should not be confused: the analysed interviews were collected in 2023.

## Code and map components

The repository’s existing Apache 2.0 licence is preserved. Third-party components retain their own terms:

- D3 7.9.0: ISC licence, reproduced in [D3-LICENSE](../docs/vendor/D3-LICENSE), with its notice retained in the offline map bundle.
- Country boundary geometry: published `@d3-maps/atlas` 1.0.0, converted with topojson-client 3.1.0. Geometry is embedded rather than redrawn by hand. The [topojson licence](../docs/vendor/TOPOJSON-LICENSE) accompanies the source dependency.
- Natural Earth boundary and label-point data: [public-domain terms](https://www.naturalearthdata.com/about/terms-of-use/). Made with Natural Earth. Approximate boundaries and small-country markers are presentation aids, not political claims.
- The standalone interface includes exported presentation utilities/state fallback from the authoring environment. It does not call ChatGPT or require an account.

Region outlines follow the dataset’s original `GlobalRegion` allocation. New geographic regions were not invented from the map colours. Country rankings use original Hellinger distances, not colours or country-tree cluster numbers.
