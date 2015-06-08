FROM ubuntu:latest

RUN apt-get update
RUN apt-get --yes install git python-twisted python-aalib python-imaging python-pymongo
RUN groupadd --gid 5000 boobiesbot
RUN useradd -m -d /home/boobiesbot -s /bin/bash --uid 5000 --no-user-group --group boobiesbot boobiesbot
RUN mkdir -p /data
RUN chown boobiesbot:boobiesbot /data

USER boobiesbot
WORKDIR /home/boobiesbot

CMD git clone https://github.com/StevenVanAcker/OverTheWire-boobiesbot.git && cd OverTheWire-boobiesbot && git checkout v2.0 && cd /data && /home/boobiesbot/OverTheWire-boobiesbot/boobiesbot.py $HOSTIP $HOSTIP
