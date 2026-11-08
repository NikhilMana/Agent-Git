# AgentGit — Evaluation and Benchmark Plan

## 1. Evaluation objective

Determine whether adaptive, versioned memory reduces the context supplied to an agent while preserving useful information and enabling reliable memory history operations.

Do not claim improvements until experiments have been run.

## 2. Baselines

1. **Full history:** Include the complete conversation history in the context.
2. **Naive summary:** Create one rolling summary with no version history.
3. **Simple retrieval:** Store conversation chunks and retrieve top-k chunks.
4. **AgentGit:** Adaptive retain / summarize / discard, versioned snapshots, and retrieval.

Use the same conversation corpus and question set across conditions.

## 3. Dataset design

Create a synthetic, controlled corpus of multi-session project conversations. Include:
- Exact facts: project names, IDs, dates, numeric settings.
- Decisions that later change.
- User preferences and constraints.
- Repeated statements.
- Irrelevant filler.
- Negations and corrections.
- Conflicting facts with timestamps.
- Facts introduced early and queried much later.

Each evaluation question must have a gold answer and source message ID(s).

## 4. Metrics

### Context efficiency
`Token reduction (%) = (1 - AgentGit context tokens / baseline context tokens) × 100`

Record tokenizer/model used. Token counts from different tokenizers are not directly comparable.

### Recall
`Recall = correctly retrieved gold facts / total gold facts`

### Answer correctness
Score answers against a fixed rubric or exact-match gold answers where suitable. Use blind human review for qualitative answers.

### Provenance accuracy
`Provenance accuracy = retrieved claims with correct source references / all retrieved claims`

### Latency
Measure ingestion, classification, snapshot creation, retrieval, restore, and merge separately. Report median and p95 over repeated runs.

### Version integrity
- Snapshot hash verification success.
- Restore equivalence: restored active state equals selected historical state.
- Branch isolation: changes on one branch do not alter another.
- Merge correctness: selected items are present; unselected items are absent; conflicts are flagged.

### Cost
For local inference, report runtime, model, hardware, energy only if measured, and token counts. For cloud models, record actual provider pricing and date. Do not mix estimated and measured costs.

## 5. Experimental procedure

1. Freeze corpus, questions, prompts, model versions, and configuration.
2. Run each baseline and AgentGit on identical inputs.
3. Repeat latency measurements at least five times where feasible.
4. Save raw JSON outputs and run metadata.
5. Calculate metrics with a script.
6. Inspect failure cases, especially lost negations, stale facts, and incorrect merges.
7. Report both strengths and limitations.

## 6. Results table template

| Metric | Full history | Naive summary | Simple retrieval | AgentGit |
|---|---:|---:|---:|---:|
| Context tokens | TBD | TBD | TBD | TBD |
| Gold fact recall | TBD | TBD | TBD | TBD |
| Answer correctness | TBD | TBD | TBD | TBD |
| Provenance accuracy | TBD | TBD | TBD | TBD |
| Median retrieval latency | TBD | TBD | TBD | TBD |
| p95 retrieval latency | TBD | TBD | TBD | TBD |

## 7. Threats to validity

- A small synthetic dataset may not represent real user conversations.
- Token counts depend on tokenizer and prompt formatting.
- LLM output variability can affect classification and summarization.
- Retrieval accuracy does not guarantee downstream answer quality.
- Human grading can introduce subjectivity.
- A local model's performance depends on hardware and quantization.

## 8. Reporting rule

Clearly label each number as `measured`, `estimated`, or `target`. Never place a target in a results table as if it were achieved.
