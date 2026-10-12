"""Freeze existing development models before reading held-out responses; fixed-model transfer only."""
from week05_core import *  # Removed when embedded in the self-contained notebook.
from frozen_assignment import *  # Removed when embedded in the self-contained notebook.
from datetime import datetime, timezone
import shutil

TRANSFER_PLAN = {
    'version':1,'global_scope':['B4','E8'],'roles':{'B':'joint worry/harm description','E':'complementary differentiated worry description'},
    'development_stability_median_min':.80,'development_stability_lower_decile_min':.80,
    'regional_k2':'diagnostic only; not a final rich regional typology',
    'development_model_refit':False,'heldout_model_refit':False,'retune_after_holdout':False,
    'heldout_expected_countries':29,'heldout_prepared_respondents':30090,
    'assignment':'nearest frozen centre; first stored centre on an exact tie',
    'distance_flag':'nearest distance > frozen assigned-profile development weighted p95',
    'distance_flag_is_overall_pass_fail':False,'ari_is_transfer_threshold':False,
    'profile_identity':'all original categories; three largest positive development category-vs-outside contrasts per profile are fixed descriptive anchors',
    'uncertainty':{'draws':1000,'seed':20261012,'unit':'countries, uniformly with replacement',
        'within_country':'preserve relative survey weights among complete cases',
        'model_fixed':True,'interval_percentiles':[2.5,97.5],
        'interpretation':'variation over the observed held-out countries; not worldwide population or fitting uncertainty'},
    'conclusion_rules':{
        'broad':'defining response contrasts remain recognizable without widespread deterioration in representation quality',
        'partial':'recognizable profiles coexist with identifiable profile/country-specific semantic or assignment-quality limitations',
        'poor':'substantial loss of defining patterns or widespread deterioration in representation quality',
        'decision':'analytical synthesis; no automatic numerical transfer score or undeclared cutoff'},
    'heldout_source':'course_artifacts/week03_heldout_country_data.parquet',
    'frozen_split_source':'course_artifacts/week03_country_split.csv',
}

def prepared_columns():
    return ['WPID_RANDOM','COUNTRY_ISO3','GlobalRegion','CountryIncomeLevel','WGT','country_split'] + \
        list(WORRY_SOURCES.values())+list(HARM_SOURCES.values())+WORRY+['harm_'+d for d in HARM_SOURCES]

def eligibility_audit(frame):
    audit=frame[['WPID_RANDOM','COUNTRY_ISO3','GlobalRegion']].copy()
    audit['observed_worry']=frame[WORRY].notna().sum(axis=1)
    audit['observed_harm_domains']=frame[['harm_'+d for d in HARM_SOURCES]].notna().sum(axis=1)
    audit['profile_eligible_any_observed']=audit.observed_worry.add(audit.observed_harm_domains).gt(0)
    audit['previous_4worry_4harm_eligible']=audit.observed_worry.ge(4)&audit.observed_harm_domains.ge(4)
    audit['complete_case']=frame[FEATURES].notna().all(axis=1)
    audit['exclusion_reason']=np.select([~audit.profile_eligible_any_observed,
        audit.profile_eligible_any_observed&~audit.previous_4worry_4harm_eligible,
        audit.previous_4worry_4harm_eligible&~audit.complete_case],
        ['zero observed profile responses','fewer than four observed worry or harm domains','remaining missing profile responses'],
        default='included complete case')
    countries=audit.groupby('COUNTRY_ISO3').agg(prepared=('WPID_RANDOM','size'),
        any_observed=('profile_eligible_any_observed','sum'),previous_4_4=('previous_4worry_4harm_eligible','sum'),
        complete=('complete_case','sum')).reset_index()
    countries['retained_fraction']=countries.complete/countries.prepared
    countries['excluded_zero_observed']=countries.prepared-countries.any_observed
    countries['excluded_4_4_stage']=countries.any_observed-countries.previous_4_4
    countries['excluded_remaining_missing']=countries.previous_4_4-countries.complete
    assert countries[['excluded_zero_observed','excluded_4_4_stage','excluded_remaining_missing']].sum().sum()==(~audit.complete_case).sum()
    return audit,countries

def freeze_existing_models(root):
    root=Path(root)
    data,old_audit,regions,references,provenance=prepare_development(root)
    base_info=json.loads((root/'.week05_build/points12_run.json').read_text())
    base=root/base_info['output_directory']
    base_manifest=json.loads((base/'run_manifest.json').read_text())
    assert base_manifest['provenance']==provenance
    raw=derive_frozen_features(pd.read_parquet(root/'course_artifacts/week03_development_data.parquet',columns=prepared_columns()))
    assert raw.country_split.eq('train').all() and raw.WPID_RANDOM.is_unique
    eligibility,country_audit=eligibility_audit(raw)
    complete=raw.loc[eligibility.complete_case].reset_index(drop=True)
    assert np.array_equal(complete.WPID_RANDOM,data.WPID_RANDOM)
    assert np.array_equal(complete[FEATURES].to_numpy(),data[FEATURES].to_numpy())
    assert len(complete)==109488
    source_names=['fixed_global_original_profiles_by_region.csv','fixed_global_profile_prevalence.csv',
        'fixed_global_assignment_quality.csv','development_distance_thresholds_provisional.csv']
    source_hashes={name:file_sha256(base/name) for name in source_names}
    profile_table=pd.read_csv(base/'fixed_global_original_profiles_by_region.csv')
    development_profiles=profile_table.loc[profile_table.scope.eq('global')].copy()
    prevalence=pd.read_csv(base/'fixed_global_profile_prevalence.csv')
    global_prevalence=prevalence.loc[prevalence.scope.eq('global')]
    thresholds=pd.read_csv(base/'development_distance_thresholds_provisional.csv')
    stability=previous_stability(root)
    assert stability.median_pairwise.ge(.8).all() and stability.p10_pairwise.ge(.8).all()
    core_hash=file_sha256(root/'.week05_build/week05_core.py')
    assignment_hash=file_sha256(root/'.week05_build/frozen_assignment.py')
    implementation_hash=file_sha256(root/'.week05_build/frozen_transfer.py')
    freeze_inputs={'development_provenance':provenance,'development_curated_sha256':file_sha256(root/'course_artifacts/week03_development_data.parquet'),
        'base_context':base_manifest['context'],'source_tables':source_hashes,'transfer_plan':TRANSFER_PLAN,
        'assignment_implementation_sha256':assignment_hash,'transfer_implementation_sha256':implementation_hash,
        'baseline_implementation_sha256':core_hash}
    context=digest_json(freeze_inputs)
    folder=root/'course_artifacts/week05_frozen_objective1_v1'/context[:16]
    if (folder/'freeze_seal.json').exists():
        bundle,manifest=load_frozen_package(folder)
        assert manifest['context']==context
        return folder,bundle,manifest,complete,regions
    folder.mkdir(parents=True,exist_ok=True)
    names=global_prevalence.set_index(['candidate','cluster']).working_description.to_dict()
    bundle={'context':context,'feature_order':FEATURES,'transform_order':TRANSFORM_COLUMNS,'models':{}}
    summary=[];anchors=[]
    for name,spec in SPECIFICATIONS.items():
        model=references[name]
        shares=structure(model['labels'],country_weights(complete))
        assert shares['global_benchmark_pass']
        bundle['models'][name]={'spec':asdict(spec),'centres':np.array(model['centres'],copy=True),
            'profile_names':{int(c):names[(name,c)] for c in range(spec.global_k)},
            'profile_distance_p95':{int(r.cluster):float(r.development_distance_p95) for r in thresholds.loc[thresholds.candidate.eq(name)].itertuples()},
            'reference_seed':20231006,'n_init':20,'source_sha256':model['source_sha256']}
        for cluster in range(spec.global_k):
            group=development_profiles.loc[development_profiles.candidate.eq(name)&development_profiles.cluster.eq(cluster)]
            top=group.sort_values('difference_vs_outside',ascending=False).head(3)
            for row in top.itertuples():
                anchors.append({'candidate':name,'cluster':cluster,'profile_name':names[(name,cluster)],
                    'feature':row.feature,'category':int(row.category),'development_proportion':row.proportion,
                    'development_outside_proportion':row.outside_proportion,'development_contrast':row.difference_vs_outside})
            subset=global_prevalence.loc[global_prevalence.candidate.eq(name)&global_prevalence.cluster.eq(cluster)].iloc[0]
            summary.append({'candidate':name,'cluster':cluster,'profile_name':names[(name,cluster)],
                'development_share':subset.equal_country_weighted_share,'development_respondents':int(subset.respondents),
                'interpretation':'descriptive development response pattern; not a latent natural population type'})
    atomic_joblib(bundle,folder/'models.joblib')
    shutil.copy2(root/'.week05_build/frozen_assignment.py',folder/'assignment.py')
    table_write(pd.DataFrame(summary),folder/'profile_definitions.csv')
    table_write(pd.DataFrame(anchors),folder/'development_defining_anchors.csv')
    table_write(development_profiles,folder/'development_original_category_profiles.csv')
    table_write(global_prevalence,folder/'development_global_prevalence.csv')
    table_write(pd.read_csv(base/'fixed_global_assignment_quality.csv'),folder/'development_assignment_quality.csv')
    table_write(thresholds,folder/'development_profile_distance_p95.csv')
    table_write(stability,folder/'development_stability.csv')
    table_write(country_audit,folder/'development_country_retention.csv')
    assigned=assign_frozen(complete,bundle)
    for name in SPECIFICATIONS:
        assert np.array_equal(assigned[name].cluster,references[name]['labels'])
        assigned[name]['profile_name']=assigned[name].cluster.map(bundle['models'][name]['profile_names'])
        assigned[name].to_parquet(folder/f'development_{name}_assignments.parquet',index=False)
    wide=eligibility.copy()
    for name in SPECIFICATIONS:
        wide=wide.merge(assigned[name][['WPID_RANDOM','cluster','nearest_distance','margin']].rename(columns={
            'cluster':name+'_cluster','nearest_distance':name+'_nearest_distance','margin':name+'_margin'}),
            on='WPID_RANDOM',how='left',validate='one_to_one')
        assert wide.loc[wide.complete_case,name+'_cluster'].notna().all()
        assert wide.loc[~wide.complete_case,name+'_cluster'].isna().all()
    wide.to_parquet(folder/'development_eligibility_and_assignments_all_respondents.parquet',index=False)
    table_write(pd.read_csv(root/'course_artifacts/week03_country_split.csv'),folder/'frozen_country_split.csv')
    for name in SPECIFICATIONS:
        for r in pd.DataFrame(bundle['models'][name]['centres']).itertuples(index=False,name=None):assert len(r)==21
    manifest={'context':context,'status':'frozen_before_heldout_responses','frozen_at_utc':datetime.now(timezone.utc).isoformat(),
        'approved_scope':['B4','E8'],'approval':'explicit user instruction: Freeze B4/E8, then run held-out validation',
        'data_population':'2023 complete-case respondents in development countries; missing responses are not imputed',
        'eligibility':'all six worry and seven original harm-domain responses substantive; equivalently all 20 derived features observed',
        'prior_screen':'at least four observed worry and four harm domains is reported; complete-case rule is stricter and determines assignment',
        'raw_codes':{'worry':{'1':2,'2':1,'3':0,'98':None,'99':None},
            'harm_personal':{'1':1,'2':0,'3':1,'4':0,'98':None,'99':None},
            'harm_known_person':{'1':0,'2':1,'3':1,'4':0,'98':None,'99':None}},
        'raw_sources':{'worry':WORRY_SOURCES,'harm':HARM_SOURCES},'feature_order':FEATURES,'transform_order':TRANSFORM_COLUMNS,
        'transformation':'recode top category, divide by top, subtract respondent mean in six worry coordinates, append mean; multiply both by sqrt(alpha/6); harm by sqrt((1-alpha)/14)',
        'imputation':None,'variance_standardization':False,'PCA':False,
        'weights':'relative WGT within included complete-case country; equal total influence per included country, separately within each split',
        'development_model_refit':False,'profile_ids':'preserved exactly from existing reference caches; not relabelled by prevalence',
        'regional_limitations':'local structure not universal; k2 only diagnostic; several smaller E profiles have weaker recovery; global/local ARI is not a retention or significance test',
        'global_stability_caution':'B has stronger whole-partition and reference-profile recovery; E meets ARI benchmarks but pooled cluster Jaccard lower tails are weak and must be reported',
        'transfer_plan':TRANSFER_PLAN,'freeze_inputs':freeze_inputs,'development_reload_verified':True,
        'development_country_count':113,'development_prepared_count':116820,'development_assigned_count':109488,
        'heldout_responses_used_at_freeze':False,'other_old_frozen_artifacts':'older course_artifacts/week04_frozen_profile_model.joblib and processed/*heldout*k3 are not this B/E analysis'}
    atomic_json(manifest,folder/'specification.json')
    files={p.name:file_sha256(p) for p in sorted(folder.iterdir()) if p.is_file()}
    atomic_json({'context':context,'status':'frozen_before_heldout_responses','frozen_at_utc':manifest['frozen_at_utc'],
        'files':files,'development_replay_verified':True,'heldout_responses_used':False},folder/'freeze_seal.json')
    reloaded,verified=load_frozen_package(folder)
    replay=assign_frozen(complete,reloaded)
    for name in SPECIFICATIONS:assert np.array_equal(replay[name].cluster,assigned[name].cluster)
    atomic_json({'package_directory':str(folder.relative_to(root)),'context':context},root/'.week05_build/freeze_run.json')
    return folder,reloaded,verified,complete,regions

def transfer_tables(frame,assigned,bundle,region_names,output_dir,split_name):
    prevalence=[];profiles=[];quality=[]
    for name,model in bundle['models'].items():
        labels=assigned[name].cluster.to_numpy()
        distance=assigned[name].nearest_distance.to_numpy();margin=assigned[name].margin.to_numpy()
        exceed=assigned[name].beyond_development_profile_p95.to_numpy()
        k=model['spec']['global_k']
        scopes=[('global',split_name,split_name,np.ones(len(frame),bool))]
        scopes += [('region',str(int(r)),region_names[r],frame.GlobalRegion.eq(r).to_numpy()) for r in sorted(frame.GlobalRegion.unique())]
        scopes += [('country',c,c,frame.COUNTRY_ISO3.eq(c).to_numpy()) for c in sorted(frame.COUNTRY_ISO3.unique())]
        for scope,key,area,mask in scopes:
            local=frame.loc[mask];ll=labels[mask];weights=frozen_country_weights(local)
            for cluster in range(k):
                inside=ll==cluster
                prevalence.append({'split':split_name,'candidate':name,'scope':scope,'area_id':key,'area_name':area,
                    'cluster':cluster,'profile_name':model['profile_names'][cluster],'respondents':int(inside.sum()),
                    'area_respondents':int(mask.sum()),'area_countries':int(local.COUNTRY_ISO3.nunique()),
                    'respondent_share':float(inside.mean()),'equal_country_weighted_share':float(weights[inside].sum())})
            pp=original_profiles(local,ll,weights)
            profiles.append(pp.assign(split=split_name,candidate=name,scope=scope,area_id=key,area_name=area))
            for cluster in [-1]+list(range(k)):
                inside=np.ones(len(local),bool) if cluster==-1 else ll==cluster
                if not inside.any():continue
                ww=weights[inside]
                quality.append({'split':split_name,'candidate':name,'scope':scope,'area_id':key,'area_name':area,
                    'cluster':cluster,'respondents':int(inside.sum()),
                    'kish_weighted_n':float(ww.sum()**2/(ww**2).sum()),
                    'distance_median':weighted_quantile(distance[mask][inside],ww,.5),
                    'distance_p90':weighted_quantile(distance[mask][inside],ww,.9),
                    'margin_median':weighted_quantile(margin[mask][inside],ww,.5),
                    'margin_p10':weighted_quantile(margin[mask][inside],ww,.1),
                    'profile_p95_exceedance':float(np.average(exceed[mask][inside],weights=ww))})
    prevalence=pd.DataFrame(prevalence);profiles=pd.concat(profiles,ignore_index=True);quality=pd.DataFrame(quality)
    for _,g in prevalence.groupby(['candidate','scope','area_id']):
        assert np.isclose(g.equal_country_weighted_share.sum(),1) and np.isclose(g.respondent_share.sum(),1)
    table_write(prevalence,Path(output_dir)/f'{split_name}_prevalence.csv')
    table_write(profiles,Path(output_dir)/f'{split_name}_original_category_profiles.csv')
    table_write(quality,Path(output_dir)/f'{split_name}_assignment_quality.csv')
    return prevalence,profiles,quality

def country_bootstrap_profiles(frame,assigned,bundle,output_dir):
    """Conditional fixed-model intervals; bootstrap country masses, not respondent/model fits."""
    plan=TRANSFER_PLAN['uncertainty'];countries=sorted(frame.COUNTRY_ISO3.unique());n=len(countries)
    rng=np.random.default_rng(plan['seed'])
    counts=rng.multinomial(n,np.ones(n)/n,size=plan['draws'])
    country_index={c:i for i,c in enumerate(countries)}
    ci=frame.COUNTRY_ISO3.map(country_index).to_numpy()
    within=(frame.WGT/frame.groupby('COUNTRY_ISO3').WGT.transform('sum')).to_numpy()
    rows=[]
    for name,model in bundle['models'].items():
        labels=assigned[name].cluster.to_numpy();k=model['spec']['global_k']
        mass=np.zeros((n,k));np.add.at(mass,(ci,labels),within)
        draws=counts@mass/n
        for cluster in range(k):
            values=draws[:,cluster]
            rows.append({'candidate':name,'cluster':cluster,'quantity':'profile_share','feature':'','category':-1,
                'estimate':float(mass[:,cluster].mean()),'p025':float(np.quantile(values,.025)),
                'p975':float(np.quantile(values,.975)),'valid_draws':len(values)})
        for feature in FEATURES:
            for category in ([0,1,2] if feature in WORRY else [0,1]):
                numerator=np.zeros((n,k));mask=frame[feature].to_numpy()==category
                np.add.at(numerator,(ci[mask],labels[mask]),within[mask])
                weighted=counts@numerator/n
                conditional=np.divide(weighted,draws,out=np.full_like(weighted,np.nan),where=draws>0)
                for cluster in range(k):
                    values=conditional[:,cluster];values=values[np.isfinite(values)]
                    total=mass[:,cluster].sum()
                    rows.append({'candidate':name,'cluster':cluster,'quantity':'original_category_probability',
                        'feature':feature,'category':category,
                        'estimate':float(numerator[:,cluster].sum()/total) if total else np.nan,
                        'p025':float(np.quantile(values,.025)) if len(values) else np.nan,
                        'p975':float(np.quantile(values,.975)) if len(values) else np.nan,'valid_draws':len(values)})
    result=pd.DataFrame(rows)
    table_write(result,Path(output_dir)/'heldout_country_bootstrap_intervals.csv')
    atomic_json({**plan,'countries':countries,'draw_count':len(counts),'bootstrap_counts_sha256':hashlib.sha256(counts.tobytes()).hexdigest()},
                Path(output_dir)/'bootstrap_design.json')
    return result

def run_heldout_transfer(root,folder,bundle,manifest,development,regions):
    root,folder=Path(root),Path(folder)
    # A valid pre-response freeze seal is a hard execution boundary.
    bundle,manifest=load_frozen_package(folder)
    assert manifest['heldout_responses_used_at_freeze'] is False
    output=root/'course_artifacts/week05_heldout_transfer_v1'/manifest['context'][:16]
    output.mkdir(parents=True,exist_ok=True)
    raw=pd.read_parquet(root/TRANSFER_PLAN['heldout_source'],columns=prepared_columns())
    first_read=datetime.now(timezone.utc).isoformat()
    assert first_read>manifest['frozen_at_utc']
    split=pd.read_csv(folder/'frozen_country_split.csv')
    expected=set(split.loc[split.country_split.eq('heldout_country'),'COUNTRY_ISO3'])
    development_ids=pd.read_parquet(root/'course_artifacts/week03_development_data.parquet',columns=['WPID_RANDOM']).WPID_RANDOM
    assert len(raw)==30090 and raw.COUNTRY_ISO3.nunique()==29 and set(raw.COUNTRY_ISO3)==expected
    assert raw.country_split.eq('heldout_country').all() and raw.WPID_RANDOM.is_unique
    assert not set(raw.WPID_RANDOM).intersection(development_ids)
    assert not set(raw.COUNTRY_ISO3).intersection(development.COUNTRY_ISO3)
    frame=derive_frozen_features(raw)
    audit,country_audit=eligibility_audit(frame)
    complete=frame.loc[audit.complete_case].reset_index(drop=True)
    zero=sorted(expected-set(complete.COUNTRY_ISO3))
    assert np.isfinite(complete.WGT).all() and complete.WGT.gt(0).all()
    region_names=regions.set_index('GlobalRegion').region_name.to_dict()
    # The split registry, not response patterns, determines country/region identities.
    lookup=split.set_index('COUNTRY_ISO3')
    assert (complete.GlobalRegion.to_numpy()==complete.COUNTRY_ISO3.map(lookup.GlobalRegion).to_numpy()).all()
    assignments=assign_frozen(complete,bundle)
    for name,table in assignments.items():
        table['profile_name']=table.cluster.map(bundle['models'][name]['profile_names'])
        table.to_parquet(output/f'heldout_{name}_assignments.parquet',index=False)
        audit=audit.merge(table[['WPID_RANDOM','cluster','nearest_distance','margin']].rename(columns={
            'cluster':name+'_cluster','nearest_distance':name+'_nearest_distance','margin':name+'_margin'}),
            on='WPID_RANDOM',how='left',validate='one_to_one')
        assert audit.loc[audit.complete_case,name+'_cluster'].notna().all()
        assert audit.loc[~audit.complete_case,name+'_cluster'].isna().all()
    audit.to_parquet(output/'heldout_eligibility_and_assignments_all_respondents.parquet',index=False)
    country_audit=country_audit.merge(split[['COUNTRY_ISO3','GlobalRegion','CountryIncomeLevel']],on='COUNTRY_ISO3',validate='one_to_one')
    table_write(country_audit,output/'heldout_country_retention.csv')
    table_write(audit.groupby('exclusion_reason').size().rename('respondents').reset_index(),output/'heldout_exclusion_counts.csv')
    prevalence,profiles,quality=transfer_tables(complete,assignments,bundle,region_names,output,'heldout')
    devprofiles=pd.read_csv(folder/'development_original_category_profiles.csv')
    devquality=pd.read_csv(folder/'development_assignment_quality.csv')
    devprev=pd.read_csv(folder/'development_global_prevalence.csv')
    differences=profiles.merge(devprofiles[['candidate','cluster','feature','category','proportion','difference_vs_outside']],
        on=['candidate','cluster','feature','category'],suffixes=('_heldout','_development'),validate='many_to_one')
    differences['difference_pp']=100*(differences.proportion_heldout-differences.proportion_development)
    table_write(differences,output/'heldout_vs_development_category_differences.csv')
    tv=differences.assign(absdiff=lambda g:abs(g.proportion_heldout-g.proportion_development)).groupby(
        ['candidate','scope','area_id','area_name','cluster','feature']).absdiff.sum().div(2).rename('feature_TV').reset_index()
    semantic=tv.groupby(['candidate','scope','area_id','area_name','cluster']).agg(mean_feature_TV=('feature_TV','mean'),
        maximum_feature_TV=('feature_TV','max')).reset_index()
    table_write(tv,output/'heldout_original_feature_TV.csv');table_write(semantic,output/'heldout_profile_semantic_TV.csv')
    anchors=pd.read_csv(folder/'development_defining_anchors.csv').merge(
        profiles.loc[profiles.scope.eq('global'),['candidate','cluster','feature','category','proportion','outside_proportion','difference_vs_outside']],
        on=['candidate','cluster','feature','category'],validate='one_to_one')
    anchors['heldout_contrast_direction_preserved']=anchors.difference_vs_outside.gt(0)
    anchors['proportion_shift_pp']=100*(anchors.proportion-anchors.development_proportion)
    table_write(anchors,output/'heldout_frozen_anchor_comparison.csv')
    comparison=quality.loc[quality.scope.eq('global')].merge(devquality.loc[devquality.scope.eq('global')].drop(columns=['scope','area_id','area_name']),
        on=['candidate','cluster'],suffixes=('_heldout','_development'),validate='one_to_one')
    comparison['distance_median_ratio']=comparison.distance_median_heldout/comparison.distance_median_development
    comparison['distance_p90_ratio']=comparison.distance_p90_heldout/comparison.distance_p90_development
    comparison['margin_median_difference']=comparison.margin_median_heldout-comparison.margin_median_development
    table_write(comparison,output/'heldout_vs_development_quality.csv')
    shares=prevalence.loc[prevalence.scope.eq('global')].merge(devprev[['candidate','cluster','equal_country_weighted_share']],
        on=['candidate','cluster'],suffixes=('_heldout','_development'),validate='one_to_one')
    shares['prevalence_difference_pp']=100*(shares.equal_country_weighted_share_heldout-shares.equal_country_weighted_share_development)
    table_write(shares,output/'heldout_vs_development_prevalence.csv')
    intervals=country_bootstrap_profiles(complete,assignments,bundle,output)
    join_checks={}
    for name in SPECIFICATIONS:
        saved=pd.read_parquet(output/f'heldout_{name}_assignments.parquet')
        check=complete[['WPID_RANDOM']].merge(saved,on='WPID_RANDOM',validate='one_to_one')
        assert len(check)==len(complete) and check.cluster.notna().all()
        replay=assign_frozen(complete,bundle)[name]
        assert np.array_equal(saved.cluster,replay.cluster)
        join_checks[name]={'unique_ids':True,'reload_assignment_identical':True,'all_prepared_ids_preserved_in_eligibility_file':len(audit)==len(raw)}
    load_frozen_package(folder)  # Verify the sealed development package did not change during transfer.
    atomic_json({'status':'completed_fixed_model_transfer','freeze_context':manifest['context'],
        'freeze_seal_sha256':file_sha256(folder/'freeze_seal.json'),'first_heldout_response_read_at_utc':first_read,
        'frozen_at_utc':manifest['frozen_at_utc'],'heldout_input_sha256':file_sha256(root/TRANSFER_PLAN['heldout_source']),
        'prepared_respondents':len(raw),'complete_respondents':len(complete),'excluded_respondents':len(raw)-len(complete),
        'prepared_countries':29,'assigned_countries':int(complete.COUNTRY_ISO3.nunique()),'zero_eligible_countries':zero,
        'model_refit':False,'retuning':False,'all_assignment_joins_verified':join_checks,
        'interpretation':'descriptive transfer, not ARI threshold testing or independent recovery by refitting',
        'tables':{p.name:file_sha256(p) for p in sorted(output.glob('*.csv'))},
        'assignments':{p.name:file_sha256(p) for p in sorted(output.glob('*.parquet'))}},output/'transfer_complete.json')
    atomic_json({'output_directory':str(output.relative_to(root)),'package_directory':str(folder.relative_to(root)),
        'context':manifest['context']},root/'.week05_build/transfer_run.json')
    return output,complete,assignments
