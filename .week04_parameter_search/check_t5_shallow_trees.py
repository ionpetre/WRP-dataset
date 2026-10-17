"""Explain fixed T5 labels with ordinary trees; do not refit clustering."""
from pathlib import Path
import hashlib
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, precision_recall_fscore_support, confusion_matrix
from sklearn.model_selection import GroupKFold
from sklearn.tree import DecisionTreeClassifier, export_text
import search

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    pointer = json.loads((ROOT / 'course_artifacts/week04_kmeans_adaptive_optimization/current_run.json').read_text())
    source = ROOT / pointer['output']
    spec = next(s for s in json.loads((source / 'selected_reference_specs.json').read_text()) if s['model'] == 'T5')
    reference_path = source / 'references' / (spec['trial'] + '.joblib')
    data_path = ROOT / 'course_artifacts/week04_search_v4/stage1_eligible_development.parquet'
    plan = {'version': 1, 'model': spec, 'depths': [1, 2, 3, 5],
            'features': search.FEATURES, 'cross_validation': 'all five GroupKFold country folds',
            'training_and_test_weights': 'WGT within country, equal totals per country within fold',
            'tree': 'DecisionTreeClassifier, Gini, min_samples_leaf=200, random_state=2023; no class reweighting',
            'target': 'fixed development reference labels, not independently refitted labels',
            'interpretation': 'explanatory fidelity; no automatic rejection threshold or claim of independent validation',
            'heldout_used': False, 'clustering_fits': 0,
            'inputs': {str(p.relative_to(ROOT)): sha256(p) for p in [reference_path, data_path]}}
    context = hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()
    base = ROOT / 'course_artifacts/week04_t5_shallow_explanations'
    output = base / context[:16]
    output.mkdir(parents=True, exist_ok=True)
    if (output / 'completion.json').exists():
        assert json.loads((output / 'protocol.json').read_text()) == plan
        print('Verified existing T5 explanatory analysis:', output)
        return output
    (output / 'protocol.json').write_text(json.dumps(plan, indent=2))
    data = pd.read_parquet(data_path)
    data = data.loc[data[search.FEATURES].notna().all(axis=1)].reset_index(drop=True)
    assert len(data) == 109488 and data.country_split.eq('train').all()
    reference = joblib.load(reference_path)
    assert reference['fingerprint'] == pointer['fingerprint']
    labels = reference['labels']
    x = data[search.FEATURES].to_numpy(float)
    folds, per_cluster, fold_countries = [], [], []
    for fold, (train, test) in enumerate(GroupKFold(5).split(x, labels, data.COUNTRY_ISO3), 1):
        assert not set(data.iloc[train].COUNTRY_ISO3) & set(data.iloc[test].COUNTRY_ISO3)
        for c in sorted(data.iloc[test].COUNTRY_ISO3.unique()):
            fold_countries.append({'fold': fold, 'evaluation_country': c})
        train_w = search.country_weights(data.iloc[train])
        test_w = search.country_weights(data.iloc[test])
        for depth in plan['depths']:
            tree = DecisionTreeClassifier(max_depth=depth, min_samples_leaf=200, random_state=2023)
            tree.fit(x[train], labels[train], sample_weight=train_w)
            predicted = tree.predict(x[test])
            folds.append({'model': 'T5', 'fold': fold, 'depth': depth,
                          'balanced_accuracy': balanced_accuracy_score(labels[test], predicted, sample_weight=test_w),
                          'leaves': tree.get_n_leaves(), 'training_countries': data.iloc[train].COUNTRY_ISO3.nunique(),
                          'evaluation_countries': data.iloc[test].COUNTRY_ISO3.nunique()})
            precision, recall, f1, _ = precision_recall_fscore_support(
                labels[test], predicted, labels=np.arange(5), sample_weight=test_w, zero_division=0)
            for c in range(5):
                per_cluster.append({'fold': fold, 'depth': depth, 'cluster': c,
                                    'precision': precision[c], 'recall': recall[c], 'f1': f1[c]})
            pd.DataFrame(confusion_matrix(labels[test], predicted, labels=np.arange(5), sample_weight=test_w)).to_csv(
                output / f'depth{depth}_fold{fold}_weighted_confusion.csv', index_label='true_cluster')
            (output / f'depth{depth}_fold{fold}_rules.txt').write_text(
                export_text(tree, feature_names=search.FEATURES, decimals=3))
    folds = pd.DataFrame(folds)
    folds.to_csv(output / 'all_feature_tree_folds.csv', index=False)
    folds.groupby('depth').balanced_accuracy.agg(['mean', 'std', 'min', 'max']).reset_index().to_csv(
        output / 'all_feature_tree_summary.csv', index=False)
    pd.DataFrame(per_cluster).to_csv(output / 'all_feature_tree_per_cluster_folds.csv', index=False)
    pd.DataFrame(per_cluster).groupby(['depth', 'cluster'])[['precision', 'recall', 'f1']].mean().reset_index().to_csv(
        output / 'all_feature_tree_per_cluster_summary.csv', index=False)
    pd.DataFrame(fold_countries).to_csv(output / 'evaluation_country_folds.csv', index=False)
    assert len(fold_countries) == 113 and len({r['evaluation_country'] for r in fold_countries}) == 113
    evaluation = ROOT / json.loads((ROOT / 'course_artifacts/week04_kmeans_profile_evaluation/current_run.json').read_text())['output']
    for filename in ['burden_tree_summary.csv', 'single_feature_summary.csv']:
        table = pd.read_csv(evaluation / filename)
        table.loc[table.model.eq('T5')].to_csv(output / filename, index=False)
    (output / 'completion.json').write_text(json.dumps({'status': 'complete', 'country_folds': 5,
        'all_113_countries_evaluated_once': True, 'classifier_fits': 20, 'clustering_fits': 0,
        'code_sha256': sha256(__file__), 'heldout_used': False,
        'files': {p.name: sha256(p) for p in output.iterdir() if p.is_file()}}, indent=2))
    (base / 'current_run.json').write_text(json.dumps({'output': str(output.relative_to(ROOT)), 'context': context}, indent=2))
    print(pd.read_csv(output / 'all_feature_tree_summary.csv').to_string(index=False))
    return output


if __name__ == '__main__':
    main()
