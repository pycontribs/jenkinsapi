#!/bin/bash
# Jenkins entrypoint script that properly handles restarts
# This script is wrapped by dumb-init to ensure proper signal handling
# and restarts Jenkins if it crashes

# Don't exit on error - we want to handle restarts
set +e

# Fix permissions on JENKINS_HOME before Jenkins starts
# This is critical for mounted volumes from the host
if [ -d /var/jenkins_home ]; then
    echo "Fixing JENKINS_HOME permissions..."
    chmod 777 /var/jenkins_home 2>/dev/null || true
    chown jenkins:jenkins /var/jenkins_home 2>/dev/null || true
fi

# Function to handle signals
handle_signal() {
    echo "Received signal, shutting down Jenkins gracefully..."
    if [ -n "$JENKINS_PID" ]; then
        kill -TERM "$JENKINS_PID" 2>/dev/null || true
        wait "$JENKINS_PID" 2>/dev/null || true
    fi
    exit 0
}

# Trap signals
trap handle_signal SIGTERM SIGINT

# Run Jenkins and keep restarting it if it crashes
while true; do
    echo "Starting Jenkins..."
    # Run Jenkins as jenkins user using gosu (available in jenkins base image)
    gosu jenkins /usr/local/bin/jenkins.sh "$@" &
    JENKINS_PID=$!

    # Wait for Jenkins to exit
    wait $JENKINS_PID
    JENKINS_EXIT_CODE=$?

    echo "Jenkins exited with code: $JENKINS_EXIT_CODE"

    # If Jenkins was stopped gracefully (by signal), exit
    if [ $JENKINS_EXIT_CODE -eq 143 ] || [ $JENKINS_EXIT_CODE -eq 0 ]; then
        echo "Jenkins shut down gracefully"
        exit 0
    fi

    # Otherwise, wait a bit and restart
    echo "Restarting Jenkins in 5 seconds..."
    sleep 5
done
