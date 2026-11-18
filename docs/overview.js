/* Overview figures share the detailed explorer's aggregate source. */
(()=>{'use strict';
 const data=window.WRP_WAVE_DATA,select=document.getElementById('overview-cluster');
 if(!data||!select)return;
 for(let cluster=0;cluster<7;cluster++){
  const card=document.getElementById('cluster-c'+cluster),score=data.overviewRuleScores?.[cluster];
  if(!card||!score)continue;
  card.querySelector('.aw-description-head strong').textContent=(100*data.shares.full['2025'][cluster]).toFixed(2)+'%';
  card.querySelector('[data-overview-precision]').textContent=(100*score.precision).toFixed(2)+'%';
  card.querySelector('[data-overview-coverage]').textContent=(100*score.coverage).toFixed(2)+'%';
 }
 const years=[2021,2023,2025],names=["Traffic", "Food and water", "Crime", "Severe weather", "Mental health", "Known-person harm", "Very-worried answer count"];
 function render(){
  const cluster=Number(select.value),values=years.map(year=>data.shares.full[year][cluster]);
  document.getElementById('overview-trend-title').textContent='Cluster C'+cluster+' · '+names[cluster];
  const bars=document.getElementById('overview-bars');
  bars.setAttribute('aria-label','Cluster C'+cluster+' · '+names[cluster]+': '+values.map((v,i)=>(100*v).toFixed(2)+'% in '+years[i]).join(', ')+'.');
  bars.innerHTML=values.map((v,i)=>'<div class="aw-overview-column"><div class="aw-overview-bar" style="height:'+(100*v/.4)+'%"><strong>'+(100*v).toFixed(2)+'%</strong></div><span>'+years[i]+'</span></div>').join('');
  const change=100*(values[2]-values[0]);
  document.getElementById('overview-change').textContent='2021 to 2025: '+(change>=0?'an increase':'a decrease')+' of '+Math.abs(change).toFixed(2)+' percentage points.';
 }
 select.addEventListener('change',render);render();
})();
