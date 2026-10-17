"""Interpret and verify completed T5 analyses. No clustering or classifier fits."""
from pathlib import Path
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import nbformat
import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'github_publication'
pointer=json.loads((ROOT/'course_artifacts/week05_T5_completion/current_run.json').read_text())
OUT=ROOT/pointer['output'];COUNTRIES=OUT/'countries'
FROZEN=ROOT/'course_artifacts/week05_t5_secondary_transfer/832b01713bc6b240'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
registry_path=FROZEN/'all_respondents_T5_eligibility_and_frozen_profiles.parquet'
assert sha(registry_path)=='b23e3d040dc91da14ef8b95c7786d937567402c9337d617335263c1a8e77a5b6'
registry=pd.read_parquet(registry_path)
complete=registry.loc[registry.complete_case].copy()
assert len(complete)==137460 and complete.WPID_RANDOM.is_unique
seal=json.loads((FROZEN/'frozen_model/freeze_seal.json').read_text())
for name,digest in seal['files'].items():assert sha(FROZEN/'frozen_model'/name)==digest,name
support=pd.read_csv(OUT/'supported_local_resolutions.csv')
full=support.loc[support.status.eq('both full stability benchmarks met')]
limited=support.loc[support.status.str.contains('limited LOO|respondent-only',regex=True)]
assert len(full)==6 and len(limited)==3 and not full.k.eq(5).any()
stability=pd.read_csv(OUT/'regional_stability_summary.csv')
assert stability.successful_fits.sum()==5228 and stability.failed_fits.sum()==0
assert len(pd.read_csv(OUT/'regional_reference_summary.csv'))==135
assert support.groupby('region').k.apply(lambda k:5 in k.values).all()
assert set(pd.read_csv(OUT/'development_regions.csv').GlobalRegion)==set(range(1,16))

# Describe the actually supported local resolutions, without equating local IDs
# or choosing them for agreement with the global profiles.
local_profiles=pd.read_csv(OUT/'regional_original_profiles.csv')
global_profiles=pd.read_csv(OUT/'fixed_global_original_profiles_by_region.csv').query("scope=='global'")
overlaps=pd.read_csv(OUT/'regional_overlaps.csv')
names=json.loads((FROZEN/'frozen_model/specification.json').read_text())['profile_names']
semantic=[]
for ref in pd.concat([full,limited]).itertuples():
 profiles=local_profiles.loc[local_profiles.region.eq(ref.region)&local_profiles.k.eq(ref.k)]
 cross=overlaps.loc[overlaps.region.eq(ref.region)&overlaps.k.eq(ref.k)]
 for cluster,group in profiles.groupby('cluster'):
  member=cross.loc[cross.local_cluster.eq(cluster)].sort_values('global_given_local',ascending=False).iloc[0]
  target=int(member.global_cluster)
  aligned=group.merge(global_profiles.loc[global_profiles.cluster.eq(target),['feature','category','proportion']],
   on=['feature','category'],suffixes=('_local','_global'),validate='one_to_one')
  tv=aligned.assign(gap=abs(aligned.proportion_local-aligned.proportion_global)).groupby('feature').gap.sum()/2
  anchors=group.sort_values('difference_vs_outside',ascending=False).drop_duplicates('feature').head(3)
  semantic.append({'region':ref.region,'region_name':ref.region_name,'k':ref.k,'local_cluster':cluster,
   'stability_status':ref.status,'local_share':group.cluster_share.iloc[0],
   'dominant_global_profile':'T5_C'+str(target),'global_description':names[str(target)],
   'dominant_global_fraction':member.global_given_local,'mean_original_feature_total_variation':tv.mean(),
   'original_contrasts':'; '.join(f'{r.feature}, category {int(r.category)}: {100*r.proportion:.1f}% (outside {100*r.outside_proportion:.1f}%)' for r in anchors.itertuples()),
   'interpretation':'overlap-based correspondence, not an identity or a new shared regional label'})
pd.DataFrame(semantic).to_csv(OUT/'supported_local_semantic_correspondence.csv',index=False)

# Verify country profile vectors and all raw/scaled matrix identities independently.
weighted=complete.assign(mass=complete.WGT/complete.groupby('COUNTRY_ISO3').WGT.transform('sum'))
vectors=weighted.groupby(['COUNTRY_ISO3','T5_cluster']).mass.sum().unstack(fill_value=0).sort_index()
assert np.allclose(vectors.sum(axis=1),1)
saved=pd.read_csv(COUNTRIES/'country_profile_vectors.csv').pivot(index='COUNTRY_ISO3',columns='cluster',values='profile_share').loc[vectors.index,vectors.columns]
assert np.allclose(vectors,saved,atol=1e-14)
hellinger=squareform(pdist(np.sqrt(vectors)))/np.sqrt(2)
country_manifest=json.loads((COUNTRIES/'country_completion.json').read_text())
for metric in ['T5_profiles','T5_responses','worry','self','known']:
 raw=pd.read_csv(COUNTRIES/f'{metric}_all_countries_post_validation_raw_matrix.csv',index_col=0).loc[vectors.index,vectors.index]
 ratio=pd.read_csv(COUNTRIES/f'{metric}_all_countries_post_validation_median_relative_matrix.csv',index_col=0).loc[vectors.index,vectors.index]
 assert np.allclose(raw,raw.T) and np.allclose(np.diag(raw),0)
 assert np.allclose(ratio,raw/country_manifest['scales'][metric])
 dev=pd.read_csv(COUNTRIES/f'{metric}_development_raw_matrix.csv',index_col=0)
 assert np.allclose(dev,raw.loc[dev.index,dev.columns])
 if metric=='T5_profiles':assert np.allclose(raw,hellinger,atol=1e-14)
alpha=country_manifest['alpha']
matrix=lambda key:pd.read_csv(COUNTRIES/f'{key}_all_countries_post_validation_raw_matrix.csv',index_col=0).to_numpy()
assert np.allclose(matrix('T5_responses'),alpha*matrix('worry')+(1-alpha)*(matrix('self')+matrix('known'))/2,atol=1e-14)
assert country_manifest['scales']['T5_responses']==.1550977480973838

interpretation='''### Interpretation of the completed T5 geographical analyses

None of the 11 regions with the full 50-fit country test has a five-cluster solution passing both stability tests. Four other regions have limited or unavailable country tests. The supported full-test resolutions are Eastern Africa k=3; Central/Western Africa k=3 and 4; Latin America/Caribbean k=3 and 4; Northern/Western Europe k=2. Northern Africa k=4 passes respondent and limited leave-one-country-out diagnostics only. The one-country development regions have no geographic-stability test. Multiple supported resolutions are alternatives, not proof of a unique local optimum. Global size/imbalance rules are reported as benchmarks, not imposed as universal regional filters.

This is a material limit on a universal interpretation of the five global profiles. T5 is a stable, useful common global description, but independent regional optimization does not reproduce five reliable groups everywhere. That does not invalidate applying fixed global profiles within regions: fixed assignment and independent regional discovery answer different questions. Neither justifies claiming five universal sociological types.

Some stable local solutions are simple. The Northern/Western European k=2 solution separates a group with 98.7% known-person mental-health harm from a group with 0%. Its stability should not be presented as evidence of a rich multifeature regional taxonomy. Supported local profiles and their original-unit contrasts are saved separately; local numeric IDs have no common meaning across regions. Correspondence to T5 uses observed membership overlap and category differences, not an assumption that local profiles equal the global ones.

Under fixed global T5 assignment, lower-worry prevalence is 56.4% in Northern/Western Europe versus 17.1% in Central/Western Africa and 13.8% in Southern Africa. Broad known-person harm is 8.2% versus 23.4% in the first two regions. These are equal-country summaries of complete-case respondents, not world-population prevalence estimates. The regional original-category tables show how meanings and frequencies vary.

Country similarity is only partly geographical. Mean Hellinger distance is 0.174 to same-region peers versus 0.233 to other-region peers, averaging countries with regional peers. The nearest country is in the same region for 23.9%, compared with an 8.1% random-peer reference. Physical map-label distance has rank correlation 0.152 with profile-mixture distance. The exploratory best-silhouette country cut has two groups (97 and 45 countries), with region-agreement ARI 0.052. It is not adopted as a replacement regional classification.

Distances depend on what is summarized. The USA's nearest country by T5 profile mixture is Bosnia Herzegovina; Iran is third. Finland's nearest is Tajikistan. By original-response distance with T5 allocation, Canada is first for the USA and Iceland first for Finland. These differences show information lost when response distributions are compressed into five profile shares. Familiar neighbours do not establish validity, and unexpected neighbours are not grounds to tune the distance. The two summaries answer different questions and neither measures societal equivalence.

Nearest ranks are uncertain even with the profiles fixed: the reference nearest neighbour recurs in only 29.5% of conditional respondent bootstraps for both the USA and Finland; the median across countries is 40.5%. These are IID respondent sensitivity checks retaining WGT, not survey-design confidence or profile-selection uncertainty. Lists should be read as proximity descriptions, not certain top-ranked relationships.

Across 141 income-classified countries, income-gap Spearman correlation is 0.2469 for profile-mixture Hellinger distance and 0.2977 for original-response distance. Within-region whole-country income-label permutations give upper-tail fractions 0.006 and 0.003. These conditional exchangeability references do not establish causation or control for all country differences; pairs are not treated as independent observations.

Two overall burden totals cannot exactly recover membership: even the within-sample optimal lookup by original worry sum and affected-domain count reaches only 60.1% accuracy in development and 58.2% in held-out data. This is a descriptive information-loss bound, not cross-validated predictive performance or proof of added value for an external outcome. Objective 3 still requires that separate test.
'''
notebook=ROOT/'weekly_notebooks/week05_validate_frozen_profiles.ipynb'
book=nbformat.read(notebook,as_version=4)
index=next(i for i,c in enumerate(book.cells) if c.cell_type=='markdown' and c.source.startswith('## 6. Complete the geographical'))
if '### Interpretation of the completed' in book.cells[index].source:
 book.cells[index].source=book.cells[index].source.split('### Interpretation of the completed')[0]
book.cells[index].source+='\n\n'+interpretation
cell=book.cells[index+1]
line="display(pd.read_csv(T5_COMPLETION / 'supported_local_semantic_correspondence.csv').round(4))"
if line not in cell.source:cell.source+='\n'+line
nbformat.write(book,notebook)
subprocess.run([sys.executable,str(ROOT/'.week06_build/replay_notebooks.py'),'weekly_notebooks/week05_validate_frozen_profiles.ipynb'],check=True)
public_book=nbformat.read(notebook,as_version=4)
for cell in public_book.cells:
 if cell.cell_type=='code':cell.outputs=[];cell.execution_count=None
nbformat.write(public_book,PUBLIC/'weekly_notebooks'/notebook.name)

for filename in ['supported_local_semantic_correspondence.csv']:
 shutil.copy2(OUT/filename,PUBLIC/OUT.relative_to(ROOT)/filename)
for filename in ['T5_RESULTS.md','RESULTS.md','METHODS.md']:
 path=PUBLIC/'research'/filename;text=path.read_text()
 text=text.replace('No new local-region clustering, independent held-out clustering or all-data refit was performed.',
  'At the transfer stage, no new local-region clustering, independent held-out clustering or all-data refit was performed. The 17 October extension below adds development-only regional fits; the global model remains fixed.')
 text=text.replace('The existing country-distance pages retain historical B/E metrics, explicitly\nlabelled, and the Week 6 B/E prediction draft is not a T5 prediction result.',
  'The country-distance pages now include T5 alongside the historical E8 comparison. Week 6 now predicts T5 membership; older B/E supervised results remain historical.')
 heading='\n\n'+interpretation
 if '### Interpretation of the completed T5 geographical analyses' in text:text=text.split('### Interpretation of the completed T5 geographical analyses')[0].rstrip()
 if filename=='T5_RESULTS.md':
  addition=interpretation
 elif filename=='RESULTS.md':
  addition='''### Interpretation of the completed T5 geographical analyses

No regional k=5 solution qualifies for both full stability tests. Six settings in four regions pass: Eastern Africa k=3; Central/Western Africa k=3/4; Latin America/Caribbean k=3/4; Northern/Western Europe k=2. Small-region diagnostics remain limited. The European binary split is almost defined by known-person mental-health harm. These results limit a universal interpretation of the global five-profile description, rather than refitting or invalidating that fixed model.

T5 country mixtures partly follow geography: within-region mean Hellinger distance 0.174 versus 0.233 across regions; nearest-country same-region rate 23.9% versus 8.1% random reference. Country groups are exploratory, not new regions. Unexpected profile-mixture neighbours show compression: USA–Bosnia Herzegovina and Finland–Tajikistan are nearest, while original-response distance makes Canada and Iceland nearest respectively. Exact-neighbour bootstrap repeat rates for the USA and Finland are only 29.5%.

Income-gap correlations are 0.247 for mixtures and 0.298 for original responses. The analyses preserve fixed denominators and disclose uncertainty, complete-case limits and pair dependence. See [full interpretation](T5_RESULTS.md) and the completed Week 5 notebook.
'''
 else:
  addition='''### Interpretation of the completed T5 geographical analyses

T5 regional references cover k=2–10. The stability shortlist is recorded before testing: matched k=5, coarse k=2/3 and an inertia-elbow alternative selected without global-label agreement. Use 50 within-country 80% respondent samples and, for regions with at least five development countries, 50 samples of floor(0.8N) countries. Two-to-four-country regions use leave-one-country-out diagnostics; one-country regions have no country test. Median and lower-decile pairwise ARI must both reach 0.80. Pairwise ARIs and repeated country subsets are dependent. Report structural global thresholds as benchmarks, not universal regional constraints.

Regional profiles are compared with T5 through weighted overlaps and original-category differences, without treating local IDs as shared labels. Country comparisons use the same frozen global labels. The 200 within-country IID respondent bootstraps retain WGT and fixed labels; 999 income randomizations permute whole countries, unrestricted or within dataset regions. These are conditional sensitivity/randomization references, not full survey or model-selection uncertainty. Two-dimensional colours preserve 75.5% of Hellinger-coordinate variation and have 22.3% relative distance error; exact distances, not projected colours, determine ranks. See [results and limitations](T5_RESULTS.md).
'''
 path.write_text(text+'\n\n'+addition)
readme=PUBLIC/'README.md';text=readme.read_text()
text=re.sub(r'\n\nT5 geographical (?:completion:|analyses are complete\.).*?(?=\n\n|\Z)','',text,flags=re.S)
text=text.replace('**Current conclusion (16 October 2026):**','**Current conclusion (17 October 2026):**')
text=text.replace('in `docs/index.html`; country-distance pages intentionally retain clearly labelled\nhistorical B/E comparisons. Current audit records are `publication_audit.json`\nand `publication_profile_test.json`.','in `docs/index.html`; country and income pages now include T5 alongside the historical E8 comparison. Current audit records include the T5 completion verification and browser checks.')
text+='\n\nT5 geographical analyses are complete. Independent regional k=5 fits do not pass both full stability tests; six coarser cases do. This limits universality claims without changing the frozen global model. See [regional and country evidence](research/T5_RESULTS.md).\n'
readme.write_text(text)
model_path=PUBLIC/'frozen_models/T5_models.json';model=json.loads(model_path.read_text())
old_centres=np.asarray(model['models']['T5']['centres']).copy()
search_status=model['models']['T5']['spec']['status']
if search_status=='provisional, not frozen':model['models']['T5']['spec']['source_search_status']=search_status
model['models']['T5']['spec']['status']='frozen; primary course specification'
model_path.write_text(json.dumps(model,indent=2)+'\n')
assert np.array_equal(old_centres,np.load(FROZEN/'frozen_model/centres.npy'))

# Keep the downloadable fragment sources consistent with the tested offline pages.
for filename,root_id,target in [('countries.html','wrp-mixture-similarity','country-similarity-fragment.html'),
                               ('country-income.html','wrp-country-income','country-income-fragment.html')]:
 text=(PUBLIC/'docs'/filename).read_text();inner=html.unescape(re.search(r'data-srcdoc="(.*?)"',text,re.S)[1])
 start=inner.index('<div id="'+root_id+'">');controller=inner.index("const root=document.getElementById('",start)
 end=inner.index('</script>',controller)+len('</script>')
 (PUBLIC/'docs'/target).write_text(inner[start:end]+'\n')

# Test scientific exports before publishing the verification report.
for p in (PUBLIC/'course_artifacts/week05_T5_completion').rglob('*.csv'):
 assert not {'wpid_random','respondent_id','wgt'} & set(pd.read_csv(p,nrows=0).columns.str.lower()),p
assert not list((PUBLIC/'course_artifacts/week05_T5_completion').rglob('*.joblib'))
assert not list((PUBLIC/'course_artifacts/week05_T5_completion').rglob('*.parquet'))
for filename in ['week05_validate_frozen_profiles.ipynb','week06_predicting_frozen_risk_profile_membership.ipynb']:
 n=nbformat.read(PUBLIC/'weekly_notebooks'/filename,as_version=4)
 assert all(not c.outputs for c in n.cells if c.cell_type=='code')
report={'status':'passed','regional_reference_fits':135,'regional_stability_fits':5228,
 'regional_fit_failures':0,'supported_full_test_cases':6,'supported_regional_k5_cases':0,
 'limited_diagnostic_cases':3,'country_profiles_recomputed_from_ID_registry':True,
 'distance_symmetry_zero_diagonal_and_scope_invariance':True,'fixed_scale_preserved':True,
 'global_assignments_unchanged':True,'sealed_global_files_unchanged':True,
 'public_notebook_outputs_cleared':True,'respondent_files_published':False,
 'reporting_incident':'Initial reporting worker referenced an undefined pointer after writing outputs; corrected reporting-only replay. No scientific fits repeated.',
 'pushed':False}
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
shutil.copy2(OUT/'verification.json',PUBLIC/OUT.relative_to(ROOT)/'verification.json')
shutil.copy2(Path(__file__),PUBLIC/'.week05_build'/Path(__file__).name)
print(json.dumps(report,indent=2))
