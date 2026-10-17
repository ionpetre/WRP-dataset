"""Verify the T5 freeze, assignments, summaries and preserved historical files."""
import ast
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from t5_secondary_transfer import ROOT, BASE, sha, save, verify_seal, old, search


def main():
    output = ROOT / json.loads((BASE / 'current_run.json').read_text())['output']
    package = output / 'frozen_model'
    verify_seal(package)
    spec = json.loads((package / 'specification.json').read_text())
    record = json.loads((output / 'transfer_complete.json').read_text())
    assert record['new_clustering_fits'] == 0 and record['heldout_previously_examined_for_BE']
    assert record['frozen_at_utc'] < record['first_T5_heldout_read_in_this_run_utc']
    for name, digest in record['files'].items():
        assert sha(output / name) == digest
    for filename, digest in json.loads((output / 'protected_sources.json').read_text()).items():
        assert sha(ROOT / filename) == digest
    # The executed source was archived before a reporting-only code repair.
    for filename, digest in spec['development_inputs'].items():
        path = output / 'executed_transfer_implementation.py' if filename == '.week05_build/t5_secondary_transfer.py' else ROOT / filename
        assert sha(path) == digest, filename
    handoff = pd.read_parquet(output / 'all_respondents_T5_eligibility_and_frozen_profiles.parquet')
    assert len(handoff) == 146910 and handoff.WPID_RANDOM.is_unique
    assert handoff.COUNTRY_ISO3.nunique() == 142 and handoff.complete_case.sum() == 137460
    assert handoff.loc[~handoff.complete_case, 'T5_cluster'].isna().all()
    assert handoff.loc[~handoff.complete_case, 'T5_profile_id'].isna().all()
    for split, prepared, complete, countries in [('train', 116820, 109488, 113), ('heldout_country', 30090, 27972, 29)]:
        g = handoff.loc[handoff.country_split.eq(split)]
        assert len(g) == prepared and g.complete_case.sum() == complete and g.COUNTRY_ISO3.nunique() == countries
        assert np.isclose(g.equal_country_weight_within_split.sum(), 1)
        assert np.allclose(g.groupby('COUNTRY_ISO3').equal_country_weight_within_split.sum(), 1 / countries)
        assert set(g.loc[g.complete_case, 'T5_profile_id']) == {f'T5_C{c}' for c in range(5)}
    assert np.isclose(handoff.equal_country_weight_all_included_countries.sum(), 1)
    # Independent feature construction and nearest-centre calculation.
    raw = old.derive_frozen_features(pd.read_parquet(ROOT / 'course_artifacts/week03_heldout_country_data.parquet', columns=old.prepared_columns()))
    data = raw.loc[raw[search.FEATURES].notna().all(axis=1)].reset_index(drop=True)
    w = search.country_weights(data)
    values = data[search.FEATURES].to_numpy(float)
    worry = np.select([values[:, :6] == 0, values[:, :6] == 1, values[:, :6] == 2], [0, spec['spec']['q'], 1])
    mean = worry.mean(axis=1, keepdims=True)
    x = np.column_stack([np.sqrt(spec['spec']['alpha'] / 6) * (worry - mean),
                         np.sqrt(spec['spec']['alpha'] / 6) * mean,
                         np.sqrt((1 - spec['spec']['alpha']) / 14) * values[:, 6:]])
    distances = cdist(x, np.load(package / 'centres.npy'))
    assigned = pd.read_parquet(output / 'heldout_assignments.parquet')
    assert np.array_equal(data.WPID_RANDOM, assigned.WPID_RANDOM)
    assert np.array_equal(distances.argmin(axis=1), assigned.cluster)
    assert np.allclose(distances.min(axis=1), assigned.nearest_distance, atol=1e-14, rtol=0)
    cutoff = assigned.cluster.map({int(c): v for c, v in spec['profile_distance_p95'].items()}).to_numpy()
    assert np.array_equal(assigned.nearest_distance.to_numpy() > cutoff, assigned.beyond_development_profile_p95)
    by_id = data[['WPID_RANDOM']].merge(handoff[['WPID_RANDOM', 'T5_cluster']], on='WPID_RANDOM', validate='one_to_one')
    assert np.array_equal(by_id.T5_cluster.astype(int), assigned.cluster)
    for base, prefix in [(package, 'development'), (output, 'heldout')]:
        prevalence = pd.read_csv(base / f'{prefix}_prevalence.csv')
        for _, g in prevalence.groupby(['scope', 'area_id']):
            assert set(g.cluster) == set(range(5))
            assert np.isclose(g.equal_country_weighted_share.sum(), 1) and np.isclose(g.respondent_share.sum(), 1)
        profiles = pd.read_csv(base / f'{prefix}_original_category_profiles.csv')
        sums = profiles.groupby(['scope', 'area_id', 'cluster', 'feature']).proportion.sum()
        assert np.allclose(sums, 1) and profiles.proportion.between(0, 1).all()
        assert len(profiles.loc[profiles.scope.eq('global')]) == 5 * 46
    # Recalculate the global category total variation independently.
    d = pd.read_csv(output / 'heldout_vs_development_category_differences.csv')
    saved = pd.read_csv(output / 'heldout_original_feature_total_variation.csv')
    for (c, feature), g in d.loc[d.scope.eq('global')].groupby(['cluster', 'feature']):
        check = .5 * np.abs(g.proportion_heldout - g.proportion_development).sum()
        value = saved.loc[saved.scope.eq('global') & saved.cluster.eq(c) & saved.feature.eq(feature), 'feature_total_variation'].iloc[0]
        assert np.isclose(check, value)
    anchors = pd.read_csv(output / 'heldout_frozen_anchor_comparison.csv')
    assert anchors.loc[anchors.scope.eq('global')].heldout_contrast_direction_preserved.all()
    assert len(anchors.loc[anchors.scope.eq('global')]) == 15
    ci = pd.read_csv(output / 'heldout_country_bootstrap_intervals.csv')
    assert len(ci) == 235 and ci.valid_draws.eq(1000).all()
    assert ci.p025.between(0, 1).all() and ci.p975.between(0, 1).all() and ci.p025.le(ci.p975).all()
    # Transfer and reporting code must contain no fitting call.
    for filename in ['t5_secondary_transfer.py', 'report_t5_secondary_transfer.py']:
        tree = ast.parse((ROOT / '.week05_build' / filename).read_text())
        calls = [n.func.attr for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
        assert not {'fit', 'fit_predict', 'partial_fit'} & set(calls)
    tree_folder = ROOT / json.loads((ROOT / 'course_artifacts/week04_t5_shallow_explanations/current_run.json').read_text())['output']
    trees = pd.read_csv(tree_folder / 'all_feature_tree_folds.csv')
    assert len(trees) == 20 and set(trees.depth) == {1, 2, 3, 5} and set(trees.fold) == set(range(1, 6))
    folds = pd.read_csv(tree_folder / 'evaluation_country_folds.csv')
    assert len(folds) == 113 and folds.evaluation_country.is_unique
    original_summary = pd.read_csv(tree_folder / 'all_feature_tree_summary.csv').set_index('depth')
    assert np.allclose(trees.groupby('depth').balanced_accuracy.mean(), original_summary['mean'])
    result = {'status': 'passed', 'frozen_seal_verified': True, 'all_146910_IDs_preserved': True,
        'all_137460_complete_respondents_assigned_only': True, 'heldout_independent_prediction_replay': True,
        'category_probabilities_prevalence_and_total_variation_verified': True, 'all_113_CV_countries_once': True,
        'historical_BE_and_week06_hashes_unchanged': True, 'no_clustering_fit_calls': True,
        'secondary_assessment_label_verified': True, 'reporting_incident_preserved': True}
    save(output / 'verification.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
