#!/bin/bash

# This just creates the configuration file for the controller
cat <<EOT >> /etc/default/controller_config.ini
[CONTROLLER]
[OPENAPI]
[KAFKA]
EOT

echo "[+] Installing opot_sdk requirements" && \
  /usr/bin/pip3 install -r /cne-opot_sdk/requirements.txt &&
  /usr/bin/pip3 install -r /cne-opot_sdk/requirements_api.txt

cp /cne-opot_sdk/install/docker/controller/entrypoint.sh /entrypoint.sh
chmod +x /entrypoint.sh
#ENTRYPOINT ["/usr/bin/bash", "/entrypoint.sh"]



