# Codex project instructions

This is a Codex-only maintenance template for the YSR Delphi 2007 codebase. Read `VISION.md` and `AGENTS.md` before planning or editing. `AGENTS.md` is the authoritative implementation, safety, SQL, and verification policy.

- Treat user requests as authorization for the requested, reversible repository work; do not stop for routine clarification.
- Preserve existing user changes and make only surgical edits in scope.
- Use `apply_patch` for repository edits. Follow the CP949 rules in `AGENTS.md` for `.pas` and `.dfm` files.
- Do not commit, push, deploy, delete material files, run migrations, or change an external issue tracker without an explicit user request.
- For product work, use `.codex/ACTIVE_ISSUE`; template maintenance does not need an active issue.
- For non-trivial work, maintain `tasks/todo.md` and run fresh, proportionate verification before reporting completion.
