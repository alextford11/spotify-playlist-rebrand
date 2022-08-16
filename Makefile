isort = isort -w 120
black = black -S -l 120 --target-version py38

.PHONY: install
install:
	pip install -r requirements.txt

.PHONY: format
format:
	isort app/ definitions.py manage.py scheduler.py
	$(black) app/ definitions.py manage.py scheduler.py

.PHONY: lint
lint:
	flake8 app/ definitions.py manage.py scheduler.py
	isort --check-only app/ definitions.py manage.py scheduler.py
	$(black) --check app/ definitions.py manage.py scheduler.py
