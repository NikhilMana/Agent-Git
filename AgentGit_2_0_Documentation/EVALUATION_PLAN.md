# AgentGit 2.0 — Evaluation Plan

## 1. Research question

Can task-aware, provenance-linked AgentGit context reduce unnecessary model input and repository exploration while maintaining or improving coding-task correctness?

## 2. Conditions

A. **Normal baseline:** Agent uses its normal repository exploration and existing context.

B. **Rules-only:** Same host and model, with concise instructions to avoid unnecessary broad scans and use targeted search. No AgentGit context retrieval.

C. **AgentGit:** Same host and model, with rules, MCP task context, codebase index, bounded retrieval and write-back.

Keep model, task, repository state, temperature/settings, tool permissions and time limits consistent where possible.

## 3. Task set

Use 10–20 reproducible tasks if time permits, stratified by:
- Small isolated change.
- API/backend change.
- Cross-file feature.
- Refactor with dependencies.
- Bug fix requiring historical decision.
- Task requiring an exact constraint or previous decision.

Reset repository to the same starting commit for each condition. Randomize run order where feasible.

## 4. Metrics

### Token use
Record actual input tokens from the host/provider when exposed. If unavailable, record AgentGit's estimated context tokens separately. Do not label an estimate as actual model usage.

### Task success
Acceptance tests passed / total acceptance tests.

### Code quality
Human review rubric: correctness, regression risk, maintainability and adherence to requirements.

### Repository exploration
Files opened/read, search calls, broad scans and duplicate reads, where host telemetry permits.

### Efficiency
Wall-clock time and AgentGit retrieval overhead.

### Reliability
Stale-context incidents, missing dependency incidents, incorrect memory retrieval and human correction count.

### Memory quality
Recall, provenance correctness, decision consistency and cross-session continuity.

## 5. Results template

| Metric | Normal baseline | Rules-only | AgentGit |
|---|---:|---:|---:|
| Actual model input tokens | TBD | TBD | TBD |
| Estimated supplied context tokens | TBD | TBD | TBD |
| Acceptance tests passed | TBD | TBD | TBD |
| Files inspected | TBD | TBD | TBD |
| Search/tool calls | TBD | TBD | TBD |
| Task completion time | TBD | TBD | TBD |
| AgentGit retrieval latency | N/A | N/A | TBD |
| Human corrections | TBD | TBD | TBD |
| Stale-context errors | TBD | TBD | TBD |

## 6. Reporting requirements

- Save raw run data, task prompts, repository commit, model/version and configuration.
- Distinguish measured, estimated and target values.
- Report failures and cases where AgentGit increased tokens.
- Do not claim improved accuracy from a small or uncontrolled test.
- Include a task-level breakdown, not only averages.
