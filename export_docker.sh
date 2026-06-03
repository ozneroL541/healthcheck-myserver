#!/bin/bash

docker build -t healthcheck-myserver:latest .
docker container create --name healthcheck-myserver healthcheck-myserver:latest
tmp_folder="tmp"
mkdir -p ${tmp_folder}
docker container export healthcheck-myserver > ${tmp_folder}/healthcheck-myserver.tar
gzip < ${tmp_folder}/healthcheck-myserver.tar > ${tmp_folder}/healthcheck-myserver.tar.gz
