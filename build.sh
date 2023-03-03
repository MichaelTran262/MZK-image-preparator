#!/bin/bash
APP=krom-app
docker build . -t ${APP}
if [ ! -d "./testFolder" ];
then
    mkdir testFolder
else
    echo "testFolder exists, skipping"
fi
if [ ! -d "./logs" ];
then
    mkdir logs
    touch logs/Preparator.log
    touch logs/DataMover.log
else
    echo "logs directory exists, skipping"
fi