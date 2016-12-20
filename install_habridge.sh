#!/bin/bash -x

owd=`pwd`
if [ -f /lib/systemd/system/habridge.service ]; then
   sudo systemctl stop habridge
fi

sudo cp habridge.service /lib/systemd/system/

cd /home/pi
if [ ! -d habridge ]; then
    mkdir habridge
fi
cd habridge
if [ ! -f ha-bridge-3.5.1.jar ]; then
    wget https://github.com/bwssytems/ha-bridge/releases/download/v3.5.1/ha-bridge-3.5.1.jar
fi

sudo systemctl --system daemon-reload
sudo systemctl enable habridge
sudo systemctl start habridge
sudo systemctl status habridge

