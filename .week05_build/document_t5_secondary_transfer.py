"""Append the T5 decision and secondary transfer; preserve all existing cells."""
from pathlib import Path
import hashlib
import json
import shutil
import textwrap
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
if json.loads((ROOT / 'weekly_notebooks/week05_validate_frozen_profiles.ipynb').read_text()).get('metadata', {}).get('week05_workflow_reorganized'):
    raise SystemExit('Historical append-only writer disabled: T5 selection and transfer are already in the reorganized Week 5 workflow.')
ARCHIVE = ROOT / 'weekly_notebooks/earlier iterations/before_T5_freeze_and_secondary_transfer_20261016'
output = ROOT / json.loads((ROOT / 'course_artifacts/week05_t5_secondary_transfer/current_run.json').read_text())['output']
trees = ROOT / json.loads((ROOT / 'course_artifacts/week04_t5_shallow_explanations/current_run.json').read_text())['output']
assert (output / 'verification.json').exists()


def cell(kind, text):
    text = textwrap.dedent(text).strip()
    result = nbf.v4.new_markdown_cell(text) if kind == 'markdown' else nbf.v4.new_code_cell(text)
    result.metadata.update(t5_secondary_assessment=True, generated_source_sha256=hashlib.sha256(text.encode()).hexdigest())
    return result


def append(filename, cells):
    path = ROOT / 'weekly_notebooks' / filename
    book = nbf.read(path, as_version=4)
    ARCHIVE.mkdir(exist_ok=True)
    backup = ARCHIVE / filename
    if not backup.exists():
        shutil.copy2(path, backup)
    # Never refresh a user-edited generated section silently.
    for c in book.cells:
        if c.metadata.get('t5_secondary_assessment'):
            assert hashlib.sha256(c.source.encode()).hexdigest() == c.metadata['generated_source_sha256']
    book.cells = [c for c in book.cells if not c.metadata.get('t5_secondary_assessment')]
    original = nbf.read(backup, as_version=4)
    assert book.cells == original.cells
    book.cells.extend(cells)
    nbf.write(book, path)
    print('Appended T5 section, preserving', len(original.cells), 'earlier cells:', filename)


append('week04_profile_robustness_and_selection.ipynb', [
cell('markdown', r'''
## 8. Select T5 and check shallow explanations — 16 October 2026

**Objective.** Decide which development model to take forward after Section 7,
then check whether its membership is almost a simple rule or a burden ranking.
This updates the earlier decision to keep B4/E8 as the main pair. Earlier
sections are the historical research record; their saved results are not changed.

**Decision: take T5 forward as the primary model.** It passes all original
structural and median/lower-decile ARI criteria. Its weakest lower-decile ARI
is 0.9131, close numerically to B4's 0.9145 on the same confirmation batch.
Every T5 reference profile recurs strongly: the smallest country-test
lower-decile matched Jaccard is 0.9427. These are different diagnostics, not
interchangeable measures or evidence of statistical equivalence.

T5 retains recognizable lower-worry, broad known-person-harm, crime/weather
and water/food patterns, and adds a useful mental-health/traffic/weather
distinction. It is not exactly B4 plus one split: the geometry also changes.
Its approximate reference agreement with B4 is ARI 0.5693.

The exact selected parameters are $k=5$, $q=0.41670089020376244$,
$t=1/q=2.399802888616365$, and $\alpha=0.5837857862168715$.
Original worry categories become $0,q,1$. Subtract each respondent's six-feature
worry mean, append that mean, and apply the existing reduced-mean geometry.
The fourteen harm indicators remain separate. This is a selected modelling
geometry, not an estimate of a uniquely correct psychological scale.

B4 is still a defensible historical benchmark, not a failed model. T4 offers
a stable but different harm/traffic-oriented typology. T3 is too close to a
single-feature classification for this scientific aim. T6/T7 have reference
representativeness concerns. E8/T9 have weak individual profiles. T8 remains
an exploratory finer alternative, not a co-equal primary model. Archive these
results; do not erase them. Do not require a new Ward comparison in this round.
'''),
cell('markdown', r'''
### 8.1. What did the two existing reconstruction checks establish?

The **burden trees** predict all five fixed cluster labels from only two scores:
mean original 0/1/2 worry and mean combined respondent-or-known-person harm.
They use country-grouped five-fold cross-validation, all five folds, trees of
depth 1, 2, 3 and 5, minimum leaf size 200, and equal-country weights in training
and evaluation. These scores are not the optimized clustering coordinates.

The **single-feature check** predicts membership in each cluster versus outside
it. On training countries, search all 20 original features, every category
threshold and both directions; maximize weighted balanced accuracy. Evaluate
the chosen rule on that fold's evaluation countries. These are custom
balanced-accuracy stumps, not ordinary Gini trees. The cohort has complete
responses, so no imputation or feature-specific exclusion is needed.

Both checks reuse fixed development labels: they describe fidelity to an
already learned partition, not independent recovery of clusters. Low burden
reconstruction does not exclude a simple rule involving several features.
'''),
cell('code', f'''
T5_EXPLANATIONS = ROOT / {str(trees.relative_to(ROOT))!r}
display(pd.read_csv(T5_EXPLANATIONS / 'burden_tree_summary.csv').round(4))
display(pd.read_csv(T5_EXPLANATIONS / 'single_feature_summary.csv').round(4))
'''),
cell('markdown', r'''
### 8.2. Additional check: ordinary shallow trees with all 20 features

**Objective.** Check the missing possibility: can a small multifeature tree
almost reproduce T5? Use the same five country folds and original features.
For each depth 1, 2, 3 and 5, fit
`DecisionTreeClassifier(max_depth=depth, min_samples_leaf=200, random_state=2023)`.
Use its default Gini criterion, no class reweighting, and equal-country sample
weights. Fit on four folds, evaluate on the fifth; every country is evaluated
once. Do not recluster respondents. The saved fold rules and weighted confusion
matrices make the behaviour inspectable; no extra full-development tree is fit.

Balanced accuracy is mean recall over the five classes. A depth-1 tree has at
most two leaves, so its five-class balanced-accuracy ceiling is 40%; depth 2
has a ceiling of 80%. Their limited capacity must be acknowledged when reading
low scores. These are ordinary greedy trees, not a search over every possible
rule set. The original labels used all development countries, so holding out
tree-evaluation countries does not turn this into independent clustering validation.
'''),
cell('code', '''
display(pd.read_csv(T5_EXPLANATIONS / 'all_feature_tree_summary.csv').round(4))
t5_tree_profiles = pd.read_csv(T5_EXPLANATIONS / 'all_feature_tree_per_cluster_summary.csv')
display(t5_tree_profiles.loc[t5_tree_profiles.depth.isin([2, 3])].round(4))
print('Example: depth-3 tree fitted without the first evaluation-country fold')
print((T5_EXPLANATIONS / 'depth3_fold1_rules.txt').read_text())
'''),
cell('markdown', '''
### 8.3. Interpretation and next step

Burden-tree balanced accuracy at depths 1/2/3 is 32.7% / 46.0% / 51.2%.
All-feature trees reach 36.8% / 54.0% / 67.9%; depth 5 reaches 73.7%.
At depth 3, recall for the broad known-person-harm profile is only 19.3%.
These trees capture interpretable worry patterns but do not almost reproduce
the five-profile solution. The strongest single-feature rule, water worry,
has 88.3% balanced accuracy, 67.4% precision and 84.3% recall. It is informative
but not a near-unique definition of that group. No new automatic rejection
threshold is imposed, and interpretability itself is not a defect.

This supports proceeding with T5; it does not prove that the profiles are
natural latent types or irreducible to every possible simpler description.
Freeze the existing development centres without refitting, then assess their
unchanged assignment in the 29 previously held-out countries. Their earlier
B/E results are already known: this is **secondary transfer assessment**, not
a newly untouched external test. See Section 8 of the Week 5 notebook.

Implementation: [shallow-tree check](../.week04_parameter_search/check_t5_shallow_trees.py).
The old B/E files and downstream results remain preserved.
''')])

append('week05_validate_frozen_profiles.ipynb', [
cell('markdown', r'''
## 8. T5 freeze and secondary transfer assessment — 16 October 2026

**Objective.** Apply the primary T5 model selected after adaptive development
search and profile-level review. Earlier sections replay the original B/E
analysis. This section records the new decision separately; it does not
retroactively change the earlier experiments, seals, assignments or findings.

T5 uses $k=5$, $t=2.399802888616365$, $q=1/t=0.41670089020376244$ and
$\alpha=0.5837857862168715$. Six respondent-centred worry coordinates and
their appended mean are multiplied by $\sqrt{\alpha/6}$; fourteen separate
harm indicators by $\sqrt{(1-\alpha)/14}$. The implementation retains the
original operation order. There is no imputation, z-standardization or PCA.
See Week 4 Section 8 for the shallow-tree and model-selection evidence.

**Validation status matters.** These countries were originally held out for
B/E, but those results were already examined before the new search. This is
secondary assessment, not pristine external confirmation. All new tuning
used development countries; no T5 fitting or tuning uses held-out responses.
'''),
cell('code', f'''
T5_TRANSFER = ROOT / {str(output.relative_to(ROOT))!r}
T5_PACKAGE = T5_TRANSFER / 'frozen_model'
t5_seal = json.loads((T5_PACKAGE / 'freeze_seal.json').read_text())
for filename, expected in t5_seal['files'].items():
    assert hashlib.sha256((T5_PACKAGE / filename).read_bytes()).hexdigest() == expected
t5_specification = json.loads((T5_PACKAGE / 'specification.json').read_text())
display(pd.Series(t5_specification['spec']))
display(pd.Series(json.loads((T5_TRANSFER / 'transfer_complete.json').read_text())).drop('files'))
'''),
cell('markdown', r'''
### 8.1. Freeze exact centres, profile IDs, thresholds and descriptive anchors

The five stored development centres are copied without a K-means refit and
reproduce all 109,488 reference assignments exactly. The seal is written
before this pipeline reads T5 held-out responses. It explicitly states that
the project had previously examined these countries for B/E.

Keep IDs **T5_C0,...,T5_C4** in stored centre order; do not order them by
prevalence or reuse B/E cluster numbers. Names are descriptive shorthands,
not exhaustive or mutually exclusive response definitions. Freeze three
largest positive category-versus-outside contrasts per profile, using distinct
features, and each assigned profile's weighted development distance p95.

Assignment is $\hat c_i=\arg\min_c\|x_i-\mu_c\|_2$, with the first stored
centre used on an exact tie. Margin is $(d_{i,2}-d_{i,1})/d_{i,2}$, where
$d_{i,1},d_{i,2}$ are the smallest two distances. A distance flag means
$d_{i,1}$ exceeds the frozen development p95 for $\hat c_i$; it does not
exclude the respondent or measure a misclassification probability.

Apply exactly these rules to 27,972 complete respondents in all 29 held-out
countries. Retain the other 2,118 respondents in the eligibility file, with
missing T5 labels. Do not impute an assignment or change any model parameter.
'''),
cell('markdown', r'''
### 8.2. Compare prevalence, original meanings and representation quality

Equal-country weights preserve relative survey weights within each complete-case
country, then give each country equal mass within the displayed area. Respondent
shares are also saved. Prevalence need not match development prevalence.

For original feature $j$, compare the complete category distributions within
profile $c$ using $V_{cj}=\tfrac12\sum_a|p^{held}_{cja}-p^{dev}_{cja}|$.
Report both mean and maximum feature total variation. These are descriptive
category shifts, not centroid distances, ARI or a new transfer cutoff. Check
the development-selected anchors' direction against outside-profile responses.

The intervals use 1,000 uniform country bootstrap draws with replacement,
preserving within-country survey weights and fixing centres and assignments.
They reflect heterogeneity over the observed 29 countries, not global sampling,
model-selection/fitting uncertainty, or the missing responses.
'''),
cell('code', '''
display(pd.read_csv(T5_TRANSFER / 'profile_transfer_summary.csv').round(4))
from IPython.display import Image
display(Image(filename=str(T5_TRANSFER / 't5_prevalence_transfer.png')))
display(Image(filename=str(T5_TRANSFER / 't5_original_response_transfer.png')))
t5_anchors = pd.read_csv(T5_TRANSFER / 'heldout_frozen_anchor_comparison.csv')
display(t5_anchors.loc[t5_anchors.scope.eq('global'),
    ['cluster', 'feature', 'category', 'development_proportion', 'proportion',
     'development_contrast', 'difference_vs_outside', 'heldout_contrast_direction_preserved']].round(4))
display(pd.read_csv(T5_TRANSFER / 'heldout_vs_development_quality.csv').round(4))
'''),
cell('markdown', '''
### 8.3. Inspect country problems, not only aggregate averages

Display distance flags together with complete-response retention. Country/profile
semantic tables also give respondent counts and Kish effective sample sizes.
Small conditional groups should not be interpreted as precisely measured
country-specific profile definitions. Missing responses can cause selective
exclusion; these results describe complete respondents, not all adults without
qualification. No new regional clustering is performed for T5 in this task.
'''),
cell('code', '''
t5_country = pd.read_csv(T5_TRANSFER / 'heldout_country_quality_and_retention.csv')
display(t5_country.sort_values('profile_p95_exceedance', ascending=False)[
    ['Country', 'prepared', 'complete', 'retained_fraction', 'profile_p95_exceedance',
     'distance_median', 'margin_median']].round(4))
t5_country_profiles = pd.read_csv(T5_TRANSFER / 'heldout_profile_semantic_differences.csv')
display(t5_country_profiles.loc[t5_country_profiles.scope.eq('country')].sort_values(
    'mean_feature_total_variation', ascending=False).head(15).round(4))
'''),
cell('markdown', '### 8.4. Interpretation and decision\n\n' + (output / 'interpretation.txt').read_text()),
cell('markdown', '''
### 8.5. ID-linked handoff and reproducibility

The separate `all_respondents_T5_eligibility_and_frozen_profiles.parquet` retains
146,910 unique IDs, eligibility and reasons, split, geography, survey weights,
T5 profile ID/name, distances, margin and flag. Its 137,460 complete cases have
assignments; 9,450 incomplete cases do not. Join on `WPID_RANDOM`, never row
position. Use the split-specific equal-country weight for split comparisons,
or the all-country weight for pooled summaries. Do not concatenate separately
normalized split weights unchanged.

**Downstream status:** T5 is the new primary scientific choice; the earlier B/E
handoff, maps, paper, publication files and Week 6 remain unchanged. Migrating
them is a separate explicit next step, not something this assessment silently
does. No all-data or held-out clustering is refitted.

The completed transfer is fingerprint-checked and not repeated on rerun.
Verification independently reconstructed held-out assignments, checked category
probabilities and weights, preserved every old B/E model hash and retained all
IDs. A final console-summary error after scientific completion was repaired
without new assignments or fits; the original table, executed source and
reporting incident are preserved in the results folder.

Implementation: [freeze and transfer](../.week05_build/t5_secondary_transfer.py),
[reporting](../.week05_build/report_t5_secondary_transfer.py),
[verification](../.week05_build/test_t5_secondary_transfer.py).
'''),
cell('code', '''
print(json.loads((T5_TRANSFER / 'verification.json').read_text()))
display(pd.Series(json.loads((T5_TRANSFER / 'primary_model_decision.json').read_text())))
# Reuse by ID, not by row position; the original survey dataset is not overwritten.
t5_handoff = pd.read_parquet(T5_TRANSFER / 'all_respondents_T5_eligibility_and_frozen_profiles.parquet')
assert t5_handoff.WPID_RANDOM.is_unique
display(t5_handoff.groupby('country_split').agg(
    prepared=('WPID_RANDOM', 'size'), complete_and_assigned=('complete_case', 'sum')))
''')])
