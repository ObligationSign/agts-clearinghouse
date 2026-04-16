# Decision Boundaries V1

**Status:** FROZEN

## Overview

Decision Boundaries define how an agent classifies actions before submitting
them to the governance clearinghouse. They represent the **human intent** side
of the proof chain: the operator specifies which actions are safe to auto-execute,
which require review, and which trigger escalation. The agent then applies these
boundaries at runtime to every tool invocation.

This is the **profile-as-gate** mechanism at the operator level: the human's
preferences become enforceable gates in the governance pipeline.

## Schema

### DecisionBoundarySet

```json
{
  "easy":             [ <DecisionBoundary>, ... ],
  "hard":             [ <DecisionBoundary>, ... ],
  "escalation_rules": [ <EscalationRule>, ... ],
  "parsed_at":        "<ISO 8601>",
  "source_sections":  [ "<string>", ... ]
}
```

### DecisionBoundary

```json
{
  "pattern":        "<natural language description>",
  "tools":          [ "<tool_name>", ... ],
  "keywords":       [ "<keyword>", ... ],
  "classification": "auto_execute" | "review_required"
}
```

### EscalationRule

```json
{
  "trigger":          "<natural language description>",
  "contact_email":    "<email>" | null,
  "urgency":          "critical" | "high" | "medium" | "low",
  "message_template": "<string>"
}
```

## Classification Algorithm

Actions are classified in strict priority order:

1. **Escalation rules** — checked first. If any rule's trigger matches,
   classification is `"escalate"`.
2. **Hard boundaries** — checked second. If any hard boundary matches,
   classification is `"review_required"`.
3. **Easy boundaries** — checked third. If any easy boundary matches,
   classification is `"auto_execute"`.
4. **Default** — if no rules match, classification is `"default"`.

### Matching

A boundary matches if either:
- The tool name appears in the boundary's `tools` list, OR
- At least 30% of the boundary's `keywords` appear in the tool name or
  stringified input (rounded up, minimum 1).

An escalation rule matches if at least 40% of its trigger words (after
stop-word removal, minimum 1) appear in the combined tool name and input string.

### Classification Output

```json
{
  "classification":   "auto_execute" | "review_required" | "escalate" | "default",
  "matched_rule":     <boundary or rule or null>,
  "boundary_source":  "easy" | "hard" | "escalation" | "default",
  "confidence":       <number 0..1>
}
```

### Confidence Scoring

```
score = 0.3 (base)
      + 0.4 if tool name is in boundary.tools
      + (matched_keywords / total_keywords) × 0.3
confidence = min(1, score)
```

## Tool Hint Map

Decision boundaries use natural language patterns. The system maps common
keywords to tool names:

| Keyword | Tools |
|---------|-------|
| mail, email, send | `send_sovereign_mail` |
| file, upload | `upload_drive_file` |
| delete | `delete_drive_file`, `delete_file`, `memory_delete` |
| share | `share_drive_file`, `share_file` |
| tunnel, vpn | `create_vpn_tunnel`, `disconnect_vpn_tunnel` |
| governance | `submit_governance`, `confirm_governance`, `governance_audit` |
| security, scan | `run_vulnerability_scan`, `run_pentest`, `check_cve` |
| delegate, sub_agent | `spawn_sub_agent` |

## Integration with Governance

After classification, the result flows into the governance pipeline:

- `auto_execute` → action proceeds, governance envelope recorded post-hoc
- `review_required` → action withheld pending operator approval
- `escalate` → escalation notice sent, action blocked
- `default` → falls through to clearinghouse evaluation
