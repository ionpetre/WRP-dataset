"""Prepare a local aggregate-only GitHub update; never commit, push or refit."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import shutil
import numpy as np
import pandas as pd
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'github_publication'
BACKUP = ROOT / '.t5_publication_20261016/before'
BACKUP.mkdir(parents=True, exist_ok=True)
T5 = ROOT / json.loads((ROOT / 'course_artifacts/week05_t5_secondary_transfer/current_run.json').read_text())['output']
SPEC = json.loads((T5 / 'frozen_model/specification.json').read_text())
changed = set()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preserve(path):
    if path.exists():
        target = BACKUP / path.relative_to(PUBLIC)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(path, target)


def write(relative, text):
    path = PUBLIC / relative
    preserve(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    changed.add(str(relative))


def copy(source):
    target = PUBLIC / source.relative_to(ROOT)
    preserve(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    changed.add(str(target.relative_to(PUBLIC)))


def main():
    audit = PUBLIC / 'publication_audit.json'
    if audit.exists() and json.loads(audit.read_text()).get('primary_model') == 'T5':
        raise SystemExit('T5 publication already prepared. Use finish_t5_publication.py for verification; do not overwrite subsequent edits.')
    assert json.loads((T5 / 'verification.json').read_text())['status'] == 'passed'
    # Only aggregate tables/figures/protocols. Never copy label arrays, models in
    # executable formats, respondent IDs, sampling indices or assignment files.
    bases = ['week04_kmeans_parameter_optimization', 'week04_kmeans_adaptive_optimization',
             'week04_kmeans_profile_evaluation', 'week04_t5_shallow_explanations', 'week05_t5_secondary_transfer']
    for base in bases:
        pointer = ROOT / 'course_artifacts' / base / 'current_run.json'
        copy(pointer)
        folder = ROOT / json.loads(pointer.read_text())['output']
        for source in folder.iterdir():
            if source.suffix in {'.csv', '.json', '.png', '.txt'} and source.is_file():
                if source.suffix == '.csv':
                    columns = pd.read_csv(source, nrows=0).columns.str.lower()
                    assert not {'wpid_random', 'respondent_id', 'wgt'} & set(columns), source
                copy(source)
        if base == 'week05_t5_secondary_transfer':
            for source in (folder / 'frozen_model').iterdir():
                if source.suffix in {'.csv', '.json'}:
                    copy(source)
    for folder in ['.week04_parameter_search', '.week05_build']:
        for source in (ROOT / folder).glob('*.py'):
            # Publish scientific and reporting source, not private runtime caches.
            copy(source)
    notebooks = sorted((ROOT / 'weekly_notebooks').glob('week0*.ipynb'))
    for source in notebooks:
        book = nbf.read(source, as_version=4)
        for cell in book.cells:
            if cell.cell_type == 'code':
                cell.outputs = []
                cell.execution_count = None
            else:
                # Historical notebook archives stay private; avoid broken links.
                cell.source = re.sub(r'\[([^\]]+)\]\(<?earlier iterations/[^)]+\)',
                                     r'\1 (historical notebook retained in the course archive)', cell.source)
                cell.source = cell.source.replace('../course_artifacts/objective1_simplified_checks/week04_merge_report.json',
                                                   '../research/REPRODUCING.md')
        write(Path('weekly_notebooks') / source.name, nbf.writes(book))
    copy(ROOT / 'weekly_notebooks/requirements-objective1.txt')
    write('requirements.txt', (ROOT / 'weekly_notebooks/requirements-objective1.txt').read_text())
    model = {'context': SPEC['context'], 'feature_order': SPEC['feature_order'], 'transform_order': SPEC['transform_order'],
        'models': {'T5': {'spec': dict(SPEC['spec'], top=SPEC['spec']['t'], global_k=5),
            'centres': np.load(T5 / 'frozen_model/centres.npy').tolist(), 'profile_names': SPEC['profile_names'],
            'profile_distance_p95': SPEC['profile_distance_p95']}},
        'validation_status': 'secondary transfer assessment; these held-out countries were previously examined for B/E',
        'source_seal_sha256': digest(T5 / 'frozen_model/freeze_seal.json')}
    write('frozen_models/T5_models.json', json.dumps(model, indent=2) + '\n')
    # The existing public loader accepts an optional file; its default is now T5.
    loader = (PUBLIC / 'frozen_models/public_assignment.py').read_text()
    loader = loader.replace('def load_public_models(folder=None):', "def load_public_models(folder=None, filename='T5_models.json'):")
    loader = loader.replace("(folder/'models.json').read_text()", '(folder/filename).read_text()')
    write('frozen_models/public_assignment.py', loader)
    # Extend the existing profile explorer rather than introduce another interface.
    page = (PUBLIC / 'docs/index.html').read_text()
    match = re.search(r'(<script id="wrp-profile-data" type="application/json">)(.*?)(</script>)', page, re.S)
    payload = json.loads(match[2])
    profiles = pd.read_csv(T5 / 'frozen_model/development_original_category_profiles.csv').query("scope=='global'")
    shares = pd.read_csv(T5 / 'profile_transfer_summary.csv')
    anchors = pd.read_csv(T5 / 'frozen_model/development_defining_anchors.csv')
    original = []
    for c in range(5):
        table = profiles.loc[profiles.cluster.eq(c)].set_index(['feature', 'category'])
        val = lambda f, category, column='proportion': float(table.loc[(f, category), column])
        worry_features = SPEC['feature_order'][:6]
        harm_features = [SPEC['feature_order'][6:13], SPEC['feature_order'][13:]]
        summary = shares.loc[shares.cluster.eq(c)].iloc[0]
        original.append({'id': c, 'name': SPEC['profile_names'][str(c)],
            'share': summary.equal_country_weighted_share_development,
            'count': int(pd.read_csv(T5 / 'frozen_model/development_prevalence.csv').query("scope=='global' and cluster==@c").respondents.iloc[0]),
            'heldoutShare': summary.equal_country_weighted_share_heldout,
            'meanSemanticGap': summary.mean_feature_total_variation,
            'worry': [[val(f, a) for a in range(3)] for f in worry_features],
            'worryOutside': [[val(f, a, 'outside_proportion') for a in range(3)] for f in worry_features],
            'harm': [[val(f, 1) for f in block] for block in harm_features],
            'harmOutside': [[val(f, 1, 'outside_proportion') for f in block] for block in harm_features],
            'anchors': [{'feature': r.feature, 'category': int(r.category), 'inside': r.development_proportion,
                         'outside': r.development_outside_proportion} for r in anchors.loc[anchors.cluster.eq(c)].itertuples()]})
    stability = json.loads((T5 / 'frozen_model/development_stability.json').read_text())
    payload['models']['T5'] = {'k': 5, 'profiles': original, 'stability': [
        {'test': kind, 'median': stability[kind + '_median'], 'p10': stability[kind + '_p10'],
         'jaccardP10': .942722 if kind == 'countries' else .957384} for kind in ['respondents', 'countries']]}
    page = page[:match.start(2)] + json.dumps(payload, separators=(',', ':')) + page[match.end(2):]
    if 'data-model="T5"' not in page:
        page = page.replace('<div class="pf-controls" aria-label="Profile solution">',
            '<div class="pf-controls" aria-label="Profile solution"><button type="button" data-model="T5" aria-pressed="true">Five profiles · primary</button>')
        page = page.replace('data-model="B" aria-pressed="true">Four broad profiles', 'data-model="B" aria-pressed="false">Four profiles · historical')
        page = page.replace('>Eight more detailed profiles</button>', '>Eight profiles · historical</button>')
    page = page.replace("let model='B',selected=0;", "let model='T5',selected=0;")
    page = page.replace("get('pf-spec').textContent=model==='B'?", "get('pf-spec').textContent=model==='T5'?'Primary five-profile solution: optimized worry coding 0 / 1 / 2.400; worry allocation 58.4%. Held-out assessment is secondary, not untouched external confirmation.':model==='B'?")
    page = page.replace('How do the two solutions overlap?', 'Historical comparison: how do B4 and E8 overlap?')
    page = page.replace('Both solutions use equal-country-weighted', 'All displayed solutions use equal-country-weighted')
    page = page.replace("['B','E'].map(m=>data.models[m].stability", "['T5','B','E'].map(m=>data.models[m].stability")
    page = page.replace("(m==='B'?'Four profiles':'Eight profiles')", "(m==='T5'?'Five profiles · primary':m==='B'?'Four profiles · historical':'Eight profiles · historical')")
    page = page.replace('Explore two frozen descriptions of worry and reported harm.', 'Explore the primary five-profile model and the historical four- and eight-profile comparisons.')
    notice = '<p class="pf-muted" id="t5-validation-note">Current primary model: T5. All 15 defining contrasts retain their direction in aggregate held-out data. This is secondary assessment after earlier B/E validation; country-specific limitations remain. Shallow all-feature tree balanced accuracies at depths 1/2/3: 36.8% / 54.0% / 67.9%. <a href="https://github.com/ionpetre/WRP-dataset/blob/main/research/T5_RESULTS.md">T5 evidence and limitations</a>.</p>'
    if 'id="t5-validation-note"' not in page:
        page = page.replace('<p id="pf-spec" class="pf-muted"></p>', '<p id="pf-spec" class="pf-muted"></p>' + notice)
    write('docs/index.html', page)
    # Do not silently reinterpret B/E country metrics as distances under T5.
    for name in ['countries.html', 'country-income.html']:
        body = (PUBLIC / 'docs' / name).read_text()
        if 'id="historical-distance-note"' not in body:
            body = body.replace('</header>', '</header><p id="historical-distance-note" style="max-width:1120px;margin:1rem auto;padding:0 1rem">Country comparisons retain the historical B/E allocations and profile mixtures. They are not T5-specific distances. <a href="./index.html">Explore the primary five-profile model</a>.</p>', 1)
        write('docs/' + name, body)
    # Correct the headline without rewriting the historical evidence below it.
    readme = (PUBLIC / 'README.md').read_text()
    start = readme.index('**Current conclusion:**')
    end = readme.index('\n\n', start)
    readme = readme[:start] + '**Current conclusion (16 October 2026):** T5 is the primary five-profile description after development-only optimization of worry coding and worry–harm allocation. Its secondary held-out assessment supports broad aggregate transfer, with important country-specific limitations. B4/E8 remain historical benchmarks. See [T5 results and limitations](research/T5_RESULTS.md). Week 6 is an earlier B/E prediction draft, not a T5 evaluation.' + readme[end:]
    readme = readme.replace('inspect the four- and eight-profile solutions', 'inspect the primary five-profile model and historical four- and eight-profile solutions')
    a = readme.index('| 3 |'); b = readme.index('\n\nNotebook code', a)
    rows = [('3', 'Curate data and establish the baseline', 'week03_prepare_2023_data_and_kmeans.ipynb'),
            ('4', 'Compare encodings, block allocation and clustering methods', 'week04_profile_robustness_and_selection.ipynb'),
            ('5', 'Optimize t/alpha, confirm, review, select T5, freeze and assess transfer', 'week05_validate_frozen_profiles.ipynb'),
            ('6', 'Earlier B/E prediction draft; not yet migrated to T5', 'week06_predicting_frozen_risk_profile_membership.ipynb')]
    readme = readme[:a] + '\n'.join(f'| {w} | {purpose} | [Week {w}](weekly_notebooks/{name}) |' for w, purpose, name in rows) + readme[b:]
    readme = readme.replace('`frozen_models/` contains the final centres', '`frozen_models/T5_models.json` contains the primary model; `models.json` retains historical B/E. `frozen_models/` contains the stored centres')
    write('README.md', readme)
    t5path = str(T5.relative_to(ROOT))
    summary = f'''# T5: primary five-profile model — 16 October 2026

{(T5 / 'interpretation.txt').read_text()}

## Evidence and reuse

- [Week 5 workflow](../weekly_notebooks/week05_validate_frozen_profiles.ipynb): grid search, adaptive extension, fresh confirmation, profile review, selection, freeze and secondary transfer.
- [Exact readable model](../frozen_models/T5_models.json). Stored IDs are T5_C0 through T5_C4; never substitute them into B/E columns.
- [Transfer summary](../{t5path}/profile_transfer_summary.csv).
- [Original held-out categories](../{t5path}/heldout_original_category_profiles.csv).
- [Country quality and retention](../{t5path}/heldout_country_quality_and_retention.csv).
- [Profile-level country shifts and sample sizes](../{t5path}/heldout_profile_semantic_differences.csv).
- [Verification](../{t5path}/verification.json).

![Profile prevalence](../{t5path}/t5_prevalence_transfer.png)

![Original-response meaning](../{t5path}/t5_original_response_transfer.png)

The public package intentionally excludes respondent-level handoffs, label arrays,
sampling indices and fit caches. Model centres alone permit assignment of complete
responses when survey data are supplied separately; no all-country refit is needed.
Country maps still show explicitly labelled historical B/E comparisons. Week 6
and the manuscript have not been migrated in this publication update.
'''
    summary = summary.replace('The existing maps, manuscript, publication package and Week 6 have not yet been migrated.',
        'The publication profile explorer now defaults to T5. Country-distance pages retain historical B/E metrics, explicitly labelled; the manuscript and Week 6 remain unchanged.')
    summary = summary.replace('The existing maps, manuscript, publication package and Week 6 have not yet been migrated.', '')
    write('research/T5_RESULTS.md', summary)
    for name in ['RESULTS.md', 'METHODS.md', 'REPRODUCING.md', 'OBJECTIVES.md']:
        body = (PUBLIC / 'research' / name).read_text()
        if '## Update: primary T5 model' not in body:
            first, rest = body.split('\n', 1)
            body = first + '\n\n## Update: primary T5 model\n\nThe 16 October development extension selects T5 as the primary model. See [T5 evidence, parameters and secondary-validation limitations](T5_RESULTS.md). B4/E8 findings below remain historical evidence, not the current primary-model decision.\n' + rest
        for old_name, new_name in [('week03_prepare_the_2023_analysis_data_v16.ipynb', rows[0][2]),
            ('week05_regional_validation_and_objective1_finalization.ipynb', rows[2][2])]:
            body = body.replace(old_name, new_name)
        if name == 'REPRODUCING.md':
            body += '\n\nFor primary T5 assignments, `load_public_models()` defaults to `T5_models.json`. Use `load_public_models(filename="models.json")` for historical B/E. Public notebooks have outputs cleared and require private data/caches for full replay; no claim of zero-input reproduction is made.\n'
        write('research/' + name, body)
    doc = (PUBLIC / 'docs/README.md').read_text()
    write('docs/README.md', '## 16 October update\n\nThe profile explorer now defaults to primary T5. B4/E8 remain selectable historical models. Country and income maps retain explicitly labelled historical B/E distances; no T5 country-distance analysis is implied. See [T5 evidence](../research/T5_RESULTS.md).\n\n' + doc)
    save_manifest(notebooks)
    print('Prepared', len(changed), 'updated/new local publication files; no push, commit or refits.')


def save_manifest(notebooks):
    path = PUBLIC / 'publication_manifest.json'
    preserve(path)
    manifest = json.loads(path.read_text())
    records = {r['path']: r for r in manifest['source_records']}
    for relative in changed:
        p = PUBLIC / relative; source = ROOT / relative
        records[relative] = {'path': relative, 'source': relative if source.exists() else 'publication-source:' + relative,
            'source_sha256': digest(source) if source.exists() else digest(p), 'publication_sha256': digest(p),
            'bytes': p.stat().st_size, 'modified_for_publication': source.exists() and digest(source) != digest(p)}
    manifest.update(last_updated='2026-10-16', notebooks=[p.name for p in notebooks], source_records=list(records.values()),
        primary_model='T5', T5_context=SPEC['context'], secondary_transfer=True,
        respondent_data_published=False, country_maps='historical B/E metrics, labelled',
        Week6='historical B/E draft; not T5 results', changed_paths=sorted(changed))
    path.write_text(json.dumps(manifest, indent=2) + '\n')
    inventory = [{'path': str(p.relative_to(PUBLIC)), 'bytes': p.stat().st_size, 'sha256': digest(p)}
        for p in PUBLIC.rglob('*') if p.is_file() and '.git' not in p.relative_to(PUBLIC).parts
        and p.name not in {'publication_file_inventory.json', 'publication_audit.json'}]
    write('publication_file_inventory.json', json.dumps(inventory, indent=2) + '\n')


if __name__ == '__main__':
    main()
