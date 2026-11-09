# Key Management

Publishers should:

- rotate signing keys on a defined schedule
- expose current public keys through a stable discovery mechanism
- separate signing keys from application runtime keys
- revoke compromised keys quickly

Early implementations may use a simple static key set. Higher-assurance deployments may adopt workload identity or hardware-backed keys.

## Optional detached profile v1

[Signing profile v1](../spec/signing-profile-v1.md) fixes the same-origin public
JWKS path, public-only Ed25519 entries, unique IDs, freshness and key windows.
A compromised or revoked key is unusable for current assurance even when a
signature claims an earlier `iat`; attackers holding the key can backdate.
Retirement records scheduled rotation and may retain earlier signatures until
expiry. It must never stand in for compromise. Offline or upstream-cached
snapshots can miss revocations; the maximum profile freshness window is 24
hours. Independent trustworthy historical timestamps are outside this profile.
Publish new keys before using them and deploy manifest/signature bytes as a
single release; consumers reject mismatched snapshots during deployment races.
