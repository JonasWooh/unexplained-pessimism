#!/bin/sh
# Stage 3 (forecast comparison). Needs stage 1 and stage 2 outputs (research_panel.csv, media_dict_monthly.csv, stage1_m1).
set -e
cd "$(dirname "$0")"
python3 stage3_forecast.py
python3 stage3_robustness.py
python3 stage3_figures.py
python3 spec_registry.py
