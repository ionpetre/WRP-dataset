"""Execute only the new saved-result notebook sections and verify preservation."""
import ast
import copy
import json
import subprocess
import sys
import nbformat as nbf
from nbclient import NotebookClient
from t5_secondary_transfer import ROOT, BASE, save

subprocess.run([sys.executable, str(ROOT / '.week05_build/test_t5_secondary_transfer.py')], check=True)
archive = ROOT / 'weekly_notebooks/earlier iterations/before_T5_freeze_and_secondary_transfer_20261016'
checks = []
for filename in ['week04_profile_robustness_and_selection.ipynb', 'week05_validate_frozen_profiles.ipynb']:
    path = ROOT / 'weekly_notebooks' / filename
    book = nbf.read(path, as_version=4)
    original = nbf.read(archive / filename, as_version=4)
    indices = [i for i, c in enumerate(book.cells) if c.metadata.get('t5_secondary_assessment')]
    assert book.cells[:len(original.cells)] == original.cells
    # This kernel reads saved results only; the scientific work is already done.
    setup = nbf.v4.new_code_cell('from pathlib import Path\nimport json, hashlib\nimport pandas as pd\nfrom IPython.display import display\nROOT = Path(' + repr(str(ROOT)) + ')')
    execution = nbf.v4.new_notebook(cells=[setup] + [copy.deepcopy(book.cells[i]) for i in indices])
    NotebookClient(execution, timeout=180, kernel_name='python3', resources={'metadata': {'path': str(ROOT)}}).execute()
    offset = max((c.get('execution_count') or 0 for c in original.cells), default=0)
    for i, c in zip(indices, execution.cells[1:]):
        if c.cell_type == 'code' and c.execution_count:
            c.execution_count += offset - 1
        book.cells[i] = c
    assert book.cells[:len(original.cells)] == original.cells
    assert not any(o.output_type == 'error' for c in book.cells[indices[0]:] if c.cell_type == 'code' for o in c.outputs)
    nbf.write(book, path)
    checks.append({'notebook': filename, 'new_section_executed': True,
                   'preceding_cells_and_outputs_preserved': len(original.cells), 'model_fits_during_execution': 0})
output = ROOT / json.loads((BASE / 'current_run.json').read_text())['output']
save(output / 'notebook_verification.json', {'status': 'passed', 'notebooks': checks})
print(json.dumps(checks, indent=2))
