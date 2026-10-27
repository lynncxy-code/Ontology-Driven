# Release, UAT, hotfix, and rollback gates

## Test-to-UAT gate

Before moving from `dev` to `release/*`, verify:

- the working tree is clean or all remaining changes are explicitly excluded;
- feature and bug batches have clear acceptance criteria;
- backend, frontend, UE, and database contracts agree;
- migrations have run successfully on a disposable database copy;
- authentication, authorization, project/tenant isolation, and destructive routes were tested;
- generated and customer-specific artifacts are not in the platform batch;
- the test environment's commit and configuration are recorded.

## UAT-to-production gate

Before merging to `main` and tagging:

- all acceptance criteria are marked passed by the product owner;
- regression testing covers unaffected core flows;
- the release candidate has a unique version;
- database backup and rollback/recovery steps are ready;
- production secrets and endpoints are separate from test;
- the exact commit intended for production is known;
- the product owner explicitly authorizes the release.

## Production deployment

1. Create or verify the immutable `v<version>` tag on the accepted `main` commit.
2. Record the tag, commit, schema version, migration result, and deployment time.
3. Back up the production database before any schema/data migration.
4. Deploy the tagged code and migration in the documented order.
5. Run health, login, authorization, core read/write, and monitoring checks.
6. Report the outcome and update the backup mirror only after production verification.

## Hotfix

Branch from the currently deployed production tag or `main` commit:

```text
main -> hotfix/<issue>
```

Keep the diff minimal. Reproduce the failure, verify the fix, deploy the tagged hotfix, then merge the same fix back into `dev` so the next release does not reintroduce the incident.

## Rollback

- Code rollback: redeploy the previous known-good tag.
- Data rollback: follow the tested database restore or migration rollback procedure.
- Never force-push or rewrite a released tag.
- If the rollback procedure has not been tested, mark the release blocked rather than improvising on production.
