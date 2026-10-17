"""Run the predeclared coarse-to-fine search, resuming only matching caches."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import product
import fcntl
import hashlib
import json
import platform
import time
import joblib
import numpy as np
import pandas as pd
import sklearn
import search

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'course_artifacts/week04_kmeans_parameter_optimization'


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    source = ROOT / 'course_artifacts/week04_search_v4/stage1_eligible_development.parquet'
    old = ROOT / 'course_artifacts/week04_experiment1_complete_overall_worry_v3'
    inputs = [source, old / 'design.json', old / 'sampling_indices.joblib',
              ROOT / 'course_artifacts/week03_country_split.csv']
    provenance = {'design': search.DESIGN, 'inputs_sha256': {str(p.relative_to(ROOT)): file_hash(p) for p in inputs}}
    fingerprint = hashlib.sha256(json.dumps(provenance, sort_keys=True).encode()).hexdigest()
    output = BASE / fingerprint[:16]
    output.mkdir(parents=True, exist_ok=True)
    protocol = dict(provenance, fingerprint=fingerprint)
    path = output / 'protocol.json'
    if path.exists():
        assert json.loads(path.read_text()) == protocol
    else:
        path.write_text(json.dumps(protocol, indent=2))
    runtime = {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__,
               'sklearn': sklearn.__version__, 'search_code_sha256': file_hash(Path(search.__file__))}
    runtime_path = output / 'runtime.json'
    if runtime_path.exists():
        assert json.loads(runtime_path.read_text()) == runtime, 'Runtime or model code changed; start a new protocol version.'
    else:
        runtime_path.write_text(json.dumps(runtime, indent=2))
    for name in ['references', 'fits', 'pilot', 'confirmation']:
        (output / name).mkdir(exist_ok=True)
    protected = [ROOT / 'course_artifacts/week05_frozen_objective1_v1/123d248adda6115f/models.joblib',
                 ROOT / 'course_artifacts/week05_frozen_objective1_v1/123d248adda6115f/freeze_seal.json',
                 ROOT / 'course_artifacts/week05_objective1_handoff_v1/123d248adda6115f/all_respondents_eligibility_and_frozen_profiles.parquet']
    protected += list((ROOT / 'weekly_notebooks').glob('week0[356]*.ipynb'))
    protected_hashes = {str(p.relative_to(ROOT)): file_hash(p) for p in protected}
    protected_path = output / 'protected_sources.json'
    if protected_path.exists():
        assert json.loads(protected_path.read_text()) == protected_hashes
    else:
        protected_path.write_text(json.dumps(protected_hashes, indent=2))
    raw = pd.read_parquet(source)
    assert raw.country_split.eq('train').all()
    data = raw.loc[raw[search.FEATURES].notna().all(axis=1)].reset_index(drop=True)
    registry = pd.read_csv(ROOT / 'course_artifacts/week03_country_split.csv')
    registry = registry.loc[registry.country_split.eq('train')]
    plans, quota = search.make_country_and_respondent_plans(data, registry, 20261016, 50)
    plan_path = output / 'confirmation_sampling_indices.joblib'
    if plan_path.exists():
        saved = joblib.load(plan_path)
        assert all(np.array_equal(a, b) for kind in plans for a, b in zip(plans[kind], saved[kind]))
    else:
        joblib.dump(plans, plan_path)
    quota.to_csv(output / 'confirmation_stratum_quotas.csv')
    # A fresh deterministic plan must not accidentally duplicate the pilot plan.
    pilot = joblib.load(old / 'sampling_indices.joblib')
    assert all(not np.array_equal(plans[kind][r], pilot[kind][r]) for kind in plans for r in range(10))
    rows = []
    for kind, repetitions in plans.items():
        for repeat, indices in enumerate(repetitions):
            rows.append({'test': kind, 'repeat': repeat, 'respondents': len(indices),
                         'countries': data.iloc[indices].COUNTRY_ISO3.nunique(),
                         'country_list': ' '.join(sorted(data.iloc[indices].COUNTRY_ISO3.unique()))})
    pd.DataFrame(rows).to_csv(output / 'confirmation_sampling_audit.csv', index=False)
    (BASE / 'current_run.json').write_text(json.dumps({'output': str(output.relative_to(ROOT)), 'fingerprint': fingerprint}, indent=2))
    return output


def run_batch(pool, tasks, stage, output):
    results = []
    futures = [pool.submit(search.evaluate, task) for task in tasks]
    for future in as_completed(futures):
        result = future.result()
        results.append(result)
        if len(results) % 10 == 0 or len(results) == len(tasks):
            print(stage, len(results), '/', len(tasks), 'complete', flush=True)
        table = pd.DataFrame(results).sort_values(['k', 'q', 'alpha'])
        table.to_csv(output / (stage + '_results.csv'), index=False)
        status = {'stage': stage, 'completed_candidates': len(results), 'stage_candidates': len(tasks),
                  'new_repetition_fits_in_completed_candidates': int(table.fits_new.sum()),
                  'reused_repetition_fits_in_completed_candidates': int(table.fits_reused.sum()),
                  'failures_in_completed_candidates': int(table.failures.sum()), 'updated_epoch': time.time()}
        (output / 'progress.json').write_text(json.dumps(status, indent=2))
    return pd.DataFrame(results)


def main():
    BASE.mkdir(parents=True, exist_ok=True)
    lock = (BASE / 'run.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    output = prepare()
    print('OUTPUT', output, flush=True)
    coarse = [(q, a, k, 'pilot') for k, q, a in product(search.DESIGN['k_values'], search.DESIGN['q_grid'], search.DESIGN['alpha_grid'])]
    with ProcessPoolExecutor(max_workers=4, initializer=search.initialize, initargs=(str(ROOT), str(output))) as pool:
        coarse_results = run_batch(pool, coarse, 'coarse', output)
        fine, seeds = search.refinement_points(coarse_results)
        seeds.to_csv(output / 'refinement_seeds.csv', index=False)
        coarse_set = set(coarse)
        fine = sorted(set(fine) - coarse_set)
        pd.DataFrame(fine, columns=['q', 'alpha', 'k', 'phase']).to_csv(output / 'refinement_plan.csv', index=False)
        fine_results = run_batch(pool, fine, 'refinement', output) if fine else pd.DataFrame()
        combined = pd.concat([coarse_results, fine_results], ignore_index=True)
        combined.to_csv(output / 'all_pilot_results.csv', index=False)
        selected = []
        for k, group in combined.groupby('k'):
            selected.extend(search.rank_settings(group).head(2).to_dict('records'))
        shortlist = pd.DataFrame(selected)
        shortlist.to_csv(output / 'shortlist_before_confirmation.csv', index=False)
        confirmation = {(float(r.q), float(r.alpha), int(r.k), 'confirmation') for r in shortlist.itertuples()}
        confirmation.update({(.5, .5, 4, 'confirmation'), (1 / 3, .75, 8, 'confirmation')})
        pd.DataFrame(sorted(confirmation), columns=['q', 'alpha', 'k', 'phase']).to_csv(output / 'confirmation_plan.csv', index=False)
        confirmed = run_batch(pool, sorted(confirmation), 'full_confirmation', output)
        confirmed.to_csv(output / 'full_confirmation_results.csv', index=False)
    winners = []
    for k, group in confirmed.groupby('k'):
        ranked = search.rank_settings(group)
        if not ranked.empty:
            winners.append(ranked.iloc[0].to_dict())
    pd.DataFrame(winners).to_csv(output / 'best_tested_setting_per_k.csv', index=False)
    protected = json.loads((output / 'protected_sources.json').read_text())
    assert all(file_hash(ROOT / p) == digest for p, digest in protected.items())
    (output / 'completion.json').write_text(json.dumps({'status': 'completed', 'output': str(output),
        'coarse_candidates': len(coarse), 'refinement_candidates': len(fine), 'confirmation_candidates': len(confirmation),
        'protected_sources_unchanged': True, 'no_heldout_responses_loaded': True,
        'interpretation': 'exploratory development tuning; no replacement of frozen B/E or independent validation'}, indent=2))
    print('COMPLETED', output, flush=True)


if __name__ == '__main__':
    main()
