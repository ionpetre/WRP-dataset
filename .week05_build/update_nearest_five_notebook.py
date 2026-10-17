"""Narrow documentation update preserving all current notebook cells and executed outputs."""
from pathlib import Path
import nbformat

root=Path(__file__).resolve().parent.parent
path=root/'weekly_notebooks/week05_regional_validation_and_objective1_finalization.ipynb'
n=nbformat.read(path,as_version=4)
for c in n.cells:
    if c.cell_type=='markdown' and c.source.startswith('## 30 Continuous country'):
        c.source=c.source.replace('The interactive inspection reports a nearest neighbour calculated from the original distances, not the colour coordinates.',
            'The interactive inspection lists the five closest countries, in order, separately for B and E, with original Hellinger distances. It excludes the selected country itself and resolves exact distance ties by ISO3 order; the rankings are not derived from colour coordinates.')
nbformat.validate(n);nbformat.write(n,path)
print('Section 30 now documents the closest-five display; all notebook cells and previous outputs preserved.')
