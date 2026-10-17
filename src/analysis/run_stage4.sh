#!/bin/sh
# Stage 4 (time order, recall path, partisan heterogeneity, falsification inputs). Needs stage 1-3 outputs.
set -e
cd "$(dirname "$0")"
python3 stage4_timing.py
python3 spec_registry.py
