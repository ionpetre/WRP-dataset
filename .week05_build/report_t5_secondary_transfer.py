"""Report the completed T5 transfer. Never fit, tune or repeat assignment."""
from pathlib import Path
import json
import shutil
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from t5_secondary_transfer import ROOT, BASE, save, sha, verify_seal


def main():
    pointer = json.loads((BASE / 'current_run.json').read_text())
    output = ROOT / pointer['output']
    package = output / 'frozen_model'
    verify_seal(package)
    # The first run completed every scientific calculation, but its last console
    # line failed because a merge had suffixed the two descriptive scope columns.
    # Repair column names only, retain the original table and the incident record.
    path = output / 'heldout_frozen_anchor_comparison.csv'
    anchors = pd.read_csv(path)
    if 'scope_y' in anchors:
        shutil.copy2(path, output / 'heldout_frozen_anchor_comparison_before_scope_column_repair.csv')
        assert anchors.scope_x.eq('global').all()
        anchors = anchors.drop(columns=['scope_x', 'area_id_x', 'area_name_x']).rename(
            columns={'scope_y': 'scope', 'area_id_y': 'area_id', 'area_name_y': 'area_name'})
        anchors.to_csv(path, index=False)
        save(output / 'reporting_incident.json', {
            'incident': 'final console summary raised AttributeError on scope after completed transfer was saved',
            'cause': 'development and held-out scope columns had merge suffixes',
            'repair': 'drop development scope columns; rename held-out scope columns; preserve original CSV',
            'scientific_values_changed': False, 'assignments_or_models_changed': False,
            'additional_clustering_or_transfer_runs': 0,
            'executed_source': 'executed_transfer_implementation.py'})
        record = json.loads((output / 'transfer_complete.json').read_text())
        record['files'][path.name] = sha(path)
        for name in ['heldout_frozen_anchor_comparison_before_scope_column_repair.csv',
                     'reporting_incident.json', 'executed_transfer_implementation.py']:
            record['files'][name] = sha(output / name)
        save(output / 'transfer_complete.json', record)
    shares = pd.read_csv(output / 'heldout_vs_development_prevalence.csv').sort_values('cluster')
    semantic = pd.read_csv(output / 'heldout_profile_semantic_differences.csv')
    global_semantic = semantic.loc[semantic.scope.eq('global')].sort_values('cluster')
    quality = pd.read_csv(output / 'heldout_vs_development_quality.csv')
    country = pd.read_csv(output / 'heldout_country_quality_and_retention.csv')
    intervals = pd.read_csv(output / 'heldout_country_bootstrap_intervals.csv')
    ci = intervals.loc[intervals.quantity.eq('profile_share')].sort_values('cluster')
    spec = json.loads((package / 'specification.json').read_text())
    names = {int(c): name for c, name in spec['profile_names'].items()}
    display_names = ['Lower worry', 'Broad known-person harm', 'Crime/weather worry',
                     'Mental-health/traffic/weather worry', 'Water/food worry']
    summary = shares[['cluster', 'equal_country_weighted_share_development', 'equal_country_weighted_share_heldout',
                      'prevalence_difference_pp', 'respondents']].merge(
        ci[['cluster', 'p025', 'p975']], on='cluster', validate='one_to_one').merge(
        global_semantic[['cluster', 'mean_feature_total_variation', 'maximum_feature_total_variation']],
        on='cluster', validate='one_to_one')
    summary['profile_name'] = summary.cluster.map(names)
    summary.to_csv(output / 'profile_transfer_summary.csv', index=False)
    fig, ax = plt.subplots(figsize=(10, 4.5))
    y = np.arange(5)
    ax.barh(y + .17, 100 * summary.equal_country_weighted_share_development, .3, label='Development', color='#4477aa')
    ax.barh(y - .17, 100 * summary.equal_country_weighted_share_heldout, .3, label='Held-out countries (secondary assessment)', color='#ee9944')
    ax.errorbar(100 * summary.equal_country_weighted_share_heldout, y - .17,
        xerr=100 * np.array([summary.equal_country_weighted_share_heldout - summary.p025,
                             summary.p975 - summary.equal_country_weighted_share_heldout]),
        fmt='none', color='#333333', capsize=3)
    ax.set(yticks=y, yticklabels=display_names, xlabel='Equal-country-weighted prevalence (%)', xlim=(0, 50))
    ax.invert_yaxis()
    ax.legend(loc='lower right', fontsize=8)
    fig.suptitle('T5: fixed development profiles retain similar held-out prevalence', fontsize=12)
    fig.text(.5, .015, 'Intervals: 1,000 country bootstrap draws, fixed model; not fitting uncertainty or an untouched validation.',
             ha='center', fontsize=8)
    fig.tight_layout(rect=(0, .04, 1, .95))
    fig.savefig(output / 't5_prevalence_transfer.png', dpi=160)
    plt.close(fig)
    dev = pd.read_csv(package / 'development_original_category_profiles.csv')
    held = pd.read_csv(output / 'heldout_original_category_profiles.csv')
    features = spec['feature_order']
    feature_names = [f.replace('worry_', '').replace('harm_', '').replace('_known_person', ' (known)').replace('_personal', ' (respondent)').replace('_', ' ') for f in features]
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.7), sharey=True)
    for ax, table, title in zip(axes, [dev, held], ['Development: stored reference', 'Held-out: unchanged centroid assignment']):
        table = table.loc[table.scope.eq('global') & np.where(table.feature.str.startswith('worry_'), table.category.eq(2), table.category.eq(1))]
        matrix = table.pivot(index='cluster', columns='feature', values='proportion').reindex(index=range(5), columns=features)
        image = ax.imshow(100 * matrix, vmin=0, vmax=100, cmap='YlGnBu', aspect='auto')
        ax.set(xticks=range(20), xticklabels=feature_names, yticks=range(5), yticklabels=display_names, title=title)
        ax.tick_params(axis='x', rotation=90, labelsize=7)
        ax.axvline(5.5, color='white'); ax.axvline(12.5, color='white')
    fig.subplots_adjust(left=.24, right=.9, bottom=.36, top=.84, wspace=.06)
    fig.colorbar(image, ax=axes, fraction=.025, pad=.02, label='Very worried / harm prevalence (%)')
    fig.suptitle('T5: original-response meanings remain recognizable', fontsize=13)
    fig.savefig(output / 't5_original_response_transfer.png', dpi=160)
    plt.close(fig)
    all_anchor = anchors.loc[anchors.scope.eq('global')]
    overall = quality.loc[quality.cluster.eq(-1)].iloc[0]
    worst = country.sort_values('profile_p95_exceedance', ascending=False).head(3)
    text = [
        'Decision and scope. T5 is the approved primary model to take forward. The exact development reference is sealed, '
        'not refitted: k=5, q=0.41670089020376244, t=2.399802888616365, alpha=0.5837857862168715. '
        'T5_C0,...,T5_C4 preserve its stored centre order. B4/E8 and every historical result remain available as benchmarks. '
        'The existing maps, manuscript, publication package and Week 6 have not yet been migrated.',
        'Shallow explanations. All five country-grouped folds were used. With the two original-unit burden scores, '
        'depths 1/2/3 achieved mean balanced accuracies 32.7%, 46.0% and 51.2%. '
        'The additional trees supplied with all 20 original features achieved 36.8%, 54.0% and 67.9%; depth 5 reached 73.7%. '
        'At depth 3, broad known-person-harm recall was only 19.3%, despite high recall for lower worry. '
        'These trees capture useful patterns but do not nearly reconstruct the entire typology. '
        'The strongest single-feature rule uses water worry, with balanced accuracy 88.3%, precision 67.4% and recall 84.3%. '
        'This is an informative marker, not a near-unique cluster definition. '
        'A depth-1 multiclass tree has at most two leaves and depth 2 at most four: for five nonempty classes their '
        'balanced-accuracy ceilings are 40% and 80%. Low shallow scores alone therefore cannot prove complexity. '
        'No new automatic rejection cutoff was introduced. Ordinary greedy Gini trees were used; this does not rule out '
        'every possible optimized rule set or establish that the profiles are natural latent types. The fixed cluster labels '
        'were originally learned using all development countries, so this cross-validation assesses explanatory fidelity, '
        'not fully independent clustering generalization.',
        'Transfer population. Apply the sealed centres to 27,972 complete respondents from all 29 held-out countries. '
        'The other 2,118 of 30,090 respondents remain unassigned because of missing profile responses. '
        'A separate ID-linked T5 handoff includes all 146,910 prepared respondents: 137,460 assigned and 9,450 excluded. '
        'Do not fill excluded labels, join by row order, or substitute T5 cluster numbers into B/E columns.',
        'Prevalence. Development to held-out equal-country shares are: ' + '; '.join(
            f'{names[int(r.cluster)]} {r.equal_country_weighted_share_development:.1%} to {r.equal_country_weighted_share_heldout:.1%}'
            for r in summary.itertuples()) + '. Different prevalence is allowed and was not used to retune the model.',
        f'Profile identity. All {int(all_anchor.heldout_contrast_direction_preserved.sum())}/15 development-selected anchor directions remain positive in aggregate held-out data. '
        f'Mean feature total variation within profiles ranges from {global_semantic.mean_feature_total_variation.min():.4f} to '
        f'{global_semantic.mean_feature_total_variation.max():.4f}; the largest single-feature difference is '
        f'{global_semantic.maximum_feature_total_variation.max():.4f}. This measures original-category distribution shifts, '
        'not centroid distances, ARI, or a newly defined pass/fail score. Semantic retention partly follows from assigning '
        'people using these same features; it supports portability of this fixed description, not independent discovery of the same groups.',
        f'Assignment quality. Overall median distance changes by a factor {overall.distance_median_ratio:.4f}; '
        f'median assignment margin changes from {overall.margin_median_development:.4f} to {overall.margin_median_heldout:.4f}. '
        f'The fraction beyond the assigned-profile development distance p95 changes from '
        f'{overall.profile_p95_exceedance_development:.2%} to {overall.profile_p95_exceedance_heldout:.2%}. '
        'Flags identify less typical assigned responses, not unassigned cases, misclassification probabilities or an overall rejection rule.',
        'Country limitations. The largest distance-flag fractions are ' + '; '.join(
            f'{r.Country} {r.profile_p95_exceedance:.1%} (complete-response retention {r.retained_fraction:.1%})'
            for r in worst.itertuples()) + '. Global averages conceal these weaknesses. Country/profile tables include respondent counts '
        'and Kish weighted effective sizes; very small groups have uncertain conditional descriptions. '
        'For example, Sweden\'s water/food group contains only 15 respondents (Kish effective size 9.8), '
        'so its mean feature total variation of .200 is poorly estimated. Somalia\'s water/food group has '
        'mean feature total variation .225 with 173 respondents (effective size 138.8): this is a substantive '
        'country-specific shift that cannot simply be dismissed as a 15-person group. These examples qualify '
        'any claim that all five profile meanings reproduce equally well in every country. '
        'Complete-case selection may change apparent country profiles; the assessment does not establish representativeness '
        'of respondents excluded for missing answers.',
        'Uncertainty and conclusion. The 1,000 country bootstrap intervals keep the model fixed and preserve relative '
        'survey weights within each sampled country. They describe variation over these 29 observed countries, not '
        'all-world sampling, respondent nonresponse, model fitting or parameter-selection uncertainty. '
        'The results support broad aggregate descriptive transfer of T5, with material country-specific qualifications. '
        'No automatic numerical transfer criterion had been specified; this is an analytical synthesis using the same '
        'diagnostic framework as the earlier B/E assessment. The held-out countries were previously examined for B/E '
        'and the new search was undertaken after those results were known. This must be reported as secondary transfer '
        'assessment, not pristine external confirmation. No new local-region clustering, independent held-out clustering '
        'or all-data refit was performed. T8 remains exploratory, not a co-equal main model.'
    ]
    (output / 'interpretation.txt').write_text('\n\n'.join(text) + '\n')
    save(output / 'primary_model_decision.json', {'primary_model': 'T5', 'context': pointer['context'],
        'conclusion': 'broad aggregate descriptive transfer, qualified by country and complete-case limitations',
        'secondary_not_untouched_validation': True, 'profile_ids': [f'T5_C{c}' for c in range(5)],
        'historical_models': ['B4', 'E8', 'other evaluated models'], 'fine_resolution': 'T8 exploratory only',
        'operational_downstream_migration': 'pending; no Week 6, map, paper or publication replacement in this task'})
    save(output / 'reporting_complete.json', {'status': 'complete', 'no_refits_or_repeat_transfer': True,
        'files': {p.name: sha(p) for p in output.iterdir() if p.is_file() and p.name not in ['transfer_complete.json', 'reporting_complete.json', 'verification.json', 'notebook_verification.json']}})
    print(summary.round(4).to_string(index=False))
    return output


if __name__ == '__main__':
    main()
