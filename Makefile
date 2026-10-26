PYTHON ?= python3
OUTPUT_DIR ?= output/demo
DATA_DIR ?= $(OUTPUT_DIR)
.PHONY: demo data check eval dashboard test bpic hypo web all

# All normal workflows are isolated from historical data/*.csv artifacts.
demo:
	$(PYTHON) src/demo.py --output-dir "$(OUTPUT_DIR)"

data:
	$(PYTHON) src/generate_log.py --out "$(DATA_DIR)/event-log-r1.csv"
	$(PYTHON) src/generate_log_r2.py --out "$(DATA_DIR)/event-log-r2.csv"

check:
	$(PYTHON) src/check_conformance.py "$(DATA_DIR)/event-log-r1.csv" --output-dir "$(DATA_DIR)"
	$(PYTHON) src/check_conformance.py "$(DATA_DIR)/event-log-r2.csv" --output-dir "$(DATA_DIR)"

eval:
	$(PYTHON) src/evaluate.py --data-dir "$(DATA_DIR)" --out "$(DATA_DIR)/evaluation.json"

dashboard:
	$(PYTHON) src/build_dashboard.py --data-dir "$(DATA_DIR)" --out "$(DATA_DIR)/dashboard.json"

test:
	$(PYTHON) -m unittest discover -s tests

web:
	@echo "Run: python3 -m http.server 8000 --directory webpage"

# Raw-field analysis remains an explicit optional scientific workflow.
bpic:
	$(PYTHON) src/analyze_bpic2019.py --cases-out "$(DATA_DIR)/bpic2019_case_results.csv" --json-out "$(DATA_DIR)/bpic2019_results.json"
	$(PYTHON) src/compare_lab_field.py --data-dir "$(DATA_DIR)" --out "$(DATA_DIR)/comparison.json"

hypo:
	@echo "Historical v1 hypothesis registry: data/hypotheses.csv (not rebuilt by the demo)."

all: demo
