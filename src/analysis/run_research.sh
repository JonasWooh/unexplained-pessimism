#!/bin/sh
# Full research rebuild, stages 1-5 in order (each stage reads the outputs of the earlier ones).
set -e
cd "$(dirname "$0")"
for s in 1 2 3 4 5; do sh run_stage$s.sh; done
