# Key Management

Publishers should:

- rotate signing keys on a defined schedule
- expose current public keys through a stable discovery mechanism
- separate signing keys from application runtime keys
- revoke compromised keys quickly

Early implementations may use a simple static key set. Higher-assurance deployments may adopt workload identity or hardware-backed keys.
