"""Audit completed fit caches and numerical reporting; no new fits."""
from pathlib import Path
from collections import Counter
import json
import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
pointer = json.loads((ROOT / 'course_artifacts/week04_kmeans_parameter_optimization/current_run.json').read_text())
output = ROOT / pointer['output']
assert (output / 'completion.json').exists()
sources, statuses, warnings = Counter(), Counter(), Counter()
iterations = []
for path in (output / 'references').glob('*.joblib'):
    result = joblib.load(path)
    assert result['fingerprint'] == pointer['fingerprint']
    assert len(result['labels']) == 109488
    sources[result['source']] += 1
    if 'iterations' in result:
        iterations.append(result['iterations'])
for path in (output / 'fits').glob('*.joblib'):
    result = joblib.load(path)
    assert result['fingerprint'] == pointer['fingerprint']
    statuses[result['status']] += 1
    if result['status'] == 'ok':
        assert len(result['labels']) == 109488
        iterations.append(result['iterations'])
        warnings.update(result.get('warnings', []))
counts = {}
for phase, expected in [('pilot', 45), ('confirmation', 1225)]:
    arrays = list((output / phase).glob('*_ari.npy'))
    assert all(len(np.load(path)) == expected for path in arrays)
    counts[phase] = {'complete_tests': len(arrays), 'pairwise_ARIs': len(arrays) * expected}
profiles = pd.read_csv(output / 'original_category_profiles.csv')
assert np.allclose(profiles.groupby(['model', 'cluster', 'feature']).proportion.sum(), 1)
assert np.allclose(profiles.groupby(['model', 'cluster']).cluster_share.first().groupby('model').sum(), 1)
result = {'status': 'passed', 'reference_sources': dict(sources), 'new_repetition_fit_cache_statuses': dict(statuses),
          'maximum_recorded_iterations': int(max(iterations)), 'recorded_fits_at_300_iteration_limit': int(sum(i >= 300 for i in iterations)),
          'warning_messages': dict(warnings), 'pairwise_comparisons': counts,
          'original_category_profiles_normalized': True,
          'new_frozen_or_heldout_models': 0}
(output / 'fit_audit.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
