#!/bin/bash
# TODO Add the commands to install the controller or the node following the install.md
install_packages () {
  echo "[+] Installing necessary packages"
  apt-get update && apt-get install -y \
      sudo \
      htop \
      git \
      curl \
      wget \
      sudo \
      libssl-dev \
      libtool \
      build-essential \
      autoconf \
      automake \
      pkg-config \
      libgtk-3-dev \
      make \
      vim \
      valgrind \
      doxygen \
      libev-dev \
      libavl-dev \
      libpcre3-dev \
      unzip \
      sudo \
      python-setuptools \
      python-dev \
      build-essential \
      bison \
      flex \
      python3 \
      python3-pip \
      python3-dev \
      gcc \
      iproute2 \
      tmux \
      iputils-ping \
      neovim \
      tcpdump \
      psmisc \
      python3-yaml \
      cmake \
      protobuf-compiler \
      libcurl4-openssl-dev \
      swig \
      python3-cffi \
      libyaml-dev

      echo "[+] Updating setuptools"
      pip3 install --upgrade pip setuptools
  }

install_libyang() {
  echo "[+] Install libyang"
  cd /opt/dev && \
  git clone --single-branch --branch libyang1 https://github.com/CESNET/libyang &> /dev/null
  cd libyang
  mkdir build
  cd build
  cmake -DGEN_LANGUAGE_BINDINGS=ON - -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_BUILD_TYPE="Release" -DWITH_ZLIB=ON -DWITH_NACL=OFF -DWITH_PCAP=OFF  .. && \
  make install
}
install_sysrepo() {
  echo "[+] Install sysrepo"
  cd /opt/dev && \
  git clone --single-branch --branch libyang1 https://github.com/sysrepo/sysrepo &> /dev/null
  cd sysrepo
  mkdir build
  cd build
  cmake -DGEN_LANGUAGE_BINDINGS=ON   -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_BUILD_TYPE="Release" -DWITH_ZLIB=ON -DWITH_NACL=OFF -DWITH_PCAP=OFF  -DREPOSITORY_LOC:PATH=/etc/sysrepo .. && \
  make install
}
install_node_packages() {

  # Install libyang
  install_libyang
  # Install sysrepo
  install_sysrepo

  # Download and install libssh:
  echo "[+] Installing libssh"
  cd /opt/dev && \
  git clone  https://git.libssh.org/projects/libssh.git &> /dev/null
  cd libssh && git checkout stable-0.9
  mkdir build
  cd build && \
  cmake  -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_BUILD_TYPE="Release" -DWITH_ZLIB=ON -DWITH_NACL=OFF -DWITH_PCAP=OFF .. && \
  make -j2 && \
  make install

  # Download and install libnetconf2
  echo "[+] Installing libnetconf2"
  cd /opt/dev && \
  git clone --single-branch --branch libyang1 https://github.com/CESNET/libnetconf2.git &> /dev/null
  cd libnetconf2 && \
  mkdir build
  cd build && \
  cmake  -DCMAKE_BUILD_TYPE:String="Release" -DCMAKE_INSTALL_PREFIX:PATH=/usr -DENABLE_BUILD_TESTS=OFF .. && \
  make -j2 && \
  make install

  # Download and install netopeer2
  echo "[+] Installing netopeer2"
  cd /opt/dev && \
  git clone --single-branch --branch libyang1 https://github.com/CESNET/Netopeer2.git &> /dev/null
  cd Netopeer2 && \
  mkdir build
  cd build && \
  cmake -DCMAKE_INSTALL_PREFIX:PATH=/usr -DCMAKE_BUILD_TYPE:String="Release" .. && \
  make -j2 && \
  make install
}

function install_node () {
  echo "[+] Configuring netconf user"
  # Setup netconf user
  adduser --system netconf
  mkdir -p /home/netconf/.ssh
  echo "netconf:netconf" | chpasswd && adduser netconf sudo
  mkdir /opt/dev && sudo chown -R netconf /opt/dev

  ## Setup ssh keys
  #echo '' > /home/netconf/.ssh/authorized_keys && \
  #ssh-keygen -A && \
  #ssh-keygen -t rsa -b 4096 -P '' -f /home/netconf/.ssh/id_rsa && \
  #cat /home/netconf/.ssh/id_rsa.pub >> /home/netconf/.ssh/authorized_keys
  # Setup main shell to bash

  echo "[+] Installing necessary packages"

  install_packages
  install_node_packages

  echo "[+] Setting bash as main shell"
  sed -i s#/home/netconf:/bin/false#/home/netconf:/bin/bash# /etc/passwd
  # Setup root password (TODO change this)
  # echo "root:netconf"
  echo "[+] Install Yang Model"
  sysrepoctl -i ${OPOT_DIRECTORY}/yang/ietf-pot-profile.yang

  # Install python scripts
  echo "[+] Installing Node"
  cd $OPOT_DIRECTORY/../
  python3 setup.py install


  if [ "$DOCKER" != "True" ]; then
    # Setting up netopeer service
    echo "[+] Setting up netopeer2 service"
    cp $OPOT_DIRECTORY/services/netopeer2server.service  /etc/systemd/system/.
    echo "[+] Starting netopeer2"
    systemctl enable netopeer2server
    systemctl start netopeer2server
    # Copy default config to /etc/default/node_config.ini
    echo "[+] Copying configuration files"
    cd $OPOT_DIRECTORY
    cp configs/node_config.ini /etc/default/node_config.ini
  else
    echo "[+] Building docker image"
  fi
  # Creating logs directory
  echo "[+] Creating logs directory"
  mkdir /var/log/opot/
}

function install_controller () {
  echo "[+] Install mandatory packages"
  mkdir /opt/dev
  install_packages
  install_libyang
  install_sysrepo
  # Install python scripts
  echo "[+] Installing Controller"
  cd $OPOT_DIRECTORY/../
  python3 setup.py install

  echo "[+] Adding pip packages for the API"
  pip3 install -r requirements_api.txt
  pip3 install connexion[swagger-ui]
  sudo pip3 install google-api-python-client
  if [ "$DOCKER" != "True" ]; then
    echo "[+] Copying configuration files"
    # Add configuration file to /etc/default/controller_config.ini
    cd $OPOT_DIRECTORY
    cp configs/controller_config.ini /etc/default/controller_config.ini
  else
      echo "[+] Building docker image"
  fi

  echo "[+] Creating logs directory"
  # Creating logs directory
  mkdir /var/log/opot/
}


OPOT_DIRECTORY=`pwd`
if [ -z $1 ]
then
  echo "\$1 is empty"
else
  if [ "$1" == "node" ]; then
    echo "[+] You have selected to install a node."
    install_node
  elif [ "$1" == "controller" ]; then
    echo "[+] You have selected to install the controller."
    install_controller
  else
    echo "[!] Bad input"
  fi
fi

