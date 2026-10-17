"""Explain weak reference profiles using saved centres and assignments. No refits."""
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
import evaluate_profiles as evaluation
import search

ROOT = evaluation.ROOT
pointer = json.loads((evaluation.BASE / 'current_run.json').read_text())
output = ROOT / pointer['output']
protocol = json.loads((output / 'protocol.json').read_text())
current = json.loads((ROOT / 'course_artifacts/week04_kmeans_adaptive_optimization/current_run.json').read_text())
assert current['fingerprint'] == protocol['source_fingerprint']
source = ROOT / current['output']
registry = json.loads((output / 'model_registry.json').read_text())
data = pd.read_parquet(ROOT / 'course_artifacts/week04_search_v4/stage1_eligible_development.parquet')
assert data.country_split.eq('train').all()
data = data.loc[data[search.FEATURES].notna().all(axis=1)].reset_index(drop=True)
assert len(data) == 109488
weights = search.country_weights(data)
inertias, flows = [], []
for spec in registry:
    name, k, trial = spec['model'], spec['k'], spec['trial']
    reference = joblib.load(source / 'references' / (trial + '.joblib'))
    assert reference['fingerprint'] == current['fingerprint']
    labels = reference['labels']
    X = search.profile_matrix(data, spec['q'], spec['alpha'])
    d = cdist(X, reference['centres'], metric='sqeuclidean')
    reference_inertia = float(weights @ d.min(axis=1))
    assert np.allclose(d[np.arange(len(X)), labels], d.min(axis=1), atol=1e-10, rtol=1e-10)
    for kind in ['respondents', 'countries']:
        normalized_flows = []
        for repeat in range(50):
            fit = joblib.load(source / 'fits' / f'{trial}_confirmation_{kind}_{repeat:02d}.joblib')
            assert fit['fingerprint'] == current['fingerprint'] and fit['status'] == 'ok'
            distances = cdist(X, fit['centres'], metric='sqeuclidean')
            minimum = distances.min(axis=1)
            assert np.allclose(distances[np.arange(len(X)), fit['labels']], minimum, atol=1e-10, rtol=1e-10)
            inertia = float(weights @ minimum)
            inertias.append({'model': name, 'test': kind, 'repeat': repeat,
                'reference_full_population_inertia': reference_inertia,
                'cached_centres_full_population_inertia': inertia,
                'relative_inertia_difference': inertia / reference_inertia - 1,
                'lower_than_reference_beyond_tolerance': inertia < reference_inertia - 1e-10,
                'limit': 'same geometry and full population within model only; no refit, no cross-geometry ranking'})
            table = evaluation.overlap(labels, fit['labels'], weights, k, k)
            columns = evaluation.cluster_scores(table)[0]
            normalized_flows.append(table[:, columns] / table.sum(axis=1)[:, None])
        values = np.stack(normalized_flows)
        for c in range(k):
            for d in range(k):
                flows.append({'model': name, 'test': kind, 'reference_cluster': c,
                    'aligned_resampled_cluster': d, 'mean_share': values[:, c, d].mean(),
                    'p10_share': np.quantile(values[:, c, d], .1), 'p90_share': np.quantile(values[:, c, d], .9),
                    'meaning': 'where members of this fixed reference cluster go after one-to-one label alignment'})
    print('Diagnosed saved references:', name, flush=True)
inertias = pd.DataFrame(inertias)
inertias.to_csv(output / 'cached_centres_full_population_inertia.csv', index=False)
inertias.groupby(['model', 'test']).agg(
    reference_full_population_inertia=('reference_full_population_inertia', 'first'),
    relative_inertia_difference_min=('relative_inertia_difference', 'min'),
    relative_inertia_difference_median=('relative_inertia_difference', 'median'),
    cached_centres_better_than_reference=('lower_than_reference_beyond_tolerance', 'sum')).reset_index().to_csv(
        output / 'reference_inertia_diagnostic.csv', index=False)
pd.DataFrame(flows).to_csv(output / 'aligned_membership_flows.csv', index=False)
assert all(evaluation.file_hash(ROOT / name) == digest for name, digest in protocol['inputs_sha256'].items())
evaluation.save_json(output / 'reference_diagnostic_verification.json', {
    'status': 'passed', 'cached_fits': len(inertias), 'all_saved_assignments_match_centres': True,
    'new_fits': 0, 'no_representatives_or_frozen_models_changed': True,
    'raw_inertia_compared_only_within_identical_geometry': True,
    'diagnostic_code_sha256': evaluation.file_hash(__file__)})
