"""Check adaptive-search provenance, geometry, resampling and available scores; no fits."""
from pathlib import Path
import hashlib
import json
import joblib
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
import adaptive_search as adaptive
import search

ROOT = adaptive.ROOT
pointer = json.loads((adaptive.BASE / 'current_run.json').read_text())
output = ROOT / pointer['output']
protocol = json.loads((output / 'protocol.json').read_text())
assert protocol['design'] == adaptive.DESIGN
runtime = json.loads((output / 'runtime.json').read_text())
assert runtime['runner_code_sha256'] == adaptive.file_hash(adaptive.__file__)
assert runtime['search_code_sha256'] == adaptive.file_hash(search.__file__)
assert runtime['optuna'] == adaptive.optuna.__version__
assert all(adaptive.file_hash(ROOT / name) == digest for name, digest in protocol['inputs_sha256'].items())
adaptive.initialize_worker(output)
assert search.DESIGN['confirmation_fit_seed'] == 2026112600
assert len(search.DATA) == 109488 and search.DATA.country_split.eq('train').all()
assert np.allclose(pd.Series(search.WEIGHTS).groupby(search.DATA.COUNTRY_ISO3).sum(), 1 / 113)
for q, alpha in [(.1, .2), (.5, .5), (.9, .8)]:
    actual = search.profile_matrix(search.DATA.iloc[:200], q, alpha)
    raw = search.DATA.iloc[:200][search.FEATURES].to_numpy(float)
    w = np.where(raw[:, :6] == 2, 1.0, raw[:, :6] * q)
    m = w.mean(axis=1, keepdims=True)
    expected = np.column_stack([(w - m) * np.sqrt(alpha / 6), m * np.sqrt(alpha / 6), raw[:, 6:] * np.sqrt((1 - alpha) / 14)])
    assert np.allclose(actual, expected) and actual.shape == (200, 21)
reference_checks = 0
for path in (output / 'references').glob('*.joblib'):
    ref = joblib.load(path)
    assert ref['fingerprint'] == pointer['fingerprint']
    assert path.stem == search.trial_id(ref['q'], ref['alpha'], ref['k'])
    assert ref['centres'].shape == (ref['k'], 21) and np.isfinite(ref['centres']).all()
    shares = np.bincount(ref['labels'], weights=search.WEIGHTS, minlength=ref['k'])
    assert np.isclose(shares.max(), ref['largest']) and np.isclose(ref['k'] * shares.max(), ref['dominance'])
    assert ref['structural_pass'] == bool(len(np.unique(ref['labels'])) == ref['k'] and shares.max() <= .4 and ref['k'] * shares.max() < 3)
    # Independently check nearest-centroid assignments; allow only floating-point ties.
    X = search.profile_matrix(search.DATA.iloc[:256], ref['q'], ref['alpha'])
    distances = cdist(X, ref['centres'])
    assigned = distances[np.arange(len(X)), ref['labels'][:len(X)]]
    assert np.allclose(assigned, distances.min(axis=1), atol=1e-10, rtol=1e-10)
    reference_checks += 1


def index_hash(indices):
    return hashlib.sha256(np.asarray(indices).tobytes()).hexdigest()


fresh = search.PLANS['confirmation']
original = joblib.load(search.LEGACY / 'sampling_indices.joblib')
previous_confirmation = joblib.load(adaptive.PREVIOUS / 'confirmation_sampling_indices.joblib')
for kind in fresh:
    hashes = {index_hash(idx) for idx in fresh[kind]}
    assert len(hashes) == 50
    assert not hashes.intersection(index_hash(idx) for idx in original[kind])
    assert not hashes.intersection(index_hash(idx) for idx in previous_confirmation[kind])
assert all(search.DATA.iloc[idx].COUNTRY_ISO3.nunique() == 90 for idx in fresh['countries'])
counts = {'previous_pilot_settings': 0, 'new_pilot_settings': 0, 'confirmed_settings': 0}
for phase, pairs in [('pilot', 45), ('confirmation', 1225)]:
    for path in (output / phase).glob('*.json'):
        row = json.loads(path.read_text())
        assert row['fingerprint'] == pointer['fingerprint']
        counts['confirmed_settings' if phase == 'confirmation' else ('previous_pilot_settings' if row.get('origin') == 'previous pilot' else 'new_pilot_settings')] += 1
        if row['status'] == 'complete':
            values = []
            for kind in ['respondents', 'countries']:
                scores = np.load(output / phase / f'{row["trial"]}_{kind}_ari.npy')
                assert len(scores) == pairs
                assert np.isclose(np.median(scores), row[kind + '_median'])
                assert np.isclose(np.quantile(scores, .1), row[kind + '_p10'])
                values.extend([row[kind + '_median'], row[kind + '_p10']])
            assert row['stability_pass'] == bool(min(values) >= .8)
            assert np.isclose(row['score'], min(row['respondents_p10'], row['countries_p10']))
assert counts['previous_pilot_settings'] == 301
for path in (output / 'studies').glob('k*_new_trials.csv'):
    trials = pd.read_csv(path)
    assert len(trials) <= 20 and not trials.duplicated(['q', 'alpha']).any()
    assert trials.q.between(.1, .9).all() and trials.alpha.between(.2, .8).all()
if (output / 'shortlist_seal.json').exists():
    seal = json.loads((output / 'shortlist_seal.json').read_text())
    for name, filename in [('confirmation_plan_sha256', 'confirmation_plan.csv'),
                           ('shortlist_sha256', 'shortlist_before_confirmation.csv'),
                           ('confirmation_samples_sha256', 'confirmation_sampling_indices.joblib')]:
        assert seal[name] == adaptive.file_hash(output / filename)
if (output / 'completion.json').exists():
    assert counts['new_pilot_settings'] == 160
    assert counts['confirmed_settings'] == len(pd.read_csv(output / 'confirmation_plan.csv'))
    assert all(len(pd.read_csv(p)) == 20 for p in (output / 'studies').glob('k*_new_trials.csv'))
protected = json.loads((output / 'protected_sources.json').read_text())
assert all(adaptive.file_hash(ROOT / name) == digest for name, digest in protected.items())
result = {'status': 'passed', **counts, 'all_new_confirmation_plans_disjoint_from_earlier_plans': True,
          'reference_centroid_and_structural_checks': reference_checks,
          'geometry_and_weights_unchanged': True, 'previous_results_and_frozen_sources_unchanged': True,
          'fit_seed_range_checked': True, 'complete_scores_reproduce_pairwise_vectors': True}
adaptive.save_json(output / 'verification.json', result)
print(json.dumps(result, indent=2))
