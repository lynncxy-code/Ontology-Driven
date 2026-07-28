#!/usr/bin/env bash
set -Eeuo pipefail

seed_file="/release-seed/zhhz.dump"

if [[ ! -s "${seed_file}" ]]; then
  echo "FATAL: PostgreSQL release seed is missing: ${seed_file}" >&2
  exit 1
fi

echo "Restoring OntoTwin ZHHZ PostgreSQL release seed..."
pg_restore \
  --username="${POSTGRES_USER}" \
  --dbname="${POSTGRES_DB}" \
  --no-owner \
  --no-privileges \
  --exit-on-error \
  "${seed_file}"
echo "PostgreSQL ZHHZ seed restored."
