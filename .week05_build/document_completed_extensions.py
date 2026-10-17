"""Integrate the completed descriptive extensions into the single canonical Week 5 notebook."""
from pathlib import Path
import json
import shutil
import nbformat

root=Path(__file__).resolve().parent.parent
path=root/'weekly_notebooks/week05_regional_validation_and_objective1_finalization.ipynb'
backup=root/'weekly_notebooks/earlier iterations/week05_v6_before_country_similarity_20261012.ipynb'
if not backup.exists():shutil.copy2(path,backup)
notebook=nbformat.read(path,as_version=4)
start=next((i for i,c in enumerate(notebook.cells) if c.cell_type=='markdown' and c.source.startswith('## 25 What profiles add')),None)
if start is not None:notebook.cells=notebook.cells[:start]
source=(root/'.week05_build/complete_week05_extensions.py').read_text()
source=source.split("if __name__=='__main__':",1)[0]
source=source.replace('    from frozen_assignment import load_frozen_package, derive_frozen_features, WORRY_SOURCES, HARM_SOURCES\n','')
extension=root/'course_artifacts/week05_country_similarity_and_profile_synthesis_v1/d694096841b06e54'
record=json.loads((extension/'extension_complete.json').read_text())

def md(text):notebook.cells.append(nbformat.v4.new_markdown_cell(text))
def code(text):notebook.cells.append(nbformat.v4.new_code_cell(text))

notebook.cells[0].source += '\n\n**Completed remaining descriptive work:** sections 25–29 report within-profile heterogeneity, information lost by two burden totals, country distances, geographical comparisons, exploratory country clustering, conditional sampling sensitivity, maps and a final completion checklist. These post-validation extensions do not change the frozen models or strengthen the held-out acceptance claim. A pre-extension snapshot is preserved under earlier iterations; there is still only one active Week 5 notebook.'
for cell in notebook.cells:
    if cell.cell_type=='markdown' and cell.source.startswith('## 23 Objective 1 conclusion'):
        cell.source=cell.source.replace('Optional country-similarity analysis remains a separate extension, not unfinished required Objective 1 work.',
            'The optional country-similarity extension is now completed in sections 26–28. It is descriptive, not additional untouched validation or a replacement geographic classification.')

md(r'''## 25 What profiles add beyond burden, and how heterogeneous their members are

**Objective:** finish the protocol's explicit requirement to describe within-profile variation and distinguish profiles from overall worry/harm scores.

**Output:** full burden distributions, original-pattern frequencies, assignment margins and an exact-burden information-loss table, separately for development and held-out respondents.

Use original 0/1/2 worry responses, not the model-specific transformed coordinates. Define \(S_W=\sum_{j=1}^{6} W_j\), ranging from 0 to 12, and \(S_H=\sum_{j=1}^{7}\max(H_{j,\mathrm{personal}},H_{j,\mathrm{known}})\), ranging from 0 to 7. A known-person indicator does not count the number of known people; each domain contributes at most one to the combined total. Also report separate personal and known-person domain counts. Profile summaries retain the original country-balanced analysis weights, normalized within the profile; countries do not receive equal weight again inside each profile.

For every observed exact pair \((S_W,S_H)\), tabulate all frozen profile labels. The largest joint profile mass in each cell gives the **best possible in-sample weighted accuracy of any deterministic label lookup using only those two totals**:
\[
A_{\mathrm{lookup}}=\sum_{s,t}\max_c P(C=c,S_W=s,S_H=t).
\]
This is a descriptive upper bound computed and evaluated on the same cohort, not a trained classifier, cross-validated accuracy or an external-outcome test. Its complement quantifies label information that these two totals cannot reconstruct. It concerns these particular summaries, not every possible definition of burden; it combines domain-pattern and personal/known-person information. Sparse cells may inflate the in-sample upper bound. We make no significance claim.

**Results:** the development ceiling is **62.95% for B** and **51.93% for E**; held-out ceilings are **62.80%** and **51.61%**. Thus approximately 37% and 48% of weighted profile membership cannot be reconstructed from these two exact totals, even with an in-sample lookup. The conditional label entropy is 1.12 bits for B and 1.81 bits for E in development. This supports the narrower descriptive claim that the profiles preserve domain/relationship distinctions absent from these totals. Because clustering used those richer features, some additional information is expected by construction; this is not proof of sociological importance or superior outcome prediction. Objective 3 must evaluate that separately.

**Profiles are not identical people.** The modal exact original response pattern accounts for only **0.5–15.4%** of a development B profile and **2.1–14.4%** of an E profile. Counts of distinct patterns depend strongly on sample size; do not compare them as a standardized diversity measure. Report distributions, rather than treating a centroid or profile mean as every member's response. Low margins remain geometric boundary ambiguity, not probabilities.

For example, B C0's development mean is 4.56 affected domains versus 1.27, 1.54 and 0.71 in C1–C3; its known-person count is 3.99 compared with a personal count of 1.30. E C4 and C5 have almost equal mean worry (0.90 and 0.89 on 0–2) but distinguish crime and severe-weather themes. Transfer is not exact equality: B C2's affected-domain mean increases from 1.54 to 1.77, and E C7's personal-harm mean from 1.28 to 1.63. These changes remain visible despite preserved broad aggregate interpretations.''')
code('# Objective: Preserve the full country-distance and burden-summary implementation; no respondent-profile fitting or retuning.\n'+source)
code(f'''# Objective: Verify completed descriptive extensions and all source fingerprints; replay outputs without recomputing or fitting.
EXTENSION_OUTPUT=ROOT/{str(extension.relative_to(root))!r}
extension_record=json.loads((EXTENSION_OUTPUT/'extension_complete.json').read_text())
assert extension_record['context']=={record['context']!r}
assert not extension_record['respondent_models_refitted'] and not extension_record['heldout_validation_reinterpreted']
extension_inputs=json.loads((EXTENSION_OUTPUT/'extension_design_and_inputs.json').read_text())
for relative_path,digest in extension_inputs['inputs'].items():
    assert extension_sha(ROOT/relative_path)==digest,'Extension input changed: '+relative_path
for relative_path,digest in extension_record['files'].items():
    assert extension_sha(EXTENSION_OUTPUT/relative_path)==digest,'Extension evidence changed: '+relative_path
load_frozen_package(FROZEN_PACKAGE)
burden_synthesis=pd.read_csv(EXTENSION_OUTPUT/'profile_burden_and_heterogeneity.csv')
burden_information=pd.read_csv(EXTENSION_OUTPUT/'burden_only_information_loss.csv')
display(burden_information)
display(burden_synthesis)
display(Image(filename=str(EXTENSION_OUTPUT/'figures/profile_burden_distributions.png')))
print('Original profile labels, split, raw codes, survey weights and all frozen package hashes remain unchanged.')''')

md(r'''## 26 Country similarity without inventing new geographical areas

**Objective:** ask whether countries have similar distributions over the same frozen global profiles, even when the dataset assigns them to different regions.

**Output:** separate B/E country vectors, complete distance matrices, five closest countries per country, dataset-region comparisons and conditional nearest-neighbour sensitivity.

For country \(a\), define \(p_{ac}\) as the survey-weighted proportion of its complete-case respondents assigned to frozen profile \(c\). The vector sums to one. Every country contributes one vector, irrespective of its population or survey sample size; relative survey weights are retained within that country. Calculate B's four-component and E's eight-component vectors **separately**; never align unrelated local-cluster numbers or concatenate these bases.

Use Hellinger distance:
\[
H(a,b)=\frac{1}{\sqrt{2}}\sqrt{\sum_c(\sqrt{p_{ac}}-\sqrt{p_{bc}})^2},\qquad 0\le H\le1.
\]
Zero means identical profile proportions; one means disjoint profile support. Square roots reduce the dominance of large components and retain sensitivity to smaller profile shares. Zero shares are valid: no pseudocount or log transform is needed. This distance compares **profile mixtures**, not all original responses, within-profile semantics, respondent-to-centroid distances, or causal/social equivalence of countries. Different response distributions can map to the same profile mixture. E's finer, sometimes fragile boundaries remain a limitation of its distance basis.

We report the 113 development countries separately from all 142 countries. The latter analysis includes the already-opened holdout and is **post-validation description**, not new external confirmation. The original 15 GlobalRegion categories remain unchanged.

For within/between-region means, first average distances to each country's same-region peers and other-region peers, then average those country means. Development has two singleton regions: both comparisons use the same 111 countries with same-region peers. All-country comparisons include all 142. The random-peer baseline accounts for the available number of countries in each region; it is not a statistical test. Pairwise distances share countries and are dependent. No ordinary correlation p-value or independent-pair significance test is reported.

**Geographical proximity:** compare profile distance with approximate great-circle distance between Natural Earth's country **map-label points**. These points are not capitals, population centroids, distances between borders or evidence of direct adjacency. For large countries/islands they are especially coarse. This answers a broad spatial-distance question only; we do not claim to have tested shared land borders. The dataset's regional comparison is the principal geographic description.

**Results across all 142 countries:** mean same-region versus other-region distance is **0.161 vs 0.211 for B** and **0.202 vs 0.273 for E**. Regional peers are closer on average. However, only **22.5% (B)** and **30.3% (E)** have their closest profile-mixture neighbour in the same region—above the random-peer reference of **8.1%**, but still leaving most nearest neighbours outside the region. Geographic-distance rank correlations are modest: **0.157** and **0.142**. Development-only findings have the same broad direction.

This is not a paradox: there are many more countries outside each region, and a within-region average need not determine the single minimum. B/E pair-distance rankings correlate **0.719**, yet they choose the same exact nearest country for only **12.7%** of countries. Broad similarity patterns are more concordant than individual nearest-country claims.

**Sampling sensitivity:** use 200 IID respondent bootstrap draws within every country, keep original WGT and frozen labels, recompute proportions/distances and keep the same country-tree cut. The same respondent multiplicities are shared across B/E. This is conditional sampling sensitivity, not full complex-survey variance: it ignores PSU/stratification, imputation/nonresponse uncertainty, model fitting and uncertainty in country selection. Exact nearest-neighbour identity recurs in a median **35.5% of B** and **46.0% of E** draws. Close ranks are often interchangeable; report the closest five and sensitivity rather than calling one partner definitive.

For example, B links Serbia with Iran at H=0.0135 despite different dataset regions; the exact neighbour recurs in 74.0% and 87.5% of their conditional draws respectively. Italy/Ivory Coast are even closer in B (H=0.0094), but their exact pairing recurs only 31.0%/33.5%. This illustrates why numerical proximity alone is insufficient to claim a robust sociological twin. Neither example says their original response patterns or circumstances are identical.''')
code('''# Objective: Display country-mixture geography results and complete nearest-neighbour evidence with conditional sampling limits.
country_geography=pd.read_csv(EXTENSION_OUTPUT/'country_geography_summary.csv')
country_distance_agreement=pd.read_csv(EXTENSION_OUTPUT/'B_E_country_distance_agreement.csv')
country_neighbours=pd.read_csv(EXTENSION_OUTPUT/'nearest_country_neighbours.csv')
neighbour_sensitivity=pd.read_csv(EXTENSION_OUTPUT/'conditional_nearest_neighbour_bootstrap.csv')
display(country_geography)
display(country_distance_agreement)
display(neighbour_sensitivity.groupby(['scope','candidate']).exact_nearest_repeated_fraction.agg(['median','mean']))
display(country_neighbours.loc[country_neighbours.scope.eq('all_countries_post_validation')&country_neighbours['rank'].eq(1)])
display(Image(filename=str(EXTENSION_OUTPUT/'figures/same_vs_different_region_distances.png')))
print('Full vectors, all pair distances and all top-five neighbours are saved; no region assignments changed.')''')

md('''## 27 Country clustering: record the attempt, but do not force a new typology

**Objective:** explore whether the country-distance geometry suggests reproducible groups, without substituting them for dataset regions or respondent profiles.

**Output:** average-linkage trees, all cuts k=2–8, silhouette/size/region-ARI diagnostics, group profile meanings and conditional bootstrap recovery.

Average linkage merges the groups with smallest mean pairwise Hellinger distance. It clusters countries, **not respondents**, and does not change the B/E models. Choose the highest-silhouette cut among 2–8 only to illustrate the tree; ties prefer smaller k. The bounded search and selected cut are exploratory, not a validated estimate of an optimal number of country types. No respondent k≥3/40%/D<3 filter is transplanted to country groups. All cuts, including singleton-heavy ones, remain reported.

**B's selected k=2 is one country (Malawi) versus 141 others.** Malawi has 58.1% in B's broad-harm profile and only 5.2% in the lower-worry/harm profile, versus group means of 18.0% and 34.1% among the other countries. Retention is 94.8%. This is a descriptive extreme in profile mixtures, not automatically a data error or a discovered two-type world. A silhouette of 0.414 does not make the 141-country remainder a coherent class.

**E's selected k=2 divides 64 and 78 countries**, largely by lower-worry versus broader/higher-worry composition. The two groups average 53.1% versus 21.6% in E C1 and 4.8% versus 15.1% in E C7. Its silhouette is 0.351 and agreement with the 15 dataset regions is ARI=0.089. This coarse mixture contrast does not capture all thematic diversity and is not a causal geographic explanation.

Both cuts are sensitive to respondent sampling. All-country partition bootstrap ARI median/lower decile is **0.659/−0.011 for B** and **0.863/0.172 for E**. Development-only lower deciles are also weak. A high E median hides fragile alternative tree splits; B's singleton/tree structure can shift sharply. These draws vary estimated country mixtures with respondent models fixed. They do not vary country inclusion or repeat model fitting. We do **not** transfer the 0.80 respondent-model screen to this different experiment, but the observed spread is plainly insufficient to promote these groups as reliable country types.

**Decision:** retain distances, top-five neighbours, continuous heatmaps and the unchanged geographical categories as the useful results. Preserve the dendrograms and illustrative coloured maps as diagnostics of why a new country classification is not warranted. Do not lower a threshold, remove Malawi, search additional linkages or pick another k merely to produce attractive groups.

Implementation references: [SciPy average linkage](https://docs.scipy.org/doc/scipy/reference/generated/scipy.cluster.hierarchy.linkage.html) and [scikit-learn silhouettes with precomputed distances](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_samples.html). Actual installed software versions and input fingerprints are saved in extension_complete.json.''')
code('''# Objective: Inspect all country-tree cuts, profile-mixture meanings and conditional recovery before interpreting coloured groups.
country_cuts=pd.read_csv(EXTENSION_OUTPUT/'country_tree_cut_diagnostics.csv')
country_groups=pd.read_csv(EXTENSION_OUTPUT/'illustrative_country_groups.csv')
country_group_meanings=pd.read_csv(EXTENSION_OUTPUT/'country_group_profile_meanings.csv')
country_group_recovery=pd.read_csv(EXTENSION_OUTPUT/'conditional_country_group_bootstrap.csv')
display(country_cuts)
display(country_groups.groupby(['scope','candidate','country_group']).size().rename('countries').reset_index())
display(country_group_meanings)
display(country_group_recovery.groupby(['scope','candidate']).country_partition_ARI.agg(
    median='median',p10=lambda x:x.quantile(.1),minimum='min',maximum='max'))
for name in ['B','E']:
    display(Image(filename=str(EXTENSION_OUTPUT/'figures'/f'{name}_country_distance_heatmap.png')))
    display(Image(filename=str(EXTENSION_OUTPUT/'figures'/f'{name}_country_dendrogram.png')))
    display(Image(filename=str(EXTENSION_OUTPUT/'figures'/f'{name}_illustrative_country_groups_map.png')))
print('Maps are diagnostic tree cuts, not retained country classifications or new regions.')''')

md('''## 28 Final scientific synthesis after the remaining Week 5 work

**Objective:** integrate the new descriptions without retrospectively changing validation, model identity or claims.

**Output:** the final interpretation for course discussion, slides and the article.

1. **Keep the common global classification.** B4 is the stronger core description; E8 gives complementary worry themes with known fragile boundaries. Country distances use these shared bases, not unmatched locally optimized cluster IDs. The regional models describe context and local splits/merges, not replacement global labels.
2. **Geography matters, but is not sufficient.** Countries in the same dataset region are closer on average. Most exact nearest mixture neighbours nevertheless cross those boundaries; many precise nearest ranks are unstable. This supports studying cross-region similarities, not claiming geography is irrelevant or proposing new geographic areas.
3. **Do not force country clusters.** B's silhouette winner mainly isolates Malawi; E resolves a broad composition contrast but lacks consistent lower-tail recovery. Neither exploratory cut is adopted as a country typology. The negative grouping result is a useful research finding, not a reason to change thresholds after seeing it.
4. **Profiles contain more than two totals, but remain broad summaries.** Exact worry/harm totals cannot recover all labels; domain and personal/known-person information remains. Members are heterogeneous. This does not establish added outcome-prediction value or natural classes; those are different claims.
5. **Keep the held-out conclusion geographically qualified.** The new all-country description is performed after validation and adds no untouched confirmation. Complete-case selection, within-profile semantic variation, country-specific fit limits and survey-design uncertainty remain. Country mixtures compress those complexities; similar mixtures do not imply interchangeable societies.

Objective 1 is complete within the approved protocol and the now-completed descriptive extension. No fixed-model holdout refit, native-Ward rerun, new regional definitions, later-wave validation or supervised Objective 2 modelling is required to close this stage. The older Moodle wording about an independent holdout refit is not silently reintroduced: the current 7 October protocol explicitly treats it as optional. Any later model redesign requires a new development/validation cycle.''')

md('''## 29 Completion checklist and evidence integrity

**Objective:** make the completed scope and reusable files explicit, with a final integrity check.

**Output:** a saved Week 5 completion checklist, extension manifest and links from the existing final evidence inventory.

The original frozen package, held-out transfer record and ID-linked handoff are immutable. New tables/figures live in a fingerprinted extension directory and are referenced from the reporting inventory only. All previous scientific failures and qualifications remain visible. The pre-extension notebook snapshot is kept under earlier iterations. There is one active canonical Week 5 notebook; replay verifies saved evidence and does not run clustering computations.''')
code('''# Objective: Save the final completion checklist and link the verified extension without altering sealed models or original validation results.
completion_checklist=pd.DataFrame([
    {'item':'Development global/regional prevalence, semantics, distances and maps','status':'complete','evidence':'Sections 1–10'},
    {'item':'Bounded regional k search and unchanged 0.80 stability qualification','status':'complete','evidence':'Sections 11–17'},
    {'item':'Final B4/E8 decision, model freeze and exact development replay','status':'complete','evidence':'Section 18; sealed package'},
    {'item':'Held-out eligibility, fixed assignment, uncertainty and geographic limits','status':'complete','evidence':'Sections 19–23a; original transfer record'},
    {'item':'Within-profile heterogeneity and comparison with burden totals','status':'complete','evidence':'Section 25; new summary/distribution tables'},
    {'item':'Country distances, regional/spatial comparisons and nearest-neighbour sensitivity','status':'complete descriptive extension','evidence':'Section 26; country vectors/distance matrices'},
    {'item':'Exploratory country grouping and maps','status':'complete; no country typology adopted','evidence':'Section 27; all cuts and bootstrap qualifications'},
    {'item':'ID-linked assignment handoff for later objectives','status':'complete','evidence':'Section 24; 146,910 IDs, 137,460 assigned'},
    {'item':'Held-out refits, later waves, native Ward or new geographic definitions','status':'not required; not performed','evidence':'Current protocol scope; no silent expansion'},
])
extension_csv(completion_checklist,TRANSFER_OUTPUT/'week05_completion_checklist.csv')
load_frozen_package(FROZEN_PACKAGE)
load_frozen_package(HANDOFF_OUTPUT/'frozen_models')
for group in ['tables','assignments']:
    for name,digest in transfer_record[group].items():assert file_sha256(TRANSFER_OUTPUT/name)==digest
for name,digest in handoff_record['files'].items():assert file_sha256(HANDOFF_OUTPUT/name)==digest
for name,digest in extension_record['files'].items():assert extension_sha(EXTENSION_OUTPUT/name)==digest
final_inventory['descriptive_extension']={
    'directory':str(EXTENSION_OUTPUT.relative_to(ROOT)),
    'context':extension_record['context'],
    'manifest_sha256':extension_sha(EXTENSION_OUTPUT/'extension_complete.json'),
    'respondent_models_refitted':False,'country_groups_adopted':False,
    'status':'completed; exploratory country similarity and burden/heterogeneity synthesis',
    'interpretation':'country-mixture similarity, not causal equivalence or new held-out confirmation'}
final_inventory['tables']={p.name:file_sha256(p) for p in sorted(TRANSFER_OUTPUT.glob('*.csv'))}
atomic_json(final_inventory,TRANSFER_OUTPUT/'objective1_final_evidence_inventory.json')
display(completion_checklist)
print('Week 5 complete. Frozen package, original transfer results and handoff hashes verified unchanged.')''')

nbformat.validate(notebook)
nbformat.write(notebook,path)
print('Integrated completed extensions into:',path)
print('Pre-extension executed snapshot:',backup)
print('Cells:',len(notebook.cells))
