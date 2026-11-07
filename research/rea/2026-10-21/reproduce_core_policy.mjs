// Research-only probe; Node 24 TypeScript type stripping. Uses caller-supplied authorized pinned source; no download/install.
import fs from'node:fs';import crypto from'node:crypto';import path from'node:path';import {pathToFileURL}from'node:url';import assert from'node:assert/strict';
const sourceRoot=process.argv[2],output=process.argv[3];
if(!sourceRoot||!output||!path.isAbsolute(sourceRoot)||!path.isAbsolute(output)||fs.existsSync(output))throw Error('Usage: node reproduce_core_policy.mjs ABSOLUTE_PINNED_SOURCE_DIRECTORY ABSOLUTE_NEW_RESULT_JSON; output must not exist');
const dir=sourceRoot;
const expected={
  "policy.ts": "eb2e32a54229beac406efb5461190a6c9ade8ebae0407f8d64ff67753fcb1518",
  "address.ts": "93ae122ac9b8f0529908a973eeee009ac23cdf0b579b4e1c932d4ca8b84175b3",
  "errors.ts": "a1003fcf41164cf2a1da3bfc67834d12a098857af7f088905b3b87c1a9328024",
  "types.ts": "2e68e1c7b0502973e73335bd8b39c7e276c1a73b66a5b632e97e965c091eea8b",
  "validation.ts": "b6dd8fd46adec96010826eb42999b35d4803c7e6d52131a677d6b619b0ae354a"
};
for(const [file,digest]of Object.entries(expected)){if(crypto.createHash('sha256').update(fs.readFileSync(path.join(dir,file))).digest('hex')!==digest)throw Error('Source digest mismatch '+file);}
const {defaultNetworkPolicy,normalizeNetworkPolicy,evaluateUrl,evaluateResolved}=await import(pathToFileURL(dir+'/policy.ts'));
const result={id:'CORE-NETWORK-01',method:'UNCHANGED_PINNED_SOURCE_MODULE_WITH_INDEPENDENT_SYNTHETIC_FIXTURES',status:'REPRODUCED',captured_at:new Date().toISOString(),node:process.version,platform:process.platform,arch:process.arch,repo:'TheHalfMoon/Ninerr',sha:'8cba15c4e4af40b12476433a49e20a1696cfc0f8',tests:[],limitations:['No socket was opened by this pure decision module; no enforcement of real outbound requests was tested.','No integrated Wispral security, tenant isolation or release gate is satisfied by these probes.']};
function test(name,run){try{run();result.tests.push({name,status:'PASS'});}catch(e){result.tests.push({name,status:'FAIL',error:e.message});result.status='FAILED';}}
const policy=normalizeNetworkPolicy({schemaVersion:1,mode:'allowlist',grants:[{id:'g1',capability:'provider.inference',scheme:'https',host:'api.example.com',port:null,allowPrivateNetwork:false,purpose:'synthetic test'}]});
test('offline policy refuses remote and loopback provider routes',()=>{for(const url of['https://example.com','http://127.0.0.1:11434'])assert.equal(evaluateUrl(defaultNetworkPolicy(),{capability:'provider.inference',url}).allowed,false);});
test('allowed route remains purpose/capability scoped',()=>{assert.equal(evaluateUrl(policy,{capability:'provider.inference',url:'https://api.example.com/v1'}).allowed,true);assert.equal(evaluateUrl(policy,{capability:'asset.fetch',url:'https://api.example.com/v1'}).allowed,false);});
test('credentials and misleading host suffix cannot widen route',()=>{for(const url of['https://name:secret@api.example.com/','https://api.example.com.evil.invalid/'])assert.equal(evaluateUrl(policy,{capability:'provider.inference',url}).allowed,false);});
test('private or mixed DNS answers fail pure postresolution decision',()=>{const issued=evaluateUrl(policy,{capability:'provider.inference',url:'https://api.example.com'});for(const ips of[['127.0.0.1'],['169.254.169.254'],['93.184.216.34','10.0.0.1'],[]])assert.equal(evaluateResolved(issued,ips).allowed,false);});
test('caller-crafted allowed decision is refused',()=>{assert.equal(evaluateResolved({allowed:true,capability:'provider.inference',host:'api.example.com'},['93.184.216.34']).allowed,false);});
test('unknown policy key is rejected',()=>assert.throws(()=>normalizeNetworkPolicy({schemaVersion:1,mode:'offline',grants:[],allowEverything:true})));
result.passed=result.tests.filter(t=>t.status==='PASS').length;result.total=result.tests.length;result.source_sha256=expected;fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));if(result.status==='FAILED')process.exitCode=1;
