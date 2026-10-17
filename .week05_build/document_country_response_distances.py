"""Append verified aggregate results and a self-contained implementation to Week 5."""
from pathlib import Path
import hashlib
import json
import nbformat
import pandas as pd

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'course_artifacts/week05_country_response_distances_v1/e1ecf01551bcf2da'
notebook=ROOT/'weekly_notebooks/week05_regional_validation_and_objective1_finalization.ipynb'
nb=nbformat.read(notebook,as_version=4)
heading='## 32 Direct country-response distances and component reporting'
assert not any(c.cell_type=='markdown' and c.source.startswith(heading) for c in nb.cells), 'Do not replace later notebook edits.'
markdown=r'''## 32 Direct country-response distances and component reporting

**Objective:** compare countries in the original worry and personal/known-person harm response distributions, avoiding the information loss from reducing each country to only four or eight profile shares. Keep the historical Hellinger analysis available: it answers a different question about the mixture of frozen profiles.

**Status and chronology:** this is a post-validation descriptive extension, added on 14 October 2026 after inspecting counterintuitive neighbours in the profile-mixture maps. It does not modify B4/E8, their assignments, the frozen split, regions, or held-out validation. It is not an untouched confirmation. The feature-block allocations are copied from B (0.50) and E (0.75), not optimized to return familiar neighbours. Income and geography are not inputs to the distance.

### Cohort and weighting

Use the exact complete-response cohort of 137,460 respondents (109,488 development; 27,972 held-out) across 142 countries. Validate counts against the original country-profile vectors and, where available, IDs against the protected frozen assignment registry. Within each country normalize the original WGT over included respondents. Missing responses are not imputed and feature-specific denominators are not substituted. These are complete-case survey-weighted summaries, not unrestricted national population estimates.

For country $c$, eligible respondent $i$, feature $j$ and category $r$,
\[
w_{ci}=\frac{\mathrm{WGT}_{ci}}{\sum_{i\in\mathcal I_c}\mathrm{WGT}_{ci}},\qquad
q_{cj}(r)=\sum_{i\in\mathcal I_c}w_{ci}\mathbf1\{X_{cij}=r\}.
\]
Six worry features have categories 0/1/2; seven personal and seven known-person harm indicators are binary. The country reference contains 46 category probabilities (18 worry, 14 personal-harm, 14 known-person-harm), not respondent records.

### Distances and components

\[
T_j(c,d)=\tfrac12\sum_r|q_{cj}(r)-q_{dj}(r)|,
\quad D_W=\tfrac16\sum_{j\in W}T_j,
\quad D_S=\tfrac17\sum_{j\in H_S}T_j,
\quad D_O=\tfrac17\sum_{j\in H_O}T_j.
\]
For binary harm, $T_j$ is the absolute difference in prevalence. Then
\[
D_\alpha=\alpha D_W+\tfrac{1-\alpha}{2}D_S+\tfrac{1-\alpha}{2}D_O.
\]
B-associated weights are 50/25/25; E-associated weights are 75/12.5/12.5. All distances are bounded by 0 and 1. No square roots are needed because total variation is linear. This preserves nominal block allocation, not K-means' centred Euclidean geometry or the middle-category spacing in 0/1/3 coding.

### What the numbers mean

Report the raw overall distance, worry-category mismatch ×100, personal/known-person mean absolute prevalence gaps in percentage points, a descriptive nearest-country rank and the overall distance percentile. The percentile is the upper empirical CDF over distinct unordered country pairs in the chosen scope: 10,011 pairs for all 142 countries; 6,328 for 113 development countries. Exact ties are included. It is not a p-value, confidence measure or probability that countries are equivalent. Country pairs are dependent because they share countries.

Only map colours are rescaled from zero (the reference country itself) to its maximum distance, in seven equal-width bands. Compute the overall distance from raw components **before** this rescaling. Reference-specific normalization is generally asymmetric and cannot replace a distance for country clustering or cross-country comparisons. Never normalize each component by its own maximum and then recombine: that would introduce country-dependent effective allocations.

### Main illustrative findings

Under direct-response B allocation, Canada's USA distance is 0.0635 (rank 1, pair percentile 1.83), compared with Iran at 0.0837 (rank 19, percentile 8.65) and Cambodia at 0.1665 (rank 113, percentile 65.63). In the historical B4 mixture comparison Iran was fifth and Cambodia second. The direct comparison exposes differences hidden by coarse profile shares; it is not validated merely because Canada becomes nearest.

Finland's nearest country is Iceland under both allocations. Finland–Sweden has personal-harm distance 0.00865 but worry distance 0.11602. Its overall distance rises from 0.06848 under B allocation to 0.09225 under E allocation. The components explain this change without claiming that one neighbour list is the natural or correct ordering.

The direct-response income-gap rank correlations are 0.3185 (B allocation) and 0.2618 (E allocation), with development-only values 0.3192 and 0.2600. These are not the historical Hellinger correlations (0.211 and 0.229), and the earlier Hellinger permutation references do not apply. The new income summaries are descriptive only.

### Limitations and decision

This is a metric on the collection of marginal category distributions, but only a pseudometric on the full joint response law: equal marginals can conceal different combinations within people. No new joint-distribution analysis or resampling uncertainty has been computed for these distances. Exact ranks, especially when scores are close, remain descriptive. Survey-design limitations, translation, reporting, known-person networks and complete-case selection still apply.

Adopt direct original-response comparison as the main country-distance display, while retaining explicitly labelled profile-mixture Hellinger views and all historical results. Do not reinterpret country similarity as societal equivalence or change the frozen respondent profile models.

The following implementation reconstructs the aggregates without fitting any model; the reporting cell verifies saved results by hash. Public notebook outputs are cleared separately, but only aggregate country results appear in this new section.
'''
implementation=(ROOT/'.week05_build/country_response_distances.py').read_text().split("if __name__ == '__main__':")[0]
code=r'''# Objective: verify and display the saved direct-response extension; no profile fitting.
from pathlib import Path
import hashlib, json
import pandas as pd
from IPython.display import display
RESPONSE_ROOT=Path.cwd().resolve()
if not (RESPONSE_ROOT/'course_artifacts').is_dir():
    RESPONSE_ROOT=next(p for p in RESPONSE_ROOT.parents if (p/'course_artifacts').is_dir())
RUN_COUNTRY_RESPONSE_RECOMPUTE=False  # True recomputes country summaries only; never fits respondent models.
RESPONSE_OUTPUT=RESPONSE_ROOT/'course_artifacts/week05_country_response_distances_v1/e1ecf01551bcf2da'
if RUN_COUNTRY_RESPONSE_RECOMPUTE:
    assert run_response_distances(RESPONSE_ROOT)==RESPONSE_OUTPUT
response_manifest=json.loads((RESPONSE_OUTPUT/'analysis_manifest.json').read_text())
assert response_manifest['design']['respondent_models_refitted'] is False
for filename,digest in response_manifest['files'].items():
    assert hashlib.sha256((RESPONSE_OUTPUT/filename).read_bytes()).hexdigest()==digest,filename
for relative,digest in response_manifest['source_hashes'].items():
    source=RESPONSE_ROOT/relative
    if source.exists():
        assert hashlib.sha256(source.read_bytes()).hexdigest()==digest,relative
display(pd.read_csv(RESPONSE_OUTPUT/'response_distance_summary.csv'))
response_neighbours=pd.read_csv(RESPONSE_OUTPUT/'nearest_country_responses.csv')
display(response_neighbours.query("scope=='all_countries_post_validation' and COUNTRY_ISO3 in ['USA','FIN'] and metric in ['B','E'] and rank<=10")
    [['metric','Country','rank','peer_country','distance','distance_percentile','worry','self','known']])
display(pd.read_csv(RESPONSE_OUTPUT/'illustrative_country_comparisons.csv'))
display(pd.read_csv(RESPONSE_OUTPUT/'response_income_summary.csv'))
print('Verified saved direct-response distances. No clustering refitted; historical profile-mixture results retained.')
'''
cell=nbformat.v4.new_code_cell(code)
outputs=[]
for filename in ['response_distance_summary.csv','nearest_country_responses.csv','illustrative_country_comparisons.csv','response_income_summary.csv']:
    table=pd.read_csv(OUT/filename)
    if filename=='nearest_country_responses.csv':
        table=table.query("scope=='all_countries_post_validation' and COUNTRY_ISO3 in ['USA','FIN'] and metric in ['B','E'] and rank<=10")
        table=table[['metric','Country','rank','peer_country','distance','distance_percentile','worry','self','known']]
    outputs.append(nbformat.v4.new_output('display_data',data={'text/plain':table.to_string(index=False),'text/html':table.to_html(index=False)}))
outputs.append(nbformat.v4.new_output('stream',name='stdout',text='Verified saved direct-response distances. No clustering refitted; historical profile-mixture results retained.\n'))
cell.outputs=outputs
nb.cells.extend([nbformat.v4.new_markdown_cell(markdown),nbformat.v4.new_code_cell(implementation),cell])
nbformat.validate(nb);nbformat.write(nb,notebook)
print('Appended the implementation, mathematical protocol, interpretation and saved aggregate results to Week 5.')
