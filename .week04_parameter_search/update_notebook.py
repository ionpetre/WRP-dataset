"""Document the tuning protocol and available results in the single Week 4 notebook."""
from pathlib import Path
import hashlib
import json
import shutil
import textwrap
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'weekly_notebooks/week04_profile_robustness_and_selection.ipynb'
if json.loads(PATH.read_text()).get('metadata', {}).get('week05_workflow_reorganized'):
    raise SystemExit('Historical writer disabled: parameter optimization is now documented in the Week 5 notebook.')
ARCHIVE = ROOT / 'weekly_notebooks/earlier iterations/before_parameter_optimization_20261016'
POINTER = ROOT / 'course_artifacts/week04_kmeans_parameter_optimization/current_run.json'
run = json.loads(POINTER.read_text())
notebook = nbf.read(PATH, as_version=4)
if not ARCHIVE.exists():
    ARCHIVE.mkdir(parents=True)
    shutil.copy2(PATH, ARCHIVE / PATH.name)


def cell(kind, text):
    source = textwrap.dedent(text).strip()
    result = nbf.v4.new_markdown_cell(source) if kind == 'markdown' else nbf.v4.new_code_cell(source)
    result.metadata['parameter_optimization'] = True
    result.metadata['generated_source_sha256'] = hashlib.sha256(source.encode()).hexdigest()
    return result


for existing in notebook.cells:
    if existing.metadata.get('parameter_optimization'):
        assert hashlib.sha256(existing.source.encode()).hexdigest() == existing.metadata['generated_source_sha256'], 'User edited the tuning section: preserve those edits before refreshing.'
notebook.cells = [c for c in notebook.cells if not c.metadata.get('parameter_optimization')]
notebook.cells += [cell('markdown', '''
## 5. Subsequent development analysis: tune worry coding and worry–harm allocation

This analysis was approved on 16 October 2026, after Objective 1 had been frozen
and the held-out countries examined. It is not part of the original Week 4 search
and is not another untouched validation. B4/E8, their IDs, their held-out results
and the Week 6 input assignments remain unchanged.

### 5.1. Parameters, objective and computational budget

Use worry coding **0 / q / 1**. This is the previous normalized **0 / 1 / t**
coding with **t = 1/q**. Search q from .1 to .9 and alpha from .2 to .8.
The six centered worry coordinates, reduced mean-worry coordinate, fourteen
personal/known-person harm coordinates, complete-response population and
equal-country weighting remain exactly as above.

For each k = 3,...,10 separately, maximize

$$S(q,\\alpha;k)=\\min\\{Q_{.10}(\\mathrm{ARI}_{respondents}),
Q_{.10}(\\mathrm{ARI}_{countries})\\}.$$

Keep the previous filters: largest cluster ≤40%, k × largest share <3, and
median and lower-decile ARI ≥.80 in both tests. Do not compare raw inertia
across geometries or select a single k solely by its stability score.
ARI is unweighted and compares assignments of the full common development
population. Equal-country weights are used in fitting and profile descriptions.

The fixed protocol is:

1. A 6 × 5 parameter grid for each k: 240 reference settings.
2. Reject structurally ineligible references. Evaluate the others using ten
   original respondent samples and ten original country samples: 45 ARIs per test.
3. For each k, refine around its strongest coarse pilot using the midpoint to
   each adjacent grid value. This tests at most nine local points, not a new
   unrestricted search. Break exact score ties by minimum median ARI, then
   distance to q=.5/alpha=.5, then q and alpha.
4. Select two parameter settings per k from the completed pilots. Add original
   B4/E8 as benchmarks. Confirm all of these using the same **fresh 50 samples
   per test**, giving 1,225 ARIs per test per setting. Reuse only matching fit caches.
5. Report the best tested setting for every k, including failures to qualify.
   Inspect nearby settings, original-response profiles, burden trees and
   single-feature explanations. Numerical winners are **not automatically frozen**.

Fresh confirmation reduces dependence on the pilot resampling draws. It does
not create new independent countries, remove selection bias, or prove that an
estimated category spacing is a true psychological scale. The result is the
best tested setting within this bounded search, not a guaranteed global optimum.
'''), cell('code', f'''
PARAMETER_SEARCH = ROOT / {run['output']!r}
parameter_protocol = json.loads((PARAMETER_SEARCH / 'protocol.json').read_text())
display(pd.Series(parameter_protocol['design'], name='predeclared_search'))
print('Saved progress:', json.loads((PARAMETER_SEARCH / 'progress.json').read_text()))
'''), cell('markdown', '''
### 5.2. The model declaration is unchanged

Only the two representation parameters vary. The original feature transform
above accepts t, so pass t = 1/q. Original worry categories remain 0/1/2 in
the stored data and in the substantive descriptions.
'''), cell('code', '''
def fit_tuned_kmeans(frame, q, alpha, k, seed):
    matrix = profile_matrix(frame, top=1 / q, alpha=alpha)
    model = KMeans(n_clusters=k, n_init=20, max_iter=300, random_state=seed)
    with threadpool_limits(limits=1):
        model.fit(matrix, sample_weight=country_weights(frame))
    return model
'''), cell('markdown', '''
### 5.3. Reproduce or resume the search

Keep the switch off when reading results. The runner uses four workers, a
single-run lock and fingerprint-checked caches. It never loads held-out responses.
The implementation is available directly as readable Python:
[model and stability code](../.week04_parameter_search/search.py),
[coarse-to-fine runner](../.week04_parameter_search/run_search.py),
[original-response and explanatory checks](../.week04_parameter_search/report_results.py).
'''), cell('code', '''
RUN_PARAMETER_OPTIMIZATION = False
if RUN_PARAMETER_OPTIMIZATION:
    import subprocess
    import sys
    subprocess.run([sys.executable, str(ROOT / '.week04_parameter_search/run_search.py')], check=True)
    subprocess.run([sys.executable, str(ROOT / '.week04_parameter_search/report_results.py')], check=True)
'''), cell('markdown', '''
### 5.4. Read the available evidence without refitting

Pilot scores are screening results, not final confirmation. The full-confirmation
table is the numerical comparison; the explanatory tables show what the resulting
partitions mean. A high-recall rule with poor precision does not define a cluster.
Treat all labels beginning T as provisional descriptions, not replacements for B/E.
Exact parameter values are in `selected_reference_specs.json` and the reference
caches. Rounded table values are for display, not exact re-assignment.
'''), cell('code', '''
for filename in ['coarse_results.csv', 'refinement_seeds.csv', 'shortlist_before_confirmation.csv',
                 'full_confirmation_results.csv', 'best_tested_setting_per_k.csv']:
    path = PARAMETER_SEARCH / filename
    if path.exists():
        table = pd.read_csv(path)
        columns = [c for c in ['k', 'q', 't', 'alpha', 'score', 'respondents_median', 'respondents_p10',
                   'countries_median', 'countries_p10', 'largest', 'dominance', 'stability_pass',
                   'selection_status', 'at_q_boundary', 'at_alpha_boundary', 'status'] if c in table]
        print(filename)
        display(table[columns].round(4))
for filename in ['frozen_baselines_on_confirmation_samples.csv', 'comparison_with_frozen_BE.csv',
                 'comparison_with_existing_Ward8.csv', 'profile_interpretations.csv',
                 'burden_tree_summary.csv', 'single_feature_summary.csv',
                 'parameter_neighbourhoods.csv', 'new_partition_comparisons.csv']:
    path = PARAMETER_SEARCH / filename
    if path.exists():
        print(filename)
        display(pd.read_csv(path).round(3))
'''), cell('code', '''
figure = PARAMETER_SEARCH / 'coarse_stability_surfaces.png'
if figure.exists():
    from IPython.display import Image
    display(Image(filename=str(figure)))
''')]
interpretation = ROOT / run['output'] / 'interpretation.txt'
if interpretation.exists():
    notebook.cells.append(cell('markdown', '### 5.5. Interpretation and remaining decision\n\n' + interpretation.read_text()))
nbf.write(notebook, PATH)
print('Updated the tuning section; all preceding notebook cells preserved.')
