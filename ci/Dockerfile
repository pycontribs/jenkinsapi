# Single stage build for Jenkins with pre-installed plugins
# Use a recent LTS Jenkins version with JDK 21
FROM jenkins/jenkins:lts-jdk25

# Install additional system utilities needed for tests and healthchecks
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        iputils-ping && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Ensure JENKINS_HOME directory exists with proper permissions for mounted volumes
RUN mkdir -p /var/jenkins_home && chmod 777 /var/jenkins_home

# Copy and setup custom entrypoint wrapper script
COPY jenkins-entrypoint.sh /usr/local/bin/jenkins-entrypoint.sh
RUN chmod +x /usr/local/bin/jenkins-entrypoint.sh

USER jenkins

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
# Use curl instead of wget, 127.0.0.1 explicitly, longer startup time
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=5 \
  CMD curl -f http://127.0.0.1:8080/api/json || exit 1

# Expose Jenkins port
EXPOSE 8080

# Expose Jenkins agent port
EXPOSE 50000

# Use tini as the init process (PID 1) to properly handle signals
# tini is included in the jenkins base image
CMD ["/usr/local/bin/jenkins-entrypoint.sh"]

USER root

ENTRYPOINT ["/bin/tini", "--"]
