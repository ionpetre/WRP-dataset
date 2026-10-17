"""Freeze the approved existing T5 reference, then assess fixed-model transfer.

This is secondary assessment of previously examined held-out countries, not a
new untouched test. No K-means fitting, parameter tuning or B/E replacement.
"""
from pathlib import Path
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import shutil
import sys
import joblib
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from threadpoolctl import threadpool_limits
import frozen_transfer as old

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.week04_parameter_search'))
import search

BASE = ROOT / 'course_artifacts/week05_t5_secondary_transfer'
PLAN = {
    'version': 1, 'model': 'T5', 'role': 'approved primary candidate; assess transfer before downstream migration',
    'approval': 'User: did you check whether shallow decision trees can give trivial explanations to T5? proceed as you suggested',
    'secondary_assessment': True, 'heldout_previously_examined_for_BE': True,
    'no_pristine_external_validation_claim': True, 'model_refits': 0, 'retuning': False,
    'eligibility': 'all 20 original-unit profile features observed; incomplete respondents remain unassigned',
    'assignment': 'nearest stored development centre; first stored centre on an exact tie; preserve cluster order',
    'profile_ids': 'T5_C0,...,T5_C4; never renumber by prevalence; never substitute for B/E IDs',
    'weights': 'WGT normalized within complete-case country, equal country totals within each reporting area',
    'anchors': 'three largest positive development category-versus-outside contrasts per profile, distinct features',
    'distance_flag': 'distance exceeds assigned-profile development weighted p95; diagnostic, not exclusion',
    'transfer_review': 'original categories, anchor directions, prevalence, distances, margins, country problems, missingness',
    'automatic_transfer_cutoff': None, 'ARI_as_transfer_threshold': False,
    'interpretation': 'descriptive transfer under a fixed classifier; not independent re-emergence of the groups',
    'uncertainty': old.TRANSFER_PLAN['uncertainty'],
    'historical_BE_models_and_handoffs': 'preserved; no silent downstream replacement',
}


def sha(path):
    return old.file_sha256(path)


def save(path, value):
    old.atomic_json(value, path)


def verify_seal(package):
    seal = json.loads((package / 'freeze_seal.json').read_text())
    assert seal['status'] == 'frozen_before_secondary_transfer'
    for name, digest in seal['files'].items():
        assert sha(package / name) == digest, 'Sealed T5 package changed: ' + name
    return seal


def assign(frame, centres, spec, cutoffs=None):
    # Keep the exact operation order used for the selected development reference.
    x = search.profile_matrix(frame, spec['q'], spec['alpha'])
    assert x.shape == (len(frame), 21) and np.isfinite(x).all()
    with threadpool_limits(limits=1):
        distances = cdist(x, centres)
    labels = distances.argmin(axis=1)
    ordered = np.sort(distances, axis=1)
    first, second = ordered[:, 0], ordered[:, 1]
    table = frame[['WPID_RANDOM', 'COUNTRY_ISO3', 'GlobalRegion']].copy()
    table['candidate'] = 'T5'
    table['cluster'] = labels.astype('int16')
    table['nearest_distance'] = first
    table['second_nearest_distance'] = second
    table['margin'] = np.divide(second - first, second, out=np.zeros_like(first), where=second > 0)
    table['equal_country_weight'] = search.country_weights(frame)
    table['beyond_development_profile_p95'] = (first > np.array([cutoffs[int(c)] for c in labels])
                                             if cutoffs is not None else False)
    return table


def assignment_audit(raw, table, names, context):
    audit, retention = old.eligibility_audit(raw)
    audit = audit.merge(raw[['WPID_RANDOM', 'Country', 'CountryIncomeLevel', 'country_split', 'WGT']],
                        on='WPID_RANDOM', validate='one_to_one')
    columns = ['WPID_RANDOM', 'cluster', 'nearest_distance', 'second_nearest_distance',
               'margin', 'beyond_development_profile_p95', 'equal_country_weight']
    renamed = {c: 'T5_' + c for c in columns if c != 'WPID_RANDOM'}
    audit = audit.merge(table[columns].rename(columns=renamed), on='WPID_RANDOM', how='left', validate='one_to_one')
    audit['T5_cluster'] = audit.T5_cluster.astype('Int16')
    audit['T5_profile_id'] = audit.T5_cluster.map(lambda c: f'T5_C{int(c)}' if pd.notna(c) else None)
    audit['T5_profile_name'] = audit.T5_cluster.map(names)
    audit['T5_context'] = context
    assert audit.loc[audit.complete_case, 'T5_cluster'].notna().all()
    assert audit.loc[~audit.complete_case, 'T5_cluster'].isna().all()
    assert len(audit) == len(raw) and audit.WPID_RANDOM.is_unique
    return audit, retention


def main():
    BASE.mkdir(parents=True, exist_ok=True)
    lock = (BASE / 'run.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    # Source-code/reporting repairs do not authorize another held-out run.
    if (BASE / 'current_run.json').exists():
        previous = ROOT / json.loads((BASE / 'current_run.json').read_text())['output']
        if (previous / 'transfer_complete.json').exists():
            verify_seal(previous / 'frozen_model')
            record = json.loads((previous / 'transfer_complete.json').read_text())
            for name, digest in record['files'].items():
                assert sha(previous / name) == digest
            print('Completed secondary transfer already exists; no repeat:', previous)
            return previous
    pointer = json.loads((ROOT / 'course_artifacts/week04_kmeans_adaptive_optimization/current_run.json').read_text())
    source = ROOT / pointer['output']
    spec = next(s for s in json.loads((source / 'selected_reference_specs.json').read_text()) if s['model'] == 'T5')
    reference_path = source / 'references' / (spec['trial'] + '.joblib')
    evaluation = ROOT / json.loads((ROOT / 'course_artifacts/week04_kmeans_profile_evaluation/current_run.json').read_text())['output']
    trees = ROOT / json.loads((ROOT / 'course_artifacts/week04_t5_shallow_explanations/current_run.json').read_text())['output']
    assert (trees / 'completion.json').exists()
    inputs = [reference_path, ROOT / 'course_artifacts/week03_development_data.parquet',
              ROOT / 'course_artifacts/week03_country_split.csv',
              ROOT / 'course_artifacts/week04_search_v4/stage1_eligible_development.parquet',
              evaluation / 'profile_review_cards.csv', source / 'confirmation' / (spec['trial'] + '.json'),
              trees / 'all_feature_tree_summary.csv', trees / 'single_feature_summary.csv', trees / 'burden_tree_summary.csv',
              ROOT / '.week04_parameter_search/search.py', Path(__file__),
              ROOT / '.week05_build/frozen_transfer.py', ROOT / '.week05_build/frozen_assignment.py', ROOT / '.week05_build/week05_core.py']
    provenance = {'spec': spec, 'plan': PLAN, 'development_inputs': {str(p.relative_to(ROOT)): sha(p) for p in inputs}}
    context = hashlib.sha256(json.dumps(provenance, sort_keys=True).encode()).hexdigest()
    output = BASE / context[:16]
    package = output / 'frozen_model'
    package.mkdir(parents=True, exist_ok=True)
    if (output / 'transfer_complete.json').exists():
        verify_seal(package)
        record = json.loads((output / 'transfer_complete.json').read_text())
        for name, digest in record['files'].items():
            assert sha(output / name) == digest
        print('Verified completed secondary transfer; no duplicate run:', output)
        return output
    protected_paths = list((ROOT / 'course_artifacts/week05_frozen_objective1_v1/123d248adda6115f').glob('*'))
    protected_paths += [ROOT / 'course_artifacts/week05_objective1_handoff_v1/123d248adda6115f/all_respondents_eligibility_and_frozen_profiles.parquet',
                        ROOT / 'weekly_notebooks/week06_predicting_frozen_risk_profile_membership.ipynb']
    protected = {str(p.relative_to(ROOT)): sha(p) for p in protected_paths if p.is_file()}
    save(output / 'protected_sources.json', protected)
    save(output / 'protocol.json', provenance)
    split = pd.read_csv(ROOT / 'course_artifacts/week03_country_split.csv')
    assert split.COUNTRY_ISO3.is_unique
    development_countries = set(split.loc[split.country_split.eq('train'), 'COUNTRY_ISO3'])
    heldout_countries = set(split.loc[split.country_split.eq('heldout_country'), 'COUNTRY_ISO3'])
    assert len(development_countries) == 113 and len(heldout_countries) == 29
    assert not development_countries & heldout_countries
    dictionary = pd.read_csv(ROOT / '23_wrp/WRP_2023_data_dictionary.csv')
    labels_text = dictionary.loc[dictionary.variable.eq('GlobalRegion'), 'value_labels'].iloc[0]
    region_names = {int(s.split(' = ', 1)[0]): s.split(' = ', 1)[1] for s in labels_text.split(' | ')}
    columns = old.prepared_columns() + ['Country']
    raw_dev = old.derive_frozen_features(pd.read_parquet(ROOT / 'course_artifacts/week03_development_data.parquet', columns=columns))
    development = raw_dev.loc[raw_dev[search.FEATURES].notna().all(axis=1)].reset_index(drop=True)
    source_dev = pd.read_parquet(ROOT / 'course_artifacts/week04_search_v4/stage1_eligible_development.parquet')
    source_dev = source_dev.loc[source_dev[search.FEATURES].notna().all(axis=1)].reset_index(drop=True)
    assert np.array_equal(source_dev.WPID_RANDOM, development.WPID_RANDOM)
    assert np.array_equal(source_dev[search.FEATURES].to_numpy(), development[search.FEATURES].to_numpy())
    assert len(raw_dev) == 116820 and len(development) == 109488
    assert set(development.COUNTRY_ISO3) == development_countries and raw_dev.WPID_RANDOM.is_unique
    reference = joblib.load(reference_path)
    assert reference['fingerprint'] == pointer['fingerprint']
    centres = reference['centres'].copy()
    assert centres.shape == (5, 21)
    assigned_dev = assign(development, centres, spec)
    assert np.array_equal(assigned_dev.cluster, reference['labels'])
    weights = search.country_weights(development)
    cutoffs = {c: old.weighted_quantile(assigned_dev.loc[assigned_dev.cluster.eq(c), 'nearest_distance'],
                                      weights[assigned_dev.cluster.eq(c)], .95) for c in range(5)}
    assigned_dev = assign(development, centres, spec, cutoffs)
    cards = pd.read_csv(evaluation / 'profile_review_cards.csv')
    names = cards.loc[cards.model.eq('T5')].set_index('cluster').description.to_dict()
    bundle = {'models': {'T5': {'spec': {'global_k': 5}, 'profile_names': names}}}
    if not (package / 'freeze_seal.json').exists():
        np.save(package / 'centres.npy', centres)
        specification = dict(provenance, context=context,
            feature_order=search.FEATURES, transform_order=['centred_' + f for f in search.WORRY] + ['overall_worry'] + search.SELF + search.KNOWN,
            geometry='sqrt(alpha)/sqrt(6) times six respondent-centred 0/q/1 worries and their mean; sqrt((1-alpha)/2)/sqrt(7) times fourteen harm indicators',
            raw_recoding={'worry': {'1': 2, '2': 1, '3': 0, '98': None, '99': None},
                          'harm_personal': {'1': 1, '2': 0, '3': 1, '4': 0, '98': None, '99': None},
                          'harm_known_person': {'1': 0, '2': 1, '3': 1, '4': 0, '98': None, '99': None}},
            profile_names=names, profile_distance_p95=cutoffs, imputation=None, z_standardization=False, PCA=False,
            source_reference_cluster_order_preserved=True,
            frozen_at_utc=datetime.now(timezone.utc).isoformat(),
            heldout_previously_examined=True, T5_heldout_responses_read_during_this_run=False)
        save(package / 'specification.json', specification)
        devprev, devprofiles, devquality = old.transfer_tables(development, {'T5': assigned_dev}, bundle, region_names, package, 'development')
        devglobal = devprofiles.loc[devprofiles.scope.eq('global')]
        anchors = devglobal.sort_values(['difference_vs_outside', 'feature', 'category'], ascending=[False, True, True])
        anchors = anchors.drop_duplicates(['cluster', 'feature']).groupby('cluster', sort=True).head(3).copy()
        assert anchors.difference_vs_outside.gt(0).all() and len(anchors) == 15
        anchors = anchors.rename(columns={'proportion': 'development_proportion', 'outside_proportion': 'development_outside_proportion',
                                          'difference_vs_outside': 'development_contrast'})
        anchors.to_csv(package / 'development_defining_anchors.csv', index=False)
        audit_dev, retention_dev = assignment_audit(raw_dev, assigned_dev, names, context)
        audit_dev.to_parquet(package / 'development_eligibility_and_assignments.parquet', index=False)
        retention_dev.to_csv(package / 'development_country_retention.csv', index=False)
        assigned_dev.to_parquet(package / 'development_assignments.parquet', index=False)
        split.to_csv(package / 'frozen_country_split.csv', index=False)
        for filename in ['all_feature_tree_summary.csv', 'single_feature_summary.csv', 'burden_tree_summary.csv']:
            shutil.copy2(trees / filename, package / filename)
        save(package / 'development_stability.json', json.loads((source / 'confirmation' / (spec['trial'] + '.json')).read_text()))
        save(package / 'freeze_seal.json', {'status': 'frozen_before_secondary_transfer', 'context': context,
            'frozen_at_utc': specification['frozen_at_utc'], 'heldout_previously_examined_for_BE': True,
            'T5_transfer_not_yet_run': True, 'clustering_refits': 0,
            'files': {p.name: sha(p) for p in package.iterdir() if p.is_file()}})
    seal = verify_seal(package)
    assert np.array_equal(centres, np.load(package / 'centres.npy'))
    frozen = json.loads((package / 'specification.json').read_text())
    assert frozen['context'] == context
    print('T5 sealed, development labels exactly replayed; now read held-out responses.', flush=True)
    # This is the first held-out response read in THIS T5 pipeline, not in the project.
    first_read = datetime.now(timezone.utc).isoformat()
    assert first_read > seal['frozen_at_utc']
    raw = old.derive_frozen_features(pd.read_parquet(ROOT / 'course_artifacts/week03_heldout_country_data.parquet', columns=columns))
    assert len(raw) == 30090 and raw.WPID_RANDOM.is_unique and raw.country_split.eq('heldout_country').all()
    assert set(raw.COUNTRY_ISO3) == heldout_countries
    assert not set(raw.WPID_RANDOM) & set(raw_dev.WPID_RANDOM)
    heldout = raw.loc[raw[search.FEATURES].notna().all(axis=1)].reset_index(drop=True)
    assert len(heldout) == 27972 and heldout.COUNTRY_ISO3.nunique() == 29
    assigned = assign(heldout, np.load(package / 'centres.npy'), frozen['spec'],
                      {int(c): v for c, v in frozen['profile_distance_p95'].items()})
    assigned['profile_name'] = assigned.cluster.map(names)
    assigned.to_parquet(output / 'heldout_assignments.parquet', index=False)
    audit, retention = assignment_audit(raw, assigned, names, context)
    audit.to_parquet(output / 'heldout_eligibility_and_assignments.parquet', index=False)
    retention = retention.merge(raw[['COUNTRY_ISO3', 'Country', 'GlobalRegion', 'CountryIncomeLevel']].drop_duplicates(),
                                on='COUNTRY_ISO3', validate='one_to_one')
    retention.to_csv(output / 'heldout_country_retention.csv', index=False)
    prevalence, profiles, quality = old.transfer_tables(heldout, {'T5': assigned}, bundle, region_names, output, 'heldout')
    devprofiles = pd.read_csv(package / 'development_original_category_profiles.csv')
    devprofiles = devprofiles.loc[devprofiles.scope.eq('global')]
    differences = profiles.merge(devprofiles[['candidate', 'cluster', 'feature', 'category', 'proportion', 'difference_vs_outside']],
        on=['candidate', 'cluster', 'feature', 'category'], suffixes=('_heldout', '_development'), validate='many_to_one')
    differences['difference_pp'] = 100 * (differences.proportion_heldout - differences.proportion_development)
    differences.to_csv(output / 'heldout_vs_development_category_differences.csv', index=False)
    tv = differences.assign(absdiff=lambda d: abs(d.proportion_heldout - d.proportion_development)).groupby(
        ['candidate', 'scope', 'area_id', 'area_name', 'cluster', 'feature']).absdiff.sum().div(2).rename('feature_total_variation').reset_index()
    tv.to_csv(output / 'heldout_original_feature_total_variation.csv', index=False)
    semantic = tv.groupby(['candidate', 'scope', 'area_id', 'area_name', 'cluster']).agg(
        mean_feature_total_variation=('feature_total_variation', 'mean'),
        maximum_feature_total_variation=('feature_total_variation', 'max')).reset_index()
    semantic = semantic.merge(quality[['candidate', 'scope', 'area_id', 'cluster', 'respondents', 'kish_weighted_n']],
                              on=['candidate', 'scope', 'area_id', 'cluster'], validate='one_to_one')
    semantic.to_csv(output / 'heldout_profile_semantic_differences.csv', index=False)
    anchors = pd.read_csv(package / 'development_defining_anchors.csv').drop(columns=['scope', 'area_id', 'area_name']).merge(
        profiles[['candidate', 'cluster', 'feature', 'category', 'scope', 'area_id', 'area_name', 'proportion', 'outside_proportion', 'difference_vs_outside']],
        on=['candidate', 'cluster', 'feature', 'category'], validate='one_to_many')
    anchors['heldout_contrast_direction_preserved'] = anchors.difference_vs_outside.gt(0)
    anchors['proportion_shift_pp'] = 100 * (anchors.proportion - anchors.development_proportion)
    anchors.to_csv(output / 'heldout_frozen_anchor_comparison.csv', index=False)
    devquality = pd.read_csv(package / 'development_assignment_quality.csv')
    comparison = quality.loc[quality.scope.eq('global')].merge(
        devquality.loc[devquality.scope.eq('global')].drop(columns=['scope', 'area_id', 'area_name']),
        on=['candidate', 'cluster'], suffixes=('_heldout', '_development'), validate='one_to_one')
    comparison['distance_median_ratio'] = comparison.distance_median_heldout / comparison.distance_median_development
    comparison['margin_median_difference'] = comparison.margin_median_heldout - comparison.margin_median_development
    comparison.to_csv(output / 'heldout_vs_development_quality.csv', index=False)
    devprev = pd.read_csv(package / 'development_prevalence.csv')
    shares = prevalence.loc[prevalence.scope.eq('global')].merge(
        devprev.loc[devprev.scope.eq('global'), ['candidate', 'cluster', 'equal_country_weighted_share']],
        on=['candidate', 'cluster'], suffixes=('_heldout', '_development'), validate='one_to_one')
    shares['prevalence_difference_pp'] = 100 * (shares.equal_country_weighted_share_heldout - shares.equal_country_weighted_share_development)
    shares.to_csv(output / 'heldout_vs_development_prevalence.csv', index=False)
    intervals = old.country_bootstrap_profiles(heldout, {'T5': assigned}, bundle, output)
    country = quality.loc[quality.scope.eq('country') & quality.cluster.eq(-1)].merge(
        retention, left_on='area_id', right_on='COUNTRY_ISO3', validate='one_to_one')
    country.to_csv(output / 'heldout_country_quality_and_retention.csv', index=False)
    # A separate handoff keeps all original IDs, including incomplete respondents.
    # Existing B/E handoffs, map inputs and Week 6 are deliberately not overwritten.
    audit_dev = pd.read_parquet(package / 'development_eligibility_and_assignments.parquet')
    handoff = pd.concat([audit_dev, audit], ignore_index=True)
    assert len(handoff) == 146910 and handoff.WPID_RANDOM.is_unique and handoff.complete_case.sum() == 137460
    eligible = handoff.loc[handoff.complete_case].copy()
    within = eligible.WGT / eligible.groupby('COUNTRY_ISO3').WGT.transform('sum')
    eligible['equal_country_weight_within_split'] = within / eligible.groupby('country_split').COUNTRY_ISO3.transform('nunique')
    eligible['equal_country_weight_all_included_countries'] = within / 142
    handoff = handoff.merge(eligible[['WPID_RANDOM', 'equal_country_weight_within_split', 'equal_country_weight_all_included_countries']],
                            on='WPID_RANDOM', how='left', validate='one_to_one')
    handoff.to_parquet(output / 'all_respondents_T5_eligibility_and_frozen_profiles.parquet', index=False)
    assert np.array_equal(assign(heldout, centres, spec, cutoffs).cluster, assigned.cluster)
    for filename, digest in protected.items():
        assert sha(ROOT / filename) == digest, 'Historical source changed: ' + filename
    verify_seal(package)
    save(output / 'transfer_complete.json', {'status': 'completed_secondary_fixed_model_transfer', 'context': context,
        'frozen_at_utc': seal['frozen_at_utc'], 'first_T5_heldout_read_in_this_run_utc': first_read,
        'heldout_previously_examined_for_BE': True, 'heldout_input_sha256': sha(ROOT / 'course_artifacts/week03_heldout_country_data.parquet'),
        'prepared': len(raw), 'assigned': len(heldout), 'excluded': len(raw) - len(heldout), 'countries': 29,
        'new_clustering_fits': 0, 'retuning': False, 'historical_BE_and_week06_preserved': True,
        'downstream_migration_performed': False, 'seal_sha256': sha(package / 'freeze_seal.json'),
        'files': {p.name: sha(p) for p in output.iterdir() if p.is_file()}})
    save(BASE / 'current_run.json', {'output': str(output.relative_to(ROOT)), 'context': context})
    print('Secondary transfer complete:', output, flush=True)
    print(shares[['cluster', 'equal_country_weighted_share_development', 'equal_country_weighted_share_heldout']].to_string(index=False))
    print(semantic.loc[semantic.scope.eq('global')].to_string(index=False))
    print('Anchor directions retained:', anchors.loc[anchors.scope.eq('global'), 'heldout_contrast_direction_preserved'].sum(), '/ 15')
    return output


if __name__ == '__main__':
    main()
