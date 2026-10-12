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
    'country_basis': 'within-country survey-weighted frozen global B or E proportions; never local cluster IDs',
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
    raw = raw.merge(assigned[['WPID_RANDOM','B_cluster','E_cluster']],on='WPID_RANDOM',validate='one_to_one')
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
        for candidate,k in [('B',4),('E',8)]:
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
    boot = {name:np.zeros((repetitions,len(metadata),k)) for name,k in [('B',4),('E',8)]}
    vectors = {}; sources = []
    for candidate,k in [('B',4),('E',8)]:
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
        for candidate,k in [('B',4),('E',8)]:
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
        for candidate in ['B','E']:
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
        agreement_rows.append({'scope':scope,'countries':len(meta),
            'B_E_distance_rank_spearman':float(spearmanr(scope_distances['B'][triangle],scope_distances['E'][triangle]).statistic),
            'B_E_exact_nearest_agreement':float((scope_nearest['B']==scope_nearest['E']).mean())})
    for table,name in [(pair_rows,'country_pair_distances'),(neighbour_rows,'nearest_country_neighbours'),
                       (summary_rows,'country_geography_summary'),(group_rows,'illustrative_country_groups'),
                       (mean_rows,'country_group_profile_meanings'),(stability_rows,'conditional_country_group_bootstrap'),
                       (nn_uncertainty,'conditional_nearest_neighbour_bootstrap'),(agreement_rows,'B_E_country_distance_agreement')]:
        extension_csv(pd.DataFrame(table),output/(name+'.csv'))
    extension_csv(pd.concat(cut_rows,ignore_index=True),output/'country_tree_cut_diagnostics.csv')

def extension_plots(root,output,definitions):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon,Patch
    from matplotlib.colors import Normalize
    from matplotlib.cm import ScalarMappable
    from scipy.cluster.hierarchy import dendrogram
    figures=output/'figures';figures.mkdir(exist_ok=True)
    mapping=map_features(root)
    summary=pd.read_csv(output/'country_geography_summary.csv')
    groups=pd.read_csv(output/'illustrative_country_groups.csv')
    pairs=pd.read_csv(output/'country_pair_distances.csv')
    burden=pd.read_csv(output/'profile_burden_and_heterogeneity.csv')
    dist=pd.read_csv(output/'profile_burden_distributions.csv')
    for candidate,k in [('B',4),('E',8)]:
        scope='all_countries_post_validation'
        meta=groups.loc[groups.candidate.eq(candidate)&groups.scope.eq(scope)].sort_values('COUNTRY_ISO3').reset_index(drop=True)
        matrix=pd.read_csv(output/f'{candidate}_{scope}_hellinger_matrix.csv').iloc[:,1:].to_numpy()
        tree=pd.read_csv(output/f'{candidate}_{scope}_average_linkage.csv').to_numpy()
        order=leaves_list(tree)
        fig,ax=plt.subplots(figsize=(12,11),layout='constrained')
        im=ax.imshow(matrix[np.ix_(order,order)],vmin=0,vmax=1,cmap='viridis')
        ticks=np.arange(0,len(meta),3)
        ax.set_xticks(ticks,meta.iloc[order[ticks]].COUNTRY_ISO3,rotation=90,fontsize=6)
        ax.set_yticks(ticks,meta.iloc[order[ticks]].COUNTRY_ISO3,fontsize=6)
        ax.set_title(candidate+': country similarity in frozen global-profile proportions\nAverage-linkage order; all 142 countries, post-validation description')
        fig.colorbar(im,ax=ax,label='Hellinger distance (0 = identical proportions; 1 = disjoint support)',shrink=.75)
        fig.savefig(figures/f'{candidate}_country_distance_heatmap.png',dpi=140);plt.close(fig)
        fig,ax=plt.subplots(figsize=(17,7),layout='constrained')
        dendrogram(tree,labels=meta.COUNTRY_ISO3.to_list(),leaf_rotation=90,leaf_font_size=6,ax=ax,color_threshold=0,above_threshold_color='#327c9e')
        ax.set_ylabel('Average Hellinger distance at merge')
        ax.set_title(candidate+': exploratory country hierarchy, not a replacement for the dataset regions')
        fig.savefig(figures/f'{candidate}_country_dendrogram.png',dpi=150);plt.close(fig)
        same=meta.set_index('COUNTRY_ISO3').country_group.to_dict()
        selected=int(meta.illustrative_k.iloc[0]); cmap=plt.get_cmap('tab10')
        fig,ax=plt.subplots(figsize=(15,7))
        for code,item in mapping.items():
            if code=='ATA':continue
            geom=item['geometry'];polys=geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]
            color=cmap((same[code]-1)%10) if code in same else '#eeeeee'
            held=code in set(meta.loc[meta.country_split.eq('heldout_country'),'COUNTRY_ISO3'])
            for poly in polys:ax.add_patch(Polygon(np.array(poly[0]),closed=True,facecolor=color,edgecolor='black' if held else '#888888',linewidth=.6 if held else .2))
            if code in same and max(np.ptp(np.array(p[0])[:,0])*np.ptp(np.array(p[0])[:,1]) for p in polys)<2:
                ax.scatter(item['properties']['LABEL_X'],item['properties']['LABEL_Y'],s=20,c=[color],edgecolor='black',linewidth=.3,zorder=5)
        ax.set(xlim=(-180,180),ylim=(-60,85),aspect='equal');ax.set_xticks([]);ax.set_yticks([])
        handles=[Patch(facecolor=cmap(g),label=f'Illustrative country group {g+1}') for g in range(selected)]
        handles += [Patch(facecolor='white',edgecolor='black',label='Black border: held-out'),Patch(facecolor='#eeeeee',label='No analysis data')]
        ax.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,-.14),ncol=3,fontsize=8)
        ax.set_title(f'{candidate}: illustrative {selected}-group cut of country-profile similarity\nNot new geographical areas or stability-qualified social types')
        fig.text(.02,.01,'All 142 complete-case country distributions; average-linkage/silhouette exploration after validation. Natural Earth de facto borders are not a political claim.',fontsize=8)
        fig.savefig(figures/f'{candidate}_illustrative_country_groups_map.png',dpi=150,bbox_inches='tight');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(14,6),layout='constrained')
    for ax,candidate in zip(axes,['B','E']):
        g=pairs.loc[pairs.candidate.eq(candidate)&pairs.scope.eq('all_countries_post_validation')]
        ax.hist([g.loc[g.same_region,'hellinger'],g.loc[~g.same_region,'hellinger']],bins=np.linspace(0,1,26),density=True,
                alpha=.6,label=['Same dataset region','Different dataset regions'],color=['#327c9e','#c47d35'])
        ax.set(title=candidate+': geography overlaps, but does not define similarity',xlabel='Hellinger distance',ylabel='Pairwise distance density');ax.legend(fontsize=9)
    fig.suptitle('Descriptive pair distributions only; pairs share countries and are not independent observations')
    fig.savefig(figures/'same_vs_different_region_distances.png',dpi=150);plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(14,10),layout='constrained')
    for row,(candidate,k) in enumerate([('B',4),('E',8)]):
        for col,feature in enumerate(['worry_sum','combined_harm_count']):
            g=dist.loc[dist.split.eq('train')&dist.candidate.eq(candidate)&dist.feature.eq(feature)]
            t=g.pivot(index='cluster',columns='value',values='conditional_weighted_share').reindex(index=range(k),fill_value=0).fillna(0)
            axes[row,col].imshow(t.to_numpy(),vmin=0,vmax=1,cmap='Blues',aspect='auto')
            axes[row,col].set_xticks(range(len(t.columns)),t.columns.astype(int));axes[row,col].set_yticks(range(k),[f'{candidate} C{c}' for c in range(k)])
            axes[row,col].set_xlabel('Original worry sum (0–12)' if feature=='worry_sum' else 'Affected domains, personal OR known person (0–7)')
    fig.colorbar(ScalarMappable(norm=Normalize(0,1),cmap='Blues'),ax=axes.ravel().tolist(),label='Within-profile weighted share',shrink=.8)
    fig.suptitle('Profiles contain distributions of burden, not a single burden value\nFrozen development labels; equal-country-weighted complete cases')
    fig.savefig(figures/'profile_burden_distributions.png',dpi=150);plt.close(fig)
    return sorted(figures.glob('*.png'))

def run_week05_extensions(root):
    from frozen_assignment import load_frozen_package, derive_frozen_features, WORRY_SOURCES, HARM_SOURCES
    root=Path(root)
    package=root/'course_artifacts/week05_frozen_objective1_v1/123d248adda6115f'
    handoff=root/'course_artifacts/week05_objective1_handoff_v1/123d248adda6115f'
    transfer=root/'course_artifacts/week05_heldout_transfer_v1/123d248adda6115f'
    inputs=[package/'freeze_seal.json',handoff/'profile_assigned_respondents.parquet',handoff/'all_respondents_eligibility_and_frozen_profiles.parquet',
        root/'course_artifacts/week03_development_data.parquet',root/'course_artifacts/week03_heldout_country_data.parquet',
        root/'course_artifacts/week03_country_split.csv',root/'23_wrp/WRP_2023_data_dictionary.csv',
        root/'course_artifacts/cartography/ne_50m_admin_0_countries.geojson',transfer/'fixed_global_all_country_prevalence.csv',
        root/'.week05_build/complete_week05_extensions.py']
    fingerprint={'design':EXTENSION_DESIGN,'inputs':{str(p.relative_to(root)):extension_sha(p) for p in inputs}}
    context=hashlib.sha256(json.dumps(fingerprint,sort_keys=True).encode()).hexdigest()
    output=root/'course_artifacts/week05_country_similarity_and_profile_synthesis_v1'/context[:16]
    output.mkdir(parents=True,exist_ok=True)
    load_frozen_package(package)
    record_path=output/'extension_complete.json'
    if record_path.exists():
        record=json.loads(record_path.read_text())
        assert record['context']==context
        for name,digest in record['files'].items():assert extension_sha(output/name)==digest,name
        print('Reusing fingerprint-checked completed descriptive extension:',output,flush=True)
        return output
    extension_json(fingerprint,output/'extension_design_and_inputs.json')
    try:
        assigned=pd.read_parquet(handoff/'profile_assigned_respondents.parquet')
        audit=pd.read_parquet(handoff/'all_respondents_eligibility_and_frozen_profiles.parquet')
        assert len(assigned)==137460 and assigned.WPID_RANDOM.is_unique
        country=pd.read_csv(root/'course_artifacts/week03_country_split.csv').sort_values('COUNTRY_ISO3').reset_index(drop=True)
        counts=audit.groupby('COUNTRY_ISO3').complete_case.agg(complete_respondents='sum',prepared_respondents='size').reset_index()
        counts['retained_fraction']=counts.complete_respondents/counts.prepared_respondents
        country=country.merge(counts,on='COUNTRY_ISO3',validate='one_to_one')
        dictionary=pd.read_csv(root/'23_wrp/WRP_2023_data_dictionary.csv')
        labels=dictionary.loc[dictionary.variable.eq('GlobalRegion'),'value_labels'].iloc[0]
        region_names={int(s.split(' = ',1)[0]):s.split(' = ',1)[1] for s in labels.split(' | ')}
        country['region_name']=country.GlobalRegion.map(region_names)
        mapping=map_features(root);assert not set(country.COUNTRY_ISO3)-set(mapping)
        columns=['WPID_RANDOM','COUNTRY_ISO3','WGT','country_split']+list(WORRY_SOURCES.values())+list(HARM_SOURCES.values())
        raw=pd.concat([pd.read_parquet(root/f'course_artifacts/{filename}',columns=columns) for filename in ['week03_development_data.parquet','week03_heldout_country_data.parquet']],ignore_index=True)
        raw=derive_frozen_features(raw.loc[raw.WPID_RANDOM.isin(assigned.WPID_RANDOM)].copy())
        assert len(raw)==len(assigned) and raw.WPID_RANDOM.is_unique
        raw=raw.merge(assigned[['WPID_RANDOM','B_margin','E_margin']],on='WPID_RANDOM',validate='one_to_one')
        definitions=pd.read_csv(package/'profile_definitions.csv')
        burden_and_heterogeneity(raw,assigned,definitions,output)
        compute_country_extensions(root,output,assigned,audit,country,mapping)
        # Reproduce the existing country shares exactly instead of trusting a new aggregation.
        old=pd.read_csv(transfer/'fixed_global_all_country_prevalence.csv')
        new=pd.read_csv(output/'country_profile_vectors.csv')
        joined=new.merge(old,left_on=['candidate','COUNTRY_ISO3','cluster'],right_on=['candidate','area_id','cluster'],validate='one_to_one')
        assert len(joined)==1704 and np.allclose(joined.profile_share,joined.equal_country_weighted_share,atol=1e-12)
        extension_plots(root,output,definitions)
        load_frozen_package(package)
        assert all(extension_sha(root/name)==digest for name,digest in fingerprint['inputs'].items())
        files=[p for p in output.rglob('*') if p.is_file() and p.name!='extension_complete.json']
        record={'status':'completed post-validation descriptive extensions','context':context,'design':EXTENSION_DESIGN,
            'software':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'sklearn':sklearn.__version__},
            'respondent_models_refitted':False,'heldout_validation_reinterpreted':False,
            'files':{str(p.relative_to(output)):extension_sha(p) for p in sorted(files)}}
        extension_json(record,record_path)
        print('Completed country similarity and burden/heterogeneity extension:',output,flush=True)
        return output
    except Exception:
        extension_json({'status':'failed; preserve diagnostics','context':context,'traceback':traceback.format_exc()},output/'extension_failure.json')
        raise

if __name__=='__main__':
    run_week05_extensions(Path(__file__).resolve().parent.parent)
