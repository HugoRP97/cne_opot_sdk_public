# Setup for node
FROM ubuntu:18.04 AS opot_main_packages
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
          valgrind \
          doxygen \
          libev-dev \
          libavl-dev \
          libpcre3-dev \
          unzip \
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
          libpam0g-dev \
          libpam-modules
RUN echo "[+] Updating setuptools" && pip3 install --upgrade pip setuptools
RUN mkdir /opt/dev
# Create Logs directory
RUN   echo "[+] Creating logs directory" && mkdir /var/log/opot/
ARG type
# Install dependencies
RUN echo "[+] Install pcre2" && \
      cd /opt/dev && \
      cd /opt/dev && \
      git clone --single-branch --branch pcre2-10.40  https://github.com/PCRE2Project/pcre2/  && \
      cd pcre2 && \
      ./autogen.sh &&\
      ./configure && \
      make install && \
      ldconfig
RUN echo "[+] Install libyang" && \
      cd /opt/dev && \
      git clone --single-branch --branch v2.0.231 https://github.com/CESNET/libyang && \
      cd libyang && mkdir build && cd build; \
      cmake -DGEN_LANGUAGE_BINDINGS=ON -DCMAKE_BUILD_TYPE:String="Release"  -DENABLE_BUILD_TESTS=OFF .. && \
      make install
RUN echo "[+] Install sysrepo" && \
      cd /opt/dev && \
      git clone --single-branch --branch v2.1.84 https://github.com/sysrepo/sysrepo && \
      cd sysrepo && mkdir build && cd build && \
      cmake -DGEN_LANGUAGE_BINDINGS=ON  -DENABLE_TESTS=OFF -DCMAKE_BUILD_TYPE="Release"  -DREPOSITORY_LOC:PATH=/etc/sysrepo .. && \
      make install && ldconfig
# Install node dependencies
RUN if [ "$type" = "node" ]; then echo "[+] Installing libssh" && \
      cd /opt/dev && \
      git clone  https://git.libssh.org/projects/libssh.git && \
      cd libssh && git checkout stable-0.9 && \
      mkdir build && cd build &&\
      cmake -DCMAKE_BUILD_TYPE="Release" -DWITH_ZLIB=ON -DWITH_NACL=OFF -DWITH_PCAP=OFF .. && \
      make -j2 && \
      make install; \
     fi
RUN if [ "$type" = "node" ]; then echo "[+] Installing libnetconf2" && \
      cd /opt/dev && \
      git clone --single-branch --branch v2.1.18 https://github.com/CESNET/libnetconf2.git && \
      cd libnetconf2 && \
      mkdir build && cd build && \
      cmake  -DCMAKE_BUILD_TYPE:String="Release"  -DENABLE_BUILD_TESTS=OFF .. && \
      make -j2 && \
      make install && \
      ldconfig; \
    fi
RUN if [ "$type" = "node" ]; then echo "[+] Installing netopeer2" && \
      cd /opt/dev && \
      git clone --single-branch --branch v2.1.36 https://github.com/CESNET/Netopeer2.git && \
      cd Netopeer2 && \
      mkdir build && cd build && \
      cmake  -DCMAKE_BUILD_TYPE:String="Release" .. && \
      make -j2 && \
      make install; \
    fi
# Add the installation files into /opt/pot
ADD . /cne-opot_sdk
# Argument to setup a node or a controller
USER root
WORKDIR /
RUN if [ "$type" = "controller" ]; then bash /cne-opot_sdk/install/docker/controller/install.sh; \
    elif [ "$type" = "node" ]; \
    then bash /cne-opot_sdk/install/docker/node/install.sh; \
    else echo "This option does not exist"; \
    fi

RUN rm -r /opt/dev

ENV NETCONF_PORT=830
ENV NETCONF_IP="0.0.0.0"




