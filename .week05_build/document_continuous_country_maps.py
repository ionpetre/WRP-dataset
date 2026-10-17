"""Append the requested continuous-colour map and its approximation limits to the current notebook."""
from pathlib import Path
import json,shutil
import nbformat

root=Path(__file__).resolve().parent.parent
path=root/'weekly_notebooks/week05_regional_validation_and_objective1_finalization.ipynb'
backup=root/'weekly_notebooks/earlier iterations/week05_v6_before_continuous_similarity_maps_20261012.ipynb'
if not backup.exists():shutil.copy2(path,backup)
n=nbformat.read(path,as_version=4)
start=next((i for i,c in enumerate(n.cells) if c.cell_type=='markdown' and c.source.startswith('## 30 Continuous country')),None)
if start is not None:n.cells=n.cells[:start]
n.cells.append(nbformat.v4.new_markdown_cell(r'''## 30 Continuous country-similarity colours with the dataset regions overlaid

**Objective:** show countries with similar frozen global-profile mixtures in similar colours on a world map, rather than show distance to a single selected country or adopt new country clusters.

**Output:** B/E world maps with continuous similarity colours, outlines of the original geographical areas, a two-dimensional colour key, and measured approximation quality. The interactive companion provides an approximate global overview and an original-distance-from-selected-country view, with regional outlines available in both. Selecting a country leaves overview colours fixed; in the distance view it updates colours to that country's original distances. No scientific fit changes.

One scalar colour scale cannot represent every pairwise relationship in a multidimensional distance matrix. We therefore make an explicit **display approximation**. For each model separately, represent countries by \(\sqrt{p_a}/\sqrt{2}\), whose Euclidean distances equal the saved Hellinger distances. Centre these country vectors and obtain the two-dimensional classical metric-MDS coordinates by singular-value decomposition. Map the two coordinates isotropically to CIELAB chromatic coordinates at a common lightness, reducing colour spread until it lies inside the display gamut. Nearby points in the colour key then have similar colours. Coordinate signs are fixed for reproducibility, not given substantive meaning.

This is **not PCA preprocessing of respondent profiles**. The no-PCA B/E specifications, labels and original distances remain unchanged. The dimensional reduction is only for presenting already-computed country distances. Hue is not a worry or harm score, colours do not define country groups, and B/E have separate colour keys: identical-looking colours across the two maps do not imply identical compositions.

**Measured display quality:** the two coordinates retain **81.4% of variation for B** and **73.6% for E** in the centred Hellinger-coordinate representation. Original/projected pair-distance rank correlation is **0.913 for B** and **0.928 for E**. Relative distance error is 0.196/0.229. These are descriptive approximation diagnostics, not confidence levels or an inferential test. The exact nearest neighbour is preserved for only **29.6% of B countries and 10.6% of E countries**. The overview maps therefore show broad similarity patterns; **do not infer exact closest partners from overview colour**. Use the saved full distances and closest-five tables for that purpose. The interactive list defaults to 10 nearest countries, with options for 20 or all 141 others, separately for B and E. It excludes the selected country itself and orders by original unrounded Hellinger distance, resolving exact ties by ISO3 order. Display values are rounded; the rankings are not derived from colour coordinates. The optional distance map uses the original distances on a common 0–1 scale, not the MDS approximation. There is no adopted threshold for "similar countries": nearest is a relative rank and even the nearest country can be substantively different.

The overlay dissolves countries according to the **unchanged dataset GlobalRegion membership**, producing fifteen separate area unions. It does not use response-derived country groups or construct geographical envelopes across seas. Areas may contain disconnected territories. Countries outside the study remain uncoloured and are not assigned invented region memberships. The published 110m cartography omits polygons for Bahrain, Comoros, Hong Kong, Malta, Mauritius and Singapore; verified Natural Earth map-label points show their colours as dots. Boundaries are presentation geometry, not political claims.

The colour view complements, rather than replaces, the exact distance heatmaps. Similar profile mixtures need not mean similar original responses within profiles or interchangeable societies. Complete-case selection and the weaker E distinctions remain limitations. Both maps include the already-used held-out countries and are post-validation description, not new untouched confirmation.

**Presentation history:** an initial reference-country map was superseded after the user clarified that all-country similarity colours were wanted. A URL-encoded local-path error in the initial map builder was corrected; no scientific fit or distance calculation failed. The discarded reference-map design is not the intended final visualization.'''))
n.cells.append(nbformat.v4.new_code_cell('''# Objective: Verify and display the requested continuous-colour maps, preserving the original regional and frozen-profile definitions.
CONTINUOUS_MAP_OUTPUT=ROOT/'course_artifacts/week05_continuous_country_similarity_maps_v1'
continuous_map_manifest=json.loads((CONTINUOUS_MAP_OUTPUT/'map_manifest.json').read_text())
assert not continuous_map_manifest['model_refitting'] and not continuous_map_manifest['region_membership_changed']
assert not continuous_map_manifest['respondent_PCA_used']
for name,digest in continuous_map_manifest['files'].items():
    assert extension_sha(CONTINUOUS_MAP_OUTPUT/name)==digest,'Map evidence changed: '+name
load_frozen_package(FROZEN_PACKAGE)
display(pd.read_csv(CONTINUOUS_MAP_OUTPUT/'colour_projection_quality.csv'))
for name in ['B','E']:
    display(Image(filename=str(CONTINUOUS_MAP_OUTPUT/f'{name}_continuous_similarity_with_region_outlines.png')))
final_inventory['continuous_country_similarity_maps']={
    'directory':str(CONTINUOUS_MAP_OUTPUT.relative_to(ROOT)),
    'manifest_sha256':extension_sha(CONTINUOUS_MAP_OUTPUT/'map_manifest.json'),
    'distance_basis':'unchanged frozen-global-profile Hellinger distances',
    'region_basis':'original dataset GlobalRegion',
    'status':'continuous approximate colours; not country clusters or exact nearest-neighbour evidence'}
atomic_json(final_inventory,TRANSFER_OUTPUT/'objective1_final_evidence_inventory.json')
print('World maps with dataset-area outlines saved. No model, profile ID, country region or original distance changed.')'''))
nbformat.validate(n);nbformat.write(n,path)
print('Saved section 30 and its maps in the canonical Week 5 notebook.')
