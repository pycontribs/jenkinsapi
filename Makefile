.PHONY: test test-parallel lint coverage coverage-parallel dist clean docker-build docker-publish docker show-workers update-plugins docker-build-test docker-publish-test

DOCKER_IMAGE := ghcr.io/pycontribs/jenkinsapi-jenkins:latest
DOCKER_TEST_IMAGE := ghcr.io/pycontribs/jenkinsapi-test:latest

# Calculate number of pytest workers as 1/3 of available CPUs (minimum 1)
NUM_WORKERS := $(shell python3 -c "import os; print(max(1, os.cpu_count() // 3))")

clean:
	rm -rf jenkinsapi_tests/systests/localinstance_files

test:
	uv run pytest -sv jenkinsapi_tests

test-parallel:
	uv run pytest -sv -n $(NUM_WORKERS) jenkinsapi_tests

lint:
	uv run ruff check jenkinsapi/ --output-format full

dist:
	uv build

coverage:
	uv run pytest -sv --cov=jenkinsapi --cov-report=term-missing --cov-report=xml jenkinsapi_tests

coverage-parallel:
	uv run pytest -sv -n $(NUM_WORKERS) --cov=jenkinsapi --cov-report=term-missing --cov-report=xml jenkinsapi_tests

docker-build:
	docker build -t $(DOCKER_IMAGE) ci/

docker-publish: docker-build
	docker push $(DOCKER_IMAGE)

docker: docker-publish

docker-build-test:
	docker build -t $(DOCKER_TEST_IMAGE) -f ci/Dockerfile.test .

docker-publish-test: docker-build-test
	docker push $(DOCKER_TEST_IMAGE)

show-workers:
	@echo "Pytest will use $(NUM_WORKERS) parallel workers (1/3 of $(shell python3 -c 'import os; print(os.cpu_count())') CPUs)"

update-plugins:
	@python3 scripts/update-jenkins-plugins.py
