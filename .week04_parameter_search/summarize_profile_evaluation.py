"""Make original-unit figures and a critical review of cached profile evidence."""
import json
import os
from pathlib import Path
import numpy as np
import pandas as pd
os.environ.setdefault('MPLCONFIGDIR', '/private/tmp/wrp-profile-evaluation-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import evaluate_profiles as evaluation
import search

ROOT = evaluation.ROOT
output = ROOT / json.loads((evaluation.BASE / 'current_run.json').read_text())['output']
assert (output / 'completion.json').exists() and (output / 'reference_diagnostic_verification.json').exists()
registry = json.loads((output / 'model_registry.json').read_text())
summary = pd.read_csv(output / 'profile_summaries.csv')
profiles = pd.read_csv(output / 'original_category_profiles.csv')
stability = pd.read_csv(output / 'cluster_stability_summary.csv')
overview = pd.read_csv(output / 'model_evaluation_overview.csv')
representative = pd.read_csv(output / 'reference_representativeness.csv')
inertia = pd.read_csv(output / 'reference_inertia_diagnostic.csv')
pairs = pd.read_csv(output / 'partition_comparisons.csv')
overlaps = pd.read_csv(output / 'partition_overlaps.csv')
parents = pd.read_csv(output / 'largest_overlap_source_comparisons.csv')
differences = pd.read_csv(output / 'original_unit_added_distinctions.csv')
names = {
    'T3': ['Food/water worry', 'Lower food/water worry, more crime worry', 'Not worried about crime'],
    'B4': ['Broad harm exposure', 'Crime/weather/traffic worry', 'Food/water worry', 'Lower worry and harm'],
    'T4': ['Low food/water worry, more traffic/weather worry', 'Broad self/known-person harm',
           'Lower traffic/weather/mental-health worry', 'Known-person traffic harm'],
    'T5': ['Lower worry', 'Broad known-person harm', 'Crime/weather worry',
           'Mental-health/traffic/weather worry', 'Water/food worry'],
    'T6': ['Traffic worry', 'Water/food worry', 'Severe-weather worry', 'Lower worry', 'Mental-health worry', 'Crime worry'],
    'T7': ['Severe-weather worry', 'Crime worry', 'Traffic worry', 'Mental-health worry',
           'Water/food worry', 'Broad known-person harm', 'Lower worry'],
    'E8': ['Traffic-focused worry', 'Lower worry intensity', 'Mental-health and other worries', 'Crime/traffic worry',
           'Crime-focused worry', 'Severe-weather-focused worry', 'Food/water worry', 'Broad high worry'],
    'T8': ['Mental-health plus water/food worry', 'Traffic worry', 'Mental-health/traffic/weather worry',
           'Lower worry', 'Broad known-person harm', 'Severe-weather worry', 'Water/food worry', 'Crime worry'],
    'T9': ['Mental-health/traffic/weather worry', 'Lower worry', 'Broad known-person harm', 'Crime worry',
           'Severe-weather worry', 'Water/food worry', 'Traffic worry', 'Mental-health plus water/food worry', 'Food worry'],
}
summary['description'] = [names[row.model][row.cluster] for row in summary.itertuples()]
summary['description_status'] = 'provisional descriptive shorthand; not new frozen profile names or IDs'
summary.to_csv(output / 'profile_review_cards.csv', index=False)
order = [(row.model, row.cluster) for row in summary.itertuples()]
index = pd.MultiIndex.from_tuples(order, names=['model', 'cluster'])
labels = [f'{row.model} C{row.cluster}  |  {row.weighted_share:.1%}' for row in summary.itertuples()]
boundaries = np.cumsum([r['k'] for r in registry])[:-1] - .5


def separate_models(ax):
    for line in boundaries:
        ax.axhline(line, color='.65', linewidth=.6)


def category_matrix(features, category):
    values = profiles.loc[profiles.feature.isin(features) & profiles.category.eq(category)]
    return values.pivot(index=['model', 'cluster'], columns='feature', values='proportion').reindex(index=index, columns=features).to_numpy()


# A common 0-100% scale: very-worried prevalence and personal/known-person harm.
matrix = np.column_stack([category_matrix(search.WORRY, 2), category_matrix(search.SELF, 1), category_matrix(search.KNOWN, 1)])
fig, ax = plt.subplots(figsize=(17, 17), layout='constrained')
image = ax.imshow(matrix, vmin=0, vmax=1, cmap='Blues', aspect='auto')
ax.set_yticks(range(len(labels)), labels, fontsize=8)
domains = ['Food', 'Water', 'Crime', 'Weather', 'Traffic', 'Mental health']
xlabels = [d + '\nVery worried' for d in domains]
xlabels += [d + '\nRespondent harm' for d in domains + ['Work']]
xlabels += [d + '\nKnown-person harm' for d in domains + ['Work']]
ax.set_xticks(range(20), xlabels, rotation=90, fontsize=8)
ax.axvline(5.5, color='.3', linewidth=1)
ax.axvline(12.5, color='.3', linewidth=1)
separate_models(ax)
ax.set_title('Profile meanings in original responses\nEqual-country-weighted within-profile prevalence; row labels show profile share', fontsize=14)
fig.colorbar(image, ax=ax, shrink=.45, label='Proportion (0 = 0%; 1 = 100%)')
fig.savefig(output / 'original_unit_profile_heatmap.png', dpi=150)
plt.close(fig)

# All three worry categories are shown, not just the very-worried response.
fig, axes = plt.subplots(1, 6, figsize=(16, 17), sharey=True, layout='constrained')
colors = ['#d8dce1', '#d8a73a', '#326c9b']
for j, ax in enumerate(axes):
    left = np.zeros(len(order))
    for c in range(3):
        value = category_matrix(search.WORRY, c)[:, j]
        ax.barh(np.arange(len(order)), value, left=left, color=colors[c], height=.85)
        left += value
    ax.set(title=domains[j], xlim=(0, 1), ylim=(len(order) - .5, -.5))
    ax.set_xticks([0, .5, 1], ['0%', '50%', '100%'])
    separate_models(ax)
axes[0].set_yticks(range(len(labels)), labels, fontsize=8)
fig.suptitle('Original worry-category distributions within each profile', fontsize=14)
fig.legend(handles=[Patch(color=c, label=name) for c, name in zip(colors, ['Not worried', 'Somewhat worried', 'Very worried'])],
           loc='outside lower center', ncol=3)
fig.savefig(output / 'original_worry_category_distributions.png', dpi=150)
plt.close(fig)

# Reference-versus-resample diagnostics: these are NOT the original pairwise ARIs.
metrics = ['jaccard_median', 'jaccard_p10', 'best_any_jaccard_p10', 'precision_p10', 'recall_p10']
metric_names = ['Matched J\nmedian', 'Matched J\nlower decile', 'Best-any J\nlower decile', 'Precision\nlower decile', 'Recall\nlower decile']
fig, axes = plt.subplots(1, 2, figsize=(13, 18), sharey=True, layout='constrained')
for kind, ax in zip(['respondents', 'countries'], axes):
    values = stability.loc[stability.test.eq(kind)].set_index(['model', 'cluster']).reindex(index)[metrics].to_numpy()
    image = ax.imshow(values, vmin=0, vmax=1, cmap='Blues', aspect='auto')
    for i in range(len(order)):
        for j in range(len(metrics)):
            ax.text(j, i, f'{values[i, j]:.2f}', ha='center', va='center', fontsize=7,
                    color='white' if values[i, j] > .62 else 'black')
    ax.set_xticks(range(len(metrics)), metric_names, fontsize=9)
    ax.set_title(kind.capitalize() + ': 50 cached repetitions')
    separate_models(ax)
axes[0].set_yticks(range(len(labels)), labels, fontsize=8)
fig.suptitle('Recovery of each fixed reference profile\nNo new cutoff: matched Jaccard and best-any Jaccard answer different matching questions', fontsize=13)
fig.colorbar(image, ax=axes, shrink=.3, label='Membership overlap or recovery (0–1)')
fig.savefig(output / 'individual_profile_stability.png', dpi=150)
plt.close(fig)

focus = [('B4', 'T4'), ('B4', 'T5'), ('B4', 'E8'), ('T5', 'T7'), ('T5', 'T8'), ('T5', 'T9'),
         ('T7', 'T8'), ('E8', 'T8'), ('T8', 'T9')]
fig, axes = plt.subplots(3, 3, figsize=(15, 13), layout='constrained')
for (a, b), ax in zip(focus, axes.flat):
    table = overlaps.loc[overlaps.source.eq(a) & overlaps.target.eq(b)].pivot(index='source_cluster', columns='target_cluster', values='share_of_target')
    image = ax.imshow(table, vmin=0, vmax=1, cmap='Blues', aspect='auto')
    for i in range(len(table.index)):
        for j in range(len(table.columns)):
            value = table.iloc[i, j]
            ax.text(j, i, f'{value:.0%}', ha='center', va='center', fontsize=7,
                    color='white' if value > .62 else 'black')
    ax.set(title=a + ' → ' + b, xlabel='Target cluster', ylabel='Source cluster')
    ax.set_xticks(range(len(table.columns)), table.columns)
    ax.set_yticks(range(len(table.index)), table.index)
fig.suptitle('Where each target profile comes from\nEach column sums to 100%; different geometries mean these are not necessarily nested splits', fontsize=14)
fig.colorbar(image, ax=axes, shrink=.4, label='Share of target profile belonging to source profile')
fig.savefig(output / 'cross_resolution_membership_overlaps.png', dpi=150)
plt.close(fig)

added = []
for a, b in focus:
    for row in parents.loc[parents.source.eq(a) & parents.target.eq(b)].itertuples():
        changes = differences.loc[differences.source.eq(a) & differences.target.eq(b) & differences.target_cluster.eq(row.target_cluster)].copy()
        changes['absolute_difference'] = changes.difference.abs()
        anchors = changes.sort_values('absolute_difference', ascending=False).drop_duplicates('feature').head(4)
        text = '; '.join(f'{r.feature} category {r.category}: {r.target_proportion:.1%} vs {r.source_proportion:.1%}' for r in anchors.itertuples())
        added.append({'source': a, 'target': b, 'target_cluster': row.target_cluster,
            'target_description': names[b][row.target_cluster], 'target_share': row.target_share,
            'largest_overlap_source_cluster': row.largest_overlap_source_cluster,
            'share_from_largest_source': row.share_from_largest_source,
            'has_single_majority_source': row.share_from_largest_source > .5,
            'worry_mean_feature_TV': row.worry_mean_feature_TV,
            'personal_harm_mean_feature_TV': row.personal_harm_mean_feature_TV,
            'known_person_harm_mean_feature_TV': row.known_person_harm_mean_feature_TV,
            'original_unit_changes': text,
            'limit': 'largest-overlap comparison only; no new eligibility threshold or strict parent-child claim'})
pd.DataFrame(added).to_csv(output / 'added_profile_review.csv', index=False)
review = overview.copy()
for kind in ['respondents', 'countries']:
    worst_any = stability.loc[stability.test.eq(kind)].groupby('model').best_any_jaccard_p10.min()
    review[kind + '_minimum_best_any_jaccard_p10'] = review.model.map(worst_any)
review['cached_centres_with_lower_full_objective'] = review.model.map(inertia.groupby('model').cached_centres_better_than_reference.sum())
review.to_csv(output / 'model_review_summary.csv', index=False)

paragraphs = [
    'Scope: compare the seven numerically eligible adaptive selections with unchanged B4/E8. These are nine fixed reference partitions and 54 profiles. '
    'All 900 existing confirmation fits are reused. No K-means, explanatory classifier, Ward, geographic or held-out model is fitted. '
    'The original ARI/structural requirements remain unchanged; no Jaccard rejection threshold is introduced.',
    'Meaning of the new diagnostic: after one-to-one maximum-overlap label matching, precision measures how much of the matched resampled group comes from '
    'the reference group; recall measures how much of the reference group remains in that matched group. Weighted Jaccard is their intersection mass divided '
    'by union mass. The weights are the fixed full-development equal-country weights. Each test has 50 reference-versus-resample values per cluster, '
    'not 1,225 independent values. The best-any Jaccard allows every reference profile to select its own best-matching resampled group without a one-to-one '
    'constraint. It diagnoses whether an apparent weakness is caused by the global assignment; it can map several reference groups to the same resampled group '
    'and therefore does not establish that all profiles remain distinct.',
]
for row in review.itertuples():
    paragraphs.append(f'{row.model}: minimum cluster lower-decile matched Jaccard is '
        f'{row.respondents_min_cluster_jaccard_p10:.3f} in the respondent test and {row.countries_min_cluster_jaccard_p10:.3f} in the country test. '
        f'With best-any matching, the corresponding minimum cluster lower deciles are '
        f'{row.respondents_minimum_best_any_jaccard_p10:.3f} and {row.countries_minimum_best_any_jaccard_p10:.3f}. '
        f'{row.cached_centres_with_lower_full_objective}/100 cached sets of centres have lower full-population inertia than the reference, '
        'comparing only identical geometry and weights within this model.')
paragraphs += [
    'Substantive comparison: T3 is very reproducible, but its no-crime-worry group is almost reconstructed by that single response '
    '(balanced accuracy 97.7%, precision 92.8%). Its high stability does not by itself make it an informative multidomain solution. '
    'B4, T4 and T5 recover all their reference profiles much more consistently than the finer models. T4 is a different family from B4 '
    '(ARI .332), with a broad-harm group and a known-person traffic-harm group. The latter has a necessary traffic-harm marker but only 67.4% '
    'single-feature precision, so it is not uniquely defined by that feature.',
    'T5 is a particularly useful intermediate candidate: lower worry (36.3%), broad known-person harm (13.8%), stronger crime/weather worry (18.5%), '
    'stronger mental-health/traffic/weather worry (15.8%), and stronger water/food worry (15.5%). Its minimum cluster lower-decile Jaccard is '
    'about .957 for respondent resampling and .943 for country resampling. The strongest single-feature rule is less reconstructive than T3: '
    'balanced accuracy 88.3%, precision 67.4%, recall 84.3%. Its depth-2 burden tree has only 46.0% balanced accuracy. '
    'This supports substantive review of T5 as an alternative, not automatic replacement of the frozen models.',
    'Fine-resolution caution: T6 and T7 pass the original pairwise-ARI requirements, yet their crime/weather distinctions do not consistently recover '
    'the fixed reference groups. In T7, country-resampled partitions have median pairwise ARI .985, while their median ARI to the saved full-data '
    'reference is only .876. Thus the saved reference is less representative of the resampling ensemble than a pairwise summary alone suggests. '
    'The selected within-test medoids are diagnostics only; they have not replaced any reference partition.',
    'E8 has a specific weakness in its crime-and-traffic group (8.1% equal-country prevalence). Lower-decile matched Jaccard is only .085/.087 '
    'in the respondent/country tests. Part of this extreme value comes from the one-to-one matching constraint: best-any lower deciles are '
    'about .414/.414, still far from complete recovery. The group and its boundary with other crime/traffic profiles are less secure than the '
    'overall ARI suggests. This qualifies the robustness claim for that fine distinction; it does not erase all useful E8 structure or invalidate '
    'the already frozen held-out assignments.',
    'T8 is the more promising fine-resolution alternative in this review, but it is not uniformly stable. Most reference groups have very high '
    'median overlap. Weather/crime boundaries occasionally change: minimum cluster lower-decile Jaccard is .524/.471 in the two tests. '
    'The low-worry, broad-harm and several other profile distinctions recover much more consistently. Report the reliable backbone and these '
    'sensitive boundaries separately, rather than describing all eight profiles as equally robust.',
    'The ninth profile is not supported as a consistently recovered fixed group. T9 passes overall ARI, but its added food-worry group (7.8%) '
    'has median matched Jaccard about .089. Even best-any lower-decile Jaccard is only about .086 in each test. This is not merely a label '
    'permutation problem. Although 99.8% of its reference members are very worried about food, that category purity does not establish '
    'reproducible joint cluster membership. Treat the ninth distinction as exploratory and fragile, not a validated extra profile.',
    'What the saved objective values show: some resampled sets of centres outperform the full-data reference on the same full-population weighted '
    'K-means objective. This occurs for 57/100 E8 fits, 57/100 T6 fits, 88/100 T7 fits and 32/100 T9 fits; the largest relative reductions are '
    'small (roughly .06%–.18%) but can accompany substantial membership changes. This directly demonstrates that these references are not the '
    'lowest-inertia solutions among the saved centres. It is consistent with competing near-optimal solutions and initialization sensitivity; '
    'it does not prove a unique global optimum, nor make the lower-inertia partition scientifically correct. No analogous improvement is found '
    'among the 100 saved fits for B4, T3, T4, T5 or T8. Raw inertia is never used to rank different geometries.',
    'Additional clusters are not automatically nested splits. T8 and T9 have ARI .870 and 91.6% aggregate largest-source overlap, but only about '
    '23.5% of the T9 food group comes from its largest single T8 source group. It cuts across existing groups rather than splitting just one. '
    'Likewise, T5-to-T8 aggregate purity is about 82.5%, but one fine group has no majority T5 source. '
    'Use the complete overlap table and original-response differences, not a strict lattice or a simple finer-is-better narrative.',
    'Current decision: keep B4/E8 and all downstream assignments unchanged. B4 remains a defensible coarse benchmark. T4 and especially T5 merit '
    'substantive comparison as alternative coarse/intermediate descriptions. T8 merits review as a fine-resolution alternative with explicit '
    'uncertainty around particular boundaries. T6/T7 reference representativeness and the T9 extra group require caution before adoption. '
    'Ward agreement is not used as a selection requirement in this round. No numerical eligibility rule was changed after seeing these results.',
    'Limits: this is a post-search development-only assessment, not an independent replication or a new held-out validation. Matching is based '
    'on a fixed reference and can be affected by merges/splits; best-any matching and reference-representativeness diagnostics are provided '
    'to expose that limitation. The within-test ARI medoid is only the most representative cached fit under that particular ARI criterion. '
    'These summaries do not separate all sources of sampling and solver variability, and no new cluster is frozen.'
]
(output / 'interpretation.txt').write_text('\n\n'.join(paragraphs) + '\n')
evaluation.save_json(output / 'reporting_complete.json', {'status': 'completed', 'figures': 4,
    'no_new_fits': True, 'Ward_not_used_as_selection_criterion': True,
    'report_code_sha256': evaluation.file_hash(__file__)})
print('Saved figures and critical interpretation:', output, flush=True)
