#!/bin/bash
#JENKINS_WAR_URL="http://mirrors.jenkins-ci.org/war/latest/jenkins.war"

if [[ "$#" -ne 3 ]]; then
    echo "Usage: $0 jenkins_url path_to_store_jenkins war_filename"
    exit 1
fi

readonly JENKINS_WAR_URL=$1
readonly JENKINS_PATH=$2
readonly WAR_FILENAME=$3

echo "Downloading $JENKINS_WAR_URL to ${JENKINS_PATH}"
VER="$(curl -fsSL "$JENKINS_WAR_URL/" | grep -oE 'href="[0-9]+\.[0-9]+/' | sed 's/href="//;s:/$::' | sort -V | tail -1)"
echo "Downloading version $VER"

curl -fL -o "$JENKINS_PATH/jenkins.war" "$JENKINS_WAR_URL/$VER/jenkins.war"

# Optional: verify checksum (Linux)
#curl -fsSL "$JENKINS_WAR_URL/$VER/jenkins.war.sha256" | awk '{print $1" "}' | sha256sum -c -

echo "Jenkins downloaded"
