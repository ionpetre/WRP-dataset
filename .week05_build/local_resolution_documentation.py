"""Reporting only: does not select resolutions, change fits, or access held-out responses."""

FULL_SUPPORT = 'both full stability benchmarks met'
LOO_SUPPORT = 'respondent benchmark + limited LOO diagnostics met'
SINGLE_SUPPORT = 'respondent-only benchmark; geographic stability unavailable'

def local_support_table(supported, regions, output_dir):
    rows = []
    for region in regions.itertuples():
        row = {'region': int(region.GlobalRegion), 'region_name': region.region_name,
               'countries': int(region.countries)}
        for name in SPECIFICATIONS:
            group = supported.loc[supported.region.eq(region.GlobalRegion) & supported.candidate.eq(name)]
            row[name + '_tested_k'] = ', '.join(map(str, sorted(group.k)))
            for status, suffix in [(FULL_SUPPORT, 'full'), (LOO_SUPPORT, 'limited_LOO'),
                                   (SINGLE_SUPPORT, 'respondent_only')]:
                values = sorted(group.loc[group.status.eq(status), 'k'])
                row[name + '_' + suffix] = ', '.join(map(str, values)) if values else 'none'
        rows.append(row)
    result = pd.DataFrame(rows)
    table_write(result, Path(output_dir) / 'regional_supported_k_sets.csv')
    return result

def qualified_local_semantics(data, supported, profiles, overlaps, fixed_profiles, fitted, output_dir):
    """All qualified resolutions: category contrasts, sample size, overlap and semantic shifts."""
    qualified = supported.loc[supported.status.isin([FULL_SUPPORT, LOO_SUPPORT, SINGLE_SUPPORT])]
    rows, category_tables = [], []
    for resolution in qualified.itertuples():
        region, name, k = resolution.region, resolution.candidate, resolution.k
        frame = data.loc[data.GlobalRegion.eq(region)].reset_index(drop=True)
        labels = fitted[(region, name, k)]['labels']
        weights = country_weights(frame)
        selected = profiles.loc[profiles.region.eq(region) & profiles.candidate.eq(name) & profiles.k.eq(k)]
        category_tables.append(selected.assign(stability_support=resolution.status))
        ov = overlaps.loc[overlaps.region.eq(region) & overlaps.candidate.eq(name) & overlaps.k.eq(k)]
        for cluster, group in selected.groupby('cluster'):
            inside = labels == cluster
            ww = weights[inside]
            dominant = ov.loc[ov.local_cluster.eq(cluster)].sort_values('global_given_local', ascending=False).iloc[0]
            gc = int(dominant.global_cluster)
            original = group.set_index(['feature', 'category']).proportion
            # Include low/middle worry and absence of harm: low-burden profiles should not
            # be described by their least-negative "very worried" or harm contrasts.
            contrasts = group
            anchors = []
            for anchor in contrasts.sort_values('difference_vs_outside', ascending=False).head(3).itertuples():
                label = anchor.feature.replace('_', ' ')
                if anchor.feature in WORRY:
                    label += ': ' + {0: 'not worried', 1: 'somewhat worried', 2: 'very worried'}[anchor.category]
                else:
                    label += ': harmed' if anchor.category == 1 else ': no harm'
                anchors.append(f'{label} {100*anchor.proportion:.1f}% ({100*anchor.difference_vs_outside:+.1f}pp vs outside)')
            semantic_tv = {}
            for scope, area in [('global', None), ('region', region)]:
                ref = fixed_profiles.loc[fixed_profiles.candidate.eq(name) & fixed_profiles.scope.eq(scope)
                                         & fixed_profiles.cluster.eq(gc)]
                if area is not None:
                    ref = ref.loc[pd.to_numeric(ref.area_id, errors='coerce').eq(area)]
                if ref.empty:
                    semantic_tv[scope] = np.nan
                else:
                    difference = abs(original - ref.set_index(['feature', 'category']).proportion)
                    assert difference.notna().all()
                    semantic_tv[scope] = float((difference.groupby(level='feature').sum()/2).mean())
            # Near-pure category flags are descriptive anchors, not a reconstruction test.
            pure = group.loc[group.proportion.ge(.98) & group.difference_vs_outside.ge(.5)]
            flags = ' | '.join(f'{r.feature}, category {r.category}' for r in pure.itertuples())
            rows.append({'region': region, 'region_name': resolution.region_name, 'candidate': name,
                         'k': k, 'cluster': int(cluster), 'stability_support': resolution.status,
                         'cluster_share': float(ww.sum()), 'respondents': int(inside.sum()),
                         'countries_represented': int(frame.loc[inside, 'COUNTRY_ISO3'].nunique()),
                         'kish_weighted_n_descriptive': float(ww.sum()**2 / (ww**2).sum()),
                         'original_response_anchors': ' | '.join(anchors),
                         'near_pure_original_category_flags': flags,
                         'largest_overlap_global_cluster': gc,
                         'largest_overlap_fraction': float(dominant.global_given_local),
                         'mean_feature_TV_vs_global_profile': semantic_tv['global'],
                         'mean_feature_TV_vs_same_region_fixed_profile': semantic_tv['region']})
    result = pd.DataFrame(rows)
    table_write(result, Path(output_dir)/'qualified_local_profile_interpretations.csv')
    if category_tables:
        table_write(pd.concat(category_tables, ignore_index=True),
                    Path(output_dir)/'qualified_local_original_category_distributions.csv')
    return result

def compare_supported_local_resolutions(data, supported, fitted, output_dir):
    """Descriptive, weighted split/merge evidence; independently fitted k are not nested."""
    qualified = supported.loc[supported.status.isin([FULL_SUPPORT, LOO_SUPPORT, SINGLE_SUPPORT])]
    rows, cells = [], []
    for (region, name), group in qualified.groupby(['region', 'candidate']):
        frame = data.loc[data.GlobalRegion.eq(region)].reset_index(drop=True)
        weights = country_weights(frame)
        for coarse, fine in itertools.combinations(sorted(group.k), 2):
            co = fitted[(region, name, coarse)]['labels']
            fi = fitted[(region, name, fine)]['labels']
            stats, overlap = compare_partitions(fi, co, weights)
            # fine -> coarse purity = mass belonging to each fine group's dominant coarse group.
            rows.append({'region': region, 'candidate': name, 'coarse_k': coarse, 'fine_k': fine,
                         'ari_unweighted': stats['ari_unweighted'],
                         'fine_to_coarse_purity': stats['local_to_global_purity'],
                         'coarse_to_fine_purity': stats['global_to_local_purity'],
                         'note': 'approximate split/merge comparison; not a nested hierarchy'})
            overlap = overlap.rename(columns={'local_cluster': 'fine_cluster', 'global_cluster': 'coarse_cluster',
                                               'global_given_local': 'coarse_given_fine', 'local_given_global': 'fine_given_coarse'})
            cells.append(overlap.assign(region=region, candidate=name, coarse_k=coarse, fine_k=fine))
    result = pd.DataFrame(rows)
    table_write(result, Path(output_dir)/'supported_local_resolution_comparisons.csv')
    if cells:
        table_write(pd.concat(cells, ignore_index=True), Path(output_dir)/'supported_local_resolution_overlaps.csv')
    return result

def plot_qualified_local_profiles(profiles, supported, regions, output_dir):
    """A deliberately labelled illustrative subset; complete category tables remain available."""
    requested = [(2, 'B', 3), (13, 'B', 2), (13, 'E', 8), (7, 'E', 3)]
    qualified = set(supported.loc[supported.status.isin([FULL_SUPPORT, LOO_SUPPORT]),
                                 ['region', 'candidate', 'k']].itertuples(index=False, name=None))
    files = []
    for region, name, k in requested:
        if (region, name, k) not in qualified:
            continue
        sel = profiles.loc[profiles.region.eq(region) & profiles.candidate.eq(name) & profiles.k.eq(k)]
        matrices = [sel.loc[sel.feature.isin(WORRY) & sel.category.eq(2)].pivot(index='feature', columns='cluster', values='proportion').reindex(WORRY),
                    sel.loc[sel.feature.isin(PERSONAL+KNOWN) & sel.category.eq(1)].pivot(index='feature', columns='cluster', values='proportion').reindex(PERSONAL+KNOWN)]
        fig, axes = plt.subplots(1, 2, figsize=(15, 7), layout='constrained')
        for ax, matrix, title in zip(axes, matrices, ['Very worried (%)', 'Personal / known-person harm (%)']):
            im = ax.imshow(matrix, aspect='auto', cmap='YlGnBu', vmin=0, vmax=1)
            ax.set_yticks(range(len(matrix)), [x.replace('worry_', '').replace('harm_', '').replace('_', ' ') for x in matrix.index])
            shares = sel.groupby('cluster').cluster_share.first()
            ax.set_xticks(range(k), [f'C{c}\n{100*shares[c]:.1f}%' for c in matrix.columns])
            ax.set_xlabel('Local cluster ID and equal-country-weighted share')
            ax.set_title(title)
            for i in range(len(matrix)):
                for j in range(k):
                    value = matrix.iloc[i,j]
                    ax.text(j, i, f'{100*value:.0f}', ha='center', va='center', fontsize=8,
                            color='white' if value > .55 else 'black')
        region_name = regions.set_index('GlobalRegion').loc[region, 'region_name']
        fig.suptitle(f'{region_name}: {name} geometry, local k={k}\nIllustration, not a unique optimal resolution; development complete cases only', fontsize=13)
        fig.colorbar(im, ax=axes, shrink=.65, label='Weighted proportion')
        folder = Path(output_dir)/'figures'; folder.mkdir(exist_ok=True)
        path = folder/f'{name}_region{region}_k{k}_qualified_original_profiles.png'
        fig.savefig(path, dpi=160, bbox_inches='tight')
        plt.close(fig); files.append(path)
    return files

def plot_report_stability(supported, regions, output_dir):
    """Readable two-panel grid; explicit distinction between untested k and unavailable tests."""
    paths = []
    for name in SPECIFICATIONS:
        fig, axes = plt.subplots(1, 2, figsize=(15, 8), sharey=True)
        for ax, field, title in zip(axes, ['respondent_p10_ari', 'country_p10_ari'],
                                    ['Respondent lower-decile ARI', 'Country / LOO lower-decile ARI']):
            sub = supported.loc[supported.candidate.eq(name)]
            matrix = sub.pivot(index='region', columns='k', values=field).reindex(index=regions.GlobalRegion, columns=range(2,11))
            im = ax.imshow(np.ma.masked_invalid(matrix.to_numpy()), vmin=0, vmax=1, cmap='viridis', aspect='auto')
            ax.set_facecolor('#dedede'); ax.set_xticks(range(9), range(2,11)); ax.set_xlabel('Local k')
            ax.set_title(title)
            ax.set_yticks(range(len(regions)), regions.region_name)
            for i, region in enumerate(regions.GlobalRegion):
                for j, k in enumerate(range(2,11)):
                    value = matrix.iloc[i,j]
                    if np.isfinite(value):
                        ax.text(j, i, f'{value:.2f}', ha='center', va='center', fontsize=8,
                                color='white' if value < .55 else 'black')
                        # Outline only a resolution that meets BOTH applicable tests.
                        row = sub.loc[sub.region.eq(region) & sub.k.eq(k)]
                        if row.iloc[0].status in [FULL_SUPPORT, LOO_SUPPORT]:
                            from matplotlib.patches import Rectangle
                            ax.add_patch(Rectangle((j-.48,i-.48),.96,.96,fill=False,edgecolor='#d62728',linewidth=1.4))
                    elif k in sub.loc[sub.region.eq(region), 'k'].tolist():
                        ax.text(j, i, 'N/A', ha='center', va='center', fontsize=7)
        axes[1].tick_params(labelleft=False)
        fig.subplots_adjust(left=.25,right=.93,bottom=.13,top=.88,wspace=.12)
        fig.colorbar(im,cax=fig.add_axes([.945,.20,.012,.60]))
        fig.suptitle(f'{name}: exploratory local-resolution stability\nRed outline: both applicable benchmarks met (not a significance test)',fontsize=14)
        fig.text(.025,.055,'Grey blank = untested k. N/A = no country test. Threshold 0.80 uses unrounded values and median AND lower decile.\nNorthern / Southern Africa: only 4 / 3 LOO fits. US / NZ: one-country descriptions. Dependent pairwise ARIs are not independent validations.',fontsize=9)
        folder=Path(output_dir)/'figures';folder.mkdir(exist_ok=True)
        path=folder/f'{name}_local_resolution_stability.png'
        fig.savefig(path,dpi=160,bbox_inches='tight');plt.close(fig);paths.append(path)
    return paths
