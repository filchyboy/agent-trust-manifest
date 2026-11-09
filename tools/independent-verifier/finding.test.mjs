import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {inspectFinding} from './finding.mjs';
const dir=fileURLToPath(new URL('../../examples/signing/',import.meta.url));
const read=name=>readFileSync(dir+name);
const args=[read('finding.json'),read('finding.jws'),read('assessor.jwks.json'),read('manifest.json'),
  'https://consumer-demo.example','https://assessor.example',['https://assessor.example'],1791309600];

test('offline evidence attribution, applicability, visitor selection and truth remain separate',()=>{
  const r=inspectFinding(...args);
  assert.equal(r.authentication.state,'authenticated');assert.equal(r.authentication.claims_truth,'unresolved');
  assert.equal(r.applicability,'matched');assert.equal(r.acceptance,'accepted_for_claim');
  assert.equal(r.independence,'unproven');assert.equal(r.access_granted,false);
  const unselected=[...args];unselected[6]=[];
  const other=inspectFinding(...unselected);
  assert.equal(other.authentication.state,'authenticated');assert.equal(other.applicability,'matched');
  assert.equal(other.acceptance,'unresolved');assert.equal(other.reason,'assessor_not_selected');
});

test('visitor age policy tightens acceptance without changing authenticated applicability',()=>{
  const accepted=inspectFinding(...args,300),old=inspectFinding(...args,299);
  assert.equal(accepted.acceptance,'accepted_for_claim');
  assert.equal(old.authentication.state,'authenticated');assert.equal(old.applicability,'matched');
  assert.equal(old.acceptance,'unresolved');assert.equal(old.reason,'finding_observation_too_old');
  for (const value of [true,-1,86401,Infinity,0.5])
    assert.equal(inspectFinding(...args,value).reason,'invalid_observation_age_policy');
});

test('missing authentication material and report-selected URLs never cause retrieval',()=>{
  const oldFetch=globalThis.fetch;globalThis.fetch=()=>{throw new Error('network attempted');};
  try {
    const missing=[...args];missing[1]=null;
    const r=inspectFinding(...missing);
    assert.equal(r.authentication.reason,'signature_not_supplied');assert.equal(r.acceptance,'unresolved');
    const missingKeys=[...args];missingKeys[2]=null;
    assert.equal(inspectFinding(...missingKeys).authentication.reason,'keys_not_supplied');
    assert.equal(inspectFinding(...args).acceptance,'accepted_for_claim');
  } finally {globalThis.fetch=oldFetch;}
});

test('finding CLI reports acceptance only for the explicit selected assessor and policy',()=>{
  const cli=fileURLToPath(new URL('./finding-cli.mjs',import.meta.url));
  const command=[cli,'--finding',dir+'finding.json','--signature',dir+'finding.jws','--jwks',dir+'assessor.jwks.json',
    '--manifest',dir+'manifest.json','--platform-origin',args[4],'--assessor-origin',args[5],'--at',String(args[7])];
  let r=spawnSync(process.execPath,command,{encoding:'utf8'});
  assert.equal(r.status,1,r.stderr);assert.equal(JSON.parse(r.stdout).reason,'assessor_not_selected');
  r=spawnSync(process.execPath,[...command,'--trusted-assessor',args[5]],{encoding:'utf8'});
  assert.equal(r.status,0,r.stderr);assert.equal(JSON.parse(r.stdout).access_granted,false);
  r=spawnSync(process.execPath,[...command,'--trusted-assessor',args[5],'--max-finding-age-seconds','299'],{encoding:'utf8'});
  assert.equal(r.status,1,r.stderr);assert.equal(JSON.parse(r.stdout).reason,'finding_observation_too_old');
});


test('publisher authentication is independent of finding issuance and selected acceptance',()=>{
  const cli=fileURLToPath(new URL('./finding-cli.mjs',import.meta.url));
  const command=[cli,'--finding',dir+'finding.json','--signature',dir+'finding.jws','--jwks',dir+'assessor.jwks.json',
    '--manifest',dir+'manifest.json','--platform-origin',args[4],'--assessor-origin',args[5],'--at',String(args[7]),
    '--manifest-signature',dir+'manifest.jws','--manifest-jwks',dir+'publisher.jwks.json','--trusted-assessor',args[5]];
  let r=spawnSync(process.execPath,command,{encoding:'utf8'});
  assert.equal(r.status,0,r.stderr);
  let report=JSON.parse(r.stdout);
  assert.equal(report.manifest_authentication.state,'authenticated');assert.equal(report.authentication.state,'authenticated');
  assert.equal(report.acceptance,'accepted_for_claim');assert.equal(report.independence,'unproven');assert.equal(report.access_granted,false);
  const wrong=[...command];wrong[wrong.indexOf('--manifest-jwks')+1]=dir+'assessor.jwks.json';
  r=spawnSync(process.execPath,wrong,{encoding:'utf8'});report=JSON.parse(r.stdout);
  assert.equal(r.status,1);assert.equal(report.manifest_authentication.state,'invalid');
  assert.equal(report.authentication.state,'authenticated');assert.equal(report.access_granted,false);
  const wrongAssessor=[...command];wrongAssessor[wrongAssessor.indexOf('--jwks')+1]=dir+'publisher.jwks.json';
  r=spawnSync(process.execPath,wrongAssessor,{encoding:'utf8'});report=JSON.parse(r.stdout);
  assert.equal(r.status,1);assert.equal(report.manifest_authentication.state,'authenticated');
  assert.equal(report.authentication.state,'invalid');assert.equal(report.acceptance,'unresolved');
  assert.equal(report.access_granted,false);
});
