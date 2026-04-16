# AGTS Variance Record V1

**Schema Identifier:** `AGTS_VARIANCE_RECORD_V1`
**Status:** FROZEN

## Overview

A Variance Record is the Leaf 3 artifact in the AGTS Triple-Leaf Ledger. It
is the output of the Variance Reconciliation Engine, computed after an
Execution Trace (Leaf 2) has been admitted to the log. It measures the gap
between what was authorized (Leaf 1) and what actually happened (Leaf 2).

The Variance Record closes the governance feedback loop: its classification
feeds back into the H/C/E observables via the HCE Feedback Loop, affecting
the next authorization cycle.

## Schema

### Minimal Interface (verticals.ts)

The base interface used by the log worker and protocol worker:

```json
{
  "type":                    "AGTS_VARIANCE_RECORD_V1",
  "authorization_leaf_hash": "<hex sha-256>",
  "execution_leaf_hash":     "<hex sha-256>",
  "classification":          "NOMINAL" | "DEVIATED" | "BREACHED",
  "omega_breach":            <boolean>,
  "timestamp":               <unix_ms>
}
```

### Extended Interface (MCP variance computation)

The MCP gateway produces a richer record with full H/C/E analysis:

```json
{
  "type":                    "AGTS_VARIANCE_RECORD_V1",
  "parent_auth_leaf_hash":   "<hex sha-256>",
  "parent_exec_leaf_hash":   "<hex sha-256>",
  "subject_id":              "<string>",
  "auth_state":              { "H": <number>, "C": <number>, "E": <number> },
  "exec_state":              { "H": <number>, "C": <number>, "E": <number> },
  "delta":                   { "H": <number>, "C": <number>, "E": <number> },
  "l2_distance":             <number>,
  "classification":          "NOMINAL" | "DRIFT" | "BREACH",
  "drift_direction":         { "H": "<dir>", "C": "<dir>", "E": "<dir>" },
  "auth_in_omega":           <boolean>,
  "exec_in_omega":           <boolean>,
  "omega_breach":            <boolean>,
  "timestamp":               "<ISO 8601>"
}
```

## Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | YES | Always `"AGTS_VARIANCE_RECORD_V1"`. |
| `authorization_leaf_hash` / `parent_auth_leaf_hash` | string (hex) | YES | Leaf hash of the authorization (Leaf 1). |
| `execution_leaf_hash` / `parent_exec_leaf_hash` | string (hex) | YES | Leaf hash of the Execution Trace (Leaf 2). |
| `classification` | enum | YES | `NOMINAL`, `DRIFT`/`DEVIATED`, or `BREACH`/`BREACHED`. |
| `omega_breach` | boolean | YES | `true` if authorization was in Omega but execution exited. |
| `subject_id` | string | extended | Identifier of the governed subject. |
| `auth_state` | object | extended | H/C/E triple at authorization time. |
| `exec_state` | object | extended | H/C/E triple at execution time. |
| `delta` | object | extended | Signed per-observable deltas: `{ H, C, E }`. |
| `l2_distance` | number | extended | L2 distance in the health-space `[H, C, 1-E]`. |
| `drift_direction` | object | extended | Per-observable direction: `improved`, `degraded`, or `stable`. |
| `auth_in_omega` | boolean | extended | Whether auth_state is inside the Omega region. |
| `exec_in_omega` | boolean | extended | Whether exec_state is inside the Omega region. |
| `timestamp` | integer or string | YES | Unix epoch ms or ISO 8601. |

## Variance Classification

Classification is computed from the L2 distance between authorization and
execution states in the health-space `[H, C, 1-E]`:

```
d_L2 = sqrt((H_exec - H_auth)^2 + (C_exec - C_auth)^2 + ((1-E_exec) - (1-E_auth))^2)
```

| Classification | Condition | Meaning |
|----------------|-----------|---------|
| `NOMINAL` | d_L2 ≤ 0.05 | Execution matched authorized intent within tolerance |
| `DRIFT` | 0.05 < d_L2 ≤ 0.20 | Measurable drift; within operational tolerance |
| `BREACH` | d_L2 > 0.20 | Execution exceeded authorized bounds |

## Omega Region

The Omega region Ω defines the "healthy" operating zone in H/C/E space:

```
Ω = { (H, C, E) : H ≥ 0.40 AND C ≥ 0.40 AND E ≤ 0.60 }
```

These thresholds match the AGTS Collapse Gate thresholds.

An **Omega Breach** occurs when `auth_in_omega = true` AND `exec_in_omega = false` —
the system was in a healthy state at authorization time but exited the healthy
region during execution.

## Drift Direction

Per-observable drift direction is computed as:

| Direction | Condition |
|-----------|-----------|
| `improved` | exec - auth > 0.01 (for H, C) |
| `degraded` | exec - auth < -0.01 (for H, C) |
| `stable` | abs(exec - auth) < 0.01 |

For E, the inversion is applied: the comparison uses `(1-E_exec) - (1-E_auth)`,
so positive delta E is degradation.

## HCE Feedback Loop

The Variance Record's classification triggers a nudge measurement in the
HCE Evidence Engine:

| Classification | Measurement Type | H | C | E |
|----------------|-----------------|-----|-----|------|
| `NOMINAL` | `execution_nominal` | +0.010 | +0.008 | -0.005 |
| `DRIFT` | `execution_drift` | -0.025 | -0.020 | +0.025 |
| `BREACH` | `execution_breach` | -0.050 | -0.035 | +0.050 |

Three consecutive `BREACH` classifications trigger QUARANTINE in the
Artifact Lifecycle Controller.

## Cross-Leaf Linkage

The Variance Record MUST NOT be admitted without valid `parent_auth_leaf_hash`
AND `parent_exec_leaf_hash`. The log worker MUST reject records referencing
non-existent parents with HTTP 422 and error code `PARENT_LEAF_NOT_FOUND`.

## Verification

A conforming verifier MUST check:

1. **Schema compliance** — `type` is `"AGTS_VARIANCE_RECORD_V1"`, required fields present.
2. **Parent linkage** — both parent hashes are valid 64-character hex strings.
3. **Classification valid** — one of the recognized values.
4. **Omega breach consistency** — if `auth_in_omega` and `exec_in_omega` are present,
   `omega_breach` MUST equal `auth_in_omega AND NOT exec_in_omega`.
5. **L2 distance consistency** — if `auth_state`, `exec_state`, and `l2_distance` are
   present, the computed L2 distance MUST match within ε = 0.001.
6. **Classification consistency** — if `l2_distance` is present, the classification
   MUST match the threshold table above.
