"""Verify moved outputs, then execute the Week 5 reading path without model fits."""
from pathlib import Path
import ast
import copy
import hashlib
import json
import nbformat as nbf
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'weekly_notebooks'
ARCHIVE = FOLDER / 'earlier iterations/before_move_optimization_to_week05_20261016'
path = FOLDER / 'week05_validate_frozen_profiles.ipynb'
book = nbf.read(path, as_version=4)
for c in book.cells:
    if c.cell_type == 'markdown' and 'a newly untouched external test. See Section 1 below.' in c.source:
        c.source = c.source.replace('a newly untouched external test. See Section 1 below.',
                                    'a newly untouched external test. See Section 5 below.')
        c.metadata.generated_source_sha256 = hashlib.sha256(c.source.encode()).hexdigest()
old4 = nbf.read(ARCHIVE / 'week04_profile_robustness_and_selection.ipynb', as_version=4)
old5 = nbf.read(ARCHIVE / path.name, as_version=4)
now4 = nbf.read(FOLDER / 'week04_profile_robustness_and_selection.ipynb', as_version=4)
assert now4.cells[:47] == old4.cells[:47]
expected = [c for c in old4.cells[47:] + old5.cells[30:] if c.cell_type == 'code']
lookup = {c.id: c for c in book.cells}
for c in expected:
    assert lookup[c.id].source == c.source and lookup[c.id].outputs == c.outputs
for c in book.cells:
    if c.cell_type == 'code':
        for node in ast.parse(c.source).body:
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id.startswith('RUN_'):
                assert isinstance(node.value, ast.Constant) and node.value.value is False
execution = copy.deepcopy(book)
# The result-check notebook may write its pre-existing verification files, but
# does not fit a model. Keep every original output in the canonical notebook.
NotebookClient(execution, timeout=300, kernel_name='python3', resources={'metadata': {'path': str(ROOT)}}).execute()
assert not any(o.output_type == 'error' for c in execution.cells if c.cell_type == 'code' for o in c.outputs)
nbf.write(book, path)
result_path = ARCHIVE / 'reorganization_verification.json'
result = json.loads(result_path.read_text())
result['moved_code_cells_with_identical_sources_and_outputs'] = len(expected)
result['entire_week05_reading_path_executed_in_fresh_kernel'] = True
result['canonical_saved_outputs_preserved'] = True
result['expensive_recomputation_switches_off'] = True
for filename, digest in result['protected_artifact_hashes'].items():
    assert hashlib.sha256((ROOT / filename).read_bytes()).hexdigest() == digest
result_path.write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
