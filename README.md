# World Risk Poll: recurring clusters of worry and reported harm

We study which worries and harmful experiences occur together, and whether similar combinations recur in independently collected surveys. The World Risk Poll is produced by Lloyd’s Register Foundation and conducted by Gallup. [Official survey data and documentation](https://github.com/lrfoundation/world_risk_poll_data).

## Start here

- [Accessible overview](https://ionpetre.github.io/WRP-dataset/) introduces the Poll, our questions and the main findings.
- [Reading the survey](https://ionpetre.github.io/WRP-dataset/about.html) explains worry, harm, weighting and the meaning of comparisons.
- [Detailed cluster explorer](https://ionpetre.github.io/WRP-dataset/explore.html) shows all seven full-model clusters, the worry-only results, rules and cross-wave recurrence.
- [Country comparisons](https://ionpetre.github.io/WRP-dataset/countries-by-wave.html) apply these same models to every surveyed country and area. Grey means not surveyed in the selected wave.
- [One complete clustering notebook](paper/wrp_cross_wave_clustering.ipynb) contains code, narrative, numerical checks and saved results. See [reproduction instructions](paper/README.md).

## Main findings

The 2021, 2023 and 2025 full analyses use six worries and all fourteen personal/known-person harm indicators. The jointly selected set of independently fitted seven-cluster models has point ARI 0.95–0.96. Water/food worry, mental-health worry, broad known-person harm and lower severe worry recur more strongly under repeated fitting; they cover 69.90% of the 2025 common-reference weight. Traffic, crime and severe-weather divisions are less consistent. The seven-way partition is not uniformly stable.

Using five worries only, the later waves yield identical three-way point assignments on all 243 complete answer patterns. Most original cross-refit pairs also agree exactly, with occasional alternatives. The 2019 wave remains different; no comparably robust classification covering all four waves was established.

2025 is the primary reporting reference. Within-wave settings were generated independently, then compared jointly using development evidence. Original frozen models remain unchanged and retain their own held-out evidence; that evidence is not transferred to the newly selected seven-cluster set.

## Reproduce and inspect

Start with `paper/`. Its manifest-checked inputs are aggregate answer patterns, centres, country summaries and metadata, without respondent records or respondent-linked assignments. Run All starts no clustering fits. Optional fitting and exhaustive rule enumeration are embedded in the same notebook and disabled by default. The complete catalogue of 47 passing settings and 259 descriptions is retained as alternatives.

The website uses `docs/` as its publication root. Export its final-model data with `python scripts/export_paper_assets.py`. Open it through a local static server for offline inspection. The source is saved locally for the repository owner to upload; no automatic publication is required.

## Historical analyses

[Archive guide](archive/README.md). Historical benchmark pages are outside `docs/` and outside public navigation. Older 2023 prediction notebooks remain supplementary provenance, separate from the complete clustering companion. Historical filenames, source keys and immutable model results are preserved.

Survey attribution does not imply endorsement of this analysis. Percentages in our combined results give countries equal influence and concern complete-answer respondents; they are not world-population shares.

## Course and author

Project lead and course lecturer: **Ion Petre**, University of Turku. This atlas supports the **Machine Learning Project Course, 2026–2027**. The website presents the lecturer’s reference analysis; students develop and explain their own analyses.
