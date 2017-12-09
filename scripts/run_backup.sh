#!/bin/bash

###########################################
# Backup process:
# 1.) pause consumer (so that no new files can be processed)
# 2.) run backup_script in webserver container
# 3.) unpause consumer

CONSUMER_NAME=paperless_consumer_1
WEBSERVER_NAME=paperless_webserver_1

docker container pause $CONSUMER_NAME

docker exec $WEBSERVER_NAME /usr/bin/backup_paperless_data.sh

docker container unpause $CONSUMER_NAME
