#!/bin/bash -x

base_dir=/home/pi/ihab

owd=`pwd`
if [ -f /lib/systemd/system/habridge.service ]; then
   sudo systemctl stop habridge
fi

sudo cp util/habridge.service /lib/systemd/system/

if [ ! -d $base_dir ]; then
    echo "? Error: $base_dir does not exist"
    exit 1
fi

cd $base_dir
if [ ! -d habridge ]; then
    mkdir habridge
fi

cd habridge
if [ ! -f ha-bridge-3.5.1.jar ]; then
    wget https://github.com/bwssytems/ha-bridge/releases/download/v3.5.1/ha-bridge-3.5.1.jar
    rm -f ha-bridge.jar
    ln -s ha-bridge-3.5.1.jar ha-bridge.jar
fi

sudo systemctl --system daemon-reload
sudo systemctl enable habridge
sudo systemctl start habridge
sudo systemctl status habridge
