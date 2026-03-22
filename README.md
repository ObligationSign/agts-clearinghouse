# AGTS Clearinghouse — Public Specification

**Autonomous Governance Transparency Standard**

Version 0.1-Draft | March 2026

---

## What is AGTS?

AGTS is a transparency-backed governance protocol that converts validated machine decisions into append-only cryptographic records, independently verified by a network of witnesses and monitors, enabling cryptographically auditable governance history for autonomous systems.

```
decision → record → immutable history → verifiable truth
```

## Specification Documents

| Document | Status | Description |
|---|---|---|
| [AGTS_CLEARINGHOUSE_SPEC.md](AGTS_CLEARINGHOUSE_SPEC.md) | NORMATIVE | Clearinghouse protocol specification — governance client layer |
| [AGTS-TERMS.md](AGTS-TERMS.md) | NORMATIVE | Terminology and definitions for the AGTS suite |
| [PROTOCOL_DIAGRAMS.md](PROTOCOL_DIAGRAMS.md) | INFORMATIVE | Architecture diagrams and protocol visualizations |

## Protocol Layers

```
Governance Layer        measurement and validation of autonomous system updates
Envelope Layer          packaging governance artifacts for transparency admission
Transparency Layer      append-only recording of governance artifacts
Verification Layer      independent checking of log integrity
Trust Policy Layer      client-side trust decisions
```

## Conformance Levels

| Level | Name | Description |
|---|---|---|
| L1 | Verified Measurement | Capability measurement with PAC bounds; Proof Bundle chain |
| L2 | Governed Updates | Five-gate validation predicate; quorum certificate; deterministic replay |
| L3 | Transparent Governance | Merkle Transparency Log; inclusion and consistency proofs |
| L4 | Networked Transparent Governance | Witness quorum; monitor network; cross-log anchoring |

## Core Invariant

> Every accepted governance decision produces exactly one canonical leaf in an append-only transparency log. No single actor can both authorize an action and hide the evidence of that action.

## Contact

ops@obligationsign.com

## License

Copyright 2026 ObligationSign. All rights reserved.

This specification is published for review and interoperability purposes. Implementations require a conformance agreement with the AGTS Technical Steering Committee.
