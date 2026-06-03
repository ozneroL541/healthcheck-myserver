#!/bin/bash

docker build -t healthcheck-myserver:latest . && docker container create --name healthcheck-myserver healthcheck-myserver:latest && \
if [ $? -ne 0 ]; then
    echo "Error: Docker build or container creation failed."
    exit $last_cmd
fi
tmp_folder="tmp"
mkdir -p ${tmp_folder}
docker container export healthcheck-myserver > ${tmp_folder}/healthcheck-myserver.tar && \
gzip < ${tmp_folder}/healthcheck-myserver.tar > ${tmp_folder}/healthcheck-myserver.tar.gz
