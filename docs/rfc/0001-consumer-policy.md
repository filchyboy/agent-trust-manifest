# Consumer-policy design review

[Issue #1: Define consumer scope, freshness, failure and issuer-trust requirements](https://github.com/filchyboy/agent-trust-manifest/issues/1) is the single source for the open design questions, proposed acceptance criteria and discussion. Read and update those in the issue; this file intentionally does not maintain a snapshot of its body.

Versioned implementation documentation remains separate:

- [Consumer contract](../v0.2.0/consumer.md): behavior and limits of the reference consumer.
- [Draft platform-control profile](../../spec/platform-controls-draft-0.1.md): the bounded experimental profile, not a change to the v0.2.0 core contract.
- [Decision and coverage record](0001-consumer-policy-resolution.md): implemented rules, regression coverage and unresolved production-profile choices.

Changes to implementation behavior and coverage belong in those documents alongside the code. They do not by themselves resolve or close issue #1.
