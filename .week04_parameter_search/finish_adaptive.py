"""Verify fits, save interpretation and execute the added notebook section only."""
from collections import Counter
import ast
import copy
import json
import subprocess
import sys
import time
import joblib
import nbformat as nbf
import numpy as np
import pandas as pd
from nbclient import NotebookClient
import adaptive_search as adaptive

ROOT = adaptive.ROOT
output = ROOT / json.loads((adaptive.BASE / 'current_run.json').read_text())['output']
if '--wait' in sys.argv:
    print('Waiting for the existing fit job; no new clustering run is launched.', flush=True)
    deadline = time.monotonic() + 7200
    while not (output / 'completion.json').exists():
        if time.monotonic() > deadline:
            raise SystemExit('Completion not yet saved. Fits and caches are untouched; rerun this reporting step later.')
        time.sleep(10)
assert (output / 'completion.json').exists(), 'The bounded run has not finished.'
if not (output / 'adaptive_reporting_complete.json').exists():
    subprocess.run([sys.executable, str(ROOT / '.week04_parameter_search/report_adaptive.py')], check=True)
subprocess.run([sys.executable, str(ROOT / '.week04_parameter_search/test_adaptive.py')], check=True)
fingerprint = json.loads((output / 'protocol.json').read_text())['fingerprint']
statuses, recorded_warnings, sources = Counter(), Counter(), Counter()
iterations = []
for path in (output / 'references').glob('*.joblib'):
    result = joblib.load(path)
    assert result['fingerprint'] == fingerprint and len(result['labels']) == 109488
    sources[result['source']] += 1
    if result['source'] == 'new reference fit' and 'iterations' in result:
        iterations.append(result['iterations'])
        recorded_warnings.update(result.get('warnings', []))
for path in (output / 'fits').glob('*.joblib'):
    result = joblib.load(path)
    assert result['fingerprint'] == fingerprint
    statuses[result['status']] += 1
    if result['status'] == 'ok':
        assert len(result['labels']) == 109488
        iterations.append(result['iterations'])
        recorded_warnings.update(result.get('warnings', []))
pairwise = {}
for phase, expected in [('pilot', 45), ('confirmation', 1225)]:
    arrays = list((output / phase).glob('*_ari.npy'))
    assert all(len(np.load(p)) == expected for p in arrays)
    pairwise[phase] = {'complete_tests': len(arrays), 'pairwise_ARIs': len(arrays) * expected}
profiles = pd.read_csv(output / 'original_category_profiles.csv')
assert np.allclose(profiles.groupby(['model', 'cluster', 'feature']).proportion.sum(), 1)
assert np.allclose(profiles.groupby(['model', 'cluster']).cluster_share.first().groupby('model').sum(), 1)
audit = {'reference_sources': dict(sources), 'new_repetition_fits': dict(statuses),
         'max_recorded_new_fit_iterations': int(max(iterations)),
         'new_fits_at_iteration_limit': sum(i >= 300 for i in iterations),
         'recorded_warnings': dict(recorded_warnings), 'pairwise_comparisons': pairwise,
         'preflight_seed_overlap': 'preserved; corrected before any new fit', 'models_replaced': 0,
         'original_category_profiles_normalized': True}
adaptive.save_json(output / 'fit_audit.json', audit)
subprocess.run([sys.executable, str(ROOT / '.week04_parameter_search/update_adaptive_notebook.py')], check=True)
path = ROOT / 'weekly_notebooks/week04_profile_robustness_and_selection.ipynb'
book = nbf.read(path, as_version=4)
indices = [i for i, c in enumerate(book.cells) if c.metadata.get('adaptive_optimization')]
for i in indices:
    cell = book.cells[i]
    if cell.cell_type == 'code':
        for node in ast.parse(cell.source).body:
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id.startswith('RUN_'):
                assert isinstance(node.value, ast.Constant) and node.value.value is False
setup = nbf.v4.new_code_cell('from pathlib import Path\nimport json\nimport pandas as pd\nfrom IPython.display import display\nROOT = Path(' + repr(str(ROOT)) + ')')
execution = nbf.v4.new_notebook(cells=[setup] + [copy.deepcopy(book.cells[i]) for i in indices])
NotebookClient(execution, timeout=600, kernel_name='python3', resources={'metadata': {'path': str(ROOT)}}).execute()
offset = max((c.get('execution_count') or 0 for c in book.cells[:indices[0]]), default=0)
for i, executed in zip(indices, execution.cells[1:]):
    if executed.cell_type == 'code' and executed.execution_count:
        executed.execution_count += offset - 1
    book.cells[i] = executed
old = nbf.read(ROOT / 'weekly_notebooks/earlier iterations/before_adaptive_optimization_20261016' / path.name, as_version=4)
assert book.cells[:len(old.cells)] == old.cells
nbf.write(book, path)
result = {'status': 'passed', 'new_section_executed': True, 'historical_cells_and_outputs_unchanged': len(old.cells),
          'new_refit_switch_off': True, 'section': 6, 'frozen_sources_unchanged': True}
adaptive.save_json(output / 'notebook_verification.json', result)
print(json.dumps(audit, indent=2), flush=True)
print(json.dumps(result, indent=2), flush=True)
