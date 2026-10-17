"""Append profile evaluation without changing the previous notebook sections."""
from pathlib import Path
import hashlib
import json
import shutil
import textwrap
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'weekly_notebooks/week04_profile_robustness_and_selection.ipynb'
if json.loads(PATH.read_text()).get('metadata', {}).get('week05_workflow_reorganized'):
    raise SystemExit('Historical writer disabled: post-search profile review is now documented in the Week 5 notebook.')
ARCHIVE = ROOT / 'weekly_notebooks/earlier iterations/before_cached_profile_evaluation_20261016'
pointer = json.loads((ROOT / 'course_artifacts/week04_kmeans_profile_evaluation/current_run.json').read_text())
output = ROOT / pointer['output']
book = nbf.read(PATH, as_version=4)
ARCHIVE.mkdir(exist_ok=True)
if not (ARCHIVE / PATH.name).exists():
    shutil.copy2(PATH, ARCHIVE / PATH.name)
for c in book.cells:
    if c.metadata.get('cached_profile_evaluation'):
        assert hashlib.sha256(c.source.encode()).hexdigest() == c.metadata['generated_source_sha256'], 'Preserve user edits before refreshing this section.'
book.cells = [c for c in book.cells if not c.metadata.get('cached_profile_evaluation')]


def cell(kind, text):
    text = textwrap.dedent(text).strip()
    c = nbf.v4.new_markdown_cell(text) if kind == 'markdown' else nbf.v4.new_code_cell(text)
    c.metadata.update(cached_profile_evaluation=True, generated_source_sha256=hashlib.sha256(text.encode()).hexdigest())
    return c


book.cells += [cell('markdown', r'''
## 7. Evaluate profile meaning, individual stability and additional distinctions

**Objective.** Evaluate steps 1–3 agreed after the adaptive search, using only
existing fits. Compare B4/E8 with the selected k=3,...,9 alternatives. Do not
run more optimization, change the eligibility rules or use Ward as a selection
requirement in this round. No geographical or held-out validation is added.

These are nine reference partitions and 54 profiles on the same 109,488
complete-response development respondents. B4/E8 refer to the original frozen
B/E models. Names such as T5 C2 are analysis keys, not new frozen assignment IDs.
All frozen models, IDs and downstream assignments remain unchanged.
'''), cell('code', f'''
PROFILE_EVALUATION = ROOT / {pointer['output']!r}
display(pd.Series(json.loads((PROFILE_EVALUATION / 'completion.json').read_text())))
'''), cell('markdown', '''
### 7.1. Step 1: compare meanings in the original survey responses

The profile cards show both equal-country-weighted prevalence and the ordinary
respondent proportion. Original worry remains 0=not, 1=somewhat, 2=very worried;
the three categories are shown separately in the stacked bars. The heatmap uses
very-worried prevalence and separate personal/known-person harm prevalence,
all on a common 0–100% scale. It is not a heatmap of transformed centroids.

The full category table includes within-profile prevalence, outside-profile
prevalence and their difference. The concise anchors use distinct features,
not several categories of the same feature. Descriptive names are provisional.
The previous one-feature and depth-1/2/3/5 burden-tree summaries are reused,
not fitted again. Precision and recall must be read together.
'''), cell('code', '''
profile_cards = pd.read_csv(PROFILE_EVALUATION / 'profile_review_cards.csv')
display(profile_cards[['model', 'cluster', 'description', 'weighted_share', 'respondent_share',
                       'mean_worry_0_to_2', 'mean_personal_harm_prevalence',
                       'mean_known_person_harm_prevalence']].round(3))
from IPython.display import Image
display(Image(filename=str(PROFILE_EVALUATION / 'original_unit_profile_heatmap.png')))
display(Image(filename=str(PROFILE_EVALUATION / 'original_worry_category_distributions.png')))
'''), cell('markdown', r'''
### 7.2. Step 2: does each fixed reference profile recur?

An overall pairwise ARI can conceal an unstable small profile or a reference
partition that is less representative than its resampled alternatives.
For each model, reuse 50 respondent-resampling and 50 country-resampling fits.
Every fit has already assigned the same full development population.

Let $C_a$ be reference cluster $a$, $C'_b$ a cluster in a resampled fit, and
$w(A)=\sum_{i\in A}w_i$ with fixed full-development equal-country weights.
Set $M_{ab}=w(C_a\cap C'_b)$. Choose a one-to-one label match $\pi$ maximizing
$\sum_a M_{a,\pi(a)}$. For each matched cluster compute

$$P_a=\frac{M_{a,\pi(a)}}{w(C'_{\pi(a)})},\qquad
R_a=\frac{M_{a,\pi(a)}}{w(C_a)},\qquad
J_a=\frac{M_{a,\pi(a)}}{w(C_a)+w(C'_{\pi(a)})-M_{a,\pi(a)}}.$$

Precision describes the purity of the matched resampled group relative to
the reference group. Recall describes how much of the reference group remains
together. Jaccard combines their intersection and union. Also report
$J_a^{best}=\max_b w(C_a\cap C'_b)/w(C_a\cup C'_b)$, without a one-to-one
constraint. This reveals matching artefacts but allows multiple reference
groups to choose the same resampled group; it cannot by itself prove that the
profiles remain distinct.

Report median, lower decile and minimum across **50 reference-versus-resample
comparisons per test and cluster**. These are not the 1,225 pairwise ARIs used
for the original retention rule. Jaccard is not ARI: **do not transfer the
0.80 ARI cutoff to this new diagnostic**. The original numerical eligibility
flags are preserved; these additional measures inform scientific review.

Reference diagnostics also compare the saved reference to each repetition
using ordinary unweighted ARI. Within each test, the cached fit with largest
mean ARI to the other 49 fits is called the ARI medoid. It is only a diagnostic
representative; no medoid has replaced a reference.

For a further numerical check, evaluate each saved set of centres on the
same full development data and weights:

$$L^{(r)}=\sum_i w_i\min_c\|X_i-c_c^{(r)}\|^2.$$

Compare $L^{(r)}$ with the saved full-data reference objective **only within
the same geometry**. A lower value proves that the reference is not the
lowest-inertia solution among these saved centres. It does not establish a
global optimum or a scientifically better profile structure. This check uses
saved centres and assignments; it performs no refitting.

Cluster-wise overlap follows the general principle of
[Hennig's cluster-stability assessment](https://www.sciencedirect.com/science/article/pii/S0167947306004622),
adapted here to fixed equal-country weights and our two existing resampling tests.
'''), cell('code', '''
review = pd.read_csv(PROFILE_EVALUATION / 'model_review_summary.csv')
display(review[['model', 'k', 'score', 'respondents_min_cluster_jaccard_p10',
                'countries_min_cluster_jaccard_p10', 'respondents_minimum_best_any_jaccard_p10',
                'countries_minimum_best_any_jaccard_p10', 'cached_centres_with_lower_full_objective']].round(3))
display(Image(filename=str(PROFILE_EVALUATION / 'individual_profile_stability.png')))
for filename in ['reference_representativeness.csv', 'reference_inertia_diagnostic.csv']:
    print(filename)
    display(pd.read_csv(PROFILE_EVALUATION / filename).round(4))
'''), cell('markdown', '''
### 7.3. Step 3: what does each additional profile contribute?

Compare fixed reference partitions through weighted membership overlaps and
original-response differences. In the figure, each target-cluster column sums
to 100% and shows which source profiles its members came from. A target group
can cut across several source groups. Different k also use different optimized
geometries, so these are approximate membership relationships, not a strict
lattice or proof that each extra group is a split of one earlier group.

The largest-overlap source comparison reports its fraction of each target group
and the changes in original category proportions. Mean feature total variation
is shown separately for worry, personal harm and known-person harm. These are
descriptive differences, not significance tests or another selection score.
A high aggregate overlap must not hide a poorly recovered or cross-cutting
additional profile.
'''), cell('code', '''
display(Image(filename=str(PROFILE_EVALUATION / 'cross_resolution_membership_overlaps.png')))
pair_comparisons = pd.read_csv(PROFILE_EVALUATION / 'partition_comparisons.csv')
display(pair_comparisons.loc[(pair_comparisons.source.isin(['B4', 'E8', 'T5', 'T7', 'T8'])) &
                            (pair_comparisons.target.isin(['T4', 'T5', 'E8', 'T7', 'T8', 'T9']))].round(3))
added_profiles = pd.read_csv(PROFILE_EVALUATION / 'added_profile_review.csv')
display(added_profiles.loc[added_profiles.source.eq('T8') & added_profiles.target.eq('T9')].round(3))
'''), cell('markdown', '### 7.4. Critical interpretation and current decision\n\n' + (output / 'interpretation.txt').read_text()),
cell('markdown', '''
### 7.5. Reproduce these diagnostics without fitting models

Leave the switch off to read saved results. The evaluation checks fingerprints
of the selected references and all 900 fit caches. The separate numerical
diagnosis only evaluates saved centres; it does not call K-means or a classifier.
All code uses the development cohort and preserves earlier results and user edits.

Implementation: [profile and membership calculations](../.week04_parameter_search/evaluate_profiles.py),
[reference diagnosis](../.week04_parameter_search/diagnose_reference_profiles.py),
[figures and interpretation](../.week04_parameter_search/summarize_profile_evaluation.py),
[verification](../.week04_parameter_search/test_profile_evaluation.py).
'''), cell('code', '''
RUN_CACHED_PROFILE_EVALUATION = False
if RUN_CACHED_PROFILE_EVALUATION:
    import subprocess
    import sys
    for filename in ['evaluate_profiles.py', 'diagnose_reference_profiles.py',
                     'summarize_profile_evaluation.py', 'test_profile_evaluation.py']:
        subprocess.run([sys.executable, str(ROOT / '.week04_parameter_search' / filename)], check=True)
print(json.loads((PROFILE_EVALUATION / 'verification.json').read_text()))
''')]
old = nbf.read(ARCHIVE / PATH.name, as_version=4)
assert book.cells[:len(old.cells)] == old.cells
nbf.write(book, PATH)
print('Profile evaluation appended; all preceding cells and outputs preserved.')
