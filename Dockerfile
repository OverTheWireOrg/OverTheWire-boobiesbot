FROM ubuntu:latest

RUN apt-get update
RUN apt-get --yes install git python-twisted python-aalib python-imaging
RUN useradd -m -d /home/boobiesbot -s /bin/bash boobiesbot

USER boobiesbot
WORKDIR /home/boobiesbot

CMD git clone https://github.com/StevenVanAcker/OverTheWire-boobiesbot.git && ./OverTheWire-boobiesbot/boobiesbot.py

