/* All inputs are country aggregates. No respondent model is fitted here. */
(()=>{'use strict';
 const root=document.getElementById('wrp-wave-atlas'),data=window.WRP_COUNTRY_WAVES,geography=window.WRP_COUNTRY_GEOGRAPHY;
 const panel=document.getElementById('country-map'),query=new URLSearchParams(location.search);
 const mapParams=['view','wave','country','map','basis','inputs','component','scope','peers'];
 if(!mapParams.some(key=>query.has(key)))return;
 panel.dataset.atlasCurrent='';
 if(!data||!geography||!window.d3){
  panel.querySelector('.atlas-page-head .atlas-deck').textContent='The country data could not be loaded. Please reload the page.';
  return;
 }
 const el=id=>root.querySelector('#cw-'+id),pct=v=>(100*v).toFixed(1)+'%',fmt=v=>v===null?'—':v.toFixed(3);
 const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
 const incomeLabels={1:'Low income',2:'Lower-middle income',3:'Upper-middle income',4:'High income',9:'Not classified'};
 const incomeColours={1:'#c17a50',2:'#e3b66a',3:'#7aa5b4',4:'#416d91',9:'#a06caa'};
 const metricLabels={
  responses:'Worry and reported harm',
  worry:'Worry answers',
  personal:'Harm to respondents',
  known:'Harm to people they know',
  clusters:'How common each cluster is'
 };
 const metricDescriptions={
  responses:'We compare the percentages who gave each answer. For example, two countries are close on the food question if similar shares said “not worried”, “somewhat worried” and “very worried”. The score combines these gaps across the worry and harm questions.',
  worry:'For every topic, we compare the percentages who said they were not worried, somewhat worried or very worried.',
  personal:'For each kind of harm, we compare the percentages who said they had experienced it themselves.',
  known:'For each kind of harm, we compare the percentages who said someone they know had experienced it.',
  clusters:'We compare the percentages of people in each cluster. Smaller scores mean the mix of clusters is more alike.'
 };
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
 function finlandSwedenDistance(year){
  const wave=data.models[state.family+'_'+year];
  const finland=wave.countries.findIndex(country=>country.iso==='FIN');
  const sweden=wave.countries.findIndex(country=>country.iso==='SWE');
  return calculate(wave)[metric][finland][sweden];
 }
 function rank(matrix,i,ids,countries){return ids.filter(j=>j!==i).sort((a,b)=>matrix[i][a]-matrix[i][b]||(countries[a].iso<countries[b].iso?-1:1));}
 function overview(m){
  const points=m.embedding.coordinates;let scale=55/Math.max(...points.map(p=>Math.hypot(...p)));
  while(scale>.001&&points.some(p=>{const c=d3.lab(67,p[0]*scale,p[1]*scale).rgb();return c.r<3||c.r>252||c.g<3||c.g>252||c.b<3||c.b>252;}))scale*=.95;
  return points.map(p=>{const colour=d3.hcl(d3.lab(67,p[0]*scale,p[1]*scale));colour.c=Math.max(25,colour.c||0);if(!Number.isFinite(colour.h))colour.h=210;return colour.formatHex();});
 }
 function save(){
  const url=new URL(location.href);for(const [k,v] of Object.entries({inputs:state.family,wave:state.year,basis:state.basis,component:state.component,scope:state.scope,country:state.country,map:state.map,view:state.view,peers:state.peers}))url.searchParams.set(k,v);
  try{history.replaceState(null,'',url);}catch(error){/* file:// may restrict URL updates; controls still work. */}
 }
 function restore(){
  const p=new URLSearchParams(location.search);
  const years=state.family!=='common_worry'?[2021,2023,2025]:[2019,2021,2023,2025];
  state.year=years.includes(Number(p.get('wave')))?Number(p.get('wave')):2025;
  for(const [key,options,fallback] of [['basis',['responses','clusters'],'responses'],['component',['responses','worry','personal','known'],'responses'],['scope',['all'],'all'],['map',['distance','overview','income'],'distance'],['view',['country','income'],'country'],['peers',['10','20','all'],'10']])state[key]=options.includes(p.get(key))?p.get(key):fallback;
  state.country=p.get('country')||'FIN';
  if(state.view==='income'&&!p.has('map'))state.map='income';
 }
 function tooltipContent(i){
  const c=current.countries[i];let text='<strong>'+esc(c.name)+'</strong><br>'+esc(c.region)+' · '+esc(incomeLabels[c.income])+'<br>'+c.respondents.toLocaleString('en-US')+' eligible respondents';
  if(state.map==='distance')text+='<br>Difference score: '+fmt(matrices[metric][selected][i]/reference);
  text+='<br>Click to compare with '+esc(c.name);
  return text;
 }
 function chooseCountry(iso){
  state.country=iso;
  if(state.view==='income'){
   state.view='country';
   state.map='distance';
  }
  render();save();
 }
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
    node.attr('data-iso',country.iso).attr('tabindex',0).attr('role','button').attr('aria-label','Compare with '+country.name);
    node.on('click',()=>chooseCountry(country.iso)).on('keydown',event=>{
     if(event.key==='Enter'||event.key===' '){
      event.preventDefault();
      chooseCountry(country.iso);
      el('map').querySelector('[data-iso="'+country.iso+'"]')?.focus();
     }
    })
     .on('pointerenter',()=>{el('tooltip').innerHTML=tooltipContent(i);el('tooltip').hidden=false;})
     .on('pointermove',event=>{const [x,y]=d3.pointer(event,el('map').parentNode);el('tooltip').style.left=Math.min(x+12,Math.max(4,el('map').clientWidth-270))+'px';el('tooltip').style.top=Math.max(5,y-72)+'px';})
     .on('pointerleave',()=>{el('tooltip').hidden=true;});
   });
  }
  const lands=svg.append('g').selectAll('path').data(geography.world.features).join('path').attr('d',path).attr('class',f=>'cw-land'+(active(byISO.get(featureISO(f)))?' cw-country-active':''))
   .attr('fill',f=>fill(byISO.get(featureISO(f))));
  lands.append('title').text(f=>{const i=byISO.get(featureISO(f));return set.has(i)?current.countries[i].name:((f.properties.name||featureISO(f))+': outside this year’s survey');});
  bind(lands,f=>byISO.get(featureISO(f)));
  svg.append('g').selectAll('path').data(geography.regions[String(current.year)]).join('path').attr('d',path).attr('class','cw-region');
  const drawn=new Set(geography.world.features.map(featureISO)),tiny=new Set(geography.tiny);
  const dots=svg.append('g').selectAll('circle').data(current.countries.map((c,i)=>({c,i})).filter(x=>set.has(x.i)&&(tiny.has(x.c.iso)||!drawn.has(x.c.iso))))
   .join('circle').attr('cx',x=>projection(x.c.point)[0]).attr('cy',x=>projection(x.c.point)[1]).attr('r',x=>x.i===selected?4.5:3.2).attr('fill',x=>fill(x.i))
   .attr('class',x=>active(x.i)?'cw-country-active':null)
   .attr('stroke','#333').attr('stroke-width',.8);
  dots.append('title').text(x=>x.c.name);bind(dots,x=>x.i);
  el('tooltip').hidden=true;
  el('map-title').textContent=state.map==='income'?'Country income groups':state.map==='overview'?'Where are the mixes of clusters alike?':'How similar are the answers to those in '+c.name+'?';
  if(state.map==='distance'&&metric==='clusters')el('map-title').textContent='Which countries have a similar mix of clusters to '+c.name+'?';
  el('map-subtitle').textContent=current.year+' survey · '+indices.length+' countries and areas'+(state.map==='distance'?' · '+metricLabels[metric]:'');
  const grey='<span><span class="cw-key-box cw-key-grey" aria-hidden="true"></span>Outside this year’s survey</span>';
  const keys='<div class="cw-map-keys"><span><span class="cw-key-box cw-key-selected" aria-hidden="true"></span>Selected country</span>'+grey+'</div>';
  el('scale-example').hidden=state.map!=='distance';
  if(state.map==='distance'){
   el('map-explainer').textContent=metricDescriptions[metric];
   el('legend').innerHTML='<div class="cw-scale"><div class="cw-gradient" aria-hidden="true" style="background:linear-gradient(to right,'+Array.from({length:21},(_,i)=>distanceColour(i/10)+' '+i*5+'%').join(',')+')"></div><div class="cw-legend-ticks"><span><strong>0</strong>Same percentages</span><span><strong>1</strong>Typical difference</span><span><strong>2+</strong>Twice typical or more</span></div></div>'+keys;
   const earlier=(finlandSwedenDistance(2021)/reference).toFixed(2);
   const later=(finlandSwedenDistance(2025)/reference).toFixed(2);
   el('example-2021').textContent=earlier;
   el('example-2025').textContent=later;
   const description=metric==='clusters'?'Their mixes of clusters were':'Their answers were';
   el('example-reading').textContent=earlier===later?'The scores round to the same value.':
    description+' more alike in '+(Number(later)<Number(earlier)?2025:2021)+'.';
   el('map-note').textContent='';
  }else if(state.map==='income'){
   el('legend').innerHTML='<div class="cw-income-key">'+[1,2,3,4,9].filter(a=>indices.some(i=>current.countries[i].income===a)).map(a=>'<span><span class="cw-key-box" style="background:'+incomeColours[a]+'"></span>'+incomeLabels[a]+'</span>').join('')+grey+'</div>';
   el('map-explainer').textContent='The colours show the national income groups recorded in this survey. These groups can change over time.';
   el('map-note').textContent='';
  }else{
   el('legend').innerHTML='<div class="cw-overview-key"><svg id="cw-colour-key" viewBox="0 0 140 85" width="140" height="85" role="img" aria-label="Colour key for similar mixes of clusters"></svg>'+keys+'</div>';
   const key=d3.select(el('colour-key')),points=current.embedding.coordinates;
   const x=d3.scaleLinear().domain(d3.extent(points,p=>p[0])).range([8,132]),y=d3.scaleLinear().domain(d3.extent(points,p=>p[1])).range([77,8]);
   key.selectAll('circle').data(indices).join('circle').attr('cx',i=>x(points[i][0])).attr('cy',i=>y(points[i][1])).attr('r',i=>i===selected?4:2.5).attr('fill',i=>overviewColours[i]).attr('stroke',i=>i===selected?'#20252b':'none');
   el('map-explainer').textContent='In this survey, countries with similar colours have roughly similar mixes of clusters.';
   el('map-note').textContent='These colours are specific to this survey. Use the scores in the list for comparisons across years.';
  }
 }
 const evidence=(value,label)=>'<div><strong>'+value+'</strong><span>'+label+'</span></div>';
 function countryPanel(){
  const c=current.countries[selected],stats=current.summaries[state.scope],matrix=matrices[metric],ordered=rank(matrix,selected,indices,current.countries);
  const comp=stats.comparison;
  el('comparison-stats').innerHTML=evidence(fmt(comp.distance_rank_spearman),'Rank correlation: cluster vs original-answer distances')+evidence(pct(comp.nearest_agreement),'Countries with the same nearest neighbour in both summaries')+evidence(pct(stats[metric].nearest_same_region),'Nearest countries in the same survey region');
  el('nearest-title').textContent='Closest matches to '+c.name;
  el('nearest-note').textContent='Countries are listed from most similar to least similar for the answers you selected. Choose a name to compare with that country.';
  if(metric==='clusters')el('nearest-note').textContent='Countries are listed by how similar their mixes of clusters are. Choose a name to compare with that country.';
  const harm=state.family!=='common_worry',response=state.basis==='responses';
  const peers=state.peers==='all'?ordered:ordered.slice(0,Number(state.peers));
  const headings=['Rank','Country','Difference score'];
  const detailedHeadings=[...headings,'Raw distance',...(response?['Worry distance',...(harm?['Personal harm gap (pp)','Known-person harm gap (pp)']:[])]:[])];
  const caption=peers.length+' of '+ordered.length+' other countries and areas · '+current.year+' survey';
  function makeTable(columns,detail){
   const head='<thead><tr>'+columns.map(title=>'<th scope="col">'+title+'</th>').join('')+'</tr></thead>';
   const rows=peers.map((j,r)=>{
    const {iso,name}=current.countries[j];
    const country=detail?esc(name):'<button class="cw-choose" type="button" data-peer="'+iso+'">'+esc(name)+'</button>';
    const distance=matrix[selected][j];
    const cells=[r+1,country,fmt(distance/reference)];
    if(detail){
     cells.push(distance.toFixed(5));
     if(response)cells.push(matrices.worry[selected][j].toFixed(5));
     if(response&&harm)cells.push((100*matrices.personal[selected][j]).toFixed(2),(100*matrices.known[selected][j]).toFixed(2));
    }
    return '<tr><td>'+cells[0]+'</td><th scope="row" class="cw-country-name">'+cells[1]+'</th>'+cells.slice(2).map(value=>'<td>'+value+'</td>').join('')+'</tr>';
   }).join('');
   return '<caption class="aw-small aw-muted">'+caption+'</caption>'+head+'<tbody>'+rows+'</tbody>';
  }
  el('neighbours').innerHTML=makeTable(headings,false);
  el('neighbour-details').innerHTML=makeTable(detailedHeadings,true);
  el('neighbours').querySelectorAll('[data-peer]').forEach(b=>b.addEventListener('click',()=>{
   chooseCountry(b.dataset.peer);
   el('country').focus();
  }));
  el('shares').innerHTML=current.shares[selected].map((p,i)=>'<div class="cw-share"><span>C'+i+' · '+esc(current.names[i])+'</span><div class="cw-share-track"><span style="width:'+100*p+'%"></span></div><span>'+pct(p)+'</span></div>').join('');
  const uncertainty=current.nearest_uncertainty.find(u=>u.scope===state.scope&&u.iso===c.iso);
  el('bootstrap').hidden=state.basis!=='clusters'||!uncertainty;
  if(state.basis==='clusters'&&uncertainty)el('bootstrap').textContent='Conditional bootstrap check: '+current.countries.find(peer=>peer.iso===uncertainty.original_nearest).name+' remains the nearest country in '+pct(uncertainty.original_nearest_frequency)+' of 200 respondent resamples within countries. Survey weights and frozen labels are retained. This checks sensitivity to the observed respondents; it does not refit the model or account for the full survey design.';
 }
 function incomePanel(){
  const stats=current.summaries[state.scope][metric],income=stats.income;
  el('income-stats').innerHTML=evidence(String(stats.classified_countries),'Countries with a recorded income group')+evidence(fmt(income.rho),'Spearman correlation: income-group gap vs distance')+evidence(String(indices.length-stats.classified_countries),'Countries excluded from income calculations');
  el('income-table').innerHTML='<caption class="aw-small aw-muted">'+current.year+' survey · '+metricLabels[metric]+' · 1 is a typical difference</caption><thead><tr><th scope="col">Income group</th>'+[1,2,3,4].map(a=>'<th scope="col">'+incomeLabels[a]+'</th>').join('')+'</tr></thead><tbody>'+stats.income_cells.map((row,i)=>'<tr><th scope="row">'+incomeLabels[i+1]+'</th>'+row.map(cell=>'<td style="background:'+(cell.mean===null?'#eeeeee':distanceColour(cell.mean/reference))+'">'+(cell.mean===null?'—':fmt(cell.mean/reference))+'<span class="cw-pair-count">'+cell.pairs.toLocaleString('en-US')+' pairs</span></td>').join('')+'</tr>').join('')+'</tbody>';
  el('income-note').textContent='Income-group gap is the absolute difference between the four ordered labels (0–3). A positive correlation means greater income-group gaps tend to accompany greater country distances. Country pairs share countries, so an ordinary independent-pair significance test would be inappropriate. Classifications are those supplied with each survey wave; this is a descriptive association.';
  el('permutation').parentElement.hidden=!income.unrestricted;
  if(income.unrestricted)el('permutation').innerHTML='<p>Shuffle whole-country income labels 999 times, keeping the distances fixed. The upper-tail fraction is (1 + shuffled correlations at least as large as observed) / 1,000.</p><p><strong>Unrestricted shuffle:</strong> '+fmt(income.unrestricted.upper_tail_fraction)+'. <strong>Shuffle only within the survey’s regions:</strong> '+fmt(income.within_regions.upper_tail_fraction)+'. The latter preserves each region’s counts of income groups.</p><p class="aw-note">These are conditional randomization checks of the recorded labels. They are not causal effects or independent evidence from every country pair. The random seed is fixed at 20261029.</p>';
 }
 function method(){
  const n=current.worryDomains.length,full=current.family==='full';
  const calibration=data.models[state.family+'_2025'];
  const countries=calibration.countries.filter(country=>country.split==='train').length;
  const pairs=(countries*(countries-1)/2).toLocaleString('en-US');
  const example=finlandSwedenDistance(2025);
  const harm=full
   ?'<p><strong>Harm answers.</strong> For each of seven topics, take the absolute difference in the shares reporting harm to themselves. Average these seven differences to obtain <var>D<sub>S</sub></var>. Repeat for harm to someone they know to obtain <var>D<sub>K</sub></var>.</p>'+
    '<p><strong>Worry and harm together.</strong> The raw difference is α<var>D<sub>W</sub></var> + (1 − α)(<var>D<sub>S</sub></var> + <var>D<sub>K</sub></var>)/2, with α = '+current.alpha+'. This gives '+(100*current.alpha)+'% of the weight to worry and '+(100*(1-current.alpha))+'% to harm.</p>'
   :'';
  el('method').innerHTML=
   '<p><strong>Country percentages.</strong> Use respondents with complete answers. For each answer or cluster, divide the survey weight of the people in that category by the total survey weight of eligible respondents in their country. Use those shares as fractions between 0 and 1.</p>'+
   '<p><strong>Worry answers.</strong> For each question, add the absolute differences for “not worried”, “somewhat worried” and “very worried”, then divide by two. For example, 70%, 20%, 10% versus 60%, 25%, 15% gives (0.10 + 0.05 + 0.05) ÷ 2 = 0.10. Average over all '+n+' worry questions to obtain <var>D<sub>W</sub></var>. This calculation uses the three response shares directly.</p>'+
   harm+
   '<p><strong>Cluster shares.</strong> For country share vectors <var>p</var> and <var>q</var>, the raw difference is the Hellinger distance √[½ Σ<sub>k</sub> (√<var>p</var><sub>k</sub> − √<var>q</var><sub>k</sub>)²], summing over the '+current.k+' clusters. The model fitted in each survey assigns respondents in every surveyed country.</p>'+
   '<p><strong>Difference score.</strong> Divide the raw difference by the median raw difference for that measure across all '+pairs+' distinct pairs of the '+countries+' countries used to fit the 2025 model. Each pair counts once. We use that same divisor for all survey years. Compare scores for the same pair of countries with the same measure selected.</p>'+
   '<p><strong>Finland and Sweden in 2025.</strong> With “'+metricLabels[metric]+'” selected, their raw difference and the reference give '+example.toFixed(8)+' ÷ '+reference.toFixed(8)+' ≈ '+(example/reference).toFixed(2)+'. The displayed values are rounded.</p>'+
   '<p>The country list is ranked by the unrounded distance. Survey coverage can change between years, which can also change the closest matches. The separate map for similar mixes of clusters uses two principal coordinates of the square-root shares. Those colours are specific to each survey.</p>'+
   '<p><a href="./methods.html#country-waves">Methods and reproduction</a> · <a href="./data/shared-five-sources.json" download>Source checksums</a></p>';
 }
 function render(){
  current=model();matrices=calculate(current);overviewColours=overview(current);
  if(state.family==='common_worry'&&!['responses','worry'].includes(state.component))state.component='responses';
  if(state.basis!=='clusters'&&state.map==='overview')state.map='distance';
  metric=state.basis==='clusters'?'clusters':state.component;reference=data.references[state.family][metric];
  indices=current.countries.map((_,i)=>i).filter(i=>state.scope==='all'||current.countries[i].split==='train');
  selected=indices.find(i=>current.countries[i].iso===state.country);
  if(selected===undefined){const old=state.country;selected=indices.find(i=>current.countries[i].iso==='FIN')??indices[0];state.country=current.countries[selected].iso;statusMessage=old+' is not available in the '+current.year+' survey. Showing '+current.countries[selected].name+'.';}
  el('status').dataset.notice=String(Boolean(statusMessage));
  el('status').textContent=statusMessage||(
   state.view==='income'?current.year+' survey selected.':current.year+' survey. Comparing with '+current.countries[selected].name+'.'
  );
  statusMessage='';
  el('basis').value=state.basis;el('component').value=state.component;el('scope').value=state.scope;el('map-mode').value=state.map;el('peers').value=state.peers;
  el('component-label').hidden=state.basis==='clusters';
  for(const option of el('component').options){option.hidden=state.family==='common_worry'&&['personal','known'].includes(option.value);option.disabled=option.hidden;if(option.value==='responses')option.textContent=state.family!=='common_worry'?metricLabels.responses:'All five common worries';}
  el('map-mode').querySelector('[value="overview"]').disabled=state.basis!=='clusters';
  el('country').innerHTML=indices.slice().sort((a,b)=>current.countries[a].name.localeCompare(current.countries[b].name)).map(i=>'<option value="'+current.countries[i].iso+'">'+esc(current.countries[i].name)+'</option>').join('');el('country').value=state.country;
  root.querySelectorAll('[data-year]').forEach(b=>{b.setAttribute('aria-pressed',String(Number(b.dataset.year)===state.year));});
  el('population').textContent=current.year+' · '+current.k+' fixed clusters · '+indices.length+' surveyed countries and areas · '+indices.reduce((n,i)=>n+current.countries[i].respondents,0).toLocaleString('en-US')+' eligible respondents · '+(state.family!=='common_worry'?'Six worries + all 14 harm indicators.':'Five common worries; no harm or traffic.')+(current.year===2019?' Separate 2019 alternative, without established shared later-wave clusters.':'');
  panel.querySelector('h1').textContent=state.view==='income'?'Do answers differ by country income group?':'Which countries answered alike?';
  el('intro').textContent=state.view==='income'
   ?'See how similarly people answered in countries with similar or different national income levels.'
   :'Find out where people gave similar answers about worry and harm in the World Risk Poll.';
  el('map-results-link').textContent=state.view==='income'?'See the income group comparison':'See the list of closest matches';
  for(const v of ['country','income']){el('tab-'+v).setAttribute('aria-selected',String(state.view===v));el('tab-'+v).tabIndex=state.view===v?0:-1;el(v+'-panel').hidden=state.view!==v;}
  drawMap();countryPanel();incomePanel();method();
 }
 root.querySelectorAll('[data-year]').forEach(b=>b.addEventListener('click',()=>{state.year=Number(b.dataset.year);render();save();}));
 for(const [id,key] of [['basis','basis'],['component','component'],['scope','scope'],['map-mode','map'],['peers','peers']])el(id).addEventListener('change',()=>{state[key]=el(id).value;if(state.family!=='common_worry'&&state.year===2019)state.year=2025;render();save();});
 el('country').addEventListener('change',()=>chooseCountry(el('country').value));
 if(location.hash==='#cw-calculation')el('calculation').open=true;
 el('calculation-link').addEventListener('click',()=>{el('calculation').open=true;});
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
