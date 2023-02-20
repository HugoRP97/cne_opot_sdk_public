FROM ubuntu
RUN mkdir /tmp/logs
WORKDIR /opt/opot_sdk
COPY requirements.txt /opt/opot_sdk/.
RUN apt-get update -y
RUN apt-get install -y python3 python3-pip python3-dev gcc iproute2 tmux iputils-ping neovim tcpdump psmisc python3-yaml htop
RUN pip3 install -r requirements.txt
WORKDIR /opt/opot_sdk/sample
# Setup the environment variables
ENV OPOT_CONTROLLER_IP="10.0.0.7"
ENV OPOT_CONTROLLER_PORT=42582
ENV NODE_CONTROLLER_PORT=44000