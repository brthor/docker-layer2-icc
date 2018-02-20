#!/bin/bash

docker network remove noiccnetwork
docker network create -o com.docker.network.bridge.enable_icc=false noiccnetwork

docker build -t "eth-listener" -f listener-Dockerfile .
docker build -t "eth-sender" -f sender-Dockerfile .

docker rm -f eth-listener eth-sender
listener_id=$(docker run --network noiccnetwork -d --name eth-listener eth-listener)
echo $listener_id
docker logs -f eth-listener > listener.log &

tail -f listener.log | docker run --network noiccnetwork -i --name eth-sender eth-sender

docker logs -f eth-listener