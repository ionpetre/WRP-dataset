// Browser verification of the published primary model; no network or fitting.
const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {pathToFileURL}=require('node:url');
const root=path.resolve(__dirname,'..'),pub=fs.existsSync(path.join(root,'docs'))?root:path.join(root,'github_publication');
const screenshots=path.join(root,'.t5_publication_20261016');fs.mkdirSync(screenshots,{recursive:true});
(async()=>{
 const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--allow-file-access-from-files']});
 try{
  const context=await browser.newContext({viewport:{width:1280,height:1000}}),external=[],errors=[];
  await context.route(/^https?:/,route=>{external.push(route.request().url());route.abort();});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  await page.goto(pathToFileURL(path.join(pub,'docs/index.html')).href);
  assert.equal(await page.locator('[data-model="T5"]').getAttribute('aria-pressed'),'true');
  assert.equal(await page.locator('#pf-cards button').count(),5);
  const data=await page.locator('#wrp-profile-data').evaluate(el=>JSON.parse(el.textContent));
  const pointer=JSON.parse(fs.readFileSync(path.join(pub,'course_artifacts/week05_t5_secondary_transfer/current_run.json')));
  assert.ok((await page.locator('#pf-spec').innerText()).includes('secondary'));
  for(const model of ['T5','B','E']){
   await page.locator('[data-model="'+model+'"]').click();
   assert.equal(await page.locator('#pf-cards button').count(),data.models[model].k);
   for(const profile of data.models[model].profiles){
    await page.locator('#pf-cards [data-profile="'+profile.id+'"]').click();
    assert.ok((await page.locator('#pf-detail h2').innerText()).includes(profile.name));
    assert.equal(await page.locator('#pf-detail .pf-stack').count(),12);
    assert.equal(await page.locator('#pf-detail .pf-harm-track').count(),14);
    assert.equal(await page.locator('#pf-detail .pf-anchor').count(),3);
    const shown=await page.locator('#pf-detail .pf-stack').evaluateAll(els=>els.filter((_,i)=>i%2===0).map(el=>[...el.querySelectorAll('span')].map(s=>parseFloat(s.style.width)/100)));
    shown.forEach((r,i)=>r.forEach((v,j)=>assert.ok(Math.abs(v-profile.worry[i][j])<1e-6)));
   }
  }
  await page.locator('[data-model="T5"]').click();
  await page.locator('details summary').click();
  assert.equal(await page.locator('#pf-evidence tbody tr').count(),6);
  for(const width of [360,768,1280])for(const theme of ['light','dark']){
   await page.setViewportSize({width,height:1000});await page.emulateMedia({colorScheme:theme});
   assert.ok(await page.locator('body').evaluate(el=>el.scrollWidth-el.clientWidth)<=2,'Horizontal overflow at '+width);
   if(width!==768)await page.screenshot({path:path.join(screenshots,'T5-'+width+'-'+theme+'.png'),fullPage:true});
  }
  for(const file of ['countries.html','country-income.html']){
   await page.goto(pathToFileURL(path.join(pub,'docs',file)).href);
   assert.ok((await page.locator('#historical-distance-note').innerText()).includes('not T5'));
   assert.equal(await page.locator('.research-view[aria-current="page"]').count(),1);
  }
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
  const receipt={status:'passed',primary:'T5',profiles_checked:17,models:['T5','B','E'],widths:[360,768,1280],themes:['light','dark'],external_requests:0,runtime_errors:0,country_maps_labelled_historical:true};
  fs.writeFileSync(path.join(pub,'publication_profile_test.json'),JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify(receipt,null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
