#!/bin/bash
i=0
for ip in $(cat path.json | jq -r ".nodes[].ip"); do
        docker exec -it "node$i" sh -c "tmux kill-session -t session"
        docker exec -it "node$i" sh -c "tmux new-session -c /opt/opot_sdk/sample -d -s \"session\" python3 /opt/opot_sdk/sample/run.py -n"
        i=$(($i + 1))
done
docker exec -it "opot_controller" sh -c "tmux kill-session -t session"
docker exec -it opot_controller sh -c "tmux new-session -c /opt/opot_sdk/sample -d -s \"session\" python3 /opt/opot_sdk/sample/run.py -o"
