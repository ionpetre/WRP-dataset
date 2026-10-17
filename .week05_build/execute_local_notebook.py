from pathlib import Path
import nbformat
from nbclient import NotebookClient
import sys

root = Path(__file__).resolve().parent.parent
version = sys.argv[1] if len(sys.argv)>1 else 'final'
assert version in ['4','5','6','final'], 'Only the existing verified notebooks are supported.'
path = (root/'weekly_notebooks/week05_regional_validation_and_objective1_finalization.ipynb'
        if version in ['6','final'] else
        root/f'weekly_notebooks/week05_regional_validation_and_objective1_finalization_v{version}.ipynb')
notebook = nbformat.read(path, as_version=4)

def save_cell(**kwargs):
    nbformat.write(notebook, path)
    print('Saved completed cell', kwargs.get('cell_index'), flush=True)

client = NotebookClient(notebook, timeout=1200, kernel_name='tf-metal',
                        resources={'metadata': {'path': str(root)}}, on_cell_executed=save_cell)
try:
    client.execute()
finally:
    nbformat.write(notebook, path)
print('Week 5 replay and analytical documentation verified; no clustering fits launched.')
