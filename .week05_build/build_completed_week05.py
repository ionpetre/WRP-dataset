"""Append the authorized freeze and fixed-model holdout validation; preserve all earlier versions."""
from pathlib import Path
import json
import nbformat

root=Path(__file__).resolve().parent.parent
info=json.loads((root/'.week05_build/transfer_run.json').read_text())
handoff=json.loads((root/'.week05_build/handoff_run.json').read_text())
source=root/'weekly_notebooks/week05_regional_validation_and_objective1_finalization_v5.ipynb'
destination=root/'weekly_notebooks/week05_regional_validation_and_objective1_finalization_v6.ipynb'
notebook=nbformat.read(source,as_version=4)
notebook.cells[0].source='''# Week 5 Final global profiles, regional evidence and held-out transfer — v6

**Objective:** complete Objective 1 by documenting the development evidence, the final B4/E8 freeze, fixed-model geographic validation and the reusable respondent assignments.

**Output:** regional comparisons; unchanged ARI 0.80 decision; a sealed, reload-tested model package; held-out inclusion and transfer diagnostics; original-unit interpretations and country limitations; bootstrap intervals; reusable figures/maps; an ID-linked handoff for later objectives.

**Current status:** global B4 and E8 are frozen as complementary descriptions. The 29 held-out countries were opened only after sealing and verifying that package. They were assigned without refitting or retuning. Objective 1 is concluded with **broad aggregate descriptive transfer and material country-specific limitations**, not a universal natural typology or eight uniformly secure E profiles.

Versions v1–v5 remain unchanged. **Sections 1–17 are the historical development-stage record**, including the earlier unopened-holdout boundary and decisions awaiting approval at that time. Sections 18–24 record the subsequent explicit approval, freeze, validation and completion. Historical “not frozen/unopened” statements describe those earlier stages; they are not the current status.

Re-execution verifies and replays completed evidence. It does not launch clustering fits, revise centres, regenerate the country split, or overwrite the frozen model package. Original model objects, complete-case rules, 21-coordinate geometry and cluster IDs are retained. All 146,910 prepared respondent IDs remain in the handoff; the 9,450 excluded respondents remain unassigned.'''
notebook.cells[3].source=notebook.cells[3].source.replace('v5: read-only','v6: read-only')
notebook.cells[3].source=notebook.cells[3].source.replace("print('Held-out responses remain unopened; no final model is frozen in this notebook version.')",
    "print('Historical development-stage replay. The completed freeze and held-out validation are reported in sections 18–24.')")
notebook.cells[1].source=notebook.cells[1].source.replace('**v5 execution rule:**','**v6 development replay rule:**')
notebook.cells[52].source=notebook.cells[52].source.replace('article_slide_evidence_inventory_v5.json','development_evidence_inventory_v6.json').replace('week05_regional_validation_and_objective1_finalization_v5.ipynb','week05_regional_validation_and_objective1_finalization_v6.ipynb')
notebook.cells[53].source=notebook.cells[53].source.replace('## 17 Next step:', '## 17 Historical pre-holdout plan:')
notebook.cells[53].source+='\n\n**Subsequent approval:** the user explicitly authorized “Freeze B4/E8, then run held-out validation.” Sections 18–24 execute that sequence and report its results. This earlier plan and its pending-approval language are preserved as a decision history.'

def md(s):notebook.cells.append(nbformat.v4.new_markdown_cell(s))
def code(s):notebook.cells.append(nbformat.v4.new_code_cell(s))

md(r'''## 18 Final development decision and a sealed model package

**Objective:** freeze the approved B4/E8 specifications before reading any held-out responses.

**Output:** a sealed model/assignment package with preserved profile IDs, original-response definitions, development reference diagnostics and exact reload checks.

The user approved **freezing B4/E8 and then running held-out validation**. B4 is the joint worry/harm description; E8 is the complementary differentiated worry description, with existing Ward corroboration. We retain both, not a universal regional model or a strict hierarchy. Local k=2 findings remain diagnostics; they do not fulfil the richer local profiling aim. The 0.80 development ARI rule is unchanged and is not a held-out transfer rule.

The existing centres were **not refitted**. Reference seed 20231006 and n_init=20 are recorded from the Week 4 reference code; stability-resampling seeds belong to their separately recorded experiments. The package preserves original raw-code mappings, six worry and fourteen separate harm features, within-person centring and appended mean, exact multipliers \(\sqrt{\alpha/6}\) and \(\sqrt{(1-\alpha)/14}\), complete-case eligibility, equal-country weighting, software versions and fingerprints. B retains top=2, alpha=0.5, k=4; E retains top=3, alpha=0.75, k=8. There is no imputation, PCA or variance standardization.

Nearest-centre assignment uses the stored centre order and first centre on an exact tie; margin is (second−nearest)/second and zero if both distances are zero. Profile-specific weighted development p95 distances are frozen as **unusual-assignment flags**, not automatic transfer failures. Three largest positive original-category-versus-outside contrasts per development profile were fixed as descriptive anchors before held-out access; the full original-category distributions remain the main semantic evidence.

The freeze seal records **09:44:34 UTC (12:44:34 Helsinki)** on 12 October 2026. First held-out response access was **09:46:25 UTC (12:46:25 Helsinki)**. This order is verified from the saved records. The exported assignment code contains no fitting or tuning operation. Reloading the sealed objects reproduces all 109,488 saved development labels exactly. Earlier frozen k=3 artifacts under processed/ or week04_frozen_profile_model.joblib are unrelated legacy analyses, not this B/E validation.

The transfer interpretation and uncertainty plan were saved in the seal before opening responses: inspect profile identity, prevalence, distances, margins and country-specific fit; synthesize broad/partial/poor transfer without an invented numeric score. Use 1,000 fixed-model country-bootstrap draws, seed 20261012, with relative survey weights preserved within sampled complete-case countries. These intervals describe the observed country set, not population-proportional worldwide prevalence, complex survey-design uncertainty or model-fitting uncertainty.''')
assignment_source=(root/'.week05_build/frozen_assignment.py').read_text()
code('# Objective: Define portable frozen-model loading, recoding, weighting and assignment; no fitting or tuning.\n'+assignment_source)
transfer_source=(root/'.week05_build/frozen_transfer.py').read_text().replace('from week05_core import *  # Removed when embedded in the self-contained notebook.\n','').replace('from frozen_assignment import *  # Removed when embedded in the self-contained notebook.\n','')
code('# Objective: Preserve the complete freeze/transfer implementation for inspection and reproducibility; execution below replays saved results.\n'+transfer_source)
code(f'''# Objective: Verify the sealed package and immutable transfer record before replaying their evidence.
FROZEN_PACKAGE = ROOT / {info['package_directory']!r}
TRANSFER_OUTPUT = ROOT / {info['output_directory']!r}
HANDOFF_OUTPUT = ROOT / {handoff['output_directory']!r}
EXPECTED_FREEZE_CONTEXT = {info['context']!r}
frozen_bundle, frozen_manifest = load_frozen_package(FROZEN_PACKAGE)
transfer_record = json.loads((TRANSFER_OUTPUT/'transfer_complete.json').read_text())
assert frozen_manifest['context']==transfer_record['freeze_context']==EXPECTED_FREEZE_CONTEXT
assert frozen_manifest['heldout_responses_used_at_freeze'] is False
assert transfer_record['first_heldout_response_read_at_utc'] > frozen_manifest['frozen_at_utc']
assert transfer_record['freeze_seal_sha256']==file_sha256(FROZEN_PACKAGE/'freeze_seal.json')
assert frozen_manifest['transfer_plan']==TRANSFER_PLAN
assert not transfer_record['model_refit'] and not transfer_record['retuning']
assert file_sha256(ROOT/TRANSFER_PLAN['heldout_source'])==transfer_record['heldout_input_sha256']
for key in ['tables','assignments']:
    for name,expected in transfer_record[key].items():
        assert file_sha256(TRANSFER_OUTPUT/name)==expected,'Transfer evidence changed: '+name
development_replay=assign_frozen(data,frozen_bundle)
for name in SPECIFICATIONS:
    assert np.array_equal(development_replay[name].cluster,global_references[name]['labels'])
display(pd.read_csv(FROZEN_PACKAGE/'profile_definitions.csv'))
display(pd.read_csv(FROZEN_PACKAGE/'development_stability.csv')[
    ['candidate','experiment','median_pairwise','p10_pairwise','p10_cluster_jaccard']])
print('Sealed scope:',frozen_manifest['approved_scope'])
print('Frozen before held-out access:',frozen_manifest['frozen_at_utc'], '<', transfer_record['first_heldout_response_read_at_utc'])
print('All development assignments reproduce exactly; no refit.')''')

md('''## 19 Held-out integrity, missingness and assignment coverage

**Objective:** apply the frozen rules to the existing 29-country split and retain excluded respondents explicitly.

**Output:** verified country/respondent separation, sequential exclusions, country retention, assignment replay and a demographic selection audit.

The prepared holdout has **30,090 respondents**. Of these, **27,972 (92.96%)** are complete cases and receive both B/E labels. All **29 countries** retain eligible respondents. The 2,118 excluded respondents comprise one with zero observed profile responses, 202 removed at the historical four-worry/four-harm screening stage, and 1,915 with remaining missing profile responses. The ultimate rule is all 20 derived features observed, equivalently substantive answers to all six worry and seven original harm questions. The historical four/four screen is weaker than this final rule. Excluded respondents are not assigned through imputation.

Conditional assigned coverage is 100% **of complete cases**, not of all prepared respondents. Development retention was 93.72% by respondent count versus 92.96% in holdout; country-balanced mean retention is 93.57% versus 92.83%. These are different estimands and are labelled separately.

Country retention varies from **78.7% to 99.8%**. Sierra Leone retains 78.7%, Laos 80.5%, Moldova 80.6%, Tajikistan 81.2% and Somalia 82.9%. The complete-case profiles therefore describe a selected respondent population. The demographic audit compares prepared, included and excluded cohorts using available age, gender, education and urbanicity variables. Each cohort's equal-country weights are recomputed; the excluded development cohort includes 112 rather than 113 countries. Differences are descriptive, not proof that missingness is ignorable or a causal selection mechanism.

Frozen raw-code checks are replayed on holdout: worry raw 1/2/3 becomes 2/1/0; harm raw 1/2/3/4 becomes personal (1/0/1/0) and known-person (0/1/1/0); 98/99 remain missing. No encoding or weighting is learned anew from responses. Survey-weight normalization is recomputed within the assigned held-out cohort, as specified before access.''')
notebook.cells[-1].source += '\n\nFor the demographic diagnostic tables, the harmonized dictionary defines Gender 1=male, 2=female; Education 1=primary or less, 2=secondary, 3=tertiary, 9=DK/refused; Urbanicity2 1=rural/small town, 2=city/suburb, 9=DK/refused; AgeGroups3 1=15–29, 2=30–49, 3=50+. DK/refused is shown separately, not interpreted as substantive education or urbanicity. Source Age=100 was already recoded to missing in the curated data. These variables are selection diagnostics, not inputs to B/E.'
code('''# Objective: Replay held-out recoding and assignment, verify disjoint IDs/countries and display all exclusions.
holdout_raw=pd.read_parquet(ROOT/TRANSFER_PLAN['heldout_source'],columns=prepared_columns())
holdout_features=derive_frozen_features(holdout_raw)
holdout_audit,holdout_country_audit=eligibility_audit(holdout_features)
heldout_complete=holdout_features.loc[holdout_audit.complete_case].reset_index(drop=True)
frozen_split=pd.read_csv(FROZEN_PACKAGE/'frozen_country_split.csv')
expected_holdout=set(frozen_split.loc[frozen_split.country_split.eq('heldout_country'),'COUNTRY_ISO3'])
assert len(holdout_raw)==30090 and holdout_raw.WPID_RANDOM.is_unique
assert set(holdout_raw.COUNTRY_ISO3)==expected_holdout and len(expected_holdout)==29
assert not set(holdout_raw.COUNTRY_ISO3).intersection(data.COUNTRY_ISO3)
development_all_ids=pd.read_parquet(ROOT/'course_artifacts/week03_development_data.parquet',columns=['WPID_RANDOM']).WPID_RANDOM
assert not set(holdout_raw.WPID_RANDOM).intersection(development_all_ids)
heldout_replay=assign_frozen(heldout_complete,frozen_bundle)
for name in SPECIFICATIONS:
    saved=pd.read_parquet(TRANSFER_OUTPUT/f'heldout_{name}_assignments.parquet')
    assert np.array_equal(saved.WPID_RANDOM,heldout_replay[name].WPID_RANDOM)
    assert np.array_equal(saved.cluster,heldout_replay[name].cluster)
    assert np.allclose(saved.nearest_distance,heldout_replay[name].nearest_distance)
assert len(heldout_complete)==27972 and heldout_complete.COUNTRY_ISO3.nunique()==29
display(pd.read_csv(TRANSFER_OUTPUT/'heldout_exclusion_counts.csv'))
display(pd.read_csv(TRANSFER_OUTPUT/'heldout_country_retention.csv').sort_values('retained_fraction'))
selection_audit=pd.read_csv(TRANSFER_OUTPUT/'missingness_selection_demographic_audit.csv')
display(selection_audit)
print('100% assignment of 27,972 complete cases; 2,118 prepared respondents explicitly remain unassigned.')''')

md('''## 20 Transfer of prevalence, profile meaning and representation quality

**Objective:** compare fixed-global development and held-out profiles without treating prevalence equality as a success condition.

**Output:** complete original-category comparisons, frozen-anchor contrasts, all-profile quality summaries and fixed-model country-bootstrap intervals.

The largest absolute change in profile prevalence is **1.45 percentage points for B** and **1.55 for E**. B's broad-harm group is 18.53% in development and 17.16% in holdout; its lower-worry/harm group is 33.77% and 34.34%. E's lower-worry group is 36.11% and 34.56%, and broad-high-worry group 10.37% and 10.69%. Frequencies are close at the aggregate, but matching prevalence is neither required nor sufficient for transfer, and the intervals do not establish statistical equivalence.

All **36 preselected development anchor contrasts retain their positive direction** in aggregate holdout profiles. Their meanings remain recognizable: B's broad exposure is especially through known people; the other B profiles distinguish food/water concern, crime/weather/traffic concern and lower worry/harm. E's domain-specific worry themes remain identifiable. Mean feature-wise categorical TV against development ranges **0.008–0.025 for B** and **0.011–0.030 for E**. These are average marginal shifts, not a test of the complete joint distribution or a declared semantic threshold.

Assignment quality is similar overall. B's median distance increases by 0.4% and p90 by 1.5%; E's corresponding increases are 1.0% and 0.6%. Median margins are B 0.134 versus development 0.137 and E 0.273 versus 0.273. Distances and margins are geometric diagnostics, not posterior probabilities, and B/E distances are not compared across their different geometries.

Beyond the frozen profile-specific development p95, **6.34%** of held-out B assignments are flagged versus **4.99%** in development; E is **5.44% versus 4.98%**. B's food/water C2 has the clearest profile-level rise, to **8.18%** flagged, and p90 distance approximately 4.8% higher. This is a warning about representation, not a post-hoc automatic failure.

Some very sharp E anchors follow partly from the frozen assignment geometry: a rule that selects a very-worried-traffic group will predictably preserve that defining category when applied to another cohort. The more informative evidence is the full remaining worry/harm distributions, non-defining contrasts, distance/margin behaviour and country-specific results. We validate the transfer of a **fixed descriptive classification**, not independent rediscovery of latent types by reclustering the holdout. No holdout refit was performed.''')
code('''# Objective: Display complete held-out/development comparisons and their fixed-model uncertainty summaries.
prevalence_transfer=pd.read_csv(TRANSFER_OUTPUT/'prevalence_comparison_with_country_intervals.csv')
quality_transfer=pd.read_csv(TRANSFER_OUTPUT/'heldout_vs_development_quality.csv')
semantic_transfer=pd.read_csv(TRANSFER_OUTPUT/'semantic_differences_with_sample_sizes.csv')
anchor_transfer=pd.read_csv(TRANSFER_OUTPUT/'heldout_frozen_anchor_comparison.csv')
bootstrap_intervals=pd.read_csv(TRANSFER_OUTPUT/'heldout_country_bootstrap_intervals.csv')
display(prevalence_transfer[['candidate','cluster','profile_name','equal_country_weighted_share_development',
    'equal_country_weighted_share_heldout','prevalence_difference_pp','p025','p975']].round(4))
display(quality_transfer[['candidate','cluster','distance_median_ratio','distance_p90_ratio',
    'margin_median_heldout','margin_median_development','profile_p95_exceedance_heldout','profile_p95_exceedance_development']].round(4))
display(semantic_transfer.loc[semantic_transfer.scope.eq('global')])
display(anchor_transfer[['candidate','cluster','feature','category','development_proportion','proportion',
    'development_contrast','difference_vs_outside','heldout_contrast_direction_preserved']])
assert anchor_transfer.heldout_contrast_direction_preserved.all() and len(anchor_transfer)==36
assert bootstrap_intervals.valid_draws.eq(1000).all()
display(bootstrap_intervals)
print('Intervals: 1,000 fixed-model country draws; no fit uncertainty, worldwide population inference or equivalence claim.')''')

md('''## 21 Country-specific limitations and smaller-profile reliability

**Objective:** prevent reassuring global averages from hiding geographic weaknesses, sparse cells or uncertain profile boundaries.

**Output:** all-country retention/quality tables, country/profile semantic shifts with sample sizes, anchor reversals and the existing per-profile development recovery record.

The most conspicuous distance flags occur in **Sierra Leone, Somalia and Namibia**:

| Held-out country | B beyond frozen p95 | E beyond frozen p95 | Prepared respondents retained |
|---|---:|---:|---:|
| Sierra Leone | 25.3% | 14.8% | 78.7% |
| Somalia | 24.0% | 12.5% | 82.9% |
| Namibia | 17.9% | 12.4% | 94.4% |

The fixed models represent these countries less well than the aggregate. Sierra Leone and Somalia also have appreciable complete-case selection, but Namibia's high retention shows that missingness alone is not an adequate explanation. None of these descriptive associations identifies a causal mechanism. The p95 flags are not a country pass/fail threshold or evidence that every flagged respondent needs a new profile.

Country-level profile meanings vary more than pooled meanings. Mean feature-wise TV reaches 0.264 for Somalia E C7, involving 104 respondents, and approximately 0.264 for Sweden E C7, involving **only three**. Sweden E C3 also has only three respondents; its large semantic shift is highly uncertain and is not evidence of broad national transfer failure. Saved tables include raw n and Kish weighted n so these cases are not interpreted alike. Across country-specific frozen anchors, all 348 B contrasts remain positive; E preserves 687 of 696, with nine reversals involving secondary features and, in some cases, sparse profiles. These counts are descriptive and partly reflect the assignment geometry, not independent hypothesis tests.

Development individual-profile recovery also matters after a model is frozen. Existing Week 4 diagnostics show B's country-test per-profile Jaccard lower deciles around **0.91–0.96**. E is less uniform: its crime/traffic C3 lower decile is about **0.088** in both respondent and country perturbations; crime-focused C4 is about **0.431–0.433**. Whole-partition ARI still passes the unchanged rule. The sealed classification can transfer descriptively while these specific eight-profile distinctions remain uncertain under re-estimation. Good fixed-model transfer does **not** erase that development limitation. E remains a complementary, more tentative thematic resolution, not eight equally established natural types.

No model, profile ID or threshold was modified in response to these findings. B/E and regional results are interpreted together rather than selecting only the most favourable statistic.''')
code('''# Objective: Inspect all country limitations and the already-computed individual-profile recovery evidence.
country_transfer=pd.read_csv(TRANSFER_OUTPUT/'heldout_country_quality_and_retention.csv')
country_anchor_transfer=pd.read_csv(TRANSFER_OUTPUT/'country_frozen_anchor_diagnostics.csv')
development_profile_recovery=pd.read_csv(TRANSFER_OUTPUT/'development_existing_per_profile_recovery.csv')
display(country_transfer[['Country','candidate','respondents','retained_fraction','distance_median','distance_p90',
    'margin_median','profile_p95_exceedance']].sort_values('profile_p95_exceedance',ascending=False))
display(semantic_transfer.loc[semantic_transfer.scope.eq('country')].sort_values('mean_feature_TV',ascending=False).head(30))
display(country_anchor_transfer.loc[~country_anchor_transfer.heldout_country_contrast_positive,
    ['candidate','area_id','cluster','feature','category','respondents','kish_weighted_n','difference_vs_outside_heldout']])
display(development_profile_recovery)
print('Sparse-cell differences and weak development recovery remain qualifications; no post-hoc rejection threshold added.')''')

md('''## 22 Visual evidence and reporting failures

**Objective:** provide reusable visual comparisons without concealing selection or geographic limitations.

**Output:** paired prevalence/interval plots, original-response anchors, country distance flags and all-country B/E prevalence maps.

The maps use the same frozen global profile IDs in all 142 countries, one 0–100% colour scale, and black borders for held-out countries. Small countries use dots/diamonds. They show profile prevalence, not a new country clustering or geographic classification; country/profile tables remain authoritative. Natural Earth de facto borders are not a political claim.

One initial map-generation attempt failed because the survey's **PSE** identifier did not directly match Natural Earth's **PSX** administrative key. It was resolved using the cartography's explicit ISO_A3=PSE field, without changing geometry, scientific results or models. The key audit now verifies all 142 analysis-country codes. This was a reporting failure, not a failed clustering or transfer computation. The earlier Week 4 computational failures and approximations remain in their preserved notebooks; no new model-fitting failure occurred here.''')
doc_source=(root/'.week05_build/transfer_documentation.py').read_text()
code('# Objective: Include the reporting-only table and plot implementation; it contains no fitting, retuning or threshold changes.\n'+doc_source)
code('''# Objective: Display the verified completed figures and cartographic key audit without regenerating fits or models.
transfer_figures=[TRANSFER_OUTPUT/'figures'/name for name in [
    'development_vs_heldout_profile_prevalence.png','frozen_anchor_original_response_transfer.png',
    'heldout_country_distance_flags.png','B_frozen_all_country_profile_maps.png','E_frozen_all_country_profile_maps.png']]
for path in transfer_figures:display(Image(filename=str(path)))
display(json.loads((TRANSFER_OUTPUT/'map_key_audit.json').read_text()))''')

md('''## 23 Objective 1 conclusion: useful fixed profiles, qualified geographic transfer

**Objective:** close the research question with a claim proportional to the evidence, including mixed findings.

**Output:** final model scope, transfer interpretation and limits for the slides/article.

**Final scope:** frozen global B4 and E8 are retained as complementary descriptive classifications of 2023 complete-case respondents. B combines worry-domain patterns and personal/known-person harm exposure; E distinguishes more worry themes. They do not form a strict hierarchy. Ward corroborates E under related Euclidean/centroid-extension geometry, not as wholly independent evidence of latent classes.

**Development:** both global candidates pass the structural screen and both full median/lower-decile ARI≥0.80 tests. The bounded regional search shows that richer global partitions do not recur independently everywhere; several regions support different resolutions or mainly a simple dominant contrast. Among the regional full-benchmark results, seven have k≥3 and seven are diagnostic binary partitions. Smaller-profile recovery is uneven, especially for some E distinctions. These results qualify the global interpretation rather than compel regional replacement models.

**Held-out transfer:** applying the sealed models to 27,972 complete cases in all 29 untouched countries preserves the aggregate defining contrasts and closely similar marginal response distributions, with broadly similar distances/margins. There are important geographic limits, especially unusually distant assignments in Sierra Leone, Somalia and Namibia, and sparse country/profile cells. The appropriate synthesis is **broad aggregate descriptive transfer with partial country-specific representation limitations**. This is an analytical judgement under the predeclared diagnostics, not a numerical acceptance score, p-value or proof of statistical equivalence.

**Scientific contribution:** the profiles provide a reproducible common language for distinguishing domain-specific worry and exposure patterns rather than only an overall burden gradient. The regional analyses reveal repeatable local distinctions, semantic variation and limitations of a universal resolution. That contribution is a structured descriptive framework, not evidence that people fall into four or eight natural social types. Some pure worry anchors are partly induced by modelling geometry and assignment. Claims about outcomes, causal explanations and demographic predictability belong to later objectives.

**Limitations:** complete-case selection; country-balanced rather than population-proportional estimates; conditional survey-weighting without full complex-design variance; marginal semantics rather than the full joint distribution; geometric assignment ambiguity; adaptive development k selection; small regional country counts; uneven individual-profile recovery; and selected country-level deterioration. Fixed-model country-bootstrap intervals reflect only variation over the observed held-out countries. No all-country refit, holdout refit, threshold relaxation or model redesign was performed.

**Completion:** Objective 1's current protocol is fulfilled: regional evidence, final scope/freeze, geographic validation, explicit limitations and a reproducible assignment handoff are documented. Completion means the research question has a defensible, qualified answer—not guaranteed universal success. The holdout has now been used; any later redesign is a new development cycle and cannot reuse these same countries as untouched confirmation. Optional country-similarity analysis remains a separate extension, not unfinished required Objective 1 work.''')

md('''## 24 Reproducible handoff to Objectives 2 and 3

**Objective:** preserve model identities, eligibility and respondent linkage so later analyses cannot silently change the profiles or weighting estimand.

**Output:** portable frozen-model objects, all-respondent and assigned-only Parquet tables, a completion/reuse manifest and verified hashes.

The handoff preserves **146,910 prepared respondent IDs across 142 countries**: 137,460 receive both frozen profile labels and **9,450 remain unassigned** because they lack complete profile responses. Join by unique WPID_RANDOM, keep COUNTRY_ISO3 and country_split, and preserve B_C0–B_C3 and E_C0–E_C7. Do not relabel profiles by their prevalence in a new subgroup or impute labels for excluded respondents.

Two weighting columns are explicitly different: **equal_country_weight_within_split** sums to one separately for development and holdout; **equal_country_weight_all_included_countries** sums to one over the complete assigned cohort across all 142 countries. Use the latter only for a deliberately pooled country-balanced analysis. Concatenating the two split-normalized weights unchanged would give each split equal total mass rather than each country equal mass.

The frozen package is copied into the handoff and its original seal is reverified. Reusing global descriptive labels does not authorize supervised validation leakage: later predictive modelling still needs an explicit country-level design. The package records geographic and E-profile limitations alongside the assignments, rather than handing off labels without their evidential qualifications.''')
code('''# Objective: Verify the final ID-linked handoff, frozen models and completed reporting evidence.
handoff_record=json.loads((HANDOFF_OUTPUT/'objective1_completion_and_reuse.json').read_text())
handoff_all=pd.read_parquet(HANDOFF_OUTPUT/'all_respondents_eligibility_and_frozen_profiles.parquet')
assert len(handoff_all)==146910 and handoff_all.WPID_RANDOM.is_unique
assert int(handoff_all.complete_case.sum())==137460 and int((~handoff_all.complete_case).sum())==9450
for name in SPECIFICATIONS:
    assert handoff_all.loc[handoff_all.complete_case,name+'_cluster'].notna().all()
    assert handoff_all.loc[~handoff_all.complete_case,name+'_cluster'].isna().all()
assert np.isclose(handoff_all.equal_country_weight_all_included_countries.sum(),1)
for split,group in handoff_all.groupby('country_split'):
    assert np.isclose(group.equal_country_weight_within_split.sum(),1)
load_frozen_package(HANDOFF_OUTPUT/'frozen_models')
for name,expected in handoff_record['files'].items():assert file_sha256(HANDOFF_OUTPUT/name)==expected
load_frozen_package(FROZEN_PACKAGE)
final_inventory={
    'status':'Objective 1 completed with qualified descriptive transfer conclusions',
    'freeze_context':EXPECTED_FREEZE_CONTEXT,'notebook':'week05_regional_validation_and_objective1_finalization_v6.ipynb',
    'frozen_scope':['B4','E8'],'models_refitted':False,'development_ARI_threshold':.80,
    'heldout_prepared':30090,'heldout_assigned':27972,'heldout_countries':29,
    'conclusion':'Broad aggregate descriptive transfer; material country-specific representation limitations',
    'freeze_seal_sha256':file_sha256(FROZEN_PACKAGE/'freeze_seal.json'),
    'transfer_record_sha256':file_sha256(TRANSFER_OUTPUT/'transfer_complete.json'),
    'handoff_record_sha256':file_sha256(HANDOFF_OUTPUT/'objective1_completion_and_reuse.json'),
    'tables':{p.name:file_sha256(p) for p in sorted(TRANSFER_OUTPUT.glob('*.csv'))},
    'figures':{str(p.relative_to(TRANSFER_OUTPUT)):file_sha256(p) for p in transfer_figures},
    'reporting_failure':'PSE/PSX map key mismatch repaired using ISO_A3; model/transfer results unchanged',
    'major_cautions':['complete-case selection','country-balanced estimand','geometry-constrained anchors',
        'weak development recovery of some E profiles','country-specific distance deterioration','no universal latent-type claim']}
atomic_json(final_inventory,TRANSFER_OUTPUT/'objective1_final_evidence_inventory.json')
display(handoff_record)
display(final_inventory)
print('Objective 1 complete: frozen models verified, fixed-model held-out transfer documented, all IDs retained for reuse.')''')
nbformat.write(notebook,destination)
print(destination)
print('Cells:',len(notebook.cells))
