"""Export checked aggregate tables for the Atlas. No fitting or respondent-row reads.

Run with the complete analysis workspace as --source-root. A public clone can
rebuild the browser data from its existing wave-results.json without raw surveys.
"""
from pathlib import Path
import argparse, csv, hashlib, json, math, re

REPO=Path(__file__).resolve().parents[1]
CONFIGS=[
 ('full',2021,'course_artifacts/wrp_2021_clustering/280d55eedc4d2067/frozen_2021',(93548,96,24130,25)),
 ('full',2023,'course_artifacts/week05_t5_secondary_transfer/832b01713bc6b240/frozen_model',(109488,113,27972,29)),
 ('full',2025,'course_artifacts/week08_clustering_2025/2206801873a41f37/frozen_2025',(107507,111,27195,29)),
 *[('common_worry',y,f'course_artifacts/wrp_{y}_common_worry/{h}/frozen_model',n) for y,h,n in [
  (2019,'9694e81b0b109044',(114428,114,27614,28)),
  (2021,'cf22836d4e663808',(96196,96,24971,25)),
  (2023,'9132b85be56c6bac',(112753,113,28871,29)),
  (2025,'682e3768a5c6795a',(110436,111,27919,29))]]]
ENSEMBLES='course_artifacts/wrp_cross_wave_ensembles/4defd9d665368b36'
DOMAINS=['food','water','crime','severe_weather','traffic','mental_health']

def validate(data):
 assert set(data['models'])=={f'{f}_{y}' for f,y,_,_ in CONFIGS}
 for key,m in data['models'].items():
  assert len(m['clusters'])==m['k'] and [c['id'] for c in m['clusters']]==list(range(m['k']))
  assert math.isclose(sum(c['share'] for c in m['clusters']),1,abs_tol=1e-10)
  for c in m['clusters']:
   for row in c['worry']:assert len(row)==3 and math.isclose(sum(row),1,abs_tol=1e-10)
   assert len(c['worry'])==(6 if m['family']=='full' else 5)
   assert len(c['harm'])==(2 if m['family']=='full' else 0)
   for row in c['harm']:assert len(row)==7
   assert all(0<=v<=1 for row in c['worry']+c['harm'] for v in row)
 for family,years in [('full',[2021,2023,2025]),('common_worry',[2019,2021,2023,2025])]:
  k=data['models'][family+'_2025']['k']
  for year in years:
   row=data['shares'][family][str(year)];assert len(row)==k and math.isclose(sum(row),1,abs_tol=1e-10)
  for year in years[:-1]:
   mat=data['overlap'][f'{family}_{year}'];assert len(mat)==data['models'][f'{family}_{year}']['k']
   assert all(len(row)==k and math.isclose(sum(row),1,abs_tol=1e-10) for row in mat)
   for s in data['stability'][f'{family}_{year}']:assert -1<=s['p10']<=s['median']<=s['p90']<=1+1e-12

def export(source):
 files={}
 def read(path,kind='csv'):
  p=source/path;files[str(path)]=hashlib.sha256(p.read_bytes()).hexdigest()
  return json.loads(p.read_text()) if kind=='json' else list(csv.DictReader(p.open()))
 data={'schemaVersion':1,'benchmarkYear':2025,'models':{},'shares':{},'overlap':{},'stability':{},'reference':{}}
 for family,year,path,counts in CONFIGS:
  p=Path(path);spec=read(p/'specification.json','json');seal=read(p/'freeze_seal.json','json');s=spec.get('spec',spec)
  assert hashlib.sha256((source/p/'specification.json').read_bytes()).hexdigest()==seal['files']['specification.json']
  names=spec.get('cluster_names',spec.get('profile_names'));names={int(k):v for k,v in (names.items() if isinstance(names,dict) else enumerate(names))}
  if family=='full' and year==2023:
   shares=[r for r in read(p/'development_prevalence.csv') if r['scope']=='global']
   for r in shares:r['share']=r['equal_country_weighted_share']
   native=[r for r in read(p/'development_original_category_profiles.csv') if r['scope']=='global']
   for r in native:r.update(answer=r['category'],probability=r['proportion'])
   assert int(shares[0]['area_respondents'])==counts[0] and int(shares[0]['area_countries'])==counts[1]
  else:
   shares=[r for r in read(p/'cluster_prevalence_by_split.csv') if r['split']=='train']
   native=read(p/'development_answer_distributions.csv');elig=read(p/'eligibility_by_split.csv')
   assert int(next(r for r in elig if r['split']=='train')['eligible'])==counts[0]
   assert int(next(r for r in elig if r['split']=='heldout_country')['eligible'])==counts[2]
  probabilities={(int(r['cluster']),r['feature'],int(r['answer'])):float(r['probability']) for r in native}
  worries=DOMAINS if family=='full' else [d for d in DOMAINS if d!='traffic']
  clusters=[]
  for c in range(int(s['k'])):
   clusters.append(dict(id=c,name=names[c],share=float(next(r for r in shares if int(r['cluster'])==c)['share']),
    worry=[[probabilities[c,'worry_'+d,a] for a in range(3)] for d in worries],
    harm=[[probabilities[c,'harm_'+d+'_'+kind,1] for d in DOMAINS+['work']] for kind in ['personal','known_person']] if family=='full' else []))
  data['models'][f'{family}_{year}']=dict(year=year,family=family,id=spec.get('model_id','T5'),k=int(s['k']),q=float(s['q']),t=float(s.get('t',1/s['q'])),alpha=float(s.get('alpha',1)),respondents=counts[0],countries=counts[1],heldoutRespondents=counts[2],heldoutCountries=counts[3],clusters=clusters,worryDomains=worries)
 for name in ['verification.json','additional_verification.json']:
  assert read(Path(ENSEMBLES)/name,'json')['status']=='passed'
 shares=read(Path(ENSEMBLES)/'fixed_2025_prevalence.csv');overlap=read(Path(ENSEMBLES)/'frozen_overlap_tables.csv');ari=read(Path(ENSEMBLES)/'ensemble_summary.csv');reference=read(Path(ENSEMBLES)/'reference_population.csv')
 for family,years in [('full',[2021,2023,2025]),('common_worry',[2019,2021,2023,2025])]:
  data['shares'][family]={str(y):[float(r['share']) for r in sorted([r for r in shares if r['family']==family and int(r['year'])==y],key=lambda r:int(r['benchmark_cluster']))] for y in years}
  rows=[r for r in reference if r['family']==family]
  data['reference'][family]=dict(countries=int(rows[0]['countries']),respondents=sum(int(r['respondents']) for r in rows),respondents2025=int(next(r for r in rows if int(r['year'])==2025)['respondents']))
  for y in years[:-1]:
   rows=[r for r in overlap if r['family']==family and int(r['year_a'])==y and int(r['year_b'])==2025 and r['evaluation']=='2025']
   data['overlap'][f'{family}_{y}']=[[float(next(r for r in rows if int(r['cluster_a'])==i and int(r['cluster_b'])==j)['row_fraction']) for j in range(data['models'][family+'_2025']['k'])] for i in range(data['models'][f'{family}_{y}']['k'])]
   values=[]
   for a,b in [(y,y),(y,2025),(2025,2025)]:
    r=next(r for r in ari if r['family']==family and r['kind']=='countries' and int(r['year_a'])==a and int(r['year_b'])==b and r['evaluation']=='2025' and r['metric']=='ARI')
    values.append({name:float(r[name]) for name in ['p10','median','p90']})
   data['stability'][f'{family}_{y}']=values
 return data,dict(exported='2026-10-29',source_files_sha256=files,aggregate_only=True,scientific_fits=0,heldout_reassessment=False,ensemble_context=ENSEMBLES,weighting={'cluster_shares_and_overlap':'Equal country totals and relative survey weights within eligible country populations.','ARI':'Ordinary respondent-count adjusted Rand index.'},country_frames={'full':92,'common_worry':90})

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-root',type=Path);args=parser.parse_args();out=REPO/'docs/data';out.mkdir(exist_ok=True)
 if args.source_root:
  data,provenance=export(args.source_root.resolve());validate(data)
  (out/'wave-results.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
  (out/'wave-results.sources.json').write_text(json.dumps(provenance,indent=2)+'\n')
 else:
  data=json.loads((out/'wave-results.json').read_text());validate(data)
 # A script asset works through file:// as well as GitHub Pages; no fetch needed.
 payload=json.dumps(data,separators=(',',':'),ensure_ascii=False).replace('<','\\u003c')
 (out/'wave-results.js').write_text('/* Aggregate WRP results. Rebuild with scripts/export_wave_atlas_data.py. */\nwindow.WRP_WAVE_DATA = '+payload+';\n')
 print('Verified seven wave models; wrote browser data without fitting or reading respondent rows.')
if __name__=='__main__':main()
