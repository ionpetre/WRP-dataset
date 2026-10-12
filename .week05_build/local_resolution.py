"""Development-only exploratory local resolution selection; no new geometry or holdout."""
from week05_core import *  # Removed when embedded in the self-contained notebook.

LOCAL_SELECTION_DESIGN = {
    'version': 1, 'coarse_k': [2, 3],
    'elbow_eligible_k': list(range(3,10)),
    'elbow_rule': 'smallest eligible nonmatched k within 95% of maximum normalized chord-minus-inertia gap',
    'max_additional_k_per_region_representation': 3,
    'global_ari_used_for_selection': False,
    'structural_global_rules_used_as_local_filters': False,
    'representation_algorithm_changes': False,
    'primary_stability': 'existing median and lower-decile pairwise ARI >=0.80 in both tests',
    'cluster_recovery': 'weighted Hungarian-overlap matching to each regional reference; descriptive Jaccard, no new threshold',
    'search_status': 'exploratory development selection after observing matched-resolution results; not independent confirmation',
}

def base_analysis_load(root, base_output):
    root, base_output = Path(root), Path(base_output)
    manifest = json.loads((base_output/'run_manifest.json').read_text())
    data,audit,regions,references,provenance = prepare_development(root)
    if manifest['provenance'] != provenance:
        raise ValueError('Baseline data, saved models, or runtime changed. Do not reuse these caches.')
    # Selection and all new fits use the identical fitting code and declared 2..10 design.
    if manifest['regional_design'] != REGIONAL_DESIGN:
        raise ValueError('Regional fitting/sampling design differs from baseline.')
    reference_summary=pd.read_csv(base_output/'regional_reference_summary.csv')
    profiles=pd.read_csv(base_output/'regional_original_profiles.csv')
    return data,regions,references,provenance,manifest['context'],reference_summary,profiles

def reference_cache(frame, region, name, k, cache_dir, context):
    spec=SPECIFICATIONS[name]
    seed=REGIONAL_DESIGN['seed']+int(region)
    payload={'context':context,'spec':asdict(spec),'k':int(k),'seed':int(seed),
             'tag':f'region_{region}_{name}_k{k}_reference',
             'training_rows_hash':hashlib.sha256(np.arange(len(frame),dtype=np.int64).tobytes()).hexdigest()}
    key=digest_json(payload)
    path=Path(cache_dir)/(key+'.joblib')
    if not path.exists():
        raise FileNotFoundError('Reference fit is missing; selection does not silently refit it: '+str(path))
    cached=joblib.load(path)
    if cached.get('cache_key')!=key or cached['status']!='ok':
        raise ValueError('Reference cache failed validation.')
    return cached

def profile_pairwise_differences(profiles):
    rows=[]
    for (region,name,k),group in profiles.groupby(['region','candidate','k']):
        matrix=group.pivot(index='cluster',columns=['feature','category'],values='proportion')
        pair=[]
        for a,b in itertools.combinations(matrix.index,2):
            difference=abs(matrix.loc[a]-matrix.loc[b])
            feature_tv=difference.groupby(level='feature').sum()/2
            pair.append(float(feature_tv.mean()))
        shares=group.groupby('cluster').cluster_share.first()
        rows.append({'region':int(region),'candidate':name,'k':int(k),
            'minimum_original_feature_TV_between_clusters':min(pair),
            'median_original_feature_TV_between_clusters':float(np.median(pair)),
            'smallest_cluster_share':float(shares.min())})
    return pd.DataFrame(rows)

def select_local_resolutions(reference_summary, profiles):
    # Deliberately omit all global agreement columns from the selection calculation.
    allowed=reference_summary[['region','candidate','k','status','inertia','largest_share','dominance']].copy()
    semantic=profile_pairwise_differences(profiles)
    decisions=[]
    diagnostics=[]
    for (region,name),group in allowed.groupby(['region','candidate']):
        group=group.loc[group.status.eq('ok')].sort_values('k').copy()
        assert group.k.tolist()==list(range(2,11))
        x=(group.k.to_numpy()-2)/8
        inertia=group.inertia.to_numpy()
        gap=(1-x)-(inertia-inertia[-1])/(inertia[0]-inertia[-1])
        group['normalized_elbow_gap']=gap
        group['incremental_inertia_gain_pct']=100*(1-group.inertia/group.inertia.shift(1))
        eligible=group.loc[group.k.isin(LOCAL_SELECTION_DESIGN['elbow_eligible_k'])
                           &group.k.ne(SPECIFICATIONS[name].global_k)]
        elbow=int(eligible.loc[eligible.normalized_elbow_gap.ge(.95*eligible.normalized_elbow_gap.max()),'k'].min())
        chosen=sorted(set(LOCAL_SELECTION_DESIGN['coarse_k']+[elbow])-{SPECIFICATIONS[name].global_k})
        for k in chosen:
            reasons=[]
            if k in [2,3]:reasons.append('prespecified coarse alternative; avoids forcing global resolution')
            if k==elbow:reasons.append('near within-region inertia elbow; coarsest of near-tied elbow candidates')
            decisions.append({'region':int(region),'candidate':name,'k':k,'selection_reason':'; '.join(reasons),
                              'global_agreement_used':False,'reference_only_semantic_review_required':True})
        diagnostics.append(group)
    diagnostics=pd.concat(diagnostics,ignore_index=True).merge(semantic,on=['region','candidate','k'],validate='one_to_one')
    decisions=pd.DataFrame(decisions).merge(diagnostics,on=['region','candidate','k'],validate='one_to_one')
    assert decisions.groupby(['region','candidate']).size().le(3).all()
    return decisions,diagnostics

def selection_profile_review(data, decisions, fitted, output_dir):
    rows=[]
    for region,name,k in decisions[['region','candidate','k']].itertuples(index=False,name=None):
        frame=data.loc[data.GlobalRegion.eq(region)].reset_index(drop=True)
        labels=fitted[(region,name,k)]['labels'];weights=country_weights(frame)
        profiles=original_profiles(frame,labels,weights)
        for cluster,group in profiles.groupby('cluster'):
            ranked=group.sort_values('difference_vs_outside',ascending=False)
            anchors=[]
            for row in ranked.head(3).itertuples():
                category_label=('very' if row.category==2 else 'somewhat' if row.category==1 else 'not worried') if row.feature in WORRY else ('harm' if row.category==1 else 'no harm')
                anchors.append(f'{row.feature}: {category_label} {100*row.proportion:.1f}% (outside difference {100*row.difference_vs_outside:+.1f}pp)')
            inside=labels==cluster;ww=weights[inside]
            rows.append({'region':region,'candidate':name,'k':k,'cluster':int(cluster),
                'cluster_share':float(ww.sum()),'respondents':int(inside.sum()),
                'effective_weighted_n':float(ww.sum()**2/(ww**2).sum()),
                'strongest_original_contrasts':' | '.join(anchors),
                'max_absolute_category_contrast':float(group.difference_vs_outside.abs().max()),
                'review_status':'screening description; not a frozen profile name'})
    result=pd.DataFrame(rows)
    table_write(result,Path(output_dir)/'shortlisted_profile_review.csv')
    return result

def cached_repetition(frame,region,name,k,kind,repeat,training,cache_dir,context):
    spec=SPECIFICATIONS[name]
    payload={'context':context,'spec':asdict(spec),'k':int(k),
             'seed':REGIONAL_DESIGN['seed']+int(region)*10000+1000+int(repeat),
             'tag':f'region_{region}_{name}_k{k}_{kind}_{repeat:02d}',
             'training_rows_hash':hashlib.sha256(np.asarray(training,dtype=np.int64).tobytes()).hexdigest()}
    key=digest_json(payload);path=Path(cache_dir)/(key+'.joblib')
    if not path.exists():raise FileNotFoundError('Missing declared repetition: '+str(path))
    result=joblib.load(path)
    if result.get('cache_key')!=key:raise ValueError('Repetition cache fingerprint mismatch.')
    return result

def cluster_recovery_summary(data,shortlist,fitted,cache_dir,context,output_dir):
    all_rows=[]
    for region,name,k in shortlist:
        frame=data.loc[data.GlobalRegion.eq(region)].reset_index(drop=True)
        weights=country_weights(frame)
        reference=fitted[(region,name,k)]['labels']
        ref_mass=np.bincount(reference,weights=weights,minlength=k)
        plans,_,_=make_regional_plans(frame,region,REGIONAL_DESIGN)
        for kind,indices in plans.items():
            values={j:[] for j in range(k)}
            for repeat,training in enumerate(indices):
                result=cached_repetition(frame,region,name,k,kind,repeat,training,cache_dir,context)
                if result['status']!='ok':continue
                labels=result['labels']
                overlap=np.bincount(reference.astype('int64')*k+labels.astype('int64'),weights=weights,minlength=k*k).reshape(k,k)
                rr,cc=linear_sum_assignment(-overlap)
                pred_mass=overlap.sum(axis=0)
                for ref,pred in zip(rr,cc):
                    union=ref_mass[ref]+pred_mass[pred]-overlap[ref,pred]
                    values[ref].append(float(overlap[ref,pred]/union) if union else np.nan)
            for cluster,series in values.items():
                all_rows.append({'region':region,'candidate':name,'k':k,'test':kind,'reference_cluster':cluster,
                    'reference_share':ref_mass[cluster], 'successful_repetitions':len(series),
                    'median_reference_jaccard':float(np.median(series)) if series else np.nan,
                    'p10_reference_jaccard':float(np.quantile(series,.1)) if series else np.nan})
    result=pd.DataFrame(all_rows)
    table_write(result,Path(output_dir)/'cluster_recovery_summary.csv')
    return result

def supported_resolution_summary(data,regions,stability,cluster_recovery,reference_summary,output_dir):
    rows=[]
    names=regions.set_index('GlobalRegion').region_name.to_dict()
    for (region,name,k),group in stability.groupby(['region','candidate','k']):
        respondent=group.loc[group.test.eq('respondents')].iloc[0]
        country=group.loc[group.test.eq('countries')].iloc[0]
        country_count=int(data.loc[data.GlobalRegion.eq(region)].COUNTRY_ISO3.nunique())
        respondent_pass=bool(respondent.full_50_fit_stability_benchmark_met)
        country_pass=bool(country.full_50_fit_stability_benchmark_met)
        loo_pass=country_count in [2,3,4] and bool(country.numerical_ari_benchmark_met)
        if respondent_pass and country_pass:status='both full stability benchmarks met'
        elif respondent_pass and loo_pass:status='respondent benchmark + limited LOO diagnostics met'
        elif respondent_pass and country_count==1:status='respondent-only benchmark; geographic stability unavailable'
        else:status='not qualified by the applicable stability benchmarks'
        ref=reference_summary.loc[reference_summary.region.eq(region)&reference_summary.candidate.eq(name)&reference_summary.k.eq(k)].iloc[0]
        recovery=cluster_recovery.loc[cluster_recovery.region.eq(region)&cluster_recovery.candidate.eq(name)&cluster_recovery.k.eq(k)]
        rr=recovery.loc[recovery.test.eq('respondents')]
        cc=recovery.loc[recovery.test.eq('countries')]
        rows.append({'region':int(region),'region_name':names[region],'candidate':name,'k':int(k),
            'countries':country_count,'status':status,'respondent_median_ari':respondent.median_pairwise,
            'respondent_p10_ari':respondent.p10_pairwise,'country_median_ari':country.median_pairwise,
            'country_p10_ari':country.p10_pairwise,'distinct_country_subsets':country.distinct_country_fits,
            'worst_cluster_respondent_p10_jaccard':rr.p10_reference_jaccard.min(),
            'worst_cluster_country_p10_jaccard':cc.p10_reference_jaccard.min(),
            'largest_share':ref.largest_share,'dominance':ref.dominance,
            'global_structural_benchmark_pass':bool(ref.global_benchmark_pass),
            'local_global_ari_descriptive_only':ref.ari_unweighted})
    result=pd.DataFrame(rows)
    table_write(result,Path(output_dir)/'supported_local_resolutions.csv')
    return result

def plot_local_stability_grid(summary, regions, output_dir):
    import matplotlib.pyplot as plt
    for name in SPECIFICATIONS:
        fig,axes=plt.subplots(1,2,figsize=(14,7))
        for ax,column,title in zip(axes,['respondent_p10_ari','country_p10_ari'],['Respondent lower-decile ARI','Country/LOO lower-decile ARI']):
            sub=summary.loc[summary.candidate.eq(name)]
            matrix=sub.pivot(index='region',columns='k',values=column).reindex(index=regions.GlobalRegion,columns=range(2,11))
            image=ax.imshow(np.ma.masked_invalid(matrix.to_numpy()),vmin=0,vmax=1,cmap='viridis',aspect='auto')
            ax.set_facecolor('#d9d9d9');ax.set_xticks(range(9),range(2,11));ax.set_xlabel('Local k (grey = untested or unavailable)')
            ax.set_yticks(range(len(regions)),regions.region_name)
            for i in range(len(matrix)):
                for j in range(9):
                    value=matrix.iloc[i,j]
                    if np.isfinite(value):ax.text(j,i,f'{value:.2f}',ha='center',va='center',fontsize=7,color='white' if value<.55 else 'black')
            ax.set_title(title)
        fig.suptitle(f'{name} geometry: tested local resolutions (exploratory selection)',fontsize=14)
        fig.tight_layout();fig.subplots_adjust(bottom=.11,right=.93)
        fig.colorbar(image,cax=fig.add_axes([.95,.20,.012,.60]))
        fig.text(.02,.025,'Benchmark 0.80. Northern/Southern Africa: LOO, not 50 country fits. US/NZ: country test unavailable. Pairwise ARIs are dependent.',fontsize=8)
        output=Path(output_dir)/'figures';output.mkdir(exist_ok=True)
        fig.savefig(output/f'{name}_local_resolution_stability.png',dpi=150,bbox_inches='tight')
        plt.show()
