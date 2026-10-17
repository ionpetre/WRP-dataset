"""Place today's development extension in Week 5, retaining every saved output."""
from pathlib import Path
import copy
import hashlib
import json
import re
import shutil
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'weekly_notebooks'
ARCHIVE = FOLDER / 'earlier iterations/before_move_optimization_to_week05_20261016'
NAMES = ['week04_profile_robustness_and_selection.ipynb', 'week05_validate_frozen_profiles.ipynb']


def md(text):
    return nbf.v4.new_markdown_cell(text)


def renumber(cell, mapping):
    result = copy.deepcopy(cell)
    if result.cell_type == 'markdown':
        result.source = re.sub(r'(?m)^(#{2,3}) ([5-8])(?=[. ])',
            lambda m: m[1] + ' ' + str(mapping[int(m[2])]), result.source)
        result.source = re.sub(r'\bSection ([5-8])\b',
            lambda m: 'Section ' + str(mapping[int(m[1])]), result.source)
    if 'generated_source_sha256' in result.metadata:
        result.metadata.generated_source_sha256 = hashlib.sha256(result.source.encode()).hexdigest()
    return result


def main():
    if ARCHIVE.exists():
        raise SystemExit('The workflow has already been reorganized. Preserve subsequent user edits; do not repeat this migration.')
    before = [nbf.read(FOLDER / name, as_version=4) for name in NAMES]
    week4, week5 = copy.deepcopy(before)
    assert week4.cells[47].source.startswith('## 5. Subsequent development analysis')
    assert week5.cells[30].source.startswith('## 8. T5 freeze')
    ARCHIVE.mkdir()
    for name in NAMES:
        shutil.copy2(FOLDER / name, ARCHIVE / name)
    protected = [ROOT / 'course_artifacts/week05_t5_secondary_transfer/current_run.json',
                 ROOT / 'course_artifacts/week05_t5_secondary_transfer/832b01713bc6b240/frozen_model/freeze_seal.json',
                 ROOT / 'course_artifacts/week05_t5_secondary_transfer/832b01713bc6b240/transfer_complete.json',
                 FOLDER / 'week06_predicting_frozen_risk_profile_membership.ipynb']
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    # The original Week 4 analyses are unchanged. Move all subsequent search,
    # profile-level review and T5-selection cells, including their saved outputs.
    moved = copy.deepcopy(week4.cells[47:])
    week4.cells = week4.cells[:47]
    week4.cells.append(md('''## Continue in Week 5

Week 4 ends with its original robustness experiments and provisional B/E
selection. The later optimization of worry spacing $t$ and worry–harm allocation
$\\alpha$, fresh confirmation, profile-level review and T5 selection belong to
the [Week 5 workflow](week05_validate_frozen_profiles.ipynb), Sections 1–4.
T5 freezing and secondary transfer assessment follow there in Section 5.
No model, assignment or numerical result was changed by moving these sections.
'''))
    workflow = []
    for c in moved:
        if c.cell_type == 'markdown':
            c.source = c.source.replace('See Section 8 of the Week 5 notebook.', 'See the freezing and transfer assessment below.')
        c = renumber(c, {5: 1, 6: 2, 7: 3, 8: 4})
        c.metadata.week05_development_workflow = True
        workflow.append(c)
    workflow[0].source = workflow[0].source.replace(
        '## 1. Subsequent development analysis: tune worry coding and worry–harm allocation',
        '## 1. Development-only optimization of worry coding and worry–harm allocation')
    workflow[0].source = workflow[0].source.replace(
        'The six centered worry coordinates, reduced mean-worry coordinate, fourteen',
        'The six centred worry coordinates, reduced mean-worry coordinate, fourteen')
    workflow[0].metadata.generated_source_sha256 = hashlib.sha256(workflow[0].source.encode()).hexdigest()
    transfer = copy.deepcopy(week5.cells[30:])
    for i, c in enumerate(transfer):
        if c.cell_type == 'markdown':
            c.source = c.source.replace('See Week 4 Section 8 for the shallow-tree and model-selection evidence.',
                                         'See Section 4 above for the shallow-tree and model-selection evidence.')
            c.source = c.source.replace('Earlier sections replay the original B/E\nanalysis.',
                                         'Appendix A replays the original B/E\nanalysis.')
        transfer[i] = renumber(c, {8: 5, 5: 5, 6: 6, 7: 7})
    legacy = [copy.deepcopy(week5.cells[6])] + copy.deepcopy(week5.cells[10:30])
    for c in legacy:
        if c.cell_type == 'markdown':
            c.source = re.sub(r'(?m)^## ([1-7])\. ', r'### A.\1. ', c.source)
        c.metadata.historical_BE_appendix = True
    title = md('''# Week 5 — optimize, select, freeze and assess profile transfer

Week 4 supplies provisional modelling choices and robustness evidence. Week 5
may refine those choices on development countries before freezing the model.
Today's search for worry spacing $t$ and worry–harm allocation $\\alpha$ belongs
to this Week 5 development stage, not to the original Week 4 experiments.

Read the main workflow in this order:

1. Search a bounded grid of worry coding and worry–harm allocation for each k.
2. Extend the search adaptively and confirm a fixed shortlist with fresh
   development resamples. Apply the unchanged structural and ARI criteria.
3. Review original-response meanings, individual-profile recovery and the
   additional distinctions contributed by larger k.
4. Select T5 using that evidence and check shallow-tree/single-feature explanations.
5. Freeze the exact development specification, then assess unchanged held-out
   assignment, original meanings, prevalence and country-specific limitations.

**Data boundary:** parameter search and model selection use development responses
only. In the intended workflow, freeze before examining held-out responses.
In our actual research history, B/E had already been evaluated on the held-out
countries before today's extension. Therefore T5's assessment is secondary,
not a newly untouched external validation. Moving notebook sections does not
change that chronology or erase the earlier decisions.

The original B/E regional checks, transfer, country distances and handoff remain
in **Appendix A** as historical analyses; they are not T5 regional validation.
Earlier stage-specific conclusions are retained to show how the decision evolved;
the current primary-model decision is in Sections 4–5. Saved outputs are preserved,
and all expensive recomputation switches remain off.

Historical artifact and implementation paths may still contain `week04`.
They are deliberately not renamed: doing so could break fingerprints and cached
results. Their location is provenance, not the revised weekly teaching sequence.
''')
    setup = copy.deepcopy(week5.cells[1:6] + week5.cells[7:10])
    transform = copy.deepcopy(before[0].cells[10])
    transform.id = 'week5-shared-profile-transform'
    transform.execution_count = None
    transform.outputs = []
    week5.cells = [title] + setup + [md('''### Shared development geometry

Use the same complete-response feature transform as Week 4. The function takes
$t$ as `top`; tuning passes `top=1/q`. It estimates no parameters from held-out
responses. The declaration below does not fit a model.
'''), transform] + workflow + transfer + [md('''## Appendix A. Original B/E analyses — preserved historical record

These results precede the new parameter search in the actual research history.
They show regional fits, transfer, country comparisons and the original B/E
handoff. They are retained for comparison and reproducibility, not presented as
new T5 results. Existing maps and Week 6 still use that B/E handoff until a
separate migration is implemented.
''')] + legacy
    # Check that every moved code cell retained its exact source and outputs.
    original_moved = {c.id: c for c in before[0].cells[47:] + before[1].cells[30:] if c.cell_type == 'code'}
    destination = {c.id: c for c in week5.cells if c.cell_type == 'code'}
    for identifier, original in original_moved.items():
        assert destination[identifier].source == original.source
        assert destination[identifier].outputs == original.outputs
    assert week4.cells[:47] == before[0].cells[:47]
    assert len({c.id for c in week5.cells}) == len(week5.cells)
    for book in [week4, week5]:
        book.metadata.week05_workflow_reorganized = '2026-10-16'
        nbf.validate(book)
    for name, book in zip(NAMES, [week4, week5]):
        nbf.write(book, FOLDER / name)
    for filename, digest in hashes.items():
        assert hashlib.sha256((ROOT / filename).read_bytes()).hexdigest() == digest
    result = {'status': 'passed', 'original_week04_cells_unchanged': 47,
              'moved_code_cells_with_identical_sources_and_outputs': len(original_moved),
              'week05_main_sections': ['grid search', 'adaptive search', 'profile review', 'T5 selection and explanations', 'freeze and secondary transfer'],
              'original_BE_results': 'historical Appendix A', 'model_fits': 0,
              'protected_artifact_hashes': hashes, 'archive': str(ARCHIVE.relative_to(ROOT))}
    (ARCHIVE / 'reorganization_verification.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
