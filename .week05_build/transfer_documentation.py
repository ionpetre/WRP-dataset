"""Post-freeze reporting only; never changes models, transformations or transfer thresholds."""

def transfer_reporting_tables(root,package,output):
    import pandas as pd
    from pathlib import Path
    root,package,output=Path(root),Path(package),Path(output)
    definitions=pd.read_csv(package/'profile_definitions.csv')
    differences=pd.read_csv(output/'heldout_vs_development_category_differences.csv')
    country_anchors=definitions[['candidate','cluster','profile_name']].merge(
        pd.read_csv(package/'development_defining_anchors.csv').drop(columns='profile_name'),
        on=['candidate','cluster'],validate='one_to_many').merge(
        differences.loc[differences.scope.eq('country')],
        on=['candidate','cluster','feature','category'],validate='one_to_many')
    country_anchors['heldout_country_contrast_positive']=country_anchors.difference_vs_outside_heldout.gt(0)
    country_quality=pd.read_csv(output/'heldout_assignment_quality.csv')
    country_anchors=country_anchors.merge(country_quality.loc[country_quality.scope.eq('country'),
        ['candidate','cluster','area_id','respondents','kish_weighted_n']],
        on=['candidate','cluster','area_id'],validate='many_to_one')
    table_write(country_anchors,output/'country_frozen_anchor_diagnostics.csv')
    semantic=pd.read_csv(output/'heldout_profile_semantic_TV.csv').merge(
        country_quality[['candidate','scope','area_id','cluster','respondents','kish_weighted_n']],
        on=['candidate','scope','area_id','cluster'],validate='one_to_one')
    semantic=semantic.merge(definitions[['candidate','cluster','profile_name']],on=['candidate','cluster'],validate='many_to_one')
    table_write(semantic,output/'semantic_differences_with_sample_sizes.csv')
    holdout=pd.read_parquet(root/'course_artifacts/week03_heldout_country_data.parquet',
        columns=['COUNTRY_ISO3','Country','Age','AgeGroups3','Gender','Education','Urbanicity2','WGT','WPID_RANDOM'])
    development=pd.read_parquet(root/'course_artifacts/week03_development_data.parquet',
        columns=['COUNTRY_ISO3','Country','Age','AgeGroups3','Gender','Education','Urbanicity2','WGT','WPID_RANDOM'])
    country_names=pd.concat([development[['COUNTRY_ISO3','Country']],holdout[['COUNTRY_ISO3','Country']]]).drop_duplicates()
    assert country_names.COUNTRY_ISO3.is_unique
    country=pd.read_csv(output/'heldout_country_retention.csv').merge(country_names,on='COUNTRY_ISO3',validate='one_to_one')
    quality_country=country_quality.loc[country_quality.scope.eq('country')&country_quality.cluster.eq(-1)].merge(
        country,left_on='area_id',right_on='COUNTRY_ISO3',validate='many_to_one')
    table_write(quality_country,output/'heldout_country_quality_and_retention.csv')
    selection=[]
    for split,raw,audit_path in [('development',development,package/'development_eligibility_and_assignments_all_respondents.parquet'),
                               ('heldout',holdout,output/'heldout_eligibility_and_assignments_all_respondents.parquet')]:
        eligibility=pd.read_parquet(audit_path,columns=['WPID_RANDOM','complete_case'])
        raw=raw.merge(eligibility,on='WPID_RANDOM',validate='one_to_one')
        for cohort,frame in [('prepared',raw),('complete_case',raw.loc[raw.complete_case]),('excluded',raw.loc[~raw.complete_case])]:
            weights=frozen_country_weights(frame)
            for feature in ['Gender','Education','Urbanicity2','AgeGroups3']:
                values=frame[feature].fillna('missing').astype(str)
                for category in sorted(values.unique()):
                    mask=values.eq(category).to_numpy()
                    selection.append({'split':split,'cohort':cohort,'feature':feature,'category':category,
                        'respondents':int(mask.sum()),'countries_in_cohort':int(frame.COUNTRY_ISO3.nunique()),
                        'equal_country_weighted_share':float(weights[mask].sum()),
                        'interpretation':'descriptive selection audit; weights recomputed within cohort; country sets may differ'})
            observed=frame.Age.notna().to_numpy()
            selection.append({'split':split,'cohort':cohort,'feature':'Age','category':'observed mean',
                'respondents':int(observed.sum()),'countries_in_cohort':int(frame.COUNTRY_ISO3.nunique()),
                'equal_country_weighted_share':float(np.average(frame.Age.to_numpy()[observed],weights=weights[observed])),
                'interpretation':'weighted mean age among observed ages; not a category proportion'})
    selection=pd.DataFrame(selection)
    table_write(selection,output/'missingness_selection_demographic_audit.csv')
    prev=pd.read_csv(output/'heldout_vs_development_prevalence.csv')
    intervals=pd.read_csv(output/'heldout_country_bootstrap_intervals.csv')
    share_intervals=intervals.loc[intervals.quantity.eq('profile_share'),['candidate','cluster','p025','p975','valid_draws']]
    comparison=prev.merge(share_intervals,on=['candidate','cluster'],validate='one_to_one')
    table_write(comparison,output/'prevalence_comparison_with_country_intervals.csv')
    recovery=[]
    for name,encoding,balance,k in [('B','012','balanced',4),('E','013','worry_emphasized',8)]:
        source=root/f'course_artifacts/week04_experiment1_complete_overall_worry_v3/{encoding}/cluster_recovery.csv'
        original=pd.read_csv(source)
        selected=original.loc[original.balance.eq(balance)&original.k.eq(k)]
        result=selected.groupby(['experiment','cluster']).jaccard.agg(median_jaccard='median',
            p10_jaccard=lambda g:g.quantile(.1),fits='size').reset_index()
        result['candidate']=name;result['source_sha256']=file_sha256(source)
        recovery.append(result)
    table_write(pd.concat(recovery,ignore_index=True),output/'development_existing_per_profile_recovery.csv')
    return comparison,quality_country,semantic,country_anchors,selection

def plot_transfer_figures(root,package,output):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon,Patch
    from matplotlib.colors import Normalize
    from matplotlib.cm import ScalarMappable
    from pathlib import Path
    root,package,output=Path(root),Path(package),Path(output)
    figures=output/'figures';figures.mkdir(exist_ok=True)
    files=[]
    shares=pd.read_csv(output/'prevalence_comparison_with_country_intervals.csv')
    fig,axes=plt.subplots(1,2,figsize=(15,7),layout='constrained',sharex=True)
    for ax,name in zip(axes,['B','E']):
        group=shares.loc[shares.candidate.eq(name)].sort_values('cluster');y=np.arange(len(group))
        dev=100*group.equal_country_weighted_share_development.to_numpy();held=100*group.equal_country_weighted_share_heldout.to_numpy()
        ax.barh(y+.17,dev,height=.32,color='#bdbdbd',label='Development: fixed reference')
        ax.barh(y-.17,held,height=.32,color='#327c9e',label='Held-out: unchanged assignments')
        ax.errorbar(held,y-.17,xerr=np.vstack([held-100*group.p025,100*group.p975-held]),fmt='none',ecolor='black',capsize=3)
        labels=['C'+str(r.cluster)+': '+r.profile_name for r in group.itertuples()]
        ax.set_yticks(y,labels,fontsize=9);ax.invert_yaxis();ax.set_xlim(0,48);ax.set_xlabel('Equal-country-weighted profile share (%)')
        ax.set_title(name+' global profiles');ax.grid(axis='x',alpha=.2)
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.5,-.045),ncol=2,fontsize=9)
    fig.suptitle('Frozen profiles: development versus 29 held-out countries\nBars: point estimates; whiskers: 95% fixed-model country-bootstrap intervals',fontsize=13)
    path=figures/'development_vs_heldout_profile_prevalence.png';fig.savefig(path,dpi=160,bbox_inches='tight');plt.close(fig);files.append(path)
    quality=pd.read_csv(output/'heldout_country_quality_and_retention.csv')
    devq=pd.read_csv(package/'development_assignment_quality.csv')
    order=quality.groupby('Country').profile_p95_exceedance.max().sort_values(ascending=False).index.tolist()
    fig,axes=plt.subplots(1,2,figsize=(13,10),sharey=True)
    for ax,name,color in zip(axes,['B','E'],['#327c9e','#b46b32']):
        g=quality.loc[quality.candidate.eq(name)].set_index('Country').reindex(order)
        ax.scatter(100*g.profile_p95_exceedance,np.arange(len(g)),c=color,s=35)
        baseline=devq.loc[devq.candidate.eq(name)&devq.scope.eq('global')&devq.cluster.eq(-1),'profile_p95_exceedance'].iloc[0]
        ax.axvline(100*baseline,color='#777777',linestyle='--',label='Development overall rate')
        ax.set_title(name+': unusually distant assignments');ax.set_xlim(0,28);ax.set_xlabel('Beyond assigned-profile development p95 (%)')
        ax.set_yticks(range(len(order)),order,fontsize=9);ax.grid(axis='x',alpha=.2);ax.legend(fontsize=8)
    axes[0].invert_yaxis()  # Shared axis: invert once, not once per subplot.
    axes[1].tick_params(labelleft=False)
    fig.subplots_adjust(left=.24,right=.98,bottom=.09,top=.90,wspace=.12)
    fig.suptitle('Country-specific transfer limitations hidden by the aggregate\nEach cutoff was frozen in development; these flags are not automatic failure thresholds',fontsize=13)
    path=figures/'heldout_country_distance_flags.png';fig.savefig(path,dpi=160,bbox_inches='tight');plt.close(fig);files.append(path)
    anchors=pd.read_csv(output/'heldout_frozen_anchor_comparison.csv')
    intervals=pd.read_csv(output/'heldout_country_bootstrap_intervals.csv')
    anchors=anchors.merge(intervals.loc[intervals.quantity.eq('original_category_probability'),['candidate','cluster','feature','category','p025','p975']],
        on=['candidate','cluster','feature','category'],validate='one_to_one')
    fig,axes=plt.subplots(1,2,figsize=(15,12),layout='constrained',sharex=True)
    for ax,name in zip(axes,['B','E']):
        g=anchors.loc[anchors.candidate.eq(name)].sort_values(['cluster','feature','category']).reset_index(drop=True)
        y=np.arange(len(g));held=100*g.proportion.to_numpy()
        ax.scatter(100*g.development_proportion,y+.12,color='#888888',marker='x',label='Development')
        ax.errorbar(held,y-.12,xerr=np.vstack([held-100*g.p025,100*g.p975-held]),fmt='o',markersize=3,color='#327c9e',capsize=2,label='Held-out + country interval')
        labels=[]
        for r in g.itertuples():
            category={0:'not',1:'somewhat',2:'very'}[r.category] if r.feature in WORRY else ('harm' if r.category==1 else 'no harm')
            labels.append(f'C{r.cluster}: {r.feature.replace("worry_","").replace("harm_","").replace("_"," ")} ({category})')
        ax.set_yticks(y,labels,fontsize=8);ax.invert_yaxis();ax.set_xlim(-2,103);ax.set_xlabel('Within-profile original response (%)');ax.set_title(name+' frozen descriptive anchors');ax.grid(axis='x',alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Original-response transfer: anchors selected before held-out access\nSome sharp E anchors follow from the geometry; preservation is not independent discovery of natural types',fontsize=13)
    path=figures/'frozen_anchor_original_response_transfer.png';fig.savefig(path,dpi=160,bbox_inches='tight');plt.close(fig);files.append(path)
    # All-profile country maps use the same global cluster IDs and a single 0–100 scale.
    split=pd.read_csv(package/'frozen_country_split.csv')
    heldout=set(split.loc[split.country_split.eq('heldout_country'),'COUNTRY_ISO3'])
    info=json.loads((root/'.week05_build/points12_run.json').read_text())
    dev=pd.read_csv(root/info['output_directory']/'fixed_global_profile_prevalence.csv')
    held=pd.read_csv(output/'heldout_prevalence.csv')
    all_countries=pd.concat([dev.loc[dev.scope.eq('country')],held.loc[held.scope.eq('country')]],ignore_index=True)
    table_write(all_countries,output/'fixed_global_all_country_prevalence.csv')
    world=json.loads((root/'course_artifacts/cartography/ne_50m_admin_0_countries.geojson').read_text())
    mapping={}
    for feature in world['features']:
        code=feature['properties'].get('ADM0_A3')
        # PSX is the cartography's administrative key; its ISO_A3 is explicitly PSE.
        # This matches identifiers only and does not alter any boundary geometry.
        aliases={'KOS':'XKX','SDS':'SSD','PSX':'PSE'}
        if code=='PSX':assert feature['properties'].get('ISO_A3')=='PSE'
        code=aliases.get(code,code);mapping[code]=feature
    assert not set(all_countries.area_id)-set(mapping)
    atomic_json({'cartography_source':'Natural Earth cached GeoJSON','country_keys_matched':int(all_countries.area_id.nunique()),
        'aliases':{'KOS':'XKX','SDS':'SSD','PSX':'PSE'},'boundaries_changed':False,
        'initial_plot_failure':'PSE had no direct ADM0_A3 match; resolved using verified ISO_A3=PSE on ADM0_A3=PSX',
        'models_and_transfer_results_changed':False},output/'map_key_audit.json')
    names=pd.read_csv(package/'profile_definitions.csv').set_index(['candidate','cluster']).profile_name.to_dict()
    cmap=plt.get_cmap('viridis');norm=Normalize(0,100)
    for name,k in [('B',4),('E',8)]:
        fig,axes=plt.subplots(k//2,2,figsize=(15,4*k//2),squeeze=False)
        for cluster,ax in enumerate(axes.ravel()):
            g=all_countries.loc[all_countries.candidate.eq(name)&all_countries.cluster.eq(cluster)]
            values=(100*g.set_index('area_id').equal_country_weighted_share).to_dict()
            for code,feature in mapping.items():
                if code=='ATA':continue
                geom=feature['geometry'];polygons=geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]
                color=cmap(norm(values[code])) if code in values else '#eeeeee'
                for polygon in polygons:
                    ax.add_patch(Polygon(np.array(polygon[0]),closed=True,facecolor=color,
                        edgecolor='black' if code in heldout else '#888888',linewidth=.55 if code in heldout else .18))
                if code in values:
                    # Use the largest polygon, not the first (which may be a small
                    # island belonging to a large country such as Canada/Russia).
                    largest_extent=max(np.ptp(np.array(p[0])[:,0])*np.ptp(np.array(p[0])[:,1]) for p in polygons)
                    if largest_extent<2:
                        prop=feature['properties'];ax.scatter(float(prop['LABEL_X']),float(prop['LABEL_Y']),
                            s=18,marker='D' if code in heldout else 'o',color=color,edgecolor='black',linewidth=.35,zorder=5)
            ax.set_xlim(-180,180);ax.set_ylim(-60,85);ax.set_aspect('equal');ax.set_xticks([]);ax.set_yticks([])
            ax.set_title(f'{name} C{cluster}: {names[(name,cluster)]}',fontsize=10);ax.set_facecolor('#f5f8fa')
        fig.subplots_adjust(left=.02,right=.90,bottom=.08,top=.94,hspace=.2)
        fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),cax=fig.add_axes([.92,.20,.015,.60])).set_label('Within-country survey-weighted profile share (%)')
        fig.legend(handles=[Patch(facecolor='white',edgecolor='black',label='Black border: held-out country'),
                            Patch(facecolor='#eeeeee',label='No 2023 analysis data')],loc='lower center',bbox_to_anchor=(.5,.04),ncol=2)
        fig.suptitle(name+': frozen global profiles across development and held-out countries',fontsize=15)
        fig.text(.02,.012,'Complete cases; shared 0–100% scale. Tiny countries use dots/diamonds. Natural Earth de facto boundaries are not a political claim.',fontsize=8)
        path=figures/f'{name}_frozen_all_country_profile_maps.png';fig.savefig(path,dpi=160,bbox_inches='tight');plt.close(fig);files.append(path)
    return files
