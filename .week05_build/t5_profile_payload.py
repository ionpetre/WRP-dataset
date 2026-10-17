"""Add the primary model to the explorer using public aggregates only."""
import json
from pathlib import Path
import pandas as pd


def add_t5(payload, public):
    public = Path(public)
    pointer = public / 'course_artifacts/week05_t5_secondary_transfer/current_run.json'
    if not pointer.exists():
        return payload
    folder = public / json.loads(pointer.read_text())['output']
    model = json.loads((public / 'frozen_models/T5_models.json').read_text())
    features = model['feature_order']
    names = model['models']['T5']['profile_names']
    profiles = pd.read_csv(folder / 'frozen_model/development_original_category_profiles.csv').query("scope=='global'")
    shares = pd.read_csv(folder / 'profile_transfer_summary.csv')
    counts = pd.read_csv(folder / 'frozen_model/development_prevalence.csv').query("scope=='global'").set_index('cluster').respondents
    anchors = pd.read_csv(folder / 'frozen_model/development_defining_anchors.csv')
    result = []
    for c in range(5):
        table = profiles.loc[profiles.cluster.eq(c)].set_index(['feature', 'category'])
        val = lambda f, a, col='proportion': float(table.loc[(f, a), col])
        row = shares.loc[shares.cluster.eq(c)].iloc[0]
        result.append({'id': c, 'name': names[str(c)], 'count': int(counts[c]),
            'share': row.equal_country_weighted_share_development, 'heldoutShare': row.equal_country_weighted_share_heldout,
            'meanSemanticGap': row.mean_feature_total_variation,
            'worry': [[val(f, a) for a in range(3)] for f in features[:6]],
            'worryOutside': [[val(f, a, 'outside_proportion') for a in range(3)] for f in features[:6]],
            'harm': [[val(f, 1) for f in block] for block in [features[6:13], features[13:]]],
            'harmOutside': [[val(f, 1, 'outside_proportion') for f in block] for block in [features[6:13], features[13:]]],
            'anchors': [{'feature': r.feature, 'category': int(r.category), 'inside': r.development_proportion,
                         'outside': r.development_outside_proportion} for r in anchors.loc[anchors.cluster.eq(c)].itertuples()]})
    stability = json.loads((folder / 'frozen_model/development_stability.json').read_text())
    review_pointer = json.loads((public / 'course_artifacts/week04_kmeans_profile_evaluation/current_run.json').read_text())
    review = pd.read_csv(public / review_pointer['output'] / 'model_evaluation_overview.csv')
    review = review.loc[review.model.eq('T5')].iloc[0]
    payload['models']['T5'] = {'k': 5, 'profiles': result, 'stability': [
        {'test': k, 'median': stability[k + '_median'], 'p10': stability[k + '_p10'],
         'jaccardP10': float(review[k + '_min_cluster_jaccard_p10'])}
        for k in ['respondents', 'countries']]}
    return payload
