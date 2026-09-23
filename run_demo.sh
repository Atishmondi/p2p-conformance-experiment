#!/usr/bin/env bash
set -e
python3 src/generate_log.py
python3 src/check_conformance.py data/event-log-r1.csv
python3 src/generate_log_r2.py
python3 src/check_conformance.py data/event-log-r2.csv
if [ -f src/evaluate.py ]; then
  python3 src/evaluate.py
elif [ -f evaluate.py ]; then
  python3 evaluate.py
else
  echo "evaluate.py not present, skipping"
fi
echo "Preview webpage with: python3 -m http.server 8000 --directory webpage"
