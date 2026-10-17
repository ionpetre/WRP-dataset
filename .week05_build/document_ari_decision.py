"""Preserve v4 and extend its research record with the approved unchanged ARI decision."""
from pathlib import Path
import nbformat

root = Path(__file__).resolve().parent.parent
source = root/'weekly_notebooks/week05_regional_validation_and_objective1_finalization_v4.ipynb'
destination = root/'weekly_notebooks/week05_regional_validation_and_objective1_finalization_v5.ipynb'
notebook = nbformat.read(source, as_version=4)
notebook.cells[0].source = notebook.cells[0].source.replace('— v4', '— v5').replace('**v1–v3 are preserved**', '**v1–v4 are preserved**').replace('Sections 11–16 document', 'Sections 11–17 document')
notebook.cells[0].source += '\n\n**Decision recorded on 12 October 2026:** retain the 0.80 ARI criterion unchanged. Sections 15a–15b document the k=2 concern, threshold sensitivity and sample-size/country-composition discussion; section 17 states the next pre-holdout step. No new model fits, final freeze or held-out response access are introduced.'
notebook.cells[3].source = notebook.cells[3].source.replace('v4: read-only', 'v5: read-only')
notebook.cells[1].source = notebook.cells[1].source.replace('**v4 execution rule:**', '**v5 execution rule:**')
notebook.cells[48].source = notebook.cells[48].source.replace('freeze the complete preprocessing/assignment procedure and interpretation; conduct the remaining approved country-block validation where required by the protocol; only then apply and assess', 'freeze the complete preprocessing/assignment procedure, development reference diagnostics and interpretation; only then apply and assess')
notebook.cells[48].source += '\n\n**Protocol clarification:** the 7 October validation protocol and the current Moodle description specify regional development analysis → final development decision/freeze → held-out assignment/transfer assessment. They do not impose a new repeated two-half Prediction Strength experiment as a prerequisite here. Earlier course descriptions or old search handoffs must not silently add that requirement back into this plan.'
notebook.cells[49].source = notebook.cells[49].source.replace('week05_regional_validation_and_objective1_finalization_v4.ipynb', 'week05_regional_validation_and_objective1_finalization_v5.ipynb').replace("'article_slide_evidence_inventory.json'", "'article_slide_evidence_inventory_v5.json'")
notebook.cells[49].source = notebook.cells[49].source.replace("'heldout_responses_used': False, 'final_specification_frozen': False,", "'heldout_responses_used': False, 'final_specification_frozen': False,\n    'unchanged_ari_decision': threshold_decision,\n    'discussion_evidence': {str(p.relative_to(LOCAL_OUTPUT)): file_sha256(p) for p in sorted(DISCUSSION_OUTPUT.glob('*')) if p.is_file()},")

decision_md = nbformat.v4.new_markdown_cell('''## 15a Research decision: retain ARI 0.80 and distinguish stability from useful profiles

**Objective:** record the discussion and the user's decision without changing the scientific design.

**Output:** unchanged criterion, diagnostic threshold sensitivity, evidence about respondent/country perturbations and explicit interpretation limits. All calculations below use saved tables; no model is refitted.

**Decision, 12 October 2026:** retain the existing criterion: all required fits must succeed, and both the median and lower-decile pairwise ARI must be at least **0.80 in both respondent and country tests**, using unrounded values. LOO and one-country limitations remain unchanged. The 0.75/0.70 calculations are sensitivity descriptions only; they do not promote additional solutions, revise the shortlist, or change saved qualification statuses. No post-hoc Jaccard threshold is introduced either.

### Why the k=2 findings do not fulfil our profiling aim

The 14 resolutions meeting both full partition-stability benchmarks include **seven k=2 and seven k≥3 resolutions**. Binary partitions can reveal dominant contrasts and are worth preserving as diagnostics, but they are not satisfactory final answers to our aim of richer, multidimensional profiles—particularly when a partition nearly reproduces one survey variable. A benchmark-qualified partition is not automatically a scientifically useful typology. The earlier headline of 14 successes therefore overstates progress if read as 14 satisfactory rich profile solutions.

We do not force a larger k or weaken reproducibility to make the profiles appear more interesting. For local models, record separately: partition stability, resolution, individual-profile recovery, original-response meaning and global structural benchmarks. The seven full-benchmark-qualified k≥3 results remain the substantive regional set to review. This does not invalidate global B4/E8, which provide a common classification rather than a promise of independent recovery in every region.

### Could fewer data explain the limited local structure?

Possibly in part, but our present evidence does not establish that cause. Regional analysis has fewer respondents and fewer countries than global analysis, and small or rare profiles may contain little weighted information. However, many richer fits survive 20% respondent removal while every country remains represented, yet fail when whole countries disappear. Even regional cohorts of around 10,000–14,000 respondents show this behaviour. Respondent count alone is not an adequate explanation.

The two tests change different things. Respondent resampling retains every regional country. Country resampling changes country composition, total respondents, profile prevalence and sometimes the severity of the reduction: floor(0.8N) can retain substantially less than 80% of countries. Both also vary K-means random initialization. Consequently, country-test failure does not by itself isolate geographic differences, respondent-sample size or optimization effects.

The saved country tests permit one additional diagnostic without new fits: compare pairs fitted to the **same country subset** versus **different country subsets**. For an identical country subset the entire training cohort and weights are identical, so variation comes from initialization/optimization. For different subsets, country composition and respondent count also change. The comparisons are dependent and differently distributed across subsets; they are descriptive, not a causal experiment or a significance test. Where there are only a handful of same-subset pairs, their lower-decile summaries are especially weak evidence.

### What a lower threshold would admit—and why we retain 0.80

For full-country-test regions, requiring all four ARI summaries to reach 0.75 would increase the qualifying k≥3 set from 7 to 14 resolutions; 0.70 would increase it to 22. Some near-misses have meaningful original profiles and reasonable individual-cluster recovery. Others have reference groups that are almost never recovered under one-to-one overlap matching. Lowering overall ARI cannot resolve that problem.

The 0.80 benchmark is a research criterion, not an intrinsic pass/fail boundary of ARI. Nevertheless, changing it now to obtain richer results would be an adaptive relaxation requiring explicit justification. **We retain it.** Sensitivity results remain visible so conclusions do not treat a borderline failure as categorically different from a borderline pass, but all formal statuses and reported counts stay tied to 0.80.

Methodological background: [Shamir and Tishby, stability and model selection in K-means](https://doi.org/10.1007/s10994-010-5177-8); [official ARI definition](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.adjusted_rand_score.html). The numerical evidence here is from our saved course analyses, not those sources.''')

decision_code = nbformat.v4.new_code_cell('''# Objective: Reproduce threshold sensitivity and country-subset diagnostics from saved outputs; retain 0.80.
DISCUSSION_OUTPUT = LOCAL_OUTPUT/'discussion_20261012'
DISCUSSION_OUTPUT.mkdir(exist_ok=True)
metric_columns = ['respondent_median_ari','respondent_p10_ari','country_median_ari','country_p10_ari']
full_country = supported.loc[supported.countries.ge(5)].copy()
assert not combined_stability.failed_fits.any(), 'These comparisons require the completed successful-fit record.'
threshold_rows, sensitivity_rows = [], []
primary = full_country[metric_columns].ge(.80).all(axis=1)
for threshold in [.80,.75,.70]:
    qualified = full_country[metric_columns].ge(threshold).all(axis=1)
    rich = qualified & full_country.k.ge(3)
    threshold_rows.append({'threshold':threshold, 'full_partition_benchmark_resolutions':int(qualified.sum()),
        'k_ge_3_resolutions':int(rich.sum()), 'regions_with_k_ge_3':int(full_country.loc[rich,'region'].nunique()),
        'status':'retained primary rule' if threshold==.80 else 'diagnostic sensitivity only; not adopted'})
    additional = full_country.loc[rich & ~primary].copy()
    additional['diagnostic_threshold'] = threshold
    sensitivity_rows.append(additional)
threshold_sensitivity = pd.DataFrame(threshold_rows)
sensitivity_candidates = pd.concat(sensitivity_rows,ignore_index=True)
table_write(threshold_sensitivity,DISCUSSION_OUTPUT/'ari_threshold_sensitivity.csv')
table_write(sensitivity_candidates,DISCUSSION_OUTPUT/'lower_threshold_richer_candidates_not_retained.csv')
display(threshold_sensitivity)
display(sensitivity_candidates.loc[sensitivity_candidates.diagnostic_threshold.eq(.75),
    ['region_name','candidate','k','respondent_p10_ari','country_p10_ari',
     'worst_cluster_country_p10_jaccard']].round(3))
rich = full_country.loc[full_country.k.ge(3)]
resp_pass = rich[['respondent_median_ari','respondent_p10_ari']].ge(.80).all(axis=1)
country_pass = rich[['country_median_ari','country_p10_ari']].ge(.80).all(axis=1)
test_comparison = pd.DataFrame([{'eligible_tested_richer_resolutions':len(rich),
    'respondent_benchmark_met':int(resp_pass.sum()),'country_benchmark_met':int(country_pass.sum()),
    'both_met':int((resp_pass&country_pass).sum()),'respondent_met_country_not_met':int((resp_pass&~country_pass).sum()),
    'country_met_respondent_not_met':int((~resp_pass&country_pass).sum())}])
table_write(test_comparison,DISCUSSION_OUTPUT/'respondent_vs_country_stability.csv')
display(test_comparison)

plans = pd.read_csv(LOCAL_OUTPUT/'regional_sampling_plan_audit.csv')
pairwise = pd.concat([pd.read_csv(OUTPUT/'regional_pairwise_ari.csv'),
                     pd.read_csv(LOCAL_OUTPUT/'regional_pairwise_ari.csv')],ignore_index=True)
assert not pairwise.duplicated(['region','candidate','k','test','pair_number']).any()
subset_rows = []
for (region,name,k), group in pairwise.loc[pairwise.test.eq('countries')].groupby(['region','candidate','k']):
    plan = plans.loc[plans.region.eq(region)&plans.test.eq('countries')].sort_values('repeat')
    if len(plan)!=50:
        continue  # LOO is not repeated 50-subset evidence.
    countries = plan.country_list.to_list()
    pairs = list(itertools.combinations(range(50),2))
    group = group.sort_values('pair_number')
    assert group.pair_number.to_list()==list(range(1225))
    same = np.asarray([countries[a]==countries[b] for a,b in pairs])
    values = group.ari_unweighted.to_numpy()
    for kind, mask in [('same training countries',same),('different training countries',~same)]:
        series = values[mask]
        subset_rows.append({'region':int(region),'candidate':name,'k':int(k),'comparison':kind,
            'pair_count':int(mask.sum()), 'median_ari':float(np.median(series)) if len(series) else np.nan,
            'p10_ari':float(np.quantile(series,.1)) if len(series) else np.nan,
            'interpretation':'dependent descriptive comparisons; country composition and n not independently controlled'})
subset_diagnostics = pd.DataFrame(subset_rows).merge(regions[['GlobalRegion','region_name']],
    left_on='region',right_on='GlobalRegion',validate='many_to_one').drop(columns='GlobalRegion')
table_write(subset_diagnostics,DISCUSSION_OUTPUT/'same_vs_different_country_subset_ari.csv')
display(subset_diagnostics.loc[subset_diagnostics.region.eq(8)&subset_diagnostics.candidate.eq('E')
    &subset_diagnostics.k.eq(8),['region_name','candidate','k','comparison','pair_count','median_ari','p10_ari']].round(3))
threshold_decision = {'date':'2026-10-12','decision':'retain existing ARI 0.80 unchanged',
    'authority':'explicit user instruction in this chat',
    'median_threshold':.80,'lower_decile_threshold':.80,'required_tests':['respondents','countries'],
    'required_successful_fits_per_full_test':50,'small_region_policy_unchanged':True,
    'lower_thresholds_adopted':False,'new_models_fitted':False,'heldout_responses_used':False,
    'final_global_scope_approved':False,'global_models_frozen':False,
    'k2_role':'diagnostic dominant contrasts; not satisfactory final rich-profile solution',
    'source_selection_context':LOCAL_SELECTION_CONTEXT}
atomic_json(threshold_decision,DISCUSSION_OUTPUT/'ari_decision.json')
assert threshold_sensitivity.k_ge_3_resolutions.tolist()==[7,14,22]
assert test_comparison.respondent_met_country_not_met.iloc[0]==23
assert int(supported.loc[supported.status.eq(FULL_SUPPORT),'k'].eq(2).sum())==7
assert int(supported.loc[supported.status.eq(FULL_SUPPORT),'k'].ge(3).sum())==7
display(threshold_decision)
print('0.80 retained; no qualification status changed, no new fitting, no held-out response access.')''')

interpretation_md = nbformat.v4.new_markdown_cell('''## 15b Interpretation of the sensitivity discussion

**Objective:** distinguish plausible near-misses, fragile profiles and untested explanations.

**Output:** a critical interpretation of the saved diagnostic tables without changing the acceptance rule.

Among 66 tested k≥3 resolutions in the 11 regions eligible for full country resampling, 30 meet the respondent benchmark and eight meet the country benchmark; seven meet both. Twenty-three meet respondent stability but fail country stability. The principal observed limitation is therefore country-removal sensitivity, not demonstrated inability to estimate any richer structure from the available respondent counts. Regional size, country diversity, rare-profile information, geometry and randomized optimization remain possible contributing factors.

Eastern Asia E8 has country-test lower-decile ARI **0.854** among 245 pairs sharing identical training countries, versus **0.691** among 980 pairs with different country subsets. In the same-country comparisons, training respondents and weights are fixed and only randomized optimization changes. This supports an additional effect of changing the included countries, but differences in n and composition are not separated. The pair comparisons are dependent. Other regions have too few repeated identical subsets to support a reliable same-subset lower decile; the table retains their pair counts rather than treating them as equally persuasive.

At the unadopted 0.75 threshold, Eastern Africa B3/B4 would qualify with country lower-decile ARIs approximately **0.793/0.784** and weakest-cluster Jaccards **0.877/0.870**. Central/Western Africa B4 would qualify at approximately **0.772**, with weakest-cluster Jaccard **0.806**. These are informative near-misses under the unchanged criterion, not newly retained regional models. Conversely, Latin America E8 and Southern Europe E8 would also enter the 0.75 set despite weakest-cluster country Jaccards around **0.013/0.043**. A relaxed whole-partition ARI rule would not establish dependable recovery of every reference profile.

An optional, separate respondent-sample-size experiment could fit learning curves within a fixed country set and compare stability at several sample fractions. A complementary comparison could downsample global development respondents while preserving country coverage. Neither has been run or authorized here; neither is required to finish the current Objective 1 protocol. They would need a declared fitting/assignment design and would still not turn a count effect into proof of latent social types.

**Conclusion:** preserve 0.80, retain the seven full-benchmark-qualified richer resolutions with their profile-specific caveats, and report binary findings and near-misses as contextual evidence. The local analysis qualifies the geographic scope of the global models; it does not select replacement global centres or require every region to yield a rich standalone typology.''')

notebook.cells[48:48] = [decision_md, decision_code, interpretation_md]
notebook.cells.append(nbformat.v4.new_markdown_cell('''## 17 Next step: a development-only decision and freeze package

**Objective:** complete the pre-holdout decisions using existing evidence, not extend the local search indefinitely.

**Output to prepare next:** a reviewable global-model scope decision, frozen model/assignment manifests and development reference diagnostics. This section records the plan; it does not claim that freezing has happened.

The current 7 October protocol and Moodle Week 5 sequence make the next step **select and freeze the global specification(s)**, then validate them on the existing 29 held-out countries. Our regional search and its qualification decision are complete within their bounded scope. We should not automatically add more k searches, lower ARI, introduce another geographic grouping, or restart Prediction Strength from older descriptions.

The proposed development decision is to retain **global B4 and E8 as complementary descriptions**, not unrelated local solutions as replacements: B describes joint worry/harm patterns; E describes more differentiated worry themes and has Ward corroboration. This is a recommendation awaiting approval, not an approved final scope. The user has approved retaining 0.80 only. Regional results must accompany this scope decision, including binary dominant contrasts, country sensitivity, non-universal local recovery and fragile minor profiles. Neither global candidate is a universal regional typology.

Before held-out access, prepare and review:

1. **Model scope and meanings:** specify whether both B and E are retained, their roles, stable cluster IDs, original-response descriptions and limitations. Use existing complete-category distributions and assignment-quality results; do not invent new profile names from held-out responses.
2. **Exact assignment package:** preserve the existing fitted centres; save feature order, raw-code mappings, complete-case/eligibility rules, centring and appended mean, exact square-root multipliers, equal-country weighting, nearest-centre rule, seeds, software versions and fingerprints. Verify reloaded objects reproduce all development labels and join correctly by respondent ID. No refit is needed if the scope and models remain unchanged.
3. **Predeclared transfer interpretation:** freeze the development reference profiles, distance/margin summaries and profile-specific weighted distance p95 thresholds. Define what broad, partial or poor transfer means using the protocol's diagnostics. The p95 is an unusual-assignment flag, not an automatic overall transfer-failure rule; development ARI 0.80 is not a held-out assignment threshold. Resolve any additional numerical rule or uncertainty-reporting choice before opening held-out responses.

Only after approval and saving this package should we open the held-out response data, apply unchanged rules, report retention/exclusions and profile prevalence, and compare profile meanings, distances and margins overall and by country. Never update the global centres to improve held-out results. A partial or negative transfer finding is a valid conclusion, not permission to retune on the holdout.

The optional country-similarity analysis based on fixed-global profile proportions and maps can be pursued separately; it is not needed to establish the current freeze or to conclude Objective 1. No new model-fit or holdout experiment is performed in this documentation update.'''))

nbformat.write(notebook,destination)
print(destination)
print('Preserved v4. New discussion cells:', len(notebook.cells)-50)
