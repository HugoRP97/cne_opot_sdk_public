#!/bin/bash
echo "[+] Configuring netconf user"
cat <<EOT >> /etc/default/node_config.ini
[NODE]
EOT
# Setup netconf user
adduser --system netconf
mkdir -p /home/netconf/.ssh
echo "netconf:netconf" | chpasswd && adduser netconf sudo;
echo "[+] Adding Netopeer Server Configuration files"
cp /cne-opot_sdk/install/docker/node/configure_netconf_server.py /configure_netconf_server.py
echo "[+] Installing opot_sdk requirements" && \
pip3 install -r /cne-opot_sdk/requirements.txt --src /usr/local/src
#pip3 install sysrepo==1.3.0 mpmath==1.2.1 numpy pycryptodome==3.10.1 scipy==1.5.4 sympy==1.8 connexion==2.7.0 PyYAML==5.3.1 ncclient==0.6.12 six==1.13.0 google-api-python-client==2.7.0 grpcio==1.48.1 grpcio-tools==1.48.1 prometheus-client==0.11.0 kafka-python==2.0.2 libyang==2.4.0 sysrepo==1.3.0 netifaces==0.11.0
echo "[+] Setting path for nectconf-acm"
cp ./cne-opot_sdk/install/docker/node/netconf-acm-conf.xml /netconf-acm-conf.xml
echo "[+] Copy entrypoint.sh"
cp /cne-opot_sdk/install/docker/node/entrypoint.sh /entrypoint.sh
chmod +x /entrypoint.sh