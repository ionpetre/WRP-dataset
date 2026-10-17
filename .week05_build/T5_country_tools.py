"""Post-validation descriptive extensions; never fit or modify respondent profiles."""
from pathlib import Path
import hashlib
import json
import platform
import traceback
import numpy as np
import pandas as pd
import scipy
import sklearn
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, cut_tree, leaves_list
from scipy.stats import spearmanr
from sklearn.metrics import silhouette_score, adjusted_rand_score

EXTENSION_DESIGN = {
    'version': 1, 'seed': 20261012, 'country_bootstrap_repetitions': 200,
    'country_basis': 'within-country survey-weighted frozen global T5 proportions; never local cluster IDs',
    'distance': 'Hellinger = Euclidean distance of square-root proportions / sqrt(2)',
    'scopes': ['development', 'all_countries_post_validation'],
    'geography': 'unchanged dataset GlobalRegion and approximate great-circle map-label-point distances',
    'country_clustering': 'average linkage; descriptive cuts 2..8; largest silhouette selects an illustrative cut only',
    'tie_break': 'smaller k on equal silhouette; country ISO order for nearest-neighbour ties',
    'uncertainty': '200 IID respondent bootstraps within each country; retain WGT and frozen labels; conditional sensitivity only',
    'inference': 'effect sizes only; no independent-pair p-values, no causal claims, no geographic regrouping',
    'burden_basis': 'original worry sum (0..12) and combined affected-domain count (0..7)',
    'holdout_use': 'post-validation descriptive extension, not untouched confirmation or model selection',
    'respondent_models_refitted': False,
}

def extension_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def extension_json(value, path):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False))
    temporary.replace(path)

def extension_csv(frame, path):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    frame.to_csv(temporary, index=False); temporary.replace(path)

def hellinger_matrix(proportions):
    p = np.asarray(proportions, float)
    assert np.isfinite(p).all() and (p >= 0).all() and np.allclose(p.sum(axis=1), 1)
    d = squareform(pdist(np.sqrt(p), metric='euclidean')) / np.sqrt(2)
    np.fill_diagonal(d, 0.)
    assert np.allclose(d, d.T) and d.max() <= 1+1e-12
    return d

def weighted_percentile(values, weights, q):
    order = np.argsort(values, kind='stable')
    return float(np.asarray(values)[order][np.searchsorted(np.cumsum(np.asarray(weights)[order])/sum(weights),q,side='left')])

def map_features(root):
    world = json.loads((root/'course_artifacts/cartography/ne_50m_admin_0_countries.geojson').read_text())
    mapping = {}
    for item in world['features']:
        code = item['properties']['ADM0_A3']
        if code == 'PSX': assert item['properties']['ISO_A3'] == 'PSE'
        mapping[{'KOS':'XKX','SDS':'SSD','PSX':'PSE'}.get(code,code)] = item
    return mapping

def great_circle_matrix(metadata, mapping):
    coords = np.array([[mapping[c]['properties']['LABEL_Y'],mapping[c]['properties']['LABEL_X']] for c in metadata.COUNTRY_ISO3],float)
    lat,lon = np.radians(coords).T
    angle = np.sin((lat[:,None]-lat[None,:])/2)**2 + np.cos(lat[:,None])*np.cos(lat[None,:])*np.sin((lon[:,None]-lon[None,:])/2)**2
    return 6371.0088*2*np.arcsin(np.sqrt(np.clip(angle,0,1)))

def descriptive_country_tree(d, metadata, candidate, scope):
    tree = linkage(squareform(d, checks=True), method='average', optimal_ordering=True)
    rows, labels = [], {}
    for k in range(2,9):
        lab = cut_tree(tree,n_clusters=k).ravel()
        labels[k] = lab
        counts = np.bincount(lab)
        rows.append({'candidate':candidate,'scope':scope,'k':k,
            'silhouette':float(silhouette_score(d,lab,metric='precomputed')),
            'smallest_country_group':int(counts.min()),'largest_country_group':int(counts.max()),
            'singleton_groups':int((counts==1).sum()),
            'ARI_with_dataset_regions':float(adjusted_rand_score(metadata.GlobalRegion,lab)),
            'status':'exploratory descriptive cut, not stability-qualified or an optimal country typology'})
    screen = pd.DataFrame(rows)
    selected = int(screen.sort_values(['silhouette','k'],ascending=[False,True]).iloc[0].k)
    return tree, screen, selected, labels[selected]

def burden_and_heterogeneity(raw, assigned, definitions, output):
    worry = ['worry_'+d for d in ['food','water','crime','severe_weather','traffic','mental_health']]
    domains = ['food','water','crime','severe_weather','traffic','mental_health','work']
    personal = ['harm_'+d+'_personal' for d in domains]
    known = ['harm_'+d+'_known_person' for d in domains]
    raw = raw.merge(assigned[['WPID_RANDOM','T5_cluster']],on='WPID_RANDOM',validate='one_to_one')
    raw['worry_sum'] = raw[worry].sum(axis=1).astype(int)
    raw['combined_harm_count'] = np.maximum(raw[personal].to_numpy(),raw[known].to_numpy()).sum(axis=1).astype(int)
    raw['personal_harm_count'] = raw[personal].sum(axis=1)
    raw['known_harm_count'] = raw[known].sum(axis=1)
    # An exact original response pattern, rather than a mean or a transformed coordinate.
    pattern = (raw[worry].to_numpy(dtype=np.int64) @ (3**np.arange(6,dtype=np.int64)))
    harm_pairs = raw[personal].to_numpy(dtype=np.int64)+2*raw[known].to_numpy(dtype=np.int64)
    raw['exact_pattern'] = pattern+3**6*(harm_pairs @ (4**np.arange(7,dtype=np.int64)))
    summaries, distributions, cells, ceilings = [], [], [], []
    names = definitions.set_index(['candidate','cluster']).profile_name.to_dict()
    for split,frame in raw.groupby('country_split'):
        weights = frame.WGT/frame.groupby('COUNTRY_ISO3').WGT.transform('sum')/frame.COUNTRY_ISO3.nunique()
        frame = frame.assign(weight=weights)
        for candidate,k in [('T5',5)]:
            label = candidate+'_cluster'
            for cluster,group in frame.groupby(label):
                w = group.weight.to_numpy(); total = w.sum()
                pattern_mass = group.groupby('exact_pattern').weight.sum()
                summaries.append({'split':split,'candidate':candidate,'cluster':int(cluster),
                    'profile_name':names[(candidate,int(cluster))], 'respondents':len(group),
                    'distinct_original_response_patterns':int(len(pattern_mass)),
                    'most_common_exact_pattern_share':float(pattern_mass.max()/total),
                    'median_margin':weighted_percentile(group[candidate+'_margin'],w,.5),
                    'p10_margin':weighted_percentile(group[candidate+'_margin'],w,.1),
                    'mean_worry_original_0_to_2':float(np.average(group.worry_sum/6,weights=w)),
                    'mean_combined_harmed_domains':float(np.average(group.combined_harm_count,weights=w)),
                    'mean_personal_harmed_domains':float(np.average(group.personal_harm_count,weights=w)),
                    'mean_known_person_harmed_domains':float(np.average(group.known_harm_count,weights=w))})
                for feature in ['worry_sum','combined_harm_count','personal_harm_count','known_harm_count']:
                    for value,g in group.groupby(feature):
                        distributions.append({'split':split,'candidate':candidate,'cluster':int(cluster),
                            'feature':feature,'value':float(value),'conditional_weighted_share':float(g.weight.sum()/total)})
            table = frame.groupby(['worry_sum','combined_harm_count',label]).weight.agg(['sum','size']).reset_index()
            table.columns = ['worry_sum','combined_harm_count','cluster','joint_weight','respondents']
            table['cell_weight'] = table.groupby(['worry_sum','combined_harm_count']).joint_weight.transform('sum')
            table['within_burden_cell_profile_share'] = table.joint_weight/table.cell_weight
            table['candidate'] = candidate; table['split'] = split; cells.append(table)
            maxima = table.groupby(['worry_sum','combined_harm_count']).joint_weight.max().sum()
            entropy = -float((table.joint_weight*np.log2(table.within_burden_cell_profile_share)).sum())
            ceilings.append({'split':split,'candidate':candidate,'burden_lookup_in_sample_accuracy_ceiling':float(maxima),
                'mass_not_reconstructible_from_two_totals':float(1-maxima),
                'conditional_profile_entropy_bits':entropy,
                'status':'descriptive exact-cell upper bound; not cross-validated performance or external-outcome benefit'})
    extension_csv(pd.DataFrame(summaries),output/'profile_burden_and_heterogeneity.csv')
    extension_csv(pd.DataFrame(distributions),output/'profile_burden_distributions.csv')
    extension_csv(pd.concat(cells,ignore_index=True),output/'same_burden_profile_composition.csv')
    extension_csv(pd.DataFrame(ceilings),output/'burden_only_information_loss.csv')
    return raw

def compute_country_extensions(root, output, assigned, audit, metadata, mapping):
    repetitions = EXTENSION_DESIGN['country_bootstrap_repetitions']
    rng = np.random.default_rng(EXTENSION_DESIGN['seed'])
    boot = {name:np.zeros((repetitions,len(metadata),k)) for name,k in [('T5',5)]}
    vectors = {}; sources = []
    for candidate,k in [('T5',5)]:
        weighted = assigned.assign(mass=assigned.WGT/assigned.groupby('COUNTRY_ISO3').WGT.transform('sum'))
        p = weighted.groupby(['COUNTRY_ISO3',candidate+'_cluster']).mass.sum().unstack(fill_value=0).reindex(index=metadata.COUNTRY_ISO3,columns=range(k),fill_value=0).to_numpy()
        vectors[candidate] = p
        for i,row in metadata.iterrows():
            group = assigned.loc[assigned.COUNTRY_ISO3.eq(row.COUNTRY_ISO3)]
            weights = group.WGT.to_numpy()
            for c in range(k):
                sources.append({'candidate':candidate,**row.to_dict(),'cluster':c,'profile_share':float(p[i,c]),
                    'profile_respondents':int(group[candidate+'_cluster'].eq(c).sum())})
    extension_csv(pd.DataFrame(sources),output/'country_profile_vectors.csv')
    # IID respondent bootstrap: common multiplicities for B and E, original WGT retained.
    for i,row in metadata.iterrows():
        group = assigned.loc[assigned.COUNTRY_ISO3.eq(row.COUNTRY_ISO3)]
        counts = rng.multinomial(len(group),np.full(len(group),1/len(group)),size=repetitions)
        weighted_counts = counts*group.WGT.to_numpy()[None,:]
        denominator = weighted_counts.sum(axis=1)
        for candidate,k in [('T5',5)]:
            for c in range(k):
                boot[candidate][:,i,c] = weighted_counts[:,group[candidate+'_cluster'].eq(c).to_numpy()].sum(axis=1)/denominator
        if (i+1)%30==0: print('Conditional country-proportion bootstrap:',i+1,'of',len(metadata),flush=True)
    pair_rows, neighbour_rows, summary_rows, cut_rows, group_rows, mean_rows, stability_rows, nn_uncertainty, agreement_rows = [],[],[],[],[],[],[],[],[]
    for scope in EXTENSION_DESIGN['scopes']:
        indices = np.flatnonzero(metadata.country_split.eq('train')) if scope=='development' else np.arange(len(metadata))
        meta = metadata.iloc[indices].reset_index(drop=True)
        geo = great_circle_matrix(meta,mapping)
        triangle = np.triu_indices(len(meta),1)
        scope_distances, scope_nearest = {},{}
        for candidate in ['T5']:
            p = vectors[candidate][indices]; d = hellinger_matrix(p)
            scope_distances[candidate] = d
            extension_csv(pd.DataFrame(d,index=meta.COUNTRY_ISO3,columns=meta.COUNTRY_ISO3).reset_index(),output/f'{candidate}_{scope}_hellinger_matrix.csv')
            same = meta.GlobalRegion.to_numpy()[:,None]==meta.GlobalRegion.to_numpy()[None,:]
            tmp = d.copy();np.fill_diagonal(tmp,np.inf)
            rank = np.argsort(tmp,axis=1,kind='stable'); nearest = rank[:,0];scope_nearest[candidate] = nearest
            within, between = [],[]
            for i,row in meta.iterrows():
                same_peers = np.flatnonzero(same[i] & (np.arange(len(meta))!=i))
                if len(same_peers):
                    within.append(float(d[i,same_peers].mean()));between.append(float(d[i,~same[i]].mean()))
                for position,j in enumerate(rank[i,:5],1):
                    other=meta.iloc[j]
                    neighbour_rows.append({'candidate':candidate,'scope':scope,'country':row.Country,'iso3':row.COUNTRY_ISO3,
                        'region_name':row.region_name,'rank':position,'neighbour':other.Country,'neighbour_iso3':other.COUNTRY_ISO3,
                        'neighbour_region':other.region_name,'same_region':bool(same[i,j]),'hellinger':float(d[i,j]),
                        'map_label_distance_km':float(geo[i,j]),'retention':row.retained_fraction,
                        'neighbour_retention':other.retained_fraction})
            for i,j in zip(*triangle):
                pair_rows.append({'candidate':candidate,'scope':scope,'iso3_a':meta.iloc[i].COUNTRY_ISO3,
                    'iso3_b':meta.iloc[j].COUNTRY_ISO3,'same_region':bool(same[i,j]),'hellinger':float(d[i,j]),
                    'map_label_distance_km':float(geo[i,j])})
            tree,screen,selected,labels = descriptive_country_tree(d,meta,candidate,scope)
            extension_csv(pd.DataFrame(tree,columns=['child_a','child_b','average_hellinger','countries']),output/f'{candidate}_{scope}_average_linkage.csv')
            cut_rows.append(screen)
            region_counts = meta.groupby('GlobalRegion').COUNTRY_ISO3.transform('size').to_numpy()
            summary_rows.append({'candidate':candidate,'scope':scope,'countries':len(meta),
                'same_region_nearest_fraction':float(same[np.arange(len(meta)),nearest].mean()),
                'same_region_random_peer_reference':float(((region_counts-1)/(len(meta)-1)).mean()),
                'same_region_top5_fraction':float(same[np.arange(len(meta))[:,None],rank[:,:5]].mean()),
                'country_balanced_within_region_distance':float(np.mean(within)),
                'country_balanced_between_region_distance_matched_countries':float(np.mean(between)),
                'countries_with_same_region_peers':len(within),
                'profile_vs_geographic_distance_spearman':float(spearmanr(d[triangle],geo[triangle]).statistic),
                'illustrative_country_k':selected,
                'illustrative_silhouette':float(screen.loc[screen.k.eq(selected),'silhouette'].iloc[0]),
                'country_group_vs_region_ARI':float(adjusted_rand_score(meta.GlobalRegion,labels))})
            for i,row in meta.iterrows():
                group_rows.append({'candidate':candidate,'scope':scope,**row.to_dict(),'country_group':int(labels[i])+1,'illustrative_k':selected})
            for group in sorted(set(labels)):
                for c in range(p.shape[1]):
                    mean_rows.append({'candidate':candidate,'scope':scope,'country_group':int(group)+1,
                        'countries':int((labels==group).sum()),'cluster':c,'mean_country_profile_share':float(p[labels==group,c].mean())})
            same_neighbour_count=np.zeros(len(meta),int);outside_count=np.zeros(len(meta),int)
            for repeat in range(repetitions):
                bd = hellinger_matrix(boot[candidate][repeat,indices])
                bt = linkage(squareform(bd),method='average')
                bl = cut_tree(bt,n_clusters=selected).ravel()
                stability_rows.append({'candidate':candidate,'scope':scope,'repeat':repeat,'fixed_illustrative_k':selected,
                    'country_partition_ARI':float(adjusted_rand_score(labels,bl))})
                np.fill_diagonal(bd,np.inf);bn=bd.argmin(axis=1)
                same_neighbour_count += bn==nearest
                outside_count += ~same[np.arange(len(meta)),bn]
            for i,row in meta.iterrows():
                nn_uncertainty.append({'candidate':candidate,'scope':scope,'iso3':row.COUNTRY_ISO3,'country':row.Country,
                    'reference_neighbour':meta.iloc[nearest[i]].Country,'reference_neighbour_same_region':bool(same[i,nearest[i]]),
                    'exact_nearest_repeated_fraction':float(same_neighbour_count[i]/repetitions),
                    'nearest_outside_region_fraction':float(outside_count[i]/repetitions),
                    'bootstrap_repetitions':repetitions,'status':'conditional IID respondent sensitivity; not survey-design confidence or model-fit uncertainty'})
    for table,name in [(pair_rows,'country_pair_distances'),(neighbour_rows,'nearest_country_neighbours'),
                       (summary_rows,'country_geography_summary'),(group_rows,'illustrative_country_groups'),
                       (mean_rows,'country_group_profile_meanings'),(stability_rows,'conditional_country_group_bootstrap'),
                       (nn_uncertainty,'conditional_nearest_neighbour_bootstrap')]:
        extension_csv(pd.DataFrame(table),output/(name+'.csv'))
    extension_csv(pd.concat(cut_rows,ignore_index=True),output/'country_tree_cut_diagnostics.csv')
