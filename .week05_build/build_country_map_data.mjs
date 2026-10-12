import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import atlas from './cartography_assets/world-countries-110m.mjs';
const require=createRequire(import.meta.url);
const topo=require('./cartography_assets/topojson-client.min.js');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const info=JSON.parse(fs.readFileSync(path.join(root,'.week05_build/country_map_numerical_data.json'),'utf8'));
const aliases={KOS:'XKX',SDS:'SSD',PSX:'PSE'};
for(const g of atlas.objects.features.geometries){g.properties.id=aliases[g.properties.id]||g.properties.id;}
const features=topo.feature(atlas,atlas.objects.features).features.filter(f=>f.properties.id!=='ATA');
const index=new Map(info.countries.map(c=>[c.iso,c]));
const regions=[];
for(const id of [...new Set(info.countries.map(c=>c.regionId))].sort((a,b)=>a-b)){
  const geometry=topo.merge(atlas,atlas.objects.features.geometries.filter(g=>index.get(g.properties.id)?.regionId===id));
  regions.push({type:'Feature',properties:{regionId:id,name:info.countries.find(c=>c.regionId===id).region},geometry});
}
const matched=new Set(features.map(f=>f.properties.id));
const missing=info.countries.filter(c=>!matched.has(c.iso)).map(c=>c.iso);
const data={...info,world:{type:'FeatureCollection',features},regions,tiny:[...new Set([...info.tiny,...missing])]};
const fragment=fs.readFileSync(path.join(root,'.week05_build/country-distance-map-template.html'),'utf8').replace('__WRP_MAP_DATA__',JSON.stringify(data));
const destination=path.join(root,'docs/country-profile-distance-map.html');
fs.writeFileSync(destination,fragment);
fs.writeFileSync(path.join(root,'.week05_build/country_map_geometry.json'),JSON.stringify({world:data.world,regions,missingCountryPolygons:missing,tiny:data.tiny}));
console.log(JSON.stringify({destination,bytes:Buffer.byteLength(fragment),countries:info.countries.length,regions:regions.length,missingCountryPolygons:missing}));
