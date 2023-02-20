#!/bin/bash
# Configure netopeer server
echo "[+] Configuring sysrepo and netopeer server."
sysrepoctl -i /cne-opot_sdk/install/yang/ietf-pot-profile.yang
/usr/bin/python3 configure_netconf_server.py
sysrepocfg --import=netconf-server-config.xml -f xml --datastore startup --module ietf-netconf-server -v3
sysrepocfg --import=netconf-server-config.xml -f xml --datastore running --module ietf-netconf-server -v3
sysrepocfg --import=netconf-acm-conf.xml -f xml --datastore startup --module ietf-netconf-acm -v3
sysrepocfg --import=netconf-acm-conf.xml -f xml --datastore running --module ietf-netconf-acm -v3
sleep 1
echo "[+] Starting Node"
# Start node and netopeer server
cd /cne-opot_sdk/opot_sdk
/usr/bin/python3 /cne-opot_sdk/opot_sdk/__main__.py -n & netopeer2-server -d -v2