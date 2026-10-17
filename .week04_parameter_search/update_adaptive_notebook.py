"""Append adaptive-search evidence, preserving every existing notebook cell and output."""
from pathlib import Path
import hashlib
import json
import shutil
import textwrap
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'weekly_notebooks/week04_profile_robustness_and_selection.ipynb'
if json.loads(PATH.read_text()).get('metadata', {}).get('week05_workflow_reorganized'):
    raise SystemExit('Historical writer disabled: adaptive optimization is now documented in the Week 5 notebook.')
ARCHIVE = ROOT / 'weekly_notebooks/earlier iterations/before_adaptive_optimization_20261016'
pointer = json.loads((ROOT / 'course_artifacts/week04_kmeans_adaptive_optimization/current_run.json').read_text())
output = ROOT / pointer['output']
book = nbf.read(PATH, as_version=4)
ARCHIVE.mkdir(exist_ok=True)
if not (ARCHIVE / PATH.name).exists():
    shutil.copy2(PATH, ARCHIVE / PATH.name)
for existing in book.cells:
    if existing.metadata.get('adaptive_optimization'):
        assert hashlib.sha256(existing.source.encode()).hexdigest() == existing.metadata['generated_source_sha256'], 'Preserve user edits before refreshing the generated section.'
book.cells = [c for c in book.cells if not c.metadata.get('adaptive_optimization')]


def cell(kind, text):
    text = textwrap.dedent(text).strip()
    c = nbf.v4.new_markdown_cell(text) if kind == 'markdown' else nbf.v4.new_code_cell(text)
    c.metadata.update(adaptive_optimization=True, generated_source_sha256=hashlib.sha256(text.encode()).hexdigest())
    return c


book.cells += [cell('markdown', r'''
## 6. Bounded adaptive optimization of worry coding and allocation

**Objective.** Search between the previous grid points without repeatedly
expanding the grid. This follow-up was approved after reviewing Section 5.
It is exploratory development analysis, not another independent validation.
The original search, frozen B4/E8 assignments and Week 6 results are preserved.

### 6.1. What changes, and what stays fixed

Optimize $q=1/t$ and $\alpha$, independently for every $k=3,\ldots,10$.
The worry coding is $(0,q,1)$ with $q\in[0.1,0.9]$; the worry allocation is
$\alpha\in[0.2,0.8]$. These are declared modelling bounds, not estimated
psychological limits. An optimum on a boundary does not establish an interior
optimum and does not trigger an automatic expansion of the range.

Keep the same 109,488 complete-response development respondents, 113 countries,
separate self/known-person harm features, equal-country weights and K-means
settings. No imputation, z-standardization, PCA or held-out responses are used.

For respondent $i$, let $m_i$ be the mean of the six normalized worry responses.
The worry coordinates remain
$\sqrt{\alpha/6}\,(w_{i1}-m_i,\ldots,w_{i6}-m_i,m_i)$;
the fourteen harm coordinates remain
$\sqrt{(1-\alpha)/14}\,h_{i\ell}$.
There are six underlying worry measurements, not seven independent features.
The transformation deliberately reduces the squared-distance contribution of
a uniform change in all six worries by a factor of six relative to uncentered
worry. The denominators set maximum block-distance budgets, not necessarily
the observed worry/harm contributions.

### 6.2. Search, shortlist and fresh confirmation

1. Import the 301 previous reference settings and their original ten-resample
   pilot evidence. Earlier full-confirmation scores are not the search objective.
2. Use Optuna 4.5.0 multivariate TPE to propose **20 additional parameter pairs
   per k**, at most 160 new pairs. Each k has its own fixed random seed.
   Proposals depend on earlier results, rather than a new fixed grid. The grid
   and midpoint-refinement fields inherited in the saved protocol describe the
   previous evidence only; the active extension is the adaptive search.
3. Screen the reference partition structurally before resampling. Require
   largest equal-country-weighted cluster share $\leq0.40$, dominance
   $D=k\times\text{largest share}<3$, and the requested number of clusters.
4. Evaluate eligible proposals using the **same ten respondent and ten country
   samples as the earlier pilots**: 45 pairwise ARIs per test. These are search
   scores, not final evidence. Maximize the smaller of the two lower-decile ARIs.
5. Select two completed, structurally eligible settings per k. Break exact ties
   by minimum median ARI, distance to $(q,\alpha)=(0.5,0.5)$, then q and alpha.
   Save and hash this shortlist before confirmation. Add unchanged B4 and E8.
6. Confirm the fixed shortlist with **50 fresh samples per test**, 1,225 ARIs
   per test. The new samples are checked against every previous original and
   confirmation sample. Different fit seeds are also used.
7. Apply the unchanged rule: **median and lower-decile ARI $\geq0.80$ in both
   tests**, together with all structural filters. Report rejected settings too,
   but label them clearly. No model is frozen automatically.

The respondent test samples 80% within every development country. The country
test selects 90 of 113 countries, stratified by region and income. ARI compares
the full common development population and is unweighted; fitting and substantive
profile summaries use equal-country weights. Singleton country strata are always
represented, a limitation inherited from the original protocol.

Fresh samples reduce dependence on the pilot draws. They do not provide new
countries, eliminate all selection bias, or establish a unique true response
scale. The prior search and prior held-out findings were already known. This
bounded search cannot guarantee a global optimum.

**Preflight correction.** An initial proposed confirmation seed range overlapped
the earlier confirmation range. The all-pairs check stopped it before any new
fits. That attempt is preserved with a failure record. The active protocol uses
a disjoint range; this was not a clustering failure or a change in the criteria.
'''), cell('code', f'''
ADAPTIVE_SEARCH = ROOT / {pointer['output']!r}
adaptive_protocol = json.loads((ADAPTIVE_SEARCH / 'protocol.json').read_text())
display(pd.Series(adaptive_protocol['design'], name='adaptive_protocol'))
status_file = ADAPTIVE_SEARCH / 'completion.json'
print(json.loads(status_file.read_text()) if status_file.exists() else 'Search or confirmation still running; no final conclusions yet.')
'''), cell('markdown', '''
### 6.3. Run or resume deliberately

The switch is off for ordinary reading. The runner uses four workers, resumable
fit caches and saved optimizer states. It shares a lock with the earlier search,
so duplicate runs are rejected. It checks the input data, model code, previous
results and runtime before resuming. Optuna is an additional search dependency;
it does not replace the ordinary scikit-learn KMeans model.

Implementation: [adaptive runner](../.week04_parameter_search/adaptive_search.py),
[unchanged model and stability functions](../.week04_parameter_search/search.py),
[verification](../.week04_parameter_search/test_adaptive.py).
'''), cell('code', '''
RUN_ADAPTIVE_OPTIMIZATION = False
if RUN_ADAPTIVE_OPTIMIZATION:
    import subprocess
    import sys
    subprocess.run([sys.executable, str(ROOT / '.week04_parameter_search/adaptive_search.py')], check=True)
    subprocess.run([sys.executable, str(ROOT / '.week04_parameter_search/report_adaptive.py')], check=True)
    subprocess.run([sys.executable, str(ROOT / '.week04_parameter_search/test_adaptive.py')], check=True)
'''), cell('markdown', '''
### 6.4. Numerical eligibility and substantive evidence

The first table contains only the best confirmed setting per k that passes
every numerical filter, plus B/E as benchmarks on the same fresh samples.
Their stability-pass flags are shown explicitly. It is not a list
of automatically adopted models. Subsequent tables retain the full evidence,
including failed qualifications, profile interpretations, burden trees and
single-feature reconstructions. Exact parameters remain in the saved specifications.
'''), cell('code', '''
best_path = ADAPTIVE_SEARCH / 'best_tested_setting_per_k.csv'
if best_path.exists():
    adaptive_best = pd.read_csv(best_path)
    eligible = adaptive_best.loc[adaptive_best.stability_pass].copy()
    eligible['model'] = 'Adaptive k' + eligible.k.astype(str)
    baseline = pd.read_csv(ADAPTIVE_SEARCH / 'frozen_baselines_on_confirmation_samples.csv')
    baseline['model'] = baseline.baseline
    comparison = pd.concat([eligible, baseline], ignore_index=True).sort_values(['k', 'model'])
    display(comparison[['model', 'k', 'q', 't', 'alpha', 'respondents_median', 'respondents_p10',
                        'countries_median', 'countries_p10', 'score', 'largest', 'dominance', 'stability_pass']].round(4))
    for filename in ['best_tested_setting_per_k.csv', 'full_confirmation_results.csv',
                     'comparison_with_frozen_BE.csv', 'comparison_with_existing_Ward8.csv',
                     'comparison_with_previous_tuned_models.csv', 'profile_interpretations.csv',
                     'burden_tree_summary_with_baselines.csv', 'single_feature_summary_with_baselines.csv',
                     'parameter_neighbourhoods.csv', 'new_partition_comparisons.csv']:
        path = ADAPTIVE_SEARCH / filename
        if path.exists():
            print(filename)
            display(pd.read_csv(path).round(4))
else:
    print('No final confirmation summary saved yet.')
'''), cell('code', '''
figure = ADAPTIVE_SEARCH / 'adaptive_search_surfaces.png'
if figure.exists():
    from IPython.display import Image
    display(Image(filename=str(figure)))
''')]
interpretation = output / 'interpretation.txt'
if interpretation.exists():
    book.cells.append(cell('markdown', '### 6.5. Interpretation and adoption decision\n\n' + interpretation.read_text()))
nbf.write(book, PATH)
old = nbf.read(ARCHIVE / PATH.name, as_version=4)
assert book.cells[:len(old.cells)] == old.cells
print('Adaptive section updated; every preceding cell and output preserved.')
