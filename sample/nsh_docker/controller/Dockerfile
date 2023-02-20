FROM python AS opot_nsh_test
# For none interaction installation
ARG DEBIAN_FRONTEND=noninteractive
ARG DOCKER=true
# Call the selected install.sh
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

COPY ./requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt
FROM opot_nsh_test
# Setting up tags for the configuration.
RUN   echo "[CONTROLLER]"  > /etc/default/controller_config.ini
RUN   echo "[OPENAPI]"  >> /etc/default/controller_config.ini

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x entrypoint.sh
