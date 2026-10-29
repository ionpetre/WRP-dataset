"""Curate saved country aggregates for the website. Never reads respondent rows.

Without --source-root, validate public JSON and regenerate its offline script.
With it, read the pinned country-analysis index and checked aggregate outputs.
The complete analytical implementation is in each wave's research notebook.
"""
from pathlib import Path
import argparse, hashlib, json, math

REPO=Path(__file__).resolve().parents[1]
INDEX='course_artifacts/wrp_country_maps_all_waves/index.json'
KEYS={f'full_{y}' for y in [2021,2023,2025]}|{f'common_worry_{y}' for y in [2019,2021,2023,2025]}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def validate(data):
    assert set(data['models'])==KEYS and data['benchmarkYear']==2025
    for key,m in data['models'].items():
        n=len(m['countries']);nw=len(m['worryDomains']);k=m['k']
        assert len({c['iso'] for c in m['countries']})==n
        assert len(m['shares'])==len(m['probabilities'])==n
        for c,p,q in zip(m['countries'],m['shares'],m['probabilities']):
            assert set(c)=={'iso','name','regionId','region','income','split','respondents','totalRespondents','retention','point'}
            assert c['respondents']>0 and c['totalRespondents']>=c['respondents']
            assert len(p)==k and math.isclose(sum(p),1,abs_tol=1e-12)
            assert len(q)==3*nw+(14 if m['family']=='full' else 0)
            assert all(math.isfinite(v) and 0<=v<=1 for v in p+q)
            assert all(math.isclose(sum(q[3*j:3*j+3]),1,abs_tol=1e-12) for j in range(nw))
        assert len(m['embedding']['coordinates'])==n
        for metric,value in data['references'][m['family']].items():assert 0<value<=1
    assert data['models']['full_2023']['original2023Verified']

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-root',type=Path);args=parser.parse_args()
    out=REPO/'docs/data';out.mkdir(exist_ok=True)
    if args.source_root:
        root=args.source_root.resolve();index=json.loads((root/INDEX).read_text());models={};sources={INDEX:sha(root/INDEX)}
        for key,folder in index.items():
            p=root/folder;manifest=json.loads((p/'manifest.json').read_text());payload=p/'country_aggregates.json'
            assert sha(payload)==manifest['files_sha256']['country_aggregates.json']
            sources[str((p/'manifest.json').relative_to(root))]=sha(p/'manifest.json')
            sources[str(payload.relative_to(root))]=sha(payload)
            models[key]=json.loads(payload.read_text())
        references={family:{metric:summary['median'] for metric,summary in models[family+'_2025']['summaries']['all'].items() if metric!='comparison'} for family in ['full','common_worry']}
        data=dict(schemaVersion=1,benchmarkYear=2025,referenceDefinition='Median over distinct unordered pairs in the 2025 all-country eligible cohort; fixed within each question family and distance/component.',references=references,models=models)
        validate(data)
        (out/'country-waves.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        (out/'country-waves.sources.json').write_text(json.dumps(dict(exported='2026-10-29',aggregate_only=True,model_refits=0,heldout_reassessment=False,source_files_sha256=sources),indent=2)+'\n')
    else:
        data=json.loads((out/'country-waves.json').read_text());validate(data)
    (out/'country-waves.js').write_text('/* Country aggregates only. See scripts/export_country_wave_data.py. */\nwindow.WRP_COUNTRY_WAVES = '+json.dumps(data,separators=(',',':'),ensure_ascii=False).replace('<','\\u003c')+';\n')
    print('Verified seven country analyses; wrote aggregate browser asset.')

if __name__=='__main__':main()
