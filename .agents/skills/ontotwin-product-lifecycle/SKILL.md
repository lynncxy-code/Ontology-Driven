---
name: ontotwin-product-lifecycle
description: Manage OntoTwin-style product lifecycle across feature, dev, release, main branches and isolated environments; use for branch strategy, testing, release, rollback, or PM workflows.
---

# OntoTwin Product Lifecycle

Use this skill when a user needs to manage an OntoTwin product from feature development through testing, acceptance, release, production operation, backup, or rollback. It is written for a product manager who may not be a developer and for any AI agent assisting that product manager.

## Core model

Keep these concepts separate:

- A **branch** is a version of source code.
- An **environment** is a running deployment with its own configuration, database, credentials, files, and logs.
- A **release** is an accepted, identifiable source version, normally a protected `main` commit plus an immutable tag.
- A **PR** (Pull Request) is a review request to merge one branch into another. A PR is not a deployment and does not itself mean that production is changed.

Never infer that a branch is safe for production merely because it runs locally. Never connect test and production to the same mutable database.

## Default branch policy

Use this topology unless the user explicitly chooses another one:

```text
feature/*  ->  dev  ->  release/*  ->  main  ->  production
                            |
                       backup/main
```

- `feature/*`: one feature, bug fix, migration, or experiment. Short-lived. Do not use as a permanent integration branch.
- `dev`: the only long-lived development/integration branch. It contains code that is still being tested, not necessarily releasable.
- `release/*`: optional short-lived stabilization branch for a named release. Freeze scope here and perform regression/UAT.
- `main`: protected, production-ready release branch. Only accepted release commits and approved hotfixes enter it.
- `backup/main`: a mirror of `main`, never an independent development line. Preserve any explicitly protected historical tags such as `1.0.0`.
- `hotfix/*`: created from `main` for a production incident; after acceptance, merge the fix into both `main` and `dev`.

Do not create or preserve multiple long-lived branches that represent the same product purpose. Once a feature branch is safely merged and no longer needed, archive or delete it only after checking that its commits are reachable from the target branch.

## Environment policy

Use this source-to-environment mapping:

| Environment | Source | Data | Purpose |
|---|---|---|---|
| Local | `feature/*` or a temporary investigation branch | disposable local data | development and diagnosis |
| Test | current `dev` commit | isolated test database | everyday functional testing |
| Release candidate/UAT | `release/*` | isolated release database copy | regression and product acceptance |
| Production | immutable tag on `main` | production database | real users and real data |
| Backup/recovery | `backup/main` and database backups | recovery copies | disaster recovery, not development |

Each environment must have separate database credentials, storage paths, secrets, and service endpoints. A deployment must record the exact Git commit/tag and the database migration version it uses. Do not deploy from an uncommitted worktree.

## Default workflow

When the user describes a new requirement or change:

1. Translate it into a small feature, bug, or migration batch with an acceptance condition.
2. Inspect the current branch, working tree, remotes, and existing uncommitted changes before creating or moving anything.
3. Create or reuse a short-lived `feature/*` branch. Preserve unrelated user changes; never use `git reset --hard`, broad cleanup, or `git add .` as a shortcut.
4. Implement and verify the batch locally. Keep generated data, customer assets, logs, acceptance records, and process files out of the product commit unless explicitly requested.
5. Create a local checkpoint commit when the batch boundary is clear. A local commit is allowed without a remote upload; pushing requires explicit user authorization.
6. Review the diff and test evidence. Only then propose or create a PR from `feature/*` to `dev`.
7. Deploy the exact `dev` commit to the test environment. The product manager accepts or rejects the behavior there.
8. For a release, cut `release/<version>` from the accepted `dev` state, freeze scope, run regression/UAT, then merge to `main` and create an immutable `v<version>` tag.
9. Deploy production only from that tag. After production verification, fast-forward `backup/main` to the same `main` commit if the user authorizes the remote update.

If acceptance fails, keep the release candidate unchanged, record the failed criterion, and create a focused follow-up feature/bug branch. Do not silently patch production or rewrite a released commit.

## Product-manager interaction mode

Explain actions in product language first:

- what changed;
- which environment contains it;
- which branch/commit is running;
- what the user needs to verify;
- what blocks promotion to the next stage.

The AI should perform read-only inspection proactively. It may create local branches and local checkpoint commits when the user asks to organize work, but it must not push, open/merge a PR, alter a remote branch, or deploy production without explicit authorization for that action.

For each batch, report:

```text
Batch: <name>
Source branch/commit: <value>
Target branch: <value>
Environment: <value>
Included: <files/features>
Excluded: <files/features>
Verification: <commands and results>
Promotion decision: ready / blocked / rejected
Blockers: <specific reason>
```

## Promotion gates

Do not promote code when any of these are true:

- the worktree contains unclassified changes that could be included accidentally;
- the exact commit running in the environment is unknown;
- a schema/data migration has not been tested on a disposable copy and given a rollback plan;
- production and test share credentials, databases, or mutable storage;
- authentication, authorization, tenant/project isolation, or destructive operations are untested;
- a UI change violates the repository's design/accessibility rules;
- only syntax checks passed for a feature that needs integration or acceptance testing;
- generated/customer-specific artifacts are mixed into a platform release;
- the user has not approved the promotion or remote mutation.

For database migrations, require: preflight, backup, migration execution, post-migration checks, rollback/recovery procedure, and evidence that old data remains readable. For production hotfixes, require a reproducible symptom, a minimal diff, a test or reproduction, and a back-merge into `dev`.

## Safe handling of special content

Classify before staging:

- **Product source**: reusable backend, frontend, UE plugin, tests, configuration contracts. Candidate for `dev`.
- **Release infrastructure**: Dockerfiles, release compose files, packaging scripts. Keep in a release/tooling batch unless the user wants them in `dev`.
- **Customer/project-specific**: 0bay, ZHHZ, F11, one-off migration scripts, customer assets, generated mappings/results. Exclude from the platform standard release.
- **Process material**: PRD, acceptance sheets, logs, incident notes, implementation records, temporary reports. Preserve separately; do not mix with product source by default.
- **Repository instructions**: `AGENTS.md`, `CLAUDE.md`, or similar. Treat as policy changes, not product features; commit only when explicitly requested.

When a file is ambiguous, leave it uncommitted and report the ambiguity instead of guessing.

## Failure and recovery rules

- Stop and report when a requested operation would overwrite, delete, force-push, reset, or modify production data without clear authorization.
- If a test mutates a local database, use a clearly named fixture and clean it up; verify that the original test data is restored.
- If a migration guard or permission check is bypassed by a legacy route, mark the batch blocked even if the main path passes.
- Keep released tags immutable. Roll back production by redeploying the previous known-good tag and applying the documented database recovery plan; do not rewrite `main` history.

## References

- Read [references/branch-environment-matrix.md](references/branch-environment-matrix.md) when explaining branch/environment mapping or deciding where a change belongs.
- Read [references/release-gates.md](references/release-gates.md) when preparing a release, UAT, production deployment, hotfix, or rollback.
