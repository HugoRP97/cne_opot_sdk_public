#!/bin/bash
echo "Stopping all the containers"
docker stop $(docker ps -a -q --filter network=opot)
echo "Removing all the containers"
docker rm $(docker ps -a -q --filter network=opot)
echo "Removing network"
docker network rm opot