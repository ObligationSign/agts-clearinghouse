# HCE Aggregation V1

**Status:** FROZEN

## Overview

The HCE aggregation algorithm combines individual plugin H, C, E scores into
a single composite assessment. It is the mathematical core of the AGTS
clearinghouse — the function that translates multiple independent evaluations
into a deterministic governance verdict.

H, C, and E are dimensionless scores in [0, 1]. At the clearinghouse
aggregation level, they carry no fixed expansion — each plugin assigns
domain-specific meaning. The formal information-theoretic definitions
(H_formal, C_formal, E_formal) used in the IEED framework are a separate
layer defined in AGTS-TERMS.

## Inputs

- `results`: array of `AGTS_PLUGIN_RESULT_V1` objects, each containing `H`, `C`, `E` values
- `profile`: a `PolicyProfile` defining threshold boundaries

## Algorithm

### Step 1: Extract Dimension Arrays

```
Hs = [r.H for r in results]
Cs = [r.C for r in results]
Es = [r.E for r in results]
```

### Step 2: Compute Aggregates

#### H_total — Weighted Mean + Tail Penalty

```
H_base = mean(Hs)
H_tail = 0.05 × max(0, max(Hs) − profile.H_max)
H_total = clamp(H_base + H_tail, 0, 1)
```

The tail penalty elevates the aggregate when any single plugin reports H
significantly above the policy threshold.

#### C_total — Geometric Mean

```
C_total = clamp(geometric_mean(max(Ci, 0.001) for Ci in Cs), 0, 1)
```

Geometric mean ensures that a single low-C plugin cannot be masked
by high-C peers. The floor of 0.001 prevents zero-collapse.

#### E_total — Weighted Mean + Tail Penalty

```
E_base = mean(Es)
E_tail = 0.05 × max(0, max(Es) − profile.E_max)
E_total = clamp(E_base + E_tail, 0, 1)
```

### Step 3: Compute φ (Phi)

The composite safety metric:

```
φ = (1 − H_total) × C_total × (1 − E_total)
```

φ ranges from 0 (worst) to 1 (best).

### Step 4: Determine Verdict

```
block_any = (H_total > profile.H_block) OR
            (C_total < profile.C_block) OR
            (E_total > profile.E_block) OR
            any(r.verdict == "BLOCK" for r in results)

pass_all  = (H_total <= profile.H_max) AND
            (C_total >= profile.C_min) AND
            (E_total <= profile.E_max)

verdict = "BLOCK"  if block_any
        = "PASS"   if pass_all
        = "REVIEW" otherwise
```

### Step 5: Round

All aggregate values MUST be rounded to 4 decimal places: `round(value, 4)`.

### Empty Results

If `results` is empty, return:
```json
{ "H_total": 0, "C_total": 0, "E_total": 0, "phi": 0, "verdict": "REVIEW" }
```

## Policy Profiles

A policy profile defines the threshold boundaries that determine verdicts.

```json
{
  "name":    "<string>",
  "H_max":   <number>,
  "C_min":   <number>,
  "E_max":   <number>,
  "H_block": <number>,
  "C_block": <number>,
  "E_block": <number>
}
```

### Standard Profiles

| Profile | H_max | C_min | E_max | H_block | C_block | E_block |
|---------|-------|-------|-------|---------|---------|---------|
| `DEFAULT` | 0.25 | 0.80 | 0.40 | 0.50 | 0.50 | 0.70 |
| `HIGH_RISK_FINANCIAL` | 0.18 | 0.90 | 0.25 | 0.35 | 0.65 | 0.50 |
| `STRICT` | 0.10 | 0.95 | 0.15 | 0.25 | 0.75 | 0.40 |
| `PERMISSIVE` | 0.40 | 0.60 | 0.55 | 0.70 | 0.30 | 0.85 |

### Profile Semantics

- **Pass thresholds** (`H_max`, `C_min`, `E_max`): All must be satisfied for `PASS`.
- **Block thresholds** (`H_block`, `C_block`, `E_block`): Any violation triggers `BLOCK`.
- The gap between pass and block thresholds is the `REVIEW` zone.

## Collapse Gate Thresholds

Separate from the clearinghouse policy profiles, the AGTS protocol defines
collapse gate thresholds applied to the IEED formal observables (H_formal,
C_formal, E_formal). These are defined in `COLLAPSE_GATE`:

| Observable | Direction | Threshold |
|------------|-----------|-----------|
| H_formal | ≥ | 0.40 |
| C_formal | ≥ | 0.40 |
| E_formal | ≤ | 0.60 |

See AGTS-TERMS for the formal IEED definitions.

## Helper Functions

### clamp(value, low, high)
```
return max(low, min(high, 0 if isnan(value) else value))
```

### weighted_mean(arr)
```
return sum(arr) / len(arr)
```

### tail_penalty(arr, threshold)
```
return 0.05 * max(0, max(arr) - threshold)
```

### geometric_mean(arr)
```
return product(max(v, 0.001) for v in arr) ** (1 / len(arr))
```

## Conformance

A conforming implementation MUST reproduce the same `H_total`, `C_total`,
`E_total`, `phi`, and `verdict` values as the reference implementation for
all test vectors in the conformance suite, within ε = 0.0001 for numeric
fields and exact match for verdict.
