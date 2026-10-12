"""Continuous similarity colour maps: a reporting projection, not a change to respondent clustering."""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
from scipy.spatial.distance import pdist,squareform
from scipy.stats import spearmanr
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Patch
from matplotlib.collections import LineCollection

root=Path(__file__).resolve().parent.parent
source=root/'course_artifacts/week05_country_similarity_and_profile_synthesis_v1/d694096841b06e54'
output=root/'course_artifacts/week05_continuous_country_similarity_maps_v1'
output.mkdir(exist_ok=True)
data=json.loads((root/'.week05_build/country_map_numerical_data.json').read_text())
geometry=json.loads((root/'.week05_build/country_map_geometry.json').read_text())
countries=data['countries'];codes=[c['iso'] for c in countries]
result={'countries':countries,'world':geometry['world'],'regions':geometry['regions'],'tiny':geometry['tiny'],'embeddings':{},'distances':{},'rankings':{}}
quality=[];coordinate_rows=[]
for name in ['B','E']:
    vectors=pd.read_csv(source/'country_profile_vectors.csv').loc[lambda d:d.candidate.eq(name)].pivot(index='COUNTRY_ISO3',columns='cluster',values='profile_share').reindex(codes)
    transformed=np.sqrt(vectors.to_numpy())/np.sqrt(2)
    centred=transformed-transformed.mean(axis=0)
    u,s,vt=np.linalg.svd(centred,full_matrices=False)
    coordinates=u[:,:2]*s[:2]
    # Deterministic sign for reproducible colours; axis meaning remains purely descriptive.
    for j in range(2):
        if vt[j,np.argmax(np.abs(vt[j]))]<0:coordinates[:,j]*=-1
    original=pdist(transformed);projected=pdist(coordinates)
    original_matrix=squareform(original)
    result['distances'][name]=np.round(original_matrix,8).tolist()
    np.fill_diagonal(original_matrix,np.inf)
    result['rankings'][name]=np.argsort(original_matrix,axis=1,kind='stable')[:,:len(countries)-1].tolist()
    projected_matrix=squareform(projected);np.fill_diagonal(projected_matrix,np.inf)
    reference=original_matrix.argmin(axis=1)
    fraction=float(np.sum(s[:2]**2)/np.sum(s**2))
    correlation=float(spearmanr(original,projected).statistic)
    stress=float(np.sqrt(np.sum((original-projected)**2)/np.sum(original**2)))
    neighbours=float((reference==projected_matrix.argmin(axis=1)).mean())
    quality.append({'candidate':name,'countries':142,'display_dimensions':2,'variance_preserved':fraction,
                    'pair_distance_rank_spearman':correlation,'relative_distance_error':stress,'exact_nearest_preserved_fraction':neighbours,
                    'status':'visual approximation only; original Hellinger tables remain authoritative'})
    result['embeddings'][name]={'coordinates':np.round(coordinates,7).tolist(),'variance':fraction,'rankCorrelation':correlation}
    for i,c in enumerate(countries):coordinate_rows.append({'candidate':name,'COUNTRY_ISO3':c['iso'],'Country':c['name'],'coordinate_1':coordinates[i,0],'coordinate_2':coordinates[i,1]})

def rounded(value):
    if isinstance(value,float):return round(value,3)
    if isinstance(value,list):return [rounded(v) for v in value]
    if isinstance(value,dict):return {k:rounded(v) for k,v in value.items()}
    return value
# Reduce only display geometry precision, never profile proportions or distances.
result['world']=rounded(result['world']);result['regions']=rounded(result['regions'])
fragment=(root/'.week05_build/country-similarity-map-template.html').read_text().replace('__WRP_SIMILARITY_DATA__',json.dumps(result,separators=(',',':')))
inline=Path('docs/index.html')
assert len(fragment.encode())<1_000_000
inline.write_text(fragment)
pd.DataFrame(quality).to_csv(output/'colour_projection_quality.csv',index=False)
pd.DataFrame(coordinate_rows).to_csv(output/'country_colour_coordinates.csv',index=False)
(output/'map_display_data.json').write_text(json.dumps(result,separators=(',',':')))

def rgb_from_lab(L,a,b):
    fy=(L+16)/116;fx=fy+a/500;fz=fy-b/200
    f=np.column_stack([fx,np.full_like(fx,fy),fz])
    delta=6/29
    xyz=np.where(f>delta,f**3,3*delta**2*(f-4/29))*[.95047,1,1.08883]
    linear=xyz @ np.array([[3.2404542,-.9692660,.0556434],[-1.5371385,1.8760108,-.2040259],[-.4985314,.0415560,1.0572252]])
    rgb=np.where(linear<=.0031308,12.92*linear,1.055*np.maximum(linear,0)**(1/2.4)-.055)
    return rgb

def rings(feature):
    g=feature['geometry'];polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
    for p in polys:
        for ring in p:yield np.asarray(ring)

for name in ['B','E']:
    points=np.asarray(result['embeddings'][name]['coordinates'])
    scale=55/np.max(np.linalg.norm(points,axis=1))
    colors=rgb_from_lab(67,points[:,0]*scale,points[:,1]*scale)
    while colors.min()<.03 or colors.max()>.97:
        scale*=.95;colors=rgb_from_lab(67,points[:,0]*scale,points[:,1]*scale)
    color_by_iso=dict(zip(codes,colors))
    fig,ax=plt.subplots(figsize=(16,8.5))
    for f in geometry['world']['features']:
        g=f['geometry'];polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
        for poly in polys:ax.add_patch(Polygon(np.asarray(poly[0]),closed=True,facecolor=color_by_iso.get(f['properties']['id'],'#eeeeee'),edgecolor='#aaaaaa',linewidth=.2))
    for r in geometry['regions']:ax.add_collection(LineCollection(list(rings(r)),colors='#444444',linewidths=.9,alpha=.8))
    for c in countries:
        if c['iso'] in geometry['tiny']:ax.scatter(*c['point'],s=25,c=[color_by_iso[c['iso']]],edgecolor='#444444',linewidth=.6,zorder=5)
    ax.set(xlim=(-180,180),ylim=(-60,85),aspect='equal');ax.set_xticks([]);ax.set_yticks([])
    q=next(q for q in quality if q['candidate']==name)
    ax.set_title(f'{name}: countries with similar frozen profile mixtures have similar colours\nOriginal dataset geographical-area boundaries overlaid',fontsize=16,pad=18)
    key=fig.add_axes([.09,.06,.15,.12]);key.scatter(points[:,0],points[:,1],c=colors,s=16,edgecolors='none');key.set_xticks([]);key.set_yticks([]);key.set_title('2D colour key',fontsize=10)
    fig.text(.27,.12,f'Colour similarity is approximate: {100*q["variance_preserved"]:.1f}% of country-distance variation preserved.',fontsize=11)
    fig.text(.27,.09,'Continuous colours are not country groups, a geographic scale or a low-to-high burden scale.',fontsize=10)
    fig.text(.27,.06,'Thin dark outlines: original GlobalRegion unions. Gray: no study data. Tiny countries: coloured dots.',fontsize=10)
    fig.text(.06,.015,'142 complete-case country mixtures; B/E interpreted separately. Natural Earth de facto boundaries are not a political claim.',fontsize=9)
    fig.savefig(output/f'{name}_continuous_similarity_with_region_outlines.png',dpi=160,bbox_inches='tight');plt.close(fig)
files=[p for p in output.iterdir() if p.is_file() and p.name!='map_manifest.json']
manifest={'status':'completed continuous country-similarity presentation','scientific_source':str(source.relative_to(root)),
          'method':'classical metric MDS of Euclidean Hellinger coordinates; isotropic CIELAB chromatic offsets; no country groups',
          'model_refitting':False,'region_membership_changed':False,'respondent_PCA_used':False,
          'interactive_modes':['approximate global similarity overview','original-distance-from-selected-country'],
          'ranked_list_sizes':[10,20,141], 'distance_display_precision':8,
          'rankings':'all other countries, ordered by unrounded original Hellinger distance; exact ties by ISO3',
          'inline_path':str(inline),'inline_sha256':hashlib.sha256(inline.read_bytes()).hexdigest(),
          'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
          'projection_quality':quality,'geometry_source':'published @d3-maps/atlas@1.0.0; 110m country unions per dataset GlobalRegion',
          'rendering_failures_preserved':['Initial reference-map builder used URL-encoded local path; corrected with fileURLToPath. Reference-map design superseded by user clarification.',
              'Inline ResizeObserver loop reproduced under resize stress (seven browser error events before repair). Repaired with coalesced requestAnimationFrame rendering, width-only resize observation and a persistent hidden colour probe.'],
          'qualifications':['Colour is a 2D approximation; exact Hellinger values remain authoritative','142 observed complete-case distributions, not population-equivalent countries','B/E colour keys are independent; do not compare colours across models']}
(output/'map_manifest.json').write_text(json.dumps(manifest,indent=2))
print('Map projection quality:',quality)
print('Inline bytes:',len(fragment.encode()),'saved static maps:',output)
