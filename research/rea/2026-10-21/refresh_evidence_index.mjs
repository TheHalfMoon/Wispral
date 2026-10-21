// Refresh current document hashes; preserve original trial results and pins.
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';
const root=path.resolve('.'),dir=path.join(root,'research/rea/2026-10-21'),file=path.join(dir,'EVIDENCE_INDEX.json');
const index=JSON.parse(fs.readFileSync(file));
const paths=fs.readdirSync(dir).filter(f=>/\.(md|json|mjs|py)$/.test(f)&&f!=='EVIDENCE_INDEX.json').map(f=>'research/rea/2026-10-21/'+f);
for(const f of ['WISPRAL_PLATFORM_ARCHITECTURE_REPLAN.md','WISPRAL_MASTER_PLAN_REBUILT.md','WISPRAL_COPY_FIRST_WORK_PACKETS.md','WISPRAL_GOVERNANCE_AMENDMENT_PROPOSAL.md','WISPRAL_MODEL_ROUTING_CONTRACTS.md'])paths.push('docs/strategy/'+f);
for(const f of fs.readdirSync(path.join(root,'docs/adr')).filter(f=>/^000[12]-/.test(f)))paths.push('docs/adr/'+f);
index.files=paths.sort().map(p=>{const b=fs.readFileSync(path.join(root,p));return{path:p,bytes:b.length,sha256:crypto.createHash('sha256').update(b).digest('hex')};});
index.repair={external_review:{pr:125,head:'3de63649256da4004d02fa7147daf714d8b65265',reviewed_original_head:'f36338138f4b4a872b05393b5cab03856dd7bf8e',state:'UNMERGED_REVISE_RETAINED'},traceability:'research/rea/2026-10-21/OPUS_REPAIR_TRACEABILITY.md',source_rows:75,source_pins_preserved:true,rea_restarted:false,implementation_authorized:false,internal_review:'NOT_INDEPENDENT',new_fit_probe:'fit-input-boundary-results.json',governance_graph:'packet-authorities.json'};
fs.writeFileSync(file,JSON.stringify(index,null,2)+'\n');console.log('Refreshed '+index.files.length+' artifact hashes; original trials retained');
