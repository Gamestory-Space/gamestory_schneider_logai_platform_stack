# Schneider LogAI Agent Operating Contract

Classification: **GAMESTORY CONFIDENTIAL INTERNAL ENGINEERING MATERIAL**

This file and `.ai/**` exist only on `project-direction`. They must never be merged into an implementation/release branch, copied to Schneider, or included in any client artifact or Git history export.

## Required session start

Before meaningful Schneider LogAI work:

1. Identify the implementation repository, branch, and commit in scope.
2. Synchronize this branch with the relevant current implementation branch without turning `project-direction` into an implementation branch.
3. Read, in order:
   - `.ai/LAST_HANDOFF.md`
   - `.ai/PROJECT_STATE.md`
   - `.ai/DECISIONS.md`
   - `.ai/DISCUSSIONS.md`
   - `.ai/OPEN_QUESTIONS.md`
4. Inspect the actual implementation relevant to the task.
5. Surface any disagreement between documentation and code. Code determines what currently exists; approved decisions determine intended direction.

## Required session completion

After meaningful implementation or architectural discussion:

1. Validate the work.
2. Update factual implementation changes in `PROJECT_STATE.md` only after they exist in code.
3. Update material reasoning in `DISCUSSIONS.md` without copying transcripts.
4. Add decisions to `DECISIONS.md` only when explicitly approved by the CTO. Never promote an agent recommendation to `APPROVED`.
5. Update `OPEN_QUESTIONS.md` for unresolved matters requiring human input.
6. Rewrite `LAST_HANDOFF.md` as the concise current handoff.
7. Commit and push `project-direction`.
8. Report push failures explicitly; local-only changes are not synchronized.

Discussion-only sessions can require direction updates even when no code changes. Cross-repository changes that materially affect the Schneider system must be consolidated here.

## Branch and release rules

- `project-direction` is permanent internal context, never a development or release source.
- Implementation changes belong on the applicable implementation branch/repository.
- Do not merge `project-direction` into `master`, `main`, or any client branch.
- Client delivery must be constructed from the explicit release allow-list and pass final-artifact leakage validation.
- Never transfer the Gamestory repository history to Schneider. Create a sanitised export with client-safe history.
- Do not weaken internal-material, secret, source-code, or IP-protection checks.

## State quality

Keep state concise. Record architecture, implementation facts, decisions, trade-offs, security/deployment/release implications, and unresolved questions. Exclude transcripts, routine commands, temporary debugging, and low-value trivia.
