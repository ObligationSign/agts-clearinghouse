# AGTS-TERMS — Terminology and Definitions

## Autonomous Governance Transparency Standard

**Version:** 0.1-Draft  
**Date:** March 2026  
**Status:** NORMATIVE  
**Audience:** All implementors, reviewers, certifiers, and auditors of the AGTS specification suite  
**Classification:** Normative vocabulary — no protocol behavior is defined here

---

## Preamble

This document defines the normative terminology used across the Autonomous Governance Transparency Standard (AGTS) specification suite.

All specifications in the AGTS suite — AGTS-0 through AGTS-12 — MUST use terms as defined in this document. Where a term was previously defined in either the RTR Protocol Suite or the OSCP Protocol Suite, its AGTS definition supersedes the source-suite definition for all AGTS-conforming implementations. The source-suite term is noted for traceability.

---

## 1. Normative Language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are to be interpreted as described in RFC 2119.

Terms defined in this document appear in **bold** at their definition site and in regular weight thereafter.

### Cryptographic Primitives

Unless otherwise stated in a specific section, the following primitive definitions apply across the entire AGTS suite:

**Hash function.** `SHA256(x)` refers to the SHA-256 algorithm as defined in FIPS 180-4. Implementations MUST NOT substitute SHA-224, SHA-512/256, or any truncated variant without an explicit version identifier distinguishing the output namespace.

**Canonical JSON.** `canonical_json(x)` refers to the JSON Canonicalization Scheme as defined in RFC 8785. Key requirements: keys sorted lexicographically by Unicode code point; no insignificant whitespace; UTF-8 encoding; no trailing commas. Implementations MUST produce byte-identical output for the same input object to ensure identical Leaf Hashes across independent implementations.

**Signature algorithm.** `Sign(x)` for log operator signatures and authority signatures MUST use one of:
- Ed25519 (RFC 8032) — recommended for new deployments
- ECDSA with curve P-256 and SHA-256 (FIPS 186-5) — acceptable for enterprise environments

Implementations MUST NOT use RSA, ECDSA with curves other than P-256, or any algorithm not listed above for signing STHs or Governance Envelopes in AGTS-conforming deployments. The algorithm used MUST be declared in the Verification Policy Bundle.

---

## 2. Suite Identity

### Autonomous Governance Transparency Standard (AGTS)

The **Autonomous Governance Transparency Standard** is the unified specification suite that integrates the RTR Protocol Suite (governance layer) and the OSCP Protocol Suite (transparency layer) into a single coherent standard for measurable, validated, cryptographically recorded, and independently verifiable autonomous system governance.

```
AGTS = RTR (governance) + OSCP (transparency)
```

### RTR Protocol Suite

The **RTR Protocol Suite** is the source governance specification, comprising RTR-CAP (capability measurement), RTR-GOV (governance validation), and RTR-CONFORMANCE (certification). Within AGTS, RTR content is incorporated into AGTS-1, AGTS-2, and AGTS-9 respectively.

### OSCP Protocol Suite

The **OSCP Protocol Suite** (ObligationSign Core Protocol) is the source transparency specification, comprising OSCP-0 through OSCP-8 and OSCP-TERMS. Within AGTS, OSCP content is incorporated into AGTS-3 through AGTS-8.

---

## 3. Protocol Layers

AGTS defines five logical protocol layers. Every term in this document belongs to one or more of these layers.

```
Governance Layer        measurement and validation of autonomous system updates
Envelope Layer          packaging governance artifacts for transparency admission
Transparency Layer      append-only recording of governance artifacts
Verification Layer      independent checking of log integrity
Trust Policy Layer      client-side trust decisions
```

---

## 4. Governance Layer Terms

These terms originate in the RTR Protocol Suite. They govern autonomous system capability measurement and update validation.

---

### Task Probability Space

The **Task Probability Space** is the triple $(T, \mathcal{A}, \mathcal{D})$ where $T$ is the task domain (a measurable space of task instances $\tau$), $\mathcal{A}$ is the action space available to the system, and $\mathcal{D}$ is the declared deployment distribution over $T$.

The deployment distribution $\mathcal{D}$ MUST be explicitly declared before any capability measurement is performed. It is referenced by `task_distribution_hash` in every Capability Certificate.

*Source: AGTS-1 (RTR-CAP §3.1)*

---

### Performance Function

The **Performance Function** $P : \mathcal{S} \times T \to [0,1]$ maps a system state $S$ and task instance $\tau$ to a normalized performance score. A score of 1 represents perfect performance; a score of 0 represents complete failure. The Performance Function MUST be bounded and measurable.

*Source: AGTS-1 (RTR-CAP §3.2)*

---

### Capability Functional

The **Capability Functional** $\mathrm{Cap}(S; \mathcal{D}) = \mathbb{E}_{\tau \sim \mathcal{D}}[P(S, \tau)]$ is the expected performance of system state $S$ under deployment distribution $\mathcal{D}$.

*Source: AGTS-1 (RTR-CAP §3.3)*

---

### Tail-Robust Capability

The **Tail-Robust Capability** $\mathrm{Cap}_\beta(S; \mathcal{D})$ is the capability analogue of Conditional Value at Risk (CVaR) at level $1 - \beta$. It measures expected performance over the worst $(1-\beta)$ fraction of the deployment distribution:

$$\mathrm{Cap}_\beta(S; \mathcal{D}) = \inf_{A \in \mathcal{C}_\beta} \mathbb{E}_{\tau \sim \mathcal{D}}[P(S, \tau) \mid \tau \in A]$$

where $\mathcal{C}_\beta = \{A \subseteq T : \mathcal{D}(A) \geq 1 - \beta\}$.

The **tail parameter** $\beta \in (0,1)$ MUST be declared in the Evaluation Configuration. Smaller $\beta$ focuses certification on more extreme tail scenarios.

*Source: AGTS-1 (RTR-CAP §3.4, §5)*

---

### PAC Estimation Margin

The **PAC Estimation Margin** $\varepsilon(n, \beta, \delta)$ is the statistical bound on the accuracy of the empirical capability estimate:

$$\varepsilon(n, \beta, \delta) = \sqrt{\frac{\ln(1/\delta)}{2\lfloor (1-\beta)n \rfloor}}$$

For sample size $n$, tail parameter $\beta$, and confidence level $1-\delta$, with probability at least $1-\delta$ over the draw of $n$ evaluation tasks:

$$\left|\widehat{\mathrm{Cap}}_\beta - \mathrm{Cap}_\beta\right| \leq \varepsilon(n, \beta, \delta)$$

*Source: AGTS-1 (RTR-CAP §6)*

---

### Capability Certificate

A **Capability Certificate** ($\mathrm{CC}_t$) is the structured measurement artifact produced at evaluation iteration $t$ by the governance measurement protocol (AGTS-1). It records:

- the tail-robust capability estimate $\widehat{\mathrm{Cap}}_\beta$
- the PAC estimation margin $\varepsilon$
- the certification rule result
- the task distribution hash
- the evaluation seed
- a hash chain linking consecutive certificates

The Capability Certificate is the primary input to the governance validation protocol. An AGTS-2 Proof Bundle MUST reference the $\mathrm{CC}_t$ produced in the same iteration.

*Source: AGTS-1 (RTR-CAP §3.5, §8)*

---

### System State

The **System State** at iteration $t$ is $S_t = (\theta_t, \phi_t)$ where $\theta_t$ denotes the plant parameters (model weights, inference configurations — typically frozen) and $\phi_t$ denotes the artifact parameters subject to governance-controlled recursive improvement. The governance protocol governs $\phi_t$ only; it does not require access to or modification of $\theta_t$.

*Source: AGTS-2 (RTR-GOV §3.1)*

---

### Candidate Update

A **Candidate Update** $\Delta S_t = \widetilde{S}_{t+1} - S_t$ is the proposed change to the system state generated by the Learning Operator. The candidate state is $\widetilde{S}_{t+1} = S_t + \Delta S_t$.

*Source: AGTS-2 (RTR-GOV §3.2)*

---

### Evaluation Record

The **Evaluation Record** $\mathcal{E}_t$ is the collection of measurement evidence assembled during a single governance iteration. It contains the performance scores $P(S, \tau_i)$, the Capability Certificate, and gate-by-gate evidence (bootstrap CI, ablation results, evidence classification). The Validation Predicate $\mathcal{V}(S_t, \widetilde{S}_{t+1}, \mathcal{E}_t)$ operates on this object.

The Evaluation Record is an internal iteration object; its contents are recorded in both $\mathrm{CC}_t$ and $\mathrm{PB}_t$ but it is not independently stored.

*Source: AGTS-2 (RTR-GOV §3.3)*

---

### Validation Predicate

The **Validation Predicate** $\mathcal{V}(S_t, \widetilde{S}_{t+1}, \mathcal{E}_t) \in \{0, 1\}$ is the central enforcement mechanism of the governance protocol. It is a conjunction of $N$ gates ($N \geq 5$ for conformance):

$$\mathcal{V}(S_t, \widetilde{S}_{t+1}, \mathcal{E}_t) = \prod_{i=1}^{N} G_i(S_t, \widetilde{S}_{t+1}, \mathcal{E}_t)$$

The predicate evaluates to 1 if and only if all gates pass simultaneously. Otherwise it returns 0 and the candidate is rejected.

*Source: AGTS-2 (RTR-GOV §3.5, §5.1)*

---

### Fail-Closed Rule

The **Fail-Closed Rule** is the normative update acceptance rule:

$$S_{t+1} := \begin{cases} \Pi_\Omega(S_t + \Delta S_t) & \text{if } \mathcal{V} = 1 \\ S_t & \text{if } \mathcal{V} = 0 \end{cases}$$

When the predicate fails, the system state is unchanged. Ambiguous or missing evidence results in rejection, not acceptance. No partial acceptance is possible.

*Source: AGTS-2 (RTR-GOV §4.3)*

---

### Admissible Region

The **Admissible Region** $\Omega \subset \mathbb{R}^d$ is a nonempty compact convex set representing the operational constraints on artifact parameters $\phi_t$. The **Projection Operator** $\Pi_\Omega$ maps any accepted candidate to its nearest point in $\Omega$, guaranteeing bounded evolution.

*Source: AGTS-2 (RTR-GOV §3.6)*

---

### Validation Gate

A **Validation Gate** $G_i \in \{0, 1\}$ is a single boolean check within the Validation Predicate. The five mandatory gates are:

| Gate | Name | Condition |
|---|---|---|
| G1 | Statistical Confidence | Bootstrap CI lower bound for score improvement exceeds zero at declared significance level |
| G2 | Causal Attribution | Measured improvement is causally attributable to the updated artifact, not confounding factors |
| G3 | Regression Safety | No protected metric degrades beyond declared tolerance |
| G4 | Evidence Integrity | Evidence is classified HOOKED, ATTESTED, or INSTRUMENTED — not PROXY |
| G5 | Human Authorization | Update is authorized by the Designated Human Operator |

Additional gates G6 through Gn MAY be added by vertical instantiations or federation configurations.

*Source: AGTS-2 (RTR-GOV §5.2–§5.6)*

---

### Artifact Lifecycle State

The **Artifact Lifecycle** is a finite state machine governing the progression of candidate artifacts:

| State | Description |
|---|---|
| PROPOSED | Candidate generated by Learning Operator; admissibility pre-check pending |
| QUARANTINE | Candidate under evaluation; sandboxed, not yet active |
| ACTIVE | Artifact accepted; $\mathcal{V} = 1$ and human authorization received |
| LOCKBOX | Previous active artifact preserved for rollback and audit |
| REJECTED | Candidate failed validation; destroyed, rejection record preserved |
| RETIRED | Artifact exceeded retention policy; retained for deterministic replay |

Artifacts MUST NOT reach ACTIVE without passing QUARANTINE and satisfying $\mathcal{V} = 1$.

*Source: AGTS-2 (RTR-GOV §4.2)*

---

### Proof Bundle

A **Proof Bundle** ($\mathrm{PB}_t = \mathcal{C}(S_t, S_{t+1}, \mathcal{E}_t)$) is the certification artifact generated for each accepted update. It is the primary object enabling independent verification, regulatory audit, and deterministic replay. It records:

- system state before and after the update (as hashes)
- per-gate results and evidence
- bootstrap confidence intervals
- ablation evidence and causal fraction
- the linked Capability Certificate ID
- a `parent_bundle_hash` linking to the previous Proof Bundle
- the evaluation seed and configuration hash enabling deterministic replay
- a cryptographic signature over all fields

Proof Bundles form an append-only hash chain. Modifying any field in $\mathrm{PB}_k$ invalidates all subsequent bundles.

**AGTS integration rule:** Every accepted $\mathrm{PB}_t$ MUST be transformed into exactly one AGTS Governance Envelope (Rule 2). The `artifact_hash` field of the Governance Envelope MUST equal SHA256($\mathrm{PB}_t$).

*Source: AGTS-2 (RTR-GOV §3.4, §6)*

---

### Deterministic Replay

**Deterministic Replay** is the protocol-level guarantee that any accepted update can be independently re-evaluated from its Proof Bundle alone, producing bit-exact identical results: identical metric values, identical gate verdicts, identical bootstrap confidence intervals.

Deterministic replay requires:
- platform-independent PRNG seeded from `PB_t.seed`
- deterministic floating-point operations across platforms
- the task distribution reconstructable from `task_distribution_hash`
- the artifact state reconstructable from `artifact_hashes`

Deterministic replay enables audit without access to live system state or model weights.

*Source: AGTS-2 (RTR-GOV §7)*

---

### Hash Chain

A **Hash Chain** is a sequence of artifacts where each artifact includes the SHA-256 hash of its predecessor. AGTS maintains two distinct hash chains:

1. **Proof Bundle chain** — $\mathrm{PB}_0 \to \mathrm{PB}_1 \to \cdots \to \mathrm{PB}_t$ via `parent_bundle_hash`
2. **Capability Certificate chain** — linking consecutive $\mathrm{CC}_t$ artifacts

Both chains are tamper-evident: modifying any artifact invalidates all successor hashes.

*Source: AGTS-2 (RTR-GOV §6), AGTS-1 (RTR-CAP §8)*

---

### AGTS Certificate

An **AGTS Certificate** is the externally-issued certification artifact produced by the AGTS Technical Steering Committee after an implementation passes the AGTS Conformance Test Suite at a declared conformance level. It records:

- conformance level (1, 2, 3, or 4)
- implementation identity
- test suite version
- Proof Bundle chain head hash
- measured capability at time of certification

*Source: AGTS-9*

---

### Intent-Execution Entropy Delta (IEED)

The **Intent-Execution Entropy Delta** (IEED) is the information-theoretic measurement framework that quantifies the divergence between declared authorization intent and observed execution behavior. It replaces RTR's density-matrix formalism with probability distributions defined over a finite alphabet of AGTS action types, making the observables computable at the governance layer without access to quantum state representations.

IEED records *authorization* (what was declared as permitted) and compares it against *occurrence* (what was observed).

IEED produces three gate observables — H_formal, C_formal, and E_formal — that together form the AGTS analogue of the RTR I1 Commitment Safety invariant.

*Source: AGTS-2 (RTR-GOV §1)*

---

### IEED Intent Alphabet

The **IEED Intent Alphabet** $\mathcal{A}$ is the finite set of all action type strings recognized by the IEED framework. It is partitioned into two disjoint subsets:

$$\mathcal{A} = \mathcal{A}_{\mathrm{auth}} \cup \mathcal{A}_{\mathrm{viol}}, \quad \mathcal{A}_{\mathrm{auth}} \cap \mathcal{A}_{\mathrm{viol}} = \emptyset$$

**Authorized types** $\mathcal{A}_{\mathrm{auth}}$: action types that represent normal, governance-authorized operation. Any observed event of an authorized type contributes zero violation weight.

**Violation types** $\mathcal{A}_{\mathrm{viol}}$: action types that represent governance-prohibited or anomalous operation (negative-h events). Any observed event of a violation type contributes its full probability mass to E_formal.

The normative alphabet is declared in the AGTS clearinghouse constants. Vertical Instantiations MAY extend the alphabet but MUST NOT remove members from either subset without a version-identified alphabet revision.

*Source: AGTS-2*

---

### Intent Distribution

The **Intent Distribution** $P_I : \mathcal{A} \to [0,1]$ is the probability distribution over the IEED Intent Alphabet that encodes what the governing authority has declared as the expected (authorized) pattern of system operation. It satisfies $\sum_{a \in \mathcal{A}} P_I(a) = 1$.

The default AGTS Intent Distribution is uniform over $\mathcal{A}_{\mathrm{auth}}$:

$$P_I(a) = \begin{cases} 1 / |\mathcal{A}_{\mathrm{auth}}| & a \in \mathcal{A}_{\mathrm{auth}} \\ 0 & a \in \mathcal{A}_{\mathrm{viol}} \end{cases}$$

Vertical Instantiations MAY declare non-uniform intent distributions to reflect domain-specific authorization policies. Any non-uniform $P_I$ MUST be cryptographically bound to the relevant governance epoch (via hash in the Proof Bundle) to prevent retroactive reinterpretation.

*Source: AGTS-2 (RTR-GOV §1.1)*

---

### Execution Distribution

The **Execution Distribution** $P_E : \mathcal{A} \to [0,1]$ is the empirical frequency distribution over the IEED Intent Alphabet derived from observed system events within a governance epoch. For a window of $n$ observed events with counts $c_a$:

$$P_E(a) = c_a / n \quad \text{for each } a \in \mathcal{A}$$

It satisfies $\sum_{a \in \mathcal{A}} P_E(a) = 1$.

The Execution Distribution is the IEED analogue of RTR's current system state $\rho(t)$: the observed distribution to be compared against the reference baseline. It is constructed from the AGTS event stream within the current measurement window.

*Source: AGTS-2*

---

### H_formal

**H_formal** is the entropy stability observable. It measures whether the execution entropy has increased relative to the declared intent entropy. Only entropy *increases* from intent are penalized; execution that is more concentrated than intent is not penalized.

$$\Delta H = H_{\mathrm{raw}}(P_E) - H_{\mathrm{raw}}(P_I), \quad H_{\mathrm{raw}}(P) = -\sum_{a \in \mathcal{A}} P(a) \log_2 P(a)$$

$$H_{\mathrm{formal}} = 1 - \min\!\left(1,\ \frac{\max(0,\, \Delta H)}{\log_2 |\mathcal{A}|}\right) \in [0, 1]$$

Key properties:
- If $P_E = P_I$: $\Delta H = 0 \Rightarrow H_{\mathrm{formal}} = 1$ (no entropy change; maximum health).
- If execution is *more* concentrated than intent ($\Delta H < 0$): $H_{\mathrm{formal}} = 1$ (not penalized).
- If execution is *more* uncertain than intent ($\Delta H > 0$): $H_{\mathrm{formal}}$ decreases below 1, proportionally to the entropy increase.

Gate threshold: $H_{\mathrm{formal}} \geq 0.40$.

*Source: AGTS-2 (RTR-GOV §1.1)*

---

### C_formal

**C_formal** is the coherence alignment observable. It measures how closely the execution distribution matches the declared intent distribution using the Bhattacharyya coefficient — the classical reduction of quantum fidelity for diagonal (classical) distributions.

$$C_{\mathrm{formal}} = \mathrm{BC}(P_E, P_I) = \sum_{a \in \mathcal{A}} \sqrt{P_E(a) \cdot P_I(a)} \in [0, 1]$$

Key properties:
- $P_E = P_I \Rightarrow C_{\mathrm{formal}} = 1$ (perfect alignment; zero Bures distance).
- $P_E \cap P_I = \emptyset \Rightarrow C_{\mathrm{formal}} = 0$ (disjoint distributions; maximum Bures distance).
- A system executing only violation types has $C_{\mathrm{formal}} = 0$ regardless of how concentrated that execution is.

Gate threshold: $C_{\mathrm{formal}} \geq 0.40$.

*Source: AGTS-2 (RTR-GOV §1.2)*

---

### C_purity

**C_purity** is the execution purity observable. It is the classical analogue of $\mathrm{Tr}(\rho^2)/\mathrm{Tr}(\rho)^2$:

$$C_{\mathrm{purity}} = \sum_{a \in \mathcal{A}} P_E(a)^2 \in [1/|\mathcal{A}|,\ 1]$$

C_purity measures how concentrated the execution distribution is, independently of whether that concentration falls on authorized or violation types. C_purity is reported as a diagnostic alongside C_formal but is **not** used as the gate metric.

*Source: AGTS-2*

---

### E_formal

**E_formal** is the energy (violation) observable. It measures the fraction of observed execution events that belong to the violation type set $\mathcal{A}_{\mathrm{viol}}$:

$$E_{\mathrm{formal}} = \sum_{a \in \mathcal{A}_{\mathrm{viol}}} P_E(a) \in [0, 1]$$

Key properties:
- $E_{\mathrm{formal}} = 0$: all observed events are authorized.
- $E_{\mathrm{formal}} = 1$: all observed events are violations.
- E_formal is independent of the shape of $P_I$. It is purely a property of how much of the observed probability mass falls on violation types.

Gate threshold: $E_{\mathrm{formal}} \leq 0.60$.

*Source: AGTS-2*

---

### IEED Gate

The **IEED Gate** is the three-condition boolean predicate applied to the IEED observables. It is the AGTS operational analogue of RTR Invariant I1 (Commitment Safety):

$$\mathrm{IEED\_GATE} = (H_{\mathrm{formal}} \geq H_{\mathrm{MIN}}) \wedge (C_{\mathrm{formal}} \geq C_{\mathrm{MIN}}) \wedge (E_{\mathrm{formal}} \leq E_{\mathrm{MAX}})$$

| Observable | Direction | Threshold | Meaning |
|---|---|---|---|
| H_formal | $\geq H_{\mathrm{MIN}} = 0.40$ | Entropy stability | Execution entropy has not increased excessively from intent |
| C_formal | $\geq C_{\mathrm{MIN}} = 0.40$ | Coherence alignment | Execution distribution remains aligned with intent |
| E_formal | $\leq E_{\mathrm{MAX}} = 0.60$ | Energy bound | Violation-type events remain below the acceptable fraction |

*Source: AGTS-2*

---

## 5. Envelope Layer Terms

---

### Governance Envelope

A **Governance Envelope** is the canonical transparency artifact submitted to the Transparency Log. It wraps a single Proof Bundle with metadata required for independent verification:

```json
{
    "type":                "AGTS_GOVERNANCE_ENVELOPE_V1",
    "version":             "AGTS-1",
    "artifact_type":       "AGTS_PROOF_BUNDLE_V1",
    "artifact_hash":       "<SHA256(PB_t)>",
    "payload_uri":         "<durable URI for retrieving PB_t>",
    "validator_signatures": [ ... ],
    "authority_signature":  "<Sovereign Authority signature>",
    "log_binding":         { "log_id": "<SHA256(DER SPKI)>", "log_url": "..." }
}
```

*Source: AGTS-3*

---

### Canonical Leaf

A **Canonical Leaf** is the fundamental unit of transparency in the AGTS log. Each leaf corresponds to exactly one governance decision and is derived deterministically from the Governance Envelope:

```
Leaf Hash = SHA256("AGTS_LEAF_V1" || canonical_json(Governance_Envelope))
```

The prefix `"AGTS_LEAF_V1"` provides domain separation between leaf nodes and internal Merkle tree nodes.

*Source: AGTS-3, AGTS-4*

---

### Sovereign Authority

The **Sovereign Authority** is the entity that holds the final signing key for Governance Envelopes. It represents the institutional authority that bears ultimate accountability for governance decisions. The Sovereign Authority key SHOULD be hardware-backed (HSM, TEE, or secure element with biometric gate).

The Sovereign Authority is NOT a validator. It does not evaluate policy. It provides the institutional authority signature after the Policy Validator quorum has approved the Proof Bundle.

*Source: AGTS-3*

---

### Policy Validator

A **Policy Validator** is an independent node that evaluates Proof Bundles against declared policy rules and produces signed approval or rejection votes. Policy Validators form a BFT quorum network.

*Source: AGTS-3, AGTS-5*

---

### Designated Human Operator

The **Designated Human Operator** (DHO) is the human role responsible for Gate G5 authorization. The DHO makes the final governance decision to accept or reject a candidate update. The DHO role is protocol-level — it cannot be delegated to an automated system without violating AGTS-2 conformance.

*Source: AGTS-2 (RTR-GOV §5.6)*

---

## 6. Transparency Layer Terms

---

### Transparency Log

A **Transparency Log** is a Merkle tree-based append-only data structure that records Canonical Leaves. It is operated by a Log Operator and provides cryptographic proofs of inclusion and consistency.

*Source: AGTS-4*

---

### Log Identity

The **Log Identity** (`log_id`) is the stable, cryptographic identifier for a Transparency Log:

```
log_id = hex( SHA256( DER SubjectPublicKeyInfo of log operator key ) )
```

All protocol messages reference logs by `log_id`, not by endpoint URL. This prevents misdirection attacks.

*Source: AGTS-4*

---

### Merkle Tree

The **Merkle Tree** used in AGTS Transparency Logs is a complete binary hash tree where:
- Each leaf is SHA256(`"AGTS_LEAF_V1"` || `canonical_json(envelope)`)
- Each internal node is SHA256(`0x01` || `left_child` || `right_child`)
- The root hash is the single hash summarizing all admitted leaves

*Source: AGTS-4*

---

## 7. Checkpoint Terms

---

### Signed Tree Head

A **Signed Tree Head** (STH) is a cryptographically signed checkpoint representing the state of the Transparency Log. It contains:

- `log_id` — the Log Identity
- `tree_size` — number of admitted leaves at this checkpoint
- `root_hash` — Merkle root hash
- `timestamp` — wall-clock time of the checkpoint
- `log_signature` — log operator's signature
- `witness_signatures` — array of witness countersignatures (optional at Level 3, required for Level 4)

For AGTS Level 4 conformance, an STH is valid only if it carries the log operator signature plus a witness quorum of size $Q$.

*Source: AGTS-4*

---

### Inclusion Proof

An **Inclusion Proof** demonstrates that a specific Leaf Hash exists within a Merkle tree at a declared tree size. It contains the minimal set of sibling hashes required to recompute the Merkle root from the Leaf Hash.

*Source: AGTS-4*

---

### Consistency Proof

A **Consistency Proof** demonstrates that a newer Merkle tree state is an append-only extension of an earlier state. It prevents silent history rewriting.

*Source: AGTS-4*

---

### Append-Only Property

The **Append-Only Property** guarantees that new log states extend previous states without modifying prior Leaf Hashes. Violation of the Append-Only Property is detectable via Consistency Proofs and equivocation detection.

*Source: AGTS-4*

---

### Anti-Equivocation Invariant

The **Anti-Equivocation Invariant** states that for any `(log_id, tree_size)` pair, exactly one valid `root_hash` MUST exist. Violation indicates log equivocation.

*Source: AGTS-4*

---

## 8. Verification Layer Terms

---

### Witness

A **Witness** is an independent system that fetches Signed Tree Heads, verifies their consistency, and countersigns checkpoints it considers valid. Witnesses constrain log operator misbehavior by providing external endorsement of log state.

*Source: AGTS-5*

---

### Witness Quorum

A **Witness Quorum** is the minimum number of witness countersignatures required for an STH to be considered valid under a deployment's Verification Policy Bundle. Two quorum modes are defined:

| Mode | Threshold | Use case |
|---|---|---|
| Minimum | $Q \geq 1$ | Small deployments; basic Level 4 compliance |
| Majority | $Q = \lfloor N/2 \rfloor + 1$ | Production networks; protects against minority witness compromise |

*Source: AGTS-5*

---

### Monitor

A **Monitor** is an independent verifier that continuously audits one or more Transparency Logs. Monitors check inclusion proofs, consistency proofs, STH evolution, and equivocation.

*Source: AGTS-6*

---

### Equivocation

**Equivocation** occurs when a log operator presents different log histories to different observers — specifically, when two STHs with the same `(log_id, tree_size)` pair have different `root_hash` values.

*Source: AGTS-6*

---

### Equivocation Proof

An **Equivocation Proof** is a cryptographic artifact that demonstrates a log operator has produced conflicting log states. It consists of two conflicting STHs (both bearing valid log operator signatures) for the same tree size. Any party holding a valid Equivocation Proof has conclusive, publicly verifiable evidence of log misbehavior.

*Source: AGTS-6*

---

### Cross-Log Commitment

A **Cross-Log Commitment** is a record in one Transparency Log that encodes a checkpoint of a second Transparency Log. Cross-log commitments create a network of mutually reinforcing logs, reducing single-operator trust.

*Source: AGTS-7*

---

## 9. Trust Policy Layer Terms

---

### Verification Policy Bundle

A **Verification Policy Bundle** is a structured artifact that defines the trust requirements a client applies when verifying governance transparency records. It specifies:

- trusted log set (identified by `log_id`)
- required witness quorum rule
- cross-log commitment requirements
- monitor validation thresholds
- version and distribution metadata

Clients MUST evaluate transparency proofs using a Verification Policy Bundle.

*Source: AGTS-8*

---

## 10. Conformance Terms

---

### AGTS Conformance Level

| Level | Name | Description |
|---|---|---|
| 1 | Verified Measurement | RTR-CAP fully implemented; $\mathrm{CC}_t$ produced; M1–M7 tests pass |
| 2 | Governed Updates | RTR-GOV five-gate predicate; $\mathrm{PB}_t$ chain; deterministic replay |
| 3 | Transparent Governance | Level 2 + Transparency Log; inclusion/consistency proofs |
| 4 | Networked Transparent Governance | Level 3 + witness quorum; monitor network; cross-log witnessing |

*Source: AGTS-9*

---

### Vertical Instantiation

A **Vertical Instantiation** is a domain-specific parameterization of the AGTS governance protocol for a particular deployment domain (e.g., cybersecurity, clinical medicine, financial risk, autonomous vehicles). A Vertical Instantiation declares domain-specific task distributions, metrics, benchmark generators, and artifact types while inheriting all invariant protocol mechanisms.

*Source: AGTS-12*

---

## 11. System Roles Summary

| Role | Layer | Description |
|---|---|---|
| Learning Operator | Governance | Proposes candidate updates |
| Designated Human Operator | Governance | Authorizes G5; makes policy decision |
| Policy Validator | Governance + Envelope | Evaluates policy rules; produces approval signatures |
| Lifecycle Controller | Governance | Manages artifact state; issues Proof Bundles |
| Sovereign Authority | Envelope | Signs Governance Envelopes; holds hardware-backed keys |
| Log Operator | Transparency | Maintains Transparency Log; generates STHs |
| Witness | Verification | Countersigns STHs; constrains log misbehavior |
| Monitor | Verification | Audits log; detects equivocation; produces Equivocation Proofs |
| Client | Trust Policy | Verifies proofs using Verification Policy Bundle |
| Federation Layer | Governance | Distributes artifacts across federated nodes |

---

## 12. Artifact Flow Summary

```
Task Probability Space (declared)
       |
       v
RTR-CAP evaluation
       | produces
       v
Capability Certificate (CC_t)
       | consumed by
       v
RTR-GOV five-gate validation
       | produces on acceptance
       v
Proof Bundle (PB_t)
[stored off-chain at payload_uri]
       | wrapped into
       v
Governance Envelope
       | hashed into
       v
Canonical Leaf  =  SHA256("AGTS_LEAF_V1" || canonical_json(Envelope))
       | admitted to
       v
Transparency Log (Merkle tree, identified by log_id)
       | produces
       v
Signed Tree Head (log_id, tree_size, root_hash, timestamp, signatures)
       | verified and countersigned by
       v
Witness Quorum
       | audited by
       v
Monitor Network
       | cross-anchored via
       v
Cross-Log Commitments
       | evaluated by clients using
       v
Verification Policy Bundle
```

---

## 13. Normative Language Reference

| Keyword | Meaning |
|---|---|
| MUST / SHALL / REQUIRED | Absolute requirement. Deviation is non-conformance. |
| MUST NOT / SHALL NOT | Absolute prohibition. |
| SHOULD / RECOMMENDED | Deviation is permitted but must be documented and justified. |
| MAY / OPTIONAL | Truly optional; no conformance implication either way. |

Per RFC 2119.

---

## 14. Document Precedence

In case of conflict between term definitions:

1. This document (AGTS-TERMS) is authoritative.
2. If a term is not defined here, the definition in the relevant normative AGTS document (AGTS-1 through AGTS-9) governs.
3. Definitions in RTR source documents or OSCP source documents are superseded by AGTS definitions for any AGTS-conforming implementation.

---

*End of AGTS-TERMS v0.1-Draft*
