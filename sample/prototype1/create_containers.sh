#!/bin/bash

# Setup the network
echo "Instantiating the network opot"
docker network create -d bridge --subnet=10.0.0.0/24 opot --gateway 10.0.0.254 2> /dev/null

# Setup the nodes

# Create a container for each of the nodes using the file path1.json. It is requested to install the package jq
# which is a json parser for the cli
i=0
for ip in $(cat path.json | jq -r ".nodes[].ip"); do
	echo "Setting up Node$i with ip $ip"
	docker run -itd --network opot \
		--mount type=bind,src="$(pwd)/../",dst=/opt/opot_sdk \
		--ip="$ip" \
		--name "node$i" \
		--hostname "node$i" \
	  -e NODE_CONTROLLER_IP="$ip"\
		opot_image:prototype1
	echo "Launching the NodeController"
	docker exec -it "node$i" sh -c "tmux new-session -c /opt/opot_sdk/sample -d -s session python3 /opt/opot_sdk/sample/run.py -n"
	i=$(($i + 1))
done

# Create the OPoTController
echo "Setting up opot_controller"
docker run -itd --network opot \
	--mount type=bind,src="$(pwd)/../",dst=/opt/opot_sdk \
	--ip="10.0.0.7" \
	--name opot_controller \
	--hostname opot_controller \
	opot_image:prototype1
echo "Launching the OPoTController"
docker exec -it opot_controller sh -c "tmux new-session -c /opt/opot_sdk/sample -d -s session python3 /opt/opot_sdk/sample/run.py -o"

# Create the receiver and the sender
echo "Setting up the receiver"
ip=$(cat path.json | jq -r ".receiver.ip")
docker run -itd --network opot \
	--mount type=bind,src="$(pwd)/../",dst=/opt/opot_sdk \
	--ip="$ip" \
	--name receiver \
	--hostname receiver \
	opot_image:prototype1

echo "Setting up the sender"
ip=$(cat path.json | jq -r ".sender.ip")
docker run -itd --network opot \
	--mount type=bind,src="$(pwd)/../",dst=/opt/opot_sdk \
	--ip="$ip" \
	--name sender \
	--hostname sender \
	opot_image:prototype1
