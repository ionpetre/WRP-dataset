"""Interpret the adaptive confirmation without replacing frozen profiles."""
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score
import adaptive_search as adaptive
import report_results
import search

ROOT = adaptive.ROOT


def main():
    pointer = json.loads((adaptive.BASE / 'current_run.json').read_text())
    output = ROOT / pointer['output']
    assert (output / 'completion.json').exists(), 'Wait for all confirmation fits.'
    if not (output / 'reporting_complete.json').exists():
        report_results.main(output)
    else:
        search.initialize(ROOT, output)
    best = pd.read_csv(output / 'best_tested_setting_per_k.csv')
    baseline = pd.read_csv(output / 'frozen_baselines_on_confirmation_samples.csv')
    pilot = pd.read_csv(output / 'all_pilot_results.csv')
    previous = pd.read_csv(adaptive.PREVIOUS / 'best_tested_setting_per_k.csv')
    weights = search.WEIGHTS
    previous_comparison, overlaps = [], []
    for row in best.loc[best.stability_pass].itertuples():
        labels = joblib.load(output / 'references' / (row.trial + '.joblib'))['labels']
        old = previous.loc[previous.k.eq(row.k)].iloc[0]
        old_labels = joblib.load(adaptive.PREVIOUS / 'references' / (old.trial + '.joblib'))['labels']
        table = pd.crosstab(labels, old_labels, values=weights, aggfunc='sum').fillna(0).to_numpy()
        rr, cc = linear_sum_assignment(-table)
        previous_comparison.append({'model': f'T{row.k}', 'previous_tuned_k': row.k,
            'previous_numerically_qualified': bool(old.stability_pass),
            'previous_q': old.q, 'previous_alpha': old.alpha, 'q': row.q, 'alpha': row.alpha,
            'reference_ARI': adjusted_rand_score(labels, old_labels),
            'matched_weight': float(table[rr, cc].sum()),
            'score_comparison_limit': 'Earlier and new confirmation use different samples; compare reference partitions, not a paired stability gain.'})
        for base in baseline.itertuples():
            base_labels = joblib.load(output / 'references' / (base.trial + '.joblib'))['labels']
            cross = pd.crosstab(labels, base_labels, values=weights, aggfunc='sum').fillna(0)
            for i in cross.index:
                for j in cross.columns:
                    overlaps.append({'model': f'T{row.k}', 'cluster': int(i), 'baseline': base.baseline,
                        'baseline_cluster': int(j), 'joint_equal_country_share': cross.loc[i, j],
                        'share_of_candidate_cluster': cross.loc[i, j] / cross.loc[i].sum(),
                        'share_of_baseline_cluster': cross.loc[i, j] / cross[j].sum()})
    pd.DataFrame(previous_comparison).to_csv(output / 'comparison_with_previous_tuned_models.csv', index=False)
    pd.DataFrame(overlaps).to_csv(output / 'weighted_overlaps_with_frozen_BE.csv', index=False)
    # Put the old explanatory checks beside the new ones without repeating any trees.
    old_folder = ROOT / 'course_artifacts/week04_experiment1_complete_overall_worry_v3/explanatory_fidelity'
    trees = pd.read_csv(old_folder / 'shallow_8ef4c1c5cfd3b7e6/burden_depths_1_2_3_5_summary.csv')
    trees = trees.rename(columns={'balanced_accuracy_mean': 'mean', 'balanced_accuracy_sd': 'std'})
    trees['model'] += trees.k.astype(str)
    pd.concat([pd.read_csv(output / 'burden_tree_summary.csv'), trees[['model', 'depth', 'mean', 'std', 'leaf_capacity_balanced_accuracy_ceiling']]],
              ignore_index=True).to_csv(output / 'burden_tree_summary_with_baselines.csv', index=False)
    rules = pd.read_csv(old_folder / '9f96567a79299de8/one_feature_summary.csv')
    rules = rules.loc[rules.view.eq('separate_20')].copy()
    assert len(rules) == 12
    rules['model'] = rules.model.map({'B': 'B4', 'E': 'E8'})
    rules = rules.rename(columns={'balanced_accuracy_mean': 'balanced_accuracy', 'precision_mean': 'precision',
        'recall_mean': 'recall', 'modal_feature': 'most_selected_feature', 'feature_selected_folds': 'selected_folds'})
    pd.concat([pd.read_csv(output / 'single_feature_summary.csv'),
               rules[['model', 'cluster', 'balanced_accuracy', 'precision', 'recall', 'most_selected_feature', 'selected_folds']]],
              ignore_index=True).to_csv(output / 'single_feature_summary_with_baselines.csv', index=False)
    fig, axes = plt.subplots(2, 4, figsize=(15, 7), sharex=True, sharey=True)
    for k, ax in zip(range(3, 11), axes.flat):
        group = pilot.loc[pilot.k.eq(k)]
        for new, marker, label in [(False, 'o', 'Previous pilot'), (True, '^', 'Adaptive proposal')]:
            is_old = group.origin.eq('previous pilot').fillna(False)
            points = group.loc[(~is_old if new else is_old) & group.status.eq('complete')]
            scatter = ax.scatter(points.q, points.alpha, c=points.score, cmap='RdYlGn', vmin=.5, vmax=1,
                                 marker=marker, s=40 if new else 22, edgecolor='black' if new else 'none',
                                 linewidth=.4, label=label)
        failed = group.loc[~group.structural_pass]
        ax.scatter(failed.q, failed.alpha, marker='x', color='.7', s=15, label='Structural failure')
        ax.set(xlim=(.08, .92), ylim=(.18, .82), title=f'k={k}', xlabel='Middle worry category q', ylabel='Worry allocation alpha')
    axes[0, 0].legend(fontsize=7, loc='lower left')
    fig.colorbar(scatter, ax=axes.ravel().tolist(), label='Pilot minimum lower-decile ARI; not final confirmation')
    fig.savefig(output / 'adaptive_search_surfaces.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    interpretation = [
        'The adaptive search imported 301 earlier settings and evaluated exactly 20 additional pairs for each k, 160 in total. '
        'The two strongest eligible pilots per k were fixed before fresh confirmation; B4/E8 were included unchanged. '
        'No new grid was run and no search bounds, structural filters or ARI thresholds were changed.',
        'The resolutions whose best confirmed setting passes every numerical filter are: ' + ', '.join(str(k) for k in best.loc[best.stability_pass, 'k']) + '. '
        'Other resolutions are reported as best tested but not retained. This bounded search cannot establish that no acceptable setting exists elsewhere.',
    ]
    for row in best.itertuples():
        state = 'passes all numerical filters' if row.stability_pass else 'fails the unchanged stability requirements'
        interpretation.append(f'For k={row.k}, the strongest confirmed setting has q={row.q:.6f}, t={row.t:.6f}, alpha={row.alpha:.6f}; '
            f'lower-decile respondent ARI={row.respondents_p10:.4f}, country ARI={row.countries_p10:.4f}, '
            f'and largest cluster={row.largest:.1%}. It {state}. '
            + ('A selected parameter is on the search boundary; this is not an identified interior optimum.' if row.at_q_boundary or row.at_alpha_boundary else ''))
    compare = pd.read_csv(output / 'comparison_with_frozen_BE.csv')
    explanations = pd.read_csv(output / 'single_feature_summary.csv')
    for k, name in [(4, 'B4'), (8, 'E8')]:
        row = best.loc[best.k.eq(k)].iloc[0]
        base = baseline.loc[baseline.baseline.eq(name)].iloc[0]
        text = f'On the same fresh samples, original {name} has score {base.score:.4f}, compared with {row.score:.4f} for the best confirmed k={k} setting. '
        if row.stability_pass:
            agreement = compare.loc[compare.model.eq(f'T{k}') & compare.baseline.eq(name)].iloc[0]
            text += f'The reference partitions have ARI {agreement.ARI:.4f} and matched equal-country-weighted agreement {agreement.matched_weight:.1%}. '
        interpretation.append(text + 'A stability increase alone does not establish that the new profiles are scientifically preferable.')
    for name, group in explanations.groupby('model'):
        strongest = group.sort_values('balanced_accuracy', ascending=False).iloc[0]
        interpretation.append(f'For {name}, the strongest single-feature reconstruction is cluster {strongest.cluster}, '
            f'usually using {strongest.most_selected_feature} ({strongest.selected_folds}/5 folds): '
            f'balanced accuracy {strongest.balanced_accuracy:.1%}, precision {strongest.precision:.1%}, recall {strongest.recall:.1%}. '
            'Read precision and recall together. This is a diagnostic of existing cluster membership, not a new clustering or an automatic rejection rule.')
    ward_path = output / 'comparison_with_existing_Ward8.csv'
    if ward_path.exists():
        for row in pd.read_csv(ward_path).itertuples():
            interpretation.append(f'{row.model} agrees with the existing Ward8 partition at ARI {row.ARI:.4f}. '
                'Ward was not refitted at the new parameters: this is agreement between existing partitions with possibly different geometries, not a new matched-geometry algorithm validation.')
    interpretation += [
        'Scientific reading of the coarser solutions. T3 is extremely stable, but one of its three groups is almost identified by not worrying about crime '
        '(97.7% balanced accuracy and 92.8% precision). This is a strong feature-dependence concern, not evidence that the numerical tests failed. '
        'T4 is not a small adjustment of B4: their ARI is only .332 and matched weighted agreement is 55.2%. Its four groups distinguish '
        'low food/water worry with more traffic/weather worry (28.6%), broad self/known-person harm exposure (14.7%), generally lower worry '
        'and harm (37.3%), and known-person traffic harm (19.4%). All members of the last group report known-person traffic harm, '
        'but that response also occurs outside the group: rule precision is only 67.4%. It is therefore a necessary marker in this fitted group, '
        'not a unique single-feature definition. The high stability supports this alternative partition; it does not make it the same scientific result as B4.',
        'Newly supported intermediate resolution. T5 passes both full tests at score .9131. Its provisional groups are lower worry (36.3%), '
        'broad known-person harm exposure (13.8%), stronger crime/weather worry (18.5%), stronger mental-health/traffic/weather worry (15.8%), '
        'and stronger water/food worry (15.5%). These descriptions summarize contrasts in the original categories, not final profile names. '
        'Its strongest single-feature rule has 88.3% balanced accuracy, 67.4% precision and 84.3% recall; the depth-2 burden tree has 46.0% balanced accuracy. '
        'It is a useful intermediate-resolution candidate to compare substantively with B/E, not an automatically adopted replacement.',
        'Stability and method agreement do not identify the same winner. The selected adaptive T8 has score .8599, above E8 at .8162 on the same samples, '
        'while retaining a low-worry group, a broad known-person harm group and domain-specific worry combinations. The depth-2 burden tree has only 29.7% balanced accuracy. '
        'However, agreement with existing Ward8 falls to .7399, from approximately .8201 for E8. The earlier grid-selected eight-cluster alternative '
        'had Ward8 ARI .9010 but was not one of the two strongest pilots in this extension, so it was not reconfirmed on the new samples. '
        'There is a real tradeoff between this stability objective, cross-method agreement and profile meaning. Ward uses its original geometry, '
        'so this comparison must not be described as a new matched-geometry test.',
        'Newly supported fine resolution. T9 passes at score .8129, only .0129 above the working threshold. '
        'It includes an additional strongly food-worried group (7.8%). A food-worry rule has recall 99.8% but precision 36.5%: '
        'food worry is shared with other groups and does not uniquely define this cluster. Sampled neighbouring settings have substantially different '
        'partitions and pilot stability. This is not evidence of a broad stable parameter plateau, and a ninth cluster must earn its place through a useful substantive distinction.',
        'Why fresh confirmation matters. For k=5, the highest pilot score (.9332) fell to .6486 and failed, whereas the other shortlisted setting '
        'confirmed at .9131. Likewise, the highest k=8 pilot did not have the strongest confirmation score. '
        'T7 remains exactly the previously selected reference partition (reference ARI 1), despite a changed confirmation score. '
        'Unchanged B4 scored .8559 in the previous confirmation and .9145 here. Different resampling draws and initialization seeds can materially '
        'change these finite-repetition summaries. Compare B/E and tuned models within the same confirmation batch; '
        'do not interpret a score change across batches as a change in the frozen model or an improvement caused by tuning.'
    ]
    interpretation += [
        'Neighbourhood evidence is descriptive. The saved table contains the nearest already tested parameter settings, their pilot stability and their reference ARI to the selected partition. '
        'It is not a complete local surface or a new automatic plateau threshold. Different k can have different geometries; comparisons are approximate refinements, not a strict lattice.',
        'Decision: retain original B4/E8 as frozen references until explicit scientific review. Numerical eligibility is necessary under this protocol, not sufficient for adoption. '
        'Review profile meaning in original response units, single-feature dependence and nearby settings before changing downstream assignments. '
        'Do not select k solely by the highest stability score or treat the tuned worry coding as an estimated psychological scale.',
        'Limitations: these are the same development countries; fresh resampling is not independent external-country validation. '
        'Earlier held-out findings were already known. Pairwise ARIs share fitted partitions and are not independent observations. '
        'Comparisons with earlier tuning scores use different confirmation samples, except where the unchanged B/E benchmarks were explicitly rerun on the new common samples. '
        'Frozen models, respondent IDs, handoff assignments, held-out results, maps, Week 6 and the manuscript remain unchanged.'
    ]
    (output / 'interpretation.txt').write_text('\n\n'.join(interpretation) + '\n')
    adaptive.save_json(output / 'adaptive_reporting_complete.json', {'status': 'completed',
        'all_source_results_preserved': True, 'no_frozen_models_replaced': True})
    print('Adaptive reporting completed:', output, flush=True)


if __name__ == '__main__':
    main()
