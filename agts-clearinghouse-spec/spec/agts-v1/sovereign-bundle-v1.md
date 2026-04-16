# OCLAW Sovereign Bundle V1

**Schema Identifier:** `OCLAW_SOVEREIGN_BUNDLE_V1`
**Version:** `1.0`
**File Extension:** `.oclaw`
**Status:** FROZEN

## Overview

A Sovereign Bundle is a portable, tamper-evident artifact that encapsulates
an agent's complete operational identity: profile data, configuration files,
content hashes, governance provenance, and an Ed25519 signature. The bundle
is owned by the human operator and can be exported, verified, and imported
into any compatible AGTS agent instance.

The bundle embodies the principle of **governed knowledge** — it is not merely
a backup, but a signed attestation of the agent's configuration at a point
in time, with cryptographic links to the governance decisions that shaped it.

## Schema

```json
{
  "type":                  "OCLAW_SOVEREIGN_BUNDLE_V1",
  "version":               "1.0",
  "exported_at":           "<ISO 8601>",
  "exported_by":           "<email>",
  "agent_id":              "<string>",
  "profile":               { ... },
  "config_files":          [ ... ],
  "file_provenance":       { ... },
  "governance_provenance": { ... },
  "heartbeat_items":       [ ... ],
  "heartbeat_config":      { ... },
  "signature":             "<base64url>",
  "signing": {
    "alg":     "Ed25519",
    "key_id":  "<string>",
    "signed_at": <unix_ms>
  }
}
```

## Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | YES | Always `"OCLAW_SOVEREIGN_BUNDLE_V1"`. |
| `version` | string | YES | Always `"1.0"`. |
| `exported_at` | string (ISO 8601) | YES | Timestamp of export. |
| `exported_by` | string (email) | YES | Email of the exporting operator. |
| `agent_id` | string | YES | Unique identifier of the agent instance. |
| `profile` | object | YES | Key-value map of profile data entries. |
| `config_files` | array | YES | Generated configuration files with names and content. |
| `file_provenance` | object | YES | Map of config file names to their governance provenance. |
| `governance_provenance` | object | YES | Map of profile keys to governance decision metadata. |
| `heartbeat_items` | array | YES | Active/proposed heartbeat monitoring items. |
| `heartbeat_config` | object | YES | Digest frequency, style, and schedule configuration. |
| `signature` | string | YES | Ed25519 signature over the canonical JSON body. |
| `signing` | object | with sig | Signing metadata (algorithm, key ID, timestamp). |

## Signing

The signature covers the entire bundle body excluding `signature` and `signing`:

```
sign_body = bundle - {signature, signing}
signature = Ed25519_sign(private_key, UTF8(canonical_json(sign_body)))
```

Sentinel values for `signature`:
- `"signing_unavailable"` — signing key was present but signing failed
- `"no_signing_key"` — no signing key was configured

These sentinels indicate the bundle was exported without cryptographic signing
and MUST NOT be treated as valid signatures.

## Import Verification

When importing a bundle, a conforming implementation MUST:

1. **Signature check** — verify Ed25519 signature against the issuing key.
2. **Tenant match** — verify `exported_by` matches the importing operator's email.
3. **Schema validation** — verify all required fields are present and correctly typed.
4. **Content hash verification** — if config files include hashes, verify them against content.

A failed signature check MUST reject the import. A tenant mismatch MUST
reject the import (bundles are non-transferable by default).

## Governance Provenance

The `governance_provenance` map links profile data entries back to the
governance decisions that produced them:

```json
{
  "profile_key": {
    "transaction_id": "<uuid>",
    "leaf_hash": "<hex>",
    "timestamp": <unix_ms>,
    "verdict": "PASS"
  }
}
```

This enables end-to-end traceability: from a profile value, to the governance
decision that approved it, to the transparency log entry that records it.
