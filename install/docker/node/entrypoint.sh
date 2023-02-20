#!/bin/bash
# Configure netopeer server
/usr/bin/python3 configure_netconf_server.py
sysrepocfg --import=netconf-server-config.xml -f xml --datastore startup --module ietf-netconf-server -v3
sysrepocfg --import=netconf-server-config.xml -f xml --datastore running --module ietf-netconf-server -v3
sysrepocfg --import=netconf-acm-conf.xml -f xml --datastore startup --module ietf-netconf-acm -v3
sysrepocfg --import=netconf-acm-conf.xml -f xml --datastore running --module ietf-netconf-acm -v3
sleep 1
# Start node controller and netopeer server
/usr/bin/python3 -m opot_sdk -n & /usr/bin/netopeer2-server -d 2 -v 3