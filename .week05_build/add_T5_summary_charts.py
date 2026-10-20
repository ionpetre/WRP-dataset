"""Add the three WARM-5 slide charts to the profile page, using saved aggregates only.

Run from any directory. No model fitting, survey data or external downloads.
The page and its editable fragment receive the same self-contained section.
"""
from pathlib import Path
import csv
import html
import json
import re

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs/index.html"
REGIONS = ROOT / "course_artifacts/week05_T5_completion/70ee2f67e95369c5/T5_fixed_profiles_by_split_and_region.csv"
START = "<!-- WARM-5 summary charts: start -->"
END = "<!-- WARM-5 summary charts: end -->"


def percent(value):
    return f"{100 * value:.1f}%"


def table(headers, rows, caption):
    return ('<details class="sc-data"><summary>Read the exact percentages</summary>'
            '<div class="sc-table-scroll"><table><caption>' + html.escape(caption) + '</caption>'
            '<thead><tr>' + ''.join('<th scope="col">' + html.escape(h) + '</th>' for h in headers)
            + '</tr></thead><tbody>'
            + ''.join('<tr><th scope="row">' + html.escape(row[0]) + '</th>'
                      + ''.join('<td>' + html.escape(v) + '</td>' for v in row[1:]) + '</tr>' for row in rows)
            + '</tbody></table></div></details>')


def build():
    document = PAGE.read_text()
    data = json.loads(re.search(r'<script id="wrp-profile-data" type="application/json">(.*?)</script>', document, re.S)[1])
    profiles = data['models']['T5']['profiles']
    assert [p['id'] for p in profiles] == list(range(5))
    with REGIONS.open() as stream:
        rows = list(csv.DictReader(stream))
    regions = {}
    for row in rows:
        if row['split'] == 'all' and row['area'] != 'global':
            area = int(row['area'])
            region = regions.setdefault(area, {'name': row['region_name'], 'countries': int(row['countries']), 'values': [None] * 5})
            region['values'][int(row['cluster'])] = float(row['equal_country_share'])
    assert len(regions) == 15
    assert all(abs(sum(r['values']) - 1) < 1e-12 for r in regions.values())

    region_rows = []
    region_table = []
    for area, region in sorted(regions.items(), reverse=True):
        name = html.escape(region['name'])
        segments = []
        for i, value in enumerate(region['values']):
            label = f"{region['name']}: profile {i + 1}, {profiles[i]['name']}, {percent(value)}"
            segments.append(f'<span class="sc-segment sc-profile-{i}" style="width:{100 * value:.12f}%" title="{html.escape(label, quote=True)}"></span>')
        summary = '; '.join(f"profile {i + 1}: {percent(v)}" for i, v in enumerate(region['values']))
        region_rows.append(f'<div class="sc-region-row"><span class="sc-region-label">{name}</span><div class="sc-region-stack" role="img" aria-label="{name}: {summary}">{"".join(segments)}</div></div>')
        region_table.append([region['name'] + f" ({region['countries']} countries)", *[percent(v) for v in region['values']]])

    legend = '<div class="sc-profile-legend">' + ''.join(
        f'<span><i class="sc-profile-{i}"></i>{i + 1} · {html.escape(p["name"])}</span>' for i, p in enumerate(profiles)) + '</div>'
    transfer = [[p['share'], p['heldoutShare']] for p in profiles]
    harm = [[sum(p['harm'][j]) / 7 for j in range(2)] for p in profiles]
    chart_data = json.dumps({'transfer': transfer, 'harm': harm}, separators=(',', ':'))
    block = START + '''
<style>
#wrp-profiles .sc-section{margin:1.8rem 0 2rem;padding-bottom:1.5rem;border-bottom:1px solid var(--page-line)}
#wrp-profiles .sc-section h2{margin-top:0}
#wrp-profiles details:not([open])>:not(summary){display:none}
#wrp-profiles .pf-card,#wrp-profiles .pf-key{overflow-wrap:anywhere}
#wrp-profiles .sc-profile-legend,#wrp-profiles .sc-pair-legend{display:flex;flex-wrap:wrap;gap:.45rem 1.1rem;font-size:.85rem;margin:.75rem 0 1rem}
#wrp-profiles .sc-profile-legend i,#wrp-profiles .sc-pair-legend i{display:inline-block;width:.75rem;height:.75rem;margin-right:.35rem;vertical-align:baseline;border-radius:2px}
#wrp-profiles .sc-profile-0{background:#637485}
#wrp-profiles .sc-profile-1{background:#e66e57}
#wrp-profiles .sc-profile-2{background:#087e8b}
#wrp-profiles .sc-profile-3{background:#7765a2}
#wrp-profiles .sc-profile-4{background:#daa638}
#wrp-profiles .sc-region-row{display:grid;grid-template-columns:15rem minmax(0,1fr);gap:.8rem;align-items:center;margin:.42rem 0}
#wrp-profiles .sc-region-label{text-align:right;font-size:.85rem;line-height:1.25}
#wrp-profiles .sc-region-stack{display:flex;height:20px;width:100%;overflow:hidden}
#wrp-profiles .sc-segment{height:100%;display:block}
#wrp-profiles .sc-region-scale{margin-left:15.8rem;display:flex;justify-content:space-between;color:var(--page-muted);font-size:.8rem;font-variant-numeric:tabular-nums}
#wrp-profiles .sc-pairs{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2rem;margin-top:2rem}
#wrp-profiles .sc-pairs figure{min-width:0;margin:0}
#wrp-profiles .sc-chart{width:100%;min-height:270px}
#wrp-profiles .sc-chart svg{display:block;max-width:100%;color:var(--page-ink)}
#wrp-profiles .sc-chart text{fill:currentColor;font-family:inherit}
#wrp-profiles .sc-chart .sc-grid{stroke:var(--page-line);stroke-width:1}
#wrp-profiles .sc-chart .sc-first{fill:#087e8b}
#wrp-profiles .sc-chart .sc-second{fill:#e66e57}
#wrp-profiles .sc-pair-legend .sc-first{background:#087e8b}
#wrp-profiles .sc-pair-legend .sc-second{background:#e66e57}
#wrp-profiles .sc-caption{font-size:.85rem;color:var(--page-muted)}
#wrp-profiles details.sc-data{margin:.7rem 0;border:0;padding:0}
#wrp-profiles .sc-data summary{font-size:.85rem;font-weight:400}
#wrp-profiles .sc-data table{table-layout:auto;font-size:.8rem}
#wrp-profiles .sc-data caption{text-align:left;padding:.4rem 0;color:var(--page-muted)}
#wrp-profiles .sc-data th:first-child{text-align:left;min-width:9rem}
#wrp-profiles .sc-data td{background:transparent}
#wrp-profiles .sc-table-scroll{overflow:auto}
@media(max-width:800px){#wrp-profiles .sc-pairs{grid-template-columns:1fr;gap:1.7rem}}
@media(max-width:560px){#wrp-profiles .sc-region-row{grid-template-columns:1fr;gap:.18rem;margin:.65rem 0}#wrp-profiles .sc-region-label{text-align:left}#wrp-profiles .sc-region-scale{margin-left:0}#wrp-profiles .sc-region-stack{height:22px}}
</style>
<section class="sc-section" aria-labelledby="sc-regions-title">
<h2 id="sc-regions-title">The same profiles have different regional frequencies</h2>
<p class="pf-muted">All 142 countries, after assignment to the five frozen WARM-5 centres. Within each region, each country has equal total weight and retains its relative survey weights. These are regional frequencies of the same global profiles, not independent regional fits.</p>
''' + legend + ''.join(region_rows) + '''
<div class="sc-region-scale" aria-hidden="true"><span>0%</span><span>20%</span><span>40%</span><span>60%</span><span>80%</span><span>100%</span></div>
<p class="sc-caption">For example, the lower-worry profile accounts for 56.4% in Northern/Western Europe and 17.1% in Central/Western Africa. Hover over a segment for its percentage, or open the table below.</p>
''' + table(['Region', 'Profile 1', 'Profile 2', 'Profile 3', 'Profile 4', 'Profile 5'], region_table, 'Equal-country-weighted profile frequencies within each region. Complete-case respondents only.') + '''
<div class="sc-pairs">
<figure aria-labelledby="sc-transfer-title"><h3 id="sc-transfer-title">Development and held-out frequencies</h3>
<div class="sc-pair-legend"><span><i class="sc-first"></i>Development countries</span><span><i class="sc-second"></i>Held-out countries</span></div>
<div class="sc-chart" id="sc-transfer"></div>
<figcaption class="sc-caption">The model and profile definitions are unchanged. Each country receives equal total weight within its set. The largest difference is +2.1 percentage points for profile 4. Similar frequencies alone do not establish transfer. The 29 countries are held out from T5 fitting and model selection. Worry coding and worry--harm allocation are optimized using only the 113 development countries; held-out responses and evaluation results do not enter that optimization.</figcaption>
''' + table(['Profile', 'Development', 'Held-out'], [[str(i + 1) + ' · ' + p['name'], percent(transfer[i][0]), percent(transfer[i][1])] for i, p in enumerate(profiles)], 'Profile frequencies among complete-case respondents, with equal country weight within each set.') + '''
</figure>
<figure aria-labelledby="sc-harm-title"><h3 id="sc-harm-title">Personal and known-person harm</h3>
<div class="sc-pair-legend"><span><i class="sc-first"></i>Respondent harmed</span><span><i class="sc-second"></i>Someone known harmed</span></div>
<div class="sc-chart" id="sc-harm"></div>
<figcaption class="sc-caption">Development countries only. Each bar averages the seven harm-domain prevalences within a profile. It does not show the percentage reporting any harm. Personal and known-person harm can overlap. The broad-harm profile is mainly distinguished by reports about someone personally known.</figcaption>
''' + table(['Profile', 'Respondent', 'Someone known'], [[str(i + 1) + ' · ' + p['name'], percent(harm[i][0]), percent(harm[i][1])] for i, p in enumerate(profiles)], 'Mean prevalence across the seven harm domains, within each development profile and using equal-country analysis weights.') + '''
</figure></div>
<p class="sc-caption">Web profile numbers 1–5 correspond to research identifiers T5_C0–T5_C4. These summaries describe eligible respondents with complete profile responses, not the world population.</p>
</section>
<h2>Inspect one profile</h2>
<script id="sc-summary-data" type="application/json">''' + chart_data + '''</script>
<script>
(()=>{
const root=document.getElementById('wrp-profiles');
const data=JSON.parse(root.querySelector('#sc-summary-data').textContent);
const ns='http://www.w3.org/2000/svg';
function element(tag,attributes={},text){const node=document.createElementNS(ns,tag);Object.entries(attributes).forEach(([k,v])=>node.setAttribute(k,v));if(text!==undefined)node.textContent=text;return node;}
function draw(container,values,maximum,step,title,series){
 const width=Math.round(container.getBoundingClientRect().width);if(!width)return;
 const height=285,left=47,right=8,top=27,bottom=43,plotHeight=height-top-bottom;
 const svg=element('svg',{width,height,viewBox:`0 0 ${width} ${height}`,role:'img','aria-label':title});
 svg.append(element('title',{},title));
 svg.append(element('desc',{},values.map((v,i)=>`Profile ${i+1}: ${series[0]} ${(100*v[0]).toFixed(1)}%; ${series[1]} ${(100*v[1]).toFixed(1)}%`).join('. ')));
 const y=v=>top+plotHeight*(1-v/maximum),group=(width-left-right)/5,barWidth=Math.min(33,group*.34);
 for(let v=0;v<=maximum+1e-8;v+=step){const yy=y(v);svg.append(element('line',{x1:left,x2:width-right,y1:yy,y2:yy,class:'sc-grid'}));svg.append(element('text',{x:left-8,y:yy+4,'text-anchor':'end','font-size':12},Math.round(v*100)+'%'));}
 values.forEach((pair,i)=>{
  const centre=left+group*(i+.5);
  pair.forEach((value,j)=>{
   const x=centre+(j===0?-barWidth-4:4),label=`Profile ${i+1}, ${series[j]}: ${(100*value).toFixed(1)}%`;
   const rect=element('rect',{x,y:y(value),width:barWidth,height:plotHeight*value/maximum,class:j===0?'sc-first':'sc-second',rx:1});
   rect.append(element('title',{},label));svg.append(rect);
   if(group>=87)svg.append(element('text',{x:x+barWidth/2,y:y(value)-6,'text-anchor':'middle','font-size':12},(100*value).toFixed(1)+'%'));
  });
  svg.append(element('text',{x:centre,y:height-22,'text-anchor':'middle','font-size':13},i+1));
 });
 svg.append(element('text',{x:left+(width-left-right)/2,y:height-3,'text-anchor':'middle','font-size':12},'Profile'));
 container.replaceChildren(svg);
}
const charts=[['sc-transfer',data.transfer,.4,.1,'WARM-5 profile frequencies in development and held-out countries',['Development','Held-out']],['sc-harm',data.harm,.7,.1,'Mean personal and known-person harm prevalence by WARM-5 profile',['Respondent harmed','Someone known harmed']]];
charts.forEach(([id,...args])=>{
 const container=root.querySelector('#'+id);let previous=-1;
 const render=()=>{const width=Math.round(container.getBoundingClientRect().width);if(width===previous)return;previous=width;draw(container,...args);};
 render();if(window.ResizeObserver)new ResizeObserver(render).observe(container);else window.addEventListener('resize',render);
});
})();
</script>
''' + END
    if START in document:
        document = re.sub(re.escape(START) + r'.*?' + re.escape(END), lambda _: block, document, flags=re.S)
    else:
        document = document.replace('<div id="pf-cards"', block + '\n<div id="pf-cards"', 1)
    PAGE.write_text(document)
    fragment = re.search(r'<main id="wrp-profiles">.*?</main>', document, re.S)[0]
    (ROOT / 'docs/response-profiles-fragment.html').write_text(fragment.replace('<main id="wrp-profiles">', '<div id="wrp-profiles">', 1).removesuffix('</main>') + '</div>')
    print('Added three WARM-5 summary charts: 15 regions, two sets, two harm indicators.')


if __name__ == '__main__':
    build()
