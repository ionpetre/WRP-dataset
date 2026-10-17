"""Remove the latest notebook's display-version suffix, preserving all scientific evidence and images."""
from pathlib import Path
import re
import nbformat
import hashlib

root=Path(__file__).resolve().parent.parent
old=root/'weekly_notebooks/week05_regional_validation_and_objective1_finalization_v6.ipynb'
new=root/'weekly_notebooks/week05_regional_validation_and_objective1_finalization.ipynb'
assert old.is_file() and not new.exists()
n=nbformat.read(old,as_version=4)
image_before=[hashlib.sha256(value.encode()).hexdigest() for c in n.cells for o in c.get('outputs',[]) for mime,value in o.get('data',{}).items() if mime.startswith('image/') and isinstance(value,str)]

def clean(text):
    text=text.replace('_v6.ipynb','.ipynb').replace('_v6.json','.json')
    text=text.replace(' — v6','').replace('**v6 development replay rule:**','**Development replay rule:**')
    text=text.replace('v6: read-only baseline replay','Read-only baseline replay')
    return re.sub(r'\bv6\b','',text,flags=re.IGNORECASE)

def clean_tree(value):
    if isinstance(value,str):return clean(value)
    if isinstance(value,list):return [clean_tree(v) for v in value]
    if isinstance(value,dict):
        return {k:(v if k.startswith(('image/','audio/','video/')) else clean_tree(v)) for k,v in value.items()}
    return value

for cell in n.cells:
    cell.source=clean(cell.source)
    cell.metadata=clean_tree(cell.metadata)
    if cell.cell_type=='code':cell.outputs=clean_tree(cell.outputs)
n.metadata=clean_tree(n.metadata)
n=nbformat.from_dict(n)
nbformat.validate(n)
image_after=[hashlib.sha256(value.encode()).hexdigest() for c in n.cells for o in c.get('outputs',[]) for mime,value in o.get('data',{}).items() if mime.startswith('image/') and isinstance(value,str)]
assert image_before==image_after
nbformat.write(n,old)
old.rename(new)
assert new.is_file() and not old.exists()
print('Renamed canonical notebook and removed internal v6 display/path references. Embedded figures unchanged.')
