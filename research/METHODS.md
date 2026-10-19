# WARM-5: encoding, weighting and validation

## Data and target population

Use the 2023 World Risk Poll: 146,910 respondents in 142 countries. The frozen country split has 113 development countries (116,820 respondents) and 29 held-out countries (30,090 respondents). Countries, not respondents, are the split unit; reuse [the country allocation](../course_artifacts/week03_country_split.csv).

WARM-5 requires complete substantive answers to all six worry and seven harm-domain questions: 109,488 development and 27,972 held-out respondents. The 9,450 others remain unassigned. No imputation, PCA or z-standardization is used. Complete-case selection limits interpretation.

For an analysis cohort containing $C$ countries, respondent $i$ in country $c(i)$ has weight

$$w_i=\frac{WGT_i}{\sum_{\ell\in c(i)}WGT_\ell}\frac1C.$$

Normalize within each reporting cohort. Country totals are equal; within-country relative survey weights are preserved. This is not a world-population estimand.

## One frozen feature geometry

The worry domains are food, water, crime, severe weather, traffic and mental health. Work is the seventh harm domain. Raw worry codes 1/2/3 mean very/somewhat/not worried. Let $u_{id}=2,1,0$ denote these original-unit recoded values for respondent $i$ and worry domain $d$.

Set $t=2.399802888616365$, $q=1/t=0.41670089020376244$ and $\alpha=0.5837857862168715$. Transform worry to $x_{id}=0,q,1$ for not/somewhat/very worried. Let $m_i=\frac16\sum_{d=1}^6x_{id}$. Use

$$z_{id}=(x_{id}-m_i)\sqrt{\alpha/6},\qquad
z_{im}=m_i\sqrt{\alpha/6}.$$

For each harm domain, raw codes 1/2/3/4 mean respondent only/known person only/both/neither. Encode personal harm as 1/0/1/0 and known-person harm as 0/1/1/0. Codes 98/99 remain missing in all features. For the 14 binary harm indicators $h_{ij}$, use

$$z_{ih_j}=h_{ij}\sqrt{(1-\alpha)/14}.$$

There are 21 transformed coordinates from 20 observed features. The mean derives from the same six worries; it is not an independent seventh question. Square roots enter because squared Euclidean distance squares each multiplier. The mean coordinate has one coordinate's multiplier, not six copies of the mean.

WARM-5 has **one** nominal allocation: worry 58.38%, personal harm 20.81%, known-person harm 20.81%. Actual contributions to distances also depend on the responses and this geometry; the percentages are not measured variance shares.

## Search and selection

For each $k=3,\ldots,10$, search $q\in[0.1,0.9]$ and $\alpha\in[0.2,0.8]$. The initial grid/refinement has 301 settings; multivariate TPE proposes 20 additional pairs per k, 160 in total. Ordinary weighted K-means uses 20 initializations and at most 300 iterations.

The pilot objective is the smaller of the two lower-decile stability ARIs. Ten repetitions per test screen candidates; two eligible settings per k receive fresh 50-repetition confirmation. Each respondent sample retains 80% within each country; each country sample retains 90 of 113 development countries, stratified by region and income. Fit on the sample and assign the common development population.

Fifty partitions give 1,225 pairwise adjusted Rand indices (ARIs), comparing co-membership independently of cluster names. Require median and 10th-percentile ARI at least 0.80 in **both** tests, k at least 3, largest equal-country share at most 40%, and dominance $D=k\max_jp_j<3$, where $p_j$ is cluster j's weighted share. Pairwise ARIs are dependent summaries, not independent observations.

Review original-category meanings, overlaps and each profile's recovery. Match reference/repetition groups one-to-one by maximum weighted membership overlap, then calculate weighted Jaccard (intersection/union), precision and recall. These 50 reference-versus-repetition comparisons per test are distinct from the 1,225 pairwise ARIs. No additional Jaccard cutoff is imposed. WARM-5 balances detail and profile recovery; it is not a proven global optimum.

The public selection tables exclude historical comparison-model rows. Full original experimental history remains private.

## Simple explanations

Use all five country-grouped folds and fold-specific equal-country weights to reconstruct fixed development labels. Burden trees use mean original worry and mean harm exposure. Single-feature rules search original features, category thresholds and both directions on training countries; evaluate the selected rule in different countries without imputation.

All-feature trees use ordinary Gini decision trees, minimum leaf size 200, seed 2023 and depths 1/2/3/5, without class reweighting. Balanced accuracy is mean class recall. Depths 1 and 2 have at most two/four leaves, hence five-class balanced-accuracy ceilings of 40%/80%. These checks assess explanatory fidelity, not independently discovered clustering or every possible optimized rule set.

## Frozen assignment and secondary transfer

Keep exact development centres and their order. Assign complete respondents to their nearest centre; exact ties choose the first stored centre. Keep IDs T5_C0–T5_C4. No held-out or all-country model is fitted.

A distance flag means distance above the assigned profile's development weighted 95th percentile. It is not an error probability or exclusion. Margin is $(d_2-d_1)/d_2$, where $d_1,d_2$ are the nearest and second-nearest distances; use zero if $d_2=0$.

Compare prevalence, original-category distributions and three development-selected descriptive contrasts per profile. Resample the 29 held-out countries 1,000 times, holding model/predictions fixed and preserving within-country relative weights. This describes variation over these observed countries, not worldwide, missingness or model-selection uncertainty. No automatic transfer-rejection cutoff was specified.

The held-out countries had been inspected before WARM-5 selection. Report secondary descriptive transfer, not untouched external confirmation. Meanings partly persist because assignment uses these same features; this is not independent rediscovery.

## Regional analysis

Distinguish applying the same frozen global profiles within regions from independent regional clustering. The latter uses development countries only, unchanged WARM-5 coding/allocation and k=2–10. Select k=5, coarse k=2/3 and one inertia-based alternative: the smallest eligible k within 95% of the maximum normalized chord-minus-inertia gap.

Run 50 respondent samples retaining 80% within each country. With at least five countries, run 50 samples retaining floor(80% of regional countries). Repeated country sets are allowed and reported. With 2–4 countries use leave-one-country-out diagnostics; with one country geographic stability is unavailable.

Require median and lower-decile ARI at least 0.80 in both full tests. Global size/dominance criteria are reported benchmarks, not universal regional filters. Compare groups using membership overlap and original answers; numeric local labels do not share meanings across regions. This local selection is exploratory.

## Country distances: two summaries of the same WARM-5 analysis

For country a, let $p_{aj}$ be the survey-weighted proportion of complete respondents in frozen profile j, j=0,...,4. Mixture Hellinger distance is

$$H(a,b)=\sqrt{\frac12\sum_{j=0}^4(\sqrt{p_{aj}}-\sqrt{p_{bj}})^2}.$$

For original feature f, let $P_{afc}$ be country a's weighted probability of category c. Feature total variation is

$$V_f(a,b)=\frac12\sum_c|P_{afc}-P_{bfc}|.$$

Average separately over six worries, seven personal harms and seven known-person harms, giving $V_W,V_S,V_K$. Overall distance is

$$V(a,b)=\alpha V_W(a,b)+\frac{1-\alpha}{2}\{V_S(a,b)+V_K(a,b)\}.$$

This uses WARM-5's allocation. Numeric spacing t deliberately does not enter original-category total variation; it does affect the fitted profiles. Component views isolate a part of the comparison, not a new model. The original-response distributions describe each question separately and omit how answers occur together within a respondent. The profile proportions summarize assignments based on joint respondent answers, but hide country differences within each profile. Neither summary contains all the information in the other.

Across all 10,011 pairs of the 142 countries, the two raw distances have Spearman rank correlation 0.824. They identify the same nearest country for 26 of 142 countries (18.3%), and share an average of 1.80 of the nearest five countries. Thus broad distance patterns agree more closely than exact neighbour identities. These are descriptive comparisons, not independent-pair significance tests. Stable respondent profiles need not preserve all country differences; the clustering was not optimized to reproduce country-distance rankings.

Map display is $R=D/m_{\mathrm{ref}}$, with fixed calibration constants retained from the approved display protocol: 0.1550977480973838 for overall responses and 0.2218094853108838 for mixtures. Component constants are 0.2019268502025546 (worry), 0.0500960004811531 (personal harm), and 0.0872275415556315 (known-person harm). They are not newly recalculated WARM-5 medians. One means the fixed reference distance. Ratios are uncapped; a continuous colour gradient spans zero to “2 or more”, with larger values sharing the endpoint colour. The gradient interpolates in CIELAB colour space through the existing blue, green, yellow and orange palette. Selection/scope never changes the denominator. Scaling and colour interpolation do not change distances or ranks. Income-group colours remain categorical; the approximate two-dimensional profile-mixture overview is unchanged.

The overview colour projection is approximate; exact rankings use raw distances. No country grouping replaces dataset regions. The 200 within-country IID respondent bootstraps retain survey weights and fixed labels; these are conditional sensitivity checks, not full survey-design or model-selection confidence. Income associations use 999 whole-country label permutations, including within-region permutations. Country pairs are not independent, and the results are not causal.

## Limits

Equal-country weighting, complete-case selection, reporting differences, small country/profile cells, dependent resampling summaries and prior held-out inspection constrain conclusions. Neither stable clusters nor familiar nearest countries establish natural social types. Predictive usefulness for an external outcome requires a separate analysis.
