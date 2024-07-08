WATCH_COMMAND=poetry run uvicorn --reload --host=::1 test_task.application:app
SERVER_COMMAND=poetry run uvicorn --host=::1 test_task.application:app

.PHONY: tags test

watch:
	${WATCH_COMMAND}

test:
	poetry run pytest -x -n auto --dist loadscope

retest:
	poetry run pytest -lx --ff -n auto

cov:
	poetry run pytest --cov=test_task

server:
	${SERVER_COMMAND}

update:
	poetry update

build:
	poetry build -f wheel

wheels: build
	sh -c "poetry run pip wheel -w dist dist/`poetry version 2>/dev/null | tr ' ' -`-*.whl"

tags:
	uctags -R
