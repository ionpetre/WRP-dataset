"""Development-only K-means parameter search. Existing B/E models are never replaced."""
from pathlib import Path
from itertools import combinations, product
import hashlib
import json
import warnings
import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from threadpoolctl import threadpool_limits

# A small grid first, then a 3-by-3 local refinement for each k.
DESIGN = {
    'version': 1, 'k_values': list(range(3, 11)),
    'q_grid': [.1, .2, 1 / 3, .5, .7, .9],
    'alpha_grid': [.2, .25, .5, .75, .8],
    'q_bounds': [.1, .9], 'alpha_bounds': [.2, .8],
    'reference_seed': 20231006, 'n_init': 20, 'max_iter': 300,
    'pilot_repetitions': 10, 'pilot_plans': 'first ten original Week 4 samples in each test',
    'pilot_fit_seed': 20261005 + 1000,
    'confirmation_repetitions': 50, 'confirmation_sample_seed': 20261016,
    'confirmation_fit_seed': 20261016 + 1000,
    'score': 'minimum respondent/country lower-decile pairwise ARI',
    'ranking': ['score descending', 'minimum median ARI descending',
                'squared distance from q=.5,alpha=.5 ascending', 'q ascending', 'alpha ascending'],
    'refinement': 'one coarse seed per k; midpoint to adjacent coarse values on each axis; retain centre; no extrapolation',
    'shortlist': 'two distinct parameter settings per k from completed eligible pilots; add frozen B4/E8 baselines',
    'filters': {'largest_share_max': .4, 'dominance_strictly_below': 3,
                'median_and_p10_ARI_each_test_at_least': .8},
    'geometry': 'unchanged 21-coordinate separate-harm geometry, reduced mean-worry coordinate',
    'data': 'all-20-feature-complete development respondents, original order; no held-out responses',
    'weights': 'WGT normalized within included country, then equal country totals; recalculate after sampling',
    'confirmation_limit': 'fresh resamples of the same development countries, not independent validation',
    'selection_limit': 'best tested setting within this bounded search, not a guaranteed continuous optimum',
    'plateau_review': 'report nearby settings and reference ARIs; no new automatic semantic threshold',
}
DOMAINS = ['food', 'water', 'crime', 'severe_weather', 'traffic', 'mental_health']
WORRY = ['worry_' + d for d in DOMAINS]
HARM = ['harm_' + d for d in DOMAINS + ['work']]
SELF = [f + '_personal' for f in HARM]
KNOWN = [f + '_known_person' for f in HARM]
FEATURES = WORRY + SELF + KNOWN


def country_weights(frame):
    return (frame.WGT / frame.groupby('COUNTRY_ISO3').WGT.transform('sum')
            / frame.COUNTRY_ISO3.nunique()).to_numpy()


def profile_matrix(frame, q, alpha):
    # 0/1/t normalized by t is 0/q/1, with t=1/q. Preserve the old operation order.
    values = frame[FEATURES].to_numpy(float)
    top = 1 / q
    worry = np.where(values[:, :6] == 2, top, values[:, :6]) / top
    mean = worry.mean(axis=1, keepdims=True)
    return np.column_stack([(worry - mean) * np.sqrt(alpha) / np.sqrt(6),
                            mean * np.sqrt(alpha) / np.sqrt(6),
                            values[:, 6:] * np.sqrt((1 - alpha) / 2) / np.sqrt(7)])


def trial_id(q, alpha, k):
    # Hash the exact floats, not rounded display values.
    point = json.dumps([float(q), float(alpha), int(k)])
    return f'k{k}_' + hashlib.sha256(point.encode()).hexdigest()[:16]


def make_country_and_respondent_plans(data, registry, seed, repetitions):
    groups = registry.groupby(['GlobalRegion', 'CountryIncomeLevel'], sort=True)
    quota = groups.size().rename('available').to_frame()
    quota['selected'] = np.maximum(1, np.floor(.8 * quota.available).astype(int))
    while quota.selected.sum() < round(.8 * len(registry)):
        remainder = (.8 * quota.available - quota.selected).where(quota.selected < quota.available, -np.inf)
        quota.loc[remainder.idxmax(), 'selected'] += 1
    country_rows = [np.flatnonzero(data.COUNTRY_ISO3.eq(c)) for c in sorted(data.COUNTRY_ISO3.unique())]
    plans = {'respondents': [], 'countries': []}
    for repeat in range(repetitions):
        rng = np.random.default_rng(seed + repeat)
        rows = np.sort(np.concatenate([rng.choice(idx, round(.8 * len(idx)), replace=False) for idx in country_rows]))
        plans['respondents'].append(rows)
        selected = []
        for key, group in groups:
            selected.extend(rng.choice(sorted(group.COUNTRY_ISO3), int(quota.loc[key, 'selected']), replace=False))
        plans['countries'].append(np.flatnonzero(data.COUNTRY_ISO3.isin(selected)))
    return plans, quota


def initialize(root, output):
    # Each worker loads these read-only objects once, not once per fit.
    global ROOT, OUTPUT, DATA, WEIGHTS, PLANS, FINGERPRINT, LEGACY, LEGACY_FINGERPRINT
    ROOT, OUTPUT = Path(root), Path(output)
    source = ROOT / 'course_artifacts/week04_search_v4/stage1_eligible_development.parquet'
    raw = pd.read_parquet(source)
    assert raw.country_split.eq('train').all()
    DATA = raw.loc[raw[FEATURES].notna().all(axis=1)].reset_index(drop=True)
    assert len(DATA) == 109488 and DATA.COUNTRY_ISO3.nunique() == 113 and DATA.WPID_RANDOM.is_unique
    assert DATA[WORRY].isin([0, 1, 2]).all().all() and DATA[SELF + KNOWN].isin([0, 1]).all().all()
    WEIGHTS = country_weights(DATA)
    LEGACY = ROOT / 'course_artifacts/week04_experiment1_complete_overall_worry_v3'
    old_design = json.loads((LEGACY / 'design.json').read_text())
    LEGACY_FINGERPRINT = hashlib.sha256(source.read_bytes() + json.dumps(old_design, sort_keys=True).encode()).hexdigest()
    protocol = json.loads((OUTPUT / 'protocol.json').read_text())
    FINGERPRINT = protocol['fingerprint']
    old_plans = joblib.load(LEGACY / 'sampling_indices.joblib')
    PLANS = {'pilot': {kind: samples[:10] for kind, samples in old_plans.items()},
             'confirmation': joblib.load(OUTPUT / 'confirmation_sampling_indices.joblib')}


def legacy_setting(q, alpha):
    encoding = next((name for name, value in [('012', .5), ('013', 1 / 3), ('015', .2)] if q == value), None)
    balance = { .25: 'harm_emphasized', .5: 'balanced', .75: 'worry_emphasized'}.get(alpha)
    return (encoding, balance) if encoding and balance else None


def fit_labels(X, indices, k, seed):
    model = KMeans(n_clusters=k, n_init=20, max_iter=300, random_state=seed)
    with warnings.catch_warnings(record=True) as caught, threadpool_limits(limits=1):
        model.fit(X[indices], sample_weight=country_weights(DATA.iloc[indices]))
        labels = model.predict(X).astype('int8')
    return {'status': 'ok', 'labels': labels, 'centres': model.cluster_centers_,
            'iterations': int(model.n_iter_), 'warnings': [str(w.message) for w in caught]}


def reference_fit(q, alpha, k):
    path = OUTPUT / 'references' / (trial_id(q, alpha, k) + '.joblib')
    if path.exists():
        result = joblib.load(path)
        assert result['fingerprint'] == FINGERPRINT
        return result
    old = legacy_setting(q, alpha)
    if old:
        encoding, balance = old
        result = joblib.load(LEGACY / f'reference_{encoding}_{balance}_k{k}.joblib')
        assert result['fingerprint'] == LEGACY_FINGERPRINT
        result = dict(result, status='ok', source='original fingerprint-checked reference')
    else:
        X = profile_matrix(DATA, q, alpha)
        result = fit_labels(X, np.arange(len(DATA)), k, DESIGN['reference_seed'])
        result['source'] = 'new reference fit'
    labels = result['labels']
    shares = np.bincount(labels, weights=WEIGHTS, minlength=k)
    result.update(fingerprint=FINGERPRINT, q=q, alpha=alpha, k=k,
                  largest=float(shares.max()), dominance=float(k * shares.max()),
                  structural_pass=bool(len(np.unique(labels)) == k and shares.max() <= .4 and k * shares.max() < 3))
    joblib.dump(result, path)
    return result


def evaluate(task):
    q, alpha, k, phase = task
    identifier = trial_id(q, alpha, k)
    summary_path = OUTPUT / phase / (identifier + '.json')
    if summary_path.exists():
        summary = json.loads(summary_path.read_text())
        assert summary['fingerprint'] == FINGERPRINT
        return summary
    reference = reference_fit(q, alpha, k)
    summary = {key: reference[key] for key in ['q', 'alpha', 'k', 'largest', 'dominance', 'structural_pass']}
    summary.update(trial=identifier, t=1 / q, phase=phase, fingerprint=FINGERPRINT,
                   reference_source=reference['source'], fits_new=0, fits_reused=0, failures=0)
    if not reference['structural_pass']:
        summary.update(status='structurally ineligible', score=None)
        summary_path.write_text(json.dumps(summary, indent=2))
        return summary
    X = profile_matrix(DATA, q, alpha)
    old = legacy_setting(q, alpha)
    for kind, samples in PLANS[phase].items():
        partitions = []
        for repeat, indices in enumerate(samples):
            fit_path = OUTPUT / 'fits' / f'{identifier}_{phase}_{kind}_{repeat:02d}.joblib'
            if fit_path.exists():
                result = joblib.load(fit_path)
                assert result['fingerprint'] == FINGERPRINT
                summary['fits_reused'] += 1
            elif phase == 'pilot' and old:
                encoding, balance = old
                result = joblib.load(LEGACY / 'fits' / f'{encoding}_{kind}_{repeat:02d}_{balance}_k{k}.joblib')
                assert result['fingerprint'] == LEGACY_FINGERPRINT
                result = dict(result, status='ok')
                summary['fits_reused'] += 1
            else:
                try:
                    seed = DESIGN[phase + '_fit_seed'] + repeat
                    result = fit_labels(X, indices, k, seed)
                except (MemoryError, ValueError, RuntimeError) as error:
                    result = {'status': 'failed', 'error': repr(error)}
                result['fingerprint'] = FINGERPRINT
                joblib.dump(result, fit_path)
                summary['fits_new'] += 1
            if result['status'] == 'ok':
                partitions.append(result['labels'])
            else:
                summary['failures'] += 1
        complete = len(partitions) == len(samples)
        scores = [adjusted_rand_score(a, b) for a, b in combinations(partitions, 2)] if complete else []
        summary[kind + '_fits'] = len(partitions)
        summary[kind + '_pairs'] = len(scores)
        summary[kind + '_median'] = float(np.median(scores)) if scores else None
        summary[kind + '_p10'] = float(np.quantile(scores, .1)) if scores else None
        np.save(OUTPUT / phase / f'{identifier}_{kind}_ari.npy', np.array(scores))
    values = [summary[kind + suffix] for kind in ['respondents', 'countries'] for suffix in ['_median', '_p10']]
    complete = all(value is not None for value in values)
    summary['score'] = min(summary['respondents_p10'], summary['countries_p10']) if complete else None
    summary['minimum_median'] = min(summary['respondents_median'], summary['countries_median']) if complete else None
    summary['stability_pass'] = bool(complete and min(values) >= .8)
    summary['status'] = 'complete' if complete else 'incomplete; see failure caches'
    summary_path.write_text(json.dumps(summary, indent=2))
    return summary


def rank_settings(table):
    candidates = table.loc[table.status.eq('complete') & table.structural_pass].copy()
    candidates['central_distance'] = (candidates.q - .5) ** 2 + (candidates.alpha - .5) ** 2
    return candidates.sort_values(['score', 'minimum_median', 'central_distance', 'q', 'alpha'],
                                  ascending=[False, False, True, True, True])


def refinement_points(table):
    points, seeds = [], []
    for k, group in table.groupby('k'):
        ranked = rank_settings(group)
        if ranked.empty:
            continue
        seed = ranked.iloc[0]
        seeds.append(seed.to_dict())
        axes = []
        for name in ['q', 'alpha']:
            grid = DESIGN[name + '_grid']
            value = float(seed[name])
            index = grid.index(value)
            axis = [value]
            if index > 0:
                axis.append((grid[index - 1] + value) / 2)
            if index < len(grid) - 1:
                axis.append((grid[index + 1] + value) / 2)
            axes.append(sorted(axis))
        points.extend((float(q), float(alpha), int(k), 'pilot') for q, alpha in product(*axes))
    return points, pd.DataFrame(seeds)
