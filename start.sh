#!/bin/bash
APP=krom_preparator
docker build . -t ${APP} && \
docker run -p 5000:5000 -v test:/mnt/storage ${APP}
