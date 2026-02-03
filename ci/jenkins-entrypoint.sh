#!/bin/bash
# Jenkins entrypoint script that properly handles restarts
# This script is wrapped by dumb-init to ensure proper signal handling
# and restarts Jenkins if it crashes

# Don't exit on error - we want to handle restarts
set +e

# Function to handle signals
handle_signal() {
    echo "Received signal, shutting down Jenkins gracefully..."
    kill -TERM "$JENKINS_PID" 2>/dev/null || true
    wait "$JENKINS_PID" 2>/dev/null || true
    exit 0
}

# Trap signals
trap handle_signal SIGTERM SIGINT

# Run Jenkins and keep restarting it if it crashes
while true; do
    echo "Starting Jenkins..."
    /usr/local/bin/jenkins.sh "$@" &
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
