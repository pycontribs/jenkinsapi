.PHONY: test lint coverage dist clean docker-build docker-run docker-clean docker-logs test-systests test-docker test-all

clean:
	rm -rf dist/ build/ *.egg-info jenkinsapi_tests/systests/localinstance_files

test:
	uv run pytest jenkinsapi_tests -n $(NUM_WORKERS) -v

lint:
	uv run pylint jenkinsapi/*.py
	uv run flake8 jenkinsapi/ --count --select=E9,F63,F7,F82 --ignore F821,W503,W504 --show-source --statistics
	uv run flake8 jenkinsapi/ --count --exit-zero --max-complexity=10 --max-line-length=79 --statistics

dist:
	uv build

coverage:
	uv run pytest jenkinsapi_tests -n $(NUM_WORKERS) -v --cov=jenkinsapi --cov-report=term-missing --cov-report=xml

# Docker image configuration
DOCKER_IMAGE ?= jenkinsapi-systest:latest
DOCKER_PORT ?= 8080
CONTAINER_NAME ?= jenkinsapi-systest

# Build the Docker image
docker-build:
	@echo "Building Docker image $(DOCKER_IMAGE)..."
	docker build -t $(DOCKER_IMAGE) docker/
	@echo "Docker image built successfully"

# Run Jenkins Docker container
docker-run: docker-build
	@echo "Starting Jenkins container on port $(DOCKER_PORT)..."
	docker run \
		--name $(CONTAINER_NAME) \
		-d \
		-p $(DOCKER_PORT):8080 \
		$(DOCKER_IMAGE)
	@echo "Jenkins running at http://localhost:$(DOCKER_PORT)"

# Stop and remove the container
docker-clean:
	docker stop $(CONTAINER_NAME) 2>/dev/null || true
	docker rm $(CONTAINER_NAME) 2>/dev/null || true

# View Jenkins logs
docker-logs:
	docker logs -f $(CONTAINER_NAME)

# Use all available CPUs by default via pytest-xdist auto detection.
# Override with: make test-systests NUM_WORKERS=4
NUM_WORKERS ?= auto

# Run system tests in parallel (uses all CPUs by default)
test-systests:
	uv run pytest jenkinsapi_tests/systests/ -n $(NUM_WORKERS) -v

# Run Docker integration unit tests
test-docker:
	uv run pytest jenkinsapi_tests/unittests/test_docker_jenkins.py -m docker -v

# Run all tests (unit + system) through the main xdist-enabled test target.
test-all:
	$(MAKE) test NUM_WORKERS=$(NUM_WORKERS)
