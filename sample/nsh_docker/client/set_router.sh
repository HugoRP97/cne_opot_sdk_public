#!/bin/bash
ip route add $NETWORK via $NEXT_HOP
ethtool --offload  eth0  rx off  tx off
ethtool -K eth0 gso off
bash