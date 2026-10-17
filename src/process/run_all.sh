#!/bin/sh
# Rebuild all processed hand-off files from immutable raw data (no network requests).
# src/annotation/build_sample.py is deliberately not rerun: the annotation sample is frozen (labels/sample_key.csv).
set -e
cd "$(dirname "$0")/../.."
PY=${PY:-/Users/jonasw/anaconda3/bin/python}
$PY src/process/econ_realtime.py
$PY src/process/survey_monthly.py
$PY src/process/build_corpus.py
$PY src/annotation/agreement.py
$PY src/annotation/build_gold.py
$PY src/process/export_labels.py
$PY src/process/media_monthly.py
