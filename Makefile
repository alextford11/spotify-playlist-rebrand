isort = isort -w 120
black = black -S -l 120 --target-version py38

.PHONY: install
install:
	pip install -r requirements.txt

.PHONY: format
format:
	isort app/ wsgi.py scheduler.py
	$(black) app/ wsgi.py scheduler.py

.PHONY: lint
lint:
	flake8 app/ wsgi.py scheduler.py
	isort --check-only app/ wsgi.py scheduler.py
	$(black) --check app/ wsgi.py scheduler.py
