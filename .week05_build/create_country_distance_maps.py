"""Present already-computed country distances, with original GlobalRegion unions; no new scientific fits."""
from pathlib import Path
import json,hashlib,subprocess
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Patch
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

root=Path(__file__).resolve().parent.parent
source=root/'course_artifacts/week05_country_similarity_and_profile_synthesis_v1/d694096841b06e54'
output=root/'course_artifacts/week05_country_distance_maps_v1'
output.mkdir(exist_ok=True)
countries=pd.read_csv(source/'country_profile_vectors.csv').drop_duplicates('COUNTRY_ISO3').sort_values('COUNTRY_ISO3').reset_index(drop=True)
world=json.loads((root/'course_artifacts/cartography/ne_50m_admin_0_countries.geojson').read_text())
features={}
for f in world['features']:
    code={'KOS':'XKX','SDS':'SSD','PSX':'PSE'}.get(f['properties']['ADM0_A3'],f['properties']['ADM0_A3'])
    features[code]=f
tiny=[];meta=[]
for row in countries.itertuples():
    f=features[row.COUNTRY_ISO3];geom=f['geometry'];polys=geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]
    if max(np.ptp(np.asarray(p[0])[:,0])*np.ptp(np.asarray(p[0])[:,1]) for p in polys)<2:tiny.append(row.COUNTRY_ISO3)
    meta.append({'iso':row.COUNTRY_ISO3,'name':row.Country,'regionId':int(row.GlobalRegion),'region':row.region_name,
                 'retention':round(row.retained_fraction,6),'point':[float(f['properties']['LABEL_X']),float(f['properties']['LABEL_Y'])]})
distances={}
for model in ['B','E']:
    table=pd.read_csv(source/f'{model}_all_countries_post_validation_hellinger_matrix.csv').set_index('COUNTRY_ISO3')
    assert list(table.index)==countries.COUNTRY_ISO3.to_list()
    assert list(table.columns)==countries.COUNTRY_ISO3.to_list()
    distances[model]=np.round(table.to_numpy(),6).tolist()
numerical={'countries':meta,'distances':distances,'tiny':tiny}
(root/'.week05_build/country_map_numerical_data.json').write_text(json.dumps(numerical,separators=(',',':')))
subprocess.run(['node',str(root/'.week05_build/build_country_map_data.mjs')],check=True)
geometry=json.loads((root/'.week05_build/country_map_geometry.json').read_text())

def ring_segments(feature):
    geom=feature['geometry'];polys=geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]
    for poly in polys:
        for ring in poly:yield np.asarray(ring)

reference='FIN'
ref=next(c for c in meta if c['iso']==reference)
for model in ['B','E']:
    row=np.asarray(distances[model][next(i for i,c in enumerate(meta) if c['iso']==reference)])
    values=dict(zip(countries.COUNTRY_ISO3,row))
    fig,ax=plt.subplots(figsize=(16,8.5))
    cmap=plt.get_cmap('viridis');norm=Normalize(0,1)
    for code,f in features.items():
        if code=='ATA':continue
        geom=f['geometry'];polys=geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]
        for poly in polys:ax.add_patch(Polygon(np.asarray(poly[0]),closed=True,facecolor=cmap(norm(values[code])) if code in values else '#e9e9e9',edgecolor='#aaaaaa',linewidth=.18))
    # Dissolved unions follow the original dataset regions. Coarse published outlines are for presentation only.
    for region in geometry['regions']:
        ax.add_collection(LineCollection(list(ring_segments(region)),colors='#53535d',linewidths=.9,alpha=.6))
    selected=next(r for r in geometry['regions'] if r['properties']['regionId']==ref['regionId'])
    ax.add_collection(LineCollection(list(ring_segments(selected)),colors='#d64b39',linewidths=2.1))
    for c in meta:
        if c['iso'] in geometry['tiny']:ax.scatter(*c['point'],s=22,c=[cmap(norm(values[c['iso']]))],edgecolor='#555555',linewidth=.5,zorder=5)
    ax.scatter(*ref['point'],s=110,marker='*',c='black',edgecolor='white',linewidth=.8,zorder=7)
    ax.annotate('Finland',ref['point'],xytext=(8,6),textcoords='offset points',fontsize=11,fontweight='bold',zorder=8)
    ax.set(xlim=(-180,180),ylim=(-60,85),aspect='equal');ax.set_xticks([]);ax.set_yticks([])
    ax.set_title(f'{model}: distance from Finland in frozen global-profile proportions\nOriginal dataset regions overlaid; highlighted region: {ref["region"]}',fontsize=15,pad=16)
    fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),ax=ax,orientation='horizontal',fraction=.035,pad=.065,shrink=.65).set_label('Hellinger distance: 0 = identical proportions; 1 = disjoint profile support')
    ax.legend(handles=[Patch(facecolor='none',edgecolor='#53535d',label='Original dataset-region outlines'),Patch(facecolor='none',edgecolor='#d64b39',label='Reference country’s region'),Patch(facecolor='#e9e9e9',label='No study data')],loc='lower center',bbox_to_anchor=(.5,-.02),ncol=3,fontsize=9)
    nearest=np.argsort(row+np.where(np.arange(len(row))==next(i for i,c in enumerate(meta) if c['iso']==reference),np.inf,0))[:5]
    text='Closest five: '+' · '.join(meta[i]['name']+f' ({row[i]:.3f})' for i in nearest)
    fig.text(.06,.03,text,fontsize=10)
    fig.text(.06,.005,'Complete-case country mixtures, not whole-country social equivalence. Reference selected for illustration. Natural Earth de facto boundaries are not a political claim.',fontsize=9)
    fig.savefig(output/f'{model}_distance_from_FIN_with_dataset_regions.png',dpi=160,bbox_inches='tight');plt.close(fig)
manifest={'status':'completed presentation of existing distances','reference_example':'FIN','region_source':'unchanged dataset GlobalRegion',
    'interactive_reference_choices':142,'regions':15,'new_model_fits':False,'distances_recomputed':False,
    'geometry':'Natural Earth 50m fills; published @d3-maps/atlas 110m regional unions; missing tiny polygons shown with verified map-label-point markers',
    'tiny_countries_without_110m_polygon':geometry['missingCountryPolygons'],
    'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.glob('*.png'))}}
(output/'country_distance_map_manifest.json').write_text(json.dumps(manifest,indent=2))
print('Saved direct distance maps with geographical overlays:',output)
