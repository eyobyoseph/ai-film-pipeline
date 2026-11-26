PYTHON ?= python
.PHONY: film validate edit clean
film:
	$(PYTHON) run_pipeline.py
validate:
	$(PYTHON) validate_storyboard.py
edit:
	$(PYTHON) assemble_final.py
clean:
	rm -rf outputs/temp_final outputs/.pipeline_cache.json
