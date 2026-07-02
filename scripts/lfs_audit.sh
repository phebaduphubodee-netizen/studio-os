#!/usr/bin/env bash
# Nightly/manual LFS health check (blueprint §11.4): finds big files NOT in LFS.
set -u
echo "== git-lfs installed? =="; git lfs version || { echo "git-lfs missing"; exit 1; }
echo; echo "== tracked patterns =="; git lfs track
echo; echo "== files >5MB in git objects that are NOT LFS pointers =="
git ls-files | while read -r f; do
  [ -f "$f" ] || continue
  sz=$(wc -c < "$f")
  if [ "$sz" -gt 5242880 ]; then
    if ! head -c 100 "$f" | grep -q "git-lfs"; then echo "  WARNING non-LFS large file: $f ($((sz/1048576)) MB)"; fi
  fi
done
echo "audit done"
