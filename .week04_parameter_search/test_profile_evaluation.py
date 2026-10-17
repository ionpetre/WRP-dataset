"""Independent arithmetic/provenance checks. No model fitting."""
import ast
import json
from pathlib import Path
import numpy as np
import pandas as pd
import evaluate_profiles as evaluation

ROOT = evaluation.ROOT
pointer = json.loads((evaluation.BASE / 'current_run.json').read_text())
output = ROOT / pointer['output']
protocol = json.loads((output / 'protocol.json').read_text())
assert all(evaluation.file_hash(ROOT / name) == digest for name, digest in protocol['inputs_sha256'].items())
protected = json.loads((output / 'protected_sources.json').read_text())
assert all(evaluation.file_hash(ROOT / name) == digest for name, digest in protected.items())
for name in ['evaluate_profiles.py', 'diagnose_reference_profiles.py', 'summarize_profile_evaluation.py']:
    tree = ast.parse((Path(__file__).parent / name).read_text())
    assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                   and n.func.attr in ['fit', 'fit_predict', 'partial_fit'] for n in ast.walk(tree))
table = evaluation.overlap(np.array([0, 0, 1, 1]), np.array([1, 1, 0, 0]), np.array([.1, .2, .3, .4]), 2, 2)
assert all(np.allclose(v, 1) for v in evaluation.cluster_scores(table)[1:5])
cols, jac, precision, recall, best_any, _ = evaluation.cluster_scores(np.array([[.2, .1], [.1, .6]]))
assert np.array_equal(cols, [0, 1]) and np.allclose(jac, [.5, .75])
assert np.allclose(precision, [2 / 3, 6 / 7]) and np.allclose(recall, precision)
assert np.allclose(best_any, jac)
assert all(np.isfinite(v).all() for v in evaluation.cluster_scores(np.array([[.3, 0], [.7, 0]]))[1:])
profiles = pd.read_csv(output / 'original_category_profiles.csv')
cards = pd.read_csv(output / 'profile_summaries.csv')
repetitions = pd.read_csv(output / 'cluster_stability_repetitions.csv')
summary = pd.read_csv(output / 'cluster_stability_summary.csv')
assert len(cards) == 54 and cards.model.nunique() == 9
assert len(repetitions) == 5400 and len(summary) == 108
assert np.allclose(profiles.groupby(['model', 'cluster', 'feature']).proportion.sum(), 1)
assert np.allclose(cards.groupby('model').weighted_share.sum(), 1)
assert cards.groupby('model').respondents.sum().eq(109488).all()
for metric in ['jaccard', 'precision', 'recall', 'best_any_jaccard']:
    assert repetitions[metric].between(-1e-12, 1 + 1e-12).all()
assert (repetitions.jaccard <= repetitions.precision + 1e-12).all()
assert (repetitions.jaccard <= repetitions.recall + 1e-12).all()
assert (repetitions.best_any_jaccard >= repetitions.jaccard - 1e-12).all()
for row in summary.itertuples():
    group = repetitions.loc[repetitions.model.eq(row.model) & repetitions.cluster.eq(row.cluster) & repetitions.test.eq(row.test)]
    assert len(group) == 50
    assert np.isclose(group.jaccard.quantile(.1), row.jaccard_p10)
    assert np.isclose(group.jaccard.median(), row.jaccard_median)
    assert np.isclose(group.best_any_jaccard.quantile(.1), row.best_any_jaccard_p10)
overlaps = pd.read_csv(output / 'partition_overlaps.csv')
assert overlaps.groupby(['source', 'target']).ngroups == 36
assert np.allclose(overlaps.groupby(['source', 'target']).joint_weighted_share.sum(), 1)
assert np.allclose(overlaps.groupby(['source', 'target', 'source_cluster']).share_of_source.sum(), 1)
assert np.allclose(overlaps.groupby(['source', 'target', 'target_cluster']).share_of_target.sum(), 1)
agreements = pd.read_csv(output / 'reference_partition_agreement.csv')
assert len(agreements) == 900 and agreements.groupby(['model', 'test']).size().eq(50).all()
assert agreements.groupby(['model', 'test']).is_test_medoid.sum().eq(1).all()
inertia = pd.read_csv(output / 'cached_centres_full_population_inertia.csv')
assert len(inertia) == 900 and inertia.reference_full_population_inertia.gt(0).all()
assert np.allclose(inertia.relative_inertia_difference,
                   inertia.cached_centres_full_population_inertia / inertia.reference_full_population_inertia - 1)
flows = pd.read_csv(output / 'aligned_membership_flows.csv')
assert np.allclose(flows.groupby(['model', 'test', 'reference_cluster']).mean_share.sum(), 1)
completion = json.loads((output / 'completion.json').read_text())
assert completion['new_clustering_fits'] == completion['new_classifier_fits'] == 0
assert not completion['Ward_work'] and not completion['heldout_responses_loaded']
result = {'status': 'passed', 'models': 9, 'profiles': 54, 'cached_fits': 900,
          'cluster_repetition_comparisons': 5400, 'partition_comparisons': 36,
          'label_permutation_invariance_and_empty_cluster_case': True,
          'metric_quantiles_and_probabilities_reproduced': True, 'sources_and_frozen_models_unchanged': True,
          'no_fit_calls_in_evaluation_scripts': True}
evaluation.save_json(output / 'verification.json', result)
print(json.dumps(result, indent=2))
