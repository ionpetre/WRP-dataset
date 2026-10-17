"""Update the canonical executed notebook; preserve its outputs and all frozen scientific artifacts."""
from pathlib import Path
import nbformat

root=Path(__file__).resolve().parent.parent
path=root/'weekly_notebooks/week05_regional_validation_and_objective1_finalization.ipynb'
notebook=nbformat.read(path,as_version=4)
for cell in notebook.cells:
    if cell.cell_type!='markdown':continue
    if cell.source.startswith('# Week 5 Final'):
        cell.source=cell.source.replace('Versions v1–v5 remain unchanged.',
            'This is the canonical Week 5 notebook. At the user’s request, superseded Week 5 notebooks v1–v5 are removed from the active workspace using recoverable deletion (Trash); model caches, result tables and the sealed packages are retained.')
    if cell.source.startswith('## 19 Held-out integrity') and 'These exclusions are not distance flags' not in cell.source:
        cell.source += '\n\n**Why 27,972 rather than 30,090?** We require complete responses to six worry and seven original harm questions. The seven harm answers generate fourteen personal/known-person indicators, so 13 original questions produce 20 features. A missing harm answer makes both corresponding indicators missing. The frozen complete-case rule—not a failed fit—leaves 2,118 respondents unassigned. The one/202/1,915 counts are mutually exclusive bookkeeping stages; all three groups ultimately lack complete profile information. These exclusions are not distance flags: atypically distant complete-case respondents still receive their nearest profile. The model does not assign incomplete cases by ignoring missing coordinates or introducing a new imputer at validation time.'
    if cell.source.startswith('## 23 Objective 1 conclusion') and 'not a formal quantitative acceptance test' not in cell.source:
        cell.source += '\n\n**Strength of validation claim:** held-out assessment was not a formal quantitative acceptance test. The diagnostic plan and qualitative broad/partial/poor-transfer criteria were fixed before response access, but no overall numerical rejection threshold was declared. We therefore report favourable, geographically qualified performance under those diagnostics, not that the models passed a prespecified quantitative test. The remaining analytical discretion is a methodological limitation. We must not create numerical rejection boundaries retrospectively from these favourable results.'

def md(text):return nbformat.v4.new_markdown_cell(text)
def code(text):return nbformat.v4.new_code_cell(text)

distance=md(r'''## 20a Discussion clarification: what a distance flag means

**Objective:** distinguish atypical representation from failed assignment, exclusion or classification error.

**Output:** a self-contained definition of the frozen distance diagnostic and its limits.

For each assigned development profile c, measure the Euclidean distance to its stored centre in that model's **scaled 21-coordinate space**. Freeze a separate equal-country/survey-weighted 95th-percentile distance \(t_c\) for each profile. A held-out respondent i is flagged if \(d(x_i,\mu_{c_i})>t_{c_i}\). Using a separate threshold accommodates profiles with different dispersion. The cutoff is learned only from development; it is not recalibrated to make the held-out rate 5%.

Approximately 5% of development assignments exceed their cutoffs by construction; discrete distances and percentile ties can make the actual rate slightly below 5%. A higher held-out rate means more respondents are atypically far from their nearest available frozen profile compared with development members of that same profile. It does not by itself say why: differences in response combinations, country composition, profile representation or selection may contribute.

The flag **does not remove the respondent or change their label**, prove the assignment wrong, establish a new cluster, or identify a statistical outlier under a fitted probability distribution. All complete cases receive their nearest profile, flagged or not. It is not an assignment probability or accuracy measure. For example, Sierra Leone's 25.3% B flag rate is a weighted fraction of its assigned complete-case respondents, not a statement that 25.3% were misclassified. It is unrelated to the 2,118 holdout respondents excluded for missing profile responses.''')

quality=md('''## 21a Discussion clarification: how good is the held-out result?

**Objective:** distinguish favourable aggregate transfer from uniform country quality, forced label assignment and latent-type discovery.

**Output:** an analytical synthesis and a reproducible explanatory concentration diagnostic.

The evidence supports **useful fixed descriptive classifications that transfer broadly in aggregate, with localized weaknesses**. All 36 frozen aggregate anchor contrasts remain positive, the full marginal category distributions change little, nearest-centre distances and margins change modestly, and profile prevalence differs by at most about 1.6 percentage points. Frequency similarity alone is not sufficient evidence: the country split balanced geographic/income metadata, and defining E categories can also be partly preserved by assignment geometry.

The distance deterioration is not spread evenly across countries. The median held-out country has a flag rate of **4.46% for B** and **4.51% for E**, despite overall country-balanced rates of 6.34% and 5.44%. Sierra Leone, Somalia and Namibia are the three highest-flag countries for both models. The remaining 26 countries average **4.49% for B** and **4.53% for E**. This is an **explanatory calculation performed after inspection**, not a new acceptance criterion: the three countries remain in every official validation result and are not removed to improve the summary. The complete country table and the concentrated failures remain part of the scientific conclusion.

There is no independent ground-truth profile label, so we cannot report classification accuracy. Receiving a mandatory nearest-centre label is not evidence of a good match, and 92.96% prepared-sample coverage is not 92.96% accuracy. Nor does this validation independently rediscover clusters through holdout refitting. It evaluates application of the frozen classification to new countries.

The scope is complete-case respondents; selective missingness remains a limitation. Rare country/profile cells require caution. B is the stronger core result because its individual development profiles recover more consistently; E adds useful thematic detail, but some boundaries remain tentative under re-estimation. E's lower aggregate distance-flag rate is not, by itself, a reason to call it the better model: it uses more centres and a different geometry.

The defensible conclusion is: **the frozen profiles retain their aggregate interpretation and broadly similar representation quality in unseen countries, but their usefulness is not geographically uniform.** They are qualified descriptive classifications, not universally reproducible natural population types.''')

concentration=code('''# Objective: Reproduce the explanatory country concentration diagnostic without excluding any country or changing model acceptance.
concentration_rows=[]
country_flag_table=pd.read_csv(TRANSFER_OUTPUT/'heldout_country_quality_and_retention.csv')
for name,group in country_flag_table.groupby('candidate'):
    assert len(group)==29 and group.COUNTRY_ISO3.is_unique
    top=group.nlargest(3,'profile_p95_exceedance')
    remaining=group.loc[~group.COUNTRY_ISO3.isin(top.COUNTRY_ISO3)]
    assert len(remaining)==26
    concentration_rows.append({'candidate':name,'all_countries':29,
        'overall_equal_country_flag_rate':float(group.profile_p95_exceedance.mean()),
        'median_country_flag_rate':float(group.profile_p95_exceedance.median()),
        'three_highest_flag_countries':'; '.join(top.Country),
        'remaining_countries':26,'remaining_26_mean_flag_rate':float(remaining.profile_p95_exceedance.mean()),
        'top_three_contribution_to_all29_rate':float(top.profile_p95_exceedance.sum()/29),
        'status':'post-validation explanatory diagnostic only; all 29 countries remain in official results'})
country_flag_concentration=pd.DataFrame(concentration_rows)
table_write(country_flag_concentration,TRANSFER_OUTPUT/'heldout_country_distance_flag_concentration.csv')
display(country_flag_concentration)
assert set(country_flag_table.COUNTRY_ISO3)==set(expected_holdout)
print('No countries excluded, no numerical rejection threshold introduced, no profile or model changed.')''')

rejection=md('''## 23a Discussion clarification: what would have rejected the models?

**Objective:** state the prespecified poor-transfer conditions and the limits of our decision procedure.

**Output:** a transparent falsifiability/rejection discussion without adding post-hoc numerical rules.

The frozen transfer plan specified poor transfer as **substantial loss of defining response patterns or widespread deterioration in representation quality**, assessed for B and E separately. It explicitly said that the final decision was an analytical synthesis, not an automatic numerical score.

Evidence against suitability for the intended global descriptive use would include:

1. **Lost profile meanings:** the full original-unit distributions no longer support the descriptions—for example, a lower-worry profile no longer showing lower worry, or broad-harm members no longer being distinguished by harm exposure. Reversed or vanished non-mechanically constrained contrasts and major shifts across features would weigh against semantic transfer.
2. **Substantially poorer representation:** widespread increases in nearest-centre distances and profile-specific flags, especially with smaller nearest/second-nearest margins, suggesting respondents are forced into poorly fitting available profiles. Mandatory assignment would not rescue such a result.
3. **Geographically widespread weakness:** reassuring aggregate averages conceal substantial loss of meaning or fit across many countries. Concentrated country/profile weaknesses instead support partial or geographically qualified transfer, rather than uniform success.

Different profile frequencies alone, a low-prevalence profile, a few distant respondents, or a sparse country/profile cell would not automatically reject a model. Large complete-case exclusions would limit population coverage; they are not themselves classification errors or proof of centre failure. The development ARI 0.80 screen is not a held-out rejection threshold.

**Important methodological qualification:** we did **not** predeclare an overall numerical rejection boundary, a required number of preserved anchors, or a statistical equivalence test. Thus we cannot claim that B/E passed a prespecified quantitative acceptance test. We can claim that they performed favourably, with explicit geographic qualifications, under the prespecified diagnostics. The discretion left in the broad/partial/poor judgement must be acknowledged in the article. No threshold is retroactively selected to certify these observed results.

The actual evidence—preserved aggregate meanings, modest aggregate geometric changes and concentrated country limitations—supports the qualified conclusion already reported. Negative transfer would have justified concluding that the frozen model was unsuitable or only partially useful for the intended scope, not retuning its centres on the holdout and calling the revised model externally validated. Any redesign now requires a new development cycle and genuinely new validation evidence. Objective 1 can be completed with a negative or mixed answer; completion is not synonymous with model acceptance.''')

if not any(c.cell_type=='markdown' and c.source.startswith('## 20a Discussion clarification') for c in notebook.cells):
    index=next(i for i,c in enumerate(notebook.cells) if c.cell_type=='markdown' and c.source.startswith('## 21 Country-specific'))
    notebook.cells[index:index]=[distance]
    index=next(i for i,c in enumerate(notebook.cells) if c.cell_type=='markdown' and c.source.startswith('## 22 Visual evidence'))
    notebook.cells[index:index]=[quality,concentration]
    index=next(i for i,c in enumerate(notebook.cells) if c.cell_type=='markdown' and c.source.startswith('## 24 Reproducible'))
    notebook.cells[index:index]=[rejection]

nbformat.write(notebook,path)
print('Saved held-out discussion in canonical v6; existing scientific outputs retained.')
