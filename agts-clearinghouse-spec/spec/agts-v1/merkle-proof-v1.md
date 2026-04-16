# Merkle Transparency Log V1

**Status:** FROZEN

## Overview

AGTS uses a SHA-256 Merkle tree as a tamper-evident transparency log. Every
governance envelope, after signing, is hashed and admitted as a leaf into the
append-only log. The log provides:

1. **Immutability** — once a leaf is admitted, it cannot be altered or removed
   without invalidating all subsequent tree heads.
2. **Public verifiability** — anyone with the leaf hash can obtain an inclusion
   proof and verify it against a signed tree head, without access to the full log.
3. **Consistency** — any two signed tree heads can be verified for consistency,
   proving the log is append-only.

This is the transparency mechanism that makes **governed agentic operations**
auditable: every action an AI agent takes under AGTS governance leaves an
indelible, publicly verifiable record.

## Leaf Hashing

The leaf hash is the SHA-256 digest of the canonical JSON serialization of
the governance envelope (including `signature` and `signing` fields, but
with `log_anchor` omitted since it is set after admission):

```
leaf_body = envelope - {log_anchor}
leaf_hash = SHA-256(canonical_json(leaf_body))
```

The canonical JSON serialization sorts keys lexicographically at every nesting
level, omits `undefined` values, and uses no whitespace.

## Tree Structure

The tree is a standard binary Merkle hash tree (RFC 6962 style):

```
leaf_node(data) = SHA-256(data)
inner_node(left, right) = SHA-256(left || right)
```

Where `||` denotes byte concatenation of the hex-encoded hashes (lowercase).

**Note:** Unlike RFC 6962, AGTS concatenates hex strings rather than raw bytes:
```
inner_hash = SHA-256(hex_left + hex_right)
```

## Signed Tree Head (STH)

The log periodically publishes a Signed Tree Head:

```json
{
  "tree_size":  <integer>,
  "root_hash":  "<hex sha-256>",
  "timestamp":  <unix_ms>,
  "log_signature": "<base64url>"
}
```

The `log_signature` is an Ed25519 (or ECDSA P-256) signature over the canonical
JSON of the STH body (excluding the signature field itself):

```
sth_body = {"root_hash": ..., "timestamp": ..., "tree_size": ...}
log_signature = sign(log_key, canonical_json(sth_body))
```

## Inclusion Proof

An inclusion proof demonstrates that a specific leaf exists at a given position
in a tree of a given size. The proof is an array of path steps:

```json
{
  "leaf_index": <integer>,
  "audit_path": [
    { "hash": "<hex sha-256>", "direction": "left" | "right" },
    ...
  ]
}
```

### Direction Semantics

Each step in the audit path provides a sibling hash and the direction of that
sibling relative to the computed intermediate hash:

- `"right"`: the sibling is on the right → `next = SHA-256(current + step.hash)`
- `"left"`: the sibling is on the left → `next = SHA-256(step.hash + current)`

### Verification Algorithm

```python
def verify_inclusion(leaf_hash, audit_path, expected_root):
    current = leaf_hash
    for step in audit_path:
        if step["direction"] == "right":
            current = sha256_hex(current + step["hash"])
        else:
            current = sha256_hex(step["hash"] + current)
    return current == expected_root
```

## Tree Size Pinning

When requesting an inclusion proof, the verifier MUST specify the `tree_size`
from a previously obtained STH. This ensures the proof is verified against a
consistent snapshot:

```
GET /v1/log/inclusion/{leaf_hash}?tree_size={sth.tree_size}
```

Without tree size pinning, the log could return a proof against a different
tree head than the one the verifier holds, leading to false verification failures.

## Public Key Distribution

Log signing keys are distributed via a JWKS endpoint:

```
GET /v1/log/jwks
```

Response:
```json
{
  "keys": [
    {
      "kty": "OKP",
      "crv": "Ed25519",
      "x": "<base64url>",
      "kid": "<key-id>"
    }
  ]
}
```

Governance envelope signing keys may use a separate JWKS endpoint:
```
GET /v1/clearinghouse/jwks
```

## Verification Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /v1/log/sth` | Current Signed Tree Head |
| `GET /v1/log/inclusion/{leaf_hash}?tree_size=N` | Inclusion proof |
| `GET /v1/log/jwks` | Log signing public keys |
| `GET /v1/clearinghouse/jwks` | Envelope signing public keys |
| `GET /v1/log/leaf/{leaf_hash}` | Retrieve leaf payload |
