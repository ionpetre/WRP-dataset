from pathlib import Path
import hashlib
import json
import nbformat

root = Path(__file__).resolve().parent.parent
info = json.loads((root/'.week05_build/local_selection_run.json').read_text())
base = root/info['base_output_directory']
output = root/info['output_directory']
assert (output/'local_selection_complete.json').exists()
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
evidence = {'base_context': json.loads((base/'run_manifest.json').read_text())['context'],
            'selection_context': info['selection_context'], 'base_files': {}, 'selection_files': {}}
for folder, key in [(base, 'base_files'), (output, 'selection_files')]:
    for path in sorted(folder.glob('*.csv')):
        evidence[key][path.name] = sha(path)
    for name in ['run_manifest.json', 'selection_manifest.json', 'local_selection_complete.json', 'points12_computation_complete.json']:
        if (folder/name).exists(): evidence[key][name] = sha(folder/name)
(output/'evidence_manifest.json').write_text(json.dumps(evidence, indent=2, sort_keys=True))

source = root/'weekly_notebooks/week05_regional_validation_and_objective1_finalization_v3.ipynb'
destination = root/'weekly_notebooks/week05_regional_validation_and_objective1_finalization_v4.ipynb'
notebook = nbformat.read(source, as_version=4)
notebook.cells[0].source = '''# Week 5 Global profile distributions and supported local resolutions — v4

**Objective:** describe the fixed global B/E profiles geographically, then ask which independently refitted regional resolutions are supported by development-only stability evidence.

**Output:** fixed-global prevalence and maps; local k=2–10 reference diagnostics; a bounded local-resolution shortlist; full and limited stability results; original-response interpretations; cluster-recovery and split/merge comparisons; article/slide-ready figures and explicit limitations.

This version extends v3; **v1–v3 are preserved**. Sections 1–10 replay saved baseline results without refitting or overwriting their tables. Sections 11–16 document the additional regional resolution analysis. The saved global B4/E8 centres and assignments remain unchanged. B and E below denote their fixed **geometries**, not an instruction to force local k=4 or k=8. All results use 109,488 complete-case respondents in 113 development countries. The 29 held-out countries remain unopened; no final profile specification is frozen.

This is a research record, not a claim that every region has one objectively optimal k. Every tested resolution is reported, including unsuccessful stability checks. Article conclusions must distinguish exploratory selection, partition-level stability, recovery of each profile, semantic meaning, and eventual held-out transfer.'''
notebook.cells[3].source = notebook.cells[3].source.replace('RUN_REGIONAL_REFERENCES = True', 'RUN_REGIONAL_REFERENCES = False').replace('RUN_REGIONAL_STABILITY = True', 'RUN_REGIONAL_STABILITY = False')
notebook.cells[3].source += "\nprint('v4: read-only baseline replay; saved regional tests are loaded even though refitting switches are off.')"
notebook.cells[1].source += '\n\n**v4 execution rule:** baseline fit switches are off. Saved evidence is loaded and checked, not regenerated. The explicit additional-fit resume switch in section 12 is also off by default.'
notebook.cells[7].source = '''# Objective: Verify development-only inputs and global label replay, then read the preserved baseline.
data, country_audit, regions, global_references, provenance = prepare_development(ROOT)
CONTEXT = digest_json({'provenance': provenance, 'design': REGIONAL_DESIGN,
                       'implementation_sha256': IMPLEMENTATION_SHA256})
OUTPUT = ROOT / 'course_artifacts/week05_regional_validation_v3' / CONTEXT[:16]
baseline_manifest = json.loads((OUTPUT/'run_manifest.json').read_text())
assert baseline_manifest['context'] == CONTEXT
assert baseline_manifest['provenance'] == provenance
assert baseline_manifest['regional_design'] == REGIONAL_DESIGN
assert baseline_manifest['heldout_responses_used'] is False
print('Verified:', len(data), 'complete respondents;', data.COUNTRY_ISO3.nunique(), 'development countries.')
print('Global B/E labels reproduce exactly. No global or regional refit; no baseline table overwrite.')
display(regions)
display(previous_stability(ROOT)[['candidate','experiment','median_pairwise','p10_pairwise']])'''
notebook.cells[12].source = notebook.cells[12].source.replace('fixed_prevalence, fixed_original_profiles, fixed_semantic_differences = fixed_global_geographical_results(\n    data, global_references, regions, OUTPUT)', '''fixed_prevalence = pd.read_csv(OUTPUT/'fixed_global_profile_prevalence.csv')
fixed_original_profiles = pd.read_csv(OUTPUT/'fixed_global_original_profiles_by_region.csv')
fixed_semantic_differences = pd.read_csv(OUTPUT/'fixed_global_regional_semantic_differences.csv')''').replace("print('Saved global", "print('Loaded preserved global")
notebook.cells[16].source = notebook.cells[16].source.replace('quality_summary, provisional_distance_thresholds = fixed_assignment_quality(data, global_references, regions, OUTPUT)', '''quality_summary = pd.read_csv(OUTPUT/'fixed_global_assignment_quality.csv')
provisional_distance_thresholds = pd.read_csv(OUTPUT/'development_distance_thresholds_provisional.csv')''')
notebook.cells[19].source = '''# Objective: Display preserved fixed-global prevalence maps; no model or geographical redesign.
from IPython.display import Image
for name in SPECIFICATIONS:
    display(Image(filename=str(OUTPUT/'figures'/f'{name}_fixed_global_prevalence_maps.png')))'''
notebook.cells[22].source = '''# Objective: Read preserved country-sampling and omission audits, without rewriting plans.
sampling_audit = pd.read_csv(OUTPUT/'regional_sampling_design_audit.csv')
display(sampling_audit[['region_name','countries','complete_respondents','country_diagnostic_y',
                       'distinct_country_fits','possible_80pct_subsets']].rename(columns={'country_diagnostic_y':'country_test'}))'''
notebook.cells[26].source = '''# Objective: Read all 270 successful regional reference diagnostics, not refit them.
regional_summary = pd.read_csv(OUTPUT/'regional_reference_summary.csv')
assert len(regional_summary) == 270 and regional_summary.status.eq('ok').all()
regional_fitted = {}  # Only needed for new fits; selected cached references are loaded in section 12.
display(regional_summary.loc[regional_summary.matched_global_resolution])'''
notebook.cells[28].source = '''# Objective: Read the initial matched B4/E8 regional stability results; section 12 extends this set.
REGIONAL_STABILITY_SHORTLIST = [(int(region), name, spec.global_k)
    for region in sorted(data.GlobalRegion.unique()) for name, spec in SPECIFICATIONS.items()]
stability_summary = pd.read_csv(OUTPUT/'regional_stability_summary.csv')
assert len(stability_summary) == 60
display(stability_summary)'''
notebook.cells[33].source = notebook.cells[33].source.replace('semantic_correspondence = matched_regional_semantics(local_profiles, fixed_original_profiles, local_overlaps, OUTPUT)', "semantic_correspondence = pd.read_csv(OUTPUT/'matched_regional_semantic_correspondence.csv')")
notebook.cells[36].source = '''# Objective: Read the baseline freeze-preparation checklist, not freeze a model.
checklist = pd.read_csv(OUTPUT/'freeze_preparation_checklist.csv')
display(checklist)
display(Markdown('The matched-resolution stage is complete. Sections 11–16 extend the local search. '
                '**No final freeze and no held-out response access.**'))'''
notebook.cells[31].source = notebook.cells[31].source.replace('only matched B4/E8 have been stability-tested in this run', 'only matched B4/E8 had been stability-tested at the initial v3 stage; sections 11–16 now extend those tests')
notebook.cells[37].source = notebook.cells[37].source.replace('## 10 Results and conclusions for agenda points 1 and 2', '## 10 Initial matched-resolution conclusions (v3 evidence, retained for context)')
notebook.cells[37].source = notebook.cells[37].source.replace('E is closer to its global partition in every region in this particular reference run.', 'E is closer to its global partition in 14 of 15 regions in this particular reference run; Latin America/Caribbean is the exception (B 0.733, E 0.729).')
notebook.cells[37].source = notebook.cells[37].source.replace('No alternative local k, new geographic grouping, or country clustering is promoted by this notebook.', 'At this initial stage no alternative local k had been stability-qualified. The new local-resolution evidence in sections 11–16 supersedes that scope limitation; no new geographic grouping or country clustering is introduced.')
notebook.cells[37].source += '\n\n**v4 update:** the negative matched-resolution results must not be read as absence of local structure. The bounded additional-k tests below support several alternative local resolutions. The cluster-recovery audit also qualifies the earlier description of Northern/Western Europe E8 as stable: the whole partition is stable, but not every smaller reference profile is recovered equally well.'

def md(text): notebook.cells.append(nbformat.v4.new_markdown_cell(text))
def code(text): notebook.cells.append(nbformat.v4.new_code_cell(text))

md(r'''## 11 Why extend the local k search?

**Objective:** separate “does the global resolution recur locally?” from “which local resolutions are supported?”

**Output:** a bounded, reproducible development-only selection rule, independent of local/global ARI.

Forcing B4 and E8 was a controlled comparison, not a local optimization procedure. A region may support fewer or different distinctions than the pooled development data. A failed B4/E8 local stability test therefore does not imply that no repeatable local structure exists.

We keep the algorithm, complete-case cohort, equal-country weights and two Week 4 geometries unchanged. B uses 0/1/2 worry coding and worry budget \(\alpha=0.5\); E uses 0/1/3 and \(\alpha=0.75\). The six normalized worry deviations and the saved overall-worry coordinate use \(\sqrt{\alpha/6}\); the fourteen separate personal/known-person harm indicators use \(\sqrt{(1-\alpha)/14}\). Section 2 gives the exact transformation. No additional imputation, standardization or PCA is introduced. Thus B/E comparisons also change coding and geometry, not just k.

For every region and geometry we already have references for k=2,…,10. We now stability-test at most three additional k: **2, 3, and one near the within-region inertia elbow**, excluding the previously tested matched k. Normalize k to \(x=(k-2)/8\), inertia to \(z=(I_k-I_{10})/(I_2-I_{10})\), and use gap \(g=(1-x)-z\). Among eligible nonmatched k=3,…,9, choose the smallest k whose gap is at least 95% of the maximum gap. This coarsest-near-tie rule avoids claiming a precise elbow. In this run the extra B values are 2/3/5 everywhere; E uses 2/3/4 in Eastern Africa, Northern Africa and Central Asia, and 2/3/5 elsewhere.

Original response distributions and smallest-group sizes are inspected before the new stability stage, but no undocumented semantic pass/fail threshold is used. All selected alternatives are tested, including unpromising ones. **Global ARI is never used to choose or retain k.** The global structural screen (k≥3, largest share≤40%, D<3) remains a reported benchmark, not a local filter: imposing it would exclude all two-group regional descriptions by construction.

This extension was planned **after seeing the matched-resolution results**. It is an exploratory, adaptive development analysis, not an independently preregistered confirmation. The bounded shortlist is a computational compromise: untested k have unknown stability. Neither minimum inertia nor the elbow identifies a uniquely “true” or “optimal” k. We retain sets of benchmark-qualified resolutions, not one winner per region.''')
extension = (root/'.week05_build/local_resolution.py').read_text().replace('from week05_core import *  # Removed when embedded in the self-contained notebook.\n', '')
code('# Objective: Implement the recorded local-k selection and fingerprint-checked cache/recovery helpers.\n'+extension)
md('''## 12 Replay the additional tests and distinguish evidence levels

**Objective:** verify provenance and recover the completed regional tests without duplicate fitting.

**Output:** shortlist, all 120 tested resolutions, successful/failed fit counts, dependent pairwise-ARI summaries and cluster-recovery diagnostics.

The existing samples and fitting settings are reused for each new k: 20 initializations, maximum 300 iterations, 50 within-country 80% respondent subsamples without replacement; for regions with at least five countries, 50 samples of floor(0.8N) whole countries. Training weights are recomputed so included countries have equal total influence. Each fitted model assigns the **entire same regional cohort** by nearest centre, including omitted respondents/countries. These are partition sensitivity tests, not independent out-of-sample prediction-accuracy estimates. Data changes and randomized K-means initializations both vary; neither effect is isolated here.

Both tests require all 50 fits to succeed and **median AND lower-decile pairwise ARI≥0.80**, using unrounded values. Fifty fits generate 1,225 pairwise ARIs; those comparisons are dependent, not 1,225 independent validations. The standard ARI is unweighted even though fitting is equal-country weighted. For 2–4 countries we report all leave-one-country-out fits as limited diagnostics, not full 50-fit country evidence. For one country, geographic stability is unavailable. Repeated country subsets and the actual retained-country fractions remain visible in the sampling audit.

The resume switch is off. Turning it on is only appropriate after verifying that no fitting process is already running; successful fingerprint-checked fits are then reused. Fit failures would remain recorded rather than silently retried. The completed run has **zero model-fitting failures**. An initial preflight attempt stopped because it expected an optional implementation-hash key absent from the replayed v3 manifest; no fits ran in that attempt. Provenance verification was corrected to recompute the context from data/runtime, design and the actual baseline implementation hash. This was an orchestration/schema mismatch, not a failed clustering result.''')
code(f'''# Objective: Verify saved evidence and load completed tests; no duplicate fits by default.
LOCAL_OUTPUT = ROOT / {info['output_directory']!r}
LOCAL_SELECTION_CONTEXT = {info['selection_context']!r}
RESUME_ADDITIONAL_FITS = False
selection_manifest = json.loads((LOCAL_OUTPUT/'selection_manifest.json').read_text())
assert selection_manifest['base_context'] == CONTEXT
assert selection_manifest['selection_context'] == LOCAL_SELECTION_CONTEXT
assert selection_manifest['selection_design'] == LOCAL_SELECTION_DESIGN
assert selection_manifest['heldout_responses_used'] is False
evidence_manifest = json.loads((LOCAL_OUTPUT/'evidence_manifest.json').read_text())
assert evidence_manifest['selection_context'] == LOCAL_SELECTION_CONTEXT
for folder, key in [(OUTPUT, 'base_files'), (LOCAL_OUTPUT, 'selection_files')]:
    for filename, expected_hash in evidence_manifest[key].items():
        assert file_sha256(folder/filename) == expected_hash, 'Saved evidence changed: ' + filename
decisions, local_diagnostics = select_local_resolutions(regional_summary, local_profiles)
expected_shortlist = pd.read_csv(LOCAL_OUTPUT/'additional_local_shortlist.csv')
pd.testing.assert_frame_equal(decisions[['region','candidate','k']].reset_index(drop=True),
                              expected_shortlist[['region','candidate','k']].reset_index(drop=True))
calculated_context = digest_json({{'base_context': CONTEXT, 'selection_design': LOCAL_SELECTION_DESIGN,
    'shortlist': decisions[['region','candidate','k']].to_dict('records'),
    'extension_code_sha256': selection_manifest['extension_code_sha256']}})
assert calculated_context == LOCAL_SELECTION_CONTEXT
tested = sorted(set(list(decisions[['region','candidate','k']].itertuples(index=False,name=None))
                    + REGIONAL_STABILITY_SHORTLIST))
local_fitted = {{}}
for region, name, k in tested:
    frame = data.loc[data.GlobalRegion.eq(region)].reset_index(drop=True)
    local_fitted[(region,name,k)] = reference_cache(frame,region,name,k,OUTPUT/'fits',CONTEXT)
if RESUME_ADDITIONAL_FITS:
    additional = regional_stability(data,local_fitted,
        list(decisions[['region','candidate','k']].itertuples(index=False,name=None)),
        REGIONAL_DESIGN,LOCAL_OUTPUT,CONTEXT,n_jobs=2)
    combined_stability = pd.concat([stability_summary,additional],ignore_index=True)
    cluster_recovery = cluster_recovery_summary(data,tested,local_fitted,OUTPUT/'fits',CONTEXT,LOCAL_OUTPUT)
    supported = supported_resolution_summary(data,regions,combined_stability,cluster_recovery,regional_summary,LOCAL_OUTPUT)
else:
    combined_stability = pd.read_csv(LOCAL_OUTPUT/'combined_regional_stability_summary.csv')
    cluster_recovery = pd.read_csv(LOCAL_OUTPUT/'cluster_recovery_summary.csv')
    supported = pd.read_csv(LOCAL_OUTPUT/'supported_local_resolutions.csv')
assert len(supported) == 120 and len(combined_stability) == 240
assert not supported.duplicated(['region','candidate','k']).any()
completion = json.loads((LOCAL_OUTPUT/'local_selection_complete.json').read_text())
display(completion)
display(supported.groupby('status').size().rename('tested_resolutions').to_frame())
display(supported.loc[supported.status.eq('both full stability benchmarks met'),
    ['region_name','candidate','k','respondent_median_ari','respondent_p10_ari',
     'country_median_ari','country_p10_ari','largest_share','global_structural_benchmark_pass']].round(4))
print('All 270 reference fits and 10,456 matched/additional stability fits succeeded. No held-out responses used.')''')
md(r'''## 13 Partition stability is not recovery of every profile

**Objective:** prevent large, repeatable groups from hiding fragile smaller groups or a poor saved reference.

**Output:** per-cluster weighted reference Jaccard, original-category distributions and contrasts, counts, weighted sample-size diagnostics, and local/global semantic associations for **every benchmark-qualified resolution**.

For each repeated fit, match its k clusters to the k reference clusters by maximizing total **equal-country-weighted overlap** (Hungarian assignment). Then compute \(J(A,B)=w(A\cap B)/w(A\cup B)\) for each matched reference cluster. Summarize its median and lower decile across fits. This is a one-to-one recovery diagnostic, not a new retention threshold; matching maximizes total overlap, not every cluster's Jaccard. Splits/merges can therefore leave an individual group poorly matched. Whole-partition ARI and individual-cluster Jaccard answer different questions and use different weighting.

Describe profiles using the **original three worry categories** and separate binary personal/known-person harm, not transformed centroids alone. For each local cluster save its share, respondent count, countries represented, strongest original-unit contrasts, and descriptive Kish weighted n. Kish n measures weight concentration; it is not a survey-design-adjusted effective sample size or confidence interval.

Associate a local cluster with its largest global overlap without forcing equal k or one-to-one global names. Report that overlap and mean feature-wise total variation from both the pooled global profile and that fixed profile **within the same region**. The latter helps distinguish general regional response differences from local regrouping. TV ignores dependence between features and has no semantic pass/fail threshold here. A near-pure-category flag (≥98% in a category and ≥50 percentage-point excess versus outside) identifies a possible single-feature anchor; it is **not** a cross-validated single-feature reconstruction test. These are descriptive interpretations, not validated social types.''')
documentation = (root/'.week05_build/local_resolution_documentation.py').read_text()
code('# Objective: Define reporting-only tables and figures; do not change selection or fit models.\n'+documentation)
code('''# Objective: Save interpretable evidence for every qualified local resolution, not only illustrative winners.
support_table = local_support_table(supported, regions, LOCAL_OUTPUT)
profile_interpretations = qualified_local_semantics(data,supported,local_profiles,local_overlaps,
    fixed_original_profiles,local_fitted,LOCAL_OUTPUT)
resolution_comparisons = compare_supported_local_resolutions(data,supported,local_fitted,LOCAL_OUTPUT)
display(support_table[['region_name','countries','B_full','E_full','B_limited_LOO','E_limited_LOO',
                      'B_respondent_only','E_respondent_only']])
display(profile_interpretations[['region_name','candidate','k','cluster','cluster_share',
    'respondents','original_response_anchors','largest_overlap_global_cluster','largest_overlap_fraction']])
display(supported.loc[supported.status.ne('not qualified by the applicable stability benchmarks'),
    ['region_name','candidate','k','status','worst_cluster_respondent_p10_jaccard',
     'worst_cluster_country_p10_jaccard']].round(3))
display(resolution_comparisons.round(3))''')
md('''## 14 Visual evidence for slides and the article

**Objective:** show the tested search space and original-response meanings without hiding unavailable or unsuccessful tests.

**Output:** B/E stability grids and illustrative original-unit profile panels, saved as PNGs and embedded below.

The grids show lower-decile ARI; both median and lower decile determine the outlined qualification status. Grey blank cells are untested k, not failures; N/A is an unavailable country test. Rounded labels must not be used for decisions. The selected original-unit examples illustrate African B3, European B2/E8 and Central Asian E3 when qualified; they are not a ranked best-of selection. Complete tables cover every qualified resolution. Each panel uses one 0–100% scale and distinguishes personal from known-person harm. The earlier country maps continue to use fixed global labels: no map pretends that unrelated local IDs have common cross-region meanings.''')
code('''# Objective: Save and embed stable-resolution evidence and original-unit examples, without further fits.
stability_figures = plot_report_stability(supported,regions,LOCAL_OUTPUT)
local_profile_figures = plot_qualified_local_profiles(local_profiles,supported,regions,LOCAL_OUTPUT)
for path in stability_figures + local_profile_figures:
    display(Image(filename=str(path)))''')
md('''## 15 Updated analytical conclusions

**Objective:** state what the additional tests establish, what changes relative to v3, and what remains unproven.

**Output:** a bounded scientific interpretation suitable for adaptation into slides and an article.

### Coarser local descriptions recover structure that matched B4/E8 missed

Of **120 tested regional resolutions**, **14 meet both full partition-stability benchmarks**, across **six regions**. Thirteen are newly tested alternatives; Northern/Western Europe E8 was already qualified. The sets are:

| Development region | B geometry, supported k | E geometry, supported k |
|---|---:|---:|
| Eastern Africa | 2 | 2 |
| Central/Western Africa | 3 | 2 |
| Latin America/Caribbean | 3, 5 | none tested qualified |
| Central Asia | 2, 3 | 2, 3 |
| Southeastern Asia | none tested qualified | 5 |
| Northern/Western Europe | 2 | 2, 8 |

These are **sets**, not unique optima. The other seven multicountry regions have no full-benchmark-qualified tested resolution; this does not prove an absence of structure. Northern Africa E8 additionally meets the respondent benchmark and four-fit LOO numerical benchmark, which is weaker geographic evidence. The US-only E8 and New Zealand-only B3/E3 meet respondent benchmarks but cannot establish regional country stability. Of the 120 tested resolutions, 102 fail at least one applicable benchmark; there are no computational fitting failures. All 270 references and 10,456 matched/additional stability fits succeeded.

The Eastern Africa B2 country lower decile is **0.800272**: it barely meets the fixed 0.80 benchmark. Report it as borderline evidence, not a robust margin above the threshold. Latin America B3 and B5 both qualify; their cross-k overlaps show whether the finer description approximately splits the coarser groups. Separate K-means optima are not guaranteed to be nested, so this is not a strict hierarchy.

### Stability does not automatically establish a multidimensional sociological type

For Central/Western Africa B3, respondent median/lower-decile ARI is **0.959/0.933** and country **0.908/0.868**. It is stronger reproducibility evidence than the failed B4 result. Its substantive meaning still depends on the original-unit profiles below, not its ARI alone.

The regional interpretations are provisional descriptions of observed response patterns, not final names or explanations of their causes:

| Region | Original-response interpretation of the qualified local resolutions |
|---|---|
| Eastern Africa | B2 separates broad known-person harm exposure (36.0%) from lower exposure (64.0%). E2 instead contrasts food/water worry (58.6%) with traffic/severe-weather worry (41.4%). The different content is consistent with the different feature budgets; these are not interchangeable solutions. |
| Central/Western Africa | B3 has a broad harm-exposure group (24.7%), a lower-harm group with food/water concern (41.3%), and a traffic/weather/crime-concern group with low food/water worry (34.0%). E2 primarily contrasts food/water concern (56.9%) with traffic concern and lower food/water worry (43.1%). This is a repeatable, multidomain pattern, not merely agreement with the global labels. |
| Latin America/Caribbean | B3 distinguishes known-person harm exposure (20.0%), lower traffic/weather worry and harm (43.2%), and traffic-oriented concern with low food/water worry (36.7%). B5 adds distinct crime-oriented, mental-health/traffic-oriented, low-crime-worry, broad-harm, and food/water-oriented groups. B5 is not simply B3 with two exact splits: fine-to-coarse weighted purity is 82.8%, leaving 17.2% outside each finer group's dominant coarse association. Both resolutions qualify, so neither is labelled uniquely optimal. |
| Central Asia | B2 almost isolates known-person traffic harm (27.4%; 97.7% report it). B3 retains a similar harm group and divides the rest mainly by traffic/weather worry. E2 is an exact very-worried-traffic contrast (34.3% versus the remainder); E3 isolates near-pure very-worried-water (16.2%) and very-worried-traffic (23.9%) groups plus a lower-worry remainder (59.9%). These strong single-category anchors warrant caution despite excellent ARIs. Fifty country fits here cover only five distinct omitted-country subsets. |
| Southeastern Asia | E5 contains a lower-worry group (37.7%), a food/water-oriented group (14.3%), a traffic-oriented group (14.3%), a mental-health/crime/weather group (16.8%), and a crime/weather-oriented group (16.8%). The traffic group has the weakest reference recovery, so its boundaries need more caution than the whole-partition qualification suggests. |
| Northern/Western Europe | B2 mostly distinguishes known-person mental-health harm; E2 mostly distinguishes very-worried severe weather. E8 adds domain-specific food/water/traffic/weather/mental-health/crime worry groups alongside the two large low-worry groups differentiated by known-person mental-health harm. The large groups are highly repeatable; several smaller groups are less secure. |

The percentages above use the equal-country weights within each region. They are not population shares. The full original-category tables distinguish no/somewhat/very worry and personal/known-person harm for every group; the brief descriptions deliberately do not turn a dominant marginal feature into a causal interpretation.

Northern/Western Europe B2 is almost a division by **known-person mental-health harm**: one group is 31.9% of regional weight with 99.3% reporting it; the other is 68.1% with 0%. E2 instead separates a 18.4% group with 100% very-worried severe weather from the remainder. Both are highly repeatable under their geometries, but these simple categorical contrasts should not be advertised as newly discovered multidimensional social types. Different B/E groupings reflect both observed responses and our different coding/feature budgets. Categorical features can generate sharp, repeatable boundaries.

### High whole-partition ARI can hide weaker smaller profiles

Northern/Western Europe E8 still passes both full ARI benchmarks. Yet its weakest reference-cluster lower-decile Jaccard is **0.644** under respondent sampling and **0.594** under country sampling. The large low-worry/harm split is very repeatable, whereas some smaller thematic groups are less secure. Its eight-profile reference should therefore be described as partition-stable **with uneven individual-profile recovery**, not uniformly stable at every profile.

Southeastern Asia E5 also qualifies globally by ARI but has weakest-cluster lower-decile Jaccard **0.765/0.734**. Northern Africa E8 has still weaker recovery (approximately **0.149/0.148**) despite meeting the respondent and limited LOO ARI benchmarks. For the US-only E8, repeated fits agree well with each other (respondent pairwise median/lower decile **0.919/0.876**) but less with the saved reference (**0.660/0.643**); one reference cluster's matched lower-decile Jaccard is zero. This is evidence against interpreting that saved reference as a reliable eight-profile local description. It is not a numerical crash. Before freezing any such local model, investigate reference/initialization dependence and the affected clusters; no extra fits or post-hoc retention rule are introduced here.

### Global and local models answer different questions

The global B/E profiles provide a common classification for country/region comparisons, while local fits examine which distinctions can be recovered within an area. Low local/global ARI is not in itself weakness or a significant scientific discovery: different resolutions, local feature prevalence and optimization can produce it. The potentially valuable finding is a **repeatable, interpretable difference** supported by overlaps, original-category contrasts and cluster recovery. Global-profile frequencies and within-profile semantics also vary, as documented in sections 4–10. Neither analysis proves universal profiles or successful transfer to unseen countries.

For later country-distance analysis, retain a common global-profile basis, separately for B and E. Local profile coordinates cannot be compared directly across countries or regions without handling semantic alignment and splits/merges. No new regional classification or country clustering is performed here.

### Limits that belong in the article, not only in technical notes

The search is bounded, exploratory and adaptively extended. Threshold crossing is not a p-value, confidence level or guarantee of a true k. Reusing sampling plans helps compare resolutions but does not create independent evidence. With only five countries, 50 country fits cover just five distinct omissions; small-region LOO and one-country rows are weaker still. K-means samples include training respondents when comparing predicted partitions, so this is not held-out transfer validation. The regional complete-case cohort can be selective, equal-country weights define a country-balanced rather than population-proportional estimand, and ARI itself is unweighted. Original-category summaries describe marginals, not causal mechanisms, full joint distributions or validated latent social types. Borderline ARIs, minority-profile fragility and reference dependence must accompany positive findings.''')
md('''## 16 Evidence files, reproducibility and remaining Week 5 work

**Objective:** make results reusable while keeping exploratory analysis separate from final validation.

**Output:** a saved evidence inventory and a clear completion boundary.

Sections 1–10 preserve the global/regional/country prevalence, semantics, assignment-quality tables, maps, and matched-resolution evidence. The extension directory contains the exact selection design and shortlist, all-k reference diagnostics, all tested stability summaries and pairwise ARIs, sampling audits, per-cluster recovery, qualified original-category distributions and interpretations, supported-k sets, cross-k overlaps, figures, and an input-evidence hash manifest. No selected failure or inconvenient result is omitted. Intermediate fits are shared via a link to the fingerprinted baseline cache; copies of these results must preserve that cache or its relative folder structure.

**Still required before Objective 1 is concluded:** decide the scope of the final global profile specification(s); freeze the complete preprocessing/assignment procedure and interpretation; conduct the remaining approved country-block validation where required by the protocol; only then apply and assess the untouched held-out-country responses. Regional resampling is not a substitute for those held-out tests. Regional/local profiles remain exploratory contextual evidence, not silently substituted global finalists. Optional country-similarity analysis is a separate question, not a condition for freezing profiles. The notebook makes no final freeze or held-out validation claim.''')
code('''# Objective: Save the article/slide evidence inventory and certify only the computations actually completed.
report_files = sorted(p.name for p in LOCAL_OUTPUT.glob('*.csv'))
report_inventory = {
    'base_context': CONTEXT, 'selection_context': LOCAL_SELECTION_CONTEXT,
    'development_respondents': len(data), 'development_countries': int(data.COUNTRY_ISO3.nunique()),
    'reference_fits': 270, 'stability_fits': int(combined_stability.successful_fits.sum()),
    'failed_stability_fits': int(combined_stability.failed_fits.sum()),
    'tested_resolutions': len(supported), 'qualified_full_partition_benchmarks': int(supported.status.eq(FULL_SUPPORT).sum()),
    'qualified_full_regions': int(supported.loc[supported.status.eq(FULL_SUPPORT),'region'].nunique()),
    'heldout_responses_used': False, 'final_specification_frozen': False,
    'reference_fit_implementation_sha256': IMPLEMENTATION_SHA256,
    'selection_code_sha256': selection_manifest['extension_code_sha256'],
    'tables': {name: file_sha256(LOCAL_OUTPUT/name) for name in report_files},
    'figures': {str(p.relative_to(LOCAL_OUTPUT)): file_sha256(p) for p in stability_figures+local_profile_figures},
    'notebook': 'week05_regional_validation_and_objective1_finalization_v4.ipynb',
    'interpretation': 'exploratory development evidence; partition qualification is not uniform profile recovery or optimal k'}
assert report_inventory['stability_fits'] == 10456
assert report_inventory['failed_stability_fits'] == 0
atomic_json(report_inventory,LOCAL_OUTPUT/'article_slide_evidence_inventory.json')
display(report_inventory)
print('Completed analysis saved. Earlier versions preserved. No held-out responses opened; no final model frozen.')''')
nbformat.write(notebook, destination)
print(destination)
print('Cells:', len(notebook.cells))
