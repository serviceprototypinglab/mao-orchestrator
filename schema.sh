#!/bin/bash

######################################
############ Scheduler USER ############
######################################
sudo -i -u postgres psql -U postgres <<EOF
CREATE USER scheduler WITH PASSWORD 'password';
EOF

######################################
############ Jobstore DB #############
######################################
sudo -i -u postgres psql -U postgres <<EOF
CREATE DATABASE schedule WITH OWNER scheduler;
GRANT ALL PRIVILEGES ON DATABASE schedule TO scheduler;
EOF
