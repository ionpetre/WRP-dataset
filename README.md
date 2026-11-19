# World Risk Poll: recurring clusters of worry and reported harm

We study which worries and harmful experiences occur together, and whether similar combinations recur in independently collected surveys. The World Risk Poll is produced by Lloyd’s Register Foundation and conducted by Gallup. [Official survey data and documentation](https://github.com/lrfoundation/world_risk_poll_data).

## Start here

- [Worry–Harm Atlas](https://ionpetre.github.io/WRP-dataset/) introduces the World Risk Poll and the five recurring clusters.
- [Reading the survey](https://ionpetre.github.io/WRP-dataset/about.html) explains worry, harm, weighting and the meaning of comparisons.
- [Detailed cluster explorer](https://ionpetre.github.io/WRP-dataset/explore.html) shows the five shared clusters, their rules and cross-wave recurrence.
- [Country comparisons](https://ionpetre.github.io/WRP-dataset/countries-by-wave.html) apply these same models to every surveyed country and area. Grey means not surveyed in the selected wave.
- [Worry alone](https://ionpetre.github.io/WRP-dataset/worry-only.html) follows four worry clusters back to 2019 and shows what asking about harm adds.
- [Income and education](https://ionpetre.github.io/WRP-dataset/background.html) compares how the five clusters and reports of harm are distributed within countries.
- [Five-cluster notebook](paper/wrp_shared_five_clusters.ipynb) reproduces the main comparisons and common rules. See [reproduction instructions](paper/README.md).

## Main findings

Five clusters recur in 2021, 2023 and 2025. Each wave uses the same worry–harm encoding and fits its centres independently. The lowest cross-wave 10th-percentile ARI is 0.904, and the lowest cluster Jaccard is 0.843. One rule per cluster reaches at least 80% precision in each wave.

## Reproduce and inspect

Start with the five-cluster notebook in the paper folder. It verifies saved model assignments, all cross-wave refit comparisons, the common rules and changes in frequency under the fixed 2025 model. Its inputs are aggregate answer patterns, centres and country summaries. The website in the docs folder reads the same five-cluster aggregates and can be viewed with a local static server.

## Historical analyses

[Archive guide](archive/README.md). Historical benchmark pages are outside `docs/` and outside public navigation. Older 2023 prediction notebooks remain supplementary provenance, separate from the complete clustering companion. Historical filenames, source keys and immutable model results are preserved.

Survey attribution does not imply endorsement of this analysis. Percentages in our combined results give countries equal influence and concern complete-answer respondents; they are not world-population shares.

## Course and author

Project lead and course lecturer: **Ion Petre**, University of Turku. This atlas supports the **Machine Learning Project Course, 2026–2027**. The website presents the lecturer’s reference analysis; students develop and explain their own analyses.
