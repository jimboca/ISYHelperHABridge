#!/bin/bash -x

owd=`pwd`
if [ -f /lib/systemd/system/ihb.service ]; then
   sudo systemctl stop ihb
fi

cd ..
git pull
cd ../PyISY
git pull

if [ -f /lib/systemd/system/ihb.service ]; then
  #sudo cp ihb.service /lib/systemd/system/
  #sudo systemctl --system daemon-reload
  #sudo systemctl enable ihb
  sudo systemctl start ihb
  sudo systemctl status ihb
fi

