#!/usr/bin/env bash
# Resolve and pin GitHub Actions to commit SHAs.
#
# Usage:
#   tools/update-action-pins.sh
#
# This is a stub that documents the resolution process — the script does
# NOT modify workflow files. Run it, copy the SHAs into the workflow
# YAMLs, and verify the lint-pinned-actions job stays green.
#
# Why pin to SHAs:
# * Tags on third-party actions are mutable. A repo owner with write
#   access can move v4 to a malicious commit; pinning to a 40-char SHA
#   removes that supply-chain seam.
# * The CI workflow lint-pinned-actions.yml fails if any `uses:` line
#   in .github/workflows/*.yml is not a 40-char hex SHA, so this stays
#   enforced rather than aspirational.
#
# Resolution process:
# 1. For each action in use, identify the *release tag* you want
#    (typically the latest semver-stable tag).
# 2. Resolve the tag to a commit SHA with:
#      git ls-remote https://github.com/<owner>/<repo> refs/tags/<tag>
# 3. Replace the `uses:` line with:
#      uses: <owner>/<repo>@<40-char-sha> # <tag>
# 4. Commit on a feature branch, let CI run lint-pinned-actions.

set -euo pipefail

ACTIONS=(
  "actions/checkout"
  "actions/setup-python"
  "actions/setup-node"
  "actions/upload-artifact"
  "actions/download-artifact"
)

for repo in "${ACTIONS[@]}"; do
  echo "=== $repo ==="
  git ls-remote --refs --tags "https://github.com/$repo" \
    | awk '{print $1, $2}' \
    | sed 's|refs/tags/||' \
    | sort -k2,2V \
    | tail -5
  echo
done

cat <<'EOF'
Copy the relevant 40-char SHA into the workflow file, e.g.:
  uses: actions/checkout@<sha>  # v4.x.y
EOF
