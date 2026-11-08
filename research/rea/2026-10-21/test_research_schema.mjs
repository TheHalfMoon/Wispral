// Negative integrity fixtures, not product tests.
import fs from 'node:fs';import os from 'node:os';import path from 'node:path';import {spawnSync} from 'node:child_process';import assert from 'node:assert/strict';
const dir=path.resolve('research/rea/2026-10-21'),original=JSON.parse(fs.readFileSync(path.join(dir,'source-transplants.json')));
const scratch=fs.mkdtempSync(path.join(os.tmpdir(),'wispral-schema-'));
const cases=[];
try{
 for(const field of ['decision','runtime_status']){
  const data=structuredClone(original);delete data.rows[0][field];const fixture=path.join(scratch,field+'.json');fs.writeFileSync(fixture,JSON.stringify(data));
  const result=spawnSync(process.execPath,[path.join(dir,'validate_research.mjs'),'--transplants',fixture],{encoding:'utf8'});
  const parsed=JSON.parse(result.stdout);assert.notEqual(result.status,0);assert(parsed.failures.some(f=>f.kind===(field==='decision'?'MISSING_OR_INCONSISTENT_DECISION':'MISSING_RUNTIME_STATUS')));
  cases.push({field,status:'PASS',outcome:'missing field rejected'});
 }
 console.log(JSON.stringify({status:'PASS',cases,scope:'Schema negative fixtures only'},null,2));
}finally{if(path.dirname(scratch)===path.resolve(os.tmpdir())&&path.basename(scratch).startsWith('wispral-schema-'))fs.rmSync(scratch,{recursive:true});}
