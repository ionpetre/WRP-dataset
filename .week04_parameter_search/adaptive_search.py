"""Bounded adaptive development search. Frozen B/E and the earlier search stay unchanged."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import fcntl
import hashlib
import json
import platform
import shutil
import sys
import time
import warnings

DEPENDENCIES = Path(__file__).resolve().parent / 'adaptive_dependencies'
if DEPENDENCIES.exists():
    sys.path.insert(0, str(DEPENDENCIES))
import optuna
import joblib
import numpy as np
import pandas as pd
import sklearn
import search

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'course_artifacts/week04_kmeans_adaptive_optimization'
PREVIOUS = ROOT / 'course_artifacts/week04_kmeans_parameter_optimization/8ecb97fd957f69f8'
DESIGN = dict(search.DESIGN, version=2, method='Optuna multivariate TPE; one sequential study per k',
    adaptive_new_trials_per_k=20, adaptive_seed_base=2026101600,
    adaptive_start='all 301 previous reference settings, with their original ten-resample pilot evidence',
    adaptive_constraints='structural failures get infeasible constraints and score -2; failed computations are failed trials',
    adaptive_budget='exactly twenty additional evaluations per k; no automatic extension or duplicate parameter pairs',
    confirmation_sample_seed=2026111600, confirmation_fit_seed=2026112600,
    confirmation_shortlist='top two completed structurally eligible pilots per k, plus unchanged B4/E8; frozen before new confirmation',
    previous_confirmation_use='not used as search objective; prior knowledge is acknowledged in the report',
    no_new_grid=True, frozen_models_unchanged=True)


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False))
    temporary.replace(path)


def save_study(path, study):
    temporary = path.with_suffix('.tmp')
    joblib.dump(study, temporary)
    temporary.replace(path)


def constraints(trial):
    return [0.0 if trial.user_attrs['structural_pass'] else 1.0]


def initialize_worker(output):
    search.initialize(ROOT, output)
    search.DESIGN = dict(search.DESIGN, confirmation_fit_seed=DESIGN['confirmation_fit_seed'])
    optuna.logging.set_verbosity(optuna.logging.WARNING)


def prepare():
    inputs = [PREVIOUS / name for name in ['protocol.json', 'runtime.json', 'all_pilot_results.csv', 'coarse_results.csv']]
    inputs += [ROOT / 'course_artifacts/week04_search_v4/stage1_eligible_development.parquet',
               ROOT / 'course_artifacts/week03_country_split.csv', Path(search.__file__)]
    provenance = {'design': DESIGN, 'inputs_sha256': {str(p.relative_to(ROOT)): file_hash(p) for p in inputs}}
    fingerprint = hashlib.sha256(json.dumps(provenance, sort_keys=True).encode()).hexdigest()
    output = BASE / fingerprint[:16]
    output.mkdir(parents=True, exist_ok=True)
    protocol = dict(provenance, fingerprint=fingerprint)
    if (output / 'protocol.json').exists():
        assert json.loads((output / 'protocol.json').read_text()) == protocol
    else:
        save_json(output / 'protocol.json', protocol)
    runtime = {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__,
               'sklearn': sklearn.__version__, 'optuna': optuna.__version__,
               'search_code_sha256': file_hash(search.__file__), 'runner_code_sha256': file_hash(__file__)}
    if (output / 'runtime.json').exists():
        assert json.loads((output / 'runtime.json').read_text()) == runtime, 'Do not resume after changing model code or runtime.'
    else:
        save_json(output / 'runtime.json', runtime)
    for name in ['references', 'fits', 'pilot', 'confirmation', 'studies']:
        (output / name).mkdir(exist_ok=True)
    protected = {name: file_hash(ROOT / name) for name in json.loads((PREVIOUS / 'protected_sources.json').read_text())}
    protected.update({str(p.relative_to(ROOT)): file_hash(p) for p in PREVIOUS.rglob('*') if p.is_file()})
    if (output / 'protected_sources.json').exists():
        assert json.loads((output / 'protected_sources.json').read_text()) == protected
    else:
        save_json(output / 'protected_sources.json', protected)
    # Import matching reference and pilot evidence, never the old confirmation scores.
    old_fingerprint = json.loads((PREVIOUS / 'protocol.json').read_text())['fingerprint']
    previous = pd.read_csv(PREVIOUS / 'all_pilot_results.csv')
    for row in previous.itertuples():
        identifier = row.trial
        ref_path = output / 'references' / (identifier + '.joblib')
        if not ref_path.exists():
            ref = joblib.load(PREVIOUS / 'references' / ref_path.name)
            assert ref['fingerprint'] == old_fingerprint
            assert identifier == search.trial_id(ref['q'], ref['alpha'], ref['k'])
            assert np.isclose(ref['q'], row.q) and np.isclose(ref['alpha'], row.alpha)
            ref.update(fingerprint=fingerprint, source='previous fingerprint-checked reference', source_fingerprint=old_fingerprint)
            joblib.dump(ref, ref_path)
        summary_path = output / 'pilot' / (identifier + '.json')
        if not summary_path.exists():
            result = json.loads((PREVIOUS / 'pilot' / summary_path.name).read_text())
            assert result['fingerprint'] == old_fingerprint
            result.update(fingerprint=fingerprint, source_fingerprint=old_fingerprint,
                          fits_reused=result['fits_new'] + result['fits_reused'], fits_new=0, origin='previous pilot')
            save_json(summary_path, result)
        for kind in ['respondents', 'countries']:
            array = PREVIOUS / 'pilot' / f'{identifier}_{kind}_ari.npy'
            if array.exists() and not (output / 'pilot' / array.name).exists():
                shutil.copy2(array, output / 'pilot' / array.name)
    if not (output / 'coarse_results.csv').exists():
        shutil.copy2(PREVIOUS / 'coarse_results.csv', output / 'coarse_results.csv')
    raw = pd.read_parquet(ROOT / 'course_artifacts/week04_search_v4/stage1_eligible_development.parquet')
    assert raw.country_split.eq('train').all()
    data = raw.loc[raw[search.FEATURES].notna().all(axis=1)].reset_index(drop=True)
    registry = pd.read_csv(ROOT / 'course_artifacts/week03_country_split.csv')
    registry = registry.loc[registry.country_split.eq('train')]
    plans, quota = search.make_country_and_respondent_plans(data, registry, DESIGN['confirmation_sample_seed'], 50)
    plan_path = output / 'confirmation_sampling_indices.joblib'
    if plan_path.exists():
        saved = joblib.load(plan_path)
        assert all(np.array_equal(a, b) for kind in plans for a, b in zip(plans[kind], saved[kind]))
    else:
        joblib.dump(plans, plan_path)
    for earlier in [joblib.load(PREVIOUS / 'confirmation_sampling_indices.joblib'),
                    joblib.load(ROOT / 'course_artifacts/week04_experiment1_complete_overall_worry_v3/sampling_indices.joblib')]:
        assert all(not np.array_equal(new, old) for kind in plans for new in plans[kind] for old in earlier[kind])
    quota.to_csv(output / 'confirmation_stratum_quotas.csv')
    audit = [{'test': kind, 'repeat': r, 'respondents': len(idx),
              'countries': data.iloc[idx].COUNTRY_ISO3.nunique(),
              'country_list': ' '.join(sorted(data.iloc[idx].COUNTRY_ISO3.unique()))}
             for kind, samples in plans.items() for r, idx in enumerate(samples)]
    pd.DataFrame(audit).to_csv(output / 'confirmation_sampling_audit.csv', index=False)
    save_json(BASE / 'current_run.json', {'output': str(output.relative_to(ROOT)), 'fingerprint': fingerprint})
    return output


def adaptive_for_k(k, output):
    output = Path(output)
    state_path = output / 'studies' / f'k{k}.joblib'
    distributions = {'q': optuna.distributions.FloatDistribution(.1, .9),
                     'alpha': optuna.distributions.FloatDistribution(.2, .8)}
    if state_path.exists():
        study = joblib.load(state_path)
    else:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', optuna.exceptions.ExperimentalWarning)
            sampler = optuna.samplers.TPESampler(seed=DESIGN['adaptive_seed_base'] + k,
                                               multivariate=True, constraints_func=constraints)
        study = optuna.create_study(direction='maximize', sampler=sampler)
        for path in sorted((output / 'pilot').glob(f'k{k}_*.json')):
            row = json.loads(path.read_text())
            assert row.get('origin') == 'previous pilot'
            if row['status'] not in ['complete', 'structurally ineligible']:
                continue
            value = row['score'] if row['status'] == 'complete' else -2.0
            attrs = {'origin': 'previous pilot', 'structural_pass': row['structural_pass'], 'trial_id': row['trial']}
            study.add_trial(optuna.trial.create_trial(params={'q': row['q'], 'alpha': row['alpha']},
                distributions=distributions, value=value, user_attrs=attrs,
                system_attrs={'constraints': (0.0 if row['structural_pass'] else 1.0,)}))
        save_study(state_path, study)
    budget = DESIGN['adaptive_new_trials_per_k']
    for attempt in range(budget):
        trials = [t for t in study.trials if t.user_attrs.get('origin') == 'new adaptive proposal']
        if attempt < len(trials) and trials[attempt].state.is_finished():
            continue
        if attempt < len(trials):
            assert trials[attempt].state == optuna.trial.TrialState.RUNNING
            trial = optuna.trial.Trial(study, trials[attempt]._trial_id)
        else:
            trial = study.ask(distributions)
            trial.set_user_attr('origin', 'new adaptive proposal')
            save_study(state_path, study)
        q, alpha = trial.params['q'], trial.params['alpha']
        assert not any(t.number != trial.number and t.params == trial.params for t in study.trials), 'Duplicate proposal: stop rather than inflate budget.'
        row = search.evaluate((q, alpha, k, 'pilot'))
        trial.set_user_attr('structural_pass', row['structural_pass'])
        trial.set_user_attr('trial_id', row['trial'])
        if row['status'] == 'complete':
            study.tell(trial, row['score'])
        elif row['status'] == 'structurally ineligible':
            study.tell(trial, -2.0)
        else:
            study.tell(trial, state=optuna.trial.TrialState.FAIL)
        save_study(state_path, study)
        records = [{'proposal': i + 1, 'optuna_trial': t.number, **t.params,
                    'trial': t.user_attrs.get('trial_id'), 'status': t.state.name,
                    'structural_pass': t.user_attrs.get('structural_pass'), 'score': t.value}
                   for i, t in enumerate(study.trials) if t.user_attrs.get('origin') == 'new adaptive proposal']
        # Proposal order is independent of the imported trials.
        for i, record in enumerate(records, 1):
            record['proposal'] = i
        pd.DataFrame(records).to_csv(output / 'studies' / f'k{k}_new_trials.csv', index=False)
        print(f'ADAPTIVE k={k} {attempt + 1}/{budget}: {row["status"]}, score={row.get("score")}', flush=True)
    return k


def main():
    BASE.mkdir(parents=True, exist_ok=True)
    # Share the old runner's lock as well: two searches must never run together.
    locks = [(BASE / 'run.lock').open('a'), (PREVIOUS.parent / 'run.lock').open('a')]
    for lock in locks:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    output = prepare()
    print('OUTPUT', output, flush=True)
    if (output / 'completion.json').exists():
        print('Already completed: no duplicate fits.', flush=True)
        return
    with ProcessPoolExecutor(max_workers=4, initializer=initialize_worker, initargs=(output,)) as pool:
        futures = [pool.submit(adaptive_for_k, k, output) for k in DESIGN['k_values']]
        for future in as_completed(futures):
            k = future.result()
            print('ADAPTIVE FINISHED k=', k, flush=True)
        pilot = pd.DataFrame([json.loads(p.read_text()) for p in sorted((output / 'pilot').glob('*.json'))])
        pilot.to_csv(output / 'all_pilot_results.csv', index=False)
        shortlist = pd.concat([search.rank_settings(group).head(2) for _, group in pilot.groupby('k')])
        shortlist.to_csv(output / 'shortlist_before_confirmation.csv', index=False)
        confirmation = {(float(r.q), float(r.alpha), int(r.k), 'confirmation') for r in shortlist.itertuples()}
        confirmation.update({(.5, .5, 4, 'confirmation'), (1 / 3, .75, 8, 'confirmation')})
        plan = pd.DataFrame(sorted(confirmation), columns=['q', 'alpha', 'k', 'phase'])
        plan_path = output / 'confirmation_plan.csv'
        if plan_path.exists():
            pd.testing.assert_frame_equal(pd.read_csv(plan_path), plan, check_exact=False)
        else:
            plan.to_csv(plan_path, index=False)
        seal = {'confirmation_plan_sha256': file_hash(plan_path),
                'shortlist_sha256': file_hash(output / 'shortlist_before_confirmation.csv'),
                'confirmation_samples_sha256': file_hash(output / 'confirmation_sampling_indices.joblib')}
        if (output / 'shortlist_seal.json').exists():
            assert json.loads((output / 'shortlist_seal.json').read_text()) == seal
        else:
            assert not list((output / 'confirmation').glob('*.json'))
            save_json(output / 'shortlist_seal.json', seal)
        results = []
        futures = [pool.submit(search.evaluate, task) for task in sorted(confirmation)]
        for future in as_completed(futures):
            row = future.result()
            results.append(row)
            table = pd.DataFrame(results).sort_values(['k', 'q', 'alpha'])
            table.to_csv(output / 'full_confirmation_results.csv', index=False)
            save_json(output / 'progress.json', {'stage': 'fresh full confirmation',
                'completed_candidates': len(results), 'stage_candidates': len(confirmation),
                'failures': int(table.failures.sum()), 'updated_epoch': time.time()})
            print(f'CONFIRMED {len(results)}/{len(confirmation)} k={row["k"]}: score={row.get("score")}, pass={row.get("stability_pass")}', flush=True)
    protected = json.loads((output / 'protected_sources.json').read_text())
    assert all(file_hash(ROOT / name) == digest for name, digest in protected.items())
    save_json(output / 'completion.json', {'status': 'completed', 'new_adaptive_proposals': 160,
        'imported_reference_settings': 301, 'confirmation_candidates': len(confirmation),
        'protected_sources_unchanged': True, 'heldout_responses_loaded': False,
        'models_replaced': False, 'interpretation': 'exploratory development tuning, no new independent validation'})
    print('COMPLETED', output, flush=True)


if __name__ == '__main__':
    main()
