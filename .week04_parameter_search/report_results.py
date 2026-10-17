"""Interpret completed development tuning; do not adopt new frozen models."""
from pathlib import Path
from itertools import combinations
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score, balanced_accuracy_score, precision_score, recall_score
from sklearn.model_selection import GroupKFold
from sklearn.tree import DecisionTreeClassifier
from threadpoolctl import threadpool_limits
import search

ROOT = Path(__file__).resolve().parents[1]


def explain_labels(data, labels, name):
    weights = search.country_weights(data)
    features = search.FEATURES
    scores = np.column_stack([data[search.WORRY].mean(axis=1), data[search.HARM].mean(axis=1)])
    rule_rows, tree_rows = [], []
    cv = GroupKFold(n_splits=5)
    for fold, (train, test) in enumerate(cv.split(data, groups=data.COUNTRY_ISO3), 1):
        train_weight = search.country_weights(data.iloc[train])
        test_weight = search.country_weights(data.iloc[test])
        for depth in [1, 2, 3, 5]:
            tree = DecisionTreeClassifier(max_depth=depth, min_samples_leaf=200, random_state=2023)
            tree.fit(scores[train], labels[train], sample_weight=train_weight)
            predicted = tree.predict(scores[test])
            tree_rows.append({'model': name, 'fold': fold, 'depth': depth,
                              'balanced_accuracy': balanced_accuracy_score(labels[test], predicted, sample_weight=test_weight)})
        for cluster in np.unique(labels):
            target = labels == cluster
            best_score, best = -np.inf, None
            for feature in features:
                x = data[feature].to_numpy(float)
                categories = np.unique(x[train])
                for threshold in (categories[:-1] + categories[1:]) / 2:
                    for above in [True, False]:
                        predicted = x[train] > threshold if above else x[train] <= threshold
                        score = balanced_accuracy_score(target[train], predicted, sample_weight=train_weight)
                        if score > best_score:
                            best_score, best = score, (feature, threshold, above)
            feature, threshold, above = best
            x = data[feature].to_numpy(float)
            predicted = x[test] > threshold if above else x[test] <= threshold
            rule_rows.append({'model': name, 'fold': fold, 'cluster': int(cluster), 'feature': feature,
                              'threshold': threshold, 'above': above,
                              'balanced_accuracy': balanced_accuracy_score(target[test], predicted, sample_weight=test_weight),
                              'precision': precision_score(target[test], predicted, sample_weight=test_weight, zero_division=np.nan),
                              'recall': recall_score(target[test], predicted, sample_weight=test_weight, zero_division=np.nan)})
    return pd.DataFrame(rule_rows), pd.DataFrame(tree_rows)


def main(output=None):
    if output is None:
        current = json.loads((ROOT / 'course_artifacts/week04_kmeans_parameter_optimization/current_run.json').read_text())
        output = ROOT / current['output']
    output = Path(output)
    assert (output / 'completion.json').exists(), 'Wait for the full confirmation to finish.'
    search.initialize(ROOT, output)
    data, weights = search.DATA, search.WEIGHTS
    pilot = pd.read_csv(output / 'all_pilot_results.csv')
    confirmed = pd.read_csv(output / 'full_confirmation_results.csv')
    rows = []
    for k in range(3, 11):
        group = confirmed.loc[confirmed.k.eq(k)]
        ranked = search.rank_settings(group)
        if ranked.empty:
            rows.append({'k': k, 'selection_status': 'no completed structurally eligible confirmation', 'stability_pass': False})
        else:
            row = ranked.iloc[0].to_dict()
            row['selection_status'] = 'passes all numerical filters' if row['stability_pass'] else 'best tested, but fails stability threshold'
            rows.append(row)
    best = pd.DataFrame(rows)
    best['at_q_boundary'] = np.isclose(best.q, .1) | np.isclose(best.q, .9)
    best['at_alpha_boundary'] = np.isclose(best.alpha, .2) | np.isclose(best.alpha, .8)
    best.to_csv(output / 'best_tested_setting_per_k.csv', index=False)
    baselines = []
    for name, k, q, alpha in [('B4', 4, .5, .5), ('E8', 8, 1 / 3, .75)]:
        row = confirmed.loc[confirmed.k.eq(k) & np.isclose(confirmed.q, q) & np.isclose(confirmed.alpha, alpha)].iloc[0].to_dict()
        row['baseline'] = name
        baselines.append(row)
    pd.DataFrame(baselines).to_csv(output / 'frozen_baselines_on_confirmation_samples.csv', index=False)
    profiles, interpretations, baseline_rows, neighbours, all_rules, all_trees = [], [], [], [], [], []
    ward_comparison, exact_specs, selected_labels = [], [], {}
    original = ROOT / 'course_artifacts/week04_experiment1_complete_overall_worry_v3'
    baseline_labels = {'B4': joblib.load(original / 'reference_012_balanced_k4.joblib')['labels'],
                       'E8': joblib.load(original / 'reference_013_worry_emphasized_k8.joblib')['labels']}
    for result in best.loc[best.stability_pass].itertuples():
        name = f'T{result.k}'
        reference = joblib.load(output / 'references' / (result.trial + '.joblib'))
        exact_specs.append({'model': name, 'trial': result.trial, 'q': reference['q'],
                            't': 1 / reference['q'], 'alpha': reference['alpha'], 'k': reference['k'],
                            'fingerprint': reference['fingerprint'], 'status': 'provisional, not frozen'})
        labels = reference['labels']
        selected_labels[name] = labels
        for cluster in range(result.k):
            inside = labels == cluster
            cluster_rows = []
            for feature in search.FEATURES:
                for category in range(3 if feature in search.WORRY else 2):
                    value = data[feature].to_numpy() == category
                    p = float(np.average(value[inside], weights=weights[inside]))
                    outside = float(np.average(value[~inside], weights=weights[~inside]))
                    row = {'model': name, 'trial': result.trial, 'q': result.q, 'alpha': result.alpha,
                           'k': result.k, 'cluster': cluster,
                           'cluster_share': float(weights[inside].sum()), 'feature': feature,
                           'category': category, 'proportion': p, 'outside_proportion': outside,
                           'difference': p - outside}
                    profiles.append(row)
                    cluster_rows.append(row)
            ranked = sorted(cluster_rows, key=lambda row: -row['difference'])[:3]
            anchors = []
            for row in ranked:
                category = ['not worried', 'somewhat worried', 'very worried'][row['category']] if row['feature'] in search.WORRY else ['no harm', 'harm'][row['category']]
                anchors.append(f"{row['feature']}: {category}, {row['proportion']:.1%} (outside {row['outside_proportion']:.1%})")
            interpretations.append({'model': name, 'trial': result.trial, 'q': result.q, 'alpha': result.alpha, 'cluster': cluster,
                'share': float(weights[inside].sum()), 'respondents': int(inside.sum()),
                'contrasts': '; '.join(anchors), 'naming_status': 'descriptive contrasts, not frozen profile names'})
        for baseline, base in baseline_labels.items():
            table = pd.crosstab(labels, base, values=weights, aggfunc='sum').fillna(0).to_numpy()
            rr, cc = linear_sum_assignment(-table)
            baseline_rows.append({'model': name, 'baseline': baseline, 'ARI': adjusted_rand_score(labels, base),
                                  'matched_weight': float(table[rr, cc].sum()) if table.shape[0] == table.shape[1] else np.nan})
        if result.k in [7, 8]:
            ward_cache = joblib.load(ROOT / 'course_artifacts/week04_other_algorithms_v1/references.joblib')
            ward = ward_cache['results'][170]['labels']
            table = pd.crosstab(labels, ward, values=weights, aggfunc='sum').fillna(0).to_numpy()
            rr, cc = linear_sum_assignment(-table)
            ward_comparison.append({'model': name, 'comparison': 'existing Ward8 at original q=1/3,alpha=.75',
                'ARI': adjusted_rand_score(labels, ward),
                'matched_weight': float(table[rr, cc].sum()) if result.k == 8 else np.nan,
                'limit': 'No Ward refit; representation can differ. This is not a matched-geometry algorithm test.'})
            del ward_cache
        candidate_neighbours = pilot.loc[pilot.k.eq(result.k) & pilot.status.eq('complete')].copy()
        candidate_neighbours['parameter_distance'] = np.sqrt((candidate_neighbours.q - result.q) ** 2 + (candidate_neighbours.alpha - result.alpha) ** 2)
        for neighbour in candidate_neighbours.sort_values(['parameter_distance', 'q', 'alpha']).head(9).itertuples():
            other = joblib.load(output / 'references' / (neighbour.trial + '.joblib'))['labels']
            neighbours.append({'model': name, 'q': neighbour.q, 'alpha': neighbour.alpha,
                               'pilot_score': neighbour.score, 'parameter_distance': neighbour.parameter_distance,
                               'reference_ARI_to_selected': adjusted_rand_score(labels, other),
                               'interpretation': 'sampled nearby settings only; not a complete local stability surface'})
        print('Explaining', name, flush=True)
        with threadpool_limits(limits=1):
            rules, trees = explain_labels(data, labels, name)
        all_rules.append(rules)
        all_trees.append(trees)
    tables = {'original_category_profiles': profiles, 'profile_interpretations': interpretations,
              'comparison_with_frozen_BE': baseline_rows, 'parameter_neighbourhoods': neighbours}
    for filename, rows in tables.items():
        pd.DataFrame(rows).to_csv(output / (filename + '.csv'), index=False)
    (output / 'selected_reference_specs.json').write_text(json.dumps(exact_specs, indent=2))
    partition_rows = []
    for coarse, fine in combinations(selected_labels, 2):
        table = pd.crosstab(selected_labels[coarse], selected_labels[fine], values=weights, aggfunc='sum').fillna(0)
        partition_rows.append({'coarse': coarse, 'fine': fine,
            'ARI': adjusted_rand_score(selected_labels[coarse], selected_labels[fine]),
            'refinement_purity': float(table.max(axis=0).sum()),
            'worst_fine_purity': float((table.max(axis=0) / table.sum(axis=0)).min()),
            'limit': 'Approximate membership refinement only; geometries differ; not a strict lattice.'})
    pd.DataFrame(partition_rows).to_csv(output / 'new_partition_comparisons.csv', index=False)
    if ward_comparison:
        pd.DataFrame(ward_comparison).to_csv(output / 'comparison_with_existing_Ward8.csv', index=False)
    if all_rules:
        rules, trees = pd.concat(all_rules), pd.concat(all_trees)
        rules.to_csv(output / 'single_feature_folds.csv', index=False)
        trees.to_csv(output / 'burden_tree_folds.csv', index=False)
        rules.groupby(['model', 'cluster']).agg(balanced_accuracy=('balanced_accuracy', 'mean'),
            precision=('precision', 'mean'), recall=('recall', 'mean'),
            most_selected_feature=('feature', lambda x: x.value_counts().index[0]),
            selected_folds=('feature', lambda x: x.value_counts().max())).reset_index().to_csv(output / 'single_feature_summary.csv', index=False)
        tree_summary = trees.groupby(['model', 'depth']).balanced_accuracy.agg(['mean', 'std']).reset_index()
        tree_summary['leaf_capacity_balanced_accuracy_ceiling'] = [
            min(2 ** depth, int(name[1:])) / int(name[1:]) for name, depth in zip(tree_summary.model, tree_summary.depth)]
        tree_summary.to_csv(output / 'burden_tree_summary.csv', index=False)
    fig, axes = plt.subplots(2, 4, figsize=(16, 7), sharex=True, sharey=True)
    coarse = pd.read_csv(output / 'coarse_results.csv')
    for k, ax in zip(range(3, 11), axes.flat):
        grid = coarse.loc[coarse.k.eq(k)].pivot(index='q', columns='alpha', values='score')
        image = ax.imshow(grid.to_numpy(), origin='lower', vmin=.5, vmax=1, cmap='RdYlGn', aspect='auto')
        ax.set_title(f'k={k}')
        ax.set_xticks(range(len(grid.columns)), [f'{v:.2f}' for v in grid.columns], rotation=45)
        ax.set_yticks(range(len(grid.index)), [f'{v:.2f}' for v in grid.index])
        ax.set_xlabel('Worry allocation alpha'); ax.set_ylabel('Somewhat-worried position q')
    fig.colorbar(image, ax=axes.ravel().tolist(), label='Pilot minimum lower-decile ARI; blank = structural failure')
    fig.savefig(output / 'coarse_stability_surfaces.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    (output / 'reporting_complete.json').write_text(json.dumps({'status': 'completed',
        'numerically_supported_k': best.loc[best.stability_pass, 'k'].tolist(),
        'no_models_frozen_or_replaced': True, 'explanations': 'five country-grouped folds; no clustering refit'}, indent=2))
    print(best[['k', 'q', 'alpha', 'score', 'stability_pass', 'selection_status']].to_string(index=False), flush=True)


if __name__ == '__main__':
    main()
