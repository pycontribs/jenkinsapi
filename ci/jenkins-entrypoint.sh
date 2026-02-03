#!/bin/bash
# Jenkins entrypoint script that handles permission fixes

# Fix permissions on JENKINS_HOME before Jenkins starts
# This is critical for mounted volumes from the host
if [ -d /var/jenkins_home ]; then
    echo "Fixing JENKINS_HOME permissions..."
    chmod 777 /var/jenkins_home 2>/dev/null || true
fi

# Execute the original Jenkins startup script
# This replaces the current shell with jenkins.sh (PID 1 becomes jenkins.sh)
exec /usr/local/bin/jenkins.sh "$@"
