#!/bin/bash

######################################
############ Gateway USER ############
######################################
sudo -i -u postgres psql -U postgres <<EOF
CREATE USER username WITH PASSWORD 'password';
EOF

######################################
############ Gateway DB #############
######################################
sudo -i -u postgres psql -U postgres <<EOF
CREATE DATABASE gateway WITH OWNER username;
GRANT ALL PRIVILEGES ON DATABASE gateway TO username;
EOF

######################################
############ Nodes table #############
######################################
psql -U username -h localhost -d gateway <<EOF
CREATE TABLE IF NOT EXISTS nodes (
  username      TEXT              PRIMARY KEY,
  ip            TEXT              NOT NULL,
  location      TEXT              NOT NULL
);
EOF
