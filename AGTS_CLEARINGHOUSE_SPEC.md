# AGTS Clearinghouse — Normative Specification

**Version:** 1.0-Draft  
**Date:** March 2026  
**Status:** NORMATIVE  
**Normative references:**  
- AGTS-TERMS (this repository)  
- PROTOCOL_DIAGRAMS (this repository)

This document specifies the AGTS-conforming clearinghouse: the client-side implementation that runs the governance measurement loop, operates the Policy Validator network, assembles Governance Envelopes, and submits canonical leaves to the Transparency Log. Every protocol behavior defined here derives directly from AGTS-TERMS.

---

## §1 Scope

The AGTS Clearinghouse is the governance client layer. It sits between the Machine Execution Layer and the Transparency Log. Its responsibilities are:

1. Accumulate a signed, Merkle-chained measurement chain of governance evidence
2. Operate the Policy Validator network (BFT vote collection, quorum certificate issuance)
3. Assemble AGTS Governance Envelopes (Proof Bundle + validator signatures + Sovereign Authority signature)
4. Submit completed Governance Envelopes to the Transparency Log for Canonical Leaf admission
5. Integrate with the settlement rail via AGTS settlement receipts

The clearinghouse is **not** a transparency log. It produces artifacts that are admitted to a log; it does not host the log itself. The clearinghouse is **not** a Sovereign Authority. It delivers the quorum certificate to the Sovereign Authority for hardware signing; it does not hold or emulate authority keys.

---

## §2 Normative language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** follow RFC 2119.

All terminology follows AGTS-TERMS.

---

## §3 Identity Model

### §3.1 Node ID derivation

Every signing entity — settlement clients, Policy Validators, Sovereign Authority, log operators, witnesses — is identified by a Node ID.

```
node_id = hex( SHA256( DER_SubjectPublicKeyInfo_bytes ) )
```

Output: 64 lowercase hex characters. **No truncation at any length.**

### §3.2 SPKI derivation

The SHA-256 input MUST be the raw DER bytes of the SubjectPublicKeyInfo structure. It MUST NOT be a hex-encoded string, a base64-encoded string, or any encoding of those bytes other than the raw binary.

### §3.3 Node ID scope

Node IDs are used in:

| Context | Field name | Value |
|---|---|---|
| Settlement client | `node_id` | SHA256(client SPKI) |
| Policy Validator | `validator_id` | SHA256(validator SPKI) |
| Sovereign Authority | `authority_node_id` | SHA256(authority SPKI) |
| Log Operator | `log_id` | SHA256(log operator SPKI) |
| Witness | `witness_id` | SHA256(witness SPKI) |
| Monitor | `monitor_id` | SHA256(monitor SPKI) |

All use the same derivation. The identity model is uniform across all entity types.

---

## §4 Cryptographic Protocol

### §4.1 Signing

All signed artifacts use this construction:

```
step 1: body      = { ...artifact_fields }
step 2: canonical = canonical_json(body)          // RFC 8785
step 3: digest    = SHA256( UTF-8(canonical) )    // raw 32-byte digest
step 4: signature = Sign(private_key, digest)     // Ed25519 or ECDSA P-256
step 5: sig_b64url = base64url(signature_bytes)   // no padding
```

The correct signed message is the **raw 32-byte SHA-256 digest** of the canonical JSON. Not the hex encoding of that digest. Not a UTF-8 string derived from it.

### §4.2 Canonical JSON

`canonical_json(x)` follows RFC 8785:

- Keys sorted lexicographically by Unicode code point
- No insignificant whitespace
- UTF-8 encoding, no BOM
- Numbers per IEEE 754 double-precision (RFC 8785 §3.2.2)
- Non-finite numbers (`Infinity`, `NaN`) are protocol errors — MUST NOT appear in any artifact body

### §4.3 Signature encoding

Ed25519 signatures: 64 bytes, base64url-encoded (RFC 4648 §5), no padding.  
ECDSA P-256: IEEE P1363 format (r || s, 32 bytes each = 64 bytes total), base64url-encoded.

Wire field name: `signature_b64url` (snake_case). All AGTS artifacts use this field name.

### §4.4 Period ID

```
period_id = hex( SHA256( canonical_json({ "node_id": "<64-char>", "period_start": "<ISO-8601>" }) ) )
```

AGTS uses canonical JSON to prevent ambiguity in the hash input. Both client and gateway compute `period_id` independently and must reach the same value.

---

## §5 Validator Network

### §5.1 Configuration

The minimum AGTS-conforming validator configuration:

| Parameter | Value | Constraint |
|---|---|---|
| `n_validators` | 4 | n = 3f + 1 (tolerates f = 1 Byzantine node) |
| `quorum_threshold` | 3 | >= floor(2n/3) + 1 |
| `proposer_selection` | `H(action_id) mod n_validators` | Deterministic |

With 4 validators and a 3-of-4 quorum, any coalition of 2 validators cannot forge an authorization without Sovereign Authority cooperation. The minimum operational quorum is 3 (1 Byzantine failure tolerated).

### §5.2 Validator identity

Each validator is identified by its `validator_id`:

```
validator_id = node_id = hex( SHA256( DER SPKI of validator key ) )
```

The validator registry stores the full SPKI for each registered validator. The clearinghouse derives `validator_id` from the SPKI and verifies the derivation on registration.

### §5.3 Proposer selection

```
proposer_index = SHA256( action_id_bytes ) mod n_validators
```

The proposer for a given action is the validator at `proposer_index` in the registered validator list (ordered by `validator_id` lexicographically). If the proposer does not respond within `PROPOSER_TIMEOUT` (default 10 seconds), rotation falls to the next validator in the list.

### §5.4 Vote protocol — AGTS_VOTE_V1

Each validator independently evaluates the Proof Bundle against policy rules and produces a signed vote.

**Vote body:**

```json
{
  "type":         "AGTS_VOTE_V1",
  "validator_id": "<64-char hex node_id>",
  "decision":     "ACCEPT | REJECT",
  "body_hash":    "<64-char hex — SHA256(canonical_json(proof_bundle_body))>",
  "voted_at":     "<ISO-8601 UTC>"
}
```

**Signing:**

```
vote_digest = SHA256( canonical_json(vote_body) )
vote_sig    = Sign( validator_key, vote_digest )
```

The `voted_at` timestamp makes each vote non-replayable across time. The `decision` field is explicit. The `body_hash` pins the vote to a specific Proof Bundle content.

### §5.5 Quorum certificate — AGTS_CERTIFICATE_V1

When the proposer collects quorum_threshold votes with `decision: "ACCEPT"`, it assembles an `AGTS_CERTIFICATE_V1`.

```json
{
  "type":               "AGTS_CERTIFICATE_V1",
  "issued_at":          "<ISO-8601 UTC>",
  "subject":            "<description of the governance decision>",
  "proof_bundle_hash":  "<64-char hex — SHA256(canonical_json(proof_bundle_body))>",
  "validators":         ["<validator_id-0>", "<validator_id-1>", "<validator_id-2>"],
  "votes": {
    "<validator_id-0>": { "verdict": "ACCEPT", "signature": "<base64url>" },
    "<validator_id-1>": { "verdict": "ACCEPT", "signature": "<base64url>" }
  },
  "quorum":             3,
  "threshold":          3,
  "cert_hash":          "<64-char hex — SHA256(canonical_json(cert_body_without_cert_hash))>"
}
```

The `cert_hash` is the content address of this certificate. It is recomputed by any recipient and MUST match the provided value.

### §5.6 What validators evaluate

Validators evaluate policy rules against the Proof Bundle — they are **Policy Validators** in AGTS-TERMS terminology.

Validators do NOT:

- Compute G1–G5 gate results (that is the Gate Evaluator's role)
- Directly execute or block the governed action
- Replace the Sovereign Authority

They verify that the Proof Bundle:

1. Contains all required G4 evidence hashes (`dataset_provenance_hash`, `evaluation_trace_hash`, `ablation_execution_log_hash`, `capability_certificate_hash`)
2. Shows `"result": "PASS"` for all five gates
3. Has a valid `parent_bundle_hash` chain (or null for genesis)
4. Has a `generated_at` within the accepted replay window
5. Matches the declared policy configuration for the tenant

---

## §6 Proof Bundle

The Proof Bundle (`AGTS_PROOF_BUNDLE_V1`) is the off-chain governance evidence artifact produced by the governance engine after all five gates pass. It is the content that validators evaluate.

### §6.1 Proof Bundle body

Key fields:

```json
{
  "type":    "AGTS_PROOF_BUNDLE_V1",
  "version": "AGTS-1",
  "subject_id":                  "<identifier of the autonomous system>",
  "capability_certificate_id":   "<64-char hex>",
  "deployment_artifact_hash":    "<64-char hex>",
  "parent_bundle_hash":          "<64-char hex | null>",
  "replay_seed":                 "<deterministic replay seed>",
  "gate_results": { "G1": {}, "G2": {}, "G3": {}, "G4": {}, "G5": {} },
  "evidence": {
    "dataset_provenance_hash":     "<64-char hex>",
    "evaluation_trace_hash":       "<64-char hex>",
    "ablation_execution_log_hash": "<64-char hex>",
    "capability_certificate_hash": "<64-char hex>"
  },
  "state_before_hash": "<64-char hex>",
  "state_after_hash":  "<64-char hex>",
  "generated_at":      "<ISO-8601 UTC>"
}
```

### §6.2 Artifact hash

```
artifact_hash = hex( SHA256( canonical_json(proof_bundle_body) ) )
```

This is the content address of the Proof Bundle. It appears in both the Governance Envelope and the quorum certificate.

### §6.3 Storage and payload_uri

The Proof Bundle body is stored at a durable `payload_uri`. The clearinghouse MUST:

1. Store the Proof Bundle at `payload_uri` before assembling the Governance Envelope
2. Verify that the stored body is retrievable at `payload_uri` before proceeding
3. Include `payload_uri` in the Governance Envelope

The `payload_uri` MUST be a content-addressed reference. Recommended patterns:

- Content-addressed path keyed by `artifact_hash`: `/pb/{artifact_hash}`
- IPFS CID URI: `ipfs://{CID}`
- Object storage key: `pb/{artifact_hash}.json`

**Why this matters:** Without `payload_uri`, the Transparency Log stores only a hash. With `payload_uri`, any third party can retrieve the Proof Bundle body, recompute `artifact_hash`, verify it matches the Governance Envelope's `artifact_hash`, and replay the G1–G5 gate evaluation deterministically. This is the difference between hash-only transparency and replayable transparency.

---

## §7 Governance Envelope

The Governance Envelope (`AGTS_GOVERNANCE_ENVELOPE_V1`) is the primary transparency artifact. It wraps a Proof Bundle, carries quorum approval, and receives the Sovereign Authority signature before Transparency Log admission.

### §7.1 Assembly sequence

```
GOVERNANCE ENGINE          CLEARINGHOUSE              SOVEREIGN AUTHORITY        LOG
==================         =============              ===================        ===

Run G1–G5 (Gate Evaluators)
  |
Produce AGTS_PROOF_BUNDLE_V1
Compute artifact_hash
Store at payload_uri
                           Distribute to validators
                           Collect AGTS_VOTE_V1 votes
                           Assert quorum met
                           Issue AGTS_CERTIFICATE_V1
                           Assemble envelope Stage 1
                           (without authority fields)
                                                      Stage 2 signing:
                                                      Review envelope details
                                                      Biometric approval
                                                      Sign canonical envelope
                                                      Return authority_signature
                           Embed authority_signature
                           Complete envelope
                           POST to log
                                                                                 Verify signatures
                                                                                 Compute Canonical Leaf
                                                                                 Append to Merkle tree
                                                                                 Return STH + proof
```

### §7.2 Envelope body (Stage 1 — before Sovereign Authority)

```json
{
  "type":                "AGTS_GOVERNANCE_ENVELOPE_V1",
  "version":             "AGTS-1",
  "artifact_type":       "AGTS_PROOF_BUNDLE_V1",
  "artifact_hash":       "<64-char hex>",
  "payload_uri":         "<durable URI>",
  "validator_signatures": [
    {
      "validator_id":  "<64-char hex>",
      "algorithm":     "Ed25519 | ECDSA-P256",
      "signature":     "<base64url>"
    }
  ],
  "authority_node_id":    "<64-char hex — placeholder before Stage 2>",
  "authority_algorithm":  "Ed25519 | ECDSA-P256",
  "log_binding": {
    "log_id":  "<64-char hex — SHA256(log operator SPKI)>",
    "log_url": "<base URL of the Transparency Log>"
  },
  "generated_at": "<ISO-8601 UTC>"
}
```

### §7.3 Validator signature construction (Stage 1)

Each validator signs a reduced envelope that excludes `authority_signature` and `log_binding`:

```
validator_input  = canonical_json(envelope_without_authority_sig_and_log_binding)
validator_digest = SHA256(validator_input)
validator_sig    = Sign(validator_key, validator_digest)
```

The clearinghouse embeds each validator signature in `validator_signatures` before sending to the Sovereign Authority.

### §7.4 Sovereign Authority signature construction (Stage 2)

The Sovereign Authority signs the complete envelope including `validator_signatures` and `log_binding`, but excluding `authority_signature`:

```
authority_input  = canonical_json(envelope_without_authority_signature)
authority_digest = SHA256(authority_input)
authority_sig    = Sign(authority_key, authority_digest)
```

AGTS signs the full canonical JSON envelope. This means the authority signature covers the artifact hash, the payload_uri, all validator signatures, and the log binding in one verifiable unit.

### §7.5 Canonical Leaf derivation

```
leaf_hash = SHA256( "AGTS_LEAF_V1" || canonical_json(governance_envelope_body) )
```

The prefix `"AGTS_LEAF_V1"` is the exact 12-byte UTF-8 sequence. No null terminator, no length prefix. The full envelope body (all fields including all signatures) is included.

---

## §8 Transparency Log Interface

The clearinghouse is a log client. It submits Governance Envelopes and processes the responses. The log itself is a separate deployment.

### §8.1 Required log endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/add` | Submit a complete Governance Envelope |
| `GET` | `/get-proof/:leaf_hash` | Retrieve inclusion proof |
| `GET` | `/get-sth` | Retrieve current Signed Tree Head |
| `GET` | `/get-consistency/:old_size/:new_size` | Retrieve consistency proof |

### §8.2 Submission request

```json
{
  "tenant_id":   "<tenant>",
  "envelope":    { },
  "certificate": { }
}
```

The log MUST verify:
1. `authority_signature` using the `authority_node_id`'s registered SPKI
2. All `validator_signatures` using their registered SPKIs
3. `artifact_hash` is consistent with the submitted `proof_bundle_hash` in the certificate

### §8.3 Submission response

```json
{
  "leaf_index":      42,
  "leaf_hash":       "<64-char hex>",
  "inclusion_proof": ["<hash>", "<hash>", "..."],
  "sth": {
    "type":       "AGTS_STH_V1",
    "log_id":     "<64-char hex>",
    "tree_size":  43,
    "root_hash":  "<64-char hex>",
    "timestamp":  "<ISO-8601 UTC>",
    "log_signature":      "<base64url>",
    "witness_signatures": []
  }
}
```

### §8.4 Signed Tree Head verification

The clearinghouse MUST verify the STH returned by the log:

1. Verify `sth.log_signature` against the log operator's registered SPKI
2. Verify the `inclusion_proof` against `sth.root_hash` starting from `leaf_hash`
3. Store the STH for later consistency proof verification

If any verification fails, the submission is treated as failed and MUST NOT be reported to the application as successful.

### §8.5 Consistency verification

Before accepting a new STH from the log, the clearinghouse MUST verify that it is consistent with the last verified STH:

```
GET /get-consistency/{last_known_tree_size}/{new_tree_size}
-> consistency_proof[]

Verify: consistency_proof proves new_root extends old_root
```

A consistency verification failure MUST be surfaced as a security alert — it indicates log misbehavior.

---

## §9 Witness Layer

### §9.1 Witness function

Witnesses are independent parties that observe STHs and countersign valid ones. They provide confidence that the log has not been selectively serving different STHs to different parties (split-view attack).

The clearinghouse does not operate witnesses. It SHOULD verify that received STHs carry witness countersignatures when the deployment targets AGTS Level 4.

### §9.2 Witness signature verification

```
witness_input  = canonical_json(sth_with_log_signature_only)
witness_digest = SHA256(witness_input)
```

For AGTS Level 4 conformance, the clearinghouse MUST accept STHs only when they carry at least `Q` witness signatures, where `Q` is configured in the Verification Policy Bundle.

---

## §10 Lifecycle State Machine

The clearinghouse maintains a lifecycle state per plugin domain (and a gateway-level state):

```
PROPOSED -> ACTIVE -> QUARANTINE -> LOCKBOX -> (terminal)
                  \               \
                   REJECTED (immediate, any state)
```

| State | Entry condition | Behavior |
|---|---|---|
| `PROPOSED` | Plugin registered, not yet verified | Measurement chain accumulating; not eligible for Governance Envelope issuance |
| `ACTIVE` | First gate pass verified | Full pipeline operational |
| `QUARANTINE` | 3+ consecutive gate failures | Measurement continues; Governance Envelope issuance suspended; alert emitted |
| `LOCKBOX` | 10+ consecutive failures | Read-only audit mode; no new measurements accepted; state preserved for forensics |
| `REJECTED` | Policy violation detected | Permanent; requires full restart with new plugin registration |

### §10.1 Collapse gate

The gateway-level lifecycle is governed by three trust observables: **H** (hypothesis support), **C** (causal attribution confidence), **E** (entropy / uncertainty).

```
COLLAPSE_GATE passed when:
  H >= H_MIN (default 0.40)
  C >= C_MIN (default 0.40)
  E <= E_MAX (default 0.60)
```

A collapse gate failure transitions the clearinghouse to QUARANTINE. These thresholds are policy-configurable.

### §10.2 HCE nudge model

Observable updates are nudge-based (not computed directly from raw entropy/density matrices). Each measurement type produces a signed delta applied to the current values:

```
new_H = clamp(old_H + nudge.h, 0.0, 1.0)
new_C = clamp(old_C + nudge.c, 0.0, 1.0)
new_E = clamp(old_E + nudge.e, 0.0, 1.0)
```

The nudge table is normative per deployment policy. Implementations MUST document which nudge table version is active in the Verification Policy Bundle.

---

## §11 Measurement Chain and Evidence Engine

The Evidence Engine maintains an append-only Merkle-chained measurement log. This is the clearinghouse's internal evidence accumulation layer — it is NOT the Transparency Log. Its purpose is to provide a local audit trail that can be batch-submitted to the Transparency Log via Governance Envelopes.

### §11.1 Measurement object

```json
{
  "type":              "<measurement type>",
  "measurement_source": "PLUGIN | METERING | SYSTEM",
  "plugin":            "<plugin name>",
  "timestamp":         "<ISO-8601 UTC>",
  "session_id":        "<session identifier>",
  "seq":               0
}
```

### §11.2 Measurement leaf

Each measurement is added to the local Merkle tree with AGTS leaf domain separation:

```
local_leaf_hash = SHA256( "AGTS_LEAF_V1" || canonical_json(measurement) )
```

The same prefix applies to local measurement leaves. This is consistent with the Transparency Log leaf construction and prevents cross-context collisions.

### §11.3 Proof Bundle construction from the measurement chain

At the end of a governance period, the Evidence Engine's state (Merkle root, H/C/E observables, collapse gate result) forms the observable state input to the Proof Bundle.

The clearinghouse MUST NOT issue a Governance Envelope if the local collapse gate is not in PASS state.

---

## §12 Settlement Integration

### §12.1 Settlement receipt generation

When a governance period closes, the clearinghouse generates an `AGTS_SETTLEMENT_V1` receipt:

```json
{
  "type":             "AGTS_SETTLEMENT_V1",
  "metering_version": "agts_metering_v1",
  "node_id":          "<64-char hex>",
  "period_id":        "<64-char hex — SHA256(canonical_json({node_id, period_start}))>",
  "period_start":     "<ISO-8601 UTC>",
  "period_end":       "<ISO-8601 UTC>",
  "counters": {
    "authorizations":    0,
    "validated_actions": 0,
    "federation_rounds": 0,
    "risk_low":          0,
    "risk_medium":       0,
    "risk_high":         0
  },
  "parent_bundle_hash": "<64-char hex | null>",
  "generated_at":       "<ISO-8601 UTC>"
}
```

### §12.2 Counter semantics

| Counter | Incremented when |
|---|---|
| `authorizations` | A Governance Envelope is successfully admitted to the Transparency Log |
| `validated_actions` | A Policy Validator vote of ACCEPT is recorded |
| `federation_rounds` | A complete validator network round concludes (vote collection + proposer assembly) |
| `risk_low` | A G3 risk assessment produces a low-risk outcome |
| `risk_medium` | A G3 risk assessment produces a medium-risk outcome |
| `risk_high` | A G3 risk assessment produces a high-risk outcome |

Counters reflect governance events, not machine execution events. An authorization increments `authorizations` once — regardless of how many downstream machine actions it covers.

### §12.3 Linking settlement to governance

The `parent_bundle_hash` field links the settlement receipt to the Proof Bundle that produced the authorized governance decision. This creates the AGTS three-layer audit chain:

```
settlement receipt
  -> parent_bundle_hash -> Proof Bundle
      -> artifact_hash in Governance Envelope
          -> Canonical Leaf in Transparency Log
              -> payload_uri -> deterministic replay
```

An auditor can traverse this chain from any billing event to its governance record.

---

## §13 Plugin Interface Contract

A plugin is a component implementing five methods. The AGTS contract requires plugins to produce AGTS-formatted evidence when emitting governance measurements.

### §13.1 Required plugin methods

| Method | Signature | Purpose |
|---|---|---|
| `name` | getter | Unique identifier for this plugin domain |
| `initialize` | `async (onMeasurement) => void` | Called once on registration; receives measurement callback |
| `getStatus` | `() => { name, initialized, lifecycleState }` | Synchronous status check |
| `onMessage` | `async (msg, sender) => any` | Message handler for inter-plugin communication |
| `destroy` | `() => void` | Cleanup on shutdown |

### §13.2 Governance evidence emission

When a plugin has completed a governed action, it MUST emit governance evidence in AGTS format via the `onMeasurement` callback:

```json
{
  "type":               "agts_governance_evidence",
  "measurement_source": "PLUGIN",
  "plugin":             "<plugin name>",
  "timestamp":          "<ISO-8601 UTC>",
  "proof_bundle": {
    "dataset_provenance_hash":     "<sha256>",
    "evaluation_trace_hash":       "<sha256>",
    "ablation_execution_log_hash": "<sha256>",
    "capability_certificate_hash": "<sha256>",
    "gate_results": {
      "G1": { "result": "PASS", "confidence_interval_lower": 0.0, "confidence_interval_upper": 1.0 },
      "G2": { "result": "PASS", "causal_attribution": true },
      "G3": { "result": "PASS", "protected_metrics": {} },
      "G4": { "result": "PASS", "evidence_class": "HOOKED" },
      "G5": { "result": "PASS", "operator_id": "<DHO identifier>" }
    }
  }
}
```

The clearinghouse assembles the full `AGTS_PROOF_BUNDLE_V1` from this input, adds system-level fields (`subject_id`, `parent_bundle_hash`, `state_before_hash`, `state_after_hash`), and proceeds with the validator network round.

### §13.3 Plugin lifecycle states

| State | AGTS meaning |
|---|---|
| `PROPOSED` | Registered, not yet active |
| `ACTIVE` | Producing governance evidence normally |
| `QUARANTINE` | Degraded — 3+ consecutive gate failures — Governance Envelope issuance suspended |
| `LOCKBOX` | Suspended — 10+ consecutive failures — audit preservation mode |
| `REJECTED` | Permanent policy violation — cannot reactivate |

---

## §14 Security Model

| Threat | Defense |
|---|---|
| Single validator compromise | Quorum consensus (3-of-4) — 2 validators cannot forge authorization |
| Multiple validator collusion | Sovereign Authority requires hardware biometric; validators cannot produce authority_signature |
| Sovereign device compromise | Hardware isolation (secure element); non-exportable key; biometric per use |
| Node ID forgery | SPKI pinning on first contact; `node_id` re-derived and verified against pinned SPKI on all subsequent requests |
| Signing key compromise | Key revocation (`AGTS_KEY_REVOCATION_V1`); retroactive quarantine of receipts within REVOCATION_LOOKBACK window |
| Receipt replay | Replay window (30-day hard expiry, 5-minute clock skew tolerance) on `generated_at` |
| Log tampering | Append-only Merkle tree; STH; inclusion proofs; consistency proofs |
| Log equivocation | Monitor gossip; equivocation proofs (two conflicting STHs = self-evident proof of misbehavior) |
| Leaf/internal-node collision | AGTS_LEAF_V1 domain separation prefix on all leaf hashes |
| Evidence fabrication | G4 HOOKED evidence class requirement; four mandatory evidence hashes in Proof Bundle |
| Governance record linkage failure | `parent_bundle_hash` chain in settlement receipts; `artifact_hash` + `payload_uri` in Governance Envelope |

---

## §15 AGTS Conformance Summary

| Level | Name | Requirements met by this spec |
|---|---|---|
| L1 | Verified Measurement | AGTS_PROOF_BUNDLE_V1 with G1–G5; AGTS_SETTLEMENT_V1 with verified counters; local Merkle measurement chain |
| L2 | Governed Updates | AGTS_GOVERNANCE_ENVELOPE_V1 with authority_signature; AGTS_CERTIFICATE_V1 with Policy Validator quorum; two-stage signing |
| L3 | Transparent Governance | Merkle Transparency Log; STH with log_signature; inclusion + consistency proofs; AGTS_LEAF_V1 domain separation |
| L4 | Networked Transparent Governance | STH witness quorum; monitor network; cross-log consistency verification |

The clearinghouse spec covers L1 through L3 fully, and provides the client-side integration points for L4 (witness verification, cross-log anchoring).

---

*End of AGTS Clearinghouse Specification v1.0-Draft*
