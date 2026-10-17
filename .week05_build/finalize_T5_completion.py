"""Finish reports and the local aggregate-only GitHub package after regional fits."""
from pathlib import Path
import html
import json
import re
import shutil
import subprocess
import sys
import time
import hashlib
import nbformat
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import LineCollection
import week05_core as a
from country_response_distances import response_features

ROOT=Path(__file__).resolve().parents[1]
pointer=json.loads((ROOT/'course_artifacts/week05_T5_completion/current_run.json').read_text())
out=ROOT/pointer['output']
c=out/'countries'; pub=ROOT/'github_publication'
while not (out/'regional_complete.json').exists():
    print('Waiting for regional stability completion',flush=True);time.sleep(30)
regional=json.loads((out/'regional_complete.json').read_text())
support=pd.read_csv(out/'supported_local_resolutions.csv')
country=json.loads((c/'country_completion.json').read_text())
registry=pd.read_parquet(ROOT/'course_artifacts/week05_t5_secondary_transfer/832b01713bc6b240/all_respondents_T5_eligibility_and_frozen_profiles.parquet')
raw=response_features(pd.concat([pd.read_parquet(ROOT/'course_artifacts'/p) for p in
 ['week03_development_data.parquet','week03_heldout_country_data.parquet']],ignore_index=True))
raw=raw.merge(registry[['WPID_RANDOM','complete_case','T5_cluster']],on='WPID_RANDOM',validate='one_to_one')
raw=raw.loc[raw.complete_case].copy();raw.T5_cluster=raw.T5_cluster.astype(int)
regions=pd.read_csv(out/'development_regions.csv').set_index('GlobalRegion').region_name.to_dict()
rows=[];profiles=[]
for split,part in [('train',raw.loc[raw.country_split.eq('train')]),('heldout_country',raw.loc[raw.country_split.eq('heldout_country')]),('all',raw)]:
 for area,group in [('global',part)]+[(str(r),g) for r,g in part.groupby('GlobalRegion')]:
  w=a.country_weights(group); labels=group.T5_cluster.to_numpy()
  for k in range(5):rows.append({'split':split,'area':area,'region_name':regions.get(int(area),area) if area!='global' else 'Global',
   'cluster':k,'countries':group.COUNTRY_ISO3.nunique(),'respondents':int((labels==k).sum()),'equal_country_share':float(w[labels==k].sum())})
  p=a.original_profiles(group,labels,w);p['split']=split;p['area']=area;profiles.append(p)
pd.DataFrame(rows).to_csv(out/'T5_fixed_profiles_by_split_and_region.csv',index=False)
pd.concat(profiles).to_csv(out/'T5_original_categories_by_split_and_region.csv',index=False)
table=pd.DataFrame(rows).query("split=='all' and area!='global'").pivot(index='region_name',columns='cluster',values='equal_country_share')
ax=table.plot.barh(stacked=True,figsize=(11,7),color=['#637485','#e66e57','#087e8b','#7462a0','#d9a441'])
ax.set(xlabel='Equal-country profile proportion',ylabel='',title='Frozen T5 profiles within dataset regions; all 142 countries')
ax.legend(['C0 Lower worry','C1 Known-person harm','C2 Crime/weather','C3 Mental/traffic/weather','C4 Water/food'],fontsize=8,loc='upper center',bbox_to_anchor=(.5,-.12),ncol=3)
plt.tight_layout();plt.savefig(out/'figures/T5_region_prevalence.png',dpi=150,bbox_inches='tight');plt.close()
geo=json.loads((ROOT/'.week05_build/country_map_geometry.json').read_text())
codes=pd.read_csv(c/'country_colour_coordinates.csv').COUNTRY_ISO3.tolist()
matrix=pd.read_csv(c/'T5_responses_all_countries_post_validation_median_relative_matrix.csv',index_col=0)
for iso in ['FIN','USA']:
 colors={code:plt.get_cmap('RdYlGn_r')(min(2,float(matrix.loc[iso,code]))/2) for code in codes}
 fig,ax=plt.subplots(figsize=(14,7))
 for f in geo['world']['features']:
  g=f['geometry'];polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
  for poly in polys:ax.add_patch(Polygon(poly[0],facecolor=colors.get(f['properties']['id'],'#eeeeee'),edgecolor='#999999',linewidth=.2))
 for f in geo['regions']:
  g=f['geometry'];polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
  ax.add_collection(LineCollection([ring for poly in polys for ring in poly],colors='#444444',linewidth=.7))
 ax.set(xlim=(-180,180),ylim=(-60,85),aspect='equal',title=f'T5 allocation: original-response distance from {iso}; dataset regions overlaid')
 ax.set_axis_off();fig.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(0,2),cmap='RdYlGn_r'),ax=ax,orientation='horizontal',shrink=.6,label='Fixed median-relative distance: 0 identical; 1 reference median; 2 or more')
 fig.savefig(c/f'T5_distance_from_{iso}_regions.png',dpi=150,bbox_inches='tight');plt.close(fig)

# Extend existing offline pages. Historical data and B/E scale denominators stay intact.
tools=(ROOT/'.week05_build/country-response-distance-tools.js').read_text()
tools=tools.replace("['worry','self','known','B','E']","['worry','self','known','B','E','T5']")
tools=tools.replace('E:.75*w+.125*s+.125*k','E:.75*w+.125*s+.125*k,T5:source.alphas.T5*w+(1-source.alphas.T5)*(s+k)/2')
tools=tools.replace("title:(basis,model,component)=>", "title:(basis,model,component)=>model==='T5'?(basis==='profiles'?'T5 · five frozen profiles':component==='overall'?'T5 · optimized worry/harm allocation':`${labels[component]} · original responses`):")
tools=tools.replace("description:(basis,model,component)=>", "description:(basis,model,component)=>model==='T5'?(basis==='profiles'?'Compares country proportions across the five fixed T5 profiles.':component==='overall'?'Worry receives 58.4%; personal and known-person harm each receive 20.8%.':'Uses this response component only.'): ")
for file,identity,template,placeholder in [('countries.html','wrp-sim-data','country-similarity-map-template.html','__WRP_SIMILARITY_DATA__'),('country-income.html','wrp-inc-data','country-income-map-template.html','__WRP_INCOME_DATA__')]:
 document=(pub/'docs'/file).read_text();match=re.search(r'data-srcdoc="(.*?)"',document,re.S);inner=html.unescape(match[1])
 data=json.loads(re.search('<script id="'+identity+'" type="application/json">(.*?)</script>',inner,re.S)[1])
 assert [v['iso'] for v in data['countries']]==codes
 d=pd.read_csv(c/'T5_profiles_all_countries_post_validation_raw_matrix.csv',index_col=0).loc[codes,codes].to_numpy()
 data['distances']['T5']=d.tolist()
 coordinates=pd.read_csv(c/'country_colour_coordinates.csv').set_index('COUNTRY_ISO3').loc[codes]
 if 'embeddings' in data:
  q=country['colour_projection_quality'];data['embeddings']['T5']={'coordinates':coordinates[['coordinate_1','coordinate_2']].values.tolist(),'variance':q['variance_preserved'],'rankCorrelation':q['distance_rank_spearman']}
 data['responses']['alphas']['T5']=country['alpha']
 income=pd.read_csv(c/'income_distance_summary.csv')
 for basis,metric in [(data['responses']['income'],'T5_responses'),(data,'T5_profiles')]:
  basis.setdefault('summaries',{})['T5']={};basis.setdefault('matrices',{})['T5']={}
  for scope in ['development','all_countries_post_validation']:
   r=income.loc[income.metric.eq(metric)&income.scope.eq(scope)].iloc[0]
   basis['summaries']['T5'][scope]={'classified_countries':int(r.classified_countries),'ordinal_gap_spearman':float(r.ordinal_gap_spearman),'within_region_spearman':float(r.within_region_spearman)}
   grid=country['income_cells'][metric+':'+scope]
   if metric=='T5_profiles':grid=[[dict(cell,mean_hellinger=cell['mean_distance']) for cell in row] for row in grid]
   basis['matrices']['T5'][scope]=grid
 text=(ROOT/'.week05_build'/template).read_text()
 # T5 replaces the primary B panel; the historical E comparison remains labelled.
 text=text.replace('-B','-T5').replace("'B'","'T5'").replace('value="B"','value="T5"').replace("['B','E']","['T5','E']")
 text=text.replace('four or eight','five or eight').replace('two weighting choices','T5 and historical worry emphasis')
 text=text.replace("mode==='E'?'E':'T5'","mode==='E'?'E':'T5'")
 text=text.replace("basis==='profiles'?'Four-profile comparison':'Worry and harm equally weighted'","basis==='profiles'?'T5 · five profiles':'T5 · optimized allocation'")
 text=text.replace('The two overall comparisons share one fixed reference median.','T5 and the historical comparison use the unchanged fixed cross-model reference median.')
 text=text.replace(placeholder,json.dumps(data,separators=(',',':'))).replace('__WRP_RESPONSE_TOOLS__',tools)
 vendor=(pub/'docs/vendor/d3.min.js').read_text()
 text=text.replace('<script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>','<script>'+vendor+'</script>')
 # Retain the proven outer wrapper and its host CSS, replacing only the fragment.
 root_id='wrp-mixture-similarity' if file=='countries.html' else 'wrp-country-income'
 start=inner.index('<div id="'+root_id+'">');tail=inner.index("const root=document.getElementById('")+len("const root=document.getElementById('")
 end=inner.index('</script>',tail)+len('</script>')
 updated=inner[:start]+text.rstrip()+'\n'+inner[end:].lstrip()
 rendered=document[:match.start(1)]+html.escape(updated,quote=True)+document[match.end(1):]
 rendered=re.sub(r'<p id="historical-distance-note".*?</p>','<p id="historical-distance-note" style="max-width:1120px;margin:1rem auto">T5 is the primary comparison; E8 is historical. Original-response distances use the stated allocation, not worry-category numeric spacing. Fixed cross-model median scales are unchanged.</p>',rendered,flags=re.S)
 (pub/'docs'/file).write_text(rendered)

supported=support.loc[support.status.eq('both full stability benchmarks met')]
summary=f"T5 regional completion: {len(supported)} cases pass both full stability tests; {regional['failed_stability_fits']} failed stability fits. Small-region LOO and respondent-only diagnostics are not full geographic confirmation. Global T5 was not refitted."
nbpath=ROOT/'weekly_notebooks/week05_validate_frozen_profiles.ipynb';nb=nbformat.read(nbpath,as_version=4)
prior=next((i for i,cell in enumerate(nb.cells) if cell.cell_type=='markdown' and cell.source.startswith('## 6. Complete the geographical')),None)
if prior is not None:
 stop=next(i for i,cell in enumerate(nb.cells) if cell.cell_type=='markdown' and cell.source.startswith('## Appendix A'))
 del nb.cells[prior:stop]
start=next(i for i,cell in enumerate(nb.cells) if cell.cell_type=='markdown' and cell.source.startswith('## Appendix A'))
extra=[nbformat.v4.new_markdown_cell('## 6. Complete the geographical and country analyses under T5\n\n'+summary+'\n\nRegional selection holds the T5 geometry fixed, examines k=2–10, and tests k=5 plus coarse and inertia-based alternatives. The 0.80 median/lower-decile ARI rule is unchanged. Structural global benchmarks are reported, not imposed as universal regional filters. Compare regional meaning and overlaps; do not equate different local labels across regions.\n\nCountry distances use common global T5 profiles or original marginal categories, not unmatched local cluster numbers. Hellinger uses profile proportions; total variation uses alpha=0.5838 and is deliberately insensitive to numeric worry coding t. Both are post-validation descriptions. Bootstrap results condition on fixed assignments and do not represent survey-design or model-selection uncertainty. Income-label permutations move whole countries, not independent pairs.\n\nThe fixed all-country cross-model median denominators are retained, so adding T5 does not recolour historical B/E results. Map projection quality measures the loss from approximate two-dimensional colours; exact rankings use the original distance.'),
 nbformat.v4.new_code_cell("T5_COMPLETION = ART / "+repr(str(out.relative_to(ROOT/'course_artifacts')))+"\nfor filename in ['supported_local_resolutions.csv','matched_regional_semantic_correspondence.csv','T5_fixed_profiles_by_split_and_region.csv']:\n    print(filename)\n    display(pd.read_csv(T5_COMPLETION / filename).round(4))\nfor filename in ['country_geography_summary.csv','income_distance_summary.csv','income_country_label_permutations.csv','profile_burden_and_heterogeneity.csv','burden_only_information_loss.csv','country_tree_cut_diagnostics.csv','conditional_nearest_neighbour_bootstrap.csv']:\n    print(filename)\n    display(pd.read_csv(T5_COMPLETION / 'countries' / filename).round(4))\ndisplay(Image(filename=str(T5_COMPLETION / 'figures/T5_local_resolution_stability.png')))\ndisplay(Image(filename=str(T5_COMPLETION / 'figures/T5_region_prevalence.png')))\nfor iso in ['FIN','USA']:\n    display(Image(filename=str(T5_COMPLETION / 'countries' / f'T5_distance_from_{iso}_regions.png')))")]
nb.cells[start:start]=extra
nbformat.write(nb,nbpath)
subprocess.run([sys.executable,str(ROOT/'.week06_build/replay_notebooks.py'),'weekly_notebooks/week05_validate_frozen_profiles.ipynb'],check=True)

# Publish only aggregate exports and cleared notebooks, never fits or student data.
changed=[]
for p in out.rglob('*'):
 if p.is_file() and 'fits' not in p.parts and p.suffix in ['.csv','.json','.png']:
  if p.suffix=='.csv':
   try: columns=set(pd.read_csv(p,nrows=0).columns.str.lower())
   except pd.errors.EmptyDataError: continue
   assert not {'wpid_random','respondent_id','wgt'}&columns,p
  dest=pub/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);changed.append(str(dest.relative_to(pub)))
for filename in ['week05_validate_frozen_profiles.ipynb','week06_predicting_frozen_risk_profile_membership.ipynb']:
 book=nbformat.read(ROOT/'weekly_notebooks'/filename,as_version=4)
 for cell in book.cells:
  if cell.cell_type=='code':cell.outputs=[];cell.execution_count=None
 nbformat.write(book,pub/'weekly_notebooks'/filename)
for filename in ['complete_T5_regions.py','complete_T5_countries.py','T5_country_tools.py','finalize_T5_completion.py']:
 shutil.copy2(ROOT/'.week05_build'/filename,pub/'.week05_build'/filename)
(pub/'.week06_build').mkdir(exist_ok=True)
for filename in ['week06_t5_core.py','run_T5.py','build_T5_notebook.py','replay_notebooks.py']:
 shutil.copy2(ROOT/'.week06_build'/filename,pub/'.week06_build'/filename)
predict=ROOT/'course_artifacts/week06_objective2_T5_prediction/c154072347caff55'
for p in predict.rglob('*'):
 if p.is_file() and p.suffix in ['.csv','.json','.png']:
  if p.suffix=='.csv' and {'wpid_random','respondent_id','wgt'}&set(pd.read_csv(p,nrows=0).columns.str.lower()):continue
  dest=pub/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
readme=pub/'README.md';body=readme.read_text();body=body.replace('Week 6 is an earlier B/E prediction draft, not a T5 evaluation.','Week 5 regional and country analyses now also use T5. Week 6 evaluates prediction of T5 membership; held-out balanced accuracy is 0.261 and macro-F1 0.223, so individual prediction remains weak.')
body=body.replace('Earlier B/E prediction draft; not yet migrated to T5','Predict frozen T5 membership from background variables')
body+='\n\nT5 geographical completion: '+summary+' Numerical tables are under `course_artifacts/'+str(out.relative_to(ROOT/'course_artifacts'))+'`. The country and income pages now include T5. No respondent assignment files, fit caches or original responses are published.\n';readme.write_text(body)
for name in ['T5_RESULTS.md','RESULTS.md','METHODS.md']:
 path=pub/'research'/name;body=path.read_text()
 body=body.replace('Country maps still show explicitly labelled historical B/E comparisons. Week 6\nand the manuscript have not been migrated in this publication update.','Country maps now include T5. Week 6 predicts T5 membership; the manuscript is maintained separately.')
 heading='\n\n## T5 geographical completion — 17 October 2026\n'
 if heading in body:body=body.split(heading)[0]
 body+=heading+summary+'\n\nThe same frozen T5 geometry is used for all independent regional fits. The regional protocol selects alternatives without using agreement with the global labels. Country mixtures, region-wise original responses, 200 conditional respondent bootstraps, exploratory country groups, original-response distances and 999 whole-country income-label permutations are saved. Small regions have limited or unavailable country tests. Global profiles, local profiles and country groups must not be treated as the same objects.\n\nCountry original-response distance gives worry alpha=0.5837857862168715, and personal/known-person harm half of the remaining allocation each. Total variation uses category probabilities and deliberately does not depend on numeric worry spacing t. The established cross-model median scales are retained. Pairwise correlations do not have independent-pair significance tests.\n\nAcross 141 income-classified countries, income-gap Spearman correlation is 0.2469 for T5 mixture Hellinger distance and 0.2977 for original-response distance. These are exploratory associations, not causal explanations.\n\nSee [Week 5 notebook](../weekly_notebooks/week05_validate_frozen_profiles.ipynb) and [completion tables](../course_artifacts/'+str(out.relative_to(ROOT/'course_artifacts'))+'/regional_complete.json). Week 6 logistic prediction remains weak: held-out balanced accuracy 0.2608 and macro-F1 0.2230.\n'
 path.write_text(body)
receipt={'status':'complete','regional':regional,'countries':country,'public_aggregate_files':len(changed),'notebook_replayed':True,'student_data_published':False,'pushed':False}
a.atomic_json(receipt,out/'completion.json');a.atomic_json({'output':str(out.relative_to(ROOT)),'context':pointer['context'],'status':'complete'},pub/'course_artifacts/week05_T5_completion/current_run.json')
a.atomic_json({'status':'prepared locally; not pushed','updated':changed,'primary_model':'T5'},pub/'T5_completion_publication.json')
manifest_path=pub/'publication_manifest.json';manifest=json.loads(manifest_path.read_text())
manifest['T5_completion_context']=pointer['context']
manifest['T5_completion_date']='2026-10-17'
records={r['path']:r for r in manifest.get('source_records',[])}
for p in pub.rglob('*'):
 if not p.is_file() or p==manifest_path or '.git' in p.relative_to(pub).parts:continue
 relative=str(p.relative_to(pub));local=ROOT/relative
 records[relative]={'path':relative,'source':relative if local.is_file() else 'publication-local:'+relative,
  'source_sha256':a.file_sha256(local) if local.is_file() else a.file_sha256(p),
  'publication_sha256':a.file_sha256(p),'bytes':p.stat().st_size,
  'modified_for_publication':local.is_file() and a.file_sha256(local)!=a.file_sha256(p)}
manifest['source_records']=list(records.values());a.atomic_json(manifest,manifest_path)
print(summary,flush=True)
