FROM jenkins/jenkins:lts-jdk21

USER root

# Install plugins required for systests
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt && \
    chown -R jenkins:jenkins /usr/share/jenkins/ref/plugins

# Install supervisor to manage Jenkins process (allows restart without container restart)
RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*

ENV JENKINS_OPTS="--disable-remember-me"
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false -Dhudson.DNSMultiCast.disabled=true -Djenkins.updatecheck.updateCheckServer=http://127.0.0.1:8000/updates/default.json -Djenkins.security.disableHudsonProtection=true"

RUN mkdir -p /var/log/supervisor /etc/supervisor/conf.d

RUN printf '[supervisord]\nnodaemon=true\nlogfile=/var/log/supervisor/supervisord.log\npidfile=/var/run/supervisord.pid\n\n[unix_http_server]\nfile=/var/run/supervisor.sock\n\n[supervisorctl]\nserverurl=unix:///var/run/supervisor.sock\n\n[rpcinterface:supervisor]\nsupervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface\n\n[include]\nfiles = /etc/supervisor/conf.d/*.conf\n\n[program:jenkins]\ncommand=java -Djenkins.install.runSetupWizard=false -Dhudson.DNSMultiCast.disabled=true -Djenkins.updatecheck.updateCheckServer=http://127.0.0.1:8000/updates/default.json -jar /usr/share/jenkins/jenkins.war --httpPort=8080\ndirectory=/var/jenkins_home\nuser=jenkins\nautostart=true\nautorestart=true\nstartsecs=10\nstopwaitsecs=10\nstdout_logfile=/var/log/supervisor/jenkins.log\nstderr_logfile=/var/log/supervisor/jenkins.err\n' > /etc/supervisor/supervisord.conf

RUN ( echo '#!/bin/bash'; \
      echo 'set -e'; \
      echo 'JENKINS_URL=${JENKINS_URL:-http://localhost:8080}'; \
      echo 'TIMEOUT=300'; \
      echo 'START=$(date +%s)'; \
      echo 'while true; do'; \
      echo '  if curl -s "$JENKINS_URL/api/json" > /dev/null 2>&1; then break; fi'; \
      echo '  NOW=$(date +%s)'; \
      echo '  if [ $((NOW - START)) -gt $TIMEOUT ]; then echo "Timeout waiting for Jenkins"; exit 1; fi'; \
      echo '  sleep 2'; \
      echo 'done'; \
      echo 'OUTPUT_FILE=${1:-/tmp/plugin_versions.txt}'; \
      echo 'mkdir -p "$(dirname "$OUTPUT_FILE")"'; \
      echo 'echo "Jenkins Plugins:" > "$OUTPUT_FILE"'; \
      echo 'curl -s "$JENKINS_URL/pluginManager/api/json?pretty=true" | grep -E "shortName|version" | paste - - >> "$OUTPUT_FILE" 2>/dev/null || true'; \
      echo 'cat "$OUTPUT_FILE"'; \
    ) > /usr/local/bin/dump-plugin-versions && \
    chmod +x /usr/local/bin/dump-plugin-versions

RUN printf '#!/bin/bash\nsupervisorctl restart jenkins\n' > /usr/local/bin/restart-jenkins && \
    chmod +x /usr/local/bin/restart-jenkins

# jenkins.sh ENTRYPOINT copies ref/plugins to JENKINS_HOME as root:root.
# Fix ownership before starting supervisord so Jenkins can unpack plugin JARs.
RUN printf '#!/bin/bash\nset -e\nchown -R jenkins:jenkins /var/jenkins_home/plugins/ 2>/dev/null || true\nexec /usr/bin/supervisord -c /etc/supervisor/supervisord.conf\n' \
    > /usr/local/bin/start-services && \
    chmod +x /usr/local/bin/start-services

EXPOSE 8080 50000

CMD ["/usr/local/bin/start-services"]
