.PHONY: test lint coverage dist clean docker-build docker-run docker-clean docker-logs test-systests test-docker test-all

clean:
	rm -rf dist/ build/ *.egg-info jenkinsapi_tests/systests/localinstance_files

test:
	uv run pytest -sv jenkinsapi_tests -m "not docker"

lint:
	uv run ruff check jenkinsapi/
	uv run ruff format --check jenkinsapi/

dist:
	uv build

coverage:
	uv run pytest -sv --cov=jenkinsapi --cov-report=term-missing --cov-report=xml jenkinsapi_tests -m "not docker"

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

# Run all tests (unit + system)
test-all:
	uv run pytest jenkinsapi_tests -m "not docker" -n auto -q
	uv run pytest jenkinsapi_tests/systests/ -n $(NUM_WORKERS) -v
