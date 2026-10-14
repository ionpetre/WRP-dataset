/* Exact aggregate response distributions; no respondent data or fitting. */
function wrpResponseTools(data){
 const source=data.responses;
 if(!source||source.shape[1]!==46)throw new Error('Missing 46-category country response reference.');
 if(source.country_order.some((iso,i)=>iso!==data.countries[i].iso))throw new Error('Country response order differs from map order.');
 const bytes=Uint8Array.from(atob(source.probabilities_f64_base64),c=>c.charCodeAt(0));
 const view=new DataView(bytes.buffer),n=source.shape[0],q=Array.from({length:n},()=>[]);
 if(bytes.length!==n*46*8)throw new Error('Unexpected response reference length.');
 for(let i=0;i<n;i++)for(let j=0;j<46;j++)q[i][j]=view.getFloat64((i*46+j)*8,true);
 const matrices={};
 for(const key of ['worry','self','known','B','E'])matrices[key]=Array.from({length:n},()=>Array(n).fill(0));
 for(let i=0;i<n;i++)for(let j=i+1;j<n;j++){
  let offset=0,w=0,s=0,k=0;
  for(let f=0;f<20;f++){
   const count=source.category_counts[f];let tv=0;
   for(let r=0;r<count;r++)tv+=Math.abs(q[i][offset+r]-q[j][offset+r])/2;
   if(f<6)w+=tv/6;else if(f<13)s+=tv/7;else k+=tv/7;
   offset+=count;
  }
  const values={worry:w,self:s,known:k,B:.5*w+.25*s+.25*k,E:.75*w+.125*s+.125*k};
  for(const key of Object.keys(values))matrices[key][i][j]=matrices[key][j][i]=values[key];
 }
 const caches=new Map();
 const labels={worry:'Worry',self:'Personal harm',known:'Known-person harm',overall:'Overall'};
 const indices=scope=>data.countries.map((c,i)=>({c,i})).filter(x=>scope!=='development'||x.c.split==='train').map(x=>x.i);
 const metric=(basis,model,component)=>basis==='profiles'?data.distances[model]:matrices[component==='overall'?model:component];
 function statistics(basis,model,component,scope='all_countries_post_validation'){
  const id=[basis,component==='overall'?model:component,scope].join(':');
  if(caches.has(id))return caches.get(id);
  const selected=indices(scope),matrix=metric(basis,model,component),pool=[];
  for(let a=0;a<selected.length;a++)for(let b=a+1;b<selected.length;b++)pool.push(matrix[selected[a]][selected[b]]);
  pool.sort((a,b)=>a-b);
  const percentile=value=>{let lo=0,hi=pool.length;while(lo<hi){const mid=(lo+hi)>>1;if(pool[mid]<=value)lo=mid+1;else hi=mid;}return 100*lo/pool.length;};
  const result={matrix,selected,pairCount:pool.length,percentile,
   neighbours:i=>selected.filter(j=>j!==i).sort((a,b)=>matrix[i][a]-matrix[i][b]||data.countries[a].iso.localeCompare(data.countries[b].iso)),
   range:i=>{const values=selected.map(j=>matrix[i][j]);return [Math.min(...values),Math.max(...values)];}};
  caches.set(id,result);return result;
 }
 function components(i,j){return {worry:matrices.worry[i][j],self:matrices.self[i][j],known:matrices.known[i][j],B:matrices.B[i][j],E:matrices.E[i][j]};}
 function componentText(i,j){const v=components(i,j);return `W ${(100*v.worry).toFixed(2)} · Self ${(100*v.self).toFixed(2)} pp · Known ${(100*v.known).toFixed(2)} pp`;}
 return {matrices,labels,metric,statistics,components,componentText,
  title:(basis,model,component)=>basis==='profiles'?`${model} · frozen profile mixture (Hellinger)`:
   component==='overall'?`${model} allocation · ${model==='B'?'50/25/25':'75/12.5/12.5'} worry/self/known`:`${labels[component]} · original responses`,
  fingerprint:source.fingerprint};
}
