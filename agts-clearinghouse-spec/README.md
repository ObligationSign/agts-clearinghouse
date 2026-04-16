# AGTS Clearinghouse Specification

Open format specification, Python reference verifier, and conformance test suite
for the **Autonomous Governance Transparency Standard (AGTS) V1**.

AGTS defines how AI agent actions are governed — evaluated, scored, verdicted,
signed, and recorded into a tamper-evident transparency log.

## Structure

```
agts-clearinghouse-spec/
├── spec/agts-v1/          # V1 format specification (8 documents)
│   ├── governance-envelope-v1.md
│   ├── plugin-result-v1.md
│   ├── hce-aggregation-v1.md
│   ├── merkle-proof-v1.md
│   ├── sovereign-bundle-v1.md
│   ├── decision-boundary-v1.md
│   ├── execution-trace-v1.md
│   └── variance-record-v1.md
├── verifier/              # Python reference verifier
│   └── agts_verify.py
└── conformance/           # Conformance test suite
    ├── run_conformance.py
    ├── test_manifest.json
    ├── valid/             # 13 valid test vectors
    └── invalid/           # 9 invalid test vectors
```

## Quick Start

Run the conformance suite (requires Python 3.10+, `cryptography` package):

```bash
pip install cryptography
cd agts-clearinghouse-spec
python conformance/run_conformance.py
```

Expected output: **22/22 tests passed**.

## Specification Documents

| Document | Description |
|----------|-------------|
| governance-envelope-v1 | Atomic unit of governed decision-making |
| plugin-result-v1 | Individual evaluator output format |
| hce-aggregation-v1 | H/C/E scoring and verdict model |
| merkle-proof-v1 | Tamper-evident append-only transparency log |
| sovereign-bundle-v1 | Portable agent identity artifact (.oclaw) |
| decision-boundary-v1 | Human-defined action classification rules |
| execution-trace-v1 | Record of governed action execution |
| variance-record-v1 | Authorization-vs-execution drift measurement |

## Conformance Test Coverage

| Category | Valid | Invalid | Checks |
|----------|-------|---------|--------|
| Governance Envelope | 4 | 4 | Schema, verdict consistency, HCE aggregation, type |
| Ed25519 Signature | 1 | 1 | Signature verification, leaf hash |
| Sovereign Bundle | 2 | 1 | Type, content hash verification |
| Merkle Proof | 1 | 1 | Inclusion proof recomputation |
| Decision Boundary | 5 | — | Tool match, keyword overlap, escalation priority, defaults |
| **Total** | **13** | **9** | **22 vectors** |

## Versioning

All V1 schemas are **FROZEN**. No breaking changes are permitted.
Additive extensions require V2 interfaces with backward-compatible adapters.

## License

This specification is published as an open format. Implementations are
encouraged. The specification itself is Copyright ObligationSign.
