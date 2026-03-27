.PHONY: run test lint

run:
	streamlit run app.py

test:
	pytest tests/ -v

lint:
	python -m py_compile app.py src/analytics.py src/charts.py
