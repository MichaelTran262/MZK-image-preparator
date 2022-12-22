#!/bin/bash
APP=krom-app
docker build . -t ${APP}
mkdir testFolder
mkdir logs
touch logs/Preparator.log
touch logs/DataMover.log