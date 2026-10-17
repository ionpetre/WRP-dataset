"""Evaluate saved K-means profiles. No clustering, classifier or Ward fits."""
from pathlib import Path
from itertools import combinations
import fcntl
import hashlib
import json
import os
import joblib
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score
import search

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'course_artifacts/week04_kmeans_profile_evaluation'
DESIGN = {
    'version': 2, 'scope': 'seven passing adaptive selections plus unchanged B4/E8',
    'population': '109488 complete-response development respondents, same row order',
    'weights': 'fixed equal-country weights on the full common development population',
    'resamples': 'the existing 50 respondent and 50 country confirmation fits per model',
    'matching': 'one-to-one Hungarian matching maximizing equal-country overlap',
    'cluster_metrics': ['Jaccard', 'membership precision', 'membership recall', 'best-any-cluster Jaccard'],
    'summaries': 'median, 10th percentile and minimum across 50 reference-versus-resample comparisons per test',
    'new_cutoffs': 'none; these diagnostics do not replace the original median/p10 ARI filters',
    'profiles': 'all original worry categories, separate personal/known-person harm, weighted and respondent prevalence',
    'extra_clusters': 'weighted membership overlaps and original-category contrasts with the largest-overlap source cluster',
    'limitations': 'different geometries; not a strict refinement lattice; fixed-reference comparisons, not independent validation',
    'reference_diagnostic': 'reference-versus-repetition ARI and within-test ARI medoid from cached pairwise vectors; no representative is adopted',
    'clustering_fits': 0, 'classifier_fits': 0, 'Ward_work': False, 'heldout_responses': False,
}


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2))


def overlap(labels, other, weights, k, other_k):
    indices = labels.astype(int) * other_k + other.astype(int)
    return np.bincount(indices, weights=weights, minlength=k * other_k).reshape(k, other_k)


def cluster_scores(table):
    """Rows are reference clusters; columns are resampled clusters."""
    a, b = table.sum(axis=1), table.sum(axis=0)
    rows, cols = linear_sum_assignment(-table)
    assert np.array_equal(rows, np.arange(len(a)))
    intersection = table[rows, cols]
    union = a + b[cols] - intersection
    jaccard = np.divide(intersection, union, out=np.zeros_like(a), where=union > 0)
    precision = np.divide(intersection, b[cols], out=np.zeros_like(a), where=b[cols] > 0)
    recall = np.divide(intersection, a, out=np.zeros_like(a), where=a > 0)
    all_union = a[:, None] + b[None, :] - table
    all_jaccard = np.divide(table, all_union, out=np.zeros_like(table), where=all_union > 0)
    return cols, jaccard, precision, recall, all_jaccard.max(axis=1), b[cols]


def profile_tables(data, weights, registry, labels):
    profiles, summaries = [], []
    for spec in registry:
        name, k = spec['model'], spec['k']
        membership = labels[name]
        for c in range(k):
            inside = membership == c
            a, b = weights[inside], weights[~inside]
            summary = {'model': name, 'k': k, 'cluster': c, 'respondents': int(inside.sum()),
                'weighted_share': float(a.sum()), 'respondent_share': float(inside.mean()),
                'mean_worry_0_to_2': float(np.average(data[search.WORRY].mean(axis=1)[inside], weights=a)),
                'mean_personal_harm_prevalence': float(np.average(data[search.SELF].mean(axis=1)[inside], weights=a)),
                'mean_known_person_harm_prevalence': float(np.average(data[search.KNOWN].mean(axis=1)[inside], weights=a))}
            features = []
            for feature in search.FEATURES:
                rows = []
                for category in range(3 if feature in search.WORRY else 2):
                    values = data[feature].to_numpy() == category
                    p = float(np.average(values[inside], weights=a))
                    outside = float(np.average(values[~inside], weights=b))
                    row = {'model': name, 'k': k, 'cluster': c, 'feature': feature,
                           'category': category, 'proportion': p, 'outside_proportion': outside,
                           'difference': p - outside, 'weighted_share': float(a.sum())}
                    profiles.append(row)
                    rows.append(row)
                tv = .5 * sum(abs(row['difference']) for row in rows)
                anchor = max(rows, key=lambda row: row['difference'])
                category_label = (['not worried', 'somewhat worried', 'very worried'][anchor['category']]
                                  if feature in search.WORRY else ['no harm', 'harm'][anchor['category']])
                features.append((tv, f"{feature}: {category_label}, {anchor['proportion']:.1%} vs {anchor['outside_proportion']:.1%} outside"))
            # At most one category per feature: avoid repeating a domain in the anchor list.
            summary['distinct_feature_anchors'] = '; '.join(text for _, text in sorted(features, reverse=True)[:4])
            summaries.append(summary)
    return pd.DataFrame(profiles), pd.DataFrame(summaries)


def main():
    BASE.mkdir(parents=True, exist_ok=True)
    lock = (BASE / 'run.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    current = json.loads((ROOT / 'course_artifacts/week04_kmeans_adaptive_optimization/current_run.json').read_text())
    source = ROOT / current['output']
    assert (source / 'notebook_verification.json').exists()
    best = pd.read_csv(source / 'best_tested_setting_per_k.csv')
    baselines = pd.read_csv(source / 'frozen_baselines_on_confirmation_samples.csv')
    registry = json.loads((source / 'selected_reference_specs.json').read_text())
    for row in baselines.itertuples():
        registry.append({'model': row.baseline, 'trial': row.trial, 'k': row.k, 'q': row.q,
                         't': row.t, 'alpha': row.alpha, 'fingerprint': current['fingerprint'], 'status': 'frozen benchmark'})
    registry.sort(key=lambda row: (row['k'], row['model']))
    data_path = ROOT / 'course_artifacts/week04_search_v4/stage1_eligible_development.parquet'
    inputs = [data_path, source / 'protocol.json', source / 'selected_reference_specs.json',
              source / 'best_tested_setting_per_k.csv', source / 'frozen_baselines_on_confirmation_samples.csv',
              source / 'single_feature_summary_with_baselines.csv', source / 'burden_tree_summary_with_baselines.csv']
    for spec in registry:
        inputs.append(source / 'references' / (spec['trial'] + '.joblib'))
        inputs.extend(source / 'confirmation' / f'{spec["trial"]}_{kind}_ari.npy' for kind in ['respondents', 'countries'])
        inputs.extend(source / 'fits' / f'{spec["trial"]}_confirmation_{kind}_{repeat:02d}.joblib'
                      for kind in ['respondents', 'countries'] for repeat in range(50))
    protected = [ROOT / 'course_artifacts/week05_frozen_objective1_v1/123d248adda6115f/models.joblib',
                 ROOT / 'course_artifacts/week05_frozen_objective1_v1/123d248adda6115f/freeze_seal.json',
                 ROOT / 'course_artifacts/week05_objective1_handoff_v1/123d248adda6115f/all_respondents_eligibility_and_frozen_profiles.parquet']
    protected += list((ROOT / 'weekly_notebooks').glob('week0[356]*.ipynb'))
    provenance = {'design': DESIGN, 'source_fingerprint': current['fingerprint'],
                  'inputs_sha256': {str(p.relative_to(ROOT)): file_hash(p) for p in inputs}}
    fingerprint = hashlib.sha256(json.dumps(provenance, sort_keys=True).encode()).hexdigest()
    output = BASE / fingerprint[:16]
    output.mkdir(exist_ok=True)
    protocol = dict(provenance, fingerprint=fingerprint)
    if (output / 'protocol.json').exists():
        assert json.loads((output / 'protocol.json').read_text()) == protocol
    else:
        save_json(output / 'protocol.json', protocol)
    save_json(output / 'model_registry.json', registry)
    save_json(output / 'protected_sources.json', {str(p.relative_to(ROOT)): file_hash(p) for p in protected})
    save_json(output / 'runtime.json', {'evaluation_code_sha256': file_hash(__file__),
                                      'numpy': np.__version__, 'pandas': pd.__version__})
    save_json(BASE / 'current_run.json', {'output': str(output.relative_to(ROOT)), 'fingerprint': fingerprint})
    data = pd.read_parquet(data_path)
    assert data.country_split.eq('train').all()
    data = data.loc[data[search.FEATURES].notna().all(axis=1)].reset_index(drop=True)
    assert len(data) == 109488 and data.COUNTRY_ISO3.nunique() == 113 and data.WPID_RANDOM.is_unique
    weights = search.country_weights(data)
    labels = {}
    for spec in registry:
        ref = joblib.load(source / 'references' / (spec['trial'] + '.joblib'))
        assert ref['fingerprint'] == current['fingerprint']
        labels[spec['model']] = ref['labels']
    profiles, summary = profile_tables(data, weights, registry, labels)
    profiles.to_csv(output / 'original_category_profiles.csv', index=False)
    summary.to_csv(output / 'profile_summaries.csv', index=False)
    # The two reconstruction checks already exist: copy summaries, do not refit trees.
    rules = pd.read_csv(source / 'single_feature_summary_with_baselines.csv')
    trees = pd.read_csv(source / 'burden_tree_summary_with_baselines.csv')
    rules.to_csv(output / 'single_feature_summary.csv', index=False)
    trees.to_csv(output / 'burden_tree_summary.csv', index=False)
    measurements, reference_agreement, medoid_rows = [], [], []
    for spec in registry:
        name, k = spec['model'], spec['k']
        for kind in ['respondents', 'countries']:
            # The saved pairwise vector uses combinations of repetitions 0,...,49.
            pairs = np.load(source / 'confirmation' / f'{spec["trial"]}_{kind}_ari.npy')
            assert len(pairs) == 1225 and np.isfinite(pairs).all()
            matrix = np.eye(50)
            ii, jj = np.triu_indices(50, 1)
            matrix[ii, jj] = pairs
            matrix[jj, ii] = pairs
            mean_ari = (matrix.sum(axis=1) - 1) / 49
            medoid = int(mean_ari.argmax())
            medoid_reference_ari = None
            for repeat in range(50):
                cache = source / 'fits' / f'{spec["trial"]}_confirmation_{kind}_{repeat:02d}.joblib'
                fit = joblib.load(cache)
                assert fit['fingerprint'] == current['fingerprint'] and fit['status'] == 'ok'
                assert len(fit['labels']) == len(data) and np.min(fit['labels']) >= 0 and np.max(fit['labels']) < k
                table = overlap(labels[name], fit['labels'], weights, k, k)
                matched, jac, precision, recall, best_any, mass = cluster_scores(table)
                ref_ari = adjusted_rand_score(labels[name], fit['labels'])
                if repeat == medoid:
                    medoid_reference_ari = ref_ari
                reference_agreement.append({'model': name, 'test': kind, 'repeat': repeat,
                    'reference_ARI': ref_ari, 'matched_equal_country_weight': float(np.trace(table[:, matched])),
                    'mean_ARI_to_other_repetitions': mean_ari[repeat], 'is_test_medoid': repeat == medoid})
                for c in range(k):
                    measurements.append({'model': name, 'k': k, 'test': kind, 'repeat': repeat,
                        'cluster': c, 'matched_fit_cluster': int(matched[c]), 'jaccard': jac[c],
                        'precision': precision[c], 'recall': recall[c], 'best_any_jaccard': best_any[c],
                        'matching_gap': best_any[c] - jac[c], 'matched_cluster_share': mass[c]})
            medoid_rows.append({'model': name, 'test': kind, 'medoid_repeat': medoid,
                'medoid_mean_ARI_to_other_repetitions': mean_ari[medoid],
                'medoid_p10_ARI_to_other_repetitions': float(np.quantile(np.delete(matrix[medoid], medoid), .1)),
                'medoid_reference_ARI': medoid_reference_ari,
                'cached_pairwise_ARI_median': float(np.median(pairs)), 'cached_pairwise_ARI_p10': float(np.quantile(pairs, .1)),
                'interpretation': 'diagnostic of representativeness; no medoid or new profile is adopted'})
        print('Evaluated 100 cached fits:', name, flush=True)
    measurements = pd.DataFrame(measurements)
    measurements.to_csv(output / 'cluster_stability_repetitions.csv', index=False)
    agreement = pd.DataFrame(reference_agreement)
    agreement.to_csv(output / 'reference_partition_agreement.csv', index=False)
    agreement.groupby(['model', 'test']).agg(reference_ARI_median=('reference_ARI', 'median'),
        reference_ARI_p10=('reference_ARI', lambda x: x.quantile(.1)),
        reference_ARI_mean=('reference_ARI', 'mean'),
        matched_weight_median=('matched_equal_country_weight', 'median'),
        matched_weight_p10=('matched_equal_country_weight', lambda x: x.quantile(.1))).reset_index().merge(
            pd.DataFrame(medoid_rows), on=['model', 'test']).to_csv(output / 'reference_representativeness.csv', index=False)
    rows = []
    for (name, k, kind, c), group in measurements.groupby(['model', 'k', 'test', 'cluster']):
        row = {'model': name, 'k': k, 'test': kind, 'cluster': c, 'repetitions': len(group)}
        for metric in ['jaccard', 'precision', 'recall', 'best_any_jaccard', 'matching_gap', 'matched_cluster_share']:
            row.update({metric + '_median': group[metric].median(), metric + '_p10': group[metric].quantile(.1),
                        metric + '_min': group[metric].min()})
        rows.append(row)
    stability = pd.DataFrame(rows).merge(summary[['model', 'cluster', 'weighted_share', 'respondents']], on=['model', 'cluster'])
    stability.to_csv(output / 'cluster_stability_summary.csv', index=False)
    overview = []
    for spec in registry:
        name = spec['model']
        numerical = (baselines.loc[baselines.baseline.eq(name)] if name in ['B4', 'E8']
                     else best.loc[best.k.eq(spec['k'])]).iloc[0]
        row = dict(spec, score=numerical.score, largest=numerical.largest)
        for kind in ['respondents', 'countries']:
            group = stability.loc[stability.model.eq(name) & stability.test.eq(kind)]
            weakest = group.sort_values('jaccard_p10').iloc[0]
            row[kind + '_weakest_cluster'] = int(weakest.cluster)
            row[kind + '_min_cluster_jaccard_p10'] = weakest.jaccard_p10
            row[kind + '_min_cluster_recall_p10'] = group.recall_p10.min()
            row[kind + '_min_cluster_precision_p10'] = group.precision_p10.min()
        strongest_rule = rules.loc[rules.model.eq(name)].sort_values('balanced_accuracy', ascending=False).iloc[0]
        row.update(strongest_rule_cluster=int(strongest_rule.cluster), strongest_rule_feature=strongest_rule.most_selected_feature,
                   strongest_rule_balanced_accuracy=strongest_rule.balanced_accuracy,
                   strongest_rule_precision=strongest_rule.precision, strongest_rule_recall=strongest_rule.recall)
        row['burden_depth2_balanced_accuracy'] = trees.loc[trees.model.eq(name) & trees.depth.eq(2), 'mean'].iloc[0]
        overview.append(row)
    pd.DataFrame(overview).to_csv(output / 'model_evaluation_overview.csv', index=False)
    pair_rows, overlap_rows, parent_rows, differences = [], [], [], []
    # Original-category probability vectors, in a common feature/category order.
    probabilities = {(name, int(c)): g.set_index(['feature', 'category']).proportion
                     for (name, c), g in profiles.groupby(['model', 'cluster'])}
    for a, b in combinations(registry, 2):
        source_name, target_name, ka, kb = a['model'], b['model'], a['k'], b['k']
        table = overlap(labels[source_name], labels[target_name], weights, ka, kb)
        source_mass, target_mass = table.sum(axis=1), table.sum(axis=0)
        purity = table.max(axis=0) / target_mass
        rr, cc = linear_sum_assignment(-table)
        pair_rows.append({'source': source_name, 'target': target_name, 'source_k': ka, 'target_k': kb,
            'ARI': adjusted_rand_score(labels[source_name], labels[target_name]),
            'target_to_source_weighted_purity': float(table.max(axis=0).sum()),
            'worst_target_source_purity': float(purity.min()),
            'matched_weight_if_same_k': float(table[rr, cc].sum()) if ka == kb else np.nan,
            'meaning': 'largest-overlap source only; different geometries; not a strict refinement'})
        for c in range(ka):
            for d in range(kb):
                overlap_rows.append({'source': source_name, 'target': target_name,
                    'source_cluster': c, 'target_cluster': d, 'joint_weighted_share': table[c, d],
                    'share_of_source': table[c, d] / source_mass[c], 'share_of_target': table[c, d] / target_mass[d]})
        for d in range(kb):
            c = int(table[:, d].argmax())
            before, after = probabilities[(source_name, c)], probabilities[(target_name, d)]
            delta = after - before
            block_tv = {}
            for block, features in [('worry', search.WORRY), ('personal_harm', search.SELF), ('known_person_harm', search.KNOWN)]:
                block_tv[block + '_mean_feature_TV'] = float(np.mean([.5 * delta.loc[f].abs().sum() for f in features]))
            parent_rows.append({'source': source_name, 'target': target_name, 'target_cluster': d,
                'largest_overlap_source_cluster': c, 'target_share': target_mass[d],
                'share_from_largest_source': purity[d], 'share_of_source_in_target': table[c, d] / source_mass[c],
                **block_tv, 'interpretation': 'descriptive comparison, not evidence of a nested split or significance test'})
            for (feature, category), value in delta.items():
                differences.append({'source': source_name, 'target': target_name, 'target_cluster': d,
                    'largest_overlap_source_cluster': c, 'share_from_largest_source': purity[d],
                    'feature': feature, 'category': int(category), 'difference': float(value),
                    'target_proportion': after.loc[(feature, category)], 'source_proportion': before.loc[(feature, category)]})
    for filename, rows in [('partition_comparisons', pair_rows), ('partition_overlaps', overlap_rows),
                           ('largest_overlap_source_comparisons', parent_rows), ('original_unit_added_distinctions', differences)]:
        pd.DataFrame(rows).to_csv(output / (filename + '.csv'), index=False)
    assert all(file_hash(ROOT / name) == digest for name, digest in provenance['inputs_sha256'].items())
    saved = json.loads((output / 'protected_sources.json').read_text())
    assert all(file_hash(ROOT / name) == digest for name, digest in saved.items())
    save_json(output / 'completion.json', {'status': 'completed', 'models': len(registry), 'profiles': len(summary),
        'cached_repetitions': 100 * len(registry), 'cluster_repetition_comparisons': len(measurements),
        'new_clustering_fits': 0, 'new_classifier_fits': 0, 'Ward_work': False, 'heldout_responses_loaded': False,
        'source_caches_and_frozen_files_unchanged': True, 'no_new_eligibility_thresholds': True})
    print('COMPLETED', output, flush=True)


if __name__ == '__main__':
    main()
