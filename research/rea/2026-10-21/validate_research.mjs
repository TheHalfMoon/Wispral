// Research-bundle integrity checks, not a product/release gate.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const root=path.resolve(process.argv[2]||'.');
const research=path.join(root,'research/rea/2026-10-21');
const failures=[];
const checked=[];
function walk(p){return fs.readdirSync(p,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path.join(p,e.name)):[path.join(p,e.name)]);}
const documents=[...walk(research),...['WISPRAL_PLATFORM_ARCHITECTURE_REPLAN.md','WISPRAL_MASTER_PLAN_REBUILT.md','WISPRAL_COPY_FIRST_WORK_PACKETS.md','WISPRAL_GOVERNANCE_AMENDMENT_PROPOSAL.md'].map(f=>path.join(root,'docs/strategy',f)),path.join(root,'docs/adr/0001-proposed-donor-boundaries-for-platform-replan.md')];
for(const p of documents){
 const text=fs.readFileSync(p,'utf8');
 if(p.endsWith('.json')){try{JSON.parse(text);}catch(e){failures.push({file:path.relative(root,p),kind:'JSON_PARSE',message:e.message});}}
 if(/(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-proj-[A-Za-z0-9_-]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)/.test(text))failures.push({file:path.relative(root,p),kind:'POTENTIAL_SECRET'});
 if(p.endsWith('.md')){
  for(const m of text.matchAll(/\]\(([^)]+)\)/g)){
   const href=m[1].replace(/^<|>$/g,'').split(/\s+"/)[0];
   if(/^[a-z][a-z0-9+.-]*:/i.test(href)||href.startsWith('#'))continue;
   const local=decodeURIComponent(href.split('#')[0]);
   if(!local)continue;
   const target=path.resolve(path.dirname(p),local);
   if(!fs.existsSync(target))failures.push({file:path.relative(root,p),kind:'MISSING_LOCAL_LINK',href});
  }
 }
 checked.push(path.relative(root,p).replaceAll('\\','/'));
}
const index=JSON.parse(fs.readFileSync(path.join(research,'EVIDENCE_INDEX.json')));
for(const f of index.files){const p=path.join(root,f.path);if(!fs.existsSync(p)){failures.push({kind:'MISSING_INDEXED_FILE',file:f.path});continue;}const bytes=fs.readFileSync(p);if(crypto.createHash('sha256').update(bytes).digest('hex')!==f.sha256||bytes.length!==f.bytes)failures.push({kind:'INDEX_HASH_MISMATCH',file:f.path});}
const catalog=JSON.parse(fs.readFileSync(path.join(research,'source-catalog.json')));
if(catalog.records.length!==132)failures.push({kind:'CATALOG_COUNT',actual:catalog.records.length});
for(const s of catalog.records){if(s.sha&&!/^[a-f0-9]{40}$/.test(s.sha))failures.push({kind:'INVALID_SOURCE_PIN',repo:s.requested});if(s.tree_truncated)failures.push({kind:'TRUNCATED_TREE',repo:s.requested});}
const transplants=JSON.parse(fs.readFileSync(path.join(research,'source-transplants.json'))).rows;
const seen=new Set();for(const r of transplants){if(seen.has(r.id))failures.push({kind:'DUPLICATE_MECHANISM_ID',id:r.id});seen.add(r.id);for(const s of r.sources||[])if(!s.path||!s.url||!s.sha256)failures.push({kind:'INCOMPLETE_SOURCE_IDENTITY',id:r.id});}
const result={status:failures.length?'FAIL':'PASS',scope:'Bundle JSON, local links, indexed hashes, pinned identities, unique source mechanism IDs and bounded secret-pattern scan only; no product/runtime/security/release approval.',files_checked:checked.length,indexed_files:index.files.length,catalog_rows:catalog.records.length,transplant_rows:transplants.length,failures};
console.log(JSON.stringify(result,null,2));if(failures.length)process.exitCode=1;
