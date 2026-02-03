# Single stage build for Jenkins with pre-installed plugins
# Use a recent LTS Jenkins version with JDK 21
FROM jenkins/jenkins:lts-jdk25

# Install additional system utilities needed for tests
# Using system level apt-get with explicit cache handling
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        iputils-ping=8:20240905-1 \
        gzip=1.12-1ubuntu1 \
        dumb-init=1.2.5-3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy and setup custom entrypoint script
COPY jenkins-entrypoint.sh /usr/local/bin/jenkins-entrypoint.sh
RUN chmod +x /usr/local/bin/jenkins-entrypoint.sh

# Ensure JENKINS_HOME directory exists with world-writable permissions
# This is critical for mounted volumes from the host that may have different ownership
RUN mkdir -p /var/jenkins_home && \
    chmod 777 /var/jenkins_home

# Note: We do NOT set USER jenkins here because the entrypoint needs to run as root
# to fix mounted volume permissions. The entrypoint will switch to jenkins user.

# Copy plugins.txt
COPY plugins.txt /tmp/plugins.txt

# Install plugins using jenkins-plugin-cli
# This handles plugin dependencies automatically
# Use --latest=false to respect version pins in plugins.txt
RUN jenkins-plugin-cli --plugin-file /tmp/plugins.txt --verbose --latest=false

# Set Jenkins configuration for faster startup and optimal performance
# Skip wizard, disable multicast, skip update center checks, enable parallel startup
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false \
  -Dhudson.DNSMultiCast.disabled=true \
  -Dhudson.model.UpdateCenter.never=true \
  -Djenkins.InitReactorRunner.concurrency=4 \
  -XX:+TieredCompilation \
  -XX:TieredStopAtLevel=4 \
  -XX:+UseG1GC \
  -Xms512m \
  -Xmx1024m"

# Health check to verify Jenkins is ready
# Reduced interval for faster detection of ready state
HEALTHCHECK --interval=5s --timeout=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/api/json || exit 1

# Expose Jenkins port
EXPOSE 8080

# Expose Jenkins agent port
EXPOSE 50000

# Use dumb-init as the init process (PID 1) to properly handle Jenkins restarts
# dumb-init manages the jenkins-entrypoint.sh process which in turn runs jenkins.sh
# This ensures the container stays running when Jenkins restarts internally
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["/usr/local/bin/jenkins-entrypoint.sh"]
