"""Verify and execute only the new cached-evaluation notebook section."""
import ast
import copy
import json
import subprocess
import sys
import nbformat as nbf
from nbclient import NotebookClient
import evaluate_profiles as evaluation

ROOT = evaluation.ROOT
output = ROOT / json.loads((evaluation.BASE / 'current_run.json').read_text())['output']
subprocess.run([sys.executable, str(ROOT / '.week04_parameter_search/test_profile_evaluation.py')], check=True)
subprocess.run([sys.executable, str(ROOT / '.week04_parameter_search/update_profile_evaluation_notebook.py')], check=True)
path = ROOT / 'weekly_notebooks/week04_profile_robustness_and_selection.ipynb'
book = nbf.read(path, as_version=4)
indices = [i for i, c in enumerate(book.cells) if c.metadata.get('cached_profile_evaluation')]
for i in indices:
    c = book.cells[i]
    if c.cell_type == 'code':
        for node in ast.parse(c.source).body:
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id.startswith('RUN_'):
                assert isinstance(node.value, ast.Constant) and node.value.value is False
setup = nbf.v4.new_code_cell('from pathlib import Path\nimport json\nimport pandas as pd\nfrom IPython.display import display\nROOT = Path(' + repr(str(ROOT)) + ')')
execution = nbf.v4.new_notebook(cells=[setup] + [copy.deepcopy(book.cells[i]) for i in indices])
NotebookClient(execution, timeout=600, kernel_name='python3', resources={'metadata': {'path': str(ROOT)}}).execute()
offset = max((c.get('execution_count') or 0 for c in book.cells[:indices[0]]), default=0)
for i, c in zip(indices, execution.cells[1:]):
    if c.cell_type == 'code' and c.execution_count:
        c.execution_count += offset - 1
    book.cells[i] = c
old = nbf.read(ROOT / 'weekly_notebooks/earlier iterations/before_cached_profile_evaluation_20261016' / path.name, as_version=4)
assert book.cells[:len(old.cells)] == old.cells
nbf.write(book, path)
result = {'status': 'passed', 'section': 7, 'new_section_executed': True,
          'historical_cells_and_outputs_unchanged': len(old.cells), 'recompute_switch_off': True,
          'new_clustering_or_classifier_fits': 0, 'Ward_fits': 0, 'frozen_models_replaced': 0}
evaluation.save_json(output / 'notebook_verification.json', result)
print(json.dumps(result, indent=2))
