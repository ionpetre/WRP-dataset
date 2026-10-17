"""Update only section 30's display explanation; preserve the rest of the current notebook."""
from pathlib import Path
import nbformat

root=Path(__file__).resolve().parent.parent
path=root/'weekly_notebooks/week05_regional_validation_and_objective1_finalization.ipynb'
n=nbformat.read(path,as_version=4)
for c in n.cells:
    if c.cell_type=='markdown' and c.source.startswith('## 30 Continuous country'):
        c.source=c.source.replace('The interactive companion allows country inspection and toggling the same regional outlines; it does not change colours or fits when a country is selected.',
            "The interactive companion provides an approximate global overview and an original-distance-from-selected-country view, with regional outlines available in both. Selecting a country leaves overview colours fixed; in the distance view it updates colours to that country's original distances. No scientific fit changes.")
        c.source=c.source.replace('The maps therefore show broad similarity patterns; **do not infer exact closest partners from colour**.',
            'The overview maps therefore show broad similarity patterns; **do not infer exact closest partners from overview colour**.')
        c.source=c.source.replace('The interactive inspection lists the five closest countries, in order, separately for B and E, with original Hellinger distances. It excludes the selected country itself and resolves exact distance ties by ISO3 order; the rankings are not derived from colour coordinates.',
            'The interactive list defaults to 10 nearest countries, with options for 20 or all 141 others, separately for B and E. It excludes the selected country itself and orders by original unrounded Hellinger distance, resolving exact ties by ISO3 order. Display values are rounded; the rankings are not derived from colour coordinates. The optional distance map uses the original distances on a common 0–1 scale, not the MDS approximation. There is no adopted threshold for "similar countries": nearest is a relative rank and even the nearest country can be substantively different.')
nbformat.validate(n);nbformat.write(n,path)
print('Documented both map modes and expandable original-distance ranking in section 30.')
