#!/bin/bash -x

owd=`pwd`
if [ -f /lib/systemd/system/ihb.service ]; then
   sudo systemctl stop ihb
fi

sudo cp ihb.service /lib/systemd/system/
sudo systemctl --system daemon-reload

cd ..
git clone https://github.com/jimboca/PyISY

sudo systemctl enable ihb
sudo systemctl start ihb
sudo systemctl status ihb
