# Setup for node
FROM python AS node_nsh_test
# For none interaction installation
ARG DEBIAN_FRONTEND=noninteractive
ARG DOCKER=true
# Call the selected install.sh
#RUN cd /cne-opot_sdk/install; bash install.sh node
RUN apt-get update && apt-get install -y \
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
          python3-cffi
RUN echo "[+] Updating setuptools" && pip3 install --upgrade pip setuptools
RUN mkdir /opt/dev

RUN  echo "[+] Configuring netconf user" && \
      # Setup netconf user
      adduser --system netconf && \
      mkdir -p /home/netconf/.ssh && \
      echo "netconf:netconf" | chpasswd && adduser netconf sudo;

RUN echo "[+] Install libyang" \
      cd /opt/dev && \
      git clone --single-branch --branch libyang1 https://github.com/CESNET/libyang; \
      cd libyang && mkdir build && cd build; \
      cmake -DGEN_LANGUAGE_BINDINGS=ON -DCMAKE_BUILD_TYPE:String="Release" -DCMAKE_INSTALL_PREFIX:PATH=/usr -DENABLE_BUILD_TESTS=OFF .. && \
      make install
RUN   echo "[+] Install sysrepo"; \
      cd /opt/dev && \
      git clone --single-branch --branch libyang1 https://github.com/sysrepo/sysrepo; \
      cd sysrepo && mkdir build && cd build; \
      cmake -DGEN_LANGUAGE_BINDINGS=ON  -DENABLE_TESTS=OFF -DCMAKE_BUILD_TYPE="Release" -DCMAKE_INSTALL_PREFIX:PATH=/usr -DREPOSITORY_LOC:PATH=/etc/sysrepo .. && \
      make install
RUN   echo "[+] Installing libssh"; \
      cd /opt/dev && \
      git clone  https://git.libssh.org/projects/libssh.git; \
      cd libssh && git checkout stable-0.9 && \
      mkdir build && cd build;\
      cmake -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_BUILD_TYPE="Release" -DWITH_ZLIB=ON -DWITH_NACL=OFF -DWITH_PCAP=OFF .. && \
      make -j2 && \
      make install
RUN echo "[+] Installing libnetconf2"; \
      cd /opt/dev && \
      git clone --single-branch --branch libyang1 https://github.com/CESNET/libnetconf2.git; \
      cd libnetconf2 && \
      mkdir build && cd build && \
      cmake  -DCMAKE_BUILD_TYPE:String="Release" -DCMAKE_INSTALL_PREFIX:PATH=/usr -DENABLE_BUILD_TESTS=OFF .. && \
      make -j2 && \
      make install
RUN echo "[+] Installing netopeer2"; \
      cd /opt/dev && \
      git clone --single-branch --branch libyang1 https://github.com/CESNET/Netopeer2.git; \
      cd Netopeer2 && \
      mkdir build && cd build && \
      cmake -DCMAKE_INSTALL_PREFIX:PATH=/usr -DCMAKE_BUILD_TYPE:String="Release" .. && \
      make -j2 && \
      make install
RUN   echo "[NODE]"  > /etc/default/node_config.ini
COPY ./requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt
ENV NETCONF_PORT=830
ENV NETCONF_IP="0.0.0.0"

#FROM node_nsh_test
COPY config_files /config
#RUN cd config && bash entrypoint.sh
RUN /usr/bin/python3 /config/configure_netconf_server.py
RUN sysrepocfg --import=/config/netconf-acm-conf.xml -f xml --datastore startup --module ietf-netconf-acm -v3
RUN sysrepocfg --import=/config/netconf-acm-conf.xml -f xml --datastore running --module ietf-netconf-acm -v3


