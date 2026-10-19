/* One frozen specification. All inputs are country aggregates; no fitting. */
function wrpResponseTools(data){
 const source=data.responses, n=data.countries.length, alpha=source.alphas.T5;
 if(!source||source.shape[1]!==32||!Number.isFinite(alpha))throw new Error('Missing 32-value WARM-5 country response reference.');
 if(source.country_order.some((iso,i)=>iso!==data.countries[i].iso))throw new Error('Country order differs from the map.');
 const bytes=Uint8Array.from(atob(source.probabilities_f64_base64),c=>c.charCodeAt(0));
 if(bytes.length!==n*32*8)throw new Error('Unexpected response reference length.');
 const view=new DataView(bytes.buffer), q=Array.from({length:n},()=>[]);
 for(let i=0;i<n;i++)for(let j=0;j<32;j++)q[i][j]=view.getFloat64((i*32+j)*8,true);
 const matrices={};
 for(const key of ['worry','self','known','T5'])matrices[key]=Array.from({length:n},()=>Array(n).fill(0));
 for(let i=0;i<n;i++)for(let j=i+1;j<n;j++){
  let w=0,s=0,k=0;
  // Six worry distributions: three categories each, with total variation / 2.
  for(let f=0;f<6;f++)for(let r=0;r<3;r++)w+=Math.abs(q[i][3*f+r]-q[j][3*f+r])/12;
  // Binary harm needs only P(harm=1); total variation is |p_i-p_j|.
  for(let f=0;f<7;f++){
   s+=Math.abs(q[i][18+f]-q[j][18+f])/7;
   k+=Math.abs(q[i][25+f]-q[j][25+f])/7;
  }
  const values={worry:w,self:s,known:k,T5:alpha*w+(1-alpha)*(s+k)/2};
  for(const key of Object.keys(values))matrices[key][i][j]=matrices[key][j][i]=values[key];
 }
 // Preserve the approved fixed calibration. Changing the model selector or
 // country scope must never change the meaning of a displayed number.
 const medians=data.reference_medians;
 const maximum=matrix=>matrix.reduce((m,row)=>Math.max(m,...row),0);
 const diameters={responses:{overall:maximum(matrices.T5)},profiles:{overall:maximum(data.distances.T5)}};
 for(const key of ['worry','self','known'])diameters.responses[key]=maximum(matrices[key]);
 function scale(basis,component='overall'){
  const referenceMedian=medians[basis][basis==='profiles'?'overall':component];
  if(!(referenceMedian>0))throw new Error('Invalid fixed reference median.');
  return {referenceMedian,normalize:value=>value/referenceMedian};
 }
 const labels={worry:'Worry',self:'Personal harm',known:'Known-person harm',overall:'Overall'};
 const metric=(basis,model,component)=>basis==='profiles'?data.distances.T5:matrices[component==='overall'?'T5':component];
 const caches=new Map();
 function statistics(basis,model,component,scope='all_countries_post_validation'){
  const key=[basis,component,scope].join(':');
  if(caches.has(key))return caches.get(key);
  const selected=data.countries.map((c,i)=>({c,i})).filter(x=>scope!=='development'||x.c.split==='train').map(x=>x.i);
  const matrix=metric(basis,'T5',component),pool=[];
  for(let a=0;a<selected.length;a++)for(let b=a+1;b<selected.length;b++)pool.push(matrix[selected[a]][selected[b]]);
  pool.sort((a,b)=>a-b);
  const percentile=value=>{let lo=0,hi=pool.length;while(lo<hi){const mid=(lo+hi)>>1;if(pool[mid]<=value)lo=mid+1;else hi=mid;}return 100*lo/pool.length;};
  const result={matrix,selected,pairCount:pool.length,percentile,
   neighbours:i=>selected.filter(j=>j!==i).sort((a,b)=>matrix[i][a]-matrix[i][b]||data.countries[a].iso.localeCompare(data.countries[b].iso))};
  caches.set(key,result);return result;
 }
 const components=(i,j)=>({worry:matrices.worry[i][j],self:matrices.self[i][j],known:matrices.known[i][j],T5:matrices.T5[i][j]});
 function componentText(i,j){const v=components(i,j);return `Worry ${(100*v.worry).toFixed(2)} · Personal harm ${(100*v.self).toFixed(2)} pp · Known-person harm ${(100*v.known).toFixed(2)} pp`;}
 return {matrices,labels,metric,statistics,components,componentText,scale,diameters,medians,
  method:basis=>basis==='profiles'?'Median-relative Hellinger distance':'Median-relative total variation distance',
  title:(basis,model,component)=>basis==='profiles'?'WARM-5 · five frozen profiles':component==='overall'?'WARM-5 · overall worry and harm':`${labels[component]} · original responses`,
  description:(basis,model,component)=>basis==='profiles'?'Compares country proportions across the same five frozen WARM-5 profiles.':component==='overall'?`One fixed WARM-5 allocation: worry ${(100*alpha).toFixed(2)}%; personal harm ${(50*(1-alpha)).toFixed(2)}%; known-person harm ${(50*(1-alpha)).toFixed(2)}%.`:'Uses only this response component; it is not a different clustering model.',
  fingerprint:source.fingerprint};
}
