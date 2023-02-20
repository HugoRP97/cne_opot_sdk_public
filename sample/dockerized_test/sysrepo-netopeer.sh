#!/bin/bash
user="netconf"
password="netconf"

# Install packages
apt-get update && apt-get install -y \
  git \
	curl \
	wget \
	libssl-dev \
	libtool \
	build-essential \
	vim \
	autoconf \
	automake \
	pkg-config \
	libgtk-3-dev \
	make \
	valgrind \
	doxygen \
	libev-dev \
	libpcre3-dev \
	unzip \
	sudo \
	python3 \
	python3-pip \
	bison \
	flex \
	swig \
	libcmocka0 \
	libcmocka-dev \
	cmake \
	supervisor

# Install pip3 packages
pip3 install libyang sysrepo

# Setup netconf user
adduser --system netconf
mkdir -p /home/netconf/.ssh
echo "netconf:netconf" | chpasswd && adduser netconf sudo

# Setup ssh keys
echo '' > /home/netconf/.ssh/authorized_keys && \
ssh-keygen -A && \
ssh-keygen -t rsa -b 4096 -P '' -f /home/netconf/.ssh/id_rsa && \
cat /home/netconf/.ssh/id_rsa.pub >> /home/netconf/.ssh/authorized_keys

# Setup main shell to bash
sed -i s#/home/netconf:/bin/false#/home/netconf:/bin/bash# /etc/passwd
mkdir /opt/dev && sudo chown -R netconf /opt/dev

# Download and install sysrepo and libyang:
sh -c "echo 'deb http://download.opensuse.org/repositories/home:/liberouter/xUbuntu_18.04/ /' > /etc/apt/sources.list.d/home:liberouter.list" && \
wget -nv https://download.opensuse.org/repositories/home:liberouter/xUbuntu_18.04/Release.key -O Release.key && \
apt-key add - < Release.key && \
apt-get update && \
apt-get install libyang1 libyang-dev sysrepo sysrepo-dev

# Download and install libssh:
cd /opt/dev && \
git clone https://git.libssh.org/projects/libssh.git && cd libssh && git checkout stable-0.9 && \
mkdir build && cd build && \
cmake -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_BUILD_TYPE="Release" -DWITH_ZLIB=ON -DWITH_NACL=OFF -DWITH_PCAP=OFF .. && \
make -j2 && \
make install

# Download and install libnetconf2
cd /opt/dev && \
git clone https://github.com/CESNET/libnetconf2.git && cd libnetconf2 && \
git checkout master && \
mkdir build && cd build && \
cmake  -DCMAKE_BUILD_TYPE:String="Release" -DCMAKE_INSTALL_PREFIX:PATH=/usr -DENABLE_BUILD_TESTS=OFF .. && \
make -j2 && \
make install

# Download and install netopeer 2
cd /opt/dev && \
git clone https://github.com/CESNET/Netopeer2.git && cd Netopeer2 && \
git checkout master && \
mkdir build && cd build && \
cmake -DCMAKE_INSTALL_PREFIX:PATH=/usr -DCMAKE_BUILD_TYPE:String="Release" .. && \
make -j2 && \
make install

# Download supervisor configuration and execute it
wget "https://raw.githubusercontent.com/sysrepo/sysrepo/master/deploy/docker/sysrepo-netopeer2/latest/supervisord.conf" -O /etc/supervisord.conf
/usr/bin/supervisord -c /etc/supervisord.conf