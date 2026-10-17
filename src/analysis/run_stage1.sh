#!/bin/sh
# Stage 1 (economic baseline). Needs Python with pandas, numpy, scipy, statsmodels, matplotlib, openpyxl.
# Data: data/raw/M01-M19, S01; data/processed/econ_monthly_realtime*.csv and survey_monthly.csv.
set -e
cd "$(dirname "$0")"
python3 panel.py
python3 stage1_m1.py
python3 stage1_h3.py
python3 stage1_h1.py
python3 spec_registry.py
