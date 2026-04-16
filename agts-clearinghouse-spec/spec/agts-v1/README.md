# AGTS V1 — Open Format Specification

This directory contains the open format specification for the Autonomous
Governance Transition System (AGTS) V1.

AGTS defines how AI agent actions are governed: evaluated, scored, verdicted,
signed, and recorded into a tamper-evident transparency log. The system creates
a **proof chain from human intent to machine action** — the human sets policy,
the clearinghouse enforces it, and the log makes it auditable.

## Specification Documents

| Document | Description |
|----------|-------------|
| [governance-envelope-v1.md](governance-envelope-v1.md) | The Governance Envelope — atomic unit of governed decision-making |
| [plugin-result-v1.md](plugin-result-v1.md) | Plugin Result — individual evaluator output format |
| [hce-aggregation-v1.md](hce-aggregation-v1.md) | HCE Aggregation — the H/C/E scoring and verdict model |
| [merkle-proof-v1.md](merkle-proof-v1.md) | Merkle Transparency Log — tamper-evident append-only log |
| [sovereign-bundle-v1.md](sovereign-bundle-v1.md) | Sovereign Bundle (.oclaw) — portable agent identity artifact |
| [decision-boundary-v1.md](decision-boundary-v1.md) | Decision Boundaries — human-defined action classification |

## Key Concepts

### Governed Agentic Operations
Every action an AI agent takes under AGTS governance produces a Governance
Envelope. The envelope records what was evaluated, by whom, what the scores
were, and what the verdict was. This is not logging — it is governance.

### Profile-as-Gate
Policy profiles define numeric thresholds on the HCE dimensions. Each profile
acts as a gate: actions that clear all thresholds pass; actions that breach
any block threshold are refused; everything else is held for review.

### Proof Chain
The chain runs from human intent (decision boundaries, policy profiles) through
machine evaluation (plugin results, HCE aggregation) to immutable record
(signed envelope, Merkle log entry). Any link in the chain can be independently
verified.

### Governed Knowledge
A Sovereign Bundle is not a backup — it is a signed attestation of an agent's
configuration, with cryptographic links to every governance decision that
shaped it. The bundle makes agent state portable and verifiable.

## Versioning

All V1 schemas are **FROZEN**. No breaking changes are permitted.
Additive extensions require V2 interfaces with backward-compatible adapters.

## Reference Implementation

See [`/verifier/`](../../verifier/) for the Python reference verifier.
See [`/conformance/`](../../conformance/) for conformance test vectors.

## License

This specification is published as an open format. Implementations are
encouraged. The specification itself is Copyright ObligationSign.
