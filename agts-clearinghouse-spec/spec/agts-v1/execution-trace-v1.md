# AGTS Execution Trace V1

**Schema Identifier:** `AGTS_EXECUTION_TRACE_V1`
**Status:** FROZEN

## Overview

An Execution Trace is the Leaf 2 artifact in the AGTS Triple-Leaf Ledger. It
is the execution witness record produced after a previously authorized action
has completed. It cryptographically links the execution outcome to its
governing authorization (Leaf 1), closing the governance loop.

The trace is produced by the same clearinghouse node that produced the
authorization, providing non-repudiation: the node that declared the action
permitted also attests to what happened.

## Schema

### Minimal Interface (verticals.ts)

The base interface used by the log worker and protocol worker:

```json
{
  "type":                    "AGTS_EXECUTION_TRACE_V1",
  "authorization_leaf_hash": "<hex sha-256>",
  "executed_payload_hash":   "<hex sha-256>",
  "execution_context":       { ... },
  "timestamp":               <unix_ms>
}
```

### Extended Interface (MCP report_execution)

The MCP gateway produces a richer trace when H/C/E state is available:

```json
{
  "type":                    "AGTS_EXECUTION_TRACE_V1",
  "parent_auth_leaf_hash":   "<hex sha-256>",
  "subject_id":              "<string>",
  "outcome":                 "EXECUTED" | "FAILED" | "DEVIATED",
  "auth_state":              { "H": <number>, "C": <number>, "E": <number> },
  "exec_state":              { "H": <number>, "C": <number>, "E": <number> },
  "timestamp":               "<ISO 8601>"
}
```

## Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | YES | Always `"AGTS_EXECUTION_TRACE_V1"`. |
| `authorization_leaf_hash` / `parent_auth_leaf_hash` | string (hex) | YES | Leaf hash of the governing authorization (Leaf 1). |
| `executed_payload_hash` | string (hex) | base only | SHA-256 of the executed payload. |
| `execution_context` | object | base only | Arbitrary execution metadata. |
| `subject_id` | string | extended | Identifier of the governed subject. |
| `outcome` | enum | extended | `EXECUTED`, `FAILED`, or `DEVIATED`. |
| `auth_state` | object | extended | H/C/E triple at authorization time. |
| `exec_state` | object | extended | H/C/E triple observed after execution. |
| `timestamp` | integer or string | YES | Unix epoch ms or ISO 8601. |

## Execution State Derivation

When the caller does not provide explicit `exec_state`, the MCP gateway derives
it from the `outcome` and `auth_state`:

| Outcome | Derivation |
|---------|-----------|
| `EXECUTED` | `exec_state = auth_state` (no drift) |
| `FAILED` | `H -= 0.15`, `C -= 0.20`, `E += 0.25` (clamped to [0,1]) |
| `DEVIATED` | `H -= 0.10`, `C -= 0.15`, `E += 0.15` (clamped to [0,1]) |

If no `auth_state` is available, defaults to `{ H: 0.50, C: 0.50, E: 0.50 }`.

## Cross-Leaf Linkage

The Execution Trace MUST NOT be admitted to the transparency log without a
valid `parent_auth_leaf_hash`. The log worker MUST reject traces referencing
non-existent authorization leaves with HTTP 422 and error code
`PARENT_AUTH_NOT_FOUND`.

The log worker maintains a reverse index:
```
log_leaf_by_hash:{leaf_hash} → {leaf_index, admitted_at}
```
enabling O(1) cross-leaf verification at admission time.

## Leaf Hashing

The Execution Trace leaf hash follows the same convention as governance
envelope leaves:

```
leaf_hash = SHA-256(canonical_json(trace_body))
```

## Verification

A conforming verifier MUST check:

1. **Schema compliance** — `type` is `"AGTS_EXECUTION_TRACE_V1"`, required fields present.
2. **Parent linkage** — `parent_auth_leaf_hash` / `authorization_leaf_hash` is a valid 64-character hex string.
3. **H/C/E ranges** — if `auth_state` and `exec_state` are present, all values in [0, 1].
4. **Timestamp** — present and valid.
