from pathlib import Path
import hashlib
import nbformat

ROOT = Path(__file__).resolve().parent.parent
source_path = Path(__file__).with_name('week05_core.py')
source = source_path.read_text()
sections = source.split('# %% ')[1:]
chunks = {section.split('\n', 1)[0]: section.split('\n', 1)[1] for section in sections}
def md(text):
    return nbformat.v4.new_markdown_cell(text.strip())
def code(text):
    return nbformat.v4.new_code_cell(text.strip())

cells = [md('''
# Week 5 Global profile distributions and regional validation

This notebook begins the development-only regional analysis from the validation protocol dated 7 October 2026. It reuses the saved **B** and **E** global K-means solutions rather than fitting replacements. Sampled Ward is already corroborating development evidence for E; a native-Ward comparison is not required by the protocol.

The sequence is: audit and verify the development inputs; describe fixed-global profile prevalence and original-response meaning by region; specify regional sampling from country metadata; run the bounded regional fits; test selected regional fits; compare local and global original-response profiles; review the final model scope. **No held-out response file is opened anywhere in this version.** Model freezing and held-out validation will follow the development-side review, not happen automatically.

This is a self-contained notebook. All modelling functions appear below. It writes new fingerprinted Week 5 outputs and preserves the Week 3/4 notebooks and earlier Week 5 versions. Points 1 and 2 cover the fixed-global geographical analysis and regional refitting/stability, respectively. Execution was authorized on 12 October 2026. Saved fingerprint-matched caches are reused; no global model is refitted. Synthetic tests confirm implementation, not scientific validity.
'''), md('''
## 1 Fixed candidates and execution controls

B uses 0/1/2 worry coding, balanced worry/harm allocation, and four clusters. E uses 0/1/3 worry coding, worry allocation 0.75, and eight clusters. Both use complete responses, separate personal/known-person harm, six within-person centred worry values, and the appended worry mean. There is no imputation, z-standardization, or PCA.

Follow the Moodle rule: 50 country samples of floor(0.8×N) countries, without replacement within each sample, for regions with at least five countries. Repeated subsets across samples are allowed and reported. Use leave-one-country-out for two–four countries. A single-country region has no country test. Country sampling is uniform within the existing region, not the global crossed-stratum quota design. LOO summaries are not a 50-fit country-stability claim. Respondent subsamples retain approximately 80% within every regional country. All of these limitations are reported before results are interpreted.
'''), code(chunks['Imports and fixed candidate definitions']), code('''
from IPython.display import display, Markdown
import matplotlib.pyplot as plt
get_ipython().run_line_magic('matplotlib', 'inline')

ROOT = Path.cwd()
if not (ROOT / 'course_artifacts').exists():
    ROOT = ROOT.parent
assert (ROOT / 'course_artifacts').is_dir(), 'Run from the course root or weekly_notebooks directory.'

REGIONAL_DESIGN_APPROVED = True
RUN_REGIONAL_REFERENCES = True
RUN_REGIONAL_STABILITY = True
IMPLEMENTATION_SHA256 = '__IMPLEMENTATION_SHA256__'

print('Regional design approved:', REGIONAL_DESIGN_APPROVED)
print('Reference fits enabled:', RUN_REGIONAL_REFERENCES)
print('Stability enabled:', RUN_REGIONAL_STABILITY)
print('Held-out responses remain unopened; no final model is frozen in this notebook version.')
'''.replace('__IMPLEMENTATION_SHA256__', hashlib.sha256(source.encode()).hexdigest())), md(r'''
## 2 Reproduce the Week 4 transformation

Let \(q_{ij}\) be respondent i's worry values after top-category recoding and division by 2 or 3. Let \(\bar q_i\) be their mean. Each centred worry value and the appended mean receives multiplier \(\sqrt{\alpha/6}\); each of the 14 harm indicators receives \(\sqrt{(1-\alpha)/14}\).

These are exactly the Week 4 rules, including the deliberately reduced overall-worry contribution. Regional fitting does not learn a new scale. Survey weights are normalized within countries, then every retained regional country receives equal total weight. In every subsample the weights are recalculated on the training respondents; comparison/profile weights describe the full regional cohort.
'''), code(chunks['Preserve the Week 4 feature geometry and equal-country weights']), md('''
## 3 Verify development inputs and saved global assignments

Read only the development-only Week 4 prepared input and country metadata. Apply the same eligibility and complete-response rules in the same row order. Verify the legacy Week 4 data/design fingerprint, then reproduce every stored B/E label from its saved centres. A mismatch stops the notebook; it is not repaired by silently refitting.

The audit distinguishes the 116,820 prepared development respondents, the 116,808-row Week 4 input after entirely unobserved profiles were removed, and the 109,488 complete-case cohort. Region labels come from the supplied data dictionary; no regions are invented from response patterns.
'''), code('''
data, country_audit, regions, global_references, provenance = prepare_development(ROOT)
CONTEXT = digest_json({'provenance': provenance, 'design': REGIONAL_DESIGN,
                       'implementation_sha256': IMPLEMENTATION_SHA256})
OUTPUT = ROOT / 'course_artifacts/week05_regional_validation_v3' / CONTEXT[:16]
OUTPUT.mkdir(parents=True, exist_ok=True)
atomic_json({'context': CONTEXT, 'provenance': provenance, 'regional_design': REGIONAL_DESIGN,
             'design_approved': REGIONAL_DESIGN_APPROVED, 'heldout_responses_used': False},
            OUTPUT / 'run_manifest.json')
table_write(country_audit, OUTPUT / 'development_complete_case_country_audit.csv')
table_write(regions, OUTPUT / 'development_region_audit.csv')
print('Verified:', len(data), 'complete respondents;', data.COUNTRY_ISO3.nunique(), 'development countries.')
print('B/E cached labels are reproduced exactly. No global K-means refit.')
print('Output directory:', OUTPUT.relative_to(ROOT))
display(regions)
display(previous_stability(ROOT)[['candidate','experiment','median_pairwise','p10_pairwise']])
'''), md('''
## 4 Comparison measures and original-response distributions

Unweighted ARI measures membership agreement on the same respondents, independent of cluster IDs. Weighted overlap tables allow many local clusters to correspond to one global cluster and vice versa. Local-to-global purity sums the largest global overlap for each local cluster; reverse purity sums the largest local overlap for each global cluster. A one-to-one matched share is also reported, but is restrictive when k differs.

Original-unit tables retain every worry category and both personal and known-person harm indicators, with cluster-versus-outside contrasts. The global structural screen (k=3–10, coverage≥90%, largest share≤40%, D<3) is reported as a **comparison benchmark**, not a mandatory rule for regional structure. A local two-group solution can be informative without passing that global benchmark. Neither ARI nor overlap is a significance test.
'''), code(chunks['Label-independent overlap, structural metrics, and original-unit profiles']), md('''
## 5 Fix and audit regional sampling plans before fitting

Reuse the same regional respondent/country plans across B/E and k candidates. Respondent sampling keeps approximately 80% without replacement within every country. Country sampling uses whole countries, with no response-derived selection. The audit reports the exact test type, the number of distinct fits, and every country's omission count.

With two–four countries, use one fit per omitted country. With five or more countries, use all 50 random samples even when subsets repeat; report the exact number of distinct country subsets and actual retained-country fraction. Rounding down means, for example, a six-country region retains four countries, not five. With only one development country, country stability is unavailable. All pairwise ARIs are dependent; they are descriptive summaries, not independent observations for a statistical test.
'''), code(chunks['Sampling plans fixed from metadata before any regional model fitting']), code('''
sampling_audits = []
omission_audits = []
for region in sorted(data.GlobalRegion.unique()):
    frame = data.loc[data.GlobalRegion.eq(region)].reset_index(drop=True)
    plans, omission, info = make_regional_plans(frame, int(region), REGIONAL_DESIGN)
    sampling_audits.append({'GlobalRegion': int(region), **info})
    omission['GlobalRegion'] = int(region)
    omission_audits.append(omission)
    atomic_joblib({'context': CONTEXT, 'plans': plans, 'info': info}, OUTPUT / f'region_{region}_sampling_plans.joblib')
sampling_audit = regions.merge(pd.DataFrame(sampling_audits), on='GlobalRegion', validate='one_to_one')
table_write(sampling_audit, OUTPUT / 'regional_sampling_design_audit.csv')
table_write(pd.concat(omission_audits, ignore_index=True), OUTPUT / 'country_omission_design_audit.csv')
display(sampling_audit[['region_name','countries','complete_respondents','country_diagnostic_y',
                       'distinct_country_fits','possible_80pct_subsets']].rename(columns={'country_diagnostic_y':'country_test'}))
'''), md('''
## 6 Regional reference fits

Fit K-means within each region under the fixed B and E geometries, with k=2–10 and 20 initializations per fit. B4/E8 are the matched-resolution comparisons. This is a bounded k search, not a new encoding/algorithm search. Fixed seeds are recorded; one numerical thread per fit limits resource contention.

Caches depend on input and code fingerprints, software versions, regional design, specification, seed, and training indices. Recorded failures remain failures until explicitly retried; retries preserve the previous failure. Failed, degenerate, and iteration-limit fits are reported rather than assigned substitute results.
'''), code(chunks['Cached regional K-means fits with numerical diagnostics and recorded failures']), code(chunks['Regional search and comparisons without held-out access']), code('''
if RUN_REGIONAL_REFERENCES:
    assert REGIONAL_DESIGN_APPROVED, 'Approve the regional settings before fitting.'
    regional_summary, regional_fitted = regional_references(data, global_references, REGIONAL_DESIGN, OUTPUT, CONTEXT)
    display(regional_summary.loc[regional_summary.matched_global_resolution])
else:
    regional_summary = pd.DataFrame()
    regional_fitted = {}
    print('Regional reference fitting is disabled. No regional results are implied by the audit.')
'''), md('''
## 7 Stability of selected regional fits

Start with matched-resolution B4/E8 in every region. Add other local k values only after documenting their reference-profile interpretation; declare the shortlist before the stability run. We do not run 50+50 refits for all 270 regional candidates automatically.

Each fit predicts the full same regional cohort. For respondent resampling, all 50 fits must succeed; median and lower-decile pairwise ARI≥0.80 remain the benchmark. The same rule applies to a full 50-fit country test. LOO summaries use their actual number of fits and explicitly cannot pass that 50-fit country benchmark. Regional structural benchmarks remain separate from stability; there is no automatic winner or final global model revision.
'''), code('''
REGIONAL_STABILITY_SHORTLIST = [(int(region), name, spec.global_k)
    for region in sorted(data.GlobalRegion.unique()) for name, spec in SPECIFICATIONS.items()]

if RUN_REGIONAL_STABILITY:
    assert REGIONAL_DESIGN_APPROVED, 'Approve regional settings first.'
    assert regional_fitted, 'Run/reload regional reference fits first.'
    stability_summary = regional_stability(data, regional_fitted, REGIONAL_STABILITY_SHORTLIST,
                                          REGIONAL_DESIGN, OUTPUT, CONTEXT)
    display(stability_summary)
else:
    stability_summary = pd.DataFrame()
    print('Regional stability is disabled; no country-stability claim is made.')
'''), md('''
## 8 Inspect local structure and compare it with global profiles

For every completed regional reference, inspect the saved overlap and original-response tables. Distinguish changed frequency from changed profile meaning. Examine which groups recur, merge, split, or appear only locally. The heatmap below shows original very-worried proportions and observed personal/known-person harm proportions; these are not the transformed model inputs.

Local labels are arbitrary and are not automatically renamed to global profile IDs. Many-to-one overlap and directional purity must guide any proposed correspondence. Record limitations of single-country regions and unsupported fixed-k fits explicitly.
'''), code('''
def plot_regional_profile(region, candidate, k):
    path = OUTPUT / 'regional_original_profiles.csv'
    if not path.exists():
        print('No regional profile output yet. Enable the approved reference stage first.')
        return
    profiles = pd.read_csv(path)
    selected = profiles.loc[profiles.region.eq(region) & profiles.candidate.eq(candidate) & profiles.k.eq(k)]
    if selected.empty:
        raise ValueError('No successful fit for that region/specification/k.')
    worry = selected.loc[selected.feature.isin(WORRY) & selected.category.eq(2)]
    harm = selected.loc[selected.feature.isin(PERSONAL + KNOWN) & selected.category.eq(1)]
    matrices = [worry.pivot(index='feature', columns='cluster', values='proportion').reindex(WORRY),
                harm.pivot(index='feature', columns='cluster', values='proportion').reindex(PERSONAL + KNOWN)]
    fig, axes = plt.subplots(1, 2, figsize=(13, 7), gridspec_kw={'width_ratios':[1,1]})
    for ax, matrix, title in zip(axes, matrices, ['Very worried', 'Harm experienced']):
        image = ax.imshow(matrix, vmin=0, vmax=1, aspect='auto', cmap='YlGnBu')
        ax.set_yticks(range(len(matrix)), matrix.index.str.replace('_', ' '))
        ax.set_xticks(range(len(matrix.columns)), ['C'+str(c) for c in matrix.columns])
        ax.set_xlabel('Local cluster ID')
        ax.set_title(title)
        for row in range(len(matrix)):
            for col in range(len(matrix.columns)):
                value = matrix.iloc[row,col]
                ax.text(col, row, f'{100*value:.0f}', ha='center', va='center',
                        color='white' if value > .55 else 'black', fontsize=8)
    region_name = regions.set_index('GlobalRegion').loc[region,'region_name']
    fig.suptitle(f'{region_name}: {candidate} geometry, local k={k}; equal-country weighted percentages')
    fig.tight_layout()
    plt.show()

if len(regional_summary):
    display(regional_summary.loc[regional_summary.matched_global_resolution,
        ['region','candidate','k','status','ari_unweighted','local_to_global_purity',
         'global_to_local_purity','global_benchmark_pass']])
else:
    print('Profile comparison awaits regional reference computation.')
# Example after fitting: plot_regional_profile(13, 'E', 8)
'''), md('''
## 9 Development decision and freeze preparation

The regional analysis may qualify B/E interpretations or justify a documented development-side revision. B and E can be complementary; do not force them into one hierarchy. Review the regional fits and limitations before deciding whether one or both models are retained. Optional native-Ward comparison is not a required completion step.

The table below is a checklist, not a freeze record. Completed regional results do not automatically approve final scope or held-out access. The next coding stage will save the approved centres, profile IDs, transforms, provenance, development distance thresholds, and decision log; only then implement and run the gated held-out transfer diagnostics. The distance thresholds saved here are provisional development references, not a final freeze. Do not use the superseded Week 4 search-v3 handoff as the candidate source.
'''), code(chunks['Frozen-model preparation only No freeze decision or held-out access']), code('''
checklist = freeze_checklist(data, global_references)
checklist['regional_analysis_complete'] = bool(len(stability_summary)==60)
table_write(checklist, OUTPUT / 'freeze_preparation_checklist.csv')
display(checklist)
display(Markdown('**Current execution status:** development audit and B/E reload verification complete. '
                'Regional reference/stability results depend on the switches above. '
                '**Held-out responses remain unopened. No final model freeze is claimed.**'))
''')]

new_cells = [md('''
## 4a Geographical distributions using fixed global profiles

Before regional refitting, retain the existing global B/E assignments. Report counts and percentages globally, within all 15 recorded regions, and within each of the 113 development countries. Survey weights are normalized within countries, and each retained country has equal total weight in its region. Unweighted respondent shares are also saved; they describe a different estimand. These are complete-case development summaries, not estimates of worldwide or regional population-proportional prevalence.

Holding centres fixed makes the profile IDs comparable. It does not imply that every region's members have the same original responses or fit the centre equally well. Save all original worry categories and personal/known-person harm proportions within each region/profile, with differences from the global profile and from outside the profile within that region. No model is refitted, and this is not an external validation result because these regions contributed to model development.
'''), code(chunks['Fixed global assignments by country and region']), code('''
fixed_prevalence, fixed_original_profiles, fixed_semantic_differences = fixed_global_geographical_results(
    data, global_references, regions, OUTPUT)
print('Saved global, regional, and country prevalence, with complete regional original-response distributions.')
display(fixed_prevalence.loc[fixed_prevalence.scope.eq('global'),
    ['candidate','cluster','working_description','respondents','equal_country_weighted_share']])
for name in SPECIFICATIONS:
    selected = fixed_prevalence.loc[fixed_prevalence.candidate.eq(name)
                                   & fixed_prevalence.scope.isin(['global','region'])].copy()
    selected['weighted_percentage'] = 100 * selected.equal_country_weighted_share
    pivot = selected.pivot(index='area_name', columns='cluster', values='weighted_percentage')
    order = ['Global development'] + regions.sort_values('GlobalRegion').region_name.tolist()
    display(Markdown('### '+name+' fixed-global cluster shares by geographical area (%)'))
    display(pivot.reindex(order).round(1))
print('Checks passed: every area sums to 100%; regional country-weighted averages reproduce global shares.')
'''), md('''
## 4b Interpretation of the fixed-global regional distributions

**B describes both worry and harm.** Globally, C0 comprises 18.53% and has broad exposure especially through personally known people; C1 (26.02%) emphasizes crime, weather and traffic worry with less harm; C2 (21.68%) emphasizes food/water worry with substantial crime worry; C3 (33.77%) has lower worry and harm. These are working descriptions tied to the saved cluster IDs, not newly frozen names.

The lower-worry/harm C3 share is 53.4% in Northern/Western Europe and 51.6% in Central Asia, versus 17.7% in Central/Western Africa and 13.1% in Southern Africa. The broad-harm C0 share is about 29.6–29.8% in Central/Western and Eastern Africa, compared with 7.6% in Central Asia and 12.0% in Northern/Western Europe. These differences describe the retained respondents under equal-country weighting; they do not establish causes, universal regional traits, or country-level homogeneity.

**E gives a finer worry description.** Globally, its lower-worry C1 comprises 36.11%. Its share is 59.9% in Northern/Western Europe, 52.3% in Central Asia and 52.2% in Eastern Europe, versus 18.2% in Central/Western Africa and 11.1% in Southern Africa. Broad high-worry C7 is 20.0% in Central/Western Africa and 18.7% in Eastern Africa, compared with 2.5% in Northern/Western Europe. B and E therefore show a similar broad geographical worry gradient, while B additionally separates substantial known-person harm. Their similarly worded low-worry groups are not identical memberships and must not be treated as the same cluster.

**Thematic differences matter too.** Under E, weather-focused C5 is 14.2% in Eastern Asia and 12.5% in Southern Europe; food/water C6 is 14.8% in Northern Africa but 3.5% in Southeastern Asia. These identify contrasts to investigate in the full original-response tables, not proof that every country in those regions shares one pattern.

**E requires a specific caution.** Its traffic-focused C0, crime-focused C4 and weather-focused C5 each have 100% very-worried responses for their defining item in the saved global assignments; C3 has 100% very worried about both crime and traffic. Regional frequencies can therefore partly reflect these response-category combinations. Stable groups and Ward agreement do not by themselves prove discrete natural types or establish added value beyond burden/category summaries.

**Semantic compatibility remains a separate empirical check.** The saved regional original-response tables and descriptive maximum category differences show how members of each fixed profile differ by region. There is no automatic semantic pass/fail threshold. Inspect defining contrasts, harm, and overall intensity together; a stable defining category can coexist with differences in other features. Distance/margin diagnostics will provide an additional representation-quality check. The example regions highlighted above are descriptive contrasts, not a preselected significance test or a complete explanation.

**Coverage and uncertainty limit interpretation.** Northern America has only the United States in development; Australia/New Zealand has only New Zealand. These are single-country summaries, not replicated regional evidence. Complete-case retention varies by country and may select respondents systematically. No confidence intervals or statistical-significance claims are provided by these point estimates. Region differences may conceal stronger differences between countries, so country prevalence is saved alongside the regional tables. Maps are planned to show these fixed-global proportions and the coverage limits, not to replace the tables.
''')]
# Insert only after the original-unit profile helper has been defined.
insert_at = next(i for i,c in enumerate(cells) if c.cell_type == 'markdown'
                 and c.source.startswith('## 5 Fix and audit'))
cells[insert_at:insert_at] = new_cells
quality_cells = [md('''
## 4c Fixed-global representation quality

Point 1 is not complete with prevalence alone. Calculate nearest-centre distances and the normalized nearest/second-nearest margin for every development respondent, without changing assignments. Save profile-specific weighted development 95th-percentile distances and report exceedance overall and by region/country. The margin is a geometric diagnostic, not a probability; distances must be interpreted within B or E, not as comparable scales across models. Thresholds are descriptive, provisional development references, not held-out pass/fail criteria or a final model freeze. Original-response semantic differences remain available alongside these diagnostics.
'''), code(chunks['Fixed-global representation quality and map-ready country summaries']), code('''
quality_summary, provisional_distance_thresholds = fixed_assignment_quality(data, global_references, regions, OUTPUT)
display(quality_summary.loc[quality_summary.scope.eq('region') & quality_summary.cluster.eq(-1),
    ['candidate','area_name','distance_median','distance_p90','margin_median','margin_p10','profile_p95_exceedance']])
display(fixed_semantic_differences.loc[fixed_semantic_differences.scope.eq('region')]
        .sort_values('largest_absolute_category_difference_pp',ascending=False).head(12))
'''), md('''
## 4d Country prevalence maps

Use the saved global assignments, not independently fitted local labels. Every panel uses the same 0–100% colour scale. Held-out countries are hatched and contain no analysed responses; countries outside the development set have no profile value rather than a zero. Tiny countries use coloured dots so they remain visible. These are within-country survey-weighted shares among complete respondents, not country populations or causal risk estimates. Natural Earth cartography is public-domain map geometry only; the country-to-region classification still comes exclusively from the survey dataset. No geographical regrouping is performed.

Source: [Natural Earth](https://www.naturalearthdata.com/about/terms-of-use/), cached 1:50m country boundaries. Country-key joins and the boundary-file SHA256 are saved. A country missing from the map keys stops the map stage rather than being silently omitted.
'''), code(chunks['Prevalence maps using external cartography only Not external responses']
    .replace('bounds=np.array(polygons[0][0])',
             'bounds=np.array(max(polygons,key=lambda polygon: np.ptp(np.array(polygon[0])[:,0])*np.ptp(np.array(polygon[0])[:,1]))[0])')
    .replace("loc='lower center',ncol=2)","loc='lower center',bbox_to_anchor=(.5,.04),ncol=2)")
    .replace("fig.text(.02,.025,","fig.text(.02,.015,")), code('''
from IPython.display import Image
map_files = prevalence_maps(fixed_prevalence, ROOT, OUTPUT)
for path in map_files:
    display(Image(filename=str(path)))
''')]
insert_at = next(i for i,c in enumerate(cells) if c.cell_type == 'markdown' and c.source.startswith('## 5 Fix and audit'))
cells[insert_at:insert_at] = quality_cells
regional_semantics_cells = [md('''
## 8a Regional semantic correspondence and exploratory resolutions

Compare matched-resolution local clusters with global original-response distributions. Associate each local cluster with its largest weighted global overlap; this is an association, not an automatic identity or renaming. Report that dominant global fraction and mean feature-wise total variation across the 20 original categorical features (six worry, fourteen harm indicators). For each feature, total variation is half the sum of absolute category-probability differences. These descriptive differences have no declared semantic pass/fail threshold.

Inspect overlaps, defining features, intensity, harm, and stability together. High overlap can coexist with shifted characteristics; low ARI can reflect local splits/merges under forced global k rather than entirely new meanings. k=2–10 reference fits are exploratory; only matched B4/E8 have been stability-tested in this run. No alternative local k is declared a supported winner merely because it matches the global partition or has a low inertia.
'''), code(chunks['Semantic correspondence of matched-resolution regional fits']), code('''
local_profiles = pd.read_csv(OUTPUT/'regional_original_profiles.csv')
local_overlaps = pd.read_csv(OUTPUT/'regional_overlaps.csv')
semantic_correspondence = matched_regional_semantics(local_profiles, fixed_original_profiles, local_overlaps, OUTPUT)
display(semantic_correspondence.sort_values('dominant_global_fraction').head(12))
display(semantic_correspondence.sort_values('mean_original_feature_TV',ascending=False).head(12))
display(regional_summary.groupby('candidate').agg(successful_references=('status',lambda s:int(s.eq('ok').sum()))))
# Illustrative local profiles: a low-B-agreement region and a high-E-agreement region.
plot_regional_profile(13, 'B', 4)
plot_regional_profile(7, 'E', 8)
''')]
insert_at=next(i for i,c in enumerate(cells) if c.cell_type=='markdown' and c.source.startswith('## 9 Development decision'))
cells[insert_at:insert_at]=regional_semantics_cells

# Explicit objective and output for every group, plus a role comment on every code cell.
objectives = {
 '## 1 ': ('Declare the unchanged B/E candidates, Moodle-compatible sampling rules, and execution boundary.', 'Specifications, seeds, and run switches; no held-out data access.'),
 '## 2 ': ('Implement the exact Week 4 feature geometry and correct equal-country weights.', 'Transformation and weighting helpers with validation checks; no model fitting.'),
 '## 3 ': ('Verify development-only inputs and exact replay of the saved global models.', 'Country/region retention audits, fingerprints, and exact B/E label-reload verification.'),
 '## 4 ': ('Define the membership and original-response measures used for regional comparisons.', 'ARI/overlap, structural, and categorical-profile functions; definitions alone do not generate results.'),
 '## 4a ': ('Describe fixed-global B/E profile prevalence at global, regional, and country levels.', 'Counts, respondent shares, weighted shares, and original-response distributions in tables and saved files.'),
 '## 4b ': ('Explain substantive geographical contrasts without causal or transfer claims.', 'Interpretation tied to saved cluster IDs, plus semantic, sample-selection, and small-region cautions.'),
 '## 4c ': ('Assess how well fixed centres represent respondents in each area.', 'Distances, margins, provisional development thresholds, exceedances, and original-response differences.'),
 '## 4d ': ('Visualize fixed-global profile prevalence without conflating missing data with zero.', 'B/E prevalence maps, country-key checks, and cartographic provenance.'),
 '## 5 ': ('Construct and audit regional resampling from country metadata before fitting.', 'Exact respondent/country samples, distinct-subset counts, omissions, and small-region limitations.'),
 '## 6 ': ('Recover local structure under fixed representations and a bounded k search.', '270 cached reference fits and local/global overlap, ARI, structural, and profile tables.'),
 '## 7 ': ('Measure respondent and country sensitivity of the matched B4/E8 regional fits.', '50-fit or LOO summaries, all failures, and dependent pairwise ARIs; unsupported tests remain unavailable.'),
 '## 8 ': ('Inspect the substantive patterns behind numerical local/global agreement.', 'Matched-resolution comparison table and a reusable original-unit plotting function.'),
 '## 8a ': ('Examine local/global semantic correspondence and delimit the exploratory k search.', 'Overlap-associated profile comparisons, original-unit TV differences, and illustrative regional profiles.'),
 '## 9 ': ('Record readiness for a later final decision without freezing models or opening the holdout.', 'Checklist distinguishing computed evidence from unapproved final scope and held-out access.'),
}
current_objective='Initialize notebook definitions.'
for cell in cells:
    if cell.cell_type=='markdown' and cell.source.startswith('## '):
        matched=next((values for prefix,values in objectives.items() if cell.source.startswith(prefix)),None)
        if matched:
            current_objective,output=matched
            lines=cell.source.split('\n',1)
            cell.source=lines[0]+'\n\n**Objective:** '+current_objective+'\n\n**Output:** '+output+'\n'+lines[1]
    elif cell.cell_type=='code':
        cell.source='# Objective: '+current_objective+'\n'+cell.source

conclusions_path=ROOT/'.week05_build/points12_conclusions.txt'
if conclusions_path.exists():
    cells.append(md(conclusions_path.read_text()))
notebook = nbformat.v4.new_notebook(cells=cells)
notebook.metadata = {'kernelspec': {'display_name':'Python 3 (tf-metal311)', 'language':'python', 'name':'tf-metal'},
                     'language_info':{'name':'python','version':'3.11'},
                     'week05':{'implementation_sha256':hashlib.sha256(source.encode()).hexdigest(),
                               'heldout_responses_used':False, 'stage':'development regional validation'}}
target = ROOT / 'weekly_notebooks/week05_regional_validation_and_objective1_finalization_v3.ipynb'
if target.exists():
    raise FileExistsError('Preserve existing notebook; choose a new version before rebuilding.')
nbformat.validate(notebook)
nbformat.write(notebook, target)
print(target)
