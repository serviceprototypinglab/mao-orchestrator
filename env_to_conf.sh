#! /bin/bash

echo "[WORKING_ENVIRONMENT]\n"\
"importdir = $importdir\n"\
"auditdir = $auditdir\n"\
"user = $workuser\n\n"\
"[ETCD]\n"\
"host = $etcdhost\n"\
"port = $port\n\n"\
"[POSTGRES]\n"\
"user = $dbuser\n"\
"password = $password\n"\
"db = $db\n"\
"host = $dbhost\n\n"\
"[DATA_REPOS]" > config.ini
