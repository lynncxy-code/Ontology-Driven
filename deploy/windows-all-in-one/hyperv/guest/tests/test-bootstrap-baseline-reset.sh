#!/bin/bash
set -Eeuo pipefail

test_root="$(mktemp -d)"
trap 'rm -rf -- "$test_root"' EXIT

export ONTOTWIN_DATA_ROOT_OVERRIDE="$test_root/data"
export ONTOTWIN_BOOTSTRAP_LIBRARY_ONLY=1
export ONTOTWIN_BOOTSTRAP_TEST_MODE=1
source "$(dirname "$0")/../bootstrap.sh"

fail() {
  printf 'bootstrap baseline reset test failed: %s\n' "$*" >&2
  exit 1
}

use_data_root() {
  DATA_ROOT="$1"
  WORK_ROOT="$DATA_ROOT/bootstrap"
  PAYLOAD_MARKER="$DATA_ROOT/bootstrap-payload.sha256"
  IMAGES_MARKER="$DATA_ROOT/bootstrap-images.sha256"
  BOOTSTRAP_LOG="$DATA_ROOT/bootstrap-last.log"
  BOOTSTRAP_IN_PROGRESS="$DATA_ROOT/bootstrap.in-progress"
  BASELINE_CAPTURE_MARKER="$DATA_ROOT/backend-baseline-captured"
  BASELINE_CAPTURE_IN_PROGRESS="$DATA_ROOT/backend-baseline-capture.in-progress"
  BASELINE_DUPLICATES_PRUNED=false
  mkdir -p "$DATA_ROOT"
}

# RC15.1 recovery is deliberately narrower than generic snapshot discovery.
# The first named directory is partial; the second is the earliest complete
# baseline and therefore the deletion boundary. Earlier partial state must
# never be deleted because it may contain one half of the customer baseline.
use_data_root "$test_root/prune-data"
if canonical_baseline_snapshot >/dev/null; then
  fail "an empty data root unexpectedly reported a baseline snapshot"
fi

baseline_root="$DATA_ROOT/baseline-backups"
earliest_partial="$baseline_root/20260826-115900-30f273786738"
canonical="$baseline_root/20260826-120000-30f273786738"
safe_duplicate="$baseline_root/20260826-120100-30f273786738"
unexpected_duplicate="$baseline_root/20260826-120200-30f273786738"
symlink_duplicate="$baseline_root/20260826-120300-30f273786738"
top_level_symlink_duplicate="$baseline_root/20260826-120400-30f273786738"
foreign_snapshot="$baseline_root/20260826-120500-bbbbbbbbbbbb"
manual_snapshot="$baseline_root/customer-manual-snapshot"
external_target="$test_root/external-target"

mkdir -p \
  "$earliest_partial/docker" \
  "$canonical/docker" "$canonical/release-data" \
  "$safe_duplicate/docker/overlay2/l" "$safe_duplicate/release-data" \
  "$unexpected_duplicate/docker" "$unexpected_duplicate/release-data" \
  "$top_level_symlink_duplicate/release-data" \
  "$foreign_snapshot/docker" "$foreign_snapshot/release-data" \
  "$manual_snapshot" "$DATA_ROOT/backups/normal-user-backup" "$external_target"
touch "$earliest_partial/docker/original-partial-state"
touch "$external_target/must-survive"
ln -s "$external_target" "$safe_duplicate/docker/overlay2/l/external-link"
touch "$unexpected_duplicate/unexpected-top-level"
ln -s "$external_target" "$symlink_duplicate"
ln -s "$external_target" "$top_level_symlink_duplicate/docker"

prune_duplicate_baseline_snapshots
# Re-running the recovery cannot manufacture a new backup or expand deletion.
prune_duplicate_baseline_snapshots

test -f "$earliest_partial/docker/original-partial-state" \
  || fail "the partial snapshot before the canonical baseline was removed"
test -d "$canonical" || fail "the earliest complete RC15.1 baseline was removed"
test ! -e "$safe_duplicate" || fail "the validated RC15.1 duplicate was not reclaimed"
test -f "$external_target/must-survive" \
  || fail "removing a nested Docker symlink followed it outside the snapshot"
test -d "$unexpected_duplicate" \
  || fail "a snapshot with an unexpected top-level item was removed"
test -L "$symlink_duplicate" || fail "a symlink snapshot was removed"
test -L "$top_level_symlink_duplicate/docker" \
  || fail "a snapshot with a top-level symlink was removed"
test -d "$foreign_snapshot" || fail "a foreign payload snapshot was removed"
test -d "$manual_snapshot" || fail "a manually named snapshot was removed"
test -d "$DATA_ROOT/backups/normal-user-backup" || fail "an ordinary backup was removed"
test "$BASELINE_DUPLICATES_PRUNED" = true || fail "successful recovery was not reported"
test "$(canonical_baseline_snapshot)" = "$canonical" \
  || fail "the earliest complete snapshot was not selected as canonical"

mapfile -t rc151_snapshots < <(list_rc151_baseline_snapshots)
printf '%s\n' "${rc151_snapshots[@]}" | grep -qx '20260826-115900-30f273786738' \
  || fail "the exact RC15.1 snapshot pattern was not recognized"
if printf '%s\n' "${rc151_snapshots[@]}" | grep -q 'bbbbbbbbbbbb'; then
  fail "a foreign fingerprint entered the RC15.1 prune set"
fi
is_rc151_payload_fingerprint "$RC151_SHA256SUMS_SHA256" \
  || fail "the delivered RC15.1 payload hash was not recognized"
if is_rc151_payload_fingerprint "${RC151_SHA256SUMS_SHA256:0:12}"; then
  fail "a truncated RC15.1 payload hash authorized recovery"
fi

# Future payload snapshots remain discoverable for normal idempotence but are
# outside the one-off RC15.1 space-recovery deletion set.
use_data_root "$test_root/future-payload-data"
future_snapshot="$DATA_ROOT/baseline-backups/20260827-090000-cccccccccccc"
mkdir -p "$future_snapshot/docker" "$future_snapshot/release-data"
test "$(canonical_baseline_snapshot)" = "$future_snapshot" \
  || fail "a future managed snapshot was not discoverable"
prune_duplicate_baseline_snapshots
test -d "$future_snapshot" || fail "RC15.1 recovery removed a future payload snapshot"

# Simulate a power loss after intent + destination mkdir + the first move. The
# partial directory must not be considered canonical and the still-live second
# component must be moved into the same destination on retry, never discarded.
use_data_root "$test_root/capture-data"
fingerprint="$(printf 'c%.0s' {1..64})"
capture_name="20260827-100000-${fingerprint:0:12}"
capture_path="$DATA_ROOT/baseline-backups/$capture_name"
mkdir -p "$DATA_ROOT/docker" "$DATA_ROOT/release-data" "$capture_path"
touch "$DATA_ROOT/docker/original-docker-state"
touch "$DATA_ROOT/release-data/original-release-state"
write_baseline_capture_intent "$fingerprint" "$capture_name"
mv -- "$DATA_ROOT/docker" "$capture_path/docker"

if canonical_baseline_snapshot >/dev/null; then
  fail "a partial capture was treated as a completed canonical baseline"
fi
test -f "$DATA_ROOT/release-data/original-release-state" \
  || fail "live original state disappeared before capture resume"

resume_baseline_capture
test -f "$capture_path/docker/original-docker-state" \
  || fail "the first original component was not preserved"
test -f "$capture_path/release-data/original-release-state" \
  || fail "the live original component was not preserved on resume"
test -d "$DATA_ROOT/docker" || fail "the disposable Docker directory was not recreated"
test -d "$DATA_ROOT/release-data/project_assets" \
  || fail "the disposable release-data directory was not recreated"
test ! -e "$BASELINE_CAPTURE_IN_PROGRESS" || fail "capture intent was not cleared"
baseline_capture_matches "$fingerprint" || fail "completed capture marker did not match"
test "$(canonical_baseline_snapshot)" = "$capture_path" \
  || fail "the resumed capture was not canonical"
mapfile -t managed_after_resume < <(list_managed_baseline_snapshots)
test "${#managed_after_resume[@]}" -eq 1 \
  || fail "capture resume created more than one managed snapshot"
if baseline_capture_matches "$(printf 'd%.0s' {1..64})"; then
  fail "the baseline marker matched a different payload"
fi

if assert_data_root_child "$test_root/outside"; then
  fail "the data-root path guard accepted an outside path"
fi

echo "bootstrap baseline reset tests: PASS"
