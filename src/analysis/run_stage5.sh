#!/bin/sh
# Stage 5 (mechanisms, group gaps, survey-mode comparability, pre-election months, recent sources). Needs stage 1 outputs.
set -e
cd "$(dirname "$0")"
python3 stage5_mechanisms.py
python3 spec_registry.py
