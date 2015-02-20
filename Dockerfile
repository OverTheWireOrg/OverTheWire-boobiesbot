FROM ubuntu:latest

RUN apt-get update
RUN apt-get --yes install git python-twisted python-aalib python-imaging
RUN useradd -m -d /home/boobiesbot -s /bin/bash boobiesbot
RUN mkdir -p /data
RUN chown boobiesbot:boobiesbot /data

USER boobiesbot
WORKDIR /home/boobiesbot

CMD git clone https://github.com/StevenVanAcker/OverTheWire-boobiesbot.git  && cd /data && /home/boobiesbot/OverTheWire-boobiesbot/boobiesbot.py $HOSTIP

