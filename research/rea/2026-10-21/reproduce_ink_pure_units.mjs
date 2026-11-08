// Research-only reproduction: exact public source files, builtin Node tests, no package install.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';
const destination=process.argv[2];
if(!destination||destination==='--help'){console.log('Usage: node reproduce_ink_pure_units.mjs ABSOLUTE_NEW_SCRATCH_DIRECTORY');process.exit(destination?0:2);}
if(!path.isAbsolute(destination)||fs.existsSync(destination))throw Error('Select an absolute, absent disposable directory; existing paths are refused.');
const pin="e4280ada144f04f20dad0bd32eaf22272f9c77b8";
const files=[
  {
    "path": "LICENSE",
    "sha256": "ecf1a12d3dc51085d2f3a720dc177c7da3cd075ea3fadcc6a1b719fb44ed30e0"
  },
  {
    "path": "package.json",
    "sha256": "619c02914ef606ccc2d5ef02e128419ca7918ecbc13840e103fea9d26d57510d"
  },
  {
    "path": "src/helpers/windowsPasteTarget.js",
    "sha256": "dc710017c902366b6d45f20b5b89a0c152ddbda617890b1d816b69b43aea9648"
  },
  {
    "path": "src/helpers/recordingGuard.js",
    "sha256": "a9b60c5b821cb99346b2060959f163ff617fb2e55e9e8d7ddbaedffe2517eb6d"
  },
  {
    "path": "src/helpers/hotkeyRepeatGate.js",
    "sha256": "4fe4433500a216efb46adc0b09cdab347e17795da401dcb28c90aed1d4ea7e4e"
  },
  {
    "path": "test/helpers/windowsPasteTarget.test.js",
    "sha256": "14e9ed9ebd299c13c689baea2fb450d7e254c2c2fd12943e8ddebe651f6bdb43"
  },
  {
    "path": "test/helpers/recordingGuard.test.js",
    "sha256": "4c1139c93167f0885cc59e9c7e04db936cdc0a9ed5145ad8c7d49acbdad3ae56"
  },
  {
    "path": "test/helpers/hotkeyRepeatGate.test.js",
    "sha256": "6a0769a73ca5ab0fc833fa79999b6bb3b1d16021460021072cbbbea9a9752a36"
  }
];
fs.mkdirSync(destination,{recursive:true});
for(const f of files){const url='https://raw.githubusercontent.com/OpenWhispr/openwhispr/'+pin+'/'+f.path;const response=await fetch(url);if(!response.ok)throw Error('Fetch failed '+response.status+' '+f.path);const bytes=Buffer.from(await response.arrayBuffer());if(crypto.createHash('sha256').update(bytes).digest('hex')!==f.sha256)throw Error('SHA256 mismatch '+f.path);const target=path.join(destination,f.path);fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,bytes);}
const tests=files.filter(f=>f.path.endsWith('.test.js')).map(f=>path.join(destination,f.path));
const result=spawnSync(process.execPath,['--test',...tests],{encoding:'utf8',timeout:30000,env:{...process.env,NODE_OPTIONS:''}});
const report={source:'OpenWhispr/openwhispr',pin,node:process.version,platform:process.platform,architecture:process.arch,files,exit_code:result.status,stdout:result.stdout,stderr:result.stderr,claim:'Pure helper unit tests only; no native app/audio/insertion/latency verification.'};
fs.writeFileSync(path.join(destination,'test-result.json'),JSON.stringify(report,null,2)+'\n');
process.stdout.write(result.stdout||'');process.stderr.write(result.stderr||'');process.exitCode=result.status??1;
