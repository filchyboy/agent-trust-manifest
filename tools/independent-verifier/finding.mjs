// Independent offline finding applicability and visitor-selected acceptance.
import {createHash} from 'node:crypto';
import {readFileSync, readdirSync} from 'node:fs';
import Ajv2020 from 'ajv/dist/2020.js';
import {strictJSON, verify, Rejection} from './verifier.mjs';
import {canonicalOrigin} from './origins.mjs';
const need = (test, reason) => { if (!test) throw new Rejection(reason); };
const shape = (value, keys) => value !== null && typeof value === 'object' && !Array.isArray(value)
  && Object.keys(value).length === keys.length && keys.every(k => Object.hasOwn(value,k));
const FINDING = 'application/atm-finding+json';
let manifestValidator;
function validateManifest(value) {
  if (!manifestValidator) {
    try {
      const directory = new URL('../../schemas/', import.meta.url);
      const ajv = new Ajv2020({strict: false, validateFormats: false, coerceTypes: false, useDefaults: false, removeAdditional: false});
      for (const name of readdirSync(directory).filter(v => v.endsWith('.schema.json')))
        ajv.addSchema(JSON.parse(readFileSync(new URL(name,directory))));
      manifestValidator = ajv.getSchema('https://agenttrustmanifest.org/schemas/agent-trust-manifest.schema.json');
    } catch { throw new Rejection('local_schema_unavailable'); }
  }
  need(manifestValidator(value), 'invalid_manifest_schema');
}
function timestamp(value) {
  const m = typeof value === 'string' && /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?(Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/.exec(value);
  need(m && !value.endsWith('-00:00'), 'invalid_manifest_time');
  const [year,month,day,hour,minute,second] = m.slice(1,7).map(Number);
  const leap = year%4 === 0 && (year%100 !== 0 || year%400 === 0);
  const days = [31,leap?29:28,31,30,31,30,31,31,30,31,30,31];
  need(year>=1 && month>=1 && month<=12 && day>=1 && day<=days[month-1]
    && hour<=23 && minute<=59 && second<=59, 'invalid_manifest_time');
  const date = new Date(0); date.setUTCFullYear(year,month-1,day); date.setUTCHours(hour,minute,second,0);
  const offset = m[8] === 'Z' ? 0 : (m[8][0] === '+' ? 1 : -1)*(Number(m[8].slice(1,3))*3600+Number(m[8].slice(4))*60);
  const whole = date.getTime()/1000 - offset;
  need(whole>=-62135596800 && whole<=253402300799, 'invalid_manifest_time');
  return whole + (m[7] ? Number('0.'+m[7]) : 0);
}
function applicableManifest(value, origin, now) {
  validateManifest(value);
  const host = new URL(origin).hostname.replace(/^\[|\]$/g,'');
  need(value.atm_version === '0.2.0' && value.issuer.uri === origin && value.issuer.domain.toLowerCase() === host, 'manifest_subject_mismatch');
  need(timestamp(value.published_at)<=now && now<timestamp(value.expires_at), 'stale_or_future_manifest');
}
export function inspectFinding(raw, signature, jwks, manifestRaw, platformOrigin, assessorOrigin, trustedAssessors, now, maxObservationAge = null) {
  let h;
  let authentication;
  if (signature === null || signature === undefined) authentication = {state:'unverified', reason:'signature_not_supplied'};
  else if (jwks === null || jwks === undefined) authentication = {state:'unverified', reason:'keys_not_supplied'};
  else {
    try {
      h = verify(raw,signature,jwks,assessorOrigin,FINDING,now);
      authentication = {state:'authenticated', issuer:h.origin, kid:h.kid, expires_at:h.exp, reason:'signature_valid', claims_truth:'unresolved'};
    } catch (e) { if (!(e instanceof Rejection)) throw e; authentication = {state:'invalid', reason:e.message}; }
  }
  const report = {authentication, applicability:'unresolved', acceptance:'unresolved', access_granted:false};
  try {
    need(maxObservationAge === null || (typeof maxObservationAge === 'number' && Number.isInteger(maxObservationAge)
      && maxObservationAge>=0 && maxObservationAge<=86400), 'invalid_observation_age_policy');
    need(Array.isArray(trustedAssessors) && trustedAssessors.length<=8, 'too_many_assessors');
    const selected = trustedAssessors.map(canonicalOrigin);
    need(authentication.state === 'authenticated', 'finding_not_authenticated');
    const fd = strictJSON(raw), f = fd.value;
    need(shape(f,['profile','id','assessor','subject','manifest_sha256','claim','observation','issued_at','expires_at','method','result','limitations'])
      && f.profile === 'atm-invocation-finding/1', 'unsupported_finding');
    need(shape(f.assessor,['origin','relationship']) && f.assessor.origin === assessorOrigin
      && ['independent','affiliated','self'].includes(f.assessor.relationship), 'assessor_mismatch');
    canonicalOrigin(platformOrigin);
    need(shape(f.subject,['origin','type']) && f.subject.origin === platformOrigin && f.subject.type === 'platform', 'wrong_subject');
    const idPrefix = assessorOrigin+'/findings/';
    need(typeof f.id === 'string' && f.id.startsWith(idPrefix) && /^[A-Za-z0-9_-]{1,64}$/.test(f.id.slice(idPrefix.length)), 'invalid_finding_id');
    need(f.manifest_sha256 === createHash('sha256').update(manifestRaw).digest('hex'), 'manifest_digest_mismatch');
    need(shape(f.claim,['pointer','value']) && f.claim.pointer === '/interaction_profile/explicit_invocation_required'
      && typeof f.claim.value === 'boolean', 'invalid_typed_claim');
    const manifest = strictJSON(manifestRaw).value;
    applicableManifest(manifest,platformOrigin,now);
    const value = manifest.interaction_profile.explicit_invocation_required;
    need(typeof value === 'boolean' && value === f.claim.value, 'claim_value_mismatch');
    const obs = f.observation;
    need(shape(obs,['start','end']) && fd.integer(obs,'start') && fd.integer(obs,'end') && fd.integer(f,'issued_at') && fd.integer(f,'expires_at')
      && obs.start<=obs.end && obs.end<=f.issued_at && f.issued_at<=now && now<f.expires_at && f.expires_at-obs.start<=86400, 'invalid_finding_time');
    need(h.iat === f.issued_at && h.exp === f.expires_at, 'finding_time_mismatch');
    need(['static','active','audit'].includes(f.method) && ['pass','fail','unknown'].includes(f.result)
      && typeof f.limitations === 'string' && f.limitations.length>0, 'invalid_finding_metadata');
    Object.assign(report,{applicability:'matched',claim:f.claim, declared_result:f.result,method:f.method,
      relationship:f.assessor.relationship,independence:'unproven',limitations:f.limitations});
    need(selected.includes(assessorOrigin), 'assessor_not_selected');
    need(assessorOrigin !== platformOrigin && f.assessor.relationship === 'independent', 'independent_assessor_required');
    need(maxObservationAge === null || now-obs.end<=maxObservationAge, 'finding_observation_too_old');
    need(f.result === 'pass' && f.claim.value === true, 'finding_not_supportive');
    report.acceptance = 'accepted_for_claim'; report.reason = 'visitor_selected_assessor';
  } catch (e) { if (!(e instanceof Rejection)) throw e; report.reason = e.message; }
  return report;
}
