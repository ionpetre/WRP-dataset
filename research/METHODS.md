# Encodings, weighting and validation

## Data and country split

The curated 2023 dataset contains 146,910 respondents in 142 countries. A country-level split was selected once and then reused: 113 development countries (116,820 respondents) and 29 held-out countries (30,090 respondents). Countries, not individual respondents, are the split unit. The allocation balances the original global-region and country-income composition; its exact country list is in `course_artifacts/week03_country_split.csv`.

Within an analysis cohort, respondent survey weights are normalized to give every included country the same total influence:

$$w_i=\frac{WGT_i}{\sum_{j\in c(i)}WGT_j}\frac{1}{C}.$$

This is a country-balanced estimand, not a world-population estimate. Renormalize after restricting the cohort. Development and held-out weights each sum to one; their concatenation is not an all-country weighting scheme.

## Response encoding and missingness

The six worry domains are food, water, crime, severe weather, traffic and mental health. Original worry codes 1/2/3 mean very/somewhat/not worried and are recoded to 2/1/0. Codes 98/99 remain missing. The seventh harm domain is work.

For combined harm, original codes 1/2/3 become 1 (respondent, known person, or both harmed); code 4 becomes 0 (neither harmed). For separate harm:

| Original code | Respondent harmed | Known person harmed |
|---|---:|---:|
| 1 | 1 | 0 |
| 2 | 0 | 1 |
| 3 | 1 | 1 |
| 4 | 0 | 0 |
| 98 or 99 | missing | missing |

Week 3 uses development-wide medians, not country-specific medians, followed by development-fitted z-standardization. Respondents with no observed profile feature are not clustered. The frozen data themselves are not imputed.

The final Week 4/5 branch uses **complete cases without imputation**: all six worry and seven original harm responses must be substantive, giving all 20 separate-harm features. There are 109,488 eligible development respondents and 27,972 eligible held-out respondents. This changes the target population and creates a selection limitation; missingness and exclusion audits accompany the results.

## Feature geometry

Worry codings 0/1/2, 0/1/3 and 0/1/5 are divided by their top value, placing the categories in [0,1]. This changes the middle category’s relative position. Combined and separate harm are compared in the development experiments.

For the final complete-case geometry, let $x_d$ be a normalized worry value and $m=\frac{1}{6}\sum_d x_d$. Use six relative-worry coordinates and one reduced overall-worry coordinate:

$$z_d=(x_d-m)\sqrt{\alpha/6},\qquad z_m=m\sqrt{\alpha/6}.$$

For each harm coordinate $h_j$, use

$$z_{h_j}=h_j\sqrt{(1-\alpha)/H},$$

where $H=7$ for combined harm and $H=14$ for separate harm. Test balanced ($\alpha=0.50$), worry-emphasized ($0.75$) and harm-emphasized ($0.25$) settings. The square roots matter because Euclidean squared distance squares each multiplier. Division by block size prevents merely adding harm coordinates from doubling their nominal block allocation. This is a controlled geometry, not a claim that empirical distance contributions are exactly equal. The reduced overall-worry coordinate deliberately receives only one coordinate’s multiplier, not six copies of the mean.

| Final model | Worry coding | Harm | Worry allocation | k | Method |
|---|---|---|---:|---:|---|
| B4 | 0/1/2, divided by 2 | Separate personal/known-person | 0.50 | 4 | Equal-country-weighted K-means |
| E8 | 0/1/3, divided by 3 | Separate personal/known-person | 0.75 | 8 | Equal-country-weighted K-means |
| Retained Ward comparison | 0/1/3, divided by 3 | Separate personal/known-person | 0.75 | 8 | Bootstrap hierarchy plus centroid extension |

No PCA is used in respondent clustering. The two-dimensional country-colour projection is only a map-display approximation and does not change profiles or assignment.

## Algorithms tested

Weighted K-means is the reference. The alternative-method search uses the same complete-case relative/overall worry geometry, separate harm, 0/1/2 and 0/1/3 encodings, all three block allocations and k=2,…,10 where applicable.

- **Gaussian mixture models:** diagonal and full covariance, five initializations, maximum 300 iterations, covariance regularization 0.001. Fit a country-balanced, survey-weighted bootstrap because this fitting implementation does not accept the K-means respondent weights directly.
- **Ward and average-linkage agglomerative clustering:** draw 150 respondents per country with replacement, using within-country survey-weighted probabilities: 16,950 reference leaves for 113 countries. Fit the native tree, cut it at the requested k, and extend labels to the full cohort using nearest native-cluster centroids. This is not native hierarchical clustering of all respondents. Bootstrap draws are redrawn within each stability training population. Native-versus-extension agreement is recorded.
- **DBSCAN:** test min_samples 20/50/100 and radius grids derived from declared neighbour-distance quantiles. Use equal-country density mass, explicit memory/edge guards and nearest-core transport within the fitted radius. Preserve training labels and leave unassigned respondents as noise. Its cluster count is an outcome, not a fixed k.

Ward and K-means both use squared-Euclidean compactness, and centroid extension adds another shared element. Their agreement is corroborating evidence, not independent proof of a natural typology.

## Global structural screen and stability

Require at least three and at most ten clusters, largest assigned-cluster weighted share at most 40%, and dominance $D=k\max_c p_c<3$. DBSCAN additionally needs at least 90% assigned coverage. Computational failures remain failures; they are not converted into statistical rejection or silently dropped.

For each structurally eligible candidate, fit 50 respondent subsamples and 50 stratified country subsamples. Each uses 80% sampling without replacement within its specified sampling unit. Transport fitted labels to the common comparison population, then calculate all $\binom{50}{2}=1,225$ pairwise ARIs per test. Retention requires **median and lower-decile ARI ≥0.80 in both tests**, all repetitions successful and acceptable group counts. DBSCAN also reports joint-assignment coverage; the lower-decile jointly assigned weight must reach 90% in both tests. ARI is a label-invariant, chance-adjusted partition comparison; the reported dependent-pair quantiles are not confidence intervals.

Inspect original-unit semantics, cluster recovery, one-feature reconstruction, burden reconstruction and overlaps after numerical screening. A stable partition can still be a poor substantive summary. Approximate refinement uses directional overlap purity; it is not a mathematical lattice.

## Week 5 regional and held-out checks

First apply the unchanged global centres within each original dataset region. Separately fit regional solutions with the B/E geometry, search k=2,…,10, and test shortlisted resolutions. Keep the 0.80 ARI rule. In regions with two to four development countries use leave-one-country-out diagnostics; with one country, country stability is unavailable. Report repeated country subsets and limited independent information. Global size filters are regional benchmarks, not automatically regional rejection rules. Stable k=2 solutions are diagnostic, not rich final regional typologies.

B4/E8 were sealed at **2026-10-12 09:44:34 UTC**, before the recorded held-out response read at **09:46:25 UTC**. The original centres, IDs, coding and thresholds were replay-verified, not refitted. Held-out complete cases are assigned to nearest frozen centres; exact ties select the first stored centre. Compare prevalence, all original categories, fixed development anchors, semantic total variation, distances and margins. The distance flag is nearest distance exceeding the assigned profile’s frozen development weighted 95th percentile; it is not an automatic rejection threshold.

Held-out intervals use 1,000 country bootstrap draws with fixed models and within-country relative weights. They describe variation across these observed countries, not worldwide coverage, fitting uncertainty or a full complex-survey design. Broad/partial/poor transfer is an analytical synthesis defined before opening held-out responses; no post-hoc pass score was introduced.

## Historical country similarity: frozen profile mixtures

Compare countries using their survey-weighted proportions across the same frozen global profiles, not unmatched local cluster IDs. Use

$$H(p,q)=\frac{1}{\sqrt{2}}\sqrt{\sum_c(\sqrt{p_c}-\sqrt{q_c})^2}.$$

The original dataset regions remain unchanged. Descriptive average-linkage country trees, illustrative cuts and 200 within-country respondent bootstraps assess sensitivity; no country grouping was adopted. Country pairs are dependent, so pair counts do not justify independent-pair significance tests. Analyses combining development and held-out countries are explicitly post-validation descriptions.

## Direct country similarity: original response distributions

Added on 14 October after inspecting the compressed profile-mixture maps, this is an exploratory post-validation comparison, not a profile refit or model-selection test. Use the same 137,460 complete respondents (109,488 development; 27,972 held-out). For country $c$, eligible respondents $\mathcal I_c$, original feature $j$ and response category $r$:

$$w_{ci}=\frac{WGT_{ci}}{\sum_{\ell\in\mathcal I_c}WGT_{c\ell}},\qquad q_{cj}(r)=\sum_{i\in\mathcal I_c}w_{ci}\mathbf1\{X_{cij}=r\}.$$

Compare each feature using total variation, then average separately over six worry, seven personal-harm and seven known-person-harm features:

$$T_j(c,d)=\frac12\sum_r|q_{cj}(r)-q_{dj}(r)|,\quad D_W=\frac16\sum_{j\in W}T_j,\quad D_S=\frac17\sum_{j\in S}T_j,\quad D_O=\frac17\sum_{j\in O}T_j.$$

For binary harm, each feature distance is the absolute prevalence difference. Combine raw components:

$$D_\alpha=\alpha D_W+\frac{1-\alpha}{2}D_S+\frac{1-\alpha}{2}D_O.$$

Use $\alpha=0.50$ for B-associated allocation (50/25/25) and $0.75$ for E-associated allocation (75/12.5/12.5). Distances lie in [0,1]. This preserves nominal block emphasis, not centred K-means geometry or 0/1/3 middle-category spacing. Total variation requires no square-root scaling and is invariant to one-to-one category recoding. It is a metric on marginal summaries but only a pseudometric on full joint response laws: equal marginals can hide different within-person combinations.

Report raw distance, worry mismatch ×100 and personal/known-person mean prevalence gaps in percentage points. Pair percentiles are $100$ times the upper empirical CDF over distinct unordered pairs: 10,011 full-scope pairs and 6,328 development pairs. Exclude self-pairs and include exact ties. Rank unrounded distances, then ISO3 for ties. These percentiles are not p-values or confidence measures.

For map colours only, use $z_c(d)=D(c,d)/\max_{e\ne c}D(c,e)$ and seven equal-width bands, including the reference at zero. A zero maximum gives the first band everywhere. This display is generally asymmetric and cannot replace a scientific distance. Combine raw components before scaling; never recombine independently normalized components. Colours are not comparable across references, allocations or scopes. Historical two-dimensional overview colours remain available only for profile mixtures.

Income summaries exclude unclassified Venezuela (141 countries/9,870 pairs in full; 112/6,216 in development). Income and geography do not enter the distance. No new joint-response analysis, bootstrap rank uncertainty or permutation test has been run. Earlier Hellinger bootstrap/permutation results do not apply to these new distances.
