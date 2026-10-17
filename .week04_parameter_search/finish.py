"""Complete reporting, execute the notebook and verify the historical sections remain unchanged."""
from pathlib import Path
import ast
import json
import subprocess
import sys
import nbformat as nbf
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
pointer = json.loads((ROOT / 'course_artifacts/week04_kmeans_parameter_optimization/current_run.json').read_text())
output = ROOT / pointer['output']
assert (output / 'completion.json').exists(), 'The search has not finished.'
if not (output / 'reporting_complete.json').exists():
    subprocess.run([sys.executable, str(ROOT / '.week04_parameter_search/report_results.py')], check=True)
subprocess.run([sys.executable, str(ROOT / '.week04_parameter_search/test_search.py')], check=True)
subprocess.run([sys.executable, str(ROOT / '.week04_parameter_search/update_notebook.py')], check=True)
path = ROOT / 'weekly_notebooks/week04_profile_robustness_and_selection.ipynb'
book = nbf.read(path, as_version=4)
for cell in book.cells:
    if cell.cell_type == 'code':
        for node in ast.parse(cell.source).body:
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id.startswith('RUN_'):
                assert isinstance(node.value, ast.Constant) and node.value.value is False, 'Turn refit switches off before verification.'
NotebookClient(book, timeout=600, kernel_name='python3', resources={'metadata': {'path': str(ROOT)}}).execute()
nbf.write(book, path)
old = nbf.read(ROOT / 'weekly_notebooks/earlier iterations/before_parameter_optimization_20261016' / path.name, as_version=4)


def outputs(notebook):
    tables, plots, text = [], [], []
    for cell in notebook.cells:
        for out in cell.get('outputs', []):
            data = out.get('data', {})
            if 'text/html' in data:
                tables.append(data['text/html'])
            if 'image/png' in data:
                plots.append(data['image/png'])
            if out.output_type == 'stream' and out.name == 'stdout':
                text.append(out.text)
    return tables, plots, ''.join(text)


before, after = outputs(old), outputs(book)
assert after[0][:len(before[0])] == before[0]
assert after[1][:len(before[1])] == before[1]
assert after[2].startswith(before[2])
result = {'status': 'passed', 'historical_tables_unchanged': len(before[0]),
          'historical_plots_unchanged': len(before[1]), 'all_cells_executed': True,
          'parameter_refit_switch_off': True, 'new_section': 5}
(output / 'notebook_verification.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2), flush=True)
