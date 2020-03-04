#!/bin/bash

# Partial testing of the Orchestrator system (can't test the federated features)

# As it is used locally for now,
# it does not handle requirements in its current state,
# for now install them manually:
# python
# Docker
# docker-compose

# Can act as a template for a future CI pipeline

# Test the spike detector and data comparison
python3.6 -m unittest test_differ.py test_audit.py
# Build the Docker image
docker build -t panosece/orchestrator .
# Scan the image with Clair
curl -s -L \
  https://raw.githubusercontent.com/simonsdave/clair-cicd/master/bin/assess-image-risk.sh | \
  bash -s -- -v panosece/orchestrator
# Set up the whole system
docker-compose up -d
# Run the test scenario
python3.6 -m unittest test_client.py
# Clean up
docker stop $(docker ps -a -q)

# Possible extensions:
# Integrate in a CI pipeline
# Deploy to the staging server via SSH
# Set up Node exporter for monitoring
