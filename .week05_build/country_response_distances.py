"""Post-validation country-response distances; never fit or modify respondent models."""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import platform
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

DOMAINS = ['food', 'water', 'crime', 'severe_weather', 'traffic', 'mental_health']
WORRY_RAW = dict(zip(DOMAINS, ['WP20720','WP20721','WP20722','WP20723','WP22213','WP20726']))
HARM_RAW = dict(zip(DOMAINS + ['work'], ['WP22442','WP22443','WP22444','WP22445','WP22446','WP22447','WP22448']))
WORRY = ['worry_' + d for d in DOMAINS]
SELF = ['harm_' + d + '_personal' for d in HARM_RAW]
KNOWN = ['harm_' + d + '_known_person' for d in HARM_RAW]
FEATURES = WORRY + SELF + KNOWN
ALPHAS = {'B': .5, 'E': .75}
SCOPES = ['development', 'all_countries_post_validation']
DESIGN = {'version': 1, 'features': FEATURES, 'category_counts': [3]*6+[2]*14,
          'eligibility': 'same 20-feature complete-response cohort as frozen B4/E8',
          'weights': 'original WGT normalized within each eligible country',
          'distance': 'mean feature total variation; six worry, seven personal harm, seven known-person harm',
          'alphas': ALPHAS, 'harm_allocation': 'half to personal and half to known-person harm',
          'percentile': '100*upper empirical CDF over distinct unordered pairs in displayed scope; exact ties included',
          'rank_ties': 'distance then ISO3; ranks descriptive, not statistical certainty',
          'display': 'seven equal-width bands from reference zero to its maximum; normalize only after combining raw components',
          'limits': 'marginal summaries, not joint distributions; no new resampling uncertainty or causal inference',
          'heldout_use': 'post-validation descriptive extension; not untouched validation or model selection',
          'respondent_models_refitted': False}

def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()

def response_features(frame):
    result = frame.copy()
    for domain, source in WORRY_RAW.items():
        assert result[source].dropna().isin([1,2,3,98,99]).all(), source
        result['worry_'+domain] = result[source].map({1:2.,2:1.,3:0.})
    for domain, source in HARM_RAW.items():
        raw = result[source]
        assert raw.dropna().isin([1,2,3,4,98,99]).all(), source
        valid = raw.isin([1,2,3,4])
        result['harm_'+domain+'_personal'] = np.where(valid,raw.isin([1,3]).astype(float),np.nan)
        result['harm_'+domain+'_known_person'] = np.where(valid,raw.isin([2,3]).astype(float),np.nan)
    return result

def response_matrices(probabilities):
    blocks, position = [], 0
    for count in DESIGN['category_counts']:
        q = probabilities[:,position:position+count]
        assert np.allclose(q.sum(axis=1),1) and np.isfinite(q).all() and (q >= 0).all()
        blocks.append(np.abs(q[:,None,:]-q[None,:,:]).sum(axis=2)/2)
        position += count
    assert position == 46
    matrices = {'worry': np.mean(blocks[:6],axis=0), 'self': np.mean(blocks[6:13],axis=0),
                'known': np.mean(blocks[13:],axis=0)}
    for model, alpha in ALPHAS.items():
        matrices[model] = alpha*matrices['worry']+(1-alpha)*(matrices['self']+matrices['known'])/2
    for matrix in matrices.values():
        assert np.allclose(matrix,matrix.T) and np.allclose(np.diag(matrix),0)
        assert np.isfinite(matrix).all() and matrix.min() >= 0 and matrix.max() <= 1+1e-12
    return matrices

def pair_percentiles(matrix):
    pool = np.sort(matrix[np.triu_indices(len(matrix),1)])
    result = 100*np.searchsorted(pool,matrix,side='right')/len(pool)
    np.fill_diagonal(result,np.nan)
    return result

def income_tables(matrix, metadata):
    classified = metadata.CountryIncomeLevel.between(1,4)
    md = metadata.loc[classified]
    d = matrix[np.ix_(np.flatnonzero(classified),np.flatnonzero(classified))]
    income = md.CountryIncomeLevel.to_numpy()
    region = md.GlobalRegion.to_numpy()
    ia,ib = np.triu_indices(len(md),1)
    values,gap = d[ia,ib],np.abs(income[ia]-income[ib])
    same_region = region[ia] == region[ib]
    cells = []
    for a in range(1,5):
        row = []
        left = np.flatnonzero(income == a)
        for b in range(1,5):
            right = np.flatnonzero(income == b)
            sub = d[np.ix_(left,right)]
            values_ab = sub[np.triu_indices(len(left),1)] if a == b else sub.ravel()
            row.append({'mean_distance':float(values_ab.mean()),'distinct_pairs':len(values_ab)})
        cells.append(row)
    summary = {'classified_countries':len(md),'distinct_pairs':len(values),
               'ordinal_gap_spearman':float(spearmanr(values,gap).statistic),
               'within_region_spearman':float(spearmanr(values[same_region],gap[same_region]).statistic),
               'interpretation':'descriptive association; no pair-independent significance test or new permutation reference'}
    return summary,cells

def run_response_distances(root):
    root = Path(root).resolve()
    source = root/'course_artifacts/week05_country_similarity_and_profile_synthesis_v1/d694096841b06e54'
    inputs = [root/'course_artifacts/week03_development_data.parquet',
              root/'course_artifacts/week03_heldout_country_data.parquet',source/'country_profile_vectors.csv',
              root/'course_artifacts/week05_frozen_objective1_v1/123d248adda6115f/freeze_seal.json']
    provenance = {'design':DESIGN,'source_hashes':{str(p.relative_to(root)):file_hash(p) for p in inputs},
                  'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__}
    fingerprint = hashlib.sha256(json.dumps(provenance,sort_keys=True).encode()).hexdigest()
    output = root/'course_artifacts/week05_country_response_distances_v1'/fingerprint[:16]
    output.mkdir(parents=True,exist_ok=True)
    vectors = pd.read_csv(source/'country_profile_vectors.csv')
    metadata = vectors.drop_duplicates('COUNTRY_ISO3').set_index('COUNTRY_ISO3').sort_index()
    columns = ['WPID_RANDOM','COUNTRY_ISO3','country_split','WGT']+list(WORRY_RAW.values())+list(HARM_RAW.values())
    raw = response_features(pd.concat([pd.read_parquet(p,columns=columns) for p in inputs[:2]],ignore_index=True))
    frame = raw.loc[raw[FEATURES].notna().all(axis=1)].copy()
    assert len(frame) == 137460 and frame.WPID_RANDOM.is_unique and frame.COUNTRY_ISO3.nunique() == 142
    assert frame.WGT.gt(0).all() and np.isfinite(frame.WGT).all()
    assert frame.groupby('COUNTRY_ISO3').size().equals(metadata.complete_respondents.rename(None).astype('int64'))
    handoff = root/'course_artifacts/week05_objective1_handoff_v1/123d248adda6115f/profile_assigned_respondents.parquet'
    if handoff.exists():
        ids = pd.read_parquet(handoff,columns=['WPID_RANDOM'])
        assert set(ids.WPID_RANDOM) == set(frame.WPID_RANDOM)
        provenance['eligibility_id_registry_verified'] = True
    frame['mass'] = frame.WGT/frame.groupby('COUNTRY_ISO3').WGT.transform('sum')
    assert np.allclose(frame.groupby('COUNTRY_ISO3').mass.sum(),1)
    arrays, distribution_rows = [], []
    for j,feature in enumerate(FEATURES):
        categories = range(DESIGN['category_counts'][j])
        q = frame.groupby(['COUNTRY_ISO3',feature]).mass.sum().unstack(fill_value=0).reindex(index=metadata.index,columns=categories,fill_value=0)
        arrays.append(q.to_numpy())
        for iso in metadata.index:
            for category in categories:
                distribution_rows.append({'COUNTRY_ISO3':iso,'feature':feature,'category':category,
                                          'proportion':float(q.loc[iso,category])})
    probabilities = np.concatenate(arrays,axis=1)
    matrices = response_matrices(probabilities)
    pd.DataFrame(distribution_rows).to_csv(output/'country_response_probabilities.csv',index=False)
    metadata.reset_index().to_csv(output/'country_metadata.csv',index=False)
    payload = {'version':1,'fingerprint':fingerprint,'country_order':metadata.index.tolist(),
               'category_counts':DESIGN['category_counts'],'shape':list(probabilities.shape),'byte_order':'little',
               'probabilities_f64_base64':base64.b64encode(probabilities.astype('<f8').tobytes()).decode(),
               'alphas':ALPHAS,'income':{'summaries':{'B':{},'E':{}},'matrices':{'B':{},'E':{}}}}
    pairs,neighbours,summary,examples,income_summary = [],[],[],[],[]
    for scope in SCOPES:
        selected = np.flatnonzero(metadata.country_split.eq('train')) if scope == 'development' else np.arange(len(metadata))
        md = metadata.iloc[selected]
        codes = md.index.tolist()
        selected_matrices = {key:value[np.ix_(selected,selected)] for key,value in matrices.items()}
        percentiles = {key:pair_percentiles(value) for key,value in selected_matrices.items()}
        ia,ib = np.triu_indices(len(md),1)
        for i,j in zip(ia,ib):
            row = {'scope':scope,'iso3_a':codes[i],'iso3_b':codes[j]}
            for key in selected_matrices:
                row[key] = float(selected_matrices[key][i,j]);row[key+'_percentile'] = float(percentiles[key][i,j])
            pairs.append(row)
        for metric,d in selected_matrices.items():
            pd.DataFrame(d,index=codes,columns=codes).to_csv(output/f'{metric}_{scope}_matrix.csv')
            pd.DataFrame(percentiles[metric],index=codes,columns=codes).to_csv(output/f'{metric}_{scope}_percentiles.csv')
            pool = d[ia,ib]
            summary.append({'metric':metric,'scope':scope,'countries':len(md),'pairs':len(pool),
                            'min':float(pool.min()),'median':float(np.median(pool)),
                            'p90':float(np.quantile(pool,.9)),'max':float(pool.max())})
            for i,iso in enumerate(codes):
                order = sorted((j for j in range(len(md)) if j != i),key=lambda j:(d[i,j],codes[j]))
                for rank,j in enumerate(order[:20],1):
                    row = {'scope':scope,'metric':metric,'COUNTRY_ISO3':iso,'Country':md.iloc[i].Country,
                           'rank':rank,'peer_iso3':codes[j],'peer_country':md.iloc[j].Country,
                           'distance':float(d[i,j]),'distance_percentile':float(percentiles[metric][i,j])}
                    for key in selected_matrices:
                        row[key] = float(selected_matrices[key][i,j]);row[key+'_percentile'] = float(percentiles[key][i,j])
                    neighbours.append(row)
                if scope == 'all_countries_post_validation' and iso in ['USA','FIN'] and metric in ['B','E']:
                    targets = ['CAN','IRN','KHM','GBR'] if iso == 'USA' else ['ISL','SWE','NOR','EST']
                    for peer in targets:
                        j = codes.index(peer)
                        row = {'reference':iso,'peer':peer,'metric':metric,'rank':order.index(j)+1,
                               'distance':float(d[i,j]),'percentile':float(percentiles[metric][i,j]),
                               'maximum_from_reference':float(d[i].max()),
                               'relative_to_max':float(d[i,j]/d[i].max())}
                        row.update({key:float(selected_matrices[key][i,j]) for key in ['worry','self','known']})
                        examples.append(row)
        for model in ['B','E']:
            stats,cells = income_tables(selected_matrices[model],md)
            payload['income']['summaries'][model][scope] = stats
            payload['income']['matrices'][model][scope] = cells
            income_summary.append({'model':model,'scope':scope,**stats})
    tables = {'country_pair_response_distances':pairs,'nearest_country_responses':neighbours,
              'response_distance_summary':summary,'illustrative_country_comparisons':examples,
              'response_income_summary':income_summary}
    for filename,rows in tables.items():
        pd.DataFrame(rows).to_csv(output/(filename+'.csv'),index=False)
    (output/'response_map_payload.json').write_text(json.dumps(payload,separators=(',',':'),allow_nan=False))
    provenance.update({'fingerprint':fingerprint,'eligible_respondents':len(frame),'country_count':len(metadata),
                       'implementation_sha256':file_hash(root/'.week05_build/country_response_distances.py'),
                       'files':{p.name:file_hash(p) for p in output.iterdir() if p.name != 'analysis_manifest.json'}})
    (output/'analysis_manifest.json').write_text(json.dumps(provenance,indent=2,sort_keys=True))
    assert file_hash(inputs[3]) == provenance['source_hashes'][str(inputs[3].relative_to(root))]
    return output

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    output = run_response_distances(args.root)
    print(json.dumps({'output_directory':str(output.relative_to(args.root.resolve())),
                      'payload_bytes':(output/'response_map_payload.json').stat().st_size,
                      'respondent_models_refitted':False},indent=2))
