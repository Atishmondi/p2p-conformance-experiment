.PHONY: data check eval bpic hypo web all

data:
	python3 src/generate_log.py
	python3 src/generate_log_r2.py

check:
	python3 src/check_conformance.py data/event-log-r1.csv
	python3 src/check_conformance.py data/event-log-r2.csv

eval:
	@if [ -f src/evaluate.py ]; then python3 src/evaluate.py; elif [ -f evaluate.py ]; then python3 evaluate.py; else echo "evaluate.py not present, skipping"; fi

web:
	@echo "Run: python3 -m http.server 8000 --directory webpage"

bpic:
	python3 src/analyze_bpic2019.py
	python3 src/compare_lab_field.py

hypo:
	@echo "H1-H8 registry (data/hypotheses.csv): 5 supported / 2 nuanced / 1 open"
	@python3 -c "import csv; rows=list(csv.DictReader(open('data/hypotheses.csv'))); print(f'hypotheses={len(rows)}'); [print(f\"{r['hypo_id']} {r['rule']} {r['track']} lab={r['lab_rate']} field={r['field_rate']} {r['status']}\") for r in rows]"

all: data check eval
