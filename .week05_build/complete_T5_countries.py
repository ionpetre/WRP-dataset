"""T5 country, burden and geographic analyses; frozen respondent profiles never refitted."""
from pathlib import Path
import ast
import fcntl
import json
import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr
from scipy.spatial.distance import pdist, squareform
import T5_country_tools as e
from country_response_distances import response_features, FEATURES, income_tables

ROOT = Path(__file__).resolve().parents[1]
lock = (ROOT/'.week05_build/T5_countries.lock').open('w')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
pointer = json.loads((ROOT/'course_artifacts/week05_T5_completion/current_run.json').read_text())
out = ROOT/pointer['output']/'countries'
out.mkdir(exist_ok=True)
frozen = ROOT/'course_artifacts/week05_t5_secondary_transfer/832b01713bc6b240'
registry = pd.read_parquet(frozen/'all_respondents_T5_eligibility_and_frozen_profiles.parquet')
assigned = registry.loc[registry.complete_case].copy()
assert len(assigned)==137460 and assigned.WPID_RANDOM.is_unique
raw = response_features(pd.concat([pd.read_parquet(ROOT/'course_artifacts'/name) for name in
    ['week03_development_data.parquet','week03_heldout_country_data.parquet']],ignore_index=True))
raw = raw.loc[raw.WPID_RANDOM.isin(assigned.WPID_RANDOM)].copy()
raw = raw.merge(assigned[['WPID_RANDOM','T5_margin']],on='WPID_RANDOM',validate='one_to_one')
metadata = pd.read_csv(ROOT/'course_artifacts/week05_country_response_distances_v1/e1ecf01551bcf2da/country_metadata.csv').sort_values('COUNTRY_ISO3').reset_index(drop=True)
assert len(metadata)==142
spec = json.loads((frozen/'frozen_model/specification.json').read_text())
definitions = pd.DataFrame([{'candidate':'T5','cluster':int(c),'profile_name':name} for c,name in spec['profile_names'].items()])
e.burden_and_heterogeneity(raw,assigned,definitions,out)
e.compute_country_extensions(ROOT,out,assigned,registry,metadata,e.map_features(ROOT))
print('Country mixtures, 200 bootstrap repetitions, geography, country groups and burden checks saved',flush=True)

# Original-category distances use the same 46 marginal probabilities as B/E;
# only the stated overall allocation changes. Nominal category total variation
# intentionally does not depend on t or on numeric spacing of worry categories.
source = ROOT/'course_artifacts/week05_country_response_distances_v1/e1ecf01551bcf2da'
components = {key:pd.read_csv(source/f'{key}_all_countries_post_validation_matrix.csv',index_col=0)
              for key in ['worry','self','known']}
codes = metadata.COUNTRY_ISO3.tolist()
components = {key:frame.loc[codes,codes].to_numpy() for key,frame in components.items()}
alpha = spec['spec']['alpha']
direct = alpha*components['worry']+(1-alpha)*(components['self']+components['known'])/2
mixture = pd.read_csv(out/'T5_all_countries_post_validation_hellinger_matrix.csv',index_col=0).loc[codes,codes].to_numpy()
matrices = {**components,'T5_responses':direct,'T5_profiles':mixture}
triangle = np.triu_indices(142,1)
# Preserve the existing cross-model display denominator; T5 does not recalibrate
# the B/E scale or silently change historical colours.
common_median = .1550977480973838
profile_reference = pd.read_csv(ROOT/'course_artifacts/week05_country_similarity_and_profile_synthesis_v1/d694096841b06e54/B_all_countries_post_validation_hellinger_matrix.csv',index_col=0)
profile_reference_E = pd.read_csv(ROOT/'course_artifacts/week05_country_similarity_and_profile_synthesis_v1/d694096841b06e54/E_all_countries_post_validation_hellinger_matrix.csv',index_col=0)
profile_median = float(np.median(np.r_[profile_reference.to_numpy()[triangle],profile_reference_E.to_numpy()[triangle]]))
scales = {'T5_responses':common_median,'T5_profiles':profile_median,
          **{k:float(np.median(v[triangle])) for k,v in components.items()}}
neighbors, income, cells = [], [], {}
for scope in ['development','all_countries_post_validation']:
    selected = np.flatnonzero(metadata.country_split.eq('train')) if scope=='development' else np.arange(142)
    md = metadata.iloc[selected].reset_index(drop=True)
    for key,m in matrices.items():
        d = m[np.ix_(selected,selected)]
        assert np.isfinite(d).all() and np.allclose(d,d.T) and np.allclose(np.diag(d),0)
        pd.DataFrame(d,index=md.COUNTRY_ISO3,columns=md.COUNTRY_ISO3).to_csv(out/f'{key}_{scope}_raw_matrix.csv')
        pd.DataFrame(d/scales[key],index=md.COUNTRY_ISO3,columns=md.COUNTRY_ISO3).to_csv(out/f'{key}_{scope}_median_relative_matrix.csv')
        if key.startswith('T5_'):
            stats, grid = income_tables(d,md)
            income.append({'scope':scope,'metric':key,**stats})
            cells[key+':'+scope] = grid
        for i,code in enumerate(md.COUNTRY_ISO3):
            order = sorted((j for j in range(len(md)) if i!=j),key=lambda j:(d[i,j],md.COUNTRY_ISO3.iloc[j]))
            for rank,j in enumerate(order,1):
                neighbors.append({'scope':scope,'metric':key,'COUNTRY_ISO3':code,'rank':rank,
                    'peer_iso3':md.COUNTRY_ISO3.iloc[j],'raw_distance':float(d[i,j]),
                    'median_relative_distance':float(d[i,j]/scales[key])})
pd.DataFrame(neighbors).to_csv(out/'all_country_neighbour_rankings.csv',index=False)
pd.DataFrame(income).to_csv(out/'income_distance_summary.csv',index=False)

# Same whole-country income-label randomization as the historical analysis.
REPETITIONS, SEED = 999, 20261013
income_source = (ROOT/'.week05_build/analyze_country_income_similarity.py').read_text()
for node in ast.parse(income_source).body:
    if isinstance(node,ast.FunctionDef) and node.name=='randomization':
        exec(ast.get_source_segment(income_source,node))
tests = []
for scope in ['development','all_countries_post_validation']:
    take = metadata.CountryIncomeLevel.between(1,4)
    if scope=='development': take &= metadata.country_split.eq('train')
    ids = np.flatnonzero(take)
    md = metadata.loc[take]
    a,b = np.triu_indices(len(md),1)
    inc, region = md.CountryIncomeLevel.to_numpy(),md.GlobalRegion.to_numpy()
    for key in ['T5_responses','T5_profiles']:
        values = matrices[key][np.ix_(ids,ids)][a,b]
        observed = float(spearmanr(values,np.abs(inc[a]-inc[b])).statistic)
        for within in [False,True]:
            tests.append({'scope':scope,'metric':key,'rho':observed,'within_region_permutation':within,
                          **randomization(values,inc,region,a,b,observed,within)})
pd.DataFrame(tests).to_csv(out/'income_country_label_permutations.csv',index=False)
embedding = np.sqrt(pd.read_csv(out/'country_profile_vectors.csv').pivot(index='COUNTRY_ISO3',columns='cluster',values='profile_share').loc[codes].to_numpy())/np.sqrt(2)
u,s,vt = np.linalg.svd(embedding-embedding.mean(axis=0),full_matrices=False)
coords = u[:,:2]*s[:2]
for j in range(2):
    if vt[j,np.argmax(abs(vt[j]))]<0: coords[:,j]*=-1
pd.DataFrame({'COUNTRY_ISO3':codes,'coordinate_1':coords[:,0],'coordinate_2':coords[:,1]}).to_csv(out/'country_colour_coordinates.csv',index=False)
quality = {'variance_preserved':float((s[:2]**2).sum()/(s**2).sum()),
    'distance_rank_spearman':float(spearmanr(pdist(embedding),pdist(coords)).statistic),
    'relative_distance_error':float(np.sqrt(((pdist(embedding)-pdist(coords))**2).sum()/(pdist(embedding)**2).sum()))}
manifest = {'status':'complete','countries':142,'assigned_respondents':137460,'alpha':alpha,
    'scales':scales,'income_cells':cells,'colour_projection_quality':quality,
    'distance_meaning':'profile mixtures: Hellinger; original responses: feature-marginal total variation',
    'numeric_t_in_total_variation':False,'country_bootstrap_repetitions':200,
    'scale_policy':'Existing fixed B/E reference medians preserved and extended to T5; never country-specific denominators.',
    'global_profile_refits':0,'scope':'post-validation description, not untouched validation',
    'source_registry_sha256':e.extension_sha(frozen/'all_respondents_T5_eligibility_and_frozen_profiles.parquet')}
e.extension_json(manifest,out/'country_completion.json')
print(pd.DataFrame(income).to_string(index=False),flush=True)
print('Country analyses complete:',out,flush=True)
