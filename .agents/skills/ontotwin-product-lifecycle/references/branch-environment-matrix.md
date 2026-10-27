# Branch and environment matrix

Use this as the default mapping. A repository may rename branches, but it should preserve the same responsibilities.

| Layer | Default name | Mutable? | Main question it answers |
|---|---|---:|---|
| Feature | `feature/<scope>` | Yes | What single change is being built? |
| Integration | `dev` | Yes | What is currently being developed and tested together? |
| Stabilization | `release/<version>` | Limited | What exact scope is being prepared for release? |
| Release | `main` | Protected | What source is safe to deploy? |
| Mirror | `backup/main` | Mirror only | What is the recoverable copy of `main`? |
| Incident | `hotfix/<issue>` | Temporary | What minimal production repair is being verified? |

## Promotion directions

```text
feature/* -> dev
dev -> release/*
release/* -> main
main -> backup/main
hotfix/* -> main and dev
```

Do not merge `backup/main` into development. Do not develop directly on `main`. Do not treat a release candidate as production until it has a version tag and a recorded acceptance result.

## Environment invariants

- Local, test, UAT, and production use different databases and credentials.
- Test and UAT deploy a known commit, never “whatever is currently in the worktree”.
- Production deploys a tag reachable from `main`.
- Every UI should expose enough version information to identify the running release.
- A database migration is part of the release contract, not an ad hoc server action.
