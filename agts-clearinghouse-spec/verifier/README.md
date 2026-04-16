# AGTS Reference Verifier

A standalone Python reference implementation for verifying AGTS Governance
Envelopes, Sovereign Bundles, Merkle inclusion proofs, Decision Boundary
classifications, and Ed25519 signatures.

## Requirements

- Python 3.10+
- `cryptography` package (required for Ed25519 signature verification)

```bash
pip install -r requirements.txt
```

## Usage

### Verify a Governance Envelope

```bash
python agts_verify.py envelope.json
```

### Verify a Sovereign Bundle (.oclaw)

```bash
python agts_verify.py bundle.oclaw
```

### Verify with Merkle Inclusion Proof

```bash
python agts_verify.py envelope.json --proof proof.json --sth sth.json
```

### JSON Output

```bash
python agts_verify.py envelope.json --format json
```

### Specify Policy Profile

```bash
python agts_verify.py envelope.json --profile STRICT
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All checks passed |
| 1 | One or more checks failed |
| 2 | Invalid input (file not found, malformed JSON) |

## What It Checks

### Governance Envelope
- Schema compliance (all required fields present)
- Type identifier correctness
- Verdict/final_state/execution consistency
- HCE aggregation recomputation (within epsilon = 0.0001)
- Ed25519 signature verification (fail-closed: errors if cryptography unavailable)
- Leaf hash verification (if log_anchor present)

### Sovereign Bundle
- Type identifier correctness
- Required field presence
- Signature presence
- Profile and provenance population
- Config file content hash verification

### Merkle Proof
- Inclusion proof walk from leaf hash to tree root
- Root hash comparison against signed tree head

### Decision Boundary Classification
- Easy/hard/escalation rule matching
- Priority ordering (escalation > hard > easy > default)
- Confidence scoring

## Conformance

This verifier is the reference implementation for the AGTS V1 specification.
All test vectors in `../conformance/` must pass when verified with this tool.
