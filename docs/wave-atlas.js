/* Survey aggregates. All analytical implementation is in the paper notebook. */
(()=>{'use strict';
 const root=document.getElementById('wrp-wave-atlas'),data=window.WRP_WAVE_DATA;
 if(!root||!data){if(root)root.textContent='The aggregate results could not be loaded.';return;}
 const el=id=>document.getElementById(id),pct=v=>(100*v).toFixed(2)+'%',num=v=>v.toLocaleString('en-US');
 const escape=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
 const nice={food:'Food',water:'Water',crime:'Crime',severe_weather:'Severe weather',traffic:'Traffic',mental_health:'Mental health',work:'Work'};
 const swatch=c=>'<span class="aw-swatch" style="background:var(--atlas-'+c+')"></span>';
 const state={view:'explore',family:'full',year:2025,earlier:2023,cluster:0};
 const model=(year=state.year)=>data.models[state.family+'_'+year];
 const name=c=>data.models[state.family+'_2025'].clusters[c].name;
 function save(){const url=new URL(location.href);for(const [key,value] of Object.entries({view:state.view,inputs:state.family,wave:state.year,earlier:state.earlier,cluster:state.cluster}))url.searchParams.set(key,value);try{history.replaceState(null,'',url);}catch(error){/* file:// may restrict URL changes. */}}
 function detail(){
  const m=model(),c=m.clusters[state.cluster];
  const worry=m.worryDomains.map((d,i)=>'<div class="aw-answer"><div class="aw-answer-label"><span>'+nice[d]+'</span><span>'+pct(c.worry[i][2])+' very worried</span></div><div class="aw-stack" role="img" aria-label="'+nice[d]+': '+c.worry[i].map((v,j)=>pct(v)+' '+['not','somewhat','very'][j]+' worried').join(', ')+'">'+c.worry[i].map((v,j)=>'<span style="width:'+100*v+'%;background:var(--atlas-'+['low','mid','blue'][j]+')"></span>').join('')+'</div></div>').join('');
  const harm=c.harm.length?'<section><h3>Reported harm</h3><div class="aw-legend">'+swatch('before')+'<span>Respondent</span>'+swatch('blue')+'<span>Someone personally known</span></div>'+['food','water','crime','severe_weather','traffic','mental_health','work'].map((d,i)=>'<div class="aw-harm-row"><span class="aw-harm-name">'+nice[d]+'</span><div>'+[0,1].map(j=>'<div class="aw-harm-line" role="img" aria-label="'+nice[d]+', '+['respondent','known person'][j]+': '+pct(c.harm[j][i])+'"><div class="aw-track"><div class="aw-fill '+(j===0?'aw-harm-personal':'')+'" style="width:'+100*c.harm[j][i]+'%"></div></div><span>'+pct(c.harm[j][i])+'</span></div>').join('')+'</div></div>').join('')+'<p class="aw-note">The two indicators concern different recipients. A report of both sets both to 1.</p></section>':'';
  const mapping=c.anchorId===null?'Independent 2019 alternative, without a claimed shared later-wave ID.':m.year===2025?'2025 reference ID C'+c.id+'.':'Corresponds to 2025 C'+c.anchorId+' by weighted point overlap.';
  const formula=escape(c.rule.text.replaceAll('_',' ').replaceAll('>=','≥').replaceAll('<=','≤'));
  el('aw-detail').innerHTML='<h2>'+m.year+' · C'+c.id+' · '+escape(c.name)+'</h2><p class="aw-muted aw-small">'+pct(c.share)+' of this model’s development population · '+mapping+'</p><div class="aw-detail-grid"'+(!harm?' style="grid-template-columns:1fr"':'')+'><section><h3>Worry responses</h3><div class="aw-legend">'+['Not worried','Somewhat worried','Very worried'].map((n,i)=>swatch(['low','mid','blue'][i])+n).join(' ')+'</div>'+worry+'</section>'+harm+'</div><section class="aw-rule"><h3>Boolean description</h3><p class="aw-rule-line">'+formula+'</p><dl class="aw-rule-scores"><div><dt>Precision</dt><dd>'+pct(c.rule.precision)+'</dd></div><div><dt>Coverage</dt><dd>'+pct(c.rule.coverage)+'</dd></div><div><dt>Condition cost</dt><dd>'+c.rule.cost+'</dd></div></dl><p class="aw-note">Scores use this model’s own development population. '+(m.family==='full'?'K counts known-person-harm domains out of seven. P counts personal-harm domains out of seven. V, N and A count very, not and at-least-somewhat worried answers across six worries.':'V, N and A count very, not and at-least-somewhat worried answers across five worries.')+' Short descriptions can overlap or leave members uncovered. They approximate the fitted labels.</p></section>';
 }
 function explore(){
  const m=model();
  el('aw-clusters').style.setProperty('--aw-columns',3);
  root.querySelectorAll('[data-year]').forEach(b=>{b.setAttribute('aria-pressed',String(Number(b.dataset.year)===state.year));});
  el('aw-availability').textContent='Six worries and all fourteen harm indicators.';
  el('aw-model-title').textContent=m.year+' · '+m.k+' clusters';
  el('aw-model-pop').textContent=num(m.respondents)+' development respondents · '+m.countries+' countries';
  el('aw-clusters').innerHTML=m.clusters.map(c=>'<button class="aw-cluster aw-interactive" type="button" data-cluster="'+c.id+'" aria-pressed="'+(c.id===state.cluster)+'"><span class="aw-card-top"><span class="aw-muted aw-small">C'+c.id+'</span><span class="aw-share">'+pct(c.share)+'</span></span><span class="aw-cname">'+escape(c.name)+'</span></button>').join('');
  el('aw-clusters').querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{state.cluster=Number(b.dataset.cluster);explore();save();}));
  el('aw-method').textContent='Each wave uses the same encoding and fits its centres independently. The same five rules apply in all three waves.';
  detail();
  const r=m.clusters[state.cluster].rule;
  if(r.reading){
   const p=document.createElement('p');
   p.className='aw-note';
   p.textContent=r.reading+(state.cluster===4?' Cost counts the three conditions in the Boolean formula.':'');
   el('aw-detail').appendChild(p);
  }
 }
 function compare(){
  const f=state.family,old=state.earlier,earlier=model(old),afterModel=model(2025),point=data.point[f+'_'+old];
  el('aw-point').textContent='Original point fits: ARI '+point.ARI.toFixed(2)+' · Optimally matched weighted agreement '+pct(point.weighted_agreement)+(old===2019?' · Separate 2019 alternative; correspondence is much weaker.':'');
  el('aw-overlap-note').textContent='Both models assign the same '+num(data.reference[f].respondents2025)+' respondents in '+data.reference[f].countries+' common development countries. Rows show where each earlier cluster falls under the fixed 2025 definition. Weighted row percentages sum to 100% before rounding.';
  el('aw-matrix').innerHTML='<table class="aw-matrix"><caption class="aw-small aw-muted" style="text-align:left;margin-bottom:8px">Rows: '+old+' model · Columns: 2025 model · Same reference answers</caption><thead><tr><th scope="col">Earlier cluster</th>'+afterModel.clusters.map(c=>'<th scope="col">C'+c.id+'<br>'+escape(c.name)+'</th>').join('')+'</tr></thead><tbody>'+data.overlap[f+'_'+old].map((row,i)=>'<tr><th scope="row">C'+i+' · '+escape(earlier.clusters[i].name)+'</th>'+row.map(v=>'<td style="--aw-cell:'+v*.45+'"><span>'+(100*v).toFixed(1)+'%</span></td>').join('')+'</tr>').join('')+'</tbody></table>';
  el('aw-stability').innerHTML='<h3>Agreement under country refitting</h3>'+data.stability[f+'_'+old].map((r,i)=>'<div class="aw-stab-row"><span>'+['Within '+old,old+' vs 2025','Within 2025'][i]+'</span><div class="aw-stab-track" role="img" aria-label="Median ARI '+r.median.toFixed(2)+', p10 '+r.p10.toFixed(2)+', p90 '+r.p90.toFixed(2)+'" style="--aw-left:'+100*r.p10+'%;--aw-range:'+100*(r.p90-r.p10)+'%;--aw-mid:'+100*r.median+'%"><span class="aw-stab-range"></span><span class="aw-stab-dot"></span></div><span>'+r.median.toFixed(2)+'</span></div>').join('')+'<div class="aw-stab-row aw-muted"><span>ARI · higher is closer</span><div style="display:flex;justify-content:space-between"><span>0</span><span>0.5</span><span>1</span></div><span></span></div>';
  const before=data.shares[f][old],after=data.shares[f]['2025'];
  el('aw-compare-key').innerHTML='<span>'+swatch('before')+old+'</span><span>'+swatch('blue')+'2025</span>';
  const ceil=Math.ceil(Math.max(...before,...after)*110/10)*10;
  el('aw-pairs').innerHTML='<div class="aw-pair-grid aw-pair-head"><span>2025 definition</span><span>Equal-country share · 0–'+ceil+'%</span><span>Change</span></div>'+before.map((v,i)=>{const delta=100*(after[i]-v);return '<div class="aw-pair-grid aw-pair"><div class="aw-pair-title"><small>C'+i+'</small>'+escape(name(i))+'</div><div class="aw-pair-plot">'+[v,after[i]].map((value,j)=>'<div class="aw-pair-bar" style="--aw-width:'+value*100/ceil*100+'%" role="img" aria-label="'+[old,2025][j]+': '+pct(value)+'"><span style="width:'+value*100/ceil*100+'%;background:var(--atlas-'+['before','blue'][j]+')"></span><em>'+pct(value)+'</em></div>').join('')+'</div><div class="aw-delta">'+(delta>0?'+':'')+delta.toFixed(2)+'<span class="aw-muted aw-small"> pp</span></div></div>';}).join('');
  el('aw-compare-note').textContent='Same '+data.reference[f].countries+' countries in every wave · Equal-country survey weights · 2025 definition held fixed. Changes are percentage points, without an individual transition interpretation.';
  el('aw-prevalence-method').textContent='Apply the fixed 2025 '+afterModel.k+'-cluster model unchanged to each wave’s own complete respondents. Average survey-weighted country shares over the common countries. This varies the respondent population while keeping the definition fixed. It differs from comparing independently fitted definitions above.';
 }
 function render(){
  el('aw-explore').hidden=state.view!=='explore';el('aw-compare').hidden=state.view!=='compare';
  ['explore','compare'].forEach(v=>{el('aw-tab-'+v).setAttribute('aria-selected',String(state.view===v));el('aw-tab-'+v).tabIndex=state.view===v?0:-1;});
  const years=state.family!=='common_worry'?[2021,2023]:[2019,2021,2023];if(!years.includes(state.earlier))state.earlier=2023;
  el('aw-earlier').innerHTML=years.map(y=>'<option value="'+y+'">'+y+(y===2019?' · separate alternative':'')+'</option>').join('');el('aw-earlier').value=state.earlier;
  explore();compare();
  const q=new URLSearchParams({inputs:state.family,wave:state.year});el('aw-country-link').href='./countries-by-wave.html?'+q;q.set('view','income');el('aw-income-link').href='./countries-by-wave.html?'+q;
 }
 function restore(){
  const p=new URLSearchParams(location.search);
  if(['explore','compare'].includes(p.get('view')))state.view=p.get('view');
  const years=state.family!=='common_worry'?[2021,2023,2025]:[2019,2021,2023,2025];
  state.year=years.includes(Number(p.get('wave')))?Number(p.get('wave')):2025;
  state.earlier=years.slice(0,-1).includes(Number(p.get('earlier')))?Number(p.get('earlier')):2023;
  const c=Number(p.get('cluster'));state.cluster=Number.isInteger(c)&&c>=0&&c<model().k?c:0;
 }
 root.querySelectorAll('[data-year]').forEach(b=>b.addEventListener('click',()=>{state.year=Number(b.dataset.year);state.cluster=0;render();save();}));
 ['explore','compare'].forEach(v=>el('aw-tab-'+v).addEventListener('click',()=>{if(v==='compare'&&state.view!=='compare'&&state.year!==2025)state.earlier=state.year;state.view=v;render();save();}));
 el('aw-earlier').addEventListener('change',()=>{state.earlier=Number(el('aw-earlier').value);compare();save();});
 root.querySelector('[role="tablist"]').addEventListener('keydown',event=>{let next;if(['ArrowRight','ArrowLeft'].includes(event.key))next=state.view==='explore'?1:0;else if(event.key==='Home')next=0;else if(event.key==='End')next=1;else return;event.preventDefault();el('aw-tab-'+['explore','compare'][next]).click();el('aw-tab-'+['explore','compare'][next]).focus();});
 window.addEventListener('popstate',()=>{restore();render();});restore();render();
})();
