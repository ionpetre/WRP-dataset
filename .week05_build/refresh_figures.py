from pathlib import Path
import nbformat
from nbclient import NotebookClient

root=Path(__file__).resolve().parent.parent
path=root/'weekly_notebooks/week05_regional_validation_and_objective1_finalization_v3.ipynb'
notebook=nbformat.read(path,4)
client=NotebookClient(notebook,timeout=180,kernel_name='tf-metal',resources={'metadata':{'path':str(root)}})
with client.setup_kernel():
    for index in [2,3,5,7,9,11]:
        client.execute_cell(notebook.cells[index],index)
    temporary=nbformat.v4.new_code_cell("regional_summary=pd.read_csv(OUTPUT/'regional_reference_summary.csv')\nfixed_original_profiles=pd.read_csv(OUTPUT/'fixed_global_original_profiles_by_region.csv')")
    notebook.cells.append(temporary)
    client.execute_cell(temporary,len(notebook.cells)-1)
    notebook.cells.pop()
    for index in [30,32,33]:
        client.execute_cell(notebook.cells[index],index)
nbformat.validate(notebook)
nbformat.write(notebook,path)
print('Refreshed two regional profile figures from completed result tables; no model fits.')
