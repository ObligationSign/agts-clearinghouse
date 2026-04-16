# AGTS Governance Envelope V1

**Schema Identifier:** `AGTS_GOVERNANCE_ENVELOPE_V1`
**Schema Version:** `1`
**Status:** FROZEN — no breaking changes permitted; additive extensions require V2.

## Overview

The Governance Envelope is the atomic unit of governed decision-making in AGTS.
Every action an AI agent takes that passes through the AGTS clearinghouse produces
exactly one envelope. The envelope contains the full audit trail: which plugins
evaluated the request, how their scores were aggregated, what verdict was reached,
and how that verdict was anchored into a tamper-evident transparency log.

The envelope is the **proof chain from human intent to machine action**: the human
defines policy profiles and decision boundaries; the clearinghouse evaluates each
request against those profiles; the envelope records the outcome; the log makes
the record immutable and publicly verifiable.

## Schema

```json
{
  "type": "AGTS_GOVERNANCE_ENVELOPE_V1",
  "schema_version": "1",
  "transaction_id": "<uuid>",
  "plugins": [ <AGTS_PLUGIN_RESULT_V1>, ... ],
  "aggregate": {
    "H_total": <number 0..1>,
    "C_total": <number 0..1>,
    "E_total": <number 0..1>,
    "phi":     <number 0..1>
  },
  "verdict":         "PASS" | "REVIEW" | "BLOCK",
  "final_state":     "ADMIT" | "QUARANTINE" | "REFUSE",
  "execution":       "EXECUTED" | "WITHHELD" | "STOPPED",
  "requires_review": <boolean>,
  "timestamp":       <unix_ms>,
  "policy_profile":  "<string>",
  "merkle_anchor":   { ... },
  "signature":       "<base64url>",
  "signing": {
    "alg":       "Ed25519",
    "key_id":    "<string>",
    "signed_at": <unix_ms>
  },
  "log_anchor": {
    "leaf_hash":  "<hex sha-256>",
    "leaf_index": <integer | null>,
    "logged_at":  <unix_ms>,
    "synthetic":  <boolean>
  }
}
```

## Field Definitions

### Core Identity

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | YES | Always `"AGTS_GOVERNANCE_ENVELOPE_V1"`. |
| `schema_version` | string | YES | Always `"1"`. |
| `transaction_id` | string (UUID) | YES | Unique identifier for this governance decision. |
| `timestamp` | integer | YES | Unix epoch milliseconds when the envelope was created. |

### Plugin Results

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `plugins` | array | YES | Ordered list of `AGTS_PLUGIN_RESULT_V1` objects. See [plugin-result-v1.md](plugin-result-v1.md). |

### Aggregate Scores

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `aggregate.H_total` | number [0,1] | YES | Aggregated H score across all plugins. |
| `aggregate.C_total` | number [0,1] | YES | Aggregated C score across all plugins. |
| `aggregate.E_total` | number [0,1] | YES | Aggregated E score across all plugins. |
| `aggregate.phi` | number [0,1] | YES | Composite safety metric: `φ = (1 − H_total) × C_total × (1 − E_total)`. |

See [hce-aggregation-v1.md](hce-aggregation-v1.md) for the aggregation algorithm.

### Verdict & Enforcement

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `verdict` | enum | YES | One of `PASS`, `REVIEW`, `BLOCK`. |
| `final_state` | enum | YES | Enforcement state: `ADMIT`, `QUARANTINE`, `REFUSE`. |
| `execution` | enum | YES | Execution outcome: `EXECUTED`, `WITHHELD`, `STOPPED`. |
| `requires_review` | boolean | YES | `true` if and only if `final_state === "QUARANTINE"`. |
| `policy_profile` | string | NO | Name of the policy profile used (e.g. `"DEFAULT"`, `"STRICT"`). |

#### Verdict → Final State → Execution Mapping

This mapping is deterministic and MUST be followed:

| Verdict | Final State | Execution |
|---------|-------------|-----------|
| `PASS` | `ADMIT` | `EXECUTED` |
| `REVIEW` | `QUARANTINE` | `WITHHELD` |
| `BLOCK` | `REFUSE` | `STOPPED` |

### Signature

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `signature` | string (base64url) | NO | Ed25519 signature over the canonical JSON body. |
| `signing.alg` | string | with sig | Algorithm identifier. Currently always `"Ed25519"`. |
| `signing.key_id` | string | with sig | Key identifier for public key lookup. |
| `signing.signed_at` | integer | with sig | Unix epoch milliseconds when signature was created. |

#### Canonical JSON for Signing

The signed body is the envelope with `signature`, `signing`, and `log_anchor` fields
removed, then serialized using **canonical JSON**: keys sorted lexicographically at
every nesting level, no whitespace, `undefined` values omitted.

```
canonical_body = canonical_json(envelope - {signature, signing, log_anchor})
signature = Ed25519_sign(private_key, UTF8(canonical_body))
```

### Log Anchor

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `log_anchor.leaf_hash` | string (hex) | NO | SHA-256 hash of the canonical JSON of the full signed envelope. |
| `log_anchor.leaf_index` | integer/null | NO | Position in the Merkle tree (null if pending). |
| `log_anchor.logged_at` | integer | NO | Unix epoch milliseconds when the leaf was admitted. |
| `log_anchor.synthetic` | boolean | NO | `true` if the log entry was created in fail-closed mode. |

## Verification

A conforming verifier MUST check:

1. **Schema compliance** — all required fields present with correct types.
2. **Verdict consistency** — `final_state` and `execution` match the deterministic mapping above.
3. **H/C/E recomputation** — recompute `aggregate` from `plugins` using the HCE aggregation algorithm and verify values match within ε = 0.0001.
4. **Signature** — if `signature` is present and not a sentinel (`"signing_unavailable"`, `"no_signing_key"`), verify Ed25519 over canonical body.
5. **Log anchor** — if `log_anchor` is present, verify `leaf_hash` matches SHA-256 of the canonical JSON of the full signed envelope body.
6. **Merkle inclusion** — if a Merkle inclusion proof is available from the transparency log, verify the proof path from `leaf_hash` to the signed tree head root.
