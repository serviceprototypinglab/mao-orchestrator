#! /bin/bash

echo "[WORKING_ENVIRONMENT]\n"\
"importdir = $importdir\n"\
"hostdir = $hostdir\n"\
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

until pg_isready -h "$dbhost" -U "$dbuser" -d "$db"
do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done

echo "StrictHostKeyChecking no" >> /home/user/.ssh/config
#echo "StrictHostKeyChecking no" >> /.ssh/config
git config --global user.email $gitemail
git config --global user.name $gitusername
