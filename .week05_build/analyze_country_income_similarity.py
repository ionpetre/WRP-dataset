"""Post-validation aggregate extension: frozen country mixtures versus fieldwork income groups.

No respondent records are loaded and no clustering models are fitted.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'course_artifacts/week05_country_similarity_and_profile_synthesis_v1/d694096841b06e54'
INPUTS = [SOURCE / 'country_profile_vectors.csv'] + [
    SOURCE / f'{m}_all_countries_post_validation_hellinger_matrix.csv' for m in ['B', 'E']]
HASHES = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in INPUTS}
FINGERPRINT = hashlib.sha256(json.dumps(HASHES, sort_keys=True).encode()).hexdigest()[:16]
OUTPUT = ROOT / 'course_artifacts/week05_country_income_similarity_v1' / FINGERPRINT
OUTPUT.mkdir(parents=True, exist_ok=True)
LABELS = {1: 'Low income', 2: 'Lower-middle income', 3: 'Upper-middle income', 4: 'High income', 9: 'Not classified'}
REPETITIONS = 999
SEED = 20261013

vectors = pd.read_csv(INPUTS[0])
metadata_cols = ['COUNTRY_ISO3', 'Country', 'GlobalRegion', 'region_name', 'CountryIncomeLevel',
                 'country_split', 'retained_fraction', 'complete_respondents']
metadata = vectors.loc[vectors.candidate.eq('B'), metadata_cols].drop_duplicates().set_index('COUNTRY_ISO3').sort_index()
assert metadata.index.is_unique and len(metadata) == 142
other = vectors.loc[vectors.candidate.eq('E'), metadata_cols].drop_duplicates().set_index('COUNTRY_ISO3').sort_index()
pd.testing.assert_frame_equal(metadata, other)
assert set(metadata.CountryIncomeLevel) == {1, 2, 3, 4, 9}
metadata['income_label'] = metadata.CountryIncomeLevel.map(LABELS)
metadata.to_csv(OUTPUT / 'country_income_metadata.csv')

def correlation(distance, gap):
    return float(spearmanr(distance, gap).statistic) if len(distance) > 2 and np.unique(gap).size > 1 else None

def randomization(distance, income, region, ia, ib, observed, within_region):
    """Permute whole country labels, not independent pairs; preserve all income counts."""
    rng = np.random.default_rng(SEED)
    h_rank = rankdata(distance)
    h_rank -= h_rank.mean()
    h_norm = np.sqrt(np.sum(h_rank * h_rank))
    permuted = np.empty(REPETITIONS)
    blocks = [np.flatnonzero(region == r) for r in np.unique(region)]
    for rep in range(REPETITIONS):
        shuffled = income.copy()
        if within_region:
            for ids in blocks:
                shuffled[ids] = rng.permutation(income[ids])
        else:
            shuffled = rng.permutation(income)
        g = np.abs(shuffled[ia] - shuffled[ib])
        counts = np.bincount(g, minlength=4)
        middle_ranks = np.cumsum(counts) - (counts - 1) / 2
        g_rank = middle_ranks[g]
        g_rank -= g_rank.mean()
        permuted[rep] = np.sum(h_rank * g_rank) / (h_norm * np.sqrt(np.sum(g_rank * g_rank)))
    return {'permutations': REPETITIONS, 'permutation_seed': SEED,
            'reference_mean_rho': float(permuted.mean()), 'reference_p025_rho': float(np.quantile(permuted, .025)),
            'reference_p975_rho': float(np.quantile(permuted, .975)),
            'reference_upper_tail_fraction': float((1 + np.sum(permuted >= observed)) / (REPETITIONS + 1))}

summaries, cells, gaps, countries, tests = [], [], [], [], []
display = {'summaries': {}, 'matrices': {}, 'incomeLabels': LABELS, 'fingerprint': FINGERPRINT}
for model in ['B', 'E']:
    full = pd.read_csv(SOURCE / f'{model}_all_countries_post_validation_hellinger_matrix.csv', index_col=0)
    full = full.loc[metadata.index, metadata.index]
    h = full.to_numpy()
    assert np.isfinite(h).all() and np.allclose(h, h.T) and np.allclose(np.diag(h), 0)
    assert h.min() >= -1e-12 and h.max() <= 1
    p = vectors.loc[vectors.candidate.eq(model)].pivot(index='COUNTRY_ISO3', columns='cluster', values='profile_share').reindex(metadata.index).to_numpy()
    assert np.allclose(p.sum(axis=1), 1)
    direct = np.sqrt(np.sum((np.sqrt(p)[:, None, :] - np.sqrt(p)[None, :, :]) ** 2, axis=2) / 2)
    assert np.max(np.abs(direct - h)) < 1e-12
    dev_ids = metadata.index[metadata.country_split.eq('train')]
    dev = pd.read_csv(SOURCE / f'{model}_development_hellinger_matrix.csv', index_col=0).loc[dev_ids, dev_ids]
    assert np.max(np.abs(dev.to_numpy() - full.loc[dev_ids, dev_ids].to_numpy())) < 1e-12
    display['summaries'][model], display['matrices'][model] = {}, {}
    for scope in ['development', 'all_countries_post_validation']:
        use = metadata.CountryIncomeLevel.between(1, 4)
        if scope == 'development':
            use &= metadata.country_split.eq('train')
        md = metadata.loc[use]
        d = full.loc[md.index, md.index].to_numpy()
        income = md.CountryIncomeLevel.to_numpy()
        region = md.GlobalRegion.to_numpy()
        ia, ib = np.triu_indices(len(md), k=1)
        distance = d[ia, ib]
        gap = np.abs(income[ia] - income[ib])
        same_region = region[ia] == region[ib]
        same_income = gap == 0
        rho = correlation(distance, gap)
        row = {'candidate': model, 'scope': scope, 'classified_countries': len(md), 'distinct_pairs': len(distance),
               'ordinal_gap_spearman': rho, 'within_region_spearman': correlation(distance[same_region], gap[same_region]),
               'across_region_spearman': correlation(distance[~same_region], gap[~same_region]),
               'same_income_pair_mean': float(distance[same_income].mean()),
               'different_income_pair_mean': float(distance[~same_income].mean()),
               'same_region_pairs': int(same_region.sum()), 'same_income_pairs': int(same_income.sum())}
        per_country = []
        for i, (iso, c) in enumerate(md.iterrows()):
            same = income == income[i]
            same[i] = False
            different = income != income[i]
            eligible = np.ones(len(md), dtype=bool)
            eligible[i] = False
            order = np.argsort(np.where(eligible, d[i], np.inf), kind='stable')[:10]
            near = order[0]
            r = {'candidate': model, 'scope': scope, 'COUNTRY_ISO3': iso, 'Country': c.Country,
                 'income_level': int(income[i]), 'income_label': LABELS[income[i]],
                 'same_income_peer_mean': float(d[i, same].mean()), 'different_income_peer_mean': float(d[i, different].mean()),
                 'nearest_country': md.index[near], 'nearest_same_income': bool(income[near] == income[i]),
                 'nearest_10_same_income_fraction': float((income[order] == income[i]).mean()),
                 'random_peer_same_income_probability': float(same.sum() / eligible.sum())}
            per_country.append(r)
            countries.append(r)
        pc = pd.DataFrame(per_country)
        row.update({'same_income_country_balanced_mean': float(pc.same_income_peer_mean.mean()),
                    'different_income_country_balanced_mean': float(pc.different_income_peer_mean.mean()),
                    'nearest_same_income_fraction': float(pc.nearest_same_income.mean()),
                    'nearest_10_same_income_fraction': float(pc.nearest_10_same_income_fraction.mean()),
                    'random_peer_same_income_probability': float(pc.random_peer_same_income_probability.mean())})
        summaries.append(row)
        display['summaries'][model][scope] = row
        grid = []
        for a in range(1, 5):
            gr = []
            for b in range(1, 5):
                chosen = ((income[ia] == a) & (income[ib] == b)) | ((income[ia] == b) & (income[ib] == a))
                values = distance[chosen]
                r = {'candidate': model, 'scope': scope, 'income_a': a, 'income_b': b,
                     'mean_hellinger': float(values.mean()), 'median_hellinger': float(np.median(values)),
                     'distinct_pairs': int(chosen.sum())}
                cells.append(r)
                gr.append(r)
            grid.append(gr)
        display['matrices'][model][scope] = grid
        for step in range(4):
            for geography, mask in [('all_pairs', np.ones(len(distance), dtype=bool)),
                                    ('within_region', same_region), ('across_region', ~same_region)]:
                values = distance[(gap == step) & mask]
                gaps.append({'candidate': model, 'scope': scope, 'income_category_gap': step, 'geography': geography,
                             'distinct_pairs': len(values), 'mean_hellinger': float(values.mean()) if len(values) else None,
                             'median_hellinger': float(np.median(values)) if len(values) else None})
        for within in [False, True]:
            result = randomization(distance, income, region, ia, ib, rho, within)
            tests.append({'candidate': model, 'scope': scope, 'scheme': 'within_dataset_regions' if within else 'all_classified_countries',
                          'observed_rho': rho, **result})

pd.DataFrame(summaries).to_csv(OUTPUT / 'income_distance_summary.csv', index=False)
pd.DataFrame(cells).to_csv(OUTPUT / 'income_group_distance_cells.csv', index=False)
pd.DataFrame(gaps).to_csv(OUTPUT / 'income_gap_distance_summary.csv', index=False)
pd.DataFrame(countries).to_csv(OUTPUT / 'country_income_peer_comparisons.csv', index=False)
pd.DataFrame(tests).to_csv(OUTPUT / 'country_label_permutation_references.csv', index=False)
metadata.groupby(['country_split', 'CountryIncomeLevel', 'income_label']).size().rename('countries').to_csv(OUTPUT / 'income_group_counts.csv')
vmax = max(c['mean_hellinger'] for c in cells)
for scope in ['development', 'all_countries_post_validation']:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8), constrained_layout=True)
    for model, ax in zip(['B', 'E'], axes):
        grid = display['matrices'][model][scope]
        values = np.array([[c['mean_hellinger'] for c in row] for row in grid])
        image = ax.imshow(values, cmap='YlGnBu', vmin=0, vmax=vmax)
        for i in range(4):
            for j in range(4):
                ax.text(j, i, f'{values[i, j]:.3f}', ha='center', va='center', color='white' if values[i, j] > vmax * .65 else 'black')
        ax.set_xticks(range(4), ['Low', 'Lower\nmiddle', 'Upper\nmiddle', 'High'])
        ax.set_yticks(range(4), ['Low', 'Lower-middle', 'Upper-middle', 'High'])
        ax.set_title(f'{model}{4 if model == "B" else 8} · income-gap Spearman ρ = {display["summaries"][model][scope]["ordinal_gap_spearman"]:.3f}')
    fig.colorbar(image, ax=axes, label='Mean original Hellinger distance (0–1)', shrink=.8)
    fig.suptitle('Country-profile distances by fieldwork income group\n' + ('112 classified development countries' if scope == 'development' else '141 classified countries; post-validation exploration'))
    fig.savefig(OUTPUT / f'{scope}_income_distance_heatmaps.png', dpi=180)
    plt.close(fig)

old = json.loads((ROOT / 'course_artifacts/week05_continuous_country_similarity_maps_v1/map_display_data.json').read_text())
display.update({key: old[key] for key in ['countries', 'world', 'regions', 'tiny', 'distances', 'rankings']})
for c in display['countries']:
    md = metadata.loc[c['iso']]
    c.update({'income': int(md.CountryIncomeLevel), 'incomeLabel': LABELS[md.CountryIncomeLevel], 'split': str(md.country_split)})
display['counts'] = {scope: {str(level): int(((metadata.CountryIncomeLevel == level) &
                     (metadata.country_split.eq('train') if scope == 'development' else True)).sum()) for level in [1, 2, 3, 4, 9]}
                     for scope in ['development', 'all_countries_post_validation']}
(OUTPUT / 'income_map_display_data.json').write_text(json.dumps(display, separators=(',', ':')))
manifest = {'objective': 'Assess whether frozen country-profile similarity is associated with fieldwork income groups.',
            'analysis_timing': 'Exploratory extension after held-out validation; not a new selection or validation criterion.',
            'source_hashes': HASHES, 'source_fingerprint': FINGERPRINT, 'model_refitting': False,
            'income_source': 'Dataset CountryIncomeLevel; World Bank FY2023–24 classification at fieldwork.',
            'income_groups': LABELS, 'excluded_from_income_association': ['VEN'],
            'distance': 'Original Hellinger distance between within-country survey-weighted frozen B4/E8 complete-case profile proportions.',
            'country_influence': 'Equal countries. Pair means give more influence to larger income groups; also report equal-focal-country peer means.',
            'correlation': 'Spearman correlation of original Hellinger distance with absolute ordinal category gap, not with GNI amounts.',
            'dependence': 'Country pairs share countries. Do not use ordinary independent-pair correlation p-values.',
            'permutation_reference': '999 whole-country income-label permutations, unrestricted and within original dataset regions. The upper-tail fraction is a conditional randomization reference under exchangeability, not a population or causal p-value.',
            'regional_reference_limits': 'Within-region permutations preserve regional income counts, including homogeneous regions; they do not adjust for every country characteristic or physical proximity within a region.',
            'qualifications': ['Ordinal income-group steps are not equal monetary increments.',
                               'Association is not evidence that income causes profiles or validates discrete country types.',
                               'Income, geography, survey context and complete-case selection may overlap.',
                               'B/E distances are model-specific; compare patterns, not individual component meanings.',
                               'Development and full-sample results are nested, not independent replications.']}
for p in INPUTS:
    assert HASHES[str(p.relative_to(ROOT))] == hashlib.sha256(p.read_bytes()).hexdigest()
manifest['files'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in OUTPUT.iterdir() if p.is_file() and p.name != 'analysis_manifest.json'}
(OUTPUT / 'analysis_manifest.json').write_text(json.dumps(manifest, indent=2))
print('OUTPUT', OUTPUT)
print(pd.DataFrame(summaries).to_string(index=False))
print(pd.DataFrame(tests).to_string(index=False))
