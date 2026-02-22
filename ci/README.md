Docker-based Jenkins CI Infrastructure

This directory contains Docker configuration for building and running Jenkins
instances for testing the jenkinsapi library.

## Quick Start: Local Development

### Build the Docker image locally

```bash
cd ci/
docker build -t jenkinsapi-jenkins:local .
```

### Run Jenkins with docker-compose

```bash
cd ci/
docker-compose up -d
```

Jenkins will be available at `http://localhost:8080` once it's ready. The
health check will monitor its status.

```bash
# View logs
docker-compose logs -f jenkins

# Stop Jenkins
docker-compose down

# Clean up volumes
docker-compose down -v
```

## Testing with Docker

Run tests using the locally built Docker image:

```bash
# From repository root
JENKINS_DOCKER_IMAGE=jenkinsapi-jenkins:local pytest -sv jenkinsapi_tests/systests/
```

### Environment Variables

- `JENKINS_DOCKER_IMAGE`: Docker image to use (e.g., `jenkinsapi-jenkins:local`)
- `SKIP_DOCKER`: Set to `1` to skip Docker and use the war file instead
- `JENKINS_URL`: Set to use an existing Jenkins instance

## Testing with War File Fallback

To verify the fallback to war file installation still works:

```bash
# From repository root
SKIP_DOCKER=1 pytest -sv jenkinsapi_tests/systests/
```

## Plugin Management

### Automatic Plugin Updates

The project includes automated plugin management via GitHub Actions:

**Update Workflow** (`.github/workflows/update-jenkins-plugins.yml`)

- Runs daily to check for available plugin updates
- Queries Jenkins Update Center for new versions
- Creates pull requests when updates are available
- Updates `ci/plugins.txt` with version-pinned plugins

**Build Workflow** (`.github/workflows/build-jenkins-image.yml`)

- Runs daily at 2 AM UTC
- Builds Docker image with current plugins
- Runs full test suite against the new image (prevents broken releases)
- Only publishes to registry if all tests pass
- Manual trigger available via workflow dispatch

### Plugin Version Management

Plugins are **version-pinned** in `ci/plugins.txt`:

```text
git:5.9.0
junit:1396.v095840ed8491
credentials:1480.v2246fd131e83
```

**Benefits:**

- Reproducible builds
- Predictable plugin behavior
- Can detect breaking changes via test failures
- Easy to rollback to previous versions

**Key flag:** `--latest=false` ensures jenkins-plugin-cli respects pinned versions

### Plugin Optimization

UI-only plugins have been removed to reduce image size:

- `bootstrap5-api` - Bootstrap UI framework
- `echarts-api` - Chart visualization
- `font-awesome-api` - Icon library
- `ionicons-api` - Icon library
- `prism-api` - Code syntax highlighting
- `antisamy-markup-formatter` - HTML sanitization

**Results:**

- Image size reduced by ~11% (removed 6 plugins)
- Faster plugin installation and image builds
- 47 essential plugins remain for testing

### Current Plugins

See `ci/plugins.txt` for the complete list of 47 plugins. Categories include:

- **SCM**: git, git-client, scm-api
- **Credentials**: credentials, ssh-credentials, plain-credentials
- **Build**: junit, matrix-project, envinject
- **Pipeline**: workflow-api, workflow-step-api, script-security
- **Nodes**: ssh-slaves, instance-identity, jdk-tool

### Manual Plugin Updates

Developers can check for and apply plugin updates locally:

```bash
# Check for available updates
make update-plugins
```

This will:

1. Query Jenkins Update Center for latest versions
2. Compare with pinned versions in `ci/plugins.txt`
3. Show available updates
4. Apply updates if any are found
5. Provide next steps (review, test, commit)

**After running make update-plugins:**

```bash
# Review changes
git diff ci/plugins.txt

# Test the new image
make docker-build

# Run tests
make coverage-parallel

# If tests pass, commit and push
git add ci/plugins.txt
git commit -m "chore: update Jenkins plugins"
git push
```

## GitHub Container Registry

The Jenkins image is automatically built and published to GitHub Container
Registry (GHCR) on:

- Daily schedule (2 AM UTC)
- Manual trigger via workflow dispatch
- When ci/Dockerfile or ci/plugins.txt changes

### Using the published image

```bash
# Pull the latest image
docker pull ghcr.io/pycontribs/jenkinsapi-jenkins:latest

# Run tests with published image
JENKINS_DOCKER_IMAGE=ghcr.io/pycontribs/jenkinsapi-jenkins:latest pytest -sv jenkinsapi_tests/systests/

# Or use make targets
make test-parallel
```

### Image Tags

The workflow publishes multiple tags for flexibility:

- `latest` - Latest daily build
- `weekly` - Alias for latest
- `YYYY-MM-DD` - Build date (daily)
- `sha` - Git commit hash

## Files

- **Dockerfile** - Single-stage build with pre-installed plugins and
  version pinning
- **plugins.txt** - Version-pinned list of 47 essential Jenkins plugins
- **docker-compose.yml** - Local development configuration
- **jenkins-entrypoint.sh** - Custom startup script for Jenkins lifecycle management

## Troubleshooting

### Jenkins takes a long time to start

Jenkins initialization may take 30-60 seconds on first run. The health
check is configured with appropriate timeouts. Check logs:

```bash
docker-compose logs jenkins
```

### Port already in use

If port 8080 is already in use, modify the port mapping in docker-compose.yml:

```yaml
ports:
  - "8081:8080"  # Use 8081 instead
```

Then access Jenkins at `http://localhost:8081`

### Image build fails

Ensure you have:

- Docker installed and running
- At least 4GB available disk space
- Network connectivity to download plugins

## Dockerfile Details

### Structure

The Dockerfile:

1. Uses `jenkins/jenkins:lts-jdk21` as base
2. Installs system utilities (iputils-ping, gzip, dumb-init)
3. Copies version-pinned plugins.txt
4. Installs plugins using `jenkins-plugin-cli --latest=false --skip-failed-plugins`
5. Configures Jenkins with disabled wizard and UDP multicast disabled
6. Sets up health checks for readiness verification

### Key Features

- **Pre-installed plugins**: All plugins installed at build time, not runtime
- **Version pinning**: Uses `--latest=false` to respect pinned versions
- **Resilience**: `--skip-failed-plugins` continues if a plugin fails to install
- **Health checks**: HTTP endpoint monitoring for container readiness
- **dumb-init**: Proper signal handling for Jenkins restarts
- **Custom entrypoint**: Handles Jenkins lifecycle management

### Size Optimization

- Removed UI-only plugins (6 plugins removed)
- Final image: ~700-800MB (with all essential plugins)
- Typical build time: 5-10 minutes on first run

## Next Steps

See the main README.rst for:

- Running the full test suite
- How the docker launcher integrates with CI
- Performance comparisons with war file approach
