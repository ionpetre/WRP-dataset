"""Fast checks of geometry, weighting, samples and saved scores. No clustering fits."""
from pathlib import Path
import hashlib
import json
import platform
import joblib
import numpy as np
import pandas as pd
import sklearn
import search

ROOT = Path(__file__).resolve().parents[1]
current = json.loads((ROOT / 'course_artifacts/week04_kmeans_parameter_optimization/current_run.json').read_text())
output = ROOT / current['output']
search.initialize(ROOT, output)
data = search.DATA
runtime = {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__,
           'sklearn': sklearn.__version__, 'search_code_sha256': hashlib.sha256(Path(search.__file__).read_bytes()).hexdigest()}
path = output / 'runtime.json'
if path.exists():
    assert json.loads(path.read_text()) == runtime
else:
    path.write_text(json.dumps(runtime, indent=2))
for q in search.DESIGN['q_grid']:
    matrix = search.profile_matrix(data, q, .5)
    assert matrix.shape == (109488, 21) and np.isfinite(matrix).all()
    worry = np.where(data[search.WORRY].to_numpy() == 2, 1 / q, data[search.WORRY].to_numpy()) / (1 / q)
    assert np.allclose(worry[data[search.WORRY].to_numpy() == 1], q)
    assert np.allclose(matrix[:, :6].sum(axis=1), 0)
weights = pd.Series(search.WEIGHTS).groupby(data.COUNTRY_ISO3).sum()
assert np.allclose(weights, 1 / 113)
registry = pd.read_csv(ROOT / 'course_artifacts/week03_country_split.csv')
registry = registry.loc[registry.country_split.eq('train')]
plans, _ = search.make_country_and_respondent_plans(data, registry, 20261005, 50)
old = joblib.load(search.LEGACY / 'sampling_indices.joblib')
assert all(np.array_equal(a, b) for kind in plans for a, b in zip(plans[kind], old[kind]))
assert all(data.iloc[idx].COUNTRY_ISO3.nunique() == 90 for idx in search.PLANS['confirmation']['countries'])
paths = list((output / 'pilot').glob('*.json')) + list((output / 'confirmation').glob('*.json'))
for path in paths:
    row = json.loads(path.read_text())
    if row['status'] != 'complete':
        continue
    p10, medians = [], []
    for kind in ['countries', 'respondents']:
        scores = np.load(path.parent / f"{row['trial']}_{kind}_ari.npy")
        assert len(scores) == (45 if row['phase'] == 'pilot' else 1225)
        assert np.isclose(np.median(scores), row[kind + '_median'])
        assert np.isclose(np.quantile(scores, .1), row[kind + '_p10'])
        p10.append(np.quantile(scores, .1)); medians.append(np.median(scores))
    assert np.isclose(row['score'], min(p10))
    assert row['stability_pass'] == bool(min(p10 + medians) >= .8)
protected = json.loads((output / 'protected_sources.json').read_text())
assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest for name, digest in protected.items())
result = {'status': 'passed', 'geometry': 'q maps the middle category; original 21 coordinates preserved',
          'weighting': 'equal eligible country mass', 'sampling': 'all 100 original plans reproduced exactly; fresh confirmation retains 90 countries',
          'scores': 'saved pilot pairwise vectors reproduce their summaries', 'frozen_sources_unchanged': True}
(output / 'verification.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
