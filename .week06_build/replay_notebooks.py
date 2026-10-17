"""Replay ordinary Python notebook cells in-process, without a Jupyter socket."""
from pathlib import Path
import contextlib
import sys
import nbformat
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

ROOT = Path(__file__).resolve().parents[1]
shell = InteractiveShell.instance()
for relative in sys.argv[1:]:
    path = ROOT / relative
    nb = nbformat.read(path, as_version=4)
    shell.user_ns.clear()
    shell.user_ns.update({'__name__':'__main__', '__builtins__':__builtins__})
    count = 0
    try:
        for i, cell in enumerate(nb.cells):
            if cell.cell_type != 'code':
                continue
            count += 1
            with capture_output(stdout=True, stderr=True, display=True) as captured:
                result = shell.run_cell(cell.source, store_history=False, silent=False)
            outputs = []
            if captured.stdout:
                outputs.append(nbformat.v4.new_output('stream', name='stdout', text=captured.stdout))
            if captured.stderr:
                outputs.append(nbformat.v4.new_output('stream', name='stderr', text=captured.stderr))
            for rich in captured.outputs:
                outputs.append(nbformat.v4.new_output('display_data', data=rich.data, metadata=rich.metadata))
            cell.outputs = outputs
            cell.execution_count = count
            print(path.name, 'cell', i, 'done', flush=True)
            if result.error_before_exec or result.error_in_exec:
                raise RuntimeError(f'{path.name}: cell {i} failed') from (result.error_before_exec or result.error_in_exec)
    finally:
        nbformat.validate(nb)
        nbformat.write(nb, path)
    print('Saved executed notebook:', path.name, flush=True)
