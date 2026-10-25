# ATM in the agent-interaction ecosystem

Research snapshot: **2026-10-25**. This is explanatory analysis, not a normative specification, implementation audit or interoperability claim. The functional placement below is our interpretation of the cited primary sources. Mutable documentation may change; the reviewed versions and remaining uncertainties are recorded below.

ATM's proposed contribution is portable declarations and assessable evidence about a receiving platform's controls, scope and capability prerequisites. Recognition, delegation and payment mechanisms can supply inputs to that platform's decisions. ATM does not own permission enforcement: receiving systems already enforce policies through their applications, gateways, site-protection services and payment infrastructure.

## Function, subject and enforcement are separate questions

Ask what an artifact does, whom its claims describe, and where its requirements are enforced. These axes do not divide whole projects into exclusive agent-control and platform-control categories. An operator's spending limit can constrain an agent while a payment service enforces it; a merchant's purchase restriction remains a receiving-platform policy.

The publisher, requesting agent, operator, credential issuer, receiving platform, control authority, enforcement point and assessor can be different parties. Matching identifiers do not make these roles interchangeable. In particular, evidence about an agent cannot substantiate a receiving-platform control merely because IDs match.

## Analytical functional map

The assurance column describes the intended role of each mechanism when its applicable checks succeed, not a guarantee that every deployment implements those checks correctly.

| Effort and artifact | Whom it describes / principal function | Intended assurance and boundary | Decision or enforcement location |
| --- | --- | --- | --- |
| [Cloudflare recognition system](https://developers.cloudflare.com/bots/concepts/bot/verified-bots/), historically “signed agents” | Requesting bot/service identity and behavior classification; signatures are one recognition method. | Recognition supplies traffic-policy signals. Intermediary recognition does not establish every end user's authority or assess the receiving application's controls. | Site owners configure receiving-side protection, including [Cloudflare rules](https://developers.cloudflare.com/bots/additional-configurations/custom-rules/); the application retains its own permissions. |
| [Visa Trusted Agent Protocol (TAP)](https://developer.visa.com/docs/trusted-agent-protocol/trusted-agent-protocol-specifications) | Agent recognition and linked consumer/payment information for merchant interactions. | Verified commerce signals can inform admission or limits. They are not universal delegation or proof of effective merchant safeguards. | Merchant or site-protection provider verifies signals and controls the interaction; payment participants retain their responsibilities. |
| [AP2 v0.2](https://ap2-protocol.org/ap2/specification/) and its [authorization framework](https://ap2-protocol.org/ap2/agent_authorization/) | Checkout/Payment mandate chains and receipts binding user authority to transactions. | Authorization evidence for particular checkout/payment actions, not general agent or platform safety. | Merchant, credential provider, network and processor have distinct verification duties; consent uses a Trusted Surface. |
| [Verifiable Intent (VI)](https://verifiableintent.dev/spec/) | Layered credentials binding user identity/key, consent or delegation, and agent fulfillment. | Inspectable delegated scope and transaction bindings; not blanket merchant permission or independent control assessment. | Merchants and payment participants validate their portions; [cumulative limits require stateful network checks](https://verifiableintent.dev/spec/security-model/). |
| [Signature Agent Card](https://www.ietf.org/archive/id/draft-meunier-webbotauth-registry-03.txt), coauthored by Thibault Meunier | Metadata and keys for an entity originating or forwarding signed requests, including declared bot behavior. | Discoverable requester metadata supports signature processing; declared behavior is not verified effectiveness or a receiving-platform assessment. | Relying origin verifies requests and applies its policy; publishing a card grants no access. |
| [Femi Alla's Agent Identity Document (AID)](https://www.ietf.org/archive/id/draft-alla-agent-identity-document-01.txt) | Hosted agent identity, accountability, lifecycle and provider/operator assertions. | Separates provider facts and dated owner checks from operator claims. Neither lifecycle status nor a provider check proves platform-control effectiveness. | Provider manages identity lifecycle; relying systems decide how to use those facts. |
| ATM manifest and companion artifacts | Receiving-platform declarations, capability conditions and scoped evidence references. | Discovery and structural validation establish no caller authority or truth of a control claim. Missing/stale information stays unresolved. | Platform independently enforces current policy. This repository's bounded consumer only reports `hold` or `manual_review`, granting no access. |

## Overlap and ATM's boundary

Cloudflare's [current documentation](https://developers.cloudflare.com/bots/concepts/bot/verified-bots/) describes the July 1, 2026 move from separate signed-agent/verified-bot categories to Direct/Intermediary metadata. Its vendor recognition system is not synonymous with the IETF Web Bot Auth drafts. The [historical announcement](https://blog.cloudflare.com/signed-agents/) remains useful background; current classifications and [policy configuration](https://developers.cloudflare.com/bots/additional-configurations/custom-rules/) should inform integration discussions.

TAP explicitly lets merchants use verified data to control or limit interactions, including paid resource access. Its merchant specification distinguishes the generic protocol from Visa implementation examples. ATM could make those accepted mechanisms, surrounding control claims and supporting evidence portable and discoverable. [TAP merchant specification](https://developer.visa.com/docs/trusted-agent-protocol/trusted-agent-protocol-specifications).

AP2 v0.2 separates checkout acceptance from payment-credential and processor checks. Its [authorization framework](https://ap2-protocol.org/ap2/agent_authorization/) distinguishes open constraints bound to an agent key from a closed transaction mandate. Its [core specification](https://ap2-protocol.org/ap2/specification/) requires deterministic validation even when a participating role is otherwise agentic. These functions cross agent and receiving-party boundaries.

VI similarly carries authorization evidence across parties. Its [security model](https://verifiableintent.dev/spec/security-model/) distinguishes cryptographic integrity from runtime/stateful enforcement. The [open draft](https://github.com/agent-intent/verifiable-intent) is not synonymous with Mastercard's Agent Pay offering; Mastercard describes [their relationship separately](https://www.mastercard.com/us/en/news-and-trends/stories/2026/verifiable-intent.html). ATM would describe claimed verification/enforcement arrangements and their evidence, rather than issue VI credentials.

Identity documents overlap with ATM in metadata discovery, lifecycle and evidence boundaries. Signature Agent Card reuses client metadata and key-discovery mechanisms; ATM should not duplicate it as another requester identity card. AID's separation of provider facts from operator assertions is useful precedent: its optional `public_key` assigns no verification semantics, and lifecycle status is not liveness. Neither artifact should silently become evidence about another system's controls. [Card -03](https://www.ietf.org/archive/id/draft-meunier-webbotauth-registry-03.txt), [AID -01](https://www.ietf.org/archive/id/draft-alla-agent-identity-document-01.txt).

A platform capability listing does not guarantee caller eligibility. An agent's ability and operator consent cannot authorize a platform-prohibited function. Conversely, platform support for purchasing cannot authorize spending outside the operator's mandate. Discovery, signature validity, user consent, platform permission and evidence of effective controls remain distinct checks.

## Illustrative interaction — no tested combined stack

1. An operator authorizes an agent to purchase within a budget through an accepted external mechanism. ATM does not issue that mandate.
2. The agent discovers the receiving merchant's ATM material and purchase prerequisites. It evaluates authenticity, applicability and freshness under its own policy. Missing or stale information is unresolved, not permission or proof of absence.
3. Supported identity/metadata mechanisms help the merchant identify the requester. AID and Signature Agent Card are possible building blocks, not required steps in an established ATM stack.
4. The merchant authenticates the request and applies current admission rules. Depending on the deployment, Cloudflare recognition or TAP signals might contribute; this does not require stacking every mechanism together.
5. Where supported, AP2 or VI artifacts substantiate the user's transaction authority. Relevant participants check constraints, bindings and any necessary runtime state. The merchant and payment issuer can still refuse.
6. Execution occurs only after the actual platform and payment gates pass. Transaction receipts may record the outcome; they do not independently prove every platform safeguard worked.

For example, an authenticated agent has user consent to spend $200, but the merchant prohibits automated purchases or requires an additional approval. Purchase must remain blocked until the merchant's current conditions are satisfied. ATM can make those conditions discoverable; it cannot satisfy or override them.

## Open integration questions

- How should requester, operator, publisher, issuer, platform subject/deployment, authority and assessor identities be bound without equating them?
- Can accepted credential or mandate mechanisms be advertised without exposing private policy or implying that every holder is eligible?
- Which statements are authenticated, provider-checked, independently assessed or merely declared? How is assessor independence established?
- Who checks expiry, key rotation, identity reassignment, revocation, policy changes and cumulative limits at the actual decision point?
- What is the response to unsupported constraints, partial disclosure, missing evidence or conflicting requirements? Which cases require a hold or additional approval?
- What fixtures and live tests would establish a particular binding's interoperability and effective enforcement, beyond document integrity?

## Appendix: source versions and payment caveats

The detailed payment research is condensed here as a source appendix rather than duplicated as a second narrative. All links below were accessed on 2026-10-25. Web specifications are mutable snapshots, not commit-pinned conformance baselines.

| Source | Reviewed version/status and date |
| --- | --- |
| Cloudflare [recognition documentation](https://developers.cloudflare.com/bots/concepts/bot/verified-bots/) and [rules documentation](https://developers.cloudflare.com/bots/additional-configurations/custom-rules/) | Vendor implementation documentation; pages show updates October 8 and April 15, 2026, respectively. |
| Visa [TAP merchant specification](https://developer.visa.com/docs/trusted-agent-protocol/trusted-agent-protocol-specifications) | Current web specification; no explicit version identifier found in retrieved text. Distinguishes protocol from Visa implementation examples. |
| AP2 [core](https://ap2-protocol.org/ap2/specification/) and [authorization framework](https://ap2-protocol.org/ap2/agent_authorization/) | Core identifies v0.2; [Google's April 28, 2026 announcement](https://blog.google/products-and-platforms/platforms/google-pay/agent-payments-protocol-fido-alliance/) announces that version and donation to FIDO. |
| VI [overview](https://verifiableintent.dev/spec/), [credential format](https://verifiableintent.dev/spec/credential-format/), [constraints](https://verifiableintent.dev/spec/constraints/) and [security model](https://verifiableintent.dev/spec/security-model/) | Source headers identify `0.1-draft`, February 18, 2026; current [repository](https://github.com/agent-intent/verifiable-intent) calls it draft and Mastercard-maintained. |
| Signature Agent Card [submitted -03](https://www.ietf.org/archive/id/draft-meunier-webbotauth-registry-03.txt) / [status](https://datatracker.ietf.org/doc/draft-meunier-webbotauth-registry/) | Individual Internet-Draft (intended Informational), June 26, 2026; expires December 28, 2026. Work in progress, not an adopted standard. |
| AID [submitted -01](https://www.ietf.org/archive/id/draft-alla-agent-identity-document-01.txt) / [status](https://datatracker.ietf.org/doc/draft-alla-agent-identity-document/) | Individual Internet-Draft (intended Informational), document header dated October 10, 2026; expires April 13, 2027. Work in progress, not an adopted standard. |

AP2's [September 16, 2025 launch article](https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol) uses earlier Intent/Cart terminology. The current analysis uses v0.2 Checkout/Payment Mandates, each open or closed. Agent-to-agent mandate delegation remains outside the [current core's scope](https://ap2-protocol.org/ap2/specification/).

The [AP2 project](https://ap2-protocol.org/) says standardization continues in FIDO technical working groups. Google's [donation announcement](https://blog.google/products-and-platforms/platforms/google-pay/agent-payments-protocol-fido-alliance/) also discusses VI. Those statements do not establish completed FIDO standards or prove every repository/governance transition has finished.

Several VI draft details need explicit agreement before an interoperability profile:

- Credential format §8.3 labels multi-transaction mandates planned, while constraints §4.7 and security model §4.2 describe recurrence and stateful enforcement. This inconsistency remains unresolved here. [Format](https://verifiableintent.dev/spec/credential-format/), [constraints](https://verifiableintent.dev/spec/constraints/), [security model](https://verifiableintent.dev/spec/security-model/).
- Format §6.3 makes checkout representation, signing algorithm and verification implementation-defined, with SHOULD-level signature guidance. Do not infer universal merchant-signature interoperability. [Credential format](https://verifiableintent.dev/spec/credential-format/).
- Constraints §5.3–5.4 specifically rejects unknown constraints in open mandates regardless of permissive mode. A broad description of permissive handling must preserve that exception. [Constraints](https://verifiableintent.dev/spec/constraints/).

Coverage comprises the supplied research and targeted rechecks of the primary-source claims retained in this document. It does not cover every referenced RFC, external implementation or deployment. No code audit, live safeguard test, certification or interoperability test of these external efforts was performed. Pin source revisions and resolve draft differences before claiming a normative integration.

ATM v0.2.0 provides schemas and structural validation. The local [platform-control profile](../spec/platform-controls-draft-0.1.md) remains explicitly **draft and unpublished**, with bounded applicability/freshness tests and no access grants, authenticated verification or runtime enforcement. [Issue #1](https://github.com/filchyboy/agent-trust-manifest/issues/1) remains the design record; draft PR #2 is a bounded consumer testbed. The combinations discussed here are proposed integrations, not implemented ATM compatibility, endorsement or partnership.
