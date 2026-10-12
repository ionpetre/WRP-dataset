# %% Imports and fixed candidate definitions
from pathlib import Path
from dataclasses import dataclass, asdict
import hashlib
import itertools
import json
import math
import platform
import traceback
import warnings
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, pairwise_distances_argmin
from scipy.optimize import linear_sum_assignment
from threadpoolctl import threadpool_limits

DOMAINS = ['food', 'water', 'crime', 'severe_weather', 'traffic', 'mental_health']
WORRY = ['worry_' + d for d in DOMAINS]
PERSONAL = ['harm_' + d + '_personal' for d in DOMAINS + ['work']]
KNOWN = ['harm_' + d + '_known_person' for d in DOMAINS + ['work']]
FEATURES = WORRY + PERSONAL + KNOWN
TRANSFORM_COLUMNS = ['centred_' + c for c in WORRY] + ['overall_worry'] + PERSONAL + KNOWN

@dataclass(frozen=True)
class Specification:
    name: str
    encoding: str
    top: float
    balance: str
    alpha: float
    global_k: int

SPECIFICATIONS = {
    'B': Specification('B', '012', 2., 'balanced', .5, 4),
    'E': Specification('E', '013', 3., 'worry_emphasized', .75, 8),
}
REGIONAL_DESIGN = {
    'version': 3, 'seed': 20261011, 'k_values': list(range(2, 11)),
    'n_init': 20, 'max_iter': 300, 'repetitions': 50, 'fraction': .8,
    'respondent_sampling': 'without replacement within each regional country',
    'country_sampling': '50 uniform samples without replacement of floor(0.8*N) countries; repeats across samples allowed and reported',
    'small_region_policy': 'leave-one-country-out for 2 to 4 countries',
    'one_country_policy': 'country stability unavailable',
    'pairwise_ari_threshold': .8,
    'global_structural_benchmark_only': {'k_min': 3, 'k_max': 10, 'coverage_min': .9,
                                        'largest_share_max': .4, 'dominance_max_exclusive': 3},
    'assignment': 'nearest centre in unchanged 21-feature geometry',
    'specifications': {name: asdict(spec) for name, spec in SPECIFICATIONS.items()},
}

def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

def digest_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def atomic_json(value, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False))
    temp.replace(path)

def atomic_joblib(value, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    joblib.dump(value, temp)
    temp.replace(path)

def table_write(table, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    table.to_csv(temp, index=False)
    temp.replace(path)

# %% Preserve the Week 4 feature geometry and equal-country weights
def transform(frame, spec):
    values = frame[FEATURES].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError('This specification requires complete observed worry and harm responses.')
    if not frame[WORRY].isin([0, 1, 2]).all().all():
        raise ValueError('Unexpected original worry code.')
    if not frame[PERSONAL + KNOWN].isin([0, 1]).all().all():
        raise ValueError('Unexpected binary harm code.')
    worry = np.where(values[:, :6] == 2, spec.top, values[:, :6]) / spec.top
    mean = worry.mean(axis=1, keepdims=True)
    multiplier = np.sqrt(spec.alpha / 6)
    return np.column_stack([(worry - mean) * multiplier, mean * multiplier,
                            values[:, 6:] * np.sqrt((1 - spec.alpha) / 14)])

def country_weights(frame):
    if not len(frame) or not np.isfinite(frame.WGT).all() or not frame.WGT.gt(0).all():
        raise ValueError('Survey weights must be finite and positive in a nonempty cohort.')
    result = frame.WGT / frame.groupby('COUNTRY_ISO3').WGT.transform('sum')
    result = result / frame.COUNTRY_ISO3.nunique()
    totals = result.groupby(frame.COUNTRY_ISO3).sum()
    assert np.allclose(totals, 1 / len(totals)) and np.isclose(result.sum(), 1)
    return result.to_numpy()

def prepare_development(root):
    root = Path(root)
    artifacts = root / 'course_artifacts'
    input_path = artifacts / 'week04_search_v4/stage1_eligible_development.parquet'
    split_path = artifacts / 'week03_country_split.csv'
    split = pd.read_csv(split_path)
    assert split.COUNTRY_ISO3.is_unique
    dev_countries = set(split.loc[split.country_split.eq('train'), 'COUNTRY_ISO3'])
    hold_countries = set(split.loc[split.country_split.eq('heldout_country'), 'COUNTRY_ISO3'])
    assert len(dev_countries) == 113 and len(hold_countries) == 29
    assert not dev_countries.intersection(hold_countries)
    raw = pd.read_parquet(input_path)  # Development-only input, never the held-out response file.
    assert raw.country_split.eq('train').all() and raw.WPID_RANDOM.is_unique
    assert set(raw.COUNTRY_ISO3) == dev_countries
    eligible = raw[WORRY].notna().sum(axis=1).ge(4) & raw[PERSONAL].notna().sum(axis=1).ge(4)
    complete = eligible & raw[FEATURES].notna().all(axis=1)
    data = raw.loc[complete].copy().reset_index(drop=True)
    audit = raw.assign(previous_eligible=eligible, complete=complete).groupby('COUNTRY_ISO3').agg(
        available_input=('WPID_RANDOM', 'size'), previous_eligible=('previous_eligible', 'sum'),
        complete=('complete', 'sum'))
    audit['retained_fraction'] = audit.complete / audit.available_input
    audit = split.loc[split.country_split.eq('train')].merge(audit, on='COUNTRY_ISO3', validate='one_to_one')
    audit['retained_of_prepared'] = audit.complete / audit.respondents
    region_rows = audit.groupby('GlobalRegion').agg(countries=('COUNTRY_ISO3', 'size'),
        prepared_respondents=('respondents', 'sum'), input_respondents=('available_input', 'sum'),
        complete_respondents=('complete', 'sum')).reset_index()
    dictionary_path = root / '23_wrp/WRP_2023_data_dictionary.csv'
    dictionary = pd.read_csv(dictionary_path)
    labels_text = dictionary.loc[dictionary.variable.eq('GlobalRegion'), 'value_labels'].iloc[0]
    region_labels = {int(pair.split(' = ', 1)[0]): pair.split(' = ', 1)[1]
                     for pair in labels_text.split(' | ')}
    region_rows['region_name'] = region_rows.GlobalRegion.map(region_labels)
    region_rows['country_diagnostic'] = np.where(region_rows.countries.eq(1),
                                                 'unavailable: one country', 'pending sampling-plan audit')
    region_map = split.set_index('COUNTRY_ISO3').GlobalRegion
    data['GlobalRegion'] = data.COUNTRY_ISO3.map(region_map)
    data['CountryIncomeLevel'] = data.COUNTRY_ISO3.map(split.set_index('COUNTRY_ISO3').CountryIncomeLevel)
    assert len(data) == 109488 and data.COUNTRY_ISO3.nunique() == 113
    for spec in SPECIFICATIONS.values():
        assert transform(data, spec).shape == (len(data), 21)
    input_hash = file_sha256(input_path)
    provenance = {'development_input': str(input_path.relative_to(root)), 'input_sha256': input_hash,
                  'country_split_sha256': file_sha256(split_path),
                  'region_dictionary_sha256': file_sha256(dictionary_path),
                  'python': platform.python_version(), 'sklearn': sklearn.__version__,
                  'numpy': np.__version__, 'pandas': pd.__version__, 'joblib': joblib.__version__}
    references = {}
    reference_dir = artifacts / 'week04_experiment1_complete_overall_worry_v3'
    design_path = reference_dir / 'design.json'
    old_design = json.loads(design_path.read_text())
    # Exact legacy fingerprint rule; preserves the existing cache contract.
    digest = hashlib.sha256()
    with input_path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    digest.update(json.dumps(old_design, sort_keys=True).encode())
    expected_fingerprint = digest.hexdigest()
    for name, spec in SPECIFICATIONS.items():
        path = reference_dir / f'reference_{spec.encoding}_{spec.balance}_k{spec.global_k}.joblib'
        cached = joblib.load(path)  # Trusted local course cache only.
        if cached.get('fingerprint') != expected_fingerprint:
            raise ValueError(f'{name}: Week 4 cache fingerprint does not match data and design.')
        labels = cached['labels']
        if len(labels) != len(data):
            raise ValueError('Reference row order/length changed.')
        matrix = transform(data, spec)
        with threadpool_limits(limits=1):
            predicted = pairwise_distances_argmin(matrix, cached['centres'])
        if not np.array_equal(predicted, labels):
            raise ValueError(f'{name}: reloaded centres do not reproduce the stored development labels.')
        references[name] = {'labels': labels, 'centres': cached['centres'], 'spec': asdict(spec),
                            'source_sha256': file_sha256(path), 'fingerprint': cached['fingerprint']}
    provenance['reference_sources'] = {name: value['source_sha256'] for name, value in references.items()}
    provenance['reference_design_sha256'] = file_sha256(design_path)
    return data, audit, region_rows, references, provenance

def previous_stability(root):
    table = pd.read_csv(Path(root) / 'course_artifacts/week04_experiment1_complete_overall_worry_v3/stability_all_encodings.csv',
                        dtype={'encoding': str})
    rows = []
    for name, spec in SPECIFICATIONS.items():
        selected = table.loc[table.encoding.str.zfill(3).eq(spec.encoding)
                             & table.balance.eq(spec.balance) & table.k.eq(spec.global_k)].copy()
        assert set(selected.experiment) == {'countries', 'respondents'}
        selected.insert(0, 'candidate', name)
        rows.append(selected)
    return pd.concat(rows, ignore_index=True)

# %% Label-independent overlap, structural metrics, and original-unit profiles
def structure(labels, weights):
    labels = np.asarray(labels)
    groups = np.unique(labels[labels >= 0])
    coverage = float(weights[labels >= 0].sum())
    shares = [float(weights[labels == group].sum() / coverage) for group in groups] if coverage else []
    largest = max(shares) if shares else np.nan
    dominance = len(groups) * largest
    return {'observed_k': len(groups), 'coverage': coverage, 'largest_share': largest,
            'dominance': dominance,
            'global_benchmark_pass': bool(3 <= len(groups) <= 10 and coverage >= .9
                                          and largest <= .4 and dominance < 3)}

def compare_partitions(local, global_labels, weights):
    local_groups, local_index = np.unique(local, return_inverse=True)
    global_groups, global_index = np.unique(global_labels, return_inverse=True)
    overlap = np.zeros((len(local_groups), len(global_groups)))
    np.add.at(overlap, (local_index, global_index), weights)
    row_sum = overlap.sum(axis=1, keepdims=True)
    col_sum = overlap.sum(axis=0, keepdims=True)
    local_purity = overlap.max(axis=1).sum() / overlap.sum()
    global_purity = overlap.max(axis=0).sum() / overlap.sum()
    matched_rows, matched_cols = linear_sum_assignment(-overlap)
    records = []
    for i, lg in enumerate(local_groups):
        for j, gg in enumerate(global_groups):
            records.append({'local_cluster': int(lg), 'global_cluster': int(gg),
                'joint_share': overlap[i, j], 'global_given_local': overlap[i, j] / row_sum[i, 0],
                'local_given_global': overlap[i, j] / col_sum[0, j]})
    return {'ari_unweighted': adjusted_rand_score(local, global_labels),
            'local_to_global_purity': local_purity, 'global_to_local_purity': global_purity,
            'one_to_one_matched_share': overlap[matched_rows, matched_cols].sum() / overlap.sum()}, pd.DataFrame(records)

def original_profiles(frame, labels, weights):
    rows = []
    for group in np.unique(labels):
        inside = labels == group
        for feature in FEATURES:
            for category in ([0, 1, 2] if feature in WORRY else [0, 1]):
                response = frame[feature].to_numpy() == category
                proportion = weights[inside & response].sum() / weights[inside].sum()
                outside = ~inside
                outside_proportion = (weights[outside & response].sum() / weights[outside].sum()
                                      if outside.any() else np.nan)
                rows.append({'cluster': int(group), 'cluster_share': weights[inside].sum(),
                    'feature': feature, 'category': category, 'proportion': proportion,
                    'outside_proportion': outside_proportion,
                    'difference_vs_outside': proportion - outside_proportion})
    return pd.DataFrame(rows)

# %% Sampling plans fixed from metadata before any regional model fitting
def make_regional_plans(frame, region, design):
    names = sorted(frame.COUNTRY_ISO3.unique())
    indices = {name: np.flatnonzero(frame.COUNTRY_ISO3.to_numpy() == name) for name in names}
    repetitions = design['repetitions']
    seed = design['seed'] + int(region) * 10000
    respondent = []
    for repeat in range(repetitions):
        rng = np.random.default_rng(seed + repeat)
        respondent.append(np.sort(np.concatenate([
            rng.choice(idx, max(1, round(design['fraction'] * len(idx))), replace=False)
            for idx in indices.values()])))
    if len(names) == 1:
        subsets, kind = [], 'unavailable_one_country'
        subset_count = 0
    else:
        selected = min(len(names) - 1, max(1, math.floor(design['fraction'] * len(names))))
        subset_count = math.comb(len(names), selected)
        if len(names) < 5:
            subsets = [tuple(name for name in names if name != omitted) for omitted in names]
            kind = 'leave_one_country_out'
        else:
            rng = np.random.default_rng(seed + 5000)
            subsets = [tuple(sorted(rng.choice(names, selected, replace=False))) for _ in range(repetitions)]
            kind = 'random_country_subsamples'
    country = [np.flatnonzero(frame.COUNTRY_ISO3.isin(subset).to_numpy()) for subset in subsets]
    audit = [{'country': name, 'omitted_count': sum(name not in subset for subset in subsets),
              'country_evaluations': len(subsets), 'diagnostic': kind} for name in names]
    info = {'country_diagnostic': kind, 'country_fit_count': len(subsets),
            'distinct_country_fits': len(set(subsets)), 'possible_80pct_subsets': subset_count,
            'country_stability_claim_available': kind == 'random_country_subsamples'}
    return {'respondents': respondent, 'countries': country}, pd.DataFrame(audit), info

# %% Cached regional K-means fits with numerical diagnostics and recorded failures
def cached_kmeans(frame, spec, k, training_rows, seed, cache_dir, context, tag, force_retry=False, full_matrix=None):
    payload = {'context': context, 'spec': asdict(spec), 'k': int(k), 'seed': int(seed), 'tag': tag,
               'training_rows_hash': hashlib.sha256(np.asarray(training_rows, dtype=np.int64).tobytes()).hexdigest()}
    key = digest_json(payload)
    path = Path(cache_dir) / (key + '.joblib')
    if path.exists():
        saved = joblib.load(path)
        if saved.get('cache_key') != key:
            raise ValueError('Corrupt or stale regional cache.')
        if saved['status'] == 'ok' or not force_retry:
            return saved
        # Explicit retry preserves previous failures.
        history_path = path.with_name(path.stem + '_failure_' + file_sha256(path)[:12] + '.joblib')
        if not history_path.exists():
            atomic_joblib(saved, history_path)
    result = {'cache_key': key, 'payload': payload, 'status': 'failed', 'labels': None}
    try:
        training = frame.iloc[training_rows]
        if len(training) < k:
            raise ValueError('Fewer training respondents than requested clusters.')
        with threadpool_limits(limits=1), warnings.catch_warnings(record=True) as caught:
            matrix = transform(frame, spec) if full_matrix is None else full_matrix
            model = KMeans(n_clusters=k, n_init=20, max_iter=300, random_state=seed)
            model.fit(matrix[training_rows], sample_weight=country_weights(training))
            labels = model.predict(matrix).astype('int16')
        # A max-iteration stop is retained as a fitting limitation, not a silently successful fit.
        if model.n_iter_ >= 300:
            raise RuntimeError('K-means reached the declared iteration limit.')
        if len(np.unique(labels)) != k:
            raise RuntimeError('The requested number of nonempty clusters was not recovered.')
        result.update(status='ok', labels=labels, centres=model.cluster_centers_,
                      iterations=int(model.n_iter_), inertia=float(model.inertia_),
                      warnings=[str(w.message) for w in caught])
    except (ValueError, RuntimeError, MemoryError) as error:
        result.update(error=str(error), traceback=traceback.format_exc())
    atomic_joblib(result, path)
    return result

def pairwise_stability(results, reference):
    good = [r['labels'] for r in results if r['status'] == 'ok']
    pairwise = [adjusted_rand_score(a, b) for a, b in itertools.combinations(good, 2)]
    reference_ari = [adjusted_rand_score(a, reference) for a in good]
    return {'requested_fits': len(results), 'successful_fits': len(good),
            'failed_fits': len(results) - len(good), 'pairwise_count': len(pairwise),
            'median_pairwise': float(np.median(pairwise)) if pairwise else np.nan,
            'p10_pairwise': float(np.quantile(pairwise, .1)) if pairwise else np.nan,
            'minimum_pairwise': float(np.min(pairwise)) if pairwise else np.nan,
            'median_reference': float(np.median(reference_ari)) if reference_ari else np.nan,
            'p10_reference': float(np.quantile(reference_ari, .1)) if reference_ari else np.nan}, np.asarray(pairwise), np.asarray(reference_ari)

# %% Regional search and comparisons without held-out access
def regional_references(data, references, design, output_dir, context):
    output_dir = Path(output_dir)
    summary, overlaps, profile_tables = [], [], []
    fitted = {}
    for region in sorted(data.GlobalRegion.unique()):
        mask = data.GlobalRegion.eq(region).to_numpy()
        frame = data.loc[mask].reset_index(drop=True)
        weights = country_weights(frame)
        for name, spec in SPECIFICATIONS.items():
            full_matrix = transform(frame, spec)
            for k in design['k_values']:
                tag = f'region_{region}_{name}_k{k}_reference'
                result = cached_kmeans(frame, spec, k, np.arange(len(frame)), design['seed'] + int(region),
                                       output_dir / 'fits', context, tag, full_matrix=full_matrix)
                fitted[(int(region), name, int(k))] = result
                row = {'region': int(region), 'candidate': name, 'k': k, 'status': result['status'],
                       'matched_global_resolution': k == spec.global_k, 'countries': frame.COUNTRY_ISO3.nunique(),
                       'respondents': len(frame)}
                if result['status'] == 'ok':
                    row.update(structure(result['labels'], weights))
                    comparison, overlap = compare_partitions(result['labels'], references[name]['labels'][mask], weights)
                    row.update(comparison, iterations=result['iterations'], inertia=result['inertia'])
                    for col, value in [('region', int(region)), ('candidate', name), ('k', k)]:
                        overlap[col] = value
                    overlaps.append(overlap)
                    profiles = original_profiles(frame, result['labels'], weights)
                    profiles['region'], profiles['candidate'], profiles['k'] = int(region), name, k
                    profile_tables.append(profiles)
                else:
                    row['error'] = result['error']
                summary.append(row)
                table_write(pd.DataFrame(summary), output_dir / 'regional_reference_summary.csv')
                print(f'Region {region}, {name}, k={k}: {result["status"]}', flush=True)
    table_write(pd.concat(overlaps, ignore_index=True) if overlaps else pd.DataFrame(), output_dir / 'regional_overlaps.csv')
    table_write(pd.concat(profile_tables, ignore_index=True) if profile_tables else pd.DataFrame(), output_dir / 'regional_original_profiles.csv')
    return pd.DataFrame(summary), fitted

def regional_stability(data, fitted, shortlist, design, output_dir, context, n_jobs=2):
    # Every selection is recorded before the stability stage. Matched B4/E8 are the starting set.
    output_dir = Path(output_dir)
    table_write(pd.DataFrame(shortlist, columns=['region', 'candidate', 'k']), output_dir / 'regional_stability_shortlist.csv')
    summaries, plan_rows, pair_rows = [], [], []
    for region in sorted({int(item[0]) for item in shortlist}):
        frame = data.loc[data.GlobalRegion.eq(region)].reset_index(drop=True)
        plans, omission, plan_info = make_regional_plans(frame, region, design)
        omission['region'] = region
        table_write(omission, output_dir / f'region_{region}_country_omissions.csv')
        for kind, samples in plans.items():
            for repeat, rows in enumerate(samples):
                plan_rows.append({'region': region, 'test': kind, 'repeat': repeat, 'respondents': len(rows),
                    'country_list': ' '.join(sorted(frame.iloc[rows].COUNTRY_ISO3.unique())), **plan_info})
        atomic_joblib({'context': context, 'plans': plans, 'info': plan_info}, output_dir / f'region_{region}_sampling_plans.joblib')
        for _, name, k in [item for item in shortlist if int(item[0]) == region]:
            ref = fitted[(region, name, k)]
            if ref['status'] != 'ok':
                summaries.append({'region': region, 'candidate': name, 'k': k, 'status': 'reference_failed'})
                continue
            for kind, samples in plans.items():
                full_matrix = transform(frame, SPECIFICATIONS[name])
                from joblib import Parallel, delayed, parallel_config
                with parallel_config(backend='loky', inner_max_num_threads=1):
                    results = Parallel(n_jobs=n_jobs)(delayed(cached_kmeans)(
                        frame, SPECIFICATIONS[name], k, training,
                        design['seed'] + region * 10000 + 1000 + repeat,
                        output_dir / 'fits', context, f'region_{region}_{name}_k{k}_{kind}_{repeat:02d}',
                        full_matrix=full_matrix) for repeat, training in enumerate(samples))
                print(f'Region {region}, {name}, k={k}, {kind}: {sum(r["status"] == "ok" for r in results)}/{len(samples)} fits succeeded', flush=True)
                stats, pairwise, ref_ari = pairwise_stability(results, ref['labels'])
                numerical_pass = (stats['successful_fits'] == len(samples) and len(samples) >= 2
                                  and stats['median_pairwise'] >= .8 and stats['p10_pairwise'] >= .8)
                formal_pass = numerical_pass and len(samples) == 50
                if kind == 'countries' and plan_info['country_diagnostic'] != 'random_country_subsamples':
                    formal_pass = False  # LOO summaries are diagnostics, not the 50-fit country-stability claim.
                summaries.append({'region': region, 'candidate': name, 'k': k, 'test': kind,
                    'status': 'complete' if samples else 'unavailable', **stats, **plan_info,
                    'numerical_ari_benchmark_met': bool(numerical_pass),
                    'full_50_fit_stability_benchmark_met': bool(formal_pass)})
                for pair, ari in enumerate(pairwise):
                    pair_rows.append({'region': region, 'candidate': name, 'k': k, 'test': kind,
                                      'pair_number': pair, 'ari_unweighted': float(ari)})
                table_write(pd.DataFrame(summaries), output_dir / 'regional_stability_summary.csv')
                failure_rows = [{'region': region, 'candidate': name, 'k': k, 'test': kind,
                                 'repeat': i, 'error': r.get('error', '')}
                                for i,r in enumerate(results) if r['status'] != 'ok']
                if failure_rows:
                    existing_path = output_dir / 'regional_failures.csv'
                    previous = pd.read_csv(existing_path) if existing_path.exists() else pd.DataFrame()
                    table_write(pd.concat([previous, pd.DataFrame(failure_rows)]).drop_duplicates(), existing_path)
    table_write(pd.DataFrame(plan_rows), output_dir / 'regional_sampling_plan_audit.csv')
    table_write(pd.DataFrame(pair_rows), output_dir / 'regional_pairwise_ari.csv')
    return pd.DataFrame(summaries)

# %% Frozen-model preparation only No freeze decision or held-out access
def freeze_checklist(data, references):
    # Descriptive preparation; never writes a final model or marks the decision approved.
    rows = []
    for name, spec in SPECIFICATIONS.items():
        weights = country_weights(data)
        rows.append({'candidate': name, 'k': spec.global_k, 'encoding': spec.encoding,
            'alpha': spec.alpha, 'assignment_reload_verified': True,
            **structure(references[name]['labels'], weights),
            'regional_analysis_complete': False, 'final_scope_approved': False,
            'holdout_access_authorized': False})
    return pd.DataFrame(rows)

# %% Fixed global assignments by country and region
WORKING_PROFILE_LABELS = {
    'B': {0: 'Broad harm exposure, especially known-person harm',
          1: 'Crime, severe-weather and traffic worry with lower harm',
          2: 'Food and water worry with substantial crime worry',
          3: 'Lower overall worry and harm'},
    'E': {0: 'Traffic-focused worry', 1: 'Lower worry intensity',
          2: 'Mental-health worry with other non-food/water worries',
          3: 'Crime and traffic worry', 4: 'Crime-focused worry',
          5: 'Severe-weather-focused worry', 6: 'Food and water worry',
          7: 'Broad high worry'},
}

def fixed_global_geographical_results(data, references, regions, output_dir):
    """Describe the saved global partitions; never fit a model or open held-out data."""
    prevalence_rows, profile_tables, semantic_rows = [], [], []
    region_names = regions.set_index('GlobalRegion').region_name.to_dict()
    for name, spec in SPECIFICATIONS.items():
        full_labels = references[name]['labels']
        weights = country_weights(data)
        global_profiles = original_profiles(data, full_labels, weights)
        global_profiles['candidate'] = name
        global_lookup = global_profiles.set_index(['cluster', 'feature', 'category']).proportion
        scopes = [('global', 'global_development', 'Global development', np.ones(len(data), dtype=bool))]
        scopes += [('region', str(int(region)), region_names[region], data.GlobalRegion.eq(region).to_numpy())
                   for region in sorted(data.GlobalRegion.unique())]
        scopes += [('country', country, country, data.COUNTRY_ISO3.eq(country).to_numpy())
                   for country in sorted(data.COUNTRY_ISO3.unique())]
        for scope, key, label, mask in scopes:
            frame = data.loc[mask]
            assigned = full_labels[mask]
            local_weights = country_weights(frame)
            country_count = frame.COUNTRY_ISO3.nunique()
            for cluster in range(spec.global_k):
                inside = assigned == cluster
                prevalence_rows.append({'candidate': name, 'scope': scope, 'area_id': key, 'area_name': label,
                    'cluster': cluster, 'working_description': WORKING_PROFILE_LABELS[name][cluster],
                    'respondents': int(inside.sum()), 'area_respondents': len(frame),
                    'area_countries': country_count, 'respondent_share': float(inside.mean()),
                    'equal_country_weighted_share': float(local_weights[inside].sum())})
            # Full original-unit distributions globally and regionally. These permit examination
            # of profile meaning rather than presuming fixed labels imply identical responses.
            if scope != 'country':
                profiles = original_profiles(frame, assigned, local_weights)
                profiles['candidate'], profiles['scope'] = name, scope
                profiles['area_id'], profiles['area_name'] = key, label
                profiles['global_proportion'] = [global_lookup.loc[(r.cluster, r.feature, r.category)]
                                                  for r in profiles.itertuples()]
                profiles['difference_from_global_pp'] = 100 * (profiles.proportion - profiles.global_proportion)
                profile_tables.append(profiles)
                for cluster in sorted(np.unique(assigned)):
                    group = profiles.loc[profiles.cluster.eq(cluster)]
                    extreme = group.loc[group.difference_from_global_pp.abs().idxmax()]
                    semantic_rows.append({'candidate': name, 'scope': scope, 'area_id': key, 'area_name': label,
                        'cluster': int(cluster), 'respondents': int((assigned == cluster).sum()),
                        'largest_absolute_category_difference_pp': abs(extreme.difference_from_global_pp),
                        'feature': extreme.feature, 'category': int(extreme.category),
                        'regional_proportion': float(extreme.proportion),
                        'global_proportion': float(extreme.global_proportion),
                        'signed_difference_pp': float(extreme.difference_from_global_pp)})
    prevalence = pd.DataFrame(prevalence_rows)
    profiles = pd.concat(profile_tables, ignore_index=True)
    semantics = pd.DataFrame(semantic_rows)
    for (_, _, _), group in prevalence.groupby(['candidate', 'scope', 'area_id']):
        assert np.isclose(group.equal_country_weighted_share.sum(), 1)
        assert np.isclose(group.respondent_share.sum(), 1)
        assert group.respondents.sum() == group.area_respondents.iloc[0]
    # Global shares are the country-count-weighted mixture of regional shares.
    for name in SPECIFICATIONS:
        global_rows = prevalence.loc[prevalence.candidate.eq(name) & prevalence.scope.eq('global')]
        local_rows = prevalence.loc[prevalence.candidate.eq(name) & prevalence.scope.eq('region')]
        for cluster in global_rows.cluster:
            local = local_rows.loc[local_rows.cluster.eq(cluster)]
            reconstructed = np.average(local.equal_country_weighted_share, weights=local.area_countries)
            expected = global_rows.loc[global_rows.cluster.eq(cluster), 'equal_country_weighted_share'].iloc[0]
            assert np.isclose(reconstructed, expected, atol=1e-12)
    table_write(prevalence, Path(output_dir) / 'fixed_global_profile_prevalence.csv')
    table_write(profiles, Path(output_dir) / 'fixed_global_original_profiles_by_region.csv')
    table_write(semantics, Path(output_dir) / 'fixed_global_regional_semantic_differences.csv')
    return prevalence, profiles, semantics

# %% Fixed-global representation quality and map-ready country summaries
def weighted_quantile(values, weights, probability):
    order = np.argsort(values, kind='stable')
    cumulative = np.cumsum(weights[order]) / np.sum(weights)
    return float(np.asarray(values)[order][min(np.searchsorted(cumulative, probability), len(order)-1)])

def fixed_assignment_quality(data, references, regions, output_dir):
    from scipy.spatial.distance import cdist
    regional_names = regions.set_index('GlobalRegion').region_name.to_dict()
    summaries, thresholds, assignment_tables = [], [], []
    for name, spec in SPECIFICATIONS.items():
        weights = country_weights(data)
        with threadpool_limits(limits=1):
            distances = cdist(transform(data, spec), references[name]['centres'], metric='euclidean')
        ordered = np.sort(distances, axis=1)
        nearest, second = ordered[:,0], ordered[:,1]
        margin = np.divide(second-nearest, second, out=np.zeros_like(second), where=second>0)
        labels = references[name]['labels']
        assert np.array_equal(distances.argmin(axis=1), labels)
        cutoff = {}
        for cluster in range(spec.global_k):
            inside = labels == cluster
            cutoff[cluster] = weighted_quantile(nearest[inside], weights[inside], .95)
            thresholds.append({'candidate': name, 'cluster': cluster, 'development_distance_p95': cutoff[cluster]})
        exceed = nearest > np.array([cutoff[int(c)] for c in labels])
        assigned = data[['WPID_RANDOM','COUNTRY_ISO3','GlobalRegion']].copy()
        assigned['candidate'], assigned['cluster'] = name, labels
        assigned['nearest_distance'], assigned['margin'] = nearest, margin
        assigned['beyond_development_profile_p95'] = exceed
        assignment_tables.append(assigned)
        scopes = [('global','global_development','Global development', np.ones(len(data),bool))]
        scopes += [('region',str(int(r)),regional_names[r],data.GlobalRegion.eq(r).to_numpy()) for r in sorted(data.GlobalRegion.unique())]
        scopes += [('country',c,c,data.COUNTRY_ISO3.eq(c).to_numpy()) for c in sorted(data.COUNTRY_ISO3.unique())]
        for scope,key,label,mask in scopes:
            local_weights = country_weights(data.loc[mask])
            for cluster in [None] + list(range(spec.global_k)):
                select = np.ones(mask.sum(),bool) if cluster is None else labels[mask] == cluster
                if not select.any():
                    continue
                ww = local_weights[select]
                summaries.append({'candidate':name, 'scope':scope,'area_id':key,'area_name':label,
                    'cluster': -1 if cluster is None else cluster, 'respondents':int(select.sum()),
                    'distance_median':weighted_quantile(nearest[mask][select],ww,.5),
                    'distance_p90':weighted_quantile(nearest[mask][select],ww,.9),
                    'margin_median':weighted_quantile(margin[mask][select],ww,.5),
                    'margin_p10':weighted_quantile(margin[mask][select],ww,.1),
                    'profile_p95_exceedance':float(np.average(exceed[mask][select],weights=ww))})
    table_write(pd.DataFrame(thresholds),Path(output_dir)/'development_distance_thresholds_provisional.csv')
    table_write(pd.DataFrame(summaries),Path(output_dir)/'fixed_global_assignment_quality.csv')
    table_write(pd.concat(assignment_tables),Path(output_dir)/'development_fixed_assignments_with_quality.csv')
    return pd.DataFrame(summaries), pd.DataFrame(thresholds)

# %% Prevalence maps using external cartography only Not external responses
def prevalence_maps(prevalence, root, output_dir):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Patch
    from matplotlib.colors import Normalize
    from matplotlib.cm import ScalarMappable
    cartography = Path(root)/'course_artifacts/cartography/ne_50m_admin_0_countries.geojson'
    world = json.loads(cartography.read_text())
    registry = pd.read_csv(Path(root)/'course_artifacts/week03_country_split.csv')
    heldout = set(registry.loc[registry.country_split.eq('heldout_country'),'COUNTRY_ISO3'])
    features = world['features']
    mapping = {}
    for feature in features:
        p = feature['properties']
        code = p.get('ADM0_A3')
        if code in ['KOS','SDS']:
            code = {'KOS':'XKX','SDS':'SSD'}[code]
        mapping[code] = feature
    dev = set(registry.loc[registry.country_split.eq('train'),'COUNTRY_ISO3'])
    missing = sorted(dev-set(mapping))
    if missing:
        raise ValueError('Country-map keys missing: '+', '.join(missing))
    cmap = plt.get_cmap('viridis')
    norm = Normalize(0,100)
    plots = Path(output_dir)/'figures'; plots.mkdir(exist_ok=True)
    files = []
    for name,spec in SPECIFICATIONS.items():
        nrows = 2 if name == 'B' else 4
        fig, axes = plt.subplots(nrows,2,figsize=(15,4*nrows),squeeze=False)
        for cluster,ax in enumerate(axes.ravel()):
            selected = prevalence.loc[prevalence.candidate.eq(name)&prevalence.scope.eq('country')&prevalence.cluster.eq(cluster)]
            values = (selected.set_index('area_id').equal_country_weighted_share*100).to_dict()
            for code,feature in mapping.items():
                if code == 'ATA':
                    continue
                geometry = feature['geometry']
                polygons = geometry['coordinates'] if geometry['type']=='MultiPolygon' else [geometry['coordinates']]
                colour = cmap(norm(values[code])) if code in values else ('#c7c7c7' if code in heldout else '#eeeeee')
                for polygon in polygons:
                    points = np.array(polygon[0])
                    ax.add_patch(Polygon(points, closed=True,facecolor=colour, edgecolor='#858585',linewidth=.18,
                                         hatch='///' if code in heldout else None))
                if code in values:
                    p=feature['properties']
                    bounds=np.array(polygons[0][0])
                    if np.ptp(bounds[:,0])*np.ptp(bounds[:,1])<2:
                        ax.scatter(float(p['LABEL_X']),float(p['LABEL_Y']),s=18,color=colour,edgecolor='black',linewidth=.3,zorder=5)
            ax.set_xlim(-180,180);ax.set_ylim(-60,85);ax.set_aspect('equal')
            ax.set_xticks([]);ax.set_yticks([])
            ax.set_title(f'{name} C{cluster}: {WORKING_PROFILE_LABELS[name][cluster]}',fontsize=11)
            ax.set_facecolor('#f4f8fc')
        fig.subplots_adjust(left=.02,right=.90,bottom=.08,top=.94,hspace=.20)
        bar=fig.colorbar(ScalarMappable(norm=norm,cmap=cmap),cax=fig.add_axes([.92,.20,.015,.60]))
        bar.set_label('Within-country survey-weighted profile share (%)')
        fig.legend(handles=[Patch(facecolor='#c7c7c7',hatch='///',label='Held-out: responses unopened'),
                            Patch(facecolor='#eeeeee',label='No development data')],loc='lower center',ncol=2)
        fig.suptitle(f'{name}: fixed global profiles in development countries',fontsize=17)
        fig.text(.02,.025,'Complete cases only. Tiny countries use dots. Natural Earth boundaries; de facto depiction is not a political claim.',fontsize=9)
        path=plots/f'{name}_fixed_global_prevalence_maps.png'
        fig.savefig(path,dpi=160,bbox_inches='tight');plt.close(fig);files.append(path)
    atomic_json({'source_url':'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson',
                 'source_sha256':file_sha256(cartography),'cartography_only':True,'development_keys_matched':len(dev),
                 'missing_development_keys':missing},Path(output_dir)/'map_source_audit.json')
    return files

# %% Semantic correspondence of matched-resolution regional fits
def matched_regional_semantics(root_profiles, fixed_profiles, overlaps, output_dir):
    rows=[]
    global_table=fixed_profiles.loc[fixed_profiles.scope.eq('global')]
    for name,spec in SPECIFICATIONS.items():
        local=root_profiles.loc[root_profiles.candidate.eq(name)&root_profiles.k.eq(spec.global_k)]
        for (region,cluster),group in local.groupby(['region','cluster']):
            cross=overlaps.loc[overlaps.candidate.eq(name)&overlaps.k.eq(spec.global_k)&overlaps.region.eq(region)&overlaps.local_cluster.eq(cluster)]
            top=cross.loc[cross.global_given_local.idxmax()]
            reference=global_table.loc[global_table.candidate.eq(name)&global_table.cluster.eq(top.global_cluster)]
            aligned=group.merge(reference[['feature','category','proportion']],on=['feature','category'],suffixes=('_local','_global'),validate='one_to_one')
            aligned['absolute_difference']=abs(aligned.proportion_local-aligned.proportion_global)
            feature_tv=aligned.groupby('feature').absolute_difference.sum()/2
            strongest=aligned.loc[aligned.absolute_difference.idxmax()]
            rows.append({'region':int(region),'candidate':name,'k':spec.global_k,'local_cluster':int(cluster),
                'associated_global_cluster':int(top.global_cluster),'dominant_global_fraction':float(top.global_given_local),
                'working_global_description':WORKING_PROFILE_LABELS[name][int(top.global_cluster)],
                'mean_original_feature_TV':float(feature_tv.mean()),
                'max_category_difference_pp':100*float(strongest.absolute_difference),
                'max_difference_feature':strongest.feature,'max_difference_category':int(strongest.category),
                'local_cluster_share':float(group.cluster_share.iloc[0])})
    result=pd.DataFrame(rows)
    table_write(result,Path(output_dir)/'matched_regional_semantic_correspondence.csv')
    return result
