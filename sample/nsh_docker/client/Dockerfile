FROM ubuntu
RUN apt update && apt install -y \
    iproute2 \
    iputils-ping \
    traceroute \
    netcat \
    python3-pip \
    python3 \
    ethtool
RUN pip3 install scapy
COPY  ./set_router.sh /set_router.sh
RUN chmod +x set_router.sh