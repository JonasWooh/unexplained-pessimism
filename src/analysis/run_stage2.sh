#!/bin/sh
# Stage 2 (measurement validation and benchmarks). Extra needs: scikit-learn, vaderSentiment 3.3.2.
# Data: corpus/items.parquet, labels/*, annotation/gold_standard_v1.csv, data/raw/LEX, M18/M19, features/media_monthly.csv.
set -e
cd "$(dirname "$0")"
python3 stage2_r35.py
python3 stage2_dictindex.py
python3 stage2_factcal.py
python3 stage2_r37.py
python3 stage2_bias.py
python3 stage2_reliability.py
python3 spec_registry.py
