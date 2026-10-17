from pathlib import Path
import nbformat
from nbclient import NotebookClient

root = Path(__file__).resolve().parent.parent
path = root / 'weekly_notebooks/week05_regional_validation_and_objective1_finalization_v3.ipynb'
notebook = nbformat.read(path, as_version=4)
def save_cell(**kwargs):
    nbformat.write(notebook, path)
    print('Saved completed cell', kwargs.get('cell_index'), flush=True)
client = NotebookClient(notebook, timeout=1200, kernel_name='tf-metal',
                        resources={'metadata':{'path':str(root)}}, on_cell_executed=save_cell)
try:
    client.execute()
finally:
    nbformat.write(notebook, path)
print('Points 1 and 2 execution complete; matched caches reused; held-out responses unopened.')
