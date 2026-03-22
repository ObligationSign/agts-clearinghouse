# PROTOCOL_DIAGRAMS.md

## AGTS Protocol Architecture Diagrams

**Version:** 0.1-Draft  
**Date:** March 2026  
**Status:** INFORMATIVE  
**Audience:** Engineers, regulators, auditors, enterprise architects, policy reviewers

This document contains the canonical architecture diagrams for the Autonomous Governance Transparency Standard (AGTS). These diagrams are informative. All normative requirements are in AGTS-1 through AGTS-9.

Seven diagrams are provided, each addressing a different reader perspective:

| Diagram | Purpose | Primary Audience |
|---|---|---|
| 1. Architecture Stack | Protocol layer structure and artifact flow | Engineers, implementors |
| 2. Threat Containment Model | Security properties and failure isolation | Security reviewers, regulators |
| 3. Machine Economy Ledger | AGTS as accounting infrastructure | Enterprise architects, economists |
| 4. The Great Inversion | Governance authority vs. compute scale | Policy makers, executives |
| 5. Minimal Deployment Architecture | Infrastructure footprint and component boundaries | Engineers, DevOps, enterprise architects |
| 6. Multi-Log Transparency Mesh | Cross-institution log federation and global accountability | Regulators, standards bodies, enterprise architects |
| 7. Triple-Leaf Ledger — Closed-Loop Accountability | Execution witness, variance reconciliation, HCE feedback | Auditors, compliance engineers, regulators |

---

# Diagram 1 — AGTS Architecture Stack

**Governance Decision → Transparency Record → Independent Verification**

This is the primary technical diagram. It shows every protocol layer, the key artifacts at each layer, and the transformation chain from a candidate autonomous system update to an independently verified governance record.

```
                     AGTS ARCHITECTURE STACK
      Governance Decision → Transparency Record → Independent Verification


┌───────────────────────────────────────────────────────────────────────┐
│                         TRUST POLICY LAYER                            │
│                            (AGTS-8)                                   │
│                                                                       │
│  Verification Policy Bundle                                           │
│  - trusted log set (log_id = SHA256(DER SubjectPublicKeyInfo))        │
│  - witness quorum rule  (Q ≥ 1  or  Q = ⌊N/2⌋ + 1)                  │
│  - monitor validation requirements                                    │
│  - cross-log commitment policy                                        │
│                                                                       │
│  Clients evaluate governance records under declared trust policy      │
└───────────────────────────────────────────────────────────────────────┘
                                  ▲
                                  │ evaluated by
┌───────────────────────────────────────────────────────────────────────┐
│                         VERIFICATION LAYER                            │
│                         (AGTS-5, AGTS-6, AGTS-7)                     │
│                                                                       │
│  Monitor Network                               (AGTS-6)               │
│      │                                                                │
│      ├── Inclusion verification                                       │
│      ├── Consistency verification                                     │
│      ├── Equivocation detection                                       │
│      └── Cross-log comparison                                         │
│                                                                       │
│  Witness Network                               (AGTS-5)               │
│      │                                                                │
│      ├── fetch Signed Tree Heads                                      │
│      ├── verify append-only evolution                                 │
│      └── countersign checkpoints (quorum Q)                           │
│                                                                       │
│  Cross-Log Anchoring                           (AGTS-7)               │
│      └── logs record each other's checkpoints                         │
│                                                                       │
│  Outputs:                                                             │
│      Equivocation Proofs  ·  Verified checkpoints                     │
└───────────────────────────────────────────────────────────────────────┘
                                  ▲
                                  │ STH
┌───────────────────────────────────────────────────────────────────────┐
│                         TRANSPARENCY LAYER                            │
│                            (AGTS-4)                                   │
│                                                                       │
│                     Transparency Log (Merkle Tree)                    │
│                                                                       │
│    Leaf Hash = SHA256("AGTS_LEAF_V1" || canonical_json(Envelope))     │
│                                                                       │
│    Log provides:                                                      │
│        inclusion proofs  ·  consistency proofs  ·  STH checkpoints    │
│                                                                       │
│    Signed Tree Head (STH)                                             │
│        log_id      = SHA256(DER SubjectPublicKeyInfo)                 │
│        tree_size   = number of admitted leaves                        │
│        root_hash   = Merkle root                                      │
│        timestamp                                                      │
│        log_signature                                                  │
│        witness_signatures  (Q required for Level 4)                  │
└───────────────────────────────────────────────────────────────────────┘
                                  ▲
                                  │ leaf_hash
┌───────────────────────────────────────────────────────────────────────┐
│                           ENVELOPE LAYER                              │
│                            (AGTS-3)                                   │
│                                                                       │
│                    Governance Envelope (AGTS-1 format)                │
│                                                                       │
│    {                                                                  │
│        version          : "AGTS-1"                                   │
│        artifact_type    : "RTR_PROOF_BUNDLE"                          │
│        artifact_hash    : SHA256(PB_t)                                │
│        payload_uri      : → durable off-chain reference to PB_t      │
│        validator_signatures : [ policy validator approvals ]          │
│        authority_signature  : Sign(canonical_envelope)               │
│        log_binding.log_id   : SHA256(DER SubjectPublicKeyInfo)        │
│    }                                                                  │
│                                                                       │
│    canonical_json(Envelope) → "AGTS_LEAF_V1" prefix → SHA256         │
│                             → Leaf Hash → admitted to log             │
└───────────────────────────────────────────────────────────────────────┘
                                  ▲
                                  │ PB_t
┌───────────────────────────────────────────────────────────────────────┐
│                          GOVERNANCE LAYER                             │
│                         (AGTS-1, AGTS-2)                              │
│                                                                       │
│                    RTR Capability Measurement (AGTS-1)                │
│                                                                       │
│      Task Probability Space  →  Performance Function                  │
│      Tail-Robust Capability (Cap_β)  →  PAC Estimation Margin (ε)    │
│                                                                       │
│                    Capability Certificate (CC_t)                      │
│                                                                       │
│                    RTR Governance Validation (AGTS-2)                 │
│                                                                       │
│      Five-Gate Validation Predicate                                   │
│          G1  Statistical Confidence     (bootstrap CI lower > 0)      │
│          G2  Causal Attribution         (improvement attributable)    │
│          G3  Regression Safety          (no protected metric degrades)│
│          G4  Evidence Integrity         (HOOKED / ATTESTED / INSTR.)  │
│          G5  Human Authorization        (Designated Human Operator)   │
│                                                                       │
│      If all gates pass  →  Proof Bundle (PB_t)                        │
│          state before/after  ·  gate results  ·  bootstrap CI        │
│          ablation evidence   ·  replay seed   ·  parent_bundle_hash  │
│          capability_certificate_id  ·  signature                      │
│                                                                       │
│      PB_t stored off-chain at payload_uri                             │
│      PB_t becomes the artifact wrapped by the Governance Envelope     │
└───────────────────────────────────────────────────────────────────────┘
```

**Core invariant:**
```
Every accepted governance decision produces exactly one
canonical leaf in an append-only transparency log.

decision → record → immutable history → verifiable truth
```

---

# Diagram 2 — AGTS Threat Containment Model

**Split Authority and Transparency Verification**

This diagram shows the security properties of the architecture: why no single actor can both authorize an action and hide the evidence of that action. Each layer is independently operated, and compromise of any one layer is detectable by the others.

```
                     AGTS THREAT CONTAINMENT MODEL


                 ┌──────────────────────────────────┐
                 │        HUMAN GOVERNANCE          │
                 │                                  │
                 │  Designated Human Operator       │
                 │  Authorizes update (Gate G5)     │
                 │                                  │
                 │  Role: governance decision        │
                 │  If compromised: blocked by       │
                 │  remaining gates G1-G4            │
                 └───────────────┬──────────────────┘
                                 │ authorization signal
                                 ▼


┌──────────────────────────────────────────────────────────────────────┐
│                      GOVERNANCE VALIDATION                           │
│                                (AGTS-2)                              │
│                                                                      │
│                 RTR Five-Gate Validation Predicate                   │
│                                                                      │
│      G1  Statistical Confidence    (bootstrap CI > 0)                │
│      G2  Causal Attribution        (ablation-verified)               │
│      G3  Regression Safety         (protected metrics guarded)       │
│      G4  Evidence Integrity        (harness-produced only)           │
│      G5  Human Authorization       (Designated Human Operator)       │
│                                                                      │
│  If all gates pass → Proof Bundle (PB_t) generated                   │
│                                                                      │
│  If any validator is compromised:                                    │
│      → remaining gates still enforce fail-closed semantics           │
│      → partial approval cannot produce a valid PB_t                  │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ PB_t
                                ▼


┌──────────────────────────────────────────────────────────────────────┐
│                       ENVELOPE AUTHORIZATION                         │
│                                (AGTS-3)                              │
│                                                                      │
│                      Sovereign Authority                             │
│                                                                      │
│          Hardware-backed signing key (HSM / TEE)                     │
│                                                                      │
│          Signs Governance Envelope referencing PB_t                  │
│              authority_signature = Sign(canonical_envelope)          │
│                                                                      │
│  If Sovereign Authority is compromised:                              │
│      → fraudulent envelope can be signed                             │
│      → BUT: monitor verifies leaf inclusion against known PB_t       │
│      → AND: auditors can replay PB_t to detect fabrication           │
│      → attack cannot be hidden                                       │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ Governance Envelope
                                ▼


┌──────────────────────────────────────────────────────────────────────┐
│                         TRANSPARENCY RECORD                          │
│                                (AGTS-4)                              │
│                                                                      │
│                    Transparency Log (Merkle Tree)                    │
│                                                                      │
│     Leaf Hash = SHA256("AGTS_LEAF_V1" || canonical_json(Envelope))   │
│     Leaf admitted to append-only Merkle tree                         │
│                                                                      │
│     Signed Tree Head (STH)                                           │
│         log_id  ·  tree_size  ·  root_hash  ·  timestamp            │
│         log_signature  ·  witness_signatures                         │
│                                                                      │
│  If Log Operator is malicious:                                       │
│      → attempts to remove or rewrite leaves                          │
│      → blocked by: consistency proofs                                │
│      → detected by: monitor gossip                                   │
│      → proven by: Equivocation Proof                                 │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ STH
                                ▼


┌──────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL VERIFICATION                         │
│                         (AGTS-5, AGTS-6, AGTS-7)                    │
│                                                                      │
│                      Witness Network            (AGTS-5)             │
│        • verifies append-only log evolution                          │
│        • countersigns Signed Tree Heads                              │
│        • quorum Q required for Level 4 validity                      │
│                                                                      │
│  If a witness is malicious:                                          │
│      → signs invalid checkpoint                                      │
│      → detected by: other witnesses in quorum                        │
│      → detected by: monitor validation                               │
│                                                                      │
│                      Monitor Network            (AGTS-6)             │
│        • checks inclusion proofs                                     │
│        • checks consistency proofs                                   │
│        • exchanges checkpoints via gossip (by log_id)                │
│        • detects equivocation                                        │
│        • produces: Equivocation Proof                                │
│                                                                      │
│  No single actor controls both authorization and history recording.  │
└──────────────────────────────────────────────────────────────────────┘
```

**Failure containment summary:**

| Compromised actor | Attack attempt | Detection mechanism |
|---|---|---|
| Single validator | Approves malicious update | Remaining gates; fail-closed rule |
| Sovereign Authority | Signs fraudulent envelope | Monitor verifies inclusion; auditor replays PB_t |
| Log Operator | Rewrites or removes leaves | Consistency proofs; monitor gossip; Equivocation Proof |
| Witness | Signs invalid checkpoint | Other quorum witnesses; monitor validation |
| Human Operator | Authorizes without evidence | Gates G1–G4 independently enforce evidence requirements |

**Core security invariant:**
```
No single actor can both authorize an action
and hide the evidence of that action.

authorization requires governance
history requires transparency
truth requires independent verification
```

---

# Diagram 3 — Machine Economy Ledger Model

**From Authorized Machine Action → Economic Record**

This diagram shows how the AGTS transparency log functions as an accounting infrastructure for autonomous systems. Once every accepted governance decision produces a canonical leaf, the log becomes a tamper-evident history of authorized machine actions that billing, settlement, and reputation systems can read directly.

```
                  MACHINE ECONOMY SETTLEMENT RAIL


           Autonomous System  /  AI Agent  /  Robot
                         │
                         │ proposes action
                         ▼


┌─────────────────────────────────────────────────────────────┐
│                     GOVERNANCE LAYER                        │
│                     (AGTS-1, AGTS-2)                        │
│                                                             │
│                RTR Capability + Validation                  │
│                                                             │
│  Task evaluation                 G1 Statistical Confidence  │
│  Capability Certificate (CC_t)   G2 Causal Attribution      │
│  PAC margin (ε)                  G3 Regression Safety       │
│  Tail-Robust Capability (Cap_β)  G4 Evidence Integrity      │
│                                  G5 Human Authorization     │
│                                                             │
│             Result → Proof Bundle (PB_t)                    │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ governance artifact
                         ▼


┌─────────────────────────────────────────────────────────────┐
│                      ENVELOPE LAYER                         │
│                         (AGTS-3)                            │
│                                                             │
│                   Governance Envelope                       │
│                                                             │
│   artifact_hash  = SHA256(PB_t)                             │
│   payload_uri    → durable off-chain reference to PB_t      │
│   validator_signatures                                      │
│   authority_signature                                       │
│   log_binding.log_id                                        │
│                                                             │
│   canonical_json(Envelope)                                  │
│       → "AGTS_LEAF_V1" prefix                               │
│       → SHA256                                              │
│       → Canonical Leaf  (one per authorized action)         │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼


┌─────────────────────────────────────────────────────────────┐
│                    TRANSPARENCY LEDGER                      │
│                         (AGTS-4)                            │
│                                                             │
│                    AGTS Transparency Log                    │
│                                                             │
│               append-only Merkle tree                       │
│                                                             │
│    ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐       ┌─────┐       │
│    │ L_1 │  │ L_2 │  │ L_3 │  │ L_4 │  ...  │ L_n │       │
│    └─────┘  └─────┘  └─────┘  └─────┘       └─────┘       │
│                                                             │
│          each leaf = one authorized machine action          │
│                                                             │
│               Signed Tree Head checkpoints                  │
│    root_hash = cryptographic commitment to entire history   │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼


┌─────────────────────────────────────────────────────────────┐
│                     ECONOMIC LAYER                          │
│                 (reads from Transparency Log)               │
│                                                             │
│              Machine Transaction Interpretation             │
│                                                             │
│     Canonical Leaf → Settlement Event                       │
│                                                             │
│     Examples:                                               │
│       AI inference billing       (leaf = inference decision)│
│       Compute usage accounting   (leaf = resource action)   │
│       Autonomous trade decision  (leaf = validated trade)   │
│       Robot task completion      (leaf = verified task)     │
│       Cybersecurity response     (leaf = approved action)   │
│       Model update governance    (leaf = accepted PB_t)     │
│                                                             │
│     Settlement systems read inclusion proofs, not raw logs  │
│     Billing is provable: charge ↔ leaf ↔ PB_t ↔ replay     │
└─────────────────────────────────────────────────────────────┘
```

**The key conceptual shift:**

```
Traditional ledger:     payment → ledger entry
AGTS ledger:   authorized action → ledger entry

Payments become a derivative layer above the action record.
```

**Why this differs from blockchains:**

| Property | Blockchain | AGTS |
|---|---|---|
| Consensus model | Global consensus | Local transparency |
| Cost | High (mining/staking) | Minimal |
| Latency | Slow (blocks) | Near real-time |
| Proof model | Consensus-based | Transparency-based |
| Governance | Protocol-embedded | Externally defined (RTR) |

AGTS does not require global consensus. Each log is independently operated. Trust is established through transparency and independent verification, not through proof-of-work or proof-of-stake.

**One-sentence definition:**
> AGTS converts authorized machine actions into immutable transparency records that serve as the accounting layer of the machine economy.

---

# AGTS as a Distributed Governance Memory

*This section is INFORMATIVE. It describes an architectural property of the AGTS suite, not a normative protocol requirement.*

## What AGTS records

A Governance Envelope — and therefore every canonical leaf — binds together more than a simple event. It binds:

```
authorized machine action
+ governance evidence (Proof Bundle hash + payload_uri)
+ policy context (validator signatures)
+ capability measurement (Capability Certificate reference)
+ deterministic replay anchor (payload_uri → durable off-chain PB_t)
```

Formally, the canonical leaf is:

```
leaf_hash = SHA256("AGTS_LEAF_V1" || canonical_json(governance_envelope))
```

And the envelope contains:

```
artifact_hash      = SHA256(PB_t)
payload_uri        → durable off-chain reference enabling deterministic replay
validator_signatures
authority_signature
log_binding.log_id = SHA256(DER SubjectPublicKeyInfo)
```

Every leaf therefore contains all information necessary to reconstruct the decision context: the governance decision itself, the evidence that justified it, the policy rules that evaluated it, and the capability measurement that preceded it.

## Why this constitutes institutional memory

Traditional governance audit systems store records in:

```
databases         mutable, non-verifiable, operator-controlled
system logs       mutable, operator-controlled, non-auditable
training logs     mutable, opaque to external observers
```

AGTS changes all three properties simultaneously. The transparency log provides:

```
append-only history          — leaves cannot be removed or modified
verifiable inclusion         — inclusion proofs are cryptographically binding
replayable decisions         — payload_uri enables deterministic reconstruction
cross-institution visibility — any monitor can verify any log
```

This transforms governance history from an operator-controlled record into a transparency-backed institutional memory that no single operator can rewrite.

## Three AI memory problems AGTS addresses

### Problem 1 — No verifiable model evolution history

AI systems evolve continuously, but traditional deployments cannot prove:
- why a model changed
- who authorized the change
- what evidence justified it

The AGTS Proof Bundle chain provides a verifiable evolution graph: each PB_t references its `parent_bundle_hash`, forming a cryptographic chain from the current model state back to its origin. The transparency log makes this chain independently auditable.

### Problem 2 — No shared institutional memory across organizations

Organizations operating AI systems have no shared audit layer. Each institution maintains its own internal logs, which are inaccessible and unverifiable by external parties.

The AGTS multi-log mesh (Diagram 6) provides a shared transparency infrastructure. Independent monitors can verify governance records across institutions without those institutions sharing raw operational data.

### Problem 3 — Opaque training feedback

Models learn from logs, but those logs are unverifiable. Regulators and auditors cannot distinguish a genuine operational log from one that has been selectively edited.

Because AGTS leaf hashes are cryptographically bound to their Governance Envelopes and inclusion-proven in append-only logs, AGTS logs are verifiable by construction. They can serve as a trusted evidence substrate for governance review.

## The full architectural claim

AGTS standardizes exactly one thing:

```
the memory of authorized machine actions
```

It does not standardize AI models, training procedures, inference systems, or payments. It standardizes only the transparency-backed record that an authorization occurred, was properly evidenced, and was independently verified.

Once that memory exists, many systems can build on top of it:

```
Compliance systems     read AGTS logs to verify regulatory requirements
Settlement systems     read AGTS logs to reconcile billable machine events
Reputation systems     read AGTS logs to score governance track records
Audit systems          read AGTS logs to reconstruct decision histories
Research systems       read AGTS logs as verified governance datasets
```

## The relationship to the Machine Economy Ledger

The Machine Economy Ledger model (Diagram 3) shows AGTS as an accounting infrastructure. That diagram is correct and follows directly from this architectural property.

The reasoning is:

```
governance memory → verifiable event history → accounting substrate

AGTS records authorized actions
↓
Settlement systems interpret authorized actions as economic events
↓
Payment obligations derive from the action record
↓
Disputes are resolved against the append-only log
↓
The log becomes the system of record
```

The settlement layer does not replace the governance layer. It reads from it. This is the critical distinction from blockchain-based payment systems, which record payments. AGTS records authorizations. Payments are a derivative layer above the authorization record.

```
┌───────────────────────────────────┐
│         SETTLEMENT LAYER          │
│  billing · reconciliation · audit │
│                                   │
│  reads from AGTS logs             │
└─────────────────┬─────────────────┘
                  │ reads
                  ▼
┌───────────────────────────────────┐
│         AGTS MEMORY LAYER         │
│  canonical leaves · Proof Bundles │
│  deterministic replay             │
│                                   │
│  authorized actions recorded      │
└───────────────────────────────────┘
```

**The fundamental distinction:**

| System | What it records |
|---|---|
| Blockchain | payments |
| Traditional databases | events |
| System logs | operations |
| AGTS | **authorized actions with verifiable evidence** |

---

# Diagram 4 — The Great Inversion

**Compute Scale vs. Governance Authority**

This diagram shows the structural inversion AGTS creates in the relationship between compute infrastructure and governance authority. In the traditional cloud model, a single provider controls compute, data, models, logs, and billing. AGTS separates execution from authority by placing governance decisions into an independently verifiable transparency log that no compute provider controls.

```
                      THE GREAT INVERSION


        Traditional Cloud Power Model:
        One operator controls the entire stack


        ┌───────────────────────────────────────────┐
        │             Hyperscaler Cloud             │
        │                                           │
        │  Compute                                  │
        │  Data                                     │
        │  Models                                   │
        │  Logs (mutable, operator-controlled)      │
        │  Billing                                  │
        │  Governance decisions                     │
        │                                           │
        │  Single operator authority                │
        │  Unverifiable by external parties         │
        └───────────────────────────────────────────┘


        ─────────────────────────────────────────────


        AGTS Structural Inversion:
        Authority separated from execution


             ┌────────────────────────────────┐
             │        INSTITUTION LAYER       │
             │          (AGTS-1, AGTS-2)      │
             │                                │
             │   Governance Authority         │
             │   Designated Human Oversight   │
             │   Five-Gate Policy Validation  │
             │   Sovereign Signing Keys (HSM) │
             │                                │
             │   RTR Governance Protocol      │
             │   Proof Bundle (PB_t) issued   │
             └───────────────┬────────────────┘
                             │
                             │ Governance Envelope
                             ▼


             ┌────────────────────────────────┐
             │      TRANSPARENCY LAYER        │
             │        (AGTS-3 to AGTS-8)      │
             │                                │
             │     AGTS Transparency Log      │
             │                                │
             │   Canonical Leaves             │
             │   Signed Tree Heads            │
             │   Witness Quorum               │
             │   Monitor Network              │
             │   Cross-Log Anchoring          │
             │                                │
             │   Immutable governance record  │
             │   Verifiable by any party      │
             └───────────────┬────────────────┘
                             │
                             │ verified record
                             ▼


             ┌────────────────────────────────┐
             │        COMPUTE LAYER           │
             │                                │
             │       Hyperscaler Clouds       │
             │                                │
             │   AI Models                    │
             │   Inference                    │
             │   Data Processing              │
             │   GPU Compute                  │
             │                                │
             │   Execution without authority  │
             │   Cannot control governance    │
             │   Cannot hide action history   │
             └────────────────────────────────┘
```

**The inversion property:**

```
Traditional model:
    compute → governance → record
    (all controlled by the provider)

AGTS model:
    governance → record → compute
    (authority separated from execution)
```

**What hyperscalers lose:**

Under AGTS, compute providers no longer control:
- governance decisions about what actions are authorized
- system evolution and update approval
- the audit history of machine actions
- institutional oversight and policy enforcement

They continue to provide: compute, storage, network.

**What institutions gain:**

Institutions independently control:
- policy enforcement (RTR five-gate predicate)
- model evolution (Proof Bundle chain)
- audit trail (Transparency Log)
- regulatory compliance evidence (AGTS Certificate)
- economic accounting (canonical leaf count)

Without needing to operate the compute infrastructure.

**One-sentence definition:**
> AGTS separates compute from authority by placing governance decisions into an independently verifiable transparency log that no compute provider controls.

---

# Diagram 5 — Minimal AGTS Deployment Architecture

**Reference Implementation Footprint**

This diagram answers the question engineers and operators ask first: how much infrastructure does this actually require? The answer is five small services. The governance overhead per event is negligible compared to the compute cost of AI inference — roughly SHA-256, one signature, and a Merkle tree update per governance decision.

```
                   MINIMAL AGTS DEPLOYMENT


              ┌──────────────────────────────┐
              │        CLIENT / AGENT        │
              │                              │
              │  AI system / robot / service │
              │  proposes candidate action   │
              └───────────────┬──────────────┘
                              │
                              ▼


┌──────────────────────────────────────────────────────────────┐
│                 GOVERNANCE EXECUTION DOMAIN                  │
│              (e.g. two Cloudflare Workers)                   │
│                                                              │
│     Validator A                   Validator B                │
│                                                              │
│   • run RTR validation gates (G1–G5)                        │
│   • verify evidence integrity                                │
│   • evaluate policy compliance                               │
│   • produce approval signatures (Ed25519 / ECDSA P-256)     │
│                                                              │
│                policy approval quorum                        │
└──────────────────────────────┬───────────────────────────────┘
                               │ validator_signatures
                               ▼


┌──────────────────────────────────────────────────────────────┐
│                SOVEREIGN AUTHORITY DOMAIN                    │
│          (one hardware-backed device: HSM / TEE)              │
│                                                              │
│               Hardware-backed signing key                    │
│         Example: HSM, TEE, or secure element                  │
│                                                              │
│         authority_signature = Sign(canonical_envelope)       │
│         biometric or operator authorization for G5           │
│                                                              │
│         Governance Envelope produced and signed here         │
└──────────────────────────────┬───────────────────────────────┘
                               │ Governance Envelope
                               ▼


┌──────────────────────────────────────────────────────────────┐
│                    TRANSPARENCY LOG DOMAIN                   │
│              (one log server or microservice)                │
│                                                              │
│              append-only Merkle tree                         │
│                                                              │
│    leaf_hash = SHA256("AGTS_LEAF_V1" ||                      │
│                       canonical_json(envelope))              │
│                                                              │
│    log_id   = SHA256(DER SubjectPublicKeyInfo)               │
│                                                              │
│    produces Signed Tree Heads (STH)                          │
│    serves inclusion proofs + consistency proofs              │
└──────────────────────────────┬───────────────────────────────┘
                               │ STH
                               ▼


┌──────────────────────────────────────────────────────────────┐
│                   VERIFICATION DOMAIN                        │
│              (one to three independent nodes)                │
│                                                              │
│             Witness Node                                     │
│               verifies append-only STH evolution            │
│               countersigns checkpoints (Ed25519 / P-256)     │
│               provides Q ≥ 1 for Level 4 compliance         │
│                                                              │
│             Monitor Node(s)                                  │
│               checks inclusion proofs                        │
│               checks consistency proofs                      │
│               detects equivocation via gossip (by log_id)   │
│               produces Equivocation Proof if needed          │
└──────────────────────────────────────────────────────────────┘
```

**Operational footprint:**

| Component | Minimum qty | Example |
|---|---|---|
| Validators | 2 | Cloudflare Workers, serverless functions |
| Sovereign signer | 1 | HSM, TEE, or secure element |
| Log server | 1 | Worker, microservice, or embedded library |
| Witness nodes | 1–3 | Independent organizations or edge nodes |
| Monitor nodes | 2+ | Auditors, regulators, or automated services |

Total: approximately five small services.

**Compute cost per governance event:**

```
SHA-256 hash      ~10^3 FLOPs
ECDSA signature   ~10^5 FLOPs
Merkle update     ~10^4 FLOPs

Total governance overhead: ~10^5–10^6 FLOPs
AI inference:              ~10^12–10^15 FLOPs

Governance overhead is < 0.001% of inference cost.
```

**Security domain layout:**

```
Cloud domain      → validators (policy evaluation)
Silicon domain    → sovereign signer (cryptographic authority)
Transparency domain → log server (append-only record)
Verification domain → witnesses + monitors (independent check)
```

Domain separation is the security property. No single domain can both authorize and hide.

**One-sentence deployment description:**
> AGTS can be deployed with two validators, one hardware signer, one transparency log, and independent monitors — enabling institutional governance without operating a large distributed system.

---

# Diagram 6 — Multi-Log Transparency Mesh

**Cross-Witnessed Governance Logs**

This diagram shows what happens when multiple AGTS deployments exist and their logs cross-witness each other. A single log can be compromised by its operator. A mesh of mutually cross-witnessing logs cannot be silently rewritten — an attacker would need to simultaneously compromise every log in the mesh, plus the witness network, plus the monitor network.

This is the same architecture used by Certificate Transparency (multiple Google, Apple, and Cloudflare logs), Sigstore, and other production transparency systems. AGTS extends it to machine governance.

```
                    GLOBAL AGTS TRANSPARENCY MESH


    Institution A              Institution B              Institution C
   ─────────────────          ─────────────────          ─────────────────

   Governance Engine          Governance Engine          Governance Engine
        (RTR)                      (RTR)                      (RTR)
           │                          │                          │
           ▼                          ▼                          ▼


  ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
  │   AGTS Log A    │        │   AGTS Log B    │        │   AGTS Log C    │
  │                 │        │                 │        │                 │
  │  Merkle Tree    │        │  Merkle Tree    │        │  Merkle Tree    │
  │  Canonical      │        │  Canonical      │        │  Canonical      │
  │  Leaves         │        │  Leaves         │        │  Leaves         │
  │  STH            │        │  STH            │        │  STH            │
  │  log_id_A       │        │  log_id_B       │        │  log_id_C       │
  └────────┬────────┘        └────────┬────────┘        └────────┬────────┘
           │                          │                          │
           │   ◄── Cross-Log Commitments ──►                     │
           │   A records checkpoint of B                         │
           │   B records checkpoint of C     ◄───────────────────┘
           │   C records checkpoint of A ────────────────────────►
           │
           ▼


  ┌─────────────────────────────────────────────────────────────────────┐
  │                         WITNESS NETWORK                             │
  │                                                                     │
  │  Independent witnesses observe multiple logs (by log_id)           │
  │  Verify consistency before countersigning each STH                 │
  │  Quorum required across the log mesh for Level 4 claims            │
  └─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼


  ┌─────────────────────────────────────────────────────────────────────┐
  │                         MONITOR NETWORK                             │
  │                                                                     │
  │  Monitors fetch checkpoints from all logs (identified by log_id)   │
  │                                                                     │
  │  Verify per log:                                                    │
  │    - inclusion proofs for admitted governance artifacts             │
  │    - consistency proofs between observed checkpoints               │
  │    - cross-log commitment integrity                                 │
  │                                                                     │
  │  Detect across logs:                                                │
  │    - equivocation (conflicting STHs for same log_id + tree_size)   │
  │    - log partition attacks (log visible to some observers only)     │
  │    - missing cross-log commitments (log disappearing from mesh)    │
  │                                                                     │
  │  Output: Equivocation Proof (public, cryptographically verifiable)  │
  └─────────────────────────────────────────────────────────────────────┘
```

**Cross-log commitment concept:**

```
Log A STH checkpoint → recorded as leaf in Log B
Log B STH checkpoint → recorded as leaf in Log C
Log C STH checkpoint → recorded as leaf in Log A

Result: a transparency ring.
Any history rewrite in Log A is detectable in Log B and Log C.
```

**Security effect of the mesh:**

To silently rewrite history in a three-log mesh, an attacker must simultaneously:
```
compromise Log A operator
AND compromise Log B operator
AND compromise Log C operator
AND compromise enough witnesses to forge a quorum
AND prevent monitor gossip from detecting the inconsistency
```

Each additional log in the mesh increases the attack cost multiplicatively.

**What the mesh enables:**

```
Local authority  →  each institution runs its own governance log
Global verification  →  logs cross-witness; monitors verify all

Governance stays local.
Accountability becomes global.
```

**Example mesh participants:**

| Participant | Role |
|---|---|
| Banks and financial institutions | Governance logs for autonomous trading systems |
| AI providers | Governance logs for model update decisions |
| Cloud providers | Transparency infrastructure (log servers, witnesses) |
| Regulators | Monitor nodes with direct inspection access |
| Research labs | Independent monitors and witness operators |
| Cybersecurity vendors | Equivocation detection and proof generation |

**Comparison with other transparency systems:**

| System | Transparency Mesh | Governance Layer |
|---|---|---|
| Certificate Transparency | Yes (multiple CT logs) | Certificate issuance (PKI) |
| Sigstore | Yes (Rekor log) | Software artifact signing |
| Blockchain | No (global consensus instead) | Embedded in protocol |
| AGTS | Yes (multi-log mesh) | RTR autonomous system governance |

AGTS adopts the proven transparency mesh model from CT and Sigstore and applies it to machine governance — a domain where verifiable authorization history is more valuable than global state consensus.

**One-sentence summary:**
> The AGTS transparency mesh allows independent governance logs to cross-verify each other, forming a global accountability network for autonomous systems where no single operator can silently rewrite history.

---

# AGTS as a Coordination Substrate

*This section is INFORMATIVE. It describes an emergent architectural property that arises from combining canonical leaf transparency, cross-log commitments, and monitor gossip. It is not a normative requirement.*

## The emergent property

A single AGTS log guarantees that an authorized action occurred and that its canonical leaf is included in an append-only record. That is a strong guarantee for one institution and one operator.

When multiple logs cross-witness each other (Diagram 6), a second property emerges that is not present in any single log:

> **History becomes entangled across institutions without requiring shared infrastructure.**

The mechanism is this:

```
Log A records a checkpoint of Log B
Log B records a checkpoint of Log C
Log C records a checkpoint of Log A
```

Now the state of Log A is partly embedded in Log B and Log C. Rewriting Log A's history requires simultaneously rewriting Log B and Log C, because they each carry evidence of Log A's prior state. Because monitors observe all logs and gossip their checkpoints, any inconsistency is publicly detectable.

This is the transparency mesh property. It is already how Certificate Transparency works for certificate issuance. AGTS extends it to machine governance.

## Why this produces coordination without consensus

Blockchain achieves coordination through global consensus: all participants must agree on a shared ledger state before any transaction is valid. That is expensive, slow, and forces all participants into a single administrative domain.

AGTS achieves coordination through a different mechanism:

```
Blockchain model:  shared ledger → agreement → action allowed
AGTS model:        local action → canonical leaf → shared transparency → agreement
```

In the AGTS model, each institution maintains its own governance log and its own governance authority. No institution needs permission from any other. But because their logs cross-witness each other, no institution can secretly rewrite its governance history without the others detecting it.

This produces shared accountability without shared infrastructure.

| Property | Blockchain coordination | AGTS coordination |
|---|---|---|
| Mechanism | Global consensus | Transparency mesh |
| Infrastructure | Single shared chain | Many independent logs |
| Governance | Protocol-embedded | Externally defined (RTR) |
| Cost | High (consensus participation) | Minimal (cryptographic operations) |
| Authority model | Flat (all validators equal) | Hierarchical (institutions retain sovereignty) |

## What this enables at institutional scale

Once multiple institutions participate in a transparency mesh, three new capabilities emerge:

**Shared audit without shared data.** A regulator monitoring Log B can verify that Log A's governance decision was anchored in Log B's checkpoint — without accessing Log A's internal systems or raw operational data. The cross-log commitment is the evidence.

**Cross-institution governance requirements.** Institution B can declare in its Verification Policy Bundle:
```
model MUST appear as a canonical leaf in a log from our trusted log set
```
This means a governance decision made in Institution A's log can satisfy Institution B's policy requirements if Institution A's log is in Institution B's trusted set. Governance decisions propagate across institutional boundaries through the log's inclusion proof alone.

**Machine-readable governance for autonomous systems.** An AI agent or robot can evaluate a policy requirement autonomously:
```
verify leaf inclusion in trusted log
verify witness quorum on the containing STH
verify cross-log anchoring
```
This produces machine-readable governance. Autonomous systems do not need to consult a central authority — they verify against the transparency log directly, using the same cryptographic primitives available to any other observer.

## The coordination layer model

```
Local governance:
    Institution A runs its RTR validation engine
    Institution A issues Proof Bundles
    Institution A signs Governance Envelopes
    Institution A's log admits canonical leaves
        ↓
Cross-log anchoring:
    Institution A's log checkpoints appear in Logs B and C
    History becomes mutually entangled
        ↓
Global accountability:
    Monitors verify inclusion and consistency across all logs
    Witnesses countersign checkpoints
    Any history rewrite becomes publicly detectable
        ↓
Emergent coordination:
    Institutions can verify each other's governance records
    Policy requirements can reference other institutions' logs
    Autonomous systems can verify governance without a central authority
```

The protocol standardizes only transparency. Coordination is the emergent property of many institutions making their governance transparent to each other.

---

# The Authorization Primitive

*This section is INFORMATIVE. It explains the canonical leaf design decision that distinguishes AGTS from execution-recording ledger systems and explains why that decision affects infrastructure adoption.*

## Most ledgers record execution

Traditional ledger systems record what happened after the fact:

| System | What the record represents |
|---|---|
| Payment systems | payment executed |
| Blockchain | transaction executed |
| System logs | event occurred |
| Audit databases | state change committed |

These systems record execution. Disputes are resolved after the fact, against the execution record. Governance is handled outside the ledger, in a separate system that the ledger does not know about.

## AGTS records authorization

A canonical leaf in AGTS represents something structurally different:

```
this action is permitted
under this policy
evidenced by this Proof Bundle
authorized by these signers
at this point in the governance chain
```

Formally:

```
leaf_hash = SHA256("AGTS_LEAF_V1" || canonical_json(governance_envelope))
```

The governance envelope binds:

```
artifact_hash      = SHA256(PB_t)       → Proof Bundle commitment
payload_uri        → replay evidence     → deterministic reconstruction
validator_signatures → policy approval   → who evaluated and approved
authority_signature  → institutional authority → who bears final accountability
log_binding.log_id   → log identity     → which log is authoritative
```

The leaf does not record that the action occurred. It records that the action was permitted. Execution is a separate event that happens downstream, and may or may not be recorded in other systems. The AGTS log is the governance record, not the execution record.

## Why this distinction changes the adoption pattern

Execution records are domain-specific. A payment ledger records payments. A logistics ledger records shipments. A robot control log records movements. Each domain needs its own record format and its own ledger infrastructure.

Authorization records are domain-universal. Every system in every domain must answer one question before any action: is this action permitted? That question appears identically in:

```
AI inference authorization
robot control authorization
financial agent authorization
cybersecurity response authorization
model update authorization
billing event authorization
```

The canonical leaf answers that question in a domain-neutral format that any verifier can evaluate using standard cryptographic operations (inclusion proof, signature verification, quorum check). No domain-specific knowledge is required to verify that a leaf is valid.

This is what allows the settlement rail, the compliance engine, the audit system, the reputation system, and the research dataset pipeline to all read the same canonical artifact.

## The infrastructure adoption path

Infrastructure systems reach critical adoption when they introduce a universal primitive that many other systems depend on.

| Infrastructure | Primitive | Dependent systems |
|---|---|---|
| DNS | name → address | all internet services |
| PKI / CT | key → identity + audit | all TLS connections |
| GPS | time → location | navigation, logistics, finance |
| AGTS | action → verifiable authorization | settlement, compliance, audit, coordination |

Because the canonical leaf records authorization rather than execution, and because authorization is a universal requirement across domains, the leaf becomes a general-purpose primitive that many systems can read without modifying the governance protocol itself.

The adoption path follows naturally from this:

```
Phase 1 — Internal governance
    AGTS used to govern model updates within one institution

Phase 2 — Settlement integration
    Billing and settlement systems read canonical leaves
    as authorization evidence for chargeable events

Phase 3 — External audit
    Regulators and auditors run monitor nodes
    and verify governance records independently

Phase 4 — Cross-institution logs
    Multiple institutions each operate AGTS logs
    and reference each other's logs in policy requirements

Phase 5 — Transparency mesh
    Logs cross-witness each other
    Monitor network detects equivocation globally
    AGTS becomes shared governance memory
    for the autonomous systems economy
```

At Phase 5, the log is no longer controlled by any single institution. It is a shared infrastructure layer that many institutions and systems depend on. Removing it would break settlement, audit, and coordination for all participants.

## The single design decision that enables this path

Every property described in this section — coordination substrate, machine-readable governance, cross-institution audit, settlement rail integration — follows from one design decision in the canonical leaf specification:

**The leaf commits to a Governance Envelope, and the Governance Envelope binds a Proof Bundle hash and a durable payload URI.**

This means the leaf is not just a hash of an event. It is a cryptographic commitment to a complete, replayable, independently verifiable authorization decision. Any verifier — internal or external, human or machine, at the time of issuance or years later — can reconstruct the decision context from the payload URI and verify that the leaf in the log corresponds to it.

That verifiability property is what makes the leaf a general primitive rather than a domain-specific record, and it is what gives AGTS a realistic path from governance protocol to accountability infrastructure.

---

# Diagram 7 — Triple-Leaf Ledger: Closed-Loop Accountability Chain

*This section is INFORMATIVE. It shows how the closed-loop extension (L6 Execution Witness, L7 Variance Reconciliation) adds two additional leaf types to the same Merkle tree, closes the authorization-to-execution accountability gap, and feeds variance back into the HCE observables for the next governance cycle.*

## The authorization gap the base protocol leaves open

The base AGTS protocol produces exactly one leaf per governed action — the authorization leaf. This satisfies the RTR Decision Firewall: only states passing the five-gate predicate can produce a commitment. However, after the gate passes and the action is authorized, the base protocol has no mechanism to verify that physical execution matched the declared intent.

Without the closed loop, the log for a governed action looks like this:

```
Leaf 1 (AGTS_GOVERNANCE_ENVELOPE_V1)
    "This action was authorized"
    ↓
[nothing — execution is invisible]
```

| Scenario | Authorization leaf | Execution reality | Detectable without closed loop? |
|----------|-------------------|-------------------|--------------------------------|
| Nominal | Permitted: deploy model v2.1 | Model v2.1 deployed, metrics stable | ✓ (no gap to detect) |
| Silent drift | Permitted: maintain temperature 2–8°C | Temperature drifted to 9°C for 3 minutes | ✗ no execution record exists |
| Governance gap | Permitted: trade within VaR limits | Algorithm exceeded VaR during execution | ✗ authorization exists; violation invisible |

## The three-leaf chain

The closed-loop extension adds two leaf types to the same Merkle tree, using the same leaf hash construction, the same signing primitives, and the same log worker infrastructure:

```
                     TRIPLE-LEAF LEDGER — ONE GOVERNED ACTION

┌──────────────────────────────────────────────────────────────────────────┐
│                     LEAF 1 — AUTHORIZATION                               │
│                    (AGTS_GOVERNANCE_ENVELOPE_V1)                         │
│                                                                          │
│   artifact_hash    = SHA256(PB_t)                                        │
│   validator_sigs   = [ policy validator approvals ]                      │
│   authority_sig    = Sign(canonical_envelope)                            │
│   auth_state       = { H: 0.90, C: 0.85, E: 0.10 }                      │
│                                                                          │
│   Leaf Hash = SHA256("AGTS_LEAF_V1" || canonical_json(envelope))         │
│                                                                          │
│   Meaning: "This action was authorized under these conditions."          │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │ parent_auth_leaf_hash
                                  ▼
          [Action executes in domain]
          [Domain Sensor or clearinghouse captures exec_state]
                                  │
┌──────────────────────────────────────────────────────────────────────────┐
│                     LEAF 2 — EXECUTION                     (Stage L6)   │
│                    (AGTS_EXECUTION_TRACE_V1)                             │
│                                                                          │
│   parent_auth_leaf_hash  = <Leaf 1 hash>                                 │
│   auth_state             = { H: 0.90, C: 0.85, E: 0.10 }                │
│   exec_state             = { H: 0.88, C: 0.83, E: 0.12 }                │
│   execution_metrics_hash = SHA256(canonical_json(domain_metrics))        │
│   outcome                = NOMINAL                                       │
│   outcome_detail         = "L2 distance: 0.030 (threshold: 0.05)"       │
│                                                                          │
│   Leaf Hash = SHA256("AGTS_LEAF_V1" || canonical_json(trace))            │
│                                                                          │
│   Meaning: "This is what actually happened."                             │
│                                                                          │
│   Log worker: verifies parent_auth_leaf_hash exists → admits or rejects  │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │ parent_exec_leaf_hash
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                     LEAF 3 — VARIANCE                      (Stage L7)   │
│                    (AGTS_VARIANCE_RECORD_V1)                             │
│                                                                          │
│   parent_auth_leaf_hash  = <Leaf 1 hash>                                 │
│   parent_exec_leaf_hash  = <Leaf 2 hash>                                 │
│   delta                  = { H: -0.02, C: -0.02, E: +0.02 }             │
│   l2_distance            = 0.035                                         │
│   classification         = NOMINAL                                       │
│   drift_direction        = { H: degraded, C: degraded, E: degraded }    │
│   auth_in_omega          = true                                          │
│   exec_in_omega          = true                                          │
│   omega_breach           = false                                         │
│                                                                          │
│   Leaf Hash = SHA256("AGTS_LEAF_V1" || canonical_json(record))           │
│                                                                          │
│   Meaning: "This is the measured gap between intent and reality."        │
│                                                                          │
│   Log worker: verifies BOTH parents exist → admits or rejects            │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │ classification → nudge
                                  ▼
```

## The HCE feedback loop

The variance classification drives a nudge update to the HCE observables, closing the loop for the next governance cycle:

```
                    HCE FEEDBACK LOOP

Variance Record classification
       │
       ├── NOMINAL   → H +0.015  C +0.015  E −0.010
       │                (execution confirmed governance quality)
       │
       ├── DEVIATED  → H −0.025  C −0.020  E +0.025
       │                (operational tolerance; degrading trend)
       │
       └── BREACHED  → H −0.070  C −0.050  E +0.070
                        (governance gap; significant penalty)
                                │
                                ▼
                    HCE Evidence Engine
                    (addMeasurement → running weighted average)
                                │
                                ▼
                    H / C / E observables updated
                                │
                                ▼
                    Next authorization cycle
                    uses updated observables
                                │
                                ▼
                    QUARANTINE triggered if
                    3 consecutive BREACHED records
```

The feedback is one-directional and forward-only. Variance from cycle N affects observables for cycle N+1. There is no retroactive modification of any admitted leaf. The append-only log enforces this guarantee structurally.

## Omega breach: the critical failure scenario

The most important condition the variance engine detects is the case where execution drove the state outside the Admissible Region despite a valid authorization:

```
auth_in_omega = true    ← system was in Ω when the five gates passed
exec_in_omega = false   ← system exited Ω during execution
omega_breach  = true    ← governance gap: correct authorization, unsafe execution
```

Without the closed loop this breach is invisible. The log contains a valid authorization leaf and nothing else. With the closed loop, the Leaf 3 variance record exposes it in the log, flagged as `omega_breach: true`, without requiring access to the operator's internal systems.

Regulatory monitors, insurance monitors, and counterparty monitors can filter the log for `omega_breach: true` in real time.

## Cross-leaf linkage enforcement

The log worker enforces referential integrity across all three leaf types:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LOG WORKER — ADMISSION RULES                     │
│                                                                     │
│   POST /agts/v1/log/add                                             │
│                                                                     │
│   AGTS_EXECUTION_TRACE_V1:                                          │
│       → look up parent_auth_leaf_hash in log_leaf_by_hash:{hash}   │
│       → not found → HTTP 422  PARENT_AUTH_NOT_FOUND                │
│       → found     → admit Leaf 2                                    │
│                                                                     │
│   AGTS_VARIANCE_RECORD_V1:                                          │
│       → look up parent_auth_leaf_hash  ─┐                          │
│       → look up parent_exec_leaf_hash  ─┤ O(1) KV lookup each      │
│       → either missing → HTTP 422       │ PARENT_LEAF_NOT_FOUND    │
│       → both found    → admit Leaf 3   ─┘                          │
│                                                                     │
│   AGTS_GOVERNANCE_ENVELOPE_V1:                                      │
│       → no cross-leaf check required                                │
│       → admit Leaf 1                                                │
│                                                                     │
│   KV index maintained per leaf:                                     │
│       log_leaf_by_hash:{leaf_hash} → {leaf_index, admitted_at}     │
│       one additional write per leaf; O(1) lookup at admission time  │
└─────────────────────────────────────────────────────────────────────┘
```

## The audit path for a single governed action

An auditor investigating a specific governed action retrieves exactly three leaves from the log:

```
Leaf 1 — Authorization
    → replay the five-gate evidence, validator votes, authority signature
    → verify: was the authorization correctly produced?

Leaf 2 — Execution
    → see the actual execution state {H, C, E} and domain metrics hash
    → request raw metrics from operator; verify SHA256(canonical_json(metrics)) === execution_metrics_hash
    → see the pre-classified outcome

Leaf 3 — Variance
    → see per-observable deltas {ΔH, ΔC, ΔE}
    → see the L2 distance and classification
    → check omega_breach field
    → verify: did execution match authorization?
```

All three leaves are linked by leaf hash references. The chain is self-contained. No external system access is required for the basic audit. Domain metrics can be requested from the operator and verified against the commitment in Leaf 2.

---

# The Complete Diagram Set

Read in sequence, the seven diagrams explain every dimension of AGTS:

```
Diagram 1 — Architecture Stack
    "Here is how the protocol works."

Diagram 2 — Threat Containment
    "Here is why it is secure even if one actor is malicious."

Diagram 3 — Machine Economy Ledger
    "Here is what the audit trail enables economically."

Diagram 4 — The Great Inversion
    "Here is the structural shift it creates in institutional power."

Diagram 5 — Minimal Deployment Architecture
    "Here is how small the infrastructure actually is."

Diagram 6 — Multi-Log Transparency Mesh
    "Here is how it scales to a global accountability network."

Diagram 7 — Triple-Leaf Ledger
    "Here is how the closed loop catches what authorization alone cannot see."
```

---

# One-sentence AGTS definition

> **AGTS is a transparency-backed governance protocol that converts validated machine decisions into append-only cryptographic records, independently verified by a network of witnesses and monitors, enabling cryptographically auditable governance history for autonomous systems.**
