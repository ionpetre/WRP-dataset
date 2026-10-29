(() => {
 const target=document.getElementById('wave-models');
 const data=window.WRP_WAVE_DATA;
 if(!target||!data)return;
 const rows=Object.values(data.models).sort((a,b)=>a.year-b.year||a.family.localeCompare(b.family));
 for(const m of rows){
  const tr=document.createElement('tr');
  [m.year,m.family==='full'?'Worry + harm':'Worry only',m.k,m.respondents.toLocaleString('en-US'),m.countries].forEach(value=>{const cell=document.createElement('td');cell.textContent=value;tr.appendChild(cell);});
  target.appendChild(tr);
 }
})();
