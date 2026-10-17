"""Build the profile explorer from frozen aggregate results only; no fits or microdata."""
from pathlib import Path
import csv
import hashlib
import json

FREEZE='course_artifacts/week05_frozen_objective1_v1/123d248adda6115f'
TRANSFER='course_artifacts/week05_heldout_transfer_v1/123d248adda6115f'
OVERLAP='course_artifacts/week04_other_algorithms_v1/retained_membership_overlaps.csv'
DOMAINS=['food','water','crime','severe_weather','traffic','mental_health','work']

def export_profiles(root):
    root=Path(root).resolve()
    public=root if (root/'docs').is_dir() else root/'github_publication'
    build=root/'.week05_build'
    sources={}
    def read(relative):
        path=public/relative
        sources[relative]=hashlib.sha256(path.read_bytes()).hexdigest()
        with path.open(newline='') as stream:
            return list(csv.DictReader(stream))
    definitions=read(FREEZE+'/profile_definitions.csv')
    original=read(FREEZE+'/development_original_category_profiles.csv')
    anchors=read(FREEZE+'/development_defining_anchors.csv')
    stability=read(FREEZE+'/development_stability.csv')
    heldout=read(TRANSFER+'/heldout_vs_development_prevalence.csv')
    semantics=read(TRANSFER+'/heldout_profile_semantic_TV.csv')
    links=[r for r in read(OVERLAP) if r['coarse']=='B' and r['fine']=='E']
    payload={'context':'123d248adda6115f','domains':DOMAINS,'models':{},'links':[], 'sources':sources}
    for model,k in [('B',4),('E',8)]:
        profiles=[]
        for cluster in range(k):
            matches=lambda rows:[r for r in rows if r['candidate']==model and int(r['cluster'])==cluster]
            definition=matches(definitions)[0]
            values={(r['feature'],int(r['category'])):r for r in matches(original)}
            def value(feature,category,key='proportion'):
                return float(values[(feature,category)][key])
            worry=[[value('worry_'+domain,c) for c in range(3)] for domain in DOMAINS[:6]]
            outside=[[value('worry_'+domain,c,'outside_proportion') for c in range(3)] for domain in DOMAINS[:6]]
            assert all(abs(sum(row)-1)<1e-10 for row in worry+outside)
            harm=[[value('harm_'+domain+'_'+kind,1) for domain in DOMAINS] for kind in ['personal','known_person']]
            harm_out=[[value('harm_'+domain+'_'+kind,1,'outside_proportion') for domain in DOMAINS] for kind in ['personal','known_person']]
            transfer=matches(heldout)[0]
            semantic=[r for r in matches(semantics) if r['scope']=='global'][0]
            profiles.append({'id':cluster,'name':definition['profile_name'],
                'share':float(definition['development_share']),'count':int(definition['development_respondents']),
                'heldoutShare':float(transfer['equal_country_weighted_share_heldout']),
                'meanSemanticGap':float(semantic['mean_feature_TV']),
                'worry':worry,'worryOutside':outside,'harm':harm,'harmOutside':harm_out,
                'anchors':[{'feature':r['feature'],'category':int(r['category']),
                    'inside':float(r['development_proportion']),'outside':float(r['development_outside_proportion'])} for r in matches(anchors)]})
        assert abs(sum(p['share'] for p in profiles)-1)<1e-10
        payload['models'][model]={'k':k,'profiles':profiles,
            'stability':[{'test':r['experiment'],'median':float(r['median_pairwise']),
                'p10':float(r['p10_pairwise']),'jaccardP10':float(r['p10_cluster_jaccard'])} for r in stability if r['candidate']==model]}
    assert len(links)==32
    for r in links:
        payload['links'].append([int(r['coarse_cluster']),int(r['fine_cluster']),float(r['joint_weight'])])
    for model,column in [('B',0),('E',1)]:
        for p in payload['models'][model]['profiles']:
            marginal=sum(r[2] for r in payload['links'] if r[column]==p['id'])
            assert abs(marginal-p['share'])<1e-10, 'Overlap labels or reference population differ from frozen profiles'
    from t5_profile_payload import add_t5
    payload=add_t5(payload,public)
    fragment=(build/'response-profiles-template.html').read_text().replace('__WRP_PROFILE_DATA__',json.dumps(payload,separators=(',',':')))
    assert len(fragment.encode())<1_000_000
    header=(build/'research-page-header.html').read_text()
    replacements={'__PAGE_TITLE__':'What do the response profiles mean?',
        '__PAGE_DESCRIPTION__':'Explore the primary five-profile model and historical four- and eight-profile comparisons. The clusters group respondents—not countries.',
        '__PROFILE_CLASS__':'is-current','__PROFILE_CURRENT__':'aria-current="page"',
        '__COUNTRY_CLASS__':'','__COUNTRY_CURRENT__':'','__INCOME_CLASS__':'','__INCOME_CURRENT__':''}
    for key,value in replacements.items():header=header.replace(key,value)
    css=(build/'research-page-style.css').read_text()
    page='<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Response profiles · World Risk Poll</title><style id="wrp-research-page-style">'+css+'</style></head><body>'+header+fragment+'</body></html>\n'
    (public/'docs/index.html').write_text(page)
    (public/'docs/response-profiles-fragment.html').write_text(fragment)
    return payload

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
    args=parser.parse_args()
    export_profiles(args.root)
    print('Prepared profile explorer from frozen aggregate tables. No model fits.')
