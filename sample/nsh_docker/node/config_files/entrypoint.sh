#!/bin/bash
/usr/bin/python3 /config/configure_netconf_server.py
sysrepocfg --import=/config/netconf-server-config.xml -f xml --datastore startup --module ietf-netconf-server -v3
sysrepocfg --import=/config/netconf-server-config.xml -f xml --datastore running --module ietf-netconf-server -v3
echo "[+] Install Yang Model"; sysrepoctl -i /config/ietf-pot-profile.yang
echo "[+] Running netopeer server in the background";
# Configure netopeer server
/usr/bin/netopeer2-server -d 2 -v 3 &