(() => {
 const root=document.getElementById('wrp-wave-atlas');
 const data=window.WRP_WAVE_DATA;
 if(!data||!data.models){root.innerHTML='<p>The wave data could not be loaded. Please reload the page.</p>';return;}
 const el=id=>root.querySelector('#'+id);
 const nice={food:'Food',water:'Water',crime:'Crime',severe_weather:'Severe weather',traffic:'Traffic',mental_health:'Mental health',work:'Work'};
 const state={family:'full',year:2025,earlier:2023,cluster:0,view:'explore'};
 const pct=v=>(v*100).toFixed(1)+'%';
 const num=v=>Number(v).toLocaleString('en-US');
 const escape=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
 const model=(year=state.year)=>data.models[state.family+'_'+year];
 const swatch=color=>'<span class="aw-swatch" style="background:var(--atlas-'+color+')"></span>';
 const name=(c,family=state.family)=>data.models[family+'_2025'].clusters[c].name;
 function saveState(){
  const url=new URL(window.location.href);
  for(const [key,value] of Object.entries({view:state.view,inputs:state.family,wave:state.year,earlier:state.earlier,cluster:state.cluster}))url.searchParams.set(key,String(value));
  try{window.history.replaceState(null,'',url);}catch(error){/* file:// hosts may restrict URL updates; the explorer still works offline. */}
 }
 function detail(){
  const m=model(),c=m.clusters[state.cluster],domains=m.worryDomains;
  const worry=domains.map((d,i)=>'<div class="aw-answer"><div class="aw-answer-label"><span>'+nice[d]+'</span><span>'+pct(c.worry[i][2])+' very worried</span></div><div class="aw-stack" role="img" aria-label="'+nice[d]+': '+pct(c.worry[i][0])+' not worried, '+pct(c.worry[i][1])+' somewhat, '+pct(c.worry[i][2])+' very worried">'+c.worry[i].map((v,j)=>'<span style="width:'+(100*v)+'%;background:var(--atlas-'+['low','mid','blue'][j]+')"></span>').join('')+'</div></div>').join('');
  const harm=c.harm.length?'<section><h3>Reported harm</h3><div class="aw-legend">'+swatch('before')+'<span>Respondent</span>'+swatch('blue')+'<span>Someone personally known</span></div>'+['food','water','crime','severe_weather','traffic','mental_health','work'].map((d,i)=>'<div class="aw-harm-row"><span class="aw-harm-name">'+nice[d]+'</span><div>'+[0,1].map(j=>'<div class="aw-harm-line" role="img" aria-label="'+nice[d]+', '+['respondent','known person'][j]+': '+pct(c.harm[j][i])+'"><div class="aw-track"><div class="aw-fill '+(j===0?'aw-harm-personal':'')+'" style="width:'+100*c.harm[j][i]+'%"></div></div><span>'+pct(c.harm[j][i])+'</span></div>').join('')+'</div></div>').join('')+'<p class="aw-note">Separate indicators. If both experienced harm, both indicators are 1.</p></section>':'';
  el('aw-detail').innerHTML='<h2>'+m.year+' · C'+c.id+' · '+escape(c.name)+'</h2><p class="aw-muted aw-small">'+pct(c.share)+' of the development population · Original survey answers</p><div class="aw-detail-grid"'+(!harm?' style="grid-template-columns:1fr"':'')+'><section><h3>Worry responses</h3><div class="aw-legend">'+['Not worried','Somewhat worried','Very worried'].map((n,i)=>'<span>'+swatch(['low','mid','blue'][i])+n+'</span>').join('')+'</div>'+worry+'<p class="aw-note">All bars span 0–100%.</p></section>'+harm+'</div>';
 }
 function explore(){
  const m=model();
  el('aw-clusters').style.setProperty('--aw-columns',m.k===4?2:3);
  root.querySelectorAll('[data-year]').forEach(b=>{const y=Number(b.dataset.year);b.disabled=state.family==='full'&&y===2019;b.setAttribute('aria-pressed',String(y===state.year));});
  el('aw-availability').textContent=state.family==='full'?'Six worries + seven personal and seven known-person harm indicators. 2019 is available in worry-only mode.':'Five common worries in every wave: food, water, crime, severe weather and mental health.';
  el('aw-model-title').textContent=m.year+' · '+m.k+' clusters';
  el('aw-model-pop').textContent=num(m.respondents)+' development respondents · '+m.countries+' countries · Each wave selected independently';
  el('aw-clusters').innerHTML=m.clusters.map(c=>'<button class="aw-cluster aw-interactive" type="button" data-cluster="'+c.id+'" aria-pressed="'+(c.id===state.cluster)+'"><span class="aw-card-top"><span class="aw-muted aw-small">C'+c.id+'</span><span class="aw-share">'+pct(c.share)+'</span></span><span class="aw-cname">'+escape(c.name)+'</span></button>').join('');
  el('aw-clusters').querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{state.cluster=Number(b.dataset.cluster);el('aw-clusters').querySelectorAll('button').forEach(button=>button.setAttribute('aria-pressed',String(Number(button.dataset.cluster)===state.cluster)));detail();saveState();}));
  el('aw-method').textContent='Weighted K-means was selected using this wave’s development evidence. Its transformation and centres were frozen before the original held-out assessment. The cards show each model’s own development population; the comparison view uses common countries and unchanged 2025 definitions.';
  detail();
  el('aw-method').textContent+=' Model: '+(m.id==='T5'?'WARM-5 (stored T5)':m.id)+'. Its original held-out population contains '+num(m.heldoutRespondents)+' respondents in '+m.heldoutCountries+' countries. The shares above use the development population only.';
 }
 function compare(){
  const family=state.family,old=state.earlier,before=data.shares[family][old],after=data.shares[family]['2025'];
  el('aw-compare-key').innerHTML='<span>'+swatch('before')+old+'</span><span>'+swatch('blue')+'2025</span>';
  const ceil=Math.ceil(Math.max(...before,...after)*110/10)*10;
  el('aw-pairs').innerHTML='<div class="aw-pair-grid aw-pair-head"><span>2025 cluster definition</span><span>Equal-country share · 0–'+ceil+'%</span><span style="text-align:right">Change</span></div>'+before.map((v,i)=>{const delta=100*(after[i]-v);return '<div class="aw-pair-grid aw-pair"><div class="aw-pair-title"><small>C'+i+'</small>'+name(i)+'</div><div class="aw-pair-plot">'+[v,after[i]].map((value,j)=>'<div class="aw-pair-bar" style="--aw-width:'+(value*100/ceil*100)+'%" role="img" aria-label="'+[old,2025][j]+' '+name(i)+': '+pct(value)+'"><span style="width:'+value*100/ceil*100+'%;background:var(--atlas-'+['before','blue'][j]+')"></span><em>'+pct(value)+'</em></div>').join('')+'</div><div class="aw-delta">'+(delta>0?'+':'')+delta.toFixed(1)+'<span class="aw-muted aw-small"> pp</span></div></div>';}).join('');
  const countries=data.reference[family].countries;
  el('aw-compare-note').textContent='Same '+countries+' countries in every wave · Equal country weights · 2025 definitions held fixed. Changes are percentage points. Different survey respondents; these are not individual transitions.';
  el('aw-prevalence-method').textContent='Apply the original frozen 2025 model to each wave’s own complete respondents, calculate survey-weighted country shares and average across the same '+countries+' countries. This compares frequencies under unchanged definitions. Comparison shares can differ from the overview because the country set is smaller. The independent wave models remain available in Explore a wave.';
  const earlier=model(old),mat=data.overlap[family+'_'+old];
  el('aw-overlap-note').textContent='Take the same 2025 respondents and assign them with both original models. Each row shows how one '+old+' cluster is divided among the 2025 clusters. Percentages are weighted and sum to 100% before rounding.';
  el('aw-matrix').innerHTML='<table class="aw-matrix"><caption class="aw-small aw-muted" style="text-align:left;margin-bottom:8px">Rows: '+old+' model · Columns: 2025 model · Same reference answers</caption><thead><tr><th scope="col">Earlier cluster</th>'+after.map((_,i)=>'<th scope="col">C'+i+'<br>'+name(i)+'</th>').join('')+'</tr></thead><tbody>'+mat.map((row,i)=>'<tr><th scope="row">C'+i+' · '+escape(earlier.clusters[i].name)+'</th>'+row.map(v=>'<td style="--aw-cell:'+(v*.45)+'"><span>'+(100*v).toFixed(0)+'%</span></td>').join('')+'</tr>').join('')+'</tbody></table>';
  const stats=data.stability[family+'_'+old];
  el('aw-stability').innerHTML='<h3>Compare disagreement with normal fitting variation</h3>'+stats.map((r,i)=>'<div class="aw-stab-row"><span>'+['Within '+old,old+' vs 2025','Within 2025'][i]+'</span><div class="aw-stab-track" aria-hidden="true" style="--aw-left:'+100*r.p10+'%;--aw-range:'+100*(r.p90-r.p10)+'%;--aw-mid:'+100*r.median+'%"><span class="aw-stab-range"></span><span class="aw-stab-dot"></span></div><span aria-label="Median ARI '+r.median.toFixed(3)+', tenth to ninetieth percentile '+r.p10.toFixed(3)+' to '+r.p90.toFixed(3)+'">'+r.median.toFixed(3)+'</span></div>').join('')+'<div class="aw-stab-row aw-muted"><span>ARI · higher is closer</span><div style="display:flex;justify-content:space-between"><span>0</span><span>0.5</span><span>1</span></div><span></span></div>';
 }
 function render(){
  el('aw-family').value=state.family;
  el('aw-explore').hidden=state.view!=='explore';el('aw-compare').hidden=state.view!=='compare';
  ['explore','compare'].forEach(v=>{el('aw-tab-'+v).setAttribute('aria-selected',String(state.view===v));el('aw-tab-'+v).tabIndex=state.view===v?0:-1;});
  const years=state.family==='full'?[2021,2023]:[2019,2021,2023];
  if(!years.includes(state.earlier))state.earlier=2023;
  el('aw-earlier').innerHTML=years.map(y=>'<option value="'+y+'">'+y+'</option>').join('');el('aw-earlier').value=state.earlier;
  explore();compare();
 }
 root.querySelectorAll('[data-year]').forEach(b=>b.addEventListener('click',()=>{state.year=Number(b.dataset.year);state.cluster=0;render();saveState();}));
 ['explore','compare'].forEach(v=>el('aw-tab-'+v).addEventListener('click',()=>{if(v==='compare'&&state.view!=='compare'&&state.year!==2025)state.earlier=state.year;state.view=v;render();saveState();}));
 el('aw-family').addEventListener('change',()=>{state.family=el('aw-family').value;if(state.family==='full'&&state.year===2019)state.year=2025;state.cluster=0;render();saveState();});
 el('aw-earlier').addEventListener('change',()=>{state.earlier=Number(el('aw-earlier').value);compare();saveState();});
 function restore(){
  const p=new URLSearchParams(window.location.search);
  if(['full','common_worry'].includes(p.get('inputs')))state.family=p.get('inputs');
  if(['explore','compare'].includes(p.get('view')))state.view=p.get('view');
  const years=state.family==='full'?[2021,2023,2025]:[2019,2021,2023,2025];
  const year=Number(p.get('wave'));state.year=years.includes(year)?year:2025;
  const earlier=Number(p.get('earlier'));state.earlier=years.slice(0,-1).includes(earlier)?earlier:2023;
  const cluster=Number(p.get('cluster'));state.cluster=Number.isInteger(cluster)&&cluster>=0&&cluster<model().k?cluster:0;
 }
 root.querySelector('[role="tablist"]').addEventListener('keydown',event=>{
  const buttons=[el('aw-tab-explore'),el('aw-tab-compare')];let next;
  if(event.key==='ArrowRight'||event.key==='ArrowLeft')next=state.view==='explore'?1:0;
  else if(event.key==='Home')next=0;else if(event.key==='End')next=1;else return;
  event.preventDefault();buttons[next].click();buttons[next].focus();
 });
 window.addEventListener('popstate',()=>{restore();render();});
 restore();render();
})();
