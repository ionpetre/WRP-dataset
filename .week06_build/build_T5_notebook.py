"""Build a readable, self-contained Week 6 notebook from the tested T5 code."""
from pathlib import Path
import ast
import hashlib
import nbformat

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / '.week06_build/week06_t5_core.py').read_text()
tree = ast.parse(source)
functions = {node.name: ast.get_source_segment(source, node)
             for node in tree.body if isinstance(node, ast.FunctionDef)}
header = source[:source.index('def timestamp')]
cells = []
def md(s): cells.append(nbformat.v4.new_markdown_cell(s))
def code(s): cells.append(nbformat.v4.new_code_cell(s))
def definitions(*names): code('\n\n'.join(functions[name] for name in names))

md('''# Week 6 — predicting T5 profile membership

## Objective 2

**Question:** how well can background characteristics predict membership in the five frozen T5 profiles, including in countries outside classifier training?

The target is T5_C0–T5_C4 from Objective 1. We do not fit new clusters, reorder profiles, fill missing labels, or include worry/harm responses as predictors. Eligible respondents are the same complete cases used in the frozen assignment registry.

Follow the steps in order: verify labels; define predictors; fit preprocessing inside country folds; compare classifiers; select and freeze the classifier; interpret development associations; evaluate held-out prediction and errors.

This first comparison uses a majority baseline, multinomial logistic regression and a random forest. Settings are fixed, not tuned. Prediction of this descriptive classification does not establish causation. Weak prediction from background variables does not invalidate the clustering itself.''')
md('''## 1. Setup and fixed design

Run from the course folder or `weekly_notebooks`, using the same scientific environment as Weeks 3–5. Code is shown in small groups beside the analysis it supports. The complete implementation is embedded; no private helper-module import is required.

Execution switches are off for ordinary reading and replay of saved fits. Deliberately enable them only for a missing computation. Existing B/E supervised results are preserved in their original result folder and earlier notebook, not presented as T5 results.''')
code('''from pathlib import Path
from IPython.display import display, Image

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents]
            if (p / 'course_artifacts/week03_country_split.csv').exists())
RUN_DEVELOPMENT = False
RUN_INTERPRETATION = False
RUN_HELDOUT = False
''' + 'IMPLEMENTATION_SHA256 = ' + repr(hashlib.sha256(source.encode()).hexdigest()) + '\n' + header)
md('''### Input and cache checks

Saved fits belong to the recorded data, T5 assignment, runtime and model-design fingerprint. A changed input uses a different result folder. Executable model caches are loaded only from this trusted course workspace. These checks prevent accidentally reading a B/E fit as a T5 fit.''')
definitions('timestamp', 'file_hash', 'json_write', 'country_weights', 'initialise')
code('''CONTEXT, OUTPUT = initialise(ROOT, IMPLEMENTATION_SHA256)
display(pd.read_csv(OUTPUT / 'predictor_manifest.csv')[
    ['variable', 'label', 'block', 'modelling_type', 'missing_codes']])
print('Results:', OUTPUT.relative_to(ROOT))''')
md('''## 2. Join the fixed T5 target

**Purpose:** link the exact saved labels to the correct respondents, never by row order. Check ID, country, original split and survey-weight agreement before selecting complete cases.

There are 109,488 eligible development respondents in 113 countries and 27,972 eligible held-out respondents in 29 countries. Keep exclusions in an audit, but do not impute their labels. This workflow describes the eligible complete-case cohort, not all survey respondents.''')
definitions('load_cohort')
code('''development, eligibility = load_cohort(ROOT, CONTEXT, 'train')
eligibility.to_csv(OUTPUT / 'development_target_eligibility.csv', index=False)
display(eligibility)
print('Development:', len(development), 'respondents,', development.COUNTRY_ISO3.nunique(), 'countries')
display(development.groupby(['T5_profile_id']).size().rename('respondents'))''')
md('''## 3. Define background predictors

**Purpose:** predict membership without reconstructing the rule that created it. Use these 18 existing variables:

- Age, gender, education, urban/rural residence, employment, income quintile, household size, children and marital status.
- Household financial buffer, perceived government/neighbour care and five discrimination questions.
- Measured country-income category at fieldwork.

The explicit predictor list excludes every worry/harm item and derived burden score, respondent/country IDs, region labels, profile shares, centre distances and assignment margins. Country identifies validation groups and weights, not a model feature.

Recoding below checks allowed survey codes without fitting anything. “Not applicable” (97) in discrimination and “not classified” (9) in country income remain distinct categories. Other documented special responses become missing. Unasked follow-ups must not be interpreted as “no”.''')
definitions('prepare_predictors', 'predictor_missingness')
code('''X_development = prepare_predictors(development)
missingness = predictor_missingness(development, X_development, 'development')
missingness.to_csv(OUTPUT / 'development_predictor_missingness.csv', index=False)
display(missingness.sort_values('equal_country_missing_fraction', ascending=False).round(4))''')
md('''## 4. Fit preprocessing in training countries only

**Purpose:** keep validation-country responses out of preprocessing estimation. Impute age with the training equal-country-weighted median, scale it with the training weighted mean/SD, and add an age-missing indicator. One-hot encode other variables, including an explicit missing category. Unseen evaluation categories are ignored rather than used to refit the encoder.

Some questions are absent in entire countries. Missing categories may carry survey-design information. Country-grouped validation does not make that a causal relationship.''')
definitions('fit_preprocessor', 'transform_predictors')
md('''## 5. Declare the three comparison models

**Purpose:** start with a clear baseline and standard classifiers. The baseline always predicts the largest weighted training profile. Logistic regression uses L2 regularization, C=1, lbfgs and at most 2,000 iterations. The random forest uses 120 trees, depth at most 14 and at least 50 records per leaf. There is no hyperparameter search in this first comparison.

Training weights give each training country equal total influence while preserving relative WGT within country. Scale fitting weights to mean one, so C has a defined convention. Recompute evaluation weights separately within each evaluation population. Do not add class balancing without recording a new design.''')
definitions('build_model')
md('''### Fit or reuse a verified model

This helper saves preprocessing and classifier together and records warnings. It does not change the model declaration above. A missing cache cannot trigger a new fit while the switch is off.''')
definitions('fit_or_load', 'probabilities')
md('''### Define prediction scores

Balanced accuracy is mean recall over the five profiles. Macro-F1 is mean per-profile F1, with F1 the harmonic mean of precision and recall. Ordinary accuracy can look acceptable while smaller profiles are rarely predicted. Report all three and the full weighted confusion matrix. A constant-label baseline has balanced accuracy 0.20.''')
definitions('metrics', 'save_confusion')
md('''## 6. Compare models using country-grouped cross-validation

**Purpose:** predict respondents from countries excluded from classifier training. Use the same five development-country folds for all models. Fit preprocessing and model on four groups; evaluate on the fifth; repeat for all five groups. No country appears in both parts of a fold.

Use mean fold macro-F1 as the primary selection criterion; balanced accuracy and per-profile recall are supporting diagnostics. If tuning is later added, it needs a separate country-grouped search inside each training fold. The T5 labels themselves were developed using all development countries, so this evaluates prediction of a fixed taxonomy, not fully nested profile discovery.''')
definitions('development_cv')
code('''CV_SUMMARY, FOLDS = development_cv(development, X_development, CONTEXT, OUTPUT, RUN_DEVELOPMENT)
display(CV_SUMMARY.round(4))
display(pd.read_csv(OUTPUT / 'development_per_profile_scores.csv').round(4))
display(pd.read_csv(OUTPUT / 'fit_warnings_and_times.csv')[
    ['classifier', 'fold', 'seconds', 'convergence_warning', 'warnings']])''')
md('''### Development decision

Logistic regression has mean macro-F1 0.217, compared with 0.186 for the forest and 0.106 for the majority baseline. Their balanced accuracies are 0.255, 0.244 and 0.200. Select logistic regression using the stated primary metric, not whichever secondary score looks best. All 15 development fits completed without convergence warnings.''')
md('''## 7. Freeze the classifier before held-out prediction

**Purpose:** finish model selection using development results only. Fit the chosen pipeline on all eligible development respondents and save it, alongside the training-majority comparator. Exact development-score ties prefer logistic regression, then the forest, then the baseline. Freeze model hashes, settings and the choice before predicting held-out respondents. The clustering itself stays unchanged.''')
definitions('freeze_supervised')
code('''SUPERVISED_SEAL = freeze_supervised(development, X_development, CV_SUMMARY, CONTEXT, OUTPUT, RUN_DEVELOPMENT)
display(pd.DataFrame(SUPERVISED_SEAL['selection']).T)
print('Classifier frozen at:', SUPERVISED_SEAL['frozen_at_utc'])''')
md('''## 8. Inspect development predictive associations

**Purpose:** ask which background blocks the selected classifier uses. For each validation fold, jointly shuffle each individual-level block within country three times. For country income, shuffle whole-country income categories across validation countries. Measure the drop in macro-F1 without refitting.

These perturbations answer different questions. Do not rank their values as causal effects. Correlated variables may substitute for each other. The country-income perturbation is not directly comparable to a within-country individual-block shuffle.''')
definitions('block_permutation')
code('''PERMUTATION = block_permutation(development, X_development, FOLDS, SUPERVISED_SEAL, CONTEXT, OUTPUT, RUN_INTERPRETATION)
display(pd.read_csv(OUTPUT / 'development_block_permutation_summary.csv').round(4))''')
md('''## 9. Evaluate held-out prediction once

**Purpose:** apply the saved classifier and preprocessing unchanged to the 29 held-out countries. These countries are outside supervised model selection but were used in Objective 1 transfer assessment; this is not a new untouched validation of profile discovery. Do not retune after this step.

Report the same metrics for the selected classifier and training-majority comparator. Country-bootstrap intervals keep models and predictions fixed. They describe variation over the observed countries, not all uncertainty in the survey, missingness or fitted models.''')
definitions('heldout_test')
code('''HELDOUT = heldout_test(ROOT, CONTEXT, OUTPUT, SUPERVISED_SEAL, RUN_HELDOUT)
display(HELDOUT.round(4))
display(pd.read_csv(OUTPUT / 'heldout_country_bootstrap_intervals.csv').round(4))
profiles = pd.read_csv(OUTPUT / 'heldout_per_profile_scores.csv')
display(profiles.loc[profiles.classifier.eq('logistic')].round(4))''')
md('''## 10. Examine profile and country errors

**Purpose:** identify which groups the classifier misses. Inspect the confusion matrix, predicted profile shares and errors in every held-out country. Country-level balanced accuracy below averages over profiles actually present in that country; it is labelled separately from the five-profile aggregate metric. Small country/profile cells are uncertain.

Compare predictor missingness between development and held-out countries before attributing differences to social conditions.''')
code('''country_errors = pd.read_csv(OUTPUT / 'heldout_country_scores.csv')
display(country_errors.loc[country_errors.classifier.eq('logistic')].sort_values(
    'balanced_accuracy_present_profiles').round(4))
display(pd.read_csv(OUTPUT / 'heldout_predictor_missingness.csv').round(4))''')
definitions('make_figures')
code('''FIGURES = make_figures(OUTPUT)
for filename in ['development_classifier_comparison.png', 'T5_heldout_confusion.png',
                 'development_predictor_block_importance.png']:
    display(Image(filename=str(FIGURES / filename)))''')
md('''## Results and limits of this first T5 comparison

The held-out logistic model has balanced accuracy **0.261**, macro-F1 **0.223** and ordinary accuracy **0.376**. The majority baseline gives **0.200**, **0.106** and **0.359**. The classifier improves on a simple baseline but has weak individual discrimination.

It predicts the lower-worry profile for **77.5%** of weighted held-out respondents, although that profile contains **35.9%**. Recall is **87.6%** for lower worry, **24.8%** for broad known-person harm, **4.9%** for crime/weather worry, **4.9%** for mental-health/traffic/weather worry and **8.2%** for water/food worry. Good recovery of the largest group hides poor recovery of the others. This is not a strong five-profile classifier.

The selected-model held-out country-bootstrap intervals are approximately 0.237–0.283 for balanced accuracy and 0.195–0.246 for macro-F1. These are conditional country-variation intervals, not paired significance tests or full model-selection uncertainty.

Development permutations show limited predictive information: discrimination drops macro-F1 by about 0.016, demographics/household by 0.006, support by 0.005 and financial buffer by 0.002. Across-country income reassignment drops it by 0.022 under a different perturbation. These are predictive associations, not causes or comparable effect sizes.

**Conclusion:** retain the frozen T5 clustering as the descriptive target. These background variables do not accurately recover its five groups with the tested classifiers. Further development-only checks may examine missing-question sensitivity or a justified predictor/tuning change. This held-out result must not be used to select such changes and then reported as untouched confirmation. Objective 3's external-outcome comparison is separate and is not completed here.''')

nb = nbformat.v4.new_notebook(cells=cells, metadata={
    'kernelspec': {'display_name':'Python 3', 'language':'python', 'name':'python3'},
    'language_info': {'name':'python', 'version':'3.11'}})
nbformat.validate(nb)
nbformat.write(nb, ROOT / 'weekly_notebooks/week06_predicting_frozen_risk_profile_membership.ipynb')
print('Week 6:', len(cells), 'cells, T5 only')
