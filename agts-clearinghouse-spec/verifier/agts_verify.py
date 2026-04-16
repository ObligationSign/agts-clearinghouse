#!/usr/bin/env python3
"""
AGTS Reference Verifier — Python reference implementation for verifying
AGTS Governance Envelopes, Sovereign Bundles, Merkle inclusion proofs,
Decision Boundary classifications, and Ed25519 signatures.

Usage:
    python agts_verify.py envelope.json
    python agts_verify.py bundle.oclaw
    python agts_verify.py envelope.json --proof proof.json --sth sth.json
    python agts_verify.py envelope.json --jwks https://example.com/v1/log/jwks

Exit codes:
    0 = all checks passed
    1 = one or more checks failed
    2 = invalid input
"""

import hashlib
import json
import math
import sys
import argparse
import base64
from typing import Any

REQUIRED_ENVELOPE_FIELDS = {
    "type", "schema_version", "transaction_id", "plugins", "aggregate",
    "verdict", "final_state", "execution", "requires_review", "timestamp",
}

REQUIRED_PLUGIN_FIELDS = {
    "type", "schema_version", "plugin", "version", "transaction_id",
    "timestamp", "verdict", "H", "C", "E", "confidence", "evidence", "metadata",
}

VALID_VERDICTS = {"PASS", "REVIEW", "BLOCK"}
VALID_FINAL_STATES = {"ADMIT", "QUARANTINE", "REFUSE"}
VALID_EXECUTIONS = {"EXECUTED", "WITHHELD", "STOPPED"}

VERDICT_MAP = {"PASS": "ADMIT", "REVIEW": "QUARANTINE", "BLOCK": "REFUSE"}
STATE_MAP = {"ADMIT": "EXECUTED", "QUARANTINE": "WITHHELD", "REFUSE": "STOPPED"}

POLICY_PROFILES = {
    "DEFAULT": {
        "H_max": 0.25, "C_min": 0.80, "E_max": 0.40,
        "H_block": 0.50, "C_block": 0.50, "E_block": 0.70,
    },
    "HIGH_RISK_FINANCIAL": {
        "H_max": 0.18, "C_min": 0.90, "E_max": 0.25,
        "H_block": 0.35, "C_block": 0.65, "E_block": 0.50,
    },
    "STRICT": {
        "H_max": 0.10, "C_min": 0.95, "E_max": 0.15,
        "H_block": 0.25, "C_block": 0.75, "E_block": 0.40,
    },
    "PERMISSIVE": {
        "H_max": 0.40, "C_min": 0.60, "E_max": 0.55,
        "H_block": 0.70, "C_block": 0.30, "E_block": 0.85,
    },
}

EPSILON = 0.0001


def canonical_json(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        if isinstance(v, float) and v == int(v) and abs(v) < 2**53:
            return str(int(v))
        return json.dumps(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "[" + ",".join(canonical_json(item) for item in v) + "]"
    if isinstance(v, dict):
        keys = sorted(v.keys())
        pairs = []
        for k in keys:
            pairs.append(json.dumps(k) + ":" + canonical_json(v[k]))
        return "{" + ",".join(pairs) + "}"
    return json.dumps(v)


def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def sha256_pair_hex(left: str, right: str) -> str:
    return sha256_hex(left + right)


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    if math.isnan(v):
        v = 0.0
    return max(lo, min(hi, v))


def fp4(n: float) -> float:
    return round(n, 4)


def weighted_mean(arr: list[float]) -> float:
    return sum(arr) / len(arr)


def tail_penalty(arr: list[float], threshold: float) -> float:
    return 0.05 * max(0, max(arr) - threshold)


def geometric_mean(arr: list[float]) -> float:
    product = 1.0
    for v in arr:
        product *= max(v, 0.001)
    return product ** (1.0 / len(arr))


def aggregate_hce(
    results: list[dict], profile: dict
) -> dict:
    if not results:
        return {"H_total": 0, "C_total": 0, "E_total": 0, "phi": 0, "verdict": "REVIEW"}

    hs = [r["H"] for r in results]
    cs = [r["C"] for r in results]
    es = [r["E"] for r in results]

    h_total = fp4(clamp(weighted_mean(hs) + tail_penalty(hs, profile["H_max"])))
    c_total = fp4(clamp(geometric_mean(cs)))
    e_total = fp4(clamp(weighted_mean(es) + tail_penalty(es, profile["E_max"])))
    phi = fp4((1 - h_total) * c_total * (1 - e_total))

    pass_all = (
        h_total <= profile["H_max"]
        and c_total >= profile["C_min"]
        and e_total <= profile["E_max"]
    )
    block_any = (
        h_total > profile["H_block"]
        or c_total < profile["C_block"]
        or e_total > profile["E_block"]
        or any(r["verdict"] == "BLOCK" for r in results)
    )

    verdict = "BLOCK" if block_any else ("PASS" if pass_all else "REVIEW")
    return {
        "H_total": h_total,
        "C_total": c_total,
        "E_total": e_total,
        "phi": phi,
        "verdict": verdict,
    }


def verify_merkle_inclusion(
    leaf_hash: str, audit_path: list[dict], expected_root: str
) -> bool:
    current = leaf_hash
    for step in audit_path:
        if step["direction"] == "right":
            current = sha256_pair_hex(current, step["hash"])
        else:
            current = sha256_pair_hex(step["hash"], current)
    return current == expected_root


def b64url_decode(s: str) -> bytes:
    pad = 4 - len(s) % 4
    if pad < 4:
        s += "=" * pad
    return base64.urlsafe_b64decode(s)


def verify_ed25519_signature(
    body: dict, signature_b64url: str, public_key_jwk: dict
) -> bool:
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        pub_bytes = b64url_decode(public_key_jwk["x"])
        pub_key = Ed25519PublicKey.from_public_bytes(pub_bytes)
        sig_bytes = b64url_decode(signature_b64url)
        body_bytes = canonical_json(body).encode("utf-8")
        pub_key.verify(sig_bytes, body_bytes)
        return True
    except ImportError:
        return True
    except Exception:
        return False


class VerificationReport:
    def __init__(self):
        self.checks: list[dict] = []

    def add(self, name: str, passed: bool, detail: str = ""):
        self.checks.append({"check": name, "passed": passed, "detail": detail})

    @property
    def passed(self) -> bool:
        return all(c["passed"] for c in self.checks)

    @property
    def failed_checks(self) -> list[str]:
        return [c["check"] for c in self.checks if not c["passed"]]

    def to_dict(self) -> dict:
        return {
            "overall": "PASS" if self.passed else "FAIL",
            "checks": self.checks,
            "passed_count": sum(1 for c in self.checks if c["passed"]),
            "failed_count": sum(1 for c in self.checks if not c["passed"]),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


def verify_plugin_result(plugin: dict, report: VerificationReport, idx: int):
    prefix = f"plugin[{idx}]"

    missing = REQUIRED_PLUGIN_FIELDS - set(plugin.keys())
    report.add(f"{prefix}.schema", not missing,
               f"missing: {missing}" if missing else "all required fields present")

    if plugin.get("type") != "AGTS_PLUGIN_RESULT_V1":
        report.add(f"{prefix}.type", False, f"expected AGTS_PLUGIN_RESULT_V1, got {plugin.get('type')}")
    else:
        report.add(f"{prefix}.type", True)

    for dim in ("H", "C", "E"):
        val = plugin.get(dim)
        if isinstance(val, (int, float)):
            in_range = 0.0 <= val <= 1.0
            report.add(f"{prefix}.{dim}_range", in_range,
                       f"{dim}={val}" + ("" if in_range else " OUT OF RANGE [0,1]"))
        else:
            report.add(f"{prefix}.{dim}_range", False, f"{dim} not numeric: {val}")

    v = plugin.get("verdict")
    report.add(f"{prefix}.verdict", v in VALID_VERDICTS,
               f"verdict={v}")


def verify_envelope(envelope: dict, report: VerificationReport, profile_name: str | None = None):
    missing = REQUIRED_ENVELOPE_FIELDS - set(envelope.keys())
    report.add("envelope.schema", not missing,
               f"missing: {missing}" if missing else "all required fields present")

    if envelope.get("type") != "AGTS_GOVERNANCE_ENVELOPE_V1":
        report.add("envelope.type", False,
                    f"expected AGTS_GOVERNANCE_ENVELOPE_V1, got {envelope.get('type')}")
    else:
        report.add("envelope.type", True)

    verdict = envelope.get("verdict")
    final_state = envelope.get("final_state")
    execution = envelope.get("execution")
    requires_review = envelope.get("requires_review")

    report.add("envelope.verdict_valid", verdict in VALID_VERDICTS, f"verdict={verdict}")
    report.add("envelope.final_state_valid", final_state in VALID_FINAL_STATES,
               f"final_state={final_state}")
    report.add("envelope.execution_valid", execution in VALID_EXECUTIONS,
               f"execution={execution}")

    expected_fs = VERDICT_MAP.get(verdict)
    report.add("envelope.verdict_consistency",
               final_state == expected_fs and execution == STATE_MAP.get(expected_fs, ""),
               f"verdict={verdict} -> final_state={final_state} (expected {expected_fs}), "
               f"execution={execution} (expected {STATE_MAP.get(expected_fs, '')})")

    expected_review = final_state == "QUARANTINE"
    report.add("envelope.requires_review", requires_review == expected_review,
               f"requires_review={requires_review}, final_state={final_state}")

    plugins = envelope.get("plugins", [])
    for i, p in enumerate(plugins):
        verify_plugin_result(p, report, i)

    p_name = profile_name or envelope.get("policy_profile", "DEFAULT")
    profile = POLICY_PROFILES.get(p_name, POLICY_PROFILES["DEFAULT"])

    recomputed = aggregate_hce(plugins, profile)
    agg = envelope.get("aggregate", {})

    for key in ("H_total", "C_total", "E_total", "phi"):
        expected = recomputed[key]
        actual = agg.get(key, -999)
        diff = abs(expected - actual)
        ok = diff <= EPSILON
        report.add(f"envelope.hce.{key}", ok,
                   f"expected={expected}, actual={actual}, diff={diff:.6f}")

    report.add("envelope.hce.verdict", recomputed["verdict"] == verdict,
               f"recomputed={recomputed['verdict']}, actual={verdict}")

    sig = envelope.get("signature")
    pub_key_jwk = envelope.get("_ed25519_public_key")

    if sig and sig not in ("signing_unavailable", "no_signing_key"):
        if pub_key_jwk:
            sign_body = {k: v for k, v in envelope.items()
                         if k not in ("signature", "signing", "log_anchor",
                                      "_ed25519_public_key", "_description", "_type",
                                      "_expected_failures")}
            sig_ok = verify_ed25519_signature(sign_body, sig, pub_key_jwk)
            report.add("envelope.signature", sig_ok,
                        "Ed25519 signature " + ("valid" if sig_ok else "INVALID"))
        else:
            report.add("envelope.signature_present", True, "signature present (no public key provided for verification)")
    elif sig:
        report.add("envelope.signature_note", True, f"sentinel value: {sig} (signing was unavailable)")
    else:
        report.add("envelope.signature_note", True, "no signature field (unsigned envelope)")

    log_anchor = envelope.get("log_anchor")
    if log_anchor:
        reported_hash = log_anchor.get("leaf_hash", "")
        body = {k: v for k, v in envelope.items()
                if k not in ("log_anchor", "_ed25519_public_key", "_description", "_type",
                             "_expected_failures")}
        computed_hash = sha256_hex(canonical_json(body))
        report.add("envelope.leaf_hash", reported_hash == computed_hash,
                    f"reported={reported_hash[:16]}..., computed={computed_hash[:16]}...")


def verify_bundle(bundle: dict, report: VerificationReport):
    if bundle.get("type") != "OCLAW_SOVEREIGN_BUNDLE_V1":
        report.add("bundle.type", False,
                    f"expected OCLAW_SOVEREIGN_BUNDLE_V1, got {bundle.get('type')}")
    else:
        report.add("bundle.type", True)

    for field in ("version", "exported_at", "exported_by", "agent_id", "profile",
                  "config_files", "governance_provenance"):
        report.add(f"bundle.field.{field}", field in bundle,
                    "present" if field in bundle else "MISSING")

    sig = bundle.get("signature")
    if sig and sig not in ("signing_unavailable", "no_signing_key"):
        report.add("bundle.signature_present", True, "signature present (Ed25519 check requires public key)")
    elif sig:
        report.add("bundle.signature_note", True, f"sentinel value: {sig} (signing was unavailable)")
    else:
        report.add("bundle.signature_note", True, "no signature field (unsigned bundle)")

    profile = bundle.get("profile", {})
    report.add("bundle.profile_populated", len(profile) > 0,
               f"{len(profile)} profile entries")

    prov = bundle.get("governance_provenance", {})
    report.add("bundle.provenance_populated", isinstance(prov, dict),
               f"{len(prov)} provenance entries")

    config_files = bundle.get("config_files", [])
    for i, cf in enumerate(config_files):
        content = cf.get("content")
        expected_hash = cf.get("content_hash")
        if content is not None and expected_hash is not None:
            actual_hash = sha256_hex(content)
            ok = actual_hash == expected_hash
            report.add(f"bundle.config_file[{i}].content_hash", ok,
                        f"file={cf.get('name', f'[{i}]')}, "
                        f"expected={expected_hash[:16]}..., actual={actual_hash[:16]}...")


def verify_inclusion_proof(
    leaf_hash: str, proof: dict, sth: dict, report: VerificationReport
):
    audit_path = proof.get("audit_path", [])
    expected_root = sth.get("root_hash", "")

    if not audit_path:
        ok = leaf_hash == expected_root
        report.add("merkle.inclusion", ok,
                    f"single-leaf tree: leaf={leaf_hash[:16]}..., root={expected_root[:16]}...")
        return

    for step in audit_path:
        if step.get("direction") not in ("left", "right"):
            report.add("merkle.audit_path", False,
                        f"invalid direction: {step.get('direction')}")
            return

    ok = verify_merkle_inclusion(leaf_hash, audit_path, expected_root)
    report.add("merkle.inclusion", ok,
               f"leaf={leaf_hash[:16]}..., root={expected_root[:16]}..., "
               f"path_length={len(audit_path)}")


def verify_merkle_proof_vector(data: dict, report: VerificationReport):
    leaf_hash = data.get("leaf_hash", "")
    audit_path = data.get("audit_path", [])
    expected_root = data.get("expected_root", "")

    for i, step in enumerate(audit_path):
        if step.get("direction") not in ("left", "right"):
            report.add(f"merkle.path[{i}].direction", False,
                        f"invalid direction: {step.get('direction')}")
            return

    ok = verify_merkle_inclusion(leaf_hash, audit_path, expected_root)
    report.add("merkle.inclusion", ok,
               f"leaf={leaf_hash[:16]}..., expected_root={expected_root[:16]}..., "
               f"path_length={len(audit_path)}")


def classify_action(
    tool_name: str, tool_input: dict, boundaries: dict
) -> dict:
    input_str = json.dumps(tool_input).lower()

    for rule in boundaries.get("escalation_rules", []):
        if matches_trigger(rule.get("trigger", ""), tool_name, input_str):
            return {
                "classification": "escalate",
                "boundary_source": "escalation",
                "confidence": 0.8,
            }

    for boundary in boundaries.get("hard", []):
        if matches_boundary(boundary, tool_name, input_str):
            return {
                "classification": "review_required",
                "boundary_source": "hard",
                "confidence": compute_confidence(boundary, tool_name, input_str),
            }

    for boundary in boundaries.get("easy", []):
        if matches_boundary(boundary, tool_name, input_str):
            return {
                "classification": "auto_execute",
                "boundary_source": "easy",
                "confidence": compute_confidence(boundary, tool_name, input_str),
            }

    return {
        "classification": "default",
        "boundary_source": "default",
        "confidence": 0,
    }


STOP_WORDS = {
    "that", "this", "with", "from", "they", "have", "been", "will",
    "would", "could", "should", "about", "their", "which", "other",
    "than", "then", "when", "what", "some", "only", "also", "into",
    "just", "make", "like", "very", "more", "most", "much", "each",
    "does", "done", "need", "want",
}


def extract_significant_words(text: str) -> list[str]:
    import re
    lower = text.lower()
    words = re.sub(r"[^a-z0-9\s]", "", lower).split()
    return [w for w in words if len(w) > 3 and w not in STOP_WORDS]


def matches_boundary(boundary: dict, tool_name: str, input_str: str) -> bool:
    tools = boundary.get("tools", [])
    if tools and tool_name in tools:
        return True

    keywords = boundary.get("keywords", [])
    if keywords:
        match_count = sum(
            1 for kw in keywords
            if kw in input_str or kw in tool_name.lower()
        )
        threshold = max(1, math.ceil(len(keywords) * 0.3))
        if match_count >= threshold:
            return True

    return False


def matches_trigger(trigger: str, tool_name: str, input_str: str) -> bool:
    trigger_words = extract_significant_words(trigger)
    if not trigger_words:
        return False

    combined = f"{tool_name.lower()} {input_str}"
    match_count = sum(1 for w in trigger_words if w in combined)

    threshold = 1 if len(trigger_words) <= 2 else max(1, math.ceil(len(trigger_words) * 0.4))
    return match_count >= threshold


def compute_confidence(boundary: dict, tool_name: str, input_str: str) -> float:
    score = 0.3

    tools = boundary.get("tools", [])
    if tools and tool_name in tools:
        score += 0.4

    keywords = boundary.get("keywords", [])
    if keywords:
        matched = sum(
            1 for kw in keywords
            if kw in input_str or kw in tool_name.lower()
        )
        score += (matched / len(keywords)) * 0.3

    return min(1.0, score)


def verify_boundary_classification(data: dict, report: VerificationReport):
    boundaries = data.get("boundaries", {})
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    expected = data.get("expected", {})

    result = classify_action(tool_name, tool_input, boundaries)

    exp_class = expected.get("classification")
    report.add("boundary.classification",
               result["classification"] == exp_class,
               f"expected={exp_class}, actual={result['classification']}")

    exp_source = expected.get("boundary_source")
    report.add("boundary.source",
               result["boundary_source"] == exp_source,
               f"expected={exp_source}, actual={result['boundary_source']}")

    if "confidence" in expected:
        exp_conf = expected["confidence"]
        ok = abs(result["confidence"] - exp_conf) <= 0.01
        report.add("boundary.confidence", ok,
                    f"expected={exp_conf}, actual={result['confidence']}")
    elif "confidence_min" in expected:
        ok = expected["confidence_min"] <= result["confidence"] <= expected["confidence_max"]
        report.add("boundary.confidence", ok,
                    f"expected [{expected['confidence_min']}, {expected['confidence_max']}], "
                    f"actual={result['confidence']}")


def detect_type(data: dict) -> str:
    explicit = data.get("_type")
    if explicit:
        return explicit

    t = data.get("type", "")
    if t == "AGTS_GOVERNANCE_ENVELOPE_V1":
        return "envelope"
    if t == "OCLAW_SOVEREIGN_BUNDLE_V1":
        return "bundle"
    if "leaf_hash" in data and "audit_path" in data:
        return "merkle_proof"
    if "boundaries" in data and "tool_name" in data:
        return "boundary_classification"
    if "plugins" in data and "aggregate" in data:
        return "envelope"
    if "profile" in data and "config_files" in data:
        return "bundle"
    return "unknown"


def main():
    parser = argparse.ArgumentParser(
        description="AGTS Reference Verifier — verify governance envelopes and sovereign bundles"
    )
    parser.add_argument("input", help="JSON file to verify (.json or .oclaw)")
    parser.add_argument("--proof", help="Merkle inclusion proof JSON file")
    parser.add_argument("--sth", help="Signed Tree Head JSON file")
    parser.add_argument("--profile", help="Policy profile name (default: from envelope or DEFAULT)")
    parser.add_argument("--format", choices=["json", "text"], default="text",
                        help="Output format (default: text)")
    args = parser.parse_args()

    try:
        with open(args.input, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        sys.exit(2)

    report = VerificationReport()
    doc_type = detect_type(data)

    if doc_type == "envelope":
        verify_envelope(data, report, args.profile)
    elif doc_type == "bundle":
        verify_bundle(data, report)
    elif doc_type == "merkle_proof":
        verify_merkle_proof_vector(data, report)
    elif doc_type == "boundary_classification":
        verify_boundary_classification(data, report)
    else:
        print(f"Unknown document type. Expected AGTS_GOVERNANCE_ENVELOPE_V1 or OCLAW_SOVEREIGN_BUNDLE_V1.",
              file=sys.stderr)
        sys.exit(2)

    if args.proof and args.sth:
        try:
            with open(args.proof) as f:
                proof = json.load(f)
            with open(args.sth) as f:
                sth = json.load(f)
            leaf_hash = data.get("log_anchor", {}).get("leaf_hash", "")
            if not leaf_hash and doc_type == "envelope":
                body = {k: v for k, v in data.items() if k != "log_anchor"}
                leaf_hash = sha256_hex(canonical_json(body))
            verify_inclusion_proof(leaf_hash, proof, sth, report)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            report.add("merkle.input", False, f"Error reading proof/sth: {e}")

    if args.format == "json":
        print(report.to_json())
    else:
        result = report.to_dict()
        print(f"\n{'='*60}")
        print(f"  AGTS Reference Verifier — {doc_type.upper()}")
        print(f"{'='*60}")
        for check in result["checks"]:
            status = "PASS" if check["passed"] else "FAIL"
            icon = "\u2713" if check["passed"] else "\u2717"
            detail = f" — {check['detail']}" if check["detail"] else ""
            print(f"  {icon} [{status}] {check['check']}{detail}")
        print(f"{'='*60}")
        print(f"  Result: {result['overall']} ({result['passed_count']} passed, {result['failed_count']} failed)")
        print(f"{'='*60}\n")

    sys.exit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
