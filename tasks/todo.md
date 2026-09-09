# Codex-only template conversion

- [x] Audit Claude-specific files and references.
- [x] Replace external Claude workflow dependencies with self-contained Codex policy.
- [x] Remove the `.claude` template and Claude-only documentation.
- [x] Verify that no Claude workflow reference remains and that Codex instructions load.

## Review

- Claude-only files were removed. The environment retained empty `.claude`
  directories after blocking recursive directory removal; empty directories are
  not tracked by Git.
- `rg --files .claude` found no files and a hidden-file scan found no remaining
  Claude references outside this task log.
- `git diff --check` passed.
- A read-only ephemeral Codex session loaded the active issue, task planning,
  CP949, and verification safeguards.
