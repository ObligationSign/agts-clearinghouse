# AGTS Plugin Result V1

**Schema Identifier:** `AGTS_PLUGIN_RESULT_V1`
**Schema Version:** `1`
**Status:** FROZEN

## Overview

A Plugin Result represents the output of a single governance plugin evaluating
one transaction. Every plugin — regardless of its internal implementation —
MUST produce output conforming to this schema. The clearinghouse aggregates
multiple Plugin Results into a single Governance Envelope.

This is the **profile-as-gate** pattern: each plugin acts as an independent
evaluator, scoring the transaction on the H, C, E dimensions. The clearinghouse
then applies a policy profile to the aggregated scores to produce a verdict.

## Schema

```json
{
  "type": "AGTS_PLUGIN_RESULT_V1",
  "schema_version": "1",
  "plugin":         "<string>",
  "version":        "<semver>",
  "transaction_id": "<uuid>",
  "timestamp":      <unix_ms>,
  "verdict":        "PASS" | "REVIEW" | "BLOCK",
  "H":              <number 0..1>,
  "C":              <number 0..1>,
  "E":              <number 0..1>,
  "confidence":     <number 0..1>,
  "evidence": {
    "hash":           "<hex sha-256>",
    "uri":            "<string>",
    "merkle_anchor":  { ... }
  },
  "metadata": { ... }
}
```

## Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | YES | Always `"AGTS_PLUGIN_RESULT_V1"`. |
| `schema_version` | string | YES | Always `"1"`. |
| `plugin` | string | YES | Plugin identifier (e.g. `"semantic_firewall"`, `"finance"`, `"aco_observer"`, `"gateway_shield"`). |
| `version` | string | YES | Semantic version of the plugin implementation. |
| `transaction_id` | string | YES | Must match the parent envelope's `transaction_id`. |
| `timestamp` | integer | YES | Unix epoch milliseconds. |
| `verdict` | enum | YES | `PASS`, `REVIEW`, or `BLOCK`. |
| `H` | number [0,1] | YES | H observable score. 0 = best, 1 = worst. Higher H increases block likelihood. |
| `C` | number [0,1] | YES | C observable score. 0 = worst, 1 = best. Lower C increases block likelihood. |
| `E` | number [0,1] | YES | E observable score. 0 = best, 1 = worst. Higher E increases block likelihood. |
| `confidence` | number [0,1] | YES | Overall confidence of the plugin's evaluation. |
| `evidence.hash` | string | YES | SHA-256 hex digest of the evaluated artifact or transaction ID. |
| `evidence.uri` | string | NO | URI for evidence retrieval (e.g. `agts://aco/<audit_id>`). |
| `evidence.merkle_anchor` | object | NO | Merkle tree anchor data for the evidence. |
| `metadata` | object | YES | Plugin-specific metadata. Schema varies by plugin. |

## H, C, E at the Plugin Level

At the clearinghouse plugin aggregation level, H, C, and E are dimensionless
scores in [0, 1]. Each plugin assigns domain-specific meaning:

### H — Examples by Plugin
- Semantic Firewall: `H = 1 − attackBlockRate`
- Finance: `H = 1 − varAccuracy`
- ACO Observer: composite of risk level + fairness status + pass rate
- Gateway Shield: rises with number of loopback violations detected

### C — Examples by Plugin
- Gate-based plugins: `C = passing_gates / total_gates`
- ACO Observer: `C = passRate / 100`
- Gateway Shield: `C = 1.0` for clean requests, drops per violation

### E — Examples by Plugin
- Semantic Firewall: `E = 1 − composite`
- Gateway Shield: `E = baseCost + fieldCount × 0.005`
- ACO Observer: `E = epsilonUsed + riskContribution`

The formal information-theoretic definitions (H_formal, C_formal, E_formal)
used in the IEED framework are defined in AGTS-TERMS. At the plugin level,
H, C, E are implementation-specific scores that the clearinghouse aggregates.

## Value Ranges

All numeric H, C, E fields MUST be in the closed interval `[0, 1]`.
Implementations MUST clamp values: `max(0, min(1, value))`.
`NaN` values MUST be treated as `0`.

## Synthetic Results

A synthetic (fail-closed) result is produced when a plugin fails to respond
or times out. Synthetic results MUST have:
- `verdict: "BLOCK"`
- `H: 1.0`, `C: 0.0`, `E: 1.0`
- `confidence: 0.0`
- `metadata.synthetic: true`
- `metadata.error: "<reason>"`

This ensures the system **fails closed** — an unresponsive plugin cannot
silently permit a potentially harmful action.

## Known Plugins

| Plugin ID | Description |
|-----------|-------------|
| `semantic_firewall` | NLP-based prompt injection and safety analysis |
| `finance` | Financial risk and VaR accuracy evaluation |
| `aco_observer` | Ant Colony Optimization fairness and compliance observer |
| `gateway_shield` | Network boundary and loopback detection |
