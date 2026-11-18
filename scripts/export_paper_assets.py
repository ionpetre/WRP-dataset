"""Validate final-model aggregates and rebuild offline browser assets. No fitting."""
from pathlib import Path
import hashlib,json,math,csv
ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'paper/assets';OUT=ROOT/'docs/data'
PRIMARY=json.loads((A/'primary_models.json').read_text())

def validate(data,country):
    expected={f'full_{y}' for y in [2021,2023,2025]}|{f'common_worry_{y}' for y in [2019,2021,2023,2025]}
    assert set(data['models'])==set(country['models'])==expected
    for key,m in data['models'].items():
        assert m['trial']==PRIMARY[m['family']][str(m['year'])]
        assert m['k']==(7 if m['family']=='full' else 3)
        assert not m['heldoutAssessed']
        assert math.isclose(sum(c['share'] for c in m['clusters']),1,abs_tol=1e-12)
        for c in m['clusters']:
            assert c['rule']['cost']<=3 and c['rule']['precision']>=.8-1e-12
            assert all(math.isclose(sum(row),1,abs_tol=1e-12) for row in c['worry'])
        national=country['models'][key]
        assert national['scope']=='all_surveyed'
        assert len(national['countries'])==national['surveyCountryCount']
        assert {c['iso'] for c in national['countries']}=={c['iso'] for c in national['surveyCountries']}
        assert not national['countriesWithoutCompleteAnswers']
        assert national['trial']==m['trial'] and national['k']==m['k']
        assert sum(c['split']=='train' for c in national['countries'])==m['countries']
        assert all(math.isclose(sum(row),1,abs_tol=1e-12) for row in national['shares'])
    for family,values in data['shares'].items():
        for year,row in values.items():
            assert len(row)==(7 if family=='full' else 3)
            assert math.isclose(sum(row),1,abs_tol=1e-12)
    for rows in data['overlap'].values():
        assert all(math.isclose(sum(row),1,abs_tol=1e-12) for row in rows)

def main():
    data=json.loads((A/'website_aggregates.json').read_text());country=json.loads((A/'country_aggregates_all_surveyed.json').read_text())
    validate(data,country)
    # Overview scores use its single 2025 common-country reporting population.
    score_file=ROOT/'paper/results/unchanged_rule_transfer.csv'
    selected=[r for r in csv.DictReader(score_file.open()) if r['family']=='full'
        and r['target_wave']=='2025' and r['evaluation_wave']=='2025']
    assert len(selected)==7 and {int(r['anchor_cluster']) for r in selected}==set(range(7))
    data['overviewRuleScores']={str(int(r['anchor_cluster'])):
        dict(precision=float(r['precision']),coverage=float(r['coverage'])) for r in selected}
    data['overviewEvaluation']=dict(year=2025,countries=92,respondents=90395)
    manifest=json.loads((A/'manifest.json').read_text())
    for name,digest in manifest['files_sha256'].items():assert hashlib.sha256((A/name).read_bytes()).hexdigest()==digest,name
    sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [A/'manifest.json',A/'models.json',A/'primary_models.json',A/'website_aggregates.json',A/'country_aggregates_all_surveyed.json',score_file]}
    provenance=dict(exported='2026-11-18',aggregate_only=True,scientific_refits=0,heldout_reassessment=False,all_surveyed_countries_displayed=True,grey_means="Not surveyed in selected WRP wave",
        principal_full_clusters=7,principal_later_worry_clusters=3,no_shared_2019_partition_established=True,
        source_files_sha256=sources)
    OUT.mkdir(exist_ok=True)
    for stem,payload,variable in [('paper-results',data,'WRP_WAVE_DATA'),('paper-country-results',country,'WRP_COUNTRY_WAVES')]:
        (OUT/(stem+'.json')).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
        (OUT/(stem+'.sources.json')).write_text(json.dumps(provenance,indent=2)+'\n')
        text=json.dumps(payload,separators=(',',':'),ensure_ascii=False).replace('<','\\u003c')
        (OUT/(stem+'.js')).write_text('/* World Risk Poll aggregate results. See paper/wrp_cross_wave_clustering.ipynb. */\nwindow.'+variable+' = '+text+';\n')
    print('Verified the seven clustering models and all surveyed countries and rebuilt both browser assets.')
if __name__=='__main__':main()
