/* All inputs are country aggregates. No respondent model is fitted here. */
(()=>{'use strict';
 const root=document.getElementById('wrp-wave-atlas'),data=window.WRP_COUNTRY_WAVES,geography=window.WRP_COUNTRY_GEOGRAPHY;
 if(!data||!geography||!window.d3){root.innerHTML='<p>The country data could not be loaded. Please reload the page.</p>';return;}
 const el=id=>root.querySelector('#cw-'+id),pct=v=>(100*v).toFixed(1)+'%',fmt=v=>v===null?'—':v.toFixed(3);
 const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
 const incomeLabels={1:'Low income',2:'Lower-middle income',3:'Upper-middle income',4:'High income',9:'Not classified'};
 const incomeColours={1:'#c17a50',2:'#e3b66a',3:'#7aa5b4',4:'#416d91',9:'#b9bdc2'};
 const metricLabels={responses:'Overall original answers',worry:'Worry answers',personal:'Personal harm',known:'Known-person harm',clusters:'Cluster proportions'};
 const palette=d3.piecewise(d3.interpolateLab,['#4d85b1','#64a779','#ead46c','#df8b45']);
 const colourPosition=ratio=>Math.min(1,Math.max(0,ratio/2));
 const distanceColour=ratio=>palette(colourPosition(ratio));
 const cache=new Map();
 const state={family:'full',year:2025,basis:'responses',component:'responses',scope:'all',country:'FIN',map:'distance',view:'country',peers:'10'};
 let current,matrices,selected,reference,metric,indices,overviewColours,statusMessage='';
 const model=()=>data.models[state.family+'_'+state.year];
 function calculate(m){
  if(cache.has(m.key))return cache.get(m.key);
  const n=m.countries.length,nw=m.worryDomains.length,hasHarm=m.family==='full';
  const keys=hasHarm?['clusters','responses','worry','personal','known']:['clusters','responses','worry'];
  const result=Object.fromEntries(keys.map(k=>[k,Array.from({length:n},()=>Array(n).fill(0))]));
  for(let i=0;i<n;i++)for(let j=i+1;j<n;j++){
   let h=0,w=0,s=0,k=0;
   for(let c=0;c<m.k;c++)h+=(Math.sqrt(m.shares[i][c])-Math.sqrt(m.shares[j][c]))**2;
   for(let c=0;c<3*nw;c++)w+=Math.abs(m.probabilities[i][c]-m.probabilities[j][c])/(2*nw);
   if(hasHarm)for(let c=0;c<7;c++){
    s+=Math.abs(m.probabilities[i][3*nw+c]-m.probabilities[j][3*nw+c])/7;
    k+=Math.abs(m.probabilities[i][3*nw+7+c]-m.probabilities[j][3*nw+7+c])/7;
   }
   const v={clusters:Math.sqrt(h/2),worry:w,responses:hasHarm?m.alpha*w+(1-m.alpha)*(s+k)/2:w,personal:s,known:k};
   for(const key of keys)result[key][i][j]=result[key][j][i]=v[key];
  }
  cache.set(m.key,result);return result;
 }
 function rank(matrix,i,ids,countries){return ids.filter(j=>j!==i).sort((a,b)=>matrix[i][a]-matrix[i][b]||(countries[a].iso<countries[b].iso?-1:1));}
 function overview(m){
  const points=m.embedding.coordinates;let scale=55/Math.max(...points.map(p=>Math.hypot(...p)));
  while(scale>.001&&points.some(p=>{const c=d3.lab(67,p[0]*scale,p[1]*scale).rgb();return c.r<3||c.r>252||c.g<3||c.g>252||c.b<3||c.b>252;}))scale*=.95;
  return points.map(p=>d3.lab(67,p[0]*scale,p[1]*scale).formatHex());
 }
 function save(){
  const url=new URL(location.href);for(const [k,v] of Object.entries({inputs:state.family,wave:state.year,basis:state.basis,component:state.component,scope:state.scope,country:state.country,map:state.map,view:state.view,peers:state.peers}))url.searchParams.set(k,v);
  try{history.replaceState(null,'',url);}catch(error){/* file:// may restrict URL updates; controls still work. */}
 }
 function restore(){
  const p=new URLSearchParams(location.search);
  state.family=['full','common_worry'].includes(p.get('inputs'))?p.get('inputs'):'full';
  const years=state.family==='full'?[2021,2023,2025]:[2019,2021,2023,2025];
  state.year=years.includes(Number(p.get('wave')))?Number(p.get('wave')):2025;
  for(const [key,options,fallback] of [['basis',['responses','clusters'],'responses'],['component',['responses','worry','personal','known'],'responses'],['scope',['all','development'],'all'],['map',['distance','overview','income'],'distance'],['view',['country','income'],'country'],['peers',['10','20','all'],'10']])state[key]=options.includes(p.get(key))?p.get(key):fallback;
  state.country=p.get('country')||'FIN';
  if(state.view==='income'&&!p.has('map'))state.map='income';
 }
 function tooltipContent(i){
  const c=current.countries[i];let text='<strong>'+esc(c.name)+'</strong><br>'+esc(c.region)+' · '+esc(incomeLabels[c.income])+'<br>'+c.respondents.toLocaleString('en-US')+' eligible respondents';
  if(state.map==='distance')text+='<br>Distance from '+esc(current.countries[selected].name)+': '+fmt(matrices[metric][selected][i]/reference)+' × reference<br>Raw distance: '+matrices[metric][selected][i].toFixed(5);
  return text;
 }
 function chooseCountry(iso){state.country=iso;render();save();}
 function drawMap(){
  const c=current.countries[selected],svg=d3.select(el('map'));svg.selectAll('*').remove();svg.attr('viewBox','0 0 1000 505');
  const set=new Set(indices),byISO=new Map(current.countries.map((c,i)=>[c.iso,i]));
  const projection=d3.geoNaturalEarth1().fitExtent([[14,12],[986,491]],geography.world),path=d3.geoPath(projection);
  const fill=i=>!set.has(i)?'#cfd3d7':state.map==='income'?incomeColours[current.countries[i].income]:state.map==='overview'?overviewColours[i]:distanceColour(matrices[metric][selected][i]/reference);
  const active=i=>set.has(i)&&i===selected;
  const featureISO=f=>f.properties.id;
  function bind(selection,indexer){
   selection.each(function(d){const i=indexer(d);if(!set.has(i))return;
    const node=d3.select(this),country=current.countries[i];
    node.attr('data-iso',country.iso).attr('tabindex',0).attr('role','button').attr('aria-label',country.name+', select as reference country');
    node.on('click',()=>chooseCountry(country.iso)).on('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();chooseCountry(country.iso);}})
     .on('pointerenter',()=>{el('tooltip').innerHTML=tooltipContent(i);el('tooltip').hidden=false;})
     .on('pointermove',event=>{const [x,y]=d3.pointer(event,el('map').parentNode);el('tooltip').style.left=Math.min(x+12,Math.max(4,el('map').clientWidth-270))+'px';el('tooltip').style.top=Math.max(5,y-72)+'px';})
     .on('pointerleave',()=>{el('tooltip').hidden=true;});
   });
  }
  const lands=svg.append('g').selectAll('path').data(geography.world.features).join('path').attr('d',path).attr('class',f=>'cw-land'+(active(byISO.get(featureISO(f)))?' cw-country-active':''))
   .attr('fill',f=>fill(byISO.get(featureISO(f))));
  lands.append('title').text(f=>{const i=byISO.get(featureISO(f));return set.has(i)?current.countries[i].name:((f.properties.name||featureISO(f))+': outside the selected eligible country set');});
  bind(lands,f=>byISO.get(featureISO(f)));
  svg.append('g').selectAll('path').data(geography.regions[String(current.year)]).join('path').attr('d',path).attr('class','cw-region');
  const drawn=new Set(geography.world.features.map(featureISO)),tiny=new Set(geography.tiny);
  const dots=svg.append('g').selectAll('circle').data(current.countries.map((c,i)=>({c,i})).filter(x=>set.has(x.i)&&(tiny.has(x.c.iso)||!drawn.has(x.c.iso))))
   .join('circle').attr('cx',x=>projection(x.c.point)[0]).attr('cy',x=>projection(x.c.point)[1]).attr('r',x=>x.i===selected?4.5:3.2).attr('fill',x=>fill(x.i))
   .attr('stroke','#333').attr('stroke-width',.8);
  dots.append('title').text(x=>x.c.name);bind(dots,x=>x.i);
  el('tooltip').hidden=true;
  el('map-title').textContent=state.map==='income'?current.year+' · Country income groups':state.map==='overview'?current.year+' · Similar cluster mixtures, similar colours':current.year+' · Distances from '+c.name;
  el('map-subtitle').textContent=state.map==='income'?'Income classifications supplied with this survey wave':state.map==='overview'?current.k+' frozen clusters · Approximate two-dimensional view':metricLabels[metric]+' · Smaller distances mean closer countries';
  const grey='<span><span class="cw-key-box" style="background:#cfd3d7"></span>Outside selected country set</span>';
  if(state.map==='distance'){
   el('legend').innerHTML='<div class="cw-gradient" style="background:linear-gradient(to right,'+Array.from({length:21},(_,i)=>distanceColour(i/10)+' '+i*5+'%').join(',')+')"></div><div class="cw-legend-ticks"><span>0 · identical</span><span>1 · reference</span><span>2+ · farther</span></div><div style="margin-top:8px">'+grey+'</div>';
   el('map-note').textContent='Fixed 2025 reference: '+reference.toFixed(6)+' raw '+(metric==='clusters'?'Hellinger':'total variation')+' distance. Divide raw distance by this reference. Colours stop changing at 2; numbers and ranks remain uncapped. Dark outlines show the survey’s regions; dots mark small countries. Select a country on the map or in the list.';
  }else if(state.map==='income'){
   el('legend').innerHTML='<div class="cw-income-key">'+[1,2,3,4,9].filter(a=>indices.some(i=>current.countries[i].income===a)).map(a=>'<span><span class="cw-key-box" style="background:'+incomeColours[a]+'"></span>'+incomeLabels[a]+'</span>').join('')+grey+'</div>';
   el('map-note').textContent='The map shows four income categories, not a distance scale. Dark outlines show the survey’s regions. Country income groups may change between waves. The distance tables below use '+metricLabels[metric].toLowerCase()+'.';
  }else{
   el('legend').innerHTML='<div class="cw-overview-key"><svg id="cw-colour-key" viewBox="0 0 140 85" width="140" height="85" role="img" aria-label="Two-dimensional cluster-similarity colour key"></svg><span>'+pct(current.embedding.variance)+' of Hellinger-coordinate variation retained<br>Colours are specific to this wave and model.</span>'+grey+'</div>';
   const key=d3.select(el('colour-key')),points=current.embedding.coordinates;
   const x=d3.scaleLinear().domain(d3.extent(points,p=>p[0])).range([8,132]),y=d3.scaleLinear().domain(d3.extent(points,p=>p[1])).range([77,8]);
   key.selectAll('circle').data(indices).join('circle').attr('cx',i=>x(points[i][0])).attr('cy',i=>y(points[i][1])).attr('r',i=>i===selected?4:2.5).attr('fill',i=>overviewColours[i]).attr('stroke',i=>i===selected?'#20252b':'none');
   el('map-note').textContent='The colour overview approximates country similarity in two dimensions. It is not a low-to-high risk scale. Its colour axes are fitted separately for each model; compare exact distances, rather than overview colours, across waves. The nearest-country list always uses the full Hellinger distance. The projection is fixed over all countries, including when only development countries are displayed.';
  }
 }
 const evidence=(value,label)=>'<div><strong>'+value+'</strong><span>'+label+'</span></div>';
 function countryPanel(){
  const c=current.countries[selected],stats=current.summaries[state.scope],matrix=matrices[metric],ordered=rank(matrix,selected,indices,current.countries);
  const comp=stats.comparison;
  el('comparison-stats').innerHTML=evidence(fmt(comp.distance_rank_spearman),'Rank correlation: cluster vs original-answer distances')+evidence(pct(comp.nearest_agreement),'Countries with the same nearest neighbour in both summaries')+evidence(pct(stats[metric].nearest_same_region),'Nearest countries in the same survey region');
  el('nearest-title').textContent='Nearest countries to '+c.name;
  el('nearest-note').textContent=metricLabels[metric]+' · Ranked by unrounded raw distance; exact ties by country ISO code. Reference country omitted.';
  const harm=state.family==='full',response=state.basis==='responses';
  const columns=['Rank','Country','Distance ÷ 2025 reference','Raw distance',...(response?['Worry TV',...(harm?['Personal gap (pp)','Known-person gap (pp)']:[])]:[])];
  const peers=state.peers==='all'?ordered:ordered.slice(0,Number(state.peers));
  el('neighbours').innerHTML='<caption class="aw-small aw-muted" style="text-align:left;margin-bottom:8px">'+peers.length+' of '+ordered.length+' other countries · '+current.year+'</caption><thead><tr>'+columns.map(t=>'<th scope="col">'+t+'</th>').join('')+'</tr></thead><tbody>'+peers.map((j,r)=>'<tr><td>'+(r+1)+'</td><td class="cw-country-name"><button class="cw-choose" type="button" data-peer="'+current.countries[j].iso+'">'+esc(current.countries[j].name)+'</button></td><td>'+fmt(matrix[selected][j]/reference)+'</td><td>'+matrix[selected][j].toFixed(5)+'</td>'+(response?'<td>'+matrices.worry[selected][j].toFixed(5)+'</td>'+(harm?'<td>'+(100*matrices.personal[selected][j]).toFixed(2)+'</td><td>'+(100*matrices.known[selected][j]).toFixed(2)+'</td>':''):'')+'</tr>').join('')+'</tbody>';
  el('neighbours').querySelectorAll('[data-peer]').forEach(b=>b.addEventListener('click',()=>chooseCountry(b.dataset.peer)));
  el('shares').innerHTML=current.shares[selected].map((p,i)=>'<div class="cw-share"><span>C'+i+' · '+esc(current.names[i])+'</span><div class="cw-share-track"><span style="width:'+100*p+'%"></span></div><span>'+pct(p)+'</span></div>').join('');
  const uncertainty=current.nearest_uncertainty.find(u=>u.scope===state.scope&&u.iso===c.iso);
  el('bootstrap').hidden=state.basis!=='clusters';
  if(state.basis==='clusters')el('bootstrap').textContent='Conditional bootstrap check: '+current.countries.find(peer=>peer.iso===uncertainty.original_nearest).name+' remains the nearest country in '+pct(uncertainty.original_nearest_frequency)+' of 200 respondent resamples within countries. Survey weights and frozen labels are retained. This checks sensitivity to the observed respondents; it does not refit the model or account for the full survey design.';
 }
 function incomePanel(){
  const stats=current.summaries[state.scope][metric],income=stats.income;
  el('income-stats').innerHTML=evidence(String(stats.classified_countries),'Countries with a recorded income group')+evidence(fmt(income.rho),'Spearman correlation: income-group gap vs distance')+evidence(String(indices.length-stats.classified_countries),'Countries excluded from income calculations');
  el('income-table').innerHTML='<caption class="aw-small aw-muted" style="text-align:left;margin-bottom:8px">'+current.year+' · '+metricLabels[metric]+' ÷ fixed 2025 reference</caption><thead><tr><th scope="col">Income group</th>'+[1,2,3,4].map(a=>'<th scope="col">'+incomeLabels[a]+'</th>').join('')+'</tr></thead><tbody>'+stats.income_cells.map((row,i)=>'<tr><th scope="row">'+incomeLabels[i+1]+'</th>'+row.map(cell=>'<td style="background:'+(cell.mean===null?'#eeeeee':distanceColour(cell.mean/reference))+'">'+(cell.mean===null?'—':fmt(cell.mean/reference))+'<span class="cw-pair-count">'+cell.pairs.toLocaleString('en-US')+' pairs</span></td>').join('')+'</tr>').join('')+'</tbody>';
  el('income-note').textContent='Income-group gap is the absolute difference between the four ordered labels (0–3). A positive correlation means greater income-group gaps tend to accompany greater country distances. Country pairs share countries, so an ordinary independent-pair significance test would be inappropriate. Classifications are those supplied with each survey wave; this is a descriptive association.';
  el('permutation').parentElement.hidden=!income.unrestricted;
  if(income.unrestricted)el('permutation').innerHTML='<p>Shuffle whole-country income labels 999 times, keeping the distances fixed. The upper-tail fraction is (1 + shuffled correlations at least as large as observed) / 1,000.</p><p><strong>Unrestricted shuffle:</strong> '+fmt(income.unrestricted.upper_tail_fraction)+'. <strong>Shuffle only within the survey’s regions:</strong> '+fmt(income.within_regions.upper_tail_fraction)+'. The latter preserves each region’s counts of income groups.</p><p class="aw-note">These are conditional randomization checks of the recorded labels. They are not causal effects or independent evidence from every country pair. The random seed is fixed at 20261029.</p>';
 }
 function method(){
  const nw=current.worryDomains.length,hasHarm=current.family==='full';
  el('method').innerHTML='<p><strong>Country summaries.</strong> Use the saved frozen assignments and precisely the respondents eligible for this wave model. In each country, normalize their survey weights to sum to one. The same respondents and weights produce cluster proportions and every original-answer distribution. All-country views include the original development and held-out countries as a post-validation description.</p><p><strong>Cluster distance.</strong> H(p,q) = √[½ Σ<sub>c</sub>(√p<sub>c</sub> − √q<sub>c</sub>)²]. There are '+current.k+' clusters in this model. Equal shares give zero distance; larger values mean greater differences in the mix of clusters.</p><p><strong>Original-answer distance.</strong> For each worry, total variation is half the sum of absolute gaps between the three category probabilities. Average over '+nw+' questions.'+(hasHarm?' For each harm indicator, total variation is the absolute prevalence gap. Average separately over seven personal and seven known-person harm indicators. Overall D = αD<sub>W</sub> + (1−α)(D<sub>S</sub> + D<sub>K</sub>)/2, with this frozen model’s α = '+current.alpha.toFixed(8)+' (worry '+pct(current.alpha)+', each harm block '+pct((1-current.alpha)/2)+').':' No harm or traffic question enters this five-common-worry model. Overall D is simply the average of its five question distances.')+' The numerical middle worry value q does not enter this category-distribution comparison. Harm to self and to someone known remain separate; both indicators are 1 if both experienced harm.</p><p><strong>Distance colours.</strong> Divide a raw distance by the median over all distinct country pairs in the original frozen 2025 model of the same question family. The denominator stays fixed when wave, country or country set changes. Each distance and component has its own denominator. These ratios are not percentages, and component ratios cannot be added. Full models retain their own worry–harm allocations; cluster definitions and counts also differ across waves. A shared colour reference does not make those definitions identical. The archived 2023 pages retain their earlier display constants.</p><p><strong>Limits of the summaries.</strong> Original-answer distances compare question marginals, so they do not describe combinations within individual respondents. Cluster shares compress answers in a different way. Different nearest countries are therefore possible. These maps use each wave’s own eligible countries; a changing nearest country may partly reflect a changing country set. There is no new respondent clustering or held-out assessment.</p><p><a href="./methods.html#country-waves">Methods and reproducibility</a> · <a href="./data/country-waves.sources.json" download>Source checksums</a></p>';
 }
 function render(){
  current=model();matrices=calculate(current);overviewColours=overview(current);
  if(state.family==='common_worry'&&!['responses','worry'].includes(state.component))state.component='responses';
  if(state.basis!=='clusters'&&state.map==='overview')state.map='distance';
  metric=state.basis==='clusters'?'clusters':state.component;reference=data.references[state.family][metric];
  indices=current.countries.map((_,i)=>i).filter(i=>state.scope==='all'||current.countries[i].split==='train');
  selected=indices.find(i=>current.countries[i].iso===state.country);
  if(selected===undefined){const old=state.country;selected=indices.find(i=>current.countries[i].iso==='FIN')??indices[0];state.country=current.countries[selected].iso;statusMessage=old+' is outside this country set. Showing '+current.countries[selected].name+'.';}
  el('status').textContent=statusMessage;statusMessage='';
  el('family').value=state.family;el('basis').value=state.basis;el('component').value=state.component;el('scope').value=state.scope;el('map-mode').value=state.map;el('peers').value=state.peers;
  el('component-label').hidden=state.basis==='clusters';
  for(const option of el('component').options){option.hidden=state.family==='common_worry'&&['personal','known'].includes(option.value);option.disabled=option.hidden;if(option.value==='responses')option.textContent=state.family==='full'?'Overall worry + harm':'All five common worries';}
  el('map-mode').querySelector('[value="overview"]').disabled=state.basis!=='clusters';
  el('country').innerHTML=indices.slice().sort((a,b)=>current.countries[a].name.localeCompare(current.countries[b].name)).map(i=>'<option value="'+current.countries[i].iso+'">'+esc(current.countries[i].name)+'</option>').join('');el('country').value=state.country;
  root.querySelectorAll('[data-year]').forEach(b=>{b.disabled=state.family==='full'&&b.dataset.year==='2019';b.setAttribute('aria-pressed',String(Number(b.dataset.year)===state.year));});
  el('population').textContent=current.year+' · '+current.k+' frozen clusters · '+indices.length+' '+(state.scope==='development'?'development':'observed')+' countries · '+indices.reduce((n,i)=>n+current.countries[i].respondents,0).toLocaleString('en-US')+' eligible respondents · '+(state.family==='full'?'Six worries + all 14 harm indicators.':'Five common worries; no harm or traffic.');
  for(const v of ['country','income']){el('tab-'+v).setAttribute('aria-selected',String(state.view===v));el('tab-'+v).tabIndex=state.view===v?0:-1;el(v+'-panel').hidden=state.view!==v;}
  drawMap();countryPanel();incomePanel();method();
 }
 root.querySelectorAll('[data-year]').forEach(b=>b.addEventListener('click',()=>{state.year=Number(b.dataset.year);render();save();}));
 for(const [id,key] of [['family','family'],['basis','basis'],['component','component'],['scope','scope'],['country','country'],['map-mode','map'],['peers','peers']])el(id).addEventListener('change',()=>{state[key]=el(id).value;if(state.family==='full'&&state.year===2019)state.year=2025;render();save();});
 for(const v of ['country','income'])el('tab-'+v).addEventListener('click',()=>{state.view=v;state.map=v==='income'?'income':'distance';render();save();});
 root.querySelector('[role="tablist"]').addEventListener('keydown',event=>{let v;if(['ArrowLeft','ArrowRight'].includes(event.key))v=state.view==='country'?'income':'country';else if(event.key==='Home')v='country';else if(event.key==='End')v='income';else return;event.preventDefault();el('tab-'+v).click();el('tab-'+v).focus();});
 el('download').addEventListener('click',()=>{
  const codes=indices.map(i=>current.countries[i].iso),lines=[['COUNTRY_ISO3',...codes].join(',')];
  for(const i of indices)lines.push([current.countries[i].iso,...indices.map(j=>matrices[metric][i][j].toPrecision(17))].join(','));
  const url=URL.createObjectURL(new Blob([lines.join('\n')+'\n'],{type:'text/csv;charset=utf-8'})),link=document.createElement('a');link.href=url;link.download=current.key+'_'+state.scope+'_'+metric+'_raw_distances.csv';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 });
 window.addEventListener('popstate',()=>{restore();render();});
 window.WRP_COUNTRY_TOOLS={calculate,rank,colourPosition,distanceColour};
 restore();render();
})();
